import { configureStore } from '@reduxjs/toolkit';
import scansReducer from './scansSlice';
import findingsReducer from './findingsSlice';

const store = configureStore({
  reducer: {
    scans: scansReducer,
    findings: findingsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;