# TODO Backlog List

## 1. Environment Setup
- [ ] Create `.env` file with SUPABASE_URL, SERVICE_ROLE_KEY, DATABASE_URL.
- [ ] Install backend dependencies (`pip install -r requirements.txt`).

## 2. Database Setup
- [ ] Create `docs/schema.sql`.
- [ ] Create tables in Supabase using SQL editor.
- [ ] Add indexes for player_id, week, and season.
- [ ] Decide if we need materialized views for fast weekly analytics.

## 3. ETL Pipeline (Python)
- [ ] Choose NFL stats data source (ESPN, Sleeper API, NFLFastR, SportsDataIO).
- [ ] Write `etl/fetch_stats.py` to pull weekly data.
- [ ] Write transformers to normalize the stats.
- [ ] Write loader to insert/update Supabase tables.
- [ ] Schedule weekly ETL updates.

## 4. FastAPI Backend
- [ ] Create main FastAPI app.
- [ ] Create `/players` endpoint.
- [ ] Create `/teams` endpoint.
- [ ] Create `/analytics/player/{id}` endpoint.
- [ ] Create `/analytics/team/{id}` endpoint.
- [ ] Add pagination + filtering.

## 5. Chatbot (ML/NLP)
- [ ] Build toy transformer model (Python).
- [ ] Train on synthetic queries for practice.
- [ ] Integrate HuggingFace pretrained model.
- [ ] Integrate with FastAPI endpoint `/chatbot/query`.

## 6. Frontend (React)
- [ ] Create React project with Vite.
- [ ] Add Bootstrap.
- [ ] Create Player Search UI.
- [ ] Create Team Analytics UI.
- [ ] Connect to backend APIs.
- [ ] Create Chatbot UI (text box + conversation history).

## 7. Deployment
- [ ] Choose hosting (Render, Railway, Supabase edge functions).
- [ ] Deploy FastAPI backend.
- [ ] Deploy React frontend.
- [ ] Connect to production database.

---

Add more as needed. This file is meant to evolve as you build the project.
