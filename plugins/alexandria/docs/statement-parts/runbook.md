# Statements past the 8 MiB limit runbook

The accepted study is `.hexaemeron/study.md`, SHA-256
`e2e78daa81ea9194968aa179abbab25dc04952395fdf39efd6f78e61e596d5e0`. This run
implements https://github.com/wildcat-finance/skills/issues/1892 on the run
branch `fiat/1892-statement-parts`, cut from `main` at
`150943da240837040478a76c3611d150fa04f2b6`, with Python 3.14.6 and the
standard library only. The controller is `fiat-v6.76.1`.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 071dcdb20c28a46fdd18933b4dcf31975d787b7c5581f2f092e5ecf00b3c2459
candidate | statement-parts
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/alexandria/tests/run_tests.py | report_target | 37c096a9f4a079c4c4c0b6cdad965f8a33ca4945fff1fd59802759e518eea4f2
```

```version-relations
alexandria | plugins/alexandria/skills/alexandria/EVOLUTION.md | next-generation-after-integration-base
```

## Rules every step keeps

**Scope.** The run adds the part form of a release statement and nothing
else. No file under `plugins/ariadne/` changes. No step edits
`plugins/alexandria/scripts/usdc_interval.py`, whose `build` and `check`
internals belong to #1891. #1888's release limits keep their values. The
security suite is waived because the run ships no Solidity.

**The Decision.** On 2026-09-30 Laurence chose option 1: `statement --output`
refuses by name a release whose single statement fits 8,388,608 bytes but
passes 262,144 key characters, and points to `--parts`. Step 3 edits the #1888
test `check_statement_beyond_the_old_limits` in
`plugins/alexandria/tests/test_release_limits.py` to match, and no other step
touches that file.

**Existing statements keep their bytes.** A release within both single bounds
takes today's `statement_for` path unchanged. The eleven statements in the
study's section 3 keep their SHA-256 at every step, and the byte refusal keeps
its exact text, `release statement encodes to N bytes, above Ariadne's
8388608-byte input limit`.

**The wire shapes.** Steps 2 and 3 implement the part, the index, the packing
rule, the part bound of 6,225,920 bytes and 262,144 key characters, and the
`--parts` command exactly as the study's section 4, "The selected wire
shapes", states them. The two predicate types are
`https://ariadne.wildcat.finance/alexandria-release-part/v1` and
`https://ariadne.wildcat.finance/alexandria-release-parts/v1`.

**Versions.** Every step changes `plugins/alexandria/`, so every step raises
Alexandria's package version in four places:

- `plugins/alexandria/.claude-plugin/plugin.json`;
- `plugins/alexandria/.codex-plugin/plugin.json`;
- the Alexandria entry in `.claude-plugin/marketplace.json`;
- the pin in `tests/test_version_propagation.py`.

`.agents/plugins/marketplace.json` carries no version. #1891 bumps Alexandria
in parallel, so by the driver's rule this run takes even patch numbers and
#1891 odd ones. Each step's number is the next even patch above the step's pull
request base and above every Alexandria version any local or remote ref claims
at the moment of the commit and again at the push. At runbook time main is
0.7.31 and #1872's branches claim up to 0.7.33, so Step 1 takes 0.7.34. Before
each commit and each push, run `git fetch origin`, read
`plugins/alexandria/.claude-plugin/plugin.json` on every `origin` ref, and
move to the next even patch above the highest claim if another run has passed
it. Ariadne keeps
1.3.6. The skill generation moves once, in Step 4, through the block above; no
concrete skill version appears in this runbook.

**Horos.** Every commit that changes the tree stages its change, runs
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`, stages
`.horos/boundary.json`, runs
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`,
stages `.horos/census.json`, and only then commits.

**Pinned digests.** The base SHA-256 and git blob id of every file a step
changes was grepped across the tree. None of `statement.py`,
`test_statement.py`, `test_release_limits.py`, `release-statements.md`,
`release-statement-v1.schema.json`, the Alexandria `SKILL.md`, `EVOLUTION.md`,
`AGENTS.md` or `README.md` is pinned. `plugins/alexandria/scripts/alexandria.py`
is named at the historical revision `104f6f82` by
`plugins/ariadne/examples/wildcat-datasets-v0/inputs.json`, its two
`preserved/*/provenance.json` and `preserved/*/statement.json` files, and
`docs/kickoff/1374/evidence/sources.json` and
`docs/kickoff/1389/evidence/sources.json`. Those name a past revision and read
no working file, so they do not move. Before editing any other file, a step
greps its SHA-256 across `tests/` and `plugins/*/tests/` first.

