import io

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.ticker import AutoMinorLocator, FixedLocator, FormatStrFormatter, MaxNLocator

from Nyquist_plot import (
    AXIS_LINEWIDTH,
    MAJOR_TICK_LENGTH,
    MAJOR_TICK_WIDTH,
    MINOR_TICK_LENGTH,
    MINOR_TICK_WIDTH,
    PALETTE,
    figure_to_bytes,
    normalize_text,
)


TEMPERATURES_C = [30, 40, 50, 60, 70]
TOP_TEMPERATURES_C = [70, 60, 50, 40, 30]
FONT_FAMILY = ["Arial", "DejaVu Sans", "Microsoft YaHei"]
FIT_LINEWIDTH = 3


def temperature_to_arrhenius_x(temperature_c):
    return 1000 / (temperature_c + 273.15)


def conductivity_s_cm(resistance_ohm, thickness_cm, area_cm2):
    return thickness_cm / (resistance_ohm * area_cm2)


def prepare_arrhenius_data(series_inputs):
    rows = []

    for series_index, item in enumerate(series_inputs):
        label = normalize_text(item["label"])
        thickness = float(item["thickness_cm"])
        area = float(item["area_cm2"])

        if thickness <= 0 or area <= 0:
            raise ValueError("Thickness and area must be positive values.")

        for temperature_c in TEMPERATURES_C:
            resistance = float(item["resistances"][temperature_c])
            if resistance <= 0:
                raise ValueError("All resistance values must be positive.")

            sigma_s_cm = conductivity_s_cm(resistance, thickness, area)
            rows.append(
                {
                    "series_index": series_index,
                    "series": label,
                    "temperature_c": temperature_c,
                    "resistance_ohm": resistance,
                    "thickness_cm": thickness,
                    "area_cm2": area,
                    "x_1000_over_t": temperature_to_arrhenius_x(temperature_c),
                    "conductivity_s_cm": sigma_s_cm,
                    "log_sigma": np.log10(sigma_s_cm),
                }
            )

    return pd.DataFrame(rows)


