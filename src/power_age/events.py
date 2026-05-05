from __future__ import annotations

import pandas as pd

from power_age.factions import HISTORICAL_PERIODS, historical_period_for_year


def filter_elite_initiated_events(events: pd.DataFrame, min_confidence: float = 0.5) -> pd.DataFrame:
    if events.empty:
        return events.copy()
    if "elite_initiated" not in events.columns:
        return events.copy()
    confidence = (
        pd.to_numeric(events["confidence"], errors="coerce")
        if "confidence" in events.columns
        else pd.Series(1.0, index=events.index)
    )
    return events[(events["elite_initiated"]) & (confidence >= min_confidence)].copy()


def events_by_decision_domain(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty or "decision_domain" not in events.columns:
        return pd.DataFrame(columns=["decision_domain", "events_count", "mean_severity", "max_severity"])
    grouped = events.dropna(subset=["decision_domain"]).groupby("decision_domain")
    return grouped.agg(
        events_count=("event_id", "count"),
        mean_severity=("severity", "mean"),
        max_severity=("severity", "max"),
    ).reset_index()


def events_by_initiator_group(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty or "initiator_group" not in events.columns:
        return pd.DataFrame(columns=["initiator_group", "events_count", "mean_severity", "max_severity"])
    grouped = events.dropna(subset=["initiator_group"]).groupby("initiator_group")
    return grouped.agg(
        events_count=("event_id", "count"),
        mean_severity=("severity", "mean"),
        max_severity=("severity", "max"),
    ).reset_index()


def events_by_period(events: pd.DataFrame) -> pd.DataFrame:
    columns = ["period_id", "period_label", "events_count", "mean_severity", "max_severity"]
    if events.empty:
        return pd.DataFrame(columns=columns)
    data = events.copy()
    data["year"] = data["date"].dt.year
    data["period_id"] = data["year"].apply(lambda year: historical_period_for_year(int(year))["period_id"])
    data["period_label"] = data["year"].apply(lambda year: historical_period_for_year(int(year))["label"])
    grouped = data.groupby(["period_id", "period_label"], as_index=False).agg(
        events_count=("event_id", "count"),
        mean_severity=("severity", "mean"),
        max_severity=("severity", "max"),
    )
    order = {period["period_id"]: index for index, period in enumerate(HISTORICAL_PERIODS)}
    grouped["period_order"] = grouped["period_id"].map(order).fillna(999)
    return grouped.sort_values("period_order").drop(columns=["period_order"]).reset_index(drop=True)
