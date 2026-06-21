from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.analytics.sql_views import BILLS_PLAYS_VIEW


SCHEMA_METADATA_PATH = Path("docs/bills_plays_schema.yaml")


class SchemaMetadataError(RuntimeError):
    """Raised when analytics schema metadata cannot be loaded."""


def load_schema_metadata(path: Path = SCHEMA_METADATA_PATH) -> dict[str, Any]:
    if not path.exists():
        raise SchemaMetadataError(f"Missing schema metadata file: {path}")

    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict):
        raise SchemaMetadataError(f"Schema metadata file is invalid: {path}")

    return payload


def view_metadata(
    view_name: str = BILLS_PLAYS_VIEW,
    *,
    path: Path = SCHEMA_METADATA_PATH,
) -> dict[str, Any]:
    payload = load_schema_metadata(path)
    views = payload.get("views")
    if not isinstance(views, dict) or view_name not in views:
        raise SchemaMetadataError(f"Schema metadata does not define view: {view_name}")

    view = views[view_name]
    if not isinstance(view, dict):
        raise SchemaMetadataError(f"Schema metadata for {view_name} is invalid.")

    columns = view.get("columns")
    if not isinstance(columns, dict) or not columns:
        raise SchemaMetadataError(f"Schema metadata for {view_name} has no columns.")

    return view


def render_view_schema_guide(view_name: str = BILLS_PLAYS_VIEW) -> str:
    view = view_metadata(view_name)
    description = view.get("description", "")
    grain = view.get("grain", "")
    columns = view["columns"]

    lines = [
        f"Approved view: {view_name}",
        f"Description: {description}",
        f"Grain: {grain}",
        "",
        "Columns:",
    ]

    for column_name, metadata in columns.items():
        if not isinstance(metadata, dict):
            raise SchemaMetadataError(
                f"Schema metadata for {view_name}.{column_name} is invalid."
            )

        column_type = metadata.get("type", "unknown")
        description = metadata.get("description", "")
        lines.append(f"- {column_name} ({column_type}): {description}")

    return "\n".join(lines).strip()
