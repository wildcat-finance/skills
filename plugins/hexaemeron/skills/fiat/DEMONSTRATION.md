# Fiat demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `fiat-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `replay-a-preserved-run`
- Current demonstration: The controller capsule exports and restores over a fixture run.
- Next demonstration job: Restore a preserved real run's checkpoint on a clean machine and continue its ledger.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "fiat",
  "plugin": "hexaemeron",
  "status": "constructed",
  "claim_id": "fiat-controller-ledger",
  "claim": "The registered offline path exercises fiat over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 900,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/hexaemeron/tests/test_hexctl_checkpoint.py",
      "sha256": "7869db93162ab3b3f70b5670e4fbf810fab18437193df0109cb711a33f65b54b"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "plugins.hexaemeron.tests.test_hexctl_checkpoint"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 138.6 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "fiat-demo-v0.1.0",
    "status": "open",
    "revision": "replay-a-preserved-run",
    "sha256": "fc4e742709eb564873abb6aacd7048bb5c09b0f9a4d0f3b5a62ae40574986955",
    "current": "The controller capsule exports and restores over a fixture run.",
    "next": "Restore a preserved real run's checkpoint on a clean machine and continue its ledger."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `fiat-demo-v0.1.0` | baseline | `replay-a-preserved-run` | `fc4e742709eb564873abb6aacd7048bb5c09b0f9a4d0f3b5a62ae40574986955` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
