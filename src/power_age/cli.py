from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from power_age.compute import add_event_summary, build_elite_year_table
from power_age.load_data import load_all_data, load_events

app = typer.Typer(help="Power age research MVP.")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
ELITE_YEAR_PATH = PROCESSED_DIR / "elite_year.csv"


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
