import React, { useState, useEffect } from 'react';
import { FileText, Download, Printer, TrendingUp, DollarSign, Award, AlertTriangle, RefreshCw, X } from 'lucide-react';
import api, { API_BASE_URL } from '../api/client';

export default function ReportModal({ isOpen, onClose }) {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchReport();
    }
  }, [isOpen]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await api.get('/report/summary');
      setReportData(res.data);
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
      alert('Failed to download CSV report.');
    } finally {
      setIsDownloading(false);
    }
  };

  if (!isOpen) return null;

  const kpis = reportData?.kpis;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '850px' }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText size={22} color="#818cf8" />
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>Executive Intelligence Report</h2>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Generated {reportData?.generated_at}</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={handleDownloadCsv}
              disabled={isDownloading || loading}
            >
              <Download size={14} /> {isDownloading ? 'Downloading...' : 'Export Full CSV'}
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={handlePrint}
              disabled={loading}
            >
              <Printer size={14} /> Print / Save PDF
            </button>
            <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', marginLeft: '6px' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Report Content */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Compiling executive report...</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* KPI Summary Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>TOTAL REVENUE</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#10b981', marginTop: '4px' }}>
                  ${kpis?.total_revenue?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>TOTAL ORDERS</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc', marginTop: '4px' }}>
                  {kpis?.total_orders?.toLocaleString()}
                </div>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>UNITS SOLD</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#38bdf8', marginTop: '4px' }}>
                  {kpis?.total_units_sold?.toLocaleString()}
                </div>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>AVG ORDER VALUE</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#fbbf24', marginTop: '4px' }}>
                  ${kpis?.average_order_value?.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Top Products Table */}
            <div>
              <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>Top Product Contributions</h4>
              <table className="custom-table" style={{ fontSize: '12px' }}>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Category</th>
                    <th style={{ textAlign: 'right' }}>Units</th>
                    <th style={{ textAlign: 'right' }}>Revenue</th>
                    <th style={{ textAlign: 'right' }}>Share</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData?.top_products?.slice(0, 5).map((p, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 600, color: '#fff' }}>{p.product}</td>
                      <td><span className="badge badge-primary">{p.category}</span></td>
                      <td style={{ textAlign: 'right' }}>{p.total_units}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: '#10b981' }}>${p.total_revenue?.toLocaleString()}</td>
                      <td style={{ textAlign: 'right' }}>{p.revenue_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Regional Breakdown Table */}
            <div>
              <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>Regional Territorial Performance</h4>
              <table className="custom-table" style={{ fontSize: '12px' }}>
                <thead>
                  <tr>
                    <th>Region</th>
                    <th style={{ textAlign: 'right' }}>Orders</th>
                    <th style={{ textAlign: 'right' }}>Units</th>
                    <th style={{ textAlign: 'right' }}>Revenue</th>
                    <th style={{ textAlign: 'right' }}>Market Share</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData?.regional_breakdown?.map((r, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 600, color: '#fff' }}>{r.region}</td>
                      <td style={{ textAlign: 'right' }}>{r.total_orders}</td>
                      <td style={{ textAlign: 'right' }}>{r.total_units}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: '#38bdf8' }}>${r.total_revenue?.toLocaleString()}</td>
                      <td style={{ textAlign: 'right' }}>{r.market_share_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* ML & Strategy Section */}
            <div style={{ background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.2)', padding: '16px', borderRadius: '8px' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#a5b4fc', marginBottom: '4px' }}>
                Machine Learning Forecasting Summary
              </div>
              <div style={{ fontSize: '12.5px', color: '#cbd5e1' }}>
                Selected Model: <strong>{reportData?.ml_model_overview?.selected_model}</strong> | Status: Active & Calibrated
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
