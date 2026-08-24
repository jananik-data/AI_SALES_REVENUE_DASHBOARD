import React, { useState, useEffect } from 'react';
import { Database, Upload, Trash2, Plus, RefreshCw } from 'lucide-react';
import SalesTable from '../components/SalesTable';
import api, { API_BASE_URL } from '../api/client';

export default function SalesDataPage({ filterOptions, onOpenUpload, onLoadDemo, isDemoLoading, refreshTrigger, setRefreshTrigger }) {
  const [sales, setSales] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [search, setSearch] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSales();
  }, [page, search, selectedRegion, selectedCategory, refreshTrigger]);

  const fetchSales = async () => {
    setLoading(true);
    try {
      const res = await api.get('/sales', {
        params: {
          page,
          limit,
          search: search || undefined,
          region: selectedRegion || undefined,
          category: selectedCategory || undefined,
        },
      });
      setSales(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSale = async (saleId) => {
    if (!window.confirm(`Are you sure you want to delete transaction #${saleId}?`)) return;
    try {
      await api.delete(`/sales/${saleId}`);
      fetchSales();
      if (setRefreshTrigger) setRefreshTrigger((t) => t + 1);
    } catch (err) {
      alert('Failed to delete sale record.');
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Warning: This will delete ALL sales records in your account. Continue?')) return;
    try {
      await api.delete('/sales/clear-all/records');
      fetchSales();
      if (setRefreshTrigger) setRefreshTrigger((t) => t + 1);
    } catch (err) {
      alert('Failed to clear records.');
    }
  };

  const handleExportCsv = () => {
    window.location.href = `${API_BASE_URL}/api/sales/export/csv`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner */}
      <div className="glass-card" style={{ padding: '20px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'rgba(99, 102, 241, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid rgba(99, 102, 241, 0.3)'
          }}>
            <Database size={20} color="#818cf8" />
          </div>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
              Sales Transactions Repository
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              {total.toLocaleString()} total sales records stored and ready for ML training & analytics
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleClearAll}
            disabled={total === 0}
            style={{ color: '#f87171', borderColor: 'rgba(239, 68, 68, 0.3)' }}
          >
            <Trash2 size={14} /> Clear All Records
          </button>

          <button
            className="btn btn-secondary btn-sm"
            onClick={onLoadDemo}
            disabled={isDemoLoading}
          >
            <RefreshCw size={14} className={isDemoLoading ? 'animate-spin' : ''} />
            <span>Load Demo Dataset (1.2k rows)</span>
          </button>

          <button
            className="btn btn-primary btn-sm"
            onClick={onOpenUpload}
          >
            <Upload size={14} />
            <span>Upload CSV / Excel</span>
          </button>
        </div>
      </div>

      {/* Sales Table */}
      <SalesTable
        sales={sales}
        total={total}
        page={page}
        limit={limit}
        setPage={setPage}
        search={search}
        setSearch={setSearch}
        selectedRegion={selectedRegion}
        setSelectedRegion={setSelectedRegion}
        selectedCategory={selectedCategory}
        setSelectedCategory={setSelectedCategory}
        filterOptions={filterOptions}
        onDeleteSale={handleDeleteSale}
        onExportCsv={handleExportCsv}
        loading={loading}
      />
    </div>
  );
}
