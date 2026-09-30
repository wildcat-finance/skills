# Study: build and check an interval release one component at a time

Issue [wildcat-finance/skills#1891](https://github.com/wildcat-finance/skills/issues/1891).
Run branch `fiat/1891-bounded-memory-build-and-check`, cut from `main`
at `150943da240837040478a76c3611d150fa04f2b6`. Controller `fiat-v6.76.1`
(hexaemeron 1.6.90). The design record `.hexaemeron/design-evidence.json`
selects `range-streamed-logs`; its SHA-256 is the one the runbook's
design-lock block names.

## Assumptions

I proceed on these unless corrected.

1. The base is `150943da240837040478a76c3611d150fa04f2b6`. The interpreter is
   Python 3.14.6 from `.python-version`, with stdlib `unittest`. No dependency
   is added. Every gate runs with `NO_COLOR=1` and `FORCE_COLOR` unset.
2. "Hold one component at a time" is read as: between two journal or part
   components, build and check keep no state that grows with the preserved
   logs except one 8-byte key per distinct transaction, and at most the
   opening-topic logs a venue declares. The manifest and four control
   components (plan, registry, reconciliation, epoch table) may stay
   resident; each is already bounded by the manifest limits or the 64 MiB
   component ceiling. Section 4 turns this reading into the gate
   `one-component-at-a-time`. If Laurence wants a looser reading, the
   design changes (see the question under section 4).
3. The acceptance fixture is synthetic, because the release this problem is
   about, a whole Aave V3 interval, needs the `aave-v3-ethereum-main` venue,
   which exists only on the #1872 step branches, and `main`'s `check`
   refuses those releases. The generator builds a constructed Wildcat V2
   plan (subject set, split attribution parts, pinned registry) through the
   real collector and reconciler over a generating transport that opens no
   socket.
4. "Too large for today's memory model to check on the host" means: base
   `check`'s peak, fitted linearly from three smaller releases the same
   generator makes, projects above the host's 137,438,953,472 bytes. The
   base check is never run on the acceptance release itself, because other
   sessions share this host and that run would need more memory than it
   has.
5. The host has about 95 GiB free disk at study time (`df`, 2026-09-30).
   The acceptance release and its staging tree need about twice the
   release's bytes at once; section 3 gives the numbers and the refusal.
6. The two preserved Wildcat staging trees and releases named in section 3
   stay available until integration. #2023 is not fixed inside this run
   (section 3, "Known failures").
7. Aave figures come from issue 1888's committed design files at the base
   commit, each checked by SHA-256 before use, and from the #1872 Step 7
   run as reported to this study (not re-measured here).

## 1. Problem statement, user, and the proving path

**What is built.** `usdc_interval.py build` and `usdc_interval.py check` that
hold one journal or part component in memory at a time, so a release at the
limits #1888 set can be built and checked on the 128 GiB collecting host.

**Why.** At the base commit both commands keep a whole release in memory.
`Builder.build` (`plugins/alexandria/scripts/usdc_interval.py:2925-3026`)
builds every component's document into one `documents` dict before writing
any. `_check_interval` (`usdc_interval.py:3369-3960`) loads every
component's bytes into `component_bytes` and its parsed document into
`documents` (`:3422-3456`), keeps every shard's parsed logs in
`logs_by_shard` (`:3625`) and every boundary header in `boundary_headers`
(`:3617`), parses
every log a second time in `_replay_release_opening` (`:4135-4176`), and
derives every attribution row in one list (`:3898-3901`). Measured on the
preserved V2 release, base `check` peaks at 5.11 times the release's bytes
(section 4), so the host can check a release of at most about 26.9 GB.

**Who uses it.** #1872's Aave V3 capture, whose Step 7 segment releases run
to 12 GB each and whose whole interval would be about 80.6 GB as one
release, and the later Maple, Euler V2 and Centrifuge V3 captures sized to
#1888's limits.

**What a working prototype means.** On `main`'s code, a synthetic release
that today's model cannot check on the host builds and checks with each
command's peak at most 4,294,967,296 bytes, measured with `/usr/bin/time
-l`; every pinned release identity reproduces; and a release that fits
today keeps its bytes.

**Success criteria.** Each is settled by a command.

1. Before Step 2 opens, `python3 .hexaemeron/design/conformance.py todays-model-projects-past-the-host --candidate range-streamed-logs`
   exits 0: the base commit's `check`, fitted over three generated releases,
   projects the acceptance release's peak at no less than 137,438,953,472
   bytes, and the report records the acceptance generator's parameters.
2. Before Step 3 opens, the same resolver exits 0 for
   `walk-matches-whole-list-derivation`: the shared log walk returns, for
   every fixture and hostile case, the rows `proxy_log_positions` and
   `attribute_logs` return at the base commit, and the same refusal text.
3. Before Step 4 opens, it exits 0 for `streamed-check-keeps-every-refusal`
   and `check-peak-independent-of-size`: the Alexandria suite's check tests
   pass unchanged, the new precedence cases pass, and `check`'s traced peak
   on a synthetic release four times larger exceeds the smaller one's by at
   most 8,388,608 bytes plus 16 bytes per added log.
4. Before Step 5 opens, it exits 0 for `build-peak-independent-of-size`
   (the same bound for `build`) and `killed-build-installs-nothing`.
5. At integration it exits 0 for `acceptance-release-within-stated-peak`
   (`build` and `check` of the acceptance release each at most
   4,294,967,296 bytes maximum resident), `v2-check-peak-halved` (V2 `check`
   at most 620,273,664 bytes), `v2-check-cpu-within-budget` (at most 9,400
   ms of user plus system time) and `pinned-release-identities-reproduce`.
6. At every step's exit, with `NO_COLOR=1` and neither staging variable set:
   `python3 -m unittest discover -s tests`,
   `python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria`
   and `python3 scripts/run_checks.py` exit 0.

**Proving path.** From the run worktree's root, with disk to spare
(section 3):

```bash
export NO_COLOR=1 PYTHONDONTWRITEBYTECODE=1
unset FORCE_COLOR
export ALEXANDRIA_WILDCAT_V1_RELEASE=<preserved V1 release>
export ALEXANDRIA_WILDCAT_V2_RELEASE=<preserved V2 release>
export ALEXANDRIA_WILDCAT_V1_STAGING=<unpacked V1 staging tree>
export ALEXANDRIA_WILDCAT_V2_STAGING=<unpacked V2 staging tree>
python3 .hexaemeron/design/conformance.py acceptance-release-within-stated-peak --candidate range-streamed-logs
python3 .hexaemeron/design/conformance.py pinned-release-identities-reproduce --candidate range-streamed-logs
```

The first command generates the acceptance staging tree, runs
`/usr/bin/time -l python3 plugins/alexandria/scripts/usdc_interval.py build`
and then `... check` on the result, records both peaks with the host's load
averages, and removes the directory it created.

**What the demonstration observes, and what it does not.** Positive: the
two peaks, the acceptance release's identifier and byte count, and the
refusal-free `check` report. Negative, bounded: the base `check` is shown
over the stated peak only by the fitted projection, not by a run; a real
Aave release is not checked on `main`; the result does not establish a
bound for a hostile release whose logs are nearly all opening-topic logs
(section 9).

## 2. Prior art

### In this repository, verified at the base commit

- `release.py:236-303` `verify` already reads one component at a time:
  each object is read, sized, hashed and parsed for its coverage count, then
  dropped (`del data` at `:284`). `ingest` (`:157-233`) does the same when it
  copies a capture plan's files. Neither needs to change.
- `release.py:56-67` sets `MAX_RAW_COMPONENT_BYTES` 64 MiB, `MAX_COMPONENTS`
  and `MAX_CAPTURES` 16,384, `MAX_MANIFEST_BYTES` 128 MiB and
  `MAX_MANIFEST_NODES` 2,000,000. `interval.py:67-89` sets `MAX_SHARD_WIDTH`
  50,000, `MAX_SHARDS` 4,096, `MAX_JOURNAL_BYTES` 64 MiB and
  `MAX_PAGE_LIMIT` 100,000; `:125-126` `MAX_EPOCHS` 256 and `MAX_SUBJECTS`
  4,096.
- `preserved_result` (`usdc_interval.py:911-945`) refuses a logs page at the
  provider limit, and `check` refuses a second logs read of one shard, so a
  release holds at most `MAX_SHARDS` × (`MAX_PAGE_LIMIT` − 1) = 409,595,904
  logs.
- `proxy_log_positions` (`interval.py:1005-1087`) walks the logs in order
  and keeps four maps: one block hash per block, one transaction hash per
  `(block, transaction)`, one position per transaction hash and the upgrade
  transactions. Because the walk refuses unordered positions, only the third
  map needs the whole interval; the others need the current block and
  transaction. `attribute_logs` (`:1355-1384`) groups rows by subject and
  `_attribute_into` (`:1205-1218`) walks each subject's epochs with one
  cursor.
- Every venue opening phase receives the whole parsed log list:
  `OpeningPhase.__init__` (`usdc_interval.py:1011-1027`) for the single-proxy
  plan, `ImmutableCodeOpening.__init__` at `venues/wildcat_v1.py:205` and
  `venues/wildcat_v2.py:205`. Each validates every position again, and
  each `epochs()` attributes every log again. What they read beyond
  validation is a few logs: the `Upgraded` announcements (`upgrade_logs`,
  `interval.py:1757`; `discover_epochs`, `:1113-1133`) and, for V2, the
  factory's `MarketDeployed` logs (`market_deploy_report`,
  `venues/wildcat_v2.py:472-533`). The preserved V2 release holds 80
  `MarketDeployed` logs and no `Upgraded` log among 74,088; V1 holds
  neither among 1,941.
- `subject_transaction_hashes` (`usdc_interval.py:4355`) derives a shard's
  expected `trace_transaction` request from that shard's logs, which is why
  `check` keeps `logs_by_shard` until the traces components are read.
- `Staging.entries` (`interval.py:916-927`) reads one physical journal file
  at a time, under `MAX_JOURNAL_BYTES`.
- `wildcat_registry.checking_release` (`wildcat_registry.py:492-513`) admits
  the pre-#1880 V2 registry inside `check`. A build run inside it stands in
  for the build that ran before #1880; `tests/test_log_attribution_parts.py:399-424`
  uses it that way.

### The last two merged pull requests that changed the subject

- [#1960](https://github.com/wildcat-finance/skills/pull/1960), merged
  2026-09-28 at `bdcf124b933a37a820d89e29e1d7b81413488150`, moved the V2
  registry pin to the corrected registry and made `build` and `collect`
  refuse the pre-#1880 registry, which the preserved V2 staging tree
  carries. Its carryover `spherex-declaration-source` (duplicate of #1868)
  does not touch this subject and stays with its owner. The refusal it added
  is the cause of the known failures below.
- [#1945](https://github.com/wildcat-finance/skills/pull/1945), merged
  2026-09-27 at `09f2169caeb9e0881e1254b6128d62747a267b2f`, bound every
  `check` read to the bytes `verify` accepted: the manifest must hash to the
  verified identity, and every component read must carry the size and
  SHA-256 the manifest records. This run keeps that binding for every read,
  including the second read of a part. Its carryover `staging-acceptance`
  pointed at #1902, now closed; this run's integration cell runs the staged
  rebuilds that item asked for, with the V2 exception below.

### Audit history

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root and exited 0 with 113 of 113 views
`committed=match`, so the verified synopses were the reading view, grepped
for memory, resident, stream, component and peak terms and read for every
finding id, status, `Covered`, `Not checked`, `Elenchus verdict` and `Leads
not pursued`. Alexandria keeps no plugin-level `audit/AUDIT.md`.

| Source | View read | Source SHA-256 | Findings |
| --- | --- | --- | --- |
| `audit/rounds/fiat-1888-epoch-table-split-and-release-caps.md` | its `.synopsis.md` | `204e233e8c62aa148d5760cc6efc764f645237fddbd2fdb7f5c44ae9dc764d57` | 14, all fixed |
| `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.md` | its `.synopsis.md` | `ff1b2a5396722ec03925962ac9f2aa63ce6e70e058cf1f8d4e4e61963d0c9820` | W1-R1-02, W6-R4-01, W7-R1-01 and W8-R1-01 open or awaiting an amendment; the rest fixed |
| `audit/rounds/fiat-1503-attribute-implementation-epochs-by-transact.md` | its `.synopsis.md` | `c891e8447d23611d5d0eaec79fbef1b7b80dd45fc0dd1e9fd5a987651d851bf1` | 2, fixed |
| `audit/rounds/fiat-1350-alexandria-1-interval-collector-run-against.md` | its `.synopsis.md` | `213d75ae346bbd6060aa330162179a215ec7f034dec961ce020404b37e47146e` | 18, fixed |
| `audit/rounds/fiat-395-resumable-ethereum-usdc-interval-collector.md` | its `.synopsis.md` | `e9369df1f8647f839e9fd43940154a8c950a8c5db907f5a56aa51c5071b620ec` | 25: 20 fixed; S1-R1-07, S2-R1-04, S5-R1-04, S5-R1-05, S6-R1-03 open |
| `audit/rounds/fiat-391-unified-live-and-archive-collection.md` | its `.synopsis.md` | `f4c89aafa550efb533c3577656de1cc394589a29d41b5d24ba59b44aa855d642` | 11, fixed |
| `audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.md` | its `.synopsis.md` | `ce1d705337f3f53cea1d3621851f05635ccf648c7df4d6db1c842c6113b19476` | 4, fixed |
| `audit/AUDIT.md`, Alexandria's Compound Phase 0 and Goldfinch rounds | `audit/AUDIT_SYNOPSIS.md` | `d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d` | none on build or check memory |

What bears on this run:

- 1888 carried risk `memory-growth` ("peak memory stays measured and stated;
  nothing claims bounded memory") through every round as reviewed, and its
  Step 4 proof measured that the memory model did not move. This run is the
  one that moves it, so that risk becomes this run's acceptance.
- 1888 Step 1 round 7, lead (2): a check-then-read gap for a release changed
  during a run. #1945 closed it for `check`. This design reads each part
  twice and the build reads each staged logs journal twice; both re-reads
  are bound again (risk `second-read-binding`).
- 1888 Step 4 round 2, lead (2): `HostileManifestRecordTests` pins a whole
  phrase of `docs/decisions/drafts/split-interval-log-attributions-across-components.md`.
  This run supersedes that draft's third decision in a new draft and does not
  edit the old one.
- 1503's rounds record "no duration or memory figure was measured"; nothing
  to carry.
- The open 1731 and 395 items concern those runs' own study, runbook,
  package ceilings and one restored-prose item. None assigns work to this
  run.

### Concurrent work

- [#1872](https://github.com/wildcat-finance/skills/issues/1872) runs as
  stacked branches; its Step 7 head is
  `5d5ec5e142d83140a0967fe13ad3498df3df2015`, merge base with `main`
  `d162d0952782f09659370b6a554c9cd4511b8db9`. Its venue
  `venues/aave_v3.py` passes the whole log list to `proxy_log_positions` in
  its own opening phase, as the Wildcat venues do. Of this design's 27 edit
  sites, 14 are ones that head changes (section 4). Whichever run
  integrates second syncs, and the Aave venue then declares its opening logs
  under the rule in section 4.
- [#1892](https://github.com/wildcat-finance/skills/issues/1892) (statement
  limit) will run beside this one. Its branch
  `fiat/1892-statements-past-the-8-mib-limit` touches `statement.py`, which
  this design does not edit; both bump Alexandria's version.
- [#1373](https://github.com/wildcat-finance/skills/issues/1373) owns the
  collection manifest that `plan-sized-releases` would lean on.

### Outside this repository

- Python's `tracemalloc` traces allocations made while tracing; it is the
  in-process measure the size-independence tests use:
  <https://docs.python.org/3.14/library/tracemalloc.html>.
- `array.array("Q")` stores fixed-width unsigned 8-byte integers without a
  Python object per item: <https://docs.python.org/3.14/library/array.html>.
- The reading of a release as ordered, independently bound parts follows
  Parquet's row groups, which a reader handles one at a time:
  <https://parquet.apache.org/docs/file-format/>.

## 3. Constraints and non-goals

**Starting point and tools.** Base `150943da240837040478a76c3611d150fa04f2b6`
on `main`; run branch `fiat/1891-bounded-memory-build-and-check`;
Python 3.14.6; controller `fiat-v6.76.1`. The Hexaemeron suite, if touched,
runs through `python3 plugins/hexaemeron/tests/run_tests.py`.

**Byte identity.** Every release that fits today keeps its identifier.
Measured at the base on 2026-09-30:

- `sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa`, `usdc-interval-v0` demonstration, build and verify exit 0.
- `sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036`, `usdc-interval-epochs-v0`.
- `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a`, current Compound, built by the epochs demonstration.
- `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32`, the historical live demonstration.
- `sha256:fccc014cd400f553814b58911bb06cd450f395e6145e21c0071a06b092b181ec`, `credit-history-v0`.
- `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`, Wildcat V1: the V1 demonstration rebuilds it, and `check` of the preserved release returns it.
- `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`, Wildcat V2: `check` of the preserved release returns it with `v3-subject-positional`, and the V2 demonstration's `build()` run inside `wildcat_registry.checking_release()` rebuilds it (three runs, identical).
- Committed releases `sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab` (Compound Phase 0) and `sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f` (proof-backed state) verify.
- The fixture release identifiers the Alexandria suite pins, `TODAYS_BYTES` and `PRE_1880_RELEASE_IDS` in `tests/test_log_attribution_parts.py`, keep passing.

**Known failures.** With both staging variables set, 4 tests fail at the
base with "Wildcat V2 registry bytes do not match the pinned registry":
`WholePreservedRebuildTests` `setUpClass` in
`tests/test_wildcat_estates_interval_demo.py`,
`test_actual_shared_logs_agree_across_both_captures_and_keep_sentinel_absence`
in `tests/test_wildcat_v1_interval_demo.py`, and
`test_the_rebuild_reproduces_the_pinned_identifier` and
`test_verify_compares_every_pinned_identity_and_the_cli_agrees` in
`tests/test_wildcat_v2_interval_demo.py`. Reproduced here: `Ran 6 tests,
FAILED (errors=4)`. The cause is #1960's refusal of the pre-#1880 registry in
`build`, which every staged V2 rebuild reaches; the driver measured the
staged suite at 1,190 of 1,190 passing at `09f2169c`, before #1960. It is
filed as [#2023](https://github.com/wildcat-finance/skills/issues/2023)
(`only-pr-needed`). The run handles it this way:

1. Step exits run the Alexandria suite with neither staging variable set, so
   those tests skip as they do in hosted CI.
2. V2 identity is proven by the `pinned-release-identities-reproduce` cell:
   `check` of the preserved V2 release, and a rebuild of the preserved V2
   staging through the new `Builder` inside `checking_release()`. That
   rebuild returns `2de87cbd…` at the base, so it isolates this run's change.
3. The estates demonstration is left out of the cell while #2023 is open. If
   #2023 has merged by the integration sync, the cell runs it too, and the
   staged suite must then pass whole.

No audit record names these failures, so the study carries no formal
known-failure inventory block; the list above is the whole inventory.

**External dependencies.** On the collecting host:

- V1 staging:
  `/Users/c0rtexzer0/Projects/wildcat-skills/tmp/fiat-evidence/fiat-1731-venue-agnostic-interval-capture-for-both-wi/step10-capture-narrow/staging`.
- V2 staging: `.../step9-repair-20260921/staging-concurrent` under the same
  directory.
- Releases: `.../step11-cli-v1-release` and `.../step11-cli-v2-release`,
  through `ALEXANDRIA_WILDCAT_V1_RELEASE` and `ALEXANDRIA_WILDCAT_V2_RELEASE`.

**Disk.** The acceptance release is sized from the fitted base factor. If
the generator's factor lands where V2's does (5.11), a release projecting
1.1 times the host is about 29.6 GB; at V1's 7.09 about 21.3 GB; at the
#1872 segment's reported 3.19, 47.4 GB. Staging and release together need
about twice that. The generator refuses by name to start unless the free
disk is at least 2.5 times its planned release bytes, removes its own
directories after the run, and never writes under the capture directories
or another run's tree. If the fitted factor would need more disk than the
host has, the Step 1 cell fails and the run stops for a decision rather
than shrinking the acceptance.

**Versions.** The required `invariants` check runs `scripts/plugin_release.py`,
which refuses a change under `plugins/alexandria/` without a version rise over
its own base. Each step raises Alexandria's package version in four places:

- `plugins/alexandria/.claude-plugin/plugin.json`;
- `plugins/alexandria/.codex-plugin/plugin.json`;
- the Alexandria entry in `.claude-plugin/marketplace.json`;
- the pin in `tests/test_version_propagation.py`.

The number is a checked property, not a literal: it must be above `main`'s
and above every version any `origin` branch claims in
`plugins/alexandria/.claude-plugin/plugin.json`, re-read immediately before
each push. At study time `main` is 0.7.31, the #1872 Step 7 branch claims
0.7.33 and #1892's branch 0.7.31, so the first rise is at least 0.7.34. The
skill generation moves once, through the runbook's `version-relations` block
for `plugins/alexandria/skills/alexandria/EVOLUTION.md`; the last step writes
the row and the frontmatter version in `SKILL.md`. The held frontier job
(`transaction-index-reconciliation`) is unchanged.

**Digests the tree pins.** Checked by grepping each candidate file's SHA-256
across the tree:

- No digest of `usdc_interval.py`, `interval.py`, `release.py`,
  `docs/usdc-interval-collector.md`, `SKILL.md`, `EVOLUTION.md` or any
  Alexandria test module this run would touch appears in the tree.
- `venues/wildcat_v1.py`, `venues/wildcat_v2.py`, `venues/compound_v3.py`
  and `venues/__init__.py` are pinned by Ariadne's
  `examples/wildcat-datasets-v0` records and V1's `rebuild-record.json` at
  historical revision `104f6f82c390003fb61039d3023d07c1abe05086`. No test or
  demonstration compares those digests with the working files, so editing
  them moves nothing there.
- `tests/test_release.py`, `tests/test_demo.py` and `tests/run_tests.py` are
  pinned by root fixtures and demonstration evidence; they do not change.
  New tests go in new modules.

**Horos.** Every step runs
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`, then
`... scan . --census --write`, before `.githooks/greenlight`, and stages both
`.horos/boundary.json` and `.horos/census.json`.

**Package budget.** `python3 scripts/portable_promise_machine.py measure` at
the base: 1,525 files against the 1,600 tripwire and 2,062,549 bytes of
margin. The committed design folder (study, runbook, record, proof, five
scripts, observations, 24 selection reports and 10 conformance reports) adds
about 45 files, and #1872 and #1892 add their own. Step 1's exit measures
the margin after the copy.

**Non-goals.**

- Changing the release format, a receipt, a schema or #1888's limits.
- Making `collect`, `reconcile`, `derive`, `index` or `statement` stream.
  `Reconciler` still loads a shard's logs (`usdc_interval.py:2575`).
- Fixing #2023.
- Admitting the Aave venue on `main`, or checking an Aave release here.
- A time budget beyond the V2 CPU ceiling; the build reads staged logs
  twice.
- Removing the hidden sibling temporary directories a killed build leaves
  (`.<name>.plan-*`, `.<name>.tmp-*`), which today's build also leaves.

**Carried forward.** Candidates for the run-level `carryover` block, settled
at integration:

- `v2-staged-rebuild`: duplicate of #2023.
- `aave-opening-logs`: none; #1872's integration sync declares its venue's
  opening logs.
- `streaming-collect-and-reconcile`: none unless a capture measures a
  `reconcile` peak above the host; nothing in view does.

**Boundaries.**

- Always: the root and Alexandria suites and `scripts/run_checks.py` before a
  commit; Imprimatur on every shipped document; the Horos pair regenerated
  in the commit that changes the tree; a version rise above every claimed
  version in every step touching Alexandria; a recorded measurement, with
  the load averages beside it, before and after the memory change.
- Ask first: adding a dependency; changing a published release byte,
  identifier, receipt or schema; adding a refusal a release that checks today
  could reach; touching CI; widening a trust boundary.
- Never: rewrite a pinned release, expected file, audit record or historical
  study; commit a staging tree, endpoint or credential; delete or weaken a
  failing test; run the base `check` on the acceptance release; write into
  the capture directories or another run's tree; claim a measurement or
  demonstration that did not run.

## 4. Design options

### What was measured

At the base commit on the collecting host (Apple M5 Max, 18 CPUs,
137,438,953,472 bytes of memory), three runs each, load averages 11.1 to
12.1 over one minute:

| Run | Peak resident bytes | Seconds | CPU seconds |
| --- | --- | --- | --- |
| `check`, Wildcat V2 (242,722,051 bytes) | 1,240,432,640 to 1,241,464,832, median 1,240,547,328 | 4.83 to 5.02 | 4.66 to 4.83, median 4.70 |
| `check`, Wildcat V1 (20,496,046 bytes) | 144,621,568 to 145,342,464 | 0.41 to 0.48 | 0.40 to 0.45 |
| V1 demonstration `build` | 161,677,312 to 163,840,000 | 0.77 to 0.96 | 0.73 to 0.88 |
| V2 `build()` inside `checking_release()` | 1,242,628,096 to 1,268,170,752 | 10.15 to 10.59 | 9.84 to 10.05 |

Base `check` peaks at 5.11 times V2's bytes and 7.09 times V1's. Reported by
the #1872 Step 7 run and not re-measured: Aave segment 4,
`sha256:5d298fe06928bd319b490a7848469917ada7fe36ac106b9569187a68dc16daa4`,
9,330,298,807 bytes, 3,399 components and 2,390,299 attribution rows,
built in 156 s at a 14.83 GB peak and checked in 199 s at a 29.79 GB peak,
3.19 times its bytes.

Per-unit costs on the preserved V2 release, traced with `tracemalloc` under
the base commit's own parser:

- A parsed log costs 1,280 bytes and an attribution row 699 bytes.
- A compact index entry (position, subject, first topic, block and
  transaction hashes shared per block and transaction) costs 219 bytes a log.
- V2's 74,088 logs sit in 15,298 transactions.
- One component's working set (its bytes, its document, one record's
  response at a time) peaks at 2.96 to 3.00 times its bytes for journals and
  4.39 times for the epoch table.
