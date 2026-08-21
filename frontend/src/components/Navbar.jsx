import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, 
  Sparkles, 
  Database, 
  Bell, 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp, 
  ArrowDownRight,
  ChevronRight,
  X
} from 'lucide-react';
import api from '../api/client';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  onOpenUpload, 
  onLoadDemo, 
  isDemoLoading,
  refreshTrigger 
}) {
  const [alerts, setAlerts] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isAlertsOpen, setIsAlertsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const titles = {
    dashboard: { title: 'Executive Sales & Revenue Dashboard', subtitle: 'Real-time performance analytics, KPI tracking & territory dynamics' },
    sales: { title: 'Sales Data Management', subtitle: 'CSV/Excel uploads, automated preprocessing, cleaning & records table' },
    prediction: { title: 'ML Revenue Forecasting Engine', subtitle: 'Linear Regression vs Random Forest predictive modeling with evaluation metrics' },
    'ai-intelligence': { title: 'Automated AI Sales Intelligence', subtitle: 'Strategic business assessment, SWOT analytics & actionable optimization actions' },
    'ai-agent': { title: 'AI Sales Analyst Agent', subtitle: 'Multi-turn conversational sales reasoning powered by Gemini & analytical tools' },
    reports: { title: 'Executive Intelligence Reports', subtitle: 'Automated KPI digests, executive forecast summaries & instant export' },
  };

  const current = titles[activeTab] || titles.dashboard;

  useEffect(() => {
    fetchAlerts();
  }, [refreshTrigger]);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsAlertsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchAlerts = async () => {
    try {
      const res = await api.get('/ai/alerts');
      if (res.data?.alerts) {
        setAlerts(res.data.alerts);
        setUnreadCount(res.data.unread_count || res.data.alerts.length);
      }
    } catch (err) {
      console.error('Failed to fetch AI alerts:', err);
    }
  };

  const handleMarkAllAsRead = () => {
    setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
    setUnreadCount(0);
  };

  const getAlertIcon = (type) => {
    switch (type) {
      case 'spike':
        return <TrendingUp size={16} color="#10b981" />;
      case 'risk':
        return <AlertTriangle size={16} color="#f87171" />;
      case 'drop':
        return <ArrowDownRight size={16} color="#f59e0b" />;
      case 'opportunity':
        return <Sparkles size={16} color="#06b6d4" />;
      default:
        return <Bell size={16} color="#818cf8" />;
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'Positive':
        return 'badge-success';
      case 'High Priority':
        return 'badge-danger';
      case 'Attention':
        return 'badge-warning';
      case 'Opportunity':
        return 'badge-primary';
      default:
        return 'badge-primary';
    }
  };

  return (
    <header style={{
      height: '74px',
      borderBottom: '1px solid var(--border-glass)',
      background: 'rgba(15, 22, 41, 0.85)',
      backdropFilter: 'blur(12px)',
      padding: '0 32px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 50
    }}>
      {/* Page Title */}
      <div>
        <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.02em' }}>
          {current.title}
        </h1>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
          {current.subtitle}
        </p>
      </div>

      {/* Action Buttons & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* ML Status Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 12px',
          borderRadius: 'var(--radius-full)',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          fontSize: '11px',
          fontWeight: 600,
          color: '#34d399'
        }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }}></span>
          <span>ML Engine Active</span>
        </div>

        {/* AI Smart Alerts Bell & Dropdown */}
        <div style={{ position: 'relative' }} ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setIsAlertsOpen(!isAlertsOpen)}
            style={{
              position: 'relative',
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-glass)',
              background: isAlertsOpen ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.05)',
              color: isAlertsOpen ? '#818cf8' : '#cbd5e1',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            title="AI Smart Anomaly Alerts"
          >
            <Bell size={17} />
            {unreadCount > 0 && (
              <span style={{
                position: 'absolute',
                top: '-4px',
                right: '-4px',
                minWidth: '17px',
                height: '17px',
                padding: '0 4px',
                borderRadius: '999px',
                background: '#ef4444',
                color: '#fff',
                fontSize: '10px',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 10px rgba(239, 68, 68, 0.7)',
                border: '2px solid #0f1629'
              }}>
                {unreadCount}
              </span>
            )}
          </button>

          {/* Alerts Dropdown Drawer */}
          {isAlertsOpen && (
            <div style={{
              position: 'absolute',
              top: '46px',
              right: 0,
              width: '380px',
              background: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: 'var(--radius-md)',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(99, 102, 241, 0.15)',
              padding: '0',
              zIndex: 100,
              overflow: 'hidden',
              animation: 'slideUp 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
            }}>
              {/* Drawer Header */}
              <div style={{
                padding: '14px 18px',
                borderBottom: '1px solid var(--border-glass)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'rgba(15, 23, 42, 0.9)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={16} color="#818cf8" />
                  <span style={{ fontSize: '13.5px', fontWeight: 700, color: '#fff' }}>
                    AI Smart Anomaly Alerts
                  </span>
                  {unreadCount > 0 && (
                    <span className="badge badge-danger" style={{ fontSize: '10px', padding: '1px 6px' }}>
                      {unreadCount} New
                    </span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button
                    type="button"
                    onClick={handleMarkAllAsRead}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#818cf8',
                      fontSize: '11px',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Mark read
                  </button>
                )}
              </div>

              {/* Alerts List */}
              <div style={{ maxHeight: '340px', overflowY: 'auto', padding: '8px' }}>
                {alerts.length === 0 ? (
                  <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                    No active anomalies detected.
                  </div>
                ) : (
                  alerts.map((alert) => (
                    <div
                      key={alert.id}
                      style={{
                        padding: '12px',
                        borderRadius: '8px',
                        marginBottom: '6px',
                        background: alert.is_read ? 'rgba(15, 23, 42, 0.4)' : 'rgba(99, 102, 241, 0.08)',
                        border: alert.is_read ? '1px solid var(--border-glass)' : '1px solid rgba(99, 102, 241, 0.25)',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          {getAlertIcon(alert.type)}
                          <span style={{ fontSize: '12.5px', fontWeight: 700, color: '#fff' }}>
                            {alert.title}
                          </span>
                        </div>
                        <span className={`badge ${getSeverityBadge(alert.severity)}`} style={{ fontSize: '10px' }}>
                          {alert.severity}
                        </span>
                      </div>

                      <p style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: '1.45', marginBottom: '8px' }}>
                        {alert.message}
                      </p>

                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8', fontWeight: 600 }}>
                          {alert.metric}
                        </span>
                        <span>{alert.timestamp}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Drawer Footer */}
              <div style={{
                padding: '10px 16px',
                borderTop: '1px solid var(--border-glass)',
                background: 'rgba(15, 23, 42, 0.95)',
                textAlign: 'center'
              }}>
                <button
                  type="button"
                  onClick={() => {
                    setIsAlertsOpen(false);
                    if (setActiveTab) setActiveTab('ai-intelligence');
                  }}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#818cf8',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span>View Full AI Intelligence</span>
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Load Sample Data Button */}
        <button
          className="btn btn-secondary btn-sm"
          onClick={onLoadDemo}
          disabled={isDemoLoading}
          title="Populate 1200+ realistic transaction rows"
        >
          <Database size={14} color="#818cf8" />
          <span>{isDemoLoading ? 'Loading Sample...' : 'Load Sample Data'}</span>
        </button>

        {/* Upload File Button */}
        <button
          className="btn btn-primary btn-sm"
          onClick={onOpenUpload}
        >
          <Upload size={14} />
          <span>Upload Sales File</span>
        </button>
      </div>
    </header>
  );
}
