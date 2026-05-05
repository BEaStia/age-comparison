from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_ID = "russia"


@dataclass(frozen=True)
class DatasetPaths:
    dataset_id: str
    root: Path
    raw: Path
    processed: Path
    figures: Path


def dataset_root(dataset_id: str) -> Path:
    if dataset_id == DEFAULT_DATASET_ID:
        return PROJECT_ROOT / "data"
    return PROJECT_ROOT / "datasets" / dataset_id


def dataset_paths(dataset_id: str) -> DatasetPaths:
    root = dataset_root(dataset_id)
    return DatasetPaths(
        dataset_id=dataset_id,
        root=root,
        raw=root / "raw",
        processed=root / "processed",
        figures=PROJECT_ROOT / "outputs" / ("figures" if dataset_id == DEFAULT_DATASET_ID else dataset_id) / "figures",
    )


def load_period_groups(data: dict[str, pd.DataFrame], dataset_id: str) -> pd.DataFrame:
    periods = data.get("periods", pd.DataFrame())
    if periods is not None and not periods.empty:
        return periods.copy()

    raw_path = dataset_paths(dataset_id).raw
    core_group_paths = sorted(raw_path.glob("core_elite_groups*.csv"))
    frames = [pd.read_csv(path) for path in core_group_paths if path.exists()]
    if frames:
        groups = pd.concat(frames, ignore_index=True)
        if "period_id" in groups.columns:
            groups = groups.drop_duplicates(subset=["period_id"], keep="first")
        sort_columns = [column for column in ["start_year", "end_year", "period_id"] if column in groups.columns]
        if sort_columns:
            groups = groups.sort_values(sort_columns)
        return groups.reset_index(drop=True)
    return pd.DataFrame()


def dataset_year_span(data: dict[str, pd.DataFrame], dataset_id: str, fallback: tuple[int, int] = (1801, 2026)) -> tuple[int, int]:
    periods = data.get("periods", pd.DataFrame())
    if periods is not None and not periods.empty:
        start = pd.to_numeric(periods.get("start_year"), errors="coerce").min()
        end = pd.to_numeric(periods.get("end_year"), errors="coerce").max()
        if pd.notna(start) and pd.notna(end):
            return int(start), int(end)

    group_periods = load_period_groups(data, dataset_id)
    if not group_periods.empty and "start_year" in group_periods.columns and "end_year" in group_periods.columns:
        start = pd.to_numeric(group_periods["start_year"], errors="coerce").min()
        end = pd.to_numeric(group_periods["end_year"], errors="coerce").max()
        if pd.notna(start) and pd.notna(end):
            return int(start), int(end)

    positions = data.get("positions", pd.DataFrame())
    if not positions.empty:
        start_dates = pd.to_datetime(positions.get("start_date"), errors="coerce")
        end_dates = pd.to_datetime(positions.get("end_date"), errors="coerce")
        start = start_dates.dt.year.min()
        end = end_dates.dt.year.max()
        if pd.notna(start) and pd.notna(end):
            return int(start), int(end)

    return fallback
