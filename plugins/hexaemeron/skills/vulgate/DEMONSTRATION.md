# Vulgate demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `vulgate-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `an-executable-demonstration`
- Current demonstration: No executable demonstration exists for this skill today.
- Next demonstration job: Build one executable demonstration of this skill over inputs a reader can check.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "vulgate",
  "plugin": "hexaemeron",
  "status": "absent",
  "claim_id": "vulgate-voice-mask",
  "claim": "This skill ships as a rewriting contract applied by an agent, with no script and no executable path in the repository, so no demonstration exists yet.",
  "non_claim": "It does not establish that the contract is applied correctly, and there is nothing here for a reader to run.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 300,
  "sources": [],
  "commands": [],
  "observations": [],
  "frontier": {
    "version": "vulgate-demo-v0.1.0",
    "status": "open",
    "revision": "an-executable-demonstration",
    "sha256": "57bd3f262fcd04cf2639013b0d070a9755bc443d29ded72305d92f1cd7389c2f",
    "current": "No executable demonstration exists for this skill today.",
    "next": "Build one executable demonstration of this skill over inputs a reader can check."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `vulgate-demo-v0.1.0` | baseline | `an-executable-demonstration` | `57bd3f262fcd04cf2639013b0d070a9755bc443d29ded72305d92f1cd7389c2f` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `absent` is decided by the material inputs above, not by the prose. |
