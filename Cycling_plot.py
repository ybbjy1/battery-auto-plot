import io
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.ticker import AutoMinorLocator, MaxNLocator

from Nyquist_plot import (
    AXIS_LINEWIDTH,
    MAJOR_TICK_LENGTH,
    MAJOR_TICK_WIDTH,
    MINOR_TICK_LENGTH,
    MINOR_TICK_WIDTH,
    PALETTE,
    figure_to_bytes,
    find_matching_column,
    get_excel_sheet_names,
    normalize_text,
    read_uploaded_file,
)


FONT_FAMILY = ["Arial", "DejaVu Sans", "Microsoft YaHei"]
DEFAULT_WIDTH_CM = 20
FIGURE_HEIGHT_CM = 16
LINEWIDTH = 3
MARKER_SIZE = 12
CE_MARKER_EDGE_WIDTH = 3
ANNOTATION_FONT_SIZE = 20


SERIES_CANDIDATES = ["series", "sample", "legend", "group", "样品", "组别", "图例"]
CYCLE_CANDIDATES = ["cycle", "cycle number", "cycle_number", "cycles", "循环", "循环圈数"]
CAPACITY_CANDIDATES = [
    "capacity",
    "specific capacity",
    "charge capacity",
    "discharge capacity",
    "specific_capacity",
    "mAh g-1",
    "mAh/g",
    "比容量",
    "容量",
]
EFFICIENCY_CANDIDATES = [
    "coulombic efficiency",
    "coulombic_efficiency",
    "ce",
    "efficiency",
    "coulombic efficiency (%)",
    "库伦效率",
    "效率",
]


def setup_plot_font():
    plt.rcParams["font.family"] = "Arial"
    plt.rcParams["mathtext.fontset"] = "custom"
    plt.rcParams["mathtext.rm"] = "Arial"
    plt.rcParams["mathtext.it"] = "Arial:italic"
    plt.rcParams["mathtext.bf"] = "Arial:bold"
    plt.rcParams["mathtext.default"] = "regular"


def figure_to_white_preview_bytes(fig, dpi=160):
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="png",
        dpi=dpi,
        bbox_inches="tight",
        pad_inches=0.45,
        transparent=False,
        facecolor="white",
        edgecolor="white",
    )
    buffer.seek(0)
    return buffer


def create_cycling_template():
    rows = []
    for sample, capacity_start, capacity_drop, efficiency_base in [
        ("Sample 1", 103.0, 2.0, 99.6),
        ("Sample 2", 93.0, 22.0, 99.5),
    ]:
        for cycle in range(1, 101):
            rows.append(
                {
                    "series": sample,
                    "cycle": cycle,
                    "capacity": capacity_start - capacity_drop * (cycle - 1) / 99,
                    "coulombic_efficiency": efficiency_base - 0.15 * np.exp(-cycle / 18),
                }
            )

    buffer = io.BytesIO()
    pd.DataFrame(rows).to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer


def numeric_columns(df):
    columns = []
    for column in df.columns:
        values = pd.to_numeric(df[column], errors="coerce")
        if values.notna().sum() >= 2:
            columns.append(column)
    return columns


def default_column(df, candidates, fallback_index=0):
    match = find_matching_column(list(df.columns), candidates)
    if match is not None:
        return match

    numeric = numeric_columns(df)
    if numeric:
        return numeric[min(fallback_index, len(numeric) - 1)]
    return list(df.columns)[min(fallback_index, len(df.columns) - 1)]


def optional_series_options(df):
    columns = list(df.columns)
    default = find_matching_column(columns, SERIES_CANDIDATES)
    options = ["None"] + columns
    index = options.index(default) if default in columns else 0
    return options, index


def prepare_cycling_data(df, cycle_col, capacity_col, efficiency_col, series_col=None):
    plot_df = df.copy()
    plot_df["_cycle"] = pd.to_numeric(plot_df[cycle_col], errors="coerce")
    plot_df["_capacity"] = pd.to_numeric(plot_df[capacity_col], errors="coerce")
    plot_df["_efficiency"] = pd.to_numeric(plot_df[efficiency_col], errors="coerce")
    if series_col is None:
        plot_df["_series"] = "Sample 1"
    else:
        plot_df["_series"] = plot_df[series_col].map(lambda value: normalize_text(str(value)))

    before = len(plot_df)
    plot_df = plot_df.dropna(subset=["_cycle", "_capacity", "_efficiency", "_series"]).copy()
    dropped = before - len(plot_df)
    if plot_df.empty:
        raise ValueError("No valid rows were found. Check the selected columns.")

    return plot_df.sort_values(["_series", "_cycle"]), dropped