- A row costs 327.51 bytes of JSON, and a logs journal 1.5357 bytes per
  response byte.

`.hexaemeron/design/observations.json` records every run, its argv and the
load averages.

### Candidates

1. `plan-sized-releases`. No code change. Build and check keep today's
   model, and a venue ships as many releases as the host can check, joined
   by #1373's collection manifest. Trade: nothing to build, but the host
   checks at most about 26.9 GB a release, so Aave needs at least 3 and a
   release at #1888's limits cannot be checked at all.
2. `stream-bytes-hold-logs`. Both commands read or write one component at a
   time and drop its bytes and document, but keep every parsed log and every
   attribution row as today. Trade: the fewest edits, and the whole Aave
   interval fits (about 66.5 GB), but state still grows 3,259 bytes a log,
   so a release at #1888's limits needs about 1.34 TB.
3. `compact-log-index`. One component at a time, plus a compact index of
   every log that the opening replay, the epochs and the row derivation read
   after the journal pass. Trade: no staged log is read twice and the
   format-limit release fits (about 92.2 GB), but state still grows 219
   bytes a log, and the parts are read twice in `check`.
4. `range-streamed-logs`. One component at a time. A shared log walk
   validates positions and derives rows range by range, keeping only the
   current block and transaction, per-subject epoch cursors and an 8-byte key
   per transaction. Venues see only the logs whose topic they declare.
   `check` attributes each range with the receipt's own epochs and holds any
   refusal until the point today's code raises it; `build` reads each staged
   logs journal twice. Trade: the most edits and the most sites shared with
   #1872, and about 28.4 GB of extra reads on the Aave interval, for a peak
   that no longer depends on the log count beyond 8 bytes a transaction.

