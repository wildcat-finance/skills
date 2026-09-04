# Address index and Probitas hand-off

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
<!-- marketplace-context:end -->

Alexandria rebuilds a disposable SQLite index from one or more verified
derived releases:

```bash
python3 plugins/alexandria/scripts/alexandria.py index derived-release \
  --output alexandria.sqlite
python3 plugins/alexandria/scripts/alexandria.py query \
  --index alexandria.sqlite --address 0x...
```

Repeat the release argument to build one catalogue from several releases.
Corrections exclude a release when a later input supersedes its raw release
ID. The database stores canonical manifests and rows, exact derived and raw
release IDs, component digests, capture IDs and evidence classes. It is an
index of release truth, not release truth itself, and can be deleted and
rebuilt at any time.

The builder verifies every input before writing through a temporary sibling
file and refuses an output path inside any input release. The reader opens
SQLite read-only, runs its integrity check and
re-verifies every release at its recorded path. It reconstructs and compares
one release partition at a time, so a multi-release catalogue does not retain
every parsed JSONL row in memory together. This check binds the rows and the
active correction set to release content instead of trusting a digest stored
beside them. A moved, missing or changed release makes the index stale and the
query fails. SQLite file bytes need not match across builds; the logical digest
and query bytes do.

## Query contract

`--address` and `--venue` are repeatable. EVM addresses are lowercased and
deduplicated. `--chain` accepts a CAIP-2 `eip155` identifier. `--from-time` and
`--to-time` accept inclusive Unix seconds. Query output is canonical JSON in
stable order.

Every event and observation is wrapped with the verified derived release ID
and retains its unchanged row. The row holds the raw release ID, component and
component digest, capture, selectors, mapping rule and evidence class. Coverage
is reported per venue and chain as `covered`, `partial` or `uncovered`.
When active cumulative releases repeat one stable row ID with the same economic
content, the query returns the copy from the newest release timestamp and then
release ID. The index refuses a repeated ID whose content disagrees, and it
never treats an event and an observation as the same row.

`empty_allowed` is true only when complete capture scope covers every requested
address and time selector and the registered mapping has no unsupported source
records. A subject-scoped capture cannot clear another address. A block-range
capture cannot prove a timestamp-filtered empty result because Alexandria has
no sourced conversion for the range boundaries.

## Probitas

Probitas uses the archive only when the operator passes an explicit index:

```bash
python3 plugins/probitas/scripts/probitas.py collect \
  --entity "Acme" --address 0x... \
  --alexandria-index alexandria.sqlite --out evidence.json
```

Aave v4 and Clearpool event families become the existing Probitas `Record`
claims. Position state remains the neutral `position_observation` claim. Each
record retains venue, evidence class, row ID, derived and raw release IDs,
component digest, capture and mapping rule. An observation without a
transaction hash cites its Alexandria release and row as a document reference.

The bridge does not infer a person, default, full repayment or current balance.
It combines per-chain coverage conservatively: a venue is checked only when
every included chain is covered. An uncovered or partial result becomes a
Probitas gap, not `empty`, even when another chain returned rows. Registry
venues absent from the index remain visible as unharvested gaps. With no
`--alexandria-index`, Probitas follows its existing fixture or live adapter
path unchanged.
