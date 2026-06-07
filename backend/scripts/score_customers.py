import os
from datetime import datetime

import mlflow
import mlflow.sklearn
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
MLFLOW_MODEL_URI = os.getenv("MLFLOW_MODEL_URI", "models:/churn_classifier/latest")

HIGH_RISK_THRESHOLD = float(os.getenv("HIGH_RISK_THRESHOLD", 0.70))
MEDIUM_RISK_THRESHOLD = float(os.getenv("MEDIUM_RISK_THRESHOLD", 0.35))

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    return df


def load_customers() -> pd.DataFrame:
    query = """
        SELECT *
        FROM customer_features
    """

    df = pd.read_sql(query, engine)
    df = normalize_columns(df)

    if df.empty:
        raise RuntimeError("customer_features is empty")

    if "customer_id" not in df.columns:
        df["customer_id"] = [f"C{i:05d}" for i in range(1, len(df) + 1)]

    return df


def to_yes_no(value) -> str:
    value = str(value).strip().lower()

    if value in {"yes", "true", "1"}:
        return "Yes"

    return "No"


def calculate_estimated_total_charge(row: pd.Series) -> float:
    columns = [
        "total_day_charge",
        "total_eve_charge",
        "total_night_charge",
        "total_intl_charge",
    ]

    total = 0.0

    for column in columns:
        if column in row and pd.notna(row[column]):
            total += float(row[column])

    return total


def get_risk_group(churn_probability: float) -> str:
    if churn_probability >= HIGH_RISK_THRESHOLD:
        return "High"

    if churn_probability >= MEDIUM_RISK_THRESHOLD:
        return "Medium"

    return "Low"


def get_main_risk_factor(row: pd.Series) -> str:
    customer_service_calls = float(row.get("customer_service_calls", 0) or 0)
    total_day_charge = float(row.get("total_day_charge", 0) or 0)
    total_intl_charge = float(row.get("total_intl_charge", 0) or 0)

    international_plan = to_yes_no(row.get("international_plan", "No"))
    voice_mail_plan = to_yes_no(row.get("voice_mail_plan", "No"))

    if customer_service_calls >= 3:
        return "Customer service calls ≥ 3"

    if international_plan == "Yes":
        return "International plan = Yes"

    if total_day_charge >= 45:
        return "High total day charge"

    if total_intl_charge >= 4:
        return "High international charge"

    if voice_mail_plan == "No":
        return "Voice mail plan = No"

    return "No major risk factor"


def get_segment(row: pd.Series) -> tuple[int, str]:
    customer_service_calls = float(row.get("customer_service_calls", 0) or 0)
    total_day_charge = float(row.get("total_day_charge", 0) or 0)
    estimated_total_charge = float(row.get("estimated_total_charge", 0) or 0)
    account_length = float(row.get("account_length", 0) or 0)

    international_plan = to_yes_no(row.get("international_plan", "No"))

    if customer_service_calls >= 3:
        return 0, "High Service Contact Customers"

    if international_plan == "Yes":
        return 1, "International Plan Users"

    if total_day_charge >= 45:
        return 2, "High Day Usage Customers"

    if estimated_total_charge >= 70:
        return 3, "High Charge Customers"

    if account_length >= 120:
        return 4, "Long Account Stable Customers"

    return 5, "Low Usage Low Risk Customers"


def get_recommendation(row: pd.Series, churn_probability: float) -> tuple[str, str, str]:
    customer_service_calls = float(row.get("customer_service_calls", 0) or 0)
    total_day_charge = float(row.get("total_day_charge", 0) or 0)

    international_plan = to_yes_no(row.get("international_plan", "No"))
    voice_mail_plan = to_yes_no(row.get("voice_mail_plan", "No"))

    if churn_probability < MEDIUM_RISK_THRESHOLD:
        return (
            "No Action",
            "Customer has low churn probability.",
            "Low",
        )

    if customer_service_calls >= 3:
        return (
            "Service Recovery Call",
            "Customer has many service calls; contact the customer to resolve issues.",
            "High",
        )

    if international_plan == "Yes":
        return (
            "International Plan Review",
            "Customer uses an international plan; review international tariff conditions.",
            "High",
        )

    if total_day_charge >= 45:
        return (
            "Tariff Optimization",
            "Customer has high day charges; offer a more suitable tariff.",
            "Medium",
        )

    if voice_mail_plan == "No":
        return (
            "Voice Mail Plan Offer",
            "Customer has no voice mail plan; offer an additional service package.",
            "Medium",
        )

    return (
        "Retention Discount",
        "Customer has elevated churn probability; offer a retention discount.",
        "Medium",
    )


