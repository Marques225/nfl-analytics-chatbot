import React, { useState } from 'react';
import { TextField, List, ListItem, ListItemText, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';

const PlayerSearch = () => {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const navigate = useNavigate();

    const handleSearch = async (e) => {
        const value = e.target.value;
        setQuery(value);

        if (value.length > 2) {
            try {
                // Calls the NEW backend search endpoint
                const res = await apiClient.get(`/players/?search=${value}&limit=5`);
                setResults(res.data);
            } catch (err) {
                console.error("Search failed", err);
            }
        } else {
            setResults([]);
        }
    };

    return (
        <div style={{ position: 'relative', marginBottom: '15px' }}>
            <TextField 
                fullWidth 
                label="Search Player Database..." 
                variant="outlined" 
                value={query} 
                onChange={handleSearch}
            />
            {results.length > 0 && (
                <Paper style={{ position: 'absolute', width: '100%', zIndex: 10, maxHeight: '200px', overflow: 'auto' }}>
                    <List>
                        {results.map((p) => (
                            <ListItem 
                                button 
                                key={p.player_id} 
                                onClick={() => navigate(`/player/${p.player_id}`)}
                            >
                                <ListItemText primary={p.name} secondary={`${p.position} - ${p.team_id}`} />
                            </ListItem>
                        ))}
                    </List>
                </Paper>
            )}
        </div>
    );
};

export default PlayerSearch;