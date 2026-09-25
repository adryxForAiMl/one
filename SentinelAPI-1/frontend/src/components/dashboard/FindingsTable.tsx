import React from 'react';

interface Finding {
    id: string;
    title: string;
    severity: string;
    status: string;
    timestamp: string;
    description: string;
    remediation: string;
}

interface FindingsTableProps {
    findings: Finding[];
}

const FindingsTable: React.FC<FindingsTableProps> = ({ findings }) => {
    return (
        <div>
            <h2>Findings</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Severity</th>
                        <th>Status</th>
                        <th>Timestamp</th>
                        <th>Description</th>
                        <th>Remediation</th>
                    </tr>
                </thead>
                <tbody>
                    {findings.map(finding => (
                        <tr key={finding.id}>
                            <td>{finding.id}</td>
                            <td>{finding.title}</td>
                            <td>{finding.severity}</td>
                            <td>{finding.status}</td>
                            <td>{finding.timestamp}</td>
                            <td>{finding.description}</td>
                            <td>{finding.remediation}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default FindingsTable;