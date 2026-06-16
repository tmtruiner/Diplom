from datetime import datetime, timedelta

from airflow.decorators import dag, task


default_args = {
    "owner": "churn-analytics",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="churn_scoring_pipeline",
    default_args=default_args,
    description="Batch inference pipeline for churn prediction, segmentation and recommendations",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["churn", "ml", "scoring"],
)
def churn_scoring_pipeline():
    @task
    def run_batch_scoring():
        from src.pipeline import run_scoring_pipeline

        run_scoring_pipeline()

    run_batch_scoring()


churn_scoring_pipeline()
