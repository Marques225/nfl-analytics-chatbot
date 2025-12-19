import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Container } from '@mui/material';
import ChatPage from './pages/ChatPage';
import DashboardPage from './pages/DashboardPage';
import PlayerPage from './pages/PlayerPage'; // <--- NEW IMPORT
function App() {
  return (
    <Router>
      {/* 1. The Navigation Bar */}
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" style={{ flexGrow: 1 }}>
            NFL Bot 🤖
          </Typography>
          <Button color="inherit" component={Link} to="/">Chat</Button>
          <Button color="inherit" component={Link} to="/dashboard">Dashboard</Button>
        </Toolbar>
      </AppBar>

      {/* 2. The Page Content */}
      <Container>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/player/:player_id" element={<PlayerPage />} /> 
        </Routes>
      </Container>
    </Router>
  );
}

export default App;