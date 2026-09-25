import React, { useEffect, useState } from 'react';
import { fetchFindings } from '../services/findings';
import StatsCards from '../components/dashboard/StatsCards';
import FindingsTable from '../components/dashboard/FindingsTable';
import RiskChart from '../components/dashboard/RiskChart';

const DashboardPage: React.FC = () => {
    const [findings, setFindings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadFindings = async () => {
            try {
                const data = await fetchFindings();
                setFindings(data);
            } catch (err) {
                setError('Failed to load findings');
            } finally {
                setLoading(false);
            }
        };

        loadFindings();
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>{error}</div>;
    }

    return (
        <div>
            <h1>Dashboard</h1>
            <StatsCards findings={findings} />
            <RiskChart findings={findings} />
            <FindingsTable findings={findings} />
        </div>
    );
};

export default DashboardPage;