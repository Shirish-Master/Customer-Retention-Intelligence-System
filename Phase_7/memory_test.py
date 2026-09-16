"""Phase 7 - prove the project memory is actually doing work.

Task 3:
Test the memory: ask a question that depends on a specific fact, confirm the
answer is grounded and correct, then remove the fact and observe the answer
degrade, then restore it

    python Phase_7/memory_test.py

The probe question depends on a fact that cannot be inferred from general
knowledge of telco churn datasets, so a correct answer can only have come from
the memory block:

    high_charge_flag is computed with AVG(monthly_charges) in
    Phase_2/LAB_SQL5.sql but with the MEDIAN (70.35) in Phase_6. The two
    disagree. That inconsistency is recorded in the "data_quirks" fact.

Run order: WITH the fact -> WITHOUT it -> WITH it again. The middle run should
either decline to answer or answer generically. If the middle run still answers
correctly, the probe is leaking the answer and needs rewording.
"""

from __future__ import annotations

import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from claude_guardrails import call_claude
from project_context import FACTS, build_system_prompt

PROJECT_DIR = Path(__file__).resolve().parents[1]

# The fact to remove in the middle run.
PROBE_FACT = "data_quirks"

# Deliberately does not mention AVG, median, or that a discrepancy exists.
PROBE_QUESTION = (
    "In this project, how is high_charge_flag calculated? Give the exact "
    "threshold each part of the codebase compares monthly_charges against, "
    "and state whether every part of the codebase agrees. Answer in under 80 "
    "words. If you do not know, say so rather than describing how such a flag "
    "is usually built."
)

# Strings that indicate the answer is genuinely grounded in the memory.
GROUNDED_MARKERS = ("avg", "mean", "median", "70.35")


def ask(client: anthropic.Anthropic, omit: set[str] | None) -> str:
    """Ask the probe question against a memory with or without PROBE_FACT."""
    system = build_system_prompt(omit=omit)

    # call_claude() always prepends the full memory, so this test talks to the
    # API directly - it is the one place that needs a modified memory block.
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": PROBE_QUESTION}],
    )
    return "\n".join(
        block.text for block in response.content if block.type == "text"
    ).strip()


def score(answer: str) -> tuple[int, list[str]]:
    """How many grounding markers the answer contains."""
    lowered = answer.lower()
    hits = [marker for marker in GROUNDED_MARKERS if marker in lowered]
    return len(hits), hits


def main() -> None:
    load_dotenv(PROJECT_DIR / ".env")
    client = anthropic.Anthropic()

    print(f"Probe question:\n  {PROBE_QUESTION}\n")
    print(f"Fact under test: {PROBE_FACT!r}")
    print("=" * 72)

    # 1. WITH the fact - expect a grounded, specific answer.
    with_answer = ask(client, omit=None)
    with_score, with_hits = score(with_answer)
    print("\n[1] WITH the fact present")
    print("-" * 72)
    print(with_answer)
    print(f"\n  grounding markers hit: {with_score}/{len(GROUNDED_MARKERS)} {with_hits}")

    # 2. WITHOUT the fact - expect degradation.
    without_answer = ask(client, omit={PROBE_FACT})
    without_score, without_hits = score(without_answer)
    print(f"\n[2] WITHOUT the {PROBE_FACT!r} fact")
    print("-" * 72)
    print(without_answer)
    print(
        f"\n  grounding markers hit: {without_score}/{len(GROUNDED_MARKERS)} "
        f"{without_hits}"
    )

    # 3. RESTORED - expect the quality to come back.
    restored_answer = ask(client, omit=None)
    restored_score, restored_hits = score(restored_answer)
    print("\n[3] RESTORED")
    print("-" * 72)
    print(restored_answer)
    print(
        f"\n  grounding markers hit: {restored_score}/{len(GROUNDED_MARKERS)} "
        f"{restored_hits}"
    )

    print("\n" + "=" * 72)
    print(
        f"scores: with={with_score}  without={without_score}  "
        f"restored={restored_score}"
    )

    degraded = without_score < with_score
    recovered = restored_score >= with_score

    if degraded and recovered:
        print(
            "PASS - the answer degraded when the fact was removed and "
            "recovered when it was restored. The memory is load-bearing."
        )
        return

    if not degraded:
        print(
            "FAIL - removing the fact changed nothing. Either the probe "
            "question leaks the answer, or the model is answering from "
            "general knowledge. Reword PROBE_QUESTION to depend on something "
            "only this codebase could tell you."
        )
    if not recovered:
        print(
            "FAIL - the answer did not recover after restoring the fact. "
            "Run again; if it persists the probe is unstable."
        )
    sys.exit(1)


if __name__ == "__main__":
    main()


# Record the observed result here after running:
#
# [1] WITH:      grounding markers hit: _/4
# [2] WITHOUT:   grounding markers hit: _/4
# [3] RESTORED:  grounding markers hit: _/4
# Verdict:
