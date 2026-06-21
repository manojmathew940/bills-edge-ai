from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.analytics.schema_metadata import (
    SchemaMetadataError,
    render_view_schema_guide,
    view_metadata,
)


class SchemaMetadataTest(unittest.TestCase):
    def test_view_metadata_loads_bills_plays_columns(self) -> None:
        view = view_metadata("bills_plays")

        self.assertEqual(view["grain"], "One row per play from a Buffalo Bills game.")
        self.assertIn("season", view["columns"])
        self.assertIn("explosive_play", view["columns"])

    def test_render_view_schema_guide_includes_columns(self) -> None:
        guide = render_view_schema_guide("bills_plays")

        self.assertIn("Approved view: bills_plays", guide)
        self.assertIn("- season (integer): NFL season.", guide)
        self.assertIn(
            "- bills_on_offense (boolean): True when Buffalo was the possession team.",
            guide,
        )
        self.assertIn(
            "- explosive_play (boolean): True for explosive plays",
            guide,
        )

    def test_missing_view_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(SchemaMetadataError, "does not define view"):
            view_metadata("missing_view")

    def test_missing_file_raises_clear_error(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "missing.yaml"

            with self.assertRaisesRegex(SchemaMetadataError, "Missing schema"):
                view_metadata("bills_plays", path=path)


if __name__ == "__main__":
    unittest.main()
