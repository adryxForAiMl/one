import React from 'react';
import { Link } from 'react-router-dom';

const Header: React.FC = () => {
    return (
        <header className="header">
            <div className="logo">
                <Link to="/">SentinelAPI</Link>
            </div>
            <nav className="navigation">
                <ul>
                    <li>
                        <Link to="/dashboard">Dashboard</Link>
                    </li>
                    <li>
                        <Link to="/scans">Scans</Link>
                    </li>
                    <li>
                        <Link to="/findings">Findings</Link>
                    </li>
                    <li>
                        <Link to="/login">Login</Link>
                    </li>
                </ul>
            </nav>
        </header>
    );
};

export default Header;