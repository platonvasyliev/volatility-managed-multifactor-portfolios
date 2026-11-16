"""Sentiment regimes (Robustness Analysis), following Barroso and Detzel (2021).

Every month of year t is classified as high (low) sentiment if the
orthogonalized Baker-Wurgler index at the end of year t-1 is above (below) its
median over 1980-2023.
"""

import pandas as pd

HIGH, LOW = "High sentiment", "Low sentiment"


def prior_year_sentiment(sentiment: pd.DataFrame) -> pd.Series:
    """December index value of year t-1, indexed by year t."""
    dec = sentiment[sentiment["Date"].dt.month == 12]
    return pd.Series(dec["SENT_ORTH"].to_numpy(), index=dec["Date"].dt.year + 1)


def sentiment_regimes(
    dates: pd.DatetimeIndex, sentiment: pd.DataFrame, first_year: int = 1980, last_year: int = 2023
) -> pd.Series:
    """'High sentiment' / 'Low sentiment' label for each date (NaN without data)."""
    signal = prior_year_sentiment(sentiment)
    cut = signal.loc[first_year:last_year].median()
    value = pd.Series(dates.year, index=dates).map(signal)
    return value.where(value.isna(), (value >= cut).map({True: HIGH, False: LOW}))


def sentiment_table(unmanaged: pd.DataFrame, managed: pd.DataFrame, columns: dict) -> pd.DataFrame:
    """Unmanaged vs managed Sharpe ratios within low- and high-sentiment years (1980-2023).

    columns maps a column of `unmanaged`/`managed` to its label in the table.
    """
    from . import data
    from .config import SAMPLE_START, SENTIMENT_END
    from .inference import bootstrap_sharpe_test

    unmanaged = unmanaged.loc[SAMPLE_START:SENTIMENT_END]
    regime = sentiment_regimes(unmanaged.index, data.load_sentiment())
    panels = {}
    for state, label in [(LOW, "Panel A: low sentiment"), (HIGH, "Panel B: high sentiment")]:
        months = regime.index[regime == state]
        rows = {}
        for col, name in columns.items():
            test = bootstrap_sharpe_test(managed[col].reindex(months), unmanaged[col].reindex(months))
            rows[name] = {
                "SR unmanaged": test["sr_unmanaged"],
                "SR managed": test["sr_managed"],
                "Delta SR": test["sr_diff"],
                "p-value": test["p_value"],
            }
        panels[label] = pd.DataFrame(rows)
    return pd.concat(panels)
