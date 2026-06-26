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
FIGURE_WIDTH_CM = 20
FIGURE_HEIGHT_CM = 16
MARKER_SIZE = 12
MARKER_ALPHA = 1.0
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


def create_rate_template():
    rows = []
    segments = [
        ("0.1C", range(1, 4), 304, 2),
        ("1C", range(4, 9), 280, 2),
        ("2C", range(9, 14), 262, 1),
        ("3C", range(14, 19), 248, 1),
        ("5C", range(19, 24), 215, -1),
        ("1C", range(24, 29), 275, 0),
    ]
    for sample, offset in [("Sample 1", 0), ("Sample 2", -18)]:
        for rate_label, cycles, start_capacity, slope in segments:
            for index, cycle in enumerate(cycles):
                rows.append(
                    {
                        "series": sample,
                        "cycle": cycle,
                        "capacity": start_capacity + offset + slope * index,
                        "rate_step": rate_label,
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


def prepare_rate_data(df, cycle_col, capacity_col, series_col=None):
    plot_df = df.copy()
    plot_df["_row_order"] = np.arange(len(plot_df))
    plot_df["_cycle"] = pd.to_numeric(plot_df[cycle_col], errors="coerce")
    plot_df["_capacity"] = pd.to_numeric(plot_df[capacity_col], errors="coerce")
    if series_col is None:
        plot_df["_series"] = "Sample 1"
    else:
        plot_df["_series"] = plot_df[series_col].map(lambda value: normalize_text(str(value)))

    before = len(plot_df)
    plot_df = plot_df.dropna(subset=["_cycle", "_capacity", "_series"]).copy()
    dropped = before - len(plot_df)
    if plot_df.empty:
        raise ValueError("No valid rows were found. Check the cycle and capacity columns.")

    return plot_df.sort_values("_row_order"), dropped


def looks_numeric(value):
    return pd.to_numeric(pd.Series([value]), errors="coerce").notna().iloc[0]


def restore_headerless_rate_table(df):
    columns = list(df.columns)
    if len(columns) < 3:
        return df

    first_header = normalize_text(str(columns[0]))
    known_headers = {candidate.lower() for candidate in SERIES_CANDIDATES + CYCLE_CANDIDATES + CAPACITY_CANDIDATES}
    header_looks_like_data = (
        first_header.lower() not in known_headers
        and looks_numeric(columns[1])
        and looks_numeric(columns[2])
    )
    if not header_looks_like_data:
        return df

    restored = pd.concat(
        [
            pd.DataFrame([[columns[0], columns[1], columns[2]]], columns=["series", "cycle", "capacity"]),
            df.iloc[:, :3].set_axis(["series", "cycle", "capacity"], axis=1),
        ],
        ignore_index=True,
    )
    for extra_column in df.columns[3:]:
        restored[str(extra_column)] = df[extra_column].reset_index(drop=True)
    return restored


def set_padded_limits(ax, x_values, y_values):
    x_values = np.asarray(x_values, dtype=float)
    y_values = np.asarray(y_values, dtype=float)

    x_max = np.nanmax(x_values)
    ax.set_xlim(0, x_max + 1 if x_max >= 0 else 1)

    y_min = np.nanmin(y_values)
    y_max = np.nanmax(y_values)
    y_span = y_max - y_min
    if y_span <= 0:
        y_span = max(abs(y_max) * 0.08, 1.0)
    y_pad = y_span * 0.12
    ax.set_ylim(y_min - y_pad, y_max + y_pad)


def style_rate_axis(ax):
    ax.set_xlabel("Cycle number", fontfamily=FONT_FAMILY, fontsize=24, fontweight="bold", labelpad=6)
    ax.set_ylabel(
        r"Specific capacity (mAh g$^{-1}$)",
        fontsize=24,
        fontweight="bold",
        labelpad=6,
    )

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(AXIS_LINEWIDTH)
        spine.set_color("black")

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

    ax.set_box_aspect(FIGURE_HEIGHT_CM / FIGURE_WIDTH_CM)


def draw_rate_markers(ax, x_values, y_values, color, label=None, zorder=3):
    ax.scatter(
        x_values,
        y_values,
        s=MARKER_SIZE**2,
        marker="o",
        c=color,
        alpha=MARKER_ALPHA,
        edgecolors="none",
        label=label,
        zorder=zorder,
    )


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


def create_rate_figure(plot_df, legend_labels, legend_x, legend_y, annotations):
    setup_plot_font()
    cm_to_inch = 1 / 2.54
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH_CM * cm_to_inch, FIGURE_HEIGHT_CM * cm_to_inch))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    series_colors = {}
    for series_index, series_name in enumerate(plot_df["_series"].drop_duplicates()):
        series_colors[series_name] = PALETTE[series_index % len(PALETTE)]

    set_padded_limits(ax, plot_df["_cycle"], plot_df["_capacity"])

    for _, row in plot_df.sort_values("_row_order").iterrows():
        series_name = row["_series"]
        row_order = row["_row_order"]
        draw_rate_markers(
            ax,
            [row["_cycle"]],
            [row["_capacity"]],
            series_colors[series_name],
            label=None,
            zorder=3 + row_order * 0.001,
        )

    for series_name in plot_df["_series"].drop_duplicates():
        color = series_colors[series_name]
        legend_label = normalize_text(legend_labels.get(series_name, series_name))
        draw_rate_markers(ax, [], [], color, legend_label)

    style_rate_axis(ax)
    add_text_annotations(ax, annotations)
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(float(legend_x), float(legend_y)),
        frameon=False,
        prop={"family": "Arial", "size": 20, "weight": "bold"},
        handletextpad=0.35,
        labelspacing=0.35,
        borderaxespad=0,
    )

    fig.subplots_adjust(left=0.20, right=0.95, bottom=0.20, top=0.94)
    return fig


