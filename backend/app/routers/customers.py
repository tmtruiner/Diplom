from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.customers_repository import CustomersRepository

router = APIRouter(
    prefix="/api/customers",
    tags=["customers"],
)


@router.get("")
def get_customers(
    search: str | None = Query(default=None),
    risk_group: str | None = Query(default=None),
    segment: str | None = Query(default=None),
    recommendation: str | None = Query(default=None),
    main_risk_factor: str | None = Query(default=None),
    min_probability: float | None = Query(default=None, ge=0, le=1),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    repository = CustomersRepository(db)

    return repository.get_customers(
        search=search,
        risk_group=risk_group,
        segment=segment,
        recommendation=recommendation,
        main_risk_factor=main_risk_factor,
        min_probability=min_probability,
        limit=limit,
        offset=offset,
    )

@router.get("/filter-options")
def get_customer_filter_options(
    db: Session = Depends(get_db),
):
    repository = CustomersRepository(db)
    return repository.get_filter_options()

@router.get("/{customer_id}")
def get_customer_detail(
    customer_id: str,
    db: Session = Depends(get_db),
):
    repository = CustomersRepository(db)
    customer = repository.get_customer_detail(customer_id)

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer
