# Study: split the interval epoch table and raise the release caps

Issue [wildcat-finance/skills#1888](https://github.com/wildcat-finance/skills/issues/1888).
Run branch `fiat/1888-epoch-table-split-and-release-caps`, cut from `main` at
`17ea8d2ab5e52081370b13b92390b64849ed880d`. Controller `fiat-v6.74.1`
(hexaemeron 1.6.77). Design record `.hexaemeron/design-evidence.json`, SHA-256
`94a3d5293c5b03a73cc584a3ea2e1843c4e4659676819d4bff293e4a75850eb5`, selects
`split-attribution-parts`.

## Assumptions

I proceed on these unless corrected.

1. The base is `17ea8d2ab5e52081370b13b92390b64849ed880d`. The interpreter is
   Python 3.14.6 from `.python-version`, with stdlib `unittest`. No dependency
   is added.
2. The Aave V3 figures are #1872's linear extrapolation from twelve sampled
   windows, read from its study at `3abcb107e22118427e08e8e23b826bc555d9f613`
   (blob SHA-256
   `42af8412e8242c99a9e2b40e571e193a5edda611043a41fb1e157deae78e4c60`). The
   densest window is one 1,000-block sample, so a real range may be denser
   than the model below.
3. #1872 keeps one `shards_per_component` for all three shard classes and
   sizes the densest class's range at 48 MiB of payload. The local Reth node
   answers at most 20,000 logs per `eth_getLogs`, which bounds shard width.
4. The split applies to subject-set plans (`alexandria-interval-plan/v2`)
   alone. All four venues in view are subject sets. Compound's single-proxy
   plan keeps one table.
5. Build and check keep today's memory model, holding the whole release in
   memory. Making them hold one component at a time is outside this run, by
   Laurence's decision below.
6. Release statements keep Ariadne's 8,388,608-byte input limit, so
   `alexandria.py statement` refuses a large release by name.
7. The two preserved Wildcat staging trees and releases named in section 3 stay
   available on the collecting host until integration.
8. A future venue's manifest costs at most 8,192 bytes and 122 nodes per
   component with its capture. The worst measured is 4,755 bytes and 54.5
   nodes (Wildcat V1).

**Decision, 2026-09-23.** Laurence kept this run to the format's limits. It
does not make `build` and `check` hold one journal component in memory at a
time, so under today's memory model a whole-interval Aave V3 release does not
fit the 128 GiB collecting host. Base `check` peaked at 4.98 times Wildcat V2's
release bytes, which projects about 401 GB for one Aave release. Holding parsed
logs and rows but streaming component bytes projects about 38 GB for `build`
and 63 GB for `check`, from the measured 1,280 bytes per parsed log and 649
bytes per attribution row. That work is carried forward as
`bounded-memory-build-and-check`. A yes would have added one step and a memory
conformance gate.

## 1. Problem statement, user, and the proving path

**What is built.** One Alexandria interval release that holds a venue-sized
capture. Two limits bind at the base commit.

1. `Builder._epoch_receipt` (`plugins/alexandria/scripts/usdc_interval.py:2429-2451`)
   writes every preserved log's attribution row into the single `epoch-table`
   component. Measured on Wildcat V2's 74,088 rows, a row costs 327.51 bytes
   with its separator and 9 nodes. Beside V2's 814,328-byte, 37,663-node rest
   of the table, one 67,108,864-byte component holds 202,417 rows; the
   2,000,000-node write limit would allow 218,037.
2. A release holds at most 128 components and 1,024 captures
   (`plugins/alexandria/scripts/alexandria_lib/release.py:56-58`), so at most
   8 GiB of raw components.

**Who uses it.** #1872's Aave V3 segment table consumes this run's merged
limits if #1872 chooses, at its Step 6, to wait for this run. Later Maple,
Euler V2 and Centrifuge V3 captures use the same limits.

**What a working prototype means.** A subject-set plan that declares the split
builds a release whose attributions sit in plan-derived `log-attributions.<k>`
components, `check` re-derives every part offline, the release may carry more
than 128 components, and every release that fits today keeps its bytes.

**Success criteria.** Each is settled by a command.

1. After Step 2, `python3 .hexaemeron/design/conformance.py split-parts-rederive-and-refuse --candidate split-attribution-parts`
   exits 0. Its seven named tests show one part per journal range, today's
   bytes for a plan without the field, offline re-derivation of every part, and
   named refusals of a missing, extra, reordered or altered part.
2. After Step 3, the same resolver exits 0 for
   `release-limits-hold-at-the-cap`: the component and capture caps admit
   16,384 and refuse 16,385, every manifest reader admits the new limits and
   refuses above them, a checkpoint for the largest admitted plan round-trips,
   and the re-derived
   `tests.test_usdc_interval.JournalSplitTests.test_a_split_beyond_the_release_component_limit_refuses_before_any_request`
   refuses before any request.
3. After Step 3, it exits 0 for `split-release-over-128-components`: a fixture
   whose attributions exceed one part builds, checks and verifies offline with
   more than 128 components. Tests may lower byte limits to reach that.
4. At integration it exits 0 for `pinned-release-identities-reproduce`, which
   rebuilds and verifies every pinned demonstration and verifies both committed
   releases (identifiers in section 3).
5. At every step's exit, with `NO_COLOR=1`:
   `python3 -m unittest discover -s tests`,
   `python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria`
   and `python3 scripts/run_checks.py` exit 0.
6. An older verifier refuses a split release by name. Measured at selection:
   the base commit's `check` refuses both split specimens (section 4).

**Proving path.** From the run worktree's root, with the two staging trees set:

```bash
export NO_COLOR=1 PYTHONDONTWRITEBYTECODE=1
export ALEXANDRIA_WILDCAT_V1_STAGING=<unpacked V1 staging tree>
export ALEXANDRIA_WILDCAT_V2_STAGING=<unpacked V2 staging tree>
(cd plugins/alexandria && python3 -m unittest -v tests.test_release_limits.SplitReleaseTests)
python3 .hexaemeron/design/conformance.py pinned-release-identities-reproduce --candidate split-attribution-parts
```

**Answer to #1872: can one release hold the whole Aave V3 interval?** At the
proposed cap of 16,384 components: yes by the format, no by today's memory.

- Blocks 16,291,071 to 26,022,093 are 9,731,023 blocks. At the densest sampled
  window, 5,718 logs per 1,000 blocks, the 20,000-log answer limit allows a
  3,497-block shard. At 13,420 trace bytes per block, a 48 MiB range holds
  3,750 blocks, so one shard per range: 2,783 shards and 2,783 ranges.
- Components: 6 fixed, 1 opening journal, 3 × 2,783 journals and 2,783
  attribution parts, 11,139 in all. Any shard width from 2,377 to 3,497 blocks
  fits. At 2,448 blocks, 70% of the answer limit, the count is 15,911; at
  2,377 it is 16,383. Narrower than that, one plan cannot fit: 2,376 blocks
  needs 16,391 components, and anything narrower needs more than MAX_SHARDS
  (4,096) shards.
- Headroom: 16,384 is four components per range at MAX_SHARDS, and it
  leaves 5,245 components, 1.47 times, over the widest-shard count. One
  release still fits if the true densest log rate is up to 1.47 times the
  sampled one (8,412 logs per 1,000 blocks), or the densest trace rate up to
  1.58 times.
- The same grid needs 2 releases at a cap of 8,192 and 3 at 4,096. The
  4,096 figure in the issue counts bytes (256 GiB), not ranges.
- Bytes: about 80.6 GB, 74.2 GB of journals with V2's envelope factors and
  6.43 GB of attribution rows.
- Memory: base `check` peaked at 1,208,811,520 bytes for V2's 242,722,051
  bytes, 4.98 times. That projects about 401 GB for one Aave release against
  this host's 137,438,953,472 bytes. At that factor the host checks releases up
  to about 27.6 GB, so under today's memory model Aave needs at least 3
  releases, 4 with a 25% margin.

**The limits #1872 sizes to.** These values are this run's published
interface. Any change to them after merge is a notice owed to #1872.

| Limit | Base | Proposed | Where |
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

The split rule:

1. A subject-set plan declares `"log_attribution_parts": "journal-ranges"`,
   the one admitted value. It requires `shards_per_component`. A single-proxy
   plan carrying it refuses by name.
2. Part `k` is the component `log-attributions.<k>`. It holds the rows of every
   preserved log in the plan's `k`th journal range, the same range as
   `logs.<k>`, in `attribute_logs` order.
3. Each part is written under 67,108,864 bytes and 2,000,000 nodes; the build
   and `check` refuse a larger one by name. In the preserved releases a range's
   rows cost at most 0.4449 of that range's logs journal.
4. Components are 6 fixed, 1 opening, one per class per range and one part per
   range. `journal_components` refuses a plan above 16,384 before any request.

## 2. Prior art

### In this repository, verified at the base commit

- `release.py:56-58` sets `MAX_RAW_COMPONENT_BYTES` 64 MiB, `MAX_COMPONENTS`
  128 and `MAX_CAPTURES` 1024, enforced at `:276-277` and `:316-317`.
  `ingest` reads the capture plan under `MAX_CONTROL_BYTES` and the default
  200,000 nodes (`:70-76`) and encodes the manifest with the default node
  limit (`:131`, `:134`). `verify` reads `manifest.json` under the same limits
  (`:151-164`).
- `alexandria_lib/canonical.py:10` sets `MAX_CONTROL_BYTES` 8 MiB, `:13`
  `MAX_NODES` 200,000 and `:22` `MAX_LARGE_NODES` 2,000,000. `_check_tree`
  counts values, not keys, so the V1 manifest costs 54.5 nodes a component, V2
  44.0 and the Compound Phase 0 release 35.0; counting keys as well gives 66.
- `usdc_interval.py:123` sets `MAX_RESPONSE_NODES` 2,000,000. `:159-162` lists
  the six `FIXED_COMPONENTS`. `journal_components` (`:177-212`) refuses a plan
  above `MAX_COMPONENTS` at `:206-211`. `Builder.build` writes each component
  under 2,000,000 nodes (`:2403`), appends one capture per component
  (`:2414`) and writes `capture-plan.json` under the default 200,000 nodes
  (`:2421`). `_epoch_receipt` is `:2429-2451`. `check_interval` reads the
  manifest under 8 MiB and 200,000 nodes (`:2713-2716`), loads every component
  at once (`:2748-2760`) and compares the whole attribution list at `:3167`.
- `alexandria_lib/interval.py:66-67` sets `MAX_SHARD_WIDTH` 50,000 and
  `MAX_SHARDS` 4,096. `SPLIT_FIELD` is `:73`. `attribute_logs` is `:1277` and
  `validate_attributions` `:1309`; a subject row carries eight fields.
  `Staging` writes its checkpoint under 200,000 nodes (`:697`, `:814`) and reads
  it the same way (`:716-717`). A checkpoint with a full 16-entry history
  holds 17 × journals + 106 nodes, so a plan with 3,920 or more ranges across
  three classes passes 200,000.
- The same readers of `manifest.json` sit in `index.py` (`_load_release`,
  `_load_manifest`, `_insert_release`), `derivation.py` (`_read_manifest`,
  `derive`, `verify_derivation`), `compound_phase0.py` (`load_phase0`) and
  `statement.py` (`_verified_manifest`).
- `shards_per_component` is the precedent: plan-derived journal ranges named
  `<class>.<k>`, re-derived by `check` from the plan alone
  (`plugins/alexandria/docs/usdc-interval-collector.md`, "Splitting a journal
  across components"). Wildcat V1 declares 20 shards per component over 667
  shards (34 ranges, 109 components); V2 declares 87 over 3,463 (40 ranges, 127
  components).
- Schemas state the caps: `capture-plan-v1` and `archive-manifest-v1` carry
  `maxItems` 128 and 1024, `address-query-v1` 1024 captures, and
  `interval-checkpoint-v2` `maxProperties` 128 offsets.
- No consumer outside Alexandria reads `log_attributions` or the epoch table.

### The last two merged pull requests that changed the subject

- [#1875](https://github.com/wildcat-finance/skills/pull/1875), merged
  2026-09-23 at `97e49ce736fa8762eb2279dac3a61a99c9960e36`, pinned the two
  Wildcat rows of `targets.json` in `wildcat_registry.py` and moved Alexandria
  to 0.7.12. It carried forward #1874 and a capture-parity item held in another
  repository. Neither touches release limits; both stay open with their owners.
- [#1838](https://github.com/wildcat-finance/skills/pull/1838), merged
  2026-09-22 at `104f6f82c390003fb61039d3023d07c1abe05086`, delivered both
  Wildcat estates. Its carryover rows that meet this subject:
  - `staging-validator-boundaries`: staging validation admits counts
    `journal_components` rejects. Still true after this run, whose checkpoint
    limit rises with the cap; it stays a named lead.
  - `resource-coverage-leads`: one gap sentence per non-complete shard grows
    every journal capture. With 16,384 components the manifest limit, not the
    gap cap, refuses such a release; risk `manifest-growth`.
  - `transaction-index-reconciliation` stays Alexandria's held frontier job.
    This run is not a frontier run and leaves it untouched.
  - Every other row concerns capture provenance, audit tooling or Hexaemeron
    and stays with its owner.

### Audit history

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root and exited 0, with 106 of 106 views
`committed=match`. So the verified synopses were the reading view, grepped for
component, manifest, node, attribution and memory terms. Alexandria keeps no
plugin-level `audit/AUDIT.md`; its history is in these round files:

| Source | View read | Source SHA-256 | Findings |
| --- | --- | --- | --- |
| `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.md` | its `.synopsis.md` | `ff1b2a5396722ec03925962ac9f2aa63ce6e70e058cf1f8d4e4e61963d0c9820` | 42: 38 fixed, 4 open or awaiting an amendment |
| `audit/rounds/fiat-1503-attribute-implementation-epochs-by-transact.md` | its `.synopsis.md` | `c891e8447d23611d5d0eaec79fbef1b7b80dd45fc0dd1e9fd5a987651d851bf1` | 2 fixed |
| `audit/rounds/fiat-1350-alexandria-1-interval-collector-run-against.md` | its `.synopsis.md` | `213d75ae346bbd6060aa330162179a215ec7f034dec961ce020404b37e47146e` | 18 fixed |
| `audit/rounds/fiat-395-resumable-ethereum-usdc-interval-collector.md` | its `.synopsis.md` | `e9369df1f8647f839e9fd43940154a8c950a8c5db907f5a56aa51c5071b620ec` | 25: 20 fixed, 5 open |
| `audit/rounds/fiat-391-unified-live-and-archive-collection.md` | its `.synopsis.md` | `f4c89aafa550efb533c3577656de1cc394589a29d41b5d24ba59b44aa855d642` | 11 fixed |
| `audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.md` | its `.synopsis.md` | `ce1d705337f3f53cea1d3621851f05635ccf648c7df4d6db1c842c6113b19476` | 4 fixed |
| `audit/AUDIT.md`, Alexandria's Compound Phase 0 and Goldfinch rounds | `audit/AUDIT_SYNOPSIS.md` | `d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d` | none on these limits |

The synopses keep every finding id and status, `Covered`, `Not checked`,
`Elenchus verdict` and `Leads not pursued`. What bears on this run:

- 1731 Step 4 round 1, lead: `interval-checkpoint-v2.schema.json` admits 128
  offsets while staging accepts 601, and `check_interval`'s component byte
  comparison is reached only under a patched ceiling. This run raises the
  schema bound to 12,289 offsets and keeps the byte comparison.
- 1731 Step 6 rounds 7 and 8, leads: "the 200,000-node component ceiling"
  and "one gap sentence per non-complete shard". Component reads and writes
  now use 2,000,000 nodes (`canonical.py:14-22`, `usdc_interval.py:2403`); the
  gap growth is risk `manifest-growth`.
- 1731 W6-R4-01 (low, open): prose trimmed from the v3 schema, the collector
  document and five docstrings, with the restoration blocked by the portable
  package ceiling. That block has lifted (3,112,116 bytes beyond the reserve
  at the base), but the restoration spans `venues/wildcat_v2.py` and
  `interval.py` docstrings outside this run. It stays open with its record.
- 1731 W1-R1-02, W7-R1-01 and W8-R1-01 (open) concern that run's own study and
  runbook wording. 395 S1-R1-07 and S6-R1-03 (open) concern package file
  ceilings since raised, S2-R1-04 and S5-R1-04 that run's runbook, and S5-R1-05
  a claim the later `implementation-code` component answered. None assigns work
  to this run, so no known-failure inventory is carried.

### Concurrent work in #1872

[#1872](https://github.com/wildcat-finance/skills/issues/1872) runs as a
stacked set of open pull requests:
[#1883](https://github.com/wildcat-finance/skills/pull/1883) at
`3abcb107e22118427e08e8e23b826bc555d9f613`,
[#1884](https://github.com/wildcat-finance/skills/pull/1884) at
`beb9f18ec889ce41d9489b6c71025cbc63b5b13f`,
[#1885](https://github.com/wildcat-finance/skills/pull/1885) at
`0eea1abc2a0193c91b7de48edebcaa9fd19a645c` and
[#1889](https://github.com/wildcat-finance/skills/pull/1889) at
`b479c21b72d58edcf1a2e8f1ca9910fc37ab5a6d`.

- #1885 adds the keyword-only `order_upgrade_transactions=False` to
  `proxy_log_positions` and `attribute_logs`.
- #1889 passes it at the `attribute_logs` calls in `Builder._epoch_receipt` and
  `check_interval`, and adds a positional-verification gap to `_gaps` and
  `check_interval`.
- Both edit `docs/usdc-interval-collector.md`. Their branches carry Alexandria
  0.7.13 to 0.7.16, and #1872 plans its own Alexandria generation row.

This design splits the rows after `attribute_logs` returns and never changes
that function's signature or ordering, so the keyword passes through
unchanged. Of this design's 31 edit sites, 3 are ones #1885 or #1889 change:
`check_interval`, `Builder._epoch_receipt` and the collector document.
Whichever run integrates second syncs.

### Issue #1373

[#1373](https://github.com/wildcat-finance/skills/issues/1373) asks for a
capture above 8 GiB, retrievable from a durable store and verifiable, by
several releases with a collection manifest or by a versioned format
extension. This run supplies the extension. Store retrieval, access policy and
the collection manifest stay with #1373, which the issue's carryover already
names.

### Outside this repository

- Apache Parquet splits a table into row groups and records where each group
  sits, so a reader handles one group at a time:
  <https://parquet.apache.org/docs/file-format/>. Here each part is its own
  digest-bound component and the ranges come from the plan, not from sizes.
- Reth documents `--rpc.max-logs-per-response` with a default of 20,000:
  <https://reth.rs/cli/reth/node>.

## 3. Constraints and non-goals

**Starting point and tools.** Base `17ea8d2ab5e52081370b13b92390b64849ed880d`
on `main`; run branch `fiat/1888-epoch-table-split-and-release-caps`; Python
3.14.6; controller `fiat-v6.74.1`. Run every gate with `NO_COLOR=1`, because
this shell sets `FORCE_COLOR`. The Hexaemeron suite, if touched, runs through
`python3 plugins/hexaemeron/tests/run_tests.py`.

**Byte identity.** Every release that fits today keeps its identifier. Measured
at the base, all reproduce:

- `sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa`, `usdc-interval-v0`.
- `sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036`, `usdc-interval-epochs-v0`.
- `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a`, current Compound, built by the epochs and estates demonstrations.
- `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32`, the historical live demonstration.
- `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`, Wildcat V1.
- `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`, Wildcat V2.
- Committed releases `sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab`
  (Compound Phase 0) and
  `sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f`
  (proof-backed state) verify.

**External dependencies.** The Wildcat estates demonstration finds its staging
trees through `ALEXANDRIA_WILDCAT_V1_STAGING` and
`ALEXANDRIA_WILDCAT_V2_STAGING`. Neither is in the repository. On the
collecting host they are unpacked at:

- V1:
  `/Users/c0rtexzer0/Projects/wildcat-skills/tmp/fiat-evidence/fiat-1731-venue-agnostic-interval-capture-for-both-wi/step10-capture-narrow/staging`,
  107 of 107 files matching `staging-manifest.json`.
- V2: `.../step9-repair-20260921/staging-concurrent` under the same directory,
  125 of 125 files matching. Its archive `replacement-staging.tar.zst` matches
  `0407fecac64ff15c23d298044cd2498180ceea2900bb6807330c104b348bd90a`.
- The design resolver also reads the built V1 and V2 releases at
  `.../step11-cli-v1-release` and `.../step11-cli-v2-release`, through
  `ALEXANDRIA_WILDCAT_V1_RELEASE` and `ALEXANDRIA_WILDCAT_V2_RELEASE`.

The integration cell needs the two staging variables set.

**Versions.** The required `invariants` check runs `scripts/plugin_release.py`,
which refuses a change under `plugins/alexandria/` without a version rise. Each
step raises Alexandria's package version in four places:

- `plugins/alexandria/.claude-plugin/plugin.json`;
- `plugins/alexandria/.codex-plugin/plugin.json`;
- the Alexandria entry in `.claude-plugin/marketplace.json`;
- the pin in `tests/test_version_propagation.py`.

Nothing else pins 0.7.12. The collector's `User-Agent` reads the version at
import and enters no release byte. The skill generation moves once, through
the runbook's `version-relations` block, and the last step writes
`plugins/alexandria/skills/alexandria/EVOLUTION.md` and the frontmatter
version in `SKILL.md`.

**Digests the tree pins.** Checked by grepping each file's SHA-256 across the
tree:

- `tests/test_release.py` is pinned by
  `tests/fixtures/promise-machine/runtime/law-runtime-result-binding.json`.
- `tests/test_demo.py` is pinned by the runtime fixtures, the coverage map and
  `docs/agent-instruction-reconciliation/demonstration-evidence/`.
- The three Wildcat `demo.py` files are pinned by `DEMONSTRATION.md`.

New tests go in new modules and none of these files changes. Ariadne's
`wildcat-datasets-v0` and `docs/kickoff/1389/evidence/sources.json` pin
`usdc_interval.py`, `release.py`, `interval.py`, `canonical.py`, `index.py`
and `address-query-v1.schema.json` at named historical revisions and read no
working file, so editing them moves nothing there.

**Horos.** Every step regenerates `.horos/boundary.json` with
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`, then
`.horos/census.json` with `... scan . --census --write`, and stages both.

**Package budget.** At the base the portable runtime holds 1,449 files, 151
below the 1,600 tripwire, and 17,859,404 bytes, 3,112,116 beyond the 5 MiB
reserve. Tests are omitted from it. Docs, schemas and the committed design
folder count, and #1872's first step adds its own design folder.

**Non-goals.**

- Retrieving releases from a durable store or joining them with a collection
  manifest (#1373).
- Capturing any venue, or re-planning #1872's segments.
- Changing the 64 MiB component ceiling, the journal ceiling or MAX_SHARDS.
- Bounded-memory build and check (the decision under the assumptions).
- A split for single-proxy plans. No single-proxy capture in view passes the
  table.
- Raising the release statement's limit, which is Ariadne's input bound.
- Restoring 1731 W6-R4-01's prose, or taking Alexandria's held frontier job.

**Carried forward.** Candidates for the run-level `carryover` block, with the
disposition proposed now and settled at integration:

- `durable-store-retrieval`: duplicate of #1373, as the issue already records.
- `aave-segment-sizing`: none; #1872's run owns its segment plan.
- `bounded-memory-build-and-check`: file it; Laurence kept it out of this run
  on 2026-09-23.
- `release-statement-limit`: `statement` refuses a release whose statement
  passes 8,388,608 bytes, about 1,790 components at V1's 4,686 statement bytes
  a component or 5,000 at V2's 1,678; file it unless an issue already covers
  it.
- `single-proxy-split`: none; no single-proxy capture in view passes the
  table.
- `w6-r4-01-prose`: none; it stays open in its own audit record.

**Boundaries.**

- Always: the root and Alexandria suites and `scripts/run_checks.py` before a
  commit; Imprimatur on every shipped document; the Horos pair regenerated in
  the commit that changes the tree; a version rise in every step touching
  Alexandria.
- Ask first: adding a dependency; changing a published release byte or
  identifier; changing the plan, receipt, checkpoint or manifest format beyond
  this study; widening a limit beyond the table in section 1; touching CI.
- Never: rewrite a pinned release, expected file, audit record or historical
  study to match new bytes; commit a staging tree, endpoint or credential;
  delete or weaken a failing test; claim a demonstration ran when it did not.

## 4. Design options

### What was measured

At the base commit, on the collecting host (Apple M5 Max, 18 CPUs,
137,438,953,472 bytes of memory):

| Run | Seconds | Peak resident bytes |
| --- | --- | --- |
| `check`, Wildcat V2 (242,722,051 bytes) | 4.36 | 1,208,811,520 |
| `check`, Wildcat V1 (20,496,046 bytes) | 0.39 | 141,230,080 |
| V2 demonstration `build` | 9.81 | 1,191,591,936 |
| V1 demonstration `build` | 0.75 | 155,910,144 |
| Estates `build`, then `verify` | 22.80, 9.98 | 1,267,826,688, 1,263,665,152 |

Also measured on the preserved releases:

- An attribution row costs 327.51 bytes and 9 nodes; without its two hashes,
  157.51 bytes and 7 nodes.
- Journal bytes per response byte are 1.5357 for logs and 1.0840 for traces.
  A boundary header costs 22,285 bytes a shard.
- A parsed log costs 1,280 bytes and an attribution row 649 bytes of Python
  memory.

`.hexaemeron/design/observations.json` records the runs and their commands.

### Candidates

1. `split-attribution-parts`. A subject-set plan declares
   `"log_attribution_parts": "journal-ranges"`. The rows move out of the epoch
   table into `log-attributions.<k>` parts at the plan's journal ranges, under
   receipt `alexandria-interval-receipt/v4`. `check` compares each part with
   the rows `attribute_logs` derives for its shards. The caps rise to 16,384,
   manifests read under 128 MiB and 2,000,000 nodes, and the checkpoint under
   2,000,000 nodes. Trade: the most edit sites and about 2,783 extra
   components for Aave, for a table bounded by the plan.
2. `compact-attribution-rows`. One table whose rows drop `block_hash` and
   `transaction_hash`, which `check` re-derives from the logs journal. The caps
   rise the same way so journals can grow. Trade: fewer changes, but the
   2,000,000-node limit caps a release at 280,333 rows. That covers
   Centrifuge's 64,000 logs and not Maple's 687,000, Euler's 3.01 million or
   Aave's 19,644,502, which needs 71 releases.
3. `raised-epoch-table-ceiling`. One table whose own ceiling rises to 8 GiB and
   200,000,000 nodes while every other component keeps 64 MiB. Trade: one
   release for Aave with a 6,434,645,664-byte table that `verify` and `check`
   parse whole, against the issue's rule that the 64 MiB ceiling stays.
4. `plan-sized-releases`. No format change. Each plan stays under 202,417
   logs, and a venue ships as many releases, joined later by #1373's
   collection manifest. Trade: no edits, but Aave needs 98 releases, Euler 15
   and Maple 4, and a dense plan still collects to its end before the build
   refuses.

### Criteria and results

`python3 .hexaemeron/design/resolve.py <criterion> --candidate <id>` wrote
every selection report under `.hexaemeron/design/reports/selection/`, and a
rerun reproduced all 36 byte for byte. Gates first:

| Criterion | Concern | Rule | parts | compact | raised | plan-sized |
| --- | --- | --- | --- | --- | --- | --- |
| `fitting-plans-keep-todays-path` | compatibility | = true | true | true | true | true |
| `older-verifier-refuses-by-name` | compatibility | = true | true | true | true | true |
| `component-ceiling-kept` | space | ≤ 67,108,864 | 50,873,606 | 50,873,606 | 6,434,645,664 fail | 67,108,543 |
| `aave-interval-in-one-release` | space | ≤ 1 | 1 | 71 fail | 1 | 98 fail |
| `attribution-bound-fixed-by-the-plan` | recovery | = true | true | false, fail | false, fail | false, fail |

Then the metrics, each minimised:

| Criterion | Concern | parts | compact | raised | plan-sized |
| --- | --- | --- | --- | --- | --- |
| `edit-sites` | time | 31 | 27 | 24 | 0 |
| `sites-shared-with-1872` | compatibility | 3 | 3 | 2 | 0 |
| `manifest-bytes-at-cap` | space | 77,907,423 | 77,907,423 | 77,907,423 | 608,652 |
| `aave-release-check-peak` | space | 401,365,872,286 | 5,494,269,507 | 401,365,872,286 | 4,139,688,751 |

What each value is:

- `fitting-plans-keep-todays-path`: no committed plan and no file at the base
  carries the candidate's trigger, so every release that fits today takes
  today's code path.
- `older-verifier-refuses-by-name`: the base commit's `check`, extracted with
  `git archive`, run on specimens built from the V1 release by the base
  `ingest`. It refused the 143-component split with
  `usdc-interval: components exceed the 128-item limit` and the plan field
  alone with `usdc-interval: interval plan has an unknown shape`. It refused
  compact rows with `interval plan has an unknown shape` or, without the field,
  `log attribution has an unknown shape`, and the raised table with
  `component epoch-table exceeds the 67108864-byte limit`. For the unchanged
  format it accepted V1 as `v3-subject-positional`. No refusal carried a
  traceback. The base `ingest`, which runs `verify`, accepted every specimen
  within 128 components, so an older generic `verify` accepts such a release;
  it claims nothing about attributions.
- `component-ceiling-kept` and `aave-interval-in-one-release`: the Aave grid
  model in section 1, per candidate.
- `attribution-bound-fixed-by-the-plan`: whether every attribution component's
  size is bounded before collection. Parts follow ranges whose logs journal the
  collector already caps per file, and the worst measured part-to-journal
  ratio is 0.4449 (V1 `logs.33`; V2 0.3731 at `logs.27`). A single table's
  size is the collected log count, and the base plan-time refusal counts no
  attribution bytes.
- `edit-sites`: declared sites, each checked to exist at the base, or to be
  absent for a new file.
- `sites-shared-with-1872`: the sites whose functions #1885 or #1889 change,
  from their pinned heads' hunks.
- `manifest-bytes-at-cap`: the cap times the worst measured 4,755.09 bytes a
  component.
- `aave-release-check-peak`: 4.98 times the candidate's largest Aave release.

Four conformance gates stay pending for every candidate. Only the selected
candidate's fall due, each at the stop point shown.

| Criterion | Concern | Stop point | Evidence |
| --- | --- | --- | --- |
| `split-parts-rederive-and-refuse` | correctness | `step:3` | 7 tests in `tests.test_log_attribution_parts` |
| `release-limits-hold-at-the-cap` | correctness | `step:4` | 4 tests in `tests.test_release_limits` and the re-derived `JournalSplitTests` refusal |
| `split-release-over-128-components` | correctness | `step:4` | `tests.test_release_limits.SplitReleaseTests` |
| `pinned-release-identities-reproduce` | compatibility | `integration` | every pinned demonstration rebuilt and verified, both committed releases verified |

`python3 .hexaemeron/design/conformance.py <criterion> --candidate split-attribution-parts`
resolves each one and writes its report under
`.hexaemeron/design/reports/conformance/`, create-only. It refuses any other
candidate by name, and `--no-report` prints the observation alone. At the base
the integration cell already passes, and the test cells refuse because their
modules do not exist.

### Selection

Three candidates fail a selection gate, so `split-attribution-parts` is the only
survivor and the non-dominated frontier under `unique-frontier`.
`design_evidence.py --transition design-lock` exits 0. The metrics record the
trade: the split costs the most edits and a manifest limit sixteen times
today's, and its one Aave release is too large for today's memory model.

### The selected design

**Plan.** `validate_plan` admits `log_attribution_parts` on a v2 plan that
declares `shards_per_component`, with the value `journal-ranges`, and refuses
it elsewhere by name. `plan_digest` covers it like every plan field. A plan
without it validates and builds exactly as today.

**Components.** `journal_components` keeps returning journals. A sibling
derivation returns the parts from `plan_partition`, and the refusal counts
fixed, journal and part components against `MAX_COMPONENTS` before any request.

**Build.** `_epoch_receipt` calls `attribute_logs` as today, with whatever
keywords #1885 adds, and validates the rows. For a split plan it slices the
returned rows by each range's blocks into part documents and writes receipt
v4. `build` adds each part to its documents with a capture from `_capture`.

**Receipt v4.** `alexandria-interval-receipt/v4` keeps v3's `epochs`,
`first_code`, `format`, `implementation_code`, `reconciliation` and `shards`.
It drops `log_attributions` and adds `log_attribution_parts`, one
`{"component", "first_shard", "last_shard", "rows"}` entry per part in order.

**Part.** `alexandria-interval-log-attributions/v1` is
`{"first_shard", "format", "last_shard", "part", "rows"}`, where `rows` are v3
subject rows. Its capture is header-bound like the epoch table's, counts
`/rows`, and names its shards and blocks in one gap sentence the plan derives.

**Check.**

1. Receipt v4 is required exactly when the plan declares the split.
2. The part list must equal the plan's, with row counts equal to each part's.
3. Each part's shape, index and shard range must be the plan's, its rows pass
   `validate_attributions`, and each row's block lies inside its range.
4. Each part must equal the rows the unchanged `attribute_logs` call derives
   for that range.
5. Missing and extra parts reach the existing component refusals.

Every mismatch refuses by name and names the part.

**Caps and limits.** The values in section 1. New constants in `release.py`
hold the manifest limits beside `MAX_COMPONENTS`, and every reader listed in
section 2 uses them. `Staging` writes and reads its checkpoint under 2,000,000
nodes; a checkpoint for 4,094 ranges costs at most about 6.9 MB, under the
unchanged 8 MiB. The schemas move with the constants, and `interval-checkpoint-v2`
admits 12,289 offsets, three classes of 4,096 plus the opening journal.

**Documents.** `docs/usdc-interval-collector.md` gains the part rule, receipt
v4 and the component count. `docs/raw-releases.md` states the caps and manifest
limits. `schemas/README.md` catalogues the two new schemas.

### Steps and stop points

The stop points in the design record fix this order.

1. Scaffold. Commit the study, runbook, design record, `.hexaemeron/design/`
   scripts, observations and selection reports under
   `plugins/alexandria/docs/epoch-table-split/`, and create the decision
   record draft named in section 12.
2. The split under today's caps: plan field, parts, receipt v4, build, check,
   schemas, the collector document and `tests/test_log_attribution_parts.py`.
   Its report falls due when Step 3 opens.
3. The caps and limits: constants, every manifest reader, the checkpoint
   limit, schemas, `docs/raw-releases.md`, the over-128 fixture in
   `tests/test_release_limits.py` and the re-derived refusal test. Its reports
   fall due when Step 4 opens.
4. Demonstration: rebuild every pinned release and run the split fixture, then
   write the generation row. The integration report falls due at the last
   `done merge-step`.

The split goes first because at 128 components the existing refusal test
still holds. Raising the cap first would break that test with no split yet
available to re-derive it.

## 5. Risk register seed

```risk-register
byte-identity | release bytes for every plan without the new field | pinned identifiers and committed releases reproduce, and no encoder path changes for undeclared plans
older-verifier | a base-commit check reading a split release | refusal is a named AlexandriaError, never acceptance or a traceback
part-tiling | the plan-derived part set in check | a missing, extra, reordered, renamed or overlapping part refuses by name before rows are compared
part-rows | rows inside each part | each row passes validate_attributions, sits inside its part's blocks and equals the derived rows for that range
receipt-plan-agreement | receipt v4 and the plan field | v4 appears exactly when the plan declares the split, and its part list matches the plan's
component-count | journal_components before any request | a plan whose fixed, journal and part components pass 16,384 refuses in the collector and the builder
manifest-limits | every manifest.json and capture-plan.json reader and writer | all use the new byte and node limits, and none keeps 8 MiB or 200,000 nodes
manifest-growth | per-capture gap sentences times components | a manifest past 134,217,728 bytes or 2,000,000 nodes refuses by name rather than exhausting memory
checkpoint-limits | Staging checkpoint writes and reads | a plan at the cap checkpoints, resumes and rewinds under 2,000,000 nodes and 8 MiB
part-budget | each part as written and read | a part above 67,108,864 bytes or 2,000,000 nodes refuses by name in build and check
memory-growth | build and check holding a whole release | peak memory stays measured and stated; nothing claims bounded memory
attribute-logs-interface | attribute_logs and proxy_log_positions | signature and ordering unchanged, so #1885's keyword passes through
overlap-1872 | edits shared with #1885 and #1889 | whichever run integrates second syncs, reruns both suites and keeps both behaviours
version-collision | Alexandria package version and generation row | each run's final numbers sit above the other's merged values after sync
pinned-digests | test files and sources whose SHA-256 the tree pins | no pinned test file is edited; any pinned source edit is checked against its readers
package-budget | portable runtime files and bytes | the runtime stays under 1,600 files and above the 5 MiB reserve after every step
staging-availability | the two staging trees for the integration cell | both stay matched to their staging manifests until integration
statement-limit | alexandria.py statement for a large release | a statement above 8,388,608 bytes refuses by name and is not raised here
```

## 6. Glossary seeds

- **Attribution part.** A `log-attributions.<k>` component holding one journal
  range's attribution rows.
- **Journal range.** A contiguous run of `shards_per_component` shards, shared
  by `<class>.<k>` journals and part `k`.
- **Receipt v4.** `alexandria-interval-receipt/v4`, the subject receipt whose
  rows moved into parts.
- **Split rule.** The plan field `log_attribution_parts: journal-ranges` and
  the part derivation it declares.
- **Manifest limits.** The byte and node ceilings for `manifest.json` and
  `capture-plan.json`.
- **Grid.** One shard width and one `shards_per_component` for every class, so
  the densest class sets the range count.
- **Pinned identifiers.** The seven release identifiers in section 3.

## 7. Sources

- Issue #1888: <https://github.com/wildcat-finance/skills/issues/1888>.
- Issue #1872 and its study,
  `plugins/alexandria/docs/aave-v3-interval/study.md` at
  `3abcb107e22118427e08e8e23b826bc555d9f613`, lines 459, 468-470, 481, 487,
  491-492 and 524: <https://github.com/wildcat-finance/skills/issues/1872>.
- Pull requests #1883, #1884, #1885 and #1889 at the heads in section 2.
- Issue #1373: <https://github.com/wildcat-finance/skills/issues/1373>.
- Merged pull requests #1875 and #1838, section 2.
- Base sources, all at `17ea8d2ab5e52081370b13b92390b64849ed880d`:
  - `plugins/alexandria/scripts/alexandria_lib/release.py`
  - `plugins/alexandria/scripts/alexandria_lib/canonical.py`
  - `plugins/alexandria/scripts/alexandria_lib/interval.py`
  - `plugins/alexandria/scripts/usdc_interval.py`
  - `plugins/alexandria/scripts/alexandria_lib/index.py`
  - `plugins/alexandria/scripts/alexandria_lib/derivation.py`
  - `plugins/alexandria/scripts/alexandria_lib/compound_phase0.py`
  - `plugins/alexandria/scripts/alexandria_lib/statement.py`
  - `plugins/alexandria/schemas/`
  - `plugins/alexandria/docs/usdc-interval-collector.md`
  - `plugins/alexandria/docs/raw-releases.md`
  - `plugins/alexandria/docs/wildcat-interval/proof.md`
  - `docs/decisions/drafts/venue-dispatch-for-the-interval-collector.md`
- Audit views: the six round files and synopses in section 2.
- Design evidence: `.hexaemeron/design-evidence.json`,
  `.hexaemeron/design/resolve.py`, `.hexaemeron/design/conformance.py`,
  `.hexaemeron/design/build_design_evidence.py`,
  `.hexaemeron/design/observations.json` and
  `.hexaemeron/design/reports/selection/`.
- Parquet: <https://parquet.apache.org/docs/file-format/>.
- Reth: <https://reth.rs/cli/reth/node>.

## 8. Signals, and the questions behind them

`build`, `check` and `verify` are operator-run and offline. The collector is
the unattended path, and this run changes only its plan-time refusal and its
checkpoint limit. The questions someone will ask:

- Why did a build refuse after a completed collection? With the split, a part
  or manifest past its limit refuses by name, naming the component and the
  limit. The plan-time count refuses first in `collect`.
- Which part failed `check`? Every part refusal names `log-attributions.<k>`
  and the shard range, and a row mismatch names the part.
- Will this plan fit before I collect for hours? `journal_components` refuses
  in the collector's constructor, before any request, naming the count and the
  cap.

No new metric or event is added. The named refusals and the collector's
existing structured receipts answer these, as
[ephoros](https://github.com/wildcat-finance/skills/blob/17ea8d2ab5e52081370b13b92390b64849ed880d/plugins/hexaemeron/skills/ephoros/SKILL.md)
requires.

## 9. Boundaries, per capability

- A release given to `check`, `verify`, `index`, `derive` or `statement` is
  untrusted bytes. The manifest parse budget widens sixteen times, to 128 MiB
  and 2,000,000 nodes, so a hostile manifest can cost an estimated 1 GB of
  memory to parse (not measured).
  Controls: the limits are enforced before parsing (`read_confined_file`
  byte bound, `load_bytes` node bound), and every part is read under the
  unchanged 64 MiB and 2,000,000-node bounds. Widening a trust boundary is an
  ask-first action, and the issue asks for this one.
- New part components are parsed from untrusted bytes. Control: closed shape
  and index checks before rows are compared.
- The collector checkpoint is read back from the operator's staging tree.
  Raising its node limit lets a tree for a plan at the cap resume; its byte
  bound stays 8,388,608.
- No subprocess, network path, credential or dependency is added to product
  code. The design resolvers run only fixed `git` and interpreter argv, and
  `phylax.py` reports them clean.

[phylax](https://github.com/wildcat-finance/skills/blob/17ea8d2ab5e52081370b13b92390b64849ed880d/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the list and the controls; risks `older-verifier`, `manifest-limits`,
`manifest-growth` and `part-budget` carry them to the audit loop.

## 10. The budget, or its absence

None is claimed: the run makes no speed or memory promise and changes no
algorithm's cost. It does record a baseline, because the raised caps admit
releases the base memory model cannot hold:

```bash
/usr/bin/time -l python3 plugins/alexandria/scripts/usdc_interval.py check "$ALEXANDRIA_WILDCAT_V2_RELEASE"
```

At the base this peaked at 1,208,811,520 bytes in 4.36 seconds. Step 4
repeats it on the same release, so a reader can see that the memory model did
not move.
[metron](https://github.com/wildcat-finance/skills/blob/17ea8d2ab5e52081370b13b92390b64849ed880d/plugins/hexaemeron/skills/metron/SKILL.md)
owns any later budget; bounded memory would need its own measured one.

## 11. The fail-closed posture

What stops the run:

- a named `AlexandriaError` from any limit, part, receipt or plan check;
- a pinned identifier that does not reproduce;
- a conformance report that refuses at its stop point;
- a red root or Alexandria suite.

A killed build installs nothing, because `ingest` builds in a sibling
temporary directory and renames at the end. A fix a round claims lands with a
`unittest` in `plugins/alexandria/tests/` that fails on the parent commit. Each
step's `Tests` field names the Elenchus command, report format and report
file, and
[elenchus](https://github.com/wildcat-finance/skills/blob/17ea8d2ab5e52081370b13b92390b64849ed880d/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns the triage order and the guard rule.

## 12. Decisions and their homes

Expensive to reverse, once a release ships in the format:

1. The split release format: the plan field, the part component, receipt v4
   and the aligned part rule.
2. The published limits in section 1, which #1872 sizes to.
3. Keeping build and check on today's memory model, as Laurence decided on
   2026-09-23.

All three go in one decision record, created by Step 1 at
`docs/decisions/drafts/split-interval-log-attributions-across-components.md`,
numberless until the merge that lands it. The Alexandria ledger,
`plugins/alexandria/skills/alexandria/EVOLUTION.md`, records the generation.
[hypomnema](https://github.com/wildcat-finance/skills/blob/17ea8d2ab5e52081370b13b92390b64849ed880d/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | split-attribution-parts
record | docs/decisions/drafts/split-interval-log-attributions-across-components.md
```
