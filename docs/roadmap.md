# Bills AI Analyst Roadmap

## Purpose

This document captures the planned build order for the Bills AI Analyst project.

The project is intended to evolve into a Bills-focused web application that combines:

- structured game analytics
- LLM-based question understanding and explanation
- web search and/or retrieval for supporting context
- future draft analysis workflows

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
- `bills_quarter_summaries_<season>.parquet`: quarter-level scoring, efficiency, and momentum summaries
- `bills_game_summaries_<season>.parquet`: game-level metrics for post-game analysis
- `bills_season_summaries.parquet`: season-level trends and comparisons

Key outcome:
A stable analysis-ready dataset that can be reused by later analytics logic.

## Phase 2: Basic Game Metrics Engine

Goal:
Provide deterministic metrics for one selected Bills game from structured data.

Example questions:

- Why did the Bills lose game X?
- Why did they take 8 sacks?
- What would have helped them win?

Initial metrics:

- sacks and pressure-related metrics
- turnover margin
- third-down conversion rate
- red-zone efficiency
- explosive plays allowed
- scoring by quarter
- drive-level outcomes

Key outcome:
A reusable game metrics packet that can be passed to an LLM or exposed through
the API without requiring advanced interpretation logic.

Deferred enhancements:

- deterministic ranking of likely game factors
- key drive and key play evidence
- team, season, and player analytics engines

## Phase 3: Initial LLM Workflow

Goal:
Allow users to ask natural-language questions and receive readable, grounded answers.

Responsibilities:

- use a planner LLM to select the available answer path
- identify the relevant game for game-specific questions
- answer game questions from the basic metrics packet
- permit direct LLM answers for questions not served by a metrics engine
- distinguish direct evidence from inference

Key outcome:
A working end-to-end question flow, with game-specific answers grounded in
structured metrics and unsupported analytic capabilities deferred.

## Phase 4: Website Workflow

Goal:
Expose the system through a usable website where users can ask Bills questions.

Likely features:

- game/question input workflow
- answer view
- metrics and routing visibility for internal testing
- supporting context panel as additional layers become available

Key outcome:
A usable vertical slice of the Bills analyst experience before adding further
context sources or analytic engines.

## Phase 5: Guarded LLM-To-SQL Analytics Engine

Goal:
Build a flexible analytics engine where an LLM generates SQL against approved
cleaned Bills analytics views.

Example questions:

- Are the Bills better in the first or second half?
- How do rushing yards compare by quarter?
- How many sacks did Buffalo allow by opponent?
- How does defensive EPA differ between wins and losses?

Likely components:

- DuckDB query layer over cleaned Parquet files
- approved analytics views instead of direct raw-file access
- schema and football-semantics guide for SQL generation
- generated SQL validation before execution
- read-only query execution with row limits and timeouts
- returned SQL, query results, and validation metadata

Key outcome:
The system can answer broader analytics questions with flexible SQL while
keeping runtime queries constrained to reviewed, cleaned analytics data.

## Phase 6: LLM-To-SQL Analytics Workflow

Goal:
Expose the guarded LLM-to-SQL engine through the planner, answer LLM, API, and
website.

Likely components:

- planner route for broad analytics questions
- SQL-generation LLM that targets the approved DuckDB analytics views
- one bounded correction attempt after validation or execution failure
- answer LLM explanations grounded in SQL results
- API and website visibility into generated SQL, query results, and validation
  status

Key outcome:
Users can ask flexible Bills analytics questions and receive inspectable,
data-grounded answers rather than unsupported direct LLM responses.

## Phase 7: Analytics Data Expansion

Goal:
Expand the analytics-ready data sources after the first flexible query flow is
validated end to end.

Likely components:

- weekly player stats
- snap counts
- Next Gen Stats offensive enrichment
- participation and charting data where available
- query-engine registry updates as each dataset becomes available

Key outcome:
The analytics engine can answer richer player, usage, and situational questions
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

- draft analytics planner
- Bills roster-needs logic
- prospect data ingestion
- draft-specific retrieval

Key outcome:
The project expands from post-game analysis into broader Bills decision-support workflows.

## Analytics Data Policy

- Runtime analytics query cleaned tables only.
- Raw nflverse files remain recoverable ingestion sources, not user-facing
  query targets.
- Promote useful raw fields deliberately into cleaned tables or normalized
  companion datasets.
- Keep separate tables for separate grains, such as play-level analytics,
  player-game production, player-game snap counts, and optional advanced
  enrichment.

## Deferred: Retrieval And Web Search Context

Goal:
Add outside context only after the deterministic analytics workflow and AWS
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
