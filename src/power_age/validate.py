from __future__ import annotations

import pandas as pd


def _unknown_values(values: pd.Series, known_values: set[str]) -> list[str]:
    present = values.dropna().astype(str)
    return sorted(value for value in present.unique() if value not in known_values)


def _check_range(
    df: pd.DataFrame,
    column: str,
    label: str,
    errors: list[str],
    low: float = 0.0,
    high: float = 1.0,
) -> None:
    if df.empty or column not in df.columns:
        return
    values = pd.to_numeric(df[column], errors="coerce")
    invalid = df[values.notna() & ~values.between(low, high, inclusive="both")]
    for index, row in invalid.iterrows():
        errors.append(f"{label}: row {index} has {column}={row[column]}, expected {low}..{high}")


def _check_year_order(df: pd.DataFrame, label: str, errors: list[str]) -> None:
    if df.empty or "start_year" not in df.columns or "end_year" not in df.columns:
        return
    start = pd.to_numeric(df["start_year"], errors="coerce")
    end = pd.to_numeric(df["end_year"], errors="coerce")
    invalid = df[start.notna() & end.notna() & (end < start)]
    for index, row in invalid.iterrows():
        errors.append(
            f"{label}: row {index} has end_year={row['end_year']} before start_year={row['start_year']}"
        )


def validate_faction_references(
    persons: pd.DataFrame,
    factions: pd.DataFrame,
    person_factions: pd.DataFrame,
    faction_relations: pd.DataFrame,
    elite_edges: pd.DataFrame,
) -> list[str]:
    errors: list[str] = []
    known_persons = set(persons.get("person_id", pd.Series(dtype=str)).dropna().astype(str))
    known_factions = set(factions.get("faction_id", pd.Series(dtype=str)).dropna().astype(str))

    for person_id in _unknown_values(person_factions.get("person_id", pd.Series(dtype=str)), known_persons):
        errors.append(f"person_factions: unknown person_id={person_id}")
    for faction_id in _unknown_values(
        person_factions.get("faction_id", pd.Series(dtype=str)),
        known_factions,
    ):
        errors.append(f"person_factions: unknown faction_id={faction_id}")

    for column in ["source_faction_id", "target_faction_id"]:
        for faction_id in _unknown_values(
            faction_relations.get(column, pd.Series(dtype=str)),
            known_factions,
        ):
            errors.append(f"faction_relations: unknown {column}={faction_id}")

    for column in ["source_person_id", "target_person_id"]:
        for person_id in _unknown_values(elite_edges.get(column, pd.Series(dtype=str)), known_persons):
            errors.append(f"elite_edges: unknown {column}={person_id}")

    _check_range(person_factions, "confidence", "person_factions", errors)
    _check_range(faction_relations, "confidence", "faction_relations", errors)
    _check_range(faction_relations, "intensity", "faction_relations", errors)
    _check_range(elite_edges, "confidence", "elite_edges", errors)
    _check_range(elite_edges, "weight", "elite_edges", errors)

    _check_year_order(person_factions, "person_factions", errors)
    _check_year_order(faction_relations, "faction_relations", errors)
    _check_year_order(elite_edges, "elite_edges", errors)

    return errors


def validate_events(events: pd.DataFrame, persons: pd.DataFrame, factions: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if events.empty:
        return errors

    if "event_id" in events.columns:
        duplicated = events[events["event_id"].duplicated(keep=False)]["event_id"].dropna().astype(str)
        for event_id in sorted(duplicated.unique()):
            errors.append(f"events: duplicate event_id={event_id}")

    if "date" in events.columns:
        missing_dates = events[events["date"].isna()]
        for index, row in missing_dates.iterrows():
            errors.append(f"events: row {index} event_id={row.get('event_id', '')} has empty date")

    _check_range(events, "severity", "events", errors, low=1, high=5)
    if "confidence" in events.columns:
        _check_range(events, "confidence", "events", errors, low=0, high=1)

    if "elite_initiated" in events.columns:
        invalid = events[
            events["elite_initiated"].notna()
            & ~events["elite_initiated"].map(lambda value: isinstance(value, bool))
        ]
        for index, row in invalid.iterrows():
            errors.append(
                f"events: row {index} event_id={row.get('event_id', '')} has non-bool elite_initiated"
            )

    known_persons = set(persons.get("person_id", pd.Series(dtype=str)).dropna().astype(str))
    if "initiator_person_id" in events.columns:
        for person_id in _unknown_values(events["initiator_person_id"], known_persons):
            errors.append(f"events: unknown initiator_person_id={person_id}")

    if not factions.empty and "initiator_group" in events.columns:
        known_factions = set(factions.get("faction_id", pd.Series(dtype=str)).dropna().astype(str))
        for faction_id in _unknown_values(events["initiator_group"], known_factions):
            errors.append(f"events: unknown initiator_group={faction_id}")

    return errors
