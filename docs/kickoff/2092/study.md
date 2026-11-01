# Study: Wildcat V2 wrapper instances as capture subjects

Task: wildcat-finance/skills#2092 (`Fiat-Required: 1`). Surveyor:
`fiat-2092-study-surveyor`. Target: this repository at `main`
`50d71a2e8c1777f8eb26db32dd8adeadb34063bd`, run branch
`fiat/2092-wildcat-v2-wrapper-instances-as-capture-sub`.

Assuming, unless corrected:

1. The interpreter is the one recorded in `.python-version`, with stdlib
   `unittest`, as every Alexandria suite uses today.
2. Only Alexandria changes. No file under `plugins/tabularium/` changes,
   because the live run for skills#2087 owns that surface.
3. No real wrapper data is collected and no RPC is called. Every new behaviour
   is proved on constructed staging trees through the existing fake transport
   in `plugins/alexandria/tests/test_wildcat_venue.py`.
4. The pinned V2 registry document, its digest
   `d486c7e3a6b31e73adf4b4b35dd43fefa860f684bae0e534935cc13462652283`, the
   pre-#1880 digest
   `1d206f36284ce51d0d23bf843899eef27316a36e5013c3df5d81da92e72ee29f` and the
   V1 digest `84b2b7a7d8d1a928145e06a66970d9d6d0a53f61c2472c1ebc6091d027532835`
   stay byte-identical.
5. The wrapper factory is the registry's one `wrapper-factory` entry,
   `0xea6de11f8f3f83c79bd9d8db5517fcfdf2bb148a`, whose merged records give
   deployment block 24750455 (source `creation-epochs`). Whether every wrapper
   comes from this factory is not established; the issue lists it as not
   checked and this study keeps it unknown.
6. `WrapperDeployed(address,address)` has topic
   `0x317d343bad96f4924450e809267dcfa70e37270e3bb036b5d6d04e3befd47a64`, with
   `market` indexed first and `wrapper` second. The topic was recomputed here
   with `plugins/tabularium/scripts/tabularium_lib/keccak.py` (read only); the
   field order is the declaration at line 17 of
   `src/vault/Wildcat4626WrapperFactory.sol` at v2-protocol commit
   `c7be4039f8f383a9dda4e45f63331c17d63f9ed9`, as Tabularium's ABI table
   records it.
7. A wrapper's code is treated as immutable over its epoch, the same model
   every V2 subject uses. Whether wrapper instances are immutable is not
   established; each wrapper release states it as a gap.

The design proceeds on these unless corrected.

## 1. Problem statement

Alexandria's Wildcat V2 venue cannot hold a wrapper instance as a capture
subject. `plugins/alexandria/scripts/alexandria_lib/wildcat_registry.py:102-117`
pins the V2 role counts, and no role holds a wrapper instance;
`:309-311` refuses an unknown role, `:445-446` refuses other counts and
`:516-528` admits exactly one generated document by digest.
`plugins/alexandria/scripts/alexandria_lib/venues/wildcat_v2.py:86-106`
refuses a plan subject the registry does not list. So no release carries a
wrapper's epoch or its native logs, and Tabularium's three wrapper rules have
nothing to read.

The consumer is anyone who maps a Wildcat V2 release: today Tabularium, later
Probitas through it. They see market-token transfers to or from a wrapper and
have no wrapper-native row to place them against.

What gets built: a V2 interval plan may declare wrapper instances. Each one is
admitted only when a preserved `WrapperDeployed` log from the registry's
wrapper factory names it and names a market the registry lists. Its deployment
block is that log's block, its epoch opens there under the venue's
`immutable-code` model, and its native logs are requested in the same `logs`
journal as every other subject's. The release binds the derived wrapper set as
one component, `wrapper-subjects`, so the manifest's `release_id` binds its
digest. A plan without the new field builds the same bytes it builds today.

A working prototype means the capability runs end to end on constructed data
and the existing release identities hold. These criteria prove it:

1. **Wrapper release.** Over a constructed staging tree whose plan declares
   two wrappers deployed by two preserved `WrapperDeployed` logs,
   `usdc_interval.py build` exits 0 and `usdc_interval.py check <release>`
   exits 0. The check result lists each wrapper with its market, its
   deployment block and log position, its epoch (start block, end block,
   runtime-code SHA-256) and the count of its attributed logs in the `logs`
   journal. The manifest lists a `wrapper-subjects` component, and `check`
   re-derives that component byte for byte from the preserved logs and the
   registry.
