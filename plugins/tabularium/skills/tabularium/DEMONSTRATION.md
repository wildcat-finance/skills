# Tabularium demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `tabularium-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `canonical-compound-v3-events`
- Current demonstration: The Aave v4 rebuild matches its record digest while the Compound witness stays reconstructed.
- Next demonstration job: Preserve canonical Compound v3 events so the release carries no reconstructed component.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "tabularium",
  "plugin": "tabularium",
  "status": "mixed",
  "claim_id": "tabularium-goldfinch-release",
  "claim": "The preserved Aave v4 credit events rebuild to their declared record digest offline.",
  "non_claim": "The Compound v3 Phase 0 witness beside them is a non-canonical reconstruction, not a preserved venue record.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 900,
  "sources": [
    {
      "id": "input-1",
      "class": "protocol",
      "path": "plugins/tabularium/examples/aave-v4-v0/events.jsonl",
      "sha256": "490d3f6399f84af8a81a5401b3cc92bf7ecfbe98a6bb02f07215b9099625ccf7"
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
        "plugins/tabularium/examples/aave-v4-v0/rebuild.py"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.3 seconds with no network.",
    "Its last reported line is: rebuild matches aave-v4-mainnet-credit-window-v0: 490d3f6399f84af8a81a5401b3cc92bf7ecfbe98a6bb02f07215b9099625ccf7"
  ],
  "frontier": {
    "version": "tabularium-demo-v0.1.0",
    "status": "open",
    "revision": "canonical-compound-v3-events",
    "sha256": "a2857ce92e63d0a2f5fedb9a02f09a118cb003109cb547f84008b9e48dc0207b",
    "current": "The Aave v4 rebuild matches its record digest while the Compound witness stays reconstructed.",
    "next": "Preserve canonical Compound v3 events so the release carries no reconstructed component."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `tabularium-demo-v0.1.0` | baseline | `canonical-compound-v3-events` | `a2857ce92e63d0a2f5fedb9a02f09a118cb003109cb547f84008b9e48dc0207b` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `mixed` is decided by the material inputs above, not by the prose. |
