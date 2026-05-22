from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any

from dotenv import load_dotenv
from openai import OpenAIError

from app.llm.answering import (
    LLMServiceError,
    build_llm_client,
    get_llm_base_url,
    get_llm_model,
)


MAX_PLANNER_OUTPUT_TOKENS = 350
DEFAULT_ENGINE = "direct_llm"
GAME_METRICS_ENGINE = "game_metrics"
SUPPORTED_ENGINES = {GAME_METRICS_ENGINE, DEFAULT_ENGINE}

PLANNER_INSTRUCTIONS = """
You are a router for a Buffalo Bills analytics assistant.

Classify the user's question into the best available engine.

Available engines:
- game_metrics: use only when the question asks about one specific Bills game,
  such as a matchup, week, result, or what happened in that game.
- direct_llm: use when the question is general, comparative across many games,
  about the team/player/season broadly, or does not require one specific game.

Return only JSON with these fields:
- engine: "game_metrics" or "direct_llm"
- reason: short reason for the route
- confidence: number from 0 to 1

Do not answer the user's question.
""".strip()


@dataclass(frozen=True)
class PlannerDecision:
    engine: str
    reason: str
    confidence: float

    @property
    def requires_game_metrics(self) -> bool:
        return self.engine == GAME_METRICS_ENGINE

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["requires_game_metrics"] = self.requires_game_metrics
        return data


def run_planner_llm(
    question: str,
    *,
    provider: str | None = None,
) -> PlannerDecision:
    load_dotenv()

    client = build_llm_client(provider)
    prompt = render_planner_prompt(question)
    model = get_llm_model(provider)

    try:
        response = client.responses.create(
            model=model,
            instructions=PLANNER_INSTRUCTIONS,
            input=prompt,
            max_output_tokens=MAX_PLANNER_OUTPUT_TOKENS,
        )
    except OpenAIError as error:
        raise LLMServiceError("The LLM planner failed to route the question.") from error

    return parse_planner_decision(response.output_text)


def parse_planner_decision(output_text: str) -> PlannerDecision:
    try:
        payload = json.loads(extract_json_object(output_text))
    except json.JSONDecodeError as error:
        raise LLMServiceError("The LLM planner returned an invalid route.") from error

    engine = str(payload.get("engine", DEFAULT_ENGINE)).strip().lower()
    if engine not in SUPPORTED_ENGINES:
        engine = DEFAULT_ENGINE

    reason = str(payload.get("reason", "")).strip()
    if not reason:
        reason = "Planner did not provide a reason."

    try:
        confidence = float(payload.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0
    confidence = max(0.0, min(confidence, 1.0))

    return PlannerDecision(engine=engine, reason=reason, confidence=confidence)


def extract_json_object(output_text: str) -> str:
    text = output_text.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMServiceError("The LLM planner returned an invalid route.")

    return text[start : end + 1]


def render_planner_prompt(question: str) -> str:
    return f"Question:\n{question}"


def build_planner_debug_payload(
    question: str,
    *,
    provider: str | None = None,
) -> dict[str, Any]:
    load_dotenv()

    return {
        "provider": provider or ("local" if get_llm_base_url() else "openai"),
        "model": get_llm_model(provider),
        "base_url": get_llm_base_url(provider),
        "instructions": PLANNER_INSTRUCTIONS,
        "input": render_planner_prompt(question),
        "max_output_tokens": MAX_PLANNER_OUTPUT_TOKENS,
    }
