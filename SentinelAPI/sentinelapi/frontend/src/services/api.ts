import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Function to handle GET requests
export const get = async (url: string, config = {}) => {
    try {
        const response = await apiClient.get(url, config);
        return response.data;
    } catch (error) {
        handleError(error);
    }
};

// Function to handle POST requests
export const post = async (url: string, data: any, config = {}) => {
    try {
        const response = await apiClient.post(url, data, config);
        return response.data;
    } catch (error) {
        handleError(error);
    }
};

// Function to handle PUT requests
export const put = async (url: string, data: any, config = {}) => {
    try {
        const response = await apiClient.put(url, data, config);
        return response.data;
    } catch (error) {
        handleError(error);
    }
};

// Function to handle DELETE requests
export const del = async (url: string, config = {}) => {
    try {
        const response = await apiClient.delete(url, config);
        return response.data;
    } catch (error) {
        handleError(error);
    }
};

// Error handling function
const handleError = (error: any) => {
    if (axios.isAxiosError(error)) {
        console.error('API Error:', error.response?.data || error.message);
    } else {
        console.error('Unexpected Error:', error);
    }
};