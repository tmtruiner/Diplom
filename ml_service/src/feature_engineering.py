import pandas as pd


CHARGE_COLUMNS = [
    "total_day_charge",
    "total_eve_charge",
    "total_night_charge",
    "total_intl_charge",
]


def add_customer_ids(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    if "customer_id" not in result.columns:
        result["customer_id"] = [
            f"C{index + 1:05d}" for index in range(len(result))
        ]

    return result


def add_estimated_total_charge(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    for column in CHARGE_COLUMNS:
        if column not in result.columns:
            result[column] = 0

    result["estimated_total_charge"] = (
        result["total_day_charge"].fillna(0)
        + result["total_eve_charge"].fillna(0)
        + result["total_night_charge"].fillna(0)
        + result["total_intl_charge"].fillna(0)
    )

    return result


def normalize_boolean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    for column in ["international_plan", "voice_mail_plan"]:
        if column in result.columns:
            result[column] = (
                result[column]
                .astype(str)
                .str.lower()
                .replace(
                    {
                        "true": "yes",
                        "false": "no",
                        "1": "yes",
                        "0": "no",
                    }
                )
            )

    return result


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    result = add_customer_ids(result)
    result = normalize_boolean_text_columns(result)
    result = add_estimated_total_charge(result)

    return result