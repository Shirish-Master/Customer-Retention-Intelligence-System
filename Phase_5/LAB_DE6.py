# 212. Discuss the three cases: new customer (INSERT), updated customer (UPDATE), unchanged (skip)

from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import create_engine, text


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_CSV = PROJECT_DIR / "customer_churn.csv"
DATABASE_URL = "mysql+pymysql://root:root@localhost/churn"
CUSTOMER_COLUMNS = [
    "customer_id",
    "gender",
    "senior_citizen",
    "partner",
    "dependents",
    "tenure",
]


def prepare_customers(filepath):
    source_df = pd.read_csv(filepath)
    customers = source_df.rename(
        columns={
            "customerID": "customer_id",
            "SeniorCitizen": "senior_citizen",
            "Partner": "partner",
            "Dependents": "dependents",
        }
    )[CUSTOMER_COLUMNS].copy()
    customers["gender"] = customers["gender"].str.upper()
    customers["partner"] = customers["partner"].map({"Yes": 1, "No": 0})
    customers["dependents"] = customers["dependents"].map({"Yes": 1, "No": 0})
    return customers


def ensure_run_log_table(engine):
    with engine.begin() as connection:
        columns = connection.execute(text("SHOW COLUMNS FROM customers")).fetchall()
        if not any(column[0] == "tenure" for column in columns):
            connection.execute(text("ALTER TABLE customers ADD COLUMN tenure INT"))
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pipeline_run_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_name VARCHAR(255) NOT NULL,
                    rows_inserted INT NOT NULL,
                    rows_updated INT NOT NULL,
                    rows_unchanged INT NOT NULL,
                    run_timestamp DATETIME NOT NULL
                )
                """
            )
        )


# 213. Implement upsert logic for the customers table using SQLAlchemy: INSERT ... ON CONFLICT (customer_id) DO UPDATE

def upsert_customers(engine, filepath):
    customers = prepare_customers(filepath)
    inserted = 0
    updated = 0
    unchanged = 0

    # MySQL uses ON DUPLICATE KEY UPDATE, the equivalent of PostgreSQL ON CONFLICT DO UPDATE.
    upsert_sql = text(
        """
        INSERT INTO customers
            (customer_id, gender, senior_citizen, partner, dependents, tenure)
        VALUES
            (:customer_id, :gender, :senior_citizen, :partner, :dependents, :tenure)
        ON DUPLICATE KEY UPDATE
            gender = VALUES(gender),
            senior_citizen = VALUES(senior_citizen),
            partner = VALUES(partner),
            dependents = VALUES(dependents),
            tenure = VALUES(tenure)
        """
    )

    with engine.begin() as connection:
        existing_rows = connection.execute(
            text(
                """
                SELECT customer_id, gender, senior_citizen, partner, dependents, tenure
                FROM customers
                """
            ),
        ).fetchall()

        existing = {
            row.customer_id: tuple(row[1:])
            for row in existing_rows
        }

        for row in customers.itertuples(index=False):
            values = tuple(row[1:])
            if row.customer_id not in existing:
                inserted += 1
            elif existing[row.customer_id] == values:
                unchanged += 1
            else:
                updated += 1

            connection.execute(
                upsert_sql,
                {
                    "customer_id": row.customer_id,
                    "gender": row.gender,
                    "senior_citizen": int(row.senior_citizen),
                    "partner": int(row.partner),
                    "dependents": int(row.dependents),
                    "tenure": int(row.tenure),
                },
            )

        connection.execute(
            text(
                """
                INSERT INTO pipeline_run_log
                    (file_name, rows_inserted, rows_updated, rows_unchanged, run_timestamp)
                VALUES
                    (:file_name, :rows_inserted, :rows_updated, :rows_unchanged, NOW())
                """
            ),
            {
                "file_name": Path(filepath).name,
                "rows_inserted": inserted,
                "rows_updated": updated,
                "rows_unchanged": unchanged,
            },
        )

    return {
        "rows_inserted": inserted,
        "rows_updated": updated,
        "rows_unchanged": unchanged,
    }


def customer_count(engine):
    with engine.connect() as connection:
        return connection.execute(text("SELECT COUNT(*) FROM customers")).scalar_one()


def reset_customers(engine):
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM customers"))
    upsert_customers(engine, SOURCE_CSV)


# 214. Test Case 1 — new customer: add one row to the CSV with a new customer_id, re-run pipeline, verify count increases by 1

def test_new_customer(engine, original_df, test_dir):
    reset_customers(engine)
    before_count = customer_count(engine)
    new_customer = original_df.iloc[[0]].copy()
    new_customer["customerID"] = "TEST-NEW-CUSTOMER"
    new_file = test_dir / "new_customer.csv"
    pd.concat([original_df, new_customer]).to_csv(new_file, index=False)

    result = upsert_customers(engine, new_file)
    after_count = customer_count(engine)
    assert before_count == 7043
    assert after_count == before_count + 1
    assert result["rows_inserted"] == 1
    print(f"PASS - new customer: count increased to {after_count}")


# 215. Test Case 2 — updated customer: change tenure of an existing customer_id in the CSV, re-run, verify the row is updated not duplicated

def test_updated_customer(engine, original_df, test_dir):
    reset_customers(engine)
    customer_id = original_df.iloc[0]["customerID"]
    updated_df = original_df.copy()
    updated_df.loc[updated_df["customerID"] == customer_id, "tenure"] = 99
    updated_file = test_dir / "updated_customer.csv"
    updated_df.to_csv(updated_file, index=False)

    result = upsert_customers(engine, updated_file)
    with engine.connect() as connection:
        stored_tenure = connection.execute(
            text("SELECT tenure FROM customers WHERE customer_id = :customer_id"),
            {"customer_id": customer_id},
        ).scalar_one()

    assert customer_count(engine) == 7043
    assert result["rows_updated"] == 1
    assert stored_tenure == 99
    print("PASS - updated customer: existing customer updated without duplication")


# 216. Test Case 3 — same file re-run: re-run with the original CSV, verify count stays at 7043 with no duplicates

def test_same_file_rerun(engine, test_dir):
    reset_customers(engine)
    result = upsert_customers(engine, SOURCE_CSV)
    count = customer_count(engine)
    with engine.connect() as connection:
        duplicate_count = connection.execute(
            text(
                """
                SELECT COUNT(*) - COUNT(DISTINCT customer_id)
                FROM customers
                """
            )
        ).scalar_one()

    assert count == 7043
    assert duplicate_count == 0
    assert result["rows_inserted"] == 0
    assert result["rows_updated"] == 0
    assert result["rows_unchanged"] == 7043
    print("PASS - same file rerun: count remains 7043 with no duplicates")


# 217. Add a pipeline run log: record file_name, rows_inserted, rows_updated, rows_unchanged, run_timestamp

def show_pipeline_run_log(engine):
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT file_name, rows_inserted, rows_updated,
                       rows_unchanged, run_timestamp
                FROM pipeline_run_log
                ORDER BY id DESC
                LIMIT 10
                """
            )
        ).fetchall()
    for row in rows:
        print(row)


# 218. Discuss: why is idempotency important in production pipelines?

def idempotency_discussion():
    print(
        "Idempotency ensures that retrying the same daily extract does not create "
        "duplicate customers or change correct results. It makes failures recoverable, "
        "supports safe reruns, and keeps production tables and downstream reports consistent."
    )


def main():
    from tempfile import TemporaryDirectory

    engine = create_engine(DATABASE_URL)
    ensure_run_log_table(engine)
    original_df = pd.read_csv(SOURCE_CSV)

    with TemporaryDirectory() as temporary_directory:
        test_dir = Path(temporary_directory)
        test_new_customer(engine, original_df, test_dir)
        test_updated_customer(engine, original_df, test_dir)
        test_same_file_rerun(engine, test_dir)

    show_pipeline_run_log(engine)
    idempotency_discussion()


if __name__ == "__main__":
    main()
