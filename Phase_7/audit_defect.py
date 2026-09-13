"""Phase 7 - Claude API defect audit for the churn prediction path.

Task 4:
Write audit_defect.py: paste train.py and predict.py into one request, and
force a structured findings response using tool_choice rather than accepting
free-text prose

Task 5:
Confirm the findings name every hardcoded feature, and that the response
explicitly does not recommend retraining - this is an inference-time bug, not a
training problem

Run from the project root so the relative paths and .env resolve:

    python Phase_7/audit_defect.py

Note on this project's file names: the checklist calls the training script
train.py. In this repo the training script is Phase_6/LAB_ML2.py (it imports
prepare_ml_data from Phase_6/LAB_ML1.py). Both are sent in the request.
"""

import json
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(__file__).resolve().parent

# The training script plays the train.py role; LAB_ML1 holds the feature build.
TRAIN_FEATURES_FILE = PROJECT_DIR / "Phase_6" / "LAB_ML1.py"
TRAIN_FILE = PROJECT_DIR / "Phase_6" / "LAB_ML2.py"
PREDICT_FILE = PROJECT_DIR / "Phase_6" / "predict.py"
API_FILE = PROJECT_DIR / "Phase_3" / "main.py"

MODEL = "claude-opus-5"

# Every feature predict.py hardcodes as a literal. Task 5 requires the findings
# to name all of them; the check below fails the run if any is missed.
#
# total_charges is deliberately NOT in this list: it is computed as
# tenure * monthly_charges, so it is derived from the caller's own data rather
# than hardcoded. It is an approximation worth reporting, but an audit that
# omits it is not wrong, and this check must not fail a correct answer.
EXPECTED_HARDCODED_FEATURES = [
    "internet_service",
    "auto_pay_flag",
    "has_streaming_bundle",
]

# The fourth hardcode is not a feature column but a training statistic frozen
# into the source as a literal: MONTHLY_CHARGES_MEDIAN = 70.35, which drives
# high_charge_flag.
EXPECTED_HARDCODED_CONSTANT = "70.35"


