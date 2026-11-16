"""Settings used throughout the thesis (Methodology section)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"

# The seven long-short equity factors
FACTORS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom", "BAB"]
FACTOR_NAMES = {
    "Mkt-RF": "Market",
    "SMB": "Size",
    "HML": "Value",
    "RMW": "Profitability",
    "CMA": "Investment",
    "Mom": "Momentum",
    "BAB": "BAB",
}

# Sample
SAMPLE_START = "1980-01-01"
SAMPLE_END = "2025-12-31"
SENTIMENT_END = "2023-12-31"  # last year of the Baker-Wurgler index
SUBPERIODS = {
    "1980-2002": ("1980-01-01", "2002-12-31"),
    "2003-2025": ("2003-01-01", "2025-12-31"),
}

# Volatility management
TRADING_DAYS_PER_MONTH = 21

# Multifactor portfolio construction
EQUAL_RISK_LOOKBACK_DAYS = 252
COVARIANCE_LOOKBACK_DAYS = 126
MEAN_LOOKBACK_MONTHS = 120
MIN_DAILY_OBSERVATIONS = 30
WEIGHT_BOUNDS = (0.05, 0.50)

# Statistical inference
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_AVG_BLOCK = 5
BOOTSTRAP_SEED = 42
NEWEY_WEST_LAGS = 12

# Factor ETFs (Table 6)
ETF_TICKERS = {"SPY": "S&P 500", "VLUE": "Value", "MTUM": "Momentum", "QUAL": "Quality"}
ETF_DOWNLOAD_START = "2013-07-01"
ETF_DOWNLOAD_END = "2024-01-01"
ETF_SAMPLE_START = "2013-08-01"
