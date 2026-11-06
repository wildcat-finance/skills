"""Closed Wildcat interpretation registry, independent of package versions."""

from .core import TabulariumError

ADAPTER_VERSION = "1.6.0"
LEGACY_VERSION = "1.0.0"
FEE_VERSIONS = ("1.1.0", "1.2.0", "1.3.0", "1.4.0", "1.5.0", "1.6.0")
NATIVE_VERSIONS = ("1.2.0", "1.3.0", "1.4.0", "1.5.0", "1.6.0")
ROUTING_VERSIONS = ("1.3.0", "1.4.0", "1.5.0", "1.6.0")
# Each later version keeps every lower version's results; `1.4.0` adds the
# accrual and state-update meanings, which every lower version leaves unsupported.
ACCRUAL_VERSIONS = ("1.4.0", "1.5.0", "1.6.0")
# `1.5.0` adds the V2 hook-call MarketState observations to `source.json` and
# adds no canonical rows; earlier versions remain explicit replay selectors.
HOOK_STATE_VERSIONS = ("1.5.0", "1.6.0")
CONTROL_VERSIONS = ("1.6.0",)
SUPPORTED_VERSIONS = (LEGACY_VERSION, *FEE_VERSIONS)


def checked_version(version):
    if not isinstance(version, str) or version not in SUPPORTED_VERSIONS:
        raise TabulariumError("unsupported Wildcat adapter version")
    return version


def has_routing(version):
    return checked_version(version) in ROUTING_VERSIONS
