import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, Typography, CircularProgress, Grid, Avatar, Chip } from '@mui/material';
import PlayerAnalytics from '../components/PlayerAnalytics';

const PlayerPage = () => {
  const { playerId } = useParams();
  const [playerData, setPlayerData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/players/${playerId}`)
      .then((res) => res.json())
      .then((data) => {
        setPlayerData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching player:", err);
        setLoading(false);
      });
  }, [playerId]);

  if (loading) return <CircularProgress style={{ display: 'block', margin: '20px auto' }} />;
  if (!playerData) return <Typography variant="h5" align="center">Player not found</Typography>;

  const { player_info, season_stats, comparison } = playerData;
  const analyticsData = { ...player_info, comparison };

  return (
    <div style={{ paddingBottom: '40px' }}>
      {/* 1. HEADER SECTION */}
      <Card style={{ marginBottom: '20px', backgroundColor: '#1e293b', color: 'white' }}>
        <CardContent style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <Avatar 
            src={player_info.headshot_url} 
            alt={player_info.name}
            sx={{ width: 100, height: 100, border: '3px solid #6366f1' }}
          />
          <div>
            <Typography variant="h3" style={{ fontWeight: 'bold' }}>{player_info.name}</Typography>
            <Typography variant="h6" style={{ color: '#94a3b8' }}>
              {player_info.position} • {player_info.team_id}
            </Typography>
          </div>
        </CardContent>
      </Card>

      {/* 2. ANALYTICS & PREDICTION */}
      <PlayerAnalytics player={analyticsData} />

      {/* 3. SEASON STATS HISTORY */}
      <Typography variant="h5" style={{ margin: '30px 0 15px', fontWeight: 'bold' }}>
        Season History
      </Typography>
      
      <Grid container spacing={2}>
        {season_stats.map((season) => {
          // SAFETY CALCULATIONS
          const p_tds = Number(season.passing_tds || 0);
          const r_tds = Number(season.rushing_tds || 0);
          const rec_tds = Number(season.receiving_tds || 0);
          const total_tds = p_tds + r_tds + rec_tds;

          return (
            <Grid item xs={12} md={4} key={season.season}>
              <Card variant="outlined" style={{ borderColor: season.season === 2025 ? '#6366f1' : '#e2e8f0' }}>
                <CardContent>
                  <Typography variant="h6" color="primary" gutterBottom>
                    {season.season} Season
                    {season.season === 2025 && <Chip label="Current" size="small" color="primary" style={{ marginLeft: 10 }} />}
                  </Typography>
                  
                  {/* THE FIX: A Clean 3-Row Grid that shows EVERYTHING */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.9rem' }}>
                    
                    {/* Row 1: Passing & TDs */}
                    <div><strong>Pass:</strong> {season.passing_yards} yds</div>
                    <div><strong>Total TDs:</strong> {total_tds}</div>

                    {/* Row 2: Rushing & Receiving (ALWAYS SHOW BOTH) */}
                    <div><strong>Rush:</strong> {season.rushing_yards} yds</div>
                    <div><strong>Rec:</strong> {season.receiving_yards} yds</div>
                    
                    {/* Row 3: Fantasy Points (Spanning full width for emphasis) */}
                    <div style={{ gridColumn: 'span 2', marginTop: '8px', borderTop: '1px solid #f1f5f9', paddingTop: '8px', fontWeight: 'bold' }}>
                      Fantasy Pts: {season.fantasy_points}
                    </div>

                  </div>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </div>
  );
};

export default PlayerPage;