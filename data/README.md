# Data

Snapshot of the data used in the thesis, so that every table can be reproduced
exactly. The providers update their files every month and occasionally revise
history, so freshly downloaded files will give slightly different numbers.

| File | Content | Frequency | Source |
|---|---|---|---|
| `ff5_daily.csv`, `ff5_monthly.csv` | Fama-French 5 factors (2x3): Mkt-RF, SMB, HML, RMW, CMA and RF, in percent | daily / monthly | [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) |
| `ff_momentum_daily.csv`, `ff_momentum_monthly.csv` | Momentum factor (Mom), in percent | daily / monthly | Kenneth R. French Data Library |
| `aqr_bab_daily.csv`, `aqr_bab_monthly.csv` | U.S. Betting-Against-Beta factor, in decimals | daily / monthly | [AQR: Betting Against Beta: Equity Factors](https://www.aqr.com/Insights/Datasets/Betting-Against-Beta-Equity-Factors-Monthly) |
| `baker_wurgler_sentiment.csv` | Baker-Wurgler investor sentiment index (`SENT`) and the version orthogonalized to macro conditions (`SENT_ORTH`) | monthly | [Jeffrey Wurgler's website](https://pages.stern.nyu.edu/~jwurgler/) (data updated May 31, 2024) |
| `etf_prices_daily.csv` | Adjusted close prices of SPY, VLUE, MTUM and QUAL, July 2013 to December 2023 (QUAL starts on 18 July 2013) | daily | Yahoo Finance |

The factor and sentiment files were downloaded in April-May 2026, the ETF prices
in November 2026. Yahoo Finance adjusts past prices for dividends and splits
(MTUM and QUAL had 4-for-1 splits on 5 November 2026, so their price levels are a
quarter of the historical quotes); returns are unaffected. The ETF file was created with:

```python
import yfinance as yf
yf.download(["SPY", "VLUE", "MTUM", "QUAL"], start="2013-07-01", end="2024-01-01", auto_adjust=False)["Adj Close"]
```

## Changes made to the original files

* **AQR BAB:** only the U.S. BAB column of the `BAB Factors` sheet is kept, and
  converted from Excel to CSV with ISO dates. The values are unchanged.
* **Baker-Wurgler:** only the date and the two index columns are kept. As
  recommended by the authors, the orthogonalized index is replaced by the raw
  index for 03/2021-07/2021, where the lagged construction creates an
  artificial drop. That replacement is done in code (`vmp.data.load_sentiment`).
* Kenneth French files are unchanged.

## Citations

* Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics*, 116(1), 1-22.
* Frazzini, A., & Pedersen, L. H. (2014). Betting against beta. *Journal of Financial Economics*, 111(1), 1-25.
* Baker, M., & Wurgler, J. (2006). Investor sentiment and the cross-section of stock returns. *Journal of Finance*, 61(4), 1645-1680.

The data belong to their providers and are redistributed here for academic
replication only.
