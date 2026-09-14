# Hermes demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `hermes-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `savings-from-a-real-contract`
- Current demonstration: The gas rule corpus validates its 120 rules and 28 rejections.
- Next demonstration job: Measure and re-prove a saving on a deployed Wildcat contract.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "hermes",
  "plugin": "hermes",
  "status": "constructed",
  "claim_id": "hermes-rule-corpus",
  "claim": "The registered offline path exercises hermes over checked-in inputs and exits zero.",
  "non_claim": "Every material input was created for this repository's own tests, so the run establishes nothing about real-world data.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 300,
  "sources": [
    {
      "id": "input",
      "class": "fixture",
      "path": "plugins/hermes/skills/hermes/references/gas-rule-corpus.json",
      "sha256": "5d1773f9a5f51e957bd769deb3b030b670fa10499e33fce4a8df3a2e221bd5ac"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/hermes/skills/hermes/scripts/hermes.py",
        "corpus",
        "--validate"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.0 seconds with no network.",
    "Its last reported line is: clean"
  ],
  "frontier": {
    "version": "hermes-demo-v0.1.0",
    "status": "open",
    "revision": "savings-from-a-real-contract",
    "sha256": "984e32e19939a5bd1bdbb2e5f9cd837b87c2c067a8066b6a9c88c2afe97dea40",
    "current": "The gas rule corpus validates its 120 rules and 28 rejections.",
    "next": "Measure and re-prove a saving on a deployed Wildcat contract."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `hermes-demo-v0.1.0` | baseline | `savings-from-a-real-contract` | `984e32e19939a5bd1bdbb2e5f9cd837b87c2c067a8066b6a9c88c2afe97dea40` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `constructed` is decided by the material inputs above, not by the prose. |
