import React from 'react';
import { Paper, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';

const ComparisonCard = ({ data }) => {
    // data contains: { player, 2024, 2025 }
    if (!data || !data['2024'] || !data['2025']) return null;

    const stats = Object.keys(data['2025']).filter(key => 
        key !== "season" && key !== "player_id" && key !== "team_id" && typeof data['2025'][key] === 'number'
    );

    return (
        <Paper elevation={3} style={{ marginTop: '10px', padding: '10px', maxWidth: '400px' }}>
            <Typography variant="h6" align="center" style={{ marginBottom: '10px' }}>
                {data.player.name} (2024 vs 2025)
            </Typography>
            <TableContainer>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell><b>Stat</b></TableCell>
                            <TableCell align="right"><b>2024</b></TableCell>
                            <TableCell align="right"><b>2025</b></TableCell>
                            <TableCell align="right"><b>Diff</b></TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {stats.slice(0, 5).map((stat) => { // Show top 5 stats
                            const val1 = data['2024'][stat] || 0;
                            const val2 = data['2025'][stat] || 0;
                            const diff = val2 - val1;
                            return (
                                <TableRow key={stat}>
                                    <TableCell style={{ textTransform: 'capitalize' }}>{stat.replace(/_/g, ' ')}</TableCell>
                                    <TableCell align="right">{val1}</TableCell>
                                    <TableCell align="right">{val2}</TableCell>
                                    <TableCell align="right" style={{ color: diff >= 0 ? 'green' : 'red' }}>
                                        {diff > 0 ? '+' : ''}{diff}
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            </TableContainer>
        </Paper>
    );
};

export default ComparisonCard;