def fit_arrhenius_series(group):
    x = group["x_1000_over_t"].to_numpy(dtype=float)
    y = group["log_sigma"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    activation_energy_ev = -0.1984 * slope
    return slope, intercept, activation_energy_ev


def style_main_axis(ax):
    ax.set_xlim(2.8, 3.4)
    ax.xaxis.set_major_locator(FixedLocator([2.8, 3.0, 3.2, 3.4]))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, min_n_ticks=4))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))

    ax.set_xlabel(r"1000/T (K$^{-1}$)", fontsize=24, fontweight="bold", labelpad=4)
    ax.set_ylabel(r"log$\sigma$ (S cm$^{-1}$)", fontsize=24, fontweight="bold", labelpad=4)

    for side in ("left", "bottom", "right"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_linewidth(AXIS_LINEWIDTH)
        ax.spines[side].set_color("black")
    ax.spines["top"].set_visible(False)

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

    ax.set_box_aspect(16 / 20)


def add_temperature_axis(ax):
    top_ax = ax.twiny()
    top_ax.set_xlim(ax.get_xlim())
    top_ticks = [temperature_to_arrhenius_x(temp) for temp in TOP_TEMPERATURES_C]
    top_ax.xaxis.set_major_locator(FixedLocator(top_ticks))
    top_ax.set_xticklabels([str(temp) for temp in TOP_TEMPERATURES_C])
    top_ax.xaxis.set_minor_locator(AutoMinorLocator(2))

    for side in ("left", "right", "bottom"):
        top_ax.spines[side].set_visible(False)
    top_ax.spines["top"].set_visible(True)
    top_ax.spines["top"].set_linewidth(AXIS_LINEWIDTH)
    top_ax.spines["top"].set_color("red")

    top_ax.tick_params(
        axis="x",
        which="major",
        direction="in",
        length=MAJOR_TICK_LENGTH,
        width=MAJOR_TICK_WIDTH,
        colors="red",
        top=True,
        bottom=False,
        labeltop=True,
        labelbottom=False,
    )
    top_ax.tick_params(
        axis="x",
        which="minor",
        direction="in",
        length=MINOR_TICK_LENGTH,
        width=MINOR_TICK_WIDTH,
        colors="red",
        top=True,
        bottom=False,
    )
    top_ax.set_xlabel(
        "Temperature (°C)",
        fontfamily=FONT_FAMILY,
        fontsize=24,
        fontweight="bold",
        color="red",
        labelpad=4,
    )

    for label in top_ax.get_xticklabels():
        label.set_fontfamily(FONT_FAMILY)
        label.set_fontsize(20)
        label.set_fontweight("bold")
        label.set_color("red")

    return top_ax


def create_arrhenius_figure(series_inputs, show_annotations=True):
    plot_df = prepare_arrhenius_data(series_inputs)

    cm_to_inch = 1 / 2.54
    plt.rcParams["font.family"] = "Arial"

    plt.rcParams["mathtext.fontset"] = "custom"
    plt.rcParams["mathtext.rm"] = "Arial"
    plt.rcParams["mathtext.it"] = "Arial:italic"
    plt.rcParams["mathtext.bf"] = "Arial:bold"
    plt.rcParams["mathtext.default"] = "regular"
    fig, ax = plt.subplots(figsize=(20 * cm_to_inch, 16 * cm_to_inch))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    summary_rows = []
    annotation_positions = [(0.61, 0.70), (0.22, 0.28), (0.61, 0.47), (0.22, 0.52)]
    annotation_position_map = {
        normalize_text(item["label"]): (
            float(item.get("annotation_x", annotation_positions[index % len(annotation_positions)][0])),
            float(item.get("annotation_y", annotation_positions[index % len(annotation_positions)][1])),
        )
        for index, item in enumerate(series_inputs)
    }

    for series_index, (series_name, group) in enumerate(plot_df.groupby("series", sort=False)):
        color = PALETTE[series_index % len(PALETTE)]
        slope, intercept, activation_energy = fit_arrhenius_series(group)
        x_fit = np.linspace(group["x_1000_over_t"].min(), group["x_1000_over_t"].max(), 100)
        y_fit = slope * x_fit + intercept

        ax.scatter(
            group["x_1000_over_t"],
            group["log_sigma"],
            s=12**2,
            marker="o",
            c=color,
            edgecolors="none",
            label=series_name,
            zorder=3,
        )
        ax.plot(x_fit, y_fit, color=color, linewidth=FIT_LINEWIDTH, zorder=2)

        summary_rows.append(
            {
                "series": series_name,
                "slope_k": slope,
                "activation_energy_eV": activation_energy,
            }
        )

        if show_annotations:
            x_frac, y_frac = annotation_position_map.get(
                series_name,
                annotation_positions[series_index % len(annotation_positions)],
            )
            ax.text(
                x_frac,
                y_frac,
                f"{series_name}\nE$_a$ = {activation_energy:.2f} eV",
                transform=ax.transAxes,
                color=color,
                fontfamily=FONT_FAMILY,
                fontsize=20,
                fontweight="bold",
                va="center",
                linespacing=0.85,
            )

    style_main_axis(ax)
    top_ax = add_temperature_axis(ax)
    fig.subplots_adjust(left=0.32, right=0.93, bottom=0.20, top=0.80)
    ax.set_box_aspect(16 / 20)
    top_ax.set_box_aspect(16 / 20)

    summary_df = pd.DataFrame(summary_rows)
    return fig, plot_df, summary_df


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


def create_arrhenius_template():
    rows = []
    for label in ("Sample 1", "Sample 2"):
        for temperature in TEMPERATURES_C:
            rows.append(
                {
                    "series": label,
                    "temperature_c": temperature,
                    "resistance_ohm": 1000,
                    "thickness_cm": 0.10,
                    "area_cm2": 1.00,
                }
            )
    template = pd.DataFrame(rows)
    buffer = io.BytesIO()
    template.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer


def render_arrhenius_page():
    st.title("Arrhenius Plot")
    st.markdown(
        """
        输入 30°C、40°C、50°C、60°C、70°C 下的阻抗，以及电解质片厚度和面积。
        网页会计算电导率 `σ = L / (R × A)`，单位为 `S cm⁻¹`，
        再绘制 `logσ` 对 `1000/T` 的 Arrhenius 图，并通过线性拟合计算活化能：

        `Ea = -0.1984 × k eV`
        """
    )

    st.download_button(
        "Download Arrhenius Excel Template",
        data=create_arrhenius_template(),
        file_name="arrhenius_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    left, right = st.columns([0.38, 0.62], gap="large")

    with left:
        series_count = st.number_input(
            "样品/曲线数量",
            min_value=1,
            max_value=8,
            value=1,
            step=1,
        )
        show_annotations = st.checkbox("在图中显示样品名和活化能", value=True)

        series_inputs = []
        default_annotation_positions = [(0.61, 0.70), (0.22, 0.28), (0.61, 0.47), (0.22, 0.52)]
        for series_index in range(int(series_count)):
            with st.expander(f"Sample {series_index + 1}", expanded=True):
                label = st.text_input(
                    "图例/样品名称",
                    value=f"Sample {series_index + 1}",
                    key=f"arr_label_{series_index}",
                )
                thickness = st.number_input(
                    "电解质片厚度 (cm)",
                    min_value=0.000001,
                    value=0.100000,
                    format="%.6f",
                    key=f"arr_thickness_{series_index}",
                )
                area = st.number_input(
                    "电解质片面积 (cm²)",
                    min_value=0.000001,
                    value=1.000000,
                    format="%.6f",
                    key=f"arr_area_{series_index}",
                )

                resistances = {}
                for temperature in TEMPERATURES_C:
                    default_resistance = 1000.0 + series_index * 500 + (70 - temperature) * 80
                    resistances[temperature] = st.number_input(
                        f"{temperature}°C 阻抗 (Ω)",
                        min_value=0.000001,
                        value=default_resistance,
                        format="%.6f",
                        key=f"arr_resistance_{series_index}_{temperature}",
                    )

                default_x, default_y = default_annotation_positions[
                    series_index % len(default_annotation_positions)
                ]
                if show_annotations:
                    st.caption("图例/活化能标注位置：0 表示靠左或靠下，1 表示靠右或靠上。")
                    annotation_x = st.slider(
                        "图例 X 位置",
                        min_value=0.00,
                        max_value=1.00,
                        value=float(default_x),
                        step=0.01,
                        key=f"arr_annotation_x_{series_index}",
                    )
                    annotation_y = st.slider(
                        "图例 Y 位置",
                        min_value=0.00,
                        max_value=1.00,
                        value=float(default_y),
                        step=0.01,
                        key=f"arr_annotation_y_{series_index}",
                    )
                else:
                    annotation_x = default_x
                    annotation_y = default_y

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

    with right:
        try:
            fig, plot_df, summary_df = create_arrhenius_figure(
                series_inputs,
                show_annotations=show_annotations,
            )
        except Exception as exc:
            st.error(f"Could not generate Arrhenius plot: {exc}")
            return

        st.subheader("Arrhenius Plot")
        st.image(
            figure_to_white_preview_bytes(fig),
            use_container_width=False,
            caption="Preview uses a white background. Downloaded PNG/PDF remains transparent.",
        )

        st.subheader("Calculated Data")
        st.dataframe(
            plot_df[
                [
                    "series",
                    "temperature_c",
                    "resistance_ohm",
                    "conductivity_s_cm",
                    "x_1000_over_t",
                    "log_sigma",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Fitting Result")
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        png_bytes = figure_to_bytes(fig, "png", dpi=600)
        pdf_bytes = figure_to_bytes(fig, "pdf", dpi=600)

        download_left, download_right = st.columns(2)
        with download_left:
            st.download_button(
                "Download PNG",
                data=png_bytes,
                file_name="arrhenius_plot.png",
                mime="image/png",
                use_container_width=True,
            )
        with download_right:
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name="arrhenius_plot.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        plt.close(fig)
