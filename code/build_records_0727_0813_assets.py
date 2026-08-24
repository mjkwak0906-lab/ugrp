from __future__ import annotations

"""Build local OpenCV transparent assets from single-target records_0727_0813 episodes.

입력은 Downloads/records_0727_0813의 원본 episode이고, 출력은 별도 작업 폴더인
records_0727_0813_assets_work 아래에만 만든다. 0728처럼 한 episode에 도형이
2개 있는 데이터와 erase_the_shape 계열은 제외한다.
"""

import argparse
import csv
from collections import Counter
from pathlib import Path

import cv2

from crop_circle_frames import process_file as crop_circle
from crop_rectangle_frames import process_file as crop_rectangle
from crop_triangle_frames import process_file as crop_triangle
from build_v4_assets_from_manifests import make_v4_asset


SHAPES = ("circle", "rectangle", "triangle")


def infer_target_shape(video_path: Path, records_root: Path) -> str | None:
    rel = video_path.relative_to(records_root).parts
    text = " ".join(rel).lower()
    if "erase_the_shape" in text:
        return None
    if "circle_square" in text or "circle_triangle" in text:
        return None

    hits = [shape for shape in SHAPES if f"erase_the_{shape}" in text]
    if len(hits) == 1:
        return hits[0]
    return None


def episode_name(video_path: Path) -> str:
    return video_path.parents[3].name


def read_first_frame(video_path: Path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    ok, frame = cap.read()
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if not ok:
        raise RuntimeError(f"Could not read first frame: {video_path}")
    return frame, width, height, fps, frames


def write_png(path: Path, image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image):
        raise RuntimeError(f"Could not write PNG: {path}")


def crop_one(shape: str, raw_png: Path, cropped_png: Path, debug_png: Path | None) -> dict[str, str | int | float]:
    if shape == "circle":
        return crop_circle(
            raw_png,
            cropped_png,
            dark_threshold=115,
            min_size=35,
            max_size=260,
            min_aspect=0.65,
            max_aspect=1.70,
            margin=18,
            transparent=False,
            alpha_dilate=1,
            backup_dir=None,
            debug_path=debug_png,
        )
    if shape == "rectangle":
        return crop_rectangle(
            raw_png,
            cropped_png,
            dark_threshold=105,
            min_size=35,
            max_size=260,
            min_aspect=0.45,
            max_aspect=2.20,
            margin=18,
            transparent=False,
            alpha_dilate=1,
            debug_path=debug_png,
        )
    if shape == "triangle":
        return crop_triangle(
            raw_png,
            cropped_png,
            dark_threshold=105,
            min_size=35,
            max_size=260,
            min_aspect=0.35,
            max_aspect=2.40,
            margin=18,
            transparent=False,
            alpha_dilate=1,
            debug_path=debug_png,
        )
    raise ValueError(shape)


def write_asset_index(rows: list[dict[str, str | int | float]], output_path: Path) -> None:
    index_rows = []
    for row in rows:
        index_rows.append(
            {
                "asset_path": str(Path(row["asset_png"]).resolve()),
                "shape": row["shape"],
                "source_center_x": float(row["x"]) + float(row["w"]) / 2.0,
                "source_center_y": float(row["y"]) + float(row["h"]) / 2.0,
                "source_width": int(row["w"]),
                "source_height": int(row["h"]),
                "source_x": int(row["crop_x"]),
                "source_y": int(row["crop_y"]),
                "manifest": str(output_path.parent / "asset_manifest.csv"),
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(index_rows[0].keys()))
        writer.writeheader()
        writer.writerows(index_rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", type=Path, default=Path(r"C:\Users\user\Downloads\records_0727_0813"))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parent / "records_0727_0813_assets_work",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--debug", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    videos = sorted(args.records_root.rglob("videos/observation.images.top/chunk-000/file-000.mp4"))
    rows: list[dict[str, str | int | float]] = []
    failures: list[dict[str, str]] = []
    counters: Counter[str] = Counter()

    for video in videos:
        date = video.relative_to(args.records_root).parts[0]
        shape = infer_target_shape(video, args.records_root)
        if shape is None:
            continue

        counters[shape] += 1
        idx = counters[shape]
        episode = episode_name(video)
        stem = f"{idx:03d}_{episode}"
        raw_png = args.output_root / "source_frames" / shape / f"{stem}.png"
        cropped_png = args.output_root / "cropped" / shape / f"{stem}.png"
        asset_png = args.output_root / "assets" / shape / f"{idx:03d}_{episode}.png"
        debug_png = args.output_root / "debug" / "crop_boxes" / shape / f"{stem}.png" if args.debug else None

        try:
            if args.overwrite or not raw_png.exists():
                frame, width, height, fps, frame_count = read_first_frame(video)
                write_png(raw_png, frame)
            else:
                image = cv2.imread(str(raw_png), cv2.IMREAD_COLOR)
                if image is None:
                    raise RuntimeError(f"Could not read cached frame: {raw_png}")
                height, width = image.shape[:2]
                fps = 0.0
                frame_count = 0

            if args.overwrite or not cropped_png.exists():
                crop_row = crop_one(shape, raw_png, cropped_png, debug_png)
            else:
                crop_row = {"input": str(raw_png), "output": str(cropped_png), "x": 0, "y": 0, "w": 0, "h": 0, "crop_x": 0, "crop_y": 0, "crop_w": 0, "crop_h": 0}

            if args.overwrite or not asset_png.exists():
                crop_bgr = cv2.imread(str(cropped_png), cv2.IMREAD_COLOR)
                if crop_bgr is None:
                    raise RuntimeError(f"Could not read crop for v4 asset: {cropped_png}")
                asset = make_v4_asset(crop_bgr, dark_threshold=140, min_component_area=15)
                asset_png.parent.mkdir(parents=True, exist_ok=True)
                if not cv2.imwrite(str(asset_png), asset):
                    raise RuntimeError(f"Could not write asset: {asset_png}")

            row = {
                "date": date,
                "shape": shape,
                "shape_index": idx,
                "episode": episode,
                "source_video": str(video),
                "raw_png": str(raw_png),
                "crop_png": str(cropped_png),
                "asset_png": str(asset_png),
                "width": width,
                "height": height,
                "fps": fps,
                "frames": frame_count,
            }
            row.update(crop_row)
            rows.append(row)
            print(f"[{len(rows):03d}] {shape} {episode} -> {asset_png.name}")
        except Exception as exc:
            failures.append({"date": date, "shape": shape, "episode": episode, "source_video": str(video), "error": str(exc)})
            print(f"failed {shape} {episode}: {exc}")

    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_root / "asset_manifest.csv"
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    failures_path = args.output_root / "asset_failures.csv"
    with failures_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "shape", "episode", "source_video", "error"])
        writer.writeheader()
        writer.writerows(failures)

    if rows:
        write_asset_index(rows, args.output_root / "asset_index.csv")

    print(f"Done. assets={len(rows)}, failures={len(failures)}")
    print(f"By shape: {dict(counters)}")
    print(f"Manifest: {manifest_path}")
    print(f"Failures: {failures_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
