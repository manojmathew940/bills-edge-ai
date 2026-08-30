from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from app.data_foundation.cleaning import (
    SOURCE_COLUMNS,
    add_derived_fields,
    processed_path_for_season,
    raw_path_for_season,
    save_processed_nfl_play_by_play,
    select_source_columns,
)


class CleaningTest(unittest.TestCase):
    def test_paths_use_nfl_wide_names(self) -> None:
        self.assertEqual(
            raw_path_for_season(2024, Path("raw")),
            Path("raw/nfl_play_by_play_2024_raw.csv.gz"),
        )
        self.assertEqual(
            processed_path_for_season(2024, Path("processed")),
            Path("processed/nfl_plays_2024.parquet"),
        )

    def test_adds_neutral_derived_fields_for_multiple_teams(self) -> None:
        plays = pd.DataFrame(
            [
                {
                    "game_id": "2024_01_ARI_BUF",
                    "play_id": 2,
                    "down": 3,
                    "yardline_100": 19,
                    "interception": 0,
                    "fumble_lost": 0,
                    "pass_attempt": 1,
                    "rush_attempt": 0,
                    "yards_gained": 21,
                },
                {
                    "game_id": "2024_01_SF_NYJ",
                    "play_id": 1,
                    "down": 1,
                    "yardline_100": 60,
                    "interception": 1,
                    "fumble_lost": 0,
                    "pass_attempt": 1,
                    "rush_attempt": 0,
                    "yards_gained": 0,
                },
            ]
        )

        result = add_derived_fields(plays)

        self.assertEqual(result["game_id"].tolist(), [
            "2024_01_ARI_BUF",
            "2024_01_SF_NYJ",
        ])
        self.assertEqual(result["third_down_attempt"].tolist(), [True, False])
        self.assertEqual(result["red_zone_play"].tolist(), [True, False])
        self.assertEqual(result["explosive_play"].tolist(), [True, False])
        self.assertEqual(result["turnover"].tolist(), [False, True])
        self.assertNotIn("bills_on_offense", result.columns)
        self.assertNotIn("opponent", result.columns)

    def test_select_source_columns_rejects_incomplete_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required processed columns"):
            select_source_columns(pd.DataFrame({"season": [2024]}))

    def test_saves_complete_source_as_processed_parquet(self) -> None:
        row = {column: None for column in SOURCE_COLUMNS}
        row.update(
            {
                "season": 2024,
                "week": 1,
                "game_id": "2024_01_ARI_BUF",
                "play_id": 1,
                "home_team": "BUF",
                "away_team": "ARI",
                "posteam": "ARI",
                "defteam": "BUF",
                "down": 3,
                "yardline_100": 15,
                "interception": 0,
                "fumble_lost": 0,
                "pass_attempt": 1,
                "rush_attempt": 0,
                "yards_gained": 20,
            }
        )

        with TemporaryDirectory() as directory:
            root = Path(directory)
            raw_dir = root / "raw"
            processed_dir = root / "processed"
            raw_dir.mkdir()
            pd.DataFrame([row]).to_csv(
                raw_path_for_season(2024, raw_dir), index=False, compression="gzip"
            )

            output_path, row_count, column_count = save_processed_nfl_play_by_play(
                2024, raw_dir, processed_dir
            )
            processed = pd.read_parquet(output_path)

            self.assertEqual(row_count, 1)
            self.assertEqual(column_count, len(SOURCE_COLUMNS) + 4)
            self.assertEqual(processed["posteam"].tolist(), ["ARI"])
            self.assertEqual(processed["turnover"].tolist(), [False])
            self.assertEqual(processed["third_down_attempt"].tolist(), [True])
            self.assertEqual(processed["red_zone_play"].tolist(), [True])
            self.assertEqual(processed["explosive_play"].tolist(), [True])

    def test_saves_processed_file_without_replacing_on_failure(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            raw_dir = root / "raw"
            processed_dir = root / "processed"
            raw_dir.mkdir()
            processed_dir.mkdir()
            output_path = processed_path_for_season(2024, processed_dir)
            output_path.write_bytes(b"existing-data")
            incomplete = pd.DataFrame({"season": [2024]})
            incomplete.to_csv(
                raw_path_for_season(2024, raw_dir), index=False, compression="gzip"
            )

            with self.assertRaisesRegex(ValueError, "missing required processed columns"):
                save_processed_nfl_play_by_play(2024, raw_dir, processed_dir)

            self.assertEqual(output_path.read_bytes(), b"existing-data")


if __name__ == "__main__":
    unittest.main()
