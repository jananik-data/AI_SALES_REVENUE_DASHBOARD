import io
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from backend.database.models import Sale

COLUMN_SYNONYMS = {
    "date": ["date", "order_date", "transaction_date", "sale_date", "timestamp"],
    "product": ["product", "product_name", "item", "item_name", "product_title"],
    "category": ["category", "product_category", "department", "genre", "segment"],
    "quantity": ["quantity", "qty", "units", "units_sold", "volume", "amount"],
    "price": ["price", "unit_price", "rate", "cost_per_unit", "selling_price"],
    "region": ["region", "location", "territory", "zone", "state", "city", "market"],
    "revenue": ["revenue", "total_revenue", "total_sales", "sales", "total_amount", "amount_total"]
}

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map flexible user column names to standardized names."""
    df_cols = {col: str(col).strip().lower().replace(" ", "_") for col in df.columns}
    df = df.rename(columns=df_cols)

    mapping = {}
    for standard_col, synonyms in COLUMN_SYNONYMS.items():
        for col in df.columns:
            if col in synonyms:
                mapping[col] = standard_col
                break

    df = df.rename(columns=mapping)
    return df

def parse_date_safely(date_val) -> str:
    """Parse various date formats into standardized ISO string YYYY-MM-DD."""
    if pd.isna(date_val):
        return datetime.utcnow().strftime("%Y-%m-%d")
    
    # If already datetime
    if isinstance(date_val, (datetime, pd.Timestamp)):
        return date_val.strftime("%Y-%m-%d")
    
    val_str = str(date_val).strip()
    formats_to_try = [
        "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y",
        "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%d-%b-%Y", "%b %d, %Y"
    ]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(val_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    try:
        parsed = pd.to_datetime(val_str, errors="coerce")
        if pd.notna(parsed):
            return parsed.strftime("%Y-%m-%d")
    except Exception:
        pass

    return datetime.utcnow().strftime("%Y-%m-%d")

def clean_and_preprocess_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean, impute missing values, extract date features, and calculate revenue."""
    initial_count = len(df)
    
    # 1. Standardize columns
    df = standardize_columns(df)

    # Check minimum required columns
    required = ["product", "region"]
    for req in required:
        if req not in df.columns:
            raise ValueError(f"Missing required column: '{req}'. Detected columns: {list(df.columns)}")

    # 2. Duplicate removal
    df = df.drop_duplicates()
    duplicates_removed = initial_count - len(df)

    # 3. Missing value imputation
    missing_count = int(df.isnull().sum().sum())
    
    if "date" not in df.columns:
        df["date"] = datetime.utcnow().strftime("%Y-%m-%d")
    else:
        df["date"] = df["date"].apply(parse_date_safely)

    if "category" not in df.columns:
        df["category"] = "General"
    else:
        df["category"] = df["category"].fillna("General").astype(str).str.strip()

    df["product"] = df["product"].fillna("Unknown Product").astype(str).str.strip()
    df["region"] = df["region"].fillna("General Region").astype(str).str.strip()

    # Helper to parse formatted numeric strings ($1,250.00, 1,000, etc.)
    def parse_numeric(series, default=0.0):
        if series is None:
            return pd.Series(default, index=df.index)
        s_str = series.astype(str).str.replace(r"[^\d.-]", "", regex=True)
        return pd.to_numeric(s_str, errors="coerce").fillna(default)

    # Quantity handling
    if "quantity" not in df.columns:
        df["quantity"] = 1
    else:
        df["quantity"] = parse_numeric(df["quantity"], 1.0)
        df["quantity"] = df["quantity"].apply(lambda q: max(1, int(round(q))))

    # Price handling
    if "price" not in df.columns:
        if "revenue" in df.columns:
            rev_numeric = parse_numeric(df["revenue"], 100.0)
            df["price"] = (rev_numeric / df["quantity"]).round(2)
        else:
            df["price"] = 50.0
    else:
        df["price"] = parse_numeric(df["price"], 50.0)
        df["price"] = df["price"].apply(lambda p: max(0.1, round(float(p), 2)))

    # Revenue calculation
    if "revenue" not in df.columns or df["revenue"].isnull().any():
        df["revenue"] = (df["quantity"] * df["price"]).round(2)
    else:
        df["revenue"] = parse_numeric(df["revenue"], 0.0)
        mask_zero_rev = df["revenue"] <= 0
        df.loc[mask_zero_rev, "revenue"] = (df.loc[mask_zero_rev, "quantity"] * df.loc[mask_zero_rev, "price"]).round(2)

    # Clean extreme negative or infinite values
    df = df[df["quantity"] > 0]
    df = df[df["price"] > 0]
    df = df[df["revenue"] > 0]

    stats = {
        "initial_rows": initial_count,
        "processed_rows": len(df),
        "duplicates_removed": duplicates_removed,
        "missing_values_handled": missing_count
    }
    return df, stats

