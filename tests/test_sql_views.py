from __future__ import annotations

from pathlib import Path
import unittest

import pyarrow as pa
import pyarrow.parquet as pq

from app.analytics.sql_views import (
    AnalyticsViewError,
    available_seasons,
    create_analytics_connection,
    describe_bills_plays,
    processed_play_paths,
    season_from_path,
)


def expected_rows_by_season(paths: list[Path]) -> list[tuple[int, int]]:
    return [
        (season_from_path(path), pq.ParquetFile(path).metadata.num_rows)
        for path in paths
    ]


class SqlViewsTest(unittest.TestCase):
    def test_bills_plays_view_counts_rows_by_season(self) -> None:
        paths = processed_play_paths()
        connection = create_analytics_connection(paths)

        rows = connection.execute(
            "SELECT season, COUNT(*) AS rows "
            "FROM bills_plays "
            "GROUP BY season "
            "ORDER BY season"
        ).fetchall()

        self.assertEqual(rows, expected_rows_by_season(paths))

    def test_available_seasons_returns_all_cleaned_seasons(self) -> None:
        paths = processed_play_paths()
        connection = create_analytics_connection(paths)

        self.assertEqual(
            available_seasons(connection),
            [season_from_path(path) for path in paths],
        )

    def test_describe_bills_plays_includes_key_columns(self) -> None:
        connection = create_analytics_connection()

        columns = {row["column_name"] for row in describe_bills_plays(connection)}

        self.assertTrue(
            {
                "season",
                "week",
                "qtr",
                "bills_on_offense",
                "rushing_yards",
                "lateral_receiver_player_name",
                "lateral_receiving_yards",
                "lateral_rusher_player_name",
                "lateral_rushing_yards",
                "epa",
            }.issubset(columns)
        )

    def test_no_processed_files_raises_clear_error(self) -> None:
        empty_dir = Path("/tmp/bills-empty-processed-test")
        empty_dir.mkdir(exist_ok=True)

        with self.assertRaisesRegex(AnalyticsViewError, "No cleaned Bills play files"):
            processed_play_paths(empty_dir)

    def test_incompatible_schema_raises_clear_error(self) -> None:
        temp_dir = Path("/tmp/bills-schema-test")
        temp_dir.mkdir(exist_ok=True)
        first = temp_dir / "bills_plays_2098.parquet"
        second = temp_dir / "bills_plays_2099.parquet"

        pq.write_table(pa.table({"season": [2098], "week": [1]}), first)
        pq.write_table(pa.table({"season": [2099], "opponent": ["NYJ"]}), second)

        with self.assertRaisesRegex(AnalyticsViewError, "schemas are not compatible"):
            create_analytics_connection([first, second])


if __name__ == "__main__":
    unittest.main()
