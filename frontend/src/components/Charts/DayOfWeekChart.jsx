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
import { Calendar, TrendingUp } from 'lucide-react';

export default function DayOfWeekChart({ data, loading }) {
  if (loading) {
    return (
      <div className="glass-card" style={{ height: '380px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Loading weekly sales velocity...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="glass-card" style={{ height: '380px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
        <Calendar size={28} color="var(--text-muted)" />
        <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No weekly pattern data available</div>
      </div>
    );
  }

  // Find peak day
  const peakDay = [...data].sort((a, b) => b.revenue - a.revenue)[0];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div style={{
          background: 'rgba(15, 23, 42, 0.95)',
          border: '1px solid var(--border-glass)',
          padding: '12px 16px',
          borderRadius: '8px',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
          fontSize: '12px'
        }}>
          <div style={{ fontWeight: 700, color: '#f8fafc', marginBottom: '6px', fontSize: '13px' }}>
            {d.day} Sales Dynamics
          </div>
          <div style={{ color: '#38bdf8', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Revenue Generated:</span>
            <strong>${d.revenue?.toLocaleString()}</strong>
          </div>
          <div style={{ color: '#a5b4fc', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Orders Completed:</span>
            <strong>{d.orders?.toLocaleString()}</strong>
          </div>
          <div style={{ color: '#10b981', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Total Units:</span>
            <strong>{d.units?.toLocaleString()}</strong>
          </div>
          <div style={{ color: '#fbbf24', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Weekly Share:</span>
            <strong>{d.percentage}%</strong>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '380px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Calendar size={16} color="#fff" />
          </div>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>Weekly Sales Velocity (Day of Week)</h3>
            <p style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>Customer purchasing intensity across days of the week</p>
          </div>
        </div>

        {peakDay && (
          <div className="badge badge-primary" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px' }}>
            <TrendingUp size={12} />
            <span>Peak: <strong>{peakDay.day}</strong> (${(peakDay.revenue / 1000).toFixed(0)}k)</span>
          </div>
        )}
      </div>

      <div style={{ flex: 1, width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" vertical={false} />
            <XAxis
              dataKey="day"
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
              tickFormatter={(d) => d.slice(0, 3)}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
              tickFormatter={(v) => `$${v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="revenue" radius={[6, 6, 0, 0]} barSize={34}>
              {data.map((entry, index) => {
                const isPeak = peakDay && entry.day === peakDay.day;
                return (
                  <Cell
                    key={`cell-${index}`}
                    fill={isPeak ? '#06b6d4' : '#6366f1'}
                    fillOpacity={isPeak ? 1 : 0.75}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