def parse_sales_file(file_content: bytes, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Parse CSV or Excel byte content into a preprocessed dataframe."""
    filename_lower = filename.lower()
    if filename_lower.endswith(".csv"):
        try:
            df = pd.read_csv(io.BytesIO(file_content), encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_content), encoding="latin1")
    elif filename_lower.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(file_content))
    else:
        raise ValueError("Unsupported file format. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file.")

    return clean_and_preprocess_dataframe(df)

def save_dataframe_to_db(df: pd.DataFrame, user_id: int, db: Session) -> int:
    """Save processed dataframe records into database for the user."""
    sales_to_insert = []
    for _, row in df.iterrows():
        sale = Sale(
            user_id=user_id,
            date=str(row["date"]),
            product=str(row["product"]),
            category=str(row["category"]),
            quantity=int(row["quantity"]),
            price=float(row["price"]),
            region=str(row["region"]),
            revenue=float(row["revenue"])
        )
        sales_to_insert.append(sale)

    db.add_all(sales_to_insert)
    db.commit()
    return len(sales_to_insert)

def generate_sample_sales_data(num_records: int = 1200) -> pd.DataFrame:
    """Generate realistic sales dataset for instant demo."""
    random.seed(42)
    np.random.seed(42)

    products_catalog = [
        # Electronics
        {"product": "Smart 4K Ultra OLED TV", "category": "Electronics", "base_price": 899.99, "qty_range": (1, 4)},
        {"product": "Noise-Cancelling Headphones Pro", "category": "Electronics", "base_price": 249.99, "qty_range": (1, 8)},
        {"product": "UltraBook Laptop 16-inch", "category": "Electronics", "base_price": 1299.99, "qty_range": (1, 3)},
        {"product": "Wireless Mechanical Keyboard", "category": "Electronics", "base_price": 119.99, "qty_range": (1, 10)},
        {"product": "Ergonomic Optical Gaming Mouse", "category": "Electronics", "base_price": 69.99, "qty_range": (1, 12)},
        # Apparel
        {"product": "Merino Wool Thermal Jacket", "category": "Apparel", "base_price": 149.50, "qty_range": (1, 6)},
        {"product": "Performance Running Shoes", "category": "Apparel", "base_price": 120.00, "qty_range": (1, 5)},
        {"product": "Classic Fit Cotton Shirt", "category": "Apparel", "base_price": 45.00, "qty_range": (1, 15)},
        {"product": "Breathable Athletic Leggings", "category": "Apparel", "base_price": 55.00, "qty_range": (1, 8)},
        # Home & Living
        {"product": "Robot Vacuum Cleaner X9", "category": "Home & Living", "base_price": 399.00, "qty_range": (1, 3)},
        {"product": "Smart Air Purifier HEPA", "category": "Home & Living", "base_price": 189.00, "qty_range": (1, 5)},
        {"product": "Cast Iron Dutch Oven 6-Qt", "category": "Home & Living", "base_price": 79.99, "qty_range": (1, 6)},
        {"product": "Espresso Coffee Machine Pro", "category": "Home & Living", "base_price": 499.99, "qty_range": (1, 4)},
        # Beauty & Wellness
        {"product": "Hydrating Facial Serum Set", "category": "Beauty & Wellness", "base_price": 38.50, "qty_range": (1, 12)},
        {"product": "Sonic Electric Toothbrush", "category": "Beauty & Wellness", "base_price": 89.90, "qty_range": (1, 7)},
        {"product": "Deep Tissue Massage Gun", "category": "Beauty & Wellness", "base_price": 139.00, "qty_range": (1, 5)},
        # Office & Furniture
        {"product": "Ergonomic Mesh Office Chair", "category": "Office", "base_price": 289.00, "qty_range": (1, 4)},
        {"product": "Dual-Motor Standing Desk 60-inch", "category": "Office", "base_price": 449.00, "qty_range": (1, 2)},
    ]

    regions = ["North", "South", "East", "West", "Central"]
    region_weights = [0.28, 0.22, 0.24, 0.16, 0.10]

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 8, 15)
    days_range = (end_date - start_date).days

    records = []
    for _ in range(num_records):
        prod_info = random.choice(products_catalog)
        region = np.random.choice(regions, p=region_weights)
        
        # Random date with seasonal bump in Nov-Dec (Holiday season)
        random_day = random.randint(0, days_range)
        date_val = start_date + timedelta(days=random_day)
        month = date_val.month
        
        qty_min, qty_max = prod_info["qty_range"]
        # Seasonal multiplier
        seasonal_boost = 1.35 if month in [11, 12] else (1.15 if month in [6, 7] else 1.0)
        
        quantity = max(1, int(random.randint(qty_min, qty_max) * (1.0 + (seasonal_boost - 1.0) * 0.5)))
        # Slight price fluctuation (+- 8%)
        price_variation = round(prod_info["base_price"] * random.uniform(0.92, 1.08), 2)
        revenue = round(quantity * price_variation, 2)

        records.append({
            "date": date_val.strftime("%Y-%m-%d"),
            "product": prod_info["product"],
            "category": prod_info["category"],
            "quantity": quantity,
            "price": price_variation,
            "region": region,
            "revenue": revenue
        })

    df = pd.DataFrame(records)
    # Sort chronologically
    df = df.sort_values(by="date").reset_index(drop=True)
    return df

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
