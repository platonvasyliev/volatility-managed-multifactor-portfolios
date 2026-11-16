"""Transaction costs (Methodology: Transaction costs).

Factor-level estimates from Barroso and Detzel (2021), Table 1, Panel D
(1986-2015). For a portfolio with effective factor exposures x[f, t]:

    TC[t] = sum_f |x[f, t]| * TCbar_f  +  sum_f |x[f, t] - x[f, t-1]| * kappa_f

TCbar_f is the average monthly cost of holding the factor and
kappa_f = TCbar_f / (2 * turnover_f) is the implied cost per unit of exposure
change. The Market factor is assumed to be free to trade.
"""

import pandas as pd

BARROSO_DETZEL = pd.DataFrame(
    {
        "monthly_turnover_pct": [0.00, 3.72, 5.15, 5.18, 9.60, 52.94, 10.32],
        "annual_cost_pct": [0.00, 0.47, 0.64, 0.60, 1.04, 5.88, 4.06],
    },
    index=["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom", "BAB"],
)


def cost_parameters() -> pd.DataFrame:
    """Monthly holding cost TCbar and cost per unit of exposure change kappa (decimals)."""
    p = BARROSO_DETZEL.copy()
    turnover = p["monthly_turnover_pct"] / 100
    p["monthly_cost"] = p["annual_cost_pct"] / 100 / 12
    p["kappa"] = (p["monthly_cost"] / (2 * turnover)).where(turnover > 0, 0.0)
    return p


def transaction_costs(exposures: pd.DataFrame) -> pd.Series:
    """Monthly transaction cost of holding the given factor exposures."""
    p = cost_parameters().loc[exposures.columns]
    holding = (exposures.abs().fillna(0) * p["monthly_cost"]).sum(axis=1)
    trading = (exposures.diff().abs().fillna(0) * p["kappa"]).sum(axis=1)
    return holding + trading
