from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


DEFAULT_MODEL = "gpt-5.5"
MAX_OUTPUT_TOKENS = 900

INSTRUCTIONS = """
You are a Buffalo Bills football analyst.

Answer the user's question using only the supplied game metrics.
Do not invent plays, injuries, quotes, coaching comments, weather effects, or
outside context that is not present in the metrics.

If the metrics are not enough to answer the question, say what is missing.
Be clear about direct evidence from the metrics versus interpretation.
Keep the answer concise and specific.
""".strip()


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM client is not configured."""


class LLMServiceError(RuntimeError):
    """Raised when the LLM provider call fails."""


def answer_game_question(
    question: str, metrics: dict[str, Any], *, load_env: bool = True
) -> str:
    if load_env:
        load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise LLMConfigurationError(
            "LLM answering is not configured. Set OPENAI_API_KEY to enable /ask."
        )

    client = OpenAI()
    prompt = render_prompt(question, metrics)

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            instructions=INSTRUCTIONS,
            input=prompt,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
    except OpenAIError as error:
        raise LLMServiceError("The LLM service failed to answer the question.") from error

    return response.output_text


def render_prompt(question: str, metrics: dict[str, Any]) -> str:
    metrics_json = json.dumps(metrics, indent=2, sort_keys=True)
    return (
        f"Question:\n{question}\n\n"
        "Game metrics JSON:\n"
        f"{metrics_json}"
    )


def render_debug_prompt(question: str, metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": DEFAULT_MODEL,
        "instructions": INSTRUCTIONS,
        "input": render_prompt(question, metrics),
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }
