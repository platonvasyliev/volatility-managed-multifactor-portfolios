"""Save tables (CSV + Markdown) and figures to results/."""

import matplotlib.pyplot as plt
import pandas as pd

from .config import FIGURES_DIR, TABLES_DIR


def _markdown(df: pd.DataFrame, decimals: int) -> str:
    def fmt(v, is_p_value):
        if isinstance(v, float):
            if pd.isna(v):
                return ""
            if is_p_value:
                return "<0.001" if v < 0.001 else f"{v:.3f}"
            return f"{v:.{decimals}f}"
        return str(v)

    levels = df.index.nlevels
    header = [""] * levels + [str(c) for c in df.columns]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    previous = (None,) * levels
    for idx, row in df.iterrows():
        idx = idx if isinstance(idx, tuple) else (idx,)
        # show each index level only when it changes, so panels read like the thesis tables
        shown = [str(v) if idx[: i + 1] != previous[: i + 1] else "" for i, v in enumerate(idx)]
        is_p_value = "p-value" in str(idx[-1])
        lines.append("| " + " | ".join(shown + [fmt(v, is_p_value) for v in row]) + " |")
        previous = idx
    return "\n".join(lines) + "\n"


def save_table(df: pd.DataFrame, name: str, title: str, decimals: int = 2) -> pd.DataFrame:
    """Write results/tables/<name>.csv and .md, and print the table."""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df.round(6).to_csv(TABLES_DIR / f"{name}.csv")
    (TABLES_DIR / f"{name}.md").write_text(f"### {title}\n\n" + _markdown(df, decimals), encoding="utf-8")
    print(f"\n{title}\n{'=' * len(title)}")
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(df.round(decimals).to_string())
    return df


def save_figure(fig: plt.Figure, name: str, dpi: int = 300) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / f"{name}.png", dpi=dpi, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"saved figure {name}.png")