### Criteria and results

`python3 .hexaemeron/design/resolve.py <criterion> --candidate <id>` wrote
every selection report under `.hexaemeron/design/reports/selection/`, and a
rerun reproduced all 24 byte for byte. Gates first; each peak is the
candidate's model evaluated with the measured costs above:

| Criterion | Concern | Rule | plan-sized | stream-bytes | compact | range |
| --- | --- | --- | --- | --- | --- | --- |
| `aave-interval-checks-on-host` | space | ≤ 137,438,953,472 | 411,903,222,444 fail | 66,521,524,616 | 6,802,238,536 | 2,657,248,614 |
| `format-limit-release-checks-on-host` | space | ≤ 137,438,953,472 | 5,620,266,925,753 fail | 1,337,373,143,734 fail | 92,201,595,574 | 5,776,859,830 |
| `one-component-at-a-time` | space | ≤ 16 | 16,745 fail | 3,259 fail | 219 fail | 8 |

Then the metrics, each minimised:

| Criterion | Concern | plan-sized | stream-bytes | compact | range |
| --- | --- | --- | --- | --- | --- |
| `extra-journal-bytes-read` | time | 0 | 0 | 6,433,770,850 | 28,388,775,602 |
| `edit-sites` | time | 0 | 7 | 24 | 27 |
| `sites-shared-with-1872` | compatibility | 0 | 7 | 13 | 14 |

