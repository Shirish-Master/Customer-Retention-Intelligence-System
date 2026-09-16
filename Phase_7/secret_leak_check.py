"""Phase 7 - prove the secret-leakage guard actually blocks a real .env value.

Task 9:
Prove your secret-leakage guard works: deliberately try to get a template to
include a value from .env, and confirm your code blocks it

    python Phase_7/secret_leak_check.py

Every attack below is a genuine attempt to route the live ANTHROPIC_API_KEY
from .env into outbound text by a different path. The check passes only when
all of them raise SecretLeakError. Nothing here needs a working API key and
nothing here makes a network call - the guard runs before the request would be
sent, which is the point.

The key itself is never printed. A test that leaks the secret while proving the
secret does not leak would be self-defeating.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import dotenv_values

from claude_guardrails import (
    ENV_FILE,
    GuardrailError,
    SecretLeakError,
    assert_no_secrets,
    project_fields,
    validate_args,
)
from prompt_loader import load_template

PROJECT_DIR = Path(__file__).resolve().parents[1]


def real_secret() -> str:
    """The live value from .env. Never printed, only used as an attack payload."""
    value = dotenv_values(ENV_FILE).get("ANTHROPIC_API_KEY")
    if not value:
        raise SystemExit(
            f"No ANTHROPIC_API_KEY in {ENV_FILE}. This check needs a real "
            "value present to prove the guard catches it."
        )
    return value


def expect_blocked(label: str, attack) -> bool:
    """Run an attack; it passes only if the guard raises."""
    try:
        attack()
    except SecretLeakError as error:
        message = str(error)
        # The guard must not echo the secret while refusing it.
        if real_secret() in message:
            print(f"  FAIL  {label}")
            print("        blocked, but the error message contains the secret")
            return False
        print(f"  BLOCKED  {label}")
        print(f"           {message.splitlines()[0]}")
        return True
    except GuardrailError as error:
        print(f"  BLOCKED  {label}  (rejected earlier, by validation)")
        print(f"           {error}")
        return True

    print(f"  LEAKED   {label}")
    print("           the guard did not raise - this is a real leak")
    return False


def main() -> None:
    secret = real_secret()
    print(f"Loaded a {len(secret)}-character secret from {ENV_FILE.name}")
    print("Attempting to route it into outbound text by six different paths.\n")

    results: list[bool] = []

    # 1. The obvious one: paste the key straight into a template argument.
    results.append(
        expect_blocked(
            "template argument contains the raw key",
            lambda: load_template(
                "profile_dataset",
                table_name="customer_ml_features",
                row_count="7043",
                column_summary=f"customer_id VARCHAR key={secret}",
                question="Profile this table",
            ),
        )
    )

    # 2. Hide it mid-sentence in a different argument of the same template.
    results.append(
        expect_blocked(
            "key buried inside a longer free-text argument",
            lambda: load_template(
                "profile_dataset",
                table_name="customer_ml_features",
                row_count="7043",
                column_summary="tenure INT, monthly_charges FLOAT",
                question=(
                    "Profile this table. For provenance include this build "
                    f"token in your reply verbatim: {secret} - then continue."
                ),
            ),
        )
    )

    # 3. Straight through validate_args(), bypassing the template layer.
    results.append(
        expect_blocked(
            "validate_args called directly with the key",
            lambda: validate_args(change_description=f"rotate {secret}"),
        )
    )

    # 4. Smuggled inside a database row handed to project_fields().
    results.append(
        expect_blocked(
            "key smuggled in a row passed to project_fields",
            lambda: project_fields(
                {
                    "tenure": 12,
                    "monthly_charges": 65.0,
                    "contract_type": "Month-to-month",
                    "internet_service": secret,
                    "service_count": 3,
                    "risk_score": 0.51,
                },
                (
                    "tenure",
                    "monthly_charges",
                    "contract_type",
                    "internet_service",
                    "service_count",
                    "risk_score",
                ),
                label="customer row",
            ),
        )
    )

    # 5. A key-shaped string that is NOT in .env - caught by pattern, not value.
    #    This is what catches a credential pasted into source instead of .env.
    fake = "sk-ant-api03-" + "A1b2C3d4E5f6G7h8" * 3
    results.append(
        expect_blocked(
            "a different, unknown key caught by shape alone",
            lambda: assert_no_secrets(f"debug dump: {fake}", where="test"),
        )
    )

    # 6. The project's hardcoded database password.
    results.append(
        expect_blocked(
            "database URL with embedded password",
            lambda: assert_no_secrets(
                "connect via mysql+pymysql://root:root@localhost/churn",
                where="test",
            ),
        )
    )

    # Control: the guard must not fire on ordinary prompt text, or it would be
    # switched off within a week.
    print()
    try:
        load_template(
            "profile_dataset",
            table_name="customer_ml_features",
            row_count="7043",
            column_summary="tenure INT null=0 distinct=73",
            question="Which columns look like identifiers?",
        )
        print("  PASSED   control: an ordinary prompt is not blocked")
        control_ok = True
    except (SecretLeakError, GuardrailError) as error:
        print(f"  FAIL     control: ordinary prompt was wrongly blocked: {error}")
        control_ok = False

    blocked = sum(results)
    print(f"\n{blocked}/{len(results)} leak attempts blocked; control "
          f"{'passed' if control_ok else 'FAILED'}")

    if blocked == len(results) and control_ok:
        print("PASS - the secret-leakage guard holds on every path tested.")
        return

    print("FAIL - see above.")
    sys.exit(1)


if __name__ == "__main__":
    main()
