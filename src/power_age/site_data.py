from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from power_age.compute import add_event_summary, build_elite_year_table
from power_age.datasets import DEFAULT_DATASET_ID, dataset_paths, dataset_year_span
from power_age.events import events_by_period, filter_elite_initiated_events
from power_age.factions import add_faction_context_to_events, build_faction_type_year_table, build_faction_year_table, compute_elite_fragmentation
from power_age.load_data import load_all_data
from power_age.model_guidance import build_model_guidance_payload


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
            return None
        return value
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, pd.Timedelta):
        return value.isoformat()
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return _jsonable(value.item())
        except Exception:
            return str(value)
    return value


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    return [{key: _jsonable(value) for key, value in row.items()} for row in df.to_dict(orient="records")]


def _corr_value(frame: pd.DataFrame, x: str, y: str) -> float | None:
    if x not in frame.columns or y not in frame.columns:
        return None
    pair = frame[[x, y]].dropna()
    if len(pair) < 2:
        return None
    value = pair[x].corr(pair[y])
    if pd.isna(value):
        return None
    return round(float(value), 3)


def _corr_matrix(frame: pd.DataFrame, columns: list[str]) -> dict[str, dict[str, float | None]]:
    matrix: dict[str, dict[str, float | None]] = {}
    for x in columns:
        matrix[x] = {}
        for y in columns:
            matrix[x][y] = 1.0 if x == y else _corr_value(frame, x, y)
    return matrix


def _top_severity_events(events: pd.DataFrame, limit: int = 8) -> list[dict[str, Any]]:
    if events.empty:
        return []
    data = events.copy()
    data = data[pd.to_numeric(data.get("severity"), errors="coerce").notna()]
    if data.empty:
        return []
    data["severity"] = pd.to_numeric(data["severity"], errors="coerce")
    if "confidence" in data.columns:
        data["confidence"] = pd.to_numeric(data["confidence"], errors="coerce").fillna(0.0)
    else:
        data["confidence"] = 1.0
    data = data[data["elite_initiated"].fillna(False)] if "elite_initiated" in data.columns else data
    data = data.sort_values(["severity", "confidence", "date"], ascending=[False, False, True])
    return _records(
        data[["date", "event_id", "event_name", "confidence"]].head(limit).assign(
            date=lambda frame: frame["date"].dt.strftime("%Y-%m-%d")
        )
    )


def _low_confidence_events(events: pd.DataFrame, limit: int = 8) -> list[dict[str, Any]]:
    if events.empty or "confidence" not in events.columns:
        return []
    data = events.copy()
    data["confidence"] = pd.to_numeric(data["confidence"], errors="coerce")
    data = data[data["confidence"].notna()].sort_values(["confidence", "date"], ascending=[True, True])
    return _records(
        data[["date", "event_id", "event_name", "confidence"]].head(limit).assign(
            date=lambda frame: frame["date"].dt.strftime("%Y-%m-%d")
        )
    )


def _build_cross_tab(frame: pd.DataFrame, row_key: str, col_key: str) -> dict[str, Any]:
    if frame.empty or row_key not in frame.columns or col_key not in frame.columns:
        return {"rows": [], "cols": [], "matrix": [], "row_totals": [], "col_totals": []}

    data = frame[[row_key, col_key]].dropna().copy()
    if data.empty:
        return {"rows": [], "cols": [], "matrix": [], "row_totals": [], "col_totals": []}

    data[row_key] = data[row_key].astype(str)
    data[col_key] = data[col_key].astype(str)
    row_order = data[row_key].value_counts().index.tolist()
    col_order = data[col_key].value_counts().index.tolist()
    pivot = pd.crosstab(data[row_key], data[col_key]).reindex(index=row_order, columns=col_order, fill_value=0)
    matrix = pivot.values.tolist()
    row_totals = pivot.sum(axis=1).astype(int).tolist()
    col_totals = pivot.sum(axis=0).astype(int).tolist()
    return {
        "rows": pivot.index.astype(str).tolist(),
        "cols": pivot.columns.astype(str).tolist(),
        "matrix": matrix,
        "row_totals": row_totals,
        "col_totals": col_totals,
    }