2. **Refusals.** Build refuses, and `check` refuses on a release edited to
   carry the case, each of: a `WrapperDeployed` naming a market the registry
   does not list; a declared wrapper with no runtime code at its first block;
   a wrapper log before its epoch's first block; a declared wrapper that no
   preserved `WrapperDeployed` names. Each refusal names the wrapper, and the
   block or market at fault.
3. **Legacy identities.** For a plan without the field, nothing changes: the
   constructed V1 and V2 release identifiers that Step 1 freezes at the base
   reproduce at every step end; the Tabularium suite, which runs
   `check_interval` over its committed raw V1 and V2 releases, passes with no
   Tabularium file changed; and in the last step the preserved V2 release
   `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`
   and V1 release
   `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`
   rebuild from their restored retained trees, with no staged test skipped.
4. **Bounded gaps.** A constructed plan whose interval holds more than 16
   discovered but undeclared wrappers yields 16 named gap sentences and one
   counted sentence, and the capture stays under `MAX_GAPS` (256).
5. **Portable budget.** `python3 scripts/portable_promise_machine.py sync`
   followed by `check` exits 0, and `tests/test_skills_sh_package.py` passes
   inside the root suite. The run adds at most five files and 100,000 bytes to
   the portable payload.

Demo path: Step 4 runs a constructed specimen through collect (fake
transport), reconcile, build and check, prints the wrapper listing, and runs
the four refusals through the same CLI. The specimen and its helper live under
`plugins/alexandria/tests/`, which the portable payload omits.

## 2. Prior art

**This repository.** The V2 venue already has the parts this needs, kept for
registry subjects:

- `ImmutableCodeOpening` (`venues/wildcat_v2.py:192-431`) is built from the
  plan, the registry and the staged logs. It probes each unrecorded subject's
  first code before any shard, makes the remaining opening reads after the
  last shard, and derives one epoch per subject from preserved code and
  header reads.
- `market_deploy_report` (`venues/wildcat_v2.py:472-535`) compares preserved
  `MarketDeployed` logs with the registry's markets and reports missing,
  misplaced and undeclared ones. The wrapper derivation follows its shape.
- `_bounded` and `LISTED_GAPS` (`venues/wildcat_v2.py:64-69, 595-601`) keep
  each scaling gap kind at 16 named sentences plus one count.
- `attribute_logs` (`alexandria_lib/interval.py:1593-1630`) refuses a log with
  no positional epoch owner, and `runtime_code`
  (`alexandria_lib/interval.py:1918-1924`) refuses empty code.
- `shard_requests` (`scripts/usdc_interval.py:1349-1369`) filters `eth_getLogs`
  and `trace_filter` by the plan's `subjects`; the request set derives from
  the plan alone.
- Opt-in plan fields keep old bytes: `shards_per_component`,
  `log_attribution_parts` and `wildcat_event_headers`
  (`alexandria_lib/interval.py:75-88, 241-310`;
  `alexandria_lib/event_headers.py`). A plan without one validates and builds
  exactly as before. The new field follows that pattern.

A release identity is the SHA-256 of the canonical manifest:
`release.py:205-218` hashes the captures, the components (each with its
SHA-256), the format and the release block. Any change to a component's bytes,
a coverage gap sentence or a capture field for an existing plan moves the
identity. So the plan field must be inert when absent: no new component, gap
sentence, receipt field or check-result key for a plan without it.

Pins on what this run might change, found by grepping every tracked file:

- V2 registry `d486c7e3…`: `plugins/tabularium/examples/wildcat-v2-v0/expected.json`
  and four files under its `registry-context/release/`.
- Pre-#1880 registry `1d206f36…`: five files under
  `plugins/ariadne/examples/wildcat-datasets-v0/`,
  `plugins/ariadne/tests/test_wildcat_datasets.py` and
  `docs/kickoff/1384/evidence/inputs.json`.
- V1 registry `84b2b7a7…`: five files in Tabularium's `wildcat-v1-v0` example
  and three in Ariadne's `preserved/v1`.
- V2 release `2de87cbd…` and V1 release `eee71d1e…`: the Alexandria example
  `expected.json` files, which `plugins/alexandria/skills/alexandria/DEMONSTRATION.md`
  pins, plus Ariadne tests and kickoff and audit records.

