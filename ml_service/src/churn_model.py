import mlflow
import mlflow.sklearn
import pandas as pd

from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


NUMERIC_FEATURES = [
    "account_length",
    "area_code",
    "number_vmail_messages",
    "total_day_minutes",
    "total_day_calls",
    "total_day_charge",
    "total_eve_minutes",
    "total_eve_calls",
    "total_eve_charge",
    "total_night_minutes",
    "total_night_calls",
    "total_night_charge",
    "total_intl_minutes",
    "total_intl_calls",
    "total_intl_charge",
    "customer_service_calls",
]

CATEGORICAL_FEATURES = [
    "state",
    "international_plan",
    "voice_mail_plan",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def ensure_registered_model_exists(registered_model_name: str) -> None:
    client = MlflowClient()

    try:
        client.get_registered_model(registered_model_name)
        print(f"Registered model already exists: {registered_model_name}")
    except MlflowException:
        client.create_registered_model(registered_model_name)
        print(f"Registered model created: {registered_model_name}")


def create_model_version(
    model_uri: str,
    run_id: str,
    registered_model_name: str,
) -> str:
    client = MlflowClient()

    ensure_registered_model_exists(registered_model_name)

    model_version = client.create_model_version(
        name=registered_model_name,
        source=model_uri,
        run_id=run_id,
    )

    print(
        f"Created model version {model_version.version} "
        f"for model {registered_model_name}"
    )

    return str(model_version.version)


def train_and_register_churn_model(
    training_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    test_df: pd.DataFrame,
    experiment_name: str = "Churn Analytics",
    registered_model_name: str = "churn_prediction_model",
) -> dict:
    for dataset_name, dataset in (
        ("training", training_df),
        ("validation", validation_df),
        ("test", test_df),
    ):
        if "churn" not in dataset.columns:
            raise ValueError(
                f"Column 'churn' is required in the {dataset_name} dataset"
            )

    x_train = training_df[FEATURE_COLUMNS]
    y_train = training_df["churn"].astype(int)
    x_validation = validation_df[FEATURE_COLUMNS]
    y_validation = validation_df["churn"].astype(int)
    x_test = test_df[FEATURE_COLUMNS]
    y_test = test_df["churn"].astype(int)

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", GradientBoostingClassifier(random_state=42)),
        ]
    )

    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name="weekly_churn_training") as run:
        run_id = run.info.run_id

        model.fit(x_train, y_train)

        validation_metrics = evaluate_model(
            model,
            x_validation,
            y_validation,
        )
        test_metrics = evaluate_model(model, x_test, y_test)

        mlflow.log_param("algorithm", "Gradient Boosting")
        mlflow.log_param("random_state", 42)
        mlflow.log_param("training_rows", len(training_df))
        mlflow.log_param("validation_rows", len(validation_df))
        mlflow.log_param("test_rows", len(test_df))
        mlflow.log_param("high_risk_threshold", 0.7)
        mlflow.log_param("medium_risk_threshold", 0.35)
        mlflow.log_param("registered_model_name", registered_model_name)

        for metric_name, metric_value in validation_metrics.items():
            mlflow.log_metric(f"validation_{metric_name}", metric_value)

        for metric_name, metric_value in test_metrics.items():
            mlflow.log_metric(f"test_{metric_name}", metric_value)

        # Важно: модель сначала логируется как артефакт run,
        # а регистрация в Model Registry выполняется отдельно.
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
        )

        model_uri = f"runs:/{run_id}/model"

        model_version = create_model_version(
            model_uri=model_uri,
            run_id=run_id,
            registered_model_name=registered_model_name,
        )

        return {
            "run_id": run_id,
            "model_uri": model_uri,
            "registered_model_name": registered_model_name,
            "model_name": "Churn prediction model",
            "model_version": model_version,
            "algorithm": "Gradient Boosting",
            "roc_auc": test_metrics["roc_auc"],
            "f1_score": test_metrics["f1_score"],
            "recall": test_metrics["recall"],
            "precision": test_metrics["precision"],
            "accuracy": test_metrics["accuracy"],
            "validation_metrics": validation_metrics,
        }


def evaluate_model(model, x: pd.DataFrame, y: pd.Series) -> dict[str, float]:
    probabilities = model.predict_proba(x)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    return {
        "roc_auc": float(roc_auc_score(y, probabilities)),
        "f1_score": float(f1_score(y, predictions, zero_division=0)),
        "recall": float(recall_score(y, predictions, zero_division=0)),
        "precision": float(precision_score(y, predictions, zero_division=0)),
        "accuracy": float(accuracy_score(y, predictions)),
    }


def score_customers(df: pd.DataFrame, model_uri: str) -> pd.DataFrame:
    model = mlflow.sklearn.load_model(model_uri)

    result = df.copy()
    x = result[FEATURE_COLUMNS]

    result["churn_probability"] = model.predict_proba(x)[:, 1]

    return result
