# Alexandria study

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
<!-- marketplace-context:end -->

This is the historical staging study that selected Alexandria's design. Its
future tense and repository references describe the work before the prototype
was built. The public README and skill state what now ships.

## Problem statement

At study time, Probitas depended on several live lending-venue surfaces. Some
were less durable than the transactions they described. Three Euler subgraphs
were published but unserved during the work that built Probitas, TrueFi's
endpoint no longer answered, and Goldfinch wound down with its front end gone.
A live adapter is useful until an API changes, an indexer deallocates a
subgraph, or a protocol stops paying for infrastructure. Reconstructing the
same history later means archive-node work, new indexing code, or both.

Alexandria will preserve the material those adapters depend on and make the
preserved record address-queryable. It has two consumers with different needs:

- Tabularium needs unchanged venue-native input, exact capture scope and a
  durable source pointer for every interpreted credit row.
- Probitas needs an address-first history across venues and an account of which
  deployments, intervals and record kinds were checked. An empty query without
  that account is not a clean record.

The archive therefore has three separate products:

1. immutable raw objects, stored byte-for-byte and named by SHA-256;
2. a small release manifest that binds those objects to their capture scope,
   coverage, mappings and correction history; and
3. a narrow Tabularium credit view that can be indexed by address and translated
   into Probitas records.

The common view needs both events and observations. Borrowing and repayment
events answer what moved. They cannot establish the amount still owed at a
later block, whether a fixed-term balance passed maturity, or whether a
repayment closed every obligation. An observation records a value at a named
capture boundary and states how that value was obtained. The schema will not
turn that observation into a universal claim of default, cure or full
repayment.

### Working prototype

The prototype will be an offline Python 3 tool in a new `plugins/alexandria/`
directory. The plugin is the operator interface to the archive; Alexandria's
eventual bulk object store may live in a separate repository or service. The
tool will:

1. ingest declared raw files into a content-addressed object directory without
   changing their bytes;
2. write a deterministic release manifest with component digests, declared
   capture scope and coverage;
3. run versioned Tabularium mappings that produce `credit-events.jsonl` and,
   where the source establishes one, `credit-observations.jsonl`;
4. verify every object, derived row, selector, mapping identifier and coverage
   count with network access disabled;
5. rebuild a disposable SQLite address index from verified releases;
6. query one or more EVM account identifiers and return venue-qualified rows
   with their coverage; and
7. translate those rows into Probitas's existing `Record` and `Coverage`
   shapes while keeping each original venue identifier.

The checked-in demonstration will use two existing source shapes:

- `plugins/tabularium/examples/goldfinch-v0/source.json`, the complete
  203,679-byte hosted-indexer capture behind the 511-row Goldfinch release; and
- `plugins/alexandria/examples/credit-history-v0/sources/clearpool.json`, a real
  Ethereum log capture containing one Clearpool factory record and one pool's
  borrow and repayment logs.

Goldfinch exercises a full-dataset hosted-indexer capture. Clearpool exercises
an address-scoped archive-log capture and forces the coverage model to
distinguish a subject query from a deployment-wide harvest. The demo succeeds
when a clean checkout can ingest both, reproduce the same release and JSONL
bytes twice, rebuild the index, query a known address, emit Probitas-compatible
evidence, and reject tampered bytes, an unresolved selector or inflated
coverage.

The prototype also carries a Compound v3 harvesting plan. Compound is the
first large follow-on capture because the user wants as much of its record as
can be retained. The plan will enumerate Comet deployments and chains, source
boundaries, event and state families, pagination or block chunking, resumable
checkpoints, finality, rate limits, expected volumes, and acceptance checks.
It will define the work required to move from the current subject-filtered
Messari subgraph adapter to deployment-wide raw logs and named observations.
The prototype will not claim that a small test fixture is a Compound corpus.

## Prior art

### In the target repository

#### Probitas

`plugins/probitas/` is the reason to build Alexandria. Its public registry
names 13 venue surfaces and its live collector implements Wildcat and Morpho
Blue. Every other venue remains visible as a coverage gap. Alexandria adds an
explicit archive-backed route for reviewed Goldfinch and Clearpool releases;
it does not relabel those venues as live Probitas adapters.

`plugins/probitas/scripts/probitas_lib/evidence.py` supplies useful consumer
rules:

