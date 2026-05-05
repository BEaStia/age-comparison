from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _to_timestamp(value: Any) -> pd.Timestamp:
    return pd.to_datetime(value)


def age_on_date(birth_date: Any, target_date: Any) -> float:
    """Return biological age in years.

    Methodological note: biological_age is not the same variable as political_age.
    A ruler can be biologically old but politically new, or biologically younger but
    long embedded in elite institutions.
    """
    birth = _to_timestamp(birth_date)
    target = _to_timestamp(target_date)
    if pd.isna(birth) or pd.isna(target):
        return float("nan")
    return round((target - birth).days / 365.2425, 2)


def years_since(start_date: Any, target_date: Any) -> float:
    start = _to_timestamp(start_date)
    target = _to_timestamp(target_date)
    if pd.isna(start) or pd.isna(target) or target < start:
        return float("nan")
    return round((target - start).days / 365.2425, 2)


def active_positions_for_year(positions: pd.DataFrame, year: int) -> pd.DataFrame:
    target = pd.Timestamp(year=year, month=7, day=1)
    active = positions[
        (positions["start_date"] <= target)
        & (positions["end_date"].isna() | (positions["end_date"] >= target))
    ].copy()
    return active


def _year_overlap_days(row: pd.Series, year: int) -> int:
    year_start = pd.Timestamp(year=year, month=1, day=1)
    year_end = pd.Timestamp(year=year, month=12, day=31)
    start = max(row["start_date"], year_start)
    end_date = row["end_date"] if pd.notna(row["end_date"]) else year_end
    end = min(end_date, year_end)
    if end < start:
        return 0
    return int((end - start).days) + 1


def ruler_for_year(persons: pd.DataFrame, positions: pd.DataFrame, year: int) -> dict[str, Any]:
    target = pd.Timestamp(year=year, month=7, day=1)
    rulers_on_date = active_positions_for_year(positions, year)
    rulers_on_date = rulers_on_date[rulers_on_date["is_ruler"]].copy()

    if rulers_on_date.empty:
        year_start = pd.Timestamp(year=year, month=1, day=1)
        year_end = pd.Timestamp(year=year, month=12, day=31)
        candidates = positions[
            (positions["is_ruler"])
            & (positions["start_date"] <= year_end)
            & (positions["end_date"].isna() | (positions["end_date"] >= year_start))
        ].copy()
        if candidates.empty:
            return {}
        candidates["overlap_days"] = candidates.apply(_year_overlap_days, axis=1, year=year)
        position = candidates.sort_values(
            ["overlap_days", "start_date"], ascending=[False, True]
        ).iloc[0]
    else:
        position = rulers_on_date.sort_values(["tier", "start_date"], ascending=[True, True]).iloc[0]

    person_rows = persons[persons["person_id"] == position["person_id"]]
    if person_rows.empty:
        return position.to_dict()

    result = position.to_dict()
    result.update(person_rows.iloc[0].to_dict())
    result["snapshot_date"] = target
    return result


def _person_lookup(df: pd.DataFrame, person_id: str) -> pd.Series | None:
    rows = df[df["person_id"] == person_id]
    if rows.empty:
        return None
    return rows.iloc[0]


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna()
    values = values[mask].astype(float)
    weights = weights[mask].astype(float)
    if values.empty or weights.sum() == 0:
        return float("nan")
    return round(float(np.average(values, weights=weights)), 2)


