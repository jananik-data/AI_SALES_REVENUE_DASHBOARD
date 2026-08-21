import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell
} from 'recharts';
import { Package, Award } from 'lucide-react';

const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#3b82f6'];

const CustomBarTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const item = payload[0].payload;
    return (
      <div style={{
        background: '#0f172a',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        borderRadius: '8px',
        padding: '10px 14px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.5)'
      }}>
        <div style={{ fontSize: '12px', fontWeight: 700, color: '#f8fafc' }}>
          {item.product}
        </div>
        <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
          Category: {item.category}
        </div>
        <div style={{ fontSize: '13px', fontWeight: 700, color: '#10b981', marginTop: '4px' }}>
          Revenue: ${item.revenue?.toLocaleString()} ({item.percentage}%)
        </div>
        <div style={{ fontSize: '11px', color: '#38bdf8', marginTop: '2px' }}>
          Units Sold: {item.units} ({item.orders} orders)
        </div>
      </div>
    );
  }
  return null;
};

export default function ProductChart({ data, loading }) {
  const topProducts = data ? data.slice(0, 6) : [];

  if (loading) {
    return (
      <div className="glass-card" style={{ padding: '24px', height: '360px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: 'var(--text-muted)' }}>Loading product distribution...</span>
      </div>
    );
  }

  if (topProducts.length === 0) {
    return (
      <div className="glass-card" style={{ padding: '24px', height: '360px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
        <Package size={36} color="var(--text-muted)" />
        <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>No product sales records found.</span>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ padding: '24px', height: '380px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
        <div>
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Award size={18} color="#f59e0b" />
            <span>Top Performing Products & Portfolio</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Highest grossing products ranked by cumulative sales revenue
          </div>
        </div>
      </div>

      <div style={{ flex: 1, width: '100%', minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={topProducts} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
            <XAxis
              type="number"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickFormatter={(v) => `$${v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}`}
            />
            <YAxis
              dataKey="product"
              type="category"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              width={140}
              tickFormatter={(v) => (v.length > 18 ? `${v.substring(0, 16)}...` : v)}
            />
            <Tooltip content={<CustomBarTooltip />} />
            <Bar dataKey="revenue" radius={[0, 6, 6, 0]}>
              {topProducts.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
