import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.db import get_db
from backend.database.models import User, Prediction
from backend.schemas.prediction_schema import (
    PredictionRequest,
    PredictionResponse,
    TrainModelResponse,
    PredictionRecordResponse
)
from backend.services.auth_service import get_current_user
from backend.services.data_processing import get_sales_dataframe
from backend.ml.predictor import RevenuePredictor

router = APIRouter(prefix="", tags=["ML Revenue Prediction"])

@router.post("/api/predict", response_model=PredictionResponse)
def generate_prediction(
    req: PredictionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    predictor = RevenuePredictor(user_id=user.id)
    if not predictor.is_trained:
        df = get_sales_dataframe(db, user.id)
        if len(df) >= 10:
            predictor.train_and_evaluate(df)

    res = predictor.predict(
        product=req.product,
        region=req.region,
        quantity=req.quantity,
        price=req.price,
        target_date=req.target_date,
        requested_model=req.model_name
    )

    # Save to prediction history
    pred_record = Prediction(
        user_id=user.id,
        product=req.product,
        region=req.region,
        target_date=req.target_date,
        input_features_json=json.dumps(res["input_summary"]),
        predicted_revenue=res["predicted_revenue"],
        model_name=res["model_used"],
        metrics_json=json.dumps(res.get("confidence_interval", {}))
    )
    db.add(pred_record)
    db.commit()

    return PredictionResponse(
        predicted_revenue=res["predicted_revenue"],
        model_used=res["model_used"],
        input_summary=res["input_summary"],
        confidence_interval=res["confidence_interval"],
        created_at=datetime.utcnow().isoformat()
    )

@router.post("/api/ml/train", response_model=TrainModelResponse)
def train_and_compare_models(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    df = get_sales_dataframe(db, user.id)
    if len(df) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"At least 10 sales records are required to train ML models. Current count: {len(df)}. Please upload data or load demo records."
        )

    try:
        predictor = RevenuePredictor(user_id=user.id)
        eval_result = predictor.train_and_evaluate(df)

        return TrainModelResponse(
            status="success",
            message="Successfully trained and evaluated Linear Regression and Random Forest models.",
            training_samples=eval_result["training_samples"],
            test_samples=eval_result["test_samples"],
            models=eval_result["models"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {str(e)}"
        )

@router.get("/api/ml/model-info")
def get_model_information(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    predictor = RevenuePredictor(user_id=user.id)
    if not predictor.is_trained:
        df = get_sales_dataframe(db, user.id)
        if len(df) >= 10:
            predictor.train_and_evaluate(df)

    return {
        "is_trained": predictor.is_trained,
        "selected_model": predictor.selected_model_name,
        "metrics": predictor.metrics,
        "feature_importance": predictor.feature_importance
    }

@router.get("/api/predictions", response_model=List[PredictionRecordResponse])
def get_prediction_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    records = db.query(Prediction).filter(
        Prediction.user_id == user.id
    ).order_by(Prediction.id.desc()).limit(limit).all()

    return [
        PredictionRecordResponse(
            id=r.id,
            product=r.product,
            region=r.region,
            target_date=r.target_date,
            predicted_revenue=r.predicted_revenue,
            model_name=r.model_name,
            created_at=r.created_at.isoformat() if r.created_at else ""
        )
        for r in records
    ]
