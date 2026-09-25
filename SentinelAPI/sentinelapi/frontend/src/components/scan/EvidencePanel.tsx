import React from 'react';

interface EvidencePanelProps {
    evidence: {
        findingId: string;
        timestamp: string;
        request: {
            method: string;
            url: string;
            user: string;
            headers: Record<string, string>;
        };
        response: any;
        responseMetadata: {
            statusCode: number;
            contentType: string;
            contentLength: number;
            bodyType: string;
            bodyHash: string;
            headers: Record<string, string>;
        };
        sensitiveFieldsExposed: string[];
    };
}

const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidence }) => {
    return (
        <div className="evidence-panel">
            <h2>Evidence Details</h2>
            <p><strong>Finding ID:</strong> {evidence.findingId}</p>
            <p><strong>Timestamp:</strong> {new Date(evidence.timestamp).toLocaleString()}</p>
            <h3>Request</h3>
            <p><strong>Method:</strong> {evidence.request.method}</p>
            <p><strong>URL:</strong> {evidence.request.url}</p>
            <p><strong>User:</strong> {evidence.request.user}</p>
            <h4>Headers</h4>
            <pre>{JSON.stringify(evidence.request.headers, null, 2)}</pre>
            <h3>Response</h3>
            <p><strong>Status Code:</strong> {evidence.responseMetadata.statusCode}</p>
            <p><strong>Content Type:</strong> {evidence.responseMetadata.contentType}</p>
            <p><strong>Content Length:</strong> {evidence.responseMetadata.contentLength}</p>
            <p><strong>Body Type:</strong> {evidence.responseMetadata.bodyType}</p>
            <p><strong>Body Hash:</strong> {evidence.responseMetadata.bodyHash}</p>
            <h4>Response Data</h4>
            <pre>{JSON.stringify(evidence.response, null, 2)}</pre>
            <h4>Sensitive Fields Exposed</h4>
            <ul>
                {evidence.sensitiveFieldsExposed.map((field, index) => (
                    <li key={index}>{field}</li>
                ))}
            </ul>
        </div>
    );
};

export default EvidencePanel;