from __future__ import annotations

"""여러 날짜의 top 영상 첫 프레임에서 도형 asset 후보를 crop한다.

0727 이후 데이터는 `erase_the_circle` 같은 단일 task 이름도 있고,
`circle_square`처럼 한 episode 이름에 여러 도형이 들어간 경우도 있다.
이 스크립트는 episode 이름에 포함된 도형마다 첫 프레임을 같은 방식으로 crop해서
배경 제거 전 source crop 이미지를 만든다.
"""

import argparse
import csv
from pathlib import Path

import cv2

from crop_circle_frames import process_file as crop_circle
from crop_triangle_frames import crop_with_margin as triangle_crop_with_margin
from crop_triangle_frames import find_triangle_candidate
from crop_rectangle_frames import process_file as crop_rectangle
from crop_triangle_frames import process_file as crop_triangle


SHAPES = ("circle", "rectangle", "triangle")


def shapes_from_episode_name(name: str) -> list[str]:
    """episode 폴더명에서 crop 대상 도형을 추정한다."""
    lower = name.lower()
    shapes: list[str] = []
    if "circle" in lower:
        shapes.append("circle")
    if "rectangle" in lower or "square" in lower:
        shapes.append("rectangle")
    if "triangle" in lower:
        shapes.append("triangle")
    return shapes


def find_top_videos(date_root: Path) -> list[Path]:
    return sorted(date_root.glob("*/videos/observation.images.top/chunk-000/file-000.mp4"))


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


def crop_search_region(date: str, episode: str, shape: str) -> str | None:
    """0728 복합 도형 episode에서는 도형별 탐색 영역을 고정한다."""
    if date != "0728":
        return None
    lower = episode.lower()
    if lower.startswith("circle_square"):
        if shape == "circle":
            return "bottom"
        if shape == "rectangle":
            return "top"
    return None


def make_region_limited_image(raw_png: Path, output_path: Path, region: str) -> Path:
    """검출용으로만 한쪽 영역을 흰색 처리한 임시 이미지를 만든다."""
    image = cv2.imread(str(raw_png), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Could not read image: {raw_png}")
    height = image.shape[0]
    midpoint = height // 2
    limited = image.copy()
    if region == "top":
        limited[midpoint:, :] = 255
    elif region == "bottom":
        limited[:midpoint, :] = 255
    else:
        raise ValueError(f"Unsupported region: {region}")
    write_png(output_path, limited)
    return output_path


def make_circle_triangle_limited_image(raw_png: Path, output_path: Path) -> Path:
    """circle_triangle episode에서 삼각형 후보를 지운 뒤 원을 찾게 한다."""
    image = cv2.imread(str(raw_png), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Could not read image: {raw_png}")
    candidate = find_triangle_candidate(
        image,
        dark_threshold=105,
        min_size=35,
        max_size=260,
        min_aspect=0.35,
        max_aspect=2.40,
    )
    _crop, (x0, y0, x1, y1) = triangle_crop_with_margin(image, candidate, margin=24)
    limited = image.copy()
    limited[y0:y1, x0:x1] = 255
    write_png(output_path, limited)
    return output_path


def crop_one_shape(shape: str, raw_png: Path, crop_png: Path, debug_png: Path | None) -> dict[str, str | int | float]:
    if shape == "circle":
        return crop_circle(
            raw_png,
            crop_png,
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
            crop_png,
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
            crop_png,
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
    raise ValueError(f"Unsupported shape: {shape}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crop source shape frames from multiple record dates.")
    parser.add_argument("--records-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--dates", nargs="+", default=["0728", "0802", "0804", "0805"])
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parent / "source_frames" / "0728_0805")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--debug", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows: list[dict[str, str | int | float]] = []
    failures: list[dict[str, str]] = []
    per_shape_index = {(date, shape): 0 for date in args.dates for shape in SHAPES}

    for date in args.dates:
        date_root = args.records_root / date
        videos = find_top_videos(date_root)
        print(f"{date}: {len(videos)} top video(s)")
        for video in videos:
            episode = video.parents[3].name
            shapes = shapes_from_episode_name(episode)
            if not shapes:
                failures.append({"date": date, "episode": episode, "shape": "", "error": "shape not inferred from episode name"})
                print(f"  skip {episode}: shape not inferred")
                continue

            try:
                frame, width, height, fps, frame_count = read_first_frame(video)
            except Exception as exc:
                failures.append({"date": date, "episode": episode, "shape": "", "error": str(exc)})
                print(f"  failed read {episode}: {exc}")
                continue

            for shape in shapes:
                per_shape_index[(date, shape)] += 1
                idx = per_shape_index[(date, shape)]
                base_name = f"{idx:03d}_{episode}.png"
                raw_png = args.output_root / date / shape / base_name
                crop_png = args.output_root / date / f"{shape}_cropped" / base_name
                debug_png = args.output_root / date / f"{shape}_crop_debug" / base_name if args.debug else None

                try:
                    if args.overwrite or not raw_png.exists():
                        write_png(raw_png, frame)
                    if args.overwrite or not crop_png.exists():
                        crop_input = raw_png
                        region = crop_search_region(date, episode, shape)
                        if region is not None:
                            crop_input = args.output_root / date / "_crop_work" / shape / base_name
                            make_region_limited_image(raw_png, crop_input, region)
                        elif date == "0728" and episode.lower().startswith("circle_triangle") and shape == "circle":
                            crop_input = args.output_root / date / "_crop_work" / shape / base_name
                            make_circle_triangle_limited_image(raw_png, crop_input)
                        crop_row = crop_one_shape(shape, crop_input, crop_png, debug_png)
                    else:
                        crop_row = {"input": str(raw_png), "output": str(crop_png)}

                    row = {
                        "date": date,
                        "shape": shape,
                        "episode": episode,
                        "source_video": str(video),
                        "raw_png": str(raw_png),
                        "crop_png": str(crop_png),
                        "width": width,
                        "height": height,
                        "fps": fps,
                        "frames": frame_count,
                    }
                    row.update(crop_row)
                    rows.append(row)
                    print(f"  {shape}: wrote {crop_png.name}")
                except Exception as exc:
                    failures.append({"date": date, "episode": episode, "shape": shape, "error": str(exc)})
                    print(f"  failed crop {episode} [{shape}]: {exc}")

    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_root / "crop_manifest.csv"
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    failures_path = args.output_root / "crop_failures.csv"
    with failures_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "episode", "shape", "error"])
        writer.writeheader()
        writer.writerows(failures)

    print(f"Done. Cropped {len(rows)} shape image(s), failed {len(failures)}.")
    print(f"Manifest: {manifest_path}")
    print(f"Failures: {failures_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
