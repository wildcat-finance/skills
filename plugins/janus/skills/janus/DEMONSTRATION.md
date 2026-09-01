# Janus demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `janus-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `conformance-over-a-deployed-hook`
- Current demonstration: The validator and reporter refuse malformed manifests over fixtures.
- Next demonstration job: Check one deployed hook against its host's economic contract.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "janus",
  "plugin": "janus",
  "status": "constructed",
  "claim_id": "janus-hook-manifest-report",
  "claim": "The registered offline path exercises janus over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/janus/tests/fixtures/j004_bad_rollback.json",
      "sha256": "3a9d4013005098b425e4c70764be643cfd771e7f158478695d425db82e08a97b"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "discover",
        "-s",
        "plugins/janus/tests",
        "-t",
        "plugins/janus"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.0 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "janus-demo-v0.1.0",
    "status": "open",
    "revision": "conformance-over-a-deployed-hook",
    "sha256": "b0119a20d30fc34d9c38db5f73f7e88923582b0f40eddc5aa75b49ef2960f082",
    "current": "The validator and reporter refuse malformed manifests over fixtures.",
    "next": "Check one deployed hook against its host's economic contract."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `janus-demo-v0.1.0` | baseline | `conformance-over-a-deployed-hook` | `b0119a20d30fc34d9c38db5f73f7e88923582b0f40eddc5aa75b49ef2960f082` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