def _build_cross_tabs(events: pd.DataFrame, factions: pd.DataFrame, faction_year: pd.DataFrame) -> dict[str, Any]:
    initiator_tab = _build_cross_tab(events, "initiator_group", "decision_domain")
    faction_tab = {"rows": [], "cols": [], "matrix": [], "row_totals": [], "col_totals": []}
    if not events.empty and not faction_year.empty and not factions.empty:
        dominant = compute_elite_fragmentation(faction_year)[["year", "dominant_faction_id"]]
        faction_types = factions[["faction_id", "faction_type"]].drop_duplicates(subset=["faction_id"])
        context = events.copy()
        context["year"] = context["date"].dt.year
        context = context.merge(dominant, on="year", how="left")
        context = context.merge(
            faction_types,
            left_on="dominant_faction_id",
            right_on="faction_id",
            how="left",
        )
        faction_tab = _build_cross_tab(context, "faction_type", "decision_domain")
    return {
        "initiator_group_x_decision_domain": initiator_tab,
        "faction_type_x_decision_domain": faction_tab,
    }


def _best_event_signal_insight(elite_corr: dict[str, dict[str, float | None]], event_corr: dict[str, dict[str, float | None]]) -> dict[str, str]:
    event_vs_severity = event_corr.get("elite_initiated_events_count", {}).get("elite_initiated_max_severity")
    event_volume = elite_corr.get("events_count", {}).get("elite_initiated_events_count")
    if event_vs_severity is not None and abs(event_vs_severity) >= 0.25:
        ru = f"Число elite-initiated событий связано с максимальной severity: r={event_vs_severity:.3f}. Это текущий событийный сигнал."
        en = f"Elite-initiated event volume is linked with max severity: r={event_vs_severity:.3f}. This is the current event signal."
        return {"key": "event_severity_signal", "ru": ru, "en": en}
    if event_volume is not None:
        ru = f"Общее число событий тесно связано с elite-initiated событиями: r={event_volume:.3f}. Для событийного слоя это главный сигнал."
        en = f"Total event volume is strongly tied to elite-initiated events: r={event_volume:.3f}. This is the main event-layer signal."
        return {"key": "event_volume_signal", "ru": ru, "en": en}
    return {
        "key": "event_signal",
        "ru": "Событийный слой пока недостаточно устойчив для уверенного сигнала.",
        "en": "The event layer is not yet stable enough for a confident signal.",
    }


def _build_insights(elite_corr: dict[str, dict[str, float | None]], event_corr: dict[str, dict[str, float | None]]) -> list[dict[str, str]]:
    ruler_vs_political = elite_corr.get("ruler_age", {}).get("ruler_political_age")
    age_vs_renewal = elite_corr.get("core_mean_age", {}).get("renewal_5y")
    ruler_vs_core_weighted = elite_corr.get("ruler_age", {}).get("core_weighted_mean_age")
    ruler_vs_core_mean = elite_corr.get("ruler_age", {}).get("core_mean_age")
    insights: list[dict[str, str]] = []

    if ruler_vs_political is not None:
        if abs(ruler_vs_political) >= 0.7:
            ru = f"Возраст правителя почти линейно связан с политическим возрастом: r={ruler_vs_political:.3f}."
            en = f"Ruler age is tightly aligned with political age: r={ruler_vs_political:.3f}."
        elif abs(ruler_vs_political) >= 0.3:
            ru = f"Возраст правителя умеренно связан с политическим возрастом: r={ruler_vs_political:.3f}."
            en = f"Ruler age is moderately aligned with political age: r={ruler_vs_political:.3f}."
        else:
            ru = f"Возраст правителя слабо связан с политическим возрастом: r={ruler_vs_political:.3f}."
            en = f"Ruler age is only weakly aligned with political age: r={ruler_vs_political:.3f}."
        insights.append({"key": "ruler_vs_political", "ru": ru, "en": en})

    if age_vs_renewal is not None:
        if age_vs_renewal <= -0.4:
            ru = f"Чем старше core elite, тем слабее обновление за 5 лет: r={age_vs_renewal:.3f}."
            en = f"Older core elite coincides with weaker 5-year renewal: r={age_vs_renewal:.3f}."
        elif age_vs_renewal < 0:
            ru = f"Старение core elite связано с более слабым обновлением за 5 лет: r={age_vs_renewal:.3f}."
            en = f"Aging core elite is linked with weaker 5-year renewal: r={age_vs_renewal:.3f}."
        else:
            ru = f"Возраст core elite не дает ожидаемого отрицательного сигнала по обновлению: r={age_vs_renewal:.3f}."
            en = f"Core elite age does not produce the expected negative renewal signal: r={age_vs_renewal:.3f}."
        insights.append({"key": "age_vs_renewal", "ru": ru, "en": en})

    if ruler_vs_core_weighted is not None and ruler_vs_core_mean is not None:
        if abs(ruler_vs_core_weighted) >= abs(ruler_vs_core_mean):
            ru = (
                "Возраст правителя сильнее совпадает со взвешенным возрастом core elite, "
                f"чем с простым средним: r={ruler_vs_core_weighted:.3f} против r={ruler_vs_core_mean:.3f}."
            )
            en = (
                "Ruler age aligns more strongly with weighted core age than with plain mean age: "
                f"r={ruler_vs_core_weighted:.3f} vs r={ruler_vs_core_mean:.3f}."
            )
        else:
            ru = (
                "Возраст правителя сильнее совпадает со средним возрастом core elite, "
                f"чем со взвешенным: r={ruler_vs_core_mean:.3f} против r={ruler_vs_core_weighted:.3f}."
            )
            en = (
                "Ruler age aligns more strongly with plain mean age than with weighted core age: "
                f"r={ruler_vs_core_mean:.3f} vs r={ruler_vs_core_weighted:.3f}."
            )
        insights.append({"key": "ruler_vs_core", "ru": ru, "en": en})

    event_signal = _best_event_signal_insight(elite_corr, event_corr)
    insights.append(event_signal)
    return insights


