"""Checks that the implementation follows the methodology described in the thesis."""

import numpy as np
import pandas as pd
import pytest

from vmp import data
from vmp.config import FACTORS, WEIGHT_BOUNDS
from vmp.factor_portfolios import equal_risk_weights, max_sharpe, min_variance, turnover
from vmp.inference import bootstrap_sharpe_test, sharpe_ratio
from vmp.sentiment import HIGH, LOW, prior_year_sentiment, sentiment_regimes
from vmp.transaction_costs import cost_parameters, transaction_costs
from vmp.volatility_management import volatility_manage

rng = np.random.default_rng(0)
MONTHS = pd.date_range("2000-01-01", periods=60, freq="MS")


def test_volatility_management_uses_previous_month_volatility():
    returns = pd.Series(rng.normal(0.01, 0.04, len(MONTHS)), index=MONTHS)
    vol = pd.Series(rng.uniform(0.02, 0.08, len(MONTHS)), index=MONTHS)
    managed, exposure = volatility_manage(returns, vol, c=0.05)

    assert np.isnan(managed.iloc[0])  # no volatility estimate before the first month
    expected = 0.05 / vol.shift(1) * returns
    pd.testing.assert_series_equal(managed, expected, check_names=False)


def test_volatility_management_has_no_look_ahead():
    returns = pd.Series(rng.normal(0.01, 0.04, len(MONTHS)), index=MONTHS)
    vol = pd.Series(rng.uniform(0.02, 0.08, len(MONTHS)), index=MONTHS)
    changed = vol.copy()
    changed.iloc[30] *= 10  # a volatility shock in month 30 ...
    a, _ = volatility_manage(returns, vol, c=1)
    b, _ = volatility_manage(returns, changed, c=1)
    assert a.iloc[:31].equals(b.iloc[:31])  # ... can only affect month 31 onwards


def test_default_c_matches_unmanaged_volatility_and_keeps_sharpe():
    returns = pd.Series(rng.normal(0.01, 0.04, len(MONTHS)), index=MONTHS)
    vol = pd.Series(rng.uniform(0.02, 0.08, len(MONTHS)), index=MONTHS)
    managed, _ = volatility_manage(returns, vol)
    assert managed.std() == pytest.approx(returns.std())
    other, _ = volatility_manage(returns, vol, c=0.123)
    assert sharpe_ratio(managed) == pytest.approx(sharpe_ratio(other))


def _random_cov(n=7):
    a = rng.normal(size=(200, n)) * 0.01
    return np.cov(a, rowvar=False)


@pytest.mark.parametrize("weights", [lambda c: min_variance(c), lambda c: max_sharpe(c, rng.normal(0.005, 0.003, 7))])
def test_optimized_weights_respect_constraints(weights):
    w = weights(_random_cov())
    assert w.sum() == pytest.approx(1)
    assert (w >= WEIGHT_BOUNDS[0] - 1e-8).all() and (w <= WEIGHT_BOUNDS[1] + 1e-8).all()


def test_equal_risk_weights_only_use_past_data():
    days = pd.bdate_range("2000-01-03", "2002-12-31")
    daily = pd.DataFrame(rng.normal(0, 0.01, (len(days), 3)), index=days, columns=list("abc"))
    w = equal_risk_weights(daily, lookback=60)
    shocked = daily.copy()
    shocked.loc["2002-06"] *= 5
    w2 = equal_risk_weights(shocked, lookback=60)
    assert w.loc[:"2002-06"].equals(w2.loc[:"2002-06"])  # weights held in June use data up to May
    np.testing.assert_allclose(w.dropna().sum(axis=1), 1)


def test_transaction_costs():
    p = cost_parameters()
    assert p.loc["SMB", "kappa"] * 1e4 == pytest.approx(52.64, abs=0.01)  # Table A2
    constant = pd.DataFrame({"SMB": 1.0}, index=MONTHS)
    assert transaction_costs(constant).eq(p.loc["SMB", "monthly_cost"]).all()  # no trading cost
    doubled = constant.copy()
    doubled.iloc[10:] = 2.0
    cost = transaction_costs(doubled)
    assert cost.iloc[10] == pytest.approx(2 * p.loc["SMB", "monthly_cost"] + p.loc["SMB", "kappa"])


def test_turnover_is_half_the_absolute_weight_change():
    w = pd.DataFrame({"a": [0.5, 0.7], "b": [0.5, 0.3]}, index=MONTHS[:2])
    assert turnover(w).iloc[0] == pytest.approx(0.2)


def test_bootstrap_detects_a_better_strategy():
    base = pd.Series(rng.normal(0.005, 0.04, 400))
    better = base + 0.01
    result = bootstrap_sharpe_test(better, base, samples=500)
    assert result["sr_diff"] > 0 and result["p_value"] < 0.01
    assert bootstrap_sharpe_test(better, base, samples=500) == result  # reproducible


def test_sentiment_uses_prior_year_december():
    sentiment = pd.DataFrame({"Date": pd.date_range("2000-01-01", "2002-12-01", freq="MS")})
    sentiment["SENT_ORTH"] = np.arange(len(sentiment), dtype=float)
    signal = prior_year_sentiment(sentiment)
    assert signal[2001] == 11 and signal[2002] == 23  # December 2000 and 2001
    regimes = sentiment_regimes(pd.date_range("2001-01-01", "2002-12-01", freq="MS"), sentiment, 2001, 2002)
    assert (regimes.loc["2001"] == LOW).all() and (regimes.loc["2002"] == HIGH).all()


def test_data_covers_the_sample_without_gaps():
    monthly = data.load_monthly_factors().set_index("Date").loc["1980-01":"2025-12", FACTORS]
    assert len(monthly) == 552 and monthly.notna().all().all()
    sentiment = data.load_sentiment()
    assert sentiment.set_index("Date").loc["2021-03":"2021-07", "SENT_ORTH"].notna().all()
