# Decision: Split interval log attributions across plan-derived components

## Status

Accepted, 2026-09-23.

## Context

[#1888](https://github.com/wildcat-finance/skills/issues/1888) asks one
Alexandria interval release to hold a venue-sized capture. At base
`17ea8d2ab5e52081370b13b92390b64849ed880d` two limits bind:

- `Builder._epoch_receipt` writes every preserved log's attribution row into
  the one `epoch-table` component. Measured on Wildcat V2, a row costs 327.51
  bytes and 9 nodes, so one 67,108,864-byte component holds 202,417 rows
  beside the rest of the table.
- A release holds at most 128 components and 1,024 captures, so at most 8 GiB
  of raw components.

[#1872](https://github.com/wildcat-finance/skills/issues/1872) extrapolates
19,644,502 logs over the 9,731,023 blocks of its Aave V3 interval. The design
record `plugins/alexandria/docs/epoch-table-split/design-evidence.json`,
SHA-256 `94a3d5293c5b03a73cc584a3ea2e1843c4e4659676819d4bff293e4a75850eb5`,
graded four candidates. Three fail a selection gate, so
`split-attribution-parts` is selected under `unique-frontier`. The study
beside it, `plugins/alexandria/docs/epoch-table-split/study.md`, holds the
measurements and the Aave model.

## Decision

This record holds three decisions.

1. The split release format. An `alexandria-interval-plan/v2` plan that
   declares `shards_per_component` may declare
   `"log_attribution_parts": "journal-ranges"`, the one admitted value. Any
   other plan carrying the field refuses by name. Part `k` is the component
   `log-attributions.<k>`: the rows of every preserved log in the plan's `k`th
   journal range, the range `logs.<k>` covers, in `attribute_logs` order. Each
   part is an `alexandria-interval-log-attributions/v1` document,
   `{first_shard, format, last_shard, part, rows}`. `build` and `check`
   refuse one above 67,108,864 bytes or 2,000,000 nodes by name. Receipt
   `alexandria-interval-receipt/v4` keeps v3's `epochs`, `first_code`,
   `format`, `implementation_code`, `reconciliation` and `shards`, drops
   `log_attributions`, and adds `log_attribution_parts`, one
   `{component, first_shard, last_shard, rows}` entry per part in order.
   `check` re-derives every part offline from the unchanged `attribute_logs`
   call. A plan without the field builds today's bytes.
2. The published limits in the table below. #1872 sizes its segment table to
   them, so a change after merge is a notice owed to #1872.
3. `build` and `check` keep today's memory model, holding the whole release in
   memory. Laurence decided this on 2026-09-23, and the follow-up is
   [#1891](https://github.com/wildcat-finance/skills/issues/1891).

| Limit | Base | Published | Where |
| --- | --- | --- | --- |
| Components per release | 128 | 16,384 | `MAX_COMPONENTS`, `release.py` |
| Captures per release | 1,024 | 16,384 | `MAX_CAPTURES`, `release.py` |
| Manifest and capture-plan bytes | 8,388,608 | 134,217,728 | new constant in `release.py` |
| Manifest and capture-plan nodes | 200,000 | 2,000,000 | new constant in `release.py` |
| Collector checkpoint nodes | 200,000 | 2,000,000 | `Staging`, `interval.py` |
| Collector checkpoint bytes | 8,388,608 | unchanged | `interval.py` |
| Bytes per component or journal file | 67,108,864 | unchanged | `MAX_RAW_COMPONENT_BYTES`, `MAX_JOURNAL_BYTES` |
| Shards per plan | 4,096 | unchanged | `MAX_SHARDS` |
| Statement bytes | 8,388,608 | unchanged | `MAX_STATEMENT_BYTES`, `statement.py` |

A split release has 6 fixed components, 1 opening journal, one journal per
class per range and one part per range. `journal_components` refuses a plan
above 16,384 before any request.

## Alternatives

- `compact-attribution-rows` keeps one table and drops `block_hash` and
  `transaction_hash` from each row, for `check` to re-derive from the logs
  journal. It needs 27 edit sites to the split's 31. But the 2,000,000-node
  limit caps a release at 280,333 rows, so Aave needs 71 releases and the
  candidate fails `aave-interval-in-one-release`.
- `raised-epoch-table-ceiling` keeps one table and raises that component's
  own ceiling to 8 GiB and 200,000,000 nodes. Aave fits one release, but
  `verify` and `check` parse its 6,434,645,664-byte table whole. The issue
  keeps the 64 MiB ceiling, so the candidate fails `component-ceiling-kept`.
- `plan-sized-releases` changes no format and keeps each plan under 202,417
  logs. Aave then needs 98 releases, Euler 15 and Maple 4, so the candidate
  fails `aave-interval-in-one-release`. A dense plan also collects to its end
  before the build refuses.

All three also fail `attribution-bound-fixed-by-the-plan`: none bounds an
attribution component's size before collection. A part follows a range whose
logs journal the collector already caps per file, and the worst measured part
is 0.4449 of that journal.

For the caps, the same Aave grid needs 2 releases at 8,192 components and 3
at 4,096. For memory, making `build` and `check` hold one journal component at
a time would have added one step and a memory conformance gate. Holding parsed
logs and rows while streaming component bytes projects about 38 GB for `build`
and 63 GB for `check`. Laurence kept this run to the format's limits instead.

## Consequences

- By the format, one release holds the Aave V3 interval: the model gives
  2,783 ranges of one shard and 11,139 components, 5,245 below the cap. It
  still fits if the densest log rate is up to 1.47 times the sampled one.
- Under today's memory model the 128 GiB collecting host cannot check it.
  Base `check` peaked at 1,208,811,520 bytes for Wildcat V2's 242,722,051,
  4.98 times, which projects about 401 GB for one Aave release. At that
  factor Aave needs at least 3 releases, 4 with a 25% margin.
- The base `check` refuses a split release by name: a 143-component split
  with `usdc-interval: components exceed the 128-item limit`, and the plan
  field alone with `usdc-interval: interval plan has an unknown shape`. The
  base `verify` accepts a split release within 128 components and claims
  nothing about its attributions.
- The manifest parse budget for an untrusted release widens sixteen times.
  Readers enforce both limits before parsing. A hostile manifest can still
  cost an estimated 1 GB of memory to parse; that figure is not measured.
- `alexandria.py statement` keeps Ariadne's 8,388,608-byte input limit. It
  refuses by name a release whose statement passes that limit: about 1,790
  components at Wildcat V1's 4,686 statement bytes a component, or 5,000 at
  V2's 1,678.
- Once a release ships in the format, each of the three decisions is
  expensive to reverse.
