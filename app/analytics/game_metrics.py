from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


BILLS_TEAM = "BUF"
PROCESSED_DATA_DIR = Path("data/processed")


def load_processed_plays(season: int) -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / f"bills_plays_{season}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing processed play data: {path}")

    return pd.read_parquet(path)


def get_game_by_week(season: int, week: int) -> pd.DataFrame:
    plays = load_processed_plays(season)
    game = plays.loc[plays["week"] == week].copy()
    if game.empty:
        raise ValueError(f"No Bills game found for season={season}, week={week}.")

    return game.sort_values("play_id")


def calculate_game_metrics(game: pd.DataFrame) -> dict[str, Any]:
    game = game.sort_values("play_id").copy()

    return {
        "game": game_context(game),
        "scoring": scoring_metrics(game),
        "turnovers": turnover_metrics(game),
        "offense": offense_metrics(game),
        "defense": defense_metrics(game),
        "downs": down_metrics(game),
        "red_zone": red_zone_metrics(game),
        "explosives": explosive_metrics(game),
        "pressure": pressure_metrics(game),
        "drives": drive_metrics(game),
        "penalties": penalty_metrics(game),
        "special_teams": special_teams_metrics(game),
    }


def game_context(game: pd.DataFrame) -> dict[str, Any]:
    first = game.iloc[0]
    bills_score = int(first["home_score"] if first["is_home"] else first["away_score"])
    opponent_score = int(first["away_score"] if first["is_home"] else first["home_score"])

    return {
        "season": int(first["season"]),
        "season_type": value_or_none(first.get("season_type")),
        "week": int(first["week"]),
        "game_id": first["game_id"],
        "game_date": str(first["game_date"]),
        "opponent": first["opponent"],
        "is_home": bool(first["is_home"]),
        "result": "win" if bills_score > opponent_score else "loss",
        "bills_score": bills_score,
        "opponent_score": opponent_score,
        "score_margin": bills_score - opponent_score,
    }


def scoring_metrics(game: pd.DataFrame) -> dict[str, Any]:
    quarter_points = {}
    for quarter in sorted(game["qtr"].dropna().unique()):
        quarter_game = game.loc[game["qtr"] == quarter]
        first = quarter_game.iloc[0]
        last = quarter_game.iloc[-1]
        quarter_points[str(int(quarter))] = {
            "bills": int(last["bills_score_after"] - first["bills_score_before"]),
            "opponent": int(
                last["opponent_score_after"] - first["opponent_score_before"]
            ),
        }

    halftime = game.loc[game["qtr"] <= 2]
    second_half = game.loc[game["qtr"] >= 3]
    first = game.iloc[0]
    last = game.iloc[-1]

    return {
        "points_by_quarter": quarter_points,
        "halftime_score": score_at_end(halftime),
        "second_half_points": points_scored(second_half),
        "largest_bills_lead": int(game["bills_score_diff_after"].max()),
        "largest_bills_deficit": int(game["bills_score_diff_after"].min()),
        "final_score": {
            "bills": int(last["bills_score_after"]),
            "opponent": int(last["opponent_score_after"]),
        },
        "score_margin": int(last["bills_score_after"] - last["opponent_score_after"]),
        "scoreless_start": bool(
            first["bills_score_before"] == 0 and first["opponent_score_before"] == 0
        ),
    }


def turnover_metrics(game: pd.DataFrame) -> dict[str, Any]:
    bills_turnover_plays = game.loc[game["bills_on_offense"] & game["turnover"]]
    opponent_turnover_plays = game.loc[game["bills_on_defense"] & game["turnover"]]

    return {
        "bills_turnovers": int(len(bills_turnover_plays)),
        "opponent_turnovers": int(len(opponent_turnover_plays)),
        "turnover_margin": int(len(opponent_turnover_plays) - len(bills_turnover_plays)),
        "interceptions_thrown": int(
            game.loc[game["bills_on_offense"], "interception"].fillna(0).sum()
        ),
        "fumbles_lost": int(
            game.loc[game["bills_on_offense"], "fumble_lost"].fillna(0).sum()
        ),
        "takeaways": int(len(opponent_turnover_plays)),
    }


def offense_metrics(game: pd.DataFrame) -> dict[str, Any]:
    offense = scrimmage_plays(game.loc[game["bills_on_offense"]])
    return efficiency_metrics(offense, prefix="bills")


