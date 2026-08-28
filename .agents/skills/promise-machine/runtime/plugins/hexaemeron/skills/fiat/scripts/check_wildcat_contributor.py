#!/usr/bin/env python3
"""Fail-silent Wildcat Labs contributor check for authenticated GitHub users."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


ORG = "wildcat-finance"
EMAIL_SUFFIX = "@wildcat.finance"
TIMEOUT_SECONDS = 15


def _gh(*args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["gh", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _json_result(*args: str) -> Any | None:
    result = _gh(*args)
    if result is None or result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError):
        return None


def _wildcat_email(value: object) -> bool:
    return isinstance(value, str) and value.casefold().endswith(EMAIL_SUFFIX)


def authenticated_github_user_is_contributor() -> bool:
    """Return eligibility without emitting identity or failure details."""

    auth = _gh("auth", "status", "--hostname", "github.com", "--active")
    if auth is None or auth.returncode != 0:
        return False

    profile = _json_result("api", "user")
    if not isinstance(profile, dict):
        return False

    membership = _json_result("api", f"user/memberships/orgs/{ORG}")
    if isinstance(membership, dict) and membership.get("state") == "active":
        return True

    if _wildcat_email(profile.get("email")):
        return True

    emails = _json_result("api", "user/emails")
    if isinstance(emails, list):
        return any(
            isinstance(item, dict)
            and item.get("verified") is True
            and _wildcat_email(item.get("email"))
            for item in emails
        )

    return False


def main() -> int:
    # Exit status is the whole interface. Never print identity evidence or errors.
    return 0 if authenticated_github_user_is_contributor() else 1


if __name__ == "__main__":
    sys.exit(main())
