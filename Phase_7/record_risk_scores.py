"""Phase 7 - before/after risk score recorder.

Task 8:
Re-run your test predictions and your batch scoring job, and record the risk
scores before and after the fix

Run this UNCHANGED both before and after the fix:

    python Phase_7/record_risk_scores.py before
    python Phase_7/record_risk_scores.py after

The personas below carry the customer's *real* attributes (internet_service,
auto_pay_flag, has_streaming_bundle, total_charges). Before the fix
ChurnPredictionRequest silently drops those extra keys, so the API path scores
every customer as if they were on Fiber optic with no autopay. After the fix the
same call honours them. The script itself never changes - only the code under it.
"""

import json
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from Phase_3.main import ChurnPredictionRequest  # noqa: E402
from Phase_3.main import predict_churn as api_predict_churn  # noqa: E402
from Phase_6.predict import predict_churn  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent
DATABASE_URL = "mysql+pymysql://root:root@localhost/churn"


# The same five customers used for the before/after table. Every field here is
# known-real customer data - nothing is invented at call time.
PERSONAS = [
    {
        "name": "P1 loyal / two-year / no internet",
        "tenure": 68,
        "monthly_charges": 24.50,
        "contract_type": "Two year",
        "service_count": 2,
        "internet_service": "No",
        "auto_pay_flag": 1,
        "has_streaming_bundle": 0,
        "total_charges": 1666.00,
    },
    {
        "name": "P2 mid-tenure / month-to-month / DSL",
        "tenure": 18,
        "monthly_charges": 55.00,
        "contract_type": "Month-to-month",
        "service_count": 3,
        "internet_service": "DSL",
        "auto_pay_flag": 1,
        "has_streaming_bundle": 0,
        "total_charges": 990.00,
    },
    {
        "name": "P3 new / month-to-month / fiber (genuine high risk)",
        "tenure": 2,
        "monthly_charges": 85.00,
        "contract_type": "Month-to-month",
        "service_count": 1,
        "internet_service": "Fiber optic",
        "auto_pay_flag": 0,
        "has_streaming_bundle": 0,
        "total_charges": 170.00,
    },
    {
        "name": "P4 long tenure / one year / DSL / autopay",
        "tenure": 44,
        "monthly_charges": 60.25,
        "contract_type": "One year",
        "service_count": 4,
        "internet_service": "DSL",
        "auto_pay_flag": 1,
        "has_streaming_bundle": 1,
        "total_charges": 2651.00,
    },
    {
        "name": "P5 new / month-to-month / no internet",
        "tenure": 3,
        "monthly_charges": 20.05,
        "contract_type": "Month-to-month",
        "service_count": 1,
        "internet_service": "No",
        "auto_pay_flag": 0,
        "has_streaming_bundle": 0,
        "total_charges": 60.15,
    },
]


def score_via_api(persona: dict) -> dict:
    """Score through the FastAPI request model - the path the React form uses."""
    payload = {key: value for key, value in persona.items() if key != "name"}
    # Extra keys are ignored by Pydantic before the fix and honoured after it.
    request = ChurnPredictionRequest(**payload)
    return api_predict_churn(request)


def score_ground_truth(persona: dict) -> dict:
    """Score by calling predict_churn directly with every real attribute."""
    payload = {key: value for key, value in persona.items() if key != "name"}
    return predict_churn(**payload)


def run_personas() -> pd.DataFrame:
    rows = []
    for persona in PERSONAS:
        api_result = score_via_api(persona)
        truth_result = score_ground_truth(persona)
        rows.append(
            {
                "persona": persona["name"],
                "internet_service": persona["internet_service"],
                "auto_pay_flag": persona["auto_pay_flag"],
                "api_risk_score": round(api_result["risk_score"], 4),
                "api_prediction": api_result["prediction"],
                "direct_risk_score": round(truth_result["risk_score"], 4),
                "direct_prediction": truth_result["prediction"],
                "api_matches_direct": (
                    round(api_result["risk_score"], 6)
                    == round(truth_result["risk_score"], 6)
                ),
            }
        )
    return pd.DataFrame(rows)


def run_batch(engine) -> dict:
    """Aggregate the full batch scoring job without writing to the database."""
    from Phase_6.batch_score import load_customers, score_customers

    customers = load_customers(engine)
    scored = score_customers(customers)
    counts = scored["prediction"].value_counts()
    return {
        "rows_scored": int(len(scored)),
        "mean_risk_score": round(float(scored["risk_score"].mean()), 6),
        "median_risk_score": round(float(scored["risk_score"].median()), 6),
        "likely_to_churn": int(counts.get("Likely to churn", 0)),
        "unlikely_to_churn": int(counts.get("Unlikely to churn", 0)),
        "likely_rate": round(
            float(counts.get("Likely to churn", 0)) / len(scored), 6
        ),
    }


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "before"
    if label not in {"before", "after"}:
        raise SystemExit("usage: python Phase_7/record_risk_scores.py [before|after]")

    persona_table = run_personas()
    print(f"=== Persona risk scores ({label} the fix) ===")
    print(persona_table.to_string(index=False))

    batch_summary = None
    try:
        batch_summary = run_batch(create_engine(DATABASE_URL))
        print(f"\n=== Batch scoring job ({label} the fix) ===")
        for key, value in batch_summary.items():
            print(f"{key}: {value}")
    except Exception as error:  # noqa: BLE001 - the DB is optional for this record
        print(f"\nBatch scoring skipped - database unavailable: {error}")

    persona_table.to_csv(OUTPUT_DIR / f"risk_scores_{label}.csv", index=False)
    (OUTPUT_DIR / f"risk_scores_{label}.json").write_text(
        json.dumps(
            {
                "label": label,
                "personas": persona_table.to_dict(orient="records"),
                "batch": batch_summary,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSaved risk_scores_{label}.csv and risk_scores_{label}.json")


if __name__ == "__main__":
    main()
