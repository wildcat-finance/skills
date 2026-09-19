# Venue-agnostic interval capture for both Wildcat estates

Topic: separate the venue-specific parts of the Alexandria interval collector
from its generic parts, so a registry, a subject set and an epoch model can be
supplied per venue rather than compiled in, and collect one bounded interval
from each of the two Wildcat Ethereum mainnet estates with the result.

Task issue: https://github.com/wildcat-finance/skills/issues/1731

Starting ref: `b2f528e9bee8dc4bd4d1653f7f66fe6b1de93bc0` on `main`. Every path,
line and digest below is read at that commit unless it says otherwise.

## Assumptions

Proceeding on these unless corrected.

1. Python 3.14.6, the interpreter in `.python-version`, with stdlib `unittest`.
   No third-party dependency is added.
2. The run branch is `fiat/1731-venue-agnostic-interval-capture-for-both-wi`,
   cut from `main` at the ref above.
3. The security suite is waived: the run ships no Solidity and no Foundry or
   Hardhat project.
4. The reference target is the Wildcat V1 and V2 Ethereum mainnet estate, both
   rows, on the issue's second amendment of 2026-09-19. The first amendment's
   narrowing to V2 alone is withdrawn and nothing in this study relies on it.
5. The run performs one bounded collection per estate, two in all. Every other
   refusal stands: no completeness claim, and no presentation of either
   collected span as that estate's whole history.
6. Every capture and digest produced before this run is void and replaceable.
   The capture maintainer said so. The Compound release identifier and the two
   recorded refusal strings are therefore regression checks worth keeping
   because they are nearly free, not constraints the design is shaped around,
   and no selection criterion is spent on them.
7. `docs/kickoff/1359/targets.json`,
   `docs/kickoff/1359/evidence/ethereum-mainnet-1590.json`,
   `docs/kickoff/1359/evidence/source-match-1590.json`,
   `docs/kickoff/1359/evidence/ethereum-mainnet.json` and
   `docs/kickoff/1374/capture.json` are merged, reviewed repository bytes and
   are this run's source for Wildcat deployment identity, for both subject sets
   and for the per-subject deployment blocks. No chain read reproduces them.
8. Selecting each interval's start block, end block and shard width stays the
   capture maintainer's decision, as recorded on
   https://github.com/wildcat-finance/skills/issues/1490 and restated in this
   issue's boundary. The study fixes the conditions an admissible interval must
   meet and names one worked pair that meets them; it does not decide either
   pair.
9. The transport figures in item 3 were measured by the controller against the
   attached node and the second endpoint during the retired first attempt at
   this run. They are recorded here, not re-probed, and item 3 says which of
   them the restored scope invalidates.

Assumptions 4 and 8 are the two that change the content. Item 4 records what
the restored scope did to the selection, which is nothing, and what the new
registry data did to the epoch model, which is one real change.

## 1. Problem statement, user, and the proving path

The interval collector can capture exactly one deployment, the Compound v3 USDC
Comet. Three constraints refuse both Wildcat estates.

The registry byte-pin. `plugins/alexandria/scripts/alexandria_lib/compound_registry.py:216`
hashes the whole registry and compares it to the single constant
`REGISTRY_SHA256` declared at `:18`. `validate_registry` at `:162` pins the
format string, the Comet repository URL, the commit, both tree identities,
exactly 28 entries and an `EXPECTED_MARKETS` allowlist.
`plugins/alexandria/scripts/usdc_interval.py:1184` calls it inside
`Builder.__init__`, so every build passes through it.

The epoch model. `plugins/alexandria/scripts/alexandria_lib/interval.py:77-78`
hard-wire the EIP-1967 implementation slot and the ERC-1967 `Upgraded(address)`
topic, and the opening reads sample the slot at `interval.py:1243`. Neither
Wildcat row records an upgradeable proxy: `docs/kickoff/1374/capture.json`
carries `upgradeable_proxies: 0` on both. The estates are direct deployments,
stored init code and create2 clones, so there is no upgrade log to read and no
implementation slot to sample.

The single subject. `interval.py:115` validates a plan whose key set is exactly
eleven names including one `proxy` address, `usdc_interval.py:483` filters
`eth_getLogs` and `trace_filter` by that one address, and
`proxy_log_positions` at `interval.py:687` refuses a log that another contract
emitted. The V2 capture has 137 subjects and the V1 capture has 16.

**Who this is for.** The capture maintainer, who selects each interval and
authorises a run; and the two consumers `docs/kickoff/1374/capture.md` names,
issues 1374 and 1493, neither of which can proceed until a Wildcat capture
exists.

**What a working prototype means here.** A Wildcat V2 interval plan over its
137 subjects and a Wildcat V1 interval plan over its 16 both build and check
offline through the collector's existing `build` and `check` path, carrying the
coverage and gap field names the Compound release carries, and both preserved
captures rebuild from committed bytes with no network.

**Success criteria.** Each is a command, run from the repository root. `<plan>`,
`<staging>`, `<registry>`, `<timestamp>` and `<output>` are the arguments the
step that owns the criterion supplies.

1. A Wildcat V2 plan over 137 subjects builds and checks.
   `python3 plugins/alexandria/scripts/usdc_interval.py build --plan <plan> --staging <staging> --registry <registry> --created-at <timestamp> --output <output>`
   prints a release identifier and
   `python3 plugins/alexandria/scripts/usdc_interval.py check <output>` exits 0.
2. A Wildcat V1 plan over 16 subjects builds and checks, through the same two
   commands with V1 arguments.
3. Both preserved captures rebuild offline. Each committed demonstration's
   `build` reproduces its recorded identifier and its `verify` exits 0, with no
   socket opened.
4. An unregistered venue refuses. A plan whose `venue` names no registered
   module exits 1 by name rather than falling back to Compound.
5. A registry that disagrees with the plan's venue refuses, and a registry that
   fails its venue's pin refuses. Both exit 1.
6. Coverage parity. Every capture object in both Wildcat releases carries the
   field names the Compound release's capture objects carry, which
   `usdc_interval.py:1324` builds: the eight top-level names `chain`,
   `component`, `coverage`, `evidence_class`, `id`, `source`, `scope` and
   `venue`, and the twelve nested names under `coverage`, `source` and `scope`.
   Compared name by name against a Compound release built in the same run, and
   against the nine coverage rows recorded under `pattern_release.coverage` in
   `docs/kickoff/1374/capture.json`.
7. The shared pair is a subject of both venues and neither venue attributes the
   other's subjects. The V1 and V2 registries both declare
   `0xfeb516d9d946dd487a9346f6fee11f40c6945ee4` and
   `0x437e0551892c2c9b06d3ffd248fe60572e08cd1a`, their declared subject sets
   intersect in exactly those two, and a log emitted by a subject of the other
   estate is refused rather than attributed.
8. The V1 release declares its source gap. Every V1 subject whose row
   establishes no source identity is named in the release's own coverage gaps,
   and the release claims source identity for no subject the row does not
   establish it for.
9. Every release component is at or below `MAX_RAW_COMPONENT_BYTES` at
   `plugins/alexandria/scripts/alexandria_lib/release.py:55`, and every staging
   journal is at or below `MAX_JOURNAL_BYTES` at `interval.py:53`. Both are
   67,108,864 bytes.
10. The Compound path still builds and checks, and the repository stays green.
    `python3 scripts/run_checks.py --scope alexandria --scope root` exits 0.

**Proving demo path.** The last step runs criteria 1 to 9 in one demonstration
under `plugins/alexandria/examples/`, in the shape the three existing interval
demonstrations already use, with no network.

## 2. Prior art

### In this repository

`plugins/alexandria/scripts/alexandria_lib/compound_registry.py` generates the
Compound registry from Git object bytes at a pinned commit and validates it
against a self-pin. It is the only in-repository example of a registry pinned
by repository URL, commit, tree and SHA-256 together, and the design below
copies its shape rather than inventing one. The Wildcat registries cannot copy
its source, though: two of the V2 estate's located source repositories,
`wildcat-finance/fee-recipient-contract` and
`wildcat-finance/chainalysis-ofac-role-provider`, are recorded in
`docs/kickoff/1359/evidence/source-match-1590.json` as private to the
organisation. The Wildcat registries are generated from the merged kickoff
records instead, which carry every address, deployment block and code digest
the capture needs and no source bytes at all.