def set_x_limits(ax, x_values):
    x_values = np.asarray(x_values, dtype=float)
    x_max = np.nanmax(x_values)
    ax.set_xlim(0, x_max + 1 if x_max >= 0 else 1)


def set_y_limits(ax, y_values, pad_ratio=0.08):
    y_values = np.asarray(y_values, dtype=float)
    y_min = np.nanmin(y_values)
    y_max = np.nanmax(y_values)
    y_span = y_max - y_min
    if y_span <= 0:
        y_span = max(abs(y_max) * pad_ratio, 1.0)
    y_pad = y_span * pad_ratio
    ax.set_ylim(y_min - y_pad, y_max + y_pad)


def set_efficiency_limits(ax, efficiency_values):
    values = np.asarray(efficiency_values, dtype=float)
    y_min = np.nanmin(values)
    y_max = np.nanmax(values)
    y_span = y_max - y_min
    if y_span <= 0:
        y_span = max(abs(y_max) * 0.02, 1.0)
    pad = y_span * 0.20
    lower = y_min - pad
    upper = y_max + pad
    if 85 <= y_min <= 100 and y_max <= 100.5:
        upper = 100
        lower = min(lower, y_min - 0.4)
    ax.set_ylim(lower, upper)


def style_left_axis(ax, plot_width_cm):
    ax.set_xlabel("Cycle number", fontfamily=FONT_FAMILY, fontsize=24, fontweight="bold", labelpad=6)
    ax.set_ylabel(
        r"Specific capacity (mAh g$^{-1}$)",
        fontsize=24,
        fontweight="bold",
        labelpad=6,
    )

    for side in ("left", "bottom", "top"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_linewidth(AXIS_LINEWIDTH)
        ax.spines[side].set_color("black")
    ax.spines["right"].set_visible(False)

    ax.xaxis.set_major_locator(MaxNLocator(nbins=6, min_n_ticks=4, integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, min_n_ticks=4))
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))

    ax.tick_params(
        axis="both",
        which="major",
        direction="in",
        length=MAJOR_TICK_LENGTH,
        width=MAJOR_TICK_WIDTH,
        bottom=True,
        left=True,
        top=False,
        right=False,
        labelbottom=True,
        labelleft=True,
        labeltop=False,
        labelright=False,
    )
    ax.tick_params(
        axis="both",
        which="minor",
        direction="in",
        length=MINOR_TICK_LENGTH,
        width=MINOR_TICK_WIDTH,
        bottom=True,
        left=True,
        top=False,
        right=False,
    )

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(FONT_FAMILY)
        label.set_fontsize(20)
        label.set_fontweight("bold")

    ax.set_box_aspect(FIGURE_HEIGHT_CM / plot_width_cm)


def style_right_axis(ax2, plot_width_cm):
    ax2.set_ylabel(
        "Coulombic efficiency (%)",
        fontfamily=FONT_FAMILY,
        fontsize=24,
        fontweight="bold",
        labelpad=10,
    )

    for side in ("left", "bottom", "top"):
        ax2.spines[side].set_visible(False)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_linewidth(AXIS_LINEWIDTH)
    ax2.spines["right"].set_color("black")

    ax2.yaxis.set_major_locator(MaxNLocator(nbins=6, min_n_ticks=4))
    ax2.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax2.tick_params(
        axis="y",
        which="major",
        direction="in",
        length=MAJOR_TICK_LENGTH,
        width=MAJOR_TICK_WIDTH,
        right=True,
        left=False,
        labelright=True,
        labelleft=False,
    )
    ax2.tick_params(
        axis="y",
        which="minor",
        direction="in",
        length=MINOR_TICK_LENGTH,
        width=MINOR_TICK_WIDTH,
        right=True,
        left=False,
    )

    for label in ax2.get_yticklabels():
        label.set_fontfamily(FONT_FAMILY)
        label.set_fontsize(20)
        label.set_fontweight("bold")

    ax2.set_box_aspect(FIGURE_HEIGHT_CM / plot_width_cm)


