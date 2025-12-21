import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Container, Paper, Typography, Grid, Chip, CircularProgress, Alert, Box } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import apiClient from '../api/client';

const PlayerPage = () => {
    const { playerId } = useParams(); // Grabs the ID from the URL
    const [playerData, setPlayerData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPlayer = async () => {
            try {
                // Fetch from our updated Backend
                const response = await apiClient.get(`/players/${playerId}`);
                setPlayerData(response.data);
                setLoading(false);
            } catch (err) {
                console.error("Profile Fetch Error:", err);
                setError("Could not load player data.");
                setLoading(false);
            }
        };

        if (playerId) fetchPlayer();
    }, [playerId]);

    if (loading) return (
        <Box display="flex" justifyContent="center" mt={5}>
            <CircularProgress />
        </Box>
    );

    if (error) return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
            <Alert severity="error">{error}</Alert>
        </Container>
    );

    if (!playerData) return null;

    const { player_info, season_stats } = playerData;
    
    // Sort stats so 2025 is last (for the graph)
    const graphData = [...(season_stats || [])].sort((a, b) => a.season - b.season);

    return (
        <Container maxWidth="lg" sx={{ mt: 4 }}>
            {/* HEADER SECTION */}
            <Paper elevation={3} sx={{ p: 3, mb: 4, bgcolor: '#f5f5f5' }}>
                <Grid container spacing={2} alignItems="center">
                    <Grid item>
                        <img 
                            src={player_info.headshot_url || "https://static.www.nfl.com/image/private/f_auto,q_auto/league/nfl-placeholder.png"} 
                            alt={player_info.name} 
                            style={{ width: 100, height: 100, borderRadius: '50%', border: '3px solid #1976d2' }} 
                        />
                    </Grid>
                    <Grid item>
                        <Typography variant="h3">{player_info.name}</Typography>
                        <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                            <Chip label={player_info.position} color="primary" />
                            <Chip label={player_info.team_id || "Free Agent"} variant="outlined" />
                            <Chip label={`ID: ${player_info.player_id}`} size="small" />
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            {/* STATS GRAPH SECTION */}
            <Grid container spacing={3}>
                <Grid item xs={12}>
                    <Paper elevation={2} sx={{ p: 3 }}>
                        <Typography variant="h5" gutterBottom>Career Performance (2023-2025)</Typography>
                        
                        {graphData.length > 0 ? (
                            <Box sx={{ height: 400, width: '100%' }}>
                                <ResponsiveContainer>
                                    <BarChart data={graphData}>
                                        <XAxis dataKey="season" />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        
                                        {/* Dynamic Bars based on Position */}
                                        {player_info.position === 'QB' && <Bar dataKey="passing_yards" name="Passing Yards" fill="#1976d2" />}
                                        {player_info.position === 'QB' && <Bar dataKey="passing_tds" name="TDs" fill="#ff9800" />}
                                        
                                        {(player_info.position === 'RB' || player_info.position === 'QB') && (
                                            <Bar dataKey="rushing_yards" name="Rushing Yards" fill="#4caf50" />
                                        )}
                                        
                                        {(player_info.position === 'WR' || player_info.position === 'TE' || player_info.position === 'RB') && (
                                            <Bar dataKey="receiving_yards" name="Receiving Yards" fill="#9c27b0" />
                                        )}
                                        
                                        <Bar dataKey="fantasy_points" name="Fantasy Pts" fill="#d32f2f" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </Box>
                        ) : (
                            <Alert severity="info">No stats recorded for this player yet.</Alert>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Container>
    );
};

export default PlayerPage;