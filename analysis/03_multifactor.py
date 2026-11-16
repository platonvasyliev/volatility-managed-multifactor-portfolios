"""Results: Multifactor portfolios. Table A4, Figure 4, Figures 5a-5b, Table 2 (A5), Table 3, Table A8."""

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from vmp import pipeline
from vmp.config import FACTORS, SAMPLE_END, SAMPLE_START, SUBPERIODS
from vmp.inference import compare, describe, jobson_korkie_memmel_test, max_drawdown
from vmp.pipeline import PORTFOLIOS
from vmp.plotting import plt, stacked_weights
from vmp.reporting import save_figure, save_table


def table_a4_correlations():
    """Pairwise correlations with t-test significance stars (1980-2025)."""
    _, monthly = pipeline.factors()
    r = monthly.loc[SAMPLE_START:SAMPLE_END, FACTORS]
    n = len(r)
    corr = r.corr()
    table = pd.DataFrame("", index=FACTORS, columns=FACTORS)
    for i, a in enumerate(FACTORS):
        for b in FACTORS[: i + 1]:
            rho = corr.loc[a, b]
            if a == b:
                table.loc[a, b] = "1"
                continue
            t_stat = rho * np.sqrt((n - 2) / (1 - rho**2))
            p = 2 * (1 - student_t.cdf(abs(t_stat), df=n - 2))
            stars = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""
            table.loc[a, b] = f"{rho:.2f}{stars}"
    save_table(table, "table_A4_correlations", "Table A4: correlation matrix of monthly factor returns")


def figure_4_factor_weights():
    weights = pipeline.multifactor_weights()
    titles = ["Equal-Weighted Portfolio", "Equal-Risk Portfolio", "Minimum Variance Portfolio", "MVE Portfolio"]
    fig, axes = plt.subplots(2, 2, figsize=(20, 10), sharex=True, sharey=True)
    for ax, name, title in zip(axes.flatten(), PORTFOLIOS, titles):
        stacked_weights(ax, weights[name], title)
    for ax in axes[:, 0]:
        ax.set_ylabel("Weight (%)")
    for ax in axes[1]:
        ax.set_xlabel("Date")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout()
    save_figure(fig, "figure_4_multifactor_weights")


def figure_5a_cumulative_returns():
    m = pipeline.multifactor()
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    for i, (ax, name) in enumerate(zip(axes.flatten(), PORTFOLIOS)):
        l1, = ax.plot(m.unmanaged.index, (1 + m.unmanaged[name]).cumprod(), linewidth=2, color="gray")
        l2, = ax.plot(m.managed.index, (1 + m.managed[name]).cumprod(), linewidth=2, linestyle="--", color="black")
        ax.set_yscale("log")
        ax.set_title(name)
        if i in (0, 2):
            ax.set_ylabel("Cumulative return")
        ax.grid(True, alpha=0.3)
    fig.legend([l1, l2], ["Unmanaged", "Managed"], loc="upper left", ncol=2, frameon=False, bbox_to_anchor=(0.08, 0.95))
    fig.tight_layout()
    save_figure(fig, "figure_5a_multifactor_cumulative_returns")


def figure_5b_exposure():
    m = pipeline.multifactor()
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    for i, (ax, name) in enumerate(zip(axes.flatten(), PORTFOLIOS)):
        ax.plot(m.exposure.index, m.exposure[name], linewidth=1, color="black")
        ax.set_title(name)
        if i in (0, 2):
            ax.set_ylabel("Exposure")
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save_figure(fig, "figure_5b_multifactor_exposure")


def _multifactor_panels(unmanaged, managed, with_drawdown=False) -> pd.DataFrame:
    rows = {}
    for name in PORTFOLIOS:
        um, vm, test = describe(unmanaged[name]), describe(managed[name]), compare(managed[name], unmanaged[name])
        row = {
            ("Unmanaged", "Re (%)"): um["Re (%)"],
            ("Unmanaged", "Volatility (%)"): um["Volatility (%)"],
            ("Unmanaged", "SR"): um["SR"],
        }
        if with_drawdown:
            row[("Unmanaged", "MDD (%)")] = max_drawdown(unmanaged[name]) * 100
        row |= {
            ("Managed", "Re (%)"): vm["Re (%)"],
            ("Managed", "Volatility (%)"): vm["Volatility (%)"],
            ("Managed", "SR"): vm["SR"],
            ("Managed", "alpha (%)"): test["alpha_annual"] * 100,
            ("Managed", "t(alpha)"): test["t_alpha"],
            ("Comparison", "Delta SR"): test["sr_diff"],
            ("Comparison", "p-value"): test["p_value"],
        }
        rows[name] = row
    return pd.DataFrame(rows)


SUMMARY_ROWS = [("Unmanaged", "SR"), ("Managed", "SR"), ("Comparison", "Delta SR"),
                ("Comparison", "p-value"), ("Managed", "alpha (%)"), ("Managed", "t(alpha)")]


def table_2_multifactor():
    m = pipeline.multifactor()
    # The full-sample panel covers the months with a managed return (1980-02 onward);
    # the two subsamples split the calendar sample in half (1980-01 to 2002-12, 2003-01 to 2025-12).
    first_managed_month = m.managed.first_valid_index()
    periods = {"Full sample 1980-2025": (first_managed_month, SAMPLE_END)}
    periods |= {f"Subsample {k}": v for k, v in SUBPERIODS.items()}
    panels = {
        label: _multifactor_panels(
            m.unmanaged.loc[start:end], m.managed.loc[start:end], with_drawdown=label.startswith("Full")
        )
        for label, (start, end) in periods.items()
    }
    save_table(pd.concat(panels), "table_A5_multifactor", "Table A5: performance of multifactor portfolios")
    summary = pd.concat({label: panel.loc[SUMMARY_ROWS] for label, panel in panels.items()})
    save_table(summary, "table_2_multifactor", "Table 2: performance summary for multifactor portfolios")
    return panels["Full sample 1980-2025"]


def table_3_multifactor_net():
    m = pipeline.multifactor()
    panel = _multifactor_panels(m.unmanaged_net, m.managed_net)
    save_table(panel.loc[SUMMARY_ROWS], "table_3_multifactor_net", "Table 3: multifactor portfolios net of transaction costs")


def table_a8_bootstrap_vs_jkm(full: pd.DataFrame):
    m = pipeline.multifactor()
    table = pd.DataFrame(
        {
            name: {
                "Delta SR": full.loc[("Comparison", "Delta SR"), name],
                "Bootstrap p-value": full.loc[("Comparison", "p-value"), name],
                "JKM one-sided p-value": jobson_korkie_memmel_test(m.managed[name], m.unmanaged[name])["p_value"],
            }
            for name in PORTFOLIOS
        }
    )
    save_table(table, "table_A8_bootstrap_vs_jkm_multifactor", "Table A8: bootstrap vs JKM test, multifactor portfolios", 3)


def main():
    table_a4_correlations()
    figure_4_factor_weights()
    figure_5a_cumulative_returns()
    figure_5b_exposure()
    full = table_2_multifactor()
    table_3_multifactor_net()
    table_a8_bootstrap_vs_jkm(full)


if __name__ == "__main__":
    main()
