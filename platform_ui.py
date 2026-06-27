"""Shared visual components for the redesigned research platform."""

import base64
from html import escape
from pathlib import Path

import streamlit as st


PLOT_META = {
    "Nyquist": {
        "code": "EIS / 01",
        "title": "Nyquist 阻抗谱",
        "description": "阻抗归一化、分组比较与论文级图件导出",
        "accent": "#2F6FED",
    },
    "Arrhenius": {
        "code": "IONICS / 02",
        "title": "Arrhenius 活化能",
        "description": "由温度阻抗计算电导率、线性拟合与活化能",
        "accent": "#D9684F",
    },
    "Rate": {
        "code": "CELL / 03",
        "title": "倍率性能",
        "description": "多样品倍率容量对比与阶段性数据呈现",
        "accent": "#8B6CCF",
    },
    "Cycling": {
        "code": "CELL / 04",
        "title": "循环性能",
        "description": "比容量与库伦效率双轴长期循环分析",
        "accent": "#239B72",
    },
}


def _embedded_font_css():
    """Embed the open Arial-compatible font so cloud browsers have a stable fallback."""
    font_dir = Path(__file__).resolve().parent / "fonts"
    regular_path = font_dir / "Arimo-Variable.ttf"
    italic_path = font_dir / "Arimo-Italic-Variable.ttf"
    if not regular_path.exists():
        return ""

    regular_data = base64.b64encode(regular_path.read_bytes()).decode("ascii")
    font_faces = [
        f"""
        @font-face {{
            font-family: "Arial Cloud";
            src: url(data:font/ttf;base64,{regular_data}) format("truetype");
            font-style: normal;
            font-weight: 400 700;
            font-display: swap;
        }}
        """
    ]
    if italic_path.exists():
        italic_data = base64.b64encode(italic_path.read_bytes()).decode("ascii")
        font_faces.append(
            f"""
            @font-face {{
                font-family: "Arial Cloud";
                src: url(data:font/ttf;base64,{italic_data}) format("truetype");
                font-style: italic;
                font-weight: 400 700;
                font-display: swap;
            }}
            """
        )
    return "\n".join(font_faces)


