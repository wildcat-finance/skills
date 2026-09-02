# Alexandria implementation runbook

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
<!-- marketplace-context:end -->

This is the historical staging runbook. Commit IDs and stacked branch rules
refer to `laurenceday/wildcat-skills-todo`; the public plugin is the audited
result, not a request to replay those branches.

This runbook builds an offline Alexandria prototype in five chained pull
requests. It starts at `main` commit
`83fef6634a560860b930a532861dbfff8cbb3442`. Each step enters on the audited
head of the previous step; later branches do not assume that an earlier pull
request has been merged.

The prototype preserves raw lending-protocol captures by digest, binds them to
scope and coverage, derives a small Tabularium credit view, rebuilds an address
index and supplies that evidence to Probitas. Production harvesting and storage
remain later work.

## Step 1: Scaffold the Alexandria plugin and contracts

**Goal.** Add the portable plugin shape, settled architecture documents and an
offline CLI boundary without claiming that the archive operations exist yet.

**Entry.** `main` at `83fef6634a560860b930a532861dbfff8cbb3442` with
the repository's existing root, Ariadne, Pandects, Probitas and Tabularium
test suites green.

**Exit.** `plugins/alexandria/` has matching skill and README files, portable
entrypoints, host manifests, licence, local instructions, standard-library CLI
scaffolding, schemas and examples directories, and committed copies of this
study and runbook. `specs/alexandria.md`, the root plugin catalogues and root
test expectations recognise Alexandria. The CLI prints help and rejects
unimplemented operations with a controlled exit. Root and Alexandria scaffold
tests pass.

**Files.** Create `plugins/alexandria/`, including `AGENTS.md`, `LICENSE`,
`README.md`, `.claude-plugin/`, `.codex-plugin/`, `skills/alexandria/`,
`scripts/alexandria.py`, `scripts/alexandria_lib/`, `schemas/`, `docs/`,
`examples/` and `tests/`. Create `.agents/skills/alexandria/SKILL.md` and the
host-neutral plugin entry. Add `specs/alexandria.md`. Update `README.md`, root
plugin manifests, `AGENTS.md` checks and root tests where the existing
distribution shape requires them.

**Tests.** Add scaffold tests for manifests, frontmatter, skill/README identity,
entrypoint targets, licence and `--help`. Run `python3 -m unittest discover -s
tests` and `python3 -m unittest discover -s plugins/alexandria/tests -t
plugins/alexandria`, plus the repository suites touched by catalogue changes.
The new plugin suite should contain at least 8 focused cases.

## Step 2: Preserve and verify digest-bound raw releases

**Goal.** Implement safe, deterministic ingestion and offline verification of
heterogeneous raw objects under a native Alexandria release manifest.

**Entry.** The audited Step 1 head with every Step 1 exit check green.

**Exit.** `alexandria ingest` reads a declared capture plan, copies exact source
bytes to digest-derived object paths, writes a canonical release manifest and
prints its release ID. `alexandria verify` checks the manifest identity,
component byte counts and SHA-256 values, path confinement, capture scope,
coverage shape and correction links without reading the network or changing
the release. Running ingest twice from the same fixed inputs produces
byte-identical objects and manifests. A fixture demonstrates both full-dataset
and subject-scoped coverage.

**Files.** Add archive-manifest, capture-plan and coverage schemas under
`plugins/alexandria/schemas/`; implement canonical JSON, byte-digest, safe-path,
manifest, ingest and verifier modules under
`plugins/alexandria/scripts/alexandria_lib/`; add small source fixtures and
capture plans under `plugins/alexandria/tests/fixtures/`; extend CLI and docs.

**Tests.** Cover exact-byte retention, repeat builds, manifest identity,
component size and digest checks, duplicate JSON keys, floats, integer and
nesting limits, traversal, absolute paths, symlinks, digest-key mismatch,
partial output cleanup, inflated coverage, malformed capture boundaries,
unknown evidence classes and `supersedes` validation. Exercise `verify` with
network APIs disabled and the release tree read-only. The Alexandria suite
should add at least 35 cases and all entry suites must remain green.

## Step 3: Derive the narrow Tabularium credit view

**Goal.** Produce protocol-neutral credit-event and position-observation rows
from versioned mappings while retaining exact source selectors and coverage.

**Entry.** The audited Step 2 head and a verified raw-release fixture.