`plugins/tabularium/scripts/tabularium_lib/wildcat_source.py:376` calls
`usdc_interval.check_interval` on Tabularium's committed raw releases, so an
Alexandria change that makes `check` refuse them breaks the Tabularium suite.
`tests/check-map-v1.json` closes the `alexandria` scope over `repo-lints`,
`tabularium` and `probitas`, so the step runner reaches that suite.
`plugins/ariadne/examples/wildcat-datasets-v0/inputs.json` records Alexandria
source digests at revision `104f6f82`, but
`plugins/ariadne/tests/test_wildcat_datasets.py:80-95` compares only the
example's `inputs/` and `spec/` files, and the recorded
`wildcat_registry.py` digest already differs from the base file, so it is a
historical record, not a live pin. `DEMONSTRATION.md` pins the preserved
examples' `expected.json`, `staging-manifest.json`, `rebuild-record.json` and
`demo.py`; this run changes none of them.

The portable Promise Machine payload, regenerated here with
`python3 scripts/portable_promise_machine.py sync`, holds 1,629 files against
the 1,700-file tripwire in `tests/test_skills_sh_package.py:217`, and
20,150,164 bytes, 821,356 under its 20 MiB line. Everything under
`plugins/alexandria/` ships except `tests/`, the manifests and the preserved
examples' JSON. `docs/kickoff/` does not ship.

**Last merged pull requests on the subject.** The two last merges touching
`wildcat_registry.py` or `venues/wildcat_v2.py` are #2028 (2026-09-30) and
#1965 (2026-09-28). #2028 added `rebuilding_preserved_release()` so the
preserved V2 example rebuilds on the pre-#1880 registry; its "Not checked"
says hosted CI runs only `invariants` and that the staged rebuilds ran
locally. This run keeps that scope and that function unchanged. #1965 moved
the V2 row pin only; its `carryover` block is
`none | none | the registry correction and the pins that follow it are the whole change`.
The last merge touching Alexandria at all, #2085 (skills#1997), added
`wildcat_event_headers`; its carryover is `none` and it states historical
missing headers as an evidence limit. Nothing from these three is carried
into this run.

**Audit history.** `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root at the base and exited 0, so the verified synopses
are the reading view. In-scope sources are the runs that built or changed the
Alexandria Wildcat interval path:
`audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.md`,
`audit/rounds/fiat-1888-epoch-table-split-and-release-caps.md`,
`audit/rounds/fiat-1892-statement-parts.md` and
`audit/rounds/fiat-1997-bind-wildcat-archive-timestamps-to-preserve.md`, plus
`audit/rounds/fiat-1378-wildcat-v1-v2-canonical-adapter.md` for Tabularium's
wrapper mapping. Each was read through its sibling `.synopsis.md`, by a
script extracting every finding row, `Elenchus verdict` and the
`Leads not pursued` sentences that mention the registry, subjects or wrappers;
no source file was read in full. Alexandria has no plugin `audit/AUDIT.md`;
the root `audit/AUDIT_SYNOPSIS.md` holds one wrapper mention, unrelated.

What those records decided that binds this design:

- 1731 W6-R2-01 (medium, fixed in `4daa9273`): per-subject coverage
  collections hit `MAX_COLLECTIONS` (256); W6-R2-02 (low, fixed): gap kinds that
  scale must be bounded under `MAX_GAPS`; W6-R2-03 (low, fixed): the
  `epoch-evidence` journal is never split and holds at most 64 MiB. Wrapper
  subjects add epochs, gap sentences and opening reads, so all three caps bind.
- 1731 W6-R1-03 (low, fixed in `80c6e6f7`): `market_deploy_report` compared
  addresses only; it now compares blocks too. The wrapper derivation compares
  the deployment block it records with the epoch it opens.
- 1731 W6-R3-02 (low, fixed in `a4f3d406`): empty code at a recorded first
  block refuses naming the block. The no-code wrapper refusal reuses it.
- 1731 W9-R1-05 (medium, fixed in `22102990`): targeted traces cover only
  transactions named by preserved subject logs, and coverage says so. Wrapper
  logs extend that selection; the existing sentence still holds.
- 1731 W3-R1-01 (medium, fixed in `49481acb`): a keyed epoch table accepted an
  epoch whose proxy belonged to another subject. A wrapper's epoch must name the
  wrapper as proxy and implementation.
- 1888 and 1892 rounds: every finding is fixed; the pinned-bytes leads ran the
  real releases only through `ALEXANDRIA_WILDCAT_V1_RELEASE` and
  `ALEXANDRIA_WILDCAT_V2_RELEASE`, which skip without those trees.
- 1997 Step 4 round 1: no finding; "Not checked" lists live RPC collection and
  a new fleet capture, both outside this run too.
- 1378 rounds reviewed a `wrapper-collapse` concern on the Tabularium side.
  Their four findings are fixed; S2-R1-01 (medium) made Tabularium require
  constructed capture subjects to be bound to declared emitters. How today's
  Tabularium treats a release whose logs come from wrapper addresses outside
  the registry is not checked here; it is the carryover's question.

Standing leads named in 1731 and still open: Fiat-1350's finality-boundary
comparison, the first-block header compared by hash alone, and the
undeclared-journal lead. This run does not touch finality, the opening header
or journal admission, so all three stay open by name. Two 1731 findings that
read "needs a runbook amendment" (W7-R1-01, W8-R1-01) were resolved later in
the same file, by a runbook-text correction and a dated erratum.

No in-scope record names a failure that this run's product edits must guard
first, so this study carries no known-failure inventory; the absent result is
the reading Protasis expects.

**Outside the repository.** The wrapper factory and wrapper are
`Wildcat4626WrapperFactory` and `Wildcat4626Wrapper` in
https://github.com/wildcat-finance/v2-protocol/tree/c7be4039f8f383a9dda4e45f63331c17d63f9ed9.
Tabularium already maps the wrapper's `Deposit`, `Withdraw` and `Transfer`
(`plugins/tabularium/scripts/tabularium_lib/wildcat_rules.py:25-32`) and the
factory's `WrapperDeployed` (`wildcat_abi.py:164`).

## 3. Constraints and non-goals

Starting ref: `main` at `50d71a2e8c1777f8eb26db32dd8adeadb34063bd`. Toolchain:
the `.python-version` interpreter; no new dependency. Alexandria's package
version is 0.7.54 on `main`, and none of the 907 local refs read here claims a
higher one; each step raises it above every local and remote claim at push time, in
`plugins/alexandria/.claude-plugin/plugin.json`,
`plugins/alexandria/.codex-plugin/plugin.json`, Alexandria's entry in
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` and the
pin in `tests/test_version_propagation.py`, because `scripts/plugin_release.py`
inside the required `invariants` job refuses a change to `plugins/alexandria/`
without a rise.

