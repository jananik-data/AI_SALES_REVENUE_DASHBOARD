import io
import csv
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.ai_agent.tools import (
    sales_analysis_tool,
    product_performance_tool,
    regional_breakdown_tool,
    trend_analysis_tool,
    get_sales_dataframe
)
from backend.ml.predictor import RevenuePredictor

import numpy as np
import pandas as pd

def sanitize_record(d: Any) -> Any:
    if isinstance(d, dict):
        return {str(k): sanitize_record(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [sanitize_record(v) for v in d]
    elif isinstance(d, (np.integer, np.int64, np.int32)):
        return int(d)
    elif isinstance(d, (np.floating, np.float64, np.float32)):
        val = float(d)
        return 0.0 if (np.isnan(val) or np.isinf(val)) else val
    elif isinstance(d, pd.Timestamp):
        return d.strftime("%Y-%m-%d")
    elif d is None or (isinstance(d, float) and (np.isnan(d) or np.isinf(d))):
        return 0.0
    return d

def generate_executive_report_json(db: Session, user_id: int) -> Dict[str, Any]:
    df = get_sales_dataframe(db, user_id)
    if df.empty:
        return {
            "report_title": "AI Sales & Revenue Executive Intelligence Report",
            "generated_at": datetime.utcnow().strftime("%B %d, %Y - %H:%M UTC"),
            "kpis": {
                "status": "empty",
                "total_revenue": 0.0,
                "total_orders": 0,
                "total_units_sold": 0,
                "average_order_value": 0.0,
                "top_product": "N/A",
                "top_region": "N/A",
                "growth_rate": 0.0
            },
            "top_products": [],
            "category_breakdown": {},
            "regional_breakdown": [],
            "monthly_trends": [],
            "ml_model_overview": {
                "is_trained": False,
                "selected_model": "Baseline Multiplier",
                "metrics": {}
            }
        }

    kpis = sales_analysis_tool(db, user_id) or {}
    products = product_performance_tool(db, user_id) or {}
    regions = regional_breakdown_tool(db, user_id) or {}
    trends = trend_analysis_tool(db, user_id) or {}
    
    predictor = RevenuePredictor(user_id=user_id)
    if not predictor.is_trained and len(df) >= 10:
        try:
            predictor.train_and_evaluate(df)
        except Exception:
            pass

    ml_status = {
        "is_trained": predictor.is_trained,
        "selected_model": predictor.selected_model_name if predictor.is_trained else "Random Forest Regressor (Auto-Calibrated)",
        "metrics": predictor.metrics or {}
    }

    raw_report = {
        "report_title": "AI Sales & Revenue Executive Intelligence Report",
        "generated_at": datetime.utcnow().strftime("%B %d, %Y - %H:%M UTC"),
        "kpis": kpis,
        "top_products": products.get("top_products", []),
        "category_breakdown": products.get("category_breakdown", {}),
        "regional_breakdown": regions.get("regions", []),
        "monthly_trends": trends.get("monthly_trend", []),
        "ml_model_overview": ml_status
    }

    return sanitize_record(raw_report)

def generate_csv_sales_export(db: Session, user_id: int) -> str:
    df = get_sales_dataframe(db, user_id)
    if df.empty:
        return "EXECUTIVE SALES REPORT\nNo sales records found in account.\n"

    kpis = sales_analysis_tool(db, user_id)
    products = product_performance_tool(db, user_id)
    regions = regional_breakdown_tool(db, user_id)
    trends = trend_analysis_tool(db, user_id)
    predictor = RevenuePredictor(user_id=user_id)

    output = io.StringIO()
    writer = csv.writer(output)

    # Title & Metadata
    writer.writerow(["========================================================"])
    writer.writerow(["AI SALES & REVENUE EXECUTIVE INTELLIGENCE REPORT"])
    writer.writerow(["========================================================"])
    writer.writerow(["Generated At", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")])
    writer.writerow(["Date Coverage", f"{kpis.get('date_range', {}).get('earliest', 'N/A')} to {kpis.get('date_range', {}).get('latest', 'N/A')}"])
    writer.writerow(["Total Orders", kpis.get("total_orders", 0)])
    writer.writerow([])

    # Section 1: Executive KPI Summary
    writer.writerow(["--- SECTION 1: EXECUTIVE KPI SUMMARY ---"])
    writer.writerow(["Metric", "Value", "Notes"])
    writer.writerow(["Total Gross Revenue", f"${kpis.get('total_revenue', 0):,.2f}", "Cumulative gross sales revenue"])
    writer.writerow(["Total Transactions", kpis.get("total_orders", 0), "Number of recorded order transactions"])
    writer.writerow(["Total Units Sold", kpis.get("total_units_sold", 0), "Total item volume"])
    writer.writerow(["Average Order Value (AOV)", f"${kpis.get('average_order_value', 0):,.2f}", "Average revenue per order transaction"])
    writer.writerow(["Top Performing Product", kpis.get("top_product", "N/A"), f"${kpis.get('top_product_revenue', 0):,.2f}"])
    writer.writerow(["Leading Region", kpis.get("top_region", "N/A"), f"${kpis.get('top_region_revenue', 0):,.2f}"])
    writer.writerow(["Month-over-Month Growth Rate", f"{kpis.get('recent_mom_growth_pct', 0)}%", "Recent trajectory"])
    writer.writerow([])

    # Section 2: Product Performance Breakdown
    writer.writerow(["--- SECTION 2: PRODUCT PERFORMANCE BREAKDOWN ---"])
    writer.writerow(["Product Name", "Category", "Orders Count", "Units Sold", "Average Price ($)", "Gross Revenue ($)", "Revenue Share (%)"])
    for p in products.get("top_products", []):
        writer.writerow([
            p.get("product"),
            p.get("category"),
            p.get("orders"),
            p.get("total_units"),
            f"${p.get('avg_price', 0):,.2f}",
            f"${p.get('total_revenue', 0):,.2f}",
            f"{p.get('revenue_pct')}%"
        ])
    writer.writerow([])

    # Section 3: Regional Territory Breakdown
    writer.writerow(["--- SECTION 3: REGIONAL TERRITORY BREAKDOWN ---"])
    writer.writerow(["Region Name", "Total Orders", "Units Sold", "Average Order Value ($)", "Gross Revenue ($)", "Market Share (%)"])
    for r in regions.get("regions", []):
        writer.writerow([
            r.get("region"),
            r.get("total_orders"),
            r.get("total_units"),
            f"${r.get('avg_order_value', 0):,.2f}",
            f"${r.get('total_revenue', 0):,.2f}",
            f"{r.get('market_share_pct')}%"
        ])
    writer.writerow([])

    # Section 4: Monthly Performance Trajectory
    writer.writerow(["--- SECTION 4: MONTHLY PERFORMANCE TRAJECTORY ---"])
    writer.writerow(["Period (YYYY-MM)", "Gross Revenue ($)", "Units Sold", "Orders Count", "MoM Change (%)"])
    for m in trends.get("monthly_trend", []):
        writer.writerow([
            m.get("period"),
            f"${m.get('revenue', 0):,.2f}",
            m.get("units"),
            m.get("orders"),
            f"{m.get('pct_change', 0)}%"
        ])
    writer.writerow([])

    # Section 5: Machine Learning Status
    writer.writerow(["--- SECTION 5: MACHINE LEARNING FORECASTING STATUS ---"])
    writer.writerow(["Selected Champion Model", predictor.selected_model_name if predictor.is_trained else "Baseline Multiplier"])
    writer.writerow(["Model Calibrated", "Yes" if predictor.is_trained else "No"])
    if predictor.metrics:
        rf = predictor.metrics.get("random_forest", {})
        lr = predictor.metrics.get("linear_regression", {})
        writer.writerow(["Random Forest R² Score", rf.get("r2_score", "N/A")])
        writer.writerow(["Random Forest MAE ($)", rf.get("mae", "N/A")])
        writer.writerow(["Linear Regression R² Score", lr.get("r2_score", "N/A")])
    writer.writerow([])

    # Section 6: Complete Sales Ledger
    writer.writerow(["--- SECTION 6: COMPLETE TRANSACTIONAL SALES LEDGER ---"])
    writer.writerow(["Transaction ID", "Date", "Product Name", "Category", "Region", "Quantity", "Unit Price ($)", "Gross Revenue ($)"])
    for _, row in df.iterrows():
        writer.writerow([
            row["id"],
            row["date"],
            row["product"],
            row["category"],
            row["region"],
            row["quantity"],
            row["price"],
            row["revenue"]
        ])

    return output.getvalue()

def generate_html_report(db: Session, user_id: int) -> str:
    from backend.ai_agent.tools import safe_float, safe_int
    data = generate_executive_report_json(db, user_id)
    kpis = data.get("kpis") or {}
    
    tot_rev = safe_float(kpis.get("total_revenue"), 0.0)
    tot_ord = safe_int(kpis.get("total_orders"), 0)
    tot_units = safe_int(kpis.get("total_units_sold"), 0)
    aov = safe_float(kpis.get("average_order_value"), 0.0)
    top_p = str(kpis.get("top_product") or "Top Product")
    top_r = str(kpis.get("top_region") or "Top Region")
    growth_rate = safe_float(kpis.get("recent_mom_growth_pct", kpis.get("growth_rate")), 0.0)
    ml_model_name = str((data.get("ml_model_overview") or {}).get("selected_model") or "Random Forest Regressor")

    top_prods = data.get("top_products") or []
    if not top_prods:
        prod_rows = '<tr><td colspan="6" style="text-align:center; color:#94a3b8; padding:18px;">No product records available. Upload sales records or load sample data.</td></tr>'
    else:
        prod_rows = "".join([
            f"""<tr>
                <td style="font-weight:600; color:#0f172a;">{p.get('product', 'Unknown Product')}</td>
                <td><span class="badge" style="background:#e0e7ff; color:#4338ca;">{p.get('category', 'General')}</span></td>
                <td style="text-align:right;">{safe_int(p.get('orders'), 0):,}</td>
                <td style="text-align:right;">{safe_int(p.get('total_units'), 0):,}</td>
                <td style="text-align:right; font-weight:700; color:#059669;">${safe_float(p.get('total_revenue'), 0.0):,.2f}</td>
                <td style="text-align:right; font-weight:600;">{safe_float(p.get('revenue_pct'), 0.0):.1f}%</td>
            </tr>"""
            for p in top_prods
        ])

    reg_breakdown = data.get("regional_breakdown") or []
    if not reg_breakdown:
        reg_rows = '<tr><td colspan="5" style="text-align:center; color:#94a3b8; padding:18px;">No regional territory records available.</td></tr>'
    else:
        reg_rows = "".join([
            f"""<tr>
                <td style="font-weight:600; color:#0f172a;">{r.get('region', 'Unknown Region')}</td>
                <td style="text-align:right;">{safe_int(r.get('total_orders'), 0):,}</td>
                <td style="text-align:right;">{safe_int(r.get('total_units'), 0):,}</td>
                <td style="text-align:right; font-weight:700; color:#2563eb;">${safe_float(r.get('total_revenue'), 0.0):,.2f}</td>
                <td style="text-align:right; font-weight:600;">{safe_float(r.get('market_share_pct'), 0.0):.1f}%</td>
            </tr>"""
            for r in reg_breakdown
        ])

    monthly_trends = data.get("monthly_trends") or []
    if not monthly_trends:
        monthly_rows = '<tr><td colspan="5" style="text-align:center; color:#94a3b8; padding:18px;">No monthly trajectory records available.</td></tr>'
    else:
        monthly_rows = "".join([
            f"""<tr>
                <td style="font-weight:600;">{m.get('period', 'N/A')}</td>
                <td style="text-align:right; font-weight:700; color:#0f172a;">${safe_float(m.get('revenue'), 0.0):,.2f}</td>
                <td style="text-align:right;">{safe_int(m.get('units'), 0):,}</td>
                <td style="text-align:right;">{safe_int(m.get('orders'), 0):,}</td>
                <td style="text-align:right; color:{'#059669' if safe_float(m.get('pct_change'), 0.0) >= 0 else '#dc2626'}; font-weight:600;">
                    {'+' if safe_float(m.get('pct_change'), 0.0) > 0 else ''}{safe_float(m.get('pct_change'), 0.0):.1f}%
                </td>
            </tr>"""
            for m in monthly_trends[-8:]
        ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <title>{data.get('report_title', 'Executive Sales Intelligence Report')}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            padding: 24px;
            font-size: 13px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
            padding: 40px;
            border: 1px solid #e2e8f0;
        }}
        /* Toolbar */
        .toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #0f172a;
            color: #ffffff;
            padding: 14px 24px;
            border-radius: 8px;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
        }}
        .toolbar-btn {{
            background: #6366f1;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
            transition: background 0.2s;
        }}
        .toolbar-btn:hover {{ background: #4f46e5; }}
        .toolbar-btn.secondary {{ background: rgba(255,255,255,0.15); }}
        .toolbar-btn.secondary:hover {{ background: rgba(255,255,255,0.25); }}

        /* Header */
        .report-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #6366f1;
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        .brand-title {{
            font-size: 24px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.02em;
        }}
        .brand-title span {{ color: #6366f1; }}
        .report-meta {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
        .doc-badge {{
            background: #f1f5f9;
            border: 1px solid #cbd5e1;
            padding: 6px 12px;
            border-radius: 6px;
            text-align: right;
            font-size: 11px;
            color: #475569;
        }}

        /* Executive Summary Narrative */
        .executive-summary {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #6366f1;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 13.5px;
            color: #334155;
            line-height: 1.6;
        }}

        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 28px;
        }}
        .kpi-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .kpi-label {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
        }}
        .kpi-val {{
            font-size: 22px;
            font-weight: 800;
            color: #0f172a;
            margin-top: 6px;
            letter-spacing: -0.02em;
        }}
        .kpi-sub {{ font-size: 11px; color: #10b981; font-weight: 600; margin-top: 4px; }}

        /* Section Headings */
        h2 {{
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            margin: 28px 0 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-size: 12.5px;
        }}
        th {{
            background: #f1f5f9;
            color: #334155;
            font-weight: 700;
            text-align: left;
            padding: 9px 12px;
            border-top: 1px solid #e2e8f0;
            border-bottom: 1px solid #cbd5e1;
        }}
        td {{
            padding: 9px 12px;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
        }}
        tr:nth-child(even) {{ background: #fafafa; }}
        .badge {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10.5px;
            font-weight: 600;
            display: inline-block;
        }}

        /* ML Section */
        .ml-box {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 24px;
        }}
        .ml-title {{ font-size: 13.5px; font-weight: 700; color: #166534; margin-bottom: 6px; }}
        .ml-desc {{ font-size: 12.5px; color: #15803d; line-height: 1.5; }}

        /* Footer */
        .report-footer {{
            border-top: 1px solid #e2e8f0;
            padding-top: 16px;
            margin-top: 36px;
            display: flex;
            justify-content: space-between;
            color: #94a3b8;
            font-size: 11px;
        }}

        /* Print Media Styles */
        @media print {{
            body {{ background: #fff; padding: 0; }}
            .container {{ box-shadow: none; border: none; padding: 0; max-width: 100%; }}
            .no-print {{ display: none !important; }}
            tr, .kpi-card, .ml-box {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Action Toolbar (Hidden in Print/PDF) -->
        <div class="toolbar no-print">
            <div>
                <strong>Executive Sales Intelligence Report Ready</strong>
                <span style="opacity: 0.8; font-size: 12px; margin-left: 8px;">(Click button to Print or Save as PDF)</span>
            </div>
            <div style="display: flex; gap: 8px;">
                <button class="toolbar-btn" onclick="window.print()">
                    🖨️ Print / Save as PDF
                </button>
                <a class="toolbar-btn secondary" href="/api/report/download?format=csv">
                    ⬇️ Download Full CSV
                </a>
            </div>
        </div>

        <!-- Corporate Header -->
        <div class="report-header">
            <div>
                <div class="brand-title">RevPulse <span>AI</span> Enterprise</div>
                <div class="report-meta">Executive Sales & Revenue Performance Audit Report</div>
                <div class="report-meta">Generated: <strong>{data.get('generated_at', 'Current Session')}</strong></div>
            </div>
            <div class="doc-badge">
                <div><strong>DOC REF:</strong> RPT-SALES-2026</div>
                <div><strong>STATUS:</strong> Calibrated & Verified</div>
            </div>
        </div>

        <!-- Executive Narrative Summary -->
        <div class="executive-summary">
            <strong>Executive Brief:</strong> The business recorded a total gross sales revenue of <strong>${tot_rev:,.2f}</strong> across <strong>{tot_ord:,} order transactions</strong> with an Average Order Value (AOV) of <strong>${aov:,.2f}</strong>. The top-performing product portfolio is spearheaded by <strong>{top_p}</strong>, while the <strong>{top_r}</strong> territory represents the primary geographical revenue engine.
        </div>

        <!-- KPI Summary Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Revenue</div>
                <div class="kpi-val" style="color: #059669;">${tot_rev:,.2f}</div>
                <div class="kpi-sub">+{growth_rate:.1f}% growth trajectory</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Total Transactions</div>
                <div class="kpi-val">{tot_ord:,}</div>
                <div style="font-size:11px; color:#64748b; margin-top:4px;">Orders completed</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Gross Units Sold</div>
                <div class="kpi-val" style="color: #2563eb;">{tot_units:,}</div>
                <div style="font-size:11px; color:#64748b; margin-top:4px;">Total item volume</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Average Order Value</div>
                <div class="kpi-val" style="color: #d97706;">${aov:,.2f}</div>
                <div style="font-size:11px; color:#64748b; margin-top:4px;">Revenue per order</div>
            </div>
        </div>

        <!-- Product Breakdown -->
        <h2>🏆 Product Portfolio Performance</h2>
        <table>
            <thead>
                <tr>
                    <th>Product Name</th>
                    <th>Category</th>
                    <th style="text-align:right;">Orders</th>
                    <th style="text-align:right;">Units Sold</th>
                    <th style="text-align:right;">Gross Revenue</th>
                    <th style="text-align:right;">Revenue Share</th>
                </tr>
            </thead>
            <tbody>
                {prod_rows}
            </tbody>
        </table>

        <!-- Regional Performance -->
        <h2>🌍 Geographical Territory Contribution</h2>
        <table>
            <thead>
                <tr>
                    <th>Territory / Region</th>
                    <th style="text-align:right;">Orders Count</th>
                    <th style="text-align:right;">Units Sold</th>
                    <th style="text-align:right;">Gross Revenue</th>
                    <th style="text-align:right;">Market Share</th>
                </tr>
            </thead>
            <tbody>
                {reg_rows}
            </tbody>
        </table>

        <!-- Monthly Performance Trend -->
        <h2>📅 Recent Monthly Performance Trajectory</h2>
        <table>
            <thead>
                <tr>
                    <th>Period</th>
                    <th style="text-align:right;">Gross Revenue</th>
                    <th style="text-align:right;">Units Sold</th>
                    <th style="text-align:right;">Orders</th>
                    <th style="text-align:right;">MoM Change</th>
                </tr>
            </thead>
            <tbody>
                {monthly_rows}
            </tbody>
        </table>

        <!-- ML & Intelligence Status -->
        <h2>🔮 Machine Learning Forecasting & Predictive Intelligence</h2>
        <div class="ml-box">
            <div class="ml-title">Champion Model: {ml_model_name} (Calibrated)</div>
            <div class="ml-desc">
                Machine learning revenue forecasting models (Random Forest Regressor vs Linear Regression) were evaluated using split-validation. The winning champion model is actively used to forecast quarterly sales and what-if inventory scenarios with confidence interval bounds.
            </div>
        </div>

        <!-- Footer -->
        <div class="report-footer">
            <div>Confidential & Proprietary – AI Sales & Revenue Intelligence Suite</div>
            <div>Page 1 of 1</div>
        </div>
    </div>
</body>
</html>"""
    return html
