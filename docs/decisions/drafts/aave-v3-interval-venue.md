# Decision: Capture the Aave V3 Ethereum interval as a pinned table of segment releases

## Status

Accepted, 2026-09-23. Numberless until the merge that lands it, under the
draft path [ADR-077](../ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md)
set out.

## Context

[#1872](https://github.com/wildcat-finance/skills/issues/1872) registers the
Aave V3 Ethereum main market as an Alexandria interval venue and collects its
evidenced interval the way
[#1731](https://github.com/wildcat-finance/skills/issues/1731) collected
Wildcat V1 and V2. The market is Pool
`0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2` and AddressesProvider
`0x2f39d218133afab8f2b819b1066c7e434ad94e9e`; the interval and the 356
subjects are the ones the merged `aave-v3` row of
`docs/kickoff/1359/targets.json` binds by digest.

The interval runs from block 16,291,071 to 26,022,093, which is 9,731,023
blocks. On 2026-09-23 a sample from the local archive node read twelve
1,000-block log windows over the 356-address filter and traced 72
transactions. Extrapolated linearly, which the growth in density makes a rough
figure rather than a forecast, the interval holds 19,644,502 logs in
14,296,415,154 response bytes and 3,329,631 traced transactions in
48,097,593,584 filtered bytes. One release in the existing format holds at
most 128 components of 64 MiB each, 8,589,934,592 bytes. One release over the
whole interval is estimated at 62,394,008,738 bytes, so the capture cannot be
one release under the format this run inherits.

`.hexaemeron/design-evidence.json` (`protasis-design-evidence/v1`, SHA-256
`cf64d97fe0c852da6df96bb1ba8a4cc21b07366d85faf5030691c1c592e19ae3`) graded
four candidates. Its repository copy, the generator that computed every
selection value and the sample it read are under
`plugins/alexandria/docs/aave-v3-interval/`. `segmented-proxy-set-venue`
passed all five selection gates and `unique-frontier` selected it.

## Decision

Capture the interval as a table of contiguous segment plans, each an ordinary
plan and an ordinary release in the existing format, with every segment plan
digest pinned in reviewed code. The table tiles blocks 16,291,071 to
26,022,093 with no gap and no overlap. Each segment's recorded estimate fits
40 component ranges per shard class at 48 MiB and 128 components in all, and
every built component and journal is at most 67,108,864 bytes.

The segment count, the shard width and the split are data, not part of this
decision: they live in the preflight record and the segment table the run
measures. At the densest sampled window, uniform segments would need 65; no
smaller count is claimed until it is measured.

## Alternatives

- `single-interval-venue`: the same venue, registry and order rule with one
  plan over the whole interval. It offered one release to reason about. It
  failed `largest-release-within-ceiling`: 62,394,008,738 bytes is more than
  seven times the 8,589,934,592-byte ceiling, so it cannot build without a
  format change this issue does not own.
- `log-discovered-subjects`: pin only the 22 listed contracts and discover the
  rest from provider and configurator events during collection. It needed no
  out-of-tree generator input. It failed
  `subject-set-frozen-before-collection` and `subject-pin-in-reviewed-code`:
  334 subjects would rest on provider answers rather than a pin.
- `global-transaction-order-rule`: remove the shared refusal of ordinary logs
  inside an upgrade transaction for every venue. It offered the smallest
  shared diff. It failed `upgrade-order-rule-venue-scoped`: Compound and
  Wildcat would accept a shape their own pinned sources never established.
- Keeping today's refusal for Aave was not a candidate. The receipt of
  transaction
  `0x6f45f51fa5dd0246298f2e6284c43e0c57ef5e6b646ee1dfcd67f3f4f11dacd9` at
  block 22,839,362 upgrades 98 subjects, each emitting an ordinary log after
  its own `Upgraded`, so no plan covering that block could build.

## Consequences

The capture builds under today's release format, and each segment release is
built, checked and rebuilt offline on its own. The trade is several releases
instead of one, and a join across them that
[#1373](https://github.com/wildcat-finance/skills/issues/1373) owns together
with the collection manifest, the store and retrieval. Reversing this after
the production collection would orphan every segment staging tree.

This draft records the first of five decisions study item 12 names for one
design. The subject-set, epoch-model and order-rule decisions follow below;
the production-name decision joins them in the step that makes it.

## The subject set is the row's 356, and the periphery stays out

### Context

The merged `aave-v3` row lists 22 contracts and binds the full set of 356
subjects by one digest,
`289bbdf765e2e66f335f46706269dfbcc63600108d0ef5eb22ba814ecbcf8d64`, over the
sorted, lowercase, newline-joined addresses with a trailing newline. The other
334 subjects, every creation block and transaction, and the 489 token-proxy
implementation epochs are carried only by two full records the row pins by
SHA-256 and byte count; neither is in this repository. The same records list
six periphery entries, ten addresses, as not subjects. One of the ten,
`0x102633152313c81cd80419b6ecf66d14ad68949a`, is also inside the digest-bound
set: it is the WETH reserve's stable debt token proxy, created at block
16,496,792, and the periphery table names it `mock_stable_debt`.

### Decision

The registry declares exactly the 356 subjects the row's digest binds, with
the row's fourteen role counts. It is generated once from the two full
records, each read only after its bytes equal the row's pin, and it is
committed at `plugins/alexandria/examples/aave-v3-interval-v0/registry.json`.
Its canonical bytes hash to
`f5689f9e2ce977689676e64c474847c8d123aa332608a5f276dd933f62480b86`, which
`plugins/alexandria/scripts/alexandria_lib/aave_registry.py` holds as
`AAVE_V3_REGISTRY_SHA256`. The same module pins the canonical bytes of the
`aave-v3` row, SHA-256
`03c07d47cbae0d176b5498e93131a881c781a8f5abd55dcb747d0e14afbc1bc8`, the way
the Wildcat rows are pinned, so a changed row refuses by name.

`0x102633152313c81cd80419b6ecf66d14ad68949a` stays a subject, and the registry
records its periphery overlap. The other nine periphery addresses and the 67
reserves' underlying assets are recorded as outside the set, and none is a
subject.

### Alternatives

- Admit the periphery: the price oracle, the pool data providers, the
  incentives controller, Umbrella and the treasury would be captured too. It
  moves the set off the digest the row records, so the registry could no
  longer be checked against the merged row.
- Drop the overlapping address: it would resolve the overlap by removing a
  subject the digest binds, with the same loss.
- Discover the 334 unlisted subjects from logs during collection: this is the
  rejected `log-discovered-subjects` candidate, which leaves the set unfrozen
  before collection and outside reviewed code.

### Consequences

Every segment plan names these 356 subjects, so a change to the set changes
every segment plan digest and needs a new registry, a new pin and a reviewed
change here. The registry can be checked from the tree alone: its subject-set
digest, role counts and 22 listed contracts are compared with the merged row
without the full records. Regenerating it needs the two full records at the
pinned digests. A release names the overlap on
`0x102633152313c81cd80419b6ecf66d14ad68949a` rather than resolving it.

## Epochs are chosen per subject by registry role

### Context

Of the 356 subjects, 172 are `InitializableImmutableAdminUpgradeabilityProxy`
instances: the Pool, the PoolConfigurator and 170 reserve token proxies. The
other 184 are implementations, strategies, libraries, the AddressesProvider
and the ACLManager, and none is a proxy. The collector's two existing epoch
models each fit only part of that set. `eip1967-proxy` serves one proxy per
plan, and `immutable-code` reads no slot and no upgrade topic. A token proxy's
first implementation is set by `initialize` without an `Upgraded` log, so it
can only be read from the slot.

### Decision

`alexandria_lib/venues/aave_v3.py` names `aave-v3-role-keyed` and picks each
subject's model from the role the pinned registry records. A subject with one
of the five proxy roles opens, at the later of the plan's start and its
recorded creation block, with the implementation its EIP-1967 slot holds at
the end of that block. Each later `Upgraded` log opens a new epoch at its own
block, transaction index and log index, and the slot read at the end of that
block must equal the announcement. Each of the nine other roles has one epoch
whose implementation is the subject and whose code digest is read at its
opening block.

The model refuses, naming the subject, block, transaction index, log index and
rule: `Upgraded` in or before the opening block, two from one subject in one
block, a slot that disagrees with the announcement, an implementation the
registry does not record for that subject, an unrecognised role, a proxy
runtime code outside the seven reviewed, an `Upgraded` log from an immutable
subject, a table above `MAX_EPOCHS` and a malformed announcement. The seven
reviewed codes are the distinct keccak-256 digests among the registry's 172
proxy entries.

### Alternatives

- One EIP-1967 table for every subject: 184 subjects have no implementation
  slot, so each would need an invented slot answer or a refusal.
- `immutable-code` for every subject: every token upgrade would go unseen,
  and each proxy's logs would be owned by the proxy's own code rather than
  the implementation that ran them.
- Discover which subjects are proxies from slot reads during collection: the
  model would then rest on provider answers rather than the pinned registry,
  which the subject-set decision above rules out.

### Consequences

Every Aave epoch table, and so every Aave release identifier, depends on this
split. Reversing it after the production collection changes every segment
release. A proxy whose code is not one of the seven, or a role the registry
did not record, refuses rather than falling back to either model.

## The upgrade-transaction order rule is scoped to this venue

### Context

The shared position walk refuses every ordinary log a proxy emits inside its
own upgrade transaction. Aave upgrades tokens with `upgradeToAndCall`, which
emits `Upgraded` and then runs the new implementation. Transaction
`0x6f45f51fa5dd0246298f2e6284c43e0c57ef5e6b646ee1dfcd67f3f4f11dacd9` at block
22,839,362 upgrades 98 subjects; every one logs after its own `Upgraded`, and 2
also log before it. The pinned source of `aave/aave-v3-core` at
`9630ab77a8ec77b39432ce0a4ff4816384fd4cbf` sets the slot and then emits
`Upgraded` in `_upgradeTo`, and delegatecalls only after `_upgradeTo`
returns. The 71 proxies compiled from `aave-dao/aave-v3-origin`, in five
source sets, carry the same bodies; the collector document cites each set's
lines. Compound's and Wildcat's pinned sources establish no such order.

### Decision

`proxy_log_positions` and `attribute_logs` in `alexandria_lib/interval.py`
take the keyword `order_upgrade_transactions`, off by default. On, an ordinary
log from a subject in its own upgrade transaction is kept and owned by log
index: before its `Upgraded` by the old epoch, after it by the new. Only the
Aave module passes it on, and a test checks that no other module in the
collector passes it. `compound-v3` still refuses the shape, and the
Wildcat venues still read no upgrade topic.

### Alternatives

- Remove the refusal for every venue: this is the rejected
  `global-transaction-order-rule` candidate. Compound and Wildcat would accept
  an order their own sources never established, and the positional
  demonstration's refusal probe would change.
- Keep the refusal for Aave: no plan covering block 22,839,362 could build.
- A separate copy of the position walk inside the Aave module: two walks
  would have to stay in step, and the difference between them is one
  comparison.

### Consequences

Every Aave release identifier depends on the rule's scope: removing it, or
widening it to another venue, changes which epoch owns every ordinary log in
an upgrade transaction. The Compound and Wildcat release identifiers do not
move, because their callers pass nothing new. Widening the rule to another
venue needs that venue's own pinned source and its own decision.
