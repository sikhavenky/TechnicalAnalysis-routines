# Technical Analysis Claude Routine

This repo is used by a Claude Code Routine (https://code.claude.com/docs/en/routines) to
generate institutional technical-analysis JSON summaries on a daily schedule, replacing the
previously manual "paste technicals + prompt into Claude" workflow.

## Workflow

1. Backend technical pipeline computes the day's technical data and pushes it directly to
   the `main` branch as:

   input/technicals_input.json

   (shape defined in schemas/technical_input_schema.json)

2. A Claude Code Routine fires on a fixed daily schedule (configured at
   claude.ai/code/routines, not in this repo), clones this repo fresh, and reads the input
   file per routine_instruction.md.

3. The routine checks that input/technicals_input.json's run_date is today's date before
   doing anything else. If the backend hasn't pushed fresh data yet, the routine skips the
   run without touching output/technicals_summary.json.

4. Claude generates one structured technical summary per ticker and writes it to:

   output/technicals_summary.json

   (shape defined in schemas/technical_summary_schema.json)

5. The routine commits and pushes output/technicals_summary.json directly to `main`
   (requires "Allow unrestricted branch pushes" enabled for this repo in the routine's
   Permissions settings — by default Claude Code Routines can only push to `claude/`-
   prefixed branches).

6. Backend reads the output JSON from `main` and stores it in the database.

## Important

Do not call Claude API from the backend.
Do not call Anthropic SDK.
Claude Code Routine itself performs the AI analysis - no API integration needed.
The routine does not call any external APIs itself; it only ever reads the input file
already committed to the repo.

## Input

input/technicals_input.json — schema: schemas/technical_input_schema.json

## Output

output/technicals_summary.json — schema: schemas/technical_summary_schema.json

## Routine prompt

routine_instruction.md — this is what the Claude Code Routine follows on every run.

## Config reference

manifest.json — reference config for the backend pipeline (ticker list, deal_type per
ticker, upstream API, timezone). Not read by the routine itself.

## Backend integration contract

BACKEND_INTEGRATION.md — the exact steps the backend cron job must follow to fetch data
from the quant_agent API and write input/technicals_input.json correctly, including the
required field-stripping rule (the API returns full previous analysis records, not raw
data, so most of each response must be discarded before it becomes input).

## Backend reference implementation

backend_reference/ — reference Django views, URLs, Celery tasks, and helper functions
implementing BACKEND_INTEGRATION.md. Not executed by this repo or by the routine — copy
into your Django backend project. See backend_reference/README.md for setup steps and
open TODOs (deal_type mapping, QuantAgent field types).