`plugins/alexandria/scripts/alexandria_lib/mappings/__init__.py:18-31` is the
nearest venue-dispatch precedent: an explicit `REGISTRY` dict keyed by the
capture's `venue`, with an unknown venue raising
`capture <id> venue <venue> has no registered mapping` rather than falling
through. `plugins/tabularium/scripts/tabularium_lib/release_v2.py:13-17` holds
the same pattern, keyed off each adapter module's own `ADAPTER` constant, which
is the better of the two because the module owns its identifier. Tabularium's
CLI then repeats the venue list a second time as an argparse `choices` tuple at
`plugins/tabularium/scripts/tabularium.py:27-32`, so admitting a venue there
means editing four places. That duplication is the mistake this design does not
repeat, and it matters more now that the run admits two venues rather than one.

The plan schema is already venue-parameterised. `validate_plan` at
`interval.py:115-131` requires `venue` and `deployment` as free names, and
`plugins/alexandria/schemas/interval-plan-v1.schema.json` constrains `venue`
only to the `name` pattern. The live Compound plan declares
`"venue":"compound-v3"`. So the plan already carries the dispatch key; nothing
reads it for dispatch today.

`plugins/alexandria/examples/usdc-interval-v0` is the precedent for a
demonstration built on constructed bytes. Its README states plainly that the
fixtures are synthetic and were not observed on any chain. Its release does not:
`usdc_interval.py:1380-1390` derives `evidence_class` and `source.locator_class`
from whether a component is an evidence journal, not from whether its bytes were
observed. Only the prose beside the release says the bytes were constructed.
Item 4 treats that as a defect to avoid, not a precedent to copy.

### The last two merged pull requests that changed the subject

This run's subject spans two trees that move independently, so both were read.

The collector. Pull request 1690, merged 2026-09-16, closed issue 1503 and
changed `usdc_interval.py` and `interval.py`. Pull request 1448, merged
2026-09-07, closed issue 1350 and changed the same two files plus the whole
`examples/usdc-interval-live-v0` capture. Neither touched
`compound_registry.py`, which last changed on 2026-08-31. `git diff --stat`
between `e4cef131` and the base commit is empty under `plugins/alexandria`, so
the collector tree is byte-identical to the one the retired first attempt read.

The kickoff records. Pull request 1733, merged 2026-09-18, closed issue 1490 and
wrote `docs/kickoff/1374/`. Pull request 1735, merged 2026-09-19 as the base
commit, closed issue 1590 and rewrote the V2 row of
`docs/kickoff/1359/targets.json` with two new evidence files.

Each body's `carryover` block is answered here by name.

From 1690: `packaged-interval-demos` (issue 1678) and
`collector-journal-descriptors` (issue 1679) stay open; 1679 touches
`Collector.collect`, which this run does change, so it is carried into the risk
register as a boundary to review rather than left elsewhere.
`tabularium-schema-enums` (issue 1362), `atlas-launcher-contradiction`
(issue 1677), `fiat-skill-wording`, `berean-recorded-frontier`,
`elenchus-round1-inconclusive`, `linux-proof-next-probe` and
`dokimasia-prose-corrections` are outside Alexandria's collector and stay open
elsewhere.

From 1448: `untestable-release-labels` (issue 1442) is the closest carried item
to this run's subject, and item 4 answers it for the one label this run
introduces rather than for the release as a whole; the wider issue stays open.
`unconsumed-release-components` (issue 1443) names the `registry` component
specifically, and this run gives that component a second consumer, because the
venue's registry validator and its gap contribution both read it; the issue
stays open for `error-receipts`. `refusal-receipt-status-field` (issue 1444) and
`socket-confinement-evidence` (issue 1445) stay open and are untouched.
`second-transport-independent-derivation`, `sources-coverage-refresh`,
`runbook-files-field-accuracy`, `epoch-boundary-headers-not-re-asked` and
`brevitas-signals-on-changed-markdown` are recorded there with reasons that
still hold.

Pull request 1735 carries one item forward in its own prose rather than in a
block, and it lands on this run. Its section "One dated line elsewhere" states
that `docs/kickoff/1374/capture.json` records the V2 row's `registry_status` as
`blocked` and quotes its blocker text, that those are dated observations in
another record which 1735 left as written, and that whoever next regenerates
that record picks up the new status. This run is that regeneration, and item 3
records the three ways the record is now behind the tree.

Pull request 1733's own prose carries no unfinished work into this run. Its
findings 4 and 5 were answered after its reviewer's last round, which
`evidence/review.json` records as bytes not reviewed in full; that is a bound on
the review of that record, not work this run owes.

One item from 1690's prose, outside its carryover block, is the alexandria
ledger's open frontier: reconciliation compares a log without its transaction
index, so a second provider reporting a different index for the same log still
records `agreed`. That is the held next job in
`plugins/alexandria/skills/alexandria/EVOLUTION.md`. This run does not take it
and does not change reconciliation's comparison, so the frontier stays open and
this delivery sits beside it as a generation bump.

Issue 1373, the component budget that survives a real venue capture, is on this
run's path rather than beside it. Item 3 records the measurement that puts it
there.

### Audit history

The whole-set currency check was run from the target root and exited 0:
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
reported 95 sources, every one `budget=pass` and `committed=match`, with empty
stderr. A verified synopsis is therefore an admitted reading view for every
source below.

There is no `plugins/alexandria/audit` directory; Alexandria's audit history
lives entirely in the root `audit/` tree, which holds 87 round records. No
round record changed between `e4cef131` and the base commit. Five in-scope
sources, and which view was read:

| Source | View read | Why |
| --- | --- | --- |
| `audit/rounds/fiat-1350-alexandria-1-interval-collector-run-against.md` | source | the run that built the live capture; its leads are design inputs |
| `audit/rounds/fiat-395-resumable-ethereum-usdc-interval-collector.md` | source | the run that built the collector; holds the only open Alexandria-file findings |
| `audit/rounds/fiat-1503-attribute-implementation-epochs-by-transact.md` | source | the run that built the v2 receipt |
| `audit/AUDIT.md` | source | the only rounds whose file column is `compound_registry.py` |
| `audit/AUDIT_SYNOPSIS.md` | synopsis | the derived view of the above, read for its legacy-field markers |

The sources were read directly rather than through their synopses, because the
synopsis of a round record is a line-collapsing projection rather than an
abridgement and is in several cases larger than its source; the currency check
establishes that either view carries the same content. `audit/AUDIT_SYNOPSIS.md`
was read as a synopsis only for the `[missing legacy field: ...]` markers, which
exist in no source.

Findings and statuses carried forward. `fiat-1350` records 25 findings, all
fixed. `fiat-1503` records 2, both fixed: S2-R1-01 in `interval.py:710`, fixed in
`cc0d9cff`, and S3-R1-01 in the epochs demonstration, fixed in `1b357ecd`.
`audit/AUDIT.md`'s four Compound v3 Phase 0 rounds record 7 findings, all fixed,
including S1-R1-01 against `compound_registry.py`, which is the round that
created the registry byte-pin. Those four rounds carry
`[missing legacy field: audit-schema]`, `[missing legacy field: covered]`,
`[missing legacy field: not-checked]` and
`[missing legacy field: elenchus-verdict]`, which remain unknown.

