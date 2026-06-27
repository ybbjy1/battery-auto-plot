"""Frontend adapters that reuse the existing plotting and calculation functions."""

import io
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

import Cycling_plot as cycling
import Nyquist_plot as nyquist
import Rate_plot as rate
import arrhenius_plot as arrhenius
from platform_ui import (
    render_data_metrics,
    render_empty_state,
    render_page_header,
    section_title,
    sidebar_section,
)


FILE_TYPES = ["csv", "xlsx", "xls"]
STANDARD_FIGURE_WIDTH_CM = 20
STANDARD_FIGURE_HEIGHT_CM = 16
AXIS_TITLE_SIZE = 24
TICK_AND_LEGEND_SIZE = 20
AXIS_TITLE_PAD = 4
LEGEND_LOCATIONS = {
    "左上": "upper left",
    "右上": "upper right",
    "左下": "lower left",
    "右下": "lower right",
    "左侧居中": "center left",
    "右侧居中": "center right",
    "顶部居中": "upper center",
    "底部居中": "lower center",
}


def _as_bytes(buffer):
    return buffer.getvalue() if hasattr(buffer, "getvalue") else buffer


def _white_preview(fig, dpi=170):
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="png",
        dpi=dpi,
        transparent=False,
        facecolor="white",
        edgecolor="white",
    )
    buffer.seek(0)
    return buffer


def _standardize_figure_canvas(fig):
    """Use the Nyquist figure size for Nyquist, Arrhenius, and rate plots."""
    fig.set_size_inches(
        STANDARD_FIGURE_WIDTH_CM / 2.54,
        STANDARD_FIGURE_HEIGHT_CM / 2.54,
        forward=True,
    )


def _standardize_arrhenius_typography(fig):
    """Match Arrhenius labels, ticks, and annotations to the Nyquist typography."""
    if not fig.axes:
        return

    main_ax = fig.axes[0]
    main_ax.xaxis.label.set_fontfamily("Arial")
    main_ax.xaxis.label.set_fontsize(AXIS_TITLE_SIZE)
    main_ax.xaxis.label.set_fontweight("bold")
    main_ax.xaxis.labelpad = AXIS_TITLE_PAD
    main_ax.yaxis.label.set_fontfamily("Arial")
    main_ax.yaxis.label.set_fontsize(AXIS_TITLE_SIZE)
    main_ax.yaxis.label.set_fontweight("bold")
    main_ax.yaxis.labelpad = AXIS_TITLE_PAD

    for label in main_ax.get_xticklabels() + main_ax.get_yticklabels():
        label.set_fontfamily("Arial")
        label.set_fontsize(TICK_AND_LEGEND_SIZE)
        label.set_fontweight("bold")
    for text in main_ax.texts:
        text.set_fontfamily("Arial")
        text.set_fontsize(TICK_AND_LEGEND_SIZE)
        text.set_fontweight("bold")

    if len(fig.axes) > 1:
        top_ax = fig.axes[1]
        top_ax.xaxis.label.set_fontfamily("Arial")
        top_ax.xaxis.label.set_fontsize(AXIS_TITLE_SIZE)
        top_ax.xaxis.label.set_fontweight("bold")
        top_ax.xaxis.labelpad = AXIS_TITLE_PAD
        for label in top_ax.get_xticklabels():
            label.set_fontfamily("Arial")
            label.set_fontsize(TICK_AND_LEGEND_SIZE)
            label.set_fontweight("bold")


def _figure_bytes(fig, output_format, dpi=600):
    """Export without tight cropping so the physical canvas size stays fixed."""
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format=output_format,
        dpi=dpi,
        transparent=True,
        facecolor="none",
        edgecolor="none",
    )
    buffer.seek(0)
    return buffer.getvalue()


