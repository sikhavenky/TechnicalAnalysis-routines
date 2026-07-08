"""
Presence/completeness checks run before pushing input data or saving output
data. These are deliberately shallow (required top-level keys per ticker,
non-empty) - they catch "a required ticker is missing" or "a ticker came back
empty", not deep schema drift. For the full field-level shape, see
schemas/technical_input_schema.json and schemas/technical_summary_schema.json
in the TechnicalAnalysis-routines repo.
"""

REQUIRED_INPUT_TICKER_FIELDS = (
    "ticker", "company", "date", "latest", "moving_averages", "performance", "history",
)

REQUIRED_OUTPUT_SUMMARY_FIELDS = (
    "ticker", "company", "date", "signal", "classification", "verdict",
    "latest", "moving_averages", "scores", "levels", "performance",
    "analysis", "trade_plan", "institutional_view", "history",
)


def _missing(entries_by_ticker, required_tickers, required_fields):
    problems = []
    for ticker in required_tickers:
        entry = entries_by_ticker.get(ticker)
        if entry is None:
            problems.append(ticker)
            continue
        if any(entry.get(field) in (None, "", []) for field in required_fields):
            problems.append(ticker)
    return problems


def validate_input_payload(payload, required_tickers):
    """Return the list of required tickers missing or incomplete in an input payload."""
    by_ticker = {t.get("ticker"): t for t in payload.get("tickers", [])}
    return _missing(by_ticker, required_tickers, REQUIRED_INPUT_TICKER_FIELDS)


def validate_output_payload(payload, required_tickers):
    """Return the list of required tickers missing or incomplete in an output payload."""
    by_ticker = {s.get("ticker"): s for s in payload.get("summaries", [])}
    return _missing(by_ticker, required_tickers, REQUIRED_OUTPUT_SUMMARY_FIELDS)
