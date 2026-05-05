from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from power_age.compute import active_positions_for_year, age_on_date, years_since


FACTION_YEAR_COLUMNS = [
    "year",
    "faction_id",
    "faction_name_ru",
    "members_count",
    "total_faction_power",
    "raw_power_share",
    "normalized_power_share",
    "mean_age",
    "weighted_mean_age",
    "mean_political_age",
    "weighted_mean_political_age",
    "mean_elite_age",
    "share_60_plus",
    "share_70_plus",
]

HISTORICAL_PERIODS = [
    {
        "period_id": "empire_1801_1917",
        "label": "Russian Empire",
        "start_year": 1801,
        "end_year": 1917,
        "slug": "empire_1801_1917",
    },
    {
        "period_id": "revolution_1917_1924",
        "label": "Revolution / early Soviet",
        "start_year": 1917,
        "end_year": 1924,
        "slug": "revolution_1917_1924",
    },
    {
        "period_id": "stalin_1924_1953",
        "label": "Stalin era",
        "start_year": 1924,
        "end_year": 1953,
        "slug": "stalin_1924_1953",
    },
    {
        "period_id": "poststalin_1953_1964",
        "label": "Post-Stalin / Khrushchev",
        "start_year": 1953,
        "end_year": 1964,
        "slug": "poststalin_1953_1964",
    },
    {
        "period_id": "lateussr_1964_1985",
        "label": "Late Soviet",
        "start_year": 1964,
        "end_year": 1985,
        "slug": "lateussr_1964_1985",
    },
    {
        "period_id": "perestroika_1985_1991",
        "label": "Perestroika",
        "start_year": 1985,
        "end_year": 1991,
        "slug": "perestroika_1985_1991",
    },
    {
        "period_id": "rf_1991_2026",
        "label": "Russian Federation",
        "start_year": 1991,
        "end_year": 2026,
        "slug": "rf_1991_2026",
    },
]


def historical_period_for_year(year: int) -> dict[str, Any]:
    for period in HISTORICAL_PERIODS:
        if int(period["start_year"]) <= year <= int(period["end_year"]):
            return period
    return {
        "period_id": "unknown",
        "label": "Unknown",
        "start_year": year,
        "end_year": year,
        "slug": "unknown",
    }


def active_person_factions_for_year(
    person_factions: pd.DataFrame,
    year: int,
    min_confidence: float = 0.0,
) -> pd.DataFrame:
    if person_factions.empty:
        return person_factions.copy()
    start = pd.to_numeric(person_factions["start_year"], errors="coerce")
    end = pd.to_numeric(person_factions["end_year"], errors="coerce")
    confidence = pd.to_numeric(person_factions["confidence"], errors="coerce")
    active = person_factions[
        (start <= year)
        & (end.isna() | (end >= year))
        & (confidence >= min_confidence)
    ].copy()
    active["confidence"] = confidence.loc[active.index].astype(float)
    return active


def _active_faction_ids_for_year(factions: pd.DataFrame, year: int) -> set[str]:
    if factions.empty:
        return set()
    if "start_year" not in factions.columns or "end_year" not in factions.columns:
        return set(factions["faction_id"].dropna().astype(str))
    start = pd.to_numeric(factions["start_year"], errors="coerce")
    end = pd.to_numeric(factions["end_year"], errors="coerce")
    active = factions[(start <= year) & (end.isna() | (end >= year))]
    return set(active["faction_id"].dropna().astype(str))


