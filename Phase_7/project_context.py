"""Phase 7 - the project's memory: facts Claude should always know.

Task 1:
Draft the contents of your project's "memory" - the facts Claude should always
know: your data quirks, your ML rules, your table names. Keep it under 200
lines  [Claude.ai]

Task 2:
Save this as project_context.py and import it into every script that calls
Claude, prepended to the system prompt

Facts are stored as named blocks so a single one can be omitted at build time.
That is what makes Task 3 possible - drop a fact, watch the answer degrade,
put it back. Never put secrets, credentials or customer rows in here; this
text is sent to the API verbatim on every call.
"""

from __future__ import annotations

FACTS: dict[str, str] = {
    "project": """
## Project
Telco customer churn pipeline, built in phases. Python 3.12, MySQL 8, FastAPI
backend, React (create-react-app) frontend. Source data: customer_churn.csv,
7043 rows, the public IBM Telco Customer Churn dataset.
Phase_1 cleaning/features, Phase_2 SQL, Phase_3 API, Phase_4 React,
Phase_5 Spark/Airflow, Phase_6 ML, Phase_7 Claude integration.
""",
    "layout": """
## Where things live
- FastAPI app:      Phase_3/main.py   (run as `uvicorn Phase_3.main:app` FROM
                    THE PROJECT ROOT - it imports Phase_6.predict, so the root
                    must be on sys.path)
- Training script:  Phase_6/LAB_ML2.py  (this is the "train.py" role; there is
                    no file named train.py). Feature prep: Phase_6/LAB_ML1.py
- Inference:        Phase_6/predict.py
- Batch scoring:    Phase_6/batch_score.py
- Model artefacts:  Phase_6/models/ (tree_churn.pkl, logistic_churn.pkl,
                    feature_columns.json)
- React app:        Phase_4/customer-dashboard/ (a git submodule)
""",
    "tables": """
## Database table names (MySQL, schema `churn`)
- stg_customer_raw      raw staging. KEEPS THE ORIGINAL CamelCase COLUMN NAMES
                        (customerID, InternetService, OnlineSecurity,
                        StreamingTV, StreamingMovies, TechSupport, ...).
                        Everything else in the project is snake_case.
- fact_customer_account fact table: customer_id, tenure, monthly_charges,
                        total_charges, churn, contract_id, payment_id
- dim_contract          contract_id, contract_type
- dim_payment           payment_id, payment_method
- customer_ml_features  one row per customer, the ML feature store
- v_high_risk_customers rule-based view (NOT ML-based), used by
                        GET /customers/high-risk
- customer_risk_table   written by batch_score.py: customer_id, risk_score,
                        prediction, confidence, scoring_date
Join key is customer_id everywhere EXCEPT stg_customer_raw, where it is
customerID.
""",
    "data_quirks": """
## Data quirks - these bite people
- total_charges arrives as a STRING with blank values (" ") for customers whose
  tenure is 0. CustomerCleaner.fix_total_charges() coerces to NaN via
  pd.to_numeric(errors="coerce"), then handle_nulls() fills them with that
  customer's monthly_charges. SQL mirrors this with
  COALESCE(f.total_charges, f.monthly_charges).
- Column names are lowercased to snake_case in Phase_1 only. stg_customer_raw
  is the exception above.
- churn is stored 0/1, already encoded. Yes/No -> 1/0 happens in
  CustomerCleaner.normalize_binary_columns() for partner, dependents,
  phone_service, paperless_billing and churn.
- Class balance is roughly 73% active / 27% churned. Never use accuracy as the
  headline metric; use F1 on the Churned class.
- internet_service has three values: "DSL", "Fiber optic", "No". "No" means no
  internet product at all, not a missing value.
- KNOWN INCONSISTENCY: high_charge_flag is computed two different ways.
  Phase_2/LAB_SQL5.sql uses `monthly_charges > AVG(monthly_charges)` (mean,
  about 64.76). Phase_6 uses `monthly_charges > median` (70.35, recorded in
  feature_columns.json). So the flag in customer_ml_features does not always
  match the one predict.py derives. It currently has zero effect because the
  tree assigns high_charge_flag zero importance, but do not assume they agree.
""",
    "feature_rules": """
## Feature engineering rules
- service_count = count of Yes across the 6 service columns (OnlineSecurity,
  OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies).
- has_streaming_bundle = 1 only when StreamingTV AND StreamingMovies are both
  Yes.
- auto_pay_flag = 1 when dim_payment.payment_method LIKE '%automatic%'.
- is_long_term_customer = 1 when tenure >= 24.
- tenure_bucket is one of '0-12', '13-24', '25-48', '49-72'.
- tenure_bucket is NOT a model feature; it exists for reporting only.
""",
    "ml_rules": """
## ML rules - non-negotiable
- customer_id is an identifier, never a feature. It must be dropped before fit.
- The production model is the Decision Tree (max_depth=5, random_state=42),
  selected on Churned-class F1, not accuracy. Held-out F1 0.6154,
  accuracy 0.7906, 5-fold CV F1 0.5710. Logistic Regression is trained and
  saved alongside it but is NOT the served model.
- Training is deterministic: random_state=42 and a fixed 80/20 stratified
  split. Retraining on unchanged data must reproduce those metrics exactly. If
  it does not, something upstream changed.
- 14 feature columns, in this fitted order: tenure, monthly_charges,
  total_charges, service_count, high_charge_flag, is_long_term_customer,
  auto_pay_flag, has_streaming_bundle, contract_type_Month-to-month,
  contract_type_One year, contract_type_Two year, internet_service_DSL,
  internet_service_Fiber optic, internet_service_No.
- contract_type and internet_service are one-hot encoded with pd.get_dummies.
- Feature importance is lopsided: contract_type_Month-to-month 0.519,
  tenure 0.166, internet_service_Fiber optic 0.165, monthly_charges 0.052,
  total_charges 0.043. FOUR FEATURES HAVE ZERO IMPORTANCE:
  is_long_term_customer, high_charge_flag, service_count, internet_service_DSL.
- Fiber optic customers churn at 41.9%, DSL at 19.0%, No internet at 7.4%,
  against a 26.5% base rate.
""",
    "feature_contract": """
## The feature contract (added in LAB_CL1)
Phase_6/LAB_ML2.py writes Phase_6/models/feature_columns.json at fit time:
the fitted column list, plus training-derived defaults (monthly_charges_median
70.35, internet_service "Fiber optic", auto_pay_flag 0, has_streaming_bundle 0).
predict.py reads that file and asserts the column list against
model.feature_names_in_ at import. Never hardcode a training statistic in
inference code; add it to this contract instead. If the assertion fires, the
pkl and the json were written by different runs - retrain, do not patch.
""",
    "known_defects": """
## Known open defects - do not "fix" these silently, they are lab material
- Phase_3/main.py defines ChurnPredictionRequest TWICE. The /predict-churn
  route was decorated before the second definition, so it binds to the FIRST
  (unvalidated) class. The LAB_API6 validators (tenure ge=0 le=100,
  monthly_charges gt=0) therefore never apply to that route.
- Phase_1/test_customer_cleaner.py opens '..\\customer_churn.csv' by relative
  path, so it only collects when run from inside Phase_1/.
- predict.py estimates total_charges as tenure * monthly_charges when the real
  billed total is not supplied. Derived, not hardcoded, but still an estimate.
""",
    "api_shape": """
## API surface
GET  /customer/{customer_id}            -> 404 "Customer not found" if absent
GET  /customer/{customer_id}/features   -> 404 "Customer features not found"
GET  /churn/summary                     -> totals + by_contract + by_internet_service
GET  /customers/high-risk               -> limit (default 50), min_tenure, max_tenure
POST /predict-churn                     -> {risk_score, prediction, confidence}
predict returns prediction as exactly "Likely to churn" or
"Unlikely to churn" - the React UI switches its risk colour on those strings.
CORS allows http://localhost:3000 only. An X-API-Key header check exists via
verify_api_key but is not currently wired onto the routes.
""",
    "conventions": """
## Conventions
- Lab step numbers appear as comments (e.g. "# 263.") and are load-bearing for
  marking. Never renumber or delete them.
- Files are named LAB_<AREA><N>.py by phase. Do not rename them to conventional
  names; other scripts and the course checklist refer to them as they are.
- Money is FLOAT in MySQL and float in Python. Risk scores are floats in [0,1].
""",
}

# Order matters: the model reads this top to bottom.
FACT_ORDER: list[str] = list(FACTS)

PREAMBLE = """You are assisting on a telco customer churn project. The facts
below are the authoritative description of this codebase. Prefer them over
assumptions from similar projects you may have seen. If a fact you need is not
listed here, say so explicitly rather than guessing - a wrong table name or a
wrong feature rule is worse than an admission of uncertainty."""


def build_system_prompt(omit: set[str] | None = None) -> str:
    """Assemble the memory block, optionally leaving one or more facts out.

    `omit` exists for the Task 3 memory test. Production callers pass nothing.
    """
    omit = omit or set()
    unknown = omit - set(FACTS)
    if unknown:
        raise KeyError(f"Unknown fact keys: {sorted(unknown)}")

    blocks = [FACTS[key].strip() for key in FACT_ORDER if key not in omit]
    return PREAMBLE + "\n\n" + "\n\n".join(blocks)


# The default memory, prepended to the system prompt of every Claude call.
SYSTEM_PROMPT: str = build_system_prompt()