def inject_platform_css():
    """Apply the platform theme without changing any plotting code."""
    font_css = _embedded_font_css()
    if font_css:
        st.markdown(f"<style>{font_css}</style>", unsafe_allow_html=True)

    st.markdown(
        """
        <style>
        :root {
            --lab-ink: #142126;
            --lab-muted: #607077;
            --lab-line: #D8E0E3;
            --lab-surface: #FFFFFF;
            --lab-canvas: #F2F5F6;
            --lab-blue: #2F6FED;
            --lab-green: #239B72;
            --lab-coral: #D9684F;
        }

        html, body, .stApp {
            font-family: Arial, "Arial Cloud", sans-serif !important;
            color: var(--lab-ink);
        }

        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp p,
        .stApp li,
        .stApp label,
        .stApp input,
        .stApp textarea,
        .stApp button,
        .stApp [data-testid="stCaptionContainer"],
        .stApp [data-testid="stMetricLabel"],
        .stApp [data-testid="stMetricValue"],
        .stApp [data-baseweb="select"] {
            font-family: Arial, "Arial Cloud", sans-serif !important;
        }

        .stApp {
            background: var(--lab-canvas);
        }

        [data-testid="stHeader"] {
            background: rgba(242, 245, 246, 0.94);
            border-bottom: 1px solid var(--lab-line);
        }

        [data-testid="stSidebar"] {
            background: #101B1F;
            border-right: 1px solid #25363C;
            min-width: 336px;
            max-width: 336px;
        }

        [data-testid="stSidebar"] > div:first-child {
            padding: 1.25rem 1.1rem 2rem;
        }

        [data-testid="stSidebar"] * {
            color: #EEF4F5;
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            color: #D6E0E3 !important;
            font-size: 0.96rem !important;
            font-weight: 650 !important;
        }

        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: #18272C !important;
            border-color: #385057 !important;
            border-radius: 5px !important;
            color: #FFFFFF !important;
        }

        [data-testid="stSidebar"] input:focus,
        [data-testid="stSidebar"] textarea:focus {
            border-color: #79A6FF !important;
            box-shadow: 0 0 0 1px #79A6FF !important;
        }

        [data-testid="stSidebar"] [data-testid="stNumberInputStepDown"],
        [data-testid="stSidebar"] [data-testid="stNumberInputStepUp"] {
            background: #24383E !important;
            color: #8DB4FF !important;
            border-left: 1px solid #456069 !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] [data-testid="stNumberInputStepDown"] svg,
        [data-testid="stSidebar"] [data-testid="stNumberInputStepUp"] svg {
            color: inherit !important;
            fill: currentColor !important;
        }

        [data-testid="stSidebar"] [data-testid="stNumberInputStepDown"]:disabled,
        [data-testid="stSidebar"] [data-testid="stNumberInputStepUp"]:disabled {
            background: #1A2A2F !important;
            color: #71878D !important;
            cursor: not-allowed;
        }

        [data-testid="stSidebar"] [data-testid="stNumberInputStepDown"]:not(:disabled):hover,
        [data-testid="stSidebar"] [data-testid="stNumberInputStepUp"]:not(:disabled):hover {
            background: #75A3FF !important;
            color: #101B1F !important;
        }

        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
            background: #17262B;
            border: 1px dashed #527078;
            border-radius: 6px;
            padding: 0.8rem;
        }

        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
            background: #EFF4F5;
            color: #132126;
            border: 0;
        }

        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button *,
        [data-testid="stSidebar"] .stDownloadButton button * {
            color: #132126 !important;
        }

        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) > div:first-child {
            border-color: #75A3FF !important;
            background: #75A3FF !important;
        }

        [data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) > div:first-child > div {
            background: #101B1F !important;
        }

        [data-testid="stSidebar"] details {
            background: #142328;
            border: 1px solid #2E444B;
            border-radius: 6px;
        }

        [data-testid="stSidebar"] hr {
            border-color: #2B3D43;
        }

        [data-testid="stSidebar"] .stDownloadButton button {
            min-height: 42px;
            background: #F4F8F9;
            color: #142126 !important;
            border: 0;
            border-radius: 5px;
            font-weight: 750;
        }

        [data-testid="stSidebar"] .stDownloadButton button:hover {
            background: #DCE8EA;
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1440px;
            padding: 2.15rem 2.6rem 4rem;
        }

        h1, h2, h3 {
            font-family: "Bahnschrift", "Arial", sans-serif;
            letter-spacing: 0;
            color: var(--lab-ink);
        }

        p, li, label, [data-testid="stCaptionContainer"] {
            font-size: 1.02rem;
            line-height: 1.55;
        }

        button, input, textarea, [data-baseweb="select"] {
            font-size: 1rem !important;
        }

        button {
            border-radius: 5px !important;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--lab-line);
            border-radius: 6px;
            overflow: hidden;
        }

        [data-testid="stMetric"] {
            background: transparent;
            border-left: 3px solid #A9B8BD;
            padding: 0.1rem 0 0.1rem 0.9rem;
        }

        [data-testid="stMetricLabel"] {
            color: var(--lab-muted);
        }

        [data-testid="stMetricValue"] {
            font-family: "Bahnschrift", "Arial", sans-serif;
            color: var(--lab-ink);
        }

        [data-baseweb="tab-list"] {
            gap: 1.4rem;
            border-bottom: 1px solid var(--lab-line);
        }

        [data-baseweb="tab"] {
            padding: 0.7rem 0.15rem 0.8rem;
            font-size: 1rem;
            font-weight: 720;
        }

        [data-baseweb="tab-highlight"] {
            background-color: var(--lab-blue);
        }

        .lab-brand {
            padding: 0.15rem 0 1.05rem;
            border-bottom: 1px solid #2B3D43;
            margin-bottom: 1rem;
        }

        .lab-brand__mark {
            display: flex;
            align-items: center;
            gap: 0.65rem;
        }

        .lab-brand__signal {
            display: grid;
            grid-template-columns: repeat(5, 3px);
            align-items: end;
            gap: 3px;
            height: 23px;
        }

        .lab-brand__signal span {
            display: block;
            width: 3px;
            background: #75A3FF;
            animation: labSignal 1.8s ease-in-out infinite;
        }

        .lab-brand__signal span:nth-child(1) { height: 7px; animation-delay: 0ms; }
        .lab-brand__signal span:nth-child(2) { height: 15px; animation-delay: 100ms; }
        .lab-brand__signal span:nth-child(3) { height: 22px; animation-delay: 200ms; }
        .lab-brand__signal span:nth-child(4) { height: 12px; animation-delay: 300ms; }
        .lab-brand__signal span:nth-child(5) { height: 5px; animation-delay: 400ms; }

        .lab-brand__name {
            font-family: Arial, "Arial Cloud", sans-serif;
            color: #FFFFFF;
            font-size: 1.22rem;
            font-weight: 760;
        }

        .lab-brand__caption {
            color: #91A5AB;
            font-family: Arial, "Arial Cloud", sans-serif;
            font-size: 0.72rem;
            margin-top: 0.4rem;
        }

        .lab-side-section {
            margin: 1.3rem 0 0.55rem;
            color: #8FA3A9;
            font-family: Arial, "Arial Cloud", sans-serif;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .lab-page-head {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: end;
            gap: 2rem;
            padding: 0.25rem 0 1.45rem;
            border-bottom: 1px solid var(--lab-line);
            animation: labDeckIn 420ms cubic-bezier(.2,.8,.2,1) both;
        }

        .lab-page-head__code {
            font-family: Arial, "Arial Cloud", sans-serif;
            color: var(--page-accent);
            font-size: 0.78rem;
            font-weight: 800;
            margin-bottom: 0.55rem;
        }

        .lab-page-head h1 {
            font-size: clamp(2rem, 4vw, 3.35rem);
            line-height: 1.02;
            margin: 0;
        }

        .lab-page-head p {
            color: var(--lab-muted);
            margin: 0.65rem 0 0;
            font-size: 1.08rem;
        }

        .lab-page-head__stamp {
            min-width: 164px;
            padding: 0.75rem 0 0.2rem;
            border-top: 3px solid var(--page-accent);
            text-align: right;
            font-family: Arial, "Arial Cloud", sans-serif;
            color: #4E6067;
            font-size: 0.76rem;
            line-height: 1.6;
        }

        .lab-section-title {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 1.55rem 0 0.75rem;
            color: #41535A;
            font-family: Arial, "Arial Cloud", sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .lab-section-title::after {
            content: "";
            height: 1px;
            flex: 1;
            background: var(--lab-line);
        }

        .lab-result {
            margin-top: 1.1rem;
            padding: 1rem 1.1rem 0.25rem;
            background: var(--lab-surface);
            border: 1px solid var(--lab-line);
            border-radius: 6px;
            animation: labResultIn 520ms 80ms cubic-bezier(.2,.8,.2,1) both;
        }

        .lab-empty {
            min-height: 355px;
            display: grid;
            place-items: center;
            text-align: center;
            border: 1px dashed #B8C5C9;
            background: #F8FAFA;
            border-radius: 6px;
            margin-top: 1.2rem;
            padding: 2.5rem;
        }

        .lab-empty__trace {
            width: 112px;
            height: 34px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            margin: 0 auto 1.1rem;
        }

        .lab-empty__trace span {
            width: 4px;
            background: #2F6FED;
            opacity: 0.8;
            animation: labSignal 1.7s ease-in-out infinite;
        }

        .lab-empty__trace span:nth-child(1) { height: 6px; }
        .lab-empty__trace span:nth-child(2) { height: 13px; animation-delay: 80ms; }
        .lab-empty__trace span:nth-child(3) { height: 27px; animation-delay: 160ms; }
        .lab-empty__trace span:nth-child(4) { height: 17px; animation-delay: 240ms; }
        .lab-empty__trace span:nth-child(5) { height: 8px; animation-delay: 320ms; }

        .lab-empty h3 {
            margin: 0;
            font-size: 1.45rem;
        }

        .lab-empty p {
            color: var(--lab-muted);
            margin: 0.55rem 0 0;
        }

        @keyframes labDeckIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes labResultIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes labSignal {
            0%, 100% { transform: scaleY(0.72); opacity: 0.55; }
            50% { transform: scaleY(1); opacity: 1; }
        }

        @media (max-width: 900px) {
            [data-testid="stMainBlockContainer"] {
                padding: 1.25rem 1rem 3rem 3.25rem;
            }
            .lab-page-head {
                grid-template-columns: 1fr;
                gap: 0.8rem;
            }
            .lab-page-head h1 {
                font-size: 2rem;
            }
            .lab-page-head__stamp {
                text-align: left;
                max-width: 220px;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand():
    st.sidebar.markdown(
        """
        <div class="lab-brand">
            <div class="lab-brand__mark">
                <div class="lab-brand__signal" aria-hidden="true">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
                <div class="lab-brand__name">ElectroPlot Lab</div>
            </div>
            <div class="lab-brand__caption">BATTERY DATA / FIGURE WORKSPACE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_section(step, title):
    st.sidebar.markdown(
        f'<div class="lab-side-section">{escape(step)} / {escape(title)}</div>',
        unsafe_allow_html=True,
    )


def render_page_header(plot_name):
    meta = PLOT_META[plot_name]
    st.markdown(
        f"""
        <section class="lab-page-head" style="--page-accent: {meta["accent"]};">
            <div>
                <div class="lab-page-head__code">{meta["code"]}</div>
                <h1>{meta["title"]}</h1>
                <p>{meta["description"]}</p>
            </div>
            <div class="lab-page-head__stamp">
                OUTPUT / PNG + PDF<br>
                TYPOGRAPHY / ARIAL<br>
                STATUS / READY
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def section_title(text):
    st.markdown(f'<div class="lab-section-title">{escape(text)}</div>', unsafe_allow_html=True)


def render_empty_state(title="等待实验数据", body="在左侧控制台上传 CSV、XLSX 或 XLS 文件。"):
    bars = "<span></span>" * 5
    st.markdown(
        f"""
        <div class="lab-empty">
            <div>
                <div class="lab-empty__trace" aria-hidden="true">{bars}</div>
                <h3>{escape(title)}</h3>
                <p>{escape(body)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_metrics(row_count, column_count, series_count, valid_count=None):
    columns = st.columns(4 if valid_count is not None else 3)
    columns[0].metric("数据行", f"{row_count:,}")
    columns[1].metric("数据列", f"{column_count:,}")
    columns[2].metric("样品组", f"{series_count:,}")
    if valid_count is not None:
        columns[3].metric("有效点", f"{valid_count:,}")
