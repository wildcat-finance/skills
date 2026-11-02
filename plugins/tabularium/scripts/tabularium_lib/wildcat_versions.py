"""Closed Wildcat interpretation registry, independent of package versions."""

from .core import TabulariumError

ADAPTER_VERSION = "1.2.0"
LEGACY_VERSION = "1.0.0"
FEE_VERSIONS = ("1.1.0", "1.2.0")
NATIVE_VERSIONS = ("1.2.0",)
SUPPORTED_VERSIONS = (LEGACY_VERSION, *FEE_VERSIONS)


def checked_version(version):
    if not isinstance(version, str) or version not in SUPPORTED_VERSIONS:
        raise TabulariumError("unsupported Wildcat adapter version")
    return version
