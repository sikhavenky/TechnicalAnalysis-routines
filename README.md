# Technical Analysis Claude Routine

This repo backs a Claude Code Routine (https://code.claude.com/docs/en/routines) that
generates institutional technical-analysis JSON summaries, replacing the previously
manual "paste technicals + prompt into Claude" workflow.

## Workflow

There is no file-based handoff. On each run, the routine itself:

1. Is triggered via its API trigger (the backend hits the routine's `/fire` endpoint
   with its permanent bearer token whenever a run should happen).
2. For each ticker in `manifest.json`'s `tickers` list (or specific tickers named in
   the triggering request), calls the technicals-data API to fetch that ticker's
   latest data — see `technical_api` in `manifest.json` and Step 1 of
   `routine_instruction.md`.
3. Generates one institutional-grade technical-analysis summary per ticker, in the
   shape defined in `schemas/technical_summary_schema.json`.
4. Uploads each generated summary via the upload API as soon as it's generated — see
   `upload_api` in `manifest.json` and Step 4 of `routine_instruction.md`. Known gap:
   this endpoint also accepts deal-level fields (`deal_type`, `region`, `sector`,
   `pricing_date`, `unique_deal_id`, `issuer_name`) that get blanked on today's record
   if omitted, and the routine has no source for them, so it intentionally omits them.

The routine reads and writes nothing in this repository at run time. This repo only
holds its prompt (`routine_instruction.md`), config (`manifest.json`), and reference
schema/example for the output shape.

## Important

Do not call Claude API from the backend. Do not call the Anthropic SDK. The Claude
Code Routine itself performs the AI analysis — it calls the technicals-data and
upload APIs directly using a bearer token read from an environment variable, never
from a file committed to this repo.

## Required routine configuration (set in the routine's edit dialog, not in this repo)

- **Trigger**: an API trigger (not a fixed schedule) — the backend fires a run whenever
  it wants one.
- **Environment variable**: `MIDAS_API_TOKEN` set to the permanent bearer token, added
  under the routine's cloud Environment settings.
- **Network access**: the environment's network access must be set to Custom with
  `midasback.goldenhillsindia.com` allowlisted (both the fetch and upload APIs are on
  this same host) — the Default/Trusted environment blocks arbitrary external hosts.

## Prompt

`routine_instruction.md` — this is what the Claude Code Routine follows on every run.

## Config reference

`manifest.json` — ticker list, technicals-data API config, upload API config. Not read
by the routine itself; it's a reference the prompt's values are kept in sync with.

## Output shape reference

`schemas/technical_summary_schema.json` and `examples/example_output.json` — the exact
shape and style of the summary the routine generates per ticker.