- every record has a transaction hash, URL or document reference;
- integer amounts remain strings on the wire and floats are refused;
- a record is scoped to a declared, linked or inferred address;
- coverage states `checked`, `empty`, `error`, `unimplemented` or
  `unconfigured`; and
- address-to-person inference, personal data and scores are outside the
  product.

Those classes are a dossier format, not an archive format. `Record.values` is
deliberately free-form, `Coverage.block_range` is free text, and coverage is a
runtime result over the whole venue registry. Alexandria needs a stronger
dataset scope. A venue missing from an Alexandria catalogue means "not
harvested"; Probitas decides whether that becomes `unimplemented`,
`unconfigured` or another visible gap in a particular run.

The Probitas adapters also show why a single amount field is insufficient.
Morpho liquidation records can have debt and collateral legs with separate
assets and scales. Goldfinch supplies position-like records for fixed-term
credit-line debt at a named snapshot.

#### Tabularium

`plugins/tabularium/` already implements the preservation rules Alexandria
should reuse:

- raw and interpreted records stay separate;
- canonical JSON and JSONL have owned ordering and encoding;
- source, capture and output files are bound by SHA-256 and byte count;
- every row records a source selector, adapter version and mapping rule;
- coverage counts both mapped and unsupported collections;
- offline verification rebuilds the interpreted bytes; and
- a correction produces a new release rather than changing the old one.

Its v1 schemas cover the first Goldfinch release rather than a settled common
model. `canonical-event-v1.json` fixes the source kind to
`the-graph-entity`, allows only borrowing and repayment, requires one asset
and amount, and fixes the adapter and mapping identifiers to Goldfinch.
`coverage-manifest-v1.json` fixes the evidence boundary and source collections
to the same capture. Alexandria should preserve that release unchanged and add
a new, protocol-neutral view rather than widening the meaning of its v1 files
in place.

Tabularium remains the owner of economic interpretation. Alexandria stores
and indexes a Tabularium-produced view. It does not decide that a native
`Repay`, `Liquidate` or credit-line balance means the same thing at every
venue.

#### Lazarus

`specs/lazarus.md` and the unmerged Lazarus format work at
`7b51fa09b7d57e0a70a08ce952b61fd7ae3ff241` define finite, fixed-block
Ethereum JSON-RPC fixtures, exact request matching and evidence classes for
proof-backed state, header-bound data and recorded RPC responses. Those
fixtures are suitable Alexandria raw components when a Tabularium observation
depends on historical state or a deterministic call result.

Lazarus does not define a universal lending payload. Its current plan is
Ethereum-mainnet-specific, finite and bound to one block. Proof verification
is still being built on another Fiat branch. Alexandria will accept a Lazarus
fixture by digest when present and will preserve its declared evidence class.
It will not require one for hosted-indexer captures or use Lazarus as a bulk
event store.

#### Mnemosyne and the preservation runbook

`specs/preservation-runbook.md` describes the route from archive node through
venue adapter and Tabularium to an Ariadne-bound release. The unmerged
`codex/mnemosyne-synthesis` branch at
`0d929a02b0bb29f91ba070a5f8a0ceb99d6be60a` adds a release index, storage
locations, retention and recovery drills while leaving each component's
format intact.

Alexandria implements the archive and catalogue parts of that plan. Mnemosyne
can remain the name for the combined release discipline, but it should not
grow a second peer catalogue. The eventual integration should point
Mnemosyne's release index and retention language at Alexandria's manifest and
locations.

#### Ariadne

Ariadne can later bind an Alexandria release manifest and its components to
build, test and review evidence. Its statement subjects are already
digest-addressed. Ariadne neither signs statements nor verifies an external
signature, so Alexandria v1 must say "digest-verified" rather than
"authentic" or "published by Wildcat". Signing and authenticated catalogue
channels are later work.

### Elsewhere in Wildcat Labs

The public `wildcat-finance/skills` repository is the eventual home for a
stable operator skill. This Fiat run targets `wildcat-skills-todo` so the data
contract and Probitas hand-off can change under review before porting.

Wildcat's own market history reinforces the need for venue-qualified rows.
Withdrawal cycles, delinquency, penalty accrual and cure carry meanings that
do not map directly to an overcollateralised lending pool's liquidation. The
common view must make comparison possible without erasing those differences.

### Outside the organisation

#### OCI descriptors

