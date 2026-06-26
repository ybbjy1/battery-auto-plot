import streamlit as st

import Nyquist_plot as nyquist_app
from arrhenius_plot import render_arrhenius_page
from Cycling_plot import render_cycling_page
from Rate_plot import render_rate_page


def apply_site_typography():
    st.markdown(
        """
        <style>
        .stApp {
            font-size: 18px;
        }
        h1 {
            font-size: 2.45rem !important;
        }
        h2, h3 {
            font-size: 1.55rem !important;
        }
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] li {
            font-size: 18px !important;
            line-height: 1.55;
        }
        div[data-testid="stWidgetLabel"] p,
        label,
        .stCaptionContainer {
            font-size: 18px !important;
        }
        input,
        textarea,
        div[data-baseweb="select"] span,
        div[data-baseweb="radio"] label,
        div[data-testid="stNumberInput"] input {
            font-size: 18px !important;
        }
        button p,
        div[data-testid="stDownloadButton"] button,
        div[data-testid="stFileUploader"] {
            font-size: 18px !important;
        }
        button[data-baseweb="tab"] p {
            font-size: 20px !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_nyquist_page_inside_tab():
    original_set_page_config = st.set_page_config
    st.set_page_config = lambda *args, **kwargs: None
    try:
        nyquist_app.main()
    finally:
        st.set_page_config = original_set_page_config


def main():
    st.set_page_config(page_title="Electrochemical Plot Generator", layout="wide")
    apply_site_typography()
    st.title("Electrochemical Plot Generator")

    nyquist_tab, arrhenius_tab, rate_tab, cycling_tab = st.tabs(
        ["Nyquist Plot", "Arrhenius Plot", "Rate Plot", "Cycling Plot"]
    )

    with nyquist_tab:
        render_nyquist_page_inside_tab()

    with arrhenius_tab:
        render_arrhenius_page()

    with rate_tab:
        render_rate_page()

    with cycling_tab:
        render_cycling_page()


if __name__ == "__main__":
    main()
