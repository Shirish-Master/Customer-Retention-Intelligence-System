# 196. Write build_features(engine) — reads cleaned_customers, computes all 6 features from CP4, writes to customer_ml_features table

from pathlib import Path

import pandas as pd
from sqlalchemy import Integer, Float, String, create_engine, text


PROJECT_DIR = Path(__file__).resolve().parents[1]
CP4_OUTPUT = PROJECT_DIR / "Phase_1" / "customer_features.csv"
DATABASE_URL = "mysql+pymysql://root:root@localhost/churn"

SERVICE_COLUMNS = [
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
]

FEATURE_COLUMNS = [
    "tenure_bucket",
    "high_charge_flag",
    "service_count",
    "is_long_term_customer",
    "has_streaming_bundle",
    "auto_pay_flag",
]


def build_features(engine):
    cleaned_df = pd.read_sql("SELECT * FROM cleaned_customers", engine)
    feature_df = cleaned_df.copy()

    for column in SERVICE_COLUMNS:
        feature_df[column] = feature_df[column].replace(
            {
                "Yes": 1,
                "No": 0,
                "No internet service": 0,
            }
        ).astype(int)

    # 197. Ensure the feature logic exactly matches CP4: same thresholds (median for high_charge_flag), same column names, same data types
    feature_df["tenure_bucket"] = pd.cut(
        feature_df["tenure"],
        bins=[0, 12, 24, 48, 72],
        labels=["0-12", "13-24", "25-48", "49-72"],
        include_lowest=True,
    ).astype(str)
    median_charge = feature_df["monthly_charges"].median()
    feature_df["high_charge_flag"] = (
        feature_df["monthly_charges"] > median_charge
    ).astype("int64")
    feature_df["service_count"] = feature_df[SERVICE_COLUMNS].sum(axis=1).astype("int64")
    feature_df["is_long_term_customer"] = (
        feature_df["tenure"] >= 24
    ).astype("int64")
    feature_df["has_streaming_bundle"] = (
        (feature_df["streaming_tv"] == 1)
        & (feature_df["streaming_movies"] == 1)
    ).astype("int64")
    feature_df["auto_pay_flag"] = (
        feature_df["payment_method"]
        .str.contains("automatic", case=False, na=False)
        .astype("int64")
    )

    output_columns = [
        "customer_id",
        "tenure",
        "monthly_charges",
        "total_charges",
        "churn",
        *FEATURE_COLUMNS,
    ]
    output_df = feature_df[output_columns].copy()
    output_df.to_sql(
        "customer_ml_features",
        engine,
        if_exists="replace",
        index=False,
        dtype={
            "customer_id": String(20),
            "tenure": Integer(),
            "monthly_charges": Float(),
            "total_charges": Float(),
            "churn": Integer(),
            "tenure_bucket": String(20),
            "high_charge_flag": Integer(),
            "service_count": Integer(),
            "is_long_term_customer": Integer(),
            "has_streaming_bundle": Integer(),
            "auto_pay_flag": Integer(),
        },
    )
    return output_df


# 198. Add a validation step: count of customer_ml_features should equal count of cleaned_customers

def validate_feature_count(engine):
    with engine.connect() as connection:
        cleaned_count = connection.execute(
            text("SELECT COUNT(*) FROM cleaned_customers")
        ).scalar_one()
        feature_count = connection.execute(
            text("SELECT COUNT(*) FROM customer_ml_features")
        ).scalar_one()

    passed = cleaned_count == feature_count
    print(
        f"{'PASS' if passed else 'FAIL'} - feature row count: "
        f"{feature_count} / cleaned row count: {cleaned_count}"
    )
    assert passed, "customer_ml_features row count does not match cleaned_customers"


# 199. Add a schema check: confirm all 6 feature columns are present and non-null

def validate_feature_schema(engine):
    with engine.connect() as connection:
        columns = {
            row[0]
            for row in connection.execute(text("DESCRIBE customer_ml_features"))
        }

    missing_columns = set(FEATURE_COLUMNS) - columns
    assert not missing_columns, f"Missing feature columns: {sorted(missing_columns)}"

    feature_df = pd.read_sql(
        f"SELECT {', '.join(FEATURE_COLUMNS)} FROM customer_ml_features",
        engine,
    )
    null_counts = feature_df[FEATURE_COLUMNS].isna().sum()
    total_nulls = int(null_counts.sum())
    print(f"{'PASS' if total_nulls == 0 else 'FAIL'} - feature schema/null check: {total_nulls} NULLs")
    assert total_nulls == 0, f"Feature columns contain NULLs: {null_counts.to_dict()}"


# 200. Test: run the function and query customer_ml_features — spot-check 3 customers against the CSV output from CP4

def spot_check_cp4_output(engine):
    database_features = pd.read_sql(
        "SELECT customer_id, tenure_bucket, high_charge_flag, service_count, "
        "is_long_term_customer, has_streaming_bundle, auto_pay_flag "
        "FROM customer_ml_features ORDER BY customer_id LIMIT 3",
        engine,
    )
    cp4_features = pd.read_csv(CP4_OUTPUT)
    cp4_features = cp4_features[
        ["customer_id", *FEATURE_COLUMNS]
    ].sort_values("customer_id").head(3).reset_index(drop=True)
    database_features = database_features.sort_values("customer_id").reset_index(drop=True)
    database_features["tenure_bucket"] = database_features["tenure_bucket"].astype(str)

    pd.testing.assert_frame_equal(
        database_features,
        cp4_features,
        check_dtype=False,
        check_like=False,
    )
    print("PASS - CP4 spot-check: 3 customers match")


# 201. Discuss: if the CP4 feature definitions change, what do you need to update in the pipeline?

def feature_definition_discussion():
    print(
        "If CP4 feature definitions change, update the feature transformation logic, "
        "feature column names and data types, the customer_ml_features schema, "
        "validation tests, and any downstream ML model or API code that consumes those features."
    )


def main():
    engine = create_engine(DATABASE_URL)
    build_features(engine)
    validate_feature_count(engine)
    validate_feature_schema(engine)
    spot_check_cp4_output(engine)
    feature_definition_discussion()


if __name__ == "__main__":
    main()
