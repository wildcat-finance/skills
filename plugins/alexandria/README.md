![Alexandria](./assets/characters/alexandria.png)

# ALEXANDRIA

<!-- marketplace-context:start -->
## In one line

Alexandria preserves heterogeneous lending captures byte for byte, then exposes only the source-bound credit view a reviewed mapping can defend.

**Current frontier.** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.

**Next Fiat job.** Use /hexaemeron:fiat to run the Ethereum USDC collector against two live providers, read the interval's first block so a finalized scope binds both boundary hashes, and preserve the implementation code each epoch names so its code hash can be rechecked offline. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## START HERE

Use Alexandria when lending data may disappear, change shape, or need to be
checked later. It keeps the original source bytes, records exactly what was and
was not captured, and can derive only the reviewed rows its mappings support.

Today it can ingest and verify releases, produce unsigned evidence statements,
derive Aave v4 and Clearpool views, build a disposable address index, verify
one Compound v3 Phase 0 execution witness, and collect a declared Ethereum USDC
Comet block interval in bounded shards that resumes after a kill, rewinds after
a reorg, reconciles against a second provider and verifies offline.

It has not run that collector against a live provider. It covers one market of
the 28 at the registry pin, never reads an interval's first block, preserves no
implementation code, and makes no credit decision.

## PLACE IN THE COLLECTIVE

Alexandria is the preservation end of the credit-data path. Tabularium consumes
its raw releases and makes venue-qualified credit events; Probitas may use those
events in a counterparty dossier. Ariadne can bind a finished release to its
evidence. None of those later jobs authorises Alexandria to interpret missing
history or make an underwriting claim.

Lazarus is the neighbouring preservation specialist for a different boundary:
the finite historical Ethereum state and exact RPC traffic one application
test needs. Alexandria preserves lending datasets and derived source views.

Synkrisis is reserved for a different kind of evidence: validated observations
from several agent runs. Its present command surface builds a cohort and infers
findings over one, and it cannot reinterpret an Alexandria release or authorise
a new capture.

Alexandria keeps heterogeneous lending-protocol captures unchanged. It binds
each capture to explicit scope and coverage, derives a narrow Tabularium credit
view and supplies that view to Probitas through a disposable index. Alexandria
is an archive and data source, not a lending venue or underwriting system.

## HOW IT WORKS

Raw GraphQL responses and archive logs do not need one payload schema. Each
release stores the original bytes under their SHA-256, names the source, chain,
scope, finality class and counted coverage, and verifies offline. Aave v4 and
Clearpool releases can then produce a narrow Tabularium view without turning
the archive itself into an interpretation layer.

The Compound v3 Phase 0 release pins 28 production Comet deployments at one
upstream commit and preserves a bounded old-and-recent Ethereum USDC RPC
corpus. Its offline checker binds archive access, nested calls,
transaction-start state, proxy implementation code, ordered storage writes and
a provider-reported finalized boundary. It is a one-provider method proof, not
an interval history or independent chain proof.

The SQLite address index is disposable. Every query rechecks its schema,
logical digest and exact release-backed contents before returning rows. The
explicit Probitas route keeps both venue and archive provenance and leaves all
unharvested registry venues visible as gaps.

## WHAT IT SHIPS

- the standard-library [`alexandria.py`](./scripts/alexandria.py)
  ingest, verify, statement, derive, index and query command;
- raw-release, release-statement, coverage, credit-row, query and
  demonstration schemas;
- registered Aave v4 and Clearpool mappings with exact source and context
  selectors;
- the offline [`credit-history-v0`](./examples/credit-history-v0/README.md)
  path through Probitas's five gates; and
- a checked-in [Compound v3 Phase 0 raw release](./examples/compound-v3-phase0-v0/README.md),
  separate explicit network capture command and pinned
  [production harvest specification](./docs/compound-v3-harvest.md).

## DAY TO DAY

**Developers.** Preserve a protocol response now, with its gaps and usage
restrictions, then rebuild the same release after the endpoint is gone.

