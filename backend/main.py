from fastapi import FastAPI
from api.routes import players, teams, leaders, compare, draft, analytics  # <--- Import analytics

app = FastAPI(title="NFL Analytics Chatbot API")

# Register Routes
app.include_router(players.router, prefix="/players", tags=["Players"])
app.include_router(teams.router, prefix="/teams", tags=["Teams"])
app.include_router(leaders.router, prefix="/leaders", tags=["Leaders"])
app.include_router(compare.router, prefix="/compare", tags=["Analytics"])
app.include_router(draft.router, prefix="/draft-suggestions", tags=["Draft"])
app.include_router(analytics.router, prefix="/analytics", tags=["Deep Dive"]) # <--- NEW

@app.get("/")
def health_check():
    return {"status": "ok", "message": "API is running 🚀"}