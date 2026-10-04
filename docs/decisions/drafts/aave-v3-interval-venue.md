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
design. The subject-set decision follows below; the epoch-model, order-rule
and production-name decisions join it in the steps that make them.

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
