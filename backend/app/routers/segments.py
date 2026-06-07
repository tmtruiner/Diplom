from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.segments_repository import SegmentsRepository

router = APIRouter(
    prefix="/api/segments",
    tags=["segments"],
)


@router.get("")
def get_segments(
    db: Session = Depends(get_db),
):
    repository = SegmentsRepository(db)
    return repository.get_segments()


@router.get("/{segment_name}/customers")
def get_segment_customers(
    segment_name: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    repository = SegmentsRepository(db)

    return repository.get_segment_customers(
        segment_name=segment_name,
        limit=limit,
        offset=offset,
    )