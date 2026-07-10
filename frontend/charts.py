import plotly.express as px
import plotly.graph_objects as go
from pandas import DataFrame
from plotly.subplots import make_subplots

from models import (
    AGG_AXIS_CONFIG,
    AggLevel,
    CLOUD_COVER_COLORS,
    CLOUD_COVER_LEGEND_LABELS,
    METRIC_CHART_CONFIG,
    MetricOption,
)


def build_metric_line_chart(
    df: DataFrame, metric: MetricOption, agg_level: AggLevel
) -> go.Figure:
    """Build a multi-series line chart tracking one metric family over time.

    Args:
        df: Output of clean_metrics (optionally rolled up) for agg_level.
        metric: Which metric family (temperature, wind, precipitation) to plot.
        agg_level: Aggregation level, used to pick the x-axis column/label.

    Returns:
        A Plotly line chart with markers and a categorical x-axis.
    """
    agg_info = AGG_AXIS_CONFIG[agg_level]
    metric_info = METRIC_CHART_CONFIG[metric]

    fig = px.line(
        df,
        x=agg_info["x_axis"],
        y=metric_info["y_fields"],
        markers=True,
        title=metric_info["title"],
        labels={
            agg_info["x_axis"]: agg_info["x_label"],
            "value": metric_info["y_label"],
            "variable": "Metric Type",
        },
    )
    fig.update_xaxes(type="category", nticks=10)
    fig.update_yaxes(nticks=5)
    return fig


def build_precipitation_dual_axis_chart(monthly_df: DataFrame) -> go.Figure:
    """Build a combo chart comparing monthly precipitation volume and duration.

    Bars show total precipitation (mm) on the primary axis; an overlaid line
    shows precipitation hours on a secondary axis, letting volume and
    duration be compared despite living on different scales.

    Args:
        monthly_df: Monthly metrics DataFrame with 'month_str',
            'precipitation_sum', and 'precipitation_hours' columns.

    Returns:
        A dual-axis Plotly figure with a range slider on the x-axis.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=monthly_df["month_str"],
            y=monthly_df["precipitation_sum"],
            name="Precipitation Sum (mm)",
            marker_color="rgb(55, 83, 109)",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=monthly_df["month_str"],
            y=monthly_df["precipitation_hours"],
            name="Precipitation Hours",
            mode="lines+markers",
            marker_color="rgb(26, 118, 255)",
            line=dict(width=3),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title_text="Monthly Precipitation: Volume vs. Duration",
        xaxis=dict(type="category", title="Month", rangeslider=dict(visible=True)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="<b>Sum</b> (mm)", secondary_y=False)
    fig.update_yaxes(title_text="<b>Duration</b> (Hours)", secondary_y=True)

    # Default to roughly one year in view when more history is loaded, rather
    # than cramming the entire range into the initial render.
    if len(monthly_df) > 12:
        fig.update_xaxes(range=[0, 11])

    return fig


def build_cloud_cover_bar_chart(daily_df_with_category: DataFrame) -> go.Figure:
    """Build a bar chart of day counts per cloud-cover category.

    Args:
        daily_df_with_category: Daily metrics DataFrame that already has a
            'cloud_category' column (see data_processing.bucket_cloud_cover).

    Returns:
        A Plotly bar chart colored by cloud-cover category.
    """
    counts = daily_df_with_category["cloud_category"].value_counts().reset_index()
    counts["legend_group"] = counts["cloud_category"].map(CLOUD_COVER_LEGEND_LABELS)

    fig = px.bar(
        counts,
        x="cloud_category",
        y="count",
        color="legend_group",
        color_discrete_map=CLOUD_COVER_COLORS,
        title="24-Hour Avg Cloud Coverage",
        labels={"cloud_category": "Cloud cover category", "count": "count"},
    )
    fig.update_layout(
        legend_title_text="Category Ranges",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02),
    )
    fig.update_xaxes(nticks=10)
    fig.update_yaxes(nticks=5)
    return fig


def build_weather_conditions_pie_chart(daily_df: DataFrame) -> go.Figure:
    """Build a donut chart showing each day's dominant weather condition.

    Args:
        daily_df: Daily metrics DataFrame with a 'weather_code_mapping' column.

    Returns:
        A Plotly donut chart (pie with a center hole).
    """
    fig = px.pie(
        daily_df,
        names="weather_code_mapping",
        title="Dominant Weather Impact Events",
        hole=0.4,
        labels={"weather_code_mapping": "Weather Condition", "count": "Number of Days"},
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        insidetextorientation="horizontal",
        hovertemplate="<b>%{label}</b><br>Days: %{value}<br>Percentage: %{percent}<extra></extra>",
    )
    fig.update_layout(
        showlegend=True,
        legend_title_text="Conditions",
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig
