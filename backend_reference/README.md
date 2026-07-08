# Backend reference implementation

This folder is reference code for your Django/Celery backend project (a different
repository from this one). It is **not** executed by anything in
TechnicalAnalysis-routines and is not read by the Claude Code Routine — copy these
files into your Django app and adjust imports/app paths to match your project
structure.

It implements the two Celery jobs described in `../BACKEND_INTEGRATION.md`, which
bracket the routine's daily run:

```
fetch_and_push_technicals_input  -->  routine runs on its 09:00 IST schedule  -->  save_technicals_output_to_db
```

1. **`fetch_and_push_technicals_input`** — calls `/api/quant_agent/all_tickers_latest/`
   for each configured ticker, strips each response down to raw data fields (drops the
   previous run's AI-generated conclusions), validates completeness, and pushes
   `input/technicals_input.json` to this repo's `main` branch via the GitHub Contents
   API. Schedule this ~30 minutes before the routine's daily run.

2. **`save_technicals_output_to_db`** — reads `output/technicals_summary.json` from
   this repo after the routine should have finished, validates completeness, and
   creates one new `QuantAgent` row per ticker for the day, copying forward deal-level
   fields the routine never generates.

## Files

| File | Purpose |
|---|---|
| `config.py` | Repo/API constants and the ticker → deal_type mapping (keep in sync with `manifest.json`'s `tickers` list) |
| `github_client.py` | Minimal GitHub Contents API read/write helpers |
| `validation.py` | Presence/completeness checks for input and output payloads |
| `tasks.py` | The two Celery tasks, plus the underlying fetch/strip helper functions |
| `views.py` | APIView endpoints to trigger either task on demand (testing; normal operation is Celery Beat) |
| `urls.py` | URL routing for the two trigger views |
| `celery_beat_schedule_snippet.py` | `CELERY_BEAT_SCHEDULE` entries to add to `settings.py` |

## Required setup before this will run

1. Adjust every relative import (`.models`, `.tasks`, etc.) to your actual Django
   app's module path.
2. Add these to your Django settings (env-var backed):
   - `MIDAS_QUANT_AGENT_API_TOKEN` — bearer token for calling your own
     `/api/quant_agent/all_tickers_latest/` endpoint
   - `GITHUB_TECHNICALS_REPO_TOKEN` — a GitHub token (fine-grained PAT or GitHub App
     installation token) with **Contents: Read and write** on
     `sikhavenky/TechnicalAnalysis-routines`
3. Fill in every `TODO_CONFIRM` in `config.py`'s `TICKER_DEAL_TYPES`. Tickers with no
   deal_type configured are skipped (logged as a warning), not fetched with a guessed
   value.
4. **Confirm `QuantAgent`'s real field types before relying on
   `save_technicals_output_to_db` in production.** See the TODO comment on
   `quant_analysis` in `tasks.py`:
   - `TextField`/`CharField` → the current `json.dumps(summary)` is correct.
   - `JSONField` → pass `summary` directly instead of `json.dumps(summary)`.
5. Register the schedule from `celery_beat_schedule_snippet.py` in
   `CELERY_BEAT_SCHEDULE`, timed around the routine's 09:00 GMT+5:30 trigger (fetch
   before it, save-to-db comfortably after it).

## Why an HTTP round-trip instead of querying QuantAgent directly?

If this Celery worker runs in the same codebase/process as
`QuantAgentAllTickersLatestAPIView`, querying `QuantAgent.objects` directly inside
`fetch_ticker_quant_analysis` (in `tasks.py`) would be simpler and avoid managing a
bearer token for your own API. This implementation follows the HTTP-endpoint approach
since that's the interface specified — swap it for a direct ORM query if the task and
the API live in the same service.
