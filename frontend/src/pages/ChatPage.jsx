import React, { useState, useRef, useEffect } from 'react';
import { 
  Container, TextField, Button, Paper, Typography, Box, 
  CircularProgress, Card, CardContent, Grid, AppBar, Toolbar, Link, 
  Table, TableBody, TableCell, TableHead, TableRow
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PersonIcon from '@mui/icons-material/Person';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows'; 
import LogoutIcon from '@mui/icons-material/Logout';
import LockIcon from '@mui/icons-material/Lock';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { createClient } from '@supabase/supabase-js';
import ComparisonCard from '../components/ComparisonCard'; // RESTORED IMPORT

// --- CONFIGURATION ---
const SUPABASE_URL = "https://recqdfjmviwhqqwapfcg.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlY3FkZmptdml3aHFxd2FwZmNnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUzODgwNzQsImV4cCI6MjA4MDk2NDA3NH0.lIJgHJjzi0Uhb1ZlJc7IxNjvTTdPgN48Eq-V_CUUMnA";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const ChatPage = () => {
    const navigate = useNavigate();
    const messagesEndRef = useRef(null);

    // --- STATE ---
    const [session, setSession] = useState(null);
    const [authLoading, setAuthLoading] = useState(true);
    const [isSignUpMode, setIsSignUpMode] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [fullName, setFullName] = useState("");

    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);

    // --- AUTH LOGIC (Same as before) ---
    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
            setAuthLoading(false);
            if (session) {
                const name = session.user.user_metadata.full_name || session.user.email;
                setMessages([{ sender: 'bot', text: `Welcome back, ${name}!` }]);
            }
        });
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
        });
        return () => subscription.unsubscribe();
    }, []);

    const handleLogin = async () => { /* ... same logic ... */ 
        setAuthLoading(true);
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) alert(error.message);
        setAuthLoading(false);
    };

    const handleSignUp = async () => { /* ... same logic ... */
        if (!email || !password || !fullName) { alert("Please fill in all fields."); return; }
        setAuthLoading(true);
        const { data, error } = await supabase.auth.signUp({ 
            email, password, options: { data: { full_name: fullName } }
        });
        if (error) alert(error.message);
        else if (!data.session) { alert("Account created! Check email."); setIsSignUpMode(false); }
        setAuthLoading(false);
    };

    const handleLogout = async () => { await supabase.auth.signOut(); setMessages([]); };

    // --- CHAT LOGIC ---
    const handleSend = async (textToSend = input) => {
        if (!textToSend.trim()) return;
        if (!session) { alert("You must be logged in to chat."); return; }

        const userMsg = { sender: 'user', text: textToSend };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const token = session.access_token;
            const response = await apiClient.post('/chat/', 
                { message: textToSend }, 
                { headers: { Authorization: `Bearer ${token}` } }
            );

            const botMsg = { 
                sender: 'bot', 
                text: response.data.text || response.data.response,
                data: response.data.data 
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            if (error.response && error.response.status === 401) {
                setMessages(prev => [...prev, { sender: 'bot', text: "🔒 Session expired." }]);
            } else {
                setMessages(prev => [...prev, { sender: 'bot', text: "Error connecting to server." }]);
            }
        } finally {
            setLoading(false);
        }
    };
    
    useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

    // --- UI COMPONENTS (RESTORED FEATURES) ---

    // 1. RESTORED DETAILED TRADE CARD
    const TradeCard = ({ data }) => {
        const pGive = data.player1;
        const pReceive = data.player2;
        const diff = data.diff;
        
        let bgColor = '#e8f5e9'; let textColor = '#2e7d32'; let label = "✅ Win"; let valueText = `${diff > 0 ? "+" : ""}${diff.toFixed(1)} Net Value`;
        if (data.verdict === "LOSS") { bgColor = '#ffebee'; textColor = '#c62828'; label = "⚠️ Bad Trade"; } 
        else if (data.verdict === "FAIR") { bgColor = '#f5f5f5'; textColor = '#616161'; label = "⚖️ Fair Trade"; } 
        else if (data.verdict === "MISMATCH") { bgColor = '#fff3e0'; textColor = '#e65100'; label = "🚫 Invalid Trade"; valueText = "Position Mismatch"; }

        return (
            <Card sx={{ mt: 2, border: `1px solid ${textColor}`, bgcolor: '#fff' }}>
                <CardContent>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', color: '#1565c0' }}>
                        <CompareArrowsIcon sx={{ mr: 1 }} /> Trade Analysis
                    </Typography>
                    <Grid container spacing={2} sx={{ mt: 1, textAlign: 'center', alignItems:'center' }}>
                        <Grid item xs={5}>
                            <Typography variant="caption" color="text.secondary">YOU GIVE</Typography>
                            <Typography variant="subtitle2" fontWeight="bold">{pGive.name}</Typography>
                            <Typography variant="body2">{pGive.fantasy_points} pts</Typography> {/* RESTORED POINTS */}
                        </Grid>
                        <Grid item xs={2}>➡️</Grid>
                        <Grid item xs={5}>
                            <Typography variant="caption" color="text.secondary">YOU GET</Typography>
                            <Typography variant="subtitle2" fontWeight="bold">{pReceive.name}</Typography>
                            <Typography variant="body2">{pReceive.fantasy_points} pts</Typography> {/* RESTORED POINTS */}
                        </Grid>
                    </Grid>
                    <Box sx={{ mt: 2, p: 1, bgcolor: bgColor, borderRadius: 1, textAlign: 'center' }}>
                         <Typography variant="body1" sx={{ fontWeight: 'bold', color: textColor }}>{valueText}</Typography>
                         <Typography variant="caption" fontWeight="bold" color={textColor}>{label}</Typography>
                    </Box>
                </CardContent>
            </Card>
        );
    };

    // 2. RESTORED CLICKABLE LEADER TABLE
    const LeaderTable = ({ title, players }) => (
        <Paper elevation={2} sx={{ mt: 1, mb: 2, overflow: 'hidden' }}>
            <Box sx={{ bgcolor: '#e3f2fd', p: 1, fontWeight: 'bold', color: '#1565c0' }}>{title}</Box>
            <Table size="small">
                <TableHead><TableRow><TableCell>Name</TableCell><TableCell align="right">FPts</TableCell></TableRow></TableHead>
                <TableBody>
                    {players.map((p, i) => (
                        <TableRow key={i} hover style={{ cursor: 'pointer' }} onClick={() => navigate(`/players/${p.player_id}`)}> {/* RESTORED CLICK */}
                            <TableCell component="th" scope="row" sx={{ fontSize: '0.9rem', color: '#1976d2', textDecoration: 'underline' }}>
                                {p.name}
                            </TableCell>
                            <TableCell align="right" sx={{ fontWeight: 'bold' }}>{p.fantasy}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </Paper>
    );

    // LOGIN UI
    if (!session && !authLoading) {
        return (
            <Container maxWidth="xs" sx={{ mt: 10 }}>
                <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
                    <LockIcon color="primary" sx={{ fontSize: 40, mb: 2 }} />
                    <Typography variant="h5" gutterBottom>{isSignUpMode ? "Create Account" : "Login"}</Typography>
                    {isSignUpMode && <TextField fullWidth label="Full Name" margin="normal" value={fullName} onChange={(e) => setFullName(e.target.value)} />}
                    <TextField fullWidth label="Email" margin="normal" value={email} onChange={(e) => setEmail(e.target.value)} />
                    <TextField fullWidth label="Password" type="password" margin="normal" value={password} onChange={(e) => setPassword(e.target.value)} />
                    <Box sx={{ mt: 3 }}><Button fullWidth variant="contained" size="large" onClick={isSignUpMode ? handleSignUp : handleLogin}>{isSignUpMode ? "Sign Up" : "Login"}</Button></Box>
                    <Box sx={{ mt: 2 }}><Link component="button" variant="body2" onClick={() => { setIsSignUpMode(!isSignUpMode); setEmail(""); setPassword(""); }}>{isSignUpMode ? "Already have an account? Login" : "Don't have an account? Sign Up"}</Link></Box>
                </Paper>
            </Container>
        );
    }

    // MAIN UI
    return (
        <Container maxWidth="md" sx={{ mt: 0, height: '90vh', display: 'flex', flexDirection: 'column' }}>
            <AppBar position="static" color="transparent" elevation={0}>
                <Toolbar sx={{ justifyContent: 'space-between', px: 0 }}>
                    <Typography variant="h5" color="primary" fontWeight="bold">Agentic Chat</Typography>
                    <Button startIcon={<LogoutIcon />} onClick={handleLogout} color="error">Logout</Button>
                </Toolbar>
            </AppBar>

            <Paper elevation={3} sx={{ flex: 1, p: 2, overflowY: 'auto', mb: 2, bgcolor: '#fafafa' }}>
                {messages.map((msg, index) => (
                    <Box key={index} sx={{ display: 'flex', justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start', mb: 2 }}>
                        <Box sx={{ maxWidth: '85%', p: 2, borderRadius: 2, bgcolor: msg.sender === 'user' ? '#1976d2' : '#ffffff', color: msg.sender === 'user' ? '#fff' : '#000', boxShadow: 1 }}>
                            <Typography variant="body1">{msg.text}</Typography>
                            
                            {/* RENDERERS */}
                            {msg.data && msg.data.type === 'trade_analysis' && <TradeCard data={msg.data} />}
                            
                            {msg.data && msg.data.type === 'comparison' && ( 
                                <Box sx={{ mt: 2 }}><ComparisonCard player1={msg.data.player1} player2={msg.data.player2} /></Box> // RESTORED COMPARISON
                            )}

                            {msg.data && msg.data.type === 'draft_board' && (
                                <Box sx={{ mt: 2 }}>
                                    {msg.data.qbs && <LeaderTable title="Top QBs" players={msg.data.qbs} />}
                                    {msg.data.rbs && <LeaderTable title="Top RBs" players={msg.data.rbs} />}
                                    {msg.data.wrs && <LeaderTable title="Top WRs" players={msg.data.wrs} />}
                                </Box>
                            )}
                            
                            {msg.data && msg.data.type === 'player_profile' && (
                                <Button variant="contained" color="secondary" size="small" startIcon={<PersonIcon />} onClick={() => navigate(`/players/${msg.data.player_id}`)} sx={{ mt: 1 }}>
                                    View {msg.data.name}'s Full Profile {/* RESTORED TEXT */}
                                </Button>
                            )}
                        </Box>
                    </Box>
                ))}
                {loading && <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}><CircularProgress size={20} /><Typography variant="caption" sx={{ ml: 1 }}>Thinking...</Typography></Box>}
                <div ref={messagesEndRef} />
            </Paper>
            
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField fullWidth variant="outlined" placeholder="Try 'Trade Lamar for CMC'..." value={input} onChange={(e) => setInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSend()} />
                <Button variant="contained" endIcon={<SendIcon />} onClick={() => handleSend()}>Send</Button>
            </Box>
        </Container>
    );
};

export default ChatPage;

