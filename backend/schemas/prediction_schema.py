from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class PredictionRequest(BaseModel):
    product: str
    region: str
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    target_date: str # "YYYY-MM-DD"
    model_name: Optional[str] = "auto" # "linear_regression", "random_forest", or "auto"

class ModelEvaluationMetrics(BaseModel):
    mae: float
    rmse: float
    r2_score: float

class ModelComparison(BaseModel):
    linear_regression: ModelEvaluationMetrics
    random_forest: ModelEvaluationMetrics
    selected_model: str
    feature_importance: Optional[Dict[str, float]] = None

class PredictionResponse(BaseModel):
    predicted_revenue: float
    model_used: str
    input_summary: Dict[str, Any]
    confidence_interval: Optional[Dict[str, float]] = None
    created_at: str

class PredictionRecordResponse(BaseModel):
    id: int
    product: Optional[str]
    region: Optional[str]
    target_date: Optional[str]
    predicted_revenue: float
    model_name: str
    created_at: str

    class Config:
        from_attributes = True

class TrainModelResponse(BaseModel):
    status: str
    message: str
    training_samples: int
    test_samples: int
    models: ModelComparison
