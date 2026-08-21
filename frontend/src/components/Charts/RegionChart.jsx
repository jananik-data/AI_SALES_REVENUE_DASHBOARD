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
import { MapPin, Globe } from 'lucide-react';

const REGION_COLORS = {
  North: '#6366f1',
  South: '#10b981',
  East: '#06b6d4',
  West: '#f59e0b',
  Central: '#8b5cf6',
};

const CustomRegionTooltip = ({ active, payload }) => {
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
        <div style={{ fontSize: '13px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <MapPin size={13} color="#818cf8" /> {item.region} Territory
        </div>
        <div style={{ fontSize: '14px', fontWeight: 700, color: '#38bdf8', marginTop: '4px' }}>
          Revenue: ${item.revenue?.toLocaleString()} ({item.percentage}% Share)
        </div>
        <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
          Units Sold: {item.units?.toLocaleString()} across {item.orders} transactions
        </div>
      </div>
    );
  }
  return null;
};

export default function RegionChart({ data, loading }) {
  if (loading) {
    return (
      <div className="glass-card" style={{ padding: '24px', height: '360px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: 'var(--text-muted)' }}>Loading regional breakdown...</span>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="glass-card" style={{ padding: '24px', height: '360px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
        <Globe size={36} color="var(--text-muted)" />
        <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>No regional metrics recorded yet.</span>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ padding: '24px', height: '380px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
        <div>
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Globe size={18} color="#06b6d4" />
            <span>Geographical Revenue Contribution</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Territorial performance metrics and regional market distribution
          </div>
        </div>
        <div className="badge badge-success">
          {data.length} Regions Active
        </div>
      </div>

      <div style={{ flex: 1, width: '100%', minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis
              dataKey="region"
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `$${v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}`}
            />
            <Tooltip content={<CustomRegionTooltip />} />
            <Bar dataKey="revenue" radius={[6, 6, 0, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-reg-${index}`}
                  fill={REGION_COLORS[entry.region] || '#6366f1'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
