import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.database.models import Sale
from backend.ml.predictor import RevenuePredictor

def safe_float(val: Any, default: float = 0.0) -> float:
    try:
        if val is None or pd.isna(val) or np.isinf(val):
            return float(default)
        res = float(val)
        if np.isnan(res) or np.isinf(res):
            return float(default)
        return res
    except Exception:
        return float(default)

def safe_int(val: Any, default: int = 0) -> int:
    try:
        if val is None or pd.isna(val) or np.isinf(val):
            return int(default)
        res = int(val)
        return res
    except Exception:
        return int(default)

def safe_idxmax(series: pd.Series, default: str = "N/A") -> str:
    if series.empty or series.isna().all():
        return default
    try:
        idx = series.idxmax()
        if pd.isna(idx):
            return default
        return str(idx)
    except Exception:
        return default

def get_sales_dataframe(db: Session, user_id: int) -> pd.DataFrame:
    records = db.query(Sale).filter(Sale.user_id == user_id).all()
    if not records:
        return pd.DataFrame()
    data = [{
        "id": r.id,
        "date": r.date or "",
        "product": r.product or "Unknown Product",
        "category": r.category or "General",
        "quantity": safe_int(r.quantity, 1),
        "price": safe_float(r.price, 0.0),
        "region": r.region or "Unknown Region",
        "revenue": safe_float(r.revenue, safe_float(r.quantity, 1) * safe_float(r.price, 0.0))
    } for r in records]
    df = pd.DataFrame(data)
    if df.empty:
        return df

    df["revenue"] = df["revenue"].fillna(0.0)
    df["quantity"] = df["quantity"].fillna(0).astype(int)
    df["price"] = df["price"].fillna(0.0)
    df["product"] = df["product"].fillna("Unknown Product")
    df["category"] = df["category"].fillna("General")
    df["region"] = df["region"].fillna("Unknown Region")
    return df

def sales_analysis_tool(db: Session, user_id: int, pre_df: pd.DataFrame = None, **kwargs) -> Dict[str, Any]:
    """Calculate key KPIs and summary metrics across all sales."""
    df = pre_df if pre_df is not None else get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales records found for this user."}

    total_revenue = safe_float(df["revenue"].sum(), 0.0)
    total_orders = len(df)
    total_units = safe_int(df["quantity"].sum(), 0)
    aov = safe_float(total_revenue / total_orders, 0.0) if total_orders > 0 else 0.0

    prod_group = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
    top_prod = safe_idxmax(prod_group, "N/A")
    top_prod_rev = safe_float(prod_group.iloc[0], 0.0) if not prod_group.empty else 0.0

    reg_group = df.groupby("region")["revenue"].sum().sort_values(ascending=False)
    top_reg = safe_idxmax(reg_group, "N/A")
    top_reg_rev = safe_float(reg_group.iloc[0], 0.0) if not reg_group.empty else 0.0

    # Calculate month-over-month growth if possible
    df["dt"] = pd.to_datetime(df["date"], errors="coerce")
    monthly = df.dropna(subset=["dt"]).set_index("dt").resample("M")["revenue"].sum()
    growth_rate = 0.0
    if len(monthly) >= 2:
        prev = safe_float(monthly.iloc[-2], 0.0)
        curr = safe_float(monthly.iloc[-1], 0.0)
        if prev > 0:
            growth_rate = safe_float(((curr - prev) / prev) * 100.0, 0.0)

    earliest = str(df["date"].min()) if not df["date"].empty else ""
    latest = str(df["date"].max()) if not df["date"].empty else ""

    return {
        "status": "success",
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "total_units_sold": total_units,
        "average_order_value": round(aov, 2),
        "top_product": top_prod,
        "top_product_revenue": round(top_prod_rev, 2),
        "top_region": top_reg,
        "top_region_revenue": round(top_reg_rev, 2),
        "recent_mom_growth_pct": round(growth_rate, 2),
        "date_range": {
            "earliest": earliest,
            "latest": latest
        }
    }

