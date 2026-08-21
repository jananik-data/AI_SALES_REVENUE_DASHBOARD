import React, { useState, useEffect } from 'react';
import { Filter, Calendar, RefreshCw } from 'lucide-react';
import KPIStats from '../components/KPIStats';
import TrendChart from '../components/Charts/TrendChart';
import ProductChart from '../components/Charts/ProductChart';
import RegionChart from '../components/Charts/RegionChart';
import CategoryPieChart from '../components/Charts/CategoryPieChart';
import AovLineChart from '../components/Charts/AovLineChart';
import api from '../api/client';

export default function DashboardPage({ filterOptions, refreshTrigger }) {
  const [kpis, setKpis] = useState(null);
  const [trends, setTrends] = useState([]);
  const [products, setProducts] = useState([]);
  const [regions, setRegions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Active filters
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, [selectedProduct, selectedRegion, selectedCategory, startDate, endDate, refreshTrigger]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const params = {
        product: selectedProduct || undefined,
        region: selectedRegion || undefined,
        category: selectedCategory || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      };

      const [kpiRes, trendRes, prodRes, regRes, catRes] = await Promise.all([
        api.get('/dashboard/kpis', { params }),
        api.get('/dashboard/trends', { params }),
        api.get('/dashboard/products', { params }),
        api.get('/dashboard/regions', { params }),
        api.get('/dashboard/categories', { params }),
      ]);

      setKpis(kpiRes.data);
      setTrends(trendRes.data);
      setProducts(prodRes.data);
      setRegions(regRes.data);
      setCategories(catRes.data);
    } catch (err) {
      console.error('Failed to load dashboard metrics', err);
    } finally {
      setLoading(false);
    }
  };

  const resetFilters = () => {
    setSelectedProduct('');
    setSelectedRegion('');
    setSelectedCategory('');
    setStartDate('');
    setEndDate('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Global Filter Bar */}
      <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Filter size={16} color="#818cf8" />
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>Dashboard Filters:</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <select
            className="form-select"
            style={{ width: '160px', padding: '6px 12px', fontSize: '13px' }}
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
          >
            <option value="">All Products</option>
            {filterOptions?.products?.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>

          <select
            className="form-select"
            style={{ width: '140px', padding: '6px 12px', fontSize: '13px' }}
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
          >
            <option value="">All Regions</option>
            {filterOptions?.regions?.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>

          <select
            className="form-select"
            style={{ width: '150px', padding: '6px 12px', fontSize: '13px' }}
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {filterOptions?.categories?.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          <button
            className="btn btn-secondary btn-sm"
            onClick={resetFilters}
          >
            Reset
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <KPIStats kpis={kpis} loading={loading} />

      {/* Chart 1: Time Series Area Chart */}
      <TrendChart data={trends} loading={loading} />

      {/* Charts 2 & 3: Product Bar Chart & Regional Donut Chart */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '24px' }}>
        <ProductChart data={products} loading={loading} />
        <RegionChart data={regions} loading={loading} />
      </div>

      {/* Charts 4 & 5: Category Pie Chart & Order Dynamics Line Chart */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '24px' }}>
        <CategoryPieChart data={categories} loading={loading} />
        <AovLineChart data={trends} loading={loading} />
      </div>
    </div>
  );
}