What each value is:

- The Aave release is issue 1888's whole-interval model: 80,591,842,575
  bytes and 19,644,502 logs, recovered from 1888's pinned check-peak report
  and coefficient.
- The format-limit release is 16,384 components of 67,108,864 bytes plus a
  134,217,728-byte manifest, 1,099,645,845,504 bytes, holding 409,595,904
  logs.
- `plan-sized-releases` is 5.11 times the release's bytes. The streaming
  candidates are a working set plus their per-log state times the logs. The
  working set is eight component ceilings at the worst measured ratio (the
  manifest twice for its 128 MiB limit, the four resident control
  components, one logs range and one part) plus one part's rows as derived,
  2,500,092,598 bytes.
- `one-component-at-a-time` is the state a candidate carries between
  components per preserved log. For `plan-sized-releases` it is the whole
  release, V2's median check peak over its logs.
- `extra-journal-bytes-read` counts reads beyond today's for the Aave
  release: a candidate that does not keep the rows reads each part twice in
  `check` (6,433,770,850 bytes), and `range-streamed-logs`' build also reads
  every staged logs journal twice (21,955,004,752 bytes).
- `edit-sites` counts declared sites, each checked to exist at the base, or
  to be absent for a new file. `sites-shared-with-1872` counts the sites
  whose source differs between #1872's merge base and Step 7 head, reading
  `_check_interval` under its earlier name `check_interval`.