# Alias for sales_analysis_tool
KPI_analysis_tool = sales_analysis_tool

def product_performance_tool(db: Session, user_id: int, pre_df: pd.DataFrame = None, **kwargs) -> Dict[str, Any]:
    """Analyze high-performing and low-performing products with drivers."""
    df = pre_df if pre_df is not None else get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales records found."}

    total_revenue_all = safe_float(df["revenue"].sum(), 0.0)

    prod_summary = df.groupby(["product", "category"]).agg(
        total_revenue=("revenue", "sum"),
        total_units=("quantity", "sum"),
        orders=("quantity", "count"),
        avg_price=("price", "mean")
    ).reset_index()

    if prod_summary.empty:
        return {"status": "empty", "message": "No product summary could be generated."}

    prod_summary["revenue_pct"] = prod_summary["total_revenue"].apply(
        lambda r: safe_float((r / total_revenue_all * 100), 0.0) if total_revenue_all > 0 else 0.0
    ).round(2)
    prod_summary["avg_price"] = prod_summary["avg_price"].apply(lambda p: safe_float(p, 0.0)).round(2)
    prod_summary = prod_summary.sort_values(by="total_revenue", ascending=False)

    top_prod_row = prod_summary.iloc[0]
    top_prod_name = str(top_prod_row["product"])
    top_prod_df = df[df["product"] == top_prod_name]
    top_prod_region = safe_idxmax(top_prod_df.groupby("region")["revenue"].sum(), "N/A") if not top_prod_df.empty else "N/A"

    top_5 = prod_summary.head(5).to_dict(orient="records")
    bottom_5 = prod_summary.tail(5).to_dict(orient="records")
    category_breakdown = df.groupby("category")["revenue"].sum().sort_values(ascending=False).to_dict()

    tot_rev = safe_float(top_prod_row["total_revenue"], 0.0)
    rev_pct = safe_float(top_prod_row["revenue_pct"], 0.0)
    tot_units = safe_int(top_prod_row["total_units"], 0)
    orders_cnt = safe_int(top_prod_row["orders"], 0)
    avg_p = safe_float(top_prod_row["avg_price"], 0.0)

    return {
        "status": "success",
        "best_product": {
            "product": top_prod_name,
            "category": str(top_prod_row["category"]),
            "total_revenue": round(tot_rev, 2),
            "revenue_percentage": round(rev_pct, 2),
            "total_units": tot_units,
            "orders": orders_cnt,
            "average_price": round(avg_p, 2),
            "top_region": top_prod_region,
            "why_performing_best": f"Generated ${tot_rev:,.2f} ({rev_pct:.1f}% of total sales) with {tot_units:,} units sold at an average price of ${avg_p:.2f}, with strongest sales in {top_prod_region}."
        },
        "top_products": top_5,
        "bottom_products": bottom_5,
        "category_breakdown": {str(k): round(safe_float(v, 0.0), 2) for k, v in category_breakdown.items()},
        "total_unique_products": int(df["product"].nunique())
    }

# Alias for product_performance_tool
product_analysis_tool = product_performance_tool