Ruled out by the operator:

- Any change under `plugins/tabularium/`, including `wildcat_rules.py`,
  `wildcat_rows.py`, `wildcat_abi.py`, `schemas/canonical-event-v3.json` and
  `docs/wildcat-canonical.md`.
- Collecting real wrapper data or calling any RPC. A new capture needs its own
  authority, which skills#2092 does not grant.
- Any number derived from a retained Wildcat capture, any private repository
  name, and any statement of where capture data came from, in any public
  record.
- Inferring an event's cause from events sharing its transaction.

Non-goals: Tabularium wrapper contexts (the issue's carryover
`tabularium-wrapper-context`); a command that lists a staging tree's
`WrapperDeployed` logs for an operator; a registry refresh for markets
deployed after the registry's snapshot; establishing wrapper immutability or
a single factory; a new Lazarus or proof-backed path for wrapper state.

Boundaries for the build:

- **Always.** Run `python3 scripts/run_checks.py --base fiat/2092-wildcat-v2-wrapper-instances-as-capture-sub --scope root --scope alexandria --format json`
  before each commit; regenerate `.horos/census.json` and, when it moves,
  `.horos/boundary.json`; run Imprimatur, Brevitas and Hypomnema on changed
  prose; keep the frozen identity tests green.
- **Ask first.** Changing the registry document or any of its three digest
  constants; changing a receipt format; touching a preserved example or the
  demonstration ledger; raising the portable tripwire; restoring retained
  capture bytes outside the Step 4 procedure.
- **Never.** Edit a Tabularium file; collect live data; publish a count or
  other number derived from retained bytes; delete or skip a failing test to
  pass a suite; claim a staged rebuild ran when its tests skipped.

## 4. Design options

Four constructions were drawn. The record in
`.hexaemeron/design-evidence.json` selects among them from checked gates and
counted metrics; this prose only explains them. Every selection value is
computed from the declared model in `.hexaemeron/design/model.json` by
`.hexaemeron/design/build_design_evidence.py`, which writes the 24 selection
reports. `.hexaemeron/design/conformance.py` resolves the pending cells.

1. **`declared-wrapper-subjects`.** A V2 plan declares its wrappers in a new
   optional field, `wildcat_v2_wrappers`, with one admitted rule,
   `wrapper-deployed/v1`, and a sorted list of addresses disjoint from
   `subjects` and from every registry entry. The address filter becomes
   `subjects` plus the declared wrappers. After the shards, the opening phase
   derives each wrapper's first block from its preserved `WrapperDeployed`
   log and reads its code and header there. Build writes the
   `wrapper-subjects` component; `check` re-derives it. Trade: the operator
   must know the wrapper set before collecting, so a wrapper the factory
   deploys inside the interval but the plan omits gets a gap and no native
   logs. In exchange every shard-class request still derives from the plan,
   the checkpoint format does not change and the registry stays as it is.
