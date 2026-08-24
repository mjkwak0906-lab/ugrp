from __future__ import annotations

"""Reprocess manually separated anomaly assets from records_0727_0813_assets_work.

assets/anomaly 안에 사용자가 분리한 더러운 asset을 대상으로 여러 threshold/contrast
프로파일을 다시 적용한다. 원본 RGB 입력은 assets가 아니라 cropped/<shape>/<name>에서
가져오므로, alpha=0 영역의 RGB 손실에 영향을 받지 않는다.
"""

import csv
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parent
WORK_ROOT = PROJECT_ROOT / "records_0727_0813_assets_work"
ANOMALY_ROOT = WORK_ROOT / "assets" / "anomaly"
CROPPED_ROOT = WORK_ROOT / "cropped"
OUT_ROOT = WORK_ROOT / "reprocessed_anomaly"


PROFILES = [
    {"name": "thr90_min8", "kind": "threshold", "threshold": 90, "min_area": 8, "close": False},
    {"name": "thr100_min8", "kind": "threshold", "threshold": 100, "min_area": 8, "close": False},
    {"name": "thr110_min8", "kind": "threshold", "threshold": 110, "min_area": 8, "close": False},
    {"name": "thr120_min10", "kind": "threshold", "threshold": 120, "min_area": 10, "close": False},
    {"name": "thr130_min15_close", "kind": "threshold", "threshold": 130, "min_area": 15, "close": True},
    {"name": "thr140_min15_close", "kind": "threshold", "threshold": 140, "min_area": 15, "close": True},
    {"name": "local_contrast_18", "kind": "local_contrast", "delta": 18, "min_area": 8},
    {"name": "local_contrast_24", "kind": "local_contrast", "delta": 24, "min_area": 8},
    {"name": "edge_canny_d1", "kind": "edge", "low": 25, "high": 80, "dilate": 1, "min_area": 5},
]


def infer_shape(name: str) -> str:
    lower = name.lower()
    if "circle" in lower:
        return "circle"
    if "rectangle" in lower:
        return "rectangle"
    if "triangle" in lower:
        return "triangle"
    raise ValueError(f"Could not infer shape from {name}")


def keep_components(mask: np.ndarray, min_area: int, reject_filled_blocks: bool = False) -> np.ndarray:
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    kept = np.zeros_like(mask)
    for label in range(1, num):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        if reject_filled_blocks:
            width = int(stats[label, cv2.CC_STAT_WIDTH])
            height = int(stats[label, cv2.CC_STAT_HEIGHT])
            fill_ratio = area / max(1, width * height)
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
        if bool(profile.get("close", False)):
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
    elif kind == "local_contrast":
        background = cv2.medianBlur(gray, 17)
        mask = np.where((background.astype(np.int16) - gray.astype(np.int16)) >= int(profile["delta"]), 255, 0).astype(np.uint8)
        reject_filled_blocks = True
    elif kind == "edge":
        mask = cv2.Canny(gray, int(profile["low"]), int(profile["high"]))
        dilate = int(profile["dilate"])
        if dilate > 0:
            mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=dilate)
        reject_filled_blocks = True
    else:
        raise ValueError(f"Unknown profile kind: {kind}")

    alpha = keep_components(mask, int(profile["min_area"]), reject_filled_blocks)
    bgra = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha
    bgra[alpha == 0, :3] = 0
    return bgra


def alpha_pixels(path: Path) -> int:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None or image.ndim != 3 or image.shape[2] < 4:
        return 0
    return int(np.count_nonzero(image[:, :, 3]))


def choose_best(original_alpha: int, candidates: list[tuple[Path, int]]) -> Path:
    # anomaly는 대체로 배경 잔여/지저분함이므로 alpha를 줄이되 선이 끊기지 않는 후보를 우선한다.
    lo = original_alpha * 0.35
    hi = original_alpha * 0.90
    plausible = [(path, alpha) for path, alpha in candidates if lo <= alpha <= hi]
    if plausible:
        return max(plausible, key=lambda item: item[1])[0]
    return min(candidates, key=lambda item: abs(item[1] - original_alpha * 0.65))[0]


def write_contact_sheet(rows: list[dict[str, str]], key: str, filename: str) -> Path:
    cell_w, cell_h = 190, 190
    cols = 9
    rows_count = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGB", (cell_w * cols, cell_h * rows_count), (34, 34, 34))
    draw = ImageDraw.Draw(sheet)
    for idx, row in enumerate(rows):
        path = Path(row[key])
        col = idx % cols
        r = idx // cols
        x0 = col * cell_w
        y0 = r * cell_h
        tile = Image.new("RGBA", (cell_w, cell_h), (34, 34, 34, 255))
        image = Image.open(path).convert("RGBA")
        image.thumbnail((cell_w - 24, cell_h - 48), Image.Resampling.LANCZOS)
        tile.alpha_composite(image, ((cell_w - image.width) // 2, 34 + (cell_h - 52 - image.height) // 2))
        sheet.paste(tile.convert("RGB"), (x0, y0))
        draw.text((x0 + 6, y0 + 7), f"{row['shape']} {row['number']}", fill=(240, 240, 240))
        draw.text((x0 + 6, y0 + 22), row.get("best_profile", "original"), fill=(190, 190, 190))
    out = OUT_ROOT / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    anomaly_files = sorted(ANOMALY_ROOT.glob("*.png"))
    if not anomaly_files:
        raise FileNotFoundError(f"No anomaly PNGs found: {ANOMALY_ROOT}")

    summary_rows: list[dict[str, str]] = []
    for anomaly_path in anomaly_files:
        shape = infer_shape(anomaly_path.name)
        number = anomaly_path.name.split("_", 1)[0]
        source_crop = CROPPED_ROOT / shape / anomaly_path.name
        crop_bgr = cv2.imread(str(source_crop), cv2.IMREAD_COLOR)
        if crop_bgr is None:
            raise RuntimeError(f"Could not read source crop: {source_crop}")

        original_alpha = alpha_pixels(anomaly_path)
        candidates: list[tuple[Path, int]] = []
        for profile in PROFILES:
            asset = make_asset(crop_bgr, profile)
            out_dir = OUT_ROOT / "profiles" / str(profile["name"]) / shape
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / anomaly_path.name
            cv2.imwrite(str(out_path), asset)
            candidates.append((out_path, int(np.count_nonzero(asset[:, :, 3]))))

        best = choose_best(original_alpha, candidates)
        best_dir = OUT_ROOT / "best_guess" / shape
        best_dir.mkdir(parents=True, exist_ok=True)
        best_path = best_dir / anomaly_path.name
        shutil.copy2(best, best_path)

        summary_rows.append(
            {
                "shape": shape,
                "number": number,
                "name": anomaly_path.name,
                "original_path": str(anomaly_path.resolve()),
                "source_crop": str(source_crop.resolve()),
                "original_alpha": str(original_alpha),
                "best_path": str(best_path.resolve()),
                "best_profile": best.parts[-3],
                "best_alpha": str(alpha_pixels(best_path)),
            }
        )
        print(f"{shape} {anomaly_path.name} -> {best.parts[-3]}")

    summary_csv = OUT_ROOT / "reprocess_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    best_contact = write_contact_sheet(summary_rows, "best_path", "best_guess_contact_sheet.png")
    original_contact = write_contact_sheet(summary_rows, "original_path", "original_anomaly_contact_sheet.png")
    print(f"Reprocessed: {len(summary_rows)}")
    print(f"Summary: {summary_csv}")
    print(f"Best contact sheet: {best_contact}")
    print(f"Original contact sheet: {original_contact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
