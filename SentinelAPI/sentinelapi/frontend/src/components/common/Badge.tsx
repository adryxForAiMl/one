import React from 'react';

interface BadgeProps {
    text: string;
    color?: string;
    onClick?: () => void;
}

const Badge: React.FC<BadgeProps> = ({ text, color = 'blue', onClick }) => {
    return (
        <span
            onClick={onClick}
            style={{
                display: 'inline-block',
                padding: '0.5em 1em',
                borderRadius: '12px',
                backgroundColor: color,
                color: 'white',
                cursor: onClick ? 'pointer' : 'default',
            }}
        >
            {text}
        </span>
    );
};

export default Badge;