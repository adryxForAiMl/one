import React from 'react';

interface StatCardProps {
    title: string;
    value: number | string;
    description: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, description }) => {
    return (
        <div className="stat-card">
            <h3>{title}</h3>
            <p className="value">{value}</p>
            <p className="description">{description}</p>
        </div>
    );
};

const StatsCards: React.FC<{ stats: StatCardProps[] }> = ({ stats }) => {
    return (
        <div className="stats-cards">
            {stats.map((stat, index) => (
                <StatCard key={index} {...stat} />
            ))}
        </div>
    );
};

export default StatsCards;