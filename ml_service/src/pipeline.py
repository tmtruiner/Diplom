import os
from datetime import datetime

import mlflow
import pandas as pd
from sqlalchemy import text

from src.churn_model import score_customers, train_and_register_churn_model
from src.customer_clustering import build_customer_segments
from src.database import get_engine
from src.feature_engineering import prepare_features
from src.recommendation_rules import build_customer_recommendations
from src.risk_rules import (
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

N_CLUSTERS = int(os.getenv("N_CLUSTERS", "4"))


def load_raw_customers() -> pd.DataFrame:
    engine = get_engine()

    query = text("""
        SELECT
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
    """)

    return pd.read_sql(query, engine)


def save_predictions(scored_df: pd.DataFrame) -> None:
    engine = get_engine()

    records = scored_df[
        [
            "customer_id",
            "churn_probability",
            "risk_group",
            "main_risk_factor",
            "estimated_total_charge",
        ]
    ].to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM predictions"))

        if records:
            connection.execute(
                text("""
                    INSERT INTO predictions (
                        customer_id,
                        churn_probability,
                        risk_group,
                        main_risk_factor,
                        estimated_total_charge
                    )
                    VALUES (
                        :customer_id,
                        :churn_probability,
                        :risk_group,
                        :main_risk_factor,
                        :estimated_total_charge
                    )
                """),
                records,
            )


def save_segments(segments_df: pd.DataFrame) -> None:
    engine = get_engine()

    records = segments_df[
        [
            "customer_id",
            "segment_id",
            "segment_name",
        ]
    ].to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM customer_segments"))

        if records:
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


def save_recommendations(recommendations_df: pd.DataFrame) -> None:
    engine = get_engine()

    records = recommendations_df[
        [
            "customer_id",
            "recommendation_type",
            "recommendation_reason",
            "priority",
        ]
    ].to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM customer_recommendations"))

        if records:
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


def save_scoring_job(training_result: dict, status: str = "success") -> None:
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
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
        )


def run_weekly_pipeline() -> None:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    print("Starting weekly churn ML pipeline...")

    raw_df = load_raw_customers()

    if raw_df.empty:
        raise ValueError("client_records_raw is empty. Nothing to train on.")

    print(f"Loaded raw customers: {len(raw_df)}")

    prepared_df = prepare_features(raw_df)

    print("Training and registering model in MLflow...")

    training_result = train_and_register_churn_model(
        df=prepared_df,
        experiment_name=EXPERIMENT_NAME,
        registered_model_name=REGISTERED_MODEL_NAME,
    )

    print(
        "Model registered. "
        f"run_id={training_result['run_id']}, "
        f"model_uri={training_result['model_uri']}"
    )

    scored_df = score_customers(
        df=prepared_df,
        model_uri=training_result["model_uri"],
    )

    scored_df = enrich_predictions(scored_df)

    print("Building customer segments...")

    segments_df = build_customer_segments(customers_df=scored_df)
    
    print("Building customer recommendations...")

    recommendations_df = build_customer_recommendations(scored_df)

    print("Saving results to PostgreSQL...")

    save_predictions(scored_df)
    save_segments(segments_df)
    save_recommendations(recommendations_df)
    save_scoring_job(training_result, status="success")

    print("Weekly churn ML pipeline finished successfully.")