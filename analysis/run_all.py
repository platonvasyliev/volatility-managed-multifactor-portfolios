"""Reproduce every table and figure of the thesis into results/.

    python analysis/run_all.py

Takes a few minutes, mostly for the bootstrap tests. Table 6 downloads ETF
prices from Yahoo Finance, so it needs an internet connection.
"""

import runpy
import time
from pathlib import Path

SCRIPTS = [
    "01_methodology.py",
    "02_single_factors.py",
    "03_multifactor.py",
    "04_sentiment.py",
    "05_etfs.py",
    "06_covariance_robustness.py",
]

if __name__ == "__main__":
    here = Path(__file__).parent
    for script in SCRIPTS:
        start = time.time()
        print(f"\n##### {script} #####")
        runpy.run_path(str(here / script), run_name="__main__")
        print(f"##### {script} done in {time.time() - start:.0f}s #####")