**Security and audit.** Check that every derived row resolves to the raw object
and mapping rule that assigned its meaning. An unknown implementation or
selector stays unsupported.

**Finance.** Query a counterparty address across the archived venues without
letting an unharvested venue read as clean history.

## COMPLETE PROTOTYPE

Alexandria can ingest raw releases, derive verified credit views, rebuild an
address index and query it:

```bash
python3 scripts/alexandria.py --help
python3 scripts/alexandria.py ingest --plan capture-plan.json --output release
python3 scripts/alexandria.py verify release
python3 scripts/alexandria.py statement release --output release-statement.json
python3 scripts/alexandria.py derive release --output derived-release
python3 scripts/alexandria.py verify derived-release
python3 scripts/alexandria.py index derived-release --output alexandria.sqlite
python3 scripts/alexandria.py query --index alexandria.sqlite --address 0x...
```

Ingest copies the declared raw bytes into SHA-256-derived paths and writes one
canonical manifest. Verification checks the release identity, every byte count
and digest, confined paths, component access and redistribution classes,
capture source, scope, finality, evidence class, counted coverage, declared
gaps, correction links and exact release-tree membership without using the
network or changing the release. Repeating an ingest from fixed inputs
produces the same objects, manifest and release ID.

For `proof-backed-state`, verification also reconstructs the embedded Lazarus
fixture by digest, reruns its offline verifier and bounds the capture to the
proved block and targets. This earns the class instead of trusting its label.

The `statement` command first performs that complete offline verification. It
then projects the logical release and every manifest component into a
canonical unsigned in-toto Statement v1 and writes it atomically outside the
release. The predicate preserves component metadata and each capture's scope,
coverage status and counts, unsupported collections and gaps. It contains one
passed offline-verification claim bound to the release digest and an empty
command list.

The statement has no DSSE envelope, cosign result or publisher identity.
Alexandria does not claim provider completeness, consensus finality or
canonical-chain membership. Ariadne can inspect the statement and run its core
gates, but the Alexandria predicate remains unregistered, signatures remain
unchecked, and gates 2 and 5 remain unchecked. See
[`docs/release-statements.md`](docs/release-statements.md) for the wire contract
and the exact demonstration.

Aave v4 and Clearpool releases can now produce deterministic Tabularium
credit events and position observations. Verification rebuilds both views from
the raw objects and reconciles provenance, mapping revisions and coverage.
Row IDs survive capture renames and raw-release corrections. Native repayment
amounts stay labelled as source amounts because neither input splits them into
principal and interest.

The SQLite index is disposable. Each build starts from verified derived
releases and refuses to write inside them. Each query checks the exact SQLite
schema and logical digest, then matches every indexed partition to its
referenced release. Equivalent rows shared by cumulative releases appear once;
conflicting rows under one ID are refused. Queries return stable event,
observation and per-venue coverage JSON. Probitas opts into the archive with
`--alexandria-index`; its normal fixture and live adapter route is unchanged.

The checked-in [`credit-history-v0`](examples/credit-history-v0/README.md)
demonstration runs that complete path from the existing Aave v4 and Clearpool
source files through Probitas's five gates without network access:

```bash
output="$(mktemp -d)/credit-history-v0"
python3 examples/credit-history-v0/demo.py build --output "$output"
python3 examples/credit-history-v0/demo.py verify "$output"
```

Its expected receipts bind 522 derived events, 31 observations, an 11-event
Clearpool address query and 11 Probitas records. Aave v4 remains partial for
that query because the mapping declares 25 unsupported native records.

## COMPOUND V3 PHASE 0

The checked-in [`compound-v3-phase0-v0`](examples/compound-v3-phase0-v0/README.md)
release pins all 28 production Comet deployments from ten chains at Compound
commit `f766f51583c23acc33b2a7824654ef2029a96804`. It preserves exact JSON-RPC
requests and responses for one old and one recent Ethereum USDC transaction.
The offline checker binds the registry, proxy implementation and code, block,
transaction, receipt, call traces, transaction-start storage and ordered
`SSTORE` trace.

