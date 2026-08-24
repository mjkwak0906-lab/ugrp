from __future__ import annotations

"""0727 데이터 전용 배치 증강 스크립트.

현재 최종 0802~0805 결과 생성에는 batch_augment_dates.py를 사용한다.
이 파일은 0727 구조와 과거 실험을 재현하거나 참고할 때 사용한다.
"""

import argparse
import csv
import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any


TARGETS = {
    "circle": {
        "class_dir": "erase_the_circle",
        "task": "erase the circle",
        "distractors": ("triangle", "rectangle"),
    },
    "rectangle": {
        "class_dir": "erase_the_rectangle",
        "task": "erase the rectangle",
        "distractors": ("triangle", "circle"),
    },
    "triangle": {
        "class_dir": "erase_the_triangle",
        "task": "erase the triangle",
        "distractors": ("circle", "rectangle"),
    },
}


def natural_asset_key(path: Path) -> tuple[int, str]:
    try:
        return int(path.stem), path.name
    except ValueError:
        return 10_000, path.name


def find_top_videos(records_root: Path, date_dir: str, class_dir: str) -> list[Path]:
    root = records_root / date_dir / class_dir
    videos = sorted(root.glob("*/videos/observation.images.top/chunk-000/file-000.mp4"))
    if not videos:
        raise FileNotFoundError(f"No top videos found under {root}")
    return videos


def list_shape_assets(assets_root: Path, shape: str) -> list[Path]:
    files = sorted((assets_root / shape).glob("*.png"), key=natural_asset_key)
    if not files:
        raise FileNotFoundError(f"No PNG assets found for {shape}: {assets_root / shape}")
    return files


