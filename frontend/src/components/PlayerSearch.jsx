import React, { useState, useEffect } from 'react';
import { TextField, Autocomplete, CircularProgress, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import SearchIcon from '@mui/icons-material/Search';

const PlayerSearch = () => {
    const [open, setOpen] = useState(false);
    const [options, setOptions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [inputValue, setInputValue] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        let active = true;

        if (inputValue === '') {
            setOptions([]);
            return undefined;
        }

        const fetchPlayers = async () => {
            setLoading(true);
            try {
                // Fetch top 10 matches
                const response = await apiClient.get(`/players/?search=${inputValue}&limit=10`);
                if (active) {
                    setOptions(response.data || []);
                }
            } catch (err) {
                console.error("Search failed", err);
            } finally {
                setLoading(false);
            }
        };

        const timer = setTimeout(() => fetchPlayers(), 300);
        return () => {
            active = false;
            clearTimeout(timer);
        };
    }, [inputValue]);

    return (
        <Autocomplete
            id="nfl-player-search"
            sx={{ 
                width: 300, 
                bgcolor: 'rgba(255,255,255,0.15)', // Semi-transparent white
                borderRadius: 1,
                '&:hover': { bgcolor: 'rgba(255,255,255,0.25)' }
            }}
            open={open}
            onOpen={() => setOpen(true)}
            onClose={() => setOpen(false)}
            isOptionEqualToValue={(option, value) => option.name === value.name}
            getOptionLabel={(option) => option.name}
            options={options}
            loading={loading}
            
            // NAVIGATE ON CLICK
            onChange={(event, newValue) => {
                if (newValue) {
                    // Handle both ID types just in case
                    const pid = newValue.gsis_id || newValue.player_id;
                    if (pid) {
                        navigate(`/players/${pid}`);
                        setInputValue(""); // Clear bar after search
                    }
                }
            }}
            
            onInputChange={(event, newInputValue) => {
                setInputValue(newInputValue);
            }}
            
            renderOption={(props, option) => (
                <Box component="li" {...props} key={option.gsis_id}>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: 'bold' }}>{option.name}</span>
                        <span style={{ fontSize: '0.8rem', color: '#666' }}>
                            {option.position} - {option.team_id}
                        </span>
                    </div>
                </Box>
            )}

            renderInput={(params) => (
                <TextField
                    {...params}
                    placeholder="Search Player..."
                    variant="outlined"
                    size="small"
                    InputProps={{
                        ...params.InputProps,
                        style: { color: 'white' }, // White text for navbar
                        startAdornment: <SearchIcon sx={{ color: 'white', mr: 1 }} />,
                        endAdornment: (
                            <React.Fragment>
                                {loading ? <CircularProgress color="inherit" size={20} /> : null}
                                {params.InputProps.endAdornment}
                            </React.Fragment>
                        ),
                    }}
                />
            )}
        />
    );
};

export default PlayerSearch;