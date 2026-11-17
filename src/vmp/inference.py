"""Performance measures and statistical tests.

* Stationary block-bootstrap test of the Sharpe-ratio difference (DeMiguel et al., 2024)
* Jobson-Korkie-Memmel test (Appendix, Tables A7-A8)
* Spanning regression of managed on unmanaged returns with Newey-West errors (Eq. 2)
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

from .config import BOOTSTRAP_AVG_BLOCK, BOOTSTRAP_SAMPLES, BOOTSTRAP_SEED, NEWEY_WEST_LAGS

MONTHS_PER_YEAR = 12


def sharpe_ratio(returns: pd.Series) -> float:
    """Annualized Sharpe ratio of monthly excess returns."""
    r = pd.Series(returns).dropna()
    return r.mean() / r.std() * np.sqrt(MONTHS_PER_YEAR)


def annualized_mean(returns: pd.Series) -> float:
    return returns.mean() * MONTHS_PER_YEAR


def annualized_volatility(returns: pd.Series) -> float:
    return returns.std() * np.sqrt(MONTHS_PER_YEAR)


def max_drawdown(returns: pd.Series) -> float:
    wealth = (1 + returns.dropna()).cumprod()
    return (wealth / wealth.cummax() - 1).min()


def describe(returns: pd.Series) -> dict:
    """Annualized excess return (%), volatility (%) and Sharpe ratio."""
    r = returns.dropna()
    return {
        "Re (%)": annualized_mean(r) * 100,
        "Volatility (%)": annualized_volatility(r) * 100,
        "SR": sharpe_ratio(r),
    }


def _aligned(managed: pd.Series, unmanaged: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    df = pd.concat([managed, unmanaged], axis=1).dropna()
    return df.iloc[:, 0].to_numpy(), df.iloc[:, 1].to_numpy()


def _stationary_bootstrap_indices(n: int, samples: int, avg_block: int, seed: int) -> np.ndarray:
    """Politis-Romano stationary bootstrap: blocks with geometric lengths, wrapping around."""
    rng = np.random.default_rng(seed)
    p_new_block = 1 / avg_block
    idx = np.empty((samples, n), dtype=np.int64)
    for b in range(samples):
        i = rng.integers(0, n)
        row = idx[b]
        row[0] = i
        for t in range(1, n):
            if rng.random() < p_new_block:
                i = rng.integers(0, n)
            else:
                i = (i + 1) % n
            row[t] = i
    return idx


def _sharpe_rows(x: np.ndarray) -> np.ndarray:
    return x.mean(axis=1) / x.std(axis=1, ddof=1) * np.sqrt(MONTHS_PER_YEAR)


def bootstrap_sharpe_test(
    managed: pd.Series,
    unmanaged: pd.Series,
    samples: int = BOOTSTRAP_SAMPLES,
    avg_block: int = BOOTSTRAP_AVG_BLOCK,
    seed: int = BOOTSTRAP_SEED,
) -> dict:
    """One-sided test of H0: SR(managed) <= SR(unmanaged).

    The p-value is the share of bootstrap samples in which the managed Sharpe
    ratio is below the unmanaged one.
    """
    x, y = _aligned(managed, unmanaged)
    sr_x, sr_y = sharpe_ratio(x), sharpe_ratio(y)
    idx = _stationary_bootstrap_indices(len(x), samples, avg_block, seed)
    diffs = _sharpe_rows(x[idx]) - _sharpe_rows(y[idx])
    return {
        "sr_managed": sr_x,
        "sr_unmanaged": sr_y,
        "sr_diff": sr_x - sr_y,
        "p_value": np.mean(diffs < 0),
    }


def jobson_korkie_memmel_p_value(managed: pd.Series, unmanaged: pd.Series) -> float:
    """One-sided p-value of the Jobson-Korkie test with the Memmel (2003) correction."""
    x, y = _aligned(managed, unmanaged)
    sr1, sr2 = x.mean() / x.std(ddof=1), y.mean() / y.std(ddof=1)
    rho = np.corrcoef(x, y)[0, 1]
    var = (2 * (1 - rho) + 0.5 * sr1**2 + 0.5 * sr2**2 - rho * sr1 * sr2) / len(x)
    return 1 - norm.cdf((sr1 - sr2) / np.sqrt(var))


def spanning_regression(managed: pd.Series, unmanaged: pd.Series, lags: int = NEWEY_WEST_LAGS) -> dict:
    """managed = alpha + beta * unmanaged + e, with Newey-West standard errors."""
    x, y = _aligned(managed, unmanaged)
    model = sm.OLS(x, sm.add_constant(y)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return {"alpha_annual": model.params[0] * MONTHS_PER_YEAR, "t_alpha": model.tvalues[0]}


def compare(managed: pd.Series, unmanaged: pd.Series) -> dict:
    """Sharpe ratios, bootstrap test and spanning-regression alpha in one go."""
    return {**bootstrap_sharpe_test(managed, unmanaged), **spanning_regression(managed, unmanaged)}
