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

    # 1. Самый проблемный сегмент — много обращений в поддержку.
    # Такой клиент может быть недоволен сервисом.
    if customer_service_calls >= 3:
        return 1, "High Service Contact Customers"

    # 2. Клиенты высокого риска с высокой финансовой значимостью.
    # Их важно выделять отдельно, потому что они могут дать больший ущерб при уходе.
    if churn_probability >= 0.7 and estimated_total_charge >= 65:
        return 2, "High Risk High Charge Customers"

    # 3. Клиенты с международным тарифом или активным международным использованием.
    # Для них логична рекомендация по пересмотру международного тарифа.
    if (
        is_yes(international_plan)
        or total_intl_minutes >= 10
        or total_intl_charge >= 3
    ):
        return 3, "International Plan Users"

    # 4. Клиенты с высоким дневным использованием.
    # Для них можно предложить более подходящий тариф.
    if total_day_minutes >= 230 or total_day_charge >= 40:
        return 4, "High Day Usage Customers"

    # 5. Клиенты с высокими расходами, но без ярко выраженного риска.
    # Их можно отслеживать как финансово значимых клиентов.
    if estimated_total_charge >= 65:
        return 5, "High Charge Customers"

    # 6. Клиенты высокого риска без отдельного яркого фактора.
    if churn_probability >= 0.7:
        return 6, "High Churn Risk Customers"

    # 7. Остальные клиенты — стабильный профиль.
    return 7, "Stable Customer Profile"


def build_customer_segments(
    customers_df: pd.DataFrame,
    n_clusters: int = 4,
) -> pd.DataFrame:
    """
    Формирует интерпретируемые клиентские сегменты на основе правил.

    Параметр n_clusters оставлен для совместимости с pipeline.py,
    но в rule-based сегментации не используется.
    """

    df = customers_df.copy()

    if "customer_id" not in df.columns:
        raise ValueError("Missing column: customer_id")

    segment_results = df.apply(assign_customer_segment, axis=1)

    df["segment_id"] = segment_results.apply(lambda item: item[0])
    df["segment_name"] = segment_results.apply(lambda item: item[1])

    return df[["customer_id", "segment_id", "segment_name"]]