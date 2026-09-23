"""The Aave V3 Ethereum main-market venue: pinned registry and plan scope.

`validate_registry` is the unedited function `aave_registry.py` defines,
re-exported rather than wrapped, so the registry's pinned digest,
`AAVE_V3_REGISTRY_SHA256`, and the pinned canonical bytes of the merged
`aave-v3` row, `ROW_PINS`, are each written in one module only. Both are
re-exported here by name. No plan field supplies either.

`validate_plan_scope` refuses a plan whose chain is not `eip155:1`, whose
registry is not the pinned one, which declares a subject the registry does
not list, or which does not declare the main market's Pool proxy and
AddressesProvider. The market addresses are the constant
`aave_registry.MARKET`, which `validate_registry` also holds the registry to.

What this module does not yet do: it derives no epochs. `EPOCH_MODEL` names
the per-subject model the design selects, EIP-1967 epochs for the 172 proxy
subjects and one immutable epoch for the other 184, keyed by registry role,
and `opening_phase` checks the plan's scope and then refuses by name rather
than planning any opening read. A plan naming this venue therefore cannot
yet be collected, reconciled or built.

`gaps` names the one subject #1591 lists both as a subject and as periphery,
so the release says so rather than resolving it silently. `evidence_gaps`
adds nothing yet.
"""

from __future__ import annotations

from ..aave_registry import (  # noqa: F401 -- re-exported pins, see the docstring
    AAVE_V3_REGISTRY_SHA256,
    MARKET,
    ROW_PINS,
    subject_entries,
    validate_registry,
)
from ..errors import AlexandriaError

VENUE = "aave-v3"
EPOCH_MODEL = "aave-v3-role-keyed"
CHAIN = "eip155:1"


def validate_plan_scope(plan, registry) -> list:
    """The plan's declared subjects, after its chain, registry and market are checked."""
    if plan.get("chain") != CHAIN:
        raise AlexandriaError(
            f"the {VENUE} venue captures the Ethereum main market on {CHAIN}; the plan names "
            f"chain {str(plan.get('chain'))[:64]!r}"
        )
    if "subjects" not in plan:
        raise AlexandriaError(
            f"the {VENUE} venue captures a declared subject set; a single-proxy plan names none"
        )
    if registry is None:
        raise AlexandriaError(
            f"the {VENUE} venue checks every subject against its pinned registry, and none was supplied"
        )
    validate_registry(registry)
    entries = subject_entries(registry)
    subjects = list(plan["subjects"])
    # The market is checked before membership, so a plan built around another
    # market's Pool is refused as the wrong market rather than as one stray subject.
    for key, label in (("pool", "Pool proxy"), ("addresses_provider", "AddressesProvider")):
        if MARKET[key] not in subjects:
            raise AlexandriaError(
                f"the plan does not declare the main market's {label} {MARKET[key]}, so it "
                f"is not a plan over the {VENUE} main market"
            )
    for subject in subjects:
        if subject not in entries:
            raise AlexandriaError(
                f"the plan declares subject {subject}, which the {VENUE} registry does not list"
            )
    return subjects


def opening_phase(plan, registry, staged_logs):
    """Check the plan's scope, then refuse: this venue plans no opening reads yet."""
    validate_plan_scope(plan, registry)
    raise AlexandriaError(
        f"the {VENUE} venue does not yet derive per-subject epochs, so it plans no opening "
        "reads and a plan naming it cannot be collected or built"
    )


def gaps(registry, plan=None) -> list[str]:
    """The periphery overlap the registry records, one sentence per address."""
    return [
        f"subject {item['address']} ({item['role']}) is also listed as periphery "
        f"({item['periphery']}) in the full record the {VENUE} row pins; it is captured as a "
        "subject because it is inside the row's digest-bound subject set"
        for item in registry["periphery"]["overlap"]
    ]


def evidence_gaps(plan, registry, logs, first_code=None) -> list[str]:
    """This venue adds nothing to an evidence scope's gaps yet."""
    return []
