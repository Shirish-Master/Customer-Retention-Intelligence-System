"""Churn prediction helpers for the Phase 6 model."""

import json
import logging
from pathlib import Path

import joblib
import pandas as pd


logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_DIR / "Phase_6" / "models"
MODEL_FILE = MODELS_DIR / "tree_churn.pkl"
FEATURE_COLUMNS_FILE = MODELS_DIR / "feature_columns.json"

# 263. Create predict.py: load the best model from models/ at module level.
# ML2 selects the Decision Tree using the strongest held-out churn F1 score.
model = joblib.load(MODEL_FILE)


# LAB_CL1 - Phase 7 fix
#
# Task 7:
# Apply the fix by hand: have train.py persist the feature column list to
# models/feature_columns.json, and have predict.py read that file instead of
# hardcoding values
#
# Before the fix this module carried its own copies of values that belong to
# the training run: MONTHLY_CHARGES_MEDIAN = 70.35 as a literal, and
# internet_service / auto_pay_flag / has_streaming_bundle as literal defaults
# in the function signatures. Nothing kept them in step with the training data,
# and internet_service is the third most important feature in the tree - so a
# wrong literal there moved the risk score more than most real inputs did.
#
# All four now come from the contract LAB_ML2.py writes at fit time.
if not FEATURE_COLUMNS_FILE.exists():
    raise FileNotFoundError(
        f"{FEATURE_COLUMNS_FILE} is missing. Run 'python Phase_6/LAB_ML2.py' to "
        "train the model and write the feature contract."
    )

_contract = json.loads(FEATURE_COLUMNS_FILE.read_text(encoding="utf-8"))

FEATURE_COLUMNS: list[str] = _contract["feature_columns"]
TRAINING_DEFAULTS: dict = _contract["training_defaults"]
MONTHLY_CHARGES_MEDIAN: float = TRAINING_DEFAULTS["monthly_charges_median"]

# The contract and the pickle must describe the same model. If they drift, the
# reindex below would silently zero-fill real features instead of failing.
_model_columns = list(model.feature_names_in_)
if FEATURE_COLUMNS != _model_columns:
    raise ValueError(
        "feature_columns.json does not match the loaded model.\n"
        f"  contract: {FEATURE_COLUMNS}\n"
        f"  model:    {_model_columns}\n"
        "Retrain with 'python Phase_6/LAB_ML2.py' so both are written together."
    )


# 264. Define preprocess_input(tenure, monthly_charges, contract_type, service_count)
# - creates a properly encoded single-row DataFrame matching the training feature columns.
def preprocess_input(
    tenure: int,
    monthly_charges: float,
    contract_type: str,
    service_count: int,
    *,
    total_charges: float | None = None,
    internet_service: str | None = None,
    high_charge_flag: int | None = None,
    is_long_term_customer: int | None = None,
    auto_pay_flag: int | None = None,
    has_streaming_bundle: int | None = None,
) -> pd.DataFrame:
    """Build one row with the same columns used when training the model.

    Every keyword argument defaults to None meaning "the caller did not supply
    this". A value that is genuinely derivable from the caller's data is
    computed; anything else falls back to the training-set default recorded in
    feature_columns.json, and the fallback is logged so it is visible rather
    than silent.
    """
    valid_contracts = {"Month-to-month", "One year", "Two year"}
    if contract_type not in valid_contracts:
        raise ValueError(f"contract_type must be one of: {sorted(valid_contracts)}")

    # Fallbacks to training-set values, recorded so callers can see them.
    defaulted: list[str] = []

    if internet_service is None:
        internet_service = TRAINING_DEFAULTS["internet_service"]
        defaulted.append("internet_service")

    if auto_pay_flag is None:
        auto_pay_flag = TRAINING_DEFAULTS["auto_pay_flag"]
        defaulted.append("auto_pay_flag")

    if has_streaming_bundle is None:
        has_streaming_bundle = TRAINING_DEFAULTS["has_streaming_bundle"]
        defaulted.append("has_streaming_bundle")

    if defaulted:
        logger.warning(
            "predict_churn fell back to training defaults for: %s. The risk "
            "score is less reliable than one scored from full customer data.",
            ", ".join(defaulted),
        )

    valid_internet = {"DSL", "Fiber optic", "No"}
    if internet_service not in valid_internet:
        raise ValueError(f"internet_service must be one of: {sorted(valid_internet)}")

    row = pd.DataFrame(
        [
            {
                "tenure": tenure,
                "monthly_charges": monthly_charges,
                # Derived from the caller's own tenure and charges, not a
                # placeholder, but still an estimate when the real billed
                # total is not passed in.
                "total_charges": (
                    tenure * monthly_charges
                    if total_charges is None
                    else total_charges
                ),
                "service_count": service_count,
                # Threshold comes from the training run via the contract.
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
        columns=_contract["categorical_prefixes"],
        dtype=int,
    )
    # Align to the persisted training column order rather than reaching into
    # the estimator for it.
    return encoded.reindex(columns=FEATURE_COLUMNS, fill_value=0)


def predict_churn(
    tenure: int,
    monthly_charges: float,
    contract_type: str,
    service_count: int,
    *,
    total_charges: float | None = None,
    internet_service: str | None = None,
    high_charge_flag: int | None = None,
    is_long_term_customer: int | None = None,
    auto_pay_flag: int | None = None,
    has_streaming_bundle: int | None = None,
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
