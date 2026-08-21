import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend
} from 'recharts';
import { PieChart as PieIcon } from 'lucide-react';

const COLORS = [
  '#6366f1', // Indigo
  '#ec4899', // Pink
  '#06b6d4', // Cyan
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#8b5cf6', // Purple
  '#3b82f6', // Blue
];

export default function CategoryPieChart({ data, loading }) {
  if (loading) {
    return (
      <div className="glass-card" style={{ height: '380px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Loading category distribution...</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="glass-card" style={{ height: '380px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
        <PieIcon size={28} color="var(--text-muted)" />
        <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No category data available</div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }) => {
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
            {d.category}
          </div>
          <div style={{ color: '#818cf8', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Gross Revenue:</span>
            <strong>${d.revenue?.toLocaleString()}</strong>
          </div>
          <div style={{ color: '#38bdf8', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Units Sold:</span>
            <strong>{d.units?.toLocaleString()}</strong>
          </div>
          <div style={{ color: '#10b981', display: 'flex', justifyContent: 'space-between', gap: '16px', margin: '3px 0' }}>
            <span>Market Share:</span>
            <strong>{d.percentage}%</strong>
          </div>
        </div>
      );
    }
    return null;
  };

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percentage }) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.55;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    if (percentage < 6) return null;

    return (
      <text
        x={x}
        y={y}
        fill="#ffffff"
        textAnchor="middle"
        dominantBaseline="central"
        style={{ fontSize: '11px', fontWeight: 700, textShadow: '0 1px 3px rgba(0,0,0,0.8)' }}
      >
        {`${percentage}%`}
      </text>
    );
  };

  return (
    <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '380px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #ec4899 0%, #a855f7 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <PieIcon size={16} color="#fff" />
          </div>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>Category Market Contribution</h3>
            <p style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>Proportional sales contribution across product categories</p>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="revenue"
              nameKey="category"
              cx="50%"
              cy="48%"
              outerRadius={105}
              labelLine={false}
              label={renderCustomLabel}
              stroke="rgba(15, 23, 42, 0.8)"
              strokeWidth={2}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              align="center"
              iconType="circle"
              wrapperStyle={{ fontSize: '11.5px', paddingTop: '10px' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