def _build_series_payload(elite_year: pd.DataFrame, events: pd.DataFrame) -> dict[str, Any]:
    elite_series_columns = [
        "year",
        "ruler_age",
        "ruler_political_age",
        "ruler_elite_age",
        "ruler_ruling_circle_age",
        "ruler_office_age",
        "core_elite_count",
        "core_mean_age",
        "core_median_age",
        "core_weighted_mean_age",
        "core_mean_political_age",
        "core_mean_elite_age",
        "core_share_60_plus",
        "core_share_70_plus",
        "core_age_std",
        "renewal_5y",
        "events_count",
        "max_event_severity",
        "elite_initiated_events_count",
        "elite_initiated_max_severity",
        "fragmentation_index",
    ]
    elite_series = elite_year.copy()
    for column in elite_series_columns:
        if column not in elite_series.columns:
            elite_series[column] = np.nan
    elite_series = elite_series[elite_series_columns]

    event_columns = [
        "date",
        "year",
        "event_id",
        "event_name",
        "event_type",
        "severity",
        "confidence",
        "elite_initiated",
        "decision_domain",
        "initiator_group",
    ]
    event_series = events.copy()
    event_series["year"] = event_series["date"].dt.year
    for column in event_columns:
        if column not in event_series.columns:
            event_series[column] = np.nan
    event_series = event_series[event_columns]
    event_series["date"] = event_series["date"].dt.strftime("%Y-%m-%d")
    return {
        "elite_year": _records(elite_series),
        "events": _records(event_series),
    }


