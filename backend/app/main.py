# app/main.py
from fastapi import FastAPI
from app.routers import players, teams

app = FastAPI(title="NFL Analytics Chatbot API")

app.include_router(players.router)
app.include_router(teams.router)

@app.get("/")
def root():
    return {"status": "API running"}