`fiat-395` records 25 findings, of which five are `open`. Two, S1-R1-07 and
S6-R1-03, sit on `.agents/skills/promise-machine/runtime/MANIFEST.json`, which
no longer exists in the tree; the ceiling they name is now 1,500 and the second
assertion they name no longer exists, so they are dead rather than live. Three
sit on Alexandria paths: S2-R1-04 and S5-R1-04 record divergences between the
receipted `docs/usdc-interval-runbook.md` and delivered behaviour, both recorded
rather than edited because that runbook is receipted; S5-R1-05 records that a
step Exit claimed every epoch is code-hash-bound when the release then carried
no implementation code to hash. S5-R1-05 is superseded: `alexandria-v2.5.0`
added the `implementation-code` component and `check` re-hashes it at
`usdc_interval.py:1984`. The other two are prose divergences with no failing
assertion.

The `Covered` vocabulary of the two collector runs is inherited by this run's
register in item 5: `fiat-1350` enumerates `finality-tag-drift`,
`start-hash-source`, `code-digest-rebind`, `opening-phase-resume`,
`traces-omission-declared`, `header-leak`, `endpoint-leak`, `rate-limit-refusal`,
`opening-reads-reconciled`, `preserved-bytes-identity`, `silent-truncation`,
`live-reads-confined`, `skip-as-pass` and `whole-battery-regression`.
`fiat-1350`'s five unpursued leads are carried into item 5 rather than treated
as closed: `bind_finality` accepting a tag hash, `_compare_opening` comparing
the first-block header by hash alone, `_gaps` naming no omitted class for an
undeclared journal, an opening refusal receipt carrying a block number as its
status, and `validate_checkpoint` accepting `next_shard` 2 with a non-zero
`epoch-evidence` offset.

**No inventory of known failures is required.** Protasis requires one only when
audit history names failures implementation must guard before product work
starts, and each entry must bind a guard whose expected verdict is `guarded`.
The only open Alexandria-path findings are two receipted-prose divergences and
one superseded claim boundary. None can supply a failing guard. The study
carries no such block and the runbook carries no assignment record.

### Outside this repository

EIP-1967 fixes the implementation storage slot and the `Upgraded(address)`
event the current epoch model reads. ERC-1167 minimal proxies and CREATE2
clones are the pattern `docs/kickoff/1374/capture.json` records for both
Wildcat rows, and neither carries an implementation slot. Sourcify is the
verification source behind the `sourcify` field in both recorded contract
inventories; 7 of the V2 row's 137 contracts and 4 of the V1 row's 6 carry
`sourcify: "match"`.

## 3. Constraints and non-goals

**Starting ref and toolchain.** `b2f528e9bee8dc4bd4d1653f7f66fe6b1de93bc0`,
Python 3.14.6, stdlib only. The alexandria package version at that ref is
`0.7.0` and the skill ledger is `alexandria-v3.5.0`, frontier status `open`,
holding the `transaction-index-reconciliation` job. This run does not take that
job, so it is a generation bump and the held job carries forward unchanged.

**The merged records this run reads, and their digests at the base commit.**
Each was recomputed with `shasum -a 256` at the base commit and matched.

| Input | Bytes | SHA-256 |
| --- | --- | --- |
| `docs/kickoff/1359/targets.json` | 327997 | `5a6a5d0e4a8f4fafe7bb41fdcdd1ef491d95ac734ca678426265d8def999efb0` |
| `docs/kickoff/1359/evidence/ethereum-mainnet-1590.json` | 429262 | `b7ce1e66f343a480ac64f8b6259e108638dc1fe473607b77f728980846d6ca70` |
| `docs/kickoff/1359/evidence/source-match-1590.json` | 38287 | `3d9a17ad9fce5306129e9975fe36f8ca8e95cacb647daca7d408b3682fdc38af` |
| `docs/kickoff/1359/evidence/ethereum-mainnet.json` | 21089 | `a34771df5764fbdedd29dfcbb78ec33970e66580baccde908e4e4dfdc0090f1c` |
| `docs/kickoff/1374/capture.json` | 31105 | `ca9988ec1e9bbe02eeca35ae2628748b0a3f1e440ab9ca8d5ea14d0b8848a80d` |
| `docs/kickoff/1374/capture.md` | 14194 | `79f1fa210f25cece3975ffd130b7e1c39edc11737c573e18a61cb47729d5cb44` |

Two of those six moved on `main` while this study was being written, and the
table stays at the base commit because that is where the run branch is cut and
what every line reference above is read at. Pull request 1736 merged as
`0dd41be5c10bc83d3df33c9fdca3d385264059ba`, taking
`docs/kickoff/1359/targets.json` to
`8cc6433a45db7744e2fd7894b3b680e9738186ffb67d43de48db4c99635ea65f` and
`docs/kickoff/1359/evidence/source-match-1590.json` to
`0bd8d53d351e46082dbb625a499bc7c6cebe1f1f43ab4c9ef2498f23fb79282e`. Its whole
content is a recompilation of the WildcatFeeRecipient verification input and
the two records' wording about it. No address, subject count, deployment block,
code digest, list digest, row status or exclusion moved, so every figure this
study derives holds unchanged at that commit. The step that generates each
registry pins whatever digests its own base carries and re-reads them, rather
than copying this table, and the integration sync re-checks both.

**What the capture record now contradicts, and what the run owes it.**
`docs/kickoff/1374/capture.json` is behind the tree in three places, all created
by pull request 1735 landing four minutes after this run's first attempt was
initialised. Its `source_revision` is `f0fa0c6632bd5fbef7f35e731646c32741ef282a`.
Its `inputs[0]` pins `docs/kickoff/1359/targets.json` at 164,821 bytes and
`9e0d3c88c76ec727ea8aabe67fb8ac0648b039ef1fa9836a6a7f2f2ae4d4ca98`, against
327,997 bytes and the digest in the table above. Its
`required_capture` row for `wildcat-v2-ethereum-mainnet` still carries
`registry_status: "blocked"`, 12 contracts, and a `registry_blocker` naming the
missing instance inventory and the unestablished WildcatFeeRecipient and
CollateralFactory source identity, all of which issue 1590 closed. Nothing
checks any of this: `scripts/kickoff_targets.py check` reads
`docs/kickoff/1359` only, and no test under `tests/` names `docs/kickoff/1374`.
The record's `selection.reference_target` and both `required_capture` rows
already list V1 and V2 together, so the target itself needs no change. The
runbook places the re-pin and the V2 row refresh in a step, and states in the
step's own Exit which fields move.

