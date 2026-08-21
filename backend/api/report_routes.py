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

@router.get("/summary")
def get_report_summary(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    token_str = token or (authorization.replace("Bearer ", "") if authorization else None)
    user = get_user_from_token(token_str, db)
    return generate_executive_report_json(db, user.id)

@router.get("/html", response_class=HTMLResponse)
def get_html_report_view(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    token_str = token or (authorization.replace("Bearer ", "") if authorization else None)
    user = get_user_from_token(token_str, db)
    html_content = generate_html_report(db, user.id)
    return HTMLResponse(content=html_content, status_code=200)

@router.get("/download")
def download_sales_report(
    format: str = "csv",
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    token_str = token or (authorization.replace("Bearer ", "") if authorization else None)
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
