import React, { useState } from 'react';
import { 
    Container, TextField, Button, Paper, Typography, Box, List, ListItem, ListItemText 
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PlayerSearch from '../components/PlayerSearch';

const ChatPage = () => {
    // 1. STATE: This memory holds the chat history and current input
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState([
        { sender: "bot", text: "Hello! I am your NFL Analytics Assistant. Ask me about players, teams, or stats! 🏈" }
    ]);

    // 2. FUNCTION: What happens when you click "Send"
    const handleSend = () => {
        if (!input.trim()) return; // Don't send empty messages

        // Add User Message
        const newMessages = [...messages, { sender: "user", text: input }];
        setMessages(newMessages);

        // Clear Input box
        setInput("");

        // Simulate Bot Response (We will connect to Real Backend later)
        setTimeout(() => {
            setMessages(prev => [...prev, { sender: "bot", text: "I'm still learning, but I heard you! 🤖" }]);
        }, 1000);
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
                                    maxWidth: '70%'
                                }}>
                                    <ListItemText primary={msg.text} />
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