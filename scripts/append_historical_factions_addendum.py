#!/usr/bin/env python3
"""
Append historical faction seed files to power_age_project.

Usage:
  python append_historical_factions_addendum.py /path/to/power_age_historical_factions_addendum --project-dir /path/to/power_age_project

It appends/merges:
  persons_historical_factions_addendum.csv -> data/raw/persons.csv, unique by person_id
  factions_historical.csv -> data/raw/factions.csv, unique by faction_id
  person_factions_historical.csv -> data/raw/person_factions.csv
  faction_relations_historical.csv -> data/raw/faction_relations.csv
  elite_edges_historical.csv -> data/raw/elite_edges.csv
  sources_historical_factions.csv -> data/raw/sources_factions.csv
  historical_faction_model_config.json -> data/raw/historical_faction_model_config.json
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


def append_unique(target: Path, addendum: Path, key_cols: list[str] | None = None) -> None:
    add_rows = read_csv(addendum)
    if not add_rows:
        print(f"No rows: {addendum}")
        return

    target_rows = read_csv(target)
    fieldnames = list(target_rows[0].keys()) if target_rows else list(add_rows[0].keys())

    if key_cols:
        existing = {tuple(r.get(c, "") for c in key_cols) for r in target_rows}
        new_rows = []
        for row in add_rows:
            key = tuple(row.get(c, "") for c in key_cols)
            if key not in existing:
                new_rows.append(row)
                existing.add(key)
    else:
        new_rows = add_rows

    write_csv(target, target_rows + new_rows, fieldnames)
    print(f"Appended {len(new_rows)} rows to {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("addendum_dir", type=Path)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    addendum_dir = args.addendum_dir.resolve()
    raw_dir = args.project_dir.resolve() / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    append_unique(raw_dir / "persons.csv", addendum_dir / "persons_historical_factions_addendum.csv", ["person_id"])
    append_unique(raw_dir / "factions.csv", addendum_dir / "factions_historical.csv", ["faction_id"])
    append_unique(raw_dir / "person_factions.csv", addendum_dir / "person_factions_historical.csv",
                  ["person_id", "faction_id", "start_year", "end_year", "relation_type"])
    append_unique(raw_dir / "faction_relations.csv", addendum_dir / "faction_relations_historical.csv",
                  ["source_faction_id", "target_faction_id", "start_year", "end_year", "relation_type"])
    append_unique(raw_dir / "elite_edges.csv", addendum_dir / "elite_edges_historical.csv",
                  ["source_person_id", "target_person_id", "start_year", "end_year", "edge_type"])

    append_unique(raw_dir / "sources_factions.csv", addendum_dir / "sources_historical_factions.csv", ["source_id"])

    cfg = addendum_dir / "historical_faction_model_config.json"
    if cfg.exists():
        shutil.copy2(cfg, raw_dir / cfg.name)
        print(f"Copied {cfg.name} -> {raw_dir / cfg.name}")

    print("\nDone. Re-run:")
    print("  .venv/bin/python -m power_age.cli diagnostics")
    print("  .venv/bin/python -m power_age.cli build-factions")
    print("  .venv/bin/python -m power_age.cli plot-factions")
    print("  .venv/bin/python -m power_age.cli faction-summary")


if __name__ == "__main__":
    main()