**Gates a step incurs.** `python3 scripts/run_checks.py --scope alexandria --scope root --plan`
selects ten checks at this ref: `alexandria-suite`, `root-suite`,
`dead-code-suite`, `dead-code-suppressions-check`, `demonstrations-suite`,
`front-door-check`, `joined-front-door-suite`, `lint-ephoros`,
`lint-hypomnema` and `lint-phylax`. The alexandria suite held 694 tests at
`e4cef131`, and the alexandria tree is unchanged at the base commit, so that
count is the entry state. Three named gates sit inside those suites: the Horos
reading boundary at `tests/test_boundary_currency.py`, refreshed with
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`; the Horos
census currency at `tests/test_demonstrations.py`, which any tracked-file edit
moves; and the demonstration ledger, which a new example must be registered in.
The step that touches `docs/kickoff/1359` also incurs
`tests/test_kickoff_targets.py`, which is inside `root-suite`. Separately,
`python3 scripts/plugin_release.py --base <base>` requires a newer package
version for every changed plugin tree, so each stacked step pull request that
touches `plugins/alexandria` owes a version rise over its own base.

Only one command outside the built-in gate registry can be declared on a
runbook Exit line. The interface adapter at
`plugins/hexaemeron/skills/protasis/scripts/gate_commands.py:183-186` requires a
builder that assigns a local named `parser` from a bare `argparse.ArgumentParser`
and then only adds arguments. Of the collector's CLIs, only
`plugins/alexandria/tests/run_tests.py` with builder `report_target` satisfies
it; `usdc_interval.py`, `alexandria.py`, `design_evidence.py` and every example
demonstration were each tested and refused during the retired first attempt, and
every other top-level function in those four modules was tested too, 61
candidates in all, with none accepted. Those four modules are unchanged at the
base commit. The runbook therefore declares that one interface and names every
other command in a step's Tests field.

**The transports, as measured, and what the restored scope invalidates.** The
primary is a local Reth archive node, `reth/v1.11.0-564ffa5/aarch64-apple-darwin`,
chain 1, still syncing with head 25,944,874 when measured. Archive state is
confirmed at the Wildcat V2 start block 21,788,182, where `eth_getCode` at the
HooksFactory returns runtime code. `eth_getLogs` caps at a 100,000-block range.
The trace and debug namespaces are served after an approved launch-flag change.
One 50,000-block `eth_getLogs` over a single address took 20.5 seconds under
sync load.

The second transport is an allocated hosted endpoint, Geth `v1.17.5-stable`,
chain 1, tip 26,008,004, archive depth confirmed by `eth_getCode` at the same
block. Its `eth_getLogs` range cap is exactly 30,000: a `toBlock` minus
`fromBlock` span of 29,999 is accepted and 30,000 is refused with
`-32012 getLogs request exceeded max allowed range`. `trace_block` and
`trace_filter` both answer, in 1.0 and 1.8 seconds, and ordinary calls take 0.1
to 0.2 seconds. That 30,000 cap, not the primary's 100,000, is what bounds the
shard width.

Two of those figures do not survive the restored scope, and the runbook step
that plans a collection re-measures rather than extrapolating. Archive depth at
the V1 start block 18,686,645 was never probed, and V1's earliest subject sits
3,101,537 blocks before the V2 start. The primary's head was 25,944,874 at
measurement time and the chain has moved since, so any interval end above it is
a claim about a block nobody has read here.

**The credential rule.** The second transport carries a bearer token. Neither
its URL nor its token may appear in any artefact this run produces: not in the
study, runbook, plan, registry, release, staging journals, receipts, tests,
fixtures, commit messages, pull request text or issue comments. Both reach the
process through environment variables and nowhere else, following the pattern
`usdc_interval.py` already sets for its endpoint. The collector sends no header
from the environment today, so bearer authentication is new capability the
runbook specifies deliberately. Each preserved release names its providers by
class alone, as the Compound release names
`archive gateway, public tier, no trace methods` and nothing more.

**What bounds an admissible interval.** Four conditions, and any pair of
intervals the capture maintainer picks has to meet all four.

- Each shard's `eth_getLogs` span is at most 29,999, the second transport's
  accepted ceiling, and the plan's `shard_width` is at most `MAX_SHARD_WIDTH`,
  50,000 at `interval.py:50`.
- The shard count is at most `MAX_SHARDS`, 4,096 at `interval.py:51`.
- The interval end is at or below the head both transports serve at collection
  time, re-read then rather than taken from the figures above.
- Every declared subject that exists at or before the interval end has an epoch
  inside the interval, and the journal components tile the shard range exactly.

One worked pair meets them. For V2, start 21,788,182 and shard width 25,000
gives 166 shards at end 25,938,181, with each shard spanning 24,999 blocks; that
is the pair the retired attempt planned, and it remains arithmetically
admissible. For V1, start 18,686,645 and the same width needs 125 shards to
reach 21,811,644, which covers the V1 estate's own span up to just past the V2
start. Neither pair is a decision. At the Compound reference's 500-block width
the V2 span alone needs 8,300 shards against the 4,096-shard limit, so the
smallest width that fits that span is 1,014; the largest the second transport
admits is 30,000, which is its last accepted value and leaves no margin.

**The component budget, and the journal split.** The retired attempt measured
the V2 estate's then-known twelve addresses at 366 logs, with the ArchController
at 220, the HooksFactory at 129, the wrapper factory at 14, the collateral
factory at 2, the fee recipient at 1 and the other seven silent. The 80 markets
emitted 68,756 logs and every one of them emitted at least once, across 139
non-empty windows, with the busiest single market at 23,694 logs and the densest
30,000-block window at 1,595. The total was 69,122 logs at a measured 671 bytes
each, which is 46.4 MB of log payload alone, 69.1 per cent of the 67,108,864-byte
ceiling that `release.py:55` and `interval.py:53` both set.

That total is now a floor rather than a figure. It was measured over 92
subjects. The V2 subject set is 137, and the 45 it gained are 42 hooks instances
and three contracts the earlier row did not carry; a hooks instance emits on
every role-provider and access change, so none of them is silent by
construction. The V1 estate's 16 subjects were never measured at all. So the
logs already stand at more than two thirds of one component's ceiling before the
JSON-RPC envelope each record carries is counted, before the hooks instances are
counted, and before a trace journal is added. That is why issue 1373 is on this
run's path. Traces are cheap when scoped, at 19 traces in 18,008 bytes for one
transaction and 1 trace in 595 bytes for a block-scoped filter, but the scale
here is two whole intervals.

The split boundary is fixed by the plan, not by observed byte sizes. The plan
declares a maximum number of shards per journal component; the component count
is then derived from the shard count, each component holds a contiguous shard
range, and their concatenation in shard order is the journal. A byte-driven
split would move the boundaries whenever a re-collection returned one more
record, so the release would stop being reproducible from its plan. `check`
re-derives the boundaries from the plan and refuses a release whose components
do not tile the shard range exactly, which is the doctrine
`validate_shard_coverage` at `interval.py:1305` already applies to shards.

**Boundaries.**

Always: both suites before a commit; the imprimatur lint on every shipped
document; the Horos boundary regenerated before the census, in the commit that
changes the tracked tree; a recorded measurement before any performance change.

Ask first: adding a dependency; changing the interval plan or receipt schema;
widening what a registry pin admits; touching CI; collecting outside a declared
interval; editing a dated observation in another record rather than appending
to it.

Never: commit an RPC endpoint, credential or key; edit a vendored directory;
vendor target protocol source into this repository; delete a failing test to
make a suite pass; claim a command ran when it did not; present constructed
bytes as preserved chain evidence.

**Non-goals.**

Neither excluded Wildcat row enters scope. `wildcat-v2-plasma-mainnet` is chain
9745, not Ethereum mainnet, and `targets.json` records its exclusion reason as
outside the operator-approved five-venue order and the Ethereum Wildcat estate.
`wildcat-v2.5-release-line` has `deployment: null` and is deployed on Sepolia
only, so there is no mainnet estate to collect. Both are `excluded` rather than
admitted, and `docs/kickoff/1374/capture.json` lists neither among its nine
admitted targets.

No credit event, position observation or repayment conclusion is derived. This
run preserves bytes and says what they cover.

No completeness claim is made. Each collected interval is what its plan
declared, and each release says so in its own coverage rather than implying the
estate's whole history.

Collateral instances are not enumerated. `targets.json` records that exclusion
against the collateral factory, and this run does not reopen it; the factory,
its stored init code and its lens are subjects, the instances it deployed are
not.

A client that serves `debug_traceBlockByNumber` instead of `trace_filter` still
needs a collector change, because `usdc_interval.py:491` compiles the trace
class to `trace_filter` alone. Both transports here serve `trace_filter`, so
that remains a named follow-on rather than this run's work.

## 4. Design options, the subject sets, and the fixture question

Four candidate constructions. The prose explains them; the selection is made in
`.hexaemeron/design-evidence.json` from the checked matrix, not from here.

**`venue-module-registry`.** One explicit `VENUES` table in a new
`alexandria_lib/venues/__init__.py`, keyed by the plan's `venue`, following
`mappings/__init__.py:18-31`. Each venue module owns four things: a registry
validator with its own byte-pin, the opening reads its epoch model needs, the
epoch derivation, and its contribution to `_gaps`. The `compound-v3` module
delegates to today's `compound_registry.validate_registry` and today's EIP-1967
functions with no change of behaviour. Trade: one indirection layer and one new
module tree, and a venue must be registered in reviewed code before any plan can
name it, so no operator can introduce one.

**`registry-format-dispatch`.** Dispatch on the registry document's own `format`
string instead of the plan's venue. Trade: the registry becomes self-describing,
but the plan's `venue` and the registry's format can then disagree with nothing
to catch it, because the venue is derived from the format rather than compared
against it.

**`venue-parameter-table`.** Keep one code path and supply the subject set, the
epoch parameters and the digest as an operator-side parameter document per
estate. Trade: no new module tree. The epoch difference is not a difference of
constants: a non-upgradeable estate reads no slot and scans no upgrade log at
all, so the branch returns anyway. An operator-supplied digest is also exactly
what the byte-pin exists to prevent.

**`separate-wildcat-collector`.** Leave `usdc_interval.py` untouched and ship a
second collector serving both estates. Trade: the Compound path is untouched for
free, but the acceptance condition asks for the existing `build` and `check`
path, and two collectors over one staging library drift.

**What the restored scope did to the selection, and what it did not.** The run
now admits two Wildcat venues rather than one, and exactly one figure in the
record moves with that. `venue-coupled-edit-sites` counts the sites each
candidate needs to admit both venues, so the per-venue cost doubles for the
three designs that add a module or an operator table per venue and stays flat
for the design that adds one further collector serving both. The counts become
4 for `venue-module-registry`, 5 for `registry-format-dispatch`, 5 for
`venue-parameter-table` and 5 for `separate-wildcat-collector`, against 2, 3, 4
and 5 under the single-venue reading. The ranking does not move, and neither
does anything else: the same three candidates fail a selection gate, the same
candidate passes all four, and `unique-frontier` resolves on one survivor before
either metric is consulted. The record says this mechanically rather than in
prose; `model-observations.json` beside it carries each candidate's declared
site list, so the count can be disputed by disputing a site rather than a
number.

What the restored scope did add is three conformance cells the V2-only record
had nowhere to put: a V1 release that builds and checks, a shared-subject rule,
and a declared V1 source gap. Those are pending at `integration`, as the other
five already were.

**What the voided digests did to the selection.** The earlier record carried a
selection gate requiring both recorded refusal strings to fire byte for byte.
With the prior captures and digests void, no criterion is spent on that.
Removing it does not move the selection either: `registry-format-dispatch`
becomes eligible, and is then removed by `venue-registry-agreement-checked`,
which asks whether the design can detect a plan whose declared venue disagrees
with the registry it was handed. Only a design that takes its venue from the
plan has two independent declarations to compare; one that derives the venue
from the registry's own format has nothing left to disagree with it.

**The two subject sets, and how each was derived.** Both come from
`docs/kickoff/1359/targets.json` at the digest in item 3, and both were
reproduced rather than read off a summary line.

V2 has 137 subjects, the length of
`targets[wildcat-v2-ethereum-mainnet].deployment.contracts`. By the `role` field
of those entries: 80 `market`, 42 `hooks-instance`, 3 `hooks-template`, 2 `lens`,
and one each of `registry`, `sanctions-sentinel`, `factory`,
`market-init-code-storage`, `wrapper-factory`, `fee-recipient`,
`collateral-factory`, `collateral-init-code-storage`, `collateral-lens` and
`role-provider`. The 32 role providers of the estate are not 32 subjects: 31 of
them are each instance's own borrower, which
`targets.json` `protected_set_exclusions` records as not protocol code, and only
the shared `OpenAccessRoleProvider` is in the row.

V1 has 16 subjects: the 6 entries of
`targets[wildcat-v1-ethereum-mainnet].deployment.contracts`, the 3 addresses of
`deployment.instances.controllers`, and the 7 of `deployment.instances.markets`.

The two sets intersect in exactly two addresses, `WildcatArchController`
`0xfeb516d9d946dd487a9346f6fee11f40c6945ee4` and `WildcatSanctionsSentinel`
`0x437e0551892c2c9b06d3ffd248fe60572e08cd1a`, which both rows carry and which
the V2 row marks `shared_with: ["wildcat-v1-ethereum-mainnet"]`. The union is
151 distinct addresses.

Three cross-checks were run against the bytes rather than assumed. First, the
arch controller's 87 registered markets at block 25,960,042 are exactly the
union of the 80 V2 markets and the 7 V1 markets, proved by set equality between
`arch_controller.getRegisteredMarkets` in
`docs/kickoff/1359/evidence/ethereum-mainnet-1590.json` and the two market
lists. Second, `getRegisteredControllersCount` is 4 while the V1 factory's
`getDeployedControllersCount` is 3; the fourth registered controller is
`0xdd7dd3b5076cf89440d05585ff56d246386207be`, the V2 HooksFactory, which the
arch controller also lists as a registered controller factory. Reading 4 as
four V1 controllers would have put a V2 subject into the V1 set. Third, the
recorded list digests reproduce, and the canonical form is not the same for both
rows. The V2 row's `v2_markets_sha256`,
`fd7174beb547e841a6f1b9716b4d13e5d861279f38b3d355d761dd6755a96ec0`, reproduces
as `sha256` over `json.dumps(sorted(lowercase addresses), separators=(',',':'))`,
which is the method the row itself declares, and the same form reproduces
`hooks_instances_sha256` over the 42 instances and `registered_markets_sha256`
over the 87. The V1 row's `markets_sha256`,
`b96da6374d45b26ac157a81b6811dc48931714d8baac80adb027f89fa8027c42`, does not
reproduce that way; it reproduces as the SHA-256 of the same addresses
lowercased, sorted, newline-joined with a trailing newline. That is the older
form, and it is also the form that reproduces the V2 row's
`prior_observation.v2_markets_sha256`,
`1b1c3684e01b3a99fe4f8ffb240639899b60ef5d7641105ef236cbf0ed73627a`, over the
current 80 addresses. So the earlier V2 digest still holds as a claim about the
set, and only the recorded canonical form moved; the two rows now disagree about
which form is canonical, and the registry generator therefore records the form
it used per row instead of assuming one.

The collected logs then check each list rather than supply it. The HooksFactory's
complete log history over blocks 21,788,182 to 26,006,347 is 129 logs, recorded
in `ethereum-mainnet-1590.json` under `factory_events`: 80 `MarketDeployed`, 42
`HooksInstanceDeployed`, 3 `HooksTemplateAdded`, 2 `HooksTemplateFeesUpdated`,
1 `ChangedSpherexEngineAddress` and 1 `ChangedSpherexOperator`. Keeping the
registry as the source and the logs as the check leaves both registries
reproducible offline while still letting a capture contradict one.

**Where the subject set lives.** The plan carries it. The cost is a second plan
format version. `validate_plan` at `interval.py:115` compares an exact key set,
so `proxy` cannot be widened in place and cannot gain a sibling field, and the
Compound plan's bytes sit inside a released component. A first-version plan
therefore keeps validating unchanged with its single-subject meaning, and a
second version carries the set. `shard_requests` filters `eth_getLogs` by the
declared address array rather than one address, `proxy_log_positions` accepts a
log emitted by any declared subject, and `attribute_logs` assigns each log to
the epoch of its own subject. Subject cardinality sits underneath the venue
dispatch rather than inside it, so the `VENUES` table and the registry pin are
unaffected, and the same is true of every candidate. It is a constraint on the
build rather than a selection axis, and the design record spends no criterion
on it.

**What the epoch axis is for a non-upgradeable estate, and the one change the
new data forces.** The code at a directly deployed address is fixed from its
deployment block onward, so the table degenerates to one epoch per subject:
`upgrade` null, `implementation` the subject's own address, and
`implementation_code_sha256` the SHA-256 of its runtime code. `upgradeable_proxies`
is 0 on both rows, and nothing in the 1590 data contradicts that, so
`immutable-code` serves both estates.

The change is where that epoch starts. The retired study bound each epoch to the
subject's own deployment block, which quietly assumes every subject predates the
interval. The new data shows it does not: `ethereum-mainnet-1590.json` records a
`deployed.block_number` for every market and every hooks instance, and those 122
deployments run from 21,866,550 to 25,895,380, inside any V2 interval that
starts at the row's declared start block of 21,788,182. So each subject's epoch
runs from the later of the interval start and that subject's deployment block to
the interval end, the code digest is read at that epoch's first block, and a
subject deployed after the interval end has no epoch at all and is named in the
release's coverage as outside the interval. Tiling is per subject over that
subject's in-interval extent, not one table over the whole interval, which is
what `validate_block_epochs` at `interval.py:961` checks today for a single
proxy. That validator is reused per subject rather than over the set, and
`MAX_EPOCHS` of 256 bounds each subject's table rather than the estate's.

Deployment-block coverage is not complete, and the gap is one subject. Of V2's
137, 134 carry a block in `ethereum-mainnet-1590.json`, in `creation_epochs` for
the core contracts and in `deployed.block_number` for the 122 instances and
markets. Two more, the shared arch controller and sentinel, carry
`deployment_block: 18686645` in their `code_match` records and in the `anchors`
of `docs/kickoff/1359/evidence/ethereum-mainnet.json`. The remaining one is the
collateral init-code storage `0xbbb998043a20a26828617769f37dc3980be25ebc`, whose
records carry a code length and keccak256 but no creation block; its epoch
therefore starts at the interval start and the release names the missing
deployment block as a gap rather than guessing it. Note also that two V2
subjects predate the row's own declared start block by 3,101,537 blocks, because
the shared pair was deployed with V1.

V1's coverage is much thinner, and this is what its blocker costs the capture.
Only the 6 recorded contracts carry a code digest, at block 25,960,042 for four
of them and 25,960,074 for the two init-code storages. The 3 controllers and the
7 markets carry neither a code digest nor a deployment block anywhere in the
merged records; `targets.json` records the exclusion in as many words, that the
code of the three controllers and seven markets was not read. Their epochs are
therefore derived entirely from the collection's own opening reads, and the V1
registry declares them as unpinned rather than carrying a digest it does not
have.

**Whether a V1 capture is admissible under its blocker, and what it owes.** It
is admissible. The blocker reads that V1 controller and market init-code source
matches have not been reproduced and that the preserved observation identifies
candidate contracts without establishing all historical implementation epochs.
Both clauses are about reproducing source from a pinned checkout; this capture
preserves logs, headers and runtime-code digests, and establishes no source
identity for anything. The recovery child is
https://github.com/wildcat-finance/skills/issues/1589 and it stays open.

What the capture owes is a declared gap, because coverage that says nothing
about source reads as though source were established. Three of V1's 16 subjects
carry a source commit in their `code_match` record: the arch controller, the
sentinel and the controller factory. The other 13 do not: the two init-code
storages and the MarketLens each record `source_commit: null`, and the 3
controllers and 7 markets are not in the contract list at all. The V1 release
therefore names those 13 in its own coverage gaps and claims source identity for
none of them. By contrast every one of V2's 137 contracts names a source commit,
so the V2 release carries no gap of that kind; what it does carry is the note
that two of those commits are in repositories private to the organisation, which
is why neither registry pins source bytes.

**Where the Wildcat staging bytes come from.** The registries and the journals
have different answers, and conflating them is the trap. Each registry is real
either way, generated from the pinned merged records above. The journals come
from the two authorised collections, so each shipped release rests on preserved
chain evidence. A constructed fixture still exists, because both venues must be
testable offline before any collection and after it, and that fixture must not
be able to pass itself off as preserved.

The mechanism: each venue module declares, in reviewed code, the set of
`deployment` names whose staging it admits as preserved. Every other deployment
under that venue carries a constructed-staging gap on each evidence scope,
emitted through the venue's own gap contribution. An operator cannot remove the
label, because it is a reviewed constant rather than a plan field, and the label
keeps working after the real captures land, because each fixture uses a
different deployment name and still carries the gap where a per-venue flag would
not have caught it. This is the one label this run adds against issue 1442.

**Selection.** `venue-module-registry`, on `unique-frontier`. It is the only
candidate that fails no selection gate, and it is lowest on both comparative
metrics. **The trade it makes:** one indirection layer and one new module tree,
in exchange for a venue set that no operator document can widen and a plan whose
declared venue is compared against the registry it is handed.

## 5. Risk register

The concerns the audit loop should look hardest at. The ids are how a round
cites them; the prose above carries what a line cannot.

```risk-register
undeclared-venue | a plan naming a venue with no registered module | build refuses by name and never falls back to Compound
venue-registry-disagreement | a plan venue and a registry format that name different venues | the build refuses rather than trusting either one
registry-pin-bypass | the two Wildcat registry digest constants | each pin lives in reviewed code and no plan field or operator document can supply it
registry-source-drift | the merged records the two Wildcat registries are generated from | the generator pins every record it reads by SHA-256 and refuses a changed one
canonical-form-mismatch | the address-list digest form, compact JSON for V2 and newline-joined for V1 | each registry records the form it used and reproduces its row's recorded digest under that form
market-list-completeness | the 80 V2 instances and the 7 V1 instances the registries declare | the collected deploy logs are compared against each list and a disagreement is reported rather than absorbed
registered-controller-miscount | the arch controller's count of 4 registered controllers | the V1 subject set takes its 3 controllers from the factory and never from that count
shared-subject-double-claim | the arch controller and sentinel, subjects of both venues | both registries declare them, their intersection is exactly those two, and neither capture attributes the other estate's subjects
epoch-model-substitution | each venue's epoch derivation | a non-upgradeable venue reaches neither the implementation slot nor the Upgraded topic
mid-interval-deployment | a subject first deployed inside the declared interval | its epoch starts at its deployment block, not at the interval start, and the table still tiles
per-subject-epoch-tiling | one epoch per subject over its in-interval extent | each tiles with no gap, declares no upgrade, and stays inside the epoch limit
missing-deployment-block | the collateral init-code storage, which records no creation block | its epoch starts at the interval start and the release names the missing block as a gap
v1-unpinned-code | the 10 V1 controllers and markets whose code was never read | the registry declares them unpinned and the epoch digest comes from the collection's own opening reads
v1-source-identity-overclaim | the 13 V1 subjects with no established source commit | the release names them in its coverage gaps and claims source identity for none of them
subject-set-attribution | a log from any declared subject of the capturing venue | every preserved log is attributed to the epoch of its own subject exactly once
plan-version-compatibility | a first-version single-subject plan | it still validates and still means one subject after the second version exists
component-budget | a journal larger than the release component ceiling | every component and every staging journal stays at or below its measured ceiling
journal-split-boundary | the shard ranges each journal component covers | the boundaries are derived from the plan and the components tile the shard range exactly
constructed-staging-claim | a release built from bytes no chain produced | the release's own coverage names the construction, not only a sibling README
credential-in-artefact | the second transport's endpoint and bearer token | neither string appears in any journal, component, receipt, test or committed byte
credential-in-error-text | a transport failure, HTTP status or redirect refusal | the message names the provider class and never the endpoint or the token
trace-reconciliation | the trace class across two transports | traces are compared rather than collected from one side, or the interval records unreconciled
unreconciled-count-misread | a reconciliation record whose matched equals compared under status unreconciled | the gap sentence and the forced partial status both survive, and no agreement is claimed
shard-width-second-transport | the shard width against the second transport's range cap | a width it cannot serve ends the interval unreconciled rather than partly agreed
v1-archive-depth-unprobed | the primary transport at the V1 start block | archive state at that block is read before the V1 plan is fixed, not assumed from the V2 probe
stale-capture-record | the dated V2 row and input digests in the 1374 capture record | the step that refreshes it names every field it moves and appends rather than rewriting a dated observation
partial-release-write | the release directory during a long build | a killed build leaves no half-written release that verifies
journal-descriptor-leak | the collector's journal handles on a refusal path | carried from issue 1679 and reviewed where this run's steps reach the same file
venue-test-member-set | the tests asserting the registered venue set | adding a venue changes a derived set rather than failing a hardcoded literal
carried-lead-bind-finality | the finality boundary comparison | fiat-1350's first unpursued lead is unchanged by this run and stays open by name
carried-lead-opening-compare | the first-block header comparison by hash alone | fiat-1350's second unpursued lead is unchanged by this run and stays open by name
carried-lead-undeclared-journal | a manifest journal for a class the plan did not declare | fiat-1350's third unpursued lead is unchanged by this run and stays open by name
```

## 6. Glossary seeds

**Venue.** The protocol generation a plan collects from, named by the plan's
`venue` field and used as the dispatch key. `compound-v3`, `wildcat-v1` and
`wildcat-v2` are the three this run ships.

**Estate.** One venue's deployed contracts on one chain, as a kickoff target row
records them. This run has two Wildcat estates, both on Ethereum mainnet.

**Deployment.** The named instance within a venue, the plan's `deployment`
field, and the granularity at which preserved provenance is admitted.

**Subject.** One address a plan collects logs and traces for. A first-version
plan has one; the V2 plan has 137 and the V1 plan has 16.

**Shared subject.** An address that is a subject of more than one venue. The
arch controller and the sanctions sentinel are the only two here.

**Deployment registry.** The digest-pinned document describing a venue's
deployed contracts and instances, generated from pinned source and validated
against a constant in reviewed code.

**Epoch model.** The rule that turns preserved opening reads into the epoch
table. `eip1967-proxy` derives epochs from upgrade logs and slot reads;
`immutable-code` yields one epoch per subject, running from the later of the
interval start and that subject's deployment block.

**Journal component.** One release component carrying a contiguous shard range
of one evidence journal, so a journal larger than the component ceiling ships as
several.

**Constructed staging.** A staging tree whose journals were written rather than
collected. Not preserved chain evidence, and named as such in the release's own
coverage.

**Preserved deployment.** A deployment name a venue module admits in reviewed
code as having been collected from a chain.

**Declared gap.** A sentence in a release's own coverage naming something the
capture does not establish, so absence is readable from the release rather than
from a sibling document.

## 7. Sources

Repository files, all read at `b2f528e9bee8dc4bd4d1653f7f66fe6b1de93bc0`:

- `plugins/alexandria/scripts/alexandria_lib/compound_registry.py`, for the
  constant at `:18`, `validate_registry` at `:162`, the byte-pin at `:216` and
  the generation shape.
- `plugins/alexandria/scripts/alexandria_lib/interval.py`, for the caps at
  `:49-58`, the EIP-1967 constants at `:77-78`, `plan_shards` at `:83`,
  `validate_plan` at `:115`, `proxy_log_positions` at `:687`, `validate_epochs`
  at `:793`, `attribute_logs` at `:832`, `validate_block_epochs` at `:961`,
  `opening_prefix` at `:1226` with its slot read at `:1243`,
  `validate_shard_coverage` at `:1305` and `validate_reconciliation` at `:1334`.
- `plugins/alexandria/scripts/usdc_interval.py`, for `HttpsTransport` at `:151`,
  `shard_requests` at `:483` with the trace class at `:491`, the registry call
  at `:1184`, `_capture` at `:1324`, `_status` at `:1431`, `_gaps` at `:1457`,
  `_recheck_implementation_code` at `:1984` and `check_interval` at `:1560`.
- `plugins/alexandria/scripts/alexandria_lib/release.py`, for
  `MAX_RAW_COMPONENT_BYTES` at `:55`.
- `plugins/alexandria/scripts/alexandria_lib/mappings/__init__.py`, for the
  venue-dispatch precedent at `:18-31`.
- `plugins/tabularium/scripts/tabularium_lib/release_v2.py` and
  `plugins/tabularium/scripts/tabularium.py`, for the adapter registry at
  `:13-17` and the duplicated argparse venue list at `:27-32`.
- `plugins/alexandria/examples/usdc-interval-live-v0/`, for the preserved live
  capture, its plan's `"venue":"compound-v3"`, and its checkpoint.
- `plugins/alexandria/examples/usdc-interval-v0/README.md`, for the synthetic
  fixture precedent and the wording it uses to disclaim its bytes.
- `plugins/alexandria/schemas/interval-plan-v1.schema.json`, for the
  unconstrained `venue` name and the three-member evidence-class enum.
- `plugins/alexandria/skills/alexandria/EVOLUTION.md`, for the current version
  `alexandria-v3.5.0` and the held next job this run does not take.
- `plugins/alexandria/docs/usdc-interval-epochs/design-evidence.json`, for the
  design-record and resolver shape this study follows.
- `docs/kickoff/1374/capture.md` and `capture.json`, for both reference-target
  rows, the required capture, `upgradeable_proxies: 0` on each, the nine
  `pattern_release.coverage` rows, the stale `source_revision` and the stale
  `inputs[0]` digest.
- `docs/kickoff/1374/evidence/commands.json`, for the six commands and both
  refusal specimens with their exact stderr and refusal sites.
- `docs/kickoff/1359/targets.json`, for the 17 rows, the V2 row's 137 contracts
  and its `deployment.instances` and `deployment.epochs` blocks, the V1 row's 6
  contracts and its `deployment.instances.controllers` and `markets`, both
  blockers, both exclusion lists, the eight `protected_set_exclusions` and the
  two excluded Wildcat rows.
- `docs/kickoff/1359/evidence/ethereum-mainnet-1590.json`, for the 170 code
  reads at block 26,006,289, the 3 templates with their creation and
  registration epochs, the 42 hooks instances with their deployment blocks and
  role providers, the 80 markets with their deployment blocks, the 32 providers,
  the creation receipts and the factory's 129 events.
- `docs/kickoff/1359/evidence/source-match-1590.json`, for the located sources
  and their reproductions, the two private repositories, the MarketLens epoch
  and consumer map, and the emitter-pin blob table.
- `docs/kickoff/1359/evidence/ethereum-mainnet.json`, for the V1 controller
  factory's 3 deployed controllers, the 7 derived V1 markets and their digest,
  the 16 code reads at block 25,960,042 and 25,960,074, and the six deployment
  anchors.
- `audit/AUDIT.md`, `audit/AUDIT_SYNOPSIS.md` and the three round records named
  in item 2.
- `plugins/hexaemeron/skills/protasis/scripts/gate_commands.py`, for the
  registry at `:28-33` and the builder requirement at `:183-186`.
- `scripts/run_checks.py`, `scripts/plugin_release.py`,
  `scripts/kickoff_targets.py`, `tests/test_boundary_currency.py`,
  `tests/test_demonstrations.py` and `tests/test_kickoff_targets.py`, for the
  gate inventory above.

Pull request bodies read in full:
https://github.com/wildcat-finance/skills/pull/1690,
https://github.com/wildcat-finance/skills/pull/1448,
https://github.com/wildcat-finance/skills/pull/1733 and
https://github.com/wildcat-finance/skills/pull/1735.

Issue bodies read in full: https://github.com/wildcat-finance/skills/issues/1731
with both its amendments.

Digests and address-set reproductions: recomputed in this phase against the base
commit, with the exact canonical forms recorded in item 4.

Transport and log-volume measurements: recorded by the controller during the
retired first attempt and reproduced in item 3, with the two figures the
restored scope invalidates named there. Not re-probed here, because the primary
is syncing and a second load was declined.

## 8. Signals, and the questions behind them

Four questions someone will ask once a capture runs unattended, and where the
signal that answers each comes from.
`plugins/hexaemeron/skills/ephoros/SKILL.md` owns what a signal must carry.

**Which shard is it on, and can it be resumed?** Already answered by the
checkpoint at `staging/checkpoint.json`, which records `next_shard`,
`last_accepted` and a per-class byte offset after fsync. This run adds no shard
behaviour and changes no checkpoint field, so it emits no new signal here. Over
a hundred and more shards rather than four, and over two collections rather than
one, that record is what tells an operator whether a long run is progressing or
stuck.

**Did the second transport answer, and where did it stop?** The reconciliation
record carries `status`, `compared`, `matched` and `provider_class`. The
register entry `unreconciled-count-misread` records that it does not carry where
the comparison stopped. The step that touches reconciliation coverage owes that
question an answer in the release's gaps rather than a new log line, because the
collector writes no log stream and the release is the artefact an operator reads.

**Which venue answered for this plan, and over how many subjects?** New. A
release must make the dispatch decision legible offline, so the capture's
`venue` field, the registry component's own format and the declared subject
count together name it, and `check` compares them. No signal is emitted at
collect time, because the dispatch happens in `build`, which is offline and
whose whole output is the release.

**Did any component or journal approach its ceiling?** New, and the reason issue
1373 is on this path. The release's component byte counts are already in its
manifest, so the signal exists; what is missing is that nothing compares them
against the ceiling. The step that splits journals makes that comparison part of
`check` rather than leaving it to a reader.

## 9. Trust boundaries, per capability

`plugins/hexaemeron/skills/phylax/SKILL.md` owns the boundary list and the
controls. Six boundaries this run opens or moves.

**The plan's `venue` string selects code.** Worth taking: letting an operator
document choose which validator and epoch model run. The control is that the
string indexes a table of modules registered in reviewed code and nothing else;
an unregistered name refuses by name, a registered name still faces its module's
own byte-pin, and the module compares the registry it is handed against the venue
the plan declared.

**The plan's subject set selects what is requested.** Up to 137 operator-supplied
addresses now reach `eth_getLogs` filters and trace filters. The control is that
each is validated as a lowercase address before use, that the venue's own
registry supplies the admitted set, and that a log from an address outside the
declared set is refused rather than attributed.

**Two venues declare the same address.** Worth taking: the arch controller and
the sentinel really are part of both estates, and dropping them from one would
lose that estate's registry events. The control is that the intersection is
asserted to be exactly those two addresses in reviewed code, so a third shared
subject appearing later fails a test rather than silently joining both captures.

**The Wildcat registry generators read repository files.** The Compound
generator runs `git` through `subprocess` at `compound_registry.py:49-58` with
no shell and pinned arguments. The Wildcat generators read merged repository
JSON instead, so they need no subprocess at all; if one is added it follows the
same shape. The control is the digest pin on every record they read, and the
recorded canonical form for each address-list digest they reproduce.

**The process holds a bearer token for the first time.** The control is that the
credential is held on one instance attribute, reaches one header, is never
written to the module-level header constant, and is proved absent from every
file the run writes by walking each staging tree and release directory for its
bytes.

**Constructed bytes could be presented as preserved evidence.** The control is
the reviewed per-deployment preserved-set declaration in item 4, which an
operator cannot edit through a plan, and the conformance criterion that proves a
constructed deployment carries the gap.

## 10. The performance budget

One budget, and it belongs to the collections rather than to the code.
`plugins/hexaemeron/skills/metron/SKILL.md` owns what a budget carries.

Each capture must finish inside a working day of wall clock on the syncing node,
measured by the collect command's own elapsed time and recorded with the
demonstration. The one measured point is 20.5 seconds for a 50,000-block
`eth_getLogs` over a single address under sync load. It is not extrapolated to a
25,000-block shard, to a 137-address filter or to a second estate, because none
of those was measured; the budget exists so that a run which cannot finish is
stopped and re-planned rather than left going. The step that plans each
collection records its own elapsed-time measurement before the collection starts,
so the budget is checked against that estate rather than against the other one.

The rest of the run claims no performance budget. Venue dispatch adds a
dictionary lookup and one branch to a path dominated by network and by canonical
JSON encoding, and the journal split changes how bytes are grouped rather than
how many are produced.

## 11. The fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md` owns the triage order and the
guard rule.

