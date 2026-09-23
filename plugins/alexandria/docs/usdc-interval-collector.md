# The resumable Ethereum USDC interval collector

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Ordinary builds now emit `alexandria-interval-receipt/v2`, which attributes each preserved proxy log to an implementation epoch by block, transaction index and log index, and `check` re-derives every owner offline; reconciliation still compares a log without its transaction index, so a second provider that reports a different index for the same log records `agreed`.
<!-- marketplace-context:end -->

`docs/compound-v3-harvest.md` specifies the production harvester. This document
covers the part of it that now exists: one collector over one market, the
Ethereum mainnet Compound v3 USDC Comet at proxy
`0xc3d688b66703497daa19211eedff47f25384cdc3`, which has now been run against two
live providers and whose preserved interval is checked in.

## The four commands

```bash
python3 plugins/alexandria/scripts/usdc_interval.py collect --plan <plan> --staging <directory>
python3 plugins/alexandria/scripts/usdc_interval.py reconcile --plan <plan> --staging <directory> --provider-class <class>
python3 plugins/alexandria/scripts/usdc_interval.py build --plan <plan> --staging <directory> \
  --registry <registry> --created-at <timestamp> --output <release>
python3 plugins/alexandria/scripts/usdc_interval.py check <release>
```

`build` no longer takes `--epochs`. The epoch table used to be an operator's
file handed in at build time; it is now derived from bytes the collector read
and journaled itself, so there is nothing left for an operator to supply and
the argument is retired rather than deprecated.

