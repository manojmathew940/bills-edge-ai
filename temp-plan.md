# Step-By-Step Migration To Simplified Data Extractor Workflow

## Summary

Migrate `/ask` from planner-driven branching to one simple flow: extractor LLM
decides whether to query local data, app validates/executes SQL, answer LLM
responds with the data or answers directly when no local data is needed. Remove
planner and game-metrics behavior from `/ask` and the UI, but keep the
standalone `/games/{season}/{week}/metrics` endpoint/module for now.

## Step-By-Step Changes

1. Add a new `app/llm/data_extraction.py`.
   - Replace planner concepts with `DataExtractionDecision`.
   - Expected fields: `needs_data`, `sql`, `reason`, `confidence`,
     `data_not_needed_reason`.
   - Extractor prompt must instruct the LLM to produce JSON only, not answer
     the user.
   - SQL must target only approved analytics views, initially `bills_plays`.

2. Add extraction parsing and debug helpers.
   - Parse JSON robustly using the existing planner-style JSON extraction
     pattern.
   - Normalize invalid/missing fields safely.
   - If `needs_data=false`, force `sql=None`.
   - If `needs_data=true` but SQL is blank, treat it as no usable data request.
   - Add `build_data_extraction_debug_payload`.

3. Refactor answer generation in `app/llm/answering.py`.
   - Replace `answer_game_question` and `answer_direct_question` as `/ask`
     dependencies with one `answer_question`.
   - Inputs: original question, extraction decision, SQL execution result or
     no-data state.
   - Instructions: answer from returned data when present; if data is
     missing/insufficient, say what is missing; do not invent current news,
     injuries, quotes, roster moves, or unprovided context.
   - Keep old game-answer helpers only if still needed by the standalone metrics
     endpoint; otherwise leave them unused for now and remove later.

4. Rewrite `/ask` in `app/main.py`.
   - Remove `run_planner_llm` from `/ask`.
   - Flow:
     - run data extractor
     - if extractor returns SQL, call `validate_and_execute_analytics_sql`
     - pass extraction decision plus SQL result to answer LLM
     - return answer plus `data_request`, `analytics`, `provider`, and optional
       `debug_payload`
   - Suggested response shape:
     - `answer`
     - `provider`
     - `data_request`
     - `analytics`: `{sql, is_valid, validation_reason, columns, rows,
       row_limit}`
   - Preserve LLM configuration/service error handling with existing `503`
     behavior.
   - Keep `/games/{season}/{week}/metrics` unchanged.

5. Handle SQL failure simply in v1.
   - Do not add repair attempts in the first pass.
   - If SQL validation fails, pass the failure reason to the answer LLM and
     return `analytics.is_valid=false`.
   - If execution raises an analytics data error, return a clear `503` or answer
     path indicating local data was unavailable.
   - Add one-repair retry as a later follow-up after the basic flow is stable.

6. Update the UI to stop looking for planner/game metrics.
   - Remove `data.plan.engine` and `data.metrics` assumptions from
     `app/static/app.js`.
   - Grounding states:
     - `SQL analytics` when `analytics.is_valid=true` and rows were returned
     - `Data unavailable` when SQL was requested but invalid or failed
     - `No local data used` when extractor did not request data
   - Developer panel should show the new analytics payload instead of
     "Raw Metrics JSON."
   - Hide/remove the game-summary card from `/ask` results for this phase.

7. Remove planner usage and tests.
   - Delete or stop importing `app/llm/planning.py`.
   - Add tests for the new extraction parser and `/ask` flow with mocked LLM
     calls.
   - Existing SQL validation/execution/view tests should remain.

8. Update docs after code changes.
   - README examples should match the actual response shape.
   - Mention that `/games/{season}/{week}/metrics` remains available as a
     standalone deterministic endpoint, but `/ask` no longer uses it.

## Test Plan

- Install dependencies from `requirements.txt` before trusting tests; current
  environment previously failed test collection without `pyarrow` and
  `sqlglot`.
- Run existing SQL tests:
  - `python3 -m pytest tests/test_sql_validation.py tests/test_sql_execution.py tests/test_sql_views.py -q`
- Add unit tests for:
  - extractor parses valid SQL decision
  - extractor parses no-data decision
  - malformed extractor JSON raises/returns clear service error
  - `needs_data=false` ignores any accidental SQL
- Add API tests with mocked LLM clients for:
  - SQL-backed question returns `analytics` with rows
  - no-data question returns answer with empty/no analytics rows
  - invalid SQL returns validation reason and still calls answer generation with
    failure context
  - LLM configuration errors still return `503`

## Assumptions

- First migration removes planner/game-metrics only from `/ask` and the UI.
- Keep the standalone `/games/{season}/{week}/metrics` endpoint and
  `app/analytics/game_metrics.py` for now.
- Use only one extractor query per request in v1.
- No SQL repair retry in the first implementation pass.
- Approved SQL surface remains `bills_plays` only.
