import random
from dataclasses import dataclass

from sqlalchemy import text

from .database import get_engine


DEFAULT_TARGET_SCORING_CUSTOMERS = 1800
SYNTHETIC_CUSTOMER_PREFIX = "SYN"

RAW_CUSTOMER_COLUMNS = [
    "customer_id",
    "dataset_split",
    "state",
    "account_length",
    "area_code",
    "international_plan",
    "voice_mail_plan",
    "number_vmail_messages",
    "total_day_minutes",
    "total_day_calls",
    "total_day_charge",
    "total_eve_minutes",
    "total_eve_calls",
    "total_eve_charge",
    "total_night_minutes",
    "total_night_calls",
    "total_night_charge",
    "total_intl_minutes",
    "total_intl_calls",
    "total_intl_charge",
    "customer_service_calls",
    "churn",
]


@dataclass(frozen=True)
class AugmentationResult:
    existing_scoring_customers: int
    inserted_customers: int
    final_scoring_customers: int


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def jitter_float(value: float, ratio: float, minimum: float = 0) -> float:
    multiplier = random.uniform(1 - ratio, 1 + ratio)
    return round(max(minimum, value * multiplier), 1)


def jitter_int(value: int, delta: int, minimum: int = 0, maximum: int | None = None) -> int:
    result = max(minimum, value + random.randint(-delta, delta))

    if maximum is not None:
        result = min(result, maximum)

    return result


def maybe_flip_plan(value: str, probability: float = 0.04) -> str:
    normalized = str(value or "No").strip()

    if random.random() >= probability:
        return normalized

    return "No" if normalized.lower() in {"yes", "true", "1"} else "Yes"


def build_synthetic_customer(source: dict, customer_number: int) -> dict:
    day_minutes = jitter_float(float(source["total_day_minutes"] or 0), 0.18)
    eve_minutes = jitter_float(float(source["total_eve_minutes"] or 0), 0.16)
    night_minutes = jitter_float(float(source["total_night_minutes"] or 0), 0.16)
    intl_minutes = jitter_float(float(source["total_intl_minutes"] or 0), 0.22)

    voice_mail_plan = maybe_flip_plan(source["voice_mail_plan"])
    number_vmail_messages = (
        jitter_int(int(source["number_vmail_messages"] or 0), 4, 1, 55)
        if voice_mail_plan.lower() in {"yes", "true", "1"}
        else 0
    )

    synthetic = {
        **source,
        "customer_id": f"{SYNTHETIC_CUSTOMER_PREFIX}_{customer_number:05d}",
        "dataset_split": "scoring_batch",
        "account_length": jitter_int(int(source["account_length"] or 1), 18, 1),
        "international_plan": maybe_flip_plan(source["international_plan"], 0.03),
        "voice_mail_plan": voice_mail_plan,
        "number_vmail_messages": number_vmail_messages,
        "total_day_minutes": day_minutes,
        "total_day_calls": jitter_int(int(source["total_day_calls"] or 0), 14),
        "total_day_charge": round(day_minutes * 0.17, 2),
        "total_eve_minutes": eve_minutes,
        "total_eve_calls": jitter_int(int(source["total_eve_calls"] or 0), 14),
        "total_eve_charge": round(eve_minutes * 0.085, 2),
        "total_night_minutes": night_minutes,
        "total_night_calls": jitter_int(int(source["total_night_calls"] or 0), 14),
        "total_night_charge": round(night_minutes * 0.045, 2),
        "total_intl_minutes": intl_minutes,
        "total_intl_calls": jitter_int(int(source["total_intl_calls"] or 0), 2),
        "total_intl_charge": round(intl_minutes * 0.27, 2),
        "customer_service_calls": jitter_int(
            int(source["customer_service_calls"] or 0),
            1,
            0,
            9,
        ),
        "churn": None,
    }

    return {column: synthetic.get(column) for column in RAW_CUSTOMER_COLUMNS}


def get_next_synthetic_customer_number(connection) -> int:
    value = connection.execute(
        text("""
            SELECT COALESCE(
                MAX(CAST(SUBSTRING(customer_id FROM 5) AS integer)),
                0
            )
            FROM client_records_raw
            WHERE customer_id LIKE 'SYN\\_%' ESCAPE '\\'
        """)
    ).scalar_one()

    return int(value) + 1


def augment_scoring_customers(
    target_count: int = DEFAULT_TARGET_SCORING_CUSTOMERS,
    seed: int = 42,
) -> AugmentationResult:
    random.seed(seed)
    engine = get_engine()

    with engine.begin() as connection:
        existing_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM client_records_raw
                WHERE dataset_split = 'scoring_batch'
            """)
        ).scalar_one()

        if existing_count >= target_count:
            return AugmentationResult(
                existing_scoring_customers=int(existing_count),
                inserted_customers=0,
                final_scoring_customers=int(existing_count),
            )

        sources = connection.execute(
            text("""
                SELECT
                    state,
                    account_length,
                    area_code,
                    international_plan,
                    voice_mail_plan,
                    number_vmail_messages,
                    total_day_minutes,
                    total_day_calls,
                    total_day_charge,
                    total_eve_minutes,
                    total_eve_calls,
                    total_eve_charge,
                    total_night_minutes,
                    total_night_calls,
                    total_night_charge,
                    total_intl_minutes,
                    total_intl_calls,
                    total_intl_charge,
                    customer_service_calls,
                    churn
                FROM client_records_raw
                WHERE dataset_split = 'scoring_batch'
                ORDER BY id
            """)
        ).mappings().all()

        if not sources:
            raise ValueError("No scoring_batch customers found to augment.")

        customers_to_insert = target_count - int(existing_count)
        next_customer_number = get_next_synthetic_customer_number(connection)
        records = []

        for index in range(customers_to_insert):
            source = dict(random.choice(sources))
            records.append(
                build_synthetic_customer(
                    source=source,
                    customer_number=next_customer_number + index,
                )
            )

        connection.execute(
            text("""
                INSERT INTO client_records_raw (
                    customer_id,
                    dataset_split,
                    state,
                    account_length,
                    area_code,
                    international_plan,
                    voice_mail_plan,
                    number_vmail_messages,
                    total_day_minutes,
                    total_day_calls,
                    total_day_charge,
                    total_eve_minutes,
                    total_eve_calls,
                    total_eve_charge,
                    total_night_minutes,
                    total_night_calls,
                    total_night_charge,
                    total_intl_minutes,
                    total_intl_calls,
                    total_intl_charge,
                    customer_service_calls,
                    churn
                )
                VALUES (
                    :customer_id,
                    :dataset_split,
                    :state,
                    :account_length,
                    :area_code,
                    :international_plan,
                    :voice_mail_plan,
                    :number_vmail_messages,
                    :total_day_minutes,
                    :total_day_calls,
                    :total_day_charge,
                    :total_eve_minutes,
                    :total_eve_calls,
                    :total_eve_charge,
                    :total_night_minutes,
                    :total_night_calls,
                    :total_night_charge,
                    :total_intl_minutes,
                    :total_intl_calls,
                    :total_intl_charge,
                    :customer_service_calls,
                    :churn
                )
            """),
            records,
        )

        final_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM client_records_raw
                WHERE dataset_split = 'scoring_batch'
            """)
        ).scalar_one()

    return AugmentationResult(
        existing_scoring_customers=int(existing_count),
        inserted_customers=customers_to_insert,
        final_scoring_customers=int(final_count),
    )