Ten conformance gates stay pending for every candidate; only the selected
candidate's fall due, each at its stop point:

| Criterion | Concern | Stop point | Evidence |
| --- | --- | --- | --- |
| `todays-model-projects-past-the-host` | space | `step:2` | base `check` fitted over three generated releases, projected ≥ 137,438,953,472 bytes |
| `walk-matches-whole-list-derivation` | correctness | `step:3` | `tests.test_log_walk` |
| `streamed-check-keeps-every-refusal` | correctness | `step:4` | the suite's check tests unchanged, and `tests.test_streamed_check` precedence cases |
| `check-peak-independent-of-size` | space | `step:4` | `tests.test_streamed_check` traced-peak case |
| `build-peak-independent-of-size` | space | `step:5` | `tests.test_streamed_build` traced-peak case |
| `killed-build-installs-nothing` | recovery | `step:5` | `tests.test_streamed_build` killed-child cases |
| `acceptance-release-within-stated-peak` | space | `integration` | `/usr/bin/time -l` of `build` and `check` on the acceptance release, each ≤ 4,294,967,296 |
| `v2-check-peak-halved` | space | `integration` | V2 `check` ≤ 620,273,664 bytes |
| `v2-check-cpu-within-budget` | time | `integration` | V2 `check` ≤ 9,400 ms user plus system |
| `pinned-release-identities-reproduce` | compatibility | `integration` | every identifier in section 3 |

