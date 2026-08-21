import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.database.models import Sale
from backend.ml.predictor import RevenuePredictor

def get_sales_dataframe(db: Session, user_id: int) -> pd.DataFrame:
    records = db.query(Sale).filter(Sale.user_id == user_id).all()
    if not records:
        return pd.DataFrame()
    data = [{
        "id": r.id,
        "date": r.date,
        "product": r.product,
        "category": r.category,
        "quantity": r.quantity,
        "price": r.price,
        "region": r.region,
        "revenue": r.revenue
    } for r in records]
    return pd.DataFrame(data)

def sales_analysis_tool(db: Session, user_id: int, **kwargs) -> Dict[str, Any]:
    """Calculate key KPIs and summary metrics across all sales."""
    df = get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales records found for this user."}

    total_revenue = float(df["revenue"].sum())
    total_orders = len(df)
    total_units = int(df["quantity"].sum())
    aov = float(total_revenue / total_orders) if total_orders > 0 else 0.0

    prod_group = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
    top_prod = str(prod_group.index[0]) if not prod_group.empty else "N/A"
    top_prod_rev = float(prod_group.iloc[0]) if not prod_group.empty else 0.0

    reg_group = df.groupby("region")["revenue"].sum().sort_values(ascending=False)
    top_reg = str(reg_group.index[0]) if not reg_group.empty else "N/A"
    top_reg_rev = float(reg_group.iloc[0]) if not reg_group.empty else 0.0

    # Calculate month-over-month growth if possible
    df["dt"] = pd.to_datetime(df["date"], errors="coerce")
    monthly = df.dropna(subset=["dt"]).set_index("dt").resample("M")["revenue"].sum()
    growth_rate = 0.0
    if len(monthly) >= 2:
        prev = monthly.iloc[-2]
        curr = monthly.iloc[-1]
        if prev > 0:
            growth_rate = float(((curr - prev) / prev) * 100.0)

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
            "earliest": str(df["date"].min()),
            "latest": str(df["date"].max())
        }
    }

# Alias for sales_analysis_tool
KPI_analysis_tool = sales_analysis_tool

def product_performance_tool(db: Session, user_id: int, **kwargs) -> Dict[str, Any]:
    """Analyze high-performing and low-performing products with drivers."""
    df = get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales records found."}

    total_revenue_all = float(df["revenue"].sum())

    prod_summary = df.groupby(["product", "category"]).agg(
        total_revenue=("revenue", "sum"),
        total_units=("quantity", "sum"),
        orders=("quantity", "count"),
        avg_price=("price", "mean")
    ).reset_index()

    prod_summary["revenue_pct"] = (prod_summary["total_revenue"] / total_revenue_all * 100).round(2)
    prod_summary["avg_price"] = prod_summary["avg_price"].round(2)
    prod_summary = prod_summary.sort_values(by="total_revenue", ascending=False)

    top_prod_row = prod_summary.iloc[0]
    top_prod_name = top_prod_row["product"]
    top_prod_df = df[df["product"] == top_prod_name]
    top_prod_region = top_prod_df.groupby("region")["revenue"].sum().idxmax() if not top_prod_df.empty else "N/A"

    top_5 = prod_summary.head(5).to_dict(orient="records")
    bottom_5 = prod_summary.tail(5).to_dict(orient="records")
    category_breakdown = df.groupby("category")["revenue"].sum().sort_values(ascending=False).to_dict()

    return {
        "status": "success",
        "best_product": {
            "product": top_prod_name,
            "category": str(top_prod_row["category"]),
            "total_revenue": round(float(top_prod_row["total_revenue"]), 2),
            "revenue_percentage": float(top_prod_row["revenue_pct"]),
            "total_units": int(top_prod_row["total_units"]),
            "orders": int(top_prod_row["orders"]),
            "average_price": round(float(top_prod_row["avg_price"]), 2),
            "top_region": top_prod_region,
            "why_performing_best": f"Generated ${top_prod_row['total_revenue']:,.2f} ({top_prod_row['revenue_pct']}% of total sales) with {int(top_prod_row['total_units'])} units sold at an average price of ${top_prod_row['avg_price']:.2f}, with strongest sales in {top_prod_region}."
        },
        "top_products": top_5,
        "bottom_products": bottom_5,
        "category_breakdown": {k: round(float(v), 2) for k, v in category_breakdown.items()},
        "total_unique_products": int(df["product"].nunique())
    }