2. **`discovered-wrapper-journal`.** The plan opts in with a rule alone. After
   the shards, the collector reads the staged `WrapperDeployed` logs and walks
   a new post-shard journal class, `wrapper-logs`, over each wrapper from its
   deployment block, as skills#1997 did for event headers. Trade: no operator
   list and no undeclared-wrapper gap, at the cost of a new journal class, a
   checkpoint field, reconcile and split handling for ranged log reads, and
   request ranges that derive from collected bytes rather than the plan.
3. **`registry-wrapper-role`.** Add a `wrapper` role to the pinned V2
   registry, generated from a merged record listing deployed wrappers. Trade:
   wrappers become ordinary registry subjects, but the registry bytes and
   `WILDCAT_V2_REGISTRY_SHA256` move, the five Tabularium files that pin the
   current digest are affected, and the merged record would list real wrapper
   data this run may not collect.
4. **`separate-wrapper-venue`.** A new venue, `wildcat-v2-wrappers`, with its
   own module and releases, taking its wrapper set from an earlier V2
   release. Trade: the V2 path is untouched, but wrapper logs sit in a release
   apart from the market logs, so no one `release_id` binds both and a
   consumer joins two releases.

The record's selection gates and what each one shows:

| Criterion | Concern | Kind | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- | --- | --- |
| `registry-bytes-unchanged` | compatibility | gate | pass | pass | fail | pass |
| `constructed-proof-suffices` | correctness | gate | pass | pass | fail | pass |
| `one-release-binds-wrapper-logs` | correctness | gate | pass | pass | pass | fail |
| `plan-derived-requests` | recovery | gate | pass | fail | pass | pass |
| `edit-sites` | time | metric, minimise count | 10 | 16 | 9 | 9 |
| `portable-files-added` | space | metric, minimise count | 2 | 2 | 0 | 3 |

`plan-derived-requests` holds a candidate to the rule written at
`alexandria_lib/interval.py:75-79` and in the `usdc_interval.py` docstring:
the shard-class journals (boundary blocks, logs, traces) and their component
ranges derive from the plan and the shard count alone, never from what a
collection returned, and `check` re-derives them from the plan. Point reads in
the never-split `epoch-evidence` journal sit outside that rule today, since
first-code probes already follow earlier answers, and candidate 1 adds only
point reads there: one code read and at most one header read per wrapper.
Candidate 2's wrapper-log walk is a ranged log read whose ranges come from
collected `WrapperDeployed` blocks, so a killed run and `check` depend on
collected bytes for that request set.

Selected: `declared-wrapper-subjects`, the only candidate that passes every
selection gate, so the rule is `unique-frontier`. Its named trade is the
operator-declared wrapper list. Each declared address is still checked
against preserved evidence, so no unverified operator assertion reaches a
release; what the operator can do wrong is omit a wrapper, and the release
then says so.

Four conformance criteria stay pending until integration, each with its
resolver: `legacy-identities-hold` (compatibility),
`wrapper-release-builds-and-checks` (correctness), `wrapper-refusals-fire`
(recovery) and `portable-payload-within-budget` (space).

The selected design in detail:

- **Plan.** `wildcat_v2_wrappers` = `{"rule": "wrapper-deployed/v1",
  "subjects": [...]}` on an `alexandria-interval-plan/v2` plan whose venue is
  `wildcat-v2`, whose `evidence_classes` include `logs`, and whose `subjects`
  include the registry's `wrapper-factory`. The list is non-empty, sorted,
  lowercase and unique, disjoint from `subjects` and from every registry
  entry, and together with `subjects` stays under `MAX_SUBJECTS` (4,096).
  `schemas/interval-plan-v2.schema.json` gains the field.
- **Discovery.** A pure function reads the preserved logs whose emitter is the
  wrapper factory and whose first topic is the `WrapperDeployed` topic. Each
  needs exactly three topics with zero-padded addresses; the market must be a
  registry `market` entry, and the wrapper must not be a registry entry or
  appear in a second `WrapperDeployed`. Every declared wrapper must be one it
  finds.
- **Epoch.** First block is the `WrapperDeployed` log's block; the epoch runs
  to the interval end with `implementation` and `proxy` both the wrapper and
  `upgrade` null, the same shape as every V2 subject. Its code and header are
  read after the shards, in the existing `epoch-evidence` journal. The epoch
  opens at the block, not at the log's position: `_validate_position_table`
  in `alexandria_lib/interval.py` requires a subject's first position to be a
  block sentinel. A log the wrapper emitted during its own construction would
  precede the factory's `WrapperDeployed` in the same transaction, so a
  positional start would refuse it. Whether the constructor emits any log was
  not checked.
