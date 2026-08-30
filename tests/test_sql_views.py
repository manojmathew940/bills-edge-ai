from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pyarrow as pa
import pyarrow.parquet as pq

from app.analytics.sql_views import (
    AnalyticsViewError,
    available_seasons,
    create_analytics_connection,
    describe_nfl_plays,
    processed_play_paths,
    season_from_path,
)


def expected_rows_by_season(paths: list[Path]) -> list[tuple[int, int]]:
    return [
        (season_from_path(path), pq.ParquetFile(path).metadata.num_rows)
        for path in paths
    ]


class SqlViewsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = TemporaryDirectory()
        self.data_dir = Path(self.temp_directory.name)
        self.paths = []
        for season in (2023, 2024):
            path = self.data_dir / f"nfl_plays_{season}.parquet"
            pq.write_table(
                pa.table(
                    {
                        "season": [season],
                        "week": [1],
                        "play_id": [1],
                        "qtr": [1],
                        "posteam": ["BUF"],
                        "defteam": ["ARI"],
                        "rushing_yards": [5.0],
                        "lateral_receiver_player_name": [None],
                        "lateral_receiving_yards": [None],
                        "lateral_rusher_player_name": [None],
                        "lateral_rushing_yards": [None],
                        "epa": [0.1],
                    }
                ),
                path,
            )
            self.paths.append(path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_nfl_plays_view_counts_rows_by_season(self) -> None:
        connection = create_analytics_connection(self.paths)

        rows = connection.execute(
            "SELECT season, COUNT(*) AS rows "
            "FROM nfl_plays "
            "GROUP BY season "
            "ORDER BY season"
        ).fetchall()

        self.assertEqual(rows, expected_rows_by_season(self.paths))

    def test_available_seasons_returns_all_cleaned_seasons(self) -> None:
        connection = create_analytics_connection(self.paths)

        self.assertEqual(
            available_seasons(connection),
            [season_from_path(path) for path in self.paths],
        )

    def test_describe_nfl_plays_includes_key_columns(self) -> None:
        connection = create_analytics_connection(self.paths)

        columns = {row["column_name"] for row in describe_nfl_plays(connection)}

        self.assertTrue(
            {
                "season",
                "week",
                "qtr",
                "posteam",
                "defteam",
                "rushing_yards",
                "lateral_receiver_player_name",
                "lateral_receiving_yards",
                "lateral_rusher_player_name",
                "lateral_rushing_yards",
                "epa",
            }.issubset(columns)
        )

    def test_no_processed_files_raises_clear_error(self) -> None:
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                AnalyticsViewError, "No cleaned NFL play files"
            ):
                processed_play_paths(Path(directory))

    def test_incompatible_schema_raises_clear_error(self) -> None:
        with TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            first = temp_dir / "nfl_plays_2098.parquet"
            second = temp_dir / "nfl_plays_2099.parquet"

            pq.write_table(pa.table({"season": [2098], "week": [1]}), first)
            pq.write_table(pa.table({"season": [2099], "posteam": ["NYJ"]}), second)

            with self.assertRaisesRegex(
                AnalyticsViewError, "schemas are not compatible"
            ):
                create_analytics_connection([first, second])


if __name__ == "__main__":
    unittest.main()
