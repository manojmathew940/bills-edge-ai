from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.analytics.sql_views import BILLS_PLAYS_VIEW


_SCHEMA_METADATA_PATH = Path("docs/bills_plays_schema.yaml")


class SchemaMetadataError(RuntimeError):
    """Raised when analytics schema metadata cannot be loaded."""


def _load_schema_metadata(path: Path = _SCHEMA_METADATA_PATH) -> dict[str, Any]:
    if not path.exists():
        raise SchemaMetadataError(f"Missing schema metadata file: {path}")

    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict):
        raise SchemaMetadataError(f"Schema metadata file is invalid: {path}")

    return payload


def _validate_schema_metadata(schema: dict[str, Any]) -> None:
    view_name = schema.get("view")
    if view_name != BILLS_PLAYS_VIEW:
        raise SchemaMetadataError(
            f"Schema metadata must define view: {BILLS_PLAYS_VIEW}"
        )

    columns = schema.get("columns")
    if not isinstance(columns, dict) or not columns:
        raise SchemaMetadataError(
            f"Schema metadata for {BILLS_PLAYS_VIEW} has no columns."
        )

    for column_name, metadata in columns.items():
        if not isinstance(metadata, dict):
            raise SchemaMetadataError(
                f"Schema metadata for {BILLS_PLAYS_VIEW}.{column_name} is invalid."
            )


def _load_validated_schema_metadata(
    path: Path = _SCHEMA_METADATA_PATH,
) -> dict[str, Any]:
    schema = _load_schema_metadata(path)
    _validate_schema_metadata(schema)
    return schema


def render_view_schema_guide() -> str:
    schema = _load_validated_schema_metadata()
    description = schema.get("description", "")
    grain = schema.get("grain", "")
    columns = schema["columns"]

    lines = [
        f"Approved view: {BILLS_PLAYS_VIEW}",
        f"Description: {description}",
        f"Grain: {grain}",
        "",
        "Columns:",
    ]

    for column_name, metadata in columns.items():
        column_type = metadata.get("type", "unknown")
        description = metadata.get("description", "")
        lines.append(f"- {column_name} ({column_type}): {description}")

    return "\n".join(lines).strip()
