# 228. Map all pipeline stages to Airflow tasks: ingest, validate_quality, clean, build_features, run_upsert, notify

import logging
import sys
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine, text


PROJECT_DIR = Path(__file__).resolve().parents[2]
PHASE_5_DIR = PROJECT_DIR / "Phase_5"
sys.path.insert(0, str(PHASE_5_DIR))

DATABASE_URL = "mysql+pymysql://root:root@localhost/churn"
logger = logging.getLogger(__name__)


def get_engine():
    return create_engine(DATABASE_URL)


# 229. Create dags/customer_pipeline_dag.py with a @daily scheduled DAG


def ingest():
    from LAB_DE2 import process_landing

    process_landing(get_engine())


def validate_quality():
    from LAB_DE7 import (
        log_warning_failures,
        run_quality_checks,
        stop_on_critical_failures,
        write_quality_report,
    )

    import pandas as pd

    quality_file = PROJECT_DIR / "Phase_1" / "customer_features.csv"
    quality_df = pd.read_csv(quality_file)
    checks = run_quality_checks(quality_df)
    write_quality_report(checks)
    log_warning_failures(checks)
    stop_on_critical_failures(checks)


def clean():
    from LAB_DE3 import clean_staging

    clean_staging(get_engine())


def build_features():
    from LAB_DE4 import build_features as build_database_features

    build_database_features(get_engine())


def run_upsert():
    from LAB_DE6 import ensure_run_log_table, upsert_customers

    engine = get_engine()
    ensure_run_log_table(engine)
    upsert_customers(engine, PROJECT_DIR / "customer_churn.csv")


# 230. Define each stage as a PythonOperator calling the relevant function


def notify():
    with get_engine().connect() as connection:
        customer_count = connection.execute(
            text("SELECT COUNT(*) FROM customers")
        ).scalar_one()

    # 233. Add a simple notify() task that logs "Customer intelligence pipeline complete — X customers processed"
    logger.info(
        "Customer intelligence pipeline complete — %s customers processed",
        customer_count,
    )


# 231. Chain: ingest >> validate_quality >> clean >> build_features >> run_upsert >> notify

with DAG(
    dag_id="customer_intelligence_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["customer", "data-engineering"],
) as customer_pipeline_dag:
    ingest_task = PythonOperator(
        task_id="ingest",
        python_callable=ingest,
    )
    validate_quality_task = PythonOperator(
        task_id="validate_quality",
        python_callable=validate_quality,
    )
    clean_task = PythonOperator(
        task_id="clean",
        python_callable=clean,
    )
    build_features_task = PythonOperator(
        task_id="build_features",
        python_callable=build_features,
    )
    run_upsert_task = PythonOperator(
        task_id="run_upsert",
        python_callable=run_upsert,
    )
    notify_task = PythonOperator(
        task_id="notify",
        python_callable=notify,
    )

    ingest_task >> validate_quality_task >> clean_task >> build_features_task >> run_upsert_task >> notify_task


# 232. Add a quality gate: if validate_quality task fails, all downstream tasks are skipped (Airflow handles this automatically via task chaining)

# 234. Trigger the DAG manually and watch all 6 tasks succeed in the Airflow UI

# 235. Break one task deliberately (e.g. delete the landing file) — confirm downstream tasks do not run

# 236. Discuss: how would you extend this DAG to trigger ML batch scoring (ML5) after build_features completes?
# Add an ML5 PythonOperator after build_features_task and before run_upsert_task,
# or use a TriggerDagRunOperator to start a separate ML scoring DAG. The ML5
# task should consume the completed customer_ml_features table and publish its
# scoring output before the upsert or notification stage.