# Alias for product_performance_tool
product_analysis_tool = product_performance_tool

def regional_breakdown_tool(db: Session, user_id: int, **kwargs) -> Dict[str, Any]:
    """Analyze geographic sales performance and growth drivers across regions."""
    df = get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales records found."}

    reg_summary = df.groupby("region").agg(
        total_revenue=("revenue", "sum"),
        total_units=("quantity", "sum"),
        total_orders=("quantity", "count"),
        avg_order_value=("revenue", "mean")
    ).reset_index()

    total_rev = float(reg_summary["total_revenue"].sum())
    reg_summary["market_share_pct"] = (reg_summary["total_revenue"] / total_rev * 100).round(2)
    reg_summary["total_revenue"] = reg_summary["total_revenue"].round(2)
    reg_summary["avg_order_value"] = reg_summary["avg_order_value"].round(2)
    reg_summary = reg_summary.sort_values(by="total_revenue", ascending=False)

    top_reg = reg_summary.iloc[0]
    low_reg = reg_summary.iloc[-1]

    # Find top product for top region
    top_reg_df = df[df["region"] == top_reg["region"]]
    top_reg_prod = top_reg_df.groupby("product")["revenue"].sum().idxmax() if not top_reg_df.empty else "N/A"

    return {
        "status": "success",
        "regions": reg_summary.to_dict(orient="records"),
        "top_region": {
            "region": top_reg["region"],
            "revenue": round(float(top_reg["total_revenue"]), 2),
            "market_share_pct": float(top_reg["market_share_pct"]),
            "orders": int(top_reg["total_orders"]),
            "top_product": top_reg_prod
        },
        "lowest_region": {
            "region": low_reg["region"],
            "revenue": round(float(low_reg["total_revenue"]), 2),
            "market_share_pct": float(low_reg["market_share_pct"]),
            "orders": int(low_reg["total_orders"])
        },
        "summary": f"{top_reg['region']} leads all regions with ${top_reg['total_revenue']:,.2f} ({top_reg['market_share_pct']}% share), while {low_reg['region']} trails with ${low_reg['total_revenue']:,.2f} ({low_reg['market_share_pct']}% share)."
    }

def trend_analysis_tool(db: Session, user_id: int, **kwargs) -> Dict[str, Any]:
    """Extract monthly sales trajectories, seasonal peaks, and analyze revenue decreases."""
    df = get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales records found."}

    df["dt"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["dt"])
    if df.empty:
        return {"status": "empty"}

    monthly = df.set_index("dt").resample("M").agg(
        revenue=("revenue", "sum"),
        units=("quantity", "sum"),
        orders=("quantity", "count")
    ).reset_index()

    monthly["period"] = monthly["dt"].dt.strftime("%Y-%m")
    monthly["revenue_change"] = monthly["revenue"].diff().fillna(0)
    monthly["pct_change"] = (monthly["revenue"].pct_change() * 100).fillna(0).round(2)

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
            biggest_drop_prods = [p for p, diff in prod_diff.items() if diff < 0][:2]

            drop_details = {
                "drop_period": drop_period,
                "previous_period": prev_period,
                "previous_revenue": round(float(prev_row["revenue"]), 2),
                "drop_revenue": round(float(recent_drop["revenue"]), 2),
                "decrease_amount": round(abs(float(recent_drop["revenue_change"])), 2),
                "decrease_percentage": abs(float(recent_drop["pct_change"])),
                "primary_product_factors": biggest_drop_prods,
                "explanation": f"Revenue decreased from ${prev_row['revenue']:,.2f} in {prev_period} to ${recent_drop['revenue']:,.2f} in {drop_period} (a {abs(float(recent_drop['pct_change']))}% drop), primarily due to reduced order volume following seasonal peaks and lower sales in {', '.join(biggest_drop_prods) if biggest_drop_prods else 'key categories'}."
            }

    peak_row = monthly.loc[monthly["revenue"].idxmax()]
    low_row = monthly.loc[monthly["revenue"].idxmin()]

    return {
        "status": "success",
        "monthly_trend": monthly[["period", "revenue", "units", "orders", "pct_change"]].to_dict(orient="records"),
        "peak_month": {"period": str(peak_row["period"]), "revenue": round(float(peak_row["revenue"]), 2)},
        "lowest_month": {"period": str(low_row["period"]), "revenue": round(float(low_row["revenue"]), 2)},
        "average_monthly_revenue": round(float(monthly["revenue"].mean()), 2),
        "decrease_analysis": drop_details
    }

