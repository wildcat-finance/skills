"""Content-free refusals for the GitHub issue publication boundary."""

from __future__ import annotations

from dataclasses import dataclass


DIAGNOSTIC_SCHEMA = "github-issue-publisher-diagnostic/v1"


@dataclass(frozen=True)
class PublisherError(ValueError):
    """A refusal whose public form carries no request-controlled bytes."""

    code: str
    field: str
    mint_attempts: int = 0
    post_attempts: int = 0

    def __str__(self) -> str:
        return f"{self.code}:{self.field}"

    def diagnostic(self) -> dict[str, str | int]:
        return {
            "schema": DIAGNOSTIC_SCHEMA,
            "outcome": "refused",
            "code": self.code,
            "field": self.field,
            "mint_attempts": self.mint_attempts,
            "post_attempts": self.post_attempts,
        }


def refuse(code: str, field: str) -> None:
    raise PublisherError(code, field)
