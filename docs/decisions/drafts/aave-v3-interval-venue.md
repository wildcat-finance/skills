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
design. The subject-set, epoch-model, order-rule and production-name
decisions join it in the steps that make them.
