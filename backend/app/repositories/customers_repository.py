from sqlalchemy import text
from sqlalchemy.orm import Session


CHURN_PROBABILITY_HEALTH_WEIGHT = 70


class CustomersRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(value, max_value))

    @staticmethod
    def _get_revenue_at_risk(
        churn_probability: float,
        estimated_total_charge: float,
    ) -> float:
        return round(churn_probability * estimated_total_charge, 2)

    def _get_health_score(
        self,
        churn_probability: float,
        risk_group: str | None,
        main_risk_factor: str | None,
        estimated_total_charge: float,
    ) -> int:
        probability_penalty = (
            churn_probability * CHURN_PROBABILITY_HEALTH_WEIGHT
        )

        if risk_group == "High":
            risk_penalty = 8
        elif risk_group == "Medium":
            risk_penalty = 4
        else:
            risk_penalty = 0

        if estimated_total_charge >= 90:
            charge_penalty = 5
        elif estimated_total_charge >= 75:
            charge_penalty = 3
        else:
            charge_penalty = 0

        has_actionable_factor = (
            main_risk_factor is not None
            and main_risk_factor != "Stable customer profile"
        )
        factor_penalty = 4 if has_actionable_factor else 0

        score = (
            100
            - probability_penalty
            - risk_penalty
            - charge_penalty
            - factor_penalty
        )

        return round(self._clamp(score, 0, 100))

    @staticmethod
    def _get_health_status(score: int) -> dict:
        if score <= 35:
            return {
                "code": "critical",
                "label": "Критическое состояние",
                "tone": "red",
            }

        if score <= 60:
            return {
                "code": "needs_attention",
                "label": "Требует внимания",
                "tone": "amber",
            }

        if score <= 80:
            return {
                "code": "stable",
                "label": "Стабильный клиент",
                "tone": "blue",
            }

        return {
            "code": "healthy",
            "label": "Здоровый клиент",
            "tone": "green",
        }

    @staticmethod
    def _get_processing_priority(
        risk_group: str | None,
        priority: str | None,
    ) -> int:
        if priority in ("High", "Высокий"):
            return 1

        if priority in ("Medium", "Средний"):
            return 2

        if priority in ("Low", "Низкий"):
            return 3

        if risk_group == "High":
            return 1

        if risk_group == "Medium":
            return 2

        return 3

    @staticmethod
    def _get_risk_reduction_potential(
        risk_group: str | None,
        recommendation_type: str | None,
    ) -> str:
        if recommendation_type == "No Action":
            return "Low"

        if risk_group == "High":
            return "High"

        if risk_group == "Medium":
            return "Medium"

        return "Low"

    def _get_risk_drivers(
        self,
        churn_probability: float,
        main_risk_factor: str | None,
        estimated_total_charge: float,
        segment_name: str | None,
        recommendation_type: str | None,
    ) -> list[dict]:
        drivers = []

        if (
            main_risk_factor
            and main_risk_factor != "Stable customer profile"
        ):
            drivers.append(
                {
                    "code": "main_risk_factor",
                    "value": main_risk_factor,
                    "label": main_risk_factor,
                    "impact": "high",
                }
            )

        if churn_probability >= 0.7:
            drivers.append(
                {
                    "code": "high_churn_probability",
                    "value": round(churn_probability, 2),
                    "label": "High churn probability",
                    "impact": "high",
                }
            )

        if estimated_total_charge >= 80:
            drivers.append(
                {
                    "code": "high_estimated_charge",
                    "value": round(estimated_total_charge, 2),
                    "label": "High estimated charge",
                    "impact": "medium",
                }
            )

        if segment_name:
            drivers.append(
                {
                    "code": "segment",
                    "value": segment_name,
                    "label": segment_name,
                    "impact": "medium",
                }
            )

        if recommendation_type and recommendation_type != "No Action":
            drivers.append(
                {
                    "code": "recommended_action",
                    "value": recommendation_type,
                    "label": recommendation_type,
                    "impact": "medium",
                }
            )

        return drivers[:4]

    def _build_customer_health(
        self,
        churn_probability: float,
        risk_group: str | None,
        main_risk_factor: str | None,
        estimated_total_charge: float,
        segment_name: str | None,
        recommendation_type: str | None,
        recommendation_reason: str | None,
        priority: str | None,
    ) -> dict:
        score = self._get_health_score(
            churn_probability=churn_probability,
            risk_group=risk_group,
            main_risk_factor=main_risk_factor,
            estimated_total_charge=estimated_total_charge,
        )

        revenue_at_risk = self._get_revenue_at_risk(
            churn_probability=churn_probability,
            estimated_total_charge=estimated_total_charge,
        )

        return {
            "score": score,
            "status": self._get_health_status(score),
            "revenue_at_risk": revenue_at_risk,
            "risk_drivers": self._get_risk_drivers(
                churn_probability=churn_probability,
                main_risk_factor=main_risk_factor,
                estimated_total_charge=estimated_total_charge,
                segment_name=segment_name,
                recommendation_type=recommendation_type,
            ),
            "next_best_action": {
                "recommendation_type": recommendation_type or "No Action",
                "recommendation_reason": recommendation_reason,
                "priority": priority,
            },
            "expected_effect": {
                "risk_reduction_potential": self._get_risk_reduction_potential(
                    risk_group=risk_group,
                    recommendation_type=recommendation_type,
                ),
                "processing_priority": self._get_processing_priority(
                    risk_group=risk_group,
                    priority=priority,
                ),
            },
        }

    def get_customers(
        self,
        search: str | None = None,
        risk_group: str | None = None,
        segment: str | None = None,
        recommendation: str | None = None,
        min_probability: float | None = None,
        main_risk_factor: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
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
                r.priority,
                COUNT(*) OVER() AS total_count
            FROM predictions p
            LEFT JOIN customer_segments s
                ON p.customer_id = s.customer_id
            LEFT JOIN customer_recommendations r
                ON p.customer_id = r.customer_id
            WHERE 1 = 1
        """

        params = {
            "limit": limit,
            "offset": offset,
        }

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

        if min_probability is not None:
            query += " AND p.churn_probability >= :min_probability"
            params["min_probability"] = min_probability

        if main_risk_factor and main_risk_factor != "All":
            query += " AND p.main_risk_factor = :main_risk_factor"
            params["main_risk_factor"] = main_risk_factor

        query += """
            ORDER BY p.churn_probability DESC
            LIMIT :limit OFFSET :offset
        """

        rows = self.db.execute(text(query), params).mappings().all()

        result = []

        for row in rows:
            churn_probability = float(row["churn_probability"] or 0)
            estimated_total_charge = float(row["estimated_total_charge"] or 0)

            health = self._build_customer_health(
                churn_probability=churn_probability,
                risk_group=row["risk_group"],
                main_risk_factor=row["main_risk_factor"],
                estimated_total_charge=estimated_total_charge,
                segment_name=row["segment_name"],
                recommendation_type=row["recommendation_type"],
                recommendation_reason=row["recommendation_reason"],
                priority=row["priority"],
            )

            result.append(
                {
                    "customer_id": row["customer_id"],
                    "churn_probability": churn_probability,
                    "risk_group": row["risk_group"],
                    "main_risk_factor": row["main_risk_factor"],
                    "estimated_total_charge": estimated_total_charge,
                    "scoring_date": str(row["scoring_date"])
                    if row["scoring_date"]
                    else None,
                    "segment_name": row["segment_name"],
                    "recommendation_type": row["recommendation_type"],
                    "recommendation_reason": row["recommendation_reason"],
                    "priority": row["priority"],

                    # Новые поля для карточки здоровья / будущей сортировки
                    "health_score": health["score"],
                    "health_status": health["status"],
                    "revenue_at_risk": health["revenue_at_risk"],
                }
            )

        total = int(rows[0]["total_count"]) if rows else 0

        return {
            "items": result,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_customer_detail(self, customer_id: str) -> dict | None:
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
            FROM predictions p
            LEFT JOIN customer_segments s
                ON p.customer_id = s.customer_id
            LEFT JOIN customer_recommendations r
                ON p.customer_id = r.customer_id
            WHERE p.customer_id = :customer_id
            LIMIT 1
        """)

        row = self.db.execute(query, {"customer_id": customer_id}).mappings().first()

        if row is None:
            return None

        churn_probability = float(row["churn_probability"] or 0)
        estimated_total_charge = float(row["estimated_total_charge"] or 0)

        health = self._build_customer_health(
            churn_probability=churn_probability,
            risk_group=row["risk_group"],
            main_risk_factor=row["main_risk_factor"],
            estimated_total_charge=estimated_total_charge,
            segment_name=row["segment_name"],
            recommendation_type=row["recommendation_type"],
            recommendation_reason=row["recommendation_reason"],
            priority=row["priority"],
        )

        return {
            "customer_id": row["customer_id"],
            "prediction": {
                "churn_probability": churn_probability,
                "risk_group": row["risk_group"],
                "main_risk_factor": row["main_risk_factor"],
                "estimated_total_charge": estimated_total_charge,
                "scoring_date": str(row["scoring_date"])
                if row["scoring_date"]
                else None,
            },
            "segment": {
                "segment_id": row["segment_id"],
                "segment_name": row["segment_name"],
            },
            "recommendation": {
                "recommendation_type": row["recommendation_type"],
                "recommendation_reason": row["recommendation_reason"],
                "priority": row["priority"],
            },
            "health": health,
        }

    def get_filter_options(self) -> dict:
        segments_query = text("""
            SELECT DISTINCT segment_name
            FROM customer_segments
            WHERE segment_name IS NOT NULL
            ORDER BY segment_name
        """)

        recommendations_query = text("""
            SELECT DISTINCT recommendation_type
            FROM customer_recommendations
            WHERE recommendation_type IS NOT NULL
            ORDER BY recommendation_type
        """)

        risk_factors_query = text("""
            SELECT DISTINCT main_risk_factor
            FROM predictions
            WHERE main_risk_factor IS NOT NULL
            ORDER BY main_risk_factor
        """)

        risk_groups_query = text("""
            SELECT risk_group
            FROM (
                SELECT DISTINCT
                    risk_group,
                    CASE
                        WHEN risk_group = 'High' THEN 1
                        WHEN risk_group = 'Medium' THEN 2
                        WHEN risk_group = 'Low' THEN 3
                        ELSE 4
                    END AS sort_order
                FROM predictions
                WHERE risk_group IS NOT NULL
            ) AS risk_groups
            ORDER BY sort_order
        """)

        segments = [
            row["segment_name"]
            for row in self.db.execute(segments_query).mappings().all()
        ]

        recommendations = [
            row["recommendation_type"]
            for row in self.db.execute(recommendations_query).mappings().all()
        ]

        main_risk_factors = [
            row["main_risk_factor"]
            for row in self.db.execute(risk_factors_query).mappings().all()
        ]

        risk_groups = [
            row["risk_group"]
            for row in self.db.execute(risk_groups_query).mappings().all()
        ]

        return {
            "risk_groups": risk_groups,
            "segments": segments,
            "recommendations": recommendations,
            "main_risk_factors": main_risk_factors,
        }
