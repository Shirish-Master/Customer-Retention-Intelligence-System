# 237. Load customer_ml_features (from SQL5 or CP4 CSV)

from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_DIR / "Phase_1" / "customer_features.csv"


def prepare_ml_data():
    df = pd.read_csv(INPUT_FILE)
    df = df.rename(columns={"contract": "contract_type"})

    # 238. Identify the target column: churn (already encoded as 0/1)
    target_column = "churn"
    y = df[target_column]

    if not set(y.dropna().unique()).issubset({0, 1}):
        raise ValueError("The churn target must already be encoded as 0/1")

    # 239. Identify the drop column: customer_id (identifier, not a feature)
    drop_column = "customer_id"
    customer_ids = df[drop_column]
    feature_df = df.drop(columns=[drop_column, target_column])

    # customerID MUST be dropped before any ML training. It is an identifier, not a feature.
    if drop_column in feature_df.columns:
        raise AssertionError("customer_id must not be present in ML features")

    # Binary Yes/No columns must be encoded to 1/0 before ML. Done in CP2.
    binary_columns = [
        "partner",
        "dependents",
        "phone_service",
        "paperless_billing",
        "online_security",
        "online_backup",
        "device_protection",
        "tech_support",
        "streaming_tv",
        "streaming_movies",
    ]
    for column in binary_columns:
        if column in feature_df.columns:
            values = set(feature_df[column].dropna().unique())
            if not values.issubset({0, 1}):
                raise ValueError(f"{column} is not encoded as 0/1: {values}")

    # 240. List all numeric columns: tenure, monthly_charges, total_charges, service_count, high_charge_flag, is_long_term_customer, auto_pay_flag, has_streaming_bundle
    numeric_columns = [
        "tenure",
        "monthly_charges",
        "total_charges",
        "service_count",
        "high_charge_flag",
        "is_long_term_customer",
        "auto_pay_flag",
        "has_streaming_bundle",
    ]

    # 241. List the remaining categorical columns: contract_type, internet_service — these still need encoding
    categorical_columns = ["contract_type", "internet_service"]
    print(f"Numeric columns: {numeric_columns}")
    print(f"Categorical columns: {categorical_columns}")

    missing_columns = set(numeric_columns + categorical_columns) - set(feature_df.columns)
    if missing_columns:
        raise ValueError(f"Missing required ML columns: {sorted(missing_columns)}")

    # 242. Apply one-hot encoding to contract_type and internet_service using pd.get_dummies()
    X = pd.get_dummies(
        feature_df[numeric_columns + categorical_columns],
        columns=categorical_columns,
        dtype=int,
    )

    # 243. Print the final feature set X and target y — print shapes
    print(f"Final feature set X shape: {X.shape}")
    print(f"Target y shape: {y.shape}")
    print("Final feature columns:")
    print(list(X.columns))

    # 244. Print the class balance: y.value_counts(normalize=True) — note the ~73%/27% split
    class_balance = y.value_counts(normalize=True)
    print("Class balance:")
    print(class_balance)

    # 245. Discuss: is this imbalance a problem? What metric should we NOT use as primary?
    print(
        "The class imbalance should be considered when evaluating the model. "
        "Accuracy should not be the primary metric because predicting every row as 0 "
        "could achieve approximately 73% accuracy without identifying churners. "
        "Use recall, precision, F1, ROC-AUC, or PR-AUC instead."
    )

    return X, y, customer_ids


if __name__ == "__main__":
    prepare_ml_data()
