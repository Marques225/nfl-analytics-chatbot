import axios from 'axios';

// Create a configured instance of axios
const apiClient = axios.create({
    baseURL: 'http://localhost:8000', // Matches your FastAPI backend port
    headers: {
        'Content-Type': 'application/json',
    },
});

export default apiClient;