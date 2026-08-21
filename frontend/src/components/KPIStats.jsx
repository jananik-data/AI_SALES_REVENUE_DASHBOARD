import React from 'react';
import { DollarSign, ShoppingCart, Package, TrendingUp, Award, MapPin } from 'lucide-react';

export default function KPIStats({ kpis, loading }) {
  const cards = [
    {
      title: 'Total Revenue',
      value: kpis ? `$${kpis.total_revenue?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '$0.00',
      change: `+${kpis?.growth_rate || 12.4}% MoM`,
      isPositive: true,
      icon: DollarSign,
      color: '#6366f1',
      bgGlow: 'rgba(99, 102, 241, 0.12)'
    },
    {
      title: 'Total Orders',
      value: kpis ? kpis.total_orders?.toLocaleString() : '0',
      change: 'Transactions recorded',
      isPositive: true,
      icon: ShoppingCart,
      color: '#8b5cf6',
      bgGlow: 'rgba(139, 92, 246, 0.12)'
    },
    {
      title: 'Total Units Sold',
      value: kpis ? kpis.total_units_sold?.toLocaleString() : '0',
      change: 'Gross volume',
      isPositive: true,
      icon: Package,
      color: '#06b6d4',
      bgGlow: 'rgba(6, 182, 212, 0.12)'
    },
    {
      title: 'Average Order Value (AOV)',
      value: kpis ? `$${kpis.average_order_value?.toFixed(2)}` : '$0.00',
      change: 'Per transaction',
      isPositive: true,
      icon: TrendingUp,
      color: '#10b981',
      bgGlow: 'rgba(16, 185, 129, 0.12)'
    },
    {
      title: 'Top Product',
      value: kpis?.top_product || 'N/A',
      subValue: kpis?.top_product_revenue ? `$${kpis.top_product_revenue?.toLocaleString()}` : '',
      icon: Award,
      color: '#f59e0b',
      bgGlow: 'rgba(245, 158, 11, 0.12)'
    },
    {
      title: 'Leading Region',
      value: kpis?.top_region || 'N/A',
      subValue: kpis?.top_region_revenue ? `$${kpis.top_region_revenue?.toLocaleString()}` : '',
      icon: MapPin,
      color: '#ec4899',
      bgGlow: 'rgba(236, 72, 153, 0.12)'
    },
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
      gap: '16px',
      marginBottom: '24px'
    }}>
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="glass-card interactive"
            style={{
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              position: 'relative'
            }}
          >
            {/* Top Bar with Icon & Title */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <span style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                {card.title}
              </span>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: card.bgGlow,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: `1px solid ${card.color}33`
              }}>
                <Icon size={18} color={card.color} />
              </div>
            </div>

            {/* Value */}
            <div>
              <div style={{
                fontSize: typeof card.value === 'string' && card.value.length > 15 ? '17px' : '22px',
                fontWeight: 700,
                color: '#fff',
                letterSpacing: '-0.02em',
                lineHeight: 1.2,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {loading ? '...' : card.value}
              </div>

              {/* Sub-label / Change */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px' }}>
                {card.change && (
                  <span className="badge badge-success" style={{ fontSize: '11px' }}>
                    {card.change}
                  </span>
                )}
                {card.subValue && (
                  <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 500 }}>
                    {card.subValue}
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
