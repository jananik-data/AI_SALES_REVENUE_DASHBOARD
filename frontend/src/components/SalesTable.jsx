import React from 'react';
import { Search, Trash2, Download, Filter, ChevronLeft, ChevronRight, Layers } from 'lucide-react';

export default function SalesTable({
  sales,
  total,
  page,
  limit,
  setPage,
  search,
  setSearch,
  selectedRegion,
  setSelectedRegion,
  selectedCategory,
  setSelectedCategory,
  filterOptions,
  onDeleteSale,
  onExportCsv,
  loading
}) {
  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="glass-card" style={{ padding: '24px' }}>
      {/* Table Toolbar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '14px',
        marginBottom: '20px'
      }}>
        {/* Search */}
        <div style={{ position: 'relative', minWidth: '240px', flex: '1 1 200px' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            className="form-input"
            style={{ paddingLeft: '36px' }}
            placeholder="Search product, region or category..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <select
            className="form-select"
            style={{ width: '150px' }}
            value={selectedRegion}
            onChange={(e) => {
              setSelectedRegion(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Regions</option>
            {filterOptions?.regions?.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>

          <select
            className="form-select"
            style={{ width: '150px' }}
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Categories</option>
            {filterOptions?.categories?.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          <button
            className="btn btn-secondary btn-sm"
            onClick={onExportCsv}
            title="Download CSV export"
          >
            <Download size={14} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div style={{ overflowX: 'auto' }}>
        <table className="custom-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Transaction Date</th>
              <th>Product Name</th>
              <th>Category</th>
              <th>Region</th>
              <th style={{ textAlign: 'right' }}>Units</th>
              <th style={{ textAlign: 'right' }}>Unit Price</th>
              <th style={{ textAlign: 'right' }}>Gross Revenue</th>
              <th style={{ textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  Loading sales data records...
                </td>
              </tr>
            ) : sales.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--text-muted)' }}>
                  <Layers size={32} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                  <div>No sales records found matching your filters.</div>
                </td>
              </tr>
            ) : (
              sales.map((sale) => (
                <tr key={sale.id}>
                  <td style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                    #{sale.id}
                  </td>
                  <td>{sale.date}</td>
                  <td style={{ fontWeight: 600, color: '#f8fafc' }}>{sale.product}</td>
                  <td>
                    <span className="badge badge-primary">{sale.category}</span>
                  </td>
                  <td>
                    <span className="badge badge-success">{sale.region}</span>
                  </td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{sale.quantity}</td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>${sale.price?.toFixed(2)}</td>
                  <td style={{ textAlign: 'right', fontWeight: 700, color: '#10b981', fontFamily: 'var(--font-mono)' }}>
                    ${sale.revenue?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => onDeleteSale(sale.id)}
                      title="Delete record"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '4px',
                        borderRadius: '4px',
                        transition: 'color 0.2s'
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = '#f87171')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginTop: '20px',
        paddingTop: '16px',
        borderTop: '1px solid var(--border-glass)',
        fontSize: '13px',
        color: 'var(--text-muted)'
      }}>
        <div>
          Showing {sales.length > 0 ? (page - 1) * limit + 1 : 0} to {Math.min(page * limit, total)} of {total} records
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            <ChevronLeft size={14} /> Previous
          </button>
          <span style={{ fontWeight: 600, color: '#fff', padding: '0 8px' }}>
            {page} / {totalPages}
          </span>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Next <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
