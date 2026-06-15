import csv
import io
import json
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


CUSTOMER_CSV_HEADERS = {
    "customer_id": "ID клиента",
    "churn_probability": "Вероятность оттока",
    "risk_group": "Группа риска",
    "main_risk_factor": "Основной фактор риска",
    "estimated_total_charge": "Оценочные расходы",
    "scoring_date": "Дата скоринга",
    "segment_name": "Сегмент",
    "recommendation_type": "Рекомендация",
    "recommendation_reason": "Причина рекомендации",
    "priority": "Приоритет",
}

RISK_GROUP_TRANSLATIONS = {
    "High": "Высокий риск",
    "Medium": "Средний риск",
    "Low": "Низкий риск",
}

PRIORITY_TRANSLATIONS = {
    "High": "Высокий",
    "Medium": "Средний",
    "Low": "Низкий",
}

RISK_FACTOR_TRANSLATIONS = {
    "Customer service calls >= 3": "Обращений в поддержку ≥ 3",
    "International plan": "Подключён международный тариф",
    "High day charge": "Высокие дневные расходы",
    "No voice mail plan": "Не подключена голосовая почта",
    "Stable customer profile": "Стабильный профиль клиента",
}

SEGMENT_TRANSLATIONS = {
    "High Service Contact Customers": "Клиенты с частыми обращениями в поддержку",
    "High Risk High Charge Customers": "Клиенты высокого риска с высокими расходами",
    "International Plan Users": "Клиенты с международным тарифом",
    "High Day Usage Customers": "Клиенты с высоким дневным использованием",
    "High Charge Customers": "Клиенты с высокими расходами",
    "High Churn Risk Customers": "Клиенты с высоким риском оттока",
    "Stable Customer Profile": "Клиенты со стабильным профилем",
}

RECOMMENDATION_TRANSLATIONS = {
    "No Action": "Без действия",
    "Service Recovery Call": "Звонок для восстановления сервиса",
    "International Plan Review": "Пересмотр международного тарифа",
    "Tariff Optimization": "Оптимизация тарифа",
    "Voice Mail Plan Offer": "Предложение голосовой почты",
    "Voice Mail Offer": "Предложение голосовой почты",
    "Retention Discount": "Скидка на удержание",
}

RECOMMENDATION_REASON_TRANSLATIONS = {
    "Customer has many service calls; contact the customer to resolve issues.":
        "У клиента много обращений в поддержку; свяжитесь с клиентом, чтобы решить проблему.",
    "Customer uses an international plan; review international tariff conditions.":
        "Клиент использует международный тариф; проверьте условия международного тарифа.",
    "Customer has high day usage; offer a more suitable tariff plan.":
        "У клиента высокое дневное потребление; предложите более подходящий тарифный план.",
    "Customer has no voice mail plan; offer voice mail plan as a retention action.":
        "У клиента не подключена голосовая почта; предложите услугу как действие по удержанию.",
    "Customer has low churn probability; no retention action is required.":
        "У клиента низкая вероятность оттока; действие по удержанию не требуется.",
}


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
        return self._customers_to_csv(rows)

    def export_filtered_customers_csv(
        self,
        search: str | None = None,
        risk_group: str | None = None,
        segment: str | None = None,
        recommendation: str | None = None,
        main_risk_factor: str | None = None,
        min_probability: float | None = None,
    ) -> str:
        query = """
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
            WHERE 1 = 1
        """

        params = {}

        if search:
            query += " AND LOWER(p.customer_id) LIKE LOWER(:search)"
            params["search"] = f"%{search}%"

        if risk_group and risk_group != "All":
            query += " AND p.risk_group = :risk_group"
            params["risk_group"] = risk_group

        if segment and segment != "All":
            query += " AND s.segment_name = :segment"
            params["segment"] = segment

        if recommendation and recommendation != "All":
            query += " AND r.recommendation_type = :recommendation"
            params["recommendation"] = recommendation

        if main_risk_factor and main_risk_factor != "All":
            query += " AND p.main_risk_factor = :main_risk_factor"
            params["main_risk_factor"] = main_risk_factor

        if min_probability is not None:
            query += " AND p.churn_probability >= :min_probability"
            params["min_probability"] = min_probability

        query += " ORDER BY p.churn_probability DESC"

        rows = self.db.execute(text(query), params).mappings().all()
        return self._customers_to_csv(rows)

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
        return self._customers_to_csv(rows)

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
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=";",
            lineterminator="\r\n",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(dict(row))

        return "\ufeff" + output.getvalue()

    def _customers_to_csv(self, rows) -> str:
        output = io.StringIO()
        fieldnames = list(CUSTOMER_CSV_HEADERS.values())

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            delimiter=";",
            lineterminator="\r\n",
        )
        writer.writeheader()

        for row in rows:
            row_data = dict(row)
            writer.writerow(
                {
                    header: self._format_customer_csv_value(key, row_data.get(key))
                    for key, header in CUSTOMER_CSV_HEADERS.items()
                }
            )

        return "\ufeff" + output.getvalue()

    @staticmethod
    def _format_customer_csv_value(key: str, value) -> str:
        if value is None:
            return ""

        if key in {"churn_probability", "estimated_total_charge"}:
            return f"{float(value):.2f}".replace(".", ",")

        if key == "scoring_date":
            if isinstance(value, (date, datetime)):
                return value.strftime("%d.%m.%Y")

            try:
                return datetime.fromisoformat(str(value)).strftime("%d.%m.%Y")
            except ValueError:
                return str(value)

        translations = {
            "risk_group": RISK_GROUP_TRANSLATIONS,
            "priority": PRIORITY_TRANSLATIONS,
            "main_risk_factor": RISK_FACTOR_TRANSLATIONS,
            "segment_name": SEGMENT_TRANSLATIONS,
            "recommendation_type": RECOMMENDATION_TRANSLATIONS,
            "recommendation_reason": RECOMMENDATION_REASON_TRANSLATIONS,
        }

        if key in translations:
            return translations[key].get(str(value), str(value))

        return str(value)
