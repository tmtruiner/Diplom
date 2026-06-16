import os
from datetime import datetime

import mlflow
import pandas as pd
from sqlalchemy import text

from .churn_model import score_customers, train_and_register_churn_model
from .customer_segmentation import build_customer_segments
from .database import get_engine
from .feature_engineering import prepare_features
from .recommendation_rules import build_customer_recommendations
from .risk_rules import (
    HIGH_RISK_THRESHOLD,
    MEDIUM_RISK_THRESHOLD,
    enrich_predictions,
)


MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "Churn Analytics")
REGISTERED_MODEL_NAME = os.getenv(
    "MLFLOW_REGISTERED_MODEL_NAME",
    "churn_prediction_model",
)
MLFLOW_MODEL_URI = os.getenv("MLFLOW_MODEL_URI")

TRAINING_SPLIT = "train"
VALIDATION_SPLIT = "validation"
TEST_SPLIT = "test"
SCORING_SPLIT = "scoring_batch"


def get_scoring_model_uri() -> str:
    if MLFLOW_MODEL_URI:
        return MLFLOW_MODEL_URI

    return f"models:/{REGISTERED_MODEL_NAME}/latest"


def load_customers_by_splits(dataset_splits: list[str]) -> pd.DataFrame:
    engine = get_engine()

    query = text("""
        SELECT
            id,
            customer_id,
            dataset_split,
            state,
            account_length,
            area_code,
            international_plan,
            voice_mail_plan,
            number_vmail_messages,
            total_day_minutes,
            total_day_calls,
            total_day_charge,
            total_eve_minutes,
            total_eve_calls,
            total_eve_charge,
            total_night_minutes,
            total_night_calls,
            total_night_charge,
            total_intl_minutes,
            total_intl_calls,
            total_intl_charge,
            customer_service_calls,
            churn
        FROM client_records_raw
        WHERE dataset_split = ANY(:dataset_splits)
        ORDER BY id
    """)

    return pd.read_sql(
        query,
        engine,
        params={"dataset_splits": dataset_splits},
    )


def create_scoring_job(training_result: dict, status: str = "running") -> int:
    engine = get_engine()

    with engine.begin() as connection:
        scoring_job_id = connection.execute(
            text("""
                INSERT INTO scoring_jobs (
                    model_name,
                    model_version,
                    algorithm,
                    roc_auc,
                    f1_score,
                    recall,
                    high_risk_threshold,
                    medium_risk_threshold,
                    status,
                    scoring_date
                )
                VALUES (
                    :model_name,
                    :model_version,
                    :algorithm,
                    :roc_auc,
                    :f1_score,
                    :recall,
                    :high_risk_threshold,
                    :medium_risk_threshold,
                    :status,
                    :scoring_date
                )
                RETURNING id
            """),
            {
                "model_name": training_result.get(
                    "model_name",
                    "Churn prediction model",
                ),
                "model_version": training_result.get("model_version", "1.0"),
                "algorithm": training_result.get("algorithm", "Gradient Boosting"),
                "roc_auc": training_result.get("roc_auc"),
                "f1_score": training_result.get("f1_score"),
                "recall": training_result.get("recall"),
                "high_risk_threshold": HIGH_RISK_THRESHOLD,
                "medium_risk_threshold": MEDIUM_RISK_THRESHOLD,
                "status": status,
                "scoring_date": datetime.utcnow(),
            },
        ).scalar_one()

    return int(scoring_job_id)


