from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from power_age.compute import add_event_summary, build_elite_year_table
from power_age.datasets import DEFAULT_DATASET_ID, dataset_paths, dataset_year_span, load_period_groups as load_dataset_period_groups
from power_age.events import (
    events_by_decision_domain,
    events_by_initiator_group,
    events_by_period,
    filter_elite_initiated_events,
)
from power_age.factions import (
    HISTORICAL_PERIODS,
    add_faction_context_to_events,
    build_faction_year_table,
    build_faction_type_year_table,
    compute_elite_fragmentation,
)
from power_age.load_data import load_all_data, load_events
from power_age.model_guidance import build_model_guidance_payload, render_model_guidance_report
from power_age.site_data import write_site_data
from power_age.validate import validate_events, validate_faction_references

app = typer.Typer(help="Power age research MVP.")

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def _dataset_root(dataset_id: str = DEFAULT_DATASET_ID) -> Path:
    return dataset_paths(dataset_id).root


def _raw_dir(dataset_id: str = DEFAULT_DATASET_ID) -> Path:
    return dataset_paths(dataset_id).raw


def _processed_dir(dataset_id: str = DEFAULT_DATASET_ID) -> Path:
    return dataset_paths(dataset_id).processed


def _figures_dir(dataset_id: str = DEFAULT_DATASET_ID) -> Path:
    return dataset_paths(dataset_id).figures


def _elite_year_path(dataset_id: str = DEFAULT_DATASET_ID) -> Path:
    return _processed_dir(dataset_id) / "elite_year.csv"


def _faction_year_path(dataset_id: str = DEFAULT_DATASET_ID) -> Path:
    return _processed_dir(dataset_id) / "faction_year.csv"


def _faction_type_year_path(dataset_id: str = DEFAULT_DATASET_ID) -> Path:
    return _processed_dir(dataset_id) / "faction_type_year.csv"


def _faction_fragmentation_path(dataset_id: str = DEFAULT_DATASET_ID) -> Path:
    return _processed_dir(dataset_id) / "faction_fragmentation.csv"


def _events_with_faction_context_path(dataset_id: str = DEFAULT_DATASET_ID) -> Path:
    return _processed_dir(dataset_id) / "events_with_faction_context.csv"


def _build_table(dataset_id: str = DEFAULT_DATASET_ID) -> pd.DataFrame:
    data = load_all_data(_dataset_root(dataset_id))
    start_year, end_year = dataset_year_span(data, dataset_id)
    elite_year = build_elite_year_table(
        data["persons"],
        data["positions"],
        data["political_entries"],
        start_year=start_year,
        end_year=end_year,
    )
    return add_event_summary(elite_year, data["events"])


def _load_or_build_table(dataset_id: str = DEFAULT_DATASET_ID) -> pd.DataFrame:
    elite_year_path = _elite_year_path(dataset_id)
    if elite_year_path.exists():
        return pd.read_csv(elite_year_path)
    table = _build_table(dataset_id)
    _processed_dir(dataset_id).mkdir(parents=True, exist_ok=True)
    table.to_csv(elite_year_path, index=False)
    return table


def _load_period_groups(dataset_id: str = DEFAULT_DATASET_ID) -> pd.DataFrame:
    data = load_all_data(_dataset_root(dataset_id))
    return load_dataset_period_groups(data, dataset_id)


def _load_faction_year_or_build(
    dataset_id: str = DEFAULT_DATASET_ID,
    start_year: int | None = None,
    end_year: int | None = None,
    min_confidence: float = 0.5,
) -> pd.DataFrame:
    faction_year_path = _faction_year_path(dataset_id)
    faction_type_year_path = _faction_type_year_path(dataset_id)
    faction_fragmentation_path = _faction_fragmentation_path(dataset_id)
    events_with_context_path = _events_with_faction_context_path(dataset_id)
    if faction_year_path.exists():
        return pd.read_csv(faction_year_path)
    data = load_all_data(_dataset_root(dataset_id))
    if start_year is None or end_year is None:
        start_year, end_year = dataset_year_span(data, dataset_id)
    faction_year = build_faction_year_table(
        data["persons"],
        data["positions"],
        data["political_entries"],
        data["factions"],
        data["person_factions"],
        start_year=start_year,
        end_year=end_year,
        min_confidence=min_confidence,
    )
    faction_type_year = build_faction_type_year_table(faction_year, data["factions"])
    _processed_dir(dataset_id).mkdir(parents=True, exist_ok=True)
    faction_year.to_csv(faction_year_path, index=False)
    faction_type_year.to_csv(faction_type_year_path, index=False)
    compute_elite_fragmentation(faction_year).to_csv(faction_fragmentation_path, index=False)
    add_faction_context_to_events(data["events"], faction_year).to_csv(events_with_context_path, index=False)
    return faction_year