def defense_metrics(game: pd.DataFrame) -> dict[str, Any]:
    opponent = scrimmage_plays(game.loc[game["bills_on_defense"]])
    metrics = efficiency_metrics(opponent, prefix="opponent")
    return metrics


def down_metrics(game: pd.DataFrame) -> dict[str, Any]:
    bills = game.loc[game["bills_on_offense"]]
    opponent = game.loc[game["bills_on_defense"]]

    return {
        "bills_third_down": conversion_metrics(
            bills["third_down_attempt"], bills["third_down_converted"]
        ),
        "opponent_third_down": conversion_metrics(
            opponent["third_down_attempt"], opponent["third_down_converted"]
        ),
        "bills_fourth_down": conversion_metrics(
            fourth_down_attempts(bills), bills["fourth_down_converted"]
        ),
        "opponent_fourth_down": conversion_metrics(
            fourth_down_attempts(opponent), opponent["fourth_down_converted"]
        ),
    }


def red_zone_metrics(game: pd.DataFrame) -> dict[str, Any]:
    return {
        "bills": red_zone_side_metrics(game.loc[game["bills_on_offense"]]),
        "opponent": red_zone_side_metrics(game.loc[game["bills_on_defense"]]),
    }


def explosive_metrics(game: pd.DataFrame) -> dict[str, Any]:
    bills = game.loc[game["bills_on_offense"] & game["explosive_play"]]
    opponent = game.loc[game["bills_on_defense"] & game["explosive_play"]]

    return {
        "bills_explosive_plays": int(len(bills)),
        "opponent_explosive_plays": int(len(opponent)),
        "explosive_play_margin": int(len(bills) - len(opponent)),
        "bills_explosive_passes": int((bills["pass_attempt"] == 1).sum()),
        "bills_explosive_runs": int((bills["rush_attempt"] == 1).sum()),
        "opponent_explosive_passes": int((opponent["pass_attempt"] == 1).sum()),
        "opponent_explosive_runs": int((opponent["rush_attempt"] == 1).sum()),
    }


def pressure_metrics(game: pd.DataFrame) -> dict[str, Any]:
    bills_offense = game.loc[game["bills_on_offense"]]
    bills_defense = game.loc[game["bills_on_defense"]]

    return {
        "sacks_taken": int(bills_offense["sack"].fillna(0).sum()),
        "sacks_made": int(bills_defense["sack"].fillna(0).sum()),
        "qb_hits_taken": int(bills_offense["qb_hit"].fillna(0).sum()),
        "qb_hits_made": int(bills_defense["qb_hit"].fillna(0).sum()),
        "tackles_for_loss_allowed": int(
            bills_offense["tackled_for_loss"].fillna(0).sum()
        ),
        "tackles_for_loss_made": int(
            bills_defense["tackled_for_loss"].fillna(0).sum()
        ),
        "negative_plays_on_offense": int((bills_offense["yards_gained"] < 0).sum()),
        "negative_plays_forced_on_defense": int(
            (bills_defense["yards_gained"] < 0).sum()
        ),
    }


def drive_metrics(game: pd.DataFrame) -> dict[str, Any]:
    drive_rows = (
        game.dropna(subset=["fixed_drive"])
        .sort_values("play_id")
        .groupby("fixed_drive", as_index=False)
        .tail(1)
    )
    bills_drives = drive_rows.loc[drive_rows["posteam"] == BILLS_TEAM]
    opponent_drives = drive_rows.loc[drive_rows["posteam"] != BILLS_TEAM]

    return {
        "bills": drive_side_metrics(bills_drives),
        "opponent": drive_side_metrics(opponent_drives),
    }


def penalty_metrics(game: pd.DataFrame) -> dict[str, Any]:
    bills_penalties = game.loc[game["penalty_team"] == BILLS_TEAM]
    opponent_penalties = game.loc[
        game["penalty_team"].notna() & (game["penalty_team"] != BILLS_TEAM)
    ]

    return {
        "bills_penalties": int(len(bills_penalties)),
        "bills_penalty_yards": int(bills_penalties["penalty_yards"].fillna(0).sum()),
        "opponent_penalties": int(len(opponent_penalties)),
        "opponent_penalty_yards": int(
            opponent_penalties["penalty_yards"].fillna(0).sum()
        ),
    }


def special_teams_metrics(game: pd.DataFrame) -> dict[str, Any]:
    bills = game.loc[game["posteam"] == BILLS_TEAM]
    opponent = game.loc[game["posteam"].notna() & (game["posteam"] != BILLS_TEAM)]

    return {
        "bills_field_goals": field_goal_metrics(bills),
        "opponent_field_goals": field_goal_metrics(opponent),
    }


