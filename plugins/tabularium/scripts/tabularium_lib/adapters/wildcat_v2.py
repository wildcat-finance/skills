"""Wildcat V2 schema 3 registration; raw releases use the dedicated builder."""

from ..core import TabulariumError
from ..wildcat_validation import ADAPTER_VERSION, CHAIN, SOURCE_API, mappings

ADAPTER = "wildcat-v2"
PROTOCOL_GENERATION = ADAPTER
CHAIN_ID = 1
MAPPINGS = mappings(ADAPTER)


def map_source(source, capture, schema_version):
    raise TabulariumError("Wildcat requires wildcat-canonical with a verified Alexandria raw release")
