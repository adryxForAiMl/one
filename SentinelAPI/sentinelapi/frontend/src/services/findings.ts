import axios from 'axios';

const API_BASE_URL = '/api/findings';

export const getFindings = async () => {
    try {
        const response = await axios.get(API_BASE_URL);
        return response.data;
    } catch (error) {
        console.error('Error fetching findings:', error);
        throw error;
    }
};

export const getFindingById = async (id: string) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/${id}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching finding with id ${id}:`, error);
        throw error;
    }
};

export const createFinding = async (findingData: any) => {
    try {
        const response = await axios.post(API_BASE_URL, findingData);
        return response.data;
    } catch (error) {
        console.error('Error creating finding:', error);
        throw error;
    }
};

export const updateFinding = async (id: string, findingData: any) => {
    try {
        const response = await axios.put(`${API_BASE_URL}/${id}`, findingData);
        return response.data;
    } catch (error) {
        console.error(`Error updating finding with id ${id}:`, error);
        throw error;
    }
};

export const deleteFinding = async (id: string) => {
    try {
        await axios.delete(`${API_BASE_URL}/${id}`);
    } catch (error) {
        console.error(`Error deleting finding with id ${id}:`, error);
        throw error;
    }
};