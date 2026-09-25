import React, { useState } from 'react';

const ScanForm: React.FC = () => {
    const [apiUrl, setApiUrl] = useState('');
    const [credentials, setCredentials] = useState('');
    const [scanResults, setScanResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleScan = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch('/api/scans', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ apiUrl, credentials }),
            });

            if (!response.ok) {
                throw new Error('Failed to initiate scan');
            }

            const data = await response.json();
            setScanResults(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h2>API Scan Form</h2>
            <form onSubmit={handleScan}>
                <div>
                    <label htmlFor="apiUrl">API URL:</label>
                    <input
                        type="url"
                        id="apiUrl"
                        value={apiUrl}
                        onChange={(e) => setApiUrl(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="credentials">Credentials:</label>
                    <input
                        type="text"
                        id="credentials"
                        value={credentials}
                        onChange={(e) => setCredentials(e.target.value)}
                        required
                    />
                </div>
                <button type="submit" disabled={loading}>
                    {loading ? 'Scanning...' : 'Start Scan'}
                </button>
            </form>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {scanResults && (
                <div>
                    <h3>Scan Results</h3>
                    <pre>{JSON.stringify(scanResults, null, 2)}</pre>
                </div>
            )}
        </div>
    );
};

export default ScanForm;