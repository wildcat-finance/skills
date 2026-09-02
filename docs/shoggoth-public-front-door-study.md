# Study: restore the Shoggoth public front door and demo frontier

This is the second study for this topic. The first is preserved at
`front-door-run-1/study.md` in the operator's archive; its receipted digest was
`d96c4b1d669e4fcda9e5b339a6b1be210c079c63e597cd5021fcf24e1f7cace7`. That run
reached step 3 of 6 and was halted deliberately. Section 2 records what it
established, what it got wrong, and what is carried forward unchanged.

Assuming, unless corrected:

1. The working base is `main` at commit
   `66b6cfd6b20610484321abcb85079a0dce1b6070`. `git rev-parse HEAD` in the run
   worktree returned that commit on 2 September 2026.
2. "Front-facing" means the maintained human entry surface: `README.md`,
   `INSTALL.md`, `FUTUREPROOFING.md`, `SHOGGOTH.md`, `PROMISE_MACHINE.md`,
   `docs/how-to-help-shoggoth.md`, `docs/fiat-in-plain-english.md`,
   `docs/the-promise-machine-explained-properly.md`, all 18 first-party plugin
   `README.md` files, and the two generated PDFs under `docs/pdf/`. Agent
   contracts, canonical `SKILL.md` files, ADRs, audits, historical studies,
   runbooks, and specimens are factual sources, not surfaces to restyle. A
   factual correction still propagates to any canonical contract or host
   metadata that owns the fact.
3. "All headers need All Caps" applies to every ATX heading on that maintained
   human entry surface. It does not rewrite headings in normative agent
   instructions, audit evidence, ADR history, or specimens.
4. The authoritative roster is whatever discovery returns at the tree under
   test. At the starting ref that is 18 plugins, 27 governed first-party
   skills, 18 canonical entry skills and 9 Hexaemeron phase skills. No number
   in this study is a target: each is an observation, and every check must
   recompute it rather than compare against a literal. The four Fiat workers
   and five vendored Pashov skill directories are described separately and are
   not added to the governed count.
5. **Dokimasia is a governed member, not a pending name.** The first study
   assumed the opposite on the user's word and found no evidence either way.
   That assumption is now false and is withdrawn. `plugins/dokimasia` ships a
   plugin manifest in both marketplaces, `SKILL.md`, `EVOLUTION.md` at
   `dokimasia-v2.1.0`, five built verbs, five schemas, two ADRs, and one
   committed scrutiny. It is counted, rostered, and given a demonstration
   ledger on exactly the same terms as every other governed skill.
6. A "real-data demonstration" is an executable path over preserved bytes
   originating in an actual chain, protocol, repository, audit, application, or
   production run. Its source identity, digest or chain anchor, command,
   expected result, and non-claim must be checkable offline. A demo with a
   constructed corpus, an unrelated target corpus, or a synthetic substitute is
   classified `mixed` or `constructed`, not promoted by good prose.
7. The old "So, You Want To Build God?" front door supplies voice and ordering,
   not current facts. Its 15-plugin and 24-skill counts, old install command,
   long warning block, and historical Atlas details are not copied forward.
8. The prototype couples two capabilities deliberately: public claims and
   governed demonstration evidence. A prose-only front door would drift again
   within one merge; a demo registry with no humane front door would not answer
   the user. The implementation splits them into auditable steps, but the final
   demo proves the joined path.
9. The public demonstration set is four cards, not three. Anamnesis, Lazarus
   and Alexandria were the first study's set. Dokimasia joins it because its
   path was verified offline on the build machine at the starting ref, and
   because the brief asks that the newest member be shown rather than promised.
   Section 4 states the caveat that could demote it, and the checker, not this
   study, is what enforces the demotion.
10. Every count in Section 2 was measured on the run worktree at the starting
    ref with the commands named beside it. Timings are single observations on
    one Apple silicon machine under CPython 3.14.6; they bound nothing about
    another machine.

## 1. Problem statement

The public front door is a complete technical catalogue placed before the
invitation, and its facts have drifted one member behind the tree.

Measured at the starting ref, `README.md` is 402 lines, 2,713 words and 20,854
bytes. `## Contribute` begins at line 295, after 2,028 of 2,713 words: 74.8% of
the way through the file. Seventeen link targets appear exactly twice. The
roster carries 27 entries whose lengths run from 8 words (Fiat) to 77
(Homologia) against a median of 17; Anamnesis takes 48 and Protasis 41. A
960-pixel Anamnesis portrait sits at line 179 inside the roster, even though
`SHOGGOTH.md` places a member portrait on that member's own landing page. All
10 H2 and 9 H3 headings are sentence case.

The count prose is worse than stale; it is self-contradictory inside one file.
`README.md:18` says 16 plugins and 25 governed skills. `README.md:21` and
`README.md:247` say 26 members as 17 domain agents and 9 phase agents. The tree
says 18, 27, 18 and 9. `SHOGGOTH.md:20` says 25 members and 16 domain agents.
`docs/the-promise-machine-explained-properly.md:157` says 16 and 25.
`docs/how-to-help-shoggoth.md:5` says all 25 members.
`.agents/skills/promise-machine/SKILL.md:18` says sixteen plugin contracts and
line 29 says 25 governed first-party skills. Six documents, four different
answers, none of them right.

The immediate users are:

- a curious person who needs to understand what the Shoggoth is in one breath;
- a potential contributor who needs the invitation and the safe route before
  the machinery;
- an engineer looking for one real operation with checked evidence rather than
  a list of possible compositions;
- an existing operator who needs the full technical map later, without losing
  the Promise Machine, identity, installation and authority boundaries; and
- a maintainer who needs public claims to stop drifting away from what the
  repository can actually demonstrate.

A working prototype has four joined outcomes.

**First, the root README becomes a front door, not the building.** It keeps the
Shoggoth portrait, opens with no more than 150 plain words explaining what the
collective is and does, then puts `## SO, YOU WANT TO BUILD GOD?` and the
external-contributor route within the first 220 words. The exact old chirp,
"Ask the Atlas for a number. Pick your harness. Finish what you start.", is a
tone anchor worth retaining. At least one further short, self-aware line
appears before the first technical section. The first mention of the Promise
Machine contract and the first roster or catalogue link come after contribution
and demonstrations. The file is at most 1,400 words, no identical link target
appears twice, and it does not inline the complete governed roster.

**Second, `## WHAT CAN IT DO?` shows four executable real-data cards.** Each has
one command, a named preserved source, one concrete observed result, and one
sentence saying what the result does not establish. The four are Anamnesis
rebuilding the committed pilot from real public audit records; Lazarus
rebuilding and verifying the Goldfinch v1 Ethereum mainnet receipt fixture at
block `0xc7da16`; Alexandria rebuilding `credit-history-v0` from preserved
Goldfinch and Clearpool inputs through release, index, query and the Probitas
handoff; and Dokimasia reproducing its `wildcat-app-v2` scrutiny at application
commit `bb9685fb` against reviewed workbook `9da2f2e8`. All four were executed
at the starting ref; Section 2 records their commands, results and durations.
Berean stays `mixed` because its chain reads are real but its document corpus
is a demonstration corpus rather than captured Wildcat material. Synkrisis
stays `constructed` until its held production cohort lands. Those distinctions
belong in the technical frontier, not under a "real data" heading.

**Third, each of the 27 governed skills gains an independently versioned
demonstration ledger beside its `EVOLUTION.md`.** The ledger carries a closed
executable record and a separate `Next demonstration job`. A new
`demo-frontier` lane can fund real-data proof without replacing or silently
advancing the skill's behaviour frontier. Where one existing `{skill}-next` job
would also satisfy the demo frontier, both ledgers may point to the same issue
and Fiat run; each ledger still advances only against its own acceptance
evidence. A demo-only job uses a governed `{skill}-demo` title and
`demo-frontier` label once the queue decision lands. Kronos ranks this lane
only when explicitly asked for it; its behaviour-frontier operation is
unchanged.

**Fourth, the rest of the maintained public surface is reconciled rather than
blindly rewritten.** All public headings take the agreed all-caps house style.
Every mutable count claim is derived from discovery, and no check compares a
live count against a literal. The full technical catalogue lives once, in
`FUTUREPROOFING.md`. The Anamnesis root portrait is removed while its
contextual member-page portrait and character section stay. Two live factual
errors are corrected: `plugins/anamnesis/README.md:106-107` still says the
version implements source admission only, while `anamnesis-v3.1.0` builds,
verifies and projects a release; and `README.md:94-96` still says Dokimasia's
compile path has not shipped, while `dokimasia-v2.1.0` compiles, imports,
reconciles and demonstrates. The contributor guide and PDFs keep the
external-human identity boundary. The portable package is tested through
`wildcat-finance/skills-runtime` rather than by recommitting the ignored
generated runtime.

