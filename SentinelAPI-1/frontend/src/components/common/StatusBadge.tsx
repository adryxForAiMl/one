import React from 'react';

interface StatusBadgeProps {
    status: 'success' | 'warning' | 'error' | 'info';
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
    let badgeColor;

    switch (status) {
        case 'success':
            badgeColor = 'bg-green-500';
            break;
        case 'warning':
            badgeColor = 'bg-yellow-500';
            break;
        case 'error':
            badgeColor = 'bg-red-500';
            break;
        case 'info':
            badgeColor = 'bg-blue-500';
            break;
        default:
            badgeColor = 'bg-gray-500';
    }

    return (
        <span className={`text-white font-bold py-1 px-3 rounded ${badgeColor}`}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
    );
};

export default StatusBadge;