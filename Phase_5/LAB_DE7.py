# 216. Define 6 quality checks as functions: check_null_rate(df, col, threshold), check_value_range(df, col, min, max), check_allowed_values(df, col, allowed_set), check_row_count(df, expected_min), check_no_duplicates(df, key_col), check_churn_distribution(df)

import json
import logging
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_FILE = PROJECT_DIR / "Phase_1" / "customer_features.csv"
REPORT_FILE = PROJECT_DIR / "Phase_5" / "quality_report.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_null_rate(df, col, threshold):
    null_rate = float(df[col].isna().mean() * 100)
    return {
        "check_name": f"null_rate_{col}",
        "passed": null_rate <= threshold,
        "value_found": null_rate,
        "threshold": threshold,
    }


# 217. Run null rate check: monthly_charges and tenure must have 0% nulls


def check_value_range(df, col, min_value, max_value=None, inclusive_min=True):
    values = pd.to_numeric(df[col], errors="coerce")
    lower_bound_failure = values < min_value if inclusive_min else values <= min_value
    invalid = values.isna() | lower_bound_failure
    if max_value is not None:
        invalid = invalid | (values > max_value)

    return {
        "check_name": f"value_range_{col}",
        "passed": not bool(invalid.any()),
        "value_found": {
            "minimum": float(values.min()),
            "maximum": float(values.max()),
            "invalid_count": int(invalid.sum()),
        },
        "threshold": {
            "minimum": min_value,
            "minimum_inclusive": inclusive_min,
            "maximum_inclusive": max_value,
        },
    }


# 218. Run value range check: tenure must be 0–100; monthly_charges must be > 0


def check_allowed_values(df, col, allowed_set):
    found_values = set(df[col].dropna().unique())
    invalid_values = found_values - set(allowed_set)
    return {
        "check_name": f"allowed_values_{col}",
        "passed": len(invalid_values) == 0,
        "value_found": sorted(str(value) for value in found_values),
        "threshold": sorted(str(value) for value in allowed_set),
        "invalid_values": sorted(str(value) for value in invalid_values),
    }


# 219. Run allowed values check: contract must be one of {Month-to-month, One year, Two year}


def check_row_count(df, expected_min):
    row_count = len(df)
    return {
        "check_name": "row_count",
        "passed": row_count >= expected_min,
        "value_found": row_count,
        "threshold": expected_min,
    }


# 220. Run row count check: must have at least 7000 rows (catches truncated files)


def check_no_duplicates(df, key_col):
    duplicate_count = int(df[key_col].duplicated().sum())
    return {
        "check_name": f"no_duplicates_{key_col}",
        "passed": duplicate_count == 0,
        "value_found": duplicate_count,
        "threshold": 0,
    }


# 221. Run duplicate check: no duplicate customer_id values


def check_churn_distribution(df):
    distribution = {
        str(key): int(value)
        for key, value in df["churn"].value_counts(dropna=False).to_dict().items()
    }
    values = set(df["churn"].dropna().unique())
    passed = values == {0, 1}
    return {
        "check_name": "churn_distribution",
        "passed": passed,
        "value_found": distribution,
        "threshold": "both churn values 0 and 1 must be present",
    }


# 222. Define the churn distribution check and classify it as a WARNING check


def run_quality_checks(df):
    checks = [
        (check_null_rate(df, "monthly_charges", 0), "CRITICAL"),
        (check_null_rate(df, "tenure", 0), "CRITICAL"),
        (check_value_range(df, "tenure", 0, 100), "CRITICAL"),
        (check_value_range(df, "monthly_charges", 0, inclusive_min=False), "CRITICAL"),
        (
            check_allowed_values(
                df,
                "contract",
                {"Month-to-month", "One year", "Two year"},
            ),
            "CRITICAL",
        ),
        (check_row_count(df, 7000), "CRITICAL"),
        (check_no_duplicates(df, "customer_id"), "CRITICAL"),
        (check_churn_distribution(df), "WARNING"),
    ]

    for result, severity in checks:
        result["severity"] = severity
    return checks


# 223. Produce a quality_report.json with: check name, PASS/FAIL, value found, threshold


def write_quality_report(checks):
    report = [
        {
            "check_name": result["check_name"],
            "status": "PASS" if result["passed"] else "FAIL",
            "value_found": result["value_found"],
            "threshold": result["threshold"],
            "severity": result["severity"],
        }
        for result, _ in checks
    ]
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Quality report written to {REPORT_FILE}")
    return report


# 224. If any CRITICAL check fails: raise an exception to stop the pipeline


def stop_on_critical_failures(checks):
    failures = [
        result["check_name"]
        for result, severity in checks
        if severity == "CRITICAL" and not result["passed"]
    ]
    if failures:
        raise RuntimeError(f"Critical quality checks failed: {', '.join(failures)}")


# 225. If WARNING checks fail: log warning but continue


def log_warning_failures(checks):
    for result, severity in checks:
        if severity == "WARNING" and not result["passed"]:
            logger.warning(
                "%s failed: found=%s threshold=%s",
                result["check_name"],
                result["value_found"],
                result["threshold"],
            )


# 226. Print every quality check as PASS or FAIL with its observed value and threshold


def print_quality_results(checks):
    for result, severity in checks:
        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"{status} [{severity}] {result['check_name']}: "
            f"found={result['value_found']} threshold={result['threshold']}"
        )


# 227. Run all quality checks, write the report, stop on critical failures, and continue after warnings


def main():
    quality_df = pd.read_csv(SOURCE_FILE)
    checks = run_quality_checks(quality_df)
    report = write_quality_report(checks)
    print_quality_results(checks)
    log_warning_failures(checks)
    stop_on_critical_failures(checks)
    return report


if __name__ == "__main__":
    main()
