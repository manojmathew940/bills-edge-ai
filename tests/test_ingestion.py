from __future__ import annotations

import csv
import gzip
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app.data_foundation.ingestion import (
    PBP_URL_TEMPLATE,
    save_raw_nfl_play_by_play,
    validate_season,
)


SOURCE_COLUMNS = [
    "game_id",
    "play_id",
    "home_team",
    "away_team",
    "posteam",
    "defteam",
    "season",
    "week",
]


class StubResponse(io.BytesIO):
    def __init__(self, payload: bytes):
        super().__init__(payload)
        self.headers = {"Content-Length": str(len(payload))}


def compressed_csv(rows: list[dict[str, str]], columns=SOURCE_COLUMNS) -> bytes:
    text_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(text_buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return gzip.compress(text_buffer.getvalue().encode())


class IngestionTest(unittest.TestCase):
    def test_saves_every_team_to_nfl_wide_raw_file(self) -> None:
        rows = [
            {
                "game_id": "2024_01_ARI_BUF",
                "play_id": "1",
                "home_team": "BUF",
                "away_team": "ARI",
                "posteam": "ARI",
                "defteam": "BUF",
                "season": "2024",
                "week": "1",
            },
            {
                "game_id": "2024_01_SF_NYJ",
                "play_id": "2",
                "home_team": "SF",
                "away_team": "NYJ",
                "posteam": "SF",
                "defteam": "NYJ",
                "season": "2024",
                "week": "1",
            },
        ]
        response = StubResponse(compressed_csv(rows))

        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            with patch(
                "app.data_foundation.ingestion.urlopen", return_value=response
            ) as urlopen:
                output_path, rows_written = save_raw_nfl_play_by_play(
                    2024, output_dir
                )

            self.assertEqual(
                output_path.name, "nfl_play_by_play_2024_raw.csv.gz"
            )
            self.assertEqual(rows_written, 2)
            with gzip.open(output_path, "rt", newline="") as output_file:
                saved_rows = list(csv.DictReader(output_file))
            self.assertEqual(saved_rows, rows)

            metadata_path = (
                output_dir / "nfl_play_by_play_2024_raw.metadata.json"
            )
            metadata = json.loads(metadata_path.read_text())
            self.assertEqual(metadata["scope"], "all_nfl")
            self.assertNotIn("team", metadata)
            self.assertEqual(metadata["rows_written"], 2)
            self.assertEqual(metadata["source_column_count"], len(SOURCE_COLUMNS))
            self.assertEqual(metadata["output_path"], str(output_path))

            urlopen.assert_called_once_with(
                PBP_URL_TEMPLATE.format(season=2024), timeout=60
            )

    def test_missing_required_columns_does_not_replace_existing_output(self) -> None:
        response = StubResponse(
            compressed_csv(
                [{"game_id": "2024_01_ARI_BUF", "play_id": "1"}],
                columns=["game_id", "play_id"],
            )
        )

        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "nfl_play_by_play_2024_raw.csv.gz"
            output_path.write_bytes(b"existing-data")

            with patch(
                "app.data_foundation.ingestion.urlopen", return_value=response
            ):
                with self.assertRaisesRegex(ValueError, "missing required columns"):
                    save_raw_nfl_play_by_play(2024, Path(directory))

            self.assertEqual(output_path.read_bytes(), b"existing-data")

    def test_incomplete_download_does_not_replace_existing_output(self) -> None:
        rows = [
            {
                "game_id": "2024_01_ARI_BUF",
                "play_id": "1",
                "home_team": "BUF",
                "away_team": "ARI",
                "posteam": "BUF",
                "defteam": "ARI",
                "season": "2024",
                "week": "1",
            }
        ]
        truncated_payload = compressed_csv(rows)[:-8]
        response = StubResponse(truncated_payload)

        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            output_path = output_dir / "nfl_play_by_play_2024_raw.csv.gz"
            output_path.write_bytes(b"existing-data")

            with patch(
                "app.data_foundation.ingestion.urlopen", return_value=response
            ):
                with self.assertRaises((EOFError, gzip.BadGzipFile)):
                    save_raw_nfl_play_by_play(2024, output_dir)

            self.assertEqual(output_path.read_bytes(), b"existing-data")
            temporary_outputs = list(
                output_dir.glob(".nfl_play_by_play_2024_raw*")
            )
            self.assertEqual(temporary_outputs, [])

    def test_rejects_season_outside_supported_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "Season must be between"):
            validate_season(1998)


if __name__ == "__main__":
    unittest.main()
