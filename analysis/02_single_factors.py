"""Results: Single Factors. Figure 2, Table 1 (A3), Figure 3, Table A7."""

import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from vmp import pipeline
from vmp.config import FACTOR_NAMES, FACTORS
from vmp.inference import compare, describe, jobson_korkie_memmel_test
from vmp.plotting import plt, seven_panel_figure
from vmp.reporting import save_figure, save_table


def figure_2_risk_return_tradeoff():
    """Next-month factor return divided by this month's realized factor variance,
    averaged within terciles of this month's market volatility (DeMiguel et al., 2024, Fig. 1)."""
    daily, _ = pipeline.factors()
    returns = pipeline.single_factors().unmanaged
    in_sample = daily.loc[returns.index[0] : returns.index[-1] + pd.offsets.MonthEnd(0)]
    by_month = in_sample.groupby(in_sample.index.to_period("M"))
    market_vol = by_month["Mkt-RF"].std().to_timestamp()
    variance = by_month[FACTORS].var().to_timestamp()

    terciles = pd.cut(
        market_vol,
        bins=[-np.inf, market_vol.quantile(0.33), market_vol.quantile(0.66), np.inf],
        labels=["Low", "Medium", "High"],
    )
    tradeoff = returns.shift(-1) / variance
    # Daily (not monthly) variance is used, and the result is divided by 10 for readability.
    plot = tradeoff.groupby(terciles, observed=True).mean()[FACTORS] / 10

    x = np.arange(len(FACTORS))
    w = 0.24
    fig, ax = plt.subplots(figsize=(12, 6))
    for offset, state, color in [(-w, "Low", "0.70"), (0, "Medium", "0.45"), (w, "High", "0.1")]:
        ax.bar(x + offset, plot.loc[state], width=w, color=color, label=f"{state} market volatility", edgecolor="none")
    ax.set_xticks(x)
    ax.set_xticklabels(FACTORS)
    ax.set_ylabel("Risk-Return Trade-off")
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    save_figure(fig, "figure_2_factor_risk_return_tradeoff")


def _single_factor_panels(unmanaged, managed) -> pd.DataFrame:
    rows = {}
    for f in FACTORS:
        um, vm, test = describe(unmanaged[f]), describe(managed[f]), compare(managed[f], unmanaged[f])
        rows[f] = {
            ("Unmanaged", "Re (%)"): um["Re (%)"],
            ("Unmanaged", "Volatility (%)"): um["Volatility (%)"],
            ("Unmanaged", "SR"): um["SR"],
            ("Managed", "Re (%)"): vm["Re (%)"],
            ("Managed", "Volatility (%)"): vm["Volatility (%)"],
            ("Managed", "SR"): vm["SR"],
            ("Managed", "alpha (%)"): test["alpha_annual"] * 100,
            ("Managed", "t(alpha)"): test["t_alpha"],
            ("Comparison", "Delta SR"): test["sr_diff"],
            ("Comparison", "p-value"): test["p_value"],
        }
    return pd.DataFrame(rows)


def table_1_single_factors():
    s = pipeline.single_factors()
    gross = _single_factor_panels(s.unmanaged, s.managed)
    net = _single_factor_panels(s.unmanaged_net, s.managed_net)
    net["Mkt-RF"] = np.nan  # the Market factor is assumed to trade at zero cost
    full = pd.concat({"Gross": gross, "Net of costs": net})
    save_table(full, "table_A3_single_factors", "Table A3: performance of single factors")

    keep = [("Unmanaged", "SR"), ("Managed", "SR"), ("Comparison", "Delta SR"),
            ("Comparison", "p-value"), ("Managed", "alpha (%)"), ("Managed", "t(alpha)")]
    summary = pd.concat({"Panel A: no transaction costs": gross.loc[keep], "Panel B: net of costs": net.loc[keep]})
    save_table(summary, "table_1_single_factors", "Table 1: performance summary for single factors")
    return gross


def figure_3_cumulative_returns():
    s = pipeline.single_factors()
    fig, axes = seven_panel_figure(figsize=(14, 13))
    for ax, f in zip(axes, FACTORS):
        l1, = ax.plot(s.unmanaged.index, (1 + s.unmanaged[f]).cumprod(), color="gray")
        l2, = ax.plot(s.managed.index, (1 + s.managed[f]).cumprod(), color="black", linestyle="--")
        ax.set_title(f, pad=8)
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(mticker.LogLocator(base=10, subs=(1, 2, 5)))
        ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
        ax.yaxis.set_minor_formatter(mticker.NullFormatter())
        ax.grid(True)
    fig.legend([l1, l2], ["Unmanaged", "VM Managed"], loc="lower left", bbox_to_anchor=(0.08, 0.025), frameon=False)
    save_figure(fig, "figure_3_single_factor_cumulative_returns")


def table_a7_bootstrap_vs_jkm(gross: pd.DataFrame):
    s = pipeline.single_factors()
    rows = {}
    for f in FACTORS:
        rows[FACTOR_NAMES[f]] = {
            "Delta SR": gross.loc[("Comparison", "Delta SR"), f],
            "Bootstrap p-value": gross.loc[("Comparison", "p-value"), f],
            "JKM one-sided p-value": jobson_korkie_memmel_test(s.managed[f], s.unmanaged[f])["p_value"],
        }
    save_table(pd.DataFrame(rows), "table_A7_bootstrap_vs_jkm_single", "Table A7: bootstrap vs JKM test, single factors", 3)


def main():
    figure_2_risk_return_tradeoff()
    gross = table_1_single_factors()
    figure_3_cumulative_returns()
    table_a7_bootstrap_vs_jkm(gross)


if __name__ == "__main__":
    main()
