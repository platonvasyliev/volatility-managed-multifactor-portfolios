"""Appendix: Ledoit-Wolf shrinkage vs sample covariance. Figure A1, Figure A2, Table A6."""

import pandas as pd

from vmp import pipeline
from vmp.factor_portfolios import turnover
from vmp.plotting import plt, stacked_weights
from vmp.reporting import save_figure, save_table


def _weights():
    lw, sample = pipeline.multifactor_weights(shrinkage=True), pipeline.multifactor_weights(shrinkage=False)
    return {
        ("Minimum Variance", "Ledoit-Wolf"): lw["Minimum Variance"],
        ("MVE", "Ledoit-Wolf"): lw["MVE"],
        ("Minimum Variance", "Sample covariance"): sample["Minimum Variance"],
        ("MVE", "Sample covariance"): sample["MVE"],
    }


def figure_a1_weights():
    fig, axes = plt.subplots(2, 2, figsize=(20, 10), sharex=True, sharey=True)
    for ax, ((name, cov), w) in zip(axes.flatten(), _weights().items()):
        title = f"{'Minimum Variance Portfolio' if name == 'Minimum Variance' else 'MVE Portfolio'}\n"
        title += "Ledoit-Wolf Shrinkage" if cov == "Ledoit-Wolf" else "Sample Covariance"
        stacked_weights(ax, w, title)
    for ax in axes[:, 0]:
        ax.set_ylabel("Weight (%)")
    for ax in axes[1]:
        ax.set_xlabel("Date")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=7, loc="upper center", bbox_to_anchor=(0.5, 1.02), frameon=False)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.90, bottom=0.10, hspace=0.35, wspace=0.12)
    save_figure(fig, "figure_A1_lw_vs_sample_cov_weights")


def turnovers() -> dict:
    return {key: turnover(w) for key, w in _weights().items()}


def figure_a2_turnover(to: dict):
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    for ax, name, title in [(axes[0], "Minimum Variance", "Minimum Variance Portfolio"),
                            (axes[1], "MVE", "Mean-Variance Efficient Portfolio")]:
        lw, sample = to[(name, "Ledoit-Wolf")], to[(name, "Sample covariance")]
        ax.plot(lw.index, lw * 100, label=f"{name}, Ledoit-Wolf", color="black", linewidth=1)
        ax.plot(sample.index, sample * 100, label=f"{name}, Sample Covariance", color="gray", linestyle="--", linewidth=1)
        ax.set_title(title)
        ax.set_ylabel("Monthly turnover (%)")
        ax.grid(True, alpha=0.3)
        ax.legend(frameon=False)
    axes[1].set_xlabel("Date")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.94, bottom=0.10, hspace=0.30)
    save_figure(fig, "figure_A2_lw_vs_sample_cov_turnover")


def table_a6_turnover(to: dict):
    table = pd.DataFrame(
        {f"{name}, {cov}": {"Annualized TO (%)": t.mean() * 12 * 100, "Max. monthly TO (%)": t.max() * 100}
         for (name, cov), t in to.items()}
    ).T
    save_table(table, "table_A6_turnover", "Table A6: turnover with Ledoit-Wolf vs sample covariance")


def main():
    figure_a1_weights()
    to = turnovers()
    figure_a2_turnover(to)
    table_a6_turnover(to)


if __name__ == "__main__":
    main()
