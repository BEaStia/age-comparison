from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from power_age.compute import add_event_summary, build_elite_year_table
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
from power_age.validate import validate_events, validate_faction_references

app = typer.Typer(help="Power age research MVP.")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
ELITE_YEAR_PATH = PROCESSED_DIR / "elite_year.csv"
FACTION_YEAR_PATH = PROCESSED_DIR / "faction_year.csv"
FACTION_TYPE_YEAR_PATH = PROCESSED_DIR / "faction_type_year.csv"
FACTION_FRAGMENTATION_PATH = PROCESSED_DIR / "faction_fragmentation.csv"
EVENTS_WITH_FACTION_CONTEXT_PATH = PROCESSED_DIR / "events_with_faction_context.csv"


def _build_table() -> pd.DataFrame:
    data = load_all_data(DATA_DIR)
    elite_year = build_elite_year_table(
        data["persons"],
        data["positions"],
        data["political_entries"],
        start_year=1801,
        end_year=2026,
    )
    return add_event_summary(elite_year, data["events"])


def _load_or_build_table() -> pd.DataFrame:
    if ELITE_YEAR_PATH.exists():
        return pd.read_csv(ELITE_YEAR_PATH)
    table = _build_table()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(ELITE_YEAR_PATH, index=False)
    return table


def _load_period_groups() -> pd.DataFrame:
    paths = sorted(RAW_DIR.glob("core_elite_groups*.csv"))
    frames = [pd.read_csv(path) for path in paths]
    if not frames:
        return pd.DataFrame()
    groups = pd.concat(frames, ignore_index=True)
    groups = groups.drop_duplicates(subset=["period_id"], keep="first")
    return groups.sort_values(["start_year", "end_year", "period_id"]).reset_index(drop=True)


def _load_faction_year_or_build(
    start_year: int = 1801,
    end_year: int = 2026,
    min_confidence: float = 0.5,
) -> pd.DataFrame:
    if FACTION_YEAR_PATH.exists():
        return pd.read_csv(FACTION_YEAR_PATH)
    data = load_all_data(DATA_DIR)
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
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    faction_year.to_csv(FACTION_YEAR_PATH, index=False)
    faction_type_year.to_csv(FACTION_TYPE_YEAR_PATH, index=False)
    compute_elite_fragmentation(faction_year).to_csv(FACTION_FRAGMENTATION_PATH, index=False)
    return faction_year


@app.command()
def build() -> None:
    """Build data/processed/elite_year.csv."""
    table = _build_table()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(ELITE_YEAR_PATH, index=False)
    typer.echo(f"Saved {len(table)} rows to {ELITE_YEAR_PATH}")


@app.command()
def plot() -> None:
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

    elite_year = _load_or_build_table()
    data = load_all_data(DATA_DIR)
    events = data["events"]
    period_groups = _load_period_groups()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    plot_ruler_age_timeline(
        elite_year,
        events,
        FIGURES_DIR / "ruler_age_timeline.png",
    )
    plot_biological_vs_political_age(
        elite_year,
        FIGURES_DIR / "biological_vs_political_age.png",
    )
    plot_core_elite_age(
        elite_year,
        FIGURES_DIR / "core_elite_age.png",
    )
    plot_core_elite_aging_dashboard(
        elite_year,
        FIGURES_DIR / "core_elite_aging_dashboard.png",
    )
    plot_ruler_vs_core_age(
        elite_year,
        FIGURES_DIR / "ruler_vs_core_age.png",
    )
    plot_institution_composition(
        data["persons"],
        data["positions"],
        FIGURES_DIR / "institution_composition.png",
    )
    plot_period_age_boxplots(
        data["persons"],
        data["positions"],
        period_groups,
        FIGURES_DIR / "period_age_boxplots.png",
    )
    typer.echo(f"Saved figures to {FIGURES_DIR}")


