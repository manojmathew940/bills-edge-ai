from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.analytics.sql_execution import execute_analytics_sql


SQL = """
SELECT
    season,
    SUM(passing_yards) AS fourth_quarter_passing_yards,
    COUNT(DISTINCT game_id) AS games,
    ROUND(SUM(passing_yards) / COUNT(DISTINCT game_id), 1) AS fourth_quarter_passing_yards_per_game
FROM bills_plays
WHERE passer_player_name = 'J.Allen'
AND season_type = 'REG'
AND qtr = 4
GROUP BY season
ORDER BY season
"""


def main() -> None:
    result = execute_analytics_sql(SQL)

    print("Executed SQL:")
    print(result["sql"])
    print()
    print_table(result["columns"], result["rows"])
    print()
    print(f"Rows returned: {result['row_count']} / limit {result['row_limit']}")


def print_table(columns: list[str], rows: list[dict]) -> None:
    if not rows:
        print("(no rows)")
        return

    widths = {
        column: max(
            len(column),
            *(len(format_cell(row.get(column))) for row in rows),
        )
        for column in columns
    }
    header = " | ".join(column.ljust(widths[column]) for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(separator)
    for row in rows:
        print(" | ".join(format_cell(row.get(column)).ljust(widths[column]) for column in columns))


def format_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value)


if __name__ == "__main__":
    main()
