import React, { useState, useEffect } from 'react';
import { FileText, Download, Printer, TrendingUp, DollarSign, Award, AlertTriangle, RefreshCw, BarChart2 } from 'lucide-react';
import api, { API_BASE_URL } from '../api/client';

export default function ReportsPage({ refreshTrigger = 0 }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    fetchReport();
  }, [refreshTrigger]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await api.get('/report/summary');
      setReport(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    const token = localStorage.getItem('sales_auth_token') || '';
    const url = `${API_BASE_URL}/api/report/html?token=${encodeURIComponent(token)}`;
    window.open(url, '_blank');
  };

  const handleDownloadCsv = async () => {
    setIsDownloading(true);
    try {
      const res = await api.get('/report/download?format=csv', {
        responseType: 'blob'
      });
      const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Executive_Sales_Report_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download CSV report. Please verify sales data is loaded.');
    } finally {
      setIsDownloading(false);
    }
  };

  const kpis = report?.kpis;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Report Header Card */}
      <div className="glass-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366f1, #a855f7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 18px rgba(99, 102, 241, 0.4)'
          }}>
            <FileText size={24} color="#fff" />
          </div>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>
              {report?.report_title || 'Executive Sales Intelligence Digest'}
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Generated on {report?.generated_at || 'Current session'} | Enterprise Audit Grade
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn btn-secondary btn-sm" onClick={fetchReport} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleDownloadCsv}
            disabled={isDownloading || loading}
          >
            <Download size={14} />
            <span>{isDownloading ? 'Downloading...' : 'Download Full CSV'}</span>
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={handlePrint}
            disabled={loading}
          >
            <Printer size={14} />
            <span>Print / Save PDF Report</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="glass-card" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Generating executive sales report...
        </div>
      ) : (
        <>
          {/* KPI Snapshot */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Total Revenue</div>
              <div className="gradient-text-emerald" style={{ fontSize: '24px', fontWeight: 800, marginTop: '6px' }}>
                ${(kpis?.total_revenue ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Total Transactions</div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#f8fafc', marginTop: '6px' }}>
                {(kpis?.total_orders ?? 0).toLocaleString()}
              </div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Gross Units Sold</div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#38bdf8', marginTop: '6px' }}>
                {(kpis?.total_units_sold ?? 0).toLocaleString()}
              </div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Average Order Value</div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#fbbf24', marginTop: '6px' }}>
                ${(kpis?.average_order_value ?? 0).toFixed(2)}
              </div>
            </div>
          </div>

          {/* Tables Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '24px' }}>
            {/* Top Products Table */}
            <div className="glass-card" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '16px' }}>
                Top Product Performance
              </h3>
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Category</th>
                    <th style={{ textAlign: 'right' }}>Revenue</th>
                    <th style={{ textAlign: 'right' }}>Share</th>
                  </tr>
                </thead>
                <tbody>
                  {report?.top_products?.slice(0, 8).map((p, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 600, color: '#fff' }}>{p.product}</td>
                      <td><span className="badge badge-primary">{p.category}</span></td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: '#10b981' }}>${p.total_revenue?.toLocaleString()}</td>
                      <td style={{ textAlign: 'right' }}>{p.revenue_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Regional Breakdown Table */}
            <div className="glass-card" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '16px' }}>
                Territorial Performance
              </h3>
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Territory</th>
                    <th style={{ textAlign: 'right' }}>Orders</th>
                    <th style={{ textAlign: 'right' }}>Revenue</th>
                    <th style={{ textAlign: 'right' }}>Share</th>
                  </tr>
                </thead>
                <tbody>
                  {report?.regional_breakdown?.map((r, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 600, color: '#fff' }}>{r.region}</td>
                      <td style={{ textAlign: 'right' }}>{r.total_orders}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: '#38bdf8' }}>${r.total_revenue?.toLocaleString()}</td>
                      <td style={{ textAlign: 'right' }}>{r.market_share_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Machine Learning Summary Card */}
          <div className="glass-card" style={{ padding: '24px', background: 'rgba(15, 23, 42, 0.6)' }}>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#a5b4fc', marginBottom: '10px' }}>
              Machine Learning Model & Forecasting Infrastructure
            </h3>
            <p style={{ fontSize: '13.5px', color: '#cbd5e1', lineHeight: '1.6' }}>
              The system evaluated Linear Regression and Random Forest Regression across 80% train / 20% test splits. The winning champion model (<strong>{report?.ml_model_overview?.selected_model}</strong>) is calibrated and actively used for real-time what-if forecasting and inventory planning.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