@app.command()
def diagnostics() -> None:
    """Print data diagnostics and faction-layer validation warnings."""
    data = load_all_data(DATA_DIR)
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

    elite_year = _load_or_build_table()
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
    start_year: int = 1801,
    end_year: int = 2026,
    min_confidence: float = 0.5,
) -> None:
    """Build faction processed tables."""
    data = load_all_data(DATA_DIR)
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

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    faction_year.to_csv(FACTION_YEAR_PATH, index=False)
    faction_type_year.to_csv(FACTION_TYPE_YEAR_PATH, index=False)
    fragmentation.to_csv(FACTION_FRAGMENTATION_PATH, index=False)
    events_with_context.to_csv(EVENTS_WITH_FACTION_CONTEXT_PATH, index=False)

    typer.echo(f"Saved {len(faction_year)} rows to {FACTION_YEAR_PATH}")
    typer.echo(f"Saved {len(faction_type_year)} rows to {FACTION_TYPE_YEAR_PATH}")
    typer.echo(f"Saved {len(fragmentation)} rows to {FACTION_FRAGMENTATION_PATH}")
    typer.echo(f"Saved {len(events_with_context)} rows to {EVENTS_WITH_FACTION_CONTEXT_PATH}")


@app.command()
def plot_factions() -> None:
    """Save faction plots as PNG files."""
    from power_age.faction_visualize import (
        plot_faction_fragmentation,
        plot_faction_mean_age,
        plot_faction_power_heatmap,
        plot_faction_power_share_stacked,
        plot_faction_type_power_share_stacked,
        plot_faction_weighted_mean_age,
    )

    faction_year = _load_faction_year_or_build()
    data = load_all_data(DATA_DIR)
    faction_type_year = (
        pd.read_csv(FACTION_TYPE_YEAR_PATH)
        if FACTION_TYPE_YEAR_PATH.exists()
        else build_faction_type_year_table(faction_year, data["factions"])
    )
    if FACTION_FRAGMENTATION_PATH.exists():
        fragmentation = pd.read_csv(FACTION_FRAGMENTATION_PATH)
    else:
        fragmentation = compute_elite_fragmentation(faction_year)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    plot_faction_power_share_stacked(
        faction_year,
        FIGURES_DIR / "faction_power_share_stacked.png",
    )
    plot_faction_type_power_share_stacked(
        faction_type_year,
        FIGURES_DIR / "faction_type_power_share_stacked.png",
    )
    plot_faction_mean_age(
        faction_year,
        FIGURES_DIR / "faction_mean_age.png",
    )
    plot_faction_weighted_mean_age(
        faction_year,
        FIGURES_DIR / "faction_weighted_mean_age.png",
    )
    plot_faction_fragmentation(
        fragmentation,
        FIGURES_DIR / "faction_fragmentation.png",
    )
    plot_faction_power_heatmap(
        faction_year,
        FIGURES_DIR / "faction_power_heatmap.png",
    )
    typer.echo(f"Saved faction figures to {FIGURES_DIR}")


@app.command()
def plot_factions_periods() -> None:
    """Save separate faction stacked area charts by historical period."""
    from power_age.faction_visualize import plot_faction_power_share_stacked

    faction_year = _load_faction_year_or_build()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for period in HISTORICAL_PERIODS:
        period_data = faction_year[
            (faction_year["year"] >= int(period["start_year"]))
            & (faction_year["year"] <= int(period["end_year"]))
        ].copy()
        output_path = FIGURES_DIR / f"factions_{period['slug']}.png"
        if period_data.empty:
            typer.echo(f"Skipped {period['label']}: no faction data")
            continue
        plot_faction_power_share_stacked(
            period_data,
            output_path,
            title=f"Фракционная власть: {period['label']}",
        )
        typer.echo(f"Saved {output_path}")


@app.command()
def faction_summary() -> None:
    """Print faction-layer summary."""
    faction_year = _load_faction_year_or_build()
    data = load_all_data(DATA_DIR)
    factions = data["factions"]
    faction_year_with_types = faction_year.merge(
        factions[["faction_id", "faction_type"]],
        on="faction_id",
        how="left",
    )
    fragmentation = (
        pd.read_csv(FACTION_FRAGMENTATION_PATH)
        if FACTION_FRAGMENTATION_PATH.exists()
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
    for period in HISTORICAL_PERIODS:
        period_factions = faction_year_with_types[
            (faction_year_with_types["year"] >= int(period["start_year"]))
            & (faction_year_with_types["year"] <= int(period["end_year"]))
        ].copy()
        period_fragmentation = fragmentation[
            (fragmentation["year"] >= int(period["start_year"]))
            & (fragmentation["year"] <= int(period["end_year"]))
        ].copy()
        typer.echo(f"  {period['label']} ({period['start_year']}-{period['end_year']}):")
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
def summary() -> None:
    """Print a short descriptive summary."""
    elite_year = _load_or_build_table()
    events = load_events(RAW_DIR / "events.csv")

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


if __name__ == "__main__":
    app()
