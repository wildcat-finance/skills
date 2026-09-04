# Ephoros demonstration ledger

Contract: [skill demonstration contract](../DEMONSTRATIONS.md)

- Current demonstration version: `ephoros-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `signals-from-a-running-step`
- Current demonstration: The lint refuses unlabelled alerts and unbounded metrics over fixtures.
- Next demonstration job: Instrument one step that actually runs unattended and show its recorded signals.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "ephoros",
  "plugin": "hexaemeron",
  "status": "constructed",
  "claim_id": "ephoros-signal-lint",
  "claim": "The registered offline path exercises ephoros over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/alert-labels.yaml",
      "sha256": "e1ce39ee69d63b8d28dc484f69205dc6dc03365befc3f556f55ef47e57572469"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "plugins.hexaemeron.tests.test_ephoros_checker"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.9 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "ephoros-demo-v0.1.0",
    "status": "open",
    "revision": "signals-from-a-running-step",
    "sha256": "4bc9af7ed4daa6f066ced6728fe4e465131d1e6875e35772221ddfa98c77d6b1",
    "current": "The lint refuses unlabelled alerts and unbounded metrics over fixtures.",
    "next": "Instrument one step that actually runs unattended and show its recorded signals."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `ephoros-demo-v0.1.0` | baseline | `signals-from-a-running-step` | `4bc9af7ed4daa6f066ced6728fe4e465131d1e6875e35772221ddfa98c77d6b1` | [ADR-076](../../../../docs/decisions/ADR-076-govern-real-data-demonstrations-separately.md) | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