The OCI content descriptor is a useful model for one component entry. It
names a media type, digest and byte size, with optional URLs and annotations.
The OCI specification expressly permits descriptors to be embedded in other
formats. Alexandria can use that small vocabulary without treating lending
datasets as container images or using mutable registry tags as release
identities.

#### Canonical JSON

RFC 8785 defines the JSON Canonicalization Scheme for repeatable hashing and
warns about numbers outside IEEE-754 precision. Alexandria's Python prototype
will use a smaller owned subset: UTF-8, object keys sorted by Unicode code
point, compact separators, no duplicate keys, no floats, no NaN or Infinity,
and one trailing newline for stored JSON documents. On-chain quantities and
block values are decimal strings or bounded integers as their schema states.
The tool will not claim full RFC 8785 conformance without its number and string
serialization rules.

#### Object storage and IPFS

S3-compatible object storage supports versioning, explicit checksums and WORM
retention through Object Lock. Object Lock protects a retained object version;
it still permits another version at the same key. Alexandria should therefore
use digest-derived keys and treat any `latest` pointer as mutable convenience.
An ETag is not the archive digest because multipart uploads and storage
behaviour change its meaning.

IPFS content identifiers are useful secondary locations. A CID depends on the
codec, chunking and DAG construction and does not say where the content is
stored. Pinning improves availability but does not guarantee it. Alexandria
will keep SHA-256 of the original object bytes as its identity and may record
a CID plus pinning profile as one publication location.

#### Chain-agnostic identifiers

CAIP-2 gives a compact network identifier such as `eip155:1`; CAIP-10 extends
it to account identifiers. CAIP-10 leaves namespace-specific canonicalisation
to the implementation. Alexandria will keep the source spelling and a
namespace-canonical query key. For EVM accounts, the query key is a lowercase
20-byte hexadecimal address qualified by `eip155:<chain-id>`.

CAIP-19 can identify assets, but the specification remains in Review and asset
profiles vary. The first schema will retain chain, token contract when known,
symbol and decimals rather than making CAIP-19 the only asset identity.

#### Data Package and RO-Crate

Frictionless Data Package uses a descriptor plus resources with paths, media
types, byte sizes and hashes. It is good prior art for package ergonomics, but
its v1 resource examples and defaults admit MD5. Alexandria will require
SHA-256.

RO-Crate can export rich research metadata about organisations, software and
provenance. Its specification says the crate metadata need not be an
exhaustive inventory and points to archival packaging formats for fixity. It
is a possible generated export, not the v1 integrity manifest.

#### Parquet, DuckDB and SQLite

Parquet and DuckDB are suitable for large analytical copies. Parquet provides
columnar compression and DuckDB pushes filters and projections into Parquet
scans. Exact Parquet bytes depend on writer version, compression, row-group
size, column order and feature set. Shipping them in the first prototype would
add a dependency stack before the row contract has been reviewed across
protocols.

SQLite has a documented, stable single-file format and suits an application
that rebuilds one local catalogue and serves many local reads. It permits only
one writer at a time and should not sit on a shared network filesystem. The
prototype uses SQLite solely as a disposable address index. Canonical JSONL
and verified manifests remain the release truth. A later bulk release may add
pinned Parquet copies and direct DuckDB queries without changing that rule.

#### TUF and in-toto

TUF addresses signed mutable channels, rollback and freeze attacks. That is
useful for a future authenticated statement such as "the current trusted
Goldfinch release", but expiring metadata creates an ongoing operator duty.
It is unnecessary for identifying an immutable blob in the prototype.

An in-toto Statement can bind a typed predicate to subjects by digest.
Ariadne already uses that family. A later Alexandria predicate can name the
harvester revision, mapping versions, inputs, outputs and validation results.
It cannot prove that a hosted API was complete or that a response belongs to
the canonical chain unless the release supplies and verifies separate evidence
for those claims.

## Constraints, choices and non-goals

The starting ref is `main` at
`83fef6634a560860b930a532861dbfff8cbb3442` in
`laurenceday/wildcat-skills-todo`. The original repository worktree contains an
active Lazarus Fiat run and must remain untouched. This run uses its own
worktree and controller state.

The plugin must match the repository's portable shape: canonical skill and
README, `.agents` entrypoint, Claude and Codex manifests, plugin `AGENTS.md`,
schemas, standard-library scripts, fixtures and offline tests. Repository and
plugin instructions apply before each change.

