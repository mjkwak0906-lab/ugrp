from __future__ import annotations

"""asset 상태별 5개 폴더를 만든다.

생성 폴더:
- 원본: v4 records_105 전체 315개
- 원본-이상: 품질 이상으로 표시된 asset을 제외한 원본 270개
- 이상: 품질 이상으로 표시된 원본 asset 45개
- 이상_수정후승인됨: 재처리 후 사용 가능하다고 판단한 34개
- 최종: 원본-이상 270개 + 이상_수정후승인됨 34개

각 폴더는 circle/rectangle/triangle 하위 폴더와 asset_index.csv를 가진다.
"""

import csv
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
BASE = PROJECT_ROOT / "candidate_assets_v4_preserve"
ORIGINAL_ROOT = BASE / "records_105"
ISSUE_CSV = BASE / "asset_quality_review" / "asset_quality_issues.csv"
APPROVED_ROOT = BASE / "recovered_approved"
SET_ROOT = BASE / "asset_sets"

SET_NAMES = {
    "original": "원본",
    "clean": "원본-이상",
    "bad": "이상",
    "approved": "이상_수정후승인됨",
    "final": "최종",
}


def asset_number(path: Path) -> int:
    return int(path.stem.split("_", 1)[0])


def load_index() -> list[dict[str, str]]:
    with (ORIGINAL_ROOT / "asset_index.csv").open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_bad_keys() -> set[tuple[str, int]]:
    with ISSUE_CSV.open("r", newline="", encoding="utf-8") as file:
        return {(row["shape"], int(row["number"])) for row in csv.DictReader(file)}


def approved_by_key() -> dict[tuple[str, int], Path]:
    approved: dict[tuple[str, int], Path] = {}
    for shape in ["circle", "rectangle", "triangle"]:
        for path in (APPROVED_ROOT / shape).glob("*.png"):
            approved[(shape, asset_number(path))] = path
    return approved


def clear_set_dirs() -> None:
    SET_ROOT.mkdir(parents=True, exist_ok=True)
    for folder in SET_NAMES.values():
        target = SET_ROOT / folder
        if target.exists():
            shutil.rmtree(target)
        for shape in ["circle", "rectangle", "triangle"]:
            (target / shape).mkdir(parents=True, exist_ok=True)


def copy_asset(row: dict[str, str], set_name: str, source_path: Path | None = None) -> dict[str, str]:
    source = source_path or Path(row["asset_path"])
    target = SET_ROOT / set_name / row["shape"] / source.name
    shutil.copy2(source, target)
    out = dict(row)
    out["asset_path"] = str(target.resolve())
    return out


def write_index(set_name: str, rows: list[dict[str, str]]) -> None:
    path = SET_ROOT / set_name / "asset_index.csv"
    if not rows:
        raise RuntimeError(f"No rows for {set_name}")
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: (row["shape"], row["asset_path"])))


def summarize(set_name: str) -> dict[str, int | str]:
    root = SET_ROOT / set_name
    counts = {
        "folder": set_name,
        "circle": len(list((root / "circle").glob("*.png"))),
        "rectangle": len(list((root / "rectangle").glob("*.png"))),
        "triangle": len(list((root / "triangle").glob("*.png"))),
    }
    counts["total"] = int(counts["circle"]) + int(counts["rectangle"]) + int(counts["triangle"])
    return counts


def main() -> int:
    rows = load_index()
    bad_keys = load_bad_keys()
    approved = approved_by_key()
    clear_set_dirs()

    sets: dict[str, list[dict[str, str]]] = {name: [] for name in SET_NAMES.values()}
    row_by_key = {(row["shape"], asset_number(Path(row["asset_path"]))): row for row in rows}

    for row in rows:
        key = (row["shape"], asset_number(Path(row["asset_path"])))
        sets[SET_NAMES["original"]].append(copy_asset(row, SET_NAMES["original"]))
        if key in bad_keys:
            sets[SET_NAMES["bad"]].append(copy_asset(row, SET_NAMES["bad"]))
        else:
            clean_row = copy_asset(row, SET_NAMES["clean"])
            final_row = copy_asset(row, SET_NAMES["final"])
            sets[SET_NAMES["clean"]].append(clean_row)
            sets[SET_NAMES["final"]].append(final_row)

    for key, source in approved.items():
        base_row = row_by_key[key]
        approved_row = copy_asset(base_row, SET_NAMES["approved"], source_path=source)
        final_row = copy_asset(base_row, SET_NAMES["final"], source_path=source)
        sets[SET_NAMES["approved"]].append(approved_row)
        sets[SET_NAMES["final"]].append(final_row)

    for set_name, set_rows in sets.items():
        write_index(set_name, set_rows)

    summary = [summarize(name) for name in SET_NAMES.values()]
    summary_csv = SET_ROOT / "asset_sets_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["folder", "circle", "rectangle", "triangle", "total"])
        writer.writeheader()
        writer.writerows(summary)

    for item in summary:
        print(item)
    print(f"Wrote asset sets under: {SET_ROOT}")
    print(f"Wrote summary: {summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
