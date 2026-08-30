from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException

from app.analytics.sql_execution import AnalyticsSqlResult
from app.analytics.sql_views import AnalyticsViewError
from app.llm.answering import LLMConfigurationError, LLMServiceError
from app.llm.data_extraction import DataExtractionDecision
from app.main import AskRequest, ask
from app.main import app


class AskApiTest(unittest.TestCase):
    def ask(self, question: str = "How did the Bills perform?"):
        return ask(
            AskRequest(
                question=question,
                provider="local",
            )
        )

    def test_application_uses_nfl_title(self) -> None:
        self.assertEqual(app.title, "NFL AI Analyst")

    @patch.dict("os.environ", {}, clear=True)
    @patch("app.main.answer_question", return_value="A direct answer.")
    @patch("app.main.validate_and_execute_analytics_sql")
    @patch("app.main.run_data_extraction_llm")
    def test_no_data_question_calls_answer_without_analytics(
        self,
        run_data_extraction_llm: Mock,
        validate_and_execute_analytics_sql: Mock,
        answer_question: Mock,
    ) -> None:
        decision = DataExtractionDecision(
            needs_data=False,
            sql=None,
            reason="No local data needed.",
            confidence=0.7,
            data_not_needed_reason="The question can be answered directly.",
        )
        run_data_extraction_llm.return_value = decision

        payload = self.ask("Who are the Bills?")

        self.assertEqual(payload["answer"], "A direct answer.")
        self.assertEqual(payload["provider"], "local")
        self.assertEqual(payload["data_request"], decision.to_dict())
        self.assertEqual(
            payload["analytics"],
            {
                "sql": None,
                "is_valid": None,
                "validation_reason": None,
                "columns": [],
                "rows": [],
                "row_limit": 100,
            },
        )
        run_data_extraction_llm.assert_called_once_with(
            "Who are the Bills?",
            provider="local",
        )
        validate_and_execute_analytics_sql.assert_not_called()
        answer_question.assert_called_once_with(
            "Who are the Bills?",
            decision,
            None,
            provider="local",
        )

    @patch.dict("os.environ", {}, clear=True)
    @patch("app.main.answer_question", return_value="The offense averaged 0.12 EPA.")
    @patch("app.main.validate_and_execute_analytics_sql")
    @patch("app.main.run_data_extraction_llm")
    def test_sql_backed_question_returns_analytics_rows(
        self,
        run_data_extraction_llm: Mock,
        validate_and_execute_analytics_sql: Mock,
        answer_question: Mock,
    ) -> None:
        sql = "SELECT season, AVG(epa) AS avg_epa FROM nfl_plays GROUP BY season"
        decision = DataExtractionDecision(
            needs_data=True,
            sql=sql,
            reason="The question asks for EPA by season.",
            confidence=0.8,
            data_not_needed_reason=None,
        )
        result = AnalyticsSqlResult(
            is_valid=True,
            validation_reason="SQL is valid.",
            columns=["season", "avg_epa"],
            rows=[{"season": 2023, "avg_epa": 0.12}],
        )
        run_data_extraction_llm.return_value = decision
        validate_and_execute_analytics_sql.return_value = result

        payload = self.ask()

        self.assertEqual(payload["answer"], "The offense averaged 0.12 EPA.")
        self.assertEqual(payload["data_request"], decision.to_dict())
        self.assertEqual(
            payload["analytics"],
            {
                "sql": sql,
                "is_valid": True,
                "validation_reason": "SQL is valid.",
                "columns": ["season", "avg_epa"],
                "rows": [{"season": 2023, "avg_epa": 0.12}],
                "row_limit": 100,
            },
        )
        validate_and_execute_analytics_sql.assert_called_once_with(sql, row_limit=100)
        answer_question.assert_called_once_with(
            "How did the Bills perform?",
            decision,
            result,
            provider="local",
        )

    @patch.dict("os.environ", {}, clear=True)
    @patch("app.main.answer_question")
    @patch("app.main.validate_and_execute_analytics_sql")
    @patch("app.main.run_data_extraction_llm")
    def test_invalid_sql_returns_structured_response_without_answer_generation(
        self,
        run_data_extraction_llm: Mock,
        validate_and_execute_analytics_sql: Mock,
        answer_question: Mock,
    ) -> None:
        sql = "DROP TABLE nfl_plays"
        decision = DataExtractionDecision(
            needs_data=True,
            sql=sql,
            reason="The question asks for local data.",
            confidence=0.8,
            data_not_needed_reason=None,
        )
        result = AnalyticsSqlResult(
            is_valid=False,
            validation_reason="SQL must be a SELECT query.",
            columns=[],
            rows=[],
        )
        run_data_extraction_llm.return_value = decision
        validate_and_execute_analytics_sql.return_value = result

        payload = self.ask()

        self.assertIn("failed validation", payload["answer"])
        self.assertEqual(payload["data_request"], decision.to_dict())
        self.assertEqual(
            payload["analytics"],
            {
                "sql": sql,
                "is_valid": False,
                "validation_reason": "SQL must be a SELECT query.",
                "columns": [],
                "rows": [],
                "row_limit": 100,
            },
        )
        answer_question.assert_not_called()

    @patch.dict("os.environ", {}, clear=True)
    @patch("app.main.run_data_extraction_llm")
    def test_extractor_llm_errors_return_503(
        self,
        run_data_extraction_llm: Mock,
    ) -> None:
        run_data_extraction_llm.side_effect = LLMServiceError("Extractor failed.")

        with self.assertRaises(HTTPException) as error:
            self.ask()

        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(error.exception.detail, "Extractor failed.")

    @patch.dict("os.environ", {}, clear=True)
    @patch("app.main.answer_question")
    @patch("app.main.run_data_extraction_llm")
    def test_answer_llm_errors_return_503(
        self,
        run_data_extraction_llm: Mock,
        answer_question: Mock,
    ) -> None:
        decision = DataExtractionDecision(
            needs_data=False,
            sql=None,
            reason="No local data needed.",
            confidence=0.7,
            data_not_needed_reason="The question can be answered directly.",
        )
        run_data_extraction_llm.return_value = decision
        answer_question.side_effect = LLMConfigurationError("Answering is not configured.")

        with self.assertRaises(HTTPException) as error:
            self.ask()

        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(error.exception.detail, "Answering is not configured.")

    @patch.dict("os.environ", {}, clear=True)
    @patch("app.main.validate_and_execute_analytics_sql")
    @patch("app.main.run_data_extraction_llm")
    def test_analytics_execution_errors_return_503(
        self,
        run_data_extraction_llm: Mock,
        validate_and_execute_analytics_sql: Mock,
    ) -> None:
        sql = "SELECT COUNT(*) AS plays FROM nfl_plays"
        decision = DataExtractionDecision(
            needs_data=True,
            sql=sql,
            reason="The question asks for local data.",
            confidence=0.8,
            data_not_needed_reason=None,
        )
        run_data_extraction_llm.return_value = decision
        validate_and_execute_analytics_sql.side_effect = AnalyticsViewError(
            "Local analytics data is unavailable."
        )

        with self.assertRaises(HTTPException) as error:
            self.ask()

        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(error.exception.detail, "Local analytics data is unavailable.")


if __name__ == "__main__":
    unittest.main()
