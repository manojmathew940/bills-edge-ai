from __future__ import annotations

from pathlib import Path
import unittest

import pyarrow.parquet as pq

from app.analytics.sql_execution import validate_and_execute_analytics_sql
from app.analytics.sql_views import (
    AnalyticsViewError,
    processed_play_paths,
    season_from_path,
)


def expected_rows_by_season(paths: list[Path]) -> list[tuple[int, int]]:
    return [
        (season_from_path(path), pq.ParquetFile(path).metadata.num_rows)
        for path in paths
    ]


class SqlExecutionTest(unittest.TestCase):
    def test_validate_and_execute_analytics_sql_returns_json_safe_rows(self) -> None:
        result = validate_and_execute_analytics_sql(
            "SELECT season, COUNT(*) AS rows "
            "FROM bills_plays "
            "GROUP BY season "
            "ORDER BY season"
        )
        paths = processed_play_paths()
        expected_rows = [
            {"season": season, "rows": rows}
            for season, rows in expected_rows_by_season(paths)
        ]

        self.assertTrue(result.is_valid)
        self.assertEqual(result.validation_reason, "SQL is valid.")
        self.assertEqual(result.columns, ["season", "rows"])
        self.assertEqual(result.rows, expected_rows)

    def test_validate_and_execute_analytics_sql_applies_row_limit(self) -> None:
        result = validate_and_execute_analytics_sql(
            "SELECT play_id FROM bills_plays ORDER BY season, play_id",
            row_limit=3,
        )

        self.assertEqual(len(result.rows), 3)

    def test_validate_and_execute_analytics_sql_rejects_invalid_row_limit(self) -> None:
        with self.assertRaisesRegex(AnalyticsViewError, "row_limit"):
            validate_and_execute_analytics_sql("SELECT 1", row_limit=0)

    def test_validate_and_execute_analytics_sql_rejects_invalid_sql(self) -> None:
        result = validate_and_execute_analytics_sql("DROP TABLE bills_plays")

        self.assertFalse(result.is_valid)
        self.assertIn("SELECT", result.validation_reason)
        self.assertEqual(result.columns, [])
        self.assertEqual(result.rows, [])


if __name__ == "__main__":
    unittest.main()
