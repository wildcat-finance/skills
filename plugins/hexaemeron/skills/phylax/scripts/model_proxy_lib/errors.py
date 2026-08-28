"""Credential-free refusal values for the model proxy policy compiler."""

from __future__ import annotations

from dataclasses import dataclass


DIAGNOSTIC_SCHEMA = "model-proxy-diagnostic/v1"


@dataclass(frozen=True, slots=True)
class PolicyError(ValueError):
    """A bounded refusal that never carries input bytes or values."""

    code: str
    field: str

    def __str__(self) -> str:
        return f"{self.code}: {self.field}"

    def diagnostic(self) -> dict[str, str]:
        return {
            "schema": DIAGNOSTIC_SCHEMA,
            "outcome": "refused",
            "code": self.code,
            "field": self.field,
        }


def refuse(code: str, field: str) -> None:
    """Raise one value-free compiler refusal."""

    raise PolicyError(code, field)
