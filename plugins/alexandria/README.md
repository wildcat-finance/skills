# Alexandria

<!-- marketplace-context:start -->
## In one line

Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend.

**Try something else when.** Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay.

**Current frontier.** Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented.

**Next Fiat job.** Use /hexaemeron:fiat to build the first resumable Ethereum USDC interval collector with implementation-epoch discovery, bounded shards, a second-provider reconciliation path, explicit finality and offline raw-release verification. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

An offline tool for digest-bound lending-data releases.

Alexandria keeps heterogeneous lending-protocol captures unchanged. It binds
each capture to explicit scope and coverage, derives a narrow Tabularium credit
view and supplies that view to Probitas through a disposable index. Alexandria
is an archive and data source, not a lending venue or underwriting system.

## Complete prototype

Alexandria can ingest raw releases, derive verified credit views, rebuild an
address index and query it:

```bash
python3 scripts/alexandria.py --help
python3 scripts/alexandria.py ingest --plan capture-plan.json --output release
python3 scripts/alexandria.py verify release
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

Goldfinch and Clearpool releases can now produce deterministic Tabularium
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
demonstration runs that complete path from the existing Goldfinch and Clearpool
source files through Probitas's five gates without network access:

```bash
output="$(mktemp -d)/credit-history-v0"
python3 examples/credit-history-v0/demo.py build --output "$output"
python3 examples/credit-history-v0/demo.py verify "$output"
```

Its expected receipts bind 522 derived events, 31 observations, an 11-event
Clearpool address query and 11 Probitas records. Goldfinch remains partial for
that query because the mapping declares 25 unsupported native records.

## Compound v3 Phase 0

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

## Architecture

The design separates:

1. unchanged raw objects named by SHA-256;
2. immutable release manifests with exact scope and coverage;
3. Tabularium-owned credit events and position observations; and
4. a disposable SQLite address index for Probitas queries.

A digest match will prove only that local bytes agree with the manifest. It
will not prove who published them, that a hosted source was complete or that
its reported block was canonical.

## Design record

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
- [`docs/compound-v3-harvest.md`](docs/compound-v3-harvest.md) pins Compound's
  official registry and specifies production capture, revision, checkpoint,
  reconciliation and acceptance rules. Phase 0 proves the required methods;
  the interval harvester remains a plan.
- [`docs/compound-v3-phase0-study.md`](../../docs/compound-v3-phase0-study.md)
  records the method study, and
  [`docs/compound-v3-phase0-runbook.md`](../../docs/compound-v3-phase0-runbook.md)
  records the shipped atomic step.
- [`docs/data-dictionary.md`](docs/data-dictionary.md) names the fields that
  cross raw releases, derived views, queries and Probitas.
- [`schemas/README.md`](schemas/README.md) states when each machine-readable
  contract enters the build.
- [`examples/README.md`](examples/README.md) states the offline demonstration
  boundary.

## Tests

From the repository root:

```bash
python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria
```

The implementation uses Python's standard library. The five core Alexandria
commands, Compound build/check commands and checked-in demonstrations reach no
network. Only the explicit Compound `capture` command performs network I/O.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
