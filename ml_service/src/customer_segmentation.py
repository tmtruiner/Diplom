import pandas as pd


def is_yes(value: object) -> bool:
    return str(value).strip().lower() in ["yes", "true", "1"]


def assign_customer_segment(row: pd.Series) -> tuple[int, str]:
    churn_probability = float(row.get("churn_probability", 0) or 0)
    customer_service_calls = float(row.get("customer_service_calls", 0) or 0)

    total_day_minutes = float(row.get("total_day_minutes", 0) or 0)
    total_day_charge = float(row.get("total_day_charge", 0) or 0)

    total_intl_minutes = float(row.get("total_intl_minutes", 0) or 0)
    total_intl_charge = float(row.get("total_intl_charge", 0) or 0)

    estimated_total_charge = float(row.get("estimated_total_charge", 0) or 0)
    international_plan = row.get("international_plan", "")

    # 1. Сервисные проблемы: частые обращения могут говорить о недовольстве.
    if customer_service_calls >= 3:
        return 1, "Service Issue Segment"

    # 2. Тарифная оптимизация: высокое дневное использование или расходы.
    if (
        total_day_minutes >= 230
        or total_day_charge >= 40
        or estimated_total_charge >= 65
    ):
        return 2, "Tariff Optimization Segment"

    # 3. Международный тариф или активное международное использование.
    if (
        is_yes(international_plan)
        or total_intl_minutes >= 10
        or total_intl_charge >= 3
    ):
        return 3, "International Usage Segment"

    # 4. Остальные клиенты — стабильный профиль.
    return 4, "Stable Customer Segment"


def build_customer_segments(
    customers_df: pd.DataFrame,
) -> pd.DataFrame:

    df = customers_df.copy()

    if "customer_id" not in df.columns:
        raise ValueError("Missing column: customer_id")

    segment_results = df.apply(assign_customer_segment, axis=1)

    df["segment_id"] = segment_results.apply(lambda item: item[0])
    df["segment_name"] = segment_results.apply(lambda item: item[1])

    return df[["customer_id", "segment_id", "segment_name"]]
