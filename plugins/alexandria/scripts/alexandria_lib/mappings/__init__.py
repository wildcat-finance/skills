"""Registered Tabularium mappings shipped by Alexandria."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import AlexandriaError
from . import aave_v4, clearpool


@dataclass(frozen=True)
class MappingResult:
    events: tuple
    observations: tuple
    declaration: dict


REGISTRY = {
    "aave-v4": aave_v4.map_capture,
    "clearpool": clearpool.map_capture,
}


def map_capture(capture, data, source_release_id):
    mapper = REGISTRY.get(capture["venue"])
    if mapper is None:
        raise AlexandriaError(
            f"capture {capture['id']} venue {capture['venue']} has no registered mapping"
        )
    events, observations, declaration = mapper(capture, data, source_release_id)
    return MappingResult(tuple(events), tuple(observations), declaration)
