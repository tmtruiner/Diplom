import pandas as pd


def build_recommendation(row: pd.Series) -> dict:
    risk_factor = row.get("main_risk_factor")

    if risk_factor == "Customer service calls >= 3":
        return {
            "recommendation_type": "Service Recovery Call",
            "recommendation_reason": (
                "Customer has many service calls; contact the customer to resolve issues."
            ),
            "priority": "High",
        }

    if risk_factor == "International plan":
        return {
            "recommendation_type": "International Plan Review",
            "recommendation_reason": (
                "Customer uses an international plan; review international tariff conditions."
            ),
            "priority": "Medium",
        }

    if risk_factor == "High day charge":
        return {
            "recommendation_type": "Tariff Optimization",
            "recommendation_reason": (
                "Customer has high day usage; offer a more suitable tariff plan."
            ),
            "priority": "Medium",
        }

    if risk_factor == "No voice mail plan":
        return {
            "recommendation_type": "Voice Mail Offer",
            "recommendation_reason": (
                "Customer has no voice mail plan; offer voice mail plan as a retention action."
            ),
            "priority": "Low",
        }

    return {
        "recommendation_type": "No Action",
        "recommendation_reason": (
            "Customer has low churn probability; no retention action is required."
        ),
        "priority": "Low",
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