Generate the registry from a local checkout at the pinned commit, or rebuild
and check fixed local captures:

```bash
python3 scripts/compound_v3_phase0.py registry \
  --comet-repository <comet-checkout> --output registry.json
python3 scripts/compound_v3_phase0.py build \
  --input <captured-input> --output <release>
python3 scripts/compound_v3_phase0.py check <release>
```

Live capture is a separate, explicit network boundary. It reads the endpoint
only from `ALEXANDRIA_COMPOUND_RPC_URL` and does not preserve that URL or its
headers:

```bash
python3 scripts/compound_v3_phase0.py capture \
  --registry registry.json --corpus corpus.json \
  --comet-repository <comet-checkout> --output <captured-input>
```

This is a fixed method proof from one RPC provider, not an interval harvester,
independent finality evidence or a canonical Compound event release.

## ARCHITECTURE

The design separates:

1. unchanged raw objects named by SHA-256;
2. immutable release manifests with exact scope and coverage;
3. Tabularium-owned credit events and position observations; and
4. a disposable SQLite address index for Probitas queries.

A digest match will prove only that local bytes agree with the manifest. It
will not prove who published them, that a hosted source was complete or that
its reported block was canonical.

## DESIGN RECORD

- [`docs/study.md`](docs/study.md) records the research, selected construction
  and risk register.
- [`docs/runbook.md`](docs/runbook.md) divides the prototype into five chained
  delivery steps.
- [`docs/raw-releases.md`](docs/raw-releases.md) defines the ingest, identity,
  coverage and offline verification rules.
- [`docs/credit-view.md`](docs/credit-view.md) defines the registered mappings,
  row contracts and derived-release verification.
- [`docs/address-index.md`](docs/address-index.md) defines index rebuilding,
  queries, false-empty refusal and the Probitas bridge.
- [`docs/usdc-interval-collector.md`](docs/usdc-interval-collector.md) covers
  the resumable Ethereum USDC interval collector: its shard plan, its finality
  policy, its epoch binding, its reconciliation boundary and what its release
  does not establish.
- [`docs/compound-v3-harvest.md`](docs/compound-v3-harvest.md) pins Compound's
  official registry and specifies production capture, revision, checkpoint,
  reconciliation and acceptance rules. Phase 0 proves the required methods;
  the interval harvester remains a plan.
- [`docs/compound-v3-phase0-study.md`](../../docs/compound-v3-phase0-study.md)
  records the method study, and
  [`docs/compound-v3-phase0-runbook.md`](../../docs/compound-v3-phase0-runbook.md)
  records the shipped atomic step.
- [`docs/release-statement-study.md`](docs/release-statement-study.md) records
  the selected unsigned predicate, and
  [`docs/release-statement-runbook.md`](docs/release-statement-runbook.md)
  records its source-bound delivery step.
- [`docs/release-statements.md`](docs/release-statements.md) defines the
  emitted statement and its Ariadne and signing boundaries.
- [`docs/data-dictionary.md`](docs/data-dictionary.md) names the fields that
  cross raw releases, derived views, queries and Probitas.
- [`schemas/README.md`](schemas/README.md) states when each machine-readable
  contract enters the build.
- [`examples/README.md`](examples/README.md) states the offline demonstration
  boundary.

## TESTS

From the repository root:

```bash
python3 plugins/alexandria/tests/run_tests.py \
  --elenchus-report .elenchus/alexandria-unittest.json
```

Alexandria's own implementation uses Python's standard library. Verifying a
`proof-backed-state` capture loads the sibling Lazarus verifier from the same
checkout with Lazarus's pinned packages. The six core Alexandria commands,
Compound build/check commands and checked-in demonstrations reach no network.
Only the explicit Compound `capture` command performs network I/O.

## LICENCE

Apache-2.0. See [LICENSE](LICENSE).