def scrimmage_plays(plays: pd.DataFrame) -> pd.DataFrame:
    return plays.loc[(plays["rush_attempt"] == 1) | (plays["pass_attempt"] == 1)]


def efficiency_metrics(plays: pd.DataFrame, *, prefix: str) -> dict[str, Any]:
    play_count = len(plays)
    total_yards = numeric_sum(plays, "yards_gained")
    epa_total = numeric_sum(plays, "epa")

    return {
        f"{prefix}_plays": int(play_count),
        f"{prefix}_total_yards": int(total_yards),
        f"{prefix}_yards_per_play": safe_divide(total_yards, play_count),
        f"{prefix}_success_rate": safe_divide(numeric_sum(plays, "success"), play_count),
        f"{prefix}_epa_total": round(float(epa_total), 3),
        f"{prefix}_epa_per_play": safe_divide(epa_total, play_count),
        f"{prefix}_pass_epa": round(
            float(numeric_sum(plays.loc[plays["pass_attempt"] == 1], "epa")), 3
        ),
        f"{prefix}_rush_epa": round(
            float(numeric_sum(plays.loc[plays["rush_attempt"] == 1], "epa")), 3
        ),
    }


def conversion_metrics(attempt_mask: pd.Series, converted: pd.Series) -> dict[str, Any]:
    attempts = int(attempt_mask.fillna(False).sum())
    conversions = int(converted.loc[attempt_mask.fillna(False)].fillna(0).sum())
    return {
        "attempts": attempts,
        "conversions": conversions,
        "rate": safe_divide(conversions, attempts),
    }


def fourth_down_attempts(plays: pd.DataFrame) -> pd.Series:
    return (plays["fourth_down_converted"].fillna(0) == 1) | (
        plays["fourth_down_failed"].fillna(0) == 1
    )


def red_zone_side_metrics(plays: pd.DataFrame) -> dict[str, Any]:
    red_zone_drives = plays.loc[plays["red_zone_play"]].dropna(subset=["fixed_drive"])
    drive_ids = red_zone_drives["fixed_drive"].unique()
    red_zone_plays = plays.loc[plays["fixed_drive"].isin(drive_ids)]
    touchdowns = red_zone_plays.groupby("fixed_drive")["touchdown"].sum()
    touchdown_drives = int((touchdowns > 0).sum())
    trips = int(len(drive_ids))

    return {
        "trips": trips,
        "touchdowns": touchdown_drives,
        "td_rate": safe_divide(touchdown_drives, trips),
    }


def drive_side_metrics(drives: pd.DataFrame) -> dict[str, Any]:
    results = drives["fixed_drive_result"].fillna("Unknown")
    return {
        "drives": int(len(drives)),
        "td_drives": int((results == "Touchdown").sum()),
        "fg_drives": int((results == "Field goal").sum()),
        "punt_drives": int((results == "Punt").sum()),
        "turnover_drives": int((results == "Turnover").sum()),
        "turnover_on_downs_drives": int((results == "Turnover on downs").sum()),
    }


def field_goal_metrics(plays: pd.DataFrame) -> dict[str, Any]:
    attempts = plays.loc[plays["field_goal_attempt"] == 1]
    made = attempts.loc[attempts["field_goal_result"] == "made"]
    return {
        "attempts": int(len(attempts)),
        "made": int(len(made)),
        "rate": safe_divide(len(made), len(attempts)),
    }


def score_at_end(plays: pd.DataFrame) -> dict[str, int] | None:
    if plays.empty:
        return None

    last = plays.iloc[-1]
    return {
        "bills": int(last["bills_score_after"]),
        "opponent": int(last["opponent_score_after"]),
    }


def points_scored(plays: pd.DataFrame) -> dict[str, int] | None:
    if plays.empty:
        return None

    first = plays.iloc[0]
    last = plays.iloc[-1]
    return {
        "bills": int(last["bills_score_after"] - first["bills_score_before"]),
        "opponent": int(last["opponent_score_after"] - first["opponent_score_before"]),
    }


def numeric_sum(plays: pd.DataFrame, column: str) -> float:
    if plays.empty or column not in plays:
        return 0.0
    return float(plays[column].fillna(0).sum())


def safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return round(float(numerator) / float(denominator), 3)


def value_or_none(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value
