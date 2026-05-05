from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from power_age.compute import add_event_summary, build_elite_year_table
from power_age.events import filter_elite_initiated_events
from power_age.factions import build_faction_year_table, compute_elite_fragmentation


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL_FAMILIES_PATH = REPO_ROOT / "codex_country_model_extension" / "model_families.yml"
DEFAULT_PRIORS_PATH = REPO_ROOT / "codex_country_model_extension" / "country_period_model_priors.yml"


MODEL_IDS = [
    "institutional_domain_crisis_model",
    "gerontocracy_succession_model",
    "dynastic_succession_model",
    "party_congress_turnover_model",
    "revolutionary_generation_model",
    "security_state_faction_model",
    "developmental_bureaucratic_model",
]


@dataclass(frozen=True)
class ModelFamily:
    model_id: str
    label: str
    description: str
    best_for: list[str] = field(default_factory=list)
    weak_for: list[str] = field(default_factory=list)
    required_data: list[str] = field(default_factory=list)
    recommended_data: list[str] = field(default_factory=list)
    recommended_metrics: list[str] = field(default_factory=list)
    forecast_features: list[str] = field(default_factory=list)
    forecast_targets: list[str] = field(default_factory=list)
    selection_signals: list[str] = field(default_factory=list)
    interpretation_template: str = ""
    forecast_template: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CountryPeriodPrior:
    country: str
    start_year: int
    end_year: int
    preferred_models: list[str] = field(default_factory=list)
    secondary_models: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass(frozen=True)
class ModelSelectionResult:
    country: str
    period: dict[str, int]
    recommended_model: str
    secondary_models: list[str]
    confidence: float
    rationale: str
    supporting_signals: list[str]
    missing_data_warnings: list[str]
    recommended_next_features: list[str]
    forecast_guidance: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ForecastGuidance:
    forecast_type: str
    forecast_horizon_years: int
    target: str
    baseline_assessment: str
    upside_scenario: str
    downside_scenario: str
    key_indicators_to_watch: list[str]
    features_used: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _strip_comments(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        stripped = raw.rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        lines.append(stripped)
    return lines


def _parse_scalar(text: str) -> Any:
    value = text.strip()
    if value == "":
        return None
    lowered = value.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return ast.literal_eval(value)
    except Exception:
        pass
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value.strip("\"'")


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines: list[str], index: int, indent: int) -> tuple[Any, int]:
    items: list[Any] = []
    mapping: dict[str, Any] = {}
    mode: str | None = None

    while index < len(lines):
        line = lines[index]
        current_indent = _line_indent(line)
        if current_indent < indent:
            break
        if current_indent > indent:
            break

        content = line[indent:]
        if content.startswith("- "):
            if mode is None:
                mode = "list"
            elif mode != "list":
                break

            item_text = content[2:].strip()
            index += 1
            if not item_text:
                value, index = _parse_block(lines, index, indent + 2)
                items.append(value)
                continue

            if ":" in item_text and not item_text.startswith(("[", "{", "\"", "'")):
                key, raw_value = item_text.split(":", 1)
                item: dict[str, Any] = {key.strip(): _parse_scalar(raw_value)}
                if index < len(lines):
                    next_indent = _line_indent(lines[index])
                    if next_indent > indent:
                        nested, index = _parse_block(lines, index, next_indent)
                        if isinstance(nested, dict):
                            item.update(nested)
                items.append(item)
                continue

            items.append(_parse_scalar(item_text))
            continue

        if mode is None:
            mode = "dict"
        elif mode != "dict":
            break

        if ":" not in content:
            break
        key, raw_value = content.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        index += 1

        if raw_value:
            mapping[key] = _parse_scalar(raw_value)
            continue

        if index >= len(lines):
            mapping[key] = None
            continue

        next_indent = _line_indent(lines[index])
        if next_indent <= indent:
            mapping[key] = None
            continue

        value, index = _parse_block(lines, index, next_indent)
        mapping[key] = value

    if mode == "list":
        return items, index
    return mapping, index


def _load_yaml_like(path: str | Path) -> Any:
    text = Path(path).read_text(encoding="utf-8")
    lines = _strip_comments(text)
    if not lines:
        return {}
    value, _ = _parse_block(lines, 0, 0)
    return value


def _ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def load_model_families(path: str | Path = DEFAULT_MODEL_FAMILIES_PATH) -> dict[str, ModelFamily]:
    raw = _load_yaml_like(path)
    families: dict[str, ModelFamily] = {}
    family_block = raw.get("model_families", {}) if isinstance(raw, dict) else {}
    for model_id, payload in family_block.items():
        if not isinstance(payload, dict):
            continue
        families[model_id] = ModelFamily(
            model_id=model_id,
            label=str(payload.get("label", model_id)),
            description=str(payload.get("description", "")),
            best_for=_ensure_list(payload.get("best_for")),
            weak_for=_ensure_list(payload.get("weak_for")),
            required_data=_ensure_list(payload.get("required_data")),
            recommended_data=_ensure_list(payload.get("recommended_data")),
            recommended_metrics=_ensure_list(payload.get("recommended_metrics")),
            forecast_features=_ensure_list(payload.get("forecast_features")),
            forecast_targets=_ensure_list(payload.get("forecast_targets")),
            selection_signals=_ensure_list(payload.get("selection_signals")),
            interpretation_template=str(payload.get("interpretation_template", "")),
            forecast_template=str(payload.get("forecast_template", "")),
            warnings=_ensure_list(payload.get("warnings")),
        )
    return families


