from __future__ import annotations

import pytest

from power_age.datasets import dataset_paths, dataset_year_span
from power_age.load_data import load_all_data
from power_age.model_guidance import (
    build_model_guidance_payload,
    generate_forecast_guidance,
    load_model_families,
    render_model_guidance_report,
    select_model_family,
)

def _available_files(dataset_id: str) -> set[str]:
    raw = dataset_paths(dataset_id).raw
    return {path.name for path in raw.glob("*") if path.is_file()}


def _country_for_dataset(data: dict, dataset_id: str) -> str:
    if "country_label" in data["persons"].columns:
        series = data["persons"]["country_label"].dropna()
        if not series.empty:
            return str(series.iloc[0])
    return dataset_id


def test_usa_selects_institutional_model_from_real_data() -> None:
    data = load_all_data(dataset_paths("usa").root)
    start_year, end_year = dataset_year_span(data, "usa")
    guidance = build_model_guidance_payload(
        "usa",
        data,
        _country_for_dataset(data, "USA"),
        start_year,
        end_year,
        _available_files("usa"),
    )

    assert guidance["selection"]["recommended_model"] == "institutional_domain_crisis_model"
    assert abs(guidance["metrics"]["corr_core_elite_age_elite_events"]) < 0.15
    assert guidance["forecast"]["forecast_type"] == "scenario"
    assert guidance["forecast"]["warnings"]


@pytest.mark.parametrize(
    ("country", "start_year", "end_year", "metrics", "available_files", "expected"),
    [
        (
            "USA",
            1945,
            2025,
            {
                "corr_core_elite_age_elite_events": 0.075,
                "event_domain_richness": 8,
                "institution_richness": 20,
                "high_severity_event_rate": 0.3,
                "elite_turnover_rate": 0.4,
                "faction_layer_available": True,
                "finance_elite_share": 0.2,
                "judicial_elite_share": 0.1,
                "security_elite_share": 0.1,
            },
            {"events.csv", "positions.csv", "factions.csv", "person_factions.csv", "periods.csv"},
            "institutional_domain_crisis_model",
        ),
        (
            "USSR",
            1964,
            1985,
            {
                "leader_age_mean": 72,
                "ruling_circle_age_mean": 68,
                "share_70_plus": 0.3,
                "elite_turnover_rate": 0.1,
                "succession_signal_count": 3,
                "event_domain_richness": 2,
                "institution_richness": 4,
                "faction_layer_available": False,
            },
            {"persons.csv", "positions.csv", "events.csv"},
            "gerontocracy_succession_model",
        ),
        (
            "Saudi Arabia",
            1953,
            2017,
            {
                "royal_elite_share": 0.25,
                "succession_signal_count": 4,
                "faction_dominant_share": 0.5,
                "security_elite_share": 0.1,
                "faction_layer_available": True,
            },
            {"persons.csv", "positions.csv", "factions.csv", "person_factions.csv", "events.csv"},
            "dynastic_succession_model",
        ),
        (
            "China",
            1978,
            2012,
            {
                "party_congress_signal": 4,
                "elite_turnover_rate": 0.3,
                "technocrat_share": 0.2,
                "faction_dominant_share": 0.35,
                "faction_layer_available": True,
            },
            {"persons.csv", "positions.csv", "factions.csv", "person_factions.csv", "events.csv"},
            "party_congress_turnover_model",
        ),
        (
            "Iran",
            1979,
            2026,
            {
                "revolutionary_generation_signal": 5,
                "security_elite_share": 0.2,
                "protest_event_count": 3,
                "succession_signal_count": 2,
                "faction_layer_available": True,
            },
            {"persons.csv", "positions.csv", "factions.csv", "person_factions.csv", "events.csv"},
            "revolutionary_generation_model",
        ),
        (
            "Russia",
            2000,
            2026,
            {
                "security_elite_share": 0.35,
                "purge_event_count": 5,
                "war_event_count": 3,
                "faction_dominant_share": 0.6,
                "elite_turnover_rate": 0.12,
                "faction_layer_available": True,
            },
            {"persons.csv", "positions.csv", "factions.csv", "person_factions.csv", "events.csv"},
            "security_state_faction_model",
        ),
    ],
)
def test_model_selector_cases(
    country: str,
    start_year: int,
    end_year: int,
    metrics: dict[str, object],
    available_files: set[str],
    expected: str,
) -> None:
    result = select_model_family(country, start_year, end_year, metrics, available_files)

    assert result.recommended_model == expected
    assert result.confidence > 0


def test_forecast_guidance_is_scenario_based_and_warns() -> None:
    families = load_model_families()
    selected_family = families["gerontocracy_succession_model"]
    forecast = generate_forecast_guidance(
        "USSR",
        {"start_year": 1964, "end_year": 1985},
        selected_family,
        {
            "leader_age_mean": 72,
            "ruling_circle_age_mean": 68,
            "share_70_plus": 0.3,
            "elite_turnover_rate": 0.1,
            "succession_signal_count": 3,
            "event_domain_richness": 2,
        },
        {"core_mean_age": 68, "elite_turnover_rate": 0.1, "high_severity_event_rate": 0.2},
    )

    assert forecast.forecast_type == "scenario"
    assert forecast.forecast_horizon_years == 5
    assert forecast.warnings
    assert "succession" in forecast.baseline_assessment.lower()


def test_render_model_guidance_report_contains_sections() -> None:
    data = load_all_data(dataset_paths("usa").root)
    start_year, end_year = dataset_year_span(data, "usa")
    guidance = build_model_guidance_payload(
        "usa",
        data,
        _country_for_dataset(data, "USA"),
        start_year,
        end_year,
        _available_files("usa"),
    )
    report = render_model_guidance_report(guidance)

    assert "Recommended model for this country-period" in report
    assert "Forecast guidance" in report
    assert guidance["selection"]["recommended_model"] in report
