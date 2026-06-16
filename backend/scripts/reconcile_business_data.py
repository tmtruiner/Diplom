import argparse

from sqlalchemy import text

from app.db import engine


RECONCILE_PREDICTION_RISK_FACTORS = text("""
    UPDATE predictions AS p
    SET main_risk_factor = CASE
        WHEN c.customer_service_calls >= 3
            THEN 'Customer service calls >= 3'
        WHEN c.total_day_charge >= 40
            THEN 'High day charge'
        WHEN LOWER(TRIM(c.international_plan)) IN ('yes', 'true', '1')
            THEN 'International plan'
        WHEN LOWER(TRIM(c.voice_mail_plan)) IN ('no', 'false', '0')
            THEN 'No voice mail plan'
        ELSE 'Stable customer profile'
    END
    FROM client_records_raw AS c
    WHERE c.customer_id = p.customer_id
      AND p.main_risk_factor IS DISTINCT FROM CASE
          WHEN c.customer_service_calls >= 3
              THEN 'Customer service calls >= 3'
          WHEN c.total_day_charge >= 40
              THEN 'High day charge'
          WHEN LOWER(TRIM(c.international_plan)) IN ('yes', 'true', '1')
              THEN 'International plan'
          WHEN LOWER(TRIM(c.voice_mail_plan)) IN ('no', 'false', '0')
              THEN 'No voice mail plan'
          ELSE 'Stable customer profile'
      END
""")


RECONCILE_RECOMMENDATIONS = text("""
    UPDATE customer_recommendations AS r
    SET
        recommendation_type = CASE
            WHEN p.risk_group = 'Low' THEN 'No Action'
            WHEN p.main_risk_factor = 'Customer service calls >= 3'
                THEN 'Service Recovery Call'
            WHEN p.main_risk_factor = 'International plan'
                THEN 'International Plan Review'
            WHEN p.main_risk_factor = 'High day charge'
                THEN 'Tariff Optimization'
            WHEN p.main_risk_factor = 'No voice mail plan'
                THEN 'Voice Mail Offer'
            ELSE 'Retention Discount'
        END,
        recommendation_reason = CASE
            WHEN p.risk_group = 'Low'
                THEN 'Customer has low churn probability; no retention action is required.'
            WHEN p.main_risk_factor = 'Customer service calls >= 3'
                THEN 'Customer has many service calls; contact the customer to resolve issues.'
            WHEN p.main_risk_factor = 'International plan'
                THEN 'Customer uses an international plan; review international tariff conditions.'
            WHEN p.main_risk_factor = 'High day charge'
                THEN 'Customer has high day usage; offer a more suitable tariff plan.'
            WHEN p.main_risk_factor = 'No voice mail plan'
                THEN 'Customer has no voice mail plan; offer voice mail plan as a retention action.'
            ELSE 'Customer has elevated churn probability; offer a retention discount.'
        END,
        priority = CASE
            WHEN p.risk_group = 'Low' THEN 'Low'
            WHEN p.churn_probability >= 0.7
                 OR p.churn_probability * p.estimated_total_charge >= 50
                THEN 'High'
            WHEN p.churn_probability >= 0.35
                 OR p.churn_probability * p.estimated_total_charge >= 25
                THEN 'Medium'
            ELSE 'Low'
        END
    FROM predictions AS p
    WHERE r.customer_id = p.customer_id
      AND (
          r.recommendation_type IS DISTINCT FROM CASE
              WHEN p.risk_group = 'Low' THEN 'No Action'
              WHEN p.main_risk_factor = 'Customer service calls >= 3'
                  THEN 'Service Recovery Call'
              WHEN p.main_risk_factor = 'International plan'
                  THEN 'International Plan Review'
              WHEN p.main_risk_factor = 'High day charge'
                  THEN 'Tariff Optimization'
              WHEN p.main_risk_factor = 'No voice mail plan'
                  THEN 'Voice Mail Offer'
              ELSE 'Retention Discount'
          END
          OR r.recommendation_reason IS DISTINCT FROM CASE
              WHEN p.risk_group = 'Low'
                  THEN 'Customer has low churn probability; no retention action is required.'
              WHEN p.main_risk_factor = 'Customer service calls >= 3'
                  THEN 'Customer has many service calls; contact the customer to resolve issues.'
              WHEN p.main_risk_factor = 'International plan'
                  THEN 'Customer uses an international plan; review international tariff conditions.'
              WHEN p.main_risk_factor = 'High day charge'
                  THEN 'Customer has high day usage; offer a more suitable tariff plan.'
              WHEN p.main_risk_factor = 'No voice mail plan'
                  THEN 'Customer has no voice mail plan; offer voice mail plan as a retention action.'
              ELSE 'Customer has elevated churn probability; offer a retention discount.'
          END
          OR r.priority IS DISTINCT FROM CASE
              WHEN p.risk_group = 'Low' THEN 'Low'
              WHEN p.churn_probability >= 0.7
                   OR p.churn_probability * p.estimated_total_charge >= 50
                  THEN 'High'
              WHEN p.churn_probability >= 0.35
                   OR p.churn_probability * p.estimated_total_charge >= 25
                  THEN 'Medium'
              ELSE 'Low'
          END
      )
""")


COUNT_INCONSISTENT_RECOMMENDATIONS = text("""
    SELECT COUNT(*)
    FROM customer_recommendations AS r
    JOIN predictions AS p
        ON r.customer_id = p.customer_id
    WHERE
        (p.risk_group = 'Low' AND r.recommendation_type != 'No Action')
        OR (p.risk_group != 'Low' AND r.recommendation_type = 'No Action')
""")