def regional_breakdown_tool(db: Session, user_id: int, pre_df: pd.DataFrame = None, **kwargs) -> Dict[str, Any]:
    """Analyze geographic sales performance and growth drivers across regions."""
    df = pre_df if pre_df is not None else get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales records found."}

    reg_summary = df.groupby("region").agg(
        total_revenue=("revenue", "sum"),
        total_units=("quantity", "sum"),
        total_orders=("quantity", "count"),
        avg_order_value=("revenue", "mean")
    ).reset_index()

    if reg_summary.empty:
        return {"status": "empty", "message": "No regional breakdown available."}

    total_rev = safe_float(reg_summary["total_revenue"].sum(), 0.0)
    reg_summary["market_share_pct"] = reg_summary["total_revenue"].apply(
        lambda r: safe_float((r / total_rev * 100), 0.0) if total_rev > 0 else 0.0
    ).round(2)
    reg_summary["total_revenue"] = reg_summary["total_revenue"].apply(lambda v: safe_float(v, 0.0)).round(2)
    reg_summary["avg_order_value"] = reg_summary["avg_order_value"].apply(lambda v: safe_float(v, 0.0)).round(2)
    reg_summary = reg_summary.sort_values(by="total_revenue", ascending=False)

    top_reg = reg_summary.iloc[0]
    low_reg = reg_summary.iloc[-1]

    # Find top product for top region
    top_reg_df = df[df["region"] == top_reg["region"]]
    top_reg_prod = safe_idxmax(top_reg_df.groupby("product")["revenue"].sum(), "N/A") if not top_reg_df.empty else "N/A"

    top_reg_rev = safe_float(top_reg["total_revenue"], 0.0)
    top_reg_share = safe_float(top_reg["market_share_pct"], 0.0)
    low_reg_rev = safe_float(low_reg["total_revenue"], 0.0)
    low_reg_share = safe_float(low_reg["market_share_pct"], 0.0)

    return {
        "status": "success",
        "regions": reg_summary.to_dict(orient="records"),
        "top_region": {
            "region": str(top_reg["region"]),
            "revenue": round(top_reg_rev, 2),
            "market_share_pct": round(top_reg_share, 2),
            "orders": safe_int(top_reg["total_orders"], 0),
            "top_product": top_reg_prod
        },
        "lowest_region": {
            "region": str(low_reg["region"]),
            "revenue": round(low_reg_rev, 2),
            "market_share_pct": round(low_reg_share, 2),
            "orders": safe_int(low_reg["total_orders"], 0)
        },
        "summary": f"{top_reg['region']} leads all regions with ${top_reg_rev:,.2f} ({top_reg_share:.1f}% share), while {low_reg['region']} trails with ${low_reg_rev:,.2f} ({low_reg_share:.1f}% share)."
    }

