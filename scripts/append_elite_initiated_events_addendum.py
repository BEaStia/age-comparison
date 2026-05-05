#!/usr/bin/env python3
"""
Append elite-initiated events addendum to power_age_project.

Usage:
  python append_elite_initiated_events_addendum.py /path/to/power_age_elite_initiated_events_addendum --project-dir /path/to/power_age_project

Behavior:
  - Appends to data/raw/events.csv, adding any missing columns.
  - Skips duplicate event_id.
  - Copies event_type_taxonomy.csv to data/raw/event_type_taxonomy.csv.

The addendum uses an extended events schema. Existing code that expects the old columns
should continue to work because the original columns are preserved:
event_id,date,event_name,event_type,severity,decision_direction,notes
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("addendum_dir", type=Path)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    addendum_dir = args.addendum_dir.resolve()
    raw_dir = args.project_dir.resolve() / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    events_path = raw_dir / "events.csv"
    add_path = addendum_dir / "events_elite_initiated_addendum.csv"

    existing = read_csv(events_path)
    add_rows = read_csv(add_path)

    if not add_rows:
        raise SystemExit(f"No addendum rows found at {add_path}")

    fieldnames: list[str] = []
    for rowset in (existing, add_rows):
        for row in rowset:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

    existing_ids = {r.get("event_id") for r in existing if r.get("event_id")}
    new_rows = []
    for row in add_rows:
        if row.get("event_id") not in existing_ids:
            new_rows.append(row)
            existing_ids.add(row.get("event_id"))

    write_csv(events_path, existing + new_rows, fieldnames)
    print(f"Appended {len(new_rows)} new events to {events_path}")

    taxonomy = addendum_dir / "event_type_taxonomy.csv"
    if taxonomy.exists():
        shutil.copy2(taxonomy, raw_dir / "event_type_taxonomy.csv")
        print(f"Copied event_type_taxonomy.csv -> {raw_dir / 'event_type_taxonomy.csv'}")

    print("\nNext:")
    print("  .venv/bin/python -m power_age.cli diagnostics")
    print("  .venv/bin/python -m power_age.cli build")
    print("  .venv/bin/python -m power_age.cli plot")
    print("  .venv/bin/python -m power_age.cli summary")


if __name__ == "__main__":
    main()