def make_plan(videos: list[Path], assets_root: Path, target: str, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    distractors = TARGETS[target]["distractors"]
    shuffled_videos = videos[:]
    rng.shuffle(shuffled_videos)

    first_count = len(shuffled_videos) // 2
    groups = {
        distractors[0]: shuffled_videos[:first_count],
        distractors[1]: shuffled_videos[first_count:],
    }

    plan: list[dict[str, Any]] = []
    for shape, group_videos in groups.items():
        assets = list_shape_assets(assets_root, shape)
        if len(assets) < len(group_videos):
            raise RuntimeError(f"Need {len(group_videos)} {shape} assets, but only found {len(assets)}")
        shuffled_assets = assets[:]
        rng.shuffle(shuffled_assets)
        for video, asset in zip(group_videos, shuffled_assets):
            episode_dir = video.parents[3]
            plan.append(
                {
                    "target": target,
                    "episode": episode_dir.name,
                    "shape": shape,
                    "asset": str(asset),
                    "input_video": str(video),
                    "seed": rng.randint(1, 2_147_483_647),
                }
            )
    return sorted(plan, key=lambda row: row["episode"])


def save_plan(plan: list[dict[str, Any]], output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / "augmentation_plan.json"
    csv_path = output_root / "augmentation_plan.csv"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["target", "episode", "shape", "asset", "input_video", "seed"])
        writer.writeheader()
        writer.writerows(plan)
    print(f"Plan JSON: {json_path}")
    print(f"Plan CSV: {csv_path}")


def output_video_for_row(row: dict[str, Any], output_root: Path) -> Path:
    return output_root / row["shape"] / row["episode"] / "augmented.mp4"


def metadata_for_row(row: dict[str, Any], output_root: Path) -> Path:
    return output_video_for_row(row, output_root).parent / "placement_metadata.json"


def output_is_complete(row: dict[str, Any], output_root: Path) -> bool:
    output_video = output_video_for_row(row, output_root)
    metadata = metadata_for_row(row, output_root)
    return output_video.exists() and output_video.stat().st_size > 0 and metadata.exists() and metadata.stat().st_size > 0


def command_for_row(args: argparse.Namespace, row: dict[str, Any], output_root: Path, overrides: dict[str, Any] | None = None) -> list[str]:
    values = {
        "sample_stride": args.sample_stride,
        "pixel_threshold": args.pixel_threshold,
        "ever_changed_threshold": args.ever_changed_threshold,
        "changed_ratio": args.changed_ratio,
        "motion_dilate": args.motion_dilate,
        "drawing_threshold": args.drawing_threshold,
        "drawing_dilate": args.drawing_dilate,
        "placement_margin": args.placement_margin,
        "board_border_margin": args.board_border_margin,
        "scale_range": args.scale_range,
        "rotation_range": args.rotation_range,
    }
    if overrides:
        values.update(overrides)

    output_video = output_video_for_row(row, output_root)
    return [
        sys.executable,
        str(Path(__file__).resolve().parent / "augment_whiteboard.py"),
        "--input",
        row["input_video"],
        "--assets",
        str(args.assets_root),
        "--asset",
        row["asset"],
        "--shape",
        row["shape"],
        "--output",
        str(output_video),
        "--task",
        TARGETS[row["target"]]["task"],
        "--roi-json",
        str(args.roi_json),
        "--sample-stride",
        str(values["sample_stride"]),
        "--pixel-threshold",
        str(values["pixel_threshold"]),
        "--ever-changed-threshold",
        str(values["ever_changed_threshold"]),
        "--changed-ratio",
        str(values["changed_ratio"]),
        "--motion-dilate",
        str(values["motion_dilate"]),
        "--drawing-threshold",
        str(values["drawing_threshold"]),
        "--drawing-dilate",
        str(values["drawing_dilate"]),
        "--placement-margin",
        str(values["placement_margin"]),
        "--board-border-margin",
        str(values["board_border_margin"]),
        f"--scale-range={values['scale_range']}",
        f"--rotation-range={values['rotation_range']}",
        "--seed",
        str(row["seed"]),
        *(["--debug"] if args.debug else []),
        *(["--keep-audio"] if args.keep_audio else []),
        *(["--stabilize"] if args.stabilize else []),
    ]


def retry_profiles(args: argparse.Namespace) -> list[dict[str, Any]]:
    return [
        {},
        {
            "changed_ratio": max(args.changed_ratio, 0.03),
            "motion_dilate": min(args.motion_dilate, 6),
            "drawing_threshold": min(args.drawing_threshold, 140),
            "drawing_dilate": min(args.drawing_dilate, 4),
            "placement_margin": min(args.placement_margin, 8),
            "board_border_margin": min(args.board_border_margin, 16),
            "scale_range": "0.80,0.95",
            "rotation_range": "-8,8",
        },
        {
            "sample_stride": max(args.sample_stride, 10),
            "pixel_threshold": max(args.pixel_threshold, 25),
            "ever_changed_threshold": max(args.ever_changed_threshold, 50),
            "changed_ratio": max(args.changed_ratio, 0.04),
            "motion_dilate": min(args.motion_dilate, 4),
            "drawing_threshold": min(args.drawing_threshold, 135),
            "drawing_dilate": min(args.drawing_dilate, 3),
            "placement_margin": min(args.placement_margin, 6),
            "board_border_margin": min(args.board_border_margin, 12),
            "scale_range": "0.70,0.90",
            "rotation_range": "-6,6",
        },
        {
            "sample_stride": max(args.sample_stride, 12),
            "pixel_threshold": max(args.pixel_threshold, 28),
            "ever_changed_threshold": max(args.ever_changed_threshold, 55),
            "changed_ratio": max(args.changed_ratio, 0.05),
            "motion_dilate": min(args.motion_dilate, 2),
            "drawing_threshold": min(args.drawing_threshold, 130),
            "drawing_dilate": min(args.drawing_dilate, 2),
            "placement_margin": min(args.placement_margin, 4),
            "board_border_margin": min(args.board_border_margin, 8),
            "scale_range": "0.65,0.85",
            "rotation_range": "-5,5",
        },
    ]


def run_plan(args: argparse.Namespace, plan: list[dict[str, Any]], output_root: Path) -> None:
    if not args.roi_json.exists():
        print(f"ROI JSON does not exist yet: {args.roi_json}")
        print("The first augment command will open the ROI picker. Click 4 whiteboard corners and press Enter.")

    failures: list[tuple[str, str]] = []
    for idx, row in enumerate(plan, start=1):
        output_video = output_video_for_row(row, output_root)
        if output_is_complete(row, output_root) and not args.overwrite:
            print(f"[{idx}/{len(plan)}] skip complete {row['episode']} -> {output_video}")
            continue

        print(f"[{idx}/{len(plan)}] {row['episode']} -> {row['shape']} using {Path(row['asset']).name}")
        last_error = ""
        for attempt_idx, overrides in enumerate(retry_profiles(args), start=1):
            if overrides:
                print(f"  retry profile {attempt_idx}: {overrides}")
            result = subprocess.run(command_for_row(args, row, output_root, overrides))
            if result.returncode == 0:
                break
            last_error = f"return code {result.returncode}"
        else:
            failures.append((row["episode"], last_error))
            print(f"  failed all retry profiles: {row['episode']} ({last_error})")

    if failures:
        print("Failures:")
        for episode, reason in failures:
            print(f"  {episode}: {reason}")
        raise RuntimeError(f"{len(failures)} augmentation(s) failed")


def default_output_root(project_root: Path, date_dir: str, target: str) -> Path:
    return project_root / "outputs" / f"{date_dir}_erase_{target}_shape_aug"


def build_parser() -> argparse.ArgumentParser:
    project_root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Batch augment 0727 erase-shape top videos with non-target distractor shapes.")
    parser.add_argument("--target", choices=sorted(TARGETS), required=True)
    parser.add_argument("--date-dir", default="0727")
    parser.add_argument("--records-root", type=Path, default=project_root.parent)
    parser.add_argument("--assets-root", type=Path, default=project_root / "assets")
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--roi-json", type=Path, default=project_root / "board_roi.json")
    parser.add_argument("--seed", type=int, default=20260802)
    parser.add_argument("--run", action="store_true", help="Actually run augmentation. Without this, only writes the plan.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate outputs even when augmented.mp4 already exists")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--keep-audio", action="store_true")
    parser.add_argument("--stabilize", action="store_true")
    parser.add_argument("--sample-stride", type=int, default=8)
    parser.add_argument("--pixel-threshold", type=int, default=22)
    parser.add_argument("--ever-changed-threshold", type=int, default=45)
    parser.add_argument("--changed-ratio", type=float, default=0.02)
    parser.add_argument("--motion-dilate", type=int, default=8)
    parser.add_argument("--drawing-threshold", type=int, default=145)
    parser.add_argument("--drawing-dilate", type=int, default=6)
    parser.add_argument("--placement-margin", type=int, default=12)
    parser.add_argument("--board-border-margin", type=int, default=20)
    parser.add_argument("--scale-range", default="0.90,1.10")
    parser.add_argument("--rotation-range", default="-10,10")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project_root = Path(__file__).resolve().parent
    output_root = args.output_root or default_output_root(project_root, args.date_dir, args.target)
    class_dir = TARGETS[args.target]["class_dir"]
    videos = find_top_videos(args.records_root, args.date_dir, class_dir)
    plan = make_plan(videos, args.assets_root, args.target, args.seed)
    save_plan(plan, output_root)

    shape_counts: dict[str, int] = {}
    for row in plan:
        shape_counts[row["shape"]] = shape_counts.get(row["shape"], 0) + 1
    print(f"Target: {args.target}")
    print(f"Videos: {len(videos)}")
    print(f"Split: {shape_counts}")
    print("Asset selection is without replacement within each shape.")

    if args.run:
        run_plan(args, plan, output_root)
    else:
        print("Dry run only. Add --run to create augmented videos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
