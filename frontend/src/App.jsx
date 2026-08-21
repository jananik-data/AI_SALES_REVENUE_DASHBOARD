import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import UploadModal from './components/UploadModal';
import DashboardPage from './pages/DashboardPage';
import SalesDataPage from './pages/SalesDataPage';
import PredictionPage from './pages/PredictionPage';
import AIIntelligencePage from './pages/AIIntelligencePage';
import AIAgentPage from './pages/AIAgentPage';
import ReportsPage from './pages/ReportsPage';
import LoginPage from './pages/LoginPage';
import api from './api/client';

function AppContent() {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isDemoLoading, setIsDemoLoading] = useState(false);
  const [filterOptions, setFilterOptions] = useState({ products: [], regions: [], categories: [] });
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    if (user) {
      fetchFilterOptions();
    }
  }, [user, refreshTrigger]);

  const fetchFilterOptions = async () => {
    try {
      const res = await api.get('/dashboard/filter-options');
      setFilterOptions(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleLoadDemo = async () => {
    setIsDemoLoading(true);
    try {
      await api.post('/sales/load-demo');
      setRefreshTrigger((t) => t + 1);
      alert('Loaded 1,200 sample transactions spanning 2024-2026!');
    } catch (err) {
      alert('Failed to load demo data.');
    } finally {
      setIsDemoLoading(false);
    }
  };

  const handleUploadSuccess = () => {
    setRefreshTrigger((t) => t + 1);
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0a0e1a', color: '#818cf8', fontSize: '15px', fontWeight: 600 }}>
        Initializing AI Sales Intelligence Suite...
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage filterOptions={filterOptions} refreshTrigger={refreshTrigger} />;
      case 'sales':
        return (
          <SalesDataPage
            filterOptions={filterOptions}
            onOpenUpload={() => setIsUploadOpen(true)}
            onLoadDemo={handleLoadDemo}
            isDemoLoading={isDemoLoading}
            refreshTrigger={refreshTrigger}
            setRefreshTrigger={setRefreshTrigger}
          />
        );
      case 'prediction':
        return <PredictionPage filterOptions={filterOptions} />;
      case 'ai-intelligence':
        return <AIIntelligencePage />;
      case 'ai-agent':
        return <AIAgentPage />;
      case 'reports':
        return <ReportsPage />;
      default:
        return <DashboardPage filterOptions={filterOptions} refreshTrigger={refreshTrigger} />;
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="main-content">
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onOpenUpload={() => setIsUploadOpen(true)}
          onLoadDemo={handleLoadDemo}
          isDemoLoading={isDemoLoading}
          refreshTrigger={refreshTrigger}
        />

        <main className="page-body">
          {renderActivePage()}
        </main>
      </div>

      {/* File Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
