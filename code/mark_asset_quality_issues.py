from __future__ import annotations

"""검수 중 발견한 불량 asset을 따로 정리하고, 학습/증강용 filtered index를 만든다.

원본 PNG는 삭제하거나 이동하지 않는다.
대신:
1. asset_quality_review 아래에 문제 asset 복사본을 모은다.
2. asset_quality_issues.csv에 문제 유형을 기록한다.
3. asset_index_filtered.csv를 만들어 batch 증강에서 불량 asset을 제외할 수 있게 한다.
"""

import csv
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
ASSET_ROOT = PROJECT_ROOT / "candidate_assets_v4_preserve" / "records_105"
REVIEW_ROOT = PROJECT_ROOT / "candidate_assets_v4_preserve" / "asset_quality_review"
ISSUE_CSV = REVIEW_ROOT / "asset_quality_issues.csv"
INDEX_CSV = ASSET_ROOT / "asset_index.csv"
FILTERED_INDEX_CSV = ASSET_ROOT / "asset_index_filtered.csv"


ISSUES: dict[str, dict[str, list[int]]] = {
    "circle": {
        "background_remaining": [6, 7, 8, 47, 63, 85, 86, 87, 88, 89, 100, 101],
        "cut_off": [13],
        "dirty": [64],
    },
    "rectangle": {
        "background_remaining": [7, 9, 13, 16, 52, 77, 78, 90],
        "dirty": [8, 18, 19, 20, 56, 74, 75, 76, 83, 105],
    },
    "triangle": {
        "background_remaining": [11, 91, 92, 93, 94, 95],
        "dirty": [8, 9, 48, 53, 58, 69, 90],
    },
}


def asset_number(path: Path) -> int | None:
    token = path.stem.split("_", 1)[0]
    try:
        return int(token)
    except ValueError:
        return None


def find_asset(shape: str, number: int) -> Path:
    matches = [p for p in (ASSET_ROOT / shape).glob("*.png") if asset_number(p) == number]
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected exactly one asset for {shape} #{number}, found {len(matches)}")
    return matches[0]


def write_issue_review() -> set[Path]:
    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    bad_paths: set[Path] = set()
    rows: list[dict[str, str]] = []

    for shape, by_issue in ISSUES.items():
        for issue, numbers in by_issue.items():
            out_dir = REVIEW_ROOT / issue / shape
            out_dir.mkdir(parents=True, exist_ok=True)
            for number in numbers:
                asset = find_asset(shape, number).resolve()
                bad_paths.add(asset)
                shutil.copy2(asset, out_dir / asset.name)
                rows.append(
                    {
                        "shape": shape,
                        "number": str(number),
                        "issue": issue,
                        "asset_path": str(asset),
                        "review_copy": str((out_dir / asset.name).resolve()),
                    }
                )

    with ISSUE_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["shape", "number", "issue", "asset_path", "review_copy"])
        writer.writeheader()
        writer.writerows(rows)

    return bad_paths


def write_filtered_index(bad_paths: set[Path]) -> tuple[int, int]:
    with INDEX_CSV.open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    kept = [row for row in rows if Path(row["asset_path"]).resolve() not in bad_paths]
    with FILTERED_INDEX_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(kept)

    return len(rows), len(kept)


def main() -> int:
    bad_paths = write_issue_review()
    total, kept = write_filtered_index(bad_paths)
    print(f"Marked bad assets: {len(bad_paths)}")
    print(f"Wrote issue CSV: {ISSUE_CSV}")
    print(f"Wrote review copies under: {REVIEW_ROOT}")
    print(f"Wrote filtered index: {FILTERED_INDEX_CSV}")
    print(f"Asset index: {total} -> {kept} usable assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
