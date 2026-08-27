from fastapi import HTTPException
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Header
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import User
from backend.services.auth_service import get_user_from_token
from backend.services.report_service import (
    generate_executive_report_json,
    generate_html_report,
    generate_csv_sales_export
)

router = APIRouter(prefix="/api/report", tags=["Executive Reports"])

def extract_token(token: Optional[str], authorization: Optional[str]) -> Optional[str]:
    if token and token.strip():
        return token.strip()
    if authorization and authorization.strip():
        auth = authorization.strip()
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        return auth
    return None

@router.get("/summary")
def get_report_summary(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    try:
        token_str = extract_token(token, authorization)
        user = get_user_from_token(token_str, db)
        return generate_executive_report_json(db, user.id)
    except HTTPException:
        raise
    except Exception:
        return {
            "report_title": "AI Sales & Revenue Executive Intelligence Report",
            "generated_at": datetime.utcnow().strftime("%B %d, %Y - %H:%M UTC"),
            "kpis": {"status": "empty", "total_revenue": 0.0, "total_orders": 0, "average_order_value": 0.0},
            "top_products": [],
            "category_breakdown": {},
            "regional_breakdown": [],
            "monthly_trends": [],
            "ml_model_overview": {"is_trained": False, "selected_model": "Baseline Multiplier", "metrics": {}}
        }

@router.get("/html", response_class=HTMLResponse)
def get_html_report_view(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    try:
        token_str = extract_token(token, authorization)
        user = get_user_from_token(token_str, db)
        html_content = generate_html_report(db, user.id)
        return HTMLResponse(content=html_content, status_code=200)
    except HTTPException:
        raise
    except Exception:
        fallback_html = "<html><body><h2>Executive Sales Report</h2><p>Report is currently initializing. Please refresh or load sales records.</p></body></html>"
        return HTMLResponse(content=fallback_html, status_code=200)

@router.get("/download")
def download_sales_report(
    format: str = "csv",
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    try:
        token_str = extract_token(token, authorization)
        user = get_user_from_token(token_str, db)

        if format == "html":
            content = generate_html_report(db, user.id)
            return Response(
                content=content,
                media_type="text/html",
                headers={"Content-Disposition": "attachment; filename=Executive_Sales_Intelligence_Report.html"}
            )
        else:
            content = generate_csv_sales_export(db, user.id)
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=Executive_Sales_Intelligence_Report.csv"}
            )
    except HTTPException:
        raise
    except Exception:
        return Response(
            content="EXECUTIVE SALES REPORT\nReport is currently unavailable. Please load sales records.\n",
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=Executive_Sales_Intelligence_Report.csv"}
        )
