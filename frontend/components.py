import streamlit as st


def weather_kpi_card(
    title: str,
    max_label: str,
    max_value: str,
    min_label: str,
    min_value: str,
    icon: str,
) -> None:
    """Render a titled card presenting a max/min metric pair side by side.

    Args:
        title: Card heading (e.g. "Temperature").
        max_label: Badge text for the left-hand metric (e.g. "Maximum").
        max_value: Pre-formatted value shown under max_label, units included.
        min_label: Badge text for the right-hand metric (e.g. "Minimum").
        min_value: Pre-formatted value shown under min_label, units included.
        icon: Material icon identifier shown on both badges.
    """
    with st.container(border=False):
        st.subheader(title, text_alignment="center")
        col1, col2 = st.columns(2, border=True, vertical_alignment="center")

        col1.badge(max_label, icon=icon, color="red")
        col1.subheader(max_value, text_alignment="center")

        col2.badge(min_label, icon=icon, color="blue")
        col2.subheader(min_value, text_alignment="center")
