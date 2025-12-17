from pydantic import BaseModel
from typing import List, Optional

# --- Shared ---
class PlayerBase(BaseModel):
    id: str
    name: str
    position: str
    team: Optional[str] = None

class TeamBase(BaseModel):
    id: int
    name: str
    city: Optional[str] = None

# --- Responses ---
class PlayerResponse(PlayerBase):
    pass

class PlayerStats(BaseModel):
    season: int
    week: int
    passing_yards: Optional[int] = 0
    rushing_yards: Optional[int] = 0
    receiving_yards: Optional[int] = 0
    # Add more fields as needed

class PlayerProfile(PlayerResponse):
    recent_stats: List[PlayerStats] = [] 

# --- Team Models ---
class TeamStats(BaseModel):
    season: int
    off_total_yards: Optional[int] = 0
    off_passing_yards: Optional[int] = 0
    off_rushing_yards: Optional[int] = 0
    def_total_yards_allowed: Optional[int] = 0
    def_sacks_made: Optional[int] = 0

class TeamProfile(BaseModel):
    id: int
    name: str
    city: Optional[str] = None
    conference: Optional[str] = None
    division: Optional[str] = None
    season_stats: List[TeamStats] = []

# --- Leaderboard Models ---
class LeaderEntry(BaseModel):
    rank: int
    player_id: str
    name: str
    team: str
    value: float # The stat value (e.g., 300 yards)