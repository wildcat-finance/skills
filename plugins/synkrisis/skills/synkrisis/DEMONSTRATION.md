# Synkrisis demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `synkrisis-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `cohort-over-preserved-runs`
- Current demonstration: The scale specimen exercises the whole cohort path over constructed run observations.
- Next demonstration job: Build a cohort from preserved Promise Machine run observations rather than constructed ones.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "synkrisis",
  "plugin": "synkrisis",
  "status": "constructed",
  "claim_id": "synkrisis-cross-run-cohort",
  "claim": "A hundred-run cohort is built, diagnosed, rendered and verified from declared observations.",
  "non_claim": "Every run in the cohort was constructed for the comparison, so the finding is about the specimen and not about any model.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/synkrisis/tests/fixtures/scale/100-runs/spec.json",
      "sha256": "af91d0aeb54bc47ee46a571fa1c385003c28df1dc5b238f64d0f717685049584"
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
        "plugins/synkrisis/tests",
        "-t",
        "plugins/synkrisis"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.8 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "synkrisis-demo-v0.1.0",
    "status": "open",
    "revision": "cohort-over-preserved-runs",
    "sha256": "584c67f7a75e0e812b9ad172e546f60196115acffe08836099abbcfa1633c4ce",
    "current": "The scale specimen exercises the whole cohort path over constructed run observations.",
    "next": "Build a cohort from preserved Promise Machine run observations rather than constructed ones."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `synkrisis-demo-v0.1.0` | baseline | `cohort-over-preserved-runs` | `584c67f7a75e0e812b9ad172e546f60196115acffe08836099abbcfa1633c4ce` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
