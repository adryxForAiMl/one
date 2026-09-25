import React from 'react';
import { Line } from 'react-chartjs-2';

interface RiskChartProps {
    data: {
        labels: string[];
        datasets: {
            label: string;
            data: number[];
            borderColor: string;
            backgroundColor: string;
        }[];
    };
}

const RiskChart: React.FC<RiskChartProps> = ({ data }) => {
    return (
        <div>
            <h2>Risk Assessment Over Time</h2>
            <Line data={data} />
        </div>
    );
};

export default RiskChart;