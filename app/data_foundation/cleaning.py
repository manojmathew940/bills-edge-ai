from __future__ import annotations

import argparse
from pathlib import Path


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
BILLS_TEAM = "BUF"

SOURCE_COLUMNS = [
    "season",
    "season_type",
    "week",
    "game_id",
    "game_date",
    "home_team",
    "away_team",
    "location",
    "result",
    "home_score",
    "away_score",
    "div_game",
    "roof",
    "surface",
    "temp",
    "wind",
    "play_id",
    "drive",
    "fixed_drive",
    "fixed_drive_result",
    "qtr",
    "time",
    "quarter_seconds_remaining",
    "half_seconds_remaining",
    "game_seconds_remaining",
    "down",
    "ydstogo",
    "yardline_100",
    "yrdln",
    "goal_to_go",
    "desc",
    "play_type",
    "play_type_nfl",
    "posteam",
    "posteam_type",
    "defteam",
    "side_of_field",
    "posteam_score",
    "defteam_score",
    "score_differential",
    "posteam_score_post",
    "defteam_score_post",
    "score_differential_post",
    "total_home_score",
    "total_away_score",
    "yards_gained",
    "first_down",
    "touchdown",
    "td_team",
    "interception",
    "fumble",
    "fumble_lost",
    "sack",
    "qb_hit",
    "penalty",
    "penalty_team",
    "penalty_type",
    "penalty_yards",
    "safety",
    "tackled_for_loss",
    "third_down_converted",
    "third_down_failed",
    "fourth_down_converted",
    "fourth_down_failed",
    "rush_attempt",
    "pass_attempt",
    "complete_pass",
    "incomplete_pass",
    "qb_dropback",
    "shotgun",
    "no_huddle",
    "qb_scramble",
    "qb_kneel",
    "qb_spike",
    "pass_length",
    "pass_location",
    "air_yards",
    "yards_after_catch",
    "run_location",
    "run_gap",
    "passing_yards",
    "receiving_yards",
    "rushing_yards",
    "passer_player_id",
    "passer_player_name",
    "receiver_player_id",
    "receiver_player_name",
    "rusher_player_id",
    "rusher_player_name",
    "special_teams_play",
    "special",
    "kickoff_attempt",
    "punt_attempt",
    "field_goal_attempt",
    "extra_point_attempt",
    "two_point_attempt",
    "field_goal_result",
    "extra_point_result",
    "two_point_conv_result",
    "kick_distance",
    "return_team",
    "return_yards",
    "drive_play_count",
    "drive_time_of_possession",
    "drive_first_downs",
    "drive_inside20",
    "drive_ended_with_score",
    "drive_quarter_start",
    "drive_quarter_end",
    "drive_yards_penalized",
    "drive_start_transition",
    "drive_end_transition",
    "drive_game_clock_start",
    "drive_game_clock_end",
    "drive_start_yard_line",
    "drive_end_yard_line",
    "drive_play_id_started",
    "drive_play_id_ended",
    "epa",
    "wp",
    "wpa",
    "home_wp",
    "away_wp",
    "success",
    "ep",
    "cp",
    "cpoe",
    "xpass",
    "pass_oe",
    "qb_epa",
]


def raw_path_for_season(season: int, raw_dir: Path = RAW_DATA_DIR) -> Path:
    return raw_dir / f"bills_play_by_play_{season}_raw.csv.gz"


def processed_path_for_season(
    season: int, processed_dir: Path = PROCESSED_DATA_DIR
) -> Path:
    return processed_dir / f"bills_plays_{season}.parquet"


def load_raw_bills_play_by_play(season: int) -> pd.DataFrame:
    try:
        import pandas as pd
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Missing dependency: pandas. Install project dependencies with "
            "`python3 -m pip install -r requirements.txt`."
        ) from error

    raw_path = raw_path_for_season(season)
    if not raw_path.exists():
        raise FileNotFoundError(f"Missing raw data file: {raw_path}")

    return pd.read_csv(raw_path, low_memory=False)


def select_source_columns(play_by_play: pd.DataFrame) -> pd.DataFrame:
    available_columns = [
        column for column in SOURCE_COLUMNS if column in play_by_play.columns
    ]
    return play_by_play.loc[:, available_columns].copy()


def add_bills_perspective_fields(play_by_play: pd.DataFrame) -> pd.DataFrame:
    play_by_play = play_by_play.sort_values(["game_id", "play_id"]).copy()

    play_by_play["opponent"] = play_by_play.apply(
        lambda row: row["away_team"] if row["home_team"] == BILLS_TEAM else row["home_team"],
        axis=1,
    )
    play_by_play["is_home"] = play_by_play["home_team"] == BILLS_TEAM
    play_by_play["bills_on_offense"] = play_by_play["posteam"] == BILLS_TEAM
    play_by_play["bills_on_defense"] = play_by_play["defteam"] == BILLS_TEAM

    bills_home = play_by_play["home_team"] == BILLS_TEAM
    home_score_after = play_by_play["total_home_score"]
    away_score_after = play_by_play["total_away_score"]
    home_score_before = home_score_after.groupby(play_by_play["game_id"]).shift(
        fill_value=0
    )
    away_score_before = away_score_after.groupby(play_by_play["game_id"]).shift(
        fill_value=0
    )

    play_by_play["bills_score_before"] = home_score_before.where(
        bills_home, away_score_before
    )
    play_by_play["opponent_score_before"] = away_score_before.where(
        bills_home, home_score_before
    )
    play_by_play["bills_score_after"] = home_score_after.where(
        bills_home, away_score_after
    )
    play_by_play["opponent_score_after"] = away_score_after.where(
        bills_home, home_score_after
    )
    play_by_play["bills_score_diff_before"] = (
        play_by_play["bills_score_before"] - play_by_play["opponent_score_before"]
    )
    play_by_play["bills_score_diff_after"] = (
        play_by_play["bills_score_after"] - play_by_play["opponent_score_after"]
    )

    play_by_play["turnover"] = (
        play_by_play[["interception", "fumble_lost"]].fillna(0).astype(int).sum(axis=1)
        > 0
    )
    play_by_play["third_down_attempt"] = play_by_play["down"] == 3
    play_by_play["red_zone_play"] = play_by_play["yardline_100"] <= 20
    play_by_play["explosive_play"] = (
        ((play_by_play["pass_attempt"] == 1) & (play_by_play["yards_gained"] >= 20))
        | ((play_by_play["rush_attempt"] == 1) & (play_by_play["yards_gained"] >= 10))
    )

    return play_by_play


def clean_bills_play_by_play(season: int) -> pd.DataFrame:
    raw_play_by_play = load_raw_bills_play_by_play(season)
    processed_play_by_play = select_source_columns(raw_play_by_play)
    return add_bills_perspective_fields(processed_play_by_play)


def save_processed_bills_play_by_play(season: int) -> tuple[Path, int, int]:
    processed_play_by_play = clean_bills_play_by_play(season)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = processed_path_for_season(season)
    processed_play_by_play.to_parquet(output_path, index=False)

    row_count, column_count = processed_play_by_play.shape

    return output_path, row_count, column_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create processed Bills play-level data for one NFL season."
    )
    parser.add_argument("season", type=int, help="NFL season to process, such as 2024")
    args = parser.parse_args()

    try:
        output_path, row_count, column_count = save_processed_bills_play_by_play(
            args.season
        )
    except (FileNotFoundError, RuntimeError) as error:
        parser.error(str(error))

    print(f"Saved {row_count} rows and {column_count} columns to {output_path}")


if __name__ == "__main__":
    main()
