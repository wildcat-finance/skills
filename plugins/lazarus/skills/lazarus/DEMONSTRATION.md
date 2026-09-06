# Lazarus demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `lazarus-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `second-preserved-market`
- Current demonstration: The Goldfinch block 13097494 fixture replays and its manifest rebuild reports identical.
- Next demonstration job: Preserve and replay a second market so the boundary is shown over more than one capture.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "lazarus",
  "plugin": "lazarus",
  "status": "real-data",
  "claim_id": "lazarus-goldfinch-replay",
  "claim": "One preserved Ethereum mainnet view of the Goldfinch market replays offline against its captured block identity.",
  "non_claim": "It does not establish that the receipt and log query are state-proof-backed, and it says nothing about current chain state.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "goldfinch-block",
      "class": "chain",
      "chain": "ethereum",
      "block": 13097494,
      "anchor": "0x41119192a8acdaae5ab06ca8f1d5943fd7ca2fb0a14323642dd6daf74eed2cfc"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/lazarus/examples/goldfinch-v0/demo.py"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "The command exits 0 in about 0.6 seconds with no network.",
    "Its last reported line is: manifest rebuild: identical"
  ],
  "frontier": {
    "version": "lazarus-demo-v0.1.0",
    "status": "open",
    "revision": "second-preserved-market",
    "sha256": "5bb3e7a9c13e32a0e93534aed0316c6dd1ff617ef5b86b7b23f14c4c3c4490a8",
    "current": "The Goldfinch block 13097494 fixture replays and its manifest rebuild reports identical.",
    "next": "Preserve and replay a second market so the boundary is shown over more than one capture."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `lazarus-demo-v0.1.0` | baseline | `second-preserved-market` | `5bb3e7a9c13e32a0e93534aed0316c6dd1ff617ef5b86b7b23f14c4c3c4490a8` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `real-data` is decided by the material inputs above, not by the prose. |