The prototype uses Python 3's standard library. Stored JSON and JSONL have
owned serialization. Monetary values never pass through binary floating-point
arithmetic. Raw objects are read and hashed as bytes before any parsing. Safe
paths are relative to the release root, cannot traverse, and cannot resolve
through a symlink.

### Ambiguity choices

- **Alexandria is an archive with an operator skill.** Bulk datasets need not
  live in the skills Git history. The todo repository will hold the contract,
  code, tests and a small reproducible demonstration. An external object store
  or dedicated repository can hold production blobs under the same manifest.
- **Tabularium owns the derived row meaning.** Alexandria may run a registered
  mapping and index its output, but the mapping identifier and adapter version
  remain Tabularium concepts. A new venue requires economic review as well as
  shape validation.
- **Raw data has no universal payload schema.** A GraphQL response, Ethereum
  log batch, receipt set, Lazarus fixture and provider export may all be raw
  components. The manifest describes bytes, media type, source and access
  class without rewriting their body.
- **The common contract is narrow.** V1 covers credit events, position
  observations and coverage. It does not attempt to model every protocol
  entity, governance action, lender position or accounting entry.
- **Coverage is scoped to capture work.** `complete` means complete for the
  named network, deployment or subject set, interval, selectors, source
  capability and evidence boundary. It never means "all history everywhere".
- **Probitas keeps its venue registry.** Alexandria is a data source, not a
  venue. Archive-backed Compound rows remain `compound-v3`; absent Alexandria
  data stays visible under Probitas's normal coverage rules.
- **SQLite is an index, not evidence.** It may be deleted and rebuilt. Every
  returned row carries the release and component identities required to find
  the verified JSONL and raw source.
- **Lazarus is optional.** A proof-backed observation can point to a Lazarus
  fixture. Hosted-indexer and raw-log captures keep their weaker evidence
  classes rather than receiving implied proof.
- **Release identity is a digest.** `release_id` is
  `sha256:<hex>` over the canonical manifest body without the `release_id`
  field. Component entries carry SHA-256 and byte count. A mutable alias such
  as `latest` is never accepted where a release identity is required.

### Proposed v1 contracts

An archive release manifest will contain:

- schema and manifest versions;
- release ID and optional `supersedes` release IDs;
- venue, network and deployment or facility identifiers;
- producer and mapping revisions supplied as fixed inputs;
- raw and derived component descriptors with role, media type, SHA-256, byte
  count and safe relative path;
- capture scope: source kind, source locator class, deployment or explicit
  subjects, start and end heights, block identifiers where known, capture
  timestamp and finality policy;
- selectors or record families requested and returned;
- coverage status, counts, omissions, failed reads and access or redistribution
  classification; and
- an evidence class that states whether the boundary is provider-reported,
  header-bound, recorded RPC or proof-backed.

A credit event row will contain:

- schema version, deterministic row ID and row kind;
- network, venue, subject account, deployment and market or facility;
- an event family and venue-qualified action;
- zero or more amount legs, each with a role, asset identity, exact base units
  and decimals;
- transaction hash, log index, block height, block identifier and timestamp
  when established by the source; and
- provenance: release ID, raw component digest, source selector, mapping rule,
  adapter and adapter version.

A position observation row will use the same identity and provenance fields
and add:

- the observed property, such as principal outstanding or maturity;
- the exact value and unit or asset;
- the observation height and time;
- the method and evidence class; and
- an optional Lazarus component and record selector.

An observation says what the source established at that boundary. A Probitas
mapping may describe a venue-defined missed maturity when the venue supplies a
maturity and outstanding principal. Alexandria will not infer a universal
`defaulted`, `fully_repaid` or current balance field.

### Compound v3 follow-on capture

Compound v3 needs a deployment-wide collector rather than repeated
subject-filtered API calls. The harvesting plan will settle the following
before any production capture:

1. enumerate every official Comet deployment, chain, deployment block, base
   asset, configurator and rewards surface from Compound's published deployment
   records;
2. pin contract code and ABI sources used to decode each revision;
3. collect raw logs in resumable finalized-block chunks with block number,
   block hash, transaction hash, transaction index and log index retained;
4. cover supply, withdrawal, base principal changes, collateral transfers,
   absorption and collateral purchase events needed to distinguish borrowing,
   repayment and liquidation legs;
