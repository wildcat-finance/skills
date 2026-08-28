# Multi-provider chain anchors

Lazarus plan v2 can preserve matching block-hash observations from several
runtime RPC sources. These records corroborate one fixed header. They do not
prove that the header is on Ethereum's canonical chain, and distinct source
IDs do not prove provider independence.

## Plan and runtime mapping

The plan contains sorted, unique, opaque source IDs and no provider URLs:

```json
{
  "schema_version": 2,
  "anchor_sources": [
    {"source_id": "archive-a"},
    {"source_id": "archive-b"}
  ]
}
```

Put each anchor RPC URL in its own environment variable. Pass only the mapping
names to capture:

```bash
python3 plugins/lazarus/scripts/lazarus.py capture \
  --plan capture-plan-v2.json \
  --rpc-url "$PRIMARY_RPC_URL" \
  --anchor-rpc-env archive-a=ARCHIVE_A_RPC \
  --anchor-rpc-env archive-b=ARCHIVE_B_RPC \
  --out fixture-v0
```

Each mapping has the exact form `SOURCE_ID=ENV_VAR`; only the first `=` is the
separator. Source IDs match `^[a-z][a-z0-9_.-]{0,127}$`. Environment names
match `^[A-Za-z_][A-Za-z0-9_]{0,127}$`. The mapping's source set must equal the
plan's set, with one mapping per source. Lazarus reads only the named,
non-empty variables after set equality passes. Anchor URL values therefore do
not enter argv, output, diagnostics, plans or fixture bytes.

Plan v1 has no anchor sources and accepts no anchor mappings. The legacy
primary `--rpc-url` remains the provider for header bracketing, declared RPC
requests and state proofs; it is not treated as an anchor automatically.

## Capture boundary

All clients share the plan's request, response-byte, component-byte,
total-byte and elapsed-time limits. For each source, Lazarus uses the existing
redirect-refusing JSON-RPC transport to call `eth_chainId` and
`eth_getBlockByNumber` with the fixed block quantity and `false`. The returned
chain must be `0x1`; the returned height and hash must match the plan.

One record contains only the source ID, injected local UTC wall-clock time,
the fixed method and parameters, and the returned chain ID, height and hash.
Records are canonical JSONL sorted by source ID. The manifest binds
`anchors.jsonl` by length and SHA-256, and whole-fixture verification requires
its source set to cover plan v2 exactly.

Before finalisation, capture scans every staged component against the union of
the primary URL and headers plus every anchor URL. It then verifies the whole
fixture and installs the staged directory with an atomic no-replace rename.
Mapping, transport, chain, height, hash, schema, limit, secret or verification
failure leaves neither a destination nor a staging directory.

## What the result means

| Output | Established | Not established |
| --- | --- | --- |
| `anchor-sources-declared: N` | The successful capture used a plan with N mapped sources. | That the labels identify different owners or infrastructure. |
| `chain-anchor-records: N` | N digest-bound records cover the plan and agree with the verified header. | Ethereum consensus, finality or canonical-chain membership. |
| `canonical_chain_claim: false` | Lazarus declines the canonical-chain claim. | A negative claim that the header is non-canonical. |
| `provider_independence_claim: false` | Lazarus declines the provider independence claim. | A negative claim that the sources share infrastructure. |

Anchor records do not enter the existing `proof_backed`, `header_bound` or
`recorded_rpc` evidence counts. Their own count prevents matching provider
answers from being promoted into an EIP-1186 proof or an independence claim.

## Offline example

The checked-in
[`multi-provider-anchor-v0`](../examples/multi-provider-anchor-v0) fixture uses
synthetic local material and two matching source records. It needs no RPC:

```bash
python3 plugins/lazarus/scripts/lazarus.py verify \
  plugins/lazarus/examples/multi-provider-anchor-v0
```

Its fixture digest is
`188eb293ac1de8036ff4be861e339fe5757b51995c88e8ea1afcfa498134a72e`.
Verification prints `chain-anchor-records: 2` while both claim booleans remain
false in the verification report.