def show_rate_excel_example():
    st.markdown(
        """
        **Excel 格式示例**

        推荐把所有样品放在同一个 Sheet 中，用 `series` 列区分样品。

        必需列：
        - `series`：样品名或图例分组，例如 `Sample 1`
        - `cycle`：循环圈数，对应横轴 `Cycle number`
        - `capacity`：比容量，对应左轴 `Specific capacity (mAh g⁻¹)`

        可选列：
        - `rate_step`：倍率标签，例如 `0.1C`、`1C`、`2C`。当前图中文字位置由网页端手动输入和调整。
        """
    )
    st.dataframe(
        pd.DataFrame(
            {
                "series": ["Sample 1", "Sample 1", "Sample 2", "Sample 2"],
                "cycle": [1, 2, 1, 2],
                "capacity": [305, 302, 285, 283],
                "rate_step": ["0.1C", "0.1C", "0.1C", "0.1C"],
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
        sheet_name = st.selectbox("Worksheet", sheet_names, key="rate_sheet")
    return restore_headerless_rate_table(read_uploaded_file(uploaded_file, sheet_name=sheet_name))


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


def render_rate_page():
    st.title("Rate Capability Plot")
    show_rate_excel_example()
    st.download_button(
        "Download Rate Excel Template",
        data=create_rate_template(),
        file_name="rate_plot_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded_file = st.file_uploader(
        "Upload a CSV, XLSX, or XLS file",
        type=["csv", "xlsx", "xls"],
        key="rate_upload",
    )
    if uploaded_file is None:
        st.info("上传 Excel 或 CSV 文件后即可生成倍率曲线。")
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
        if len(columns) < 2:
            st.error("The file must contain at least cycle and capacity columns.")
            return

        cycle_default = default_column(df, CYCLE_CANDIDATES, fallback_index=0)
        capacity_default = default_column(df, CAPACITY_CANDIDATES, fallback_index=1)
        series_options, series_index = optional_series_options(df)

        cycle_col = st.selectbox("Cycle number column", columns, index=columns.index(cycle_default))
        capacity_col = st.selectbox("Specific capacity column", columns, index=columns.index(capacity_default))
        series_selected = st.selectbox("Series / legend column", series_options, index=series_index)
        series_col = None if series_selected == "None" else series_selected

        try:
            plot_df, dropped = prepare_rate_data(df, cycle_col, capacity_col, series_col)
        except Exception as exc:
            st.error(f"Could not prepare plot data: {exc}")
            return
        if dropped:
            st.warning(f"{dropped} rows were ignored because required numeric data was missing.")

        st.subheader("Legend")
        legend_labels = {}
        for series_name in plot_df["_series"].drop_duplicates():
            legend_labels[series_name] = st.text_input(
                f"Legend label: {series_name}",
                value=series_name,
                key=f"rate_legend_{series_name}",
            )
        legend_x = st.slider("图例 X 位置", 0.00, 1.00, 0.84, 0.01, key="rate_legend_x")
        legend_y = st.slider("图例 Y 位置", 0.00, 1.00, 0.96, 0.01, key="rate_legend_y")

        st.subheader("Text annotations")
        st.caption("文本位置使用图内比例坐标：0 靠左/靠下，1 靠右/靠上。")
        annotations = collect_text_annotations("rate")

    with right:
        fig = create_rate_figure(plot_df, legend_labels, legend_x, legend_y, annotations)
        st.subheader("Rate Capability Plot")
        st.image(
            figure_to_white_preview_bytes(fig),
            use_container_width=False,
            caption="Preview uses a white background. Downloaded PNG/PDF remains transparent.",
        )
        st.subheader("Parsed Data")
        st.dataframe(
            plot_df[["_series", "_cycle", "_capacity"]].rename(
                columns={"_series": "series", "_cycle": "cycle", "_capacity": "capacity"}
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
                file_name="rate_capability_plot.png",
                mime="image/png",
                use_container_width=True,
            )
        with download_right:
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name="rate_capability_plot.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        plt.close(fig)
