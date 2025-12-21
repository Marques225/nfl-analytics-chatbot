import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Container } from '@mui/material'; // cleaned up unused imports
import ChatPage from './pages/ChatPage';
import DashboardPage from './pages/DashboardPage';
import PlayerPage from './pages/PlayerPage';
import Navbar from './components/Navbar'; // <--- We use this now!

function App() {
  return (
    <Router>
      {/* 1. The Navigation Bar (Includes Search Bar) */}
      <Navbar />

      {/* 2. The Page Content */}
      <Container style={{ marginTop: '20px' }}>
        <Routes>
          {/* Home is Chat */}
          <Route path="/" element={<ChatPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          
          {/* CRITICAL FIX: Matches the links from SearchBar and Chat */}
          <Route path="/players/:playerId" element={<PlayerPage />} /> 
        </Routes>
      </Container>
    </Router>
  );
}

export default App;