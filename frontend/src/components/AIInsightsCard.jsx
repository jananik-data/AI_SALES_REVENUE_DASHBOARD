import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  ShieldCheck, 
  TrendingUp, 
  AlertTriangle, 
  Target, 
  CheckCircle2, 
  RefreshCw,
  Bell,
  ArrowDownRight
} from 'lucide-react';
import api from '../api/client';

export default function AIInsightsCard() {
  const [insightsData, setInsightsData] = useState(null);
  const [alertsData, setAlertsData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchInsights();
    fetchAlerts();
  }, []);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const res = await api.get('/ai/insights');
      setInsightsData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const res = await api.get('/ai/alerts');
      if (res.data?.alerts) {
        setAlertsData(res.data.alerts);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRefreshAll = () => {
    fetchInsights();
    fetchAlerts();
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'Strength': return <ShieldCheck size={18} color="#10b981" />;
      case 'Growth Opportunity':
      case 'Opportunity': return <Target size={18} color="#06b6d4" />;
      case 'Risk': return <AlertTriangle size={18} color="#f59e0b" />;
      case 'Trend': return <TrendingUp size={18} color="#8b5cf6" />;
      default: return <Sparkles size={18} color="#6366f1" />;
    }
  };

  const getCategoryBadgeClass = (category) => {
    switch (category) {
      case 'Strength': return 'badge-success';
      case 'Growth Opportunity':
      case 'Opportunity': return 'badge-primary';
      case 'Risk': return 'badge-warning';
      case 'Trend': return 'badge-primary';
      default: return 'badge-primary';
    }
  };

  const getAlertIcon = (type) => {
    switch (type) {
      case 'spike': return <TrendingUp size={16} color="#10b981" />;
      case 'risk': return <AlertTriangle size={16} color="#f87171" />;
      case 'drop': return <ArrowDownRight size={16} color="#f59e0b" />;
      case 'opportunity': return <Sparkles size={16} color="#06b6d4" />;
      default: return <Bell size={16} color="#818cf8" />;
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'Positive': return 'badge-success';
      case 'High Priority': return 'badge-danger';
      case 'Attention': return 'badge-warning';
      case 'Opportunity': return 'badge-primary';
      default: return 'badge-primary';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Executive Summary Card */}
      <div className="glass-card" style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(15, 23, 42, 0.8) 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={20} color="#818cf8" />
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
              AI Sales Summary
            </h3>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleRefreshAll}
            disabled={loading}
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Refreshing...' : 'Refresh Intelligence'}</span>
          </button>
        </div>

        <p style={{ fontSize: '14px', lineHeight: '1.6', color: '#cbd5e1' }}>
          {insightsData?.summary || 'Upload sales data to generate real-time AI strategic assessment.'}
        </p>
      </div>

      {/* Real-Time AI Smart Anomaly Alerts Section */}
      {alertsData && alertsData.length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <Bell size={18} color="#818cf8" />
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>
              Active AI Anomaly & Outlier Alerts
            </h3>
            <span className="badge badge-danger" style={{ fontSize: '11px' }}>
              {alertsData.length} Live
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            {alertsData.map((alert) => (
              <div
                key={alert.id}
                className="glass-card interactive"
                style={{
                  padding: '18px',
                  background: 'rgba(15, 23, 42, 0.65)',
                  border: '1px solid rgba(99, 102, 241, 0.25)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {getAlertIcon(alert.type)}
                      <span style={{ fontSize: '13.5px', fontWeight: 700, color: '#fff' }}>
                        {alert.title}
                      </span>
                    </div>
                    <span className={`badge ${getSeverityBadge(alert.severity)}`} style={{ fontSize: '10.5px' }}>
                      {alert.severity}
                    </span>
                  </div>

                  <p style={{ fontSize: '12.5px', color: '#cbd5e1', lineHeight: '1.5' }}>
                    {alert.message}
                  </p>
                </div>

                <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8', fontWeight: 600 }}>
                    {alert.metric}
                  </span>
                  <span>{alert.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SWOT & Insight Category Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {insightsData?.insights?.map((item, idx) => (
          <div
            key={idx}
            className="glass-card interactive"
            style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {getCategoryIcon(item.category)}
                  <span className={`badge ${getCategoryBadgeClass(item.category)}`}>
                    {item.category === 'Opportunity' ? 'Growth Opportunity' : item.category}
                  </span>
                </div>
                {item.metric_value && (
                  <span style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
                    {item.metric_value}
                  </span>
                )}
              </div>

              <h4 style={{ fontSize: '14.5px', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>
                {item.title}
              </h4>
              <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                {item.description}
              </p>
            </div>

            <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
              <span>Strategic Priority</span>
              <span style={{ color: item.impact === 'High' ? '#f87171' : '#38bdf8', fontWeight: 600 }}>
                {item.impact} Impact
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Actionable Recommendations Checklist */}
      {insightsData?.recommendations && insightsData.recommendations.length > 0 && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={18} color="#10b981" />
            <span>AI Recommendations</span>
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {insightsData.recommendations.map((rec, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  background: 'rgba(15, 23, 42, 0.5)',
                  border: '1px solid var(--border-glass)'
                }}
              >
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: 'rgba(99, 102, 241, 0.15)',
                  color: '#818cf8',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '12px',
                  fontWeight: 700,
                  flexShrink: 0
                }}>
                  {i + 1}
                </div>
                <div style={{ fontSize: '13.5px', color: '#f8fafc', lineHeight: '1.5' }}>
                  {rec}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
