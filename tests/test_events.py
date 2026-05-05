from __future__ import annotations

import pandas as pd

from power_age.events import (
    events_by_period,
    filter_elite_initiated_events,
)
from power_age.validate import validate_events


def test_filter_elite_initiated_events_excludes_low_confidence() -> None:
    events = pd.DataFrame(
        {
            "event_id": ["a", "b"],
            "date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
            "event_name": ["A", "B"],
            "event_type": ["x", "y"],
            "severity": [5, 5],
            "elite_initiated": [True, True],
            "confidence": [0.9, 0.4],
        }
    )

    filtered = filter_elite_initiated_events(events, min_confidence=0.5)

    assert filtered["event_id"].tolist() == ["a"]


def test_filter_elite_initiated_events_without_flag_returns_all() -> None:
    events = pd.DataFrame(
        {
            "event_id": ["a"],
            "date": pd.to_datetime(["2020-01-01"]),
            "event_name": ["A"],
            "event_type": ["x"],
            "severity": [5],
        }
    )

    filtered = filter_elite_initiated_events(events)

    assert filtered["event_id"].tolist() == ["a"]


def test_validate_events_duplicate_event_id() -> None:
    events = pd.DataFrame(
        {
            "event_id": ["dup", "dup"],
            "date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
            "event_name": ["A", "B"],
            "event_type": ["x", "y"],
            "severity": [5, 4],
            "elite_initiated": [True, True],
            "confidence": [0.9, 0.8],
            "initiator_person_id": ["a", "a"],
        }
    )
    persons = pd.DataFrame({"person_id": ["a"]})
    factions = pd.DataFrame({"faction_id": ["f1"]})

    errors = validate_events(events, persons, factions)

    assert any("duplicate event_id=dup" in error for error in errors)


def test_validate_events_confidence_above_one() -> None:
    events = pd.DataFrame(
        {
            "event_id": ["a"],
            "date": pd.to_datetime(["2020-01-01"]),
            "event_name": ["A"],
            "event_type": ["x"],
            "severity": [5],
            "elite_initiated": [True],
            "confidence": [1.2],
        }
    )

    errors = validate_events(events, pd.DataFrame({"person_id": ["a"]}), pd.DataFrame({"faction_id": ["f1"]}))

    assert any("confidence=1.2" in error for error in errors)


def test_validate_events_unknown_initiator_person_id() -> None:
    events = pd.DataFrame(
        {
            "event_id": ["a"],
            "date": pd.to_datetime(["2020-01-01"]),
            "event_name": ["A"],
            "event_type": ["x"],
            "severity": [5],
            "elite_initiated": [True],
            "confidence": [0.9],
            "initiator_person_id": ["missing"],
        }
    )

    errors = validate_events(events, pd.DataFrame({"person_id": ["a"]}), pd.DataFrame({"faction_id": ["f1"]}))

    assert any("unknown initiator_person_id=missing" in error for error in errors)


def test_events_by_period_classifies_history_periods() -> None:
    events = pd.DataFrame(
        {
            "event_id": ["a", "b", "c"],
            "date": pd.to_datetime(["1937-01-01", "1988-01-01", "2014-01-01"]),
            "event_name": ["A", "B", "C"],
            "event_type": ["x", "y", "z"],
            "severity": [5, 4, 5],
            "elite_initiated": [True, True, True],
            "confidence": [0.9, 0.9, 0.9],
        }
    )

    period = events_by_period(events)

    assert period.loc[period["period_id"] == "stalin_1924_1953", "events_count"].iloc[0] == 1
    assert period.loc[period["period_id"] == "perestroika_1985_1991", "events_count"].iloc[0] == 1
    assert period.loc[period["period_id"] == "rf_1991_2026", "events_count"].iloc[0] == 1
