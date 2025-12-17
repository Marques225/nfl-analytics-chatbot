from fastapi import FastAPI
from api.routes import players, teams, leaders # <--- Import new routes

app = FastAPI(title="NFL Analytics Chatbot API")

# Register Routes
app.include_router(players.router, prefix="/players", tags=["Players"])
app.include_router(teams.router, prefix="/teams", tags=["Teams"])
app.include_router(leaders.router, prefix="/leaders", tags=["Leaders"])

@app.get("/")
def health_check():
    return {"status": "ok", "message": "API is running 🚀"}