5. name the state observations required to answer outstanding debt, including
   the exact Comet calls or storage values and a fixed block for each snapshot;
6. record provider, request, response, retry, rate-limit, empty-range and failed
   range information rather than silently moving past an error;
7. reconcile event-derived accounts and totals against independent contract
   queries at sampled blocks without treating reconciliation as proof of chain
   canonicality;
8. partition raw objects by network, deployment and bounded block interval so a
   failed chunk can resume without rewriting accepted chunks;
9. specify correction and reorg handling through new manifests and
   `supersedes`; and
10. accept the harvest only when ranges are contiguous, requested selectors
    reconcile to returned counts, duplicate log identities are absent, every
    derived row resolves to raw bytes, and an offline index rebuild returns the
    same logical rows.

The plan will compare archive-node logs, Compound's official interfaces and
hosted indexers as acquisition routes. Raw chain logs are the preferred event
source because they outlive one indexer. A hosted source can still be retained
as an independently named component or gap-filling source. State observations
need a named block and evidence class; Lazarus can later package the finite
calls and proofs selected by that plan.

### Deferred work

- live network harvesting and production credentials;
- the production Compound v3 corpus;
- continuous ingestion, queues, leases and concurrent workers;
- an HTTP query service or hosted database;
- object-store upload, replication, retention monitoring and recovery drills;
- IPFS or OCI publication;
- Parquet and DuckDB analytical copies;
- Lazarus proof checking or replay beyond accepting a verified component;
- Ariadne predicates, external signatures, TUF channels and publisher identity;
- an Ethereum consensus trust root or an assertion of canonical-chain finality;
- migration to `wildcat-finance/skills` or a dedicated Alexandria repository;
- complete mappings for every Probitas venue;
- scores, underwriting conclusions, entity resolution, personal data and
  address-to-person claims; and
- redistribution of provider responses whose licence or terms do not permit
  publication.

## Design options

### Option 1: extend each Probitas adapter with a private fixture cache

Each live adapter could retain its responses and replay them later. This is the
shortest route to offline dossiers and reuses code already present. It leaves
no shared release identity, correction history or deployment coverage, and it
duplicates storage and verification rules across adapters. A subject fixture
also cannot answer a later query for an address that was not in the original
request. This option remains useful as an acquisition method, not as the
archive contract.

### Option 2: use Lazarus as the universal archive format

Lazarus records a finite set of Ethereum JSON-RPC requests and proof material
at a fixed block. It gives stronger evidence for selected state values than a
hosted indexer response. It does not fit GraphQL exports, protocol CSVs,
multi-block event corpora or non-Ethereum networks without changing its
purpose. Making it the outer container would also block Alexandria on the
proof-verifier work now in progress. Lazarus remains an optional component.

### Option 3: raw objects, a native manifest, thin Tabularium views and a
rebuildable SQLite index

Store each source file unchanged under its digest. A deterministic manifest
binds components, capture scope, coverage and mapping revisions. Tabularium
produces small event and observation views whose rows point into raw objects.
A local SQLite database indexes verified rows by account, venue, network and
time and can be discarded at any point.

This is the selected construction. It meets the Probitas query and negative-
space requirements while keeping raw preservation independent of a common
protocol schema. A reviewer can inspect the manifest and JSONL with ordinary
tools. The standard-library implementation can run offline. Parquet, DuckDB,
object storage and a service API remain compatible later projections rather
than prototype prerequisites.

### Option 4: a hosted analytical database as the source of truth

Load every protocol into a warehouse and expose SQL or an address API. This
would answer large queries quickly and could use existing indexer tables. It
adds authentication, migrations, backups, endpoint availability and database
semantics before the release contract is settled. A mutable database row also
does not preserve the raw response or explain which bytes supported an older
dossier. A hosted service may index Alexandria releases later, but it should
be rebuildable from them.

### Option 5: make OCI artifacts or IPFS CIDs the native format

Both provide useful distribution. OCI has typed descriptors and registry
tooling; IPFS has content-derived identifiers. Each also adds transport rules
that are unrelated to the lending record, and neither guarantees long-term
availability. Alexandria's manifest will carry ordinary SHA-256 descriptors
and optional locations so the same release can be copied to S3, IPFS, an OCI
registry or offline media without changing its identity.

