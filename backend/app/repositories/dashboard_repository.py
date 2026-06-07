from sqlalchemy import text
from sqlalchemy.orm import Session


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self) -> dict:
        return {
            "kpis": self._get_kpis(),
            "risk_distribution": self._get_risk_distribution(),
            "average_churn_by_segment": self._get_average_churn_by_segment(),
            "high_risk_share_by_segment": self._get_high_risk_share_by_segment(),
            "recommendations_summary": self._get_recommendations_summary(),
            "top_risk_factors": self._get_top_risk_factors(),
            "priority_segments": self._get_priority_segments(),
            "scoring_info": self._get_scoring_info(),
        }

    def _get_kpis(self) -> dict:
        query = text("""
            SELECT
                COUNT(*) AS total_customers,
                SUM(CASE WHEN risk_group = 'High' THEN 1 ELSE 0 END) AS high_risk_customers,
                AVG(churn_probability) AS average_churn_probability,
                SUM(churn_probability * estimated_total_charge) AS estimated_revenue_at_risk,
                MAX(scoring_date) AS last_scoring_date
            FROM predictions
        """)

        row = self.db.execute(query).mappings().one()

        return {
            "total_customers": row["total_customers"] or 0,
            "high_risk_customers": row["high_risk_customers"] or 0,
            "average_churn_probability": float(row["average_churn_probability"] or 0),
            "estimated_revenue_at_risk": float(row["estimated_revenue_at_risk"] or 0),
            "last_scoring_date": str(row["last_scoring_date"]) if row["last_scoring_date"] else None,
        }

    def _get_risk_distribution(self) -> list[dict]:
        query = text("""
            SELECT
                risk_group,
                COUNT(*) AS customers_count
            FROM predictions
            GROUP BY risk_group
            ORDER BY customers_count DESC
        """)

        rows = self.db.execute(query).mappings().all()

        return [
            {
                "risk_group": row["risk_group"],
                "customers_count": row["customers_count"],
            }
            for row in rows
        ]

    def _get_average_churn_by_segment(self) -> list[dict]:
        query = text("""
            SELECT
                s.segment_name AS segment,
                AVG(p.churn_probability) AS average_churn_probability
            FROM predictions p
            JOIN customer_segments s
                ON p.customer_id = s.customer_id
            GROUP BY s.segment_name
            ORDER BY average_churn_probability DESC
        """)

        rows = self.db.execute(query).mappings().all()

        return [
            {
                "segment": row["segment"],
                "average_churn_probability": float(row["average_churn_probability"] or 0),
            }
            for row in rows
        ]

    def _get_high_risk_share_by_segment(self) -> list[dict]:
        query = text("""
            SELECT
                s.segment_name AS segment,
                COUNT(*) AS customers_count,
                SUM(CASE WHEN p.risk_group = 'High' THEN 1 ELSE 0 END) AS high_risk_customers
            FROM predictions p
            JOIN customer_segments s
                ON p.customer_id = s.customer_id
            GROUP BY s.segment_name
            ORDER BY high_risk_customers DESC
        """)

        rows = self.db.execute(query).mappings().all()

        result = []

        for row in rows:
            customers_count = row["customers_count"] or 0
            high_risk_customers = row["high_risk_customers"] or 0

            result.append(
                {
                    "segment": row["segment"],
                    "high_risk_share": (
                        high_risk_customers / customers_count
                        if customers_count
                        else 0
                    ),
                }
            )

        return result

    def _get_recommendations_summary(self) -> list[dict]:
        query = text("""
            SELECT
                recommendation_type,
                COUNT(*) AS customers_count
            FROM customer_recommendations
            GROUP BY recommendation_type
            ORDER BY customers_count DESC
        """)

        rows = self.db.execute(query).mappings().all()

        return [
            {
                "recommendation_type": row["recommendation_type"],
                "customers_count": row["customers_count"],
            }
            for row in rows
        ]

    def _get_top_risk_factors(self) -> list[dict]:
        query = text("""
            SELECT
                main_risk_factor AS factor,
                COUNT(*) AS customers_count
            FROM predictions
            WHERE risk_group = 'High'
              AND main_risk_factor IS NOT NULL
            GROUP BY main_risk_factor
            ORDER BY customers_count DESC
            LIMIT 5
        """)

        rows = self.db.execute(query).mappings().all()

        return [
            {
                "factor": row["factor"],
                "customers_count": row["customers_count"],
                "impact": "High",
            }
            for row in rows
        ]

    def _get_priority_segments(self) -> list[dict]:
        query = text("""
            SELECT
                s.segment_name AS segment,
                COUNT(*) AS clients_count,
                AVG(p.churn_probability) AS average_churn_probability,
                SUM(CASE WHEN p.risk_group = 'High' THEN 1 ELSE 0 END) AS high_risk_customers,
                MIN(p.main_risk_factor) AS main_risk_factor,
                MIN(r.recommendation_type) AS main_recommendation
            FROM predictions p
            JOIN customer_segments s
                ON p.customer_id = s.customer_id
            LEFT JOIN customer_recommendations r
                ON p.customer_id = r.customer_id
            GROUP BY s.segment_name
            ORDER BY average_churn_probability DESC
            LIMIT 3
        """)

        rows = self.db.execute(query).mappings().all()

        result = []

        for row in rows:
            clients_count = row["clients_count"] or 0
            high_risk_customers = row["high_risk_customers"] or 0

            result.append(
                {
                    "segment": row["segment"],
                    "clients_count": clients_count,
                    "average_churn_probability": float(row["average_churn_probability"] or 0),
                    "high_risk_share": (
                        high_risk_customers / clients_count
                        if clients_count
                        else 0
                    ),
                    "main_risk_factor": row["main_risk_factor"],
                    "main_recommendation": row["main_recommendation"],
                }
            )

        return result

    def _get_scoring_info(self) -> dict:
        query = text("""
            SELECT
                model_name,
                model_version,
                algorithm,
                roc_auc,
                f1_score,
                recall,
                high_risk_threshold,
                medium_risk_threshold,
                scoring_date
            FROM scoring_jobs
            WHERE status = 'success'
            ORDER BY scoring_date DESC
            LIMIT 1
        """)

        row = self.db.execute(query).mappings().first()

        if row is None:
            return {
                "model_name": None,
                "model_version": None,
                "algorithm": None,
                "roc_auc": None,
                "f1_score": None,
                "recall": None,
                "high_risk_threshold": 0.7,
                "medium_risk_threshold": 0.35,
                "last_scoring_date": None,
            }

        return {
            "model_name": row["model_name"],
            "model_version": row["model_version"],
            "algorithm": row["algorithm"],
            "roc_auc": float(row["roc_auc"]) if row["roc_auc"] is not None else None,
            "f1_score": float(row["f1_score"]) if row["f1_score"] is not None else None,
            "recall": float(row["recall"]) if row["recall"] is not None else None,
            "high_risk_threshold": float(row["high_risk_threshold"] or 0.7),
            "medium_risk_threshold": float(row["medium_risk_threshold"] or 0.35),
            "last_scoring_date": str(row["scoring_date"]) if row["scoring_date"] else None,
        }