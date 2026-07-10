import pandas as pd
from pandas import DataFrame

from models import (
    AGG_AXIS_CONFIG,
    AggLevel,
    CLOUD_COVER_BINS,
    CLOUD_COVER_LABELS,
    RESPONSE_KEY_BY_AGG_LEVEL,
    WEATHER_METRIC_COLUMNS,
)


def clean_metrics(payload: dict, agg_level: AggLevel) -> DataFrame:
    """Build a typed, chart-ready DataFrame from a dashboard API payload.

    Numeric metric columns are coerced to float64, and month/week views get
    a human-readable x-axis label synthesized (e.g. "Jan 2024" or "Mar
    2024, Week 09"), since the API only returns the raw date components.

    Args:
        payload: JSON response from the dashboard data endpoint.
        agg_level: Aggregation level the payload was requested at

    Returns:
        A DataFrame
    """
    response_key = RESPONSE_KEY_BY_AGG_LEVEL[agg_level]
    df = pd.DataFrame(payload[response_key])
    df[WEATHER_METRIC_COLUMNS] = df[WEATHER_METRIC_COLUMNS].astype("float64")

    x_axis_col = AGG_AXIS_CONFIG[agg_level]["x_axis"]

    if agg_level == AggLevel.MONTH:
        df[x_axis_col] = _build_month_label(df)
    elif agg_level == AggLevel.WEEK:
        df[x_axis_col] = _build_week_label(df)

    return df


def rollup_to_yearly(monthly_df: DataFrame, agg_map: dict) -> DataFrame:
    """Collapse monthly rows into one row per year for the yearly chart view.

    Args:
        monthly_df: Output of clean_metrics for AggLevel.MONTH, containing
            a 'year_int' column.
        agg_map: Column -> aggregation function mapping (e.g. mean for
            averages, sum for totals) used to combine months within a year.

    Returns:
        A DataFrame with one row per year_int.
    """
    return monthly_df.groupby(by="year_int").agg(agg_map).reset_index()


def _build_month_label(df: DataFrame) -> pd.Series:
    """Derive a "Mon YYYY" label from integer month/year components."""
    return (
        pd.to_datetime(df["month_int"], format="%m").dt.month_name().str[:3]
        + " "
        + df["year_int"].astype(str)
    )


def _build_week_label(df: DataFrame) -> pd.Series:
    """Derive a "Mon YYYY, Week NN" label from ISO year/week components.

    Args:
        df: DataFrame containing 'year_int' and 'week_of_year' columns.

    Returns:
        A Series of formatted week labels aligned to df's index.
    """
    padded_week = df["week_of_year"].astype(str).str.zfill(2)
    iso_string = df["year_int"].astype(str) + padded_week + "1"
    week_start = pd.to_datetime(iso_string, format="%G%V%u")

    return (
        week_start.dt.strftime("%b")
        + " "
        + df["year_int"].astype(str)
        + ", Week "
        + df["week_of_year"].astype(str)
    )


def bucket_cloud_cover(daily_df: DataFrame) -> DataFrame:
    """Classify each day's average cloud cover into a readable sky condition.

    Args:
        daily_df: Daily metrics DataFrame containing 'cloud_cover_mean'.

    Returns:
        A copy of daily_df with an added 'cloud_category' column.
    """
    daily_df = daily_df.copy()
    daily_df["cloud_category"] = pd.cut(
        daily_df["cloud_cover_mean"],
        bins=CLOUD_COVER_BINS,
        labels=CLOUD_COVER_LABELS,
        include_lowest=True,
    )
    return daily_df
