"""Robustness Analysis: factor ETFs. Table 6.

S&P 500 over 1980-2023 is proxied by the Market factor. For 2013-2023 the
tradable ETFs SPY, VLUE, MTUM and QUAL are used (adjusted prices from Yahoo
Finance, stored in data/, in excess of the Fama-French risk-free rate).
"""

import pandas as pd

from vmp import data, pipeline
from vmp.config import ETF_SAMPLE_START, SENTIMENT_END
from vmp.reporting import save_table
from vmp.sentiment import sentiment_table
from vmp.volatility_management import realized_volatility, volatility_manage


def etf_excess_returns() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily and monthly ETF returns in excess of the risk-free rate."""
    daily_rf, monthly_rf = (df["RF"] for df in pipeline.factors())
    prices = data.load_etf_prices()

    daily = prices.pct_change().iloc[1:]
    daily = daily.sub(daily_rf.reindex(daily.index), axis=0)

    month_end = prices.resample("ME").last()
    month_end.index = month_end.index.to_period("M").to_timestamp()
    monthly = month_end.pct_change().iloc[1:]
    monthly = monthly.sub(monthly_rf.reindex(monthly.index), axis=0)
    return daily, monthly.loc[ETF_SAMPLE_START:SENTIMENT_END]


def table_6_etfs_by_sentiment():
    daily, monthly = etf_excess_returns()
    # July 2013 is incomplete (QUAL launched on 18 July), so volatility is only measured
    # from August 2013 and the managed ETFs start in September 2013.
    daily = daily.loc[ETF_SAMPLE_START:]
    managed = pd.DataFrame(index=monthly.index)
    for col in monthly.columns:
        managed[col], _ = volatility_manage(monthly[col], realized_volatility(daily[col]))

    s = pipeline.single_factors()
    long_sample = sentiment_table(s.unmanaged, s.managed, {"Mkt-RF": "S&P 500, 1980-2023"})
    etfs = sentiment_table(
        monthly, managed,
        {"S&P 500": "S&P 500, 2013-2023", "Value": "MSCI USA Value", "Momentum": "MSCI USA Momentum", "Quality": "MSCI USA Quality"},
    )
    save_table(pd.concat([long_sample, etfs], axis=1), "table_6_etfs_by_sentiment",
               "Table 6: volatility-managed ETFs by sentiment regime", 2)


def main():
    table_6_etfs_by_sentiment()


if __name__ == "__main__":
    main()