**The Promise Machine block stays.** The `alexandria-release-statement`
contract in the Alexandria `SKILL.md` has a semantic digest in
`tests/promise_machine_id_history.json` and executable cases in
`tests/promise_machine_coverage.json`. No step edits that block. Step 4
documents the part form in the skill's prose outside the contract, and a
promise of its own is a carried-forward item.

**Checks.** Every Exit runs the Alexandria runner and
`scripts/run_checks.py --base fiat/1892-statement-parts --scope root --scope alexandria --scope ariadne`.
Its plan at the base selects the root suite (`python3 -m unittest discover -s
tests`), the Alexandria suite (`python3 -m unittest discover -s
plugins/alexandria/tests -t plugins/alexandria`), the Ariadne suite, which the
new tests rely on, and the Probitas, Tabularium, dead-code, demonstration,
front-door and Phylax, Ephoros and Hypomnema checks. Run every gate with
`NO_COLOR=1` set and `FORCE_COLOR` unset. The checked runner needs a clean,
still tree, so commit before running it and run no other suite beside it.

**Staging variables stay unset.** No Exit exports
`ALEXANDRIA_WILDCAT_V1_STAGING` or `ALEXANDRIA_WILDCAT_V2_STAGING`, so the
staged Wildcat rebuild tests skip. With both exported, four staged V2 rebuild
tests fail on main with "Wildcat V2 registry bytes do not match the pinned
registry", filed as #2023. No gate runs the staged suite, so the run carries no
known-failure inventory; a staged run showing exactly those four failures is
not a finding of this run.

**Conformance cells.** The operator, not a step's worker, runs
`python3 .hexaemeron/design/conformance.py <criterion> --candidate statement-parts`
after a step's audit closes and before its push:

- `part-projection-verifies` before Step 2's push;
- `past-limit-refuses-by-name` and `killed-emit-leaves-no-set` before Step 3's
  push;
- `pinned-statements-keep-bytes`, with `ALEXANDRIA_WILDCAT_V1_RELEASE` and
  `ALEXANDRIA_WILDCAT_V2_RELEASE` exported to the study's section 3 releases,
  before the last `done merge-step`.

Each cell blocks the transition that opens the step after the one that
builds it, and the controller checks it at the previous step's `done push`:
`part-projection-verifies` blocks `step:3`, `past-limit-refuses-by-name` and
`killed-emit-leaves-no-set` block `step:4`, and
`pinned-statements-keep-bytes` blocks `integration`. No Exit runs the
resolver, and no worker writes these reports. Each report is
create-only. The eleven test names the first three cells load are fixed by the
study's section 4; a step creates them under exactly those names.

**Overlap with #1891.** #1891's study selected `range-streamed-logs`, which
changes `usdc_interval.py` build and check. This run edits none of its files.
The shared files are the four version surfaces, the Alexandria `EVOLUTION.md`
and `SKILL.md` frontmatter, `.horos/census.json`, and possibly
`plugins/alexandria/AGENTS.md`. Whichever run merges second syncs: it merges
the other's `main`, keeps both changes, regenerates the Horos pair, reruns both
suites, and moves its Alexandria package version and generation row above the
merged values.

**Copies.** Step 1's copies of the study and runbook stay byte-identical to
`.hexaemeron/study.md` and `.hexaemeron/runbook.md`. A step that follows an
amendment re-copies both in the same commit, and every later step lists them.

## The decision record

The three decisions in study item 12 share one unnumbered draft,
`docs/decisions/drafts/split-a-release-statement-into-parts.md`. Step 1
creates it whole: the part form and its two predicate types, the part bound
and why it is 6,225,920 bytes, and Laurence's 2026-09-30 answer on the band.
No step writes a number into its bytes or its filename, and no document cites
it by anything but that path.

## Step 1: Preserve the design records and open the decision draft

**Goal.** Commit the receipted study and runbook, the locked design record with its 20 selection reports and three resolvers, and the decision draft, with no product change.

