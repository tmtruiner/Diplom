from sqlalchemy import text
from sqlalchemy.orm import Session


class RecommendationsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_recommendations(self) -> dict:
        query = text("""
            SELECT
                r.recommendation_type,

                COUNT(*) AS customers_count,

                SUM(
                    CASE WHEN p.risk_group = 'High'
                    THEN 1 ELSE 0 END
                ) AS high_risk_customers,

                SUM(
                    CASE WHEN r.priority = 'High'
                    THEN 1 ELSE 0 END
                ) AS high_priority_customers,

                AVG(p.churn_probability) AS average_churn_probability,

                SUM(
                    p.churn_probability * p.estimated_total_charge
                ) AS estimated_revenue_at_risk,

                MIN(r.recommendation_reason) AS recommendation_reason,

                MIN(r.priority) AS priority,

                MIN(p.main_risk_factor) AS main_risk_factor

            FROM customer_recommendations r
            JOIN predictions p
                ON r.customer_id = p.customer_id

            WHERE r.recommendation_type IS NOT NULL

            GROUP BY r.recommendation_type
            ORDER BY
                CASE
                    WHEN r.recommendation_type = 'No Action' THEN 2
                    ELSE 1
                END,
                estimated_revenue_at_risk DESC
        """)

        rows = self.db.execute(query).mappings().all()

        items = []

        for row in rows:
            customers_count = row["customers_count"] or 0
            high_risk_customers = row["high_risk_customers"] or 0

            items.append(
                {
                    "recommendation_type": row["recommendation_type"],
                    "customers_count": customers_count,
                    "high_risk_customers": high_risk_customers,
                    "high_priority_customers": row["high_priority_customers"] or 0,
                    "average_churn_probability": float(
                        row["average_churn_probability"] or 0
                    ),
                    "high_risk_share": (
                        high_risk_customers / customers_count
                        if customers_count
                        else 0
                    ),
                    "estimated_revenue_at_risk": float(
                        row["estimated_revenue_at_risk"] or 0
                    ),
                    "recommendation_reason": row["recommendation_reason"],
                    "priority": row["priority"],
                    "main_risk_factor": row["main_risk_factor"],
                }
            )

        return {"items": items}

    def get_recommendation_customers(
        self,
        recommendation_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        query = text("""
            SELECT
                p.customer_id,
                p.churn_probability,
                p.risk_group,
                p.main_risk_factor,
                p.estimated_total_charge,
                p.scoring_date,

                s.segment_name,

                r.recommendation_type,
                r.recommendation_reason,
                r.priority

            FROM customer_recommendations r
            JOIN predictions p
                ON r.customer_id = p.customer_id
            LEFT JOIN customer_segments s
                ON r.customer_id = s.customer_id

            WHERE r.recommendation_type = :recommendation_type

            ORDER BY p.churn_probability DESC
            LIMIT :limit OFFSET :offset
        """)

        rows = self.db.execute(
            query,
            {
                "recommendation_type": recommendation_type,
                "limit": limit,
                "offset": offset,
            },
        ).mappings().all()

        return {
            "items": [
                {
                    "customer_id": row["customer_id"],
                    "churn_probability": float(row["churn_probability"]),
                    "risk_group": row["risk_group"],
                    "main_risk_factor": row["main_risk_factor"],
                    "estimated_total_charge": float(
                        row["estimated_total_charge"] or 0
                    ),
                    "scoring_date": (
                        str(row["scoring_date"])
                        if row["scoring_date"]
                        else None
                    ),
                    "segment_name": row["segment_name"],
                    "recommendation_type": row["recommendation_type"],
                    "recommendation_reason": row["recommendation_reason"],
                    "priority": row["priority"],
                }
                for row in rows
            ]
        }