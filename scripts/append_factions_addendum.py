#!/usr/bin/env python3
"""
Append faction addendum files to an existing power_age_project.

Usage:
  python append_factions_addendum.py /path/to/power_age_factions_addendum --project-dir /path/to/power_age_project

What it does:
  - appends persons_faction_addendum.csv to data/raw/persons.csv, skipping duplicate person_id;
  - copies faction-layer files into data/raw:
      factions.csv
      person_factions.csv
      faction_relations.csv
      elite_edges.csv
      faction_model_config.json
      sources_factions.csv
"""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def append_unique_by_id(target: Path, addendum: Path, id_col: str) -> None:
    target_rows = read_csv(target)
    add_rows = read_csv(addendum)

    if not add_rows:
        print(f"No addendum rows found: {addendum}")
        return

    fieldnames = list(target_rows[0].keys()) if target_rows else list(add_rows[0].keys())
    existing = {r[id_col] for r in target_rows if r.get(id_col)}

    new_rows = []
    for row in add_rows:
        if row.get(id_col) not in existing:
            new_rows.append(row)
            existing.add(row.get(id_col))

    write_csv(target, target_rows + new_rows, fieldnames)
    print(f"Appended {len(new_rows)} new rows to {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("addendum_dir", type=Path)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    addendum_dir = args.addendum_dir.resolve()
    project_dir = args.project_dir.resolve()
    raw_dir = project_dir / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    append_unique_by_id(
        raw_dir / "persons.csv",
        addendum_dir / "persons_faction_addendum.csv",
        "person_id",
    )

    for filename in [
        "factions.csv",
        "person_factions.csv",
        "faction_relations.csv",
        "elite_edges.csv",
        "faction_model_config.json",
        "sources_factions.csv",
    ]:
        src = addendum_dir / filename
        dst = raw_dir / filename
        shutil.copy2(src, dst)
        print(f"Copied {src.name} -> {dst}")

    print("\nDone. Next: ask Codex to implement faction-layer loading, validation, computations, and plots.")


if __name__ == "__main__":
    main()
