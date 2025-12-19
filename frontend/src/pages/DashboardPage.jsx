import React, { useEffect, useState } from 'react';
import { Container, Typography, Paper, Table, TableBody, TableCell, TableHead, TableRow, Grid, CircularProgress, Alert } from '@mui/material';
import apiClient from '../api/client';

const DashboardPage = () => {
    const [leaders, setLeaders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // 1. Fetch Real Data when page loads
    useEffect(() => {
        const fetchData = async () => {
            try {
                // We ask for "Top 5 Teams by Total Offense" (from Day 9)
                const response = await apiClient.get('/teams/leaders/offense?season=2024&metric=off_total_yards&limit=5');
                setLeaders(response.data);
                setLoading(false);
            } catch (err) {
                console.error("API Error:", err);
                setError("Failed to connect to the NFL Brain 🧠");
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    return (
        <Container maxWidth="lg" style={{ marginTop: '20px' }}>
            <Typography variant="h4" gutterBottom>
                NFL Analytics Dashboard 📊
            </Typography>

            {/* Error Message */}
            {error && <Alert severity="error">{error}</Alert>}

            {/* Loading Spinner */}
            {loading && <CircularProgress />}

            {/* Data Table */}
            {!loading && !error && (
                <Grid container spacing={3}>
                    <Grid item xs={12} md={8}>
                        <Paper elevation={3} style={{ padding: '20px' }}>
                            <Typography variant="h6" gutterBottom>
                                Top 5 Offenses (2024)
                            </Typography>
                            <Table>
                                <TableHead>
                                    <TableRow style={{ backgroundColor: '#f5f5f5' }}>
                                        <TableCell><b>Rank</b></TableCell>
                                        <TableCell><b>Team</b></TableCell>
                                        <TableCell align="right"><b>Total Yards</b></TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {leaders.map((row) => (
                                        <TableRow key={row.rank}>
                                            <TableCell>{row.rank}</TableCell>
                                            <TableCell>{row.team}</TableCell>
                                            <TableCell align="right">{row.value}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </Paper>
                    </Grid>
                </Grid>
            )}
        </Container>
    );
};

export default DashboardPage;