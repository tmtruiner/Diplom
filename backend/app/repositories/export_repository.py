import csv
import io
import json

from sqlalchemy import text
from sqlalchemy.orm import Session


class ExportRepository:
    def __init__(self, db: Session):
        self.db = db

    def export_customers_csv(self) -> str:
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
            FROM predictions p
            LEFT JOIN customer_segments s
                ON p.customer_id = s.customer_id
            LEFT JOIN customer_recommendations r
                ON p.customer_id = r.customer_id
            ORDER BY p.churn_probability DESC
        """)

        rows = self.db.execute(query).mappings().all()
        return self._to_csv(rows)

    def export_high_risk_customers_csv(self) -> str:
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
            FROM predictions p
            LEFT JOIN customer_segments s
                ON p.customer_id = s.customer_id
            LEFT JOIN customer_recommendations r
                ON p.customer_id = r.customer_id
            WHERE p.risk_group = 'High'
            ORDER BY p.churn_probability DESC
        """)

        rows = self.db.execute(query).mappings().all()
        return self._to_csv(rows)

    def export_segments_csv(self) -> str:
        query = text("""
            WITH segment_stats AS (
                SELECT
                    s.segment_name,
                    COUNT(*) AS clients_count,
                    AVG(p.churn_probability) AS average_churn_probability,
                    SUM(CASE WHEN p.risk_group = 'High' THEN 1 ELSE 0 END) AS high_risk_customers,
                    AVG(p.estimated_total_charge) AS average_estimated_total_charge
                FROM customer_segments s
                JOIN predictions p
                    ON s.customer_id = p.customer_id
                GROUP BY s.segment_name
            ),
            recommendation_stats AS (
                SELECT
                    s.segment_name,
                    r.recommendation_type,
                    COUNT(*) AS recommendation_count,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.segment_name
                        ORDER BY COUNT(*) DESC
                    ) AS row_number
                FROM customer_segments s
                LEFT JOIN customer_recommendations r
                    ON s.customer_id = r.customer_id
                GROUP BY s.segment_name, r.recommendation_type
            )
            SELECT
                ss.segment_name,
                ss.clients_count,
                ss.average_churn_probability,
                ss.high_risk_customers,
                CASE
                    WHEN ss.clients_count > 0
                    THEN ss.high_risk_customers::float / ss.clients_count
                    ELSE 0
                END AS high_risk_share,
                ss.average_estimated_total_charge,
                rs.recommendation_type AS main_recommendation
            FROM segment_stats ss
            LEFT JOIN recommendation_stats rs
                ON ss.segment_name = rs.segment_name
                AND rs.row_number = 1
            ORDER BY ss.average_churn_probability DESC
        """)

        rows = self.db.execute(query).mappings().all()
        return self._to_csv(rows)

    def export_recommendations_csv(self) -> str:
        query = text("""
            SELECT
                r.recommendation_type,
                COUNT(*) AS customers_count,
                SUM(CASE WHEN p.risk_group = 'High' THEN 1 ELSE 0 END) AS high_risk_customers,
                AVG(p.churn_probability) AS average_churn_probability,
                SUM(p.churn_probability * p.estimated_total_charge) AS estimated_revenue_at_risk,
                MIN(r.priority) AS priority,
                MIN(r.recommendation_reason) AS recommendation_reason,
                MIN(p.main_risk_factor) AS main_risk_factor
            FROM customer_recommendations r
            JOIN predictions p
                ON r.customer_id = p.customer_id
            WHERE r.recommendation_type IS NOT NULL
              AND r.recommendation_type != 'No Action'
            GROUP BY r.recommendation_type
            ORDER BY estimated_revenue_at_risk DESC
        """)

        rows = self.db.execute(query).mappings().all()
        return self._to_csv(rows)

    def export_dashboard_summary_json(self) -> str:
        kpis_query = text("""
            SELECT
                COUNT(*) AS total_customers,
                SUM(CASE WHEN risk_group = 'High' THEN 1 ELSE 0 END) AS high_risk_customers,
                AVG(churn_probability) AS average_churn_probability,
                SUM(churn_probability * estimated_total_charge) AS estimated_revenue_at_risk,
                MAX(scoring_date) AS last_scoring_date
            FROM predictions
        """)

        risk_query = text("""
            SELECT
                risk_group,
                COUNT(*) AS customers_count
            FROM predictions
            GROUP BY risk_group
            ORDER BY customers_count DESC
        """)

        recommendations_query = text("""
            SELECT
                recommendation_type,
                COUNT(*) AS customers_count
            FROM customer_recommendations
            WHERE recommendation_type != 'No Action'
            GROUP BY recommendation_type
            ORDER BY customers_count DESC
        """)

        kpis = self.db.execute(kpis_query).mappings().one()
        risk_distribution = self.db.execute(risk_query).mappings().all()
        recommendations = self.db.execute(recommendations_query).mappings().all()

        payload = {
            "kpis": dict(kpis),
            "risk_distribution": [dict(row) for row in risk_distribution],
            "recommendations_summary": [dict(row) for row in recommendations],
        }

        return json.dumps(payload, default=str, ensure_ascii=False, indent=2)

    def _to_csv(self, rows) -> str:
        output = io.StringIO()

        if not rows:
            return ""

        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()

        for row in rows:
            writer.writerow(dict(row))

        return output.getvalue()