**Entry.** The run branch `fiat/1892-statement-parts` at `150943da240837040478a76c3611d150fa04f2b6`, with the study, design-lock and runbook receipts accepted and the Alexandria suite passing there.

**Exit.** The design records sit under the Alexandria docs tree byte-identical to their controller sources, the decision draft exists, and every command below exits 0.
The study, runbook and record are copied to
`plugins/alexandria/docs/statement-parts/study.md`, `runbook.md` and
`design-evidence.json`. The folder `.hexaemeron/design/` is copied to
`plugins/alexandria/docs/statement-parts/design/`, holding `resolve.py`,
`conformance.py`, `build_design_evidence.py` and the 20
`reports/selection/*.json` at the relative paths the record binds. The draft
carries the heading `# Decision: Split a release statement past Ariadne's
bounds into an index and parts`, the sections Status, Context, Decision,
Alternatives and Consequences, the status `Accepted, 2026-09-30`, and no
number.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1892-statement-parts --scope root --scope alexandria --scope ariadne --format json
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/alexandria/docs/statement-parts/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/alexandria/docs/statement-parts/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study plugins/alexandria/docs/statement-parts/study.md --design-evidence plugins/alexandria/docs/statement-parts/design-evidence.json --repo-root .
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions/drafts/split-a-release-statement-into-parts.md plugins/alexandria/docs/statement-parts
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/alexandria/docs/statement-parts
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins/alexandria/docs/statement-parts
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/drafts/split-a-release-statement-into-parts.md plugins/alexandria/docs/statement-parts/study.md plugins/alexandria/docs/statement-parts/runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/drafts/split-a-release-statement-into-parts.md
```

**Files.**

- Create under `plugins/alexandria/docs/statement-parts/`: `study.md`,
  `runbook.md`, `design-evidence.json`, `design/resolve.py`,
  `design/conformance.py`, `design/build_design_evidence.py` and the 20
  `design/reports/selection/*.json`.
- Create `docs/decisions/drafts/split-a-release-statement-into-parts.md` and
  `plugins/alexandria/tests/test_statement_parts_records.py`.
- Raise the version in the four places the rules list, to the next even
  patch above every ref's claim at commit and at push.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`.

**Tests.** Add `DesignRecordCopyTests` to `plugins/alexandria/tests/test_statement_parts_records.py` with three tests. `test_the_record_copy_is_the_locked_design_record` asserts the copy's SHA-256 is the design-lock value above. `test_every_selection_report_the_record_binds_is_committed` asserts that each resolved cell's report exists at its bound path with its bound SHA-256. `test_the_conformance_harness_refuses_every_other_candidate` asserts that the committed `conformance.py` exits 2 for each of the three rejected candidates, names the refusal and writes no report. The full count is set by execution. Also run by hand before the commit, outside the suite:

- `cmp` of every copy against its `.hexaemeron/` source;
- `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py plugins/alexandria/docs/statement-parts/design-evidence.json --transition design-lock`, which prints `clean`;
- `python3 -m unittest tests.test_skills_sh_package`, which measures the portable package's file and byte headroom with the new folder;
- `python3 scripts/plugin_release.py --base fiat/1892-statement-parts --head HEAD`, which names the Alexandria rise to 0.7.34 or the next even patch above every ref's claim.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`

**Disciplines.** phylax: the committed resolvers enter the `lint-phylax` walk under `plugins/`, start only fixed-argv git, demo and Ariadne children, and the Phylax run above keeps them clean. ephoros: none, nothing in this step runs unattended. metron: none, this step makes no performance claim. elenchus: a copy that differs from its source is a failure to reproduce and repair, never a copy to re-pin. hypomnema: the step opens the decision record and ships the study and runbook under the repository's lint.

## Step 2: Project a release past the single bounds into an index and parts

**Goal.** Add the pure projection from a verified manifest to a part set, with its packing rule, key count, part bound and two closed schemas, while `emit_statement` and the command stay exactly as they are.

**Entry.** Step 1's branch with its `--audit` head merged into it.

**Exit.** A manifest past the single bounds projects into an index and parts that Ariadne verifies with its defaults, a manifest within them still projects into today's one statement, and every command below exits 0.
In `plugins/alexandria/scripts/alexandria_lib/statement.py`:

- constants `MAX_STATEMENT_KEY_CHARACTERS` (262,144), `MAX_PART_BYTES`
  (6,225,920, derived as three quarters of `MAX_STATEMENT_BYTES` less 65,536),
  `PART_PREDICATE_TYPE` and `INDEX_PREDICATE_TYPE`;
- `key_characters(statement)`, counting every object key under the predicate
  and every key of each subject's digest object, as Ariadne's gates 4 and 7
  scan them;
- a projection that returns today's one canonical statement when it is within
  8,388,608 bytes and 262,144 key characters, and otherwise the index and
  parts in the study's wire shapes: greedy parts in manifest order, each
  capture in the part holding its component, each part within the part bound,
  and the index binding every part by SHA-256;
- a named `AlexandriaError` when one component with its captures needs a part
  past either bound, naming the component, the bound and the size.

`plugins/alexandria/schemas/release-statement-part-v1.schema.json` and
`release-statement-parts-v1.schema.json` are closed, and
`plugins/alexandria/schemas/README.md` catalogues them.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1892-statement-parts --scope root --scope alexandria --scope ariadne --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/alexandria/schemas/README.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/alexandria/schemas/README.md
```

**Files.**

- Change `plugins/alexandria/scripts/alexandria_lib/statement.py` beside
  `statement_for`, without changing `statement_for`, `validate_projection` or
  `emit_statement`.
- Create `plugins/alexandria/schemas/release-statement-part-v1.schema.json`,
  `plugins/alexandria/schemas/release-statement-parts-v1.schema.json` and
  `plugins/alexandria/tests/test_statement_parts.py`.
- Change `plugins/alexandria/schemas/README.md`.
- Raise the version in the four places the rules list, to the next even
  patch above every ref's claim at commit and at push. Re-copy
  `plugins/alexandria/docs/statement-parts/study.md` and `runbook.md` if an
  amendment has landed since the last copy.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`.

**Tests.** The resolver loads five tests for `part-projection-verifies`, so `StatementPartProjectionTests` in `plugins/alexandria/tests/test_statement_parts.py` carries exactly `test_a_release_past_the_limit_projects_into_parts_ariadne_verifies`, `test_every_component_and_capture_lands_in_exactly_one_part_in_order`, `test_each_part_stays_within_the_part_limit_and_key_budget`, `test_the_index_binds_every_part_by_digest` and `test_a_release_within_both_bounds_keeps_one_statement`. The acceptance test builds a 16,384-component, 16,384-capture synthetic release like `write_synthetic_release` in `tests/test_release_limits.py`, whose single statement passes 8,388,608 bytes, and runs `ariadne.py verify` with default bounds on the index and every part, bare and inside an unsigned DSSE envelope built with Ariadne's `envelope.Envelope`, requiring exit 0 each time. Cover in addition:

- the heavy variant of seven 941-character gaps a capture, which packs by bytes rather than by keys;
- a 2,000-component release under 8,388,608 bytes but over the key budget projecting into parts;
- `key_characters` agreeing with the characters `ariadne_lib.gates.scanned` yields on the same statement;
- `MAX_STATEMENT_KEY_CHARACTERS` equal to Ariadne's `MAX_STRUCTURED_KEY_CHARACTERS_TOTAL`, read with `runpy` as `test_statement_limit_tracks_ariadne_bounded_reader` reads `DEFAULT_MAX_BYTES`, and `MAX_PART_BYTES` derived from `DEFAULT_MAX_BYTES`;
- one component past the part bound refusing by name, using the shape of `OutputBoundaryTests.near_limit_release` in `tests/test_statement.py`;
- the eleven pinned manifests of the study's section 3 that are in the tree projecting to today's bytes;
- both new schemas closed, catalogued and matching the emitted field sets.

At least the five named tests; the full count is set by execution. The local version proof is `python3 scripts/plugin_release.py --base <previous step's branch> --head HEAD`, which names an even Alexandria patch above every ref's claim.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`

**Disciplines.** phylax: the projection reads only a manifest the existing `verify` already accepted, and the part bound keeps every output inside Ariadne's default reader bounds without widening them. ephoros: the oversized-component refusal names the component, the bound and the size, because an operator meets it after a long collection. metron: none, the projection is linear in the manifest and no budget is claimed; Step 4 records the observation. elenchus: each bound has a guard at its value and one past it that fails on the parent. hypomnema: the part form and its bound are the first two decisions in the Step 1 draft, and the schemas README catalogues the new shapes.

## Step 3: Write a part set with statement --parts and route the single-path refusals

**Goal.** Add `statement <release> --parts <directory>` with a confined, atomic directory writer and receipt, and make `--output` refuse a release past either single bound by name while naming `--parts`.

**Entry.** Step 2's branch with its `--audit` head merged into it, and the `part-projection-verifies` report written.

**Exit.** The command writes a part set only whole, refuses every out-of-bound or unsafe case by name, keeps every pinned statement's bytes, and every command below exits 0.

- `plugins/alexandria/scripts/alexandria.py` declares `--output` and
  `--parts` on `statement` as a required mutually exclusive pair.
- `--parts` verifies the release, projects it, and refuses a release within
  both single bounds, naming `--output`. It refuses a target that exists,
  lies inside the release, or passes through a symlink, reusing the parent
  checks of `_prepare_output`. It makes a fresh temporary sibling directory
  with `mkdir` under the confined parent descriptor and writes each file with
  `O_EXCL` and `O_NOFOLLOW`. It fsyncs every file and the directory,
  re-verifies the release, and renames the directory into place. Any failure
  removes the temporary directory and installs nothing.
- Its canonical JSON receipt reports `release_id`, `part_count`,
  `component_count`, `capture_count`, both predicate types and the absolute
  `output` path.
- `emit_statement` raises a subclass of `AlexandriaError` for a release past
  either single bound. The byte case keeps its exact text; the key case reads
  `release statement carries N key characters, above Ariadne's
  262144-character scan budget`. The command prints one more `alexandria:`
  line naming `--parts <directory>`, with no traceback.
- `check_statement_beyond_the_old_limits` in `test_release_limits.py` asserts
  that the 6,500-component release now refuses with the key text and writes
  nothing, and that `--parts` writes its set. The 16,384-component case keeps
  its exact byte-refusal assertion.
- `plugins/alexandria/AGENTS.md` states the `--parts` side effects beside the
  `statement` entry.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1892-statement-parts --scope root --scope alexandria --scope ariadne --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/alexandria/AGENTS.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/alexandria/AGENTS.md
```

**Files.**

- Change `plugins/alexandria/scripts/alexandria_lib/statement.py` at
  `emit_statement` and beside `_write_statement`.
- Change `plugins/alexandria/scripts/alexandria_lib/__init__.py` if the new
  entry point is exported, and `plugins/alexandria/scripts/alexandria.py` at
  the `statement` parser and its dispatch.
- Change `plugins/alexandria/tests/test_statement_parts.py`,
  `plugins/alexandria/tests/test_release_limits.py` at
  `check_statement_beyond_the_old_limits`, and `plugins/alexandria/AGENTS.md`.
- Raise the version in the four places the rules list, to the next even
  patch above every ref's claim at commit and at push. Re-copy
  `plugins/alexandria/docs/statement-parts/study.md` and `runbook.md` if an
  amendment has landed since the last copy.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`.

**Tests.** The resolver loads six tests for `past-limit-refuses-by-name` and `killed-emit-leaves-no-set`, so `StatementPartsCommandTests` in `plugins/alexandria/tests/test_statement_parts.py` carries exactly `test_a_component_past_the_part_limit_refuses_by_name`, `test_output_refuses_a_release_past_the_single_bounds_naming_parts`, `test_parts_refuses_a_release_that_fits_one_statement`, `test_an_interrupted_write_leaves_no_output_directory`, `test_an_existing_output_is_refused_unchanged` and `test_output_inside_or_through_a_symlink_into_the_release_is_refused`. Cover in addition:

- the command's receipt and its canonical bytes, and a repeated run to a fresh directory writing byte-identical files;
- a release changed between verification and the rename installing nothing;
- `--output` and `--parts` together, and neither, refusing as a usage error;
- a failure in each of the file write, the fsync and the rename leaving no output directory and no temporary sibling;
- the eleven pinned statements of the study's section 3 in the tree keeping their SHA-256 through `--output`;
- every existing test in `tests/test_statement.py` passing unchanged.

At least the six named tests; the full count is set by execution. The local version proof is `python3 scripts/plugin_release.py --base <previous step's branch> --head HEAD`, which names an even Alexandria patch above every ref's claim.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`

**Disciplines.** phylax: this step opens a directory write boundary, and the controls are the confined parent, the absent target, the exclusive no-follow creates, the re-verification before the rename and the removal on failure; a hostile writer with permission on the output parent stays outside the promise, as #653 carried forward. ephoros: every refusal is one `alexandria:` line naming the bound or the path, and the receipt names what was written. metron: none, the writer adds one fsync a file and no budget is claimed. elenchus: each unsafe case is a fail-closed refusal with a guard test that fails on the parent. hypomnema: the band routing is the third decision in the Step 1 draft, and `AGENTS.md` states the new side effects.

## Step 4: Document the part set, record the demonstration and write the generation row

**Goal.** State the part form where readers look for it, record the heavy-fixture demonstration with its Ariadne results in a proof, and move the Alexandria skill generation once.

**Entry.** Step 3's branch with its `--audit` head merged into it, and the `past-limit-refuses-by-name` and `killed-emit-leaves-no-set` reports written.

**Exit.** The documents state what the code does, the proof records a run on this step's tree, the generation row is written, and every command below exits 0.

- `plugins/alexandria/docs/release-statements.md` replaces the promise at
  lines 17 to 19 with both single bounds, adds a section on part sets with the
  wire shapes, the part bound and why it is 6,225,920 bytes, and a
  stranger's three checks: `verify` on the index, `verify` on each part, and
  each part's SHA-256 against its index subject.
- The Alexandria `SKILL.md` statement prose outside the Promise Machine block
  states `--parts` and the two bounds, and its frontmatter version moves with
  the generation.
- `plugins/alexandria/docs/statement-parts/proof.md` records, on this step's
  commit: the heavy 16,384-component fixture's part count, largest part bytes
  and key characters; `ariadne.py verify` exit 0 on the index and every part,
  bare and as unsigned DSSE; `/usr/bin/time -l` for `statement --parts`; and
  the eleven pinned statement digests.
- `plugins/alexandria/skills/alexandria/EVOLUTION.md` gains one generation row
  through the `version-relations` block, keeping the held frontier.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1892-statement-parts --scope root --scope alexandria --scope ariadne --format json
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/alexandria/docs/release-statements.md plugins/alexandria/docs/statement-parts/proof.md plugins/alexandria/skills/alexandria/SKILL.md plugins/alexandria/skills/alexandria/EVOLUTION.md
for file in plugins/alexandria/docs/release-statements.md plugins/alexandria/docs/statement-parts/proof.md plugins/alexandria/skills/alexandria/SKILL.md; do python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$file"; done
```

**Files.**

- Change `plugins/alexandria/docs/release-statements.md`,
  `plugins/alexandria/skills/alexandria/SKILL.md` outside its Promise Machine
  block and `plugins/alexandria/skills/alexandria/EVOLUTION.md`.
- Create `plugins/alexandria/docs/statement-parts/proof.md`, and add
  `ProofRecordTests` to `plugins/alexandria/tests/test_statement_parts_records.py`.
- Raise the version in the four places the rules list, to the next even
  patch above every ref's claim at commit and at push. Re-copy
  `plugins/alexandria/docs/statement-parts/study.md` and `runbook.md` if an
  amendment has landed since the last copy.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`.

**Tests.** `ProofRecordTests` asserts that `proof.md` names the commit its runs used and that every digest it records equals the study's section 3 table, so the proof cannot restate a number the tree does not hold. The root suite's version-propagation and evolution-contract tests cover the generation row and the four version surfaces. The full count is set by execution. The local version proof is `python3 scripts/plugin_release.py --base <previous step's branch> --head HEAD`, which names an even Alexandria patch above every ref's claim.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-4.json`

**Disciplines.** phylax: none, no new boundary opens and the documents state the ones Step 3 opened. ephoros: none, nothing new runs unattended. metron: the proof records `/usr/bin/time -l` for `statement --parts` on the heavy fixture as an observation with no threshold, as the study's section 10 sets out. elenchus: a proof figure that disagrees with the tree is a failure to reproduce, never a figure to re-type. hypomnema: the step finishes the reader-facing record, and the generation row is the ledger home the design bridge names.
