import io
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.ticker import AutoMinorLocator, FuncFormatter, MaxNLocator


AXIS_LINEWIDTH = 4
MAJOR_TICK_LENGTH = 8
MINOR_TICK_LENGTH = 3
MAJOR_TICK_WIDTH = 3
MINOR_TICK_WIDTH = 2

PALETTE = [
    "#FF7DC5",
    "#9DD79D",
    "#C2B2D6",
    "#F8F4C0",
    "#9ABBF3",
    "#F8BF92",
    "#B2B791",
    "#B6E4EB",
]


SUPERSCRIPT_MAP = str.maketrans({
    "-": "⁻",
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
})


def normalize_text(value):
    if not isinstance(value, str):
        return value

    replacements = {
        "℃": "°C",
        "Â°C": "°C",
        "â„ƒ": "°C",
        "鈩�": "°C",
        "掳C": "°C",
        "惟": "Ω",
        "Ω cm": "Ω cm",
        "cm虏": "cm²",
    }
    text = value.strip()
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def format_scientific_tick(value, _position=None):
    if pd.isna(value) or value == 0:
        return "0"

    sign = "-" if value < 0 else ""
    absolute = abs(float(value))
    exponent = int(f"{absolute:e}".split("e")[1])
    coefficient = absolute / (10**exponent)

    if coefficient >= 10:
        coefficient /= 10
        exponent += 1

    coefficient_text = f"{coefficient:.3g}".rstrip("0").rstrip(".")
    exponent_text = str(exponent).translate(SUPERSCRIPT_MAP)
    return f"{sign}{coefficient_text}×10{exponent_text}"


def find_default_column(columns, candidates):
    lowered = {str(col).strip().lower(): col for col in columns}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in lowered:
            return lowered[key]
    return columns[0] if len(columns) else None


def numeric_like_columns(df, min_values=2):
    numeric_columns = []
    for column in df.columns:
        numeric_values = pd.to_numeric(df[column], errors="coerce")
        if numeric_values.notna().sum() >= min_values:
            numeric_columns.append(column)
    return numeric_columns


def find_default_xy_columns(df):
    columns = list(df.columns)
    numeric_columns = numeric_like_columns(df)

    x_match = find_matching_column(
        columns,
        ["x", "zreal", "z_real", "z'", "z′", "zre", "re(z)", "real"],
    )
    y_match = find_matching_column(
        columns,
        ["y", "zimag", "z_imag", "z''", "z″", "-z''", "-z″", "im(z)", "imag"],
    )

    x_col = x_match or (numeric_columns[0] if numeric_columns else columns[0])

    if y_match is not None and y_match != x_col:
        y_col = y_match
    else:
        remaining_numeric = [column for column in numeric_columns if column != x_col]
        y_col = remaining_numeric[0] if remaining_numeric else columns[1 if len(columns) > 1 else 0]

    return x_col, y_col


def find_matching_column(columns, candidates):
    lowered = {str(col).strip().lower(): col for col in columns}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in lowered:
            return lowered[key]
    return None


def read_csv_bytes(file_bytes):
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return clean_table(pd.read_csv(io.BytesIO(file_bytes), encoding=encoding))
        except UnicodeDecodeError:
            continue
    return clean_table(pd.read_csv(io.BytesIO(file_bytes)))


def make_unique_columns(columns):
    seen = {}
    unique_columns = []

    for index, column in enumerate(columns):
        text = normalize_text(str(column))
        if not text or text.lower().startswith("unnamed:"):
            text = f"Column {index + 1}"

        count = seen.get(text, 0)
        seen[text] = count + 1
        unique_columns.append(text if count == 0 else f"{text}.{count + 1}")

    return unique_columns


def clean_table(df):
    df = df.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
    df.columns = make_unique_columns(df.columns)

    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].map(normalize_text)

    return df


def read_uploaded_file(uploaded_file, sheet_name=None):
    file_bytes = uploaded_file.getvalue()
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix == ".csv":
        return read_csv_bytes(file_bytes)

    if suffix in (".xlsx", ".xls"):
        return clean_table(pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name))

    raise ValueError("Only CSV, XLSX, and XLS files are supported.")


