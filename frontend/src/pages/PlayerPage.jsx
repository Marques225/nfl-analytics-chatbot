import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Container, Typography, Paper, Grid, CircularProgress, Alert, Card, CardContent } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import apiClient from '../api/client';

const PlayerPage = () => {
    const { player_id } = useParams(); // Get ID from URL
    const [player, setPlayer] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPlayer = async () => {
            try {
                const response = await apiClient.get(`/players/${player_id}`);
                setPlayer(response.data);
                setLoading(false);
            } catch (err) {
                setError("Could not load player data.");
                setLoading(false);
            }
        };
        fetchPlayer();
    }, [player_id]);

    if (loading) return <CircularProgress style={{ margin: '20px' }} />;
    if (error) return <Alert severity="error">{error}</Alert>;

    // Determine which stat to graph based on position (naive check)
    const position = player.player_info.position;
    let dataKey = "passing_yards"; // default
    if (position === "RB") dataKey = "rushing_yards";
    if (position === "WR" || position === "TE") dataKey = "receiving_yards";

    return (
        <Container style={{ marginTop: '20px' }}>
            {/* Header Bio */}
            <Paper elevation={3} style={{ padding: '20px', marginBottom: '20px', borderLeft: '5px solid #1976d2' }}>
                <Typography variant="h4">{player.player_info.name}</Typography>
                <Typography variant="subtitle1" color="textSecondary">
                    Position: {player.player_info.position} | ID: {player.player_info.player_id}
                </Typography>
            </Paper>

            {/* Sparkline Chart */}
            <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Performance Trend ({dataKey.replace('_', ' ')}) 📈
                            </Typography>
                            <div style={{ height: 300, width: '100%' }}>
                                <ResponsiveContainer>
                                    <LineChart data={player.season_stats}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="season" />
                                        <YAxis />
                                        <Tooltip />
                                        <Line type="monotone" dataKey={dataKey} stroke="#1976d2" strokeWidth={3} dot={{ r: 5 }} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Stat Table (Mini Results Panel) */}
                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6">Season History</Typography>
                            {player.season_stats.map((s) => (
                                <div key={s.season} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #eee' }}>
                                    <span>{s.season}</span>
                                    <b>{s[dataKey]} yds</b>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Container>
    );
};

export default PlayerPage;