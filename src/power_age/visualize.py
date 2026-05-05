from __future__ import annotations

import os
from pathlib import Path

_MPL_CONFIG_DIR = Path(__file__).resolve().parents[2] / "outputs" / ".matplotlib"
_MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG_DIR))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MultipleLocator  # noqa: E402
import pandas as pd  # noqa: E402

from power_age.compute import active_positions_for_year, age_on_date  # noqa: E402
from power_age.events import filter_elite_initiated_events  # noqa: E402


def _prepare_output(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _set_year_axis(ax: plt.Axes, tick_step: int = 5) -> None:
    ax.xaxis.set_major_locator(MultipleLocator(tick_step))
    ax.tick_params(axis="x", labelrotation=45, labelsize=8)


def plot_ruler_age_timeline(
    elite_year: pd.DataFrame,
    events: pd.DataFrame,
    output_path: str | Path,
    elite_only: bool = True,
    min_confidence: float = 0.5,
) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(elite_year["year"], elite_year["ruler_age"], color="#1f5a7a", linewidth=2)

    event_points = (
        filter_elite_initiated_events(events, min_confidence=min_confidence)
        if elite_only
        else events.copy()
    )
    event_points["year"] = event_points["date"].dt.year
    event_points = event_points.merge(
        elite_year[["year", "ruler_age"]], on="year", how="left"
    ).dropna(subset=["ruler_age"])

    if not event_points.empty:
        ax.scatter(
            event_points["year"],
            event_points["ruler_age"],
            s=event_points["severity"] * 35,
            color="#b33a3a",
            alpha=0.75,
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        for _, row in event_points[event_points["severity"] >= 5].iterrows():
            ax.annotate(
                row["event_name"],
                (row["year"], row["ruler_age"]),
                xytext=(5, 7),
                textcoords="offset points",
                fontsize=8,
                rotation=25,
                ha="left",
            )

    ax.set_title("Возраст правителя и ключевые события, 1801-2026")
    ax.set_xlabel("Год")
    ax.set_ylabel("Возраст правителя")
    _set_year_axis(ax)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_events_by_year(events: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    elite_events = filter_elite_initiated_events(events)
    fig, ax = plt.subplots(figsize=(14, 7))
    if elite_events.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        counts = elite_events.groupby(elite_events["date"].dt.year).size()
        ax.bar(counts.index, counts.values, color="#1f5a7a")
    ax.set_title("Elite-initiated события по годам")
    ax.set_xlabel("Год")
    ax.set_ylabel("Событий")
    _set_year_axis(ax)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_events_by_period(period_summary: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(12, 7))
    if period_summary.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        ax.bar(period_summary["period_label"], period_summary["events_count"], color="#6f4e9b")
        ax.tick_params(axis="x", rotation=25)
    ax.set_title("Elite-initiated события по периодам")
    ax.set_ylabel("Событий")
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_events_by_domain(domain_summary: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(12, 7))
    if domain_summary.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        data = domain_summary.sort_values("events_count", ascending=False).head(20)
        ax.bar(data["decision_domain"], data["events_count"], color="#2f7d4f")
        ax.tick_params(axis="x", rotation=35, labelsize=8)
    ax.set_title("Elite-initiated события по decision_domain")
    ax.set_ylabel("Событий")
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_event_severity_timeline(events: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    elite_events = filter_elite_initiated_events(events)
    fig, ax = plt.subplots(figsize=(14, 7))
    if elite_events.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        data = elite_events.copy()
        data["year"] = data["date"].dt.year
        confidence = (
            pd.to_numeric(data["confidence"], errors="coerce").fillna(1.0)
            if "confidence" in data.columns
            else pd.Series(1.0, index=data.index)
        )
        ax.scatter(
            data["year"],
            data["severity"],
            s=40 + confidence * 120,
            alpha=0.35 + confidence * 0.55,
            color="#b33a3a",
            edgecolor="white",
            linewidth=0.7,
        )
        for _, row in data[data["severity"] >= 5].iterrows():
            ax.annotate(
                row["event_name"],
                (row["year"], row["severity"]),
                xytext=(5, 6),
                textcoords="offset points",
                fontsize=7,
                rotation=25,
                ha="left",
            )
    ax.set_title("Severity timeline elite-initiated событий")
    ax.set_xlabel("Год")
    ax.set_ylabel("Severity")
    ax.set_ylim(0.5, 5.5)
    _set_year_axis(ax)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_core_elite_aging_dashboard(elite_year: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), sharex=True)
    ax_age, ax_share, ax_renewal, ax_count = axes.ravel()

    ax_age.plot(elite_year["year"], elite_year["core_mean_age"], label="mean", linewidth=2)
    ax_age.plot(
        elite_year["year"],
        elite_year["core_weighted_mean_age"],
        label="weighted mean",
        linewidth=2,
    )
    ax_age.set_title("Возраст core elite")
    ax_age.set_ylabel("Возраст, лет")
    ax_age.legend()
    ax_age.grid(True, alpha=0.25)

    ax_share.plot(elite_year["year"], elite_year["core_share_60_plus"], label="60+", linewidth=2)
    ax_share.plot(elite_year["year"], elite_year["core_share_70_plus"], label="70+", linewidth=2)
    ax_share.set_title("Доля старших возрастов")
    ax_share.set_ylabel("Доля")
    ax_share.set_ylim(0, 1)
    ax_share.legend()
    ax_share.grid(True, alpha=0.25)

    ax_renewal.plot(elite_year["year"], elite_year["renewal_5y"], color="#2f7d4f", linewidth=2)
    ax_renewal.set_title("Renewal 5y")
    ax_renewal.set_xlabel("Год")
    ax_renewal.set_ylabel("Доля новых за 5 лет")
    ax_renewal.set_ylim(0, 1)
    ax_renewal.grid(True, alpha=0.25)

    ax_count.plot(elite_year["year"], elite_year["core_elite_count"], color="#6f4e9b", linewidth=2)
    ax_count.set_title("Размер учтенной core elite")
    ax_count.set_xlabel("Год")
    ax_count.set_ylabel("Людей")
    ax_count.grid(True, alpha=0.25)

    for ax in axes.ravel():
        _set_year_axis(ax)

    fig.suptitle("Core elite aging dashboard", fontsize=14)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_ruler_vs_core_age(elite_year: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(elite_year["year"], elite_year["ruler_age"], label="ruler_age", linewidth=2)
    ax.plot(elite_year["year"], elite_year["core_mean_age"], label="core_mean_age", linewidth=2)
    ax.plot(
        elite_year["year"],
        elite_year["core_weighted_mean_age"],
        label="core_weighted_mean_age",
        linewidth=1.8,
        linestyle="--",
    )
    ax.set_title("Возраст правителя и core elite")
    ax.set_xlabel("Год")
    ax.set_ylabel("Возраст, лет")
    _set_year_axis(ax)
    ax.legend()
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _core_person_year_rows(
    persons: pd.DataFrame,
    positions: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    person_columns = ["person_id", "name_ru", "birth_date", "origin_group"]
    for year in range(start_year, end_year + 1):
        target = pd.Timestamp(year=year, month=7, day=1)
        active = active_positions_for_year(positions, year)
        core = active[active["is_core_elite"]].copy()
        if core.empty:
            continue
        core = core.merge(persons[person_columns], on="person_id", how="left")
        core = core.sort_values(["person_id", "influence_weight"], ascending=[True, False])
        core = core.drop_duplicates(subset=["person_id"], keep="first")
        for _, row in core.iterrows():
            rows.append(
                {
                    "year": year,
                    "person_id": row["person_id"],
                    "institution": row["institution"],
                    "influence_weight": row["influence_weight"],
                    "origin_group": row.get("origin_group"),
                    "age": age_on_date(row["birth_date"], target),
                }
            )
    return pd.DataFrame(rows)


def plot_institution_composition(
    persons: pd.DataFrame,
    positions: pd.DataFrame,
    output_path: str | Path,
    start_year: int = 1801,
    end_year: int = 2026,
) -> None:
    path = _prepare_output(output_path)
    person_year = _core_person_year_rows(persons, positions, start_year, end_year)

    fig, ax = plt.subplots(figsize=(14, 7))
    if person_year.empty:
        ax.set_title("Институциональный состав core elite")
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        composition = (
            person_year.pivot_table(
                index="year",
                columns="institution",
                values="influence_weight",
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
            .astype(float)
        )
        totals = composition.sum(axis=1).replace(0, pd.NA)
        shares = composition.div(totals, axis=0).fillna(0)
        shares = shares.reindex(range(start_year, end_year + 1), fill_value=0)
        shares.plot.area(ax=ax, linewidth=0, alpha=0.86)
        ax.set_title("Институциональный состав core elite")
        ax.set_xlabel("Год")
        ax.set_ylabel("Доля influence_weight")
        ax.set_ylim(0, 1)
        _set_year_axis(ax)
        ax.legend(title="institution", loc="upper left", bbox_to_anchor=(1.01, 1.0))
        ax.grid(True, axis="y", alpha=0.25)

    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_period_age_boxplots(
    persons: pd.DataFrame,
    positions: pd.DataFrame,
    period_groups: pd.DataFrame,
    output_path: str | Path,
) -> None:
    path = _prepare_output(output_path)
    if period_groups.empty:
        period_groups = pd.DataFrame(
            [
                {"period_id": "1801_1917", "start_year": 1801, "end_year": 1917},
                {"period_id": "1917_1991", "start_year": 1917, "end_year": 1991},
                {"period_id": "1991_2026", "start_year": 1991, "end_year": 2026},
            ]
        )

    rows: list[dict[str, object]] = []
    for _, period in period_groups.iterrows():
        period_id = str(period["period_id"])
        person_year = _core_person_year_rows(
            persons,
            positions,
            int(period["start_year"]),
            int(period["end_year"]),
        )
        if person_year.empty:
            continue
        for age in person_year["age"].dropna():
            rows.append({"period_id": period_id, "age": age})

    fig, ax = plt.subplots(figsize=(13, 7))
    boxplot_data = pd.DataFrame(rows)
    if boxplot_data.empty:
        ax.set_title("Распределение возраста core elite по периодам")
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        labels = period_groups["period_id"].astype(str).tolist()
        values = [
            boxplot_data.loc[boxplot_data["period_id"] == label, "age"].dropna().tolist()
            for label in labels
        ]
        labels = [label for label, vals in zip(labels, values, strict=False) if vals]
        values = [vals for vals in values if vals]
        ax.boxplot(values, tick_labels=labels, showmeans=True, patch_artist=True)
        ax.set_title("Распределение возраста core elite по периодам")
        ax.set_ylabel("Возраст, лет")
        ax.tick_params(axis="x", rotation=25)
        ax.grid(True, axis="y", alpha=0.25)

    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_biological_vs_political_age(elite_year: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(elite_year["year"], elite_year["ruler_age"], label="biological_age", linewidth=2)
    ax.plot(
        elite_year["year"],
        elite_year["ruler_political_age"],
        label="political_age",
        linewidth=2,
    )
    ax.set_title("Биологический и политический возраст правителя")
    ax.set_xlabel("Год")
    ax.set_ylabel("Возраст, лет")
    _set_year_axis(ax)
    ax.legend()
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_core_elite_age(elite_year: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(elite_year["year"], elite_year["core_mean_age"], label="core_mean_age", linewidth=2)
    ax.plot(
        elite_year["year"],
        elite_year["core_weighted_mean_age"],
        label="core_weighted_mean_age",
        linewidth=2,
    )
    ax.set_title("Средний возраст core elite")
    ax.set_xlabel("Год")
    ax.set_ylabel("Возраст, лет")
    _set_year_axis(ax)
    ax.legend()
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
