"""Closed Wildcat interpretation registry, independent of package versions."""

from .core import TabulariumError

ADAPTER_VERSION = "1.1.0"
SUPPORTED_VERSIONS = ("1.0.0", "1.1.0")


def checked_version(version):
    if not isinstance(version, str) or version not in SUPPORTED_VERSIONS:
        raise TabulariumError("unsupported Wildcat adapter version")
    return version
