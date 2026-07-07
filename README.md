# Technical Analysis Claude Routine

This repo is used by Claude Code Routine to generate institutional technical-analysis JSON summaries.

## Workflow

1. Backend technical pipeline writes latest ticker technical data to:

   input/technicals_input.json

2. Claude Code Routine reads the input file.

3. Claude generates one structured technical summary per ticker.

4. Claude writes final JSON to:

   output/technicals_summary.json

5. Backend reads the output JSON and stores it in the database.

## Important

Do not call Claude API from the backend.
Do not call Anthropic SDK.
Claude Code Routine itself performs the AI analysis.

## Input

input/technicals_input.json

## Output

output/technicals_summary.json

## Schema

schemas/technical_summary_schema.json
