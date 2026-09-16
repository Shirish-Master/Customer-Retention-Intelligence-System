"""Phase 7 - the one place every Claude call passes through.

Task 7:
Build a short security checklist into code: never let a prompt contain secrets
from .env, validate every argument before it's used, forward only the specific
fields a task needs, and cap token usage and history length in one shared place

The four checklist items map to:
  1. never let a prompt contain secrets from .env  -> assert_no_secrets()
  2. validate every argument before it's used      -> validate_args()
  3. forward only the fields a task needs          -> project_fields()
  4. cap tokens and history in one shared place    -> Limits + call_claude()

Nothing in this project should call client.messages.create() directly. Go
through call_claude() so all four apply on every request.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import anthropic
from dotenv import dotenv_values

from project_context import SYSTEM_PROMPT

PROJECT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_DIR / ".env"


class SecretLeakError(RuntimeError):
    """Raised when outbound text contains a value sourced from .env."""


class GuardrailError(ValueError):
    """Raised when an argument fails validation before use."""


# --- 4. Caps, in one shared place -------------------------------------------


@dataclass(frozen=True)
class Limits:
    """Every cap in the project. Change here, not at a call site."""

    model: str = "claude-opus-5"
    # What a call gets if it asks for nothing in particular.
    default_max_tokens: int = 4096
    # The most any single call may ask for, however loudly it asks. A caller
    # can raise its own ceiling up to this and no further.
    max_tokens_ceiling: int = 16_000
    # How many prior turns may be replayed. Long histories are the main way
    # customer data leaks from one task into an unrelated one.
    max_history_messages: int = 10
    # Hard ceiling on a single outbound prompt, characters not tokens - cheap
    # to enforce and catches a runaway file paste before it is billed.
    max_prompt_chars: int = 120_000
    # Refuse a request that would obviously blow the context window.
    max_total_chars: int = 400_000


LIMITS = Limits()


# --- 1. Secret leakage guard -------------------------------------------------

# Values shorter than this are ignored when scanning: a secret of "1" or "on"
# would match almost any prompt and make the guard useless noise.
MIN_SECRET_LENGTH = 8

# Shapes that are secrets regardless of whether they are in this .env file.
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("anthropic api key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}")),
    ("aws access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    # The hardcoded DB credentials used across this project.
    ("database url with password", re.compile(r"mysql\+pymysql://[^\s:]+:[^\s@]+@")),
)


def _env_secret_values() -> dict[str, str]:
    """Values from .env that must never appear in outbound text.

    Read from the file rather than os.environ so an unrelated environment
    variable that happens to share a value does not widen the net.
    """
    if not ENV_FILE.exists():
        return {}
    return {
        key: value
        for key, value in dotenv_values(ENV_FILE).items()
        if value and len(value) >= MIN_SECRET_LENGTH
    }


def assert_no_secrets(text: str, *, where: str = "prompt") -> None:
    """Raise SecretLeakError if `text` contains anything secret.

    Checks .env values first, then generic secret shapes so a credential that
    was pasted into source rather than .env is still caught.
    """
    for key, value in _env_secret_values().items():
        if value in text:
            raise SecretLeakError(
                f"{where} contains the value of {key} from .env. "
                "Secrets must never be sent to the API. "
                f"(matched {len(value)} characters; value not shown)"
            )

    for label, pattern in SECRET_PATTERNS:
        match = pattern.search(text)
        if match:
            raise SecretLeakError(
                f"{where} contains something shaped like a {label} at offset "
                f"{match.start()}. Remove it before sending. "
                "(value not shown)"
            )


# --- 2. Argument validation --------------------------------------------------

_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.\-]{1,64}$")


def validate_args(**kwargs: Any) -> dict[str, Any]:
    """Validate arguments before they are used to build a prompt.

    Rejects None, empty strings, and anything that is not a str/int/float/bool.
    Template variables become prompt text, so an unvalidated one is an
    injection vector, not just a typo.
    """
    cleaned: dict[str, Any] = {}

    for name, value in kwargs.items():
        if not _IDENTIFIER.match(name):
            raise GuardrailError(f"Invalid argument name: {name!r}")

        if value is None:
            raise GuardrailError(f"Argument {name!r} is None; supply a value")

        if isinstance(value, bool) or isinstance(value, (int, float)):
            cleaned[name] = value
            continue

        if not isinstance(value, str):
            raise GuardrailError(
                f"Argument {name!r} has unsupported type {type(value).__name__}; "
                "pass a str, int, float or bool"
            )

        stripped = value.strip()
        if not stripped:
            raise GuardrailError(f"Argument {name!r} is empty")

        if len(stripped) > LIMITS.max_prompt_chars:
            raise GuardrailError(
                f"Argument {name!r} is {len(stripped):,} chars, over the "
                f"{LIMITS.max_prompt_chars:,} cap"
            )

        # An argument must never smuggle a secret into the filled template.
        assert_no_secrets(stripped, where=f"argument {name!r}")
        cleaned[name] = stripped

    return cleaned


# --- 3. Field projection -----------------------------------------------------


def project_fields(
    record: Mapping[str, Any],
    fields: Sequence[str],
    *,
    label: str = "record",
) -> dict[str, Any]:
    """Return ONLY `fields` from `record`.

    Use this before putting any database row into a prompt. Passing a whole
    row means every column the query happened to select is sent to a third
    party, including ones the task has no use for.
    """
    missing = [field for field in fields if field not in record]
    if missing:
        raise GuardrailError(f"{label} is missing required fields: {missing}")

    projected = {field: record[field] for field in fields}
    assert_no_secrets(repr(projected), where=f"{label} projection")
    return projected


# Fields each task is allowed to send. Deliberately narrow.
ALLOWED_FIELDS: dict[str, tuple[str, ...]] = {
    # Never includes customer_id - a churn explanation does not need identity.
    "explain_risk": (
        "tenure",
        "monthly_charges",
        "contract_type",
        "internet_service",
        "service_count",
        "risk_score",
    ),
    "profile_dataset": ("column_name", "dtype", "null_count", "distinct_count"),
}


# --- 4. The single chokepoint ------------------------------------------------


def _trim_history(messages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Keep only the most recent turns, and keep the window starting on a user
    turn so the API never sees a history opening with an assistant message."""
    trimmed = list(messages[-LIMITS.max_history_messages :])
    while trimmed and trimmed[0].get("role") != "user":
        trimmed.pop(0)
    if not trimmed:
        raise GuardrailError("No user message left after trimming history")
    return [dict(message) for message in trimmed]


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, Iterable):
        return " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, Mapping)
        )
    return str(content)


