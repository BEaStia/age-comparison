#!/usr/bin/env python3
"""
Append the elite addendum CSV files into an existing power_age_project/data/raw folder.
Run from repository root:
  python scripts/append_elite_addendum.py /path/to/power_age_elite_addendum
or copy this file into scripts/ and run:
  python scripts/append_elite_addendum.py ../power_age_elite_addendum
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd


def append_unique(raw_path: Path, addendum_path: Path, key_cols: list[str]) -> None:
    base = pd.read_csv(raw_path)
    add = pd.read_csv(addendum_path)
    # Keep only columns that exist in the base file so the project schema is not changed.
    add = add[[c for c in base.columns if c in add.columns]]
    merged = pd.concat([base, add], ignore_index=True)
    merged = merged.drop_duplicates(subset=key_cols, keep="first")
    merged.to_csv(raw_path, index=False)
    print(f"Updated {raw_path}: {len(base)} -> {len(merged)} rows")


def main() -> None:
    addendum_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("power_age_elite_addendum")
    raw = Path("data/raw")
    append_unique(raw / "persons.csv", addendum_dir / "persons_elite_addendum.csv", ["person_id"])
    append_unique(raw / "positions.csv", addendum_dir / "positions_elite_addendum.csv", ["person_id", "position", "start_date"])
    append_unique(raw / "political_entries.csv", addendum_dir / "political_entries_elite_addendum.csv", ["person_id"])
    # core_elite_groups and sources are copied rather than appended.
    for name in ["core_elite_groups.csv", "sources_elite_addendum.csv"]:
        src = addendum_dir / name
        dst = raw / name
        if src.exists():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Copied {dst}")


if __name__ == "__main__":
    main()
