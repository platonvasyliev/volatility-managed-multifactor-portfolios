"""Volatility management (Methodology: Volatility management, Eq. 1).

    f_vm[t+1] = c / sigma[t] * f[t+1]

sigma[t] is the realized volatility of daily returns in month t, scaled to a
monthly horizon. c is set so that the managed series has the same full-sample
volatility as the unmanaged one (it does not affect the Sharpe ratio).
"""

import numpy as np
import pandas as pd

from .config import TRADING_DAYS_PER_MONTH


def _by_month(daily: pd.Series):
    return daily.groupby(daily.index.to_period("M"))


def _to_month_start(s: pd.Series) -> pd.Series:
    s.index = s.index.to_timestamp()
    return s


def realized_volatility(daily: pd.Series) -> pd.Series:
    """Monthly realized volatility from daily returns (std x sqrt(21))."""
    return _to_month_start(_by_month(daily).std() * np.sqrt(TRADING_DAYS_PER_MONTH))


def realized_variance(daily: pd.Series) -> pd.Series:
    """Monthly realized variance from daily returns (var x 21)."""
    return _to_month_start(_by_month(daily).var() * TRADING_DAYS_PER_MONTH)


def volatility_manage(
    monthly: pd.Series, risk: pd.Series, c: float | None = None
) -> tuple[pd.Series, pd.Series]:
    """Scale next month's exposure by this month's risk estimate.

    Parameters
    ----------
    monthly : monthly returns of the unmanaged portfolio over the sample.
    risk : monthly realized volatility (or variance) of the same portfolio.
    c : scaling constant. By default it matches the unmanaged volatility.

    Returns
    -------
    managed returns and the exposure c / risk[t-1]. The first month of the
    sample has no lagged risk estimate, so both are NaN there.
    """
    lagged = risk.reindex(monthly.index).shift(1)
    raw = monthly / lagged
    if c is None:
        c = monthly.std() / raw.std()
    return c * raw, c / lagged


def daily_portfolio_returns(daily: pd.DataFrame, weights: pd.DataFrame) -> pd.Series:
    """Daily returns of a portfolio holding each month's weights."""
    month = daily.index.to_period("M").to_timestamp()
    w = weights[daily.columns].reindex(month).to_numpy()
    return (daily * w).sum(axis=1, skipna=False)
