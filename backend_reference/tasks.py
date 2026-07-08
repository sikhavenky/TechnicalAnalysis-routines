"""
Celery tasks that bracket the Claude Code Routine's daily run:

  fetch_and_push_technicals_input  ->  routine runs on its own schedule  ->  save_technicals_output_to_db

Schedule fetch_and_push_technicals_input comfortably before the routine's
daily trigger (e.g. 08:30 IST for a 09:00 IST routine), and
save_technicals_output_to_db comfortably after it (e.g. 09:45 IST), so the
routine has a fresh input to read and has had time to finish before you read
its output back.

Adjust the `from .models import QuantAgent` import (and any other relative
imports in this file) to match your actual Django app's module path.
"""

import json
import logging
from datetime import date

import requests
from celery import shared_task
from django.conf import settings

from .config import (
    GITHUB_BRANCH,
    GITHUB_REPO,
    INPUT_PATH,
    OUTPUT_PATH,
    QUANT_AGENT_API_URL,
    TICKER_DEAL_TYPES,
)
from .github_client import get_file, put_file
from .models import QuantAgent
from .validation import validate_input_payload, validate_output_payload

logger = logging.getLogger(__name__)

RAW_DATA_FIELDS = ("ticker", "company", "date", "latest", "moving_averages", "performance", "history")


def fetch_ticker_quant_analysis(ticker, deal_type):
    """
    Call /api/quant_agent/all_tickers_latest/ for one ticker and return the
    parsed quant_analysis dict, or None if no record exists for that
    ticker/deal_type.

    Note: if this task runs in the same codebase/process as
    QuantAgentAllTickersLatestAPIView, querying QuantAgent.objects directly
    here would be simpler and avoid managing a bearer token for your own API.
    This follows the HTTP-endpoint approach since that's the interface given -
    swap for a direct ORM call if task and API live in the same service.
    """
    resp = requests.post(
        QUANT_AGENT_API_URL,
        json={"ticker": ticker, "deal_type": deal_type},
        headers={"Authorization": f"Bearer {settings.MIDAS_QUANT_AGENT_API_TOKEN}"},
        timeout=15,
    )
    if resp.status_code == 404:
        logger.warning("No quant_agent record for %s (deal_type=%s)", ticker, deal_type)
        return None
    resp.raise_for_status()

    raw = resp.json()["data"]["quant_analysis"]
    # quant_analysis comes back as a JSON-encoded STRING, not a nested object.
    return json.loads(raw)


def strip_to_raw_fields(parsed):
    """
    Keep only the raw-data fields. Drop signal/classification/verdict/scores/
    levels/analysis/trade_plan/institutional_view - those are the PREVIOUS
    run's AI-generated conclusions and must not be fed back in as fresh input.
    """
    return {field: parsed.get(field) for field in RAW_DATA_FIELDS}


@shared_task(bind=True, max_retries=2)
def fetch_and_push_technicals_input(self, tickers=None):
    """
    Fetch each ticker's latest stored technical data, strip it down to raw
    fields, and push input/technicals_input.json to the routine repo's main
    branch. tickers defaults to every ticker configured in TICKER_DEAL_TYPES.
    """
    tickers = tickers or list(TICKER_DEAL_TYPES.keys())
    run_date = date.today().isoformat()

    ticker_payloads = []
    for ticker in tickers:
        deal_type = TICKER_DEAL_TYPES.get(ticker)
        if not deal_type:
            logger.warning("Skipping %s - no deal_type configured in config.TICKER_DEAL_TYPES", ticker)
            continue
        parsed = fetch_ticker_quant_analysis(ticker, deal_type)
        if parsed is None:
            continue
        ticker_payloads.append(strip_to_raw_fields(parsed))

    payload = {
        "run_date": run_date,
        "source": "technical_indicator_pipeline",
        "tickers": ticker_payloads,
    }

    missing = validate_input_payload(payload, required_tickers=tickers)
    if missing:
        logger.error("Not pushing input - missing/incomplete tickers: %s", missing)
        # Deliberately do not push a partial file. The routine's freshness
        # check (routine_instruction.md Step 0) will see today's date is
        # missing/stale and skip its run rather than process incomplete data.
        return {"pushed": False, "missing": missing}

    _, sha = get_file(GITHUB_REPO, INPUT_PATH, GITHUB_BRANCH, settings.GITHUB_TECHNICALS_REPO_TOKEN)
    put_file(
        GITHUB_REPO,
        INPUT_PATH,
        GITHUB_BRANCH,
        settings.GITHUB_TECHNICALS_REPO_TOKEN,
        content_str=json.dumps(payload, indent=2),
        message=f"Daily technicals input - {run_date}",
        sha=sha,
    )
    return {"pushed": True, "ticker_count": len(ticker_payloads)}


@shared_task(bind=True, max_retries=2)
def save_technicals_output_to_db(self):
    """
    Read output/technicals_summary.json from the routine repo and create one
    new QuantAgent row per ticker for today. Deal-level fields the routine
    never generates (pricing_date, region, deal_type, unique_deal_id,
    issuer_name, sector) are copied forward from each ticker's prior latest
    row, matching the existing _get_ticker_data lookup pattern.
    """
    content, _ = get_file(GITHUB_REPO, OUTPUT_PATH, GITHUB_BRANCH, settings.GITHUB_TECHNICALS_REPO_TOKEN)
    if content is None:
        logger.error("output/technicals_summary.json not found on %s", GITHUB_BRANCH)
        return {"saved": 0, "missing": list(TICKER_DEAL_TYPES.keys())}

    payload = json.loads(content)

    required_tickers = list(TICKER_DEAL_TYPES.keys())
    missing = validate_output_payload(payload, required_tickers=required_tickers)
    if missing:
        logger.error("Not saving to DB - missing/incomplete tickers in output: %s", missing)
        return {"saved": 0, "missing": missing}

    saved = 0
    for summary in payload.get("summaries", []):
        ticker = summary.get("ticker")
        prior = (
            QuantAgent.objects.filter(ticker=ticker)
            .order_by("-run_date", "-updated_at")
            .first()
        )
        QuantAgent.objects.create(
            ticker=ticker,
            run_date=payload.get("run_date"),
            pricing_date=prior.pricing_date if prior else None,
            region=prior.region if prior else None,
            deal_type=prior.deal_type if prior else TICKER_DEAL_TYPES.get(ticker),
            unique_deal_id=prior.unique_deal_id if prior else None,
            issuer_name=prior.issuer_name if prior else summary.get("company"),
            sector=prior.sector if prior else None,
            # TODO: confirm QuantAgent.quant_analysis's real field type.
            # TextField/CharField -> json.dumps(summary) as below is correct.
            # JSONField -> pass summary directly instead of json.dumps(summary).
            quant_analysis=json.dumps(summary),
            quant_signal=summary.get("signal"),
        )
        saved += 1

    return {"saved": saved}
