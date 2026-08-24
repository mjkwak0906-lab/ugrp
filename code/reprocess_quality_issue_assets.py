from __future__ import annotations

"""품질 제외 asset 45개를 별도 폴더에 재처리 후보로 만든다.

주의:
- 기존 315개 asset은 덮어쓰지 않는다.
- 입력 RGB는 candidate_assets/records_105의 기존 PNG에서 가져온다.
  이 파일은 alpha=0 영역에도 원본 crop RGB가 남아 있어 재처리 소스로 쓸 수 있다.
- 결과는 candidate_assets_v4_preserve/reprocessed_candidates 아래에 쌓는다.
"""

import csv
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parent
OLD_ASSET_ROOT = PROJECT_ROOT / "candidate_assets" / "records_105"
V4_ASSET_ROOT = PROJECT_ROOT / "candidate_assets_v4_preserve" / "records_105"
ISSUE_CSV = PROJECT_ROOT / "candidate_assets_v4_preserve" / "asset_quality_review" / "asset_quality_issues.csv"
OUT_ROOT = PROJECT_ROOT / "candidate_assets_v4_preserve" / "reprocessed_candidates"


PROFILES = [
    {"name": "thr100_min8", "kind": "threshold", "threshold": 100, "min_area": 8, "close": False},
    {"name": "thr110_min8", "kind": "threshold", "threshold": 110, "min_area": 8, "close": False},
    {"name": "thr120_min10", "kind": "threshold", "threshold": 120, "min_area": 10, "close": False},
    {"name": "thr130_min15", "kind": "threshold", "threshold": 130, "min_area": 15, "close": True},
    {"name": "local_contrast_18", "kind": "local_contrast", "delta": 18, "min_area": 8},
    {"name": "local_contrast_24", "kind": "local_contrast", "delta": 24, "min_area": 8},
    {"name": "edge_canny_d1", "kind": "edge", "low": 25, "high": 80, "dilate": 1, "min_area": 5},
]


def keep_components(mask: np.ndarray, min_area: int, reject_filled_blocks: bool = False) -> np.ndarray:
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    kept = np.zeros_like(mask)
    for label in range(1, num):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        if reject_filled_blocks:
            w = int(stats[label, cv2.CC_STAT_WIDTH])
            h = int(stats[label, cv2.CC_STAT_HEIGHT])
            fill_ratio = area / max(1, w * h)
            # Marker strokes are sparse inside their bounding box. Board/background
            # remnants are often dense blobs, especially near the crop corners.
            if fill_ratio > 0.55 and area > 40:
                continue
        kept[labels == label] = 255
    return kept


def make_asset(crop_bgr: np.ndarray, profile: dict[str, object]) -> np.ndarray:
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    kind = str(profile["kind"])
    reject_filled_blocks = False
    if kind == "threshold":
        mask = np.where(gray <= int(profile["threshold"]), 255, 0).astype(np.uint8)
        if bool(profile["close"]):
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
    elif kind == "local_contrast":
        background = cv2.medianBlur(gray, 17)
        mask = np.where((background.astype(np.int16) - gray.astype(np.int16)) >= int(profile["delta"]), 255, 0).astype(
            np.uint8
        )
        reject_filled_blocks = True
    elif kind == "edge":
        mask = cv2.Canny(gray, int(profile["low"]), int(profile["high"]))
        dilate = int(profile["dilate"])
        if dilate > 0:
            mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=dilate)
        reject_filled_blocks = True
    else:
        raise ValueError(f"Unknown profile kind: {kind}")

    kept = keep_components(mask, int(profile["min_area"]), reject_filled_blocks=reject_filled_blocks)

    bgra = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = kept
    bgra[kept == 0, :3] = 0
    return bgra


def source_for(shape: str, name: str) -> Path:
    old = OLD_ASSET_ROOT / shape / name
    if old.exists():
        return old
    return V4_ASSET_ROOT / shape / name


def alpha_pixels(path: Path) -> int:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None or image.ndim != 3 or image.shape[2] < 4:
        return 0
    return int(np.count_nonzero(image[:, :, 3]))


