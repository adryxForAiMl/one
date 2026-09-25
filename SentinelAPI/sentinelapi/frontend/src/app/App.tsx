import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { AuthProvider } from './providers/AuthProvider';
import Routes from './routes';
import './styles/globals.css';

const App: React.FC = () => {
    return (
        <AuthProvider>
            <Router>
                <Routes />
            </Router>
        </AuthProvider>
    );
};

export default App;