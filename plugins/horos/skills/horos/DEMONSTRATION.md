# Horos demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `horos-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `boundary-over-an-external-tree`
- Current demonstration: The example fixture's committed boundary matches a fresh scan.
- Next demonstration job: Publish a checked boundary over an external repository this collective does not own.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "horos",
  "plugin": "horos",
  "status": "constructed",
  "claim_id": "horos-fixture-boundary",
  "claim": "The registered offline path exercises horos over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 300,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/horos/examples/fixture/yarn.lock",
      "sha256": "37268e82bef6c4860c650f4feedff10b213b767d30298df719938ca1977999b4"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/horos/skills/horos/scripts/horos.py",
        "check",
        "plugins/horos/examples/fixture"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.1 seconds with no network.",
    "Its last reported line is: boundary matches the tree"
  ],
  "frontier": {
    "version": "horos-demo-v0.1.0",
    "status": "open",
    "revision": "boundary-over-an-external-tree",
    "sha256": "1dedbd239d28d758499215587209a9f67cca19bf9e54a4aae82f8faa2b2f9eea",
    "current": "The example fixture's committed boundary matches a fresh scan.",
    "next": "Publish a checked boundary over an external repository this collective does not own."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `horos-demo-v0.1.0` | baseline | `boundary-over-an-external-tree` | `1dedbd239d28d758499215587209a9f67cca19bf9e54a4aae82f8faa2b2f9eea` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
