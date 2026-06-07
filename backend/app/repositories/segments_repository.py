from sqlalchemy import text
from sqlalchemy.orm import Session


class SegmentsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_segments(self) -> dict:
        query = text("""
            WITH segment_stats AS (
                SELECT
                    s.segment_id,
                    s.segment_name,
                    COUNT(*) AS clients_count,
                    AVG(p.churn_probability) AS average_churn_probability,
                    SUM(CASE WHEN p.risk_group = 'High' THEN 1 ELSE 0 END) AS high_risk_customers,
                    AVG(p.estimated_total_charge) AS average_estimated_total_charge
                FROM customer_segments s
                JOIN predictions p
                    ON s.customer_id = p.customer_id
                GROUP BY s.segment_id, s.segment_name
            ),
            recommendation_stats AS (
                SELECT
                    s.segment_id,
                    s.segment_name,
                    r.recommendation_type,
                    COUNT(*) AS recommendation_count,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.segment_id, s.segment_name
                        ORDER BY COUNT(*) DESC
                    ) AS row_number
                FROM customer_segments s
                JOIN customer_recommendations r
                    ON s.customer_id = r.customer_id
                WHERE r.recommendation_type IS NOT NULL
                  AND r.recommendation_type != 'No Action'
                GROUP BY s.segment_id, s.segment_name, r.recommendation_type
            ),
            risk_factor_stats AS (
                SELECT
                    s.segment_id,
                    s.segment_name,
                    p.main_risk_factor,
                    COUNT(*) AS factor_count,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.segment_id, s.segment_name
                        ORDER BY COUNT(*) DESC
                    ) AS row_number
                FROM customer_segments s
                JOIN predictions p
                    ON s.customer_id = p.customer_id
                WHERE p.main_risk_factor IS NOT NULL
                GROUP BY s.segment_id, s.segment_name, p.main_risk_factor
            )
            SELECT
                ss.segment_id,
                ss.segment_name,
                ss.clients_count,
                ss.average_churn_probability,
                ss.high_risk_customers,
                ss.average_estimated_total_charge,
                rs.recommendation_type AS main_recommendation,
                rfs.main_risk_factor AS main_risk_factor
            FROM segment_stats ss
            LEFT JOIN recommendation_stats rs
                ON ss.segment_id = rs.segment_id
                AND ss.segment_name = rs.segment_name
                AND rs.row_number = 1
            LEFT JOIN risk_factor_stats rfs
                ON ss.segment_id = rfs.segment_id
                AND ss.segment_name = rfs.segment_name
                AND rfs.row_number = 1
            ORDER BY ss.average_churn_probability DESC
        """)

        rows = self.db.execute(query).mappings().all()

        items = []

        for row in rows:
            clients_count = row["clients_count"] or 0
            high_risk_customers = row["high_risk_customers"] or 0

            items.append(
                {
                    "segment_id": row["segment_id"],
                    "segment_name": row["segment_name"],
                    "clients_count": clients_count,
                    "average_churn_probability": float(
                        row["average_churn_probability"] or 0
                    ),
                    "high_risk_share": (
                        high_risk_customers / clients_count
                        if clients_count
                        else 0
                    ),
                    "average_estimated_total_charge": float(
                        row["average_estimated_total_charge"] or 0
                    ),
                    "main_recommendation": row["main_recommendation"] or "No Action",
                    "main_risk_factor": row["main_risk_factor"],
                }
            )

        return {"items": items}

    def get_segment_customers(
        self,
        segment_name: str,
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
                s.segment_id,
                s.segment_name,
                r.recommendation_type,
                r.recommendation_reason,
                r.priority
            FROM customer_segments s
            JOIN predictions p
                ON s.customer_id = p.customer_id
            LEFT JOIN customer_recommendations r
                ON s.customer_id = r.customer_id
            WHERE s.segment_name = :segment_name
            ORDER BY p.churn_probability DESC
            LIMIT :limit OFFSET :offset
        """)

        rows = self.db.execute(
            query,
            {
                "segment_name": segment_name,
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
                    "segment_id": row["segment_id"],
                    "segment_name": row["segment_name"],
                    "recommendation_type": row["recommendation_type"],
                    "recommendation_reason": row["recommendation_reason"],
                    "priority": row["priority"],
                }
                for row in rows
            ]
        }