def _render_downloads(fig, file_stem):
    png_bytes = _figure_bytes(fig, "png", dpi=600)
    pdf_bytes = _figure_bytes(fig, "pdf", dpi=600)

    sidebar_section("05", "导出图件")
    st.sidebar.download_button(
        "下载 PNG",
        data=png_bytes,
        file_name=f"{file_stem}.png",
        mime="image/png",
        width="stretch",
        icon=":material/download:",
        key=f"{file_stem}_png_download",
    )
    st.sidebar.download_button(
        "下载 PDF",
        data=pdf_bytes,
        file_name=f"{file_stem}.pdf",
        mime="application/pdf",
        width="stretch",
        icon=":material/picture_as_pdf:",
        key=f"{file_stem}_pdf_download",
    )


def _render_workspace(preview, data_df, series_count, display_columns=None, summary_df=None):
    section_title("实验数据概览")
    render_data_metrics(
        row_count=len(data_df),
        column_count=len(data_df.columns),
        series_count=series_count,
        valid_count=len(data_df),
    )

    section_title("分析工作区")
    tab_labels = ["绘图结果", "数据预览"]
    if summary_df is not None:
        tab_labels.append("拟合结果")
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        with st.container(border=True):
            st.image(preview, width="stretch")

    with tabs[1]:
        preview_df = data_df
        if display_columns:
            existing = [column for column in display_columns if column in data_df.columns]
            if existing:
                preview_df = data_df[existing]
        st.dataframe(preview_df, width="stretch", hide_index=True, height=430)

    if summary_df is not None:
        with tabs[2]:
            st.dataframe(summary_df, width="stretch", hide_index=True)


def _annotation_controls(prefix):
    count = st.number_input(
        "文字说明数量",
        min_value=0,
        max_value=12,
        value=0,
        step=1,
        key=f"{prefix}_annotation_count_v2",
    )
    annotations = []
    for index in range(int(count)):
        with st.expander(f"文字说明 {index + 1}", expanded=index == 0):
            text = st.text_area(
                "内容",
                value="",
                key=f"{prefix}_annotation_text_v2_{index}",
            )
            x = st.slider(
                "横向位置",
                0.0,
                1.0,
                0.10,
                0.01,
                key=f"{prefix}_annotation_x_v2_{index}",
            )
            y = st.slider(
                "纵向位置",
                0.0,
                1.0,
                0.90,
                0.01,
                key=f"{prefix}_annotation_y_v2_{index}",
            )
            color = st.text_input(
                "颜色",
                value="black",
                key=f"{prefix}_annotation_color_v2_{index}",
            )
            annotations.append({"text": text, "x": x, "y": y, "color": color})
    return annotations


def _read_general_file(uploaded_file, sheet_key):
    suffix = Path(uploaded_file.name).suffix.lower()
    sheet_name = None
    if suffix in (".xlsx", ".xls"):
        sheet_names = nyquist.get_excel_sheet_names(uploaded_file)
        sheet_name = st.selectbox("工作表", sheet_names, key=sheet_key)
    return nyquist.read_uploaded_file(uploaded_file, sheet_name=sheet_name)


def _optional_column(label, columns, default, key):
    options = ["不使用"] + list(columns)
    index = options.index(default) if default in columns else 0
    selected = st.selectbox(label, options, index=index, key=key)
    return None if selected == "不使用" else selected


