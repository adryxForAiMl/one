import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { Finding } from '../../services/findings';

const FindingsTable: React.FC = () => {
    const findings = useSelector((state: RootState) => state.findings.findings);

    return (
        <div className="findings-table">
            <h2>Findings</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Severity</th>
                        <th>Status</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {findings.map((finding: Finding) => (
                        <tr key={finding.id}>
                            <td>{finding.id}</td>
                            <td>{finding.title}</td>
                            <td>{finding.severity}</td>
                            <td>{finding.status}</td>
                            <td>{new Date(finding.timestamp).toLocaleString()}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default FindingsTable;