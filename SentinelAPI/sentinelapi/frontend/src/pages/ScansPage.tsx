import React, { useEffect, useState } from 'react';
import { fetchScans } from '../services/scans';
import ScanCard from '../components/scan/ScanCard';

const ScansPage: React.FC = () => {
    const [scans, setScans] = useState<any[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadScans = async () => {
            try {
                const response = await fetchScans();
                setScans(response);
            } catch (err) {
                setError('Failed to load scans');
            } finally {
                setLoading(false);
            }
        };

        loadScans();
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>{error}</div>;
    }

    return (
        <div>
            <h1>Scans</h1>
            <div>
                {scans.map(scan => (
                    <ScanCard key={scan.id} scan={scan} />
                ))}
            </div>
        </div>
    );
};

export default ScansPage;