def call_claude(
    client: anthropic.Anthropic,
    messages: Sequence[Mapping[str, Any]],
    *,
    system_extra: str | None = None,
    tools: Sequence[Mapping[str, Any]] | None = None,
    tool_choice: Mapping[str, Any] | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
) -> anthropic.types.Message:
    """The only place this project should call the Messages API.

    Prepends the project memory to the system prompt, scans everything
    outbound for secrets, trims history, and applies the shared caps.
    """
    system = SYSTEM_PROMPT
    if system_extra:
        system = f"{system}\n\n{system_extra.strip()}"

    trimmed = _trim_history(messages)

    outbound = "\n".join(
        [system, *(_content_text(message.get("content")) for message in trimmed)]
    )
    if tools:
        outbound += "\n" + repr(tools)

    # 1. Secrets never leave, whichever part of the request they got into.
    assert_no_secrets(outbound, where="outbound request")

    # 4. Caps.
    if len(outbound) > LIMITS.max_total_chars:
        raise GuardrailError(
            f"Request is {len(outbound):,} chars, over the "
            f"{LIMITS.max_total_chars:,} cap. Send less context."
        )

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise GuardrailError(
            "ANTHROPIC_API_KEY is not set. Add it to .env in the project root."
        )

    request: dict[str, Any] = {
        "model": model or LIMITS.model,
        "max_tokens": min(
            max_tokens or LIMITS.default_max_tokens,
            LIMITS.max_tokens_ceiling,
        ),
        "system": system,
        "messages": trimmed,
    }
    if tools:
        request["tools"] = list(tools)
    if tool_choice:
        request["tool_choice"] = dict(tool_choice)

    return client.messages.create(**request)
