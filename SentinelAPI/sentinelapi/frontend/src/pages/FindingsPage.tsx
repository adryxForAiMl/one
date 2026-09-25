import React, { useEffect, useState } from 'react';
import { fetchFindings } from '../services/findings';
import FindingsTable from '../components/dashboard/FindingsTable';
import { Finding } from '../types';

const FindingsPage: React.FC = () => {
    const [findings, setFindings] = useState<Finding[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
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
            <h1>Findings</h1>
            <FindingsTable findings={findings} />
        </div>
    );
};

export default FindingsPage;