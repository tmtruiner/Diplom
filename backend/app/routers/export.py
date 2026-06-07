from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.export_repository import ExportRepository

router = APIRouter(
    prefix="/api/export",
    tags=["export"],
)


def csv_response(content: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


def json_response(content: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


@router.get("/customers.csv")
def export_customers(db: Session = Depends(get_db)):
    repository = ExportRepository(db)
    content = repository.export_customers_csv()
    return csv_response(content, "customers_export.csv")


@router.get("/high-risk-customers.csv")
def export_high_risk_customers(db: Session = Depends(get_db)):
    repository = ExportRepository(db)
    content = repository.export_high_risk_customers_csv()
    return csv_response(content, "high_risk_customers.csv")


@router.get("/segments.csv")
def export_segments(db: Session = Depends(get_db)):
    repository = ExportRepository(db)
    content = repository.export_segments_csv()
    return csv_response(content, "segments_summary.csv")


@router.get("/recommendations.csv")
def export_recommendations(db: Session = Depends(get_db)):
    repository = ExportRepository(db)
    content = repository.export_recommendations_csv()
    return csv_response(content, "recommendations_plan.csv")


@router.get("/dashboard-summary.json")
def export_dashboard_summary(db: Session = Depends(get_db)):
    repository = ExportRepository(db)
    content = repository.export_dashboard_summary_json()
    return json_response(content, "dashboard_summary.json")