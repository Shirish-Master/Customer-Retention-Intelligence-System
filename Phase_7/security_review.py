"""Phase 7 - human-invoked security review. NOT for automation.

Task 6:
Keep the security-review template isolated in its own module that only a human
ever calls directly - never wire it into anything that runs automatically

This module is deliberately awkward to call from code. It refuses to run unless
it is the program entry point, stdin is a real terminal, no CI environment
variable is set, and a human types a confirmation. Importing it and calling
run_security_review() from a script or a hook will raise.

Why the isolation: a security review produces a list of exploitable weaknesses
in a system holding real customer records. Wired into CI it would write that
list into build logs on every push, where it is retained, widely readable, and
outside the access controls on the code itself. It also invites the failure
mode where nobody reads the output and a green check mark is mistaken for a
clean review.

    python Phase_7/security_review.py --diff-from HEAD~1
    python Phase_7/security_review.py --diff-file changes.diff
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from claude_guardrails import GuardrailError, call_claude
from prompt_loader import load_template

PROJECT_DIR = Path(__file__).resolve().parents[1]

# Any of these being set means we are not on a human's terminal.
CI_MARKERS = (
    "CI",
    "CONTINUOUS_INTEGRATION",
    "GITHUB_ACTIONS",
    "GITLAB_CI",
    "JENKINS_URL",
    "BUILDKITE",
    "TF_BUILD",
)

CONFIRMATION = "review"


class NotHumanInvokedError(RuntimeError):
    """Raised when this module is reached from anything but a person."""


def _assert_human_invocation() -> None:
    """Four independent checks. All must pass."""
    if __name__ != "__main__":
        raise NotHumanInvokedError(
            "security_review is a human-invoked tool. Run it directly:\n"
            "  python Phase_7/security_review.py --diff-from HEAD~1\n"
            "Do not import it or call it from a script, hook or scheduler."
        )

    for marker in CI_MARKERS:
        if os.getenv(marker):
            raise NotHumanInvokedError(
                f"{marker} is set, so this looks like an automated run. "
                "Security review findings must not be written into build logs."
            )

    if not sys.stdin.isatty():
        raise NotHumanInvokedError(
            "stdin is not a terminal. This tool only runs interactively."
        )

    answer = input(
        "\nThis sends a code diff to the Claude API and returns a list of "
        "exploitable weaknesses\nin a system holding real customer data. "
        f"A person must read the output.\n\nType '{CONFIRMATION}' to continue: "
    )
    if answer.strip().lower() != CONFIRMATION:
        raise NotHumanInvokedError("Not confirmed; nothing was sent.")


def collect_diff(diff_from: str | None, diff_file: Path | None) -> str:
    if diff_file:
        diff = diff_file.read_text(encoding="utf-8")
    elif diff_from:
        diff = subprocess.run(
            ["git", "diff", diff_from],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    else:
        diff = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    if not diff.strip():
        raise GuardrailError("Empty diff - nothing to review.")
    return diff


def run_security_review(change_description: str, diff: str) -> str:
    """Send the review. Reachable only after _assert_human_invocation()."""
    load_dotenv(PROJECT_DIR / ".env")

    prompt = load_template(
        "security_review",
        change_description=change_description,
        diff=diff,
    )

    client = anthropic.Anthropic()
    response = call_claude(
        client,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )

    return "\n".join(
        block.text for block in response.content if block.type == "text"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diff-from", help="git ref to diff against, e.g. HEAD~1")
    parser.add_argument("--diff-file", type=Path, help="read the diff from a file")
    parser.add_argument(
        "--describe",
        default="Uncategorised change to the churn project",
        help="one line describing what the change does",
    )
    args = parser.parse_args()

    _assert_human_invocation()

    diff = collect_diff(args.diff_from, args.diff_file)
    print(f"\nReviewing {len(diff.splitlines())} diff lines...\n")
    print(run_security_review(args.describe, diff))
    print("\n--- Read the findings above. This tool does not gate anything. ---")


if __name__ == "__main__":
    main()
