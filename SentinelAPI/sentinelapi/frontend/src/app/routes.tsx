import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import ScansPage from './pages/ScansPage';
import FindingsPage from './pages/FindingsPage';
import LoginPage from './pages/LoginPage';

const Routes = () => {
    return (
        <Router>
            <Switch>
                <Route path="/" exact component={DashboardPage} />
                <Route path="/scans" component={ScansPage} />
                <Route path="/findings" component={FindingsPage} />
                <Route path="/login" component={LoginPage} />
            </Switch>
        </Router>
    );
};

export default Routes;