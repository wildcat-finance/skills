# Lazarus demonstration ledger

Contract: `plugins/hexaemeron/skills/DEMONSTRATIONS.md`

- Current demonstration version: `lazarus-demo-v0.1.0`
- Demo frontier status: `open`
- Demo frontier revision: `second-preserved-market`
- Current demonstration: The Aave v4 spoke block 25870892 fixture replays and its manifest rebuild reports identical.
- Next demonstration job: Preserve and replay a second market so the boundary is shown over more than one capture.

The registered record below runs `aave-v4-spoke-v1`, the receipt-proving
successor to the deleted Goldfinch capture. `aave-v4-spoke-v0` preserves the
same block without a receipt witness, so it cannot carry this record's
receipt-trie claim.

```shoggoth-demonstration
{
  "schema": "shoggoth-demonstration/v1",
  "skill": "lazarus",
  "plugin": "lazarus",
  "status": "real-data",
  "claim_id": "lazarus-goldfinch-replay",
  "claim": "The preserved Ethereum mainnet Aave v4 spoke capture at block 0x18ac22c rebuilds offline to its shipped fixture and release, and its receipt-trie relation is proved against the recorded header.",
  "non_claim": "It does not establish canonical-chain finality or provider independence for the Aave v4 capture: transaction hashes are recorded RPC metadata, not a proved header identity, and nothing here describes current chain state.",
  "network": {
    "policy": "denied"
  },
  "timeout_seconds": 600,
  "sources": [
    {
      "id": "spoke-block",
      "class": "chain",
      "chain": "ethereum",
      "block": 25870892,
      "anchor": "0x11e9be2ff9ff6a04319af0b04c24b95f3f1117c2df79f44f94d208857d01af07"
    },
    {
      "id": "fixture-manifest",
      "class": "protocol",
      "path": "plugins/lazarus/examples/aave-v4-spoke-v1/manifest.json",
      "sha256": "af7ec64ea4df28b3a5d88586d507a8a0f3651bfb1447ee28ebdd0a1282bc8f47"
    },
    {
      "id": "program",
      "class": "repository",
      "path": "plugins/lazarus/examples/aave-v4-spoke-v1/demo.py",
      "sha256": "d8c1da22a04dd12b1db19b3ae47dcbfe7d70e8f2a1a19907b3c82780719e0d00"
    }
  ],
  "commands": [
    {
      "id": "run",
      "argv": [
        "python3",
        "plugins/lazarus/examples/aave-v4-spoke-v1/demo.py"
      ],
      "expect_exit": 0
    }
  ],
  "observations": [
    "run: json block.number \"0x18ac22c\"",
    "run: json network \"denied\"",
    "run: json relation.receipt_count 177",
    "run: json relation.target_index \"0x3f\"",
    "run: json relation.target_log_count 4",
    "run: json relation.filtered_log_count 2",
    "run: json relation.proved_relations 2",
    "run: json relation.transaction_hash_attribution \"recorded_rpc\"",
    "run: json fixture_rebuild \"identical\"",
    "run: json digests.fixture \"ea047af74636f278d1641807edbce7860bc831e6822db187fd8d5290d0dc937b\"",
    "run: json digests.release \"a104fc78d4c7b6b1df8fe0abd9daa74236b382154f4246604662040d1298aa39\""
  ],
  "frontier": {
    "version": "lazarus-demo-v0.1.0",
    "status": "open",
    "revision": "second-preserved-market",
    "sha256": "791b317650ebef12a52df7bc7d5ffe0fa67979c991ca7f650851473499dac5db",
    "current": "The Aave v4 spoke block 25870892 fixture replays and its manifest rebuild reports identical.",
    "next": "Preserve and replay a second market so the boundary is shown over more than one capture."
  }
}
```

## History

| Version | Axis | Demo frontier revision | Demo frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `lazarus-demo-v0.1.0` | baseline | `second-preserved-market` | `791b317650ebef12a52df7bc7d5ffe0fa67979c991ca7f650851473499dac5db` | `adr/govern-real-data-demonstrations-separately` | The demonstration lane starts here. Status `real-data` is decided by the material inputs above, not by the prose. The record was re-derived onto `aave-v4-spoke-v1` when the Goldfinch fixtures left the tree; the demo frontier digest moved with the current-demonstration sentence. |
