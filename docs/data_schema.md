# Bills Analysis Dataset Schema

## Purpose

This document defines the first analysis-ready dataset for the Bills AI Analyst project.

The initial target is a cleaned Bills game dataset with one row per play.

This dataset is intended to support post-game analysis questions such as:

- Why did the Bills lose?
- Why did they take 8 sacks?
- What were the biggest turning points?

## Row Grain

One row represents one play from a Buffalo Bills game.

## Core Fields

### Game Context

- `season`: NFL season as an integer
- `week`: regular season or playoff week identifier
- `game_id`: unique game identifier
- `game_date`: date of the game
- `team`: always `BUF` for Bills-perspective records
- `opponent`: opposing team abbreviation
- `is_home`: boolean flag indicating whether Buffalo was the home team
- `result`: game result from the Bills perspective, such as `win` or `loss`

### Drive and Play Context

- `drive_id`: unique drive identifier within a game
- `play_id`: unique play identifier within a game
- `quarter`: quarter number
- `clock`: game clock at the start of the play
- `down`: current down
- `yards_to_go`: yards needed for a first down
- `yardline`: normalized field position representation

### Team Context

- `offense_team`: team in possession
- `defense_team`: team on defense
- `bills_on_offense`: boolean flag for whether Buffalo is on offense
- `bills_on_defense`: boolean flag for whether Buffalo is on defense

### Play Details

- `play_type`: normalized play type
- `yards_gained`: yards gained on the play
- `first_down`: boolean flag for first down gained
- `touchdown`: boolean flag for touchdown scored
- `turnover`: boolean flag for turnover on the play
- `sack`: boolean flag for sack on the play
- `penalty`: boolean flag for penalty on the play

### Score Context

- `score_team_before`: Bills score before the play
- `score_opponent_before`: opponent score before the play
- `score_team_after`: Bills score after the play
- `score_opponent_after`: opponent score after the play
- `score_diff_before`: Bills score differential before the play
- `score_diff_after`: Bills score differential after the play

## Optional Derived Fields

These are not required for the first version, but are useful for later analytics.

- `third_down_attempt`
- `third_down_converted`
- `red_zone_play`
- `explosive_play`
- `drive_result`
- `pressure_allowed`
- `blitz_faced`
- `win_probability`
- `epa`
- `success`

## Storage

Recommended first output:

- `data/processed/bills_plays_<season>.parquet`

Optional companion files:

- raw source snapshot in `data/raw/`
- metadata JSON describing pull time, source, and schema version

## Design Notes

- The dataset should use Bills-perspective fields where possible to simplify downstream analysis.
- Field names should stay consistent across seasons.
- Missing values should be handled explicitly rather than silently dropped.
- The schema should be versioned once the ingestion pipeline is in place.
