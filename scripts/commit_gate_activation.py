"""One activation policy for the checkout suite and checked-runner preflight."""

from pathlib import Path
from typing import Mapping

SNAPSHOT_ENV = "WILDCAT_CHECK_SNAPSHOT_ROOT"
ACTIVATION_COMMAND = "git config core.hooksPath .githooks"
DECLARED_OFF = frozenset({"0", "false", "no", "off"})


def nobody_commits_here(root: Path, environment: Mapping[str, str]) -> str | None:
    """Name a hosted execution or the exact disposable snapshot being checked."""
    hosted = environment.get("GITHUB_ACTIONS", "").strip()
    if hosted and hosted.lower() not in DECLARED_OFF:
        return "GITHUB_ACTIONS"
    snapshot = environment.get(SNAPSHOT_ENV, "")
    if snapshot and Path(snapshot).is_absolute():
        try:
            if Path(snapshot).resolve() == root.resolve():
                return SNAPSHOT_ENV
        except (OSError, RuntimeError):
            pass
    return None


def activation_complaint(root: Path, configured: str | None) -> str | None:
    """What is wrong with this `core.hooksPath`, or None when nothing is.

    Separate from the case that reads the checkout, so the wording can be
    driven both ways without a fixture and without making a real checkout
    wrong to do it. Git runs a hook from the top of the working tree, so a
    relative value resolves against the repository root rather than against
    whatever directory the suite was started from.
    """
    remedy = (
        f"Turn it on with `{ACTIVATION_COMMAND}`, run from the top of this "
        "working tree. pre-commit and greenlight are tracked in "
        ".githooks/, README.md says what each one does, and "
        "FIAT_SKIP_PRECOMMIT=1 admits a commit you mean to make without a "
        "recorded green."
    )
    if configured is None or not configured.strip():
        return (
            "the commit gate is not activated in this checkout: core.hooksPath "
            "is unset, so git runs no tracked hook and a commit of a tree no "
            f"suite has passed on is admitted silently. {remedy}"
        )
    value = configured.strip()
    resolved = Path(value)
    if not resolved.is_absolute():
        resolved = root / resolved
    try:
        elsewhere = resolved.resolve() != (root / ".githooks").resolve()
    except OSError:
        elsewhere = True
    if not elsewhere:
        return None
    return (
        "the commit gate is not activated in this checkout: core.hooksPath is "
        f"{value!r}, which resolves to {resolved} rather than to the tracked "
        f"{root / ".githooks"}, so git runs some other directory's hooks. {remedy}"
    )
