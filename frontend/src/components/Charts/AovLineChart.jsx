import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';
import { TrendingUp } from 'lucide-react';

export default function AovLineChart({ data, loading }) {
  if (loading) {
    return (
      <div className="glass-card" style={{ height: '380px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Loading timeline velocity metrics...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="glass-card" style={{ height: '380px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
        <TrendingUp size={28} color="var(--text-muted)" />
        <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No timeline data available</div>
      </div>
    );
  }

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
            Period: {label}
          </div>
          <div style={{ color: '#38bdf8', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Avg Order Value (AOV):</span>
            <strong>${d.aov?.toFixed(2)}</strong>
          </div>
          <div style={{ color: '#10b981', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Monthly Orders:</span>
            <strong>{d.orders?.toLocaleString()}</strong>
          </div>
          <div style={{ color: '#a5b4fc', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Total Units:</span>
            <strong>{d.units?.toLocaleString()}</strong>
          </div>
          <div style={{ color: '#fbbf24', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Gross Revenue:</span>
            <strong>${d.revenue?.toLocaleString()}</strong>
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
            background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <TrendingUp size={16} color="#fff" />
          </div>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>Average Order Value & Volume Velocity</h3>
            <p style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>Average order value trajectory vs transaction volume</p>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" vertical={false} />
            <XAxis
              dataKey="period"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
            />
            <YAxis
              yAxisId="left"
              stroke="#38bdf8"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
              tickFormatter={(v) => `$${v}`}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#10b981"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
              tickFormatter={(v) => `${v}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ paddingBottom: '10px', fontSize: '11.5px' }}
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="aov"
              name="Avg Order Value ($)"
              stroke="#38bdf8"
              strokeWidth={3}
              dot={{ r: 4, fill: '#38bdf8', strokeWidth: 2, stroke: '#0f172a' }}
              activeDot={{ r: 6, fill: '#38bdf8' }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="orders"
              name="Monthly Orders Count"
              stroke="#10b981"
              strokeWidth={2.5}
              strokeDasharray="4 4"
              dot={{ r: 3.5, fill: '#10b981', strokeWidth: 2, stroke: '#0f172a' }}
              activeDot={{ r: 6, fill: '#10b981' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