What stops the run. Every failure in this subject is an `AlexandriaError`, caught
with `OSError` at `usdc_interval.py:2222`, printed as
`usdc-interval: <message>` and exited 1.
A venue that cannot be resolved, a registry that disagrees with its plan or
fails its pin, an epoch table that does not tile its subject's extent, a log
from an undeclared subject, a component over its ceiling and a reconciliation
that could not complete all stop rather than degrade. The reconciler already
abandons to `unreconciled` rather than recording a partial agreement, at
`usdc_interval.py:1042`, and that posture is kept for the trace class too. A V1
subject whose code the merged records never read is a declared gap rather than a
guessed digest, and a release that would claim source identity for it refuses.

Guard convention. A fix claimed in an audit round is proved by a test that fails
without it, run through the step's declared Elenchus command with one `{report}`
argument, its report format and its report file named in the runbook step's
`Tests` field. Alexandria's suite is
`python3 plugins/alexandria/tests/run_tests.py`, and new guards go beside the
existing ones in `plugins/alexandria/tests/test_interval.py` and
`test_usdc_interval.py`, which between them already hold the registry, subject
and epoch assertions this run moves.

## 12. Decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` owns which decisions earn a
record and where each lives. Five here are expensive to reverse.

**Dispatch on the plan's venue rather than the registry's format.** Once plans
and releases exist under it, changing the key changes which releases still
build. Home: a decision record at
`docs/adr/<number>-venue-dispatch-for-the-interval-collector.md`. The number is
allocated at the scaffold step against the default branch and re-checked
immediately before pushing, because ADR numbers collide before merge.

