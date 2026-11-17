"""Build every return series used in the thesis once, and cache it.

Sample: 1980-02 to 2025-12 for all strategies (see config.SAMPLE_START).
Each strategy starts holding its position in the first sample month, so no
trading cost is charged for setting it up.
"""

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from . import data
from .config import FACTORS, SAMPLE_END, SAMPLE_START
from .factor_portfolios import (
    equal_risk_weights,
    equal_weights,
    optimized_weights,
    portfolio_returns,
)
from .transaction_costs import transaction_costs
from .volatility_management import daily_portfolio_returns, realized_volatility, volatility_manage

PORTFOLIOS = ["Equal Weights", "Equal Risk", "Minimum Variance", "MVE"]


@dataclass
class Strategies:
    """Unmanaged and volatility-managed returns, gross and net of costs."""

    unmanaged: pd.DataFrame
    managed: pd.DataFrame
    exposure: pd.DataFrame
    unmanaged_net: pd.DataFrame
    managed_net: pd.DataFrame


@lru_cache
def factors() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Full-history daily and monthly factor returns, indexed by date."""
    return data.load_daily_factors().set_index("Date"), data.load_monthly_factors().set_index("Date")


def sample_months() -> pd.DatetimeIndex:
    _, monthly = factors()
    return monthly.loc[SAMPLE_START:SAMPLE_END].index


@lru_cache
def single_factors() -> Strategies:
    """The seven factors, unmanaged and volatility-managed (Table 1)."""
    daily, monthly = factors()
    unmanaged = monthly.loc[sample_months(), FACTORS]

    managed, exposure = pd.DataFrame(index=unmanaged.index), pd.DataFrame(index=unmanaged.index)
    for f in FACTORS:
        managed[f], exposure[f] = volatility_manage(unmanaged[f], realized_volatility(daily[f]))

    unmanaged_net, managed_net = unmanaged.copy(), managed.copy()
    for f in FACTORS:
        unmanaged_net[f] -= transaction_costs(pd.DataFrame({f: 1.0}, index=unmanaged.index))
        managed_net[f] -= transaction_costs(exposure[[f]])
    return Strategies(unmanaged, managed, exposure, unmanaged_net, managed_net)


@lru_cache
def multifactor_weights(shrinkage: bool = True, with_previous_month: bool = False) -> dict[str, pd.DataFrame]:
    """Weights held in each sample month for the four construction methods.

    with_previous_month also returns the weights of the month before the sample,
    which are needed for that month's realized portfolio volatility.
    """
    daily, monthly = factors()
    months = sample_months()
    if with_previous_month:
        months = months.insert(0, months[0] - pd.offsets.MonthBegin(1))
    return {
        "Equal Weights": equal_weights(months, FACTORS),
        "Equal Risk": equal_risk_weights(daily[FACTORS]).reindex(months),
        "Minimum Variance": optimized_weights(daily[FACTORS], monthly, months, "min_variance", shrinkage),
        "MVE": optimized_weights(daily[FACTORS], monthly, months, "mve", shrinkage),
    }


@lru_cache
def multifactor() -> Strategies:
    """The four multifactor portfolios, unmanaged and volatility-managed (Tables 2-3)."""
    daily, monthly = factors()
    months = sample_months()
    weights = multifactor_weights(with_previous_month=True)

    unmanaged, managed, exposure = (pd.DataFrame(index=months) for _ in range(3))
    unmanaged_net, managed_net = pd.DataFrame(index=months), pd.DataFrame(index=months)
    for name in PORTFOLIOS:
        risk = realized_volatility(daily_portfolio_returns(daily[FACTORS], weights[name]))
        w = weights[name].loc[months]
        unmanaged[name] = portfolio_returns(monthly.loc[months], w)
        managed[name], exposure[name] = volatility_manage(unmanaged[name], risk)

        unmanaged_net[name] = unmanaged[name] - transaction_costs(w)
        managed_net[name] = managed[name] - transaction_costs(w.mul(exposure[name], axis=0))
    return Strategies(unmanaged, managed, exposure, unmanaged_net, managed_net)
