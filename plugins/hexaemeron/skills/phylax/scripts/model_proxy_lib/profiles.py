"""Closed code-owned provider profiles for model proxy policy version 1."""

from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Mapping

from .errors import refuse


FEATURE_NAMES = (
    "audio",
    "background",
    "conversations",
    "files",
    "images",
    "remote_urls",
    "storage",
    "streaming",
    "tools",
    "uploads",
)


@dataclass(frozen=True, slots=True)
class ProviderProfile:
    """One immutable provider/model/schema mapping owned by reviewed code."""

    identifier: str
    provider: str
    origin_family: str
    path_family: str
    method: str
    operation: str
    model: str
    request_schema: str
    response_schema: str
    token_counter: str
    storage: bool
    retention: str
    allowed_data_classes: tuple[str, ...]
    limit_ceilings: Mapping[str, int]
    scheme: str
    hostname: str
    port: int
    credential_environment: str
    authorization_scheme: str
    provider_request_schema: str
    provider_response_schema: str

    def policy_fields(self) -> dict[str, object]:
        return {
            "id": self.identifier,
            "provider": self.provider,
            "origin_family": self.origin_family,
            "path_family": self.path_family,
            "method": self.method,
            "operation": self.operation,
            "model": self.model,
            "request_schema": self.request_schema,
            "response_schema": self.response_schema,
            "token_counter": self.token_counter,
            "storage": self.storage,
            "retention": self.retention,
        }


_LOOPBACK_CEILINGS = MappingProxyType(
    {
        "max_requests": 32,
        "max_request_bytes": 65_536,
        "max_response_bytes": 131_072,
        "max_input_tokens": 8_192,
        "max_output_tokens": 4_096,
        "max_total_request_bytes": 1_048_576,
        "max_total_response_bytes": 2_097_152,
        "max_total_input_tokens": 65_536,
        "max_total_output_tokens": 32_768,
        "max_concurrency": 4,
        "max_json_depth": 12,
        "max_json_members": 256,
        "max_string_bytes": 32_768,
        "max_receipt_bytes": 4_096,
        "max_receipts": 34,
        "total_wall_seconds": 900,
    }
)


LOOPBACK_TEXT_V1 = ProviderProfile(
    identifier="loopback-text/v1",
    provider="synthetic-loopback",
    origin_family="https://model-proxy.loopback.invalid",
    path_family="/v1/responses",
    method="POST",
    operation="text.generate",
    model="fixture-text-1",
    request_schema="model-request/v1",
    response_schema="model-response/v1",
    token_counter="unicode-codepoint-fixture/v1",
    storage=False,
    retention="process-memory-only",
    allowed_data_classes=("synthetic-public",),
    limit_ceilings=_LOOPBACK_CEILINGS,
    scheme="https",
    hostname="model-proxy.loopback.invalid",
    port=443,
    credential_environment="WILDCAT_MODEL_PROXY_CREDENTIAL",
    authorization_scheme="Bearer",
    provider_request_schema="synthetic-provider-request/v1",
    provider_response_schema="synthetic-provider-response/v1",
)


_PROFILES = MappingProxyType({LOOPBACK_TEXT_V1.identifier: LOOPBACK_TEXT_V1})
_PROFILE_VERSION = re.compile(r"loopback-text/v[0-9]+\Z")


def resolve_profile(identifier: str) -> ProviderProfile:
    """Resolve exactly one known profile without accepting a runtime default."""

    if not isinstance(identifier, str):
        refuse("MP112", "model_proxy.provider_profile")
    profile = _PROFILES.get(identifier)
    if profile is not None:
        return profile
    if _PROFILE_VERSION.fullmatch(identifier):
        refuse("MP121", "model_proxy.provider_profile")
    refuse("MP112", "model_proxy.provider_profile")
