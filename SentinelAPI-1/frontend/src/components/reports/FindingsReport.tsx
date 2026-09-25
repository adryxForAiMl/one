import React from 'react';
import { Findings } from '../../types/findings';

interface FindingsReportProps {
    findings: Findings[];
}

const FindingsReport: React.FC<FindingsReportProps> = ({ findings }) => {
    return (
        <div>
            <h1>Findings Report</h1>
            {findings.length === 0 ? (
                <p>No findings to report.</p>
            ) : (
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
                        {findings.map((finding) => (
                            <tr key={finding.id}>
                                <td>{finding.id}</td>
                                <td>{finding.title}</td>
                                <td>{finding.severity}</td>
                                <td>{finding.status}</td>
                                <td>{finding.timestamp}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};

export default FindingsReport;