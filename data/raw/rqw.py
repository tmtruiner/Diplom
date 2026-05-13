import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = [
        col.strip()
        .replace(" ", "_")
        .replace("-", "_")
        .lower()
        for col in df.columns
    ]

    return df


def main():
    df = pd.read_csv(r'C:\Users\Milkis Enjoyer\Desktop\Diplom\data\raw\Telecom_churn.csv')
    df = normalize_columns(df)

    print("Rows:", len(df))
    print("Columns:", list(df.columns))

    df.to_sql(
        "customer_features",
        engine,
        if_exists="append",
        index=False
    )

    print("Dataset loaded to PostgreSQL")


if __name__ == "__main__":
    main()