from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import players, teams, leaders, compare, draft, analytics, chat  # <--- IMPORT CHAT

app = FastAPI(title="NFL Analytics Chatbot API")

# --- NEW: ALLOW FRONTEND CONNECTION ---
origins = [
    "http://localhost:5173",  # React App
    "http://localhost:3000",  # Backup port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------------------

# Register Routes
app.include_router(players.router, prefix="/players", tags=["Players"])
app.include_router(teams.router, prefix="/teams", tags=["Teams"])
app.include_router(leaders.router, prefix="/leaders", tags=["Leaders"])
app.include_router(compare.router, prefix="/compare", tags=["Analytics"])
app.include_router(draft.router, prefix="/draft-suggestions", tags=["Draft"])
app.include_router(analytics.router, prefix="/analytics", tags=["Deep Dive"])
app.include_router(chat.router, prefix="/chat", tags=["Chat Interface"])  # <--- NEW REGISTRATION

@app.get("/")
def health_check():
    return {"status": "ok", "message": "API is running 🚀"}