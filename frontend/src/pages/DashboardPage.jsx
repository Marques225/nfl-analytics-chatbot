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
                // UPDATE: Changed season to 2025 to match the live data we just generated
                const response = await apiClient.get('/teams/leaders/offense?season=2025&metric=off_total_yards&limit=5');
                
                // --- SAFETY CHECK (The Fix) ---
                // We verify the data is actually an array before setting it.
                // This prevents the "map is not a function" crash.
                const data = response.data;
                
                if (Array.isArray(data)) {
                    setLeaders(data);
                } else if (data.results && Array.isArray(data.results)) {
                    // Handle case where backend wraps it in { results: [] }
                    setLeaders(data.results);
                } else {
                    console.error("Unexpected Data Format:", data);
                    setLeaders([]); 
                }
                
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
            {loading && (
                <Grid container justifyContent="center" style={{ marginTop: '50px' }}>
                    <CircularProgress />
                </Grid>
            )}

            {/* Data Table */}
            {!loading && !error && (
                <Grid container spacing={3}>
                    <Grid item xs={12} md={8}>
                        <Paper elevation={3} style={{ padding: '20px' }}>
                            <Typography variant="h6" gutterBottom>
                                🏆 Top 5 Offenses (2025)
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
                                    {leaders.length > 0 ? (
                                        leaders.map((row, index) => (
                                            <TableRow key={row.team || index}>
                                                <TableCell>{index + 1}</TableCell>
                                                <TableCell>{row.team}</TableCell>
                                                {/* Added toLocaleString() for comma formatting (e.g., 4,500) */}
                                                <TableCell align="right">
                                                    {row.value?.toLocaleString()}
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    ) : (
                                        <TableRow>
                                            <TableCell colSpan={3} align="center">
                                                No stats available for 2025 yet.
                                            </TableCell>
                                        </TableRow>
                                    )}
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