from sqlalchemy import text

def calculate_fantasy(stats):
    if not stats: return 0.0
    try:
        if stats.get('fantasy_points'): return float(stats.get('fantasy_points'))
        p_yds = float(stats.get('passing_yards', 0) or 0)
        p_tds = float(stats.get('passing_tds', 0) or 0)
        ints = float(stats.get('interceptions', 0) or 0)
        r_yds = float(stats.get('rushing_yards', 0) or 0)
        r_tds = float(stats.get('rushing_tds', 0) or 0)
        rec_yds = float(stats.get('receiving_yards', 0) or 0)
        rec_tds = float(stats.get('receiving_tds', 0) or 0)
        recs = float(stats.get('receptions', 0) or 0)
        return round((p_yds/25) + (p_tds*4) - (ints*2) + (r_yds/10) + (r_tds*6) + (rec_yds/10) + (rec_tds*6) + recs, 2)
    except:
        return 0.0

class RetrievalEngine:
    def __init__(self, db_session):
        self.db = db_session

    def get_rankings(self, position=None, metric="fantasy_points", limit=5):
        """Get a single list of leaders (e.g. Top 5 QBs)."""
        sort_col = metric if metric in ["passing_yards", "rushing_yards", "receiving_yards"] else "fantasy_points"
        pos_filter = f"AND p.position = '{position}'" if position else ""
        
        sql = text(f"""
            SELECT p.name, p.team_id, p.gsis_id, s.*
            FROM season_stats s
            JOIN players p ON s.gsis_id = p.gsis_id
            WHERE s.season = 2025 {pos_filter}
            ORDER BY s.{sort_col} DESC NULLS LAST
            LIMIT :limit
        """)
        results = self.db.execute(sql, {"limit": limit}).mappings().all()
        return [self._format_player(r, sort_col) for r in results]

    def get_draft_board(self):
        """Get the full 3-category draft board (Day 11 logic)."""
        # Top 3 QBs
        qbs = self.get_rankings(position="QB", metric="fantasy_points", limit=3)
        # Top 3 RBs
        rbs = self.get_rankings(position="RB", metric="fantasy_points", limit=3)
        # Top 3 WRs/TEs (Combined logic for retrieval simplicity, or just WR)
        # For simplicity, we'll just grab WRs to keep tables clean
        wrs = self.get_rankings(position="WR", metric="fantasy_points", limit=3)
        
        return {
            "qbs": qbs,
            "rbs": rbs,
            "wrs": wrs
        }

    def get_player_stats(self, name):
        sql_p = text("SELECT * FROM players WHERE name ILIKE :name LIMIT 1")
        p = self.db.execute(sql_p, {"name": f"%{name}%"}).mappings().first()
        if not p: return None
        
        pid = p.get('gsis_id') or p.get('player_id')
        sql_s = text("SELECT * FROM season_stats WHERE gsis_id = :pid AND season = 2025")
        s = self.db.execute(sql_s, {"pid": pid}).mappings().first()
        
        stats = dict(s) if s else {}
        return {
            "info": dict(p),
            "stats": stats,
            "fantasy": calculate_fantasy(stats)
        }

    def _format_player(self, row, sort_col):
        return {
            "name": row['name'],
            "team": row['team_id'],
            "val": row[sort_col],
            "fantasy": calculate_fantasy(dict(row)),
            "player_id": row['gsis_id']
        }