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
  "claim": "The preserved Ethereum mainnet Goldfinch capture at block 0xc7da16 rebuilds offline to its shipped fixture and release, and its receipt-trie relation is proved against the recorded header.",
  "non_claim": "It does not establish canonical-chain finality or provider independence: transaction hashes are recorded RPC metadata, not a proved header identity, and nothing here describes current chain state.",
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
    },
    {
      "id": "fixture-manifest",
      "class": "protocol",
      "path": "plugins/lazarus/examples/goldfinch-v1/manifest.json",
      "sha256": "b350b6070755a2944bafa8035b5c3f97502ee1abe86abd4c560c4492f6412ba6"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/lazarus/examples/goldfinch-v1/demo.py"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "run: json block.number \"0xc7da16\"",
    "run: json network \"denied\"",
    "run: json relation.receipt_count 224",
    "run: json relation.target_index \"0xbf\"",
    "run: json relation.target_log_count 110",
    "run: json relation.filtered_log_count 5",
    "run: json relation.proved_relations 2",
    "run: json relation.transaction_hash_attribution \"recorded_rpc\"",
    "run: json fixture_rebuild \"identical\"",
    "run: json digests.fixture \"aadf1b809ae45946967e17f2132ae4d73b06026345b0e8c7f1ca4c3c0add9535\"",
    "run: json digests.release \"701fa846f81c28ede5ab9539c0c19815dfe7435eca45ba663219c0c88c3bdb74\""
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
