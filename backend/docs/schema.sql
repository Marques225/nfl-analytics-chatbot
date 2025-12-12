-- Teams table
CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    conference TEXT,
    division TEXT
);

-- Players table
CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    team_id INT REFERENCES teams(team_id)
);

-- Weekly player stats
CREATE TABLE player_weekly_stats (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(player_id),
    season INT,
    week INT,
    passing_yards INT DEFAULT 0,
    rushing_yards INT DEFAULT 0,
    receiving_yards INT DEFAULT 0,
    touchdowns INT DEFAULT 0,
    tackles INT DEFAULT 0,
    sacks FLOAT DEFAULT 0,
    interceptions INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Weekly team stats
CREATE TABLE team_weekly_stats (
    id SERIAL PRIMARY KEY,
    team_id INT REFERENCES teams(team_id),
    season INT,
    week INT,
    points_for INT,
    points_against INT,
    offensive_rank INT,
    defensive_rank INT,
    created_at TIMESTAMP DEFAULT NOW()
);
