from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException

from app.analytics.game_metrics import (
    calculate_game_metrics,
    get_game_by_week,
)
from app.llm.answering import (
    LLMConfigurationError,
    LLMServiceError,
    answer_game_question,
)


class AskRequest(BaseModel):
    season: int
    week: int
    question: str = Field(min_length=1)

app = FastAPI(title="Bills AI Analyst")


@app.get("/")
def root():
    return {"message": "Bills AI Analyst is running"}


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

    try:
        answer = answer_game_question(request.question, metrics)
    except LLMConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LLMServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return {"answer": answer, "metrics": metrics}
