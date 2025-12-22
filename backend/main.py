from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import players, teams, leaders, chat, predict 

app = FastAPI()

# 1. BULLETPROOF SECURITY (CORS)
# We accept requests from ANY origin to stop the 400 Bad Request errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (localhost:3000, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, PUT, DELETE)
    allow_headers=["*"],  # Allows all headers
)

# 2. CONNECT ROUTES
app.include_router(players.router, prefix="/players", tags=["Players"])
app.include_router(teams.router, prefix="/teams", tags=["Teams"])
app.include_router(leaders.router, prefix="/leaders", tags=["Leaders"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(predict.router, prefix="/predict", tags=["ML Predictions"]) # <--- Add this

# 3. HEALTH CHECK
@app.get("/")
def read_root():
    return {"status": "NFL Analytics Brain is Online 🧠"}