RECONCILE_SEGMENTS = text("""
    UPDATE customer_segments AS s
    SET
        segment_id = CASE
            WHEN c.customer_service_calls >= 3
                THEN 1
            WHEN c.total_day_minutes >= 230
                 OR c.total_day_charge >= 40
                 OR p.estimated_total_charge >= 65
                THEN 2
            WHEN LOWER(TRIM(c.international_plan)) IN ('yes', 'true', '1')
                 OR c.total_intl_minutes >= 10
                 OR c.total_intl_charge >= 3
                THEN 3
            ELSE 4
        END,
        segment_name = CASE
            WHEN c.customer_service_calls >= 3
                THEN 'Service Issue Segment'
            WHEN c.total_day_minutes >= 230
                 OR c.total_day_charge >= 40
                 OR p.estimated_total_charge >= 65
                THEN 'Tariff Optimization Segment'
            WHEN LOWER(TRIM(c.international_plan)) IN ('yes', 'true', '1')
                 OR c.total_intl_minutes >= 10
                 OR c.total_intl_charge >= 3
                THEN 'International Usage Segment'
            ELSE 'Stable Customer Segment'
        END
    FROM predictions AS p
    JOIN client_records_raw AS c
        ON c.customer_id = p.customer_id
    WHERE s.customer_id = p.customer_id
      AND (
          s.segment_id IS DISTINCT FROM CASE
              WHEN c.customer_service_calls >= 3
                  THEN 1
              WHEN c.total_day_minutes >= 230
                   OR c.total_day_charge >= 40
                   OR p.estimated_total_charge >= 65
                  THEN 2
              WHEN LOWER(TRIM(c.international_plan)) IN ('yes', 'true', '1')
                   OR c.total_intl_minutes >= 10
                   OR c.total_intl_charge >= 3
                  THEN 3
              ELSE 4
          END
          OR s.segment_name IS DISTINCT FROM CASE
              WHEN c.customer_service_calls >= 3
                  THEN 'Service Issue Segment'
              WHEN c.total_day_minutes >= 230
                   OR c.total_day_charge >= 40
                   OR p.estimated_total_charge >= 65
                  THEN 'Tariff Optimization Segment'
              WHEN LOWER(TRIM(c.international_plan)) IN ('yes', 'true', '1')
                   OR c.total_intl_minutes >= 10
                   OR c.total_intl_charge >= 3
                  THEN 'International Usage Segment'
              ELSE 'Stable Customer Segment'
          END
      )
""")


COUNT_INCONSISTENT_SEGMENTS = text("""
    WITH expected_segments AS (
        SELECT
            s.customer_id,
            s.segment_id,
            s.segment_name,
            CASE
                WHEN c.customer_service_calls >= 3
                    THEN 1
                WHEN c.total_day_minutes >= 230
                     OR c.total_day_charge >= 40
                     OR p.estimated_total_charge >= 65
                    THEN 2
                WHEN LOWER(TRIM(c.international_plan)) IN ('yes', 'true', '1')
                     OR c.total_intl_minutes >= 10
                     OR c.total_intl_charge >= 3
                    THEN 3
                ELSE 4
            END AS expected_segment_id,
            CASE
                WHEN c.customer_service_calls >= 3
                    THEN 'Service Issue Segment'
                WHEN c.total_day_minutes >= 230
                     OR c.total_day_charge >= 40
                     OR p.estimated_total_charge >= 65
                    THEN 'Tariff Optimization Segment'
                WHEN LOWER(TRIM(c.international_plan)) IN ('yes', 'true', '1')
                     OR c.total_intl_minutes >= 10
                     OR c.total_intl_charge >= 3
                    THEN 'International Usage Segment'
                ELSE 'Stable Customer Segment'
            END AS expected_segment_name
        FROM customer_segments AS s
        JOIN predictions AS p
            ON p.customer_id = s.customer_id
        JOIN client_records_raw AS c
            ON c.customer_id = s.customer_id
    )
    SELECT COUNT(*)
    FROM expected_segments
    WHERE segment_id IS DISTINCT FROM expected_segment_id
       OR segment_name IS DISTINCT FROM expected_segment_name
""")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only count inconsistent recommendations.",
    )
    args = parser.parse_args()

    with engine.begin() as connection:
        before = connection.execute(
            COUNT_INCONSISTENT_RECOMMENDATIONS
        ).scalar_one()
        segment_before = connection.execute(
            COUNT_INCONSISTENT_SEGMENTS
        ).scalar_one()

        if args.check:
            print(f"Inconsistent recommendations: {before}")
            print(f"Inconsistent segments: {segment_before}")
            return

        risk_factor_result = connection.execute(RECONCILE_PREDICTION_RISK_FACTORS)
        result = connection.execute(RECONCILE_RECOMMENDATIONS)
        segment_result = connection.execute(RECONCILE_SEGMENTS)
        after = connection.execute(
            COUNT_INCONSISTENT_RECOMMENDATIONS
        ).scalar_one()
        segment_after = connection.execute(
            COUNT_INCONSISTENT_SEGMENTS
        ).scalar_one()

    print(f"Updated prediction risk factors: {risk_factor_result.rowcount}")
    print(f"Updated recommendations: {result.rowcount}")
    print(f"Inconsistent recommendations remaining: {after}")
    print(f"Updated segments: {segment_result.rowcount}")
    print(f"Inconsistent segments remaining: {segment_after}")


if __name__ == "__main__":
    main()
