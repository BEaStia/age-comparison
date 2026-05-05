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


def _prepare_output(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _set_year_axis(ax: plt.Axes, tick_step: int = 5) -> None:
    ax.xaxis.set_major_locator(MultipleLocator(tick_step))
    ax.tick_params(axis="x", labelrotation=45, labelsize=8)


def _top_factions(faction_year: pd.DataFrame, top_n: int = 8) -> list[str]:
    if faction_year.empty:
        return []
    return (
        faction_year.groupby("faction_id")["normalized_power_share"]
        .mean()
        .sort_values(ascending=False)
        .head(top_n)
        .index.astype(str)
        .tolist()
    )


def _with_other(faction_year: pd.DataFrame, value_column: str, top_n: int = 8) -> pd.DataFrame:
    if faction_year.empty:
        return faction_year.copy()
    top = set(_top_factions(faction_year, top_n=top_n))
    df = faction_year.copy()
    df["plot_faction_id"] = df["faction_id"].where(df["faction_id"].isin(top), "other")
    grouped = (
        df.groupby(["year", "plot_faction_id"], as_index=False)[value_column]
        .sum()
        .rename(columns={"plot_faction_id": "faction_id"})
    )
    return grouped


def plot_faction_power_share_stacked(
    faction_year: pd.DataFrame,
    output_path: str | Path,
    top_n: int = 8,
    title: str = "Фракционная власть: normalized power share",
) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(14, 7))
    if faction_year.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        plot_data = _with_other(faction_year, "normalized_power_share", top_n=top_n)
        pivot = plot_data.pivot_table(
            index="year",
            columns="faction_id",
            values="normalized_power_share",
            aggfunc="sum",
            fill_value=0,
        ).sort_index()
        pivot.plot.area(ax=ax, linewidth=0, alpha=0.86)
        ax.set_ylim(0, 1)
        ax.legend(title="faction", loc="upper left", bbox_to_anchor=(1.01, 1.0))
    ax.set_title(title)
    ax.set_xlabel("Год")
    ax.set_ylabel("Доля")
    _set_year_axis(ax)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_faction_type_power_share_stacked(
    faction_type_year: pd.DataFrame,
    output_path: str | Path,
    top_n: int = 8,
) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(14, 7))
    if faction_type_year.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        data = faction_type_year.copy()
        top = (
            data.groupby("faction_type")["normalized_power_share"]
            .mean()
            .sort_values(ascending=False)
            .head(top_n)
            .index
        )
        data["plot_faction_type"] = data["faction_type"].where(
            data["faction_type"].isin(top),
            "other",
        )
        plot_data = data.groupby(["year", "plot_faction_type"], as_index=False)[
            "normalized_power_share"
        ].sum()
        pivot = plot_data.pivot_table(
            index="year",
            columns="plot_faction_type",
            values="normalized_power_share",
            aggfunc="sum",
            fill_value=0,
        ).sort_index()
        pivot.plot.area(ax=ax, linewidth=0, alpha=0.86)
        ax.set_ylim(0, 1)
        ax.legend(title="faction_type", loc="upper left", bbox_to_anchor=(1.01, 1.0))
    ax.set_title("Фракционная власть по faction_type")
    ax.set_xlabel("Год")
    ax.set_ylabel("Доля")
    _set_year_axis(ax)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _plot_faction_metric(
    faction_year: pd.DataFrame,
    metric: str,
    title: str,
    output_path: str | Path,
    top_n: int = 8,
) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(14, 7))
    if faction_year.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        top = set(_top_factions(faction_year, top_n=top_n))
        data = faction_year[faction_year["faction_id"].isin(top)].copy()
        for faction_id, group in data.groupby("faction_id"):
            group = group.sort_values("year")
            ax.plot(group["year"], group[metric], label=faction_id, linewidth=1.8)
        ax.legend(title="faction", loc="upper left", bbox_to_anchor=(1.01, 1.0))
    ax.set_title(title)
    ax.set_xlabel("Год")
    ax.set_ylabel("Возраст, лет")
    _set_year_axis(ax)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_faction_mean_age(
    faction_year: pd.DataFrame,
    output_path: str | Path,
    top_n: int = 8,
) -> None:
    _plot_faction_metric(
        faction_year,
        "mean_age",
        "Средний возраст по фракциям",
        output_path,
        top_n=top_n,
    )


def plot_faction_weighted_mean_age(
    faction_year: pd.DataFrame,
    output_path: str | Path,
    top_n: int = 8,
) -> None:
    _plot_faction_metric(
        faction_year,
        "weighted_mean_age",
        "Взвешенный средний возраст по фракциям",
        output_path,
        top_n=top_n,
    )


def plot_faction_fragmentation(fragmentation: pd.DataFrame, output_path: str | Path) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(14, 7))
    if fragmentation.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        ax.plot(
            fragmentation["year"],
            fragmentation["fragmentation_index"],
            color="#6f4e9b",
            linewidth=2,
        )
        ax.set_ylim(0, 1)
    ax.set_title("Индекс фрагментации элиты")
    ax.set_xlabel("Год")
    ax.set_ylabel("1 - sum(share^2)")
    _set_year_axis(ax)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_faction_power_heatmap(
    faction_year: pd.DataFrame,
    output_path: str | Path,
    top_n: int = 8,
) -> None:
    path = _prepare_output(output_path)
    fig, ax = plt.subplots(figsize=(14, 7))
    if faction_year.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
    else:
        plot_data = _with_other(faction_year, "normalized_power_share", top_n=top_n)
        pivot = plot_data.pivot_table(
            index="faction_id",
            columns="year",
            values="normalized_power_share",
            aggfunc="sum",
            fill_value=0,
        )
        order = pivot.mean(axis=1).sort_values(ascending=False).index
        pivot = pivot.loc[order]
        image = ax.imshow(pivot.values, aspect="auto", cmap="YlGnBu", vmin=0, vmax=1)
        years = pivot.columns.astype(int).tolist()
        tick_positions = [i for i, year in enumerate(years) if year % 5 == 0]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([str(years[i]) for i in tick_positions], rotation=45, fontsize=8)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        fig.colorbar(image, ax=ax, label="normalized_power_share")
    ax.set_title("Фракционная власть: heatmap")
    ax.set_xlabel("Год")
    ax.set_ylabel("Фракция")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
