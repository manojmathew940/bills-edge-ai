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

## Phase 5: RAG Context

Goal:
Retrieve curated Bills-related context when structured metrics alone cannot
answer the question.

Likely uses:

- selected game recaps
- press-conference transcripts or summaries
- injury and reporting documents
- other controlled Bills source material

Key outcome:
The system can combine Bills analytics with retrieved supporting context and
citations through a stable context-source workflow.

## Phase 6: Web Search Context

Goal:
Extend the retrieval and citation workflow with fresh public reporting when it
improves answers.

Likely uses:

- current injury updates
- recent Bills news
- post-game articles
- coach and player quotes

Key outcome:
The system can supplement structured analytics and curated RAG with current
public information when needed.

## Phase 7: AWS Deployment / Operations

Goal:
Deploy the usable application workflow and establish basic operational hosting.

Likely concerns:

- application hosting
- environment and secret configuration
- storage/access strategy for processed data
- basic logging and monitoring

Key outcome:
The locally validated application can run in a managed environment without
coupling deployment work to future analytics expansion.

## Phase 8: Analytics Enhancements

Goal:
Deepen the analytics layer behind stable engine boundaries after the initial
product, context, retrieval, and deployment flows are established.

Likely components:

- ranked explanations for game outcomes
- key drive and key play evidence packets
- team and season trend engines
- player metrics engines
- planner routes for newly available engines

Key outcome:
Higher-quality, inspectable analysis can be added modularly without redesigning
the website, web search, RAG, or deployment layers.

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
