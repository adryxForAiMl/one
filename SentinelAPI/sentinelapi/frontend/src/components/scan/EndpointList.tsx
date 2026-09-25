import React from 'react';

interface Endpoint {
    id: string;
    name: string;
    path: string;
    method: string;
}

interface EndpointListProps {
    endpoints: Endpoint[];
}

const EndpointList: React.FC<EndpointListProps> = ({ endpoints }) => {
    return (
        <div>
            <h2>API Endpoints</h2>
            <ul>
                {endpoints.map((endpoint) => (
                    <li key={endpoint.id}>
                        <strong>{endpoint.method}</strong> {endpoint.path} - {endpoint.name}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default EndpointList;