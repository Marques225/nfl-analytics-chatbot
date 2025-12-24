import React, { useState } from 'react';
import { 
  Container, TextField, Button, Paper, Typography, Box, 
  Table, TableBody, TableCell, TableHead, TableRow, Grid 
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PersonIcon from '@mui/icons-material/Person';
import AdsClickIcon from '@mui/icons-material/AdsClick';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
// IMPORT THE COMPARISON CARD
import ComparisonCard from '../components/ComparisonCard'; 

const ChatPage = () => {
    const navigate = useNavigate();
    const [messages, setMessages] = useState([
        { sender: 'bot', text: "Hello! I am your NFL Analytics Assistant. Ask 'Who should I draft?' to see the 2025 Fantasy Leaders! 🏈" }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSend = async (textToSend = input) => {
        if (!textToSend.trim()) return;

        const userMsg = { sender: 'user', text: textToSend };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const response = await apiClient.post('/chat/', { message: textToSend });
            const botMsg = { 
                sender: 'bot', 
                text: response.data.text || response.data.response,
                data: response.data.data 
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            setMessages(prev => [...prev, { sender: 'bot', text: "Sorry, I couldn't reach the brain. 🧠" }]);
        } finally {
            setLoading(false);
        }
    };

    const handlePlayerClick = (playerId) => {
        if (playerId) navigate(`/players/${playerId}`);
    };

    // --- SUB-COMPONENT FOR DRAFT TABLES ---
    const LeaderTable = ({ title, players, icon }) => (
        <Paper elevation={2} sx={{ mt: 1, mb: 2, overflow: 'hidden' }}>
            <Box sx={{ bgcolor: '#e3f2fd', p: 1, fontWeight: 'bold', color: '#1565c0' }}>{icon} {title}</Box>
            <Table size="small">
                <TableHead><TableRow><TableCell>Name</TableCell><TableCell align="right">FPts</TableCell></TableRow></TableHead>
                <TableBody>
                    {players.map((p, i) => (
                        <TableRow key={i} hover style={{ cursor: 'pointer' }} onClick={() => handlePlayerClick(p.player_id)}>
                            <TableCell component="th" scope="row" sx={{ fontSize: '0.9rem', color: '#1976d2', textDecoration: 'underline' }}>
                                {p.name} <span style={{color:'#666', fontSize:'0.75rem'}}>({p.team})</span>
                            </TableCell>
                            <TableCell align="right" sx={{ fontWeight: 'bold' }}>{p.fantasy}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </Paper>
    );

    return (
        <Container maxWidth="md" sx={{ mt: 4, height: '80vh', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h4" gutterBottom>Chat Room</Typography>
            <Paper elevation={3} sx={{ flex: 1, p: 2, overflowY: 'auto', mb: 2, bgcolor: '#fafafa' }}>
                {messages.map((msg, index) => (
                    <Box key={index} sx={{ display: 'flex', justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start', mb: 2 }}>
                        <Box sx={{ maxWidth: '90%', p: 2, borderRadius: 2, bgcolor: msg.sender === 'user' ? '#1976d2' : '#ffffff', color: msg.sender === 'user' ? '#fff' : '#000', boxShadow: 1 }}>
                            <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>{msg.text}</Typography>
                            
                            {/* 1. RENDER DRAFT BOARD (The Tables You Wanted) */}
                            {msg.data && msg.data.type === 'draft_board' && (
                                <Box sx={{ mt: 2, minWidth: '300px' }}>
                                    {msg.data.qbs && <LeaderTable title="Top QBs" icon="🎯" players={msg.data.qbs} />}
                                    {msg.data.rbs && <LeaderTable title="Top RBs" icon="🏃" players={msg.data.rbs} />}
                                    {msg.data.wrs && <LeaderTable title="Top WRs" icon="👐" players={msg.data.wrs} />}
                                </Box>
                            )}

                            {/* 2. RENDER COMPARISON CARD (The Missing Fix) */}
                            {msg.data && msg.data.type === 'comparison' && (
                                <Box sx={{ mt: 2 }}>
                                    <ComparisonCard 
                                        player1={msg.data.player1} 
                                        player2={msg.data.player2} 
                                    />
                                </Box>
                            )}

                            {/* 3. RENDER OPTIONS BUTTONS */}
                            {msg.data && msg.data.type === 'options' && (
                                <Box sx={{ mt: 2 }}>
                                    <Grid container spacing={1}>
                                        {msg.data.options.map((opt, i) => (
                                            <Grid item key={i}>
                                                <Button 
                                                    variant="outlined" size="small" startIcon={<AdsClickIcon />}
                                                    onClick={() => opt.action === 'view_player' ? handlePlayerClick(opt.id) : handleSend(opt.label)}
                                                    sx={{ textTransform: 'none', borderRadius: 4 }}
                                                >
                                                    {opt.label}
                                                </Button>
                                            </Grid>
                                        ))}
                                    </Grid>
                                </Box>
                            )}

                            {/* 4. RENDER PLAYER PROFILE BUTTON */}
                            {msg.data && msg.data.type === 'player_profile' && (
                                <Box sx={{ mt: 2 }}>
                                    <Button 
                                        variant="contained" color="secondary" size="small" startIcon={<PersonIcon />}
                                        onClick={() => handlePlayerClick(msg.data.player_id)}
                                    >
                                        View {msg.data.name}'s Full Profile
                                    </Button>
                                </Box>
                            )}
                        </Box>
                    </Box>
                ))}
                {loading && <Typography variant="caption" sx={{ ml: 2, fontStyle: 'italic' }}>Thinking...</Typography>}
            </Paper>
            
            <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField 
                    fullWidth variant="outlined" placeholder="Ask 'Who is Lamar?' or 'Who should I draft?'..." 
                    value={input} onChange={(e) => setInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSend()} 
                />
                <Button variant="contained" endIcon={<SendIcon />} onClick={() => handleSend()}>Send</Button>
            </Box>
        </Container>
    );
};

export default ChatPage;