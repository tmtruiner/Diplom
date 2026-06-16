import pandas as pd


HIGH_RISK_THRESHOLD = 0.7
MEDIUM_RISK_THRESHOLD = 0.35


def assign_risk_group(probability: float) -> str:
    if probability >= HIGH_RISK_THRESHOLD:
        return "High"

    if probability >= MEDIUM_RISK_THRESHOLD:
        return "Medium"

    return "Low"


def assign_main_risk_factor(row: pd.Series) -> str:
    if row.get("customer_service_calls", 0) >= 3:
        return "Customer service calls >= 3"

    if row.get("total_day_charge", 0) >= 40:
        return "High day charge"

    if str(row.get("international_plan", "")).lower() in ["yes", "true", "1"]:
        return "International plan"

    if str(row.get("voice_mail_plan", "")).lower() in ["no", "false", "0"]:
        return "No voice mail plan"

    return "Stable customer profile"


def enrich_predictions(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    result["risk_group"] = result["churn_probability"].apply(assign_risk_group)
    result["main_risk_factor"] = result.apply(assign_main_risk_factor, axis=1)

    return result
