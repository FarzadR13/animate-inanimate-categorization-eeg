"""Replot Figure 4A with a common y-axis across stimulus conditions.

This script only changes the visualization. It reads the existing
AllCorrelation6plus.xlsx table and plots the already-computed correlations
for the five stimulus conditions across VGG-19 layers.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "AllCorrelation6plus.xlsx"
OUT_DIR = ROOT / "R_output" / "Figure4A_same_yaxis"

CONDITIONS = [
    ("Color", "Color"),
    ("Grayscale", "Grayscale"),
    ("Color-Scrambled", "Color-Scrambled"),
    ("Grayscale-Scrambled", "Grayscale-Scrambled"),
    ("Texform", "Texform"),
]

COLORS = {
    "Color": "#C43C2F",
    "Grayscale": "#4B6777",
    "Color-Scrambled": "#2E8B57",
    "Grayscale-Scrambled": "#6F5AA8",
    "Texform": "#B26B2E",
}

Y_LIM = (0.0, 1.05)


def load_data() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Expected source table not found: {DATA_FILE}")

    df = pd.read_excel(DATA_FILE)
    required = ["Layer"] + [condition for condition, _ in CONDITIONS]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s) in {DATA_FILE.name}: {missing}")

    df = df[required].copy()
    for column in required[1:]:
        df[column] = pd.to_numeric(df[column], errors="raise")
    df["Layer"] = df["Layer"].astype(str)
    return df


def style_axis(ax: plt.Axes, title: str, show_xlabel: bool) -> None:
    ax.set_ylim(*Y_LIM)
    ax.set_ylabel("RSA correlation", fontsize=12, fontweight="bold")
    ax.grid(True, which="major", axis="both", color="#D0D0D0", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.25)
    ax.spines["bottom"].set_linewidth(1.25)
    ax.tick_params(axis="both", labelsize=11, width=1.2)
    for label in ax.get_yticklabels():
        label.set_fontweight("bold")
    add_facet_strip(ax, title)
    if show_xlabel:
        ax.set_xlabel("VGG-19 layer", fontsize=13, fontweight="bold")
    else:
        ax.set_xlabel("")


def add_facet_strip(ax: plt.Axes, title: str) -> None:
    """Add a gray strip title similar to the previous faceted version."""
    strip = plt.Rectangle(
        (0, 1.01),
        1,
        0.16,
        transform=ax.transAxes,
        facecolor="#D9D9D9",
        edgecolor="#8F8F8F",
        linewidth=1.0,
        clip_on=False,
    )
    ax.add_patch(strip)
    ax.text(
        0.5,
        1.09,
        title,
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color="black",
        clip_on=False,
    )


def plot_main(df: pd.DataFrame) -> None:
    x = range(len(df))
    fig, ax = plt.subplots(figsize=(10.8, 5.8), constrained_layout=True)

    for column, title in CONDITIONS:
        ax.plot(
            x,
            df[column],
            label=title,
            color=COLORS[column],
            linewidth=3.0,
            marker="o",
            markersize=6.0,
            markerfacecolor="white",
            markeredgewidth=1.6,
        )

    ax.set_ylim(*Y_LIM)
    ax.set_ylabel("RSA correlation (Spearman ρ)", fontsize=13, fontweight="bold")
    ax.set_xlabel("VGG-19 layer", fontsize=13, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["Layer"], rotation=45, ha="right")
    ax.grid(True, which="major", axis="both", color="#D0D0D0", linewidth=0.8, alpha=0.3)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.6)
    ax.spines["bottom"].set_linewidth(1.6)
    ax.tick_params(axis="both", labelsize=11, width=1.5, length=5)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")

    legend = ax.legend(
        loc="upper left",
        frameon=True,
        facecolor="white",
        edgecolor="#B0B0B0",
        framealpha=0.95,
        fontsize=10.5,
    )
    for text in legend.get_texts():
        text.set_fontweight("bold")

    fig.savefig(OUT_DIR / "Figure4A_same_yaxis_main.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / "Figure4A_same_yaxis_main.pdf", bbox_inches="tight")
    fig.savefig(OUT_DIR / "Figure4A_same_yaxis_main_highres.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


def plot_plus_zoom(df: pd.DataFrame) -> tuple[float, float]:
    x = range(len(df))
    zoom_columns = ["Color-Scrambled", "Grayscale-Scrambled", "Texform"]
    zoom_min = max(0.0, float(df[zoom_columns].min().min()) - 0.03)
    zoom_max = min(1.05, float(df[zoom_columns].max().max()) + 0.04)

    fig, axes = plt.subplots(
        nrows=len(CONDITIONS) + 1,
        ncols=1,
        sharex=True,
        figsize=(12.5, 18.5),
        constrained_layout=True,
        gridspec_kw={"height_ratios": [1, 1, 1, 1, 1, 1.15]},
    )

    for idx, (ax, (column, title)) in enumerate(zip(axes[: len(CONDITIONS)], CONDITIONS)):
        ax.plot(
            x,
            df[column],
            color=COLORS[column],
            linewidth=3.1,
            marker="o",
            markersize=5.5,
            markerfacecolor="white",
            markeredgewidth=1.6,
        )
        style_axis(ax, title, show_xlabel=False)

    zoom_ax = axes[-1]
    for column in zoom_columns:
        zoom_ax.plot(
            x,
            df[column],
            label=dict(CONDITIONS)[column],
            color=COLORS[column],
            linewidth=2.8,
            marker="o",
            markersize=5.0,
            markerfacecolor="white",
            markeredgewidth=1.5,
        )
    add_facet_strip(zoom_ax, "Auxiliary zoom: impoverished conditions only")
    zoom_ax.set_ylim(zoom_min, zoom_max)
    zoom_ax.set_ylabel("RSA correlation", fontsize=12, fontweight="bold")
    zoom_ax.set_xlabel("VGG-19 layer", fontsize=13, fontweight="bold")
    zoom_ax.grid(True, which="major", axis="both", color="#D0D0D0", linewidth=0.8)
    zoom_ax.set_axisbelow(True)
    zoom_ax.spines["top"].set_visible(False)
    zoom_ax.spines["right"].set_visible(False)
    zoom_ax.spines["left"].set_linewidth(1.25)
    zoom_ax.spines["bottom"].set_linewidth(1.25)
    zoom_ax.tick_params(axis="both", labelsize=11, width=1.2)
    for label in zoom_ax.get_xticklabels() + zoom_ax.get_yticklabels():
        label.set_fontweight("bold")
    zoom_ax.legend(frameon=False, ncol=3, fontsize=10, loc="upper left")
    zoom_ax.set_xticks(list(x))
    zoom_ax.set_xticklabels(df["Layer"], rotation=45, ha="right")
    for label in zoom_ax.get_xticklabels():
        label.set_fontweight("bold")
    fig.savefig(OUT_DIR / "Figure4A_same_yaxis_plus_zoom.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / "Figure4A_same_yaxis_plus_zoom.pdf", bbox_inches="tight")
    plt.close(fig)
    return zoom_min, zoom_max


def write_notes(df: pd.DataFrame, zoom_range: tuple[float, float]) -> None:
    observed_min = float(df[[column for column, _ in CONDITIONS]].min().min())
    observed_max = float(df[[column for column, _ in CONDITIONS]].max().max())
    notes = f"""# Figure 4A Revision Notes

