import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { fetchFindings } from '../services/findings';

interface Finding {
    id: string;
    title: string;
    type: string;
    severity: string;
    description: string;
    timestamp: string;
}

interface FindingsState {
    findings: Finding[];
    loading: boolean;
    error: string | null;
}

const initialState: FindingsState = {
    findings: [],
    loading: false,
    error: null,
};

export const loadFindings = createAsyncThunk('findings/loadFindings', async () => {
    const response = await fetchFindings();
    return response.data;
});

const findingsSlice = createSlice({
    name: 'findings',
    initialState,
    reducers: {
        clearFindings(state) {
            state.findings = [];
            state.error = null;
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(loadFindings.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(loadFindings.fulfilled, (state, action) => {
                state.loading = false;
                state.findings = action.payload;
            })
            .addCase(loadFindings.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to load findings';
            });
    },
});

export const { clearFindings } = findingsSlice.actions;

export default findingsSlice.reducer;