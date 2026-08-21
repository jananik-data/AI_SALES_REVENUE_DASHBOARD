import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';
import { Layers } from 'lucide-react';

export default function CategoryChart({ data, loading }) {
  if (loading) {
    return (
      <div className="glass-card" style={{ height: '360px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Loading category analytics...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="glass-card" style={{ height: '360px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
        <Layers size={28} color="var(--text-muted)" />
        <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No category data available</div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const catData = payload[0].payload;
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
            {label} Category
          </div>
          <div style={{ color: '#818cf8', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Gross Revenue:</span>
            <strong>${catData.revenue?.toLocaleString()}</strong>
          </div>
          <div style={{ color: '#38bdf8', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Units Sold:</span>
            <strong>{catData.units?.toLocaleString()}</strong>
          </div>
          <div style={{ color: '#10b981', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Avg Order Value (AOV):</span>
            <strong>${catData.aov?.toFixed(2)}</strong>
          </div>
          <div style={{ color: '#fbbf24', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Revenue Share:</span>
            <strong>{catData.percentage}%</strong>
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
            background: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Layers size={16} color="#fff" />
          </div>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>Category Revenue & Average Order Value</h3>
            <p style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>Revenue volume compared with Average Basket Size (AOV)</p>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
            <defs>
              <linearGradient id="catBarGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#a855f7" stopOpacity={0.9} />
                <stop offset="100%" stopColor="#6366f1" stopOpacity={0.5} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" vertical={false} />
            <XAxis
              dataKey="category"
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
            />
            <YAxis
              yAxisId="left"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
              tickFormatter={(v) => `$${v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v}`}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#10b981"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
              tickFormatter={(v) => `$${v}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ paddingBottom: '10px', fontSize: '11.5px' }}
            />
            <Bar
              yAxisId="left"
              dataKey="revenue"
              name="Gross Revenue ($)"
              fill="url(#catBarGrad)"
              radius={[6, 6, 0, 0]}
              barSize={38}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="aov"
              name="Avg Order Value ($)"
              stroke="#10b981"
              strokeWidth={3}
              dot={{ r: 4, fill: '#10b981', strokeWidth: 2, stroke: '#fff' }}
              activeDot={{ r: 6, fill: '#10b981' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
