# Alexandria schemas

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Ordinary builds now emit `alexandria-interval-receipt/v2`, which attributes each preserved proxy log to an implementation epoch by block, transaction index and log index, and `check` re-derives every owner offline; reconciliation still compares a log without its transaction index, so a second provider that reports a different index for the same log records `agreed`.
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

The resumable interval collector has plan, checkpoint and receipt contracts.
`interval-plan-v1.schema.json` declares the chain, deployment, proxy, block
interval, shard width, the evidence classes the plan collects and the named
finality policy that fixed the interval's end. The evidence classes are a
non-empty subset of `boundary-blocks`, `logs` and `traces` in the plan's own
order: the collector requests only those, opens one journal per declared
class, and refuses an empty list, a duplicate or an unknown name by name. The
finality boundary is a block number and the hash it carried: the collector
reads that block by number and refuses a different hash, then under
`finalized` or `safe` requires the tag's number to be at or above it, so the
plan survives the tag advancing and fails only when its boundary block leaves
the chain.

A second plan format, `interval-plan-v2.schema.json` (format
`alexandria-interval-plan/v2`), replaces the single `proxy` address with a
non-empty, duplicate-free `subjects` array of up to 4096 declared addresses.
Every other field is unchanged. The collector filters `eth_getLogs` and
`trace_filter` by the whole declared array rather than one address, accepts a
log from any declared subject and refuses one from outside the set, and
attributes each preserved log to the epoch of its own subject. The epoch
table then carries one list per subject rather than one list for the whole
interval. Each tiles from that subject's own first in-interval position
through the interval's end. `MAX_EPOCHS` bounds each subject's own list
rather than their sum, and a subject whose extent starts after the interval
end carries no list at all. A v1 plan validates exactly as before and still
means one subject.

Either plan format may carry one optional field, `shards_per_component`, an
integer from 1 to 4096. It splits each shard-class journal (`boundary-blocks`,
`logs`, `traces`) into release components of at most that many shards each.
The component count is derived from the shard count and this field alone. Each
component holds a contiguous shard range, and their concatenation in shard
order is the journal. The boundaries therefore move only when the plan changes
and never because a re-collection returned one more record. The components are
named `<class>.<k>` in shard order. A plan without the field declares no
split. It yields one component per class under the class's own name, which is
how every release before this field was built. The `epoch-evidence` journal is
never split. `check` re-derives the ranges from the plan. It refuses a
component the plan does not derive, one missing, one holding a shard outside
its range and one holding a shard twice. It also refuses any component above
the release ceiling by name.

`interval-checkpoint-v1.schema.json` covers the
working state a killed collection resumes from: the next shard, the last
accepted block and hash, and each journal's committed byte offset. The
offsets cover the declared classes and a fourth journal, `epoch-evidence`,
which holds the opening reads the collector makes after the last shard: the
first block's header, the EIP-1967 slot at the first block and at each
upgrade block, the header at each upgrade block and the block before it, and
each implementation's runtime code. Those reads are staged under the virtual
shard index one past the plan's last, so a checkpoint whose next shard is one
past the plan says the shards are done and its `epoch-evidence` offset says
how many opening reads are committed. It is not
release truth and no release names it. A plan that declares
`shards_per_component` stages one file per class and component. Its checkpoint
is the one `interval-checkpoint-v2.schema.json` covers (format
`alexandria-interval-checkpoint/v2`) instead: the same fields, with `offsets`
and each history entry's offsets keyed by physical journal, `<class>.<k>` and
`epoch-evidence`, up to 128 of them. A v1 checkpoint is refused for a split
plan and a v2 one for an unsplit plan. An unsplit plan keeps writing v1 byte
for byte. The immutable
`interval-receipt-v1.schema.json` covers the original block-only receipt: its code-hash-bound
implementation epochs, its shards with their status and record counts, and
what a second provider said about it. A dispute names one of six kinds: the
three shard kinds, `boundary-hash`, `log-identity` and `transaction-order`,
and the three opening-read kinds, `first-block-hash`, `slot-word` and
`code-digest`, filed under the virtual shard index. Runtime checks bind a
checkpoint to its own plan's digest and refuse a shard outside it.

New builds use `interval-receipt-v2.schema.json`, format
`alexandria-interval-receipt/v2`. Each epoch adds `start_position` and exclusive
`end_position`, each containing a decimal-string `block_number` and integer or
null `transaction_index` and `log_index`. Both indexes are null together only
at a block edge. The first start is before all logs at interval start; the
last end is before all logs at interval end plus one. Interior boundaries carry
the upgrade's indexes, and non-null `upgrade` objects add `transaction_index`.
Block envelopes and their hashes remain, with the upgrade block shared by
adjacent envelopes.

V2 also requires ordered `log_attributions` rows containing `block_number`,
`block_hash`, `transaction_hash`, `transaction_index`, `log_index`, zero-based
`epoch_index` and `kind` (`proxy-log` or `upgrade-boundary`). Runtime checks
validate typed coordinates, strict log order, consistent transaction and block
hashes, exact positional tiling and agreement with freshly derived ownership.
They refuse first-block upgrades without prior implementation evidence,
multiple upgrades in a block and ordinary logs in an upgrade transaction.
An omitted logs class keeps its coverage gap and an empty attribution array.
The [standing design decision](../skills/alexandria/EVOLUTION.md#transaction-position-design-decision)
records why these limits remain. V1 verification preserves its original bytes,
identifiers and block-only meaning; it gains no v2 attribution guarantee.
[`examples/usdc-interval-epochs-v0`](../examples/usdc-interval-epochs-v0/README.md)
builds v2 releases and pins each log's owner.

A subject-set plan's release carries `interval-receipt-v3.schema.json`, format
`alexandria-interval-receipt/v3`, instead.
Its `epochs` is an object keyed by declared subject address rather than one list.
Each value is that subject's own epoch list under the v2 epoch and position rules, unedited.
A subject's first epoch opens at a block sentinel, as the single-proxy table's does at the interval start.
A subject with no extent inside the interval carries no key.
Every `log_attributions` row adds the required `subject` that emitted the log, and `epoch_index` counts within that subject's own list.
`check` refuses a v3 receipt under a single-proxy plan and a v2 receipt under a subject-set plan, by name.
A single-proxy plan keeps writing v2 byte for byte.
The epoch-table capture counts one collection per subject, `/epochs/<address>`, because a coverage selector has to resolve to a list.
A release therefore carries at most 256 in-interval subjects, Alexandria's collection limit, below the plan's 4096-subject limit.

The interval release itself enters through the ordinary capture plan. Its
components are one JSON journal per declared evidence class, format
`alexandria-interval-journal/v1`, each carrying the plan's interval and one
record per preserved exchange under `/records`, or one such journal document
per plan-derived component, `<class>.<k>`, when the plan declares
`shards_per_component`; the `epoch-evidence` journal of
opening reads, in the same format; and six more -- the interval receipt, the
`implementation-code` component carrying each implementation's runtime bytecode
under `/records`, the reconciliation record, the error receipts, the plan and
the pinned registry. Every coverage count is a JSON pointer into the component
it describes, so `ingest` refuses a count the payload does not carry. An
evidence capture whose plan names `finalized` or `safe` carries that finality
class with both boundary hashes bound; a `confirmations` plan and every derived
component stay `provider-reported`.