def choose_best(issue: str, original_alpha: int, candidates: list[tuple[Path, int]]) -> Path:
    # 배경 남음은 alpha를 줄이는 것이 목적이다. 너무 줄어들면 선이 끊길 수 있으므로
    # 원래 alpha의 45~85% 범위 중 가장 큰 후보를 우선 고른다.
    if issue == "background_remaining":
        lo = original_alpha * 0.45
        hi = original_alpha * 0.85
        plausible = [(p, a) for p, a in candidates if lo <= a <= hi]
        if plausible:
            return max(plausible, key=lambda item: item[1])[0]
        return min(candidates, key=lambda item: abs(item[1] - original_alpha * 0.65))[0]

    # 지저분함/잘림은 자동 복구 확신도가 낮으므로 원래 alpha와 가장 가까우면서 약간 줄어든 후보를 고른다.
    plausible = [(p, a) for p, a in candidates if original_alpha * 0.55 <= a <= original_alpha * 1.05]
    if plausible:
        return min(plausible, key=lambda item: abs(item[1] - original_alpha * 0.8))[0]
    return min(candidates, key=lambda item: abs(item[1] - original_alpha))[0]


def write_contact_sheet(rows: list[dict[str, str]]) -> Path:
    entries = []
    for row in rows:
        entries.append((row["shape"], row["number"], Path(row["best_path"])))

    cell_w, cell_h = 170, 190
    cols = 9
    rows_count = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGB", (cell_w * cols, cell_h * rows_count), (34, 34, 34))
    draw = ImageDraw.Draw(sheet)
    for idx, (shape, number, path) in enumerate(entries):
        col = idx % cols
        row = idx // cols
        x0 = col * cell_w
        y0 = row * cell_h
        tile = Image.new("RGBA", (cell_w, cell_h), (34, 34, 34, 255))
        image = Image.open(path).convert("RGBA")
        image.thumbnail((cell_w - 24, cell_h - 44), Image.Resampling.LANCZOS)
        tile.alpha_composite(image, ((cell_w - image.width) // 2, 32 + (cell_h - 44 - image.height) // 2))
        sheet.paste(tile.convert("RGB"), (x0, y0))
        draw.text((x0 + 6, y0 + 7), f"{shape} #{number}", fill=(240, 240, 240))
    out = OUT_ROOT / "best_guess_contact_sheet.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with ISSUE_CSV.open("r", newline="", encoding="utf-8") as file:
        issue_rows = list(csv.DictReader(file))

    summary_rows: list[dict[str, str]] = []
    for row in issue_rows:
        shape = row["shape"]
        number = row["number"]
        issue = row["issue"]
        v4_path = Path(row["asset_path"])
        name = v4_path.name
        source_path = source_for(shape, name)
        crop_bgr = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
        if crop_bgr is None:
            raise RuntimeError(f"Could not read {source_path}")

        original_alpha = alpha_pixels(v4_path)
        candidates: list[tuple[Path, int]] = []
        for profile in PROFILES:
            asset = make_asset(crop_bgr, profile)
            out_dir = OUT_ROOT / "profiles" / profile["name"] / issue / shape
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / name
            cv2.imwrite(str(out_path), asset)
            candidates.append((out_path, int(np.count_nonzero(asset[:, :, 3]))))

        best = choose_best(issue, original_alpha, candidates)
        best_dir = OUT_ROOT / "best_guess" / issue / shape
        best_dir.mkdir(parents=True, exist_ok=True)
        best_path = best_dir / name
        shutil.copy2(best, best_path)

        summary_rows.append(
            {
                "shape": shape,
                "number": number,
                "issue": issue,
                "source_path": str(source_path.resolve()),
                "original_path": str(v4_path.resolve()),
                "original_alpha": str(original_alpha),
                "best_path": str(best_path.resolve()),
                "best_profile": best.parts[-4],
                "best_alpha": str(alpha_pixels(best_path)),
            }
        )

    summary_csv = OUT_ROOT / "reprocess_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    contact = write_contact_sheet(summary_rows)
    print(f"Reprocessed: {len(summary_rows)} assets")
    print(f"Wrote summary: {summary_csv}")
    print(f"Wrote best guesses under: {OUT_ROOT / 'best_guess'}")
    print(f"Wrote contact sheet: {contact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
