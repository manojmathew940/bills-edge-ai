from __future__ import annotations

from typing import Any

from app.analytics.sql_views import AnalyticsViewError, create_analytics_connection


DEFAULT_SQL_ROW_LIMIT = 100


def execute_analytics_sql(
    sql: str,
    *,
    row_limit: int = DEFAULT_SQL_ROW_LIMIT,
) -> dict[str, Any]:
    if row_limit < 1:
        raise AnalyticsViewError("row_limit must be at least 1.")

    connection = create_analytics_connection()
    limited_sql = apply_limit(sql, row_limit)
    cursor = connection.execute(limited_sql)
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    return {
        "sql": limited_sql,
        "columns": columns,
        "rows": [dict(zip(columns, row)) for row in rows],
        "row_count": len(rows),
        "row_limit": row_limit,
    }


def apply_limit(sql: str, row_limit: int) -> str:
    stripped = sql.strip().rstrip(";")
    return f"SELECT * FROM ({stripped}) AS analytics_query LIMIT {int(row_limit)}"
