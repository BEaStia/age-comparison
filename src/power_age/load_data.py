from __future__ import annotations

from pathlib import Path

import pandas as pd


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _read_csv(path: str | Path, date_columns: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path, keep_default_na=True)
    for column in date_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def load_persons(path: str | Path) -> pd.DataFrame:
    return _read_csv(path, ["birth_date", "death_date"])


def load_positions(path: str | Path) -> pd.DataFrame:
    df = _read_csv(path, ["start_date", "end_date"])
    for column in ["is_ruler", "is_core_elite"]:
        if column in df.columns:
            df[column] = df[column].map(_parse_bool)
    return df


def load_events(path: str | Path) -> pd.DataFrame:
    return _read_csv(path, ["date"])


def load_political_entries(path: str | Path) -> pd.DataFrame:
    return _read_csv(
        path,
        ["political_entry_date", "elite_entry_date", "ruling_circle_entry_date"],
    )


def load_all_data(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    data_path = Path(data_dir)
    raw_path = data_path / "raw"
    return {
        "persons": load_persons(raw_path / "persons.csv"),
        "positions": load_positions(raw_path / "positions.csv"),
        "events": load_events(raw_path / "events.csv"),
        "political_entries": load_political_entries(raw_path / "political_entries.csv"),
    }
