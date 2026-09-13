# 190. Write clean_staging(engine) — reads stg_customer_raw into a DataFrame, runs CustomerCleaner.clean(), writes to a cleaned_customers table

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "Phase_1"))

from customer_cleaner import CustomerCleaner


DATABASE_URL = "mysql+pymysql://root:root@localhost/churn"


def clean_staging(engine):
    staging_df = pd.read_sql("SELECT * FROM stg_customer_raw", engine)
    cleaned_df = CustomerCleaner(staging_df).clean()
    cleaned_df.to_sql("cleaned_customers", engine, if_exists="replace", index=False)
    return cleaned_df


# 191. Write build_curated_tables(engine) — populates dim_contract, dim_payment, customers, fact_customer_account from the cleaned staging data

def build_curated_tables(engine):
    cleaned_df = pd.read_sql("SELECT * FROM cleaned_customers", engine)

    contract_values = cleaned_df[["contract", "payment_method"]].copy()
    dim_contract = (
        contract_values[["contract"]]
        .drop_duplicates()
        .sort_values("contract")
        .reset_index(drop=True)
    )
    dim_contract.insert(0, "contract_id", range(1, len(dim_contract) + 1))
    dim_contract = dim_contract.rename(columns={"contract": "contract_type"})

    dim_payment = (
        contract_values[["payment_method"]]
        .drop_duplicates()
        .sort_values("payment_method")
        .reset_index(drop=True)
    )
    dim_payment.insert(0, "payment_id", range(1, len(dim_payment) + 1))

    customers = cleaned_df[
        ["customer_id", "gender", "senior_citizen", "partner", "dependents"]
    ].copy()
    customers["gender"] = customers["gender"].str.upper()

    fact_customer_account = cleaned_df[
        [
            "customer_id",
            "contract",
            "payment_method",
            "tenure",
            "monthly_charges",
            "total_charges",
            "churn",
        ]
    ].copy()
    fact_customer_account = fact_customer_account.merge(
        dim_contract,
        left_on="contract",
        right_on="contract_type",
        how="inner",
    ).merge(
        dim_payment,
        on="payment_method",
        how="inner",
    )
    fact_customer_account = fact_customer_account[
        [
            "customer_id",
            "contract_id",
            "payment_id",
            "tenure",
            "monthly_charges",
            "total_charges",
            "churn",
        ]
    ]

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM fact_customer_account"))
        connection.execute(text("DELETE FROM customers"))
        connection.execute(text("DELETE FROM dim_payment"))
        connection.execute(text("DELETE FROM dim_contract"))

    dim_contract.to_sql("dim_contract", engine, if_exists="append", index=False)
    dim_payment.to_sql("dim_payment", engine, if_exists="append", index=False)
    customers.to_sql("customers", engine, if_exists="append", index=False)
    fact_customer_account.to_sql(
        "fact_customer_account",
        engine,
        if_exists="append",
        index=False,
    )

    return {
        "dim_contract": len(dim_contract),
        "dim_payment": len(dim_payment),
        "customers": len(customers),
        "fact_customer_account": len(fact_customer_account),
    }


# 192. Add a row count check: assert cleaned_customers row count == stg_customer_raw row count (no rows dropped unless intentional)

def row_count_check(engine):
    with engine.connect() as connection:
        staging_count = connection.execute(
            text("SELECT COUNT(*) FROM stg_customer_raw")
        ).scalar_one()
        cleaned_count = connection.execute(
            text("SELECT COUNT(*) FROM cleaned_customers")
        ).scalar_one()

    difference = abs(staging_count - cleaned_count)
    passed = staging_count == cleaned_count
    print(f"{'PASS' if passed else 'FAIL'} - row count check: {difference} difference")
    assert passed, "cleaned_customers row count does not match stg_customer_raw"
    return difference


# 193. Add data quality assertions: no NULLs in customer_id or monthly_charges; churn column values are only 0 or 1

def data_quality_checks(engine):
    cleaned_df = pd.read_sql("SELECT * FROM cleaned_customers", engine)
    null_customer_ids = int(cleaned_df["customer_id"].isna().sum())
    null_monthly_charges = int(cleaned_df["monthly_charges"].isna().sum())
    invalid_churn = int((~cleaned_df["churn"].isin([0, 1])).sum())

    checks = {
        "customer_id NULL check": null_customer_ids,
        "monthly_charges NULL check": null_monthly_charges,
        "churn values check": invalid_churn,
    }

    for check_name, failure_count in checks.items():
        passed = failure_count == 0
        print(f"{'PASS' if passed else 'FAIL'} - {check_name}: {failure_count} failures")
        assert passed, f"{check_name} failed with {failure_count} invalid rows"

    return checks


# 194. Write a simple quality report: for each check, print PASS or FAIL with count

def quality_report(engine):
    print("Quality report:")
    row_count_check(engine)
    data_quality_checks(engine)


# 195. Test: run clean_staging() followed by build_curated_tables() — verify all four curated tables are populated

def main():
    engine = create_engine(DATABASE_URL)

    clean_staging(engine)
    table_counts = build_curated_tables(engine)
    quality_report(engine)

    print("Curated table counts:")
    for table_name, count in table_counts.items():
        status = "PASS" if count > 0 else "FAIL"
        print(f"{status} - {table_name}: {count} rows")
        assert count > 0, f"{table_name} is empty"


if __name__ == "__main__":
    main()
