from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.recommendations_repository import RecommendationsRepository

router = APIRouter(
    prefix="/api/recommendations",
    tags=["recommendations"],
)


@router.get("")
def get_recommendations(
    db: Session = Depends(get_db),
):
    repository = RecommendationsRepository(db)
    return repository.get_recommendations()


@router.get("/{recommendation_type}/customers")
def get_recommendation_customers(
    recommendation_type: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    repository = RecommendationsRepository(db)

    return repository.get_recommendation_customers(
        recommendation_type=recommendation_type,
        limit=limit,
        offset=offset,
    )