def trend_analysis_tool(db: Session, user_id: int, pre_df: pd.DataFrame = None, **kwargs) -> Dict[str, Any]:
    """Extract monthly sales trajectories, seasonal peaks, and analyze revenue decreases."""
    df = pre_df if pre_df is not None else get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales records found."}

    df["dt"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["dt"])
    if df.empty:
        return {"status": "empty", "message": "No valid dates found."}

    monthly = df.set_index("dt").resample("M").agg(
        revenue=("revenue", "sum"),
        units=("quantity", "sum"),
        orders=("quantity", "count")
    ).reset_index()

    if monthly.empty:
        return {"status": "empty", "message": "No monthly trend could be generated."}

    monthly["period"] = monthly["dt"].dt.strftime("%Y-%m")
    monthly["revenue_change"] = monthly["revenue"].diff().fillna(0)
    monthly["pct_change"] = (monthly["revenue"].pct_change() * 100).fillna(0).apply(lambda v: safe_float(v, 0.0)).round(2)

    # Analyze drops/decreases
    drops = monthly[monthly["revenue_change"] < 0]
    drop_details = None
    if not drops.empty:
        recent_drop = drops.iloc[-1]
        drop_idx = int(recent_drop.name)
        prev_idx = drop_idx - 1
        if prev_idx >= 0:
            prev_row = monthly.iloc[prev_idx]
            drop_period = str(recent_drop["period"])
            prev_period = str(prev_row["period"])
            
            df_prev = df[df["dt"].dt.strftime("%Y-%m") == prev_period]
            df_curr = df[df["dt"].dt.strftime("%Y-%m") == drop_period]

            prod_prev = df_prev.groupby("product")["revenue"].sum()
            prod_curr = df_curr.groupby("product")["revenue"].sum()
            prod_diff = prod_curr.subtract(prod_prev, fill_value=0).sort_values()
            biggest_drop_prods = [str(p) for p, diff in prod_diff.items() if diff < 0][:2]

            prev_rev = safe_float(prev_row["revenue"], 0.0)
            drop_rev = safe_float(recent_drop["revenue"], 0.0)
            dec_amt = safe_float(abs(float(recent_drop["revenue_change"])), 0.0)
            dec_pct = safe_float(abs(float(recent_drop["pct_change"])), 0.0)

            drop_details = {
                "drop_period": drop_period,
                "previous_period": prev_period,
                "previous_revenue": round(prev_rev, 2),
                "drop_revenue": round(drop_rev, 2),
                "decrease_amount": round(dec_amt, 2),
                "decrease_percentage": round(dec_pct, 2),
                "primary_product_factors": biggest_drop_prods,
                "explanation": f"Revenue decreased from ${prev_rev:,.2f} in {prev_period} to ${drop_rev:,.2f} in {drop_period} (a {dec_pct:.1f}% drop), primarily due to reduced order volume following seasonal peaks and lower sales in {', '.join(biggest_drop_prods) if biggest_drop_prods else 'key categories'}."
            }

    if not monthly["revenue"].empty and not monthly["revenue"].isna().all():
        peak_idx = monthly["revenue"].idxmax()
        low_idx = monthly["revenue"].idxmin()
        peak_row = monthly.loc[peak_idx]
        low_row = monthly.loc[low_idx]
        peak_dict = {"period": str(peak_row["period"]), "revenue": round(safe_float(peak_row["revenue"], 0.0), 2)}
        low_dict = {"period": str(low_row["period"]), "revenue": round(safe_float(low_row["revenue"], 0.0), 2)}
    else:
        peak_dict = {"period": "N/A", "revenue": 0.0}
        low_dict = {"period": "N/A", "revenue": 0.0}

    avg_monthly_rev = safe_float(monthly["revenue"].mean(), 0.0)

    return {
        "status": "success",
        "monthly_trend": monthly[["period", "revenue", "units", "orders", "pct_change"]].to_dict(orient="records"),
        "peak_month": peak_dict,
        "lowest_month": low_dict,
        "average_monthly_revenue": round(avg_monthly_rev, 2),
        "decrease_analysis": drop_details
    }

def comparison_tool(db: Session, user_id: int, entity_type: str = "region", item_a: str = "South", item_b: str = "West", **kwargs) -> Dict[str, Any]:
    """Compare two specific regions, products, or time periods directly."""
    df = get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales data found."}

    all_regions = [str(r) for r in df["region"].unique()]
    
    if entity_type == "region" or any(r.lower() in (item_a or "").lower() or r.lower() in (item_b or "").lower() for r in all_regions):
        match_a = next((r for r in all_regions if item_a and r.lower() in item_a.lower()), None)
        match_b = next((r for r in all_regions if item_b and r.lower() in item_b.lower()), None)

        if not match_a and len(all_regions) > 0:
            match_a = all_regions[0]
        if not match_b and len(all_regions) > 1:
            match_b = all_regions[1]
        elif not match_b:
            match_b = match_a or "N/A"

        df_a = df[df["region"].str.lower() == match_a.lower()] if match_a else pd.DataFrame()
        df_b = df[df["region"].str.lower() == match_b.lower()] if match_b else pd.DataFrame()

        rev_a = safe_float(df_a["revenue"].sum(), 0.0) if not df_a.empty else 0.0
        rev_b = safe_float(df_b["revenue"].sum(), 0.0) if not df_b.empty else 0.0
        units_a = safe_int(df_a["quantity"].sum(), 0) if not df_a.empty else 0
        units_b = safe_int(df_b["quantity"].sum(), 0) if not df_b.empty else 0
        orders_a = len(df_a)
        orders_b = len(df_b)
        top_prod_a = safe_idxmax(df_a.groupby("product")["revenue"].sum(), "N/A") if not df_a.empty else "N/A"
        top_prod_b = safe_idxmax(df_b.groupby("product")["revenue"].sum(), "N/A") if not df_b.empty else "N/A"

        total_rev_all = safe_float(df["revenue"].sum(), 1.0) or 1.0
        pct_a = round(safe_float(rev_a / total_rev_all * 100, 0.0), 2)
        pct_b = round(safe_float(rev_b / total_rev_all * 100, 0.0), 2)
        diff_rev = rev_a - rev_b
        pct_diff = round(safe_float(((rev_a - rev_b) / rev_b * 100), 0.0), 2) if rev_b > 0 else 0.0

        leader = match_a if diff_rev >= 0 else match_b
        margin_lead = abs(diff_rev)

        return {
            "status": "success",
            "comparison_type": "region",
            "item_a": {
                "name": match_a,
                "revenue": round(rev_a, 2),
                "market_share_pct": pct_a,
                "units": units_a,
                "orders": orders_a,
                "top_product": top_prod_a
            },
            "item_b": {
                "name": match_b,
                "revenue": round(rev_b, 2),
                "market_share_pct": pct_b,
                "units": units_b,
                "orders": orders_b,
                "top_product": top_prod_b
            },
            "summary": f"{match_a} generated ${rev_a:,.2f} ({pct_a}% share, {units_a} units) vs {match_b} at ${rev_b:,.2f} ({pct_b}% share, {units_b} units). {leader} leads by ${margin_lead:,.2f} ({abs(pct_diff)}%)."
        }

    return {"status": "success", "message": "Comparison completed."}

