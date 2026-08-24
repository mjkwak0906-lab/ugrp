from __future__ import annotations

"""단일 이미지에서 투명 PNG asset을 시험적으로 추출하기 위한 실험용 스크립트.

최종 asset은 웹 기반 배경 제거 결과를 assets/<shape>/에 넣어 사용했다.
현재 0802~0805 최종 증강 경로에서는 직접 호출하지 않는다.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np


def make_alpha_crop(input_path: Path, output_path: Path, threshold: int, margin: int, dilate: int, min_area: int) -> tuple[int, int, int, int]:
    image = cv2.imread(str(input_path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Could not read image: {input_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = np.where(gray >= threshold, 255, 0).astype(np.uint8)

    count, labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, 8)
    cleaned = np.zeros_like(mask)
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] >= min_area:
            cleaned[labels == label] = 255

    if dilate > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate * 2 + 1, dilate * 2 + 1))
        cleaned = cv2.dilate(cleaned, kernel)

    ys, xs = np.where(cleaned > 0)
    if len(xs) == 0:
        raise RuntimeError(f"No foreground pixels found in {input_path}; lower --threshold")

    x0 = max(0, int(xs.min()) - margin)
    y0 = max(0, int(ys.min()) - margin)
    x1 = min(image.shape[1], int(xs.max()) + margin + 1)
    y1 = min(image.shape[0], int(ys.max()) + margin + 1)

    crop_bgr = image[y0:y1, x0:x1]
    crop_alpha = cleaned[y0:y1, x0:x1]
    crop_bgra = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2BGRA)
    crop_bgra[:, :, 3] = crop_alpha

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), crop_bgra):
        raise RuntimeError(f"Could not write PNG: {output_path}")
    return x0, y0, x1, y1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crop a dark-background source frame into a transparent shape PNG.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--threshold", type=int, default=35, help="Foreground gray threshold")
    parser.add_argument("--margin", type=int, default=12, help="Pixels to keep around the detected shape")
    parser.add_argument("--dilate", type=int, default=1, help="Slightly thicken alpha mask")
    parser.add_argument("--min-area", type=int, default=8, help="Drop tiny specks below this component size")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    x0, y0, x1, y1 = make_alpha_crop(args.input, args.output, args.threshold, args.margin, args.dilate, args.min_area)
    print(f"Wrote {args.output}")
    print(f"Crop box: x={x0}, y={y0}, w={x1 - x0}, h={y1 - y0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
