# Backend Integration — Daily Input Feed

This is the exact contract the backend cron job must follow to populate
input/technicals_input.json for the Claude Code Routine. Without this job running
correctly, the routine's daily run has nothing fresh to read and will skip itself
(see routine_instruction.md Step 0).

## When

Write and push input/technicals_input.json to the `main` branch of this repo **before**
the routine's scheduled run.

- Routine trigger: daily at 9:00 AM GMT+5:30 (Asia/Kolkata).
- Recommended: run this job by 08:30 GMT+5:30 to leave buffer.

If this job fails or runs late on a given day, do nothing further — the routine's
freshness check will detect the stale `run_date` and skip that day's run rather than
regenerating a summary from old data. There is no need to backfill or retry from the
routine side.

## Steps

1. For each ticker in `manifest.json`'s `tickers` list, call:

   ```
   POST https://midasback.goldenhillsindia.com/api/quant_agent/all_tickers_latest/
   Authorization: Bearer <token>
   Content-Type: application/json

   {"ticker": "<ticker>", "deal_type": "<deal_type>"}
   ```

   Use the exact `deal_type` recorded for that ticker in `manifest.json` — it is **not**
   uniformly `"IPO"` (the API defaults to `"IPO"` if omitted, which is wrong for most of
   these tickers and will return a 404). See "Open item" below.

2. From each response, read `data.quant_analysis`. This field is a **JSON-encoded string**,
   not a nested object — it must be parsed (`json.loads` / `JSON.parse`) before use.

3. From the parsed object, keep **only** these fields:
   - `ticker`
   - `company`
   - `date`
   - `latest`
   - `moving_averages`
   - `performance`
   - `history`

   Discard everything else in the parsed object: `signal`, `classification`, `verdict`,
   `scores`, `levels`, `analysis`, `trade_plan`, `institutional_view`. Those are the
   **previous day's AI-generated conclusions**, stored by the last routine run. Feeding
   them back in as if they were fresh input would bias the routine toward repeating
   yesterday's verdict instead of doing a fresh read of the data.

4. Assemble the trimmed per-ticker objects into:

   ```json
   {
     "run_date": "<today's date, YYYY-MM-DD, Asia/Kolkata>",
     "source": "technical_indicator_pipeline",
     "tickers": [ /* trimmed ticker objects */ ]
   }
   ```

   This must match the shape in `schemas/technical_input_schema.json`.

5. If a ticker's API call fails or returns no data, either omit it from the array or
   include it with nulls in the numeric fields — `routine_instruction.md` (rule 11)
   already handles incomplete per-ticker data. Do not fail the whole job because one
   ticker is missing.

6. Write the result to `input/technicals_input.json`, commit, and push directly to
   `main`.

## Open item

`manifest.json` currently has `deal_type` confirmed only for `TSHA US` (`"FO"`). The
other 8 tickers — `GOOGL US`, `LEGN US`, `MLTX US`, `PTRN US`, `QURE US`, `SLDB US`,
`TNGX US`, `SYRE US` — are marked `"TODO_CONFIRM"` and must be filled in with real
values before this job can fetch them.