def compute_year_snapshot(
    year: int,
    persons: pd.DataFrame,
    positions: pd.DataFrame,
    political_entries: pd.DataFrame,
) -> dict[str, Any]:
    target = pd.Timestamp(year=year, month=7, day=1)
    ruler = ruler_for_year(persons, positions, year)
    ruler_person_id = ruler.get("person_id")
    ruler_position_start = ruler.get("start_date")
    ruler_entry = _person_lookup(political_entries, ruler_person_id) if ruler_person_id else None

    # political_entry_date, elite_entry_date and ruling_circle_entry_date are often
    # approximate in the starter dataset. Treat them as explicit research inputs.
    ruler_political_age = (
        years_since(ruler_entry["political_entry_date"], target) if ruler_entry is not None else np.nan
    )
    ruler_elite_age = (
        years_since(ruler_entry["elite_entry_date"], target) if ruler_entry is not None else np.nan
    )
    ruler_ruling_circle_age = (
        years_since(ruler_entry["ruling_circle_entry_date"], target)
        if ruler_entry is not None
        else np.nan
    )

    active = active_positions_for_year(positions, year)
    # The "core elite" filter is a research assumption. In a real historical dataset,
    # the Russian Empire, USSR and Russian Federation need different institutional rules
    # for identifying the actual high-power elite.
    core_positions = active[active["is_core_elite"]].copy()
    core_positions = core_positions.sort_values(
        ["person_id", "influence_weight", "tier"],
        ascending=[True, False, True],
    ).drop_duplicates(subset=["person_id"], keep="first")
    core = core_positions.merge(persons, on="person_id", how="left").merge(
        political_entries, on="person_id", how="left"
    )

    if core.empty:
        ages = pd.Series(dtype=float)
        political_ages = pd.Series(dtype=float)
        elite_ages = pd.Series(dtype=float)
        weights = pd.Series(dtype=float)
    else:
        ages = core["birth_date"].apply(lambda value: age_on_date(value, target))
        political_ages = core["political_entry_date"].apply(lambda value: years_since(value, target))
        elite_ages = core["elite_entry_date"].apply(lambda value: years_since(value, target))
        weights = core["influence_weight"]

    recent_cutoff = target - pd.DateOffset(years=5)
    if core.empty:
        renewal_5y = np.nan
    else:
        recent_entries = core["elite_entry_date"].between(recent_cutoff, target, inclusive="both")
        renewal_5y = round(float(recent_entries.mean()), 3)

    return {
        "year": year,
        "ruler_person_id": ruler_person_id,
        "ruler_name_ru": ruler.get("name_ru"),
        "ruler_age": age_on_date(ruler.get("birth_date"), target) if ruler else np.nan,
        "ruler_political_age": ruler_political_age,
        "ruler_elite_age": ruler_elite_age,
        "ruler_ruling_circle_age": ruler_ruling_circle_age,
        "ruler_office_age": years_since(ruler_position_start, target) if ruler else np.nan,
        "core_elite_count": int(len(core)),
        "core_mean_age": round(float(ages.mean()), 2) if not ages.empty else np.nan,
        "core_median_age": round(float(ages.median()), 2) if not ages.empty else np.nan,
        "core_weighted_mean_age": _weighted_mean(ages, weights),
        "core_mean_political_age": round(float(political_ages.mean()), 2)
        if not political_ages.empty
        else np.nan,
        "core_mean_elite_age": round(float(elite_ages.mean()), 2) if not elite_ages.empty else np.nan,
        "core_share_60_plus": round(float((ages >= 60).mean()), 3) if not ages.empty else np.nan,
        "core_share_70_plus": round(float((ages >= 70).mean()), 3) if not ages.empty else np.nan,
        "core_age_std": round(float(ages.std(ddof=0)), 2) if not ages.empty else np.nan,
        "renewal_5y": renewal_5y,
    }


def build_elite_year_table(
    persons: pd.DataFrame,
    positions: pd.DataFrame,
    political_entries: pd.DataFrame,
    start_year: int = 1801,
    end_year: int = 2026,
) -> pd.DataFrame:
    rows = [
        compute_year_snapshot(year, persons, positions, political_entries)
        for year in range(start_year, end_year + 1)
    ]
    return pd.DataFrame(rows)


def events_for_year(events: pd.DataFrame, year: int) -> pd.DataFrame:
    return events[events["date"].dt.year == year].copy()


def add_event_summary(elite_year: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    result = elite_year.copy()
    result["events_count"] = 0
    result["max_event_severity"] = 0
    result["event_types"] = ""
    result["event_names"] = ""
    result["elite_initiated_events_count"] = 0
    result["elite_initiated_max_severity"] = 0
    result["decision_domains"] = ""
    result["initiator_groups"] = ""
    result["high_confidence_events_count"] = 0

    for year, group in events.groupby(events["date"].dt.year):
        mask = result["year"] == int(year)
        result.loc[mask, "events_count"] = len(group)
        result.loc[mask, "max_event_severity"] = int(group["severity"].max())
        result.loc[mask, "event_types"] = ", ".join(sorted(group["event_type"].dropna().unique()))
        result.loc[mask, "event_names"] = "; ".join(group["event_name"].dropna().astype(str))
        if "elite_initiated" in group.columns:
            elite_group = group[group["elite_initiated"]].copy()
        else:
            elite_group = group.copy()
        result.loc[mask, "elite_initiated_events_count"] = len(elite_group)
        if not elite_group.empty:
            result.loc[mask, "elite_initiated_max_severity"] = int(elite_group["severity"].max())
        if "decision_domain" in group.columns:
            result.loc[mask, "decision_domains"] = ", ".join(
                sorted(group["decision_domain"].dropna().astype(str).unique())
            )
        if "initiator_group" in group.columns:
            result.loc[mask, "initiator_groups"] = ", ".join(
                sorted(group["initiator_group"].dropna().astype(str).unique())
            )
        if "confidence" in group.columns:
            confidence = pd.to_numeric(group["confidence"], errors="coerce")
            result.loc[mask, "high_confidence_events_count"] = int((confidence >= 0.8).sum())

    return result