def add_text_annotations(ax, annotations):
    for item in annotations:
        text = normalize_text(item.get("text", ""))
        if not text:
            continue
        ax.text(
            float(item.get("x", 0.1)),
            float(item.get("y", 0.9)),
            text,
            transform=ax.transAxes,
            fontfamily=FONT_FAMILY,
            fontsize=ANNOTATION_FONT_SIZE,
            fontweight="bold",
            color=normalize_text(item.get("color", "black")),
            va="center",
            ha="left",
            linespacing=0.85,
        )


def create_cycling_figure(plot_df, legend_labels, legend_x, legend_y, annotations, plot_width_cm):
    setup_plot_font()
    cm_to_inch = 1 / 2.54
    plot_width_cm = float(plot_width_cm)
    fig, ax = plt.subplots(figsize=(plot_width_cm * cm_to_inch, FIGURE_HEIGHT_CM * cm_to_inch))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax2 = ax.twinx()
    ax2.set_facecolor("none")

    capacity_handles = []
    for series_index, (series_name, group) in enumerate(plot_df.groupby("_series", sort=False)):
        color = PALETTE[series_index % len(PALETTE)]
        legend_label = normalize_text(legend_labels.get(series_name, series_name))
        capacity_line, = ax.plot(
            group["_cycle"],
            group["_capacity"],
            color=color,
            linewidth=LINEWIDTH,
            marker="o",
            markersize=MARKER_SIZE,
            markerfacecolor=color,
            markeredgecolor=color,
            markeredgewidth=0,
            label=legend_label,
            zorder=3,
        )
        capacity_handles.append(capacity_line)

        ax2.plot(
            group["_cycle"],
            group["_efficiency"],
            color=color,
            linewidth=LINEWIDTH,
            marker="o",
            markersize=MARKER_SIZE,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=CE_MARKER_EDGE_WIDTH,
            label="_nolegend_",
            zorder=2,
        )

    set_x_limits(ax, plot_df["_cycle"])
    ax2.set_xlim(ax.get_xlim())
    set_y_limits(ax, plot_df["_capacity"])
    set_efficiency_limits(ax2, plot_df["_efficiency"])

    style_left_axis(ax, plot_width_cm)
    style_right_axis(ax2, plot_width_cm)
    add_text_annotations(ax, annotations)

    ax.legend(
        handles=capacity_handles,
        loc="upper left",
        bbox_to_anchor=(float(legend_x), float(legend_y)),
        frameon=False,
        prop={"family": "Arial", "size": 20, "weight": "bold"},
        handletextpad=0.35,
        labelspacing=0.35,
        borderaxespad=0,
    )

    fig.subplots_adjust(left=0.18, right=0.84, bottom=0.20, top=0.94)
    return fig