def _active_core_elite(
    persons: pd.DataFrame,
    positions: pd.DataFrame,
    political_entries: pd.DataFrame,
    year: int,
) -> pd.DataFrame:
    target = pd.Timestamp(year=year, month=7, day=1)
    core = active_positions_for_year(positions, year)
    core = core[core["is_core_elite"]].copy()
    if core.empty:
        return core
    core = core.sort_values(
        ["person_id", "influence_weight", "tier"],
        ascending=[True, False, True],
    ).drop_duplicates(subset=["person_id"], keep="first")
    core = core.merge(persons, on="person_id", how="left")
    core = core.merge(political_entries, on="person_id", how="left")
    core["age"] = core["birth_date"].apply(lambda value: age_on_date(value, target))
    core["political_age"] = core["political_entry_date"].apply(lambda value: years_since(value, target))
    core["elite_age"] = core["elite_entry_date"].apply(lambda value: years_since(value, target))
    core["influence_weight"] = pd.to_numeric(core["influence_weight"], errors="coerce").fillna(0.0)
    return core


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna()
    values = values[mask].astype(float)
    weights = weights[mask].astype(float)
    if values.empty or weights.sum() == 0:
        return float("nan")
    return round(float(np.average(values, weights=weights)), 2)


def compute_faction_year_snapshot(
    year: int,
    persons: pd.DataFrame,
    positions: pd.DataFrame,
    political_entries: pd.DataFrame,
    factions: pd.DataFrame,
    person_factions: pd.DataFrame,
    min_confidence: float = 0.5,
) -> pd.DataFrame:
    core = _active_core_elite(persons, positions, political_entries, year)
    active_factions = active_person_factions_for_year(person_factions, year, min_confidence)
    active_faction_ids = _active_faction_ids_for_year(factions, year)
    if active_faction_ids:
        active_factions = active_factions[
            active_factions["faction_id"].astype(str).isin(active_faction_ids)
        ].copy()
    if core.empty or active_factions.empty or factions.empty:
        return pd.DataFrame(columns=FACTION_YEAR_COLUMNS)

    active_factions = active_factions[["person_id", "faction_id", "confidence"]].copy()
    joined = core.merge(active_factions, on="person_id", how="inner")
    if joined.empty:
        return pd.DataFrame(columns=FACTION_YEAR_COLUMNS)

    joined["faction_person_power"] = joined["influence_weight"] * joined["confidence"]
    total_core_influence = float(core["influence_weight"].sum())

    rows: list[dict[str, Any]] = []
    for faction_id, group in joined.groupby("faction_id", dropna=False):
        weights = group["faction_person_power"]
        ages = group["age"]
        political_ages = group["political_age"]
        total_power = float(weights.sum())
        rows.append(
            {
                "year": year,
                "faction_id": faction_id,
                "members_count": int(group["person_id"].nunique()),
                "total_faction_power": round(total_power, 4),
                "raw_power_share": round(total_power / total_core_influence, 4)
                if total_core_influence
                else np.nan,
                "mean_age": round(float(ages.mean()), 2) if ages.notna().any() else np.nan,
                "weighted_mean_age": _weighted_mean(ages, weights),
                "mean_political_age": round(float(political_ages.mean()), 2)
                if political_ages.notna().any()
                else np.nan,
                "weighted_mean_political_age": _weighted_mean(political_ages, weights),
                "mean_elite_age": round(float(group["elite_age"].mean()), 2)
                if group["elite_age"].notna().any()
                else np.nan,
                "share_60_plus": round(float((ages >= 60).mean()), 4) if not ages.empty else np.nan,
                "share_70_plus": round(float((ages >= 70).mean()), 4) if not ages.empty else np.nan,
            }
        )

    result = pd.DataFrame(rows)
    total_faction_power = result["total_faction_power"].sum()
    result["normalized_power_share"] = (
        result["total_faction_power"] / total_faction_power if total_faction_power else np.nan
    )
    result["normalized_power_share"] = result["normalized_power_share"].round(4)
    names = factions[["faction_id", "faction_name_ru"]].drop_duplicates(subset=["faction_id"])
    result = result.merge(names, on="faction_id", how="left")
    result = result[FACTION_YEAR_COLUMNS]
    return result.sort_values(["year", "normalized_power_share"], ascending=[True, False])


