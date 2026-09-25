import React from 'react';
import './globals.css';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
        <div className="layout">
            <header>
                <h1>SentinelAPI: Zero-Trust API Vulnerability Scanner</h1>
            </header>
            <main>{children}</main>
            <footer>
                <p>&copy; {new Date().getFullYear()} SentinelAPI. All rights reserved.</p>
            </footer>
        </div>
    );
};

export default Layout;