def get_excel_sheet_names(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    return pd.ExcelFile(io.BytesIO(file_bytes)).sheet_names


def numeric_series(df, column, fixed_value, field_name):
    if column is not None:
        return pd.to_numeric(df[column], errors="coerce")

    if fixed_value is None:
        raise ValueError(f"Please provide a {field_name} column or fixed {field_name} value.")

    return pd.Series([fixed_value] * len(df), index=df.index, dtype="float64")


def prepare_plot_data(
    df,
    x_col,
    y_col,
    series_col,
    annotation_col,
    thickness_col,
    area_col,
    fixed_thickness,
    fixed_area,
    y_mode,
):
    if x_col == y_col:
        raise ValueError(
            "X and Y columns are the same. Select two different impedance columns."
        )

    x = pd.to_numeric(df[x_col], errors="coerce")
    y = pd.to_numeric(df[y_col], errors="coerce")
    thickness = numeric_series(df, thickness_col, fixed_thickness, "thickness")
    area = numeric_series(df, area_col, fixed_area, "area")

    invalid_scale = thickness.isna() | area.isna() | (thickness <= 0) | (area <= 0)
    if invalid_scale.any():
        raise ValueError(
            "Thickness and area must be numeric positive values. "
            f"Invalid rows: {invalid_scale.sum()}."
        )

    plot_df = df.copy()
    plot_df["_x_norm"] = x / (thickness / area)
    raw_y_norm = y / (thickness / area)

    if y_mode == "auto_positive":
        plot_df["_y_norm"] = raw_y_norm.abs()
    elif y_mode == "negate":
        plot_df["_y_norm"] = -raw_y_norm
    elif y_mode == "keep":
        plot_df["_y_norm"] = raw_y_norm
    else:
        raise ValueError(f"Unknown y-axis mode: {y_mode}")

    required = ["_x_norm", "_y_norm"]
    if series_col is not None:
        required.append(series_col)
    if annotation_col is not None:
        required.append(annotation_col)

    before = len(plot_df)
    plot_df = plot_df.dropna(subset=required)
    dropped = before - len(plot_df)

    return plot_df, dropped


def apply_nyquist_style(ax, x_label, y_label):
    ax.set_xlabel(normalize_text(x_label), fontname="Arial", fontsize=24, fontweight="bold")
    ax.set_ylabel(normalize_text(y_label), fontname="Arial", fontsize=24, fontweight="bold")

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(AXIS_LINEWIDTH)

    ax.xaxis.set_major_locator(MaxNLocator(nbins=5, min_n_ticks=4))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5, min_n_ticks=4))
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))

    formatter = FuncFormatter(format_scientific_tick)
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(formatter)

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
        label.set_fontname("Arial")
        label.set_fontsize(20)
        label.set_fontweight("bold")

    for offset_text in (ax.xaxis.get_offset_text(), ax.yaxis.get_offset_text()):
        offset_text.set_fontname("Arial")
        offset_text.set_fontsize(20)
        offset_text.set_fontweight("bold")

    ax.set_box_aspect(16 / 20)


def apply_axis_limits(ax):
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)


def create_nyquist_figure(
    plot_df,
    x_label,
    y_label,
    series_col=None,
    annotation_col=None,
    legend_labels=None,
    single_legend_label=None,
    legend_loc="upper left",
):
    cm_to_inch = 1 / 2.54
    plt.rcParams["font.family"] = "Arial"

    fig, ax = plt.subplots(figsize=(20 * cm_to_inch, 16 * cm_to_inch))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    if series_col is None:
        ax.scatter(
            plot_df["_x_norm"],
            plot_df["_y_norm"],
            s=12**2,
            marker="o",
            c=PALETTE[0],
            edgecolors="none",
            label=normalize_text(single_legend_label) if single_legend_label else None,
        )
        if single_legend_label:
            ax.legend(
                loc=legend_loc,
                frameon=False,
                prop={"family": "Arial", "size": 20, "weight": "bold"},
                handletextpad=0.35,
                labelspacing=0.35,
            )
    else:
        legend_labels = legend_labels or {}
        for index, (series_name, group) in enumerate(plot_df.groupby(series_col, sort=False)):
            legend_label = normalize_text(legend_labels.get(str(series_name), str(series_name)))
            ax.scatter(
                group["_x_norm"],
                group["_y_norm"],
                s=12**2,
                marker="o",
                c=PALETTE[index % len(PALETTE)],
                edgecolors="none",
                label=legend_label,
            )

        ax.legend(
            loc=legend_loc,
            frameon=False,
            prop={"family": "Arial", "size": 20, "weight": "bold"},
            handletextpad=0.35,
            labelspacing=0.35,
        )

    if annotation_col is not None:
        for _, row in plot_df.dropna(subset=[annotation_col]).iterrows():
            ax.annotate(
                normalize_text(str(row[annotation_col])),
                xy=(row["_x_norm"], row["_y_norm"]),
                xytext=(6, 6),
                textcoords="offset points",
                fontname="Arial",
                fontsize=20,
                fontweight="bold",
            )

    apply_axis_limits(ax)
    apply_nyquist_style(ax, x_label, y_label)
    fig.tight_layout()
    return fig


