import unittest

import pandas as pd

from backend.app.repositories.customers_repository import CustomersRepository
from ml_service.src.customer_segmentation import assign_customer_segment
from ml_service.src.recommendation_rules import build_recommendation, get_priority
from ml_service.src.risk_rules import assign_main_risk_factor


class RecommendationRulesTests(unittest.TestCase):
    def test_low_risk_customer_requires_no_action(self):
        recommendation = build_recommendation(
            pd.Series(
                {
                    "churn_probability": 0.2,
                    "main_risk_factor": "No voice mail plan",
                }
            )
        )

        self.assertEqual(recommendation["recommendation_type"], "No Action")

    def test_elevated_risk_without_specific_factor_gets_retention_action(self):
        recommendation = build_recommendation(
            pd.Series(
                {
                    "churn_probability": 0.5,
                    "main_risk_factor": "Stable customer profile",
                }
            )
        )

        self.assertEqual(
            recommendation["recommendation_type"],
            "Retention Discount",
        )

    def test_priority_depends_on_risk_metrics_not_recommendation_type(self):
        service_recommendation = build_recommendation(
            pd.Series(
                {
                    "churn_probability": 0.4,
                    "estimated_total_charge": 40,
                    "main_risk_factor": "Customer service calls >= 3",
                }
            )
        )
        tariff_recommendation = build_recommendation(
            pd.Series(
                {
                    "churn_probability": 0.8,
                    "estimated_total_charge": 80,
                    "main_risk_factor": "High day charge",
                }
            )
        )

        self.assertEqual(service_recommendation["priority"], "Medium")
        self.assertEqual(tariff_recommendation["priority"], "High")

    def test_high_revenue_at_risk_raises_priority(self):
        priority = get_priority(
            pd.Series(
                {
                    "churn_probability": 0.6,
                    "estimated_total_charge": 90,
                }
            )
        )

        self.assertEqual(priority, "High")

    def test_tariff_factor_has_priority_over_international_plan(self):
        risk_factor = assign_main_risk_factor(
            pd.Series(
                {
                    "customer_service_calls": 1,
                    "total_day_charge": 45,
                    "international_plan": "yes",
                    "voice_mail_plan": "no",
                }
            )
        )

        recommendation = build_recommendation(
            pd.Series(
                {
                    "churn_probability": 0.8,
                    "main_risk_factor": risk_factor,
                }
            )
        )

        self.assertEqual(risk_factor, "High day charge")
        self.assertEqual(
            recommendation["recommendation_type"],
            "Tariff Optimization",
        )


class CustomerHealthTests(unittest.TestCase):
    def setUp(self):
        self.repository = CustomersRepository(db=None)

    def test_stable_profile_does_not_reduce_health_score(self):
        without_factor = self.repository._get_health_score(
            churn_probability=0.2,
            risk_group="Low",
            main_risk_factor=None,
            estimated_total_charge=40,
        )
        stable_profile = self.repository._get_health_score(
            churn_probability=0.2,
            risk_group="Low",
            main_risk_factor="Stable customer profile",
            estimated_total_charge=40,
        )

        self.assertEqual(stable_profile, without_factor)

    def test_certain_churn_produces_critical_health_score(self):
        score = self.repository._get_health_score(
            churn_probability=1.0,
            risk_group="High",
            main_risk_factor="High day charge",
            estimated_total_charge=80,
        )

        self.assertEqual(score, 15)
        self.assertEqual(
            self.repository._get_health_status(score)["code"],
            "critical",
        )

    def test_low_churn_probability_remains_healthy(self):
        score = self.repository._get_health_score(
            churn_probability=0.2,
            risk_group="Low",
            main_risk_factor="Stable customer profile",
            estimated_total_charge=40,
        )

        self.assertEqual(score, 86)
        self.assertEqual(
            self.repository._get_health_status(score)["code"],
            "healthy",
        )


class CustomerSegmentationTests(unittest.TestCase):
    def test_service_issue_segment_has_highest_priority(self):
        segment_id, segment_name = assign_customer_segment(
            pd.Series(
                {
                    "churn_probability": 0.9,
                    "estimated_total_charge": 80,
                    "customer_service_calls": 4,
                }
            )
        )

        self.assertEqual(segment_id, 1)
        self.assertEqual(segment_name, "Service Issue Segment")

    def test_tariff_segment_handles_high_value_customers(self):
        segment_id, segment_name = assign_customer_segment(
            pd.Series(
                {
                    "churn_probability": 0.9,
                    "estimated_total_charge": 80,
                    "customer_service_calls": 1,
                }
            )
        )

        self.assertEqual(segment_id, 2)
        self.assertEqual(segment_name, "Tariff Optimization Segment")


if __name__ == "__main__":
    unittest.main()
