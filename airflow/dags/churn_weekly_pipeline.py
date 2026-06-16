from datetime import datetime, timedelta

from airflow.decorators import dag, task


default_args = {
    "owner": "churn-analytics",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="churn_weekly_pipeline",
    default_args=default_args,
    description="Weekly ML pipeline for churn prediction, segmentation and recommendations",
    start_date=datetime(2026, 1, 1),
    schedule="@weekly",
    catchup=False,
    tags=["churn", "ml", "weekly"],
)
def churn_weekly_pipeline():
    @task
    def run_ml_pipeline():
        from src.pipeline import run_weekly_pipeline

        run_weekly_pipeline()

    run_ml_pipeline()


churn_weekly_pipeline()
