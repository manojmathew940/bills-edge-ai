import os

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.analytics.game_metrics import (
    calculate_game_metrics,
    get_game_by_week,
)
from app.llm.answering import (
    LLMConfigurationError,
    LLMServiceError,
    answer_game_question,
    render_debug_prompt,
)


class AskRequest(BaseModel):
    season: int
    week: int
    question: str = Field(min_length=1)


def is_prompt_debug_enabled() -> bool:
    return os.getenv("BILLS_AI_DEBUG_PROMPT", "").lower() in {"1", "true", "yes", "on"}


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
        game = get_game_by_week(request.season, request.week)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    metrics = calculate_game_metrics(game)
    debug_prompt = (
        render_debug_prompt(request.question, metrics)
        if is_prompt_debug_enabled()
        else None
    )

    try:
        answer = answer_game_question(request.question, metrics)
    except LLMConfigurationError as error:
        detail = {"error": str(error), "debug_prompt": debug_prompt} if debug_prompt else str(error)
        raise HTTPException(status_code=503, detail=detail) from error
    except LLMServiceError as error:
        detail = {"error": str(error), "debug_prompt": debug_prompt} if debug_prompt else str(error)
        raise HTTPException(status_code=503, detail=detail) from error

    response = {"answer": answer, "metrics": metrics}

    if debug_prompt:
        response["debug_prompt"] = debug_prompt

    return response