## Risk register seed

- **False clean history.** A query can return zero rows from a partial or
  subject-scoped capture. The query result must include matching coverage and
  must not label the result empty unless the named scope contains that subject
  and the requested selectors.
- **Coverage inflation.** `complete` without a network, deployment or subject
  set, interval, selector set and boundary can be read as more than was
  captured. The schema requires each dimension and the verifier reconciles
  counts and intervals.
- **Semantic overreach.** A repayment, liquidation or debt decrease can be
  misreported as full repayment or default. Derived actions stay
  venue-qualified; conclusions requiring position state use separately
  sourced observations.
- **Selector drift.** A derived row can cite a valid digest but the wrong
  record inside that object. Mappings define deterministic selectors and the
  verifier resolves every selector against parsed raw data.
- **Wrong-byte verification.** A filename or object-store ETag can point at
  bytes other than those named by the release. Verification reads the actual
  file, checks byte count and SHA-256, and confines paths to the release root.
- **Mutable correction.** A mapping change can silently rewrite earlier
  history. Published object and release keys are immutable; corrections use a
  new release with `supersedes` and retain the earlier bytes.
- **Index drift.** SQLite rows can outlive or diverge from their release. The
  index is rebuilt only from verified manifests, records release and component
  IDs per row, and is never the only copy of evidence.
- **Chain reorganisation.** Heights alone do not bind a fork. Coverage records
  block identifiers when the source supplies them and states the finality
  policy. Provider-reported heights remain labelled as such.
- **Evidence-class inflation.** Recorded RPC, header-bound data and
  proof-backed state support different claims. The manifest and row preserve
  the source class; Alexandria does not promote one to another.
- **Raw-source restrictions.** Provider terms, credentials or personal data
  may make a response unsuitable for publication. Components need access and
  redistribution classifications. A manifest may describe a restricted object
  without publishing secret material.
- **Availability loss.** A digest detects changed bytes but does not keep a
  copy online. Production publication needs at least one independent mirror,
  retention receipts and recovery drills; the prototype makes no availability
  promise.
- **Publisher confusion.** A digest does not establish who issued it. The
  prototype verifies internal consistency only. Authenticated publisher claims
  require an external signature verifier and later channel policy.
- **Address aliasing.** CAIP-10 does not prescribe account canonicalisation.
  Namespace rules produce one query key while the source representation is
  retained for audit.
- **Amount corruption.** Large integers, decimals and multi-asset liquidation
  legs can round or collapse. Amounts remain exact decimal strings with asset,
  decimals and role; floats are refused.
- **Duplicate events.** Provider pagination, chunk overlap or reorg recovery
  can repeat a log. Stable row identities include network, transaction and log
  coordinates or a source-specific identity; duplicates fail verification.
- **Incomplete Compound enumeration.** A deployment or event revision can be
  missed before a long harvest starts. The capture plan pins official
  deployment sources and ABI revisions, and the release records unsupported
  chains, deployments and selectors.
- **Format drift.** A library upgrade can change Parquet or SQLite bytes.
  Neither is a v1 release identity. Canonical JSONL supplies the prototype's
  reproducible logical view; later columnar writers must pin versions and
  settings.
- **Resource exhaustion.** Malicious or damaged manifests can name huge files,
  deep JSON, excessive rows or path cycles. The tool applies file-size, row,
  nesting and string limits before indexing and fails without partial output.
- **Archive/service confusion.** A future API can be mistaken for the evidence
  source. Query responses must name immutable release IDs, and service state
  must remain disposable.

There are no smart contracts, custody paths, signing keys or production
network writes in the prototype. Security review should concentrate on file
confinement, parser limits, digest binding, selector resolution, coverage
truthfulness and query provenance.

## Glossary seeds

- **Alexandria:** the raw-object archive, release catalogue and query boundary
  described here; also the name of its operator plugin.
- **Raw object:** unchanged bytes received from a chain reader, indexer,
  provider export or other declared source.
- **Object digest:** `sha256:<hex>` over the exact raw object bytes.
- **Component descriptor:** a manifest entry naming a component's role, media
  type, byte count, digest and safe local path or publication locations.
- **Release manifest:** the canonical document that binds components to
  capture scope, coverage, mapping versions and supersession history.
- **Release ID:** SHA-256 of the canonical manifest body, excluding the ID
  field itself.
