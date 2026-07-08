"""
Constants shared by the fetch and save-output Celery tasks.

Keep TICKER_DEAL_TYPES in sync with manifest.json's "tickers" list in this repo.
A ticker with deal_type None is treated as not-yet-confirmed: the fetch task will
skip it and log a warning instead of guessing (the API defaults to deal_type="IPO"
if omitted, which is wrong for most of these tickers and returns a 404).
"""

GITHUB_REPO = "sikhavenky/TechnicalAnalysis-routines"
GITHUB_BRANCH = "main"
INPUT_PATH = "input/technicals_input.json"
OUTPUT_PATH = "output/technicals_summary.json"

QUANT_AGENT_API_URL = "https://midasback.goldenhillsindia.com/api/quant_agent/all_tickers_latest/"

TICKER_DEAL_TYPES = {
    "GOOGL US": None,  # TODO_CONFIRM
    "LEGN US": None,  # TODO_CONFIRM
    "MLTX US": None,  # TODO_CONFIRM
    "PTRN US": None,  # TODO_CONFIRM
    "QURE US": None,  # TODO_CONFIRM
    "SLDB US": None,  # TODO_CONFIRM
    "TNGX US": None,  # TODO_CONFIRM
    "TSHA US": "FO",
    "SYRE US": None,  # TODO_CONFIRM
}
