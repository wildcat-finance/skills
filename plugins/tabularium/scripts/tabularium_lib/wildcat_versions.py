"""Closed interpretation registry shared by Wildcat builders and validators."""

from .core import TabulariumError

LEGACY_VERSION = "1.0.0"
ADAPTER_VERSION = "1.3.0"
SUPPORTED_VERSIONS = (LEGACY_VERSION, ADAPTER_VERSION)


def checked_version(version):
    if not isinstance(version, str) or version not in SUPPORTED_VERSIONS:
        raise TabulariumError("unsupported Wildcat adapter version")
    return version


def has_routing(version):
    return checked_version(version) == "1.3.0"