def figure_to_bytes(fig, fmt, dpi=600):
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format=fmt,
        dpi=dpi,
        bbox_inches="tight",
        pad_inches=0.45,
        transparent=True,
        facecolor="none",
        edgecolor="none",
    )
    buffer.seek(0)
    return buffer


def optional_column_select(label, columns, default=None, key=None):
    options = ["None"] + list(columns)
    index = 0
    if default in columns:
        index = options.index(default)

    selected = st.selectbox(label, options, index=index, key=key)
    return None if selected == "None" else selected


def show_excel_format_example():
    st.subheader("Excel 数据格式示例")
    st.markdown(
        """
        请把数据整理在 **同一个 Excel 文件的同一个 Sheet** 中，推荐使用下面这种“长表”格式。
        每一行代表一个阻抗点，多组数据通过 `series` 列区分。

        必需列：
        - `series`：数据组名称，也就是图例分组，例如 `300°C-2h`、`350°C-2h`
        - `x`：横轴原始阻抗数据，对应 `Z'`
        - `y`：纵轴原始阻抗数据，可以是 `Z''`，也可以是已经处理好的 `-Z''`

        可选列：
        - `thickness`：样品厚度，单位 `cm`
        - `area`：样品面积，单位 `cm²`

        如果所有数据使用相同厚度和面积，可以不在 Excel 中写 `thickness` 和 `area`，
        上传后在网页左侧选择固定值即可。若不同组使用不同厚度或面积，则建议在 Excel 中保留这两列。
        """
    )

    example_df = pd.DataFrame(
        {
            "series": [
                "300°C-2h",
                "300°C-2h",
                "350°C-2h",
                "350°C-2h",
                "400°C-2h",
                "400°C-2h",
            ],
            "x": [115.86, 551.93, 302.11, 704.92, 6320.42, 11129.30],
            "y": [1035.86, 617.08, 421.65, 416.42, 29361.88, 40602.05],
            "thickness": [0.10, 0.10, 0.10, 0.10, 0.10, 0.10],
            "area": [1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
        }
    )
    st.dataframe(example_df, use_container_width=True, hide_index=True)
    st.info(
        "不推荐把四组数据分别放在多个 Excel 文件或多个 Sheet 中。"
        "当前网页最稳定的读取方式是：一个 Sheet + 一列 series 分组。"
    )


def main():
    st.set_page_config(page_title="Nyquist Plot Generator", layout="wide")

    st.title("Nyquist Plot Generator")

    show_excel_format_example()

    uploaded_file = st.file_uploader(
        "Upload a CSV, XLSX, or XLS file",
        type=["csv", "xlsx", "xls"],
    )

    if uploaded_file is None:
        st.info("Upload a data file to generate a normalized Nyquist plot.")
        return

    suffix = Path(uploaded_file.name).suffix.lower()

    try:
        sheet_name = None
        if suffix in (".xlsx", ".xls"):
            sheet_names = get_excel_sheet_names(uploaded_file)
            sheet_name = st.selectbox("Worksheet", sheet_names)

        df = read_uploaded_file(uploaded_file, sheet_name=sheet_name)
    except Exception as exc:
        st.error(f"Could not read the uploaded file: {exc}")
        return

    if df.empty:
        st.error("The uploaded table is empty.")
        return

    columns = list(df.columns)
    left, right = st.columns([0.36, 0.64], gap="large")

    with left:
        st.subheader("Data Mapping")

        default_x, default_y = find_default_xy_columns(df)
        default_series = find_matching_column(columns, ["series", "sample", "group", "label"])
        default_annotation = find_matching_column(columns, ["annotation", "note", "point"])
        default_thickness = find_matching_column(columns, ["thickness", "thickness_cm"])
        default_area = find_matching_column(columns, ["area", "area_cm2"])

        x_col = st.selectbox("X column: raw Z'", columns, index=columns.index(default_x))
        y_col = st.selectbox("Y column: raw Z''", columns, index=columns.index(default_y))
        if x_col == y_col:
            st.error("X and Y columns must be different.")

        series_col = optional_column_select(
            "Legend group column",
            columns,
            default_series,
            key="series_col",
        )
        annotation_col = optional_column_select(
            "Annotation column",
            columns,
            default_annotation,
            key="annotation_col",
        )

        st.subheader("Legend")
        legend_labels = {}
        single_legend_label = None
        if series_col is None:
            single_legend_label = st.text_input("Legend text", value="Sample 1")
        else:
            series_values = [str(value) for value in df[series_col].dropna().unique()]
            for index, series_value in enumerate(series_values):
                legend_labels[series_value] = st.text_input(
                    f"Legend text {index + 1}",
                    value=series_value,
                    key=f"legend_label_{index}",
                )
        legend_loc = st.selectbox(
            "Legend position",
            [
                "upper left",
                "upper right",
                "lower left",
                "lower right",
                "center left",
                "center right",
                "upper center",
                "lower center",
                "center",
            ],
            index=0,
        )

        st.subheader("Normalization")
        use_column_scale = st.radio(
            "Thickness and area source",
            ["Use table columns", "Use fixed values"],
            index=0 if default_thickness is not None and default_area is not None else 1,
            horizontal=True,
        )

        thickness_col = None
        area_col = None
        fixed_thickness = None
        fixed_area = None

        if use_column_scale == "Use table columns":
            if default_thickness is None or default_area is None:
                st.warning("Select valid thickness and area columns before plotting.")
            thickness_col = st.selectbox(
                "Thickness column (cm)",
                columns,
                index=columns.index(default_thickness) if default_thickness in columns else 0,
            )
            area_col = st.selectbox(
                "Area column (cm²)",
                columns,
                index=columns.index(default_area) if default_area in columns else 0,
            )
        else:
            fixed_thickness = st.number_input(
                "Fixed thickness (cm)",
                min_value=0.000001,
                value=0.100000,
                format="%.6f",
            )
            fixed_area = st.number_input(
                "Fixed area (cm²)",
                min_value=0.000001,
                value=1.000000,
                format="%.6f",
            )

        y_mode_label = st.radio(
            "Y-axis processing",
            [
                "Auto: plot positive -Z''",
                "Raw column is Z''; multiply by -1",
                "Raw column is already -Z''; keep as is",
            ],
            index=0,
        )
        y_mode = {
            "Auto: plot positive -Z''": "auto_positive",
            "Raw column is Z''; multiply by -1": "negate",
            "Raw column is already -Z''; keep as is": "keep",
        }[y_mode_label]

        st.subheader("Figure Text")
        x_label = st.text_input("X axis label", value="Z' (Ω cm)")
        y_label = st.text_input("Y axis label", value="-Z'' (Ω cm)")

    with right:
        st.subheader("Data Preview")
        st.dataframe(df.head(50), use_container_width=True)

        try:
            plot_df, dropped = prepare_plot_data(
                df=df,
                x_col=x_col,
                y_col=y_col,
                series_col=series_col,
                annotation_col=annotation_col,
                thickness_col=thickness_col,
                area_col=area_col,
                fixed_thickness=fixed_thickness,
                fixed_area=fixed_area,
                y_mode=y_mode,
            )
        except Exception as exc:
            st.error(f"Could not prepare plot data: {exc}")
            return

        if plot_df.empty:
            st.error("No valid rows remain after numeric conversion and normalization.")
            return

        if dropped:
            st.warning(f"Dropped {dropped} row(s) with missing x, y, group, or annotation values.")

        fig = create_nyquist_figure(
            plot_df=plot_df,
            x_label=x_label,
            y_label=y_label,
            series_col=series_col,
            annotation_col=annotation_col,
            legend_labels=legend_labels,
            single_legend_label=single_legend_label,
            legend_loc=legend_loc,
        )

        st.subheader("Nyquist Plot")
        st.pyplot(fig, clear_figure=False, use_container_width=False)

        png_bytes = figure_to_bytes(fig, "png", dpi=600)
        pdf_bytes = figure_to_bytes(fig, "pdf", dpi=600)

        download_left, download_right = st.columns(2)
        with download_left:
            st.download_button(
                "Download PNG",
                data=png_bytes,
                file_name="nyquist_plot.png",
                mime="image/png",
                use_container_width=True,
            )
        with download_right:
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name="nyquist_plot.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        plt.close(fig)


if __name__ == "__main__":
    main()
