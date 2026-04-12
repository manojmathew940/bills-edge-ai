from fastapi import FastAPI

app = FastAPI(title="Bills AI Analyst")

@app.get("/")
def root():
    return {"message": "Bills AI Analyst is running"}