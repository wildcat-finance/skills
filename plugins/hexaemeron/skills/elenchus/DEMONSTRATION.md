# Elenchus demonstration ledger

Contract: [skill demonstration contract](../DEMONSTRATIONS.md)

- Current demonstration version: `elenchus-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `guard-a-preserved-failure`
- Current demonstration: The checker refuses and admits reports over its fixture corpus.
- Next demonstration job: Work a preserved production failure end to end and keep its guard.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "elenchus",
  "plugin": "hexaemeron",
  "status": "constructed",
  "claim_id": "elenchus-guard-verdict",
  "claim": "The registered offline path exercises elenchus over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/hexaemeron/tests/test_elenchus_checker.py",
      "sha256": "0ea5bd2c57bbd16f044c7279509f822d13205c2eedea05a0b44aa6301a224110"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "plugins.hexaemeron.tests.test_elenchus_checker"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "On 2026-09-21 the command ran 63 tests in 28.440 seconds and exited 0.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "elenchus-demo-v0.1.0",
    "status": "open",
    "revision": "guard-a-preserved-failure",
    "sha256": "a0af41cec8e317a97aa5f82ef08b7303495fee12e7731e064595e03215c1bde7",
    "current": "The checker refuses and admits reports over its fixture corpus.",
    "next": "Work a preserved production failure end to end and keep its guard."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `elenchus-demo-v0.1.0` | baseline | `guard-a-preserved-failure` | `a0af41cec8e317a97aa5f82ef08b7303495fee12e7731e064595e03215c1bde7` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
