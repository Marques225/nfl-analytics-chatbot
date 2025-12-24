import React from 'react';
import { Card, CardContent, Typography, Grid, Avatar, Box, Divider, Chip } from '@mui/material';

const StatRow = ({ label, value1, value2, highlight }) => {
    const v1 = Number(value1) || 0;
    const v2 = Number(value2) || 0;
    
    // Simple logic to bold the winner
    const win1 = v1 > v2;
    const win2 = v2 > v1;

    return (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, p: 0.5, bgcolor: highlight ? '#f5f5f5' : 'transparent', borderRadius: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: win1 ? 'bold' : 'normal', color: win1 ? 'green' : 'text.secondary', width: '30%', textAlign: 'left' }}>
                {value1}
            </Typography>
            <Typography variant="caption" sx={{ fontWeight: 'bold', color: '#666', width: '40%', textAlign: 'center', textTransform: 'uppercase' }}>
                {label}
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: win2 ? 'bold' : 'normal', color: win2 ? 'green' : 'text.secondary', width: '30%', textAlign: 'right' }}>
                {value2}
            </Typography>
        </Box>
    );
};

const PlayerColumn = ({ player }) => (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Avatar 
            src={player.headshot_url} 
            alt={player.name}
            sx={{ width: 60, height: 60, mb: 1, border: '2px solid #e0e0e0' }}
        />
        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', textAlign: 'center', lineHeight: 1.2 }}>
            {player.name}
        </Typography>
        <Typography variant="caption" color="textSecondary">
            {player.position} • {player.team_id}
        </Typography>
    </Box>
);

const ComparisonCard = ({ player1, player2 }) => {
    // Safety check: If data is missing, don't crash
    if (!player1 || !player2) return null;

    const s1 = player1.stats || {};
    const s2 = player2.stats || {};

    return (
        <Card variant="outlined" sx={{ mt: 2, bgcolor: '#fff', borderRadius: 2 }}>
            <CardContent>
                <Typography variant="overline" display="block" align="center" sx={{ color: '#999', mb: 1 }}>
                    2025 Head-to-Head
                </Typography>
                
                {/* Players Header */}
                <Grid container alignItems="center" spacing={1}>
                    <Grid item xs={5}><PlayerColumn player={player1} /></Grid>
                    <Grid item xs={2} sx={{ textAlign: 'center' }}><Typography variant="h6" color="textSecondary">VS</Typography></Grid>
                    <Grid item xs={5}><PlayerColumn player={player2} /></Grid>
                </Grid>

                <Divider sx={{ my: 2 }} />

                {/* Stats Grid */}
                <StatRow label="Fantasy Pts" value1={s1.fantasy_points} value2={s2.fantasy_points} highlight />
                <StatRow label="Pass Yds" value1={s1.passing_yards} value2={s2.passing_yards} />
                <StatRow label="Pass TDs" value1={s1.passing_tds} value2={s2.passing_tds} />
                <StatRow label="Rush Yds" value1={s1.rushing_yards} value2={s2.rushing_yards} />
                <StatRow label="Rush TDs" value1={s1.rushing_tds} value2={s2.rushing_tds} />
                <StatRow label="Rec Yds" value1={s1.receiving_yards} value2={s2.receiving_yards} />
                <StatRow label="Rec TDs" value1={s1.receiving_tds} value2={s2.receiving_tds} />

            </CardContent>
        </Card>
    );
};

export default ComparisonCard;