def load_country_period_priors(path: str | Path = DEFAULT_PRIORS_PATH) -> list[CountryPeriodPrior]:
    raw = _load_yaml_like(path)
    priors: list[CountryPeriodPrior] = []
    if not isinstance(raw, dict):
        return priors

    for country, periods in raw.items():
        if not isinstance(periods, list):
            continue
        for entry in periods:
            if not isinstance(entry, dict):
                continue
            start_year = entry.get("start_year")
            end_year = entry.get("end_year")
            if start_year is None or end_year is None:
                continue
            priors.append(
                CountryPeriodPrior(
                    country=str(country),
                    start_year=int(start_year),
                    end_year=int(end_year),
                    preferred_models=_ensure_list(entry.get("preferred_models")),
                    secondary_models=_ensure_list(entry.get("secondary_models")),
                    rationale=str(entry.get("rationale", "")),
                )
            )
    return priors


def _normalize_country_name(country: str) -> str:
    country = country.strip().lower()
    aliases = {
        "united states": "usa",
        "united states of america": "usa",
        "u.s.a.": "usa",
        "us": "usa",
        "soviet union": "ussr",
        "russian federation": "russia",
        "kingdom of saudi arabia": "saudi arabia",
    }
    return aliases.get(country, country)


def _country_matches(country: str, prior_country: str) -> bool:
    normalized = _normalize_country_name(country)
    prior = _normalize_country_name(prior_country)
    return normalized == prior or normalized in prior or prior in normalized


