from __future__ import annotations

"""밝은 배경 crop 이미지에서 도형 선만 남겨 투명 PNG asset을 만든다.

Adobe 배경 제거가 실패하는 샘플을 피하기 위한 로컬 OpenCV 기반 처리이다.
밝은 화이트보드/회색 배경은 투명화하고, 어두운 펜 선은 alpha로 유지한다.
"""

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


def auto_crop_to_alpha(rgba: np.ndarray, pad: int) -> np.ndarray:
    alpha = rgba[:, :, 3]
    ys, xs = np.where(alpha > 0)
    if len(xs) == 0 or len(ys) == 0:
        return rgba

    h, w = alpha.shape
    x1 = max(0, int(xs.min()) - pad)
    y1 = max(0, int(ys.min()) - pad)
    x2 = min(w, int(xs.max()) + pad + 1)
    y2 = min(h, int(ys.max()) + pad + 1)
    return rgba[y1:y2, x1:x2]


def keep_largest_components(mask: np.ndarray, min_area: int) -> np.ndarray:
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    kept = np.zeros_like(mask)
    for label in range(1, num):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= min_area:
            kept[labels == label] = 255
    return kept


def make_line_alpha(
    src: Path,
    dst: Path,
    dark_threshold: int,
    edge_threshold1: int,
    edge_threshold2: int,
    use_edges: bool,
    min_component_area: int,
    dilate: int,
    blur_alpha: float,
    crop_pad: int,
    line_rgb: tuple[int, int, int],
    preserve_rgb: bool,
    soft_alpha: bool,
    soft_low: int,
) -> dict[str, int | str]:
    bgr = cv2.imread(str(src), cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(src)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # 배경보다 어두운 펜 선 후보를 alpha로 사용한다.
    # Canny edge는 선 양쪽 경계를 잡아 이중선/흰 테두리처럼 보일 수 있어 옵션으로만 사용한다.
    dark = np.where(gray <= dark_threshold, 255, 0).astype(np.uint8)
    if use_edges:
        edges = cv2.Canny(gray, edge_threshold1, edge_threshold2)
        mask = cv2.bitwise_or(dark, edges)
    else:
        mask = dark

    kernel3 = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel3, iterations=1)
    mask = keep_largest_components(mask, min_component_area)

    if dilate > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate * 2 + 1, dilate * 2 + 1))
        mask = cv2.dilate(mask, kernel, iterations=1)

    if soft_alpha:
        # threshold 안쪽의 어두운 정도를 alpha 강도로 사용해 원본 선의 얇고 진한 느낌을 살린다.
        alpha_f = (dark_threshold - gray.astype(np.float32)) / max(1, dark_threshold - soft_low)
        alpha = np.clip(alpha_f * 255.0, 0, 255).astype(np.uint8)
        alpha[mask == 0] = 0
        alpha = np.minimum(alpha, mask)
    elif blur_alpha > 0:
        k = int(round(blur_alpha * 4)) | 1
        k = max(3, k)
        alpha = cv2.GaussianBlur(mask, (k, k), blur_alpha)
    else:
        alpha = mask

    if preserve_rgb:
        # 선으로 판정된 픽셀 위치는 원본 crop의 RGB를 그대로 사용한다.
        # 즉, 위치/색상은 원본 기반이고 alpha만 새로 만든다.
        bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
        bgra[alpha == 0, :3] = 0
    else:
        # 필요하면 선 색을 어두운 마커 색으로 고정할 수 있다.
        line_r, line_g, line_b = line_rgb
        bgra = np.zeros((bgr.shape[0], bgr.shape[1], 4), dtype=np.uint8)
        bgra[:, :, 0] = line_b
        bgra[:, :, 1] = line_g
        bgra[:, :, 2] = line_r
    bgra[:, :, 3] = alpha

    if crop_pad >= 0:
        bgra = auto_crop_to_alpha(bgra, crop_pad)

    dst.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(dst), bgra)

    return {
        "src": src.name,
        "dst": str(dst),
        "input_w": int(bgr.shape[1]),
        "input_h": int(bgr.shape[0]),
        "output_w": int(bgra.shape[1]),
        "output_h": int(bgra.shape[0]),
        "alpha_pixels": int(np.count_nonzero(bgra[:, :, 3])),
    }


def iter_inputs(input_dir: Path, limit: int | None) -> list[Path]:
    files = sorted(input_dir.glob("*.png"))
    if limit is not None:
        files = files[:limit]
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dark-threshold", type=int, default=170)
    parser.add_argument("--edge-threshold1", type=int, default=35)
    parser.add_argument("--edge-threshold2", type=int, default=100)
    parser.add_argument("--use-edges", action="store_true")
    parser.add_argument("--min-component-area", type=int, default=20)
    parser.add_argument("--dilate", type=int, default=1)
    parser.add_argument("--blur-alpha", type=float, default=0.8)
    parser.add_argument("--crop-pad", type=int, default=12)
    parser.add_argument("--line-rgb", default="35,40,40")
    parser.add_argument("--preserve-rgb", action="store_true")
    parser.add_argument("--soft-alpha", action="store_true")
    parser.add_argument("--soft-low", type=int, default=60)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    line_rgb = tuple(int(x) for x in args.line_rgb.split(","))
    if len(line_rgb) != 3:
        raise ValueError("--line-rgb must be R,G,B")

    rows = []
    for src in iter_inputs(args.input_dir, args.limit):
        dst = args.output_dir / src.name
        row = make_line_alpha(
            src=src,
            dst=dst,
            dark_threshold=args.dark_threshold,
            edge_threshold1=args.edge_threshold1,
            edge_threshold2=args.edge_threshold2,
            use_edges=args.use_edges,
            min_component_area=args.min_component_area,
            dilate=args.dilate,
            blur_alpha=args.blur_alpha,
            crop_pad=args.crop_pad,
            line_rgb=line_rgb,
            preserve_rgb=args.preserve_rgb,
            soft_alpha=args.soft_alpha,
            soft_low=args.soft_low,
        )
        rows.append(row)
        print(f"wrote {dst}")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["src"])
            writer.writeheader()
            writer.writerows(rows)

    print(f"done: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
