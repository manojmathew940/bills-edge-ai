from __future__ import annotations

import unittest

from app.llm.answering import LLMServiceError
from app.llm.data_extraction import (
    EXTRACT_DATA_INSTRUCTIONS,
    parse_data_extraction_decision,
    render_data_extraction_prompt,
)


class DataExtractionTest(unittest.TestCase):
    def test_render_prompt_includes_schema_metadata(self) -> None:
        prompt = render_data_extraction_prompt("How did the Bills offense perform?")

        self.assertIn("Approved view: bills_plays", prompt)
        self.assertIn("- season (integer): NFL season.", prompt)
        self.assertIn(
            "- passer_player_name (string): Player name for the passer.",
            prompt,
        )
        self.assertIn("Question:\nHow did the Bills offense perform?", prompt)
        self.assertNotIn("Example JSON when data is useful", prompt)

    def test_instructions_include_extraction_examples(self) -> None:
        self.assertIn("Example JSON when data is useful", EXTRACT_DATA_INSTRUCTIONS)
        self.assertIn(
            "Example JSON when local data is not useful",
            EXTRACT_DATA_INSTRUCTIONS,
        )

    def test_parses_valid_data_request(self) -> None:
        decision = parse_data_extraction_decision(
            """
            {
              "needs_data": true,
              "sql": "SELECT season, COUNT(*) AS plays FROM bills_plays GROUP BY season ORDER BY season",
              "reason": "The question asks for play counts by season.",
              "confidence": 0.8,
              "data_not_needed_reason": null
            }
            """
        )

        self.assertTrue(decision.needs_data)
        self.assertEqual(
            decision.sql,
            "SELECT season, COUNT(*) AS plays FROM bills_plays GROUP BY season ORDER BY season",
        )
        self.assertEqual(decision.reason, "The question asks for play counts by season.")
        self.assertEqual(decision.confidence, 0.8)
        self.assertIsNone(decision.data_not_needed_reason)

    def test_parses_valid_no_data_decision(self) -> None:
        decision = parse_data_extraction_decision(
            """
            {
              "needs_data": false,
              "sql": null,
              "reason": "The question asks about current injuries.",
              "confidence": 0.9,
              "data_not_needed_reason": "Local play data does not include injuries."
            }
            """
        )

        self.assertFalse(decision.needs_data)
        self.assertIsNone(decision.sql)
        self.assertEqual(decision.reason, "The question asks about current injuries.")
        self.assertEqual(decision.confidence, 0.9)
        self.assertEqual(
            decision.data_not_needed_reason,
            "Local play data does not include injuries.",
        )

    def test_strips_fenced_json(self) -> None:
        decision = parse_data_extraction_decision(
            """```json
            {
              "needs_data": true,
              "sql": "SELECT 1 FROM bills_plays",
              "reason": "Test query.",
              "confidence": 1,
              "data_not_needed_reason": null
            }
            ```"""
        )

        self.assertTrue(decision.needs_data)
        self.assertEqual(decision.sql, "SELECT 1 FROM bills_plays")

    def test_clamps_confidence(self) -> None:
        high = parse_data_extraction_decision(
            """
            {
              "needs_data": false,
              "sql": null,
              "reason": "Too high.",
              "confidence": 10,
              "data_not_needed_reason": null
            }
            """
        )
        low = parse_data_extraction_decision(
            """
            {
              "needs_data": false,
              "sql": null,
              "reason": "Too low.",
              "confidence": -5,
              "data_not_needed_reason": null
            }
            """
        )

        self.assertEqual(high.confidence, 1.0)
        self.assertEqual(low.confidence, 0.0)

    def test_invalid_confidence_defaults_to_zero(self) -> None:
        decision = parse_data_extraction_decision(
            """
            {
              "needs_data": false,
              "sql": null,
              "reason": "Bad confidence.",
              "confidence": "high",
              "data_not_needed_reason": null
            }
            """
        )

        self.assertEqual(decision.confidence, 0.0)

    def test_ignores_sql_when_data_not_needed(self) -> None:
        decision = parse_data_extraction_decision(
            """
            {
              "needs_data": false,
              "sql": "SELECT * FROM bills_plays",
              "reason": "No data needed.",
              "confidence": 0.5,
              "data_not_needed_reason": "The question can be answered directly."
            }
            """
        )

        self.assertFalse(decision.needs_data)
        self.assertIsNone(decision.sql)

    def test_string_false_does_not_request_data(self) -> None:
        decision = parse_data_extraction_decision(
            """
            {
              "needs_data": "false",
              "sql": "SELECT * FROM bills_plays",
              "reason": "String boolean.",
              "confidence": 0.5,
              "data_not_needed_reason": "No local data needed."
            }
            """
        )

        self.assertFalse(decision.needs_data)
        self.assertIsNone(decision.sql)

    def test_blank_sql_when_data_needed_becomes_no_data_decision(self) -> None:
        decision = parse_data_extraction_decision(
            """
            {
              "needs_data": true,
              "sql": " ",
              "reason": "",
              "confidence": 0.5,
              "data_not_needed_reason": null
            }
            """
        )

        self.assertFalse(decision.needs_data)
        self.assertIsNone(decision.sql)
        self.assertIn("did not provide usable SQL", decision.reason)
        self.assertIn("did not provide usable SQL", decision.data_not_needed_reason)

    def test_missing_reason_uses_fallback(self) -> None:
        decision = parse_data_extraction_decision(
            """
            {
              "needs_data": false,
              "sql": null,
              "confidence": 0.2,
              "data_not_needed_reason": null
            }
            """
        )

        self.assertEqual(decision.reason, "Extractor did not provide a reason.")

    def test_malformed_json_raises_service_error(self) -> None:
        with self.assertRaisesRegex(LLMServiceError, "invalid JSON"):
            parse_data_extraction_decision("{not valid json")

    def test_missing_json_object_raises_service_error(self) -> None:
        with self.assertRaisesRegex(LLMServiceError, "invalid JSON"):
            parse_data_extraction_decision("no JSON here")


if __name__ == "__main__":
    unittest.main()
