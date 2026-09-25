import httpClient from './api';

export const fetchScans = async () => {
    const response = await httpClient.get('/scans');
    return response.data;
};

export const createScan = async (scanData) => {
    const response = await httpClient.post('/scans', scanData);
    return response.data;
};

export const fetchScanById = async (scanId) => {
    const response = await httpClient.get(`/scans/${scanId}`);
    return response.data;
};

export const deleteScan = async (scanId) => {
    const response = await httpClient.delete(`/scans/${scanId}`);
    return response.data;
};