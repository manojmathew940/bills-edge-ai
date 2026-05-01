from fastapi import FastAPI, HTTPException

from app.analytics.game_metrics import (
    calculate_game_metrics,
    get_game_by_week,
)

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