- **Capture scope:** the network, deployment or subject set, interval,
  selectors, source capability and evidence boundary a harvest attempted.
- **Coverage:** the machine-readable result of that attempt, including counts,
  omissions, failures and unsupported parts.
- **Coverage status:** `complete`, `partial`, `failed` or `unsupported` within
  the declared capture scope.
- **Negative space:** the distinction among a checked empty result, an
  uncovered venue, a failed capture and an unsupported record family.
- **Credit event:** a venue-qualified occurrence such as borrowing, repayment
  or liquidation, backed by a raw record.
- **Position observation:** a value established for a credit position at a
  named capture boundary, such as principal outstanding or maturity.
- **Amount leg:** one exact asset quantity with a role; a liquidation may have
  separate debt-repaid and collateral-seized legs.
- **Subject account:** the chain-qualified address whose conduct or position a
  derived row describes.
- **Source selector:** a deterministic pointer from a derived row to one record
  inside a raw object.
- **Mapping rule:** a versioned Tabularium identifier for the economic and
  structural transformation from a source record to a derived row.
- **Evidence class:** the declared support for a boundary or value, such as
  provider-reported, recorded RPC, header-bound or proof-backed.
- **Address index:** a disposable SQLite projection rebuilt from verified
  manifests and derived rows.
- **Publication location:** one place from which component bytes may be
  obtained; it is not the component identity or a promise of availability.
- **Supersession:** a new immutable release that names an earlier release it
  corrects or extends.
- **Retention receipt:** later evidence that an operator undertook to keep a
  copy for a named period; not implemented in the prototype.

## Sources

### Target repository

- Base `83fef6634a560860b930a532861dbfff8cbb3442`:
  `README.md`, `specs/probitas.md`, `specs/tabularium.md`,
  `specs/lazarus.md`, `specs/preservation-runbook.md`,
  `plugins/probitas/`, `plugins/tabularium/` and `plugins/ariadne/`.
- Mnemosyne synthesis, unmerged commit
  `0d929a02b0bb29f91ba070a5f8a0ceb99d6be60a`:
  `specs/mnemosyne.md`.
- Lazarus format work, unmerged commit
  `7b51fa09b7d57e0a70a08ce952b61fd7ae3ff241`:
  `plugins/lazarus/docs/study.md` and `plugins/lazarus/schemas/`.

### External specifications and official documentation

- OCI content descriptors:
  `https://github.com/opencontainers/image-spec/blob/main/descriptor.md`.
- OCI image manifests and artifact guidance:
  `https://github.com/opencontainers/image-spec/blob/main/manifest.md`.
- RFC 8785, JSON Canonicalization Scheme:
  `https://www.rfc-editor.org/rfc/rfc8785.html`.
- Amazon S3 Object Lock:
  `https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html`.
- Amazon S3 object integrity and checksums:
  `https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html`.
- IPFS content addressing:
  `https://docs.ipfs.tech/concepts/content-addressing/`.
- IPFS persistence and pinning:
  `https://docs.ipfs.tech/concepts/persistence/`.
- CAIP-2 blockchain identifiers:
  `https://standards.chainagnostic.org/CAIPs/caip-2`.
- CAIP-10 account identifiers:
  `https://standards.chainagnostic.org/CAIPs/caip-10`.
- CAIP-19 asset identifiers:
  `https://standards.chainagnostic.org/CAIPs/caip-19`.
- Apache Parquet file format:
  `https://parquet.apache.org/docs/file-format/`.
- Apache Parquet compatibility notes:
  `https://parquet.apache.org/docs/file-format/versions/`.
- DuckDB Parquet support:
  `https://duckdb.org/docs/stable/data/parquet/overview`.
- SQLite single-file format:
  `https://www.sqlite.org/onefile.html`.
- SQLite appropriate-use guidance:
  `https://www.sqlite.org/whentouse.html`.
- Frictionless Data Package and Data Resource:
  `https://specs.frictionlessdata.io/data-package/` and
  `https://specs.frictionlessdata.io/data-resource/`.
- RO-Crate 1.3 structure:
  `https://www.researchobject.org/ro-crate/specification/1.3/structure.html`.
- The Update Framework specification:
  `https://theupdateframework.github.io/specification/latest/`.
- in-toto Attestation Framework, Statement v1:
  `https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md`.