@app.command()
def build(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Build the yearly elite table for a dataset."""
    paths = dataset_paths(dataset)
    table = _build_table(dataset)
    paths.processed.mkdir(parents=True, exist_ok=True)
    output_path = _elite_year_path(dataset)
    table.to_csv(output_path, index=False)
    typer.echo(f"Saved {len(table)} rows to {output_path}")


@app.command()
def plot(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Save all timeline plots as PNG files."""
    from power_age.visualize import (
        plot_biological_vs_political_age,
        plot_core_elite_age,
        plot_core_elite_aging_dashboard,
        plot_institution_composition,
        plot_period_age_boxplots,
        plot_ruler_vs_core_age,
        plot_ruler_age_timeline,
    )

    elite_year = _load_or_build_table(dataset)
    data = load_all_data(_dataset_root(dataset))
    events = data["events"]
    period_groups = _load_period_groups(dataset)
    figures_dir = _figures_dir(dataset)
    figures_dir.mkdir(parents=True, exist_ok=True)
    start_year, end_year = dataset_year_span(data, dataset)

    plot_ruler_age_timeline(
        elite_year,
        events,
        figures_dir / "ruler_age_timeline.png",
    )
    plot_biological_vs_political_age(
        elite_year,
        figures_dir / "biological_vs_political_age.png",
    )
    plot_core_elite_age(
        elite_year,
        figures_dir / "core_elite_age.png",
    )
    plot_core_elite_aging_dashboard(
        elite_year,
        figures_dir / "core_elite_aging_dashboard.png",
    )
    plot_ruler_vs_core_age(
        elite_year,
        figures_dir / "ruler_vs_core_age.png",
    )
    plot_institution_composition(
        data["persons"],
        data["positions"],
        figures_dir / "institution_composition.png",
        start_year=start_year,
        end_year=end_year,
    )
    plot_period_age_boxplots(
        data["persons"],
        data["positions"],
        period_groups,
        figures_dir / "period_age_boxplots.png",
    )
    typer.echo(f"Saved figures to {figures_dir}")


@app.command()
def diagnostics(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Print data diagnostics and faction-layer validation warnings."""
    data = load_all_data(_dataset_root(dataset))
    persons = data["persons"]
    positions = data["positions"]
    political_entries = data["political_entries"]
    factions = data["factions"]
    person_factions = data["person_factions"]
    faction_relations = data["faction_relations"]
    elite_edges = data["elite_edges"]

    typer.echo(f"persons: {len(persons)}")
    typer.echo(f"positions: {len(positions)}")
    typer.echo(f"political_entries: {len(political_entries)}")
    typer.echo(f"events: {len(data['events'])}")
    typer.echo(f"factions: {len(factions)}")
    typer.echo(f"person_factions: {len(person_factions)}")
    typer.echo(f"elite_edges: {len(elite_edges)}")
    typer.echo(f"faction_relations: {len(faction_relations)}")

    if not person_factions.empty:
        multi = (
            person_factions.groupby("person_id")["faction_id"]
            .nunique()
            .sort_values(ascending=False)
            .head(10)
        )
        typer.echo("Топ-10 людей с несколькими фракциями:")
        for person_id, count in multi.items():
            if count > 1:
                typer.echo(f"  {person_id}: {count}")

    if not factions.empty:
        used_factions = set(person_factions["faction_id"].dropna().astype(str))
        empty_factions = sorted(
            faction_id
            for faction_id in factions["faction_id"].dropna().astype(str).unique()
            if faction_id not in used_factions
        )
        typer.echo("Фракции без участников:")
        if empty_factions:
            for faction_id in empty_factions:
                typer.echo(f"  {faction_id}")
        else:
            typer.echo("  нет")

    errors = validate_faction_references(
        persons,
        factions,
        person_factions,
        faction_relations,
        elite_edges,
    )
    typer.echo("Ошибки валидации фракционного слоя:")
    if errors:
        for error in errors:
            typer.echo(f"  {error}")
    else:
        typer.echo("  нет")

    event_errors = validate_events(data["events"], persons, factions)
    typer.echo("Ошибки валидации событий:")
    if event_errors:
        for error in event_errors:
            typer.echo(f"  {error}")
    else:
        typer.echo("  нет")

    elite_year = _load_or_build_table(dataset)
    faction_year = build_faction_year_table(
        persons,
        positions,
        political_entries,
        factions,
        person_factions,
        start_year=int(elite_year["year"].min()),
        end_year=int(elite_year["year"].max()),
        min_confidence=0.5,
    )
    elite_years = set(elite_year.loc[elite_year["core_elite_count"] > 0, "year"].astype(int))
    faction_years = set(faction_year["year"].astype(int)) if not faction_year.empty else set()
    empty_faction_years = sorted(elite_years - faction_years)
    typer.echo("Годы с elite_year, но без faction_year:")
    if empty_faction_years:
        preview = ", ".join(str(year) for year in empty_faction_years[:40])
        suffix = " ..." if len(empty_faction_years) > 40 else ""
        typer.echo(f"  {preview}{suffix}")
        typer.echo(f"  всего: {len(empty_faction_years)}")
    else:
        typer.echo("  нет")


@app.command()
def build_factions(
    dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id"),
    start_year: int | None = None,
    end_year: int | None = None,
    min_confidence: float = 0.5,
) -> None:
    """Build faction processed tables."""
    paths = dataset_paths(dataset)
    data = load_all_data(_dataset_root(dataset))
    if start_year is None or end_year is None:
        start_year, end_year = dataset_year_span(data, dataset)
    faction_year = build_faction_year_table(
        data["persons"],
        data["positions"],
        data["political_entries"],
        data["factions"],
        data["person_factions"],
        start_year=start_year,
        end_year=end_year,
        min_confidence=min_confidence,
    )
    faction_type_year = build_faction_type_year_table(faction_year, data["factions"])
    fragmentation = compute_elite_fragmentation(faction_year)
    events_with_context = add_faction_context_to_events(data["events"], faction_year)

    paths.processed.mkdir(parents=True, exist_ok=True)
    faction_year_path = _faction_year_path(dataset)
    faction_type_year_path = _faction_type_year_path(dataset)
    fragmentation_path = _faction_fragmentation_path(dataset)
    events_context_path = _events_with_faction_context_path(dataset)
    faction_year.to_csv(faction_year_path, index=False)
    faction_type_year.to_csv(faction_type_year_path, index=False)
    fragmentation.to_csv(fragmentation_path, index=False)
    events_with_context.to_csv(events_context_path, index=False)

    typer.echo(f"Saved {len(faction_year)} rows to {faction_year_path}")
    typer.echo(f"Saved {len(faction_type_year)} rows to {faction_type_year_path}")
    typer.echo(f"Saved {len(fragmentation)} rows to {fragmentation_path}")
    typer.echo(f"Saved {len(events_with_context)} rows to {events_context_path}")


@app.command()
def plot_factions(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Save faction plots as PNG files."""
    from power_age.faction_visualize import (
        plot_faction_fragmentation,
        plot_faction_mean_age,
        plot_faction_power_heatmap,
        plot_faction_power_share_stacked,
        plot_faction_type_power_share_stacked,
        plot_faction_weighted_mean_age,
    )

    faction_year = _load_faction_year_or_build(dataset)
    data = load_all_data(_dataset_root(dataset))
    figures_dir = _figures_dir(dataset)
    faction_type_year = (
        pd.read_csv(_faction_type_year_path(dataset))
        if _faction_type_year_path(dataset).exists()
        else build_faction_type_year_table(faction_year, data["factions"])
    )
    if _faction_fragmentation_path(dataset).exists():
        fragmentation = pd.read_csv(_faction_fragmentation_path(dataset))
    else:
        fragmentation = compute_elite_fragmentation(faction_year)
    figures_dir.mkdir(parents=True, exist_ok=True)

    plot_faction_power_share_stacked(
        faction_year,
        figures_dir / "faction_power_share_stacked.png",
    )
    plot_faction_type_power_share_stacked(
        faction_type_year,
        figures_dir / "faction_type_power_share_stacked.png",
    )
    plot_faction_mean_age(
        faction_year,
        figures_dir / "faction_mean_age.png",
    )
    plot_faction_weighted_mean_age(
        faction_year,
        figures_dir / "faction_weighted_mean_age.png",
    )
    plot_faction_fragmentation(
        fragmentation,
        figures_dir / "faction_fragmentation.png",
    )
    plot_faction_power_heatmap(
        faction_year,
        figures_dir / "faction_power_heatmap.png",
    )
    typer.echo(f"Saved faction figures to {figures_dir}")


@app.command()
def plot_factions_periods(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Save separate faction stacked area charts by historical period."""
    from power_age.faction_visualize import plot_faction_power_share_stacked

    faction_year = _load_faction_year_or_build(dataset)
    period_groups = _load_period_groups(dataset)
    figures_dir = _figures_dir(dataset)
    figures_dir.mkdir(parents=True, exist_ok=True)
    if period_groups.empty:
        period_groups = pd.DataFrame(HISTORICAL_PERIODS)
    for _, period in period_groups.iterrows():
        period_slug = str(period.get("slug") or period.get("period_id"))
        period_data = faction_year[
            (faction_year["year"] >= int(period["start_year"]))
            & (faction_year["year"] <= int(period["end_year"]))
        ].copy()
        output_path = figures_dir / f"factions_{period_slug}.png"
        if period_data.empty:
            typer.echo(f"Skipped {period.get('label_en') or period.get('label') or period_slug}: no faction data")
            continue
        title = period.get("label_en") or period.get("label_ru") or period.get("label") or period_slug
        plot_faction_power_share_stacked(
            period_data,
            output_path,
            title=f"Фракционная власть: {title}",
        )
        typer.echo(f"Saved {output_path}")


@app.command()
def plot_events(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Save event-focused plots as PNG files."""
    from power_age.visualize import (
        plot_event_severity_timeline,
        plot_events_by_domain,
        plot_events_by_period,
        plot_events_by_year,
    )

    data = load_all_data(_dataset_root(dataset))
    events = data["events"]
    figures_dir = _figures_dir(dataset)
    figures_dir.mkdir(parents=True, exist_ok=True)

    plot_events_by_year(events, figures_dir / "events_by_year.png")
    plot_events_by_period(
        events_by_period(filter_elite_initiated_events(events), data.get("periods")),
        figures_dir / "events_by_period.png",
    )
    plot_events_by_domain(
        events_by_decision_domain(filter_elite_initiated_events(events)),
        figures_dir / "events_by_domain.png",
    )
    plot_event_severity_timeline(
        events,
        figures_dir / "event_severity_timeline.png",
    )
    typer.echo(f"Saved event figures to {figures_dir}")


@app.command()
def event_summary(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Print event-layer summary."""
    data = load_all_data(_dataset_root(dataset))
    events = data["events"]
    elite_events = filter_elite_initiated_events(events)

    typer.echo(f"Всего событий: {len(events)}")
    typer.echo(f"Всего elite_initiated событий: {len(elite_events)}")

    typer.echo("События по периодам:")
    period_summary = events_by_period(elite_events, data.get("periods"))
    for _, row in period_summary.iterrows():
        typer.echo(
            f"  {row['period_label']}: events={int(row['events_count'])}, mean_severity={row['mean_severity']:.2f}, max_severity={int(row['max_severity'])}"
        )

    typer.echo("События по decision_domain:")
    for _, row in events_by_decision_domain(elite_events).sort_values("events_count", ascending=False).iterrows():
        typer.echo(
            f"  {row['decision_domain']}: events={int(row['events_count'])}, mean_severity={row['mean_severity']:.2f}, max_severity={int(row['max_severity'])}"
        )

    typer.echo("События по initiator_group:")
    for _, row in events_by_initiator_group(elite_events).sort_values("events_count", ascending=False).iterrows():
        typer.echo(
            f"  {row['initiator_group']}: events={int(row['events_count'])}, mean_severity={row['mean_severity']:.2f}, max_severity={int(row['max_severity'])}"
        )

    typer.echo("Топ-20 событий severity=5:")
    top_severe = elite_events[elite_events["severity"] == 5].sort_values("date").head(20)
    for _, row in top_severe.iterrows():
        typer.echo(f"  {row['date'].date()}: {row['event_id']} - {row['event_name']}")

    typer.echo("Топ-20 событий confidence < 0.6:")
    if "confidence" in elite_events.columns:
        confidence = pd.to_numeric(elite_events["confidence"], errors="coerce")
        low_conf = elite_events[confidence < 0.6]
    else:
        low_conf = elite_events.iloc[0:0]
    for _, row in low_conf.sort_values("confidence").head(20).iterrows():
        typer.echo(
            f"  {row['date'].date()}: {row['event_id']} confidence={row.get('confidence')} - {row['event_name']}"
        )


@app.command()
def faction_summary(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Print faction-layer summary."""
    faction_year = _load_faction_year_or_build(dataset)
    data = load_all_data(_dataset_root(dataset))
    factions = data["factions"]
    faction_year_with_types = faction_year.merge(
        factions[["faction_id", "faction_type"]],
        on="faction_id",
        how="left",
    )
    fragmentation_path = _faction_fragmentation_path(dataset)
    fragmentation = (
        pd.read_csv(fragmentation_path)
        if fragmentation_path.exists()
        else compute_elite_fragmentation(faction_year)
    )
    if faction_year.empty:
        typer.echo("faction_year.csv пустой")
        return

    typer.echo(f"Диапазон лет: {int(faction_year['year'].min())}-{int(faction_year['year'].max())}")

    typer.echo("Топ фракций по среднему normalized_power_share:")
    top_power = (
        faction_year.groupby("faction_id")["normalized_power_share"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )
    for faction_id, value in top_power.items():
        typer.echo(f"  {faction_id}: {value:.3f}")

    typer.echo("Топ фракций по среднему возрасту:")
    top_age = faction_year.groupby("faction_id")["mean_age"].mean().sort_values(ascending=False).head(10)
    for faction_id, value in top_age.items():
        typer.echo(f"  {faction_id}: {value:.2f}")

    typer.echo("Топ фракций по среднему political_age:")
    top_political_age = (
        faction_year.groupby("faction_id")["mean_political_age"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )
    for faction_id, value in top_political_age.items():
        typer.echo(f"  {faction_id}: {value:.2f}")

    if not fragmentation.empty:
        max_fragmentation = fragmentation["fragmentation_index"].max()
        min_fragmentation = fragmentation["fragmentation_index"].min()
        max_years = fragmentation.loc[
            fragmentation["fragmentation_index"] == max_fragmentation,
            "year",
        ].tolist()
        min_years = fragmentation.loc[
            fragmentation["fragmentation_index"] == min_fragmentation,
            "year",
        ].tolist()
        typer.echo(
            "Годы с максимальной fragmentation_index: "
            + ", ".join(str(int(year)) for year in max_years)
        )
        typer.echo(
            "Годы с минимальной fragmentation_index: "
            + ", ".join(str(int(year)) for year in min_years)
        )

        typer.echo("Доминирующая фракция по десятилетиям:")
        decade_rows = fragmentation.copy()
        decade_rows["decade"] = (decade_rows["year"] // 10) * 10
        for decade, group in decade_rows.groupby("decade"):
            dominant = group["dominant_faction_id"].mode()
            value = dominant.iloc[0] if not dominant.empty else ""
            typer.echo(f"  {int(decade)}s: {value}")

    typer.echo("Исторические периоды:")
    periods = _load_period_groups(dataset)
    if periods.empty:
        periods = pd.DataFrame(HISTORICAL_PERIODS)
    for _, period in periods.iterrows():
        period_factions = faction_year_with_types[
            (faction_year_with_types["year"] >= int(period["start_year"]))
            & (faction_year_with_types["year"] <= int(period["end_year"]))
        ].copy()
        period_fragmentation = fragmentation[
            (fragmentation["year"] >= int(period["start_year"]))
            & (fragmentation["year"] <= int(period["end_year"]))
        ].copy()
        period_label = period.get("label_en") or period.get("label_ru") or period.get("label") or period.get("period_id")
        typer.echo(f"  {period_label} ({period['start_year']}-{period['end_year']}):")
        if period_factions.empty:
            typer.echo("    нет faction_year данных")
            continue

        period_years = range(int(period["start_year"]), int(period["end_year"]) + 1)
        faction_shares = period_factions.pivot_table(
            index="year",
            columns="faction_id",
            values="normalized_power_share",
            aggfunc="sum",
            fill_value=0,
        )
        top_factions_period = faction_shares.reindex(period_years, fill_value=0).mean()
        top_factions_period = top_factions_period.sort_values(ascending=False).head(5)
        typer.echo("    top factions:")
        for faction_id, value in top_factions_period.items():
            mean_age = period_factions.loc[
                period_factions["faction_id"] == faction_id,
                "mean_age",
            ].mean()
            typer.echo(f"      {faction_id}: share={value:.3f}, mean_age={mean_age:.2f}")

        type_shares = period_factions.pivot_table(
            index="year",
            columns="faction_type",
            values="normalized_power_share",
            aggfunc="sum",
            fill_value=0,
        )
        top_types_period = type_shares.reindex(period_years, fill_value=0).mean()
        top_types_period = top_types_period.sort_values(ascending=False).head(5)
        typer.echo("    top faction_types:")
        for faction_type, value in top_types_period.items():
            typer.echo(f"      {faction_type}: {value:.3f}")

        if not period_fragmentation.empty:
            avg_fragmentation = period_fragmentation["fragmentation_index"].mean()
            dominant = period_fragmentation["dominant_faction_id"].mode()
            dominant_value = dominant.iloc[0] if not dominant.empty else ""
            typer.echo(f"    average fragmentation_index: {avg_fragmentation:.3f}")
            typer.echo(f"    dominant faction: {dominant_value}")


@app.command()
def summary(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Print a short descriptive summary."""
    elite_year = _load_or_build_table(dataset)
    events = load_events(_raw_dir(dataset) / "events.csv")

    mean_ruler_age = elite_year["ruler_age"].mean()
    max_ruler_age = elite_year["ruler_age"].max()
    max_political_age = elite_year["ruler_political_age"].max()
    max_core_mean_age = elite_year["core_mean_age"].max()

    political_age_years = elite_year.loc[
        elite_year["ruler_political_age"] == max_political_age, "year"
    ].tolist()
    core_age_years = elite_year.loc[elite_year["core_mean_age"] == max_core_mean_age, "year"].tolist()
    event_counts = events["event_type"].value_counts().sort_index()

    typer.echo(f"Средний возраст правителя: {mean_ruler_age:.2f}")
    typer.echo(f"Максимальный возраст правителя: {max_ruler_age:.2f}")
    typer.echo(
        "Годы с максимальным ruler_political_age: "
        + ", ".join(str(year) for year in political_age_years)
    )
    typer.echo(
        "Годы с максимальным core_mean_age: " + ", ".join(str(year) for year in core_age_years)
    )
    typer.echo("События по типам:")
    for event_type, count in event_counts.items():
        typer.echo(f"  {event_type}: {count}")


@app.command("model-guidance")
def model_guidance(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Print model selection and cautious forecast guidance."""
    data = load_all_data(_dataset_root(dataset))
    start_year, end_year = dataset_year_span(data, dataset)
    raw_path = _raw_dir(dataset)
    available_files = {path.name for path in raw_path.glob("*") if path.is_file()}
    country_series = data["persons"].get("country_label") if "country_label" in data["persons"].columns else None
    country = (
        str(country_series.dropna().iloc[0])
        if country_series is not None and not country_series.dropna().empty
        else dataset.upper()
    )
    guidance = build_model_guidance_payload(
        dataset,
        data,
        country,
        start_year,
        end_year,
        available_files,
    )
    typer.echo(render_model_guidance_report(guidance))


@app.command("build-docs-data")
def build_docs_data(dataset: str = typer.Option(DEFAULT_DATASET_ID, "--dataset", help="Dataset id")) -> None:
    """Rebuild docs/site-data.json and docs/series-data.json for a dataset."""
    site_path, series_path = write_site_data(dataset, PROJECT_ROOT / "docs" / "data")
    typer.echo(f"Saved docs data to {site_path}")
    typer.echo(f"Saved docs series to {series_path}")


if __name__ == "__main__":
    app()
