"""Robustness Analysis: sentiment regimes. Figure 6, Table 4, Table 5."""

import numpy as np
import pandas as pd

from vmp import data, pipeline
from vmp.config import FACTOR_NAMES, FACTORS, SENTIMENT_END
from vmp.inference import sharpe_ratio
from vmp.pipeline import PORTFOLIOS
from vmp.plotting import seven_panel_figure
from vmp.reporting import save_figure, save_table
from vmp.sentiment import HIGH, LOW, sentiment_regimes, sentiment_table
from vmp.volatility_management import previous_month, realized_variance


def figure_6_sharpe_by_sentiment_and_volatility():
    """Sharpe ratios of each factor in the four sentiment x factor-volatility states."""
    daily, _ = pipeline.factors()
    returns = pipeline.single_factors().unmanaged.loc[:SENTIMENT_END]
    regime = sentiment_regimes(returns.index, data.load_sentiment())

    sharpe = {}
    for f in FACTORS:
        lagged_var = previous_month(realized_variance(daily[f]), returns.index)
        df = pd.DataFrame({"r": returns[f], "var": lagged_var, "sent": regime}).dropna()
        df["vol"] = np.where(df["var"] >= df["var"].median(), "High", "Low")
        sharpe[f] = df.groupby(["sent", "vol"])["r"].apply(sharpe_ratio)

    fig, axes = seven_panel_figure(figsize=(16, 18), bottom=0.07)
    x, width = np.arange(2), 0.35
    for i, (ax, f) in enumerate(zip(axes, FACTORS)):
        low = [sharpe[f][(LOW, "Low")], sharpe[f][(HIGH, "Low")]]
        high = [sharpe[f][(LOW, "High")], sharpe[f][(HIGH, "High")]]
        b1 = ax.bar(x - width / 2, low, width, color="black")
        b2 = ax.bar(x + width / 2, high, width, color="gray")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([LOW, HIGH])
        ax.set_title(FACTOR_NAMES[f])
        ax.grid(axis="y", alpha=0.3)
        if i % 2 == 0:
            ax.set_ylabel("Sharpe ratio")
    fig.legend([b1, b2], ["Low volatility", "High volatility"], loc="lower left",
               bbox_to_anchor=(0.06, 0.015), ncol=2, frameon=False)
    save_figure(fig, "figure_6_sharpe_by_sentiment_and_volatility")


def table_4_single_factors_by_sentiment():
    s = pipeline.single_factors()
    table = sentiment_table(s.unmanaged, s.managed, {f: f for f in FACTORS})
    save_table(table, "table_4_single_factors_by_sentiment", "Table 4: volatility-managed factors by sentiment regime (1980-2023)", 3)


def table_5_multifactor_by_sentiment():
    m = pipeline.multifactor()
    table = sentiment_table(m.unmanaged, m.managed, {p: p for p in PORTFOLIOS})
    save_table(table, "table_5_multifactor_by_sentiment", "Table 5: volatility-managed multifactor portfolios by sentiment regime (1980-2023)", 3)


def main():
    figure_6_sharpe_by_sentiment_and_volatility()
    table_4_single_factors_by_sentiment()
    table_5_multifactor_by_sentiment()


if __name__ == "__main__":
    main()
