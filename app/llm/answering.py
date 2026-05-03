from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


DEFAULT_MODEL = "gpt-5.5"
DEFAULT_API_KEY = "ollama"
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


def get_llm_model() -> str:
    return os.getenv("LLM_MODEL", DEFAULT_MODEL)


def get_llm_base_url() -> str | None:
    return os.getenv("LLM_BASE_URL") or None


def get_llm_api_key() -> str | None:
    if get_llm_base_url():
        return os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or DEFAULT_API_KEY

    return os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")


def build_llm_client() -> OpenAI:
    api_key = get_llm_api_key()
    base_url = get_llm_base_url()

    if not api_key:
        raise LLMConfigurationError(
            "LLM answering is not configured. Set OPENAI_API_KEY for OpenAI, "
            "or set LLM_BASE_URL and LLM_MODEL for a local provider such as Ollama."
        )

    client_options = {"api_key": api_key}
    if base_url:
        client_options["base_url"] = base_url

    return OpenAI(**client_options)


def answer_game_question(
    question: str, metrics: dict[str, Any], *, load_env: bool = True
) -> str:
    if load_env:
        load_dotenv()

    client = build_llm_client()
    prompt = render_prompt(question, metrics)
    model = get_llm_model()

    try:
        response = client.responses.create(
            model=model,
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


def render_debug_prompt(
    question: str, metrics: dict[str, Any], *, load_env: bool = True
) -> dict[str, Any]:
    if load_env:
        load_dotenv()

    return {
        "model": get_llm_model(),
        "base_url": get_llm_base_url(),
        "instructions": INSTRUCTIONS,
        "input": render_prompt(question, metrics),
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }
