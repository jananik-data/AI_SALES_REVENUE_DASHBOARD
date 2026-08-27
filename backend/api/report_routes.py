from fastapi import HTTPException
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import User
from backend.services.auth_service import oauth2_scheme, get_user_from_token
from backend.services.report_service import (
    generate_executive_report_json,
    generate_html_report,
    generate_csv_sales_export
)

router = APIRouter(prefix="/api/report", tags=["Executive Reports"])

def resolve_report_user(
    auth_token: Optional[str] = Depends(oauth2_scheme),
    query_token: Optional[str] = Query(None, alias="token"),
    db: Session = Depends(get_db)
) -> User:
    token = auth_token or query_token
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")
    return get_user_from_token(token, db)

@router.get("/summary")
def get_report_summary(
    user: User = Depends(resolve_report_user),
    db: Session = Depends(get_db)
):
    return generate_executive_report_json(db, user.id)

@router.get("/html", response_class=HTMLResponse)
def get_html_report_view(
    user: User = Depends(resolve_report_user),
    db: Session = Depends(get_db)
):
    html_content = generate_html_report(db, user.id)
    return HTMLResponse(content=html_content, status_code=200)

@router.get("/download")
def download_sales_report(
    format: str = "csv",
    user: User = Depends(resolve_report_user),
    db: Session = Depends(get_db)
):
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

