# Tabularium demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `tabularium-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `canonical-compound-v3-events`
- Current demonstration: The Goldfinch rebuild matches its record digest while the Compound witness stays reconstructed.
- Next demonstration job: Preserve canonical Compound v3 events so the release carries no reconstructed component.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "tabularium",
  "plugin": "tabularium",
  "status": "mixed",
  "claim_id": "tabularium-goldfinch-release",
  "claim": "The preserved Goldfinch credit events rebuild to their declared record digest offline.",
  "non_claim": "The Compound v3 Phase 0 witness beside them is a non-canonical reconstruction, not a preserved venue record.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 900,
  "sources": [
    {
      "id": "input-1",
      "class": "protocol",
      "path": "plugins/tabularium/examples/goldfinch-v0/events.jsonl",
      "sha256": "751754a2f913691cf95f3e9f859b156f9ccd7963b1d72d4fc3379348924469b1"
    },
    {
      "id": "input-2",
      "class": "model-record",
      "path": "plugins/tabularium/examples/compound-v3-phase0-v0/witness.json",
      "sha256": "b6009daeaef2ee09ce4babb4cd8dff05f6a481dfb7f87e74c1b54152a6ad7c0a"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/tabularium/examples/goldfinch-v0/rebuild.py"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.1 seconds with no network.",
    "Its last reported line is: coverage manifest sha256 58184a75d8eca6ae8d9b44653c36ce8c482549c5d3cecd1a2a991b0936561f6d"
  ],
  "frontier": {
    "version": "tabularium-demo-v0.1.0",
    "status": "open",
    "revision": "canonical-compound-v3-events",
    "sha256": "e3e0e7c08f95dfeafb8ed02d69737ec6fe01ef2ae81245372d540aa97ae2069a",
    "current": "The Goldfinch rebuild matches its record digest while the Compound witness stays reconstructed.",
    "next": "Preserve canonical Compound v3 events so the release carries no reconstructed component."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `tabularium-demo-v0.1.0` | baseline | `canonical-compound-v3-events` | `e3e0e7c08f95dfeafb8ed02d69737ec6fe01ef2ae81245372d540aa97ae2069a` | `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` | The demonstration lane starts here. Status `mixed` is decided by the material inputs above, not by the prose. |
