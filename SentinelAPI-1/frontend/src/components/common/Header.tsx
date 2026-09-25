import React from 'react';

const Header: React.FC = () => {
    return (
        <header className="header">
            <h1>SentinelAPI: Zero-Trust API Vulnerability Scanner</h1>
            <nav>
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/scans">Scans</a></li>
                    <li><a href="/reports">Reports</a></li>
                    <li><a href="/about">About</a></li>
                </ul>
            </nav>
        </header>
    );
};

export default Header;