import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { fetchScans } from '../services/scans';

interface Scan {
    id: string;
    name: string;
    status: string;
    createdAt: string;
}

interface ScansState {
    scans: Scan[];
    loading: boolean;
    error: string | null;
}

const initialState: ScansState = {
    scans: [],
    loading: false,
    error: null,
};

export const loadScans = createAsyncThunk('scans/loadScans', async () => {
    const response = await fetchScans();
    return response.data;
});

const scansSlice = createSlice({
    name: 'scans',
    initialState,
    reducers: {
        clearScans(state) {
            state.scans = [];
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(loadScans.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(loadScans.fulfilled, (state, action) => {
                state.loading = false;
                state.scans = action.payload;
            })
            .addCase(loadScans.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to load scans';
            });
    },
});

export const { clearScans } = scansSlice.actions;

export default scansSlice.reducer;