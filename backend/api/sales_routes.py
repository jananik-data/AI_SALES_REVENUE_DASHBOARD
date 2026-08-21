from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, List
from backend.database.db import get_db
from backend.database.models import User, Sale
from backend.schemas.sales_schema import UploadResponse, SalesListResponse, SaleResponse
from backend.services.auth_service import get_current_user
from backend.services.data_processing import (
    parse_sales_file,
    save_dataframe_to_db,
    generate_sample_sales_data,
    get_sales_dataframe
)
from backend.ml.predictor import RevenuePredictor

router = APIRouter(prefix="/api/sales", tags=["Sales Management"])

@router.post("/upload", response_model=UploadResponse)
async def upload_sales_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not file.filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Only CSV (.csv) or Excel (.xlsx, .xls) files are supported."
        )

    try:
        content = await file.read()
        df, stats = parse_sales_file(content, file.filename)
        inserted_count = save_dataframe_to_db(df, user.id, db)

        # Trigger background model training if data volume is sufficient
        if inserted_count >= 10:
            try:
                predictor = RevenuePredictor(user_id=user.id)
                predictor.train_and_evaluate(df)
            except Exception:
                pass

        sample_preview = df.head(5).to_dict(orient="records")

        return UploadResponse(
            status="success",
            message=f"Successfully processed {stats['processed_rows']} sales records from {file.filename}.",
            records_processed=stats["processed_rows"],
            duplicates_removed=stats["duplicates_removed"],
            missing_values_handled=stats["missing_values_handled"],
            total_sales_inserted=inserted_count,
            sample_preview=sample_preview
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data processing failed: {str(e)}"
        )

@router.post("/load-demo", response_model=UploadResponse)
def load_sample_demo_data(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Load 1,200+ realistic transaction records for the current user."""
    df = generate_sample_sales_data(num_records=1200)
    inserted_count = save_dataframe_to_db(df, user.id, db)

    # Train ML models
    try:
        predictor = RevenuePredictor(user_id=user.id)
        predictor.train_and_evaluate(df)
    except Exception:
        pass

    return UploadResponse(
        status="success",
        message="Successfully loaded 1,200 sample transactions spanning 2024-2026 across 5 regions.",
        records_processed=len(df),
        duplicates_removed=0,
        missing_values_handled=0,
        total_sales_inserted=inserted_count,
        sample_preview=df.head(5).to_dict(orient="records")
    )

@router.get("", response_model=SalesListResponse)
def get_sales_records(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    search: Optional[str] = None,
    product: Optional[str] = None,
    region: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    query = db.query(Sale).filter(Sale.user_id == user.id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Sale.product.ilike(s)) | (Sale.region.ilike(s)) | (Sale.category.ilike(s)))

    if product:
        query = query.filter(Sale.product == product)

    if region:
        query = query.filter(Sale.region == region)

    if category:
        query = query.filter(Sale.category == category)

    if start_date:
        query = query.filter(Sale.date >= start_date)

    if end_date:
        query = query.filter(Sale.date <= end_date)

    total = query.count()
    records = query.order_by(Sale.date.desc(), Sale.id.desc()).offset((page - 1) * limit).limit(limit).all()

    return SalesListResponse(
        total=total,
        page=page,
        limit=limit,
        items=[SaleResponse.model_validate(r) for r in records]
    )

@router.delete("/{sale_id}")
def delete_sale_record(
    sale_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    record = db.query(Sale).filter(Sale.id == sale_id, Sale.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Sale record not found.")

    db.delete(record)
    db.commit()
    return {"status": "success", "message": f"Sale record #{sale_id} deleted."}

@router.delete("/clear-all/records")
def clear_all_sales_records(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    deleted_count = db.query(Sale).filter(Sale.user_id == user.id).delete()
    db.commit()
    return {"status": "success", "message": f"Cleared {deleted_count} records."}

@router.get("/export/csv")
def export_sales_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    from backend.services.report_service import generate_csv_sales_export
    csv_data = generate_csv_sales_export(db, user.id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sales_data_export.csv"}
    )