`collect` and `reconcile` also accept `--registry <registry>`. A venue that
plans its opening reads from its deployment registry requires it; see
[per-subject epochs](#per-subject-epochs-under-an-immutable-code-venue).

`collect` and `reconcile` are the two network paths, and each reads its endpoint
from `ALEXANDRIA_COMPOUND_RPC_URL` alone. The endpoint reaches no file, no
receipt and no message. `build` and `check` are offline.

An optional bearer credential rides the hosted path alone: set
`ALEXANDRIA_RPC_BEARER` and the transport adds it as one `Authorization` header
on every request, over HTTPS only. It lives on that one transport instance,
never on a module constant, and it reaches no file, no receipt and no message
any more than the endpoint does.

A second, bounded path exists beside the hosted one: an explicit opt-in local
loopback path, for a node reachable only from this machine. Set
`ALEXANDRIA_RPC_ALLOW_LOOPBACK_HTTP=1` together with an
`ALEXANDRIA_COMPOUND_RPC_URL` whose host is the literal `127.0.0.1` or `::1`
-- not `localhost`, not a hostname that merely resolves there by DNS, and not
a differently-written form of the same address. That path carries no bearer,
ignores `HTTP_PROXY`/`http_proxy`, follows no redirect, and refuses every
other host, URL user information and malformed authority before opening a
connection. Any other `ALEXANDRIA_COMPOUND_RPC_URL` still falls to the hosted
path's own HTTPS-only rule.

Two historical demonstrations run the whole path with no network at all:
`examples/usdc-interval-v0/demo.py` over synthetic fixtures, and
`examples/usdc-interval-live-v0/demo.py` over the preserved bytes of a real
Ethereum mainnet interval. Their confined reconstruction paths preserve the
original v1 release identifiers. Ordinary `build` emits
`alexandria-interval-receipt/v2`; it has no public legacy-build option.
`examples/usdc-interval-epochs-v0/demo.py` demonstrates v2 offline: literal
owners over a synthetic upgrade block, a v2 rebuild of the live staging bytes
under its own identifier, and the refusals the positional rules require. Its
[proof](usdc-interval-epochs/proof.md) records the guard's failure on the
parent and the four production conformance reports.

## What a request carries

Every request carries exactly two headers: `Content-Type: application/json` and
a constant `User-Agent` of the form `alexandria-usdc-interval/<package
version>`, built at import from the plugin manifest. Two of the five providers
the study probed answer HTTP 403 to Python's default `User-Agent`, so a
constant one is the difference between a run and a refusal.

Every request over the hosted path also carries an `Authorization` header once
`ALEXANDRIA_RPC_BEARER` is set; the local loopback path never adds one, and
refuses to build at all if one is present. No other header value comes from
the environment, and there is no argument or plan field that adds one. Neither
the bearer token nor the endpoint reaches a log, a receipt, an error message
or any file the collector, reconciler or builder writes: the environment
supplies both, and the token reaches exactly one HTTP header on the request
that needs it.

A release names the provider by class, not by operator. The plan carries a
non-secret `provider.class` string, such as `archive gateway, public tier, no
trace methods`, and that string is what reaches every error receipt, every
reconciliation record and every evidence scope's source reference. A hostname
would be a credential-shaped value in a durable file. A class carries what a
reader needs: which methods the provider served and which it refused.

## The shard plan

An `alexandria-interval-plan/v1` document names the chain, the deployment, the
proxy, the inclusive block interval, the shard width, the evidence classes and
the finality policy. The planner tiles the interval with ordered,
non-overlapping shards, at most 4,096 of them and at most 50,000 blocks each,
and refuses a reversed, empty, zero-width or unbounded interval by name.

The plan also declares its evidence classes: a non-empty subset of
`boundary-blocks`, `logs` and `traces`, in the order the collector requests
them. A shard asks one question per declared class -- the block at its end, the
proxy's logs across its range, the traces of calls into the proxy across the
same range -- and the collector issues no request and opens no journal for a
class the plan omits. An omitted class is not silence: the release names it as a
coverage gap on every evidence scope, with the reason it was not preserved. A
plan that omits `boundary-blocks` is refused outright, because every shard is
checkpointed by its boundary block's hash.

Declaring the classes in the plan is what makes a `traces` omission a stated
scope rather than a provider's limitation quietly inherited. Every request
identifier is derived from the shard index and the evidence class, so an
interrupted run and a clean run ask for the same bytes.

## Splitting a journal across components

Every staging journal and every release component is capped at 67,108,864
bytes. The two ceilings are `MAX_JOURNAL_BYTES` in `alexandria_lib/interval.py`
and `MAX_RAW_COMPONENT_BYTES` in `alexandria_lib/release.py`. A long interval's
logs can outgrow that, so a plan may declare `shards_per_component`, an integer
from 1 to 4,096. Each shard class's journal is then kept and released as one
component per contiguous range of at most that many shards. The components are
named `<class>.<k>` in shard order: `logs.0`, `logs.1` and so on. The component
count is derived from the shard count and that one field, so the boundaries are
fixed by the plan and move only when the plan changes. A byte-driven split
would move them whenever a re-collection returned one more record. The release
would then stop being reproducible from its plan.

The staging tree carries the same partition. It holds one file per class and
component, each under `MAX_JOURNAL_BYTES` on its own while the class's logical
journal may pass it. Its checkpoint is in the `alexandria-interval-checkpoint/v2`
format, with offsets keyed by those files. A record no single file can hold
still refuses where it would be written. Resume, reorg rewind, reconciliation,
the opening reads, `build` and `check` all read the components in shard order,
one file at a time. Nothing joins them into one oversized file. The
`epoch-evidence` journal is never split, because its records sit under the
virtual shard index rather than in any shard range.

A plan without the field declares no split. It produces exactly one component
per class under the class's own name, as every release before the field did,
so the preserved demonstrations verify unchanged. `check` re-derives the
ranges from the plan alone. It refuses a component the plan does not derive, a
component the release lacks, one holding a shard outside its range, one
holding a shard twice, and one whose coverage does not name the shards it
holds. It also compares every component's byte count in the manifest with the
ceiling and refuses one above it by name. Each split component's scope binds
the whole interval's two boundary hashes, because those are the hashes the
collector read. Its coverage names which shards and blocks the component holds
and says the journal's other components hold the rest.

## The opening reads

After the last shard commits, `collect` makes one more pass, journaled and
checkpointed exactly like a shard: it reads the interval's first block, the
EIP-1967 implementation slot at that block and at each upgrade block, the header
at each upgrade block and the block before it, and each named implementation's
runtime code.

These reads are staged as a fourth journal class, `epoch-evidence`, under the
virtual shard index one past the plan's last. A checkpoint whose next shard is
one past the plan therefore says the shards are done, and its `epoch-evidence`
offset says how many opening reads are committed, so a run killed inside the
opening pass resumes into it rather than restarting the interval.

Two things follow. The interval's start hash is now a value the collector read,
so a scope can bind both boundary hashes. And the implementation code is now
bytes in the tree, so an epoch's code hash can be re-derived rather than
trusted.

## What a finality class now says

No Compound source defines a finality depth. The plan names one of `finalized`,
`safe` or a stated confirmation depth, pins the boundary block's number and the
hash it carried, and the collector reads that block by number before it asks for
a shard. A different hash for the same number is a boundary that left the chain,
and the run refuses by name. Under `finalized` or `safe` it then reads the tag
and requires the tag's number to be at or above the pinned boundary, so a plan
survives the tag advancing and fails only when its own boundary block goes.

This is the rebind. Every evidence capture used to carry finality class
`provider-reported` whatever the plan named, because Alexandria requires a
`safe` or `finalized` block-range scope to bind both boundary hashes and the
collector read only each shard's end block. The opening reads supply the missing
one. A plan naming `finalized` or `safe` now earns that class on each evidence
capture's scope, with the interval's start hash and its end hash both bound; a
`confirmations` plan keeps `provider-reported`, because a depth this collector
chose is not a class the chain reports, and it still carries both hashes. The
derived captures -- the epoch table, the code, the plan, the receipts, the
reconciliation record and the registry -- stay `provider-reported`, because they
are built offline from the journals rather than read from a chain.

What a `finalized` scope establishes is still bounded: that a provider answered
the finalized tag, and that both boundary hashes are the ones this collector was
given. It is not consensus finality and not canonical-chain membership.

## Implementation epochs are bound by code hash

`CometExt.version()` returns the constant string `0` in the pinned source, so it
cannot tell two implementations apart. An epoch is bound instead by the SHA-256
of its implementation's runtime bytecode.

`discover_epochs` takes all preserved proxy logs, including `Upgraded(address)`, the
EIP-1967 implementation slot read at each boundary and the runtime code read at
each implementation. V2 epochs tile transaction positions across the declared
interval with no gap or overlap. `build` reads the logs from committed shard
journals and the slot and code evidence from `epoch-evidence`, so the table is
derived from preserved bytes. A boundary with no slot read of its own
does not inherit the implementation beside it: it refuses. So do a zero-address slot, an empty code
read, a slot that is not a left-padded address, a log from another contract,
malformed upgrade topics, unordered logs, a log outside the interval and a
missing block hash. Where the log's announced implementation and the slot read
disagree, or the log's own block hash and the preserved block disagree, the
epoch table refuses rather than choosing.

The implementation slot and the `Upgraded(address)` topic are pinned constants
rather than computed values, because the standard library carries no keccak.
Both are attested by the Phase 0 capture preserved in this repository, and a
test binds them to it.

## Transaction-position ownership

Each v2 epoch adds `start_position` and exclusive `end_position`. A position
contains exactly `block_number`, `transaction_index` and `log_index`: a decimal
block string and non-negative integer indexes. Both indexes are null together
only for a block-edge sentinel, meaning before every log in that block. The
first epoch starts at the interval's first block; the last ends at the block
after the interval's inclusive end. Interior boundaries use the preserved
upgrade's transaction and log indexes, and adjacent epoch positions match.

The existing `start_block`, `end_block`, `start_hash` and `end_hash` describe
each epoch's block envelope. Adjacent envelopes share the upgrade block;
exclusive positions determine ownership inside it. A non-null `upgrade` also
carries `transaction_index`, and its coordinates match the epoch's start.

The receipt's `log_attributions` array records every preserved proxy log in
validated order. Each row contains `block_number`, `block_hash`,
`transaction_hash`, `transaction_index`, `log_index`, zero-based `epoch_index`
and `kind`. An ordinary log has kind `proxy-log`; the upgrade announcement has
kind `upgrade-boundary`. A log in an earlier transaction belongs to the preceding
implementation, and one in a later transaction belongs to the replacement.
The announcement records a boundary without claiming which implementation
executed it.

Missing, boolean, negative, malformed, duplicate, contradictory, unordered or
out-of-range coordinates refuse. Transaction and log indexes retain the
canonical JSON ceiling of 78 decimal digits, checked before conversion or
diagnostic formatting. Within a block, transaction indexes cannot
decrease and block-wide log indexes must increase; transaction indexes and
hashes must agree, as must block hashes. Three unsupported histories also
refuse: an upgrade in the interval's first block without prior implementation
evidence, more than one upgrade in a block, and an ordinary proxy log in the
upgrade transaction, whether before or after the announcement. Only the
`aave-v3` venue admits the third, under the order rule in its section below.
End-of-block slot reads and log order cannot establish intermediate execution
state.

A plan omitting logs keeps its omission gap and an empty attribution array.
It claims neither unpreserved log coverage nor the absence of unseen upgrades.
`check` re-derives the positions and ownership from preserved journals and
compares the complete attribution array. Rebinding a changed receipt to new
component digests does not make invented ownership pass.

The check result names `receipt_semantics` as `v1-block-only` or
`v2-positional`. V1 verification retains its block-only meaning and immutable
schema; a valid v1 release gains no positional guarantee. The reasons for the v2 format and
these refusals live in the [standing design decision](../skills/alexandria/EVOLUTION.md#transaction-position-design-decision).

## Per-subject epochs under an immutable-code venue

A venue module names its epoch model. `compound-v3` names `eip1967-proxy`, the
model every section above describes. `wildcat-v2` names `immutable-code` and
owns its opening reads and its epoch derivation, in
`alexandria_lib/venues/wildcat_v2.py`. Every path that plans, replays or
re-derives opening reads dispatches on the plan's venue first: `collect`,
`reconcile`, `build` and `check`. A subject-set plan under `compound-v3` and a
single-proxy plan under `wildcat-v2` both refuse by name before any request is
made.

The rule is one epoch per declared subject. The epoch names no upgrade, and
its implementation is the subject's own address. Its code digest is the
SHA-256 of the runtime code read at the epoch's first block. That block is the
later of the interval's start and the subject's own deployment block, which
the venue's pinned registry carries. The epoch runs through the interval's end
and opens at a block sentinel, so every log in its first block has an owner.
A subject deployed after the interval's end has no epoch and no row in the
table. Every evidence scope names it as outside the interval. A log from a
subject before its own first block refuses, because no epoch owns it.

One `wildcat-v2` subject has no creation block in the merged records: the
collateral init-code storage at `0xbbb998043a20a26828617769f37dc3980be25ebc`.
The rule below holds for any subject without one. `collect` reads its code at
the interval's start. With runtime code there, its epoch opens at the start
with that one read. With none, `collect` reads the interval's end. Empty code
there too means the subject has no extent inside the interval, and the
collection refuses by name with error receipt code `no-code-at-interval-end`.
Otherwise it bisects between a block it read as empty and a block it read
with code until the two are adjacent. The epoch opens at the second of that
pair. One subject costs at most two reads plus the base-2 logarithm of the
interval's length, rounded up.

The probes happen before the first shard request, so that refusal costs no
shard. A checkpoint cannot commit an opening read while a shard is
uncollected, so their bytes are held and written as the first `epoch-evidence`
records after the last shard. A run stopped among the shards asks them again.

This establishes an observed boundary inside the interval: empty code at one
block and runtime code at the next, both read and preserved. It does not
establish the contract's first creation. Code destroyed before the interval's
start, or between two blocks the bisection did not read, is not seen. The receipt's `first_code`
rows say which opening applied, `interval-start` or `observed-block`, and name
the pair. The registry capture names the missing deployment block as a gap
rather than guess it.
Every evidence scope does too, and says which opening applied, so an observed
block is never presented as a recorded one. `reconcile` asks the second
provider for every probe; a different answer is a `code-digest` dispute.
`check` replays the probes, re-derives the rows, and refuses rows the reads do
not give or a pair that does not bracket the epoch's first block.

A subject with a recorded creation block is never probed. Empty code at its
recorded first block means the registry is wrong, and the collection refuses
by name with error receipt code `no-code-at-recorded-block`.

The opening reads are those probes, then the interval's first header, one
header per distinct later first block, and each recorded in-interval
subject's `eth_getCode` at its own first block. This model issues no `eth_getStorageAt` and compares no log topic
with the ERC-1967 announcement. A subject's log carrying that topic is an
ordinary `proxy-log`. `reconcile` asks the second provider for every one of
these reads, header and code alike. A disagreement is recorded as
`first-block-hash` or `code-digest`.

Because the first blocks come from the registry, `collect` and `reconcile`
take `--registry <registry>` for this venue and refuse without it. The
registry is validated against the digest pinned in
`alexandria_lib/wildcat_registry.py` before any of it is read. `check`
validates the release's own `registry` component the same way before it
re-derives the table.

A subject-set release carries `alexandria-interval-receipt/v3`. Its `epochs`
is one list with a row per in-interval subject, `{"epochs": [...], "subject":
"<address>"}`, in ascending subject order. `check` refuses a repeated subject,
rows out of order and an undeclared subject. The list is one coverage
collection at `/epochs` whose count is its number of rows, so a release's
collections do not grow with its subjects and the plan's 4096-subject limit is
the bound. Every `log_attributions` row names the `subject` that emitted the
log, and its `epoch_index` counts within that subject's own list. Two subjects that emit in one block and one transaction each
reach their own epoch. `check` reports `receipt_semantics` as
`v3-subject-positional`. It refuses a v3 receipt under a single-proxy plan and
a v2 receipt under a subject-set plan.

The venue also contributes gaps to every evidence scope, and `check` refuses a
release that drops one. The first is the constructed-staging gap: the venue
module holds the set of `deployment` names it admits as preserved, and that
set is empty today. Every `wildcat-v2` release therefore says its staging
bytes are declared constructed rather than collected from a chain. The second
compares the HooksFactory's preserved `MarketDeployed` logs with the 80
markets the registry declares. A declared market deployed inside the interval
with no such log is named as a gap. So is a log naming a market the registry
does not declare, and a log that deploys a declared market at another block
than the registry records. A plan that omits the factory says the markets were
not compared.

A capture holds at most 256 gap sentences, so four kinds of gap are bounded:
subjects deployed after the interval's end, declared markets with no deploy
log, deploy logs at another block, and deploy logs naming an undeclared
market. Each kind names up to 16, and one further sentence per kind counts the
rest and the total. `check` re-derives the same sentences.

Every code read lands in the one `epoch-evidence` journal, which holds at most
67,108,864 bytes. From the registry's code lengths, `collect`, `reconcile` and
`build` refuse a subject set whose code cannot fit while the plan is
validated, before any request. The Wildcat V2 estate's 137 subjects need about
5.6 MB of it read once each. The estimate also charges a subject with no
recorded creation block its whole code at every probe it could need, which
makes about 6.0 MB over an interval of 4.1 million blocks.

## Per-subject epochs under the Aave V3 venue

`aave-v3` names `aave-v3-role-keyed`: its epoch model is chosen per subject by
the role the pinned registry records. The 172 subjects with a proxy role
(`pool-proxy`, `pool-configurator-proxy`, `aToken-proxy`,
`variableDebtToken-proxy`, `stableDebtToken-proxy`) follow the EIP-1967 slot
and their `Upgraded` positions. The other 184 have one immutable epoch whose
implementation is the subject itself and whose code digest is the SHA-256 of
the runtime code read at its opening block. `derive_epochs` in
`alexandria_lib/venues/aave_v3.py` builds the table from preserved reads alone.

The venue plans those reads itself, after the last shard, in an order the staged
logs fix: the plan's first block header; a header at each later opening block
and each upgrade block, in ascending order; the implementation slot of each
proxy at its opening block and at each block it announces an upgrade in; then
the runtime code of each subject and each implementation those slots hold, read
once per address at the first block an epoch needs it. An upgrade block's header
has to carry the block hash its `Upgraded` logs name. An `Upgraded` log from a
subject with an immutable role, or an upgrade shape the rules below refuse
without a read, refuses before any opening read is made. A plan whose opening
reads could exceed the one epoch-evidence journal refuses when the plan is
checked.

A subject opens at the later of the plan's start and the creation block the
registry records, at a block sentinel. A proxy opens with the implementation
its slot holds at the end of that block. Each later `Upgraded` log from that
proxy opens a new epoch at its own block, transaction index and log index, and
the slot read at the end of that block must equal the announced
implementation. A subject created after the plan's end has no epoch in it.
`MAX_EPOCHS` in `alexandria_lib/interval.py` bounds each subject's table; the
largest the registry records is the Pool's 11.

**The order rule.** Inside a subject's own upgrade transaction, an ordinary
log from that subject is owned by log index: before its `Upgraded`, the old
epoch; after it, the new one. The pinned source of `aave/aave-v3-core` at
`9630ab77a8ec77b39432ce0a4ff4816384fd4cbf` establishes it:

- `BaseUpgradeabilityProxy._upgradeTo` sets the implementation slot and then
  emits `Upgraded`, at
  [lines 44 to 46](https://github.com/aave/aave-v3-core/blob/9630ab77a8ec77b39432ce0a4ff4816384fd4cbf/contracts/dependencies/openzeppelin/upgradeability/BaseUpgradeabilityProxy.sol#L44-L46);
- `BaseImmutableAdminUpgradeabilityProxy.upgradeToAndCall` calls `_upgradeTo`
  and only then delegatecalls the new implementation, at
  [lines 69 to 77](https://github.com/aave/aave-v3-core/blob/9630ab77a8ec77b39432ce0a4ff4816384fd4cbf/contracts/protocol/libraries/aave-upgradeability/BaseImmutableAdminUpgradeabilityProxy.sol#L69-L77);
- `InitializableUpgradeabilityProxy.initialize` sets the slot without emitting
  `Upgraded`, at
  [lines 20 to 25](https://github.com/aave/aave-v3-core/blob/9630ab77a8ec77b39432ce0a4ff4816384fd4cbf/contracts/dependencies/openzeppelin/upgradeability/InitializableUpgradeabilityProxy.sol#L20-L25),
  which is why a proxy's first implementation is read from the slot.

Those lines are `aave-v3-core`'s, the source of `set-003`, which compiles two
of the seven reviewed codes and 101 of the 172 proxies. The other 71 compile
from `aave-dao/aave-v3-origin`, in five source sets. The pinned `source_match`
full record names the git blob of every file each set compiled, and each link
below is at a commit holding that exact blob. `BaseUpgradeabilityProxy.sol` is
blob `aec817cb346ac6b178a806394c33a8ecc2145ce1` and
`InitializableUpgradeabilityProxy.sol` is blob
`4b43fa6a87dd84be15fc77b3ea4b1a88350c4175` under both origin paths;
`BaseImmutableAdminUpgradeabilityProxy.sol` is blob
`252b4a4ba0c05dae0b28eb0d23f9a80fc2a8f7aa` under `src/contracts/misc` and
`06d2f82789af01b12e5df87e11ff5c259a5a2e35` under `src/core`. In every set,
`_upgradeTo` sets the slot and then emits `Upgraded`, `upgradeToAndCall` calls
`_upgradeTo` before its delegatecall, and `initialize` emits nothing.

| Source set | Proxies | `_upgradeTo` | `upgradeToAndCall` | `initialize` |
| --- | --- | --- | --- | --- |
| `set-003` | 101 | [core L44-L46](https://github.com/aave/aave-v3-core/blob/9630ab77a8ec77b39432ce0a4ff4816384fd4cbf/contracts/dependencies/openzeppelin/upgradeability/BaseUpgradeabilityProxy.sol#L44-L46) | [core L69-L77](https://github.com/aave/aave-v3-core/blob/9630ab77a8ec77b39432ce0a4ff4816384fd4cbf/contracts/protocol/libraries/aave-upgradeability/BaseImmutableAdminUpgradeabilityProxy.sol#L69-L77) | [core L20-L28](https://github.com/aave/aave-v3-core/blob/9630ab77a8ec77b39432ce0a4ff4816384fd4cbf/contracts/dependencies/openzeppelin/upgradeability/InitializableUpgradeabilityProxy.sol#L20-L28) |
| `set-078` | 36 | [origin L44-L46](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/dependencies/openzeppelin/upgradeability/BaseUpgradeabilityProxy.sol#L44-L46) | [origin L69-L76](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/misc/aave-upgradeability/BaseImmutableAdminUpgradeabilityProxy.sol#L69-L76) | [origin L20-L28](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/dependencies/openzeppelin/upgradeability/InitializableUpgradeabilityProxy.sol#L20-L28) |
| `set-079` | 4 | [origin L44-L46](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/dependencies/openzeppelin/upgradeability/BaseUpgradeabilityProxy.sol#L44-L46) | [origin L69-L76](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/misc/aave-upgradeability/BaseImmutableAdminUpgradeabilityProxy.sol#L69-L76) | [origin L20-L28](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/dependencies/openzeppelin/upgradeability/InitializableUpgradeabilityProxy.sol#L20-L28) |
| `set-080` | 20 | [origin L44-L46](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/dependencies/openzeppelin/upgradeability/BaseUpgradeabilityProxy.sol#L44-L46) | [origin L69-L76](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/misc/aave-upgradeability/BaseImmutableAdminUpgradeabilityProxy.sol#L69-L76) | [origin L20-L28](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/dependencies/openzeppelin/upgradeability/InitializableUpgradeabilityProxy.sol#L20-L28) |
| `set-081` | 2 | [origin L44-L46](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/dependencies/openzeppelin/upgradeability/BaseUpgradeabilityProxy.sol#L44-L46) | [origin L69-L76](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/misc/aave-upgradeability/BaseImmutableAdminUpgradeabilityProxy.sol#L69-L76) | [origin L20-L28](https://github.com/aave-dao/aave-v3-origin/blob/7c6023e64a1c462f138997ec122d49a97a3d4890/src/contracts/dependencies/openzeppelin/upgradeability/InitializableUpgradeabilityProxy.sol#L20-L28) |
| `set-121` | 9 | [origin L44-L46](https://github.com/aave-dao/aave-v3-origin/blob/e627c7428cbb358b9c84b601a009a86b4b871c08/src/core/contracts/dependencies/openzeppelin/upgradeability/BaseUpgradeabilityProxy.sol#L44-L46) | [origin L69-L76](https://github.com/aave-dao/aave-v3-origin/blob/e627c7428cbb358b9c84b601a009a86b4b871c08/src/core/contracts/protocol/libraries/aave-upgradeability/BaseImmutableAdminUpgradeabilityProxy.sol#L69-L76) | [origin L20-L28](https://github.com/aave-dao/aave-v3-origin/blob/e627c7428cbb358b9c84b601a009a86b4b871c08/src/core/contracts/dependencies/openzeppelin/upgradeability/InitializableUpgradeabilityProxy.sol#L20-L28) |

So the slot changes at the moment `Upgraded` is logged, and log order is
execution order. The shared walk, `proxy_log_positions` and `attribute_logs`,
takes the rule as the keyword `order_upgrade_transactions`, off by default.
The Aave module sets `ORDER_UPGRADE_TRANSACTIONS`, which the collector's
reconcile, build and check paths read from the plan's venue module and pass
on; no other venue module sets it. `compound-v3` still refuses an ordinary log
in its upgrade transaction, and the Wildcat venues read no upgrade topic at
all.

The rule is admitted only for a proxy whose runtime code is one of the seven
reviewed proxy codes: the distinct keccak-256 digests among the registry's 172
proxy entries, which the module holds as `REVIEWED_PROXY_CODES` and a test
recomputes from the registry. The standard library carries no keccak-256, so
the module carries its own, tested against SHA3-256 through the same
permutation and against the two constants it can derive, the slot and the
`Upgraded` topic.

**Refusals.** Each names the rule, the subject, the block, the transaction
index and the log index, which read `none` where the refusal concerns a
subject's opening rather than one log:

- `upgrade-in-opening-block`: an `Upgraded` log in the subject's opening block.
- `upgrade-before-opening-block`: an `Upgraded` log before the subject's opening block.
- `two-upgrades-in-one-block`: a second `Upgraded` log from one subject in one block.
- `slot-disagrees-with-announcement`: a slot read at the end of the block that differs from the announcement.
- `unrecorded-implementation`: an opening or announced implementation the registry does not record for that subject.
- `unrecognised-role`: a registry role that is neither a proxy role nor an immutable one.
- `unreviewed-proxy-code`: a proxy runtime code outside the seven reviewed.
- `upgrade-from-immutable-subject`: an `Upgraded` log from a subject with an immutable role.
- `epoch-limit`: more announcements than `MAX_EPOCHS` epochs can hold.
- `malformed-upgrade-log`: an `Upgraded` log whose topics are not the event topic and one left-padded, non-zero address.

A missing slot read, code read or block hash refuses by what it needed rather
than being inferred. The pinned registry holds only the fourteen roles it
counts, so `unrecognised-role` is reached only by calling
`derive_subject_epochs` with entries the pinned registry does not hold.

## Resuming, and rewinding

A checkpoint is written only after a shard's bytes are flushed and fsynced. It
records the next shard, the last accepted block and hash, each journal's
committed byte offset, and a bounded trail of the sixteen most recent accepted
boundaries. It is working state; no release names it.

Resume truncates every journal back to its committed offset, so a process
killed between a record and its checkpoint leaves nothing a resumed run keeps.
Before continuing, the collector re-reads the boundary blocks it remembers. When
one has changed under it, it rewinds to the deepest boundary that still matches,
drops the records above it and re-collects. A reorg below every remembered
boundary starts over. One deeper than the trail refuses, because the collector
would otherwise have to guess which of its journals is still on the chain it
started from.

`reconcile`, `build` and `check` read the checkpoint without truncating
anything, so none of them can lose a record it declined to use.

## What a refusal leaves behind

A response is refused when it exceeds the component byte ceiling, fails bounded
JSON parsing, carries a JSON-RPC error, answers a different request, is marked
truncated, or returns a page at the provider's declared limit and may therefore
be short. Each refusal appends a receipt naming the code, the evidence class,
the shard, the unresolved block range and the provider class the plan declared.

A receipt copies nothing a provider or a transport said. The exception text
reaches the operator on stderr instead. That boundary exists because a receipt
is a durable file and a transport's message can carry its own endpoint, and with
it a credential.

Retrying does not erase the earlier receipt.

## Reconciliation settles nothing

`reconcile` runs the finished interval past a second transport and compares each
shard's boundary hash, the ordered transaction hashes in that block, and the
identity tuple `(blockHash, transactionHash, logIndex, address, topics, data)`
for every log.

Both log streams undergo coordinate validation, but the preserved comparison
tuple does not include `transactionIndex`. V2 ownership is derived from the
primary journal; an `agreed` reconciliation does not establish second-provider
agreement on transaction indexes.

An `aave-v3` release says so itself. Every evidence scope carries the venue's
`POSITIONAL_VERIFICATION_LIMIT` among its gaps: provider agreement over logs
excludes `transactionIndex`, and the held `transaction-index-reconciliation`
job owns that comparison. `check` refuses an Aave release whose evidence scope
omits the sentence. A second provider that differs from the first only in one
log's `transactionIndex` still records `agreed`; the collector tests keep that
specimen.

A disagreement is recorded, not resolved. Neither provider wins by answering
first or by being in a majority of two. A shard whose boundary hash disagrees is
`failed`; one whose logs or transaction order disagree is `partial`; the second
provider's bytes for that shard are kept beside the first's. A second provider
that cannot answer leaves the interval `unreconciled`, keeps the counts it
reached, and says so.

## The release, and what it claims

`build` emits an ordinary `alexandria-capture-plan/v1` document and calls the
existing `ingest`. Its components are one JSON journal per declared evidence
class, each carrying the interval and one record per preserved exchange, or one
per plan-derived shard range when the plan declares `shards_per_component`; the
`epoch-evidence` journal of opening reads; and six more -- the interval receipt,
the implementation code, the reconciliation record, the error receipts, the plan
and the pinned registry.

Two of those are new with the opening reads. `epoch-evidence` preserves the
exchanges the epoch table was derived from, so a reader can rebuild the table
rather than take it. `implementation-code` carries each implementation's runtime
bytecode as its own component, so `check` re-hashes those bytes and compares the
digest with the one the epoch table declares, offline, from the release alone.

Every coverage count is a JSON pointer into the component it describes, so
`ingest` refuses a count the payload does not carry. `check` then re-derives
every shard's record counts from the journals, because a release rebuilt with an
inflated receipt would otherwise be self-consistent.

`check` runs Alexandria's own verification first, then the things only an
interval release can be wrong about: every component at or below the byte
ceiling, journal components tiling the plan's shard range exactly, shards
contiguous and non-overlapping across the declared interval, epochs tiling it
under their declared receipt version and naming this market's proxy, each
epoch's declared code hash re-derived from the `implementation-code` component's
bytes, the opening reads replayed against the plan so the journal holds exactly
the reads the plan names and no others, a finality boundary with its hash above
the interval's end, a reconciliation record for the same plan agreeing with the
receipt about every shard, and every shard that is not complete named in the
coverage of every evidence component. For v2, it also compares freshly derived
log ownership with every attribution row. A v1 result remains block-only; it
does not inherit that stronger check.

## The interval it has actually collected

The collector has run against two live providers, of classes `archive gateway,
public tier, no trace methods` and `public relay endpoint, archive logs and
state, no trace methods`, over Ethereum mainnet blocks 25,903,935 to
25,905,934. Four shards of 500 blocks all came back `complete`, carrying 93
proxy logs. The opening reads bound the start hash
`0xa4e35dad60b77815249c12cf22ad83056f2ad041ef9b6340dee03e83502d70f0` and the end
hash `0xc0ac604f5eaf0b78ee147ed3cec4f5c5ab1f7d66d1607266cbf343d7bdc959bd` into
every evidence scope under a `finalized` boundary, and produced two
implementation epochs split by an `Upgraded(address)` at block 25,904,935, both
implementations' runtime code preserved and re-hashed by `check`. Reconciliation
came back `agreed` over 106 comparisons with none disputed. `collect` and
`reconcile` together took 5,370 ms against the study's 120,000 ms budget.

The whole capture is committed at `examples/usdc-interval-live-v0/`, and its
demonstration rebuilds it offline to release identifier
`sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32`.
Neither provider's endpoint or hostname appears anywhere in it.

The historical v1 epoch table tiles by block, so a
proxy log emitted earlier in an upgrade block than the upgrade itself would be
attributed to the implementation that replaced the one which produced it. Block
25,904,935 here carries only the upgrade, at transaction index 193 and log index
524, so nothing in this capture is misattributed. These preserved bytes do not
demonstrate the before-upgrade defect, and their original identifier retains
the v1 scope. A v2 reconstruction has its own identifier,
`sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a`.

## What this does not establish

- No publisher identity and no provider completeness. Two providers agreeing
  says they agree, not that either preserved everything there was.
- No consensus finality and no canonical-chain membership. A `finalized` scope
  records that a provider answered the finalized tag and that both boundary
  hashes are bound; a digest check establishes neither claim.
- No traces, unless a plan declares the class and a provider serves it. Neither
  provider of the live capture serves `trace_filter`, so that capture declares
  the omission as a gap rather than covering it.
- No credit event, position observation, repayment or default, and no mapping.
  Turning this evidence into venue-qualified events is Tabularium's Compound v3
  Phase 1.
- No market other than the Ethereum mainnet USDC Comet. The other 27 markets at
  the registry pin are each a declared gap.
- No staging integrity after reconcile. `build` refuses a staging journal that
  is missing, shorter than its committed offset or no longer parses. The
  reconciliation record binds no staging digest, so a well-formed,
  length-preserving edit made after `reconcile` still builds, and its release
  checks.

## Wildcat estate delivery

The registered `wildcat-v1` and `wildcat-v2` modules use the same collector,
builder and checker as `compound-v3`. Their version-2 plans name 16 and 137
subjects. Each subject's epochs begin at its own established deployment or
preserved first-code position, with a per-subject ceiling. Unknown venues,
registry-format disagreement and a changed registry pin refuse by name.
The [whole offline proof](wildcat-interval/proof.md) binds both retained captures,
Compound compatibility, the eight conformance reports and the collection timings.

The production runs use targeted `trace_transaction` reads for transactions
with matching subject logs. They make no claim about logless transactions.
The paired subject Sentinel has zero preserved logs in both intervals; constructed
positive tests are labelled separately. Provider agreement is not a chain proof.

Correction recorded 2026-09-22: the historical Step 8 claim that every error
string names a provider class was too broad. Structured error and reconciliation
records carry `provider_class`; a CLI error can name only its read or shard.
The previous audit and specification remain unchanged as historical records.
