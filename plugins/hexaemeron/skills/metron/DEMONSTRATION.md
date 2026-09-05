# Metron demonstration ledger

Contract: [skill demonstration contract](../DEMONSTRATIONS.md)

- Current demonstration version: `metron-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `measure-a-real-regression`
- Current demonstration: The gate refuses a speed claim with no recorded before and after.
- Next demonstration job: Measure and repair one recorded performance regression.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "metron",
  "plugin": "hexaemeron",
  "status": "constructed",
  "claim_id": "metron-measurement-gate",
  "claim": "The registered offline path exercises metron over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/hexaemeron/tests/fixtures/metron/metron-budgets.json",
      "sha256": "90788aacae2b964d0f63d6cfd474b00f8f05bf270e320e9a437b5df544b39083"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "-m",
        "unittest",
        "plugins.hexaemeron.tests.test_metron_check"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.8 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "metron-demo-v0.1.0",
    "status": "open",
    "revision": "measure-a-real-regression",
    "sha256": "12abf64cec6e108883b76b837362833517e6ea14b8a57fe9f2522d3dde6574f0",
    "current": "The gate refuses a speed claim with no recorded before and after.",
    "next": "Measure and repair one recorded performance regression."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `metron-demo-v0.1.0` | baseline | `measure-a-real-regression` | `12abf64cec6e108883b76b837362833517e6ea14b8a57fe9f2522d3dde6574f0` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
