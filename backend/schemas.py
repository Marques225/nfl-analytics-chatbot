from pydantic import BaseModel
from typing import Optional, List, Any

# --- SHARED BASES ---
class PlayerBase(BaseModel):
    name: str
    position: str
    team_id: str

class TeamBase(BaseModel):
    team_name: str
    city: str
    abbreviation: str

# --- PLAYER SCHEMAS ---
class Player(PlayerBase):
    player_id: str

    class Config:
        from_attributes = True

# --- TEAM SCHEMAS ---
class Team(TeamBase):
    id: int

    class Config:
        from_attributes = True

# --- LEADERBOARD SCHEMAS (Fixes the current error) ---
class LeaderEntry(BaseModel):
    rank: int
    player_id: str
    name: str
    team: str
    value: float

# --- STATS SCHEMAS ---
class SeasonStat(BaseModel):
    season: int
    value: float