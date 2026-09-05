# Protasis demonstration ledger

Contract: [skill demonstration contract](../DEMONSTRATIONS.md)

- Current demonstration version: `protasis-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `design-lock-from-a-shipped-run`
- Current demonstration: The design-evidence checker locks a selection over fixture reports.
- Next demonstration job: Lock a design from a shipped run's own reports rather than fixtures.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "protasis",
  "plugin": "hexaemeron",
  "status": "constructed",
  "claim_id": "protasis-design-lock",
  "claim": "The registered offline path exercises protasis over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/hexaemeron/tests/fixtures/protasis/complete-study.md",
      "sha256": "b62449254c8bf669ade0985d1b899e0f318f5a98b8a3390b15a6f7749c79b151"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "plugins.hexaemeron.tests.test_protasis_design_evidence"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.1 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "protasis-demo-v0.1.0",
    "status": "open",
    "revision": "design-lock-from-a-shipped-run",
    "sha256": "9b9cb8e31f3b7b47023380fd2b7aa13fa539a7bea41cdba079426918819993ae",
    "current": "The design-evidence checker locks a selection over fixture reports.",
    "next": "Lock a design from a shipped run's own reports rather than fixtures."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `protasis-demo-v0.1.0` | baseline | `design-lock-from-a-shipped-run` | `9b9cb8e31f3b7b47023380fd2b7aa13fa539a7bea41cdba079426918819993ae` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
