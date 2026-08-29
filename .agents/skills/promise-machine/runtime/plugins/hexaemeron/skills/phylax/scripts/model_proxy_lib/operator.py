"""Render operator disclosure from exact replayed model proxy policy bytes."""

from __future__ import annotations

from .errors import PolicyError, refuse
from .policy import CompiledPolicy, compile_policy


def render_operator_text(policy: CompiledPolicy) -> str:
    """Describe the configured disclosure without strengthening its promise."""

    if type(policy) is not CompiledPolicy:
        refuse("MP400", "lifecycle.policy")
    try:
        replayed = compile_policy(policy.accepted_job_bytes)
    except (PolicyError, TypeError):
        refuse("MP400", "lifecycle.policy")
    if (
        replayed.policy_bytes != policy.policy_bytes
        or replayed.policy_sha256 != policy.policy_sha256
        or replayed.jobspec_sha256 != policy.jobspec_sha256
        or replayed.profile != policy.profile
    ):
        refuse("MP400", "lifecycle.policy")

    document = replayed.document
    provider = document["provider"]
    disclosure = document["disclosure"]
    receipt = document["receipt"]
    limits = document["limits"]
    disabled = ", ".join(disclosure["disabled_features"])
    rendered_limits = ", ".join(
        f"{name}={limits[name]}" for name in sorted(limits)
    )
    return "\n".join(
        (
            f"Model proxy job: {document['job']['id']}",
            (
                "Leaves this machine: the mapped text input and the provider "
                "bearer credential; model output returns through the closed response schema."
            ),
            (
                f"Destination: {provider['provider']} at {provider['origin_family']}"
                f"{provider['path_family']} through profile {provider['id']} "
                f"and model {provider['model']}."
            ),
            (
                f"Retention: provider storage={str(provider['storage']).lower()}, "
                f"provider rule={provider['retention']}; local receipts retain "
                f"{receipt['content']} model content for {receipt['retention_seconds']} seconds."
            ),
            f"Disabled features: {disabled}.",
            f"Limits: {rendered_limits}.",
            (
                "Provider non-exfiltration qualification: these controls restrict "
                "the selected destination and keep the credential from the guest, "
                "but they do not prove that the provider will not retain or "
                "exfiltrate disclosed model content."
            ),
        )
    )
