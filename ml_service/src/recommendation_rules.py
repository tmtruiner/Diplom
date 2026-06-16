import pandas as pd

from .risk_rules import HIGH_RISK_THRESHOLD, MEDIUM_RISK_THRESHOLD


HIGH_REVENUE_AT_RISK_THRESHOLD = 50
MEDIUM_REVENUE_AT_RISK_THRESHOLD = 25


def get_priority(row: pd.Series) -> str:
    churn_probability = float(row.get("churn_probability", 0) or 0)
    estimated_total_charge = float(row.get("estimated_total_charge", 0) or 0)
    revenue_at_risk = churn_probability * estimated_total_charge

    if (
        churn_probability >= HIGH_RISK_THRESHOLD
        or revenue_at_risk >= HIGH_REVENUE_AT_RISK_THRESHOLD
    ):
        return "High"

    if (
        churn_probability >= MEDIUM_RISK_THRESHOLD
        or revenue_at_risk >= MEDIUM_REVENUE_AT_RISK_THRESHOLD
    ):
        return "Medium"

    return "Low"


def build_recommendation(row: pd.Series) -> dict:
    risk_factor = row.get("main_risk_factor")
    churn_probability = float(row.get("churn_probability", 0) or 0)
    priority = get_priority(row)

    if churn_probability < MEDIUM_RISK_THRESHOLD:
        return {
            "recommendation_type": "No Action",
            "recommendation_reason": (
                "Customer has low churn probability; no retention action is required."
            ),
            "priority": "Low",
        }

    if risk_factor == "Customer service calls >= 3":
        return {
            "recommendation_type": "Service Recovery Call",
            "recommendation_reason": (
                "Customer has many service calls; contact the customer to resolve issues."
            ),
            "priority": priority,
        }

    if risk_factor == "International plan":
        return {
            "recommendation_type": "International Plan Review",
            "recommendation_reason": (
                "Customer uses an international plan; review international tariff conditions."
            ),
            "priority": priority,
        }

    if risk_factor == "High day charge":
        return {
            "recommendation_type": "Tariff Optimization",
            "recommendation_reason": (
                "Customer has high day usage; offer a more suitable tariff plan."
            ),
            "priority": priority,
        }

    if risk_factor == "No voice mail plan":
        return {
            "recommendation_type": "Voice Mail Offer",
            "recommendation_reason": (
                "Customer has no voice mail plan; offer voice mail plan as a retention action."
            ),
            "priority": priority,
        }

    return {
        "recommendation_type": "Retention Discount",
        "recommendation_reason": (
            "Customer has elevated churn probability; offer a retention discount."
        ),
        "priority": priority,
    }


def build_customer_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    records = []

    for _, row in df.iterrows():
        recommendation = build_recommendation(row)

        records.append(
            {
                "customer_id": row["customer_id"],
                **recommendation,
            }
        )

    return pd.DataFrame(records)
