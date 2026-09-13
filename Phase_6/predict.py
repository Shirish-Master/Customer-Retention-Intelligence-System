"""Churn prediction helpers for the Phase 6 model."""

from pathlib import Path

import joblib
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_FILE = PROJECT_DIR / "Phase_6" / "models" / "tree_churn.pkl"
MONTHLY_CHARGES_MEDIAN = 70.35

# 263. Create predict.py: load the best model from models/ at module level.
# ML2 selects the Decision Tree using the strongest held-out churn F1 score.
model = joblib.load(MODEL_FILE)


# 264. Define preprocess_input(tenure, monthly_charges, contract_type, service_count)
# - creates a properly encoded single-row DataFrame matching the training feature columns.
def preprocess_input(
    tenure: int,
    monthly_charges: float,
    contract_type: str,
    service_count: int,
    *,
    total_charges: float | None = None,
    internet_service: str = "Fiber optic",
    high_charge_flag: int | None = None,
    is_long_term_customer: int | None = None,
    auto_pay_flag: int = 0,
    has_streaming_bundle: int = 0,
) -> pd.DataFrame:
    """Build one row with the same columns used when training the model."""
    valid_contracts = {"Month-to-month", "One year", "Two year"}
    if contract_type not in valid_contracts:
        raise ValueError(f"contract_type must be one of: {sorted(valid_contracts)}")

    row = pd.DataFrame(
        [
            {
                "tenure": tenure,
                "monthly_charges": monthly_charges,
                "total_charges": (
                    tenure * monthly_charges
                    if total_charges is None
                    else total_charges
                ),
                "service_count": service_count,
                "high_charge_flag": (
                    int(monthly_charges > MONTHLY_CHARGES_MEDIAN)
                    if high_charge_flag is None
                    else high_charge_flag
                ),
                "is_long_term_customer": (
                    int(tenure >= 24)
                    if is_long_term_customer is None
                    else is_long_term_customer
                ),
                "auto_pay_flag": auto_pay_flag,
                "has_streaming_bundle": has_streaming_bundle,
                "contract_type": contract_type,
                "internet_service": internet_service,
            }
        ]
    )

    encoded = pd.get_dummies(
        row,
        columns=["contract_type", "internet_service"],
        dtype=int,
    )
    return encoded.reindex(columns=model.feature_names_in_, fill_value=0)


def predict_churn(
    tenure: int,
    monthly_charges: float,
    contract_type: str,
    service_count: int,
    *,
    total_charges: float | None = None,
    internet_service: str = "Fiber optic",
    high_charge_flag: int | None = None,
    is_long_term_customer: int | None = None,
    auto_pay_flag: int = 0,
    has_streaming_bundle: int = 0,
) -> dict[str, float | str]:
    """Return churn probability, class label, and predicted-class confidence."""
    # 265. Define predict_churn(tenure, monthly_charges, contract_type, service_count)
    # - calls preprocess_input, then model.predict() and predict_proba().
    features = preprocess_input(
        tenure,
        monthly_charges,
        contract_type,
        service_count,
        total_charges=total_charges,
        internet_service=internet_service,
        high_charge_flag=high_charge_flag,
        is_long_term_customer=is_long_term_customer,
        auto_pay_flag=auto_pay_flag,
        has_streaming_bundle=has_streaming_bundle,
    )
    prediction_value = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]
    risk_score = float(probabilities[1])
    confidence = float(probabilities[prediction_value])

    # 266. Return: {"risk_score": float, "prediction": "Likely to churn" /
    # "Unlikely to churn", "confidence": float}.
    return {
        "risk_score": risk_score,
        "prediction": (
            "Likely to churn" if prediction_value == 1 else "Unlikely to churn"
        ),
        "confidence": confidence,
    }
