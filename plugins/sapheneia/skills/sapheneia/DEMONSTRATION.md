# Sapheneia demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `sapheneia-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `shape-a-published-record`
- Current demonstration: The promise cases exercise the record shaping contract over fixtures.
- Next demonstration job: Shape one durable record that was actually published and compare its inventory.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "sapheneia",
  "plugin": "sapheneia",
  "status": "constructed",
  "claim_id": "sapheneia-record-shape",
  "claim": "The registered offline path exercises sapheneia over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/sapheneia/tests/fixtures/promise-machine/cases.json",
      "sha256": "02868e65be7ec505abec7db65950e5bb11c305194cf3f7f2fa41f4f66bef9c11"
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
        "plugins/sapheneia/tests",
        "-t",
        "plugins/sapheneia"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.0 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "sapheneia-demo-v0.1.0",
    "status": "open",
    "revision": "shape-a-published-record",
    "sha256": "7d43abb98c7e0000cb93be6c48fd87bae59e19ba3994c64fcc98b58a230132a3",
    "current": "The promise cases exercise the record shaping contract over fixtures.",
    "next": "Shape one durable record that was actually published and compare its inventory."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `sapheneia-demo-v0.1.0` | baseline | `shape-a-published-record` | `7d43abb98c7e0000cb93be6c48fd87bae59e19ba3994c64fcc98b58a230132a3` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