def update_scoring_job_status(scoring_job_id: int, status: str) -> None:
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE scoring_jobs
                SET status = :status
                WHERE id = :scoring_job_id
            """),
            {
                "scoring_job_id": scoring_job_id,
                "status": status,
            },
        )


def save_predictions(connection, scored_df: pd.DataFrame, scoring_job_id: int) -> None:
    scored_df = scored_df.copy()
    scored_df["scoring_job_id"] = scoring_job_id

    records = scored_df[
        [
            "customer_id",
            "scoring_job_id",
            "churn_probability",
            "risk_group",
            "main_risk_factor",
            "estimated_total_charge",
        ]
    ].to_dict(orient="records")

    if not records:
        return

    connection.execute(
        text("""
            INSERT INTO predictions (
                customer_id,
                scoring_job_id,
                churn_probability,
                risk_group,
                main_risk_factor,
                estimated_total_charge
            )
            VALUES (
                :customer_id,
                :scoring_job_id,
                :churn_probability,
                :risk_group,
                :main_risk_factor,
                :estimated_total_charge
            )
        """),
        records,
    )


def save_segments(connection, segments_df: pd.DataFrame) -> None:
    records = segments_df[
        [
            "customer_id",
            "segment_id",
            "segment_name",
        ]
    ].to_dict(orient="records")

    if not records:
        return

    connection.execute(
        text("""
            INSERT INTO customer_segments (
                customer_id,
                segment_id,
                segment_name
            )
            VALUES (
                :customer_id,
                :segment_id,
                :segment_name
            )
        """),
        records,
    )


def save_recommendations(connection, recommendations_df: pd.DataFrame) -> None:
    records = recommendations_df[
        [
            "customer_id",
            "recommendation_type",
            "recommendation_reason",
            "priority",
        ]
    ].to_dict(orient="records")

    if not records:
        return

    connection.execute(
        text("""
            INSERT INTO customer_recommendations (
                customer_id,
                recommendation_type,
                recommendation_reason,
                priority
            )
            VALUES (
                :customer_id,
                :recommendation_type,
                :recommendation_reason,
                :priority
            )
        """),
        records,
    )


def replace_result_tables(
    scored_df: pd.DataFrame,
    segments_df: pd.DataFrame,
    recommendations_df: pd.DataFrame,
    scoring_job_id: int,
) -> None:
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM customer_recommendations"))
        connection.execute(text("DELETE FROM customer_segments"))
        connection.execute(text("DELETE FROM predictions"))

        save_predictions(connection, scored_df, scoring_job_id)
        save_segments(connection, segments_df)
        save_recommendations(connection, recommendations_df)
        connection.execute(
            text("""
                UPDATE scoring_jobs
                SET status = 'success'
                WHERE id = :scoring_job_id
            """),
            {"scoring_job_id": scoring_job_id},
        )


def score_and_save_customers(
    scoring_raw_df: pd.DataFrame,
    model_uri: str,
    scoring_job_id: int,
) -> None:
    if scoring_raw_df.empty:
        raise ValueError("Scoring data is empty.")

    scoring_df = scoring_raw_df.drop(columns=["id", "dataset_split"], errors="ignore")
    prepared_scoring_df = prepare_features(scoring_df)

    print(f"Scoring customers with model_uri={model_uri}...")

    scored_df = score_customers(
        df=prepared_scoring_df,
        model_uri=model_uri,
    )

    scored_df = enrich_predictions(scored_df)

    print("Building customer segments...")

    segments_df = build_customer_segments(customers_df=scored_df)

    print("Building customer recommendations...")

    recommendations_df = build_customer_recommendations(scored_df)

    print("Saving scoring results to PostgreSQL...")

    replace_result_tables(
        scored_df=scored_df,
        segments_df=segments_df,
        recommendations_df=recommendations_df,
        scoring_job_id=scoring_job_id,
    )


def run_scoring_pipeline() -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    print("Starting churn scoring pipeline...")

    scoring_raw_df = load_customers_by_splits([SCORING_SPLIT])

    if scoring_raw_df.empty:
        raise ValueError("Scoring data is empty.")

    print(f"Loaded scoring customers: {len(scoring_raw_df)}")

    model_uri = get_scoring_model_uri()
    scoring_job_id = create_scoring_job(
        {
            "model_name": "Churn prediction model",
            "model_version": model_uri,
            "algorithm": "Gradient Boosting",
            "roc_auc": None,
            "f1_score": None,
            "recall": None,
        },
        status="running",
    )

    print(f"Created scoring job: {scoring_job_id}")

    try:
        score_and_save_customers(
            scoring_raw_df=scoring_raw_df,
            model_uri=model_uri,
            scoring_job_id=scoring_job_id,
        )
    except Exception:
        update_scoring_job_status(scoring_job_id, "failed")
        raise

    print("Churn scoring pipeline finished successfully.")


def run_weekly_pipeline() -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    print("Starting weekly churn ML pipeline...")

    training_raw_df = load_customers_by_splits([TRAINING_SPLIT])
    validation_raw_df = load_customers_by_splits([VALIDATION_SPLIT])
    test_raw_df = load_customers_by_splits([TEST_SPLIT])
    scoring_raw_df = load_customers_by_splits([SCORING_SPLIT])

    datasets = {
        "training": training_raw_df,
        "validation": validation_raw_df,
        "test": test_raw_df,
        "scoring": scoring_raw_df,
    }

    for dataset_name, dataset in datasets.items():
        if dataset.empty:
            raise ValueError(f"{dataset_name.title()} data is empty.")

    print(f"Loaded training customers: {len(training_raw_df)}")
    print(f"Loaded validation customers: {len(validation_raw_df)}")
    print(f"Loaded test customers: {len(test_raw_df)}")
    print(f"Loaded scoring customers: {len(scoring_raw_df)}")

    training_df = training_raw_df.drop(columns=["id", "dataset_split"], errors="ignore")
    validation_df = validation_raw_df.drop(
        columns=["id", "dataset_split"],
        errors="ignore",
    )
    test_df = test_raw_df.drop(columns=["id", "dataset_split"], errors="ignore")
    prepared_training_df = prepare_features(training_df)
    prepared_validation_df = prepare_features(validation_df)
    prepared_test_df = prepare_features(test_df)

    print("Training and registering model in MLflow...")

    training_result = train_and_register_churn_model(
        training_df=prepared_training_df,
        validation_df=prepared_validation_df,
        test_df=prepared_test_df,
        experiment_name=EXPERIMENT_NAME,
        registered_model_name=REGISTERED_MODEL_NAME,
    )

    print(
        "Model registered. "
        f"run_id={training_result['run_id']}, "
        f"model_uri={training_result['model_uri']}"
    )

    print("Creating scoring job...")

    scoring_job_id = create_scoring_job(training_result, status="running")

    print(f"Created scoring job: {scoring_job_id}")

    try:
        score_and_save_customers(
            scoring_raw_df=scoring_raw_df,
            model_uri=training_result["model_uri"],
            scoring_job_id=scoring_job_id,
        )
    except Exception:
        update_scoring_job_status(scoring_job_id, "failed")
        raise

    print("Weekly churn ML pipeline finished successfully.")
