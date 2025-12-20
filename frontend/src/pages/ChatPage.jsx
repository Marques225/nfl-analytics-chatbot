import apiClient from '../api/client';
import { useNavigate } from 'react-router-dom';
import React, { useState } from 'react';
import { 
    Container, TextField, Button, Paper, Typography, Box, List, ListItem, ListItemText 
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PlayerSearch from '../components/PlayerSearch';
import ComparisonCard from '../components/ComparisonCard';

const ChatPage = () => {
    // 1. STATE: This memory holds the chat history and current input
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState([
        { sender: "bot", text: "Hello! I am your NFL Analytics Assistant. Ask me about players, teams, or stats! 🏈" }
    ]);

    // ... (inside ChatPage component)
    const navigate = useNavigate(); // Hook for navigation

    const handleSend = async () => {
        if (!input.trim()) return;

        // 1. Add User Message immediately
        const userMsg = { sender: "user", text: input };
        setMessages(prev => [...prev, userMsg]);
        const currentInput = input; // Save for API call
        setInput(""); // Clear box

        try {
            // 2. Call the Backend Brain 🧠
            const response = await apiClient.post('/chat/', { message: currentInput });
            const botData = response.data;

            // 3. Handle different response types
            let botMsg = { sender: "bot", text: botData.text, type: botData.type, data: botData.data };
            
            // If it's a player card, we can add a "View Profile" button or link
            if (botData.type === "player_card") {
                botMsg.action = {
                    label: "View Full Profile",
                    link: `/player/${botData.data.player_id}`
                };
            }
            
            // If it's a comparison, we display raw text for now (we'll upgrade this in a moment)
            if (botData.type === "comparison_card") {
                 // You can add special formatting here later
            }

            setMessages(prev => [...prev, botMsg]);

        } catch (error) {
            console.error("Chat Error:", error);
            setMessages(prev => [...prev, { sender: "bot", text: "My brain is offline. Check the terminal! 🔌" }]);
        }
    };
    return (
        <Container maxWidth="md" style={{ marginTop: '20px' }}>
            <PlayerSearch />
            <Paper elevation={3} style={{ padding: '20px', height: '80vh', display: 'flex', flexDirection: 'column' }}>
                
                {/* Header */}
                <Typography variant="h5" gutterBottom>
                    Chat Room
                </Typography>

                {/* Message Display Area (The Scrollable Box) */}
                <Box style={{ flexGrow: 1, overflowY: 'auto', marginBottom: '20px', border: '1px solid #eee', padding: '10px' }}>
                    <List>
                        {messages.map((msg, index) => (
                            <ListItem key={index} style={{ justifyContent: msg.sender === "user" ? "flex-end" : "flex-start" }}>
                                <Paper style={{ 
                                    padding: '10px 15px', 
                                    backgroundColor: msg.sender === "user" ? "#1976d2" : "#f1f1f1", 
                                    color: msg.sender === "user" ? "#fff" : "#000",
                                    borderRadius: '15px',
                                    maxWidth: '80%'
                                }}>
                                    {/* 1. Text Message */}
                                    <ListItemText primary={msg.text} />
                                    
                                    {/* 2. Action Button (Profile) */}
                                    {msg.action && (
                                        <Button 
                                            variant="contained" 
                                            size="small" 
                                            style={{ marginTop: '10px', backgroundColor: '#fff', color: '#1976d2' }}
                                            onClick={() => navigate(msg.action.link)}
                                        >
                                            {msg.action.label}
                                        </Button>
                                    )}

                                    {/* 3. Comparison Card (NEW) */}
                                    {msg.type === "comparison_card" && (
                                        <ComparisonCard data={msg.data} />
                                    )}

                                    {/* 4. Draft List (NEW) */}
                                    {msg.type === "draft_card" && (
                                        <div style={{ marginTop: '10px', background: 'white', padding: '10px', borderRadius: '5px', color: 'black' }}>
                                            {msg.data.map((p, i) => (
                                                <div key={i} style={{ borderBottom: '1px solid #eee', padding: '4px 0' }}>
                                                    <b>#{i+1} {p.name}</b> ({p.team_id}) - {p.value} yds
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </Paper>
                            </ListItem>
                        ))}
                    </List>
                </Box>

                {/* Input Area */}
                <Box style={{ display: 'flex', gap: '10px' }}>
                    <TextField 
                        fullWidth 
                        variant="outlined" 
                        placeholder="Ask about Lamar Jackson..." 
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    />
                    <Button variant="contained" color="primary" endIcon={<SendIcon />} onClick={handleSend}>
                        Send
                    </Button>
                </Box>
            </Paper>
        </Container>
    );
};

export default ChatPage;