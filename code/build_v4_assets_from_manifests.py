from __future__ import annotations

"""records_105 manifest를 이용해 315개 투명 PNG asset을 v4 방식으로 다시 만든다.

기존 crop 위치와 파일명/manifest 구조는 유지하고, 배경 제거만 우리 v4 방식으로 수행한다.
v4 원칙:
- 원본 source frame에서 manifest의 crop_x/y/w/h로 그대로 crop한다.
- 선 위치는 gray threshold로만 결정한다.
- 선 RGB는 원본 crop 픽셀을 그대로 유지한다.
- edge/blur/dilate를 기본 적용하지 않는다.
"""

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


def make_v4_asset(crop_bgr: np.ndarray, dark_threshold: int, min_component_area: int) -> np.ndarray:
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    mask = np.where(gray <= dark_threshold, 255, 0).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)

    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    kept = np.zeros_like(mask)
    for label in range(1, num):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= min_component_area:
            kept[labels == label] = 255

    bgra = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = kept
    bgra[kept == 0, :3] = 0
    return bgra


def process_manifest(
    manifest_path: Path,
    project_root: Path,
    source_root: Path,
    output_root: Path,
    dark_threshold: int,
    min_component_area: int,
) -> list[dict[str, str | int | float]]:
    rows: list[dict[str, str | int | float]] = []
    with manifest_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            source_rel = Path(row["input"])
            output_rel = Path(row["output"])
            source_path = source_rel if source_rel.is_absolute() else project_root / source_rel
            old_asset_path = output_rel if output_rel.is_absolute() else project_root / output_rel
            output_path = output_rel if output_rel.is_absolute() else output_root / output_rel.relative_to(source_root)
            if not output_path.is_absolute():
                output_path = project_root / output_path

            image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
            if image is not None:
                crop_x = int(float(row["crop_x"]))
                crop_y = int(float(row["crop_y"]))
                crop_w = int(float(row["crop_w"]))
                crop_h = int(float(row["crop_h"]))
                crop = image[crop_y : crop_y + crop_h, crop_x : crop_x + crop_w]
                if crop.size == 0:
                    raise RuntimeError(f"Empty crop for {source_path}: {crop_x},{crop_y},{crop_w},{crop_h}")
            else:
                # 공유 패키지에는 source_frames/records_105가 없을 수 있다.
                # 기존 transparent PNG는 alpha=0 영역에도 원본 RGB가 남아 있으므로,
                # 그 파일 전체를 입력 crop으로 사용해 alpha만 v4 방식으로 다시 만든다.
                crop = cv2.imread(str(old_asset_path), cv2.IMREAD_COLOR)
                if crop is None:
                    raise RuntimeError(f"Could not read source frame or existing asset: {source_path} / {old_asset_path}")

            asset = make_v4_asset(crop, dark_threshold, min_component_area)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), asset)

            alpha = asset[:, :, 3]
            out_row = dict(row)
            out_row["output"] = str(output_path.resolve().relative_to(project_root.resolve()))
            out_row["alpha_pixels"] = int(np.count_nonzero(alpha))
            out_row["visible_ratio"] = round(float(np.count_nonzero(alpha) / alpha.size), 6)
            rows.append(out_row)
            print(f"wrote {output_path}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path("candidate_assets/records_105"))
    parser.add_argument("--output-root", type=Path, default=Path("candidate_assets_v4_preserve/records_105"))
    parser.add_argument("--dark-threshold", type=int, default=140)
    parser.add_argument("--min-component-area", type=int, default=15)
    args = parser.parse_args()

    project_root = Path.cwd()
    all_rows: list[dict[str, str | int | float]] = []
    for manifest in sorted(args.source_root.rglob("*manifest.csv")):
        rel_manifest = manifest.relative_to(args.source_root)
        out_manifest = args.output_root / rel_manifest
        rows = process_manifest(
            manifest,
            project_root,
            args.source_root,
            args.output_root,
            args.dark_threshold,
            args.min_component_area,
        )
        out_manifest.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(rows[0].keys()) if rows else []
        with out_manifest.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        all_rows.extend(rows)

    print(f"done: {len(all_rows)} assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
