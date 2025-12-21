import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link } from 'react-router-dom';
import PlayerSearch from './PlayerSearch'; // <--- UPDATED IMPORT to match your filename

const Navbar = () => {
    return (
        <AppBar position="static">
            <Toolbar>
                {/* 1. Logo / Title */}
                <Typography variant="h6" component={Link} to="/" style={{ textDecoration: 'none', color: 'white', marginRight: '20px' }}>
                    NFL Bot 🤖
                </Typography>

                {/* 2. Navigation Links */}
                <Box sx={{ flexGrow: 1, display: 'flex', gap: 2 }}>
                    <Button color="inherit" component={Link} to="/">Chat</Button>
                    <Button color="inherit" component={Link} to="/dashboard">Dashboard</Button>
                </Box>

                {/* 3. The Search Bar (Right Side) */}
                {/* We use the imported component here */}
                <PlayerSearch />
            </Toolbar>
        </AppBar>
    );
};

export default Navbar;