# 4a. Force a structured findings response using tool_choice rather than
# accepting free-text prose. strict=True guarantees the arguments validate
# against this schema exactly, so the parsing below never has to defend itself
# against prose or malformed JSON.
AUDIT_TOOL = {
    "name": "report_audit_findings",
    "description": (
        "Report the results of a code audit comparing a model training script "
        "against the inference script that loads the trained model. Every "
        "defect found must be reported as a separate entry in findings."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "defect_class": {
                "type": "string",
                "enum": [
                    "inference-time",
                    "training-time",
                    "data-quality",
                    "none",
                ],
                "description": (
                    "Where the defect actually lives. Choose inference-time if "
                    "the trained model is correct but the prediction path feeds "
                    "it wrong inputs."
                ),
            },
            "requires_retraining": {
                "type": "boolean",
                "description": (
                    "True only if the saved model artefact itself must be "
                    "rebuilt to fix the defect."
                ),
            },
            "retraining_rationale": {
                "type": "string",
                "description": (
                    "One or two sentences justifying the requires_retraining "
                    "value."
                ),
            },
            "findings": {
                "type": "array",
                "description": "One entry per distinct defect.",
                "items": {
                    "type": "object",
                    "properties": {
                        "feature_name": {
                            "type": "string",
                            "description": (
                                "The exact feature column affected, e.g. "
                                "internet_service. Use 'n/a' for defects that "
                                "are not tied to a single feature."
                            ),
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                        "location": {
                            "type": "string",
                            "description": "file and approximate line or function",
                        },
                        "problem": {
                            "type": "string",
                            "description": "What is wrong, stated concretely.",
                        },
                        "training_expectation": {
                            "type": "string",
                            "description": (
                                "What the training script assumes this feature "
                                "contains."
                            ),
                        },
                        "inference_reality": {
                            "type": "string",
                            "description": (
                                "What the prediction script actually supplies."
                            ),
                        },
                        "impact_on_risk_score": {
                            "type": "string",
                            "description": (
                                "Direction and rough magnitude of the error in "
                                "the produced risk score."
                            ),
                        },
                        "recommended_fix": {"type": "string"},
                    },
                    "required": [
                        "feature_name",
                        "severity",
                        "location",
                        "problem",
                        "training_expectation",
                        "inference_reality",
                        "impact_on_risk_score",
                        "recommended_fix",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "defect_class",
            "requires_retraining",
            "retraining_rationale",
            "findings",
        ],
        "additionalProperties": False,
    },
}


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_prompt() -> str:
    """4b. Paste train.py and predict.py into one request."""
    return f"""You are auditing a churn model's inference path.

Below are four files from the same project. Compare the feature columns the
training script builds and fits on against the feature row the prediction
script actually constructs at inference time.

Report every place where the prediction script supplies a value that was not
derived from the caller's real customer data. For each one, state what training
expected versus what inference supplies, and which direction that pushes the
risk score.

Decide whether fixing this requires retraining the saved model, or whether the
model artefact is fine and only the inference path is wrong.

Call the report_audit_findings tool with your results.

===== FILE: Phase_6/LAB_ML1.py (feature preparation used by training) =====
{read_source(TRAIN_FEATURES_FILE)}

===== FILE: Phase_6/LAB_ML2.py (training script - the train.py role) =====
{read_source(TRAIN_FILE)}

===== FILE: Phase_6/predict.py (inference script) =====
{read_source(PREDICT_FILE)}

===== FILE: Phase_3/main.py (FastAPI route that calls predict_churn) =====
{read_source(API_FILE)}
"""


def run_audit() -> dict:
    load_dotenv(PROJECT_DIR / ".env")

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set. Add it to .env in the project root."
        )

    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            tools=[AUDIT_TOOL],
            # 4c. tool_choice forces the tool - the model cannot answer in prose.
            tool_choice={"type": "tool", "name": "report_audit_findings"},
            messages=[{"role": "user", "content": build_prompt()}],
        )
    except anthropic.AuthenticationError as error:
        raise SystemExit(
            f"Claude rejected the API key ({error.status_code}). Check that "
            "ANTHROPIC_API_KEY in .env is a live key. Run "
            "'python Phase_7/audit_defect.py --dry-run' to check the request "
            "builds correctly without calling the API."
        ) from error

    print(f"usage: {response.usage}")

    for block in response.content:
        if block.type == "tool_use" and block.name == "report_audit_findings":
            return block.input

    raise RuntimeError(
        "No report_audit_findings tool_use block in the response. "
        f"stop_reason={response.stop_reason}"
    )


def dry_run() -> None:
    """Build and validate the request without spending a call or needing a key."""
    prompt = build_prompt()
    payload = {
        "model": MODEL,
        "max_tokens": 16000,
        "tools": [AUDIT_TOOL],
        "tool_choice": {"type": "tool", "name": "report_audit_findings"},
        "messages": [{"role": "user", "content": prompt}],
    }

    # Round-trips cleanly => the tool schema and prompt are JSON-serialisable.
    json.dumps(payload)

    schema = AUDIT_TOOL["input_schema"]
    assert schema["additionalProperties"] is False, "strict mode needs this"
    assert set(schema["required"]) == set(schema["properties"]), (
        "strict mode requires every property to be listed in required"
    )

    print("Dry run OK - request builds and the tool schema is strict-mode valid.")
    print(f"  model:          {MODEL}")
    print(f"  forced tool:    {AUDIT_TOOL['name']}")
    print(f"  files pasted:   4")
    print(f"  prompt chars:   {len(prompt):,}")
    print(f"  payload bytes:  {len(json.dumps(payload)):,}")
    print(f"  required keys:  {sorted(schema['required'])}")


# 5. Confirm the findings name every hardcoded feature, and that the response
# explicitly does not recommend retraining - this is an inference-time bug, not
# a training problem.
def verify_findings(findings: dict) -> list[str]:
    """Return a list of verification failures; empty means the audit passed."""
    failures: list[str] = []

    named_features = " ".join(
        f"{item['feature_name']} {item['problem']} {item['inference_reality']}"
        for item in findings["findings"]
    ).lower()

    for feature in EXPECTED_HARDCODED_FEATURES:
        if feature.lower() not in named_features:
            failures.append(f"findings never name the hardcoded feature: {feature}")

    if EXPECTED_HARDCODED_CONSTANT not in named_features:
        failures.append(
            "findings never name the hardcoded training statistic "
            f"MONTHLY_CHARGES_MEDIAN = {EXPECTED_HARDCODED_CONSTANT}"
        )

    if findings["requires_retraining"] is not False:
        failures.append(
            "response recommends retraining; this is an inference-time defect "
            "and the saved model artefact is correct"
        )

    if findings["defect_class"] != "inference-time":
        failures.append(
            f"defect_class is {findings['defect_class']!r}, expected "
            "'inference-time'"
        )

    if not findings["findings"]:
        failures.append("findings array is empty")

    return failures


def main() -> None:
    if "--dry-run" in sys.argv:
        dry_run()
        return

    findings = run_audit()

    output_file = OUTPUT_DIR / "audit_findings.json"
    output_file.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    print(f"\nWrote {output_file}")

    print(f"\ndefect_class: {findings['defect_class']}")
    print(f"requires_retraining: {findings['requires_retraining']}")
    print(f"retraining_rationale: {findings['retraining_rationale']}")
    print(f"\n{len(findings['findings'])} findings:")
    for item in findings["findings"]:
        print(f"  [{item['severity']:<6}] {item['feature_name']}: {item['problem']}")
        print(f"           impact: {item['impact_on_risk_score']}")

    failures = verify_findings(findings)
    if failures:
        print("\nVERIFICATION FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)

    print("\nVERIFICATION PASSED: every hardcoded feature is named and the "
          "audit correctly does not recommend retraining.")


if __name__ == "__main__":
    main()