def build_site_data_payload(dataset_id: str = DEFAULT_DATASET_ID) -> dict[str, Any]:
    data = load_all_data(dataset_paths(dataset_id).root)
    periods = data["periods"]
    start_year, end_year = dataset_year_span(data, dataset_id)
    raw_path = dataset_paths(dataset_id).raw
    available_files = {path.name for path in raw_path.glob("*") if path.is_file()}
    country_series = data["persons"].get("country_label") if "country_label" in data["persons"].columns else None
    country = (
        str(country_series.dropna().iloc[0])
        if country_series is not None and not country_series.dropna().empty
        else dataset_id
    )
    elite_year = build_elite_year_table(
        data["persons"],
        data["positions"],
        data["political_entries"],
        start_year=start_year,
        end_year=end_year,
    )
    elite_year = add_event_summary(elite_year, data["events"])

    faction_year = build_faction_year_table(
        data["persons"],
        data["positions"],
        data["political_entries"],
        data["factions"],
        data["person_factions"],
        start_year=start_year,
        end_year=end_year,
        min_confidence=0.5,
    )
    if not faction_year.empty:
        fragmentation = compute_elite_fragmentation(faction_year)
        elite_year = elite_year.merge(fragmentation, on="year", how="left")
    else:
        elite_year["fragmentation_index"] = np.nan

    faction_type_year = build_faction_type_year_table(faction_year, data["factions"])
    elite_year = elite_year.merge(
        faction_type_year.groupby("year", as_index=False)["normalized_power_share"].sum().rename(
            columns={"normalized_power_share": "faction_type_power_share"}
        ),
        on="year",
        how="left",
    )

    elite_events = filter_elite_initiated_events(data["events"], min_confidence=0.5)
    event_periods = events_by_period(data["events"], periods)
    elite_event_periods = events_by_period(elite_events, periods)
    period_summary = event_periods if not event_periods.empty else elite_event_periods

    top_severity_5 = _top_severity_events(elite_events)
    low_confidence = _low_confidence_events(elite_events)

    if not faction_year.empty:
        events_with_context = add_faction_context_to_events(data["events"], faction_year)
        if "dominant_faction_id" in events_with_context.columns and not data["factions"].empty:
            dominant_types = data["factions"][["faction_id", "faction_type"]].drop_duplicates(subset=["faction_id"])
            events_with_context = events_with_context.merge(
                dominant_types,
                left_on="dominant_faction_id",
                right_on="faction_id",
                how="left",
                suffixes=("", "_dominant"),
            )
    else:
        events_with_context = data["events"].copy()

    cross_tabs = _build_cross_tabs(data["events"], data["factions"], faction_year)

    elite_columns = [
        "ruler_age",
        "ruler_political_age",
        "core_mean_age",
        "core_weighted_mean_age",
        "core_share_60_plus",
        "core_share_70_plus",
        "renewal_5y",
        "events_count",
        "elite_initiated_events_count",
        "elite_initiated_max_severity",
        "fragmentation_index",
    ]
    faction_columns = [
        "normalized_power_share",
        "mean_age",
        "weighted_mean_age",
        "mean_political_age",
        "weighted_mean_political_age",
        "members_count",
        "raw_power_share",
    ]
    event_columns = [
        "core_mean_age",
        "core_weighted_mean_age",
        "renewal_5y",
        "fragmentation_index",
        "elite_initiated_events_count",
        "elite_initiated_max_severity",
    ]
    elite_corr = _corr_matrix(elite_year, elite_columns)
    faction_corr = _corr_matrix(faction_year, faction_columns)
    event_corr = _corr_matrix(elite_year, event_columns)

    meta = {
        "years": {"start": int(start_year), "end": int(end_year)},
        "counts": {
            "persons": int(len(data["persons"])),
            "events": int(len(data["events"])),
            "elite_events": int(len(elite_events)),
            "factions": int(len(data["factions"])),
            "person_factions": int(len(data["person_factions"])),
        },
    }

    return {
        "meta": meta,
        "insights": _build_insights(elite_corr, event_corr),
        "model_guidance": build_model_guidance_payload(
            dataset_id,
            data,
            country,
            start_year,
            end_year,
            available_files,
        ),
        "correlations": {
            "elite": elite_corr,
            "faction": faction_corr,
            "event": event_corr,
        },
        "cross_tabs": cross_tabs,
        "periods": _records(periods),
        "event_summaries": {
            "periods": _records(period_summary),
            "top_severity_5": top_severity_5,
            "low_confidence": low_confidence,
        },
        "series": _build_series_payload(elite_year, data["events"]),
    }


def write_site_data(dataset_id: str = DEFAULT_DATASET_ID, docs_root: str | Path | None = None) -> tuple[Path, Path]:
    if docs_root is None:
        docs_root = Path(__file__).resolve().parents[2] / "docs" / "data"
    docs_root = Path(docs_root)
    payload = build_site_data_payload(dataset_id)
    if dataset_id == DEFAULT_DATASET_ID:
        dataset_dir = docs_root
    else:
        dataset_dir = docs_root / dataset_id
        dataset_dir.mkdir(parents=True, exist_ok=True)

    site_path = dataset_dir / "site-data.json"
    series_path = dataset_dir / "series-data.json"
    site_payload = {key: value for key, value in payload.items() if key != "series"}
    series_payload = payload["series"]

    site_path.write_text(json.dumps(site_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    series_path.write_text(json.dumps(series_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return site_path, series_path