`python3 .hexaemeron/design/conformance.py <criterion> --candidate range-streamed-logs`
resolves each and writes its report under
`.hexaemeron/design/reports/conformance/`, create-only. Step 1 creates it; it
refuses any other candidate by name and refuses a cell whose test module or
generator does not exist yet.

### Selection

Three candidates fail a selection gate, so `range-streamed-logs` is the only
survivor and the non-dominated frontier under `unique-frontier`.
`design_evidence.py --transition design-lock` exits 0. The metrics record the
trade: the selected design costs the most edits, the most overlap with
#1872 and the most extra reads.

**Question for Laurence.** The `one-component-at-a-time` gate is how this
study reads the issue's title. `compact-log-index` passes both host gates and
fails only that one. If a looser reading is wanted, the design changes to
`compact-log-index` (fewer reads, 219 bytes a log, about 92.2 GB at the
format limit). This study proceeds on the literal reading.

### The selected design

**The log walk.** A new `alexandria_lib/log_walk.py` holds one `LogWalk`
fed logs in plan order, one shard's result at a time. It applies every rule
`proxy_log_positions` applies, with bounded state:

1. the previous position, for the ordering rule;
2. the current block's hash and the current transaction's hash, for the two
   contradiction rules that the ordering rule makes local;
3. the upgrade positions seen, and the ordinary logs of the current
   transaction, held until the transaction ends, for the upgrade-transaction
   rule;
4. one 8-byte key per distinct transaction (the first 8 bytes of its hash),
   in 256 `array("Q")` buckets by first byte.

After the pass, each bucket is sorted on its own. A repeated key is either a
transaction hash at two positions or a key collision; the walk then reads
the logs once more, collecting full hashes for the repeated keys only, and
refuses with today's message and coordinate or continues. Given epochs, the
walk also attributes each log with one cursor per subject, as
`_attribute_into` does, and yields each row.

`proxy_log_positions` and `attribute_logs` become whole-list wrappers over
the walk. Their rows, row order and refusal text do not change, so every
existing caller and test keeps its result.

**Opening logs.** Each venue declares which logs its opening phase and gaps
read: `Upgraded` announcements for the single-proxy plan, `MarketDeployed`
logs from the factory for Wildcat V2, none for V1. The walk hands only those
to `opening_phase`, `epochs_from_opening` and `evidence_gaps`; the positions
of all the others were already checked by the walk. For a plan whose logs
include upgrades, `discover_epochs` receives only the `Upgraded` logs and
selects the same boundaries. A release whose opening-topic logs pass
1,048,576 (`MAX_SUBJECTS` × `MAX_EPOCHS`) refuses by name; no release in view
holds more than 80.

**Check, in today's order.**

1. `verify` as today.
2. The manifest, plan, registry, reconciliation and epoch table stay
   resident. The implementation code is read, re-hashed and dropped; any
   refusal is held until today's point.
3. The parts are read one at a time for their shape (`_check_attribution_parts`).
4. The journals are read one at a time in today's order. For each shard the
   check keeps its record counts, its boundary block number and hash, and
   the SHA-256 of the `trace_transaction` request its logs derive, in place
   of `logs_by_shard`. Each logs range is fed to the walk, attributed with the
   receipt's epochs, and compared with its part (read again and bound to the
   manifest again) or with its slice of an unsplit receipt's rows.
5. After the loop, each refusal the walk or a comparison found is raised
   where today's code raises it: position refusals just before the opening
   replay, the code-digest refusal after it, the epoch comparison, then any
   row mismatch, then the first-code rows, the venue gaps, the scopes and the
   journal bindings.

