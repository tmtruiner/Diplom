from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.export_repository import CUSTOMER_CSV_HEADERS, ExportRepository

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


def has_customer_export_filter(
    search: str | None,
    risk_group: str | None,
    segment: str | None,
    recommendation: str | None,
    main_risk_factor: str | None,
    min_probability: float | None,
) -> bool:
    return any(
        [
            bool(search and search.strip()),
            bool(risk_group and risk_group != "All"),
            bool(segment and segment != "All"),
            bool(recommendation and recommendation != "All"),
            bool(main_risk_factor and main_risk_factor != "All"),
            bool(min_probability and min_probability > 0),
        ]
    )


@router.get("/customers-filtered.csv")
def export_filtered_customers(
    search: str | None = Query(default=None),
    risk_group: str | None = Query(default=None),
    segment: str | None = Query(default=None),
    recommendation: str | None = Query(default=None),
    main_risk_factor: str | None = Query(default=None),
    min_probability: float | None = Query(default=None, ge=0, le=1),
    fields: list[str] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if not has_customer_export_filter(
        search=search,
        risk_group=risk_group,
        segment=segment,
        recommendation=recommendation,
        main_risk_factor=main_risk_factor,
        min_probability=min_probability,
    ):
        raise HTTPException(
            status_code=400,
            detail="At least one customer export filter is required",
        )

    if fields:
        unknown_fields = [
            field for field in fields if field not in CUSTOMER_CSV_HEADERS
        ]

        if unknown_fields:
            raise HTTPException(
                status_code=400,
                detail="Unknown customer export fields",
            )

    repository = ExportRepository(db)
    content = repository.export_filtered_customers_csv(
        search=search,
        risk_group=risk_group,
        segment=segment,
        recommendation=recommendation,
        main_risk_factor=main_risk_factor,
        min_probability=min_probability,
        fields=fields,
    )
    return csv_response(content, "customers_filtered_export.csv")


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


@router.get("/dashboard-summary.csv")
def export_dashboard_summary_csv(db: Session = Depends(get_db)):
    repository = ExportRepository(db)
    content = repository.export_dashboard_summary_csv()
    return csv_response(content, "dashboard_summary.csv")
