"""Methodology section: Figure 1, Table A1, Table A2."""

import numpy as np
import pandas as pd

from vmp import pipeline
from vmp.inference import describe
from vmp.plotting import plt
from vmp.reporting import save_figure, save_table
from vmp.transaction_costs import cost_parameters
from vmp.volatility_management import realized_variance, realized_volatility, volatility_manage


def figure_1_exposure_variance_vs_volatility():
    """Implied exposure to the Market factor when scaling by variance vs volatility."""
    daily, _ = pipeline.factors()
    market = pipeline.single_factors().unmanaged["Mkt-RF"]
    _, exp_var = volatility_manage(market, realized_variance(daily["Mkt-RF"]))
    _, exp_vol = volatility_manage(market, realized_volatility(daily["Mkt-RF"]))

    fig, axes = plt.subplots(1, 2, figsize=(16, 5), sharex=True)
    for ax, exposure, title in [(axes[0], exp_var, "Realized Variance"), (axes[1], exp_vol, "Realized Volatility")]:
        ax.plot(exposure.index, exposure, linewidth=1.4, color="black")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("Exposure")
    fig.tight_layout()
    save_figure(fig, "figure_1_market_exposure_variance_vs_volatility")

    summary = pd.DataFrame(
        {"Realized variance": exp_var.describe(), "Realized volatility": exp_vol.describe()}
    ).loc[["mean", "max"]]
    save_table(summary, "figure_1_exposure_summary", "Figure 1: average and maximum exposure", decimals=2)


def table_a1_choice_of_c():
    """Managed Market factor with a fixed target volatility instead of the ex-post c."""
    daily, _ = pipeline.factors()
    market = pipeline.single_factors().unmanaged["Mkt-RF"]
    rows = {}
    for target in (0.12, 0.20):
        managed, _ = volatility_manage(market, realized_volatility(daily["Mkt-RF"]), c=target / np.sqrt(12))
        rows[f"c = {target:.2f} / sqrt(12)"] = describe(managed)
    save_table(pd.DataFrame(rows).T, "table_A1_choice_of_c", "Table A1: different choices of c (managed Market factor)")


def table_a2_transaction_cost_parameters():
    p = cost_parameters().drop(index="Mkt-RF")
    table = pd.DataFrame(
        {
            "Monthly turnover (%)": p["monthly_turnover_pct"],
            "Monthly TC (bps)": p["monthly_cost"] * 1e4,
            "Implied kappa (bps)": p["kappa"] * 1e4,
        }
    ).T
    save_table(table, "table_A2_transaction_cost_parameters", "Table A2: transaction-cost parameters (Barroso and Detzel, 2021)")


def main():
    figure_1_exposure_variance_vs_volatility()
    table_a1_choice_of_c()
    table_a2_transaction_cost_parameters()


if __name__ == "__main__":
    main()