- **Logs and traces.** Wrapper logs join the `logs` journal through the
  address filter, and attribution rows name each wrapper as subject. Trace
  selection follows the same filter.
- **Component.** `wrapper-subjects`, format
  `alexandria-wildcat-v2-wrapper-subjects/v1`, lists the factory, the topic,
  the discovery window and every discovered wrapper with its market,
  deployment log identity (block, transaction hash, transaction index, log
  index) and whether the plan declared it. A schema file describes it.
- **Gaps.** A wrapper release adds, bounded by `_bounded`: one sentence per
  discovered but undeclared wrapper; one sentence, when the factory's recorded
  deployment block precedes the interval start, saying `WrapperDeployed` logs
  before the start were not requested; and two fixed sentences saying wrapper
  immutability and single-factory provenance are not established.
- **Receipts.** No new receipt format: wrappers are subjects in the v3 or v4
  epoch table, and `check` requires the component exactly when the plan
  carries the field.

## 5. Risk register seed

```risk-register
legacy-identity | release bytes for any plan without wildcat_v2_wrappers | the Step 1 frozen V1 and V2 constructed identifiers reproduce and no component, gap sentence, receipt field or check-result key changes for such a plan
registry-pin | wildcat_registry.py constants and generated registry bytes | the three registry digest constants and the generated document are byte-identical to the base
cross-plugin-check | Tabularium's check_interval call over its committed raw releases | the tabularium suite passes through run_checks with no Tabularium file changed
wrapper-log-parsing | provider-returned WrapperDeployed records in the logs journal | emitter, topic, topic count, address padding and block are validated and a malformed record refuses by name
unknown-market | a WrapperDeployed naming a market the registry does not list | build and check refuse naming the market and block; no gap stands in for it
declared-undeployed | a declared wrapper that no preserved WrapperDeployed names | build and check refuse; no first-code fallback grants the wrapper role
duplicate-deployment | one wrapper named by two WrapperDeployed logs or equal to a registry entry | the derivation refuses rather than picking one
undeclared-wrapper | a discovered wrapper the plan did not declare | the component lists it as undeclared and a bounded gap says no native logs were requested
empty-code | a wrapper's runtime code at its first block | missing or empty code refuses naming the wrapper and block
epoch-escape | a wrapper log before its WrapperDeployed block | attribution refuses naming the wrapper and no log is attributed outside its epoch
epoch-owner | the wrapper's epoch row | proxy and implementation both equal the wrapper and no other subject's epoch can own its logs
gap-bound | gap sentences that scale with discovered wrappers | each scaling kind names at most 16 and counts the rest, and a capture stays under MAX_GAPS
subject-cap | subjects plus wrappers against MAX_SUBJECTS, MAX_COLLECTIONS and the 64 MiB epoch-evidence journal | limits refuse by name before any request
plan-field-shape | the operator's wildcat_v2_wrappers field | closed shape, one rule value, sorted lowercase unique addresses, venue wildcat-v2 only, wrapper factory declared, logs class present
component-rederive | the wrapper-subjects component | check re-derives it from preserved logs and the registry and compares canonical bytes
check-result-shape | the dict check_interval returns | new keys appear only for a wrapper plan, so Tabularium's reader of a legacy release sees the same result
portable-budget | the portable Promise Machine payload | sync then check exit 0 and the run adds at most five files and 100,000 bytes
version-gate | Alexandria's package version on each step branch | each step rises above every local and remote claim in all five surfaces
private-data | public records of the Step 4 retained rebuild | only release identifiers and pass or fail are published, and restored trees live in a 0700 directory outside every repository and are purged
causal-claim | gap sentences and documents about wrapper events | no cause is inferred from co-occurring events and the two not-checked items stay stated unknowns
concurrent-run-merge | files shared with the skills#2087 run: tests/test_version_propagation.py, both marketplace files and .horos/census.json | each conflict is resolved by taking main and regenerating, never by editing a Tabularium line
```

The audit loop should look hardest at `legacy-identity`, `component-rederive`
and `epoch-escape`: they decide whether old releases move and whether a new
release can claim a log it does not own.

## 6. Glossary seeds

- **Wrapper.** A `Wildcat4626Wrapper` instance, named by topic two of a
  `WrapperDeployed` log.