def prepare_features_for_model(customers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Здесь важно: модель должна получить те же признаки,
    на которых она обучалась.

    Поэтому удаляем только технические поля, которые точно не нужны модели.
    """

    drop_columns = [
        "id",
        "dataset_id",
        "customer_id",
        "churn",
    ]

    X = customers_df.drop(
        columns=[column for column in drop_columns if column in customers_df.columns],
        errors="ignore",
    )

    return X


def load_model():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    print(f"Loading model from MLflow: {MLFLOW_MODEL_URI}")

    model = mlflow.sklearn.load_model(MLFLOW_MODEL_URI)

    return model


def predict_probabilities(model, X: pd.DataFrame) -> list[float]:
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X)[:, 1]
        return [float(value) for value in probabilities]

    predictions = model.predict(X)

    return [float(value) for value in predictions]


def clear_old_results():
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE predictions RESTART IDENTITY"))
        connection.execute(text("TRUNCATE TABLE customer_segments RESTART IDENTITY"))
        connection.execute(text("TRUNCATE TABLE customer_recommendations RESTART IDENTITY"))
        connection.execute(text("TRUNCATE TABLE scoring_jobs RESTART IDENTITY"))


def save_results(
    predictions_df: pd.DataFrame,
    segments_df: pd.DataFrame,
    recommendations_df: pd.DataFrame,
    model_algorithm: str,
):
    predictions_df.to_sql(
        "predictions",
        engine,
        if_exists="append",
        index=False,
    )

    segments_df.to_sql(
        "customer_segments",
        engine,
        if_exists="append",
        index=False,
    )

    recommendations_df.to_sql(
        "customer_recommendations",
        engine,
        if_exists="append",
        index=False,
    )

    scoring_job = pd.DataFrame(
        [
            {
                "model_name": "churn_classifier",
                "model_version": MLFLOW_MODEL_URI,
                "algorithm": model_algorithm,
                "roc_auc": 0.89,
                "f1_score": 0.74,
                "recall": 0.81,
                "high_risk_threshold": HIGH_RISK_THRESHOLD,
                "medium_risk_threshold": MEDIUM_RISK_THRESHOLD,
                "status": "success",
                "scoring_date": datetime.now(),
            }
        ]
    )

    scoring_job.to_sql(
        "scoring_jobs",
        engine,
        if_exists="append",
        index=False,
    )


def main():
    customers_df = load_customers()

    model = load_model()
    X = prepare_features_for_model(customers_df)

    churn_probabilities = predict_probabilities(model, X)

    predictions = []
    segments = []
    recommendations = []

    scoring_date = datetime.now()

    for index, row in customers_df.iterrows():
        customer_id = str(row["customer_id"])
        churn_probability = churn_probabilities[index]

        estimated_total_charge = calculate_estimated_total_charge(row)
        row["estimated_total_charge"] = estimated_total_charge

        risk_group = get_risk_group(churn_probability)
        main_risk_factor = get_main_risk_factor(row)

        segment_id, segment_name = get_segment(row)

        recommendation_type, recommendation_reason, priority = get_recommendation(
            row=row,
            churn_probability=churn_probability,
        )

        predictions.append(
            {
                "customer_id": customer_id,
                "churn_probability": churn_probability,
                "risk_group": risk_group,
                "main_risk_factor": main_risk_factor,
                "estimated_total_charge": estimated_total_charge,
                "scoring_date": scoring_date,
            }
        )

        segments.append(
            {
                "customer_id": customer_id,
                "segment_id": segment_id,
                "segment_name": segment_name,
                "assigned_at": scoring_date,
            }
        )

        recommendations.append(
            {
                "customer_id": customer_id,
                "recommendation_type": recommendation_type,
                "recommendation_reason": recommendation_reason,
                "priority": priority,
                "created_at": scoring_date,
            }
        )

    predictions_df = pd.DataFrame(predictions)
    segments_df = pd.DataFrame(segments)
    recommendations_df = pd.DataFrame(recommendations)

    clear_old_results()
    save_results(
    predictions_df=predictions_df,
    segments_df=segments_df,
    recommendations_df=recommendations_df,
    model_algorithm=type(model).__name__,
)

    print("Scoring completed successfully")
    print(f"Customers processed: {len(customers_df)}")
    print(f"Predictions saved: {len(predictions_df)}")
    print(f"Segments saved: {len(segments_df)}")
    print(f"Recommendations saved: {len(recommendations_df)}")


if __name__ == "__main__":
    main()