def render_nyquist_page():
    render_page_header("Nyquist")

    sidebar_section("01", "导入数据")
    uploaded_file = st.sidebar.file_uploader(
        "实验数据文件",
        type=FILE_TYPES,
        key="lab_nyquist_upload",
        help="支持 CSV、XLSX 和 XLS。",
    )
    if uploaded_file is None:
        render_empty_state()
        return

    try:
        with st.sidebar:
            df = _read_general_file(uploaded_file, "lab_nyquist_sheet")
    except Exception as exc:
        st.error(f"文件读取失败：{exc}")
        return
    if df.empty:
        st.error("上传的数据表为空。")
        return

    columns = list(df.columns)
    default_x, default_y = nyquist.find_default_xy_columns(df)
    default_series = nyquist.find_matching_column(columns, ["series", "sample", "group", "label"])
    default_annotation = nyquist.find_matching_column(columns, ["annotation", "note", "point"])
    default_thickness = nyquist.find_matching_column(columns, ["thickness", "thickness_cm"])
    default_area = nyquist.find_matching_column(columns, ["area", "area_cm2"])

    sidebar_section("02", "数据列映射")
    x_col = st.sidebar.selectbox(
        "Z' 数据列",
        columns,
        index=columns.index(default_x),
        key="lab_nyquist_x",
    )
    y_col = st.sidebar.selectbox(
        "Z'' 数据列",
        columns,
        index=columns.index(default_y),
        key="lab_nyquist_y",
    )
    series_col = _optional_column(
        "样品分组列",
        columns,
        default_series,
        "lab_nyquist_series",
    )
    annotation_col = _optional_column(
        "点标注列",
        columns,
        default_annotation,
        "lab_nyquist_annotation",
    )
    if x_col == y_col:
        st.error("Z' 与 Z'' 必须选择不同的数据列。")
        return

    sidebar_section("03", "归一化与坐标")
    source_options = ["使用固定值", "使用表格列"]
    source_index = 1 if default_thickness is not None and default_area is not None else 0
    scale_source = st.sidebar.radio(
        "厚度与面积来源",
        source_options,
        index=source_index,
        key="lab_nyquist_scale_source",
    )

    thickness_col = area_col = fixed_thickness = fixed_area = None
    if scale_source == "使用表格列":
        thickness_col = st.sidebar.selectbox(
            "厚度列 (cm)",
            columns,
            index=columns.index(default_thickness) if default_thickness in columns else 0,
            key="lab_nyquist_thickness_col",
        )
        area_col = st.sidebar.selectbox(
            "面积列 (cm²)",
            columns,
            index=columns.index(default_area) if default_area in columns else 0,
            key="lab_nyquist_area_col",
        )
    else:
        fixed_thickness = st.sidebar.number_input(
            "固定厚度 (cm)",
            min_value=0.000001,
            value=0.100000,
            format="%.6f",
            key="lab_nyquist_thickness",
        )
        fixed_area = st.sidebar.number_input(
            "固定面积 (cm²)",
            min_value=0.000001,
            value=1.000000,
            format="%.6f",
            key="lab_nyquist_area",
        )

    y_mode_label = st.sidebar.selectbox(
        "虚部处理",
        ["自动转为正值 -Z''", "Z'' 乘以 -1", "数据已是 -Z''"],
        key="lab_nyquist_y_mode",
    )
    y_mode = {
        "自动转为正值 -Z''": "auto_positive",
        "Z'' 乘以 -1": "negate",
        "数据已是 -Z''": "keep",
    }[y_mode_label]
    x_label = st.sidebar.text_input("横轴标题", "Z' (Ω cm)", key="lab_nyquist_xlabel")
    y_label = st.sidebar.text_input("纵轴标题", "-Z'' (Ω cm)", key="lab_nyquist_ylabel")

    try:
        plot_df, dropped = nyquist.prepare_plot_data(
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
        st.error(f"数据处理失败：{exc}")
        return
    if plot_df.empty:
        st.error("数值转换后没有可绘制的数据。")
        return

    sidebar_section("04", "图形参数")
    legend_labels = {}
    single_legend_label = None
    if series_col is None:
        single_legend_label = st.sidebar.text_input(
            "图例名称",
            "Sample 1",
            key="lab_nyquist_single_legend",
        )
        series_count = 1
    else:
        series_values = [str(value) for value in plot_df[series_col].dropna().unique()]
        series_count = len(series_values)
        with st.sidebar.expander("图例名称", expanded=True):
            for index, series_value in enumerate(series_values):
                legend_labels[series_value] = st.text_input(
                    f"样品 {index + 1}",
                    value=series_value,
                    key=f"lab_nyquist_legend_{index}",
                )
    legend_label = st.sidebar.selectbox(
        "图例位置",
        list(LEGEND_LOCATIONS),
        key="lab_nyquist_legend_location",
    )

    if dropped:
        st.warning(f"已忽略 {dropped} 行缺失或无效数据。")

    try:
        fig = nyquist.create_nyquist_figure(
            plot_df=plot_df,
            x_label=x_label,
            y_label=y_label,
            series_col=series_col,
            annotation_col=annotation_col,
            legend_labels=legend_labels,
            single_legend_label=single_legend_label,
            legend_loc=LEGEND_LOCATIONS[legend_label],
        )
        _standardize_figure_canvas(fig)
        preview = _white_preview(fig)
        _render_downloads(fig, "nyquist_plot")
        _render_workspace(preview, plot_df, series_count)
    finally:
        if "fig" in locals():
            plt.close(fig)


def _arrhenius_from_excel(df):
    columns = list(df.columns)
    candidates = {
        "series": ["series", "sample", "group", "样品"],
        "temperature": ["temperature_c", "temperature", "temp", "温度"],
        "resistance": ["resistance_ohm", "resistance", "阻抗", "电阻"],
        "thickness": ["thickness_cm", "thickness", "厚度"],
        "area": ["area_cm2", "area", "面积"],
    }
    defaults = {
        name: nyquist.find_matching_column(columns, values)
        for name, values in candidates.items()
    }

    sidebar_section("02", "数据列映射")
    selected = {}
    labels = {
        "series": "样品分组列",
        "temperature": "温度列 (°C)",
        "resistance": "阻抗列 (Ω)",
        "thickness": "厚度列 (cm)",
        "area": "面积列 (cm²)",
    }
    for fallback, name in enumerate(("series", "temperature", "resistance", "thickness", "area")):
        default = defaults[name]
        index = columns.index(default) if default in columns else min(fallback, len(columns) - 1)
        selected[name] = st.sidebar.selectbox(
            labels[name],
            columns,
            index=index,
            key=f"lab_arrhenius_{name}_column",
        )

    working = df.copy()
    for target in ("temperature", "resistance", "thickness", "area"):
        working[f"_{target}"] = pd.to_numeric(working[selected[target]], errors="coerce")
    working["_series"] = working[selected["series"]].map(lambda value: nyquist.normalize_text(str(value)))
    working = working.dropna(
        subset=["_series", "_temperature", "_resistance", "_thickness", "_area"]
    )
    if working.empty:
        raise ValueError("所选数据列中没有有效数值。")

    show_annotations = st.sidebar.checkbox(
        "显示样品名和活化能",
        value=True,
        key="lab_arrhenius_excel_annotations",
    )
    series_inputs = []
    positions = [(0.61, 0.70), (0.22, 0.28), (0.61, 0.47), (0.22, 0.52)]
    sidebar_section("03", "样品与标注")
    for index, (series_name, group) in enumerate(working.groupby("_series", sort=False)):
        with st.sidebar.expander(f"样品 {index + 1}", expanded=index == 0):
            label = st.text_input(
                "图例名称",
                value=series_name,
                key=f"lab_arrhenius_excel_label_{index}",
            )
            resistances = {}
            for temperature in arrhenius.TEMPERATURES_C:
                match = group[np.isclose(group["_temperature"], temperature)]
                if match.empty:
                    raise ValueError(f"{series_name} 缺少 {temperature}°C 的阻抗数据。")
                resistances[temperature] = float(match["_resistance"].iloc[0])
            default_x, default_y = positions[index % len(positions)]
            annotation_x = default_x
            annotation_y = default_y
            if show_annotations:
                annotation_x = st.slider(
                    "标注横向位置",
                    0.0,
                    1.0,
                    float(default_x),
                    0.01,
                    key=f"lab_arrhenius_excel_x_{index}",
                )
                annotation_y = st.slider(
                    "标注纵向位置",
                    0.0,
                    1.0,
                    float(default_y),
                    0.01,
                    key=f"lab_arrhenius_excel_y_{index}",
                )
            series_inputs.append(
                {
                    "label": label,
                    "thickness_cm": float(group["_thickness"].iloc[0]),
                    "area_cm2": float(group["_area"].iloc[0]),
                    "resistances": resistances,
                    "annotation_x": annotation_x,
                    "annotation_y": annotation_y,
                }
            )
    return series_inputs, show_annotations


def _arrhenius_manual_inputs():
    sidebar_section("02", "样品参数")
    series_count = st.sidebar.number_input(
        "样品数量",
        min_value=1,
        max_value=8,
        value=1,
        step=1,
        key="lab_arrhenius_series_count",
    )
    show_annotations = st.sidebar.checkbox(
        "显示样品名和活化能",
        value=True,
        key="lab_arrhenius_manual_annotations",
    )
    positions = [(0.61, 0.70), (0.22, 0.28), (0.61, 0.47), (0.22, 0.52)]
    series_inputs = []
    for index in range(int(series_count)):
        with st.sidebar.expander(f"样品 {index + 1}", expanded=index == 0):
            label = st.text_input(
                "图例名称",
                value=f"Sample {index + 1}",
                key=f"lab_arrhenius_manual_label_{index}",
            )
            thickness = st.number_input(
                "电解质片厚度 (cm)",
                min_value=0.000001,
                value=0.100000,
                format="%.6f",
                key=f"lab_arrhenius_manual_thickness_{index}",
            )
            area = st.number_input(
                "电解质片面积 (cm²)",
                min_value=0.000001,
                value=1.000000,
                format="%.6f",
                key=f"lab_arrhenius_manual_area_{index}",
            )
            resistances = {}
            for temperature in arrhenius.TEMPERATURES_C:
                default_value = 1000.0 + index * 500 + (70 - temperature) * 80
                resistances[temperature] = st.number_input(
                    f"{temperature}°C 阻抗 (Ω)",
                    min_value=0.000001,
                    value=default_value,
                    format="%.6f",
                    key=f"lab_arrhenius_manual_resistance_{index}_{temperature}",
                )
            default_x, default_y = positions[index % len(positions)]
            annotation_x = default_x
            annotation_y = default_y
            if show_annotations:
                annotation_x = st.slider(
                    "标注横向位置",
                    0.0,
                    1.0,
                    float(default_x),
                    0.01,
                    key=f"lab_arrhenius_manual_x_{index}",
                )
                annotation_y = st.slider(
                    "标注纵向位置",
                    0.0,
                    1.0,
                    float(default_y),
                    0.01,
                    key=f"lab_arrhenius_manual_y_{index}",
                )
            series_inputs.append(
                {
                    "label": label,
                    "thickness_cm": thickness,
                    "area_cm2": area,
                    "resistances": resistances,
                    "annotation_x": annotation_x,
                    "annotation_y": annotation_y,
                }
            )
    return series_inputs, show_annotations


def render_arrhenius_page():
    render_page_header("Arrhenius")

    sidebar_section("01", "输入方式")
    input_mode = st.sidebar.radio(
        "数据来源",
        ["手动输入", "上传 Excel / CSV"],
        key="lab_arrhenius_input_mode",
    )
    st.sidebar.download_button(
        "下载数据模板",
        data=_as_bytes(arrhenius.create_arrhenius_template()),
        file_name="arrhenius_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
        icon=":material/table_view:",
        key="lab_arrhenius_template",
    )

    raw_df = None
    if input_mode == "上传 Excel / CSV":
        uploaded_file = st.sidebar.file_uploader(
            "实验数据文件",
            type=FILE_TYPES,
            key="lab_arrhenius_upload",
        )
        if uploaded_file is None:
            render_empty_state("等待温度阻抗数据", "上传数据模板或切换为手动输入。")
            return
        try:
            with st.sidebar:
                raw_df = _read_general_file(uploaded_file, "lab_arrhenius_sheet")
            series_inputs, show_annotations = _arrhenius_from_excel(raw_df)
        except Exception as exc:
            st.error(f"Arrhenius 数据读取失败：{exc}")
            return
    else:
        series_inputs, show_annotations = _arrhenius_manual_inputs()

    try:
        fig, plot_df, summary_df = arrhenius.create_arrhenius_figure(
            series_inputs,
            show_annotations=show_annotations,
        )
        _standardize_figure_canvas(fig)
        _standardize_arrhenius_typography(fig)
        preview = _white_preview(fig)
        _render_downloads(fig, "arrhenius_plot")
        source_df = raw_df if raw_df is not None else plot_df
        _render_workspace(
            preview,
            source_df,
            series_count=len(series_inputs),
            summary_df=summary_df,
        )
    except Exception as exc:
        st.error(f"Arrhenius 图生成失败：{exc}")
    finally:
        if "fig" in locals():
            plt.close(fig)


def render_rate_page():
    render_page_header("Rate")

    sidebar_section("01", "导入数据")
    st.sidebar.download_button(
        "下载数据模板",
        data=_as_bytes(rate.create_rate_template()),
        file_name="rate_plot_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
        icon=":material/table_view:",
        key="lab_rate_template",
    )
    uploaded_file = st.sidebar.file_uploader(
        "实验数据文件",
        type=FILE_TYPES,
        key="lab_rate_upload",
    )
    if uploaded_file is None:
        render_empty_state()
        return

    try:
        with st.sidebar:
            df = rate.read_plot_file(uploaded_file)
    except Exception as exc:
        st.error(f"文件读取失败：{exc}")
        return
    columns = list(df.columns)
    if len(columns) < 2:
        st.error("数据文件至少需要循环圈数和比容量两列。")
        return

    sidebar_section("02", "数据列映射")
    cycle_default = rate.default_column(df, rate.CYCLE_CANDIDATES, fallback_index=0)
    capacity_default = rate.default_column(df, rate.CAPACITY_CANDIDATES, fallback_index=1)
    series_options, series_index = rate.optional_series_options(df)
    cycle_col = st.sidebar.selectbox(
        "循环圈数列",
        columns,
        index=columns.index(cycle_default),
        key="lab_rate_cycle",
    )
    capacity_col = st.sidebar.selectbox(
        "比容量列",
        columns,
        index=columns.index(capacity_default),
        key="lab_rate_capacity",
    )
    series_selected = st.sidebar.selectbox(
        "样品分组列",
        series_options,
        index=series_index,
        key="lab_rate_series",
    )
    series_col = None if series_selected == "None" else series_selected
    try:
        plot_df, dropped = rate.prepare_rate_data(df, cycle_col, capacity_col, series_col)
    except Exception as exc:
        st.error(f"数据处理失败：{exc}")
        return

    sidebar_section("03", "图形参数")
    legend_labels = {}
    with st.sidebar.expander("图例名称", expanded=True):
        for index, series_name in enumerate(plot_df["_series"].drop_duplicates()):
            legend_labels[series_name] = st.text_input(
                f"样品 {index + 1}",
                value=series_name,
                key=f"lab_rate_legend_{index}",
            )
    legend_x = st.sidebar.slider(
        "图例横向位置",
        0.0,
        1.0,
        0.84,
        0.01,
        key="lab_rate_legend_x",
    )
    legend_y = st.sidebar.slider(
        "图例纵向位置",
        0.0,
        1.0,
        0.96,
        0.01,
        key="lab_rate_legend_y",
    )

    sidebar_section("04", "文字说明")
    with st.sidebar:
        annotations = _annotation_controls("lab_rate")

    if dropped:
        st.warning(f"已忽略 {dropped} 行缺失或无效数据。")

    try:
        fig = rate.create_rate_figure(plot_df, legend_labels, legend_x, legend_y, annotations)
        _standardize_figure_canvas(fig)
        preview = _white_preview(fig)
        _render_downloads(fig, "rate_capability_plot")
        series_count = int(plot_df["_series"].nunique())
        display_df = plot_df[["_series", "_cycle", "_capacity"]].rename(
            columns={"_series": "series", "_cycle": "cycle", "_capacity": "capacity"}
        )
        _render_workspace(
            preview,
            display_df,
            series_count,
            display_columns=["series", "cycle", "capacity"],
        )
    except Exception as exc:
        st.error(f"倍率图生成失败：{exc}")
    finally:
        if "fig" in locals():
            plt.close(fig)


def render_cycling_page():
    render_page_header("Cycling")

    sidebar_section("01", "导入数据")
    st.sidebar.download_button(
        "下载数据模板",
        data=_as_bytes(cycling.create_cycling_template()),
        file_name="cycling_plot_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
        icon=":material/table_view:",
        key="lab_cycling_template",
    )
    uploaded_file = st.sidebar.file_uploader(
        "实验数据文件",
        type=FILE_TYPES,
        key="lab_cycling_upload",
    )
    if uploaded_file is None:
        render_empty_state()
        return

    try:
        with st.sidebar:
            df = cycling.read_plot_file(uploaded_file)
    except Exception as exc:
        st.error(f"文件读取失败：{exc}")
        return
    columns = list(df.columns)
    if len(columns) < 3:
        st.error("数据文件至少需要循环圈数、比容量和库伦效率三列。")
        return

    sidebar_section("02", "数据列映射")
    cycle_default = cycling.default_column(df, cycling.CYCLE_CANDIDATES, fallback_index=0)
    capacity_default = cycling.default_column(df, cycling.CAPACITY_CANDIDATES, fallback_index=1)
    efficiency_default = cycling.default_column(df, cycling.EFFICIENCY_CANDIDATES, fallback_index=2)
    series_options, series_index = cycling.optional_series_options(df)
    cycle_col = st.sidebar.selectbox(
        "循环圈数列",
        columns,
        index=columns.index(cycle_default),
        key="lab_cycling_cycle",
    )
    capacity_col = st.sidebar.selectbox(
        "比容量列",
        columns,
        index=columns.index(capacity_default),
        key="lab_cycling_capacity",
    )
    efficiency_col = st.sidebar.selectbox(
        "库伦效率列",
        columns,
        index=columns.index(efficiency_default),
        key="lab_cycling_efficiency",
    )
    series_selected = st.sidebar.selectbox(
        "样品分组列",
        series_options,
        index=series_index,
        key="lab_cycling_series",
    )
    series_col = None if series_selected == "None" else series_selected

    try:
        plot_df, dropped = cycling.prepare_cycling_data(
            df,
            cycle_col,
            capacity_col,
            efficiency_col,
            series_col,
        )
    except Exception as exc:
        st.error(f"数据处理失败：{exc}")
        return

    sidebar_section("03", "图形参数")
    plot_width_cm = st.sidebar.number_input(
        "图宽 (cm)",
        min_value=12.0,
        max_value=60.0,
        value=float(cycling.DEFAULT_WIDTH_CM),
        step=0.5,
        format="%.1f",
        key="lab_cycling_width",
    )
    legend_labels = {}
    with st.sidebar.expander("图例名称", expanded=True):
        for index, series_name in enumerate(plot_df["_series"].drop_duplicates()):
            legend_labels[series_name] = st.text_input(
                f"样品 {index + 1}",
                value=series_name,
                key=f"lab_cycling_legend_{index}",
            )
    legend_x = st.sidebar.slider(
        "图例横向位置",
        0.0,
        1.0,
        0.05,
        0.01,
        key="lab_cycling_legend_x",
    )
    legend_y = st.sidebar.slider(
        "图例纵向位置",
        0.0,
        1.0,
        0.22,
        0.01,
        key="lab_cycling_legend_y",
    )

    sidebar_section("04", "文字说明")
    with st.sidebar:
        annotations = _annotation_controls("lab_cycling")

    if dropped:
        st.warning(f"已忽略 {dropped} 行缺失或无效数据。")

    try:
        fig = cycling.create_cycling_figure(
            plot_df,
            legend_labels,
            legend_x,
            legend_y,
            annotations,
            plot_width_cm,
        )
        preview = cycling.figure_to_white_preview_bytes(fig)
        _render_downloads(fig, "cycling_performance_plot")
        series_count = int(plot_df["_series"].nunique())
        display_df = plot_df[["_series", "_cycle", "_capacity", "_efficiency"]].rename(
            columns={
                "_series": "series",
                "_cycle": "cycle",
                "_capacity": "capacity",
                "_efficiency": "coulombic_efficiency",
            }
        )
        _render_workspace(
            preview,
            display_df,
            series_count,
            display_columns=["series", "cycle", "capacity", "coulombic_efficiency"],
        )
    except Exception as exc:
        st.error(f"循环图生成失败：{exc}")
    finally:
        if "fig" in locals():
            plt.close(fig)


PAGE_RENDERERS = {
    "Nyquist": render_nyquist_page,
    "Arrhenius": render_arrhenius_page,
    "Rate": render_rate_page,
    "Cycling": render_cycling_page,
}
