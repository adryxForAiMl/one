import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar: React.FC = () => {
    return (
        <div className="sidebar">
            <h2>SentinelAPI</h2>
            <nav>
                <ul>
                    <li>
                        <NavLink to="/dashboard" activeClassName="active">
                            Dashboard
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/scans" activeClassName="active">
                            Scans
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/reports" activeClassName="active">
                            Reports
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/settings" activeClassName="active">
                            Settings
                        </NavLink>
                    </li>
                </ul>
            </nav>
        </div>
    );
};

export default Sidebar;