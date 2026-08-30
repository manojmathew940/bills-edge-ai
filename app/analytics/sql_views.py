from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import duckdb
import pyarrow.parquet as pq


PROCESSED_DATA_DIR = Path("data/processed")
NFL_PLAYS_VIEW = "nfl_plays"
PLAY_FILE_PATTERN = re.compile(r"^nfl_plays_(\d{4})\.parquet$")


class AnalyticsViewError(RuntimeError):
    """Raised when analytics views cannot be created from cleaned data."""


def processed_play_paths(data_dir: Path = PROCESSED_DATA_DIR) -> list[Path]:
    paths = []
    for path in data_dir.glob("nfl_plays_*.parquet"):
        if PLAY_FILE_PATTERN.match(path.name):
            paths.append(path)

    paths.sort(key=season_from_path)
    if not paths:
        raise AnalyticsViewError(f"No cleaned NFL play files found in {data_dir}.")

    return paths


def season_from_path(path: Path) -> int:
    match = PLAY_FILE_PATTERN.match(path.name)
    if not match:
        raise AnalyticsViewError(f"Unexpected cleaned play filename: {path}")

    return int(match.group(1))


def connect_duckdb() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(database=":memory:")


def initialize_analytics_views(
    connection: duckdb.DuckDBPyConnection,
    paths: list[Path] | None = None,
) -> None:
    play_paths = paths or processed_play_paths()
    validate_compatible_schemas(play_paths)
    create_nfl_plays_view(connection, play_paths)


def create_analytics_connection(
    paths: list[Path] | None = None,
) -> duckdb.DuckDBPyConnection:
    connection = connect_duckdb()
    initialize_analytics_views(connection, paths)
    return connection


def create_nfl_plays_view(
    connection: duckdb.DuckDBPyConnection,
    paths: list[Path],
) -> None:
    if not paths:
        raise AnalyticsViewError("Cannot create nfl_plays view without files.")

    path_list = ", ".join(sql_string(str(path)) for path in paths)
    connection.execute(
        "CREATE OR REPLACE VIEW nfl_plays AS "
        f"SELECT * FROM read_parquet([{path_list}], union_by_name=true)"
    )


def describe_nfl_plays(connection: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    rows = connection.execute(f"DESCRIBE {NFL_PLAYS_VIEW}").fetchall()
    columns = [column[0] for column in connection.description]
    return [dict(zip(columns, row)) for row in rows]


def available_seasons(connection: duckdb.DuckDBPyConnection) -> list[int]:
    rows = connection.execute(
        f"SELECT DISTINCT season FROM {NFL_PLAYS_VIEW} ORDER BY season"
    ).fetchall()
    return [int(row[0]) for row in rows]


def validate_compatible_schemas(paths: list[Path]) -> None:
    if not paths:
        raise AnalyticsViewError("Cannot validate schemas without files.")

    base_path = paths[0]
    base_schema = pq.read_schema(base_path)
    base_fields = [field.name for field in base_schema]

    for path in paths[1:]:
        schema = pq.read_schema(path)
        fields = [field.name for field in schema]
        if fields != base_fields:
            raise AnalyticsViewError(
                "Cleaned play schemas are not compatible: "
                f"{base_path} differs from {path}."
            )


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
