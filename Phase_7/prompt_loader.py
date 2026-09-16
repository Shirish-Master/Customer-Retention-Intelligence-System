"""Phase 7 - versioned prompt template loading.

Task 5:
Save each template as a versioned file under prompts/, and write a small
load_template(name, **kwargs) function that loads and fills them - never inline
template text directly in a script

Templates live in Phase_7/prompts/<name>.v<N>.md and use $placeholder syntax
(string.Template, not str.format) so JSON braces inside a template do not have
to be escaped.

load_template() resolves the highest version unless one is pinned, validates
that the supplied kwargs exactly match the template's placeholders, and runs
the secret scan on the filled result before handing it back.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from string import Template

from claude_guardrails import GuardrailError, assert_no_secrets, validate_args

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

_TEMPLATE_FILE = re.compile(r"^(?P<name>[a-z0-9_]+)\.v(?P<version>\d+)\.md$")


def available_templates() -> dict[str, list[int]]:
    """Map template name -> sorted list of available versions."""
    found: dict[str, list[int]] = {}
    for path in PROMPTS_DIR.glob("*.md"):
        match = _TEMPLATE_FILE.match(path.name)
        if match:
            found.setdefault(match["name"], []).append(int(match["version"]))
    return {name: sorted(versions) for name, versions in found.items()}


def resolve_path(name: str, version: int | None = None) -> Path:
    """Locate a template file, defaulting to the highest version present."""
    versions = available_templates().get(name)
    if not versions:
        known = ", ".join(sorted(available_templates())) or "none"
        raise GuardrailError(f"No template named {name!r}. Available: {known}")

    if version is None:
        version = versions[-1]
    elif version not in versions:
        raise GuardrailError(
            f"Template {name!r} has no version {version}. Available: {versions}"
        )

    return PROMPTS_DIR / f"{name}.v{version}.md"


@lru_cache(maxsize=32)
def _read_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def required_placeholders(name: str, version: int | None = None) -> set[str]:
    """The $placeholders a template expects."""
    template = Template(_read_template(resolve_path(name, version)))
    return set(template.get_identifiers())


def load_template(name: str, version: int | None = None, **kwargs) -> str:
    """Load a versioned template and fill it.

    Every kwarg goes through validate_args() first, so an argument can never
    smuggle a secret or an unexpected type into the prompt. Supplying an
    unknown placeholder, or omitting a required one, is an error rather than a
    silently half-filled prompt.
    """
    path = resolve_path(name, version)
    raw = _read_template(path)
    template = Template(raw)

    expected = set(template.get_identifiers())
    supplied = set(kwargs)

    if missing := expected - supplied:
        raise GuardrailError(
            f"Template {path.name} needs placeholders {sorted(missing)}"
        )
    if unexpected := supplied - expected:
        raise GuardrailError(
            f"Template {path.name} has no placeholders {sorted(unexpected)}"
        )

    cleaned = validate_args(**kwargs)
    filled = template.substitute(cleaned)

    # Belt and braces: the template body itself could contain a pasted secret.
    assert_no_secrets(filled, where=f"filled template {path.name}")
    return filled
