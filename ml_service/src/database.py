import os

from sqlalchemy import create_engine


def get_database_url() -> str:
    database_url = os.getenv("CHURN_DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "CHURN_DATABASE_URL is not set. "
            "For Docker Compose use: "
            "postgresql+psycopg2://user:password@db:5432/churn_db"
        )

    return database_url


def get_engine():
    return create_engine(get_database_url())