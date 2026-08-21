from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SaleCreate(BaseModel):
    date: str
    product: str
    category: Optional[str] = "General"
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    region: str
    revenue: Optional[float] = None

class SaleResponse(BaseModel):
    id: int
    user_id: int
    date: str
    product: str
    category: str
    quantity: int
    price: float
    region: str
    revenue: float

    class Config:
        from_attributes = True

class SalesListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[SaleResponse]

class UploadResponse(BaseModel):
    status: str
    message: str
    records_processed: int
    duplicates_removed: int
    missing_values_handled: int
    total_sales_inserted: int
    sample_preview: List[Dict[str, Any]]

class KPISummaryResponse(BaseModel):
    total_revenue: float
    total_orders: int
    total_units_sold: int
    average_order_value: float
    top_product: str
    top_product_revenue: float
    top_region: str
    top_region_revenue: float
    growth_rate: float
    gross_margin_pct: float

class TrendPoint(BaseModel):
    period: str # e.g. "2025-01" or "2025-01-15"
    revenue: float
    units: int
    orders: int
    aov: float = 0.0


class ProductStat(BaseModel):
    product: str
    category: str
    revenue: float
    units: int
    orders: int
    percentage: float

class RegionStat(BaseModel):
    region: str
    revenue: float
    units: int
    orders: int
    percentage: float

class CategoryStat(BaseModel):
    category: str
    revenue: float
    units: int
    orders: int
    aov: float
    percentage: float

class DayOfWeekStat(BaseModel):
    day: str
    day_number: int
    revenue: float
    orders: int
    units: int
    percentage: float

