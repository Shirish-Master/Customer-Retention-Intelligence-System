"""Batch churn scoring for questions 271-279."""

from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import Float, Integer, String, create_engine, text

try:
    from .predict import predict_churn
except ImportError:
    from predict import predict_churn


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATABASE_URL = "mysql+pymysql://root:root@localhost/churn"


# 271. Create batch_score.py.

def load_customers(engine) -> pd.DataFrame:
    """Load all ML features and add contract_type for model preprocessing."""
    query = text(
        """
        SELECT
            features.customer_id,
            features.tenure,
            features.monthly_charges,
            features.total_charges,
            features.service_count,
            features.high_charge_flag,
            features.is_long_term_customer,
            features.auto_pay_flag,
            features.has_streaming_bundle,
            raw.InternetService AS internet_service,
            contracts.contract_type
        FROM customer_ml_features AS features
        JOIN fact_customer_account AS accounts
            ON accounts.customer_id = features.customer_id
        JOIN dim_contract AS contracts
            ON contracts.contract_id = accounts.contract_id
        JOIN stg_customer_raw AS raw
            ON raw.customerID = features.customer_id
        ORDER BY features.customer_id
        """
    )
    return pd.read_sql(query, engine)


# 272. Load all customers from customer_ml_features.
# customer_ml_features does not store contract_type, so the query above joins
# the existing contract dimension to provide the model's required input.


# 273. Apply predict_churn() to every row using df.apply().
def score_customers(customers: pd.DataFrame) -> pd.DataFrame:
    scored = customers.copy()
    predictions = scored.apply(
        lambda row: predict_churn(
            tenure=int(row["tenure"]),
            monthly_charges=float(row["monthly_charges"]),
            contract_type=row["contract_type"],
            service_count=int(row["service_count"]),
            total_charges=float(row["total_charges"]),
            internet_service=row["internet_service"],
            high_charge_flag=int(row["high_charge_flag"]),
            is_long_term_customer=int(row["is_long_term_customer"]),
            auto_pay_flag=int(row["auto_pay_flag"]),
            has_streaming_bundle=int(row["has_streaming_bundle"]),
        ),
        axis=1,
        result_type="expand",
    )
    return pd.concat([scored, predictions], axis=1)


# 274. Extract risk_score, prediction, confidence into new columns.
# The prediction dictionary returned by predict_churn already expands into
# those three columns in score_customers().


# 275. Add a scoring_date column: datetime.today().strftime("%Y-%m-%d").
def add_scoring_date(scored: pd.DataFrame) -> pd.DataFrame:
    result = scored.copy()
    result["scoring_date"] = datetime.today().strftime("%Y-%m-%d")
    return result


# 276. Save to customer_risk_table (SQL table or CSV): customer_id, risk_score,
# prediction, confidence, scoring_date.
def save_risk_scores(scored: pd.DataFrame, engine) -> pd.DataFrame:
    output = scored[
        ["customer_id", "risk_score", "prediction", "confidence", "scoring_date"]
    ].copy()
    output.to_sql(
        "customer_risk_table",
        engine,
        if_exists="replace",
        index=False,
        dtype={
            "customer_id": String(20),
            "risk_score": Float(),
            "prediction": String(30),
            "confidence": Float(),
            "scoring_date": String(10),
        },
    )
    return output


# 277. Print a summary: count of "Likely to churn" vs "Unlikely to churn" -
# verify approximately 27% churn rate aligns with the training distribution.
def print_summary(scored: pd.DataFrame) -> None:
    counts = scored["prediction"].value_counts().reindex(
        ["Likely to churn", "Unlikely to churn"],
        fill_value=0,
    )
    likely_count = int(counts["Likely to churn"])
    total_count = len(scored)
    likely_rate = likely_count / total_count if total_count else 0.0
    print("Prediction summary:")
    print(counts.to_string())
    print(f"Likely-to-churn rate: {likely_rate:.2%}")
    print("Training churn rate: approximately 26.54%")


# 278. Print top 10 highest risk_score customers - cross-check against SQL6
# view (do the rule-based high-risk customers have high ML scores?).
def print_top_risk(scored: pd.DataFrame, engine) -> None:
    top_10 = scored.nlargest(10, "risk_score")
    print("Top 10 highest-risk customers:")
    print(top_10[["customer_id", "risk_score", "prediction"]].to_string(index=False))

    rule_based = pd.read_sql(
        text("SELECT customer_id FROM v_high_risk_customers"),
        engine,
    )
    rule_based_ids = set(rule_based["customer_id"])
    top_ids = set(top_10["customer_id"])
    overlap = top_ids & rule_based_ids
    print(f"SQL6 high-risk overlap: {len(overlap)} of 10 ({len(overlap) / 10:.1%})")


# 279. Discuss: how would you add this batch scoring as the 7th task in the
# DE7 Airflow DAG?
def dag_discussion() -> None:
    print(
        "Add a score_batch PythonOperator after build_features or run_upsert. "
        "The task should call this script's batch_score(engine) function, "
        "depend on successful feature creation, and publish customer_risk_table "
        "before notify. Airflow will skip scoring when the quality gate fails."
    )


def batch_score(engine) -> pd.DataFrame:
    customers = load_customers(engine)
    scored = add_scoring_date(score_customers(customers))
    output = save_risk_scores(scored, engine)
    print_summary(scored)
    print_top_risk(scored, engine)
    dag_discussion()
    return output


if __name__ == "__main__":
    batch_score(create_engine(DATABASE_URL))
