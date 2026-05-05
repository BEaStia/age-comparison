from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

PAIRS = [
    ("persons_early_elite_addendum.csv", "persons.csv", ["person_id"]),
    ("positions_early_elite_addendum.csv", "positions.csv", ["person_id", "position", "start_date", "end_date"]),
    ("political_entries_early_elite_addendum.csv", "political_entries.csv", ["person_id"]),
]


def append_unique(project_dir: Path, addendum_dir: Path, src_name: str, dst_name: str, key_cols: list[str]) -> None:
    src = addendum_dir / src_name
    dst = project_dir / "data" / "raw" / dst_name
    if not src.exists():
        raise FileNotFoundError(src)
    if not dst.exists():
        raise FileNotFoundError(dst)

    base = pd.read_csv(dst)
    extra = pd.read_csv(src)
    merged = pd.concat([base, extra], ignore_index=True)
    merged = merged.drop_duplicates(subset=key_cols, keep="first")
    merged.to_csv(dst, index=False)
    print(f"Updated {dst}: {len(base)} -> {len(merged)} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description="Append early elite addendum CSV files to power_age_project/data/raw.")
    parser.add_argument("addendum_dir", type=Path, help="Path to extracted power_age_early_elite_addendum directory")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd(), help="Path to power_age_project; default: current dir")
    args = parser.parse_args()

    for src_name, dst_name, key_cols in PAIRS:
        append_unique(args.project_dir, args.addendum_dir, src_name, dst_name, key_cols)

    # Optional copy for documentation. It is not required by the current MVP build.
    src_group = args.addendum_dir / "core_elite_groups_early.csv"
    dst_group = args.project_dir / "data" / "raw" / "core_elite_groups_early.csv"
    if src_group.exists():
        dst_group.write_text(src_group.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Copied {dst_group}")

    src_sources = args.addendum_dir / "sources_early_elite_addendum.csv"
    dst_sources = args.project_dir / "data" / "raw" / "sources_early_elite_addendum.csv"
    if src_sources.exists():
        dst_sources.write_text(src_sources.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Copied {dst_sources}")


if __name__ == "__main__":
    main()