A row mismatch against an epoch table that also fails the epoch comparison
therefore still reports the epoch table, as today.

**Build.**

1. Pass one reads each staged logs journal once, runs the walk and collects
   the opening logs.
2. The opening replay and the epochs follow as today.
3. Pass two writes components one at a time into the plan directory: for
   each range, the logs component and its part come from one more read of
   that staged file, bound again to the reconciliation record's journal
   digest; other journals are written from their own files.
4. The epoch table is written last, once the part row counts are known.
5. `ingest` and `verify` run as today.

An unsplit plan's rows sit in the epoch table, which the 64 MiB ceiling
already bounds, so they are kept until it is written.

**Documents.** `docs/usdc-interval-collector.md` states the memory model:
what stays resident, the per-transaction key, the opening-log rule and its
limit, and the two reads.

### Steps and stop points

The stop points fix this order. Each conformance cell blocks the transition
after the step that builds it, which Fiat checks when that step's push opens
the next one:

1. Scaffold and today's model: copy the study, runbook, record,
   `.hexaemeron/design/` scripts, observations and reports to
   `plugins/alexandria/docs/bounded-memory-interval/`, write
   `.hexaemeron/design/conformance.py`, the deterministic generator with its
   disk refusal, and create the decision draft named in section 12. The three
   base-commit `check` runs (from a `git archive` of the base) produce the
   `step:2` report. No product change.
2. The log walk, the whole-list wrappers, the venue opening-log
   declarations and `tests/test_log_walk.py`, for the `step:3` report.
   Release bytes unchanged.
3. The streamed `check` and `tests/test_streamed_check.py`, for the two
   `step:4` reports.
4. The streamed `build` and `tests/test_streamed_build.py`, for the two
   `step:5` reports.
5. Demonstration: the acceptance release, the V2 figures, the pinned
   identities, `proof.md`, the collector document and the generation row, for
   the four `integration` reports.

Each step is green at both ends: Step 1 touches no product code, Step 2
changes no caller's result, and Steps 3 and 4 each change one command.

## 5. Risk register seed

```risk-register
byte-identity | release bytes for every plan build accepts today | every identifier in section 3 reproduces and the suite's fixture identifiers still pass
refusal-order | check's refusals on a release with more than one defect | each refusal is raised at the point today's code raises it, so the first message is today's
walk-equivalence | the walk and its whole-list wrappers | rows, row order and refusal text equal the base proxy_log_positions and attribute_logs on every fixture and hostile case
transaction-keys | the 8-byte transaction keys and their collision path | a repeated transaction hash refuses with today's message and coordinate; a forced key collision refuses nothing
opening-logs | the logs each venue opening phase and evidence_gaps receive | each venue declares its topics, epochs and gaps equal today's, and the 1,048,576 limit refuses by name
second-read-binding | the second read of a part in check and of a staged logs journal in build | each re-read is bound again to the manifest or the reconciliation digest, and a changed file refuses by name
resident-set | what stays in memory between components | only the manifest, four control components, per-shard scalars, opening logs and transaction keys persist
peak-measurement | the stated peaks and the load beside them | each peak is /usr/bin/time -l maximum resident set size with uptime's load recorded, three runs where the budget is close
killed-build | a build stopped by SIGKILL at any point | no release appears at the output path and a rerun builds the same identifier
acceptance-sizing | the synthetic acceptance release | today's fitted model projects past the host, the release is at least the planned size, and the base check never runs on it
disk-headroom | the generator's staging and release | it refuses without 2.5 times its planned bytes free and removes only the directories it created
v2-known-failure | the four staged tests #2023 breaks | they are not counted green; V2 identity comes from check and the checking_release rebuild
overlap-1872 | edits shared with the #1872 step branches | whichever run integrates second syncs, reruns both suites and declares the Aave venue's opening logs
version-collision | Alexandria package version and generation row | each push's version sits above every version any ref claims, re-read before the push
pinned-digests | files whose SHA-256 the tree pins | no pinned test file is edited, and the pinned venue digests stay historical records
package-budget | the portable runtime's files and bytes | the runtime stays under 1,600 files and within its byte margin after every step
```

## 6. Glossary seeds

- **Log walk.** The ordered, bounded-state pass over preserved logs that
  validates positions and yields attribution rows.
- **Transaction key.** The first 8 bytes of a transaction hash, one per
  distinct transaction, kept for the cross-interval uniqueness rule.
- **Opening logs.** The logs a venue declares its opening phase and gaps
  read; every other log is only walked.
- **Held refusal.** A refusal found early and raised at the point today's
  code raises it.
- **Resident set.** What stays in memory between components: the manifest,
  plan, registry, reconciliation, epoch table, per-shard scalars, opening
  logs and transaction keys.
- **Today's model.** Base `check`'s peak as a linear function of release
  bytes, fitted on the generator's releases.
- **Acceptance release.** The generated release that today's model projects
  past the host.
- **Stated peak.** 4,294,967,296 bytes of maximum resident set size, for
  `build` and for `check` of the acceptance release.

## 7. Sources

- Issue #1891: <https://github.com/wildcat-finance/skills/issues/1891>.
- Issue #1888 and its committed records under
  `plugins/alexandria/docs/epoch-table-split/` at the base:
  <https://github.com/wildcat-finance/skills/issues/1888>.
- Pull requests #1960 and #1945, section 2.
- Issues #1872, #1892, #1373 and #2023, section 2 and 3.
- #1872 Step 7 head `5d5ec5e142d83140a0967fe13ad3498df3df2015` and merge
  base `d162d0952782f09659370b6a554c9cd4511b8db9`.
- Base sources, all at `150943da240837040478a76c3611d150fa04f2b6`:
  - `plugins/alexandria/scripts/usdc_interval.py`
  - `plugins/alexandria/scripts/alexandria_lib/interval.py`
  - `plugins/alexandria/scripts/alexandria_lib/release.py`
  - `plugins/alexandria/scripts/alexandria_lib/canonical.py`
  - `plugins/alexandria/scripts/alexandria_lib/wildcat_registry.py`
  - `plugins/alexandria/scripts/alexandria_lib/venues/`
  - `plugins/alexandria/docs/usdc-interval-collector.md`
  - `plugins/alexandria/tests/test_log_attribution_parts.py`
  - `docs/decisions/drafts/split-interval-log-attributions-across-components.md`
