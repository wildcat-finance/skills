# Alexandria data dictionary

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
<!-- marketplace-context:end -->

Alexandria keeps raw release truth, derived release truth and disposable query
state separate. JSON integers represent counts only. On-chain amounts and block
coordinates remain decimal strings where their schemas require exact values.

## Raw release

| Field | Meaning |
| --- | --- |
| `release_id` | SHA-256 identity of the canonical manifest with this field omitted |
| `components[].sha256` | SHA-256 of the unchanged object bytes |
| `components[].object_path` | Confined digest-derived path inside the release |
| `captures[].source` | Non-secret source kind, locator class and reference |
| `captures[].scope` | Venue, chain, deployment, subjects and snapshot or block interval |
| `captures[].coverage` | Counted collections, status, gaps and unsupported collections |
| `supersedes` | Earlier release corrected by this release; it does not mutate the earlier bytes |

`complete` applies only to the declared scope and collections. A digest match
does not establish publisher identity, provider completeness or canonical-chain
finality.

## Derived release

| Field | Meaning |
| --- | --- |
| `derivation.source_release_id` | Verified raw release used by every mapping |
| `derivation.mappings[]` | Venue, adapter version, mapping revision and reconciliation counts |
| `credit-events.jsonl` | Canonical, deterministically ordered venue-qualified credit events |
| `credit-observations.jsonl` | Canonical position readings at named observation boundaries |
| `id` | Hash of stable native identity, row kind and mapping rule; exposed as `row_id` by queries |
| `provenance.component_sha256` | Raw object containing the selected source record |
| `provenance.source_selector` | Exact native record selector |
| `provenance.context_selectors` | Other native records needed to interpret the row |
| `provenance.mapping_rule` | Registered rule which assigned the row meaning |

Events do not imply a current balance, default or complete repayment.
Observations apply only at their recorded boundary.
Economic row content is checked separately when active releases carry the same
stable ID. Equivalent rows collapse to one query result; conflicting rows are
refused.

## Address index and query

The SQLite database is rebuilt from verified derived releases and is not
release evidence. Its `logical_digest` covers stable logical rows rather than
SQLite page bytes. A query returns:

- `events` and `observations`, each wrapped with its derived `release_id` and
  `row_id` while retaining full raw provenance inside the row;
- `coverage` per venue and chain, including `covered`, `partial` or `uncovered`,
  record counts and whether zero rows may be treated as empty; and
- the normalized request and the exact release set represented by the index.

## Probitas translation

Alexandria-backed Probitas records retain the source venue, chain, action,
amounts, transaction or document source, and Alexandria release, capture,
component and row identities. The translation expands the Probitas venue
registry to 13 coverage rows in the current public prototype. A venue absent
from the index remains `unconfigured` or `unimplemented`; it is not presented
as clean.

## Demonstration receipts

`demo-plan.json` pins repository source paths and their SHA-256 values. It is
materialized into a normal capture plan before ingestion. `expected-query.json`
records stable query row IDs, coverage and the output digest.
`expected-probitas.json` records stable evidence and dossier digests, record
counts, venue distribution, coverage distribution and all five gate results.
`summary.json` binds those artifacts to raw and derived release identities,
the logical index digest and every release-truth file digest.
