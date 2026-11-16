"""Multifactor portfolio construction (Methodology: Factor portfolios).

Every function returns a DataFrame of weights indexed by the month in which
they are held. Weights for month t only use data up to the end of month t-1.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

from .config import (
    COVARIANCE_LOOKBACK_DAYS,
    EQUAL_RISK_LOOKBACK_DAYS,
    MEAN_LOOKBACK_MONTHS,
    MIN_DAILY_OBSERVATIONS,
    TRADING_DAYS_PER_MONTH,
    WEIGHT_BOUNDS,
)


def equal_weights(months: pd.DatetimeIndex, factors: list[str]) -> pd.DataFrame:
    """1/N in every factor."""
    return pd.DataFrame(1 / len(factors), index=months, columns=factors)


def equal_risk_weights(daily: pd.DataFrame, lookback: int = EQUAL_RISK_LOOKBACK_DAYS) -> pd.DataFrame:
    """Inverse-volatility weights from the last `lookback` daily returns."""
    inv_vol = 1 / daily.rolling(lookback).std()
    w = inv_vol.div(inv_vol.sum(axis=1), axis=0)
    formed = w.resample("ME").last()
    formed.index = (formed.index.to_period("M") + 1).to_timestamp()
    return formed


def _optimize(objective, n: int) -> np.ndarray:
    res = minimize(
        objective,
        x0=np.repeat(1 / n, n),
        method="SLSQP",
        bounds=[WEIGHT_BOUNDS] * n,
        constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1},
    )
    return res.x if res.success else np.repeat(np.nan, n)


def min_variance(cov: np.ndarray) -> np.ndarray:
    """Constrained minimum-variance weights."""
    return _optimize(lambda w: float(w @ cov @ w) * 1e6, cov.shape[0])


def max_sharpe(cov: np.ndarray, mu: np.ndarray) -> np.ndarray:
    """Constrained mean-variance efficient (maximum Sharpe ratio) weights."""

    def objective(w):
        vol = np.sqrt(w @ cov @ w)
        return 1e10 if vol == 0 else -(w @ mu) / vol

    return _optimize(objective, cov.shape[0])


def optimized_weights(
    daily: pd.DataFrame,
    monthly: pd.DataFrame,
    months: pd.DatetimeIndex,
    method: str,
    shrinkage: bool = True,
) -> pd.DataFrame:
    """Minimum-variance ("min_variance") or MVE ("mve") weights, rebalanced monthly.

    The covariance matrix uses the last 126 daily returns (Ledoit-Wolf shrinkage
    or the sample estimate), scaled to a monthly horizon. MVE expected returns
    are the average of the last 120 monthly returns.
    """
    factors = list(daily.columns)
    rows = []
    for month in months:
        hist = daily.loc[daily.index < month].dropna().tail(COVARIANCE_LOOKBACK_DAYS)
        hist_m = monthly.loc[monthly.index < month, factors].dropna().tail(MEAN_LOOKBACK_MONTHS)

        enough = len(hist) >= MIN_DAILY_OBSERVATIONS
        if method == "mve":
            enough = enough and len(hist_m) >= MEAN_LOOKBACK_MONTHS
        if not enough:
            rows.append(np.repeat(np.nan, len(factors)))
            continue

        cov = LedoitWolf().fit(hist.to_numpy()).covariance_ if shrinkage else hist.cov().to_numpy()
        cov = cov * TRADING_DAYS_PER_MONTH
        if method == "min_variance":
            rows.append(min_variance(cov))
        elif method == "mve":
            rows.append(max_sharpe(cov, hist_m.mean().to_numpy()))
        else:
            raise ValueError(f"unknown method {method!r}")
    return pd.DataFrame(rows, index=months, columns=factors)


def portfolio_returns(monthly: pd.DataFrame, weights: pd.DataFrame) -> pd.Series:
    """Monthly portfolio returns given the weights held in each month."""
    w = weights.reindex(monthly.index)
    return (monthly[w.columns] * w).sum(axis=1)


def turnover(weights: pd.DataFrame) -> pd.Series:
    """One-way turnover: half the sum of absolute weight changes."""
    return 0.5 * weights.diff().abs().sum(axis=1).iloc[1:]