Source data: `{DATA_FILE}`

This revision changes only the plotting of Panel A. The correlation values were read from
`AllCorrelation6plus.xlsx` and were not recomputed or transformed.

- Conditions plotted: Color, Grayscale, Color-Scrambled, Grayscale-Scrambled, Texform.
- Observed value range in the source table: {observed_min:.6f} to {observed_max:.6f}.
- Main-panel y-axis range used for all five condition panels: {Y_LIM[0]:.2f} to {Y_LIM[1]:.2f}.
- Same y-axis range applied to all five panels: yes.
- Main figure layout: single overlaid plot with one x-axis and one y-axis for direct comparison.
- The legend lists the five conditions as Color, Grayscale, Color-Scrambled, Grayscale-Scrambled, and Texform.
- The main y-axis label specifies the Spearman correlation coefficient: RSA correlation (Spearman ρ).
- Axis labels, tick labels, tick marks, and visible spines are bolded for manuscript readability.
- No figure-level title is shown in the plot area.
- Optional zoomed version produced: yes.
- Auxiliary zoom y-axis range for CPS/GPS/Texform only: {zoom_range[0]:.3f} to {zoom_range[1]:.3f}.

Generated files:
- `Figure4A_same_yaxis_main.png`
- `Figure4A_same_yaxis_main.pdf`
- `Figure4A_same_yaxis_main_highres.png`
- `Figure4A_same_yaxis_plus_zoom.png`
- `Figure4A_same_yaxis_plus_zoom.pdf`
"""
    (OUT_DIR / "figure4A_revision_notes.md").write_text(notes, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    plot_main(df)
    zoom_range = plot_plus_zoom(df)
    write_notes(df, zoom_range)
    print(f"Wrote Figure 4A same-y-axis outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