def show_cycling_excel_example():
    st.markdown(
        """
        **Excel 格式示例**

        推荐把所有样品放在同一个 Sheet 中，用 `series` 列区分样品。

        必需列：
        - `series`：样品名或图例分组，例如 `NVP@C`
        - `cycle`：循环圈数，对应横轴 `Cycle number`
        - `capacity`：比容量，对应左轴 `Specific capacity (mAh g⁻¹)`
        - `coulombic_efficiency`：库伦效率，对应右轴 `Coulombic efficiency (%)`

        图例只对应容量曲线；库伦效率曲线会自动使用相同颜色，但不会进入图例。
        """
    )
    st.dataframe(
        pd.DataFrame(
            {
                "series": ["Sample 1", "Sample 1", "Sample 2", "Sample 2"],
                "cycle": [1, 2, 1, 2],
                "capacity": [103.0, 102.9, 93.0, 92.6],
                "coulombic_efficiency": [98.0, 99.5, 96.0, 99.4],
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def read_plot_file(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()
    sheet_name = None
    if suffix in (".xlsx", ".xls"):
        sheet_names = get_excel_sheet_names(uploaded_file)
        sheet_name = st.selectbox("Worksheet", sheet_names, key="cycling_sheet")
    return read_uploaded_file(uploaded_file, sheet_name=sheet_name)


def collect_text_annotations(prefix, default_count=0):
    count = st.number_input(
        "文本数量",
        min_value=0,
        max_value=12,
        value=default_count,
        step=1,
        key=f"{prefix}_annotation_count",
    )
    annotations = []
    for index in range(int(count)):
        with st.expander(f"Text {index + 1}", expanded=True):
            text = st.text_input("文本内容", value="", key=f"{prefix}_text_{index}")
            x = st.slider("文本 X 位置", 0.00, 1.00, 0.10, 0.01, key=f"{prefix}_text_x_{index}")
            y = st.slider("文本 Y 位置", 0.00, 1.00, 0.90, 0.01, key=f"{prefix}_text_y_{index}")
            color = st.text_input("文本颜色", value="black", key=f"{prefix}_text_color_{index}")
            annotations.append({"text": text, "x": x, "y": y, "color": color})
    return annotations


def render_cycling_page():
    st.title("Cycling Performance Plot")
    show_cycling_excel_example()
    st.download_button(
        "Download Cycling Excel Template",
        data=create_cycling_template(),
        file_name="cycling_plot_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded_file = st.file_uploader(
        "Upload a CSV, XLSX, or XLS file",
        type=["csv", "xlsx", "xls"],
        key="cycling_upload",
    )
    if uploaded_file is None:
        st.info("上传 Excel 或 CSV 文件后即可生成循环曲线。")
        return

    try:
        df = read_plot_file(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read the file: {exc}")
        return

    left, right = st.columns([0.38, 0.62], gap="large")
    with left:
        st.subheader("Data columns")
        columns = list(df.columns)
        if len(columns) < 3:
            st.error("The file must contain cycle, capacity, and coulombic efficiency columns.")
            return

        cycle_default = default_column(df, CYCLE_CANDIDATES, fallback_index=0)
        capacity_default = default_column(df, CAPACITY_CANDIDATES, fallback_index=1)
        efficiency_default = default_column(df, EFFICIENCY_CANDIDATES, fallback_index=2)
        series_options, series_index = optional_series_options(df)

        cycle_col = st.selectbox("Cycle number column", columns, index=columns.index(cycle_default))
        capacity_col = st.selectbox("Specific capacity column", columns, index=columns.index(capacity_default))
        efficiency_col = st.selectbox(
            "Coulombic efficiency column",
            columns,
            index=columns.index(efficiency_default),
        )
        series_selected = st.selectbox("Series / legend column", series_options, index=series_index)
        series_col = None if series_selected == "None" else series_selected

        try:
            plot_df, dropped = prepare_cycling_data(
                df,
                cycle_col,
                capacity_col,
                efficiency_col,
                series_col,
            )
        except Exception as exc:
            st.error(f"Could not prepare plot data: {exc}")
            return
        if dropped:
            st.warning(f"{dropped} rows were ignored because required numeric data was missing.")

        st.subheader("Figure size")
        plot_width_cm = st.number_input(
            "横轴长度 / 图宽 (cm)",
            min_value=12.0,
            max_value=60.0,
            value=float(DEFAULT_WIDTH_CM),
            step=0.5,
            format="%.1f",
            key="cycling_width_cm",
        )

        st.subheader("Legend")
        legend_labels = {}
        for series_name in plot_df["_series"].drop_duplicates():
            legend_labels[series_name] = st.text_input(
                f"Legend label: {series_name}",
                value=series_name,
                key=f"cycling_legend_{series_name}",
            )
        legend_x = st.slider("图例 X 位置", 0.00, 1.00, 0.05, 0.01, key="cycling_legend_x")
        legend_y = st.slider("图例 Y 位置", 0.00, 1.00, 0.22, 0.01, key="cycling_legend_y")

        st.subheader("Text annotations")
        st.caption("文本位置使用图内比例坐标：0 靠左/靠下，1 靠右/靠上。")
        annotations = collect_text_annotations("cycling")

    with right:
        fig = create_cycling_figure(
            plot_df,
            legend_labels,
            legend_x,
            legend_y,
            annotations,
            plot_width_cm,
        )
        st.subheader("Cycling Performance Plot")
        st.image(
            figure_to_white_preview_bytes(fig),
            use_container_width=False,
            caption="Preview uses a white background. Downloaded PNG/PDF remains transparent.",
        )
        st.subheader("Parsed Data")
        st.dataframe(
            plot_df[["_series", "_cycle", "_capacity", "_efficiency"]].rename(
                columns={
                    "_series": "series",
                    "_cycle": "cycle",
                    "_capacity": "capacity",
                    "_efficiency": "coulombic_efficiency",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        png_bytes = figure_to_bytes(fig, "png", dpi=600)
        pdf_bytes = figure_to_bytes(fig, "pdf", dpi=600)
        download_left, download_right = st.columns(2)
        with download_left:
            st.download_button(
                "Download PNG",
                data=png_bytes,
                file_name="cycling_performance_plot.png",
                mime="image/png",
                use_container_width=True,
            )
        with download_right:
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name="cycling_performance_plot.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        plt.close(fig)
