from __future__ import annotations

from pathlib import Path

import pandas as pd

FACTIONS_COLUMNS = [
    "faction_id",
    "faction_name_ru",
    "faction_name_en",
    "faction_type",
    "start_year",
    "end_year",
    "description_ru",
    "notes",
]
PERSON_FACTIONS_COLUMNS = [
    "person_id",
    "faction_id",
    "start_year",
    "end_year",
    "confidence",
    "relation_type",
    "notes",
]
FACTION_RELATIONS_COLUMNS = [
    "source_faction_id",
    "target_faction_id",
    "start_year",
    "end_year",
    "relation_type",
    "intensity",
    "confidence",
    "notes",
]
ELITE_EDGES_COLUMNS = [
    "source_person_id",
    "target_person_id",
    "start_year",
    "end_year",
    "edge_type",
    "weight",
    "confidence",
    "notes",
]


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


def _read_optional_csv(path: str | Path, columns: list[str]) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        return pd.DataFrame(columns=columns)
    return pd.read_csv(csv_path, keep_default_na=True)


def _coerce_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = df.copy()
    for column in columns:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def load_persons(path: str | Path) -> pd.DataFrame:
    return _read_csv(path, ["birth_date", "death_date"])


def load_positions(path: str | Path) -> pd.DataFrame:
    df = _read_csv(path, ["start_date", "end_date"])
    for column in ["is_ruler", "is_core_elite"]:
        if column in df.columns:
            df[column] = df[column].map(_parse_bool)
    return df


def load_events(path: str | Path) -> pd.DataFrame:
    df = _read_csv(path, ["date"])
    if "severity" in df.columns:
        df["severity"] = pd.to_numeric(df["severity"], errors="coerce").astype("Int64")
    if "confidence" in df.columns:
        df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    if "elite_initiated" in df.columns:
        df["elite_initiated"] = df["elite_initiated"].map(_parse_bool)
    return df


def load_political_entries(path: str | Path) -> pd.DataFrame:
    return _read_csv(
        path,
        ["political_entry_date", "elite_entry_date", "ruling_circle_entry_date"],
    )


def load_factions(path: str | Path) -> pd.DataFrame:
    df = _read_optional_csv(path, FACTIONS_COLUMNS)
    if "faction_name_ru" not in df.columns and "faction_name" in df.columns:
        df = df.rename(columns={"faction_name": "faction_name_ru"})
    if "faction_name_en" not in df.columns and "faction_name_ru" in df.columns:
        df["faction_name_en"] = df["faction_name_ru"]
    return _coerce_numeric_columns(df, ["start_year", "end_year"])


def load_person_factions(path: str | Path) -> pd.DataFrame:
    df = _read_optional_csv(path, PERSON_FACTIONS_COLUMNS)
    return _coerce_numeric_columns(df, ["start_year", "end_year", "confidence"])


def load_faction_relations(path: str | Path) -> pd.DataFrame:
    df = _read_optional_csv(path, FACTION_RELATIONS_COLUMNS)
    return _coerce_numeric_columns(df, ["start_year", "end_year", "intensity", "confidence"])


def load_elite_edges(path: str | Path) -> pd.DataFrame:
    df = _read_optional_csv(path, ELITE_EDGES_COLUMNS)
    return _coerce_numeric_columns(df, ["start_year", "end_year", "weight", "confidence"])


def load_periods(path: str | Path) -> pd.DataFrame:
    df = _read_optional_csv(path, [
        "period_id",
        "label",
        "start_year",
        "end_year",
        "slug",
        "label_ru",
        "label_en",
        "notes",
    ])
    return _coerce_numeric_columns(df, ["start_year", "end_year"])


def load_all_data(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    data_path = Path(data_dir)
    raw_path = data_path / "raw"
    return {
        "persons": load_persons(raw_path / "persons.csv"),
        "positions": load_positions(raw_path / "positions.csv"),
        "events": load_events(raw_path / "events.csv"),
        "political_entries": load_political_entries(raw_path / "political_entries.csv"),
        "factions": load_factions(raw_path / "factions.csv"),
        "person_factions": load_person_factions(raw_path / "person_factions.csv"),
        "faction_relations": load_faction_relations(raw_path / "faction_relations.csv"),
        "elite_edges": load_elite_edges(raw_path / "elite_edges.csv"),
        "periods": load_periods(raw_path / "periods.csv"),
    }