def _to_year(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _safe_mean(series: pd.Series | list[float]) -> float | None:
    if isinstance(series, list):
        data = pd.Series(series)
    else:
        data = series
    data = pd.to_numeric(data, errors="coerce").dropna()
    if data.empty:
        return None
    return float(data.mean())


def _safe_corr(frame: pd.DataFrame, x: str, y: str) -> float | None:
    if frame.empty or x not in frame.columns or y not in frame.columns:
        return None
    pair = frame[[x, y]].dropna()
    if len(pair) < 2:
        return None
    value = pair[x].corr(pair[y])
    if pd.isna(value):
        return None
    return float(value)


def _contains_any(values: Iterable[str], needles: list[str]) -> bool:
    normalized = [str(value).lower() for value in values if value is not None]
    return any(any(needle in value for needle in needles) for value in normalized)


def _keyword_series_contains(series: pd.Series, needles: list[str]) -> pd.Series:
    if series.empty:
        return pd.Series(dtype=bool)
    text = series.fillna("").astype(str).str.lower()
    pattern = "|".join(re.escape(needle) for needle in needles)
    return text.str.contains(pattern, regex=True, na=False)


def _build_country_file_set(data_dir: str | Path) -> set[str]:
    root = Path(data_dir)
    raw = root / "raw"
    processed = root / "processed"
    files = {path.name for path in raw.glob("*") if path.is_file()}
    files.update(path.name for path in processed.glob("*") if path.is_file())
    return files


def _yearly_turnover_proxy(elite_year: pd.DataFrame) -> float | None:
    if elite_year.empty or "renewal_5y" not in elite_year.columns:
        return None
    return _safe_mean(elite_year["renewal_5y"])


def _event_domain_richness(events: pd.DataFrame) -> int:
    if events.empty or "decision_domain" not in events.columns:
        return 0
    return int(events["decision_domain"].dropna().astype(str).nunique())


def _institution_richness(positions: pd.DataFrame) -> int:
    if positions.empty or "institution" not in positions.columns:
        return 0
    return int(positions["institution"].dropna().astype(str).nunique())


def _faction_layer_available(data: dict[str, pd.DataFrame]) -> bool:
    factions = data.get("factions", pd.DataFrame())
    person_factions = data.get("person_factions", pd.DataFrame())
    return not factions.empty and not person_factions.empty


def _build_elite_snapshot(
    data: dict[str, pd.DataFrame],
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    elite_year = build_elite_year_table(
        data["persons"],
        data["positions"],
        data["political_entries"],
        start_year=start_year,
        end_year=end_year,
    )
    return add_event_summary(elite_year, data["events"])


def _build_faction_snapshot(
    data: dict[str, pd.DataFrame],
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    if data.get("factions", pd.DataFrame()).empty or data.get("person_factions", pd.DataFrame()).empty:
        return pd.DataFrame()
    return build_faction_year_table(
        data["persons"],
        data["positions"],
        data["political_entries"],
        data["factions"],
        data["person_factions"],
        start_year=start_year,
        end_year=end_year,
        min_confidence=0.5,
    )


def _position_share(
    positions: pd.DataFrame,
    keywords: list[str],
    weight_col: str = "influence_weight",
) -> float | None:
    if positions.empty:
        return None
    if "institution" not in positions.columns and "position" not in positions.columns:
        return None
    text = pd.Series("", index=positions.index)
    if "institution" in positions.columns:
        text = text.astype(str) + " " + positions["institution"].fillna("").astype(str)
    if "position" in positions.columns:
        text = text.astype(str) + " " + positions["position"].fillna("").astype(str)
    mask = _keyword_series_contains(text, keywords)
    weights = pd.to_numeric(positions.get(weight_col, pd.Series(1.0, index=positions.index)), errors="coerce").fillna(1.0)
    total = float(weights.sum())
    if total == 0:
        return None
    return float(weights[mask].sum() / total)


def _event_count_with_keywords(events: pd.DataFrame, keywords: list[str]) -> int:
    if events.empty:
        return 0
    columns = [column for column in ["event_type", "event_name", "notes", "decision_domain", "initiator_group"] if column in events.columns]
    if not columns:
        return 0
    text = events[columns].fillna("").astype(str).agg(" ".join, axis=1)
    mask = _keyword_series_contains(text, keywords)
    return int(mask.sum())


def _feature_presence_notes(metrics: dict[str, Any], available_files: set[str]) -> list[str]:
    notes: list[str] = []
    if "yearly_context.csv" not in available_files:
        notes.append("yearly_context.csv is absent, so party-control and crisis flags are inferred indirectly.")
    if "factions.csv" not in available_files or "person_factions.csv" not in available_files:
        notes.append("Faction-layer features are absent, so selection relies more heavily on age, institutions, and event structure.")
    if "periods.csv" not in available_files:
        notes.append("periods.csv is absent, so periodization is weaker and priors matter more.")
    if metrics.get("corr_core_elite_age_elite_events") is None:
        notes.append("core elite age versus elite-initiated event correlation is unavailable or too sparse.")
    return notes


def extract_country_period_metrics(
    data: dict[str, pd.DataFrame],
    start_year: int,
    end_year: int,
) -> dict[str, Any]:
    elite_year = _build_elite_snapshot(data, start_year, end_year)
    faction_year = _build_faction_snapshot(data, start_year, end_year)
    events = data["events"].copy()
    elite_events = filter_elite_initiated_events(events, min_confidence=0.5)

    elite_period = elite_year[
        (elite_year["year"] >= start_year) & (elite_year["year"] <= end_year)
    ].copy()
    events_period = events[
        (events["date"].dt.year >= start_year) & (events["date"].dt.year <= end_year)
    ].copy()
    elite_events_period = elite_events[
        (elite_events["date"].dt.year >= start_year) & (elite_events["date"].dt.year <= end_year)
    ].copy()

    corr_core_elite_age_elite_events = _safe_corr(
        elite_period,
        "core_mean_age",
        "elite_initiated_events_count",
    )
    corr_core_weighted_age_elite_events = _safe_corr(
        elite_period,
        "core_weighted_mean_age",
        "elite_initiated_events_count",
    )

    share_70_plus = _safe_mean(elite_period["core_share_70_plus"]) if "core_share_70_plus" in elite_period.columns else None
    turnover_rate = _yearly_turnover_proxy(elite_period)
    leader_age = _safe_mean(elite_period["ruler_age"]) if "ruler_age" in elite_period.columns else None
    ruling_circle_age_mean = (
        _safe_mean(elite_period["ruler_ruling_circle_age"]) if "ruler_ruling_circle_age" in elite_period.columns else None
    )
    core_age_mean = _safe_mean(elite_period["core_mean_age"]) if "core_mean_age" in elite_period.columns else None
    high_severity_rate = None
    if not elite_events_period.empty and "severity" in elite_events_period.columns:
        severity = pd.to_numeric(elite_events_period["severity"], errors="coerce")
        high_severity_rate = float((severity >= 4).mean()) if not severity.dropna().empty else None

    metrics = {
        "corr_core_elite_age_elite_events": corr_core_elite_age_elite_events,
        "corr_core_weighted_age_elite_events": corr_core_weighted_age_elite_events,
        "core_mean_age_mean": core_age_mean,
        "leader_age_mean": leader_age,
        "ruling_circle_age_mean": ruling_circle_age_mean,
        "share_70_plus": share_70_plus,
        "elite_turnover_rate": turnover_rate,
        "high_severity_event_rate": high_severity_rate,
        "event_count": int(len(events_period)),
        "elite_initiated_event_count": int(len(elite_events_period)),
        "event_domain_richness": _event_domain_richness(elite_events_period),
        "institution_richness": _institution_richness(data["positions"]),
        "faction_layer_available": _faction_layer_available(data),
        "faction_mean_dominant_share": (
            float(
                compute_elite_fragmentation(faction_year)["dominant_faction_share"].dropna().mean()
            )
            if not faction_year.empty and "dominant_faction_share" in compute_elite_fragmentation(faction_year).columns
            else None
        ),
        "security_elite_share": _position_share(
            data["positions"],
            ["security", "military", "intelligence", "siloviki", "irgc", "defense", "coercive"],
        ),
        "judicial_elite_share": _position_share(
            data["positions"],
            ["judicial", "court", "supreme court", "judge", "prosecutor"],
        ),
        "finance_elite_share": _position_share(
            data["positions"],
            ["finance", "central bank", "treasury", "economic", "budget"],
        ),
        "technocrat_share": _position_share(
            data["positions"],
            ["technocrat", "bureaucrat", "economic", "planning", "development", "ministry"],
        ),
        "royal_elite_share": _position_share(
            data["positions"],
            ["royal", "king", "queen", "prince", "crown prince", "dynasty", "house of"],
        ),
        "party_congress_signal": max(
            _event_count_with_keywords(events_period, ["congress", "politburo", "central committee", "standing committee"]),
            _event_count_with_keywords(data.get("periods", pd.DataFrame()), ["congress", "politburo", "central committee"]),
        ),
        "revolutionary_generation_signal": max(
            _event_count_with_keywords(events_period, ["revolution", "founding", "liberation", "old guard", "founder"]),
            _position_share(data["positions"], ["revolution", "founding", "liberation", "old guard"], weight_col="influence_weight")
            or 0.0,
        ),
        "succession_signal_count": _event_count_with_keywords(
            events_period,
            ["succession", "heir", "transition", "replacement", "incapacitation", "death", "abdication"],
        ),
        "purge_event_count": _event_count_with_keywords(
            events_period,
            ["purge", "crackdown", "repression", "coup", "assassination", "arrest"],
        ),
        "war_event_count": _event_count_with_keywords(
            events_period,
            ["war", "battle", "invasion", "intervention", "mobilization", "military"],
        ),
        "protest_event_count": _event_count_with_keywords(
            events_period,
            ["protest", "demonstration", "strike", "riot", "uprising"],
        ),
        "reform_event_count": _event_count_with_keywords(
            events_period,
            ["reform", "liberalization", "economic reform", "policy shift", "opening"],
        ),
        "congress_cycle": _event_count_with_keywords(
            events_period,
            ["congress", "party congress", "party congress"],
        ),
        "labels": {
            "country_label": data["persons"].get("country_label"),
            "positions_columns": list(data["positions"].columns),
            "event_columns": list(events.columns),
        },
    }
    if not faction_year.empty and "normalized_power_share" in faction_year.columns:
        dominant_share = faction_year.groupby("year")["normalized_power_share"].max().dropna().mean()
        metrics["faction_dominant_share"] = float(dominant_share) if pd.notna(dominant_share) else None
    else:
        metrics["faction_dominant_share"] = None

    return metrics


def _family_score_from_priors(
    model_id: str,
    country: str,
    start_year: int,
    end_year: int,
    priors: list[CountryPeriodPrior],
) -> tuple[float, list[str]]:
    score = 0.0
    signals: list[str] = []
    for prior in priors:
        if not _country_matches(country, prior.country):
            continue
        if end_year < prior.start_year or start_year > prior.end_year:
            continue
        if model_id in prior.preferred_models:
            score += 3.5
            signals.append(f"Prior match: {prior.country} {prior.start_year}-{prior.end_year} prefers {model_id}.")
        if model_id in prior.secondary_models:
            score += 1.5
            signals.append(f"Prior match: {prior.country} {prior.start_year}-{prior.end_year} marks {model_id} as secondary.")
    return score, signals


def _score_model_family(model_id: str, metrics: dict[str, Any], country: str) -> tuple[float, list[str]]:
    score = 0.0
    signals: list[str] = []

    def add(condition: bool, points: float, message: str) -> None:
        nonlocal score
        if condition:
            score += points
            signals.append(message)

    if model_id == "institutional_domain_crisis_model":
        corr = metrics.get("corr_core_elite_age_elite_events")
        domain_richness = metrics.get("event_domain_richness", 0)
        institution_richness = metrics.get("institution_richness", 0)
        add(corr is not None and abs(float(corr)) < 0.15, 2.2, "Core elite age is weakly correlated with elite-initiated events.")
        add(domain_richness >= 4, 1.1, "Event data contains rich decision-domain structure.")
        add(institution_richness >= 6, 1.0, "Institutional layer is broad enough for an institutional model.")
        add(float(metrics.get("high_severity_event_rate") or 0.0) >= 0.25, 0.7, "High-severity events are frequent enough to justify crisis framing.")
        add(float(metrics.get("finance_elite_share") or 0.0) > 0.05, 0.2, "Finance layer is available.")
        add(float(metrics.get("judicial_elite_share") or 0.0) > 0.05, 0.2, "Judicial layer is available.")
        add(float(metrics.get("security_elite_share") or 0.0) > 0.05, 0.2, "Security layer is available.")

    elif model_id == "gerontocracy_succession_model":
        leader_age = metrics.get("leader_age_mean")
        ruling_circle_age = metrics.get("ruling_circle_age_mean")
        share_70_plus = metrics.get("share_70_plus")
        turnover = metrics.get("elite_turnover_rate")
        succession = metrics.get("succession_signal_count", 0)
        add(leader_age is not None and float(leader_age) >= 70, 1.8, "Leader age is in a gerontocratic range.")
        add(ruling_circle_age is not None and float(ruling_circle_age) >= 65, 1.4, "Ruling-circle age is high.")
        add(share_70_plus is not None and float(share_70_plus) >= 0.25, 1.4, "The share of elders in core elite is high.")
        add(turnover is not None and float(turnover) <= 0.25, 1.6, "Elite renewal is low.")
        add(float(succession) > 0, 0.9, "Succession-related signals are present.")

    elif model_id == "dynastic_succession_model":
        royal_share = metrics.get("royal_elite_share")
        succession = metrics.get("succession_signal_count", 0)
        add(royal_share is not None and float(royal_share) > 0.1, 2.0, "Royal or dynastic positions are present.")
        add(float(metrics.get("faction_dominant_share") or 0.0) >= 0.4, 0.8, "Factional concentration is consistent with dynastic consolidation.")
        add(float(succession) > 0, 1.1, "Succession signals are present.")
        add(float(metrics.get("security_elite_share") or 0.0) > 0.05, 0.5, "Security elite share is non-trivial.")

    elif model_id == "party_congress_turnover_model":
        congress = metrics.get("party_congress_signal", 0)
        turnover = metrics.get("elite_turnover_rate")
        technocrat = metrics.get("technocrat_share")
        add(float(congress) > 0, 2.2, "Party-congress or cycle signals are present.")
        add(turnover is not None and float(turnover) >= 0.15, 0.7, "Renewal is visible around cycle boundaries.")
        add(technocrat is not None and float(technocrat) > 0.05, 0.7, "Technocratic elite is present.")
        add(float(metrics.get("faction_dominant_share") or 0.0) >= 0.25, 0.6, "Faction balance is visible.")

    elif model_id == "revolutionary_generation_model":
        rev = metrics.get("revolutionary_generation_signal", 0)
        security = metrics.get("security_elite_share")
        protest = metrics.get("protest_event_count", 0)
        add(float(rev) > 0, 2.0, "Revolutionary/founding-generation signals are present.")
        add(security is not None and float(security) > 0.1, 1.0, "Security-apparatus influence is non-trivial.")
        add(float(protest) > 0, 0.8, "Protest pressure is present.")
        add(float(metrics.get("succession_signal_count") or 0) > 0, 0.6, "Succession pressure is present.")

    elif model_id == "security_state_faction_model":
        security = metrics.get("security_elite_share")
        war = metrics.get("war_event_count", 0)
        purge = metrics.get("purge_event_count", 0)
        protest = metrics.get("protest_event_count", 0)
        add(security is not None and float(security) >= 0.15, 2.2, "Security elite share is high.")
        add(float(war) > 0, 1.0, "War or military pressure signals are present.")
        add(float(purge) > 0, 1.1, "Purge or repression signals are present.")
        add(float(protest) > 0, 0.7, "Protest signals are present.")
        add(float(metrics.get("faction_dominant_share") or 0.0) >= 0.3, 0.8, "Faction concentration is substantial.")

    elif model_id == "developmental_bureaucratic_model":
        technocrat = metrics.get("technocrat_share")
        finance = metrics.get("finance_elite_share")
        reform = metrics.get("reform_event_count", 0)
        add(technocrat is not None and float(technocrat) > 0.1, 2.1, "Technocratic/bureaucratic positions are present.")
        add(finance is not None and float(finance) > 0.05, 1.0, "Finance and economic ministries are visible.")
        add(float(reform) > 0, 1.0, "Reform-package signals are present.")
        add(float(metrics.get("elite_turnover_rate") or 0.0) >= 0.1, 0.5, "Some elite turnover is present.")

    return score, signals


def _missing_feature_warnings(model_family: ModelFamily, available_files: set[str], metrics: dict[str, Any]) -> list[str]:
    warnings = _feature_presence_notes(metrics, available_files)
    for required in model_family.required_data:
        if required not in available_files:
            warnings.append(f"Missing required file for ideal model fit: {required}.")
    return warnings


def _recommended_next_features(model_id: str, metrics: dict[str, Any], available_files: set[str]) -> list[str]:
    candidates = {
        "institutional_domain_crisis_model": [
            "yearly_context.csv with party-control, divided-government, and crisis flags",
            "institution-level decision-domain classification",
            "war, emergency, and institutional-control indicators",
        ],
        "gerontocracy_succession_model": [
            "succession-event annotations",
            "leader and ruling-circle age series by year",
            "lagged turnover indicators",
        ],
        "dynastic_succession_model": [
            "crown-prince and heir-role annotations",
            "royal-branch faction labels",
            "generational-transition markers",
        ],
        "party_congress_turnover_model": [
            "congress-cycle periodization",
            "politburo and central-committee membership by year",
            "retirement-norm and norm-breaking flags",
        ],
        "revolutionary_generation_model": [
            "founding-generation membership flags",
            "old-guard replacement markers",
            "security-apparatus influence by year",
        ],
        "security_state_faction_model": [
            "security-faction labels",
            "purge and repression event tags",
            "military/intelligence network mapping",
        ],
        "developmental_bureaucratic_model": [
            "bureaucratic and technocratic faction labels",
            "economic-ministry and central-bank share series",
            "policy-package and reform indicators",
        ],
    }
    output = list(candidates.get(model_id, []))
    if not metrics.get("faction_layer_available"):
        output.append("faction-layer files if they are available for this country-period")
    if "yearly_context.csv" not in available_files:
        output.append("yearly_context.csv for better crisis and control signals")
    return output


def generate_forecast_guidance(
    country: str,
    period: dict[str, int],
    selected_model: ModelFamily,
    metrics: dict[str, Any],
    recent_trends: dict[str, Any] | None = None,
) -> ForecastGuidance:
    recent_trends = recent_trends or {}
    forecast_target = selected_model.forecast_targets[0] if selected_model.forecast_targets else "elite_initiated_event_count_next_period"
    warnings = list(selected_model.warnings)
    if metrics.get("event_domain_richness", 0) == 0:
        warnings.append("Decision-domain data is sparse, so scenario quality is limited.")
    if metrics.get("elite_turnover_rate") is None:
        warnings.append("Turnover is estimated indirectly or is missing.")

    baseline = "Moderate scenario pressure"
    upside = "The favorable scenario is orderly adjustment with limited disruption."
    downside = "The adverse scenario is sharper than baseline adjustment, with a higher-risk cluster of events."
    indicators = list(selected_model.forecast_features)
    features_used = list(dict.fromkeys(selected_model.recommended_metrics + selected_model.forecast_features))

    if selected_model.model_id == "institutional_domain_crisis_model":
        corr = metrics.get("corr_core_elite_age_elite_events")
        bucket = "moderate"
        if corr is not None and abs(float(corr)) < 0.15:
            bucket = "low"
        if float(metrics.get("high_severity_event_rate") or 0.0) >= 0.35:
            bucket = "elevated"
        if float(metrics.get("event_domain_richness") or 0.0) >= 4:
            baseline = f"{bucket.capitalize()} scenario pressure: crisis and domain structure matter more than age."
        else:
            baseline = f"{bucket.capitalize()} scenario pressure: institutions dominate interpretation, but data are sparse."
        upside = "Upside: institutional control and crisis containment keep event severity bounded."
        downside = "Downside: crisis concentration, divided control, or security/finance/judicial conflict raises event risk."

    elif selected_model.model_id == "gerontocracy_succession_model":
        score = (
            0.25 * float(metrics.get("leader_age_mean") or 0.0)
            + 0.20 * float(metrics.get("ruling_circle_age_mean") or 0.0)
            + 20.0 * float(metrics.get("share_70_plus") or 0.0)
            + 25.0 * (1.0 - float(metrics.get("elite_turnover_rate") or 0.0))
        )
        if score >= 70:
            bucket = "high"
        elif score >= 55:
            bucket = "elevated"
        elif score >= 40:
            bucket = "moderate"
        else:
            bucket = "low"
        baseline = f"{bucket.capitalize()} succession pressure: aging, low renewal, and lagged succession effects deserve attention."
        upside = "Upside: orderly succession produces managed transition and a short-lived reform window."
        downside = "Downside: unresolved succession increases the odds of crisis, delay, or post-transition purge."

    elif selected_model.model_id == "dynastic_succession_model":
        royal_share = float(metrics.get("royal_elite_share") or 0.0)
        bucket = "moderate"
        if royal_share > 0.15:
            bucket = "high"
        elif royal_share > 0.05:
            bucket = "elevated"
        baseline = f"{bucket.capitalize()} dynastic succession pressure: heir consolidation and branch balance are the key variables."
        upside = "Upside: heir consolidation reduces factional uncertainty and allows managed reform."
        downside = "Downside: succession ambiguity or branch displacement raises purge and displacement risk."

    elif selected_model.model_id == "party_congress_turnover_model":
        congress = float(metrics.get("party_congress_signal") or 0.0)
        turnover = float(metrics.get("elite_turnover_rate") or 0.0)
        bucket = "moderate"
        if congress > 0 and turnover >= 0.2:
            bucket = "elevated"
        baseline = f"{bucket.capitalize()} congress-cycle pressure: turnover and norm changes matter more than annual age averages."
        upside = "Upside: the next cycle is orderly and promotes predictable retirement and promotion."
        downside = "Downside: norm-breaking centralization or central-committee conflict shifts policy unexpectedly."

    elif selected_model.model_id == "revolutionary_generation_model":
        rev = float(metrics.get("revolutionary_generation_signal") or 0.0)
        bucket = "moderate"
        if rev > 0:
            bucket = "elevated"
        baseline = f"{bucket.capitalize()} generational pressure: the aging and replacement of the founding cohort shapes the next period."
        upside = "Upside: generational replacement is controlled and keeps the security apparatus aligned."
        downside = "Downside: old-guard blockage or replacement shock raises repression and succession risk."

    elif selected_model.model_id == "security_state_faction_model":
        security = float(metrics.get("security_elite_share") or 0.0)
        purge = float(metrics.get("purge_event_count") or 0.0)
        bucket = "moderate"
        if security >= 0.2 or purge > 0:
            bucket = "elevated"
        baseline = f"{bucket.capitalize()} security-faction pressure: coercive institutions and faction closure dominate the scenario."
        upside = "Upside: security consolidation remains stable and keeps spillovers contained."
        downside = "Downside: faction conflict, repression, or war pressure creates a higher-risk event cluster."

    elif selected_model.model_id == "developmental_bureaucratic_model":
        technocrat = float(metrics.get("technocrat_share") or 0.0)
        reform = float(metrics.get("reform_event_count") or 0.0)
        bucket = "moderate"
        if technocrat > 0.12 or reform > 0:
            bucket = "elevated"
        baseline = f"{bucket.capitalize()} bureaucratic-reform pressure: technocratic turnover and policy packages matter more than age alone."
        upside = "Upside: technocratic renewal keeps reform execution smooth and contained."
        downside = "Downside: reform paralysis or economic stress shifts the system toward stagnation."

    if recent_trends:
        trend_parts = []
        for key in ["core_mean_age", "elite_turnover_rate", "high_severity_event_rate", "security_elite_share"]:
            if key in recent_trends and recent_trends[key] is not None:
                trend_parts.append(f"{key}={recent_trends[key]}")
        if trend_parts:
            baseline += " Recent trend context: " + ", ".join(trend_parts) + "."

    return ForecastGuidance(
        forecast_type="scenario",
        forecast_horizon_years=5,
        target=forecast_target,
        baseline_assessment=baseline,
        upside_scenario=upside,
        downside_scenario=downside,
        key_indicators_to_watch=indicators,
        features_used=features_used,
        warnings=warnings,
    )


def _score_to_confidence(top_score: float, second_score: float, data_quality: float) -> float:
    margin = max(top_score - second_score, 0.0)
    confidence = 0.35 + 0.08 * top_score + 0.1 * margin + 0.15 * data_quality
    return round(_clamp(confidence, 0.0, 0.95), 2)


def _quality_score(metrics: dict[str, Any]) -> float:
    keys = [
        "corr_core_elite_age_elite_events",
        "elite_turnover_rate",
        "event_domain_richness",
        "institution_richness",
        "security_elite_share",
        "technocrat_share",
        "royal_elite_share",
    ]
    present = sum(1 for key in keys if metrics.get(key) is not None)
    return present / len(keys)


def select_model_family(
    country: str,
    start_year: int,
    end_year: int,
    metrics: dict[str, Any],
    available_files: Iterable[str],
) -> ModelSelectionResult:
    families = load_model_families()
    priors = load_country_period_priors()
    files = {str(item) for item in available_files}

    scores: dict[str, float] = {}
    signals_by_model: dict[str, list[str]] = {}

    for model_id in MODEL_IDS:
        family = families.get(model_id)
        if family is None:
            continue
        prior_score, prior_signals = _family_score_from_priors(model_id, country, start_year, end_year, priors)
        observed_score, observed_signals = _score_model_family(model_id, metrics, country)
        scores[model_id] = prior_score + observed_score
        signals_by_model[model_id] = prior_signals + observed_signals

        if model_id == "institutional_domain_crisis_model" and metrics.get("corr_core_elite_age_elite_events") is not None:
            if abs(float(metrics["corr_core_elite_age_elite_events"])) < 0.15:
                signals_by_model[model_id].append("Weak core elite age / elite-initiated event correlation supports a non-age-centered model.")
                scores[model_id] += 1.5
        if model_id == "gerontocracy_succession_model" and metrics.get("elite_turnover_rate") is not None:
            if float(metrics["elite_turnover_rate"]) <= 0.25:
                scores[model_id] += 0.8
                signals_by_model[model_id].append("Low turnover strengthens the succession model.")

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked:
        recommended = "institutional_domain_crisis_model"
        secondary: list[str] = []
        confidence = 0.25
        rationale = "No registry data were available; defaulting to the institutional model."
        selected_family = families[recommended]
    else:
        recommended = ranked[0][0]
        secondary = [model_id for model_id, _ in ranked[1:3] if model_id != recommended]
        top_score = ranked[0][1]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        data_quality = _quality_score(metrics)
        confidence = _score_to_confidence(top_score, second_score, data_quality)
        selected_family = families[recommended]
        rationale_bits = signals_by_model.get(recommended, [])[:4]
        rationale = "; ".join(rationale_bits) if rationale_bits else selected_family.description

    if recommended not in families:
        selected_family = ModelFamily(model_id=recommended, label=recommended, description="")

    period = {"start_year": int(start_year), "end_year": int(end_year)}
    missing_warnings = _missing_feature_warnings(selected_family, files, metrics)
    next_features = _recommended_next_features(recommended, metrics, files)
    recent_trends = {
        "core_mean_age": metrics.get("core_mean_age_mean"),
        "elite_turnover_rate": metrics.get("elite_turnover_rate"),
        "high_severity_event_rate": metrics.get("high_severity_event_rate"),
        "security_elite_share": metrics.get("security_elite_share"),
    }
    forecast = generate_forecast_guidance(country, period, selected_family, metrics, recent_trends)

    return ModelSelectionResult(
        country=country,
        period=period,
        recommended_model=recommended,
        secondary_models=secondary,
        confidence=confidence,
        rationale=rationale,
        supporting_signals=signals_by_model.get(recommended, [])[:8],
        missing_data_warnings=missing_warnings,
        recommended_next_features=next_features,
        forecast_guidance=forecast.baseline_assessment,
    )


def build_model_guidance_payload(
    dataset_id: str,
    data: dict[str, pd.DataFrame],
    country: str,
    start_year: int,
    end_year: int,
    available_files: Iterable[str],
) -> dict[str, Any]:
    metrics = extract_country_period_metrics(data, start_year, end_year)
    selection = select_model_family(country, start_year, end_year, metrics, available_files)
    families = load_model_families()
    selected_family = families.get(selection.recommended_model) or ModelFamily(
        model_id=selection.recommended_model,
        label=selection.recommended_model,
        description="",
    )
    forecast = generate_forecast_guidance(
        country,
        selection.period,
        selected_family,
        metrics,
        {
            "core_mean_age": metrics.get("core_mean_age_mean"),
            "elite_turnover_rate": metrics.get("elite_turnover_rate"),
            "high_severity_event_rate": metrics.get("high_severity_event_rate"),
            "security_elite_share": metrics.get("security_elite_share"),
        },
    )
    return {
        "dataset_id": dataset_id,
        "selection": selection.to_dict(),
        "selected_family": asdict(selected_family),
        "forecast": forecast.to_dict(),
        "metrics": {key: value for key, value in metrics.items() if key != "labels"},
    }


def render_model_guidance_report(guidance: dict[str, Any]) -> str:
    selection = guidance.get("selection", {})
    forecast = guidance.get("forecast", {})
    family = guidance.get("selected_family", {})
    lines = [
        "## Recommended model for this country-period",
        "",
        f"Recommended model: `{selection.get('recommended_model', '')}`",
        f"Confidence: `{selection.get('confidence', '')}`",
        "",
        "### Why this model fits",
    ]
    for signal in selection.get("supporting_signals", [])[:6]:
        lines.append(f"- {signal}")
    if selection.get("rationale"):
        lines.append(f"- Rationale: {selection['rationale']}")
    lines.extend(
        [
            "",
            "### Why a simple elite-age model may be weak or misleading",
        ]
    )
    for warning in selection.get("missing_data_warnings", [])[:6]:
        lines.append(f"- {warning}")
    lines.extend(
        [
            "",
            "### Forecast guidance",
            "",
            f"Forecast type: `{forecast.get('forecast_type', '')}`",
            f"Forecast horizon: `{forecast.get('forecast_horizon_years', '')}` years",
            f"Primary target: `{forecast.get('target', '')}`",
            "",
            f"Baseline: {forecast.get('baseline_assessment', '')}",
            "",
            f"Upside scenario: {forecast.get('upside_scenario', '')}",
            "",
            f"Downside scenario: {forecast.get('downside_scenario', '')}",
            "",
            "Key indicators to watch:",
        ]
    )
    for indicator in forecast.get("key_indicators_to_watch", [])[:8]:
        lines.append(f"- {indicator}")
    lines.extend(
        [
            "",
            "Warnings:",
        ]
    )
    for warning in forecast.get("warnings", [])[:8]:
        lines.append(f"- {warning}")
    if family.get("warnings"):
        lines.append("- Model-family warnings: " + "; ".join(str(item) for item in family["warnings"]))
    return "\n".join(lines)
