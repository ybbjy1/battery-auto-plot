"""Redesigned Streamlit entry point.

Run with:
    streamlit run research_platform.py

The original app.py and all original plotting modules remain unchanged.
"""

import streamlit as st

from platform_pages import PAGE_RENDERERS
from platform_ui import inject_platform_css, render_sidebar_brand, sidebar_section


NAVIGATION = {
    "Nyquist 阻抗谱": "Nyquist",
    "Arrhenius 活化能": "Arrhenius",
    "倍率性能": "Rate",
    "循环性能": "Cycling",
}


def main():
    st.set_page_config(
        page_title="ElectroPlot Lab",
        page_icon=":material/ssid_chart:",
        layout="wide",
        initial_sidebar_state="auto",
    )
    inject_platform_css()
    render_sidebar_brand()

    sidebar_section("00", "图类型")
    selected_label = st.sidebar.radio(
        "选择图类型",
        list(NAVIGATION),
        label_visibility="collapsed",
        key="lab_plot_navigation",
    )
    PAGE_RENDERERS[NAVIGATION[selected_label]]()


if __name__ == "__main__":
    main()
