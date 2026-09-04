# Alexandria schemas

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
<!-- marketplace-context:end -->

Step 2 defines three raw-release contracts:

- `capture-plan-v1.schema.json` declares local source files, source references,
  capture scope, finality and evidence boundaries. `proof-backed-state` stays
  a declared `evidence_class` value; its guarantee is earned only after
  `verify` reruns Lazarus and confirms the claim stays within the proved block
  and targets;
- `coverage-v1.schema.json` declares counted source collections, explicit gaps
  and complete, partial, failed or unsupported status; and
- `archive-manifest-v1.schema.json` binds copied objects and captures to one
  release identity.

The standard-library verifier enforces the cross-field rules that JSON Schema
cannot express: canonical bytes, safe paths, exact digests, sorted entries,
component access and redistribution classes, capture-source references,
scope, finality and block-identifier semantics, JSON-pointer counts, gap
semantics and correction self-reference.

`release-statement-v1.schema.json` closes the unsigned in-toto Statement v1
shape emitted after offline verification. It binds the logical release and
component subjects to the Alexandria predicate's component metadata, capture
scope, coverage and gaps. The schema does not describe a DSSE envelope,
signature verification, publisher identity, provider completeness, consensus
finality or canonical-chain membership.

Step 3 adds `credit-event-v1.schema.json` and
`position-observation-v1.schema.json` for the narrow Tabularium view. The
`tabularium-view-v1.schema.json` manifest section binds both JSONL files,
registered mapping revisions, coverage reconciliation and row counts to the
verified raw release. Runtime checks also require row subjects, actions,
properties and mapping rules to agree with their declared chain and venue.

Step 4 adds `address-index-v1.sql`, the disposable SQLite layout, and
`address-query-v1.schema.json`, the stable query envelope. Index rows retain
derived release, raw release, component, capture and credit-row identities.
Runtime checks also cover the database application ID, schema version, logical
digest, exact release-backed contents, cumulative-row overlap and
coverage-to-empty rules.

`demo-plan-v1.schema.json` covers the repository-source pins and fixed query
used by the offline example. `demo-summary-v1.schema.json` covers its release
identities, logical index digest and artifact receipts. These are demonstration
contracts; production captures still enter through the ordinary capture-plan
schema.

Compound v3 Phase 0 adds `compound-v3-registry-v1.schema.json` for the pinned
28-market deployment catalogue and
`compound-v3-method-receipt-v1.schema.json` for the bounded archive, nested
call, ordered-storage and provider-reported finality gate outcomes. Runtime
checks bind these contracts to the exact upstream commit and raw RPC objects.

The resumable interval collector adds three more.
`interval-plan-v1.schema.json` declares the chain, deployment, proxy, block
interval, shard width, evidence classes and the named finality policy that
fixed the interval's end. `interval-checkpoint-v1.schema.json` covers the
working state a killed collection resumes from: the next shard, the last
accepted block and hash, and each journal's committed byte offset. It is not
release truth and no release names it. `interval-receipt-v1.schema.json`
covers what a collected interval turns out to hold: its code-hash-bound
implementation epochs, its shards with their status and record counts, and
what a second provider said about it. Runtime checks bind a checkpoint to its
own plan's digest and refuse a shard outside it.

The interval release itself enters through the ordinary capture plan. Its
components are one JSON journal per evidence class, format
`alexandria-interval-journal/v1`, each carrying the plan's interval and one
record per preserved exchange under `/records`, plus the interval receipt, the
reconciliation record, the error receipts, the plan and the pinned registry.
Every coverage count is a JSON pointer into the component it describes, so
`ingest` refuses a count the payload does not carry.
