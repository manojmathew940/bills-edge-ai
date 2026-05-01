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

## Phase 2: Analytics Engine

Goal:
Create deterministic logic for answering post-game questions from structured data.

Example questions:

- Why did the Bills lose game X?
- Why did they take 8 sacks?
- What would have helped them win?

Planned metrics:

- sacks and pressure-related metrics
- turnover margin
- third-down conversion rate
- red-zone efficiency
- explosive plays allowed
- scoring by quarter
- drive-level outcomes

Key outcome:
A backend analysis layer that can produce ranked, evidence-based reasons for game outcomes.

## Phase 3: LLM Layer

Goal:
Allow users to ask natural-language questions and receive readable, grounded answers.

Responsibilities:

- parse user intent
- identify the relevant game or topic
- convert analytics output into clear explanations
- distinguish direct evidence from inference

Key outcome:
A question-answering workflow that feels natural while remaining grounded in structured data.

## Phase 4: Web Search

Goal:
Add live public context when it improves answers.

Likely uses:

- post-game articles
- press conferences
- injury updates
- coach and player quotes

Key outcome:
The system can combine Bills analytics with fresh public reporting when needed.

## Phase 5: RAG Comparison

Goal:
Compare curated retrieval against web search for Bills-specific questions.

Focus areas:

- consistency
- source control
- citation quality
- repeatability
- answer usefulness

Key outcome:
A clear understanding of when RAG adds value beyond web search.

## Phase 6: Website

Goal:
Expose the system through a simple website where users can ask Bills questions.

Likely features:

- game selector
- question input
- answer view
- supporting evidence panel

Key outcome:
A usable Bills analysis experience rather than just a backend prototype.

## Phase 7: Draft Extension

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
