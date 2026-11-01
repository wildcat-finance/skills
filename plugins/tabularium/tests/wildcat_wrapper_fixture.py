"""A constructed Wildcat V2 interval whose plan declares one wrapper (skills#2116).

The registry-context fixture is extended with the registry's wrapper factory
as a subject, one preserved `WrapperDeployed` log from it naming the declared
wrapper and the registry market the fixture deploys, the wrapper's own
`Deposit`, `Withdraw` and `Transfer` logs, and a second `WrapperDeployed`
naming a wrapper the plan does not declare. Alexandria derives the
`wrapper-subjects` component from those logs and attributes the declared
wrapper's logs to its own epoch; the undeclared wrapper's logs were never
requested. Every record is constructed; none was observed on a chain.
"""

import json
from pathlib import Path
import sys
import tempfile

if __package__:
    from .wildcat_v3_registry_fixture import (
        ASSET, CREATED_AT, IDENTITIES, PAYER, REPO_ROOT, RegistryFixtureTransport, _log,
        _word, registry_inputs,
    )
else:
    from wildcat_v3_registry_fixture import (
        ASSET, CREATED_AT, IDENTITIES, PAYER, REPO_ROOT, RegistryFixtureTransport, _log,
        _word, registry_inputs,
    )

from tabularium_lib import verifier  # noqa: E402
from tabularium_lib.wildcat_release import build_wildcat_canonical  # noqa: E402
from tabularium_lib.wildcat_source import _api  # noqa: E402


VENUE = "wildcat-v2"
# The registry's one wrapper-factory entry and the wrapper variant's pinned commit.
WRAPPER_FACTORY = "0xea6de11f8f3f83c79bd9d8db5517fcfdf2bb148a"
WRAPPER = "0x" + "ab" * 20
UNDECLARED_WRAPPER = "0x" + "cd" * 20
ACCOUNT = "0x" + "44" * 20
OTHER = "0x" + "66" * 20
MARKET = IDENTITIES[VENUE]["market"]
WRAPPER_DEPLOYED = "WrapperDeployed(address,address)"
WRAPPER_EVENTS = (
    ("Deposit(address,address,uint256,uint256)", (PAYER, ACCOUNT), (100, 80)),
    ("Withdraw(address,address,address,uint256,uint256)", (PAYER, OTHER, ACCOUNT), (60, 45)),
    ("Transfer(address,address,uint256)", (ACCOUNT, OTHER), (5,)),
)


def _data(values):
    return "0x" + b"".join(_word(value) for value in values).hex()


def wrapper_inputs(*, declare=True, undeclared=True):
    """The registry-context inputs plus the wrapper factory, its logs and the wrapper's."""
    _api()
    from alexandria_lib import interval

    state, registry = registry_inputs(VENUE)
    plan, logs = state["plan"], state["logs"]
    plan["subjects"] = sorted(plan["subjects"] + [WRAPPER_FACTORY])
    plan["deployment"] = VENUE + "-2116-constructed-wrapper"
    if declare:
        plan[interval.WRAPPERS_FIELD] = {"rule": interval.WRAPPERS_RULE, "subjects": [WRAPPER]}
    logs.append(_log(VENUE, WRAPPER_FACTORY, WRAPPER_DEPLOYED, len(logs), (MARKET, WRAPPER)))
    if undeclared:
        logs.append(_log(VENUE, WRAPPER_FACTORY, WRAPPER_DEPLOYED, len(logs), (MARKET, UNDECLARED_WRAPPER)))
    if declare:
        for signature, indexed, values in WRAPPER_EVENTS:
            logs.append(_log(VENUE, WRAPPER, signature, len(logs), indexed, _data(values)))
    state["code"][WRAPPER_FACTORY] = "0x6000600055"
    state["code"][WRAPPER] = "0x" + "60006000556001" * 4
    return state, registry


def build_wrapper_release(base: Path, release_id: str, **options) -> Path:
    """Collect, build and check the wrapper interval, then publish its canonical root."""
    state, registry = wrapper_inputs(**options)
    interval_api, release_api, _, _ = _api()
    with tempfile.TemporaryDirectory(prefix="wildcat-wrapper-fixture-") as temporary:
        scratch = Path(temporary).resolve()
        staging = scratch / "staging"
        staging.mkdir()
        interval_api.Collector(state["plan"], staging, RegistryFixtureTransport(state),
                               registry=registry).collect()
        interval_api.Reconciler(state["plan"], staging, RegistryFixtureTransport(state),
                                "second constructed provider, class only", registry=registry).reconcile()
        raw = scratch / "raw"
        interval_api.Builder(state["plan"], staging, registry, created_at=CREATED_AT).build(raw)
        interval_api.check_interval(raw)
        release_api.verify_release(raw)
        build_wildcat_canonical(raw, base, release_id)
    coverage = base / "coverage.json"
    verifier.verify(coverage)
    return coverage
