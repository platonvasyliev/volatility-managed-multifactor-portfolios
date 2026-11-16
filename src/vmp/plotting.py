"""Shared figure layouts (grayscale, as in the thesis)."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

WEIGHT_GRAYS = ["0.05", "0.15", "0.30", "0.45", "0.60", "0.75", "0.90"]


def seven_panel_figure(figsize, bottom=0.10):
    """4x2 grid for the seven factors, with the seventh panel centred on the last row."""
    fig, axes = plt.subplots(4, 2, figsize=figsize)
    axes = axes.flatten()
    fig.delaxes(axes[-1])
    fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=bottom, hspace=0.45, wspace=0.25)
    pos = axes[6].get_position()
    axes[6].set_position([0.5 - pos.width / 2, pos.y0, pos.width, pos.height])
    return fig, axes[:7]


def stacked_weights(ax, weights: pd.DataFrame, title: str) -> None:
    """One 100% bar per month, one gray shade per factor."""
    x = np.arange(len(weights))
    bottom = np.zeros(len(weights))
    for col, color in zip(weights.columns, WEIGHT_GRAYS):
        values = weights[col].to_numpy() * 100
        ax.bar(x, values, bottom=bottom, width=1.02, color=color, edgecolor="none", linewidth=0, label=col)
        bottom += values
    ticks = np.arange(0, len(weights), 60)
    ax.set_xticks(ticks)
    ax.set_xticklabels(weights.index[ticks].strftime("%Y"), rotation=45)
    ax.set_ylim(0, 100)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
