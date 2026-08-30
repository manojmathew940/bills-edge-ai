from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import NamedTemporaryFile


RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

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
    "lateral_reception",
    "lateral_rush",
    "lateral_receiver_player_id",
    "lateral_receiver_player_name",
    "lateral_receiving_yards",
    "lateral_rusher_player_id",
    "lateral_rusher_player_name",
    "lateral_rushing_yards",
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
    return raw_dir / f"nfl_play_by_play_{season}_raw.csv.gz"


def processed_path_for_season(
    season: int, processed_dir: Path = PROCESSED_DATA_DIR
) -> Path:
    return processed_dir / f"nfl_plays_{season}.parquet"


def load_raw_nfl_play_by_play(
    season: int, raw_dir: Path = RAW_DATA_DIR
) -> pd.DataFrame:
    try:
        import pandas as pd
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Missing dependency: pandas. Install project dependencies with "
            "`python3 -m pip install -r requirements.txt`."
        ) from error

    raw_path = raw_path_for_season(season, raw_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Missing raw data file: {raw_path}")

    return pd.read_csv(raw_path, low_memory=False)


def select_source_columns(play_by_play: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [
        column for column in SOURCE_COLUMNS if column not in play_by_play.columns
    ]
    if missing_columns:
        raise ValueError(
            "Raw play-by-play data is missing required processed columns: "
            + ", ".join(missing_columns)
        )

    return play_by_play.loc[:, SOURCE_COLUMNS].copy()


def add_derived_fields(play_by_play: pd.DataFrame) -> pd.DataFrame:
    play_by_play = play_by_play.sort_values(["game_id", "play_id"]).copy()

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


def clean_nfl_play_by_play(
    season: int, raw_dir: Path = RAW_DATA_DIR
) -> pd.DataFrame:
    raw_play_by_play = load_raw_nfl_play_by_play(season, raw_dir)
    processed_play_by_play = select_source_columns(raw_play_by_play)
    return add_derived_fields(processed_play_by_play)


def save_processed_nfl_play_by_play(
    season: int,
    raw_dir: Path = RAW_DATA_DIR,
    processed_dir: Path = PROCESSED_DATA_DIR,
) -> tuple[Path, int, int]:
    processed_play_by_play = clean_nfl_play_by_play(season, raw_dir)

    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_path_for_season(season, processed_dir)
    with NamedTemporaryFile(
        "wb", dir=processed_dir, prefix=f".{output_path.stem}.", delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        processed_play_by_play.to_parquet(temp_path, index=False)
        temp_path.replace(output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    row_count, column_count = processed_play_by_play.shape

    return output_path, row_count, column_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create processed NFL play-level data for one season."
    )
    parser.add_argument("season", type=int, help="NFL season to process, such as 2024")
    args = parser.parse_args()

    try:
        output_path, row_count, column_count = save_processed_nfl_play_by_play(
            args.season
        )
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        parser.error(str(error))

    print(f"Saved {row_count} rows and {column_count} columns to {output_path}")


if __name__ == "__main__":
    main()
