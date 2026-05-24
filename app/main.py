import os

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.analytics.game_metrics import (
    calculate_game_metrics,
    get_game_from_question,
    get_game_by_week,
)
from app.llm.answering import (
    LLMConfigurationError,
    LLMServiceError,
    answer_direct_question,
    answer_game_question,
    build_answer_direct_debug_payload,
    build_answer_game_debug_payload,
)
from app.llm.planning import build_planner_debug_payload, run_planner_llm


class AskRequest(BaseModel):
    season: int
    question: str = Field(min_length=1)
    provider: str = Field(default="local", pattern="^(openai|local)$")


def is_llm_debug_enabled() -> bool:
    enabled_values = {"1", "true", "yes", "on"}
    return (
        os.getenv("BILLS_AI_DEBUG_PAYLOAD", "").lower() in enabled_values
        or os.getenv("BILLS_AI_DEBUG_PROMPT", "").lower() in enabled_values
    )


def build_request_planner_debug_payload(request: AskRequest) -> dict | None:
    if not is_llm_debug_enabled():
        return None

    return {
        "planner": build_planner_debug_payload(request.question, provider=request.provider)
    }


def build_request_llm_debug_payload(request: AskRequest, answer_payload: dict) -> dict | None:
    if not is_llm_debug_enabled():
        return None

    return {
        "planner": build_planner_debug_payload(request.question, provider=request.provider),
        "answer": answer_payload,
    }


def raise_llm_http_error(error: Exception, debug_payload: dict | None) -> None:
    detail = {"error": str(error), "debug_payload": debug_payload} if debug_payload else str(error)
    raise HTTPException(status_code=503, detail=detail) from error


app = FastAPI(title="Bills AI Analyst")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def root():
    return FileResponse("app/static/index.html")


@app.get("/games/{season}/{week}/metrics")
def game_metrics(season: int, week: int):
    try:
        game = get_game_by_week(season, week)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return calculate_game_metrics(game)


@app.post("/ask")
def ask(request: AskRequest):
    try:
        planner_decision = run_planner_llm(request.question, provider=request.provider)
    except LLMConfigurationError as error:
        raise_llm_http_error(error, build_request_planner_debug_payload(request))
    except LLMServiceError as error:
        raise_llm_http_error(error, build_request_planner_debug_payload(request))

    if planner_decision.requires_game_metrics:
        try:
            game = get_game_from_question(request.season, request.question)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            response = {
                "answer": str(error),
                "metrics": {},
                "provider": request.provider,
                "plan": planner_decision.to_dict(),
            }
            debug_payload = build_request_planner_debug_payload(request)
            if debug_payload:
                response["debug_payload"] = debug_payload
            return response

        metrics = calculate_game_metrics(game)
        debug_payload = build_request_llm_debug_payload(
            request,
            build_answer_game_debug_payload(request.question, metrics, provider=request.provider),
        )

        try:
            answer = answer_game_question(request.question, metrics, provider=request.provider)
        except LLMConfigurationError as error:
            raise_llm_http_error(error, debug_payload)
        except LLMServiceError as error:
            raise_llm_http_error(error, debug_payload)

        response = {
            "answer": answer,
            "metrics": metrics,
            "provider": request.provider,
            "plan": planner_decision.to_dict(),
        }
    else:
        debug_payload = build_request_llm_debug_payload(
            request,
            build_answer_direct_debug_payload(request.question, provider=request.provider),
        )

        try:
            answer = answer_direct_question(request.question, provider=request.provider)
        except LLMConfigurationError as error:
            raise_llm_http_error(error, debug_payload)
        except LLMServiceError as error:
            raise_llm_http_error(error, debug_payload)

        response = {
            "answer": answer,
            "metrics": {},
            "provider": request.provider,
            "plan": planner_decision.to_dict(),
        }

    if debug_payload:
        response["debug_payload"] = debug_payload

    return response
