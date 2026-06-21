from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any

from dotenv import load_dotenv
from openai import OpenAIError

from app.analytics.schema_metadata import render_view_schema_guide
from app.analytics.sql_views import BILLS_PLAYS_VIEW
from app.llm.answering import (
    LLMServiceError,
    build_llm_client,
    get_llm_base_url,
    get_llm_model,
)


_MAX_DATA_EXTRACTION_OUTPUT_TOKENS = 700
_FALLBACK_REASON = "Extractor did not provide a reason."
_BLANK_SQL_REASON = "Extractor said data was needed but did not provide usable SQL."

_EXTRACT_DATA_INSTRUCTIONS = f"""
You are a data extraction assistant for a Buffalo Bills analytics app.

Your job is to decide whether local structured play data can help answer the
user's question. If it can, write exactly one DuckDB SELECT query against the
approved `{BILLS_PLAYS_VIEW}` view. If local data is not useful or not available
for the question, do not write SQL.

Do not answer the user's question.
Return only JSON with these fields:
- needs_data: boolean
- sql: string or null
- reason: short reason for the decision
- confidence: number from 0 to 1
- data_not_needed_reason: string or null

SQL rules:
- Use only the `{BILLS_PLAYS_VIEW}` view.
- Return exactly one SELECT query.
- Do not use INSERT, UPDATE, DELETE, DROP, CREATE, COPY, ATTACH, or file-reading
  functions.
- Prefer concise aggregate queries over returning raw play rows.
- Include ORDER BY when comparing grouped results.

If the question needs current news, injuries, transactions, roster context,
quotes, reporting, or information not represented in play-level data, return
needs_data=false and explain what local data is missing.

Example JSON when data is useful:
{{
  "needs_data": true,
  "sql": "SELECT season, AVG(epa) AS avg_epa FROM {BILLS_PLAYS_VIEW} WHERE bills_on_offense = true GROUP BY season ORDER BY season",
  "reason": "The question asks for an offensive trend that can be answered from play-level EPA.",
  "confidence": 0.8,
  "data_not_needed_reason": null
}}

Example JSON when local data is not useful:
{{
  "needs_data": false,
  "sql": null,
  "reason": "The question depends on current injury reporting that is not in the play-level database.",
  "confidence": 0.9,
  "data_not_needed_reason": "Local play data does not include current injuries or reporting."
}}
""".strip()


@dataclass(frozen=True)
class DataExtractionDecision:
    needs_data: bool
    sql: str | None
    reason: str
    confidence: float
    data_not_needed_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_data_extraction_llm(
    question: str,
    *,
    provider: str | None = None,
) -> DataExtractionDecision:
    load_dotenv()

    client = build_llm_client(provider)
    prompt = _render_data_extraction_prompt(question)
    model = get_llm_model(provider)

    try:
        response = client.responses.create(
            model=model,
            instructions=_EXTRACT_DATA_INSTRUCTIONS,
            input=prompt,
            max_output_tokens=_MAX_DATA_EXTRACTION_OUTPUT_TOKENS,
        )
    except OpenAIError as error:
        raise LLMServiceError("The LLM data extractor failed to inspect the question.") from error

    return _parse_data_extraction_decision(response.output_text)


def _parse_data_extraction_decision(output_text: str) -> DataExtractionDecision:
    try:
        payload = json.loads(_extract_json_object(output_text))
    except json.JSONDecodeError as error:
        raise LLMServiceError("The LLM data extractor returned invalid JSON.") from error

    needs_data = _normalize_bool(payload.get("needs_data"))
    sql = _normalize_optional_text(payload.get("sql"))
    reason = _normalize_optional_text(payload.get("reason")) or _FALLBACK_REASON
    data_not_needed_reason = _normalize_optional_text(
        payload.get("data_not_needed_reason")
    )

    try:
        confidence = float(payload.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0
    confidence = max(0.0, min(confidence, 1.0))

    if not needs_data:
        sql = None
    elif not sql:
        needs_data = False
        sql = None
        reason = reason if reason != _FALLBACK_REASON else _BLANK_SQL_REASON
        if data_not_needed_reason is None:
            data_not_needed_reason = _BLANK_SQL_REASON

    return DataExtractionDecision(
        needs_data=needs_data,
        sql=sql,
        reason=reason,
        confidence=confidence,
        data_not_needed_reason=data_not_needed_reason,
    )


def _extract_json_object(output_text: str) -> str:
    text = output_text.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMServiceError("The LLM data extractor returned invalid JSON.")

    return text[start : end + 1]


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}

    return bool(value)


def _render_data_extraction_prompt(question: str) -> str:
    schema_guide = render_view_schema_guide()
    return (
        "Use the schema below to choose the exact view and column names for any "
        "SQL query.\n"
        "Before writing SQL, identify which listed columns are relevant to the "
        "question.\n"
        "Do not reference columns that are not listed in the schema.\n\n"
        f"{schema_guide}\n\n"
        f"Question:\n{question}"
    )


def build_data_extraction_debug_payload(
    question: str,
    *,
    provider: str | None = None,
) -> dict[str, Any]:
    load_dotenv()

    return {
        "provider": provider or ("local" if get_llm_base_url() else "openai"),
        "model": get_llm_model(provider),
        "base_url": get_llm_base_url(provider),
        "instructions": _EXTRACT_DATA_INSTRUCTIONS,
        "input": _render_data_extraction_prompt(question),
        "max_output_tokens": _MAX_DATA_EXTRACTION_OUTPUT_TOKENS,
    }
