# Bills AI Analyst Roadmap

## Purpose

This document captures the planned build order for the Bills AI Analyst project.

The project is intended to evolve into a Bills-focused web application that
combines:

- structured NFL and Bills analytics data
- LLM-based data extraction from approved analytics views
- deterministic SQL validation and execution
- LLM-powered explanation generation grounded in returned data
- optional retrieval or web search for context that is not available locally
- future draft and roster analysis workflows

## Target Architecture

The primary question-answering flow should be data-extractor first:

1. A user asks a natural-language Bills or NFL question.
2. A data extractor LLM decides whether the local analytics database can help.
3. If data is useful, the extractor produces one SQL query against approved
   analytics views.
4. Application code validates the SQL before execution.
5. Application code executes valid read-only SQL with row limits.
6. The answer LLM receives the original question, extractor decision, SQL,
   validation status, and returned rows.
7. The answer LLM explains what the data supports, or says what context is
   missing when the data is insufficient.

If the question does not need local structured data, the answer LLM may answer
directly. If the question needs unavailable current, injury, roster, reporting,
or transaction context, the answer should say what extra context is missing
instead of guessing.

## Phase 1: Data Foundation

Goal:
Build a repeatable ingestion pipeline for Bills game data.

Deliverables:

- pull schedule and Bills play-by-play data
- normalize game, drive, play, and score-context fields
- save cleaned outputs in Parquet
- document the dataset schema

Analysis-ready dataset grains:

- `bills_plays_<season>.parquet`: atomic play-level source of truth
- `bills_drives_<season>.parquet`: possession-level outcomes and context
- `bills_quarter_summaries_<season>.parquet`: quarter-level scoring,
  efficiency, and momentum summaries
- `bills_game_summaries_<season>.parquet`: game-level metrics for post-game
  analysis
- `bills_season_summaries.parquet`: season-level trends and comparisons

Key outcome:
A stable analysis-ready dataset that can be reused by deterministic analytics
logic and LLM-generated SQL.

## Phase 2: Guarded SQL Analytics Foundation

Goal:
Create the approved query surface that the data extractor LLM can target.

Likely components:

- DuckDB query layer over cleaned Parquet files
- approved analytics views instead of direct raw-file access
- schema and football-semantics guide for SQL generation
- generated SQL validation before execution
- read-only query execution with row limits and timeouts
- returned SQL, query results, and validation metadata

Example questions:

- Are the Bills better in the first or second half?
- How do rushing yards compare by quarter?
- How many sacks did Buffalo allow by opponent?
- How does defensive EPA differ between wins and losses?

Key outcome:
The system has a constrained, inspectable way to retrieve local data for broad
analytics questions.

## Phase 3: Data Extractor LLM Workflow

Goal:
Use an LLM to extract the best available local data for a user question before
answer generation.

Responsibilities:

- decide whether approved local data can help answer the question
- generate one SQL query when data is useful
- return a structured extraction decision, not a final answer
- validate all generated SQL before execution
- optionally allow one bounded correction attempt after validation or execution
  failure
- pass extractor metadata, SQL, validation status, and rows to the answer LLM

Suggested extractor output:

- `needs_data`: whether local structured data should be queried
- `sql`: SQL query, or null when no local data is needed
- `reason`: why this data was or was not requested
- `confidence`: extractor confidence
- `data_not_needed_reason`: explanation when no query is produced

Key outcome:
The application answers analytics questions through visible data retrieval
rather than planner-selected answer paths or unsupported direct responses.

## Phase 4: Answer Generation And API Workflow

Goal:
Expose the extractor-first workflow through the API and produce grounded,
readable answers.

Likely components:

- `/ask` runs the data extractor before the answer LLM
- SQL is validated and executed deterministically by application code
- answer LLM receives the question plus any SQL results
- responses expose data-request metadata, SQL, rows, and validation status
- direct answers remain available when local data is unnecessary
- insufficient-data answers clearly describe what is missing

Key outcome:
Users can ask flexible Bills analytics questions and receive inspectable,
data-grounded answers.

## Phase 5: Website Workflow

Goal:
Expose the system through a usable website where users can ask Bills questions.

Likely features:

- question input workflow
- answer view
- grounding indicator such as `SQL analytics`, `No local data used`, or
  `Data unavailable`
- developer visibility into generated SQL, validation status, and result rows
- supporting context panel as additional layers become available

Key outcome:
A usable vertical slice of the Bills analyst experience with visible evidence
for data-backed answers.

## Phase 6: Deterministic Metrics And Evidence Enhancements

Goal:
Keep deterministic metrics as useful reusable evidence while the primary answer
path remains extractor-first.

Likely components:

- game-level metric packets for selected matchups
- deterministic ranking of likely game factors
- key drive and key play evidence
- companion views or summaries that make common analyses easier for SQL
  extraction

Key outcome:
Frequently needed football evidence can be computed consistently and exposed to
the extractor workflow without replacing the SQL validation boundary.

## Phase 7: Analytics Data Expansion

Goal:
Expand the analytics-ready data sources after the first flexible query flow is
validated end to end.

Likely components:

- weekly player stats
- snap counts
- Next Gen Stats offensive enrichment
- participation and charting data where available
- approved-view updates as each dataset becomes available

Key outcome:
The extractor can answer richer player, usage, and situational questions
without widening the cleaned play table indefinitely.

## Phase 8: AWS Deployment / Operations

Goal:
Deploy the locally validated analytics workflow and establish basic operational
hosting.

Likely concerns:

- application hosting
- environment and secret configuration
- storage and access strategy for processed analytics data
- basic logging and monitoring

Key outcome:
The locally validated application can run in a managed environment without
coupling deployment work to future analytics expansion.

## Phase 9: Draft And Roster Extension

Goal:
Extend the architecture to support Bills draft and roster questions.

Example questions:

- What are the Bills' biggest draft needs?
- Which prospects best fit Buffalo at pick X?
- Should Buffalo prioritize WR or CB?

Likely components:

- draft and roster data extraction workflow
- Bills roster-needs logic
- prospect data ingestion
- draft-specific retrieval

Key outcome:
The project expands from post-game analysis into broader Bills decision-support
workflows while preserving the same principle: retrieve inspectable evidence
first, then synthesize.

## Analytics Data Policy

- Runtime analytics query cleaned tables only.
- Raw nflverse files remain recoverable ingestion sources, not user-facing
  query targets.
- LLMs may propose SQL, but application code must validate and execute it.
- Promote useful raw fields deliberately into cleaned tables or normalized
  companion datasets.
- Keep separate tables for separate grains, such as play-level analytics,
  player-game production, player-game snap counts, and optional advanced
  enrichment.
- Responses should expose the data used, validation status, and limits whenever
  local data contributes to an answer.

## Deferred: Retrieval And Web Search Context

Goal:
Add outside context only after the local data extraction workflow and AWS
deployment are established.

Possible future uses:

- official game recaps
- press-conference transcripts or summaries
- injury updates
- coach and player quotes
- current Bills reporting

Key outcome:
The system can eventually supplement structured analytics with cited external
context without making retrieval a prerequisite for the core analytics product.