- Audit views: the seven round files and synopses and the root pair in
  section 2.
- Design evidence: `.hexaemeron/design-evidence.json`,
  `.hexaemeron/design/resolve.py`,
  `.hexaemeron/design/build_design_evidence.py`,
  `.hexaemeron/design/observations.json` and
  `.hexaemeron/design/reports/selection/`.
- Python `tracemalloc`: <https://docs.python.org/3.14/library/tracemalloc.html>.
- Python `array`: <https://docs.python.org/3.14/library/array.html>.
- Parquet: <https://parquet.apache.org/docs/file-format/>.

## 8. Signals, and the questions behind them

`build` and `check` are operator-run and offline; the unattended collector
does not change. The questions an operator will ask:

- Will this release check on this host? The collector document states the
  bound: the resident set plus 8 bytes a transaction, about 2.5 GB at the
  component ceilings. No new output is needed to answer it.
- Why did a release that used to check now refuse? It should not; a refusal
  names its component, shard and rule as today, and `refusal-order` keeps the
  first message today's.
- Which range failed? Every part and row refusal names `log-attributions.<k>`
  and its shards, as today.

No metric or event is added. The named refusals and the peaks this run
records answer these, as
[ephoros](https://github.com/wildcat-finance/skills/blob/150943da240837040478a76c3611d150fa04f2b6/plugins/hexaemeron/skills/ephoros/SKILL.md)
requires.

## 9. Boundaries, per capability

- A release given to `check` is untrusted bytes. The design keeps #1945's
  binding for every read and adds one re-read per part, bound to the
  manifest's size and SHA-256 again (risk `second-read-binding`).
- A staging tree given to `build` is the operator's, but it is read twice;
  the second read is bound to the reconciliation record's journal digest, so
  a tree changed between reads refuses by name.
- Memory is a resource a hostile release can try to exhaust. Journal and
  part working sets are bounded by the component ceiling. Opening-topic logs
  are held whole, so a release whose logs are all opening-topic logs could
  make `check` hold up to 1,048,576 of them (about 1.34 GB at 1,280 bytes)
  before the new limit refuses; this is outside the stated peak and is named
  as such. The limit is an ask-first item because it is a new refusal; no
  release that checks today comes near it.
- A transaction-key collision only costs one more read of the logs; it
  never admits a release.
- No subprocess, network path, credential or dependency is added to product
  code. The design resolvers run only fixed `git` reads, the base commit's
  own `check` from a `git archive`, and `/usr/bin/time`.

[phylax](https://github.com/wildcat-finance/skills/blob/150943da240837040478a76c3611d150fa04f2b6/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the list and the controls; risks `second-read-binding`, `opening-logs`
and `transaction-keys` carry them to the audit loop.

## 10. The budget, or its absence

This run states a budget, measured as `/usr/bin/time -l` maximum resident set
size with the load averages recorded beside it:

- `build` and `check` of the acceptance release: each at most 4,294,967,296
  bytes.
- `check` of the preserved V2 release: at most 620,273,664 bytes, half the
  base median, and at most 9,400 ms of user plus system time, twice the base
  median.
- In process, `check` and `build`'s `tracemalloc` peak on a synthetic release
  four times larger exceeds the smaller one's by at most 8,388,608 bytes plus
  16 bytes per added log.

```bash
/usr/bin/time -l python3 plugins/alexandria/scripts/usdc_interval.py check "$ALEXANDRIA_WILDCAT_V2_RELEASE"
python3 .hexaemeron/design/conformance.py acceptance-release-within-stated-peak --candidate range-streamed-logs
```

The base figures are in section 4.
[metron](https://github.com/wildcat-finance/skills/blob/150943da240837040478a76c3611d150fa04f2b6/plugins/hexaemeron/skills/metron/SKILL.md)
owns what the budget carries and how it is re-measured.

## 11. The fail-closed posture

What stops the run:

- a named `AlexandriaError` from any check the design keeps or adds;
- a pinned identifier that does not reproduce;
- a conformance report that refuses at its stop point, including a fitted
  projection below the host or a disk refusal in Step 1;
- a peak above its budget;
- a red root or Alexandria suite.

A killed build installs nothing, because the plan directory is temporary and
`ingest` renames only at the end; Step 4 proves it by killing a child build.
`check` writes no file. A fix a round claims lands with a `unittest` in
`plugins/alexandria/tests/` that fails on the parent commit. Each step's
`Tests` field names the Elenchus command, report format and report file, and
[elenchus](https://github.com/wildcat-finance/skills/blob/150943da240837040478a76c3611d150fa04f2b6/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns the triage order and the guard rule.

## 12. Decisions and their homes

Expensive to reverse once a venue sizes its releases to them:

1. The memory model: what stays resident, one component at a time, and the
   8-byte transaction key as the only per-log state.
2. The held-refusal rule, which keeps `check`'s refusal order.
3. The venue opening-log declaration, which #1872's Aave venue must adopt,
   and its 1,048,576 limit.
4. Superseding the third decision in
   `docs/decisions/drafts/split-interval-log-attributions-across-components.md`,
   which kept build and check on today's memory model; that draft is not
   edited, because a test pins its phrases.

All four go in one decision record, created by Step 1 at
`docs/decisions/drafts/stream-interval-build-and-check-one-component-at-a-time.md`,
numberless until the merge that lands it. The Alexandria ledger,
`plugins/alexandria/skills/alexandria/EVOLUTION.md`, records the generation.
[hypomnema](https://github.com/wildcat-finance/skills/blob/150943da240837040478a76c3611d150fa04f2b6/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | range-streamed-logs
record | docs/decisions/drafts/stream-interval-build-and-check-one-component-at-a-time.md
```