The proving path for the joined prototype is:

```bash
python3 scripts/check_public_front_door.py --root .
python3 scripts/demonstrations.py check --root .
python3 scripts/demonstrations.py run --public-set \
  --report .hexaemeron/reports/public-set.json
python3 scripts/run_checks.py --full
```

The first command proves ordering, word and link budgets, all-caps public
headings, one full technical catalogue, portrait placement, derived counts, and
that Dokimasia is described as a shipped member. The second discovers exactly
the same governed skills the evolution tests discover and checks every
demonstration ledger. The third runs only the entries marked `real-data` and
named by the root public-demo list, with network denied by default, and fails
if a card, record, source, command, expected result or non-claim disagrees. The
last closes the repository's whole 28-check dependency map, which is what CI
runs; three lints are not CI.

## 2. Prior art

### What the first run established, and what it got wrong

The first run's study was sound when written and most of it survives. Its
problem analysis, its layering argument, its status taxonomy, its risk
register, its glossary, and its selected design are carried forward. Its
runbook produced two complete, receipted, still-open pull requests:
[#1077](https://github.com/wildcat-finance/skills/pull/1077) at `34f6b8ab`
scaffolded `scripts/shoggoth_topology.py` and its tests, and
[#1078](https://github.com/wildcat-finance/skills/pull/1078) at `d06e63c9`
governed one demonstration ledger per skill. Neither is merged. Both are prior
art this run must consume or refuse by name.

Its base `a2b634d8` predated the Dokimasia merge, so its tree had 17 plugins
and 26 governed skills while `main` had 18 and 27. Three specific defects
followed, and correcting them is the whole reason for this re-run.

**Defect one: the tests bound literal counts to the live tree.**
`tests/test_shoggoth_topology.py:159-177` on branch `d06e63c9` runs one test,
`test_valid_fixture_and_live_tree_return_17_26_17_9`, which loops over both the
synthetic specimen and the live tree asserting the same `17`, `26`, `17`, `9`,
plus the same `EXPECTED_CANONICAL` and `EXPECTED_PHASES` tuples for both. Lines
176 and 177 then assert `specimen.plugin_ids == live.plugin_ids` and
`specimen.governed_ids == live.governed_ids`. The fixture
`tests/fixtures/shoggoth-topology/valid-17-26.json` names the real plugin ids,
so the specimen is yoked to live identity and any new plugin breaks it. The
first run's own risk register had already forbidden this: `count-drift` reads
"tests derive 17 canonical and 26 governed agents and reject stale mutable
literals". The runbook then contradicted the study it was derived from.

**Defect two: the module was innocent.** `scripts/shoggoth_topology.py` at
`d06e63c9` is 424 lines and contains no hardcoded count. It anchors discovery
at `plugins/<plugin_id>/skills`, walks without following symlinks, refuses a
duplicate id, a manifest disagreement, a governed directory with no regular
`SKILL.md`, and a phase outside Hexaemeron. Run unmodified against the current
tree it returns 18, 27, 18 and 9, and the 9 phase ids `elenchus`, `ephoros`,
`hypomnema`, `imprimatur`, `kronos`, `metron`, `phylax`, `protasis`, `vulgate`.
Only the test and the fixture carried literals. Carry the module forward
essentially unchanged; replace the test.

**Defect three: a macOS workaround that is no longer needed.** The first run's
third amendment moved the registered Lazarus demonstration off
`plugins/lazarus/examples/goldfinch-v1/demo.py` because the fixture producer
resolved its stage through `/proc/self/fd` or `/dev/fd`, which macOS does not
supply as traversable directories. [PR
#1049](https://github.com/wildcat-finance/skills/pull/1049) merged as
`20ba7691` at 2026-08-31T18:26:36Z, closing issue #881, and is an ancestor of
the starting ref. The `REQUIRES_TRAVERSABLE_DESCRIPTOR_STAGE` skip is gone from
`plugins/lazarus/`. Verified rather than assumed: the whole demo was run at the
starting ref under the ambient macOS `TMPDIR` of
`/var/folders/2l/ft_wrtys7tj88xf2pkdjcflw0000gn/T/`, exited 0 in 7.87 seconds,
and reported `"fixture_rebuild":"identical"`. The registered Lazarus path is
the real producer command again, and the amendment's reasoning is dropped.

Two things the first run halted over are also settled here. Its steps 1 and 2
were complete and receipted, so `amend runbook` could not reach their exits;
this run's step 1 and step 2 are written against 18/27 topology from the start.
And Dokimasia's 27th ledger could not be authored in a tree with no
`plugins/dokimasia`; it exists at the starting ref.

### Current repository evidence

`README.md` is 402 lines, 2,713 words, 20,854 bytes. Its H2 sequence is `What
can it do today?` at 23, `What is not built yet?` at 89, `How the collective
works` at 117, `Meet the collective` at 152, `Try it` at 261, `Contribute` at
295, `Repository map` at 353, `Identity and authority` at 379, `Licence` at 390
and `Thanks` at 398. The intro to the first H2 is 159 words. The Atlas
bootstrap badges, which opened the old front door at line 40 of 421, now sit at
lines 317 to 319.

`tests/test_marketplace_prose.py` is where the count problem is best evidenced,
because the same 564-line file both derives the roster and pins a stale
literal, and the suite is green. Line 300 reads
`self.assertEqual(len(governed), 27)` over a live glob of
`plugins/*/skills/**/SKILL.md` with an `EVOLUTION.md` sibling. Line 187 reads
`self.assertIn("26 members: 17 domain agents and\n9 phase agents", readme)`.
Twenty-seven and twenty-six, in one file, neither noticing the other.

`git log -S` isolates the moment. Commit `67a01a6c`, the Dokimasia landing,
changed `README.md:21` from "25 members as 16 domain agents" to "26 members as
17 domain agents", changed `README.md:247` the same way, and changed the test
literal from 26 to 27, all by hand, in one commit. The author applied the
Anamnesis correction that was overdue and did not apply their own. The literal
lags exactly one member behind, permanently, because a person has to move it
and the suite passes either way. `README.md:18` was not touched at all and
still says 16 and 25.

`python3 -m unittest tests.test_marketplace_prose` runs 23 tests and exits OK at
the starting ref. That is the point: nothing in the repository can currently
tell a reader that its own front door is wrong.

The count sources themselves agree. Both `.claude-plugin/marketplace.json` and
`.agents/plugins/marketplace.json` list the same 18 plugin names. `find plugins
-name EVOLUTION.md` returns 28 paths; one,
`plugins/hexaemeron/tests/fixtures/hypomnema/design-bridge/plugins/example/skills/example/EVOLUTION.md`,
is a test fixture, leaving 27. `find plugins -name SKILL.md` returns 33; one is
the same fixture, leaving 32, of which 5 are upstream Pashov directories with
no `EVOLUTION.md`: `fizz`, its nested `fizz-convert` and `fizz-sync`,
`solidity-auditor`, and `x-ray`. Twenty-seven governed plus five upstream is
thirty-two. The fixture tree is excluded structurally, because discovery is
anchored at `plugins/<id>/skills` and the fixture lives under
`plugins/hexaemeron/tests`; that exclusion is cheap to break by widening a glob
and therefore earns its own check.

`INSTALL.md:214`, `215` and `242` say thirteen and fourteen plugins. Those are
historical statements about a dated capture, not current-topology claims. They
must not be rewritten. Any derived-count check has to distinguish a claim about
now from a record of then, and the safest boundary is that only sentences the
check itself owns are rewritten.

All 27 evolution ledgers were surveyed. Five are `mature` (Ariadne, Elenchus,
Kronos, Phylax and Protasis) and 22 are `open`. Berean's ledger requires
captured Wildcat documents and market reads; Synkrisis's requires a captured
production cohort; Tabularium's holds `compound-v3-phase-1`. Those are useful
real-data jobs, but forcing every demo gap into the one behaviour frontier
would displace unrelated held work and rewrite existing digests. That is the
case for a parallel demonstration lane.

Four real-data paths were executed at the starting ref on the build machine.

- **Anamnesis.** `python3
  plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo --specimen
  plugins/anamnesis/specimens/pilot`, exit 0, 0.19 s wall. Two fresh builds
  agree on `079ed18d172d6031551cbda55d25a2c064d255186cd8e27a62e90d26da06ae56`
  across 7 components; the committed release verifies at 41 findings over 31
  rounds with 12 rounds carrying none; the Elenchus projection returns 2 high
  analogues and a `None` verdict; the Synkrisis cohort
  `cohort:079ed18d172d6031` includes 41 of 41 findings with 0 exclusions and
  144 unknowns. It does not prove corpus completeness, finding truth, or remedy
  effectiveness.
- **Lazarus.** `python3 plugins/lazarus/examples/goldfinch-v1/demo.py`, exit 0,
  7.87 s wall, `"network":"denied"`. Block `0xc7da16`, 224 contiguous receipts,
  receipts root `0xaf03b0508121deb9ed0282a8961dc0ea695a97244a42ed2b0af04cb9bbc6226e`,
  target index `0xbf`, 110 target logs, the exact 5-log projection, 2 proved
  relations, and six mutation classes rejected. Fixture digest
  `aadf1b809ae45946967e17f2132ae4d73b06026345b0e8c7f1ca4c3c0add9535`, release
  `701fa846f81c28ede5ab9539c0c19815dfe7435eca45ba663219c0c88c3bdb74`. It
  records `"transaction_hash_attribution":"recorded_rpc"`: transaction hashes
  are recorded RPC metadata, not a proved header identity, and nothing here
  establishes canonical-chain finality or provider independence.
- **Alexandria.** `python3
  plugins/alexandria/examples/credit-history-v0/demo.py build --output <dir>`
  in 1.12 s and `verify <dir>` in 0.75 s, both exit 0, both printing derived
  release `sha256:d57f0b009d40a804e5f760e8cde4a6b1eb1ada1cc9dbf858e0494c1e750e840c`.
  The derived release holds 522 credit events (39 borrowing, 483 repayment,
  over 13 subject addresses) and 31 position observations. The Clearpool
  adapter mapped 11 of 12 source records; Goldfinch coverage is `partial`.
  Probitas emits 11 records and passes its five gates, accounting for 15 venues
  over 15 rows with 1 queried and 14 gaps stated. It does not establish source
  authenticity, complete venue coverage, or canonical-chain finality.
- **Dokimasia.** `python3 plugins/dokimasia/scripts/dokimasia.py demonstrate
  --check`, exit 0, 0.38 s wall, reporting that a scrutiny is deterministic,
  each moved identity names its own cause, and the committed evidence
  regenerates. The scrutiny scopes 261 items: 59 compiled from application
  `wildcat-app-v2` at commit `bb9685fb7dbe9cd2f5b7683a9b3f164509dc2de9`, 202
  imported from reviewed workbook `wildcat_v25_uat_v2-jack.xlsx` at
  `9da2f2e8bbdb0271fac8d9a71f3f4129ca2d4ad79a4c1ee2f46412e831212a25`. At
  `dokimasia-v2.1.0` it reports a closure ratio of 202 over 261, or
  0.7739463601532567, with 202 gaps stated and 59 items left undisposed. All
  202 dispositions are `manual` and `covered` is still zero, because ADR-001
  reserves `covered` to a person holding an item to a reviewed oracle. It does
  not establish that anything passed; a closure ratio states only that nothing
  is unaccounted for, and the 59 compiled items carry drafted exclusions
  nobody has decided on.

### The last two merged pull requests that changed the subject

1. [PR #1115](https://github.com/wildcat-finance/skills/pull/1115), "Stop the
   frontier prose sweep checking nothing in a .claude clone", merged
   `75d8b658` at 2026-09-01T23:45:54Z. It is the sharpest possible prior art
   for this study, because it fixes the defect family the register calls
   `absent-document-as-clean` in the very file this run must change.
   `plugin_marketplace_surfaces` now tests the nested-checkout condition
   against a repository-relative path rather than absolute parts, because a
   clone living under `.claude/worktrees/` carried that name in every absolute
   path it contained, so the enumeration returned nothing, the consuming loop
   ran zero times, and its assertions passed while checking nothing. The fix
   adds `self.assertTrue(surfaces, plugin_root)` and a `SurfaceEnumerationTests`
   class that proves the sweep is not vacuous. Carry forward both moves
   verbatim: this run's front-door and maintained-surface checkers must assert
   that their own sweep found something, and must prove it under a clone whose
   path contains a skipped name.
2. [PR #1113](https://github.com/wildcat-finance/skills/pull/1113), "Dokimasia:
   draft a disposition set a reviewer edits, and count only what a person
   confirmed", merged `27b555e0` at 2026-09-01T23:27:41Z. It moved Dokimasia to
   `dokimasia-v2.1.0`, added the `propose` verb, `ADR-002`, a fifth schema, and
   a committed disposition set, and moved the pinned scrutiny's closure ratio
   from 0 to 202 over 261. It is why this study's Dokimasia card carries
   different numbers from the run before it. Carry forward the numbers as
   measured; refuse any temptation to describe 202 confirmations as coverage,
   because `covered` is still zero by design.

The two earlier pull requests that changed this subject were read by the first
run and are carried without re-derivation. [PR
#1060](https://github.com/wildcat-finance/skills/pull/1060), merged
`67a01a6cddd508541c5dab5012caa72fe6e9293b`, added the eighteenth plugin, both
marketplace rows, the roster entry, a `What is not built yet?` entry, and the
hand-bumped literals analysed above; its own design record, shipping 18
selection reports beside it, is the closest prior art for this study's Section
4. [PR #1044](https://github.com/wildcat-finance/skills/pull/1044), merged
`88f5684d`, with [PR
#1043](https://github.com/wildcat-finance/skills/pull/1043) before it, moved
Homologia to `homologia-v1.1.0` and rewrote its README entry, which is still
the longest in the roster at 77 words against a median of 17. Carry forward the
discipline of shipping reports beside a record and the accurate frontier text;
refuse the hand-maintained literals, the now-stale `What is not built yet?`
entry, and the unbudgeted roster paragraph.

The two pull requests that created the front-door defect were read by the first
run and are not re-derived here. [PR
#1003](https://github.com/wildcat-finance/skills/pull/1003), merged
`1c113789`, rewrote the whole maintained public surface and placed contribution
after the complete roster. [PR
#1037](https://github.com/wildcat-finance/skills/pull/1037), merged
`42ac62a0`, inserted the Anamnesis portrait into the root README as well as its
member page. Both are ancestors of the starting ref. Carry forward the intended
progressive disclosure and the sourced member portrait; refuse the duplicated
catalogue, the buried invitation, the length, and the uncontextualised root
image.

### In-scope audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exited 0 at the starting ref: every source and synopsis digest in the
repository is current, so the modern round records below were read through
their verified synopses. The legacy Shoggoth contributor-guide section was read
directly from `audit/AUDIT.md:7832` because its root synopsis flags missing
legacy fields and omits the finding records; those missing legacy fields stay
unknown.

Three records are new since the first study and all three carry obligations
this run inherits.

- **Dokimasia frontend coverage skill,
  `audit/rounds/fiat-dokimasia-frontend-coverage-skill.synopsis.md`, synopsis
  read.** Five steps, 20 rounds, every step ending `null`: step 1
  `passed/null`, step 2 `guarded/null`, steps 3 and 4 each four `guarded`
  rounds then `null`, step 5 five `guarded` rounds then `null`. Findings
  `S1-R1-01`, `S2-R1-01`, `S2-R1-02`, `S3-R1-01` through
  `S3-R1-03`, `S3-R2-01` through `S3-R2-03`, `S3-R3-01`, `S3-R4-01`,
  `S4-R1-01` through `S4-R1-04`, `S4-R2-01`, `S4-R3-01`, `S4-R4-01`,
  `S4-R4-02`, `S5-R1-01`, `S5-R1-02`, `S5-R2-01`, `S5-R2-02`, `S5-R3-01`,
  `S5-R4-01` and `S5-R5-01` are recorded. Six of them name failure modes this
  run can reproduce and must guard against by construction:
  - `S1-R1-01` (low, accepted and mitigated in `1de8557c` rather than fixed)
    is the one this study answers directly. All 18 committed selection
    reports record their `command` as
    `python3 .hexaemeron/design/build_design_evidence.py`, a path that resolves
    only inside the controller's own gitignored run directory, so a reader who
    clones the repository cannot run the command the evidence names. The
    committed generator is at
    `plugins/dokimasia/docs/design/build_design_evidence.py`. The record was
    immutable after `done study`, so the field could not be corrected. Section
    4 of this study takes that finding as a requirement rather than a warning,
    and names a path the delivered branch will actually carry rather than
    documenting the discrepancy beside it.
  - `S4-R1-01` (high): a reviewed-oracle check compared a status against the
    unreviewed value and nothing else, so a workbook with no status column
    passed every oracle, because absence never equals a value. A demonstration
    record with no `status` field must not pass as `real-data` for the same
    reason.
  - `S5-R4-01` (high): four committed schemas each declared that an unknown key
    is a refusal, and nothing checked any of it; the `--check` verbs asserted
    behaviour rather than shape. The demonstration record contract must be
    validated as a shape, not only exercised.
  - `S5-R2-02` (medium): `--label` became a file name under the declared
    evidence root with no check on its shape, and `--label
    ../../../../tmp/pwned` wrote outside that root. The demonstration runner
    takes a caller-supplied report path and inherits this exactly.
  - `S3-R4-01` (medium): five refusals were added to a reader while the
    `Refuses` clause that declares them was left naming nine of fourteen. Code
    stricter than its contract still counts as drift. `DEMONSTRATIONS.md` and
    the runner must move together.
  - `S5-R5-01` (low): three commits shipped a stale `.horos/boundary.json`
    because the scan output was piped to `/dev/null` and its success taken on
    trust. Read the Horos output.
- **Anamnesis corpus projection into Synkrisis,
  `audit/rounds/fiat-admit-the-anamnesis-corpus-projection-into-a-syn.synopsis.md`,
  synopsis read.** Three steps; verdicts `guarded/guarded/null`,
  `guarded/null`, `guarded/null`. Findings `S1-R1-01`, `S1-R2-01`, `S2-R1-01`,
  `S2-R1-02` and `S3-R1-01` were fixed. Three obligations transfer:
  - `S1-R1-01` (low): five discipline citations were written as
    `../<skill>/SKILL.md`, which resolve from the Protasis skill directory the
    style was copied out of and from neither location the study actually
    occupies; Hypomnema exited 1 with five H001 findings on the committed copy,
    and the receipted study was immutable. This study therefore cites
    discipline contracts as plain backticked repository paths from the root
    rather than as relative Markdown links, so no H001 can arise wherever the
    committed copy is sited.
  - `S1-R2-01` (medium): extending the admitted step range made steps
    reachable before their test files existed, and `wasSuccessful()` is true
    for an empty suite, so the runner exited 0 and published a report reading
    complete `true`, `testsRun` 0. A public demo run that selects zero records
    must fail, not pass.
  - `S3-R1-01` (medium): a prose sweep named three live documents and skipped
    any that was absent, so renaming one would drop it silently. The front-door
    checker sweeps a fixed document set and must assert on absence.
  - Its final round recorded 1,110 root tests green alongside 194 Anamnesis and
    118 Synkrisis tests, with the phylax, ephoros and hypomnema lints each
    exiting 0.
- **Dokimasia proposed dispositions,
  `audit/rounds/fiat-dokimasia-proposed-dispositions.synopsis.md`, synopsis
  read.** Four steps, 8 rounds, every step running `guarded` then `null`.
  Findings `S1-R1-01`, `S1-R1-02`, `S2-R1-01`, `S3-R1-01`, `S3-R1-02` and
  `S4-R1-01` were fixed. Two of them bear directly on this run:
  - `S1-R1-02` (low) is the second occurrence of the defect this study already
    carries as `design-command-unreachable`, and it sharpens it. Every
    selection report recorded `command` as the bare generator path, and the
    generator's own `--record` default pointed at
    `.hexaemeron/design-evidence.json`, the controller's gitignored state
    directory, so a reader running exactly the command the evidence names would
    write a record somewhere other than the artefact the evidence describes. It
    is not enough for the committed generator to sit at a path a cloner can
    reach: it must also refuse to default its output into the run directory.
    Section 4 and the register both take that stronger form.
  - `S4-R1-01` (medium) found committed evidence recording `generated_by:
    1.1.0` when the draft predated the ledger move and that version had no
    `propose` verb. Provenance that is merely stale reads the same as
    provenance that is wrong. Every demonstration record this run authors names
    the skill version that actually produced its result.
  - Its negative space is worth carrying too: whether the 202 confirmations are
    correct judgements about `wildcat-app-v2` is the reviewer's claim and
    nothing in the record establishes it, and the 59 compiled items carry
    drafted exclusions nobody has decided on, so they are undecided rather than
    out of scope. The public card must say that and not round it up.

The records the first study read remain in scope and their dispositions are
unchanged. The **Shoggoth contributor guide**
(`audit/AUDIT.md:7832-7995`) preserves two obligations here. External
contributors keep their own authorship, and regenerated public images and PDFs
receive a committed-tree Horos scan plus rendered visual inspection. **Primer
removal** (`fiat-975-...`) explicitly did not check the product choice to remove
the primer or the rendered appearance of the resulting README; this run does not
restore the child or golden-retriever framing, fills the admitted entry gap with
a direct adult explanation, and adds rendered review. **Large generated prose
packet** (`fiat-972-...`) found nothing and established that a missing generated
runtime is current topology. **Skills-runtime siting and move** (`fiat-940-...`
and `fiat-949-...`) leave `S3-R1-02` to issue
[#971](https://github.com/wildcat-finance/skills/issues/971); the public install
link stays `wildcat-finance/skills-runtime` and #971 is the named carryover this
run does not solve. **Anamnesis seed**
(`fiat-anamnesis-source-bound-curation-and-release-of-a`) did not establish
source lawfulness or the truth of the selected 41 findings; the root card
repeats the demo's non-claim. **Lazarus Goldfinch receipt proof**
(`fiat-383-...`, 33 rounds) closed `S1-R1-01` by narrowing transaction hashes to
recorded RPC metadata and did not check a new live capture, canonical-chain
identity, or provider independence; the root card repeats that boundary.
**Alexandria and Probitas joined demo** (`fiat-391-...`) leaves open leads on
coverage-field length ceilings, the loader's coverage-list shape check, an index
venue unknown to the registry being dropped, and a thin Alexandria evolution
citation; the public card claims no complete venue or source coverage.

### Organisation prior art

The public Shoggoth Wave Atlas demonstrates useful provenance fields: a selected
source mode, source revision, build revision, and generated time. It selects
open issue work; it does not prove that a skill has a real-data demo. The
existing `held-job` label and `{skill}-next` issues are behaviour-frontier work
and stay authoritative for that lane. A demo lane should borrow the explicit
revision and evidence shape without pretending the Atlas already governs
demonstration status.

The repository's own strongest precedent is `plugins/dokimasia/docs/`: a
committed `design-evidence.json`, a `reports/selection/` directory beside it,
and a `docs/design/build_design_evidence.py` that regenerates both so the record
can be compared byte for byte. That is the shape Section 4 adopts, with the
`command` defect its audit found already corrected.

### Outside prior art

- GitHub's "About READMEs" documentation says a repository README should tell
  readers why the work is useful, what they can do with it, and how to begin;
  only start-here material belongs there, with longer documentation elsewhere.
- Diátaxis separates tutorials, how-to guides, reference and explanation, and
  recommends a short orientation that links into the mode a reader needs. That
  supports moving the full roster, install matrix and Promise Machine
  explanation behind the front door rather than deleting them.
- NISO RP-31-2021 supplies a vocabulary for distinguishing available,
  functional and reproduced research artefacts. The Systems Research Artifacts
  guidance similarly expects exact automated workflows and separates "it runs"
  from "it reproduces a result". Neither taxonomy maps perfectly to these
  skills, but both reject one vague `demo` label. The Shoggoth status set keeps
  the source-specific distinction explicit: `real-data`, `mixed`,
  `constructed`, `absent`, or `not-applicable` with a reason.

## 3. Constraints and non-goals

### Constraints

- Start from exact ref `66b6cfd6b20610484321abcb85079a0dce1b6070` on `main`.
- Use the exact CPython `3.14.6` named by `.python-version` and the standard
  checked runner. Do not substitute an ambient interpreter.
- **No check may compare a live-tree count against a literal.** Step 1's test
  asserts agreement between independent sources: both marketplace manifests,
  discovery over the plugin tree's `EVOLUTION.md` files, and the counts written
  into public prose must all return the same number. It also asserts the
  structural invariants that do not move: one canonical entry skill per
  plugin, phase skills only inside Hexaemeron, no duplicate id, no governed
  directory without a regular `SKILL.md`, no symlinked skill-tree entry, and no
  fixture tree counted as a real skill. A new plugin landing mid-run must
  change a derived number and nothing else.
- **Synthetic fixtures stay pinned to exact counts.** A frozen specimen exists
  to exercise the parser, so it keeps literal expectations. It must use its own
  arbitrary plugin and skill ids, and no assertion may compare a specimen
  identity set with a live identity set. Pinned-specimen and derived-live only
  compose if they are kept apart.
- Preserve the Promise Machine `promise-machine/v1` evidence boundary and every
  plugin's `AGENTS.md` ownership boundary.
- Preserve the external-human contribution rule: the contributor remains "not
  Shoggoth", keeps their own Git author, signing identity and GitHub account,
  and does not receive private Shoggoth credentials.
- Preserve `wildcat-finance/skills-runtime` as the portable installation
  source. Build and test generated packages in disposable directories; do not
  commit `.agents/skills/promise-machine/runtime/`.
- Preserve all existing `EVOLUTION.md` frontier lines and digests unless this
  run actually completes that exact behaviour frontier. The demonstration lane
  is additive and independently versioned.
- Preserve historical audits, studies, runbooks, ADR bodies, specimens and
  content-addressed releases. Public corrections describe current truth; they
  do not rewrite old evidence. `INSTALL.md`'s thirteen and fourteen plugin
  figures are historical and stay.
- Keep every root claim weaker than or equal to its selected demonstration
  record. A successful runner cannot strengthen source completeness, chain
  finality, finding truth, remedy correctness, protocol safety, coverage
  adequacy, or underwriting merit.
- Treat demonstration manifests, sources, subprocess arguments and output paths
  as untrusted. Execute argv arrays without a shell, deny network by default,
  bound bytes, time and output, and write reports atomically below an
  operator-selected directory whose containment is checked after path
  resolution.
- The new public-heading style is checked only over the maintained surface in
  assumption 2. It must not churn operational contracts and history to satisfy
  an aesthetic rule.
- Public images and both contributor PDFs remain Horos-classified binary
  assets. Regenerate and visually inspect every PDF page after source prose
  changes, and read the Horos scan output rather than its exit alone.
- This run ships no Solidity. The security suite is waived on the ledger; every
  audit round runs the phylax, ephoros and hypomnema lints instead. The waiver
  removes a target, not a boundary: Section 9 still applies.
- There is no task issue. Do not invent one, do not file one, and do not claim
  a carryover contract that was never read.

### Non-goals

- Do not implement or extend Dokimasia. Describe what it ships and stop.
- Do not make every governed skill real-data-ready in this prototype. Classify
  all 27 honestly, prove the four, and leave an explicit demo frontier.
- Do not turn a demo into a certification, security badge, maturity score,
  coverage guarantee, or protocol recommendation.
- Do not replace the current behaviour frontier, Wave Atlas, Promise Machine or
  Fiat controller with the demonstration lane.
- Do not automatically open, close or publish GitHub issues in any checker.
  Queue changes and issue filing remain explicit, reviewed actions.
- Do not solve issue #971, the Lazarus provider and canonical-chain limits, the
  Alexandria coverage leads, Berean's held Wildcat release, Synkrisis's held
  production cohort, or Dokimasia's `proposed-dispositions` frontier.
- Do not restore the deleted child or golden-retriever primer, its assets, or
  its patronising register.
- Do not flatten the technical documents into a second short README. The path
  is easy first and technical later, not easy only.
- Do not hand-edit generated portable copies or historical package bytes.
- Do not reopen or rebase the first run's pull requests #1077 and #1078. This
  run supersedes them; the controller decides their disposal.

## 4. Design options

The closed selection record is `.hexaemeron/design-evidence.json`, SHA-256
`e66cd1c56570e629cac254dd4ae74817c0d01496a77f75bb35cb1efd7e5d8407`. It carries
4 candidates, 9 criteria and 36 results: 24 resolved selection cells, each
asserted by a named report under `.hexaemeron/reports/`, and 12 pending
conformance cells. `python3
plugins/hexaemeron/skills/protasis/scripts/design_evidence.py
.hexaemeron/design-evidence.json --transition design-lock` exits 0.

The six selection criteria mean:

- `complete-ledger-coverage`: every discovered governed skill has an explicit
  demonstration state.
- `demo-state-is-discovered`: the demonstration state of a newly landed
  governed skill is found by walking the plugin tree, with no central inventory
  a person must edit. This is the criterion the first run did not have, and it
  is the one that encodes why this run exists.
- `update-owner-hops`: independent ownership locations a maintainer must edit
  to advance one skill's demonstration.
- `global-registry-files`: central inventory files whose merge surface grows
  with every skill.
- `preserves-evolution-digests`: the construction adds no field to the
  existing `EVOLUTION.md` frontier grammar.
- `stale-claim-blocked`: a public real-data card cannot pass when its record
  is absent, downgraded, or fails verification.

The matrix the reports assert, in the order `complete-ledger-coverage`,
`demo-state-is-discovered`, `update-owner-hops`, `global-registry-files`,
`preserves-evolution-digests`, `stale-claim-blocked`:

```design-properties
editorial-only | false | false | 0 | 0 | true | false
central-registry | true | false | 2 | 1 | true | true
evolution-embedded | true | true | 1 | 0 | false | true
per-skill-demo-ledger | true | true | 1 | 0 | true | true
```

Three candidates fail a hard gate. One survives, so `unique-frontier` selects
it without needing the comparative metrics; the metrics stay in the record
because the trade they measure is real and a later reader is entitled to see
it.

Each of the 24 reports records its `command` as `python3
docs/design/build_shoggoth_front_door_design_evidence.py`. **That file does not
exist at the starting ref.** Step 1 owes it, at exactly that path, and step 1's
exit is that running it regenerates `.hexaemeron/design-evidence.json` and all
24 reports byte for byte. It requires an explicit output directory and
defaults to none, because the second occurrence of this defect,
`S1-R1-02` in the proposed-dispositions record, was a generator that resolved
for a cloner and still defaulted its output into the gitignored run directory.
The serialisation is fixed so the reproduction is achievable: UTF-8,
ASCII-only, `json.dumps` with `indent=2` and `sort_keys=True`, one trailing
newline. This is the direct answer to Dokimasia
finding `S1-R1-01`: a cloner could never reach
`.hexaemeron/design/build_design_evidence.py`, because `.hexaemeron/` is
ignored, whereas a cloner of the delivered branch can run
`docs/design/build_shoggoth_front_door_design_evidence.py`. The record is
immutable after `done study`, so the obligation is stated here and enforced by
step 1 rather than repaired later; risk `design-command-unreachable` tracks it.

The three conformance criteria are pending with exact resolvers:
`derived-count-agreement` blocks `step:2` and resolves with `python3 -m unittest
tests.test_shoggoth_topology`; `public-demo-set-runs` blocks `step:4` and
resolves with `python3 scripts/demonstrations.py run --public-set --report
.hexaemeron/reports/public-set.json`; `front-door-contract-met` blocks `step:5`
and resolves with `python3 scripts/check_public_front_door.py --root .`.

### Candidate: editorial-only

Rewrite the public prose, derive its counts, link the four current commands,
and rely on ordinary frontier prose to keep them current. Smallest
implementation, no new format, zero new owner hops and zero registry files. It
has no demonstration state at all, so nothing can be discovered and nothing can
refuse when a source, command, classification or public card drifts. It fails
`complete-ledger-coverage`, `demo-state-is-discovered` and
`stale-claim-blocked`. It would produce the same kind of ungoverned rewrite
that created the current problem: commit `67a01a6c` is what editorial-only
looks like after one merge.

### Candidate: central-registry

Put one suite-level registry under the repository root with an entry for every
governed skill, and make the root README and the runner consume it. It gives
complete coverage and fail-closed public claims while leaving evolution digests
alone. It fails `demo-state-is-discovered`: a newly landed skill is absent from
the registry until a person edits it, which is the precise defect this run
exists to remove, and a registry that must be regenerated is a cache
masquerading as a source. It also loses both comparative measures: two owner
hops against one, and one central merge hotspot against none.

### Candidate: evolution-embedded

Add demonstration status, source, commands and a demo frontier directly to
every `EVOLUTION.md`. The facts stay beside the owning skill, discovery finds
them, and it costs one owner hop and no registry file. The existing versioning
grammar hashes the current frontier and is consumed by Kronos, the marketplace
tests, issue review and Fiat version resolution. Adding a second frontier to
that record changes the meaning and digest of all 27 established behaviour
lanes. It fails `preserves-evolution-digests`.

### Candidate: per-skill-demo-ledger, selected

Add `DEMONSTRATION.md` beside each governed `EVOLUTION.md`. Each file carries a
human ledger plus one fenced, strict `shoggoth-demonstration/v1` object. The
object names the skill, status, source class and identity, source digests or
chain anchor, network policy, argv arrays, expected observations, public claim
id, non-claim, and per-command timeout. The ledger independently carries
demonstration version, frontier status and revision, current demonstration,
next demonstration job, and history digest.

A suite checker discovers the same governed skill directories the evolution
tests discover and requires exactly one record per directory. A runner opens
only the selected record, rejects symlinks and non-regular sources, executes
argv without a shell in a private temporary root, denies sockets unless the
record's capture phase explicitly allows a named endpoint, and emits a closed
report. `check-public` requires each root demo marker to bind a record digest
whose current status is `real-data`; it never grades free-form voice.

Discovery is the registry, so a plugin landing mid-run adds one file in its own
directory and changes one derived number. One skill owner advances one
demonstration ledger. Existing `EVOLUTION.md` bytes and Kronos behaviour
ranking are untouched. A new explicit demo-lane operation reads only
demonstration ledgers; a behaviour job may co-deliver a demo by satisfying both
independent records.

The record uses these closed status meanings:

- `real-data`: every material input is a preserved real-world source and the
  registered offline path reproduces the named result;
- `mixed`: at least one real-world source is present, but a constructed or
  target-mismatched component is material to the result;
- `constructed`: the whole executable example is built from fixtures or model
  records created for the example;
- `absent`: no complete executable demonstration exists; and
- `not-applicable`: the owner gives a checked reason why a real-world input
  would not make sense for that skill. This is not a synonym for unfinished.

Dokimasia is classified `real-data` on the evidence in Section 2: its
demonstration reproduces offline from preserved records derived from a real
application checkout at a named commit and a real reviewed workbook at a named
digest, which is the same shape as Lazarus reproducing from a preserved chain
capture rather than from the chain. The caveat that could demote it is that the
repository cannot re-derive the inventory record from the application checkout,
because that checkout is not here. If Warden or the record's owner judges that
material, the status becomes `mixed`, the checker removes the card, and the
front door shows three. Risk `dokimasia-source-class` carries that decision.

The root README is hand-written for voice. It contains one hidden marker per
demo card binding the skill id, claim id and demonstration-record digest. The
checker owns structural truth for status, source, command, result, non-claim
and link uniqueness. Imprimatur, Vulgate, Brevitas, rendered review and human
audit own the prose. Generated text is not allowed to sand the Shoggoth back
into generic product copy.

## 5. Risk register seed

```risk-register
claim-without-demo | root capability cards against per-skill demonstration records | a missing, stale, mixed, constructed, or failing record blocks a real-data public claim
demo-class-inflation | status assigned to preserved or constructed inputs | every material input has a source class and a mixed component prevents real-data status
dokimasia-source-class | the Dokimasia scrutiny's preserved records against the absent application checkout and workbook | the owner records which inputs are material, and a material absent input demotes the record to mixed and removes the card
source-drift | preserved chain, audit, repository, application, and lending inputs | declared byte digests or chain anchors are checked before a command runs
frontier-lane-collision | EVOLUTION.md behaviour state beside DEMONSTRATION.md state | advancing either lane leaves the other digest and held job unchanged unless both accept the same evidence
count-literal-reintroduction | every check that reads a live-tree count | no assertion compares a live count with a literal, and a probe that adds a plugin to a scratch tree changes exactly the derived numbers
specimen-live-coupling | pinned synthetic fixtures against discovered live identity | the specimen uses its own arbitrary ids and no assertion compares a specimen identity set with a live one
fixture-tree-miscount | discovery walk against test fixtures carrying SKILL.md and EVOLUTION.md | discovery is anchored at plugins/<id>/skills and a check proves the hypomnema design-bridge fixture is excluded
generated-copy-drift | source prose against the separately published skills-runtime package | a disposable package rebuild and package tests replace hand edits to the ignored runtime
external-data-egress | demos that could reach RPC, HTTP, models, or credentials | network is denied by default and any capture exception names an allowlisted endpoint and secret environment without recording its value
subprocess-execution | argv loaded from a demonstration record | strict argv arrays run without a shell under timeout and bounded output in a private execution root
report-path-escape | caller-supplied report and label paths under the declared output root | containment is checked after resolution, refusing traversal, symlinks, and existing targets
empty-selection-as-pass | a public demo run that selects no record | a run with zero selected demonstrations exits nonzero rather than reporting a clean empty suite
schema-declared-not-checked | the shoggoth-demonstration/v1 and report schemas | a committed schema is validated as a shape, with an unknown key refused, not merely exercised by behaviour tests
contract-refusal-drift | DEMONSTRATIONS.md refusal clause against the runner's enforced refusals | the clause and the code change in the same commit and a test counts both
partial-demo-output | demonstration build and report destinations | existing outputs are refused and new outputs stage privately then publish atomically or remain visibly incomplete
front-door-regression | root order, length, links, headings, and catalogue boundary | a dedicated checker guards the 150-word intro, 220-word contribution position, 1400-word file, unique link targets, and one technical catalogue
absent-document-as-clean | the fixed maintained-surface document set the checker sweeps | a named document that is absent fails the sweep, every sweep asserts it found something, and a case proves the enumeration is not vacuous under a clone whose path contains a skipped directory name
stale-member-status | public not-built-yet prose against each skill's own ledger | a member described as unshipped is checked against its EVOLUTION.md current version and frontier
portrait-inconsistency | collective root imagery against member landing portraits | root admits only collective art while member portraits remain on contextual member pages
historical-record-rewrite | current prose corrections beside audits, ADRs, fixtures, INSTALL.md history, and old runbooks | checks constrain edits to mutable current claims and preserve digest-bound, append-only, or explicitly historical text
design-command-unreachable | the command field in every committed selection report | step 1 commits docs/design/build_shoggoth_front_door_design_evidence.py, requires an explicit output directory with no default into the run directory, and proves it regenerates the record and all 24 reports byte for byte
demo-skip-as-pass | optional dependency or missing specimen during public demo execution | a registered public demo missing its command, source, or dependency fails rather than skips
real-data-nonclaim-loss | concise root cards derived from detailed demo boundaries | each card binds and displays the record's non-claim before public checks pass
stale-record-provenance | the skill version each demonstration record names against the version that produced its result | a record naming a version whose verbs could not have produced the recorded observation is refused
queue-duplication | demo frontier issue against an existing behaviour frontier issue | the ledger points to one canonical issue and reuses it when both acceptance sets can be satisfied by one run
visual-surface-drift | Markdown and both regenerated PDFs after mechanical heading and layout changes | rendered root and every PDF page are inspected for hierarchy, overflow, anomalous images, and broken links
horos-boundary-staleness | the committed reading boundary after files are added | the Horos scan output is read rather than discarded, and the committed boundary matches the tree it describes
```

Warden must enumerate every id. A concern can be not applicable only with a
candidate-specific reason; "docs only" does not dispose of the demo runner, the
generated package, the queue, or the binary PDF boundaries, and the recorded
Solidity waiver disposes of none of them.

## 6. Glossary seeds

**Front door.** The bounded root README that explains, invites, demonstrates
and then links deeper; it is not the complete catalogue.

**Maintained public surface.** The explicit current source documents and PDFs
listed in assumption 2, excluding historical and agent-operational records.

**Governed skill.** A first-party skill directory carrying both `SKILL.md` and
`EVOLUTION.md`; discovery finds 27 at the starting ref.

**Canonical or domain agent.** The one canonical entry skill for each shipped
plugin, with Fiat as Hexaemeron's entry; discovery finds 18.

**Phase agent.** One of the nine additional governed Hexaemeron disciplines,
not an extra plugin.

**Derived count.** A number produced by walking the tree at check time. Its
correctness is agreement between independent sources, never equality with a
written figure.

**Pinned specimen.** A synthetic fixture whose counts are literal on purpose,
because its job is exercising the parser. It carries its own arbitrary ids and
is never compared with live identity.

**Real-data demonstration.** An executable, source-bound, reproducible path
whose material inputs came from a real chain, protocol, repository, audit,
application, or production run.

**Mixed demonstration.** An executable path in which real data and a material
constructed or target-mismatched input coexist.

**Demonstration ledger.** One skill-owned `DEMONSTRATION.md` containing the
current evidence record and its independent demo frontier and history.

**Behaviour frontier.** The existing `EVOLUTION.md` held job that changes what
a skill can do.

**Demo frontier.** The independent held job that improves what a skill can show
over real data without pretending its behaviour changed.

**Co-delivery.** One Fiat run satisfying both a behaviour frontier and a demo
frontier while each ledger verifies and advances independently.

**Public demo set.** The small set of `real-data` records named by root
capability cards and run by the joined proving command; four at the starting
ref.

**Claim id.** A stable identifier joining one hand-written public card to the
bounded claim and non-claim in its demonstration record.

**Closure ratio.** Dokimasia's statement that nothing scoped is unaccounted
for. It never states that anything passed, and a public card may not translate
it into coverage.

## 7. Sources

Repository and history, all at `66b6cfd6b20610484321abcb85079a0dce1b6070`
unless a ref is given:

- `README.md`, especially lines 18, 21, 23, 89, 94-96, 117, 152, 179, 247, 261,
  295 and 317-319.
- `git show daa64e5f^:README.md`, especially the line-40 contribution heading
  and its three-sentence Atlas opening.
- `tests/test_marketplace_prose.py`, especially the `discovered_plugins`
  docstring, line 187's pinned README literal, and line 300's
  `assertEqual(len(governed), 27)`.
- `git log -S "assertEqual(len(governed), 27)" -- tests/test_marketplace_prose.py`,
  returning `67a01a6c`, and `git show 67a01a6c -- README.md`.
- `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, and
  all 27 governed `plugins/*/skills/**/EVOLUTION.md` files.
- `plugins/hexaemeron/tests/fixtures/hypomnema/design-bridge/plugins/example/skills/example/`,
  the fixture that a widened discovery walk would miscount.
- `plugins/hexaemeron/skills/VERSIONING.md`, especially "What every frontier
  run owes", and `plugins/hexaemeron/skills/kronos/SKILL.md`.
- `plugins/hexaemeron/skills/protasis/scripts/design_evidence.py`, for the
  closed record contract, the `unique-frontier` rule, and the report key set.
- `SHOGGOTH.md:20`, `INSTALL.md:214-215` and `:242`,
  `docs/how-to-help-shoggoth.md:5`,
  `docs/the-promise-machine-explained-properly.md:157`, and
  `.agents/skills/promise-machine/SKILL.md:18` and `:29`.
- `tests/check-map-v1.json`, whose 28 checks are what `scripts/run_checks.py
  --full` executes.
- `.gitignore`, `distribution/skills-runtime/sync.yml`,
  `scripts/portable_promise_machine.py` and `tests/test_skills_sh_package.py`.
- `plugins/anamnesis/README.md:106-107`, `plugins/anamnesis/docs/demo.md`, and
  `plugins/anamnesis/skills/anamnesis/EVOLUTION.md`.
- `plugins/lazarus/examples/goldfinch-v1/demo.py`,
  `plugins/lazarus/docs/macos-path-repair-study.md`, and the v1 fixture and
  release.
- `plugins/alexandria/examples/credit-history-v0/README.md` and its `demo.py`.
- `plugins/dokimasia/skills/dokimasia/EVOLUTION.md`,
  `plugins/dokimasia/scripts/dokimasia.py`,
  `plugins/dokimasia/docs/evidence/wildcat-app-v2.scrutiny.json`,
  `plugins/dokimasia/docs/design-evidence.json`,
  `plugins/dokimasia/docs/design/build_design_evidence.py`, and one selection
  report under `plugins/dokimasia/docs/reports/selection/`.
- `plugins/berean/skills/berean/EVOLUTION.md`,
  `plugins/synkrisis/skills/synkrisis/EVOLUTION.md`, and open issues
  [#411](https://github.com/wildcat-finance/skills/issues/411) and
  [#398](https://github.com/wildcat-finance/skills/issues/398).

The first run's preserved artefacts, read in full:

- `front-door-run-1/study.md`, `runbook.md` including all three amendments,
  `design-evidence.json`, `state.json` and `ledger.jsonl` in the operator's
  archive.
- `origin/fiat/restore-the-shoggoth-public-front-door-and-demo-step-1-commit-the-design-boundary-and-s`
  at `34f6b8ab`, and
  `origin/fiat/restore-the-shoggoth-public-front-door-and-demo-step-2-govern-one-demonstration-ledger`
  at `d06e63c9`, specifically `scripts/shoggoth_topology.py`,
  `tests/test_shoggoth_topology.py:120-200` and
  `tests/fixtures/shoggoth-topology/valid-17-26.json`.

Pull requests and issues:

- [PR #1115](https://github.com/wildcat-finance/skills/pull/1115) and
  [PR #1113](https://github.com/wildcat-finance/skills/pull/1113), the two most
  recent merges that changed this subject.
- [PR #1060](https://github.com/wildcat-finance/skills/pull/1060) and
  [PR #1044](https://github.com/wildcat-finance/skills/pull/1044), with
  [PR #1043](https://github.com/wildcat-finance/skills/pull/1043).
- [PR #1003](https://github.com/wildcat-finance/skills/pull/1003) and
  [PR #1037](https://github.com/wildcat-finance/skills/pull/1037), the two that
  created the defect.
- [PR #1049](https://github.com/wildcat-finance/skills/pull/1049), merged
  `20ba7691` at 2026-08-31T18:26:36Z, closing issue #881.
- [PR #1077](https://github.com/wildcat-finance/skills/pull/1077) and
  [PR #1078](https://github.com/wildcat-finance/skills/pull/1078), both open.
- [Issue #971](https://github.com/wildcat-finance/skills/issues/971), retained
  as a separate framework carryover this run does not solve.

Audit evidence, with the reading choice recorded in Section 2:

- `audit/rounds/fiat-dokimasia-frontend-coverage-skill.md` and its verified
  synopsis.
- `audit/rounds/fiat-dokimasia-proposed-dispositions.md` and its verified
  synopsis.
- `audit/rounds/fiat-admit-the-anamnesis-corpus-projection-into-a-syn.md` and
  its verified synopsis.
- `audit/AUDIT.md:7832-7995`, the authoritative legacy contributor-guide source.
- `audit/rounds/fiat-975-remove-the-child-or-golden-retriever-primer.md`,
  `fiat-972-let-a-prose-phase-survive-a-large-generated.md`,
  `fiat-940-site-the-generated-skills-sh-payload.md`,
  `fiat-949-move-the-skills-sh-payload-to-its-own-reposi.md`,
  `fiat-anamnesis-source-bound-curation-and-release-of-a.md`,
  `fiat-383-prove-receipts-against-the-captured-header-s.md` and
  `fiat-391-unified-live-and-archive-collection.md`, each with its verified
  synopsis.
- `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`,
  exit 0.

Organisation and outside sources:

- `wildcat-finance/shoggoth-wave-atlas`, for source and build revision and
  selection provenance, not demo proof.
- GitHub Docs, "About READMEs":
  <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes>.
- Diátaxis, "Start here": <https://diataxis.fr/start-here/>.
- NISO RP-31-2021, "Reproducibility Badging and Definitions":
  <https://www.niso.org/publications/rp-31-2021-badging>.
- Systems Research Artifacts guidance:
  <https://sysartifacts.github.io/eurosys2026/call> and
  <https://sysartifacts.github.io/cais2026/badges>.

## 8. Signals, and the questions behind them

This has an unattended surface: CI public-demo execution and any explicitly
started demo-frontier ranking loop. The source contract is
`plugins/hexaemeron/skills/ephoros/SKILL.md`; the implementation cites it
rather than copying its event rules.

The on-call questions are:

1. Which skill, claim id, demonstration version, source digest or chain anchor,
   and repository revision did the runner select, and how many records did the
   selection return?
2. Did the run finish, time out, refuse before execution, or fail verification,
   and what exact rule and recovery action apply?
3. Did a root card bind a record whose status or digest changed since the card
   was written?
4. Did the run request network or credentials, and which declared boundary
   admitted or refused that request?
5. When a derived count moved, which independent source moved first: a
   manifest, the plugin tree, or public prose?

The checker step emits one bounded `demonstration.public_claim.checked` event
per card. The runner emits `demonstration.selected`, `started`, `verified` or
`refused`, sharing a correlation id and the fields above; `selected` carries
the record count, so a zero-selection run is visible as a refusal rather than
as silence. The topology check emits one
`shoggoth.topology.derived` event carrying each source's answer separately for
manifest, discovery and prose, so a disagreement names the mover. The frontier
selector emits the chosen lane, skill, revision, canonical issue, and whether
the job is demo-only or co-delivered. A no-eligible-job result is a normal
bounded event rather than a silent loop.

Duration and peak RSS are recorded as observations, never as success claims.
The runner never records source bytes, credential values, raw provider
responses, or unbounded stderr.

## 9. Boundaries, per capability

The source contract is `plugins/hexaemeron/skills/phylax/SKILL.md`. The
Solidity waiver on this run's ledger removes the Pashov targets; it removes no
off-chain boundary, and the demonstration runner starts subprocesses and sits
against the network boundary.

- **Public prose.** Worth taking: concise current claims and links. Control:
  cards bind claim ids and record digests; the checker owns structure while
  audit checks that free prose does not strengthen evidence.
- **Demonstration record parsing.** Worth taking: one closed, local,
  owner-specific record. Control: bounded regular-file reads, duplicate-key
  refusal, depth and byte caps, exact field sets validated against a committed
  schema with unknown keys refused, portable relative paths, and no symlink
  traversal. A record with no `status` is a refusal, because absence is not a
  value.
- **Preserved inputs.** Worth taking: exact audit, chain, repository,
  application, or protocol bytes. Control: source class plus SHA-256, or a
  chain, block and address anchor, verified before work; `real-data` refuses
  when a material input has no provenance.
- **Subprocesses.** Worth taking: fixed Python or repository commands named by
  the owner. Control: JSON argv arrays, no shell, pinned interpreter, private
  working root, minimal environment with credential and Git keys stripped,
  timeout, bounded stdout and stderr, and process-group teardown.
- **Network and credentials.** Worth taking only in a separately declared
  capture phase. Control: offline verification and public demo runs deny
  sockets by default; an admitted capture names the HTTPS endpoint class,
  chain, secret environment names, request ceilings, and redaction, without
  persisting secret values.
- **Filesystem output.** Worth taking: a disposable build and one report.
  Control: caller-selected confined report root with containment checked after
  path resolution, refusal of traversal in any label or name component,
  refusal of existing targets, no-follow component access, private staging,
  atomic publication, and a visibly incomplete stage after an unsafe cleanup
  refusal.
- **Topology discovery.** Worth taking: the plugin tree and both manifests.
  Control: anchored walk at `plugins/<id>/skills`, no-follow descriptor
  traversal, entry and depth caps, duplicate-id refusal, and manifest
  disagreement as a refusal rather than a tie-break.
- **GitHub queue.** Worth taking: a canonical issue URL after explicit filing.
  Control: every checker is read-only; queue creation follows the repository's
  issue-body, Sapheneia, Imprimatur, Vulgate and issue-check gates and reuses
  an existing behaviour issue when acceptance overlaps.
- **Generated package.** Worth taking: a disposable `skills-runtime` package
  built from source. Control: use the package command and package tests in a
  temporary directory; do not invoke the source-tree `check` against an absent
  runtime, and do not commit generated payload bytes here.
- **PDF and image assets.** Worth taking: the two existing contributor PDFs and
  contextual portraits. Control: deterministic regeneration where available,
  binary signature and link checks, a committed-tree Horos scan whose output is
  read, and visual render inspection; no new portrait is generated for this
  task.

## 10. The budget, or its absence

There is no claim that this change makes an existing skill faster, so there is
no before-and-after optimisation budget. The source contract is
`plugins/hexaemeron/skills/metron/SKILL.md`.

The content budgets are contract limits, not Metron performance claims: root
README at most 1,400 words against 2,713 today, intro at most 150 words,
contribution heading within 220 words against 2,028 today, no repeated link
target against 17 today, and no complete inline roster. They are measured by:

```bash
python3 scripts/check_public_front_door.py --root .
```

The public demo run does have an operator-time ceiling. All four registered
demonstrations must complete within an aggregate 600,000 milliseconds on the
pinned CI runner, and each record declares a tighter per-command timeout. The
measured aggregate at the starting ref on one Apple silicon machine was about
10.3 seconds: Anamnesis 0.19 s, Lazarus 7.87 s, Alexandria 1.12 s plus 0.75 s,
Dokimasia 0.38 s. The same four measured about 3.9 seconds on the same machine
one run earlier against an almost identical tree, which is the clearest
available evidence that these are observations and not a budget. A single
observation bounds nothing about the
hosted runner; the ceiling exists to catch a demo that hangs, not to assert
this figure. The runner records a three-repetition baseline without claiming an
improvement:

```bash
python3 scripts/demonstrations.py run --public-set --repeat 3 \
  --report .hexaemeron/reports/public-set-budget.json
```

The report records interpreter, platform, record and source digests, each
repetition, slowest duration, peak RSS, timeout and exit. Per-skill durations
and RSS stay baselines with no skill-level threshold; the ten-minute ceiling
belongs only to the front-door demo set.

## 11. The fail-closed posture

The source contract is `plugins/hexaemeron/skills/elenchus/SKILL.md`.

Integration stops on a missing or duplicate demonstration ledger; an unknown
status, an absent status, or an unknown field; an unsafe path or argv; a source
digest or anchor mismatch; an unexpected network request; a nonzero command; a
timeout; an absent expected observation; a skipped public demo; a public marker
mismatch; a mixed or constructed demo presented as real; a public demo run that
selected zero records; a count disagreement between manifests, discovery and
prose; any surviving 16, 25 or 26 topology claim; a repeated root link target;
a lowercase maintained heading; a contribution heading after the 220-word
boundary; a root Anamnesis portrait; a member described as unshipped whose
ledger says otherwise; an absent document in the maintained-surface sweep; a
committed schema that nothing validates; a `Refuses` clause that undercounts
the runner's refusals; a stale committed Horos boundary; a generated-package
failure; a broken link; or a failed visual or PDF review.

A refusal names the smallest failed relation and a recovery action. It does not
delete a prior good demo, downgrade an unrelated skill, advance either
frontier, or continue to another public card as though the public demo set
passed.

Every defect found during implementation gets a minimal bad specimen and a
guard that fails on the entry parent and passes on the fix. The initial
regression corpus is: the current stale count in each of the six documents that
carries one; a sentence-case maintained heading; a late contribution heading; a
duplicate link target; the root Anamnesis portrait; the Anamnesis stale
capability paragraph; the Dokimasia stale `What is not built yet?` entry; a
`mixed` record labelled `real-data`; a record with the `status` key removed; a
registered public demo missing its command that tries to skip; a public demo
set that resolves to zero records; a maintained-surface sweep that enumerates
nothing and passes; a shell-shaped argv string; a symlinked
source; a changed record digest; a report path containing `..`; a scratch tree
with a nineteenth plugin added, which must change exactly the derived numbers
and break nothing; and a specimen whose ids are deliberately unlike the live
ones, which must still pass.

Elenchus reports distinguish assertion failure from environment or dependency
failure. An inconclusive parent comparison does not become a guarded verdict by
wording, and a suite that ran zero tests is not a pass.

## 12. Decisions and their homes

The source contract is `plugins/hexaemeron/skills/hypomnema/SKILL.md`.

- The separate demonstration ledger, the status taxonomy, the independent
  frontier, the co-delivery rule, the `{skill}-demo` queue, and the explicit
  Kronos lane are expensive to reverse. Record them in
  `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` and
  put the normative current policy in
  `plugins/hexaemeron/skills/DEMONSTRATIONS.md`.
- The root README's front-door role, progressive order, word and link budgets,
  and single-catalogue boundary are durable public information architecture.
  Record them in
  `docs/decisions/ADR-069-keep-the-root-readme-as-a-front-door.md`.
- **Deriving topology counts instead of writing them down is the decision this
  run exists to make, and it is the most expensive one to reverse**, because
  every later check either inherits the discipline or quietly reintroduces a
  literal. Record it in
  `docs/decisions/ADR-070-derive-topology-counts-from-the-tree.md`, including
  the pinned-specimen exception, the rule that a specimen never shares identity
  with the live tree, and commit `67a01a6c` as the worked example of the
  failure it prevents.
- The design record and its 24 selection reports are regenerated by
  `docs/design/build_shoggoth_front_door_design_evidence.py`, committed by step
  1 at exactly that path. Its home is the repository, not the controller's run
  directory, because a reader who clones the repository must be able to run the
  command the evidence names.
- Current skill-specific demonstration facts and next jobs live in each
  governed `<skill-directory>/DEMONSTRATION.md`; behaviour facts and jobs
  remain in the adjacent `EVOLUTION.md`.
- The complete current technical catalogue lives in `FUTUREPROOFING.md` and is
  discovered and tested there once. `README.md` contains only the introduction,
  the contributor invitation, the checked demo set, a compact mechanism, the
  frontier link, an install pointer, the identity and authority boundary, the
  licence and the thanks.
- Root and member portrait placement remains governed by `SHOGGOTH.md`.
  Removing the root Anamnesis image while keeping the contextual member image
  does not earn a separate ADR.
- Dokimasia's identity, promises and boundaries are owned by
  `plugins/dokimasia/skills/dokimasia/SKILL.md` and its ADR-001. Public prose
  describes what that contract already says and adds nothing.
- Current testable facts belong in mutable public prose and checks. Historical
  pull-request bodies, audits, studies, runbooks, ADR histories, specimens, and
  `INSTALL.md`'s dated capture figures remain unchanged even where they record
  old counts or an old package topology.
