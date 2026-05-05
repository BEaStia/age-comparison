from __future__ import annotations

import pandas as pd
import pytest

from power_age.factions import (
    active_person_factions_for_year,
    build_faction_year_table,
    build_faction_type_year_table,
    compute_elite_fragmentation,
    historical_period_for_year,
)
from power_age.validate import validate_faction_references


def _sample_persons() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_id": ["a", "b"],
            "name_ru": ["A", "B"],
            "birth_date": pd.to_datetime(["1960-01-01", "1970-01-01"]),
        }
    )


def _sample_positions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_id": ["a", "b"],
            "position": ["core", "core"],
            "start_date": pd.to_datetime(["2010-01-01", "2010-01-01"]),
            "end_date": pd.to_datetime([None, None]),
            "tier": [1, 1],
            "institution": ["test", "test"],
            "influence_weight": [1.0, 1.0],
            "is_ruler": [False, False],
            "is_core_elite": [True, True],
        }
    )


def _sample_entries() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_id": ["a", "b"],
            "political_entry_date": pd.to_datetime(["2000-01-01", "2005-01-01"]),
            "elite_entry_date": pd.to_datetime(["2010-01-01", "2010-01-01"]),
            "ruling_circle_entry_date": pd.to_datetime(["2010-01-01", "2010-01-01"]),
        }
    )


def _sample_factions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "faction_id": ["f1", "f2"],
            "faction_name_ru": ["Ф1", "Ф2"],
            "faction_type": ["type_a", "type_b"],
        }
    )


def test_active_person_factions_for_year_filters_years() -> None:
    person_factions = pd.DataFrame(
        {
            "person_id": ["a", "b"],
            "faction_id": ["f1", "f2"],
            "start_year": [2000, 2021],
            "end_year": [2020, None],
            "confidence": [0.8, 0.8],
        }
    )

    active = active_person_factions_for_year(person_factions, 2020)

    assert active["person_id"].tolist() == ["a"]


def test_confidence_below_min_confidence_is_excluded() -> None:
    person_factions = pd.DataFrame(
        {
            "person_id": ["a", "b"],
            "faction_id": ["f1", "f2"],
            "start_year": [2000, 2000],
            "end_year": [None, None],
            "confidence": [0.4, 0.7],
        }
    )

    active = active_person_factions_for_year(person_factions, 2020, min_confidence=0.5)

    assert active["person_id"].tolist() == ["b"]


def test_one_person_in_two_factions_counts_in_both_and_normalizes_to_one() -> None:
    person_factions = pd.DataFrame(
        {
            "person_id": ["a", "a", "b"],
            "faction_id": ["f1", "f2", "f2"],
            "start_year": [2000, 2000, 2000],
            "end_year": [None, None, None],
            "confidence": [1.0, 1.0, 1.0],
        }
    )

    faction_year = build_faction_year_table(
        _sample_persons(),
        _sample_positions(),
        _sample_entries(),
        _sample_factions(),
        person_factions,
        start_year=2020,
        end_year=2020,
        min_confidence=0.5,
    )

    assert set(faction_year["faction_id"]) == {"f1", "f2"}
    assert faction_year.set_index("faction_id").loc["f1", "members_count"] == 1
    assert faction_year.set_index("faction_id").loc["f2", "members_count"] == 2
    assert faction_year["normalized_power_share"].sum() == pytest.approx(1.0, abs=0.001)


def test_fragmentation_index_between_zero_and_one() -> None:
    faction_year = pd.DataFrame(
        {
            "year": [2020, 2020],
            "faction_id": ["f1", "f2"],
            "normalized_power_share": [0.25, 0.75],
        }
    )

    fragmentation = compute_elite_fragmentation(faction_year)

    assert fragmentation["fragmentation_index"].iloc[0] >= 0
    assert fragmentation["fragmentation_index"].iloc[0] <= 1


def test_validate_faction_references_unknown_person() -> None:
    errors = validate_faction_references(
        _sample_persons(),
        _sample_factions(),
        pd.DataFrame(
            {
                "person_id": ["missing"],
                "faction_id": ["f1"],
                "start_year": [2020],
                "end_year": [None],
                "confidence": [0.8],
            }
        ),
        pd.DataFrame(),
        pd.DataFrame(),
    )

    assert any("unknown person_id=missing" in error for error in errors)


def test_validate_faction_references_unknown_faction() -> None:
    errors = validate_faction_references(
        _sample_persons(),
        _sample_factions(),
        pd.DataFrame(
            {
                "person_id": ["a"],
                "faction_id": ["missing"],
                "start_year": [2020],
                "end_year": [None],
                "confidence": [0.8],
            }
        ),
        pd.DataFrame(),
        pd.DataFrame(),
    )

    assert any("unknown faction_id=missing" in error for error in errors)


def test_validate_faction_references_confidence_above_one() -> None:
    errors = validate_faction_references(
        _sample_persons(),
        _sample_factions(),
        pd.DataFrame(
            {
                "person_id": ["a"],
                "faction_id": ["f1"],
                "start_year": [2020],
                "end_year": [None],
                "confidence": [1.2],
            }
        ),
        pd.DataFrame(),
        pd.DataFrame(),
    )

    assert any("confidence=1.2" in error for error in errors)


def test_build_factions_from_1801_tolerates_sparse_data() -> None:
    faction_year = build_faction_year_table(
        _sample_persons(),
        _sample_positions(),
        _sample_entries(),
        _sample_factions(),
        pd.DataFrame(
            {
                "person_id": ["a"],
                "faction_id": ["f1"],
                "start_year": [2020],
                "end_year": [None],
                "confidence": [0.9],
            }
        ),
        start_year=1801,
        end_year=1802,
    )

    assert faction_year.empty


def test_faction_type_aggregation_sums_to_one_by_year() -> None:
    faction_year = pd.DataFrame(
        {
            "year": [2020, 2020],
            "faction_id": ["f1", "f2"],
            "total_faction_power": [1.0, 3.0],
            "normalized_power_share": [0.25, 0.75],
            "mean_age": [50.0, 60.0],
            "weighted_mean_age": [50.0, 60.0],
            "mean_political_age": [20.0, 30.0],
            "weighted_mean_political_age": [20.0, 30.0],
        }
    )

    faction_type_year = build_faction_type_year_table(faction_year, _sample_factions())

    assert faction_type_year.groupby("year")["normalized_power_share"].sum().iloc[0] == pytest.approx(
        1.0,
        abs=0.001,
    )


def test_historical_period_for_year() -> None:
    assert historical_period_for_year(1937)["label"] == "Stalin era"
    assert historical_period_for_year(1982)["label"] == "Late Soviet"
    assert historical_period_for_year(1988)["label"] == "Perestroika"
