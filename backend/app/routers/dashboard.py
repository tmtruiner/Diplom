from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.dashboard_repository import DashboardRepository

router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"],
)


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    repository = DashboardRepository(db)
    return repository.get_summary()