"""Load the factor, sentiment and ETF data (Methodology: Data).

All returns are returned as decimals. Monthly observations are dated at the
first day of the month.
"""

import pandas as pd

from .config import DATA_DIR, ETF_TICKERS


def _read_french(name: str, date_format: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / name, skipinitialspace=True)
    df["Date"] = pd.to_datetime(df["Date"].astype(str), format=date_format)
    return df


def load_daily_factors() -> pd.DataFrame:
    """Daily FF5 factors, Momentum, BAB and the risk-free rate."""
    ff5 = _read_french("ff5_daily.csv", "%Y%m%d")
    mom = _read_french("ff_momentum_daily.csv", "%Y%m%d")
    bab = pd.read_csv(DATA_DIR / "aqr_bab_daily.csv", parse_dates=["Date"])

    df = ff5.merge(mom, on="Date", how="left")
    pct_cols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF", "Mom"]
    df[pct_cols] = df[pct_cols] / 100
    df = df.merge(bab, on="Date", how="left")  # AQR data is already in decimals
    return df


def load_monthly_factors() -> pd.DataFrame:
    """Monthly FF5 factors, Momentum, BAB and the risk-free rate."""
    ff5 = _read_french("ff5_monthly.csv", "%Y%m")
    mom = _read_french("ff_momentum_monthly.csv", "%Y%m")
    bab = pd.read_csv(DATA_DIR / "aqr_bab_monthly.csv", parse_dates=["Date"])
    bab["Date"] = bab["Date"].dt.to_period("M").dt.to_timestamp()

    df = ff5.merge(mom, on="Date", how="left")
    pct_cols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF", "Mom"]
    df[pct_cols] = df[pct_cols] / 100
    df = df.merge(bab, on="Date", how="left")
    return df


def load_sentiment() -> pd.DataFrame:
    """Baker-Wurgler sentiment index, orthogonalized to macro conditions.

    Following the authors' recommendation, the orthogonalized index is replaced
    by the raw index for 03/2021-07/2021, where the lagged construction creates
    an artificial drop.
    """
    df = pd.read_csv(DATA_DIR / "baker_wurgler_sentiment.csv").dropna()
    artifact = df["yearmo"].between(202103, 202107)
    df.loc[artifact, "SENT_ORTH"] = df.loc[artifact, "SENT"]
    df["Date"] = pd.to_datetime(df["yearmo"].astype(int).astype(str), format="%Y%m")
    return df[["Date", "SENT_ORTH"]].reset_index(drop=True)


def load_etf_prices() -> pd.DataFrame:
    """Daily adjusted close prices of SPY, VLUE, MTUM and QUAL (Yahoo Finance snapshot).

    Only days on which all four ETFs trade are kept, so the sample starts when
    QUAL launched (18 July 2013).
    """
    prices = pd.read_csv(DATA_DIR / "etf_prices_daily.csv", index_col="Date", parse_dates=True)
    return prices.rename(columns=ETF_TICKERS).dropna()
