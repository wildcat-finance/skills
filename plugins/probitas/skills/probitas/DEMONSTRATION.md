# Probitas demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `probitas-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `dossier-over-a-declared-counterparty`
- Current demonstration: The five dossier gates run over the demo adapter fixtures.
- Next demonstration job: Build a dossier for a counterparty that actually applied for a market.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "probitas",
  "plugin": "probitas",
  "status": "constructed",
  "claim_id": "probitas-dossier-gates",
  "claim": "The registered offline path exercises probitas over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 900,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/probitas/tests/fixtures/demo/morpho-midnight.json",
      "sha256": "c01533bdfabf40da61a7a21b73767615083ef336665e974ed56c12275615b4b5"
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
        "plugins/probitas/tests",
        "-t",
        "plugins/probitas"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 6.4 seconds with no network.",
    "Its last reported line is: OK"
  ],
  "frontier": {
    "version": "probitas-demo-v0.1.0",
    "status": "open",
    "revision": "dossier-over-a-declared-counterparty",
    "sha256": "f13aee27da8d20b9ef1a899eec17eb296fcc389fbd61e4ba0525b2bbb8c854fb",
    "current": "The five dossier gates run over the demo adapter fixtures.",
    "next": "Build a dossier for a counterparty that actually applied for a market."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `probitas-demo-v0.1.0` | baseline | `dossier-over-a-declared-counterparty` | `f13aee27da8d20b9ef1a899eec17eb296fcc389fbd61e4ba0525b2bbb8c854fb` | `docs/decisions/ADR-076-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