**Preserved provenance is declared per deployment in reviewed code.** It decides
what a release may claim about its own bytes, and loosening it later would
silently upgrade the claim of every release already built. Home: the same
decision record, as a second section, because the two decisions are one design.

**The plan gains a second format version carrying a subject set.** A plan format
is read by every later release and by `check`, so reversing it would orphan
every plan written under it. Home: the same decision record, as a third section,
with the exact-key-set reason that forces a version rather than a new field.

**A subject may belong to more than one venue.** Reversing it would force one of
the two estates to drop the arch controller and the sentinel, which is where
that estate's registration events are emitted. Home: the same decision record,
as a fourth section, with the asserted intersection.

**One epoch per subject, starting at the later of the interval start and that
subject's deployment block.** Reversing it would change every Wildcat epoch
table and therefore every Wildcat release identifier. Home: the alexandria
evolution ledger row for this delivery, at
`plugins/alexandria/skills/alexandria/EVOLUTION.md`, in the shape the
transaction-position decision already uses there, plus the collector document
`plugins/alexandria/docs/usdc-interval-collector.md`.

Two decisions deliberately get no record. The venue set this run ships is data,
not a decision, and it is readable from the `VENUES` table. The narrowing to
Wildcat V2 and its withdrawal are the capture maintainer's, recorded on
https://github.com/wildcat-finance/skills/issues/1490 and
https://github.com/wildcat-finance/skills/issues/1731 rather than here.