- **Wrapper factory.** The registry's `wrapper-factory` entry, the only
  emitter whose `WrapperDeployed` logs this design reads.
- **Declared wrapper.** An address in the plan's `wildcat_v2_wrappers.subjects`.
- **Discovered wrapper.** A wrapper named by a preserved `WrapperDeployed`
  log inside the interval.
- **Undeclared wrapper.** Discovered, not declared; listed, with no native
  logs requested.
- **Wrapper subject set.** The `wrapper-subjects` component, bound by digest
  in the manifest.
- **Legacy plan.** Any plan without `wildcat_v2_wrappers`; its bytes must not
  move.
- **Frozen identifier.** A constructed release identifier computed at the base
  and asserted by a Step 1 test.

## 7. Sources

- Issue: https://github.com/wildcat-finance/skills/issues/2092
- Base: https://github.com/wildcat-finance/skills/tree/50d71a2e8c1777f8eb26db32dd8adeadb34063bd
- Registry and venue: `plugins/alexandria/scripts/alexandria_lib/wildcat_registry.py`,
  `plugins/alexandria/scripts/alexandria_lib/venues/wildcat_v2.py`
- Collector and plan rules: `plugins/alexandria/scripts/usdc_interval.py`,
  `plugins/alexandria/scripts/alexandria_lib/interval.py`,
  `plugins/alexandria/scripts/alexandria_lib/event_headers.py`
- Release identity: `plugins/alexandria/scripts/alexandria_lib/release.py:205-218`
- Constructed fixture and fake transport:
  `plugins/alexandria/tests/test_wildcat_venue.py:205-262`,
  `plugins/alexandria/tests/fixtures/wildcat-interval-transport.json`
- Preserved examples: `plugins/alexandria/examples/wildcat-v2-interval-v0/`,
  `plugins/alexandria/examples/wildcat-v1-interval-v0/`
- Tabularium reader: `plugins/tabularium/scripts/tabularium_lib/wildcat_source.py:27-50, 370-390`
- Portable payload: `scripts/portable_promise_machine.py`, `tests/test_skills_sh_package.py:205-217`
- Check map: `tests/check-map-v1.json`
- Versioning: `plugins/hexaemeron/skills/VERSIONING.md`,
  `plugins/alexandria/skills/alexandria/EVOLUTION.md`
- Prior pull requests: https://github.com/wildcat-finance/skills/pull/2028,
  https://github.com/wildcat-finance/skills/pull/1965,
  https://github.com/wildcat-finance/skills/pull/2085