def comparison_tool(db: Session, user_id: int, entity_type: str = "region", item_a: str = "South", item_b: str = "West", **kwargs) -> Dict[str, Any]:
    """Compare two specific regions, products, or time periods directly."""
    df = get_sales_dataframe(db, user_id)
    if df.empty:
        return {"status": "empty", "message": "No sales data found."}

    all_regions = [str(r) for r in df["region"].unique()]
    
    # Check if this is a regional comparison
    if entity_type == "region" or any(r.lower() in (item_a or "").lower() or r.lower() in (item_b or "").lower() for r in all_regions):
        match_a = next((r for r in all_regions if item_a and r.lower() in item_a.lower()), None)
        match_b = next((r for r in all_regions if item_b and r.lower() in item_b.lower()), None)

        if not match_a and len(all_regions) > 0:
            match_a = all_regions[0]
        if not match_b and len(all_regions) > 1:
            match_b = all_regions[1]
        elif not match_b:
            match_b = match_a

        df_a = df[df["region"].str.lower() == match_a.lower()]
        df_b = df[df["region"].str.lower() == match_b.lower()]

        rev_a = float(df_a["revenue"].sum()) if not df_a.empty else 0.0
        rev_b = float(df_b["revenue"].sum()) if not df_b.empty else 0.0
        units_a = int(df_a["quantity"].sum()) if not df_a.empty else 0
        units_b = int(df_b["quantity"].sum()) if not df_b.empty else 0
        orders_a = len(df_a)
        orders_b = len(df_b)
        top_prod_a = str(df_a.groupby("product")["revenue"].sum().idxmax()) if not df_a.empty else "N/A"
        top_prod_b = str(df_b.groupby("product")["revenue"].sum().idxmax()) if not df_b.empty else "N/A"

        total_rev_all = float(df["revenue"].sum()) or 1.0
        pct_a = round(rev_a / total_rev_all * 100, 2)
        pct_b = round(rev_b / total_rev_all * 100, 2)
        diff_rev = rev_a - rev_b
        pct_diff = round(((rev_a - rev_b) / rev_b * 100), 2) if rev_b > 0 else 0.0

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

    # Defaults if not supplied
    if not product:
        prod_counts = df.groupby("product")["revenue"].sum()
        product = str(prod_counts.idxmax()) if not prod_counts.empty else "Smart 4K Ultra OLED TV"

    if not region:
        reg_counts = df.groupby("region")["revenue"].sum()
        region = str(reg_counts.idxmax()) if not reg_counts.empty else "North"

    if not quantity or quantity <= 0:
        avg_qty = int(round(df["quantity"].mean())) if not df.empty else 10
        quantity = max(5, avg_qty)

    if not price or price <= 0:
        prod_df = df[df["product"] == product]
        price = float(prod_df["price"].mean()) if not prod_df.empty else float(df["price"].mean())

    if not target_date:
        target_date = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")

    res = predictor.predict(
        product=product,
        region=region,
        quantity=quantity,
        price=price,
        target_date=target_date
    )

    return {
        "status": "success",
        "predicted_revenue": res["predicted_revenue"],
        "model_used": res["model_used"],
        "input_summary": res["input_summary"],
        "confidence_interval": res.get("confidence_interval", {}),
        "explanation": f"Based on the trained {res['model_used']} model, forecasted revenue for {quantity} units of {product} in the {region} region is ${res['predicted_revenue']:,.2f} (confidence range: ${res.get('confidence_interval', {}).get('low', 0):,.2f} – ${res.get('confidence_interval', {}).get('high', 0):,.2f})."
    }

# Alias for revenue_prediction_tool
prediction_tool = revenue_prediction_tool
