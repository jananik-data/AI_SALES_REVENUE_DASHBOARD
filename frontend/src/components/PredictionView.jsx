import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Cpu, 
  Sparkles, 
  RefreshCw, 
  CheckCircle2, 
  BarChart3, 
  Calendar, 
  Clock,
  ArrowRight
} from 'lucide-react';
import api from '../api/client';

export default function PredictionView({ filterOptions }) {
  const [modelInfo, setModelInfo] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [isTraining, setIsTraining] = useState(false);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);

  // Form State
  const [product, setProduct] = useState(filterOptions?.products?.[0] || 'Smart 4K Ultra OLED TV');
  const [region, setRegion] = useState(filterOptions?.regions?.[0] || 'North');
  const [quantity, setQuantity] = useState(10);
  const [price, setPrice] = useState(350);
  const [targetDate, setTargetDate] = useState(new Date().toISOString().split('T')[0]);
  const [modelChoice, setModelChoice] = useState('auto');

  useEffect(() => {
    fetchModelInfo();
    fetchPredictionHistory();
  }, []);

  useEffect(() => {
    if (filterOptions?.products?.length && !product) {
      setProduct(filterOptions.products[0]);
    }
    if (filterOptions?.regions?.length && !region) {
      setRegion(filterOptions.regions[0]);
    }
  }, [filterOptions]);

  const fetchModelInfo = async () => {
    setLoadingModels(true);
    try {
      const res = await api.get('/ml/model-info');
      setModelInfo(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingModels(false);
    }
  };

  const fetchPredictionHistory = async () => {
    try {
      const res = await api.get('/predictions?limit=10');
      setPredictions(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleTrainModels = async () => {
    setIsTraining(true);
    try {
      const res = await api.post('/ml/train');
      setModelInfo({
        is_trained: true,
        selected_model: res.data.models.selected_model,
        metrics: res.data.models,
        feature_importance: res.data.models.feature_importance
      });
      fetchPredictionHistory();
    } catch (err) {
      alert(err.response?.data?.detail || 'Training failed. Please ensure at least 10 sales records exist.');
    } finally {
      setIsTraining(false);
    }
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    setIsPredicting(true);
    try {
      const res = await api.post('/predict', {
        product,
        region,
        quantity: parseInt(quantity),
        price: parseFloat(price),
        target_date: targetDate,
        model_name: modelChoice
      });
      setPredictionResult(res.data);
      fetchPredictionHistory();
    } catch (err) {
      alert(err.response?.data?.detail || 'Prediction failed.');
    } finally {
      setIsPredicting(false);
    }
  };

  const lrMetrics = modelInfo?.metrics?.linear_regression;
  const rfMetrics = modelInfo?.metrics?.random_forest;
  const championModel = modelInfo?.selected_model || 'Random Forest Regressor';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner: Model Evaluation & Comparison */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #6366f1, #3b82f6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)'
            }}>
              <Cpu size={22} color="#fff" />
            </div>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
                Machine Learning Model Evaluation & Benchmark
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Comparing Linear Regression baseline vs Random Forest Ensemble (80/20 train/test split)
              </p>
            </div>
          </div>

          <button
            className="btn btn-primary btn-sm"
            onClick={handleTrainModels}
            disabled={isTraining}
          >
            <RefreshCw size={14} className={isTraining ? 'animate-spin' : ''} />
            <span>{isTraining ? 'Training Models...' : 'Retrain ML Models'}</span>
          </button>
        </div>

        {/* Evaluation Metrics Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {/* Linear Regression Card */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: championModel === 'Linear Regression' ? '1px solid #6366f1' : '1px solid var(--border-glass)',
            borderRadius: '12px',
            padding: '18px',
            position: 'relative'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>Linear Regression</span>
              <span className="badge badge-primary">Baseline Model</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', textAlign: 'center' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 6px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>MAE</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>${lrMetrics?.mae ?? '0.00'}</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 6px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>RMSE</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>${lrMetrics?.rmse ?? '0.00'}</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 6px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>R² Score</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#38bdf8' }}>{lrMetrics?.r2_score ?? '0.00'}</div>
              </div>
            </div>
          </div>

          {/* Random Forest Card */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: championModel.includes('Random Forest') ? '1px solid #10b981' : '1px solid var(--border-glass)',
            borderRadius: '12px',
            padding: '18px',
            position: 'relative'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>Random Forest Regressor</span>
              <span className="badge badge-success">
                <CheckCircle2 size={12} /> Champion Model
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', textAlign: 'center' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 6px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>MAE</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>${rfMetrics?.mae ?? '0.00'}</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 6px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>RMSE</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>${rfMetrics?.rmse ?? '0.00'}</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 6px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>R² Score</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#34d399' }}>{rfMetrics?.r2_score ?? '0.00'}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Interactive Simulator + Prediction Output */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px' }}>
        {/* Prediction Form */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
            <TrendingUp size={20} color="#6366f1" />
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
              Future Revenue Simulator
            </h3>
          </div>

          <form onSubmit={handlePredict}>
            <div className="form-group">
              <label className="form-label">Product Selection</label>
              <select
                className="form-select"
                value={product}
                onChange={(e) => setProduct(e.target.value)}
                required
              >
                {filterOptions?.products?.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
                {(!filterOptions?.products || filterOptions.products.length === 0) && (
                  <option value="Smart 4K Ultra OLED TV">Smart 4K Ultra OLED TV</option>
                )}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Territory / Region</label>
                <select
                  className="form-select"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  required
                >
                  {filterOptions?.regions?.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                  {(!filterOptions?.regions || filterOptions.regions.length === 0) && (
                    <option value="North">North</option>
                  )}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Target Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Target Quantity / Units</label>
                <input
                  type="number"
                  min="1"
                  className="form-input"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Unit Selling Price ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.1"
                  className="form-input"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Model Selection Strategy</label>
              <select
                className="form-select"
                value={modelChoice}
                onChange={(e) => setModelChoice(e.target.value)}
              >
                <option value="auto">Auto (Best Performing R² Model)</option>
                <option value="random_forest">Random Forest Regressor</option>
                <option value="linear_regression">Linear Regression</option>
              </select>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '8px', padding: '12px' }}
              disabled={isPredicting}
            >
              <Sparkles size={16} />
              <span>{isPredicting ? 'Calculating ML Forecast...' : 'Generate Revenue Prediction'}</span>
            </button>
          </form>
        </div>

        {/* Prediction Results Display */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>
                Forecast Result & Analysis
              </h3>
              {predictionResult && (
                <span className="badge badge-success">Forecast Ready</span>
              )}
            </div>

            {predictionResult ? (
              <div>
                <div style={{
                  background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%)',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  borderRadius: '12px',
                  padding: '24px',
                  textAlign: 'center',
                  marginBottom: '20px'
                }}>
                  <div style={{ fontSize: '12px', color: '#a5b4fc', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>
                    Predicted Revenue
                  </div>
                  <div className="gradient-text" style={{ fontSize: '36px', fontWeight: 800, margin: '8px 0', letterSpacing: '-0.03em' }}>
                    ${predictionResult.predicted_revenue?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Model: <strong style={{ color: '#f8fafc' }}>{predictionResult.model_used}</strong>
                  </div>
                </div>

                {/* Confidence Interval */}
                {predictionResult.confidence_interval && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '18px' }}>
                    <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Estimated Lower Bound</div>
                      <div style={{ fontSize: '15px', fontWeight: 700, color: '#38bdf8', marginTop: '4px' }}>
                        ${predictionResult.confidence_interval.low?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Estimated Upper Bound</div>
                      <div style={{ fontSize: '15px', fontWeight: 700, color: '#34d399', marginTop: '4px' }}>
                        ${predictionResult.confidence_interval.high?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  </div>
                )}

                {/* Scenario details */}
                <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px' }}>
                  <strong>Simulated Scenario:</strong> {predictionResult.input_summary.quantity} units of <em>{predictionResult.input_summary.product}</em> in the <em>{predictionResult.input_summary.region}</em> territory at ${predictionResult.input_summary.price}/unit.
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '48px 16px', color: 'var(--text-muted)' }}>
                <TrendingUp size={44} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>Awaiting Simulation Input</div>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>
                  Adjust parameters on the left and click Generate Revenue Prediction to forecast outcomes.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Prediction History Table */}
      {predictions.length > 0 && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Clock size={16} color="#818cf8" />
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>Recent ML Predictions Log</h3>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Region</th>
                  <th>Target Date</th>
                  <th>Model Used</th>
                  <th style={{ textAlign: 'right' }}>Predicted Revenue</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 600, color: '#fff' }}>{p.product || 'N/A'}</td>
                    <td><span className="badge badge-primary">{p.region || 'General'}</span></td>
                    <td>{p.target_date || 'N/A'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{p.model_name}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#10b981', fontFamily: 'var(--font-mono)' }}>
                      ${p.predicted_revenue?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
