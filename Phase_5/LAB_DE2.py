# 181. Create the folder structure: data/landing/, data/raw/, data/rejected/, data/logs/

import csv
import logging
import shutil
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LANDING_DIR = DATA_DIR / "landing"
RAW_DIR = DATA_DIR / "raw"
REJECTED_DIR = DATA_DIR / "rejected"
LOGS_DIR = DATA_DIR / "logs"

EXPECTED_COLS = [
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn",
]

logging.basicConfig(
    filename=LOGS_DIR / "ingestion.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
DATABASE_ENGINE = None


# 182. Place customer_churn.csv into data/landing/

def create_data_directories():
    for directory in (LANDING_DIR, RAW_DIR, REJECTED_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


# 183. Write detect_files() — scans landing/ and returns list of CSV files

def detect_files():
    return sorted(LANDING_DIR.glob("*.csv"))


# 184. Write validate_schema(filepath) — reads the header row and checks it matches EXPECTED_COLS (21 column names exactly)

def validate_schema(filepath):
    with open(filepath, newline="", encoding="utf-8-sig") as file:
        header = next(csv.reader(file))

    return header == EXPECTED_COLS, header


# 185. Write load_to_staging(filepath, engine) — loads valid CSV into stg_customer_raw, returns row count

def load_to_staging(filepath, engine):
    df = pd.read_csv(filepath)
    df.to_sql("stg_customer_raw", engine, if_exists="replace", index=False)
    return len(df)


# 186. Write log_ingestion(filename, status, rows, reason) — writes to ingestion_log table

def ensure_ingestion_log_table(engine):
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ingestion_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_name VARCHAR(255) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    row_count INT NOT NULL DEFAULT 0,
                    reason TEXT,
                    load_timestamp DATETIME NOT NULL
                )
                """
            )
        )
        columns = connection.execute(
            text("SHOW COLUMNS FROM ingestion_log")
        ).fetchall()
        if not any(column[0] == "reason" for column in columns):
            connection.execute(
                text("ALTER TABLE ingestion_log ADD COLUMN reason TEXT")
            )


def log_ingestion(filename, status, rows, reason):
    if DATABASE_ENGINE is None:
        raise RuntimeError("Database engine has not been configured")

    with DATABASE_ENGINE.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO ingestion_log
                    (file_name, status, row_count, reason, load_timestamp)
                VALUES
                    (:filename, :status, :rows, :reason, NOW())
                """
            ),
            {
                "filename": filename,
                "status": status,
                "rows": rows,
                "reason": reason,
            },
        )


# 187. Write process_landing() — orchestrates: detect → validate → load → log for each file

def process_landing(engine):
    global DATABASE_ENGINE
    DATABASE_ENGINE = engine
    create_data_directories()
    ensure_ingestion_log_table(engine)
    results = []

    for filepath in detect_files():
        valid, header = validate_schema(filepath)

        if not valid:
            missing_columns = [column for column in EXPECTED_COLS if column not in header]
            extra_columns = [column for column in header if column not in EXPECTED_COLS]
            reason_parts = []
            if missing_columns:
                reason_parts.append(f"missing columns: {missing_columns}")
            if extra_columns:
                reason_parts.append(f"unexpected columns: {extra_columns}")
            reason = "; ".join(reason_parts) or "columns are not in the expected order"

            shutil.move(str(filepath), REJECTED_DIR / filepath.name)
            log_ingestion(filepath.name, "REJECTED", 0, reason)
            results.append((filepath.name, "REJECTED", reason))
            continue

        try:
            row_count = load_to_staging(filepath, engine)
            shutil.copy2(filepath, RAW_DIR / filepath.name)
            log_ingestion(filepath.name, "LOADED", row_count, "")
            results.append((filepath.name, "LOADED", row_count))
        except Exception as error:
            logger.exception("Failed to load %s", filepath.name)
            log_ingestion(filepath.name, "REJECTED", 0, str(error))
            results.append((filepath.name, "REJECTED", str(error)))

    return results


# 188. Test: run with a valid file (expect LOADED), an invalid file missing a column (expect REJECTED)

def create_invalid_test_file():
    source = LANDING_DIR / "customer_churn.csv"
    invalid_file = LANDING_DIR / "invalid_customer_churn.csv"
    frame = pd.read_csv(source)
    frame.drop(columns=["Churn"]).to_csv(invalid_file, index=False)
    return invalid_file


# 189. Verify: SELECT * FROM ingestion_log shows both entries

def verify_ingestion_log(engine):
    with engine.connect() as connection:
        return connection.execute(
            text("SELECT * FROM ingestion_log ORDER BY id")
        ).fetchall()


def main():
    create_data_directories()
    database_url = "mysql+pymysql://root:root@localhost/churn"
    engine = create_engine(database_url)

    results = process_landing(engine)
    print("Processing results:")
    for result in results:
        print(result)

    print("Ingestion log:")
    for row in verify_ingestion_log(engine):
        print(row)


if __name__ == "__main__":
    main()
