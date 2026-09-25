import React from 'react';
import Header from '../components/common/Header';
import Sidebar from '../components/common/Sidebar';
import ScanOverview from '../components/dashboard/ScanOverview';
import FindingsTable from '../components/dashboard/FindingsTable';
import AuthPanel from '../components/dashboard/AuthPanel';

const Page: React.FC = () => {
    return (
        <div className="app-container">
            <Header />
            <div className="main-content">
                <Sidebar />
                <div className="content-area">
                    <AuthPanel />
                    <ScanOverview />
                    <FindingsTable />
                </div>
            </div>
        </div>
    );
};

export default Page;