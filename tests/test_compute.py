from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from power_age.compute import (
    age_on_date,
    active_positions_for_year,
    build_elite_year_table,
    compute_year_snapshot,
    years_since,
)
from power_age.load_data import load_all_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_age_on_date() -> None:
    age = age_on_date("1952-10-07", "2026-07-01")
    assert age == pytest.approx(73.73, abs=0.02)


def test_years_since() -> None:
    years = years_since("2000-01-01", "2005-01-01")
    assert years == pytest.approx(5.0, abs=0.01)


def test_active_positions_for_year() -> None:
    data = load_all_data(PROJECT_ROOT / "data")
    active = active_positions_for_year(data["positions"], 2026)
    assert "putin" in active["person_id"].tolist()
    assert active.loc[active["person_id"] == "putin", "position"].iloc[0] == "president_rf"


def test_build_elite_year_table() -> None:
    data = load_all_data(PROJECT_ROOT / "data")
    table = build_elite_year_table(
        data["persons"],
        data["positions"],
        data["political_entries"],
        start_year=1801,
        end_year=2026,
    )
    assert table["year"].min() == 1801
    assert table["year"].max() == 2026
    assert len(table) == 226


def test_weighted_mean_age() -> None:
    persons = pd.DataFrame(
        {
            "person_id": ["a", "b"],
            "name_ru": ["A", "B"],
            "birth_date": pd.to_datetime(["1980-01-01", "1960-01-01"]),
        }
    )
    positions = pd.DataFrame(
        {
            "person_id": ["a", "b"],
            "position": ["core", "core"],
            "start_date": pd.to_datetime(["2010-01-01", "2010-01-01"]),
            "end_date": pd.to_datetime([None, None]),
            "tier": [1, 1],
            "institution": ["test", "test"],
            "influence_weight": [1.0, 3.0],
            "is_ruler": [False, False],
            "is_core_elite": [True, True],
            "notes": [None, None],
        }
    )
    political_entries = pd.DataFrame(
        {
            "person_id": ["a", "b"],
            "political_entry_date": pd.to_datetime(["2010-01-01", "2010-01-01"]),
            "elite_entry_date": pd.to_datetime(["2010-01-01", "2010-01-01"]),
            "ruling_circle_entry_date": pd.to_datetime(["2010-01-01", "2010-01-01"]),
        }
    )

    snapshot = compute_year_snapshot(2020, persons, positions, political_entries)
    age_a = age_on_date("1980-01-01", "2020-07-01")
    age_b = age_on_date("1960-01-01", "2020-07-01")
    expected = (age_a * 1.0 + age_b * 3.0) / 4.0

    assert snapshot["core_weighted_mean_age"] == pytest.approx(expected, abs=0.01)


def test_core_elite_deduplicates_person_year() -> None:
    persons = pd.DataFrame(
        {
            "person_id": ["a"],
            "name_ru": ["A"],
            "birth_date": pd.to_datetime(["1960-01-01"]),
        }
    )
    positions = pd.DataFrame(
        {
            "person_id": ["a", "a"],
            "position": ["core_low", "core_high"],
            "start_date": pd.to_datetime(["2010-01-01", "2010-01-01"]),
            "end_date": pd.to_datetime([None, None]),
            "tier": [3, 2],
            "institution": ["test", "test"],
            "influence_weight": [0.3, 0.8],
            "is_ruler": [False, False],
            "is_core_elite": [True, True],
            "notes": [None, None],
        }
    )
    political_entries = pd.DataFrame(
        {
            "person_id": ["a"],
            "political_entry_date": pd.to_datetime(["2010-01-01"]),
            "elite_entry_date": pd.to_datetime(["2010-01-01"]),
            "ruling_circle_entry_date": pd.to_datetime(["2010-01-01"]),
        }
    )

    snapshot = compute_year_snapshot(2020, persons, positions, political_entries)

    assert snapshot["core_elite_count"] == 1
    assert snapshot["core_weighted_mean_age"] == pytest.approx(
        age_on_date("1960-01-01", "2020-07-01"), abs=0.01
    )