def build_faction_year_table(
    persons: pd.DataFrame,
    positions: pd.DataFrame,
    political_entries: pd.DataFrame,
    factions: pd.DataFrame,
    person_factions: pd.DataFrame,
    start_year: int = 1801,
    end_year: int = 2026,
    min_confidence: float = 0.5,
) -> pd.DataFrame:
    frames = [
        compute_faction_year_snapshot(
            year,
            persons,
            positions,
            political_entries,
            factions,
            person_factions,
            min_confidence=min_confidence,
        )
        for year in range(start_year, end_year + 1)
    ]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=FACTION_YEAR_COLUMNS)
    return pd.concat(frames, ignore_index=True)


def build_faction_type_year_table(faction_year: pd.DataFrame, factions: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "year",
        "faction_type",
        "total_power",
        "normalized_power_share",
        "mean_age",
        "weighted_mean_age",
        "mean_political_age",
        "weighted_mean_political_age",
        "factions_count",
    ]
    if faction_year.empty or factions.empty:
        return pd.DataFrame(columns=columns)

    data = faction_year.merge(
        factions[["faction_id", "faction_type"]],
        on="faction_id",
        how="left",
    )
    data["faction_type"] = data["faction_type"].fillna("unknown")
    rows: list[dict[str, Any]] = []
    for (year, faction_type), group in data.groupby(["year", "faction_type"]):
        power = group["total_faction_power"].fillna(0).astype(float)
        share = group["normalized_power_share"].fillna(0).astype(float)
        rows.append(
            {
                "year": int(year),
                "faction_type": faction_type,
                "total_power": round(float(power.sum()), 4),
                "normalized_power_share": round(float(share.sum()), 4),
                "mean_age": round(float(group["mean_age"].mean()), 2)
                if group["mean_age"].notna().any()
                else np.nan,
                "weighted_mean_age": _weighted_mean(group["weighted_mean_age"], power),
                "mean_political_age": round(float(group["mean_political_age"].mean()), 2)
                if group["mean_political_age"].notna().any()
                else np.nan,
                "weighted_mean_political_age": _weighted_mean(
                    group["weighted_mean_political_age"],
                    power,
                ),
                "factions_count": int(group["faction_id"].nunique()),
            }
        )
    result = pd.DataFrame(rows)
    year_totals = result.groupby("year")["normalized_power_share"].transform("sum")
    result["normalized_power_share"] = (
        result["normalized_power_share"] / year_totals.replace(0, np.nan)
    ).round(4)
    return result[columns].sort_values(["year", "normalized_power_share"], ascending=[True, False])


def compute_elite_fragmentation(faction_year: pd.DataFrame) -> pd.DataFrame:
    if faction_year.empty:
        return pd.DataFrame(
            columns=[
                "year",
                "fragmentation_index",
                "dominant_faction_id",
                "dominant_faction_share",
                "factions_count",
            ]
        )
    rows: list[dict[str, Any]] = []
    for year, group in faction_year.groupby("year"):
        shares = group["normalized_power_share"].fillna(0).astype(float)
        dominant = group.sort_values("normalized_power_share", ascending=False).iloc[0]
        rows.append(
            {
                "year": int(year),
                "fragmentation_index": round(float(1 - (shares**2).sum()), 4),
                "dominant_faction_id": dominant["faction_id"],
                "dominant_faction_share": round(float(dominant["normalized_power_share"]), 4),
                "factions_count": int(group["faction_id"].nunique()),
            }
        )
    return pd.DataFrame(rows)


def add_faction_context_to_events(events: pd.DataFrame, faction_year: pd.DataFrame) -> pd.DataFrame:
    result = events.copy()
    if result.empty:
        return result
    result["year"] = result["date"].dt.year
    fragmentation = compute_elite_fragmentation(faction_year)
    top_factions = (
        faction_year.sort_values(["year", "normalized_power_share"], ascending=[True, False])
        .groupby("year")
        .head(3)
        .groupby("year")["faction_id"]
        .apply(lambda values: ", ".join(values.astype(str)))
        .rename("top_3_factions")
        .reset_index()
    )
    context = fragmentation.merge(top_factions, on="year", how="left")
    context = context[["year", "dominant_faction_id", "fragmentation_index", "top_3_factions"]]
    return result.merge(context, on="year", how="left")