### Amendment -- 2026-09-19

**What changed.** Section 12's home for the dispatch, provenance, plan-version
and shared-subject decisions is corrected from
`docs/adr/<number>-venue-dispatch-for-the-interval-collector.md` to this
repository's convention: the record begins as an unnumbered draft at
`docs/decisions/drafts/<slug>.md` and becomes
`docs/decisions/ADR-<NNN>-<slug>.md` when the integration composer numbers it.
The clause allocating the number at the scaffold step against the default
branch and re-checking it before pushing is corrected with the path: the author
writes no number, and
`plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py` assigns
one in the final integration composition. Which decisions earn a record, how
many there are, what each says, and the fifth decision's home in the alexandria
evolution ledger are all unchanged.

**Why.** No `docs/adr` directory exists anywhere in the tree, so the section
named a home that is not there. The convention stated in
`plugins/hexaemeron/skills/hypomnema/SKILL.md` and visible in the tree places
102 numbered records directly under `docs/decisions/` and 3 unnumbered drafts
under `docs/decisions/drafts/`, numbered only at integration. Step 1 ships this
study into the repository under `plugins/alexandria/docs/wildcat-interval/`,
where a pointer at an absent directory reads as though the home exists and was
checked. Recorded as finding W1-R1-02 in the step 1 round 1 audit and left open
there because the study is controller-pinned.

**Steps touched.** Steps 1, 2, 3, 6 and 7.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds. Step 8: entry holds; exit holds. Step 9: entry holds; exit holds. Step 10: entry holds; exit holds. Step 11: entry holds; exit holds.