**Exit.** Registered Goldfinch and Clearpool mappings read verified Alexandria
raw components and emit deterministic `credit-events.jsonl` plus an empty or
populated `credit-observations.jsonl` as their source permits. Rows support
multiple amount legs, chain-qualified subject accounts, venue-qualified
actions, optional transaction and block coordinates, and complete provenance.
The release manifest binds the derived files and mapping revisions. The
verifier resolves every selector back to the named raw object, rebuilds both
views and reconciles row, family, subject and coverage counts. No mapping
claims default, full repayment or a current balance.

**Files.** Add credit-event and position-observation schemas; add mapping
registry, row builders, Goldfinch and Clearpool mapping modules; add the
Goldfinch release and Clearpool fixture as test inputs by declared repository
path rather than duplicating large bytes; extend release schemas, verification,
CLI and adapter documentation.

**Tests.** Cover both protocols, hosted-indexer and archive-log evidence
classes, exact integer amounts, multi-leg schema admission, deterministic row
IDs and order, selector resolution, mapping version changes, duplicate record
identity, unsupported source collections, subject-scoped coverage, corrupted
native shapes, unknown actions and refusal of unsupported conclusions. Compare
repeat JSONL bytes and verify no source object changes. The Alexandria suite
should add at least 30 cases; Tabularium's full suite must also pass.

## Step 4: Rebuild the address index and serve Probitas

**Goal.** Make verified Alexandria releases queryable by address and usable as
an archive-backed Probitas source without collapsing venue coverage.

**Entry.** The audited Step 3 head with verified Goldfinch and Clearpool credit
views.

**Exit.** `alexandria index` rebuilds a disposable SQLite database from one or
more verified release manifests. `alexandria query --address` returns matching
events, observations and capture coverage in stable JSON order, with release
and raw-object identities on every row. Probitas accepts an explicit
Alexandria catalogue or index input, translates supported rows to its existing
`Record` and `Coverage` classes, retains `goldfinch` and `clearpool` as venue
IDs, and leaves unharvested registry entries visible as gaps. A zero-row result
is `empty` only when matching coverage includes the subject and requested
selectors.

**Files.** Add SQLite schema, index builder, query and Probitas translation
modules under Alexandria. Extend `plugins/probitas/scripts/probitas.py`, its
adapter runner or source configuration, documentation and tests without
changing the default live/fixture path. Update Alexandria CLI and operator
instructions.

**Tests.** Cover deterministic logical index contents, idempotent rebuilds,
multiple releases, superseded releases, case-normalised EVM addresses,
multi-address queries, venue and interval filters, index tampering, stale
release references, partial coverage, false-empty refusal and Probitas dossier
gates from archive-backed evidence. The Alexandria suite should add at least
25 cases and Probitas's full suite must pass.

## Step 5: Specify Compound harvesting and ship the offline demonstration

**Goal.** Finish the checked-in prototype, document the production Compound v3
harvest and prove the complete offline path from raw bytes to a Probitas
dossier.

**Entry.** The audited Step 4 head with raw ingestion, derived views, address
query and Probitas translation green.

**Exit.** A Compound v3 harvesting plan names official deployment sources,
chains, Comet revisions, event and observation families, chunking,
checkpoints, finality, provider reconciliation, error receipts, expected data
shape and acceptance checks. A checked-in Alexandria demo plan ingests the
Goldfinch and Clearpool sources, builds and verifies release manifests and
credit views, rebuilds the SQLite index, queries known addresses, runs Probitas
from Alexandria and verifies the rendered dossier with network access
disabled. Two clean temporary builds are byte-identical for every release
truth file and logically identical in SQLite. Changed source, manifest,
derived row, coverage or query provenance fails at the correct boundary.

**Files.** Add `plugins/alexandria/docs/compound-v3-harvest.md`, release and
operator documentation, `plugins/alexandria/examples/credit-history-v0/`, a
small demo driver, expected query and Probitas outputs, final schemas and data
dictionary. Update `specs/alexandria.md`, `specs/preservation-runbook.md`, root
README and the Alexandria and Probitas skill prose to describe only the
implemented path and its evidence limits.

**Tests.** Add one clean-machine demonstration test, one read-only and
network-disabled verification test, two-build digest comparison, expected
Goldfinch and Clearpool row and coverage counts, Probitas render and five-gate
verification, every component-tamper case, no-live-fallback checks and local
link validation. Run every repository suite named in root `AGENTS.md`, validate
all changed skill frontmatter, parse every changed JSON document and schema,
compile every changed Python file, and run the documented commands exactly.
The final Alexandria suite should exceed 100 focused cases.