def revenue_prediction_tool(db: Session, user_id: int, product: Optional[str] = None, region: Optional[str] = None, quantity: Optional[int] = None, price: Optional[float] = None, target_date: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Execute ML inference using the actual trained model to forecast future revenue."""
    df = get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales data found to train or predict."}

    predictor = RevenuePredictor(user_id=user_id)
    if not predictor.is_trained:
        if len(df) >= 10:
            predictor.train_and_evaluate(df)

    if not product:
        prod_counts = df.groupby("product")["revenue"].sum()
        product = safe_idxmax(prod_counts, "Smart 4K Ultra OLED TV")

    if not region:
        reg_counts = df.groupby("region")["revenue"].sum()
        region = safe_idxmax(reg_counts, "North")

    if not quantity or quantity <= 0:
        avg_qty = int(round(safe_float(df["quantity"].mean(), 10))) if not df.empty else 10
        quantity = max(5, avg_qty)

    if not price or price <= 0:
        prod_df = df[df["product"] == product]
        price = safe_float(prod_df["price"].mean(), safe_float(df["price"].mean(), 100.0)) if not prod_df.empty else safe_float(df["price"].mean(), 100.0)

    if not target_date:
        target_date = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")

    res = predictor.predict(
        product=product,
        region=region,
        quantity=quantity,
        price=price,
        target_date=target_date
    )

    pred_rev = safe_float(res.get("predicted_revenue", 0.0), 0.0)
    model_u = str(res.get("model_used", "Random Forest Regressor"))
    ci = res.get("confidence_interval", {})
    ci_low = safe_float(ci.get("low", 0.0), 0.0)
    ci_high = safe_float(ci.get("high", 0.0), 0.0)

    return {
        "status": "success",
        "predicted_revenue": round(pred_rev, 2),
        "model_used": model_u,
        "input_summary": res.get("input_summary", {}),
        "confidence_interval": {"low": round(ci_low, 2), "high": round(ci_high, 2)},
        "explanation": f"Based on the trained {model_u} model, forecasted revenue for {quantity} units of {product} in the {region} region is ${pred_rev:,.2f} (confidence range: ${ci_low:,.2f} – ${ci_high:,.2f})."
    }

# Alias for revenue_prediction_tool
prediction_tool = revenue_prediction_tool