- Wrapper source: https://github.com/wildcat-finance/v2-protocol/tree/c7be4039f8f383a9dda4e45f63331c17d63f9ed9
- Audit synopses: the five `audit/rounds/*.synopsis.md` files named in
  [Prior art](#2-prior-art)

## 8. Signals, and the questions behind them

None is added, and here is why: this delivery ships no unattended path. Every
new behaviour runs offline on constructed data, and a future wrapper capture
runs through the existing collector, whose failure receipts already name the
code, shard, range and provider class. The questions an operator will ask are
answered from what the release and its refusals already carry:

1. Which wrappers did this release admit, and which did it see but not
   collect? The `wrapper-subjects` component and the bounded gap sentences.
2. Why did build or check refuse? The refusal names the wrapper, and the
   market or block at fault.
3. Did adding wrappers move an existing release? The frozen identifier tests,
   which fail on any byte change.

Ephoros owns what a signal must carry; no step here adds a metric, an alert or
a log stream.

## 9. Boundaries, per capability

Phylax owns the boundary list and its controls. This design opens no new
network path, subprocess, credential, dependency or model input. It widens
two existing boundaries:

1. **Preserved log records.** `WrapperDeployed` records are provider-returned
   JSON. Parsing checks the emitter, topic, topic count, padding, address
   form and block quantity, refuses by name and never trusts a field it did
   not check. Risk ids `wrapper-log-parsing`, `duplicate-deployment`.
2. **Operator plan field.** The field has one closed shape and one rule value,
   and its addresses are bounded, sorted, lowercase, unique and disjoint from
   the registry. A wrapper the operator lists without preserved evidence
   refuses. Risk ids `plan-field-shape`, `declared-undeployed`.

The network request grows by the declared wrapper addresses in the existing
`eth_getLogs` and `trace_filter` filters, inside the existing request and
response caps. Release writing stays on `ingest`'s sibling temporary
directory and atomic install. The Step 4 retained rebuild reads internal-only
bytes; risk id `private-data` holds its control.

## 10. The budget, or its absence

No performance budget is claimed, and here is why: the specimens are a few
records, and the change adds at most one code read and one header read per
declared wrapper, inside the existing journal and request caps (risk id
`subject-cap`). Metron owns a budget's shape; there is no latency target to
measure.

One space budget is hard: the portable payload. The run adds at most five
files and 100,000 bytes to it, measured by
`python3 scripts/portable_promise_machine.py measure` after `sync`, and
`check` must exit 0. The run keeps its study, runbook, design record and
reports under `docs/kickoff/2092/`, which does not ship, and its fixtures under
`plugins/alexandria/tests/`, which is omitted.

## 11. The fail-closed posture

Every refusal named in section 1 and the risk register stops build or check
with a named `AlexandriaError` and writes nothing: build installs through
`ingest`'s temporary directory, and `check` changes no file. A plan field that
fails its shape check refuses before any request. A legacy plan never reaches
the wrapper code, so a fault there cannot move an old release.

Guard convention, owned by Elenchus: a fix lands with a test that fails
without it, in the Alexandria suite. Step 1 creates
`plugins/alexandria/tests/emit_wrapper_report.py`, which runs the named
classes for one step and writes a `unittest-json-v1` report, following
`plugins/tabularium/tests/emit_wildcat_batch_report.py` from the skills#2087
run. Each step's Elenchus command is
`python3 plugins/alexandria/tests/emit_wrapper_report.py --step N --report {report}`
with report file `.elenchus/2092-step-N.json`.

## 12. Decisions and their homes

Two decisions are expensive to reverse, because each becomes part of every
wrapper release's identity:

1. Wrapper instances are plan-declared subjects checked against preserved
   `WrapperDeployed` logs, not registry entries, and an unknown market
   refuses rather than becoming a gap.
2. The `wrapper-subjects` component format,
   `alexandria-wildcat-v2-wrapper-subjects/v1`, and the plan field
   `wildcat_v2_wrappers` with rule `wrapper-deployed/v1`.

Both live in one draft decision record that Step 1 creates at
`docs/decisions/drafts/admit-wildcat-v2-wrappers-as-declared-subjects.md`;
its number is assigned at integration. Alexandria's
`plugins/alexandria/skills/alexandria/EVOLUTION.md` gains one generation row,
`alexandria-v3.12.0`, with `SKILL.md` frontmatter to match, in the step that
changes `SKILL.md`; the frontier revision, frontier digest and next job stay as
they are.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | declared-wrapper-subjects
record | docs/decisions/drafts/admit-wildcat-v2-wrappers-as-declared-subjects.md
```

Proposed steps, for the runbook to derive:

1. **Scaffold the run records and freeze legacy identities.** Commit the study,
   runbook, design record, reports and resolver under `docs/kickoff/2092/`,
   create the decision draft and `emit_wrapper_report.py`, and add tests that
   pin the constructed V1 and V2 release identifiers computed at the base.
2. **Derive wrapper subjects from WrapperDeployed logs.** The plan field and
   its schema, the pure discovery and component functions, their refusals and
   bounded gaps, with no collector wiring yet.
3. **Collect, build and check wrapper subjects.** Wire the address filter,
   opening reads, epochs, attribution, component and `check` re-derivation;
   update `SKILL.md`, the collector document and the generation row.
4. **Demonstrate the constructed wrapper release and rebuild the preserved
   identities.** Run the specimen and refusals through the CLI, measure the
   portable payload, and rebuild V2 `2de87cbd…` and V1 `eee71d1e…` from trees
   restored from internal custody, the route ADR-110 records.

Every step's Files list Alexandria's five version surfaces from section 3,
`.horos/census.json` and `.horos/boundary.json`. Every step's Exit names
`python3 scripts/run_checks.py --base fiat/2092-wildcat-v2-wrapper-instances-as-capture-sub --scope root --scope alexandria --format json`,
which closes over `repo-lints`, `tabularium` and `probitas`, and the AGENTS.md
lints over the files it changed.

Step 4 needs the real retained V1 and V2 staging trees, because only they
rebuild the preserved identifiers; constructed pins prove the same code path
but not those two releases. The trees are internal-only: restore them through
the internal custody route ADR-110 records, into a
0700 directory outside every repository, export `ALEXANDRIA_WILDCAT_V2_STAGING`
and `ALEXANDRIA_WILDCAT_V1_STAGING`, run `test_wildcat_v2_interval_demo`,
`test_wildcat_v1_interval_demo` and `test_wildcat_estates_interval_demo` with
zero skips, and purge the directory afterwards. The public record carries only the two identifiers and
pass or fail. No capture data is read from any other source.
