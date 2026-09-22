# Runbook: portable payload reserve and standing measurement

Derived from the receipted study `.hexaemeron/study.md`, SHA-256
`d954a80f9c71cb764ec308d36452fcf053ff848548e6dde2bf21e9d3b1d34081` at its
receipt, for [wildcat-finance/skills#1720](https://github.com/wildcat-finance/skills/issues/1720).
The run branch is `fiat/1720-portable-payload-reserve-and-standing-measu`, cut
from `main` at `66f52785813a8453e7c7d54f2371aa8f6e465640`. Step 1 branches from
the run branch and every later step from the step below it. Take every branch,
parent and pull-request base from the controller directive.

The selected design is `example-payload-class` (study section 4), confirmed by
the operator on 2026-09-20. The generator gains a `measure` action that prints
the package's bytes, the line, the margin, the file count against the tripwire
and the largest default-included paths, and that still answers on a tree over
the line. One omission class then replaces the five example-specific rows:
non-Markdown files under `plugins/*/examples/` leave the package, except any
file a packaged Markdown document links and the retained Lazarus release under
`plugins/lazarus/examples/aave-v4-spoke-v1-release/`. The cap (26,214,400
bytes), the reserve (5,242,880 bytes), the line (20,971,520 bytes) and the
1,600-file tripwire keep their values. Module order is `measure`, then
`example-class`: Step 2 builds the first and Step 3 the second.

The run is an ordinary delivery. No file under `plugins/` changes, so no plugin
version and no `EVOLUTION.md` row is owed and this runbook carries no version
relation. A step that finds it must edit a plugin file stops and asks first;
that step would owe the plugin's version rise. The study carries no inventory
of known failures (study section 2), so this runbook assigns none.

Conventions for every step:

- Exits run from the run worktree root on the committed step head, with
  `NO_COLOR=1` in the environment because this shell sets `FORCE_COLOR=3`,
  which reddens argparse assertions. `scripts/run_checks.py` freezes a snapshot
  without ignored files, so its suites never read the run's `.hexaemeron/`. The
  exit code alone is not the proof: read the JSON outcome and the list of
  checks that ran, because a clean tree with no `--base` selects nothing and
  still exits 0.
- The root suite is the check `root-suite` in `tests/check-map-v1.json`, argv
  `python3 -m unittest discover -s tests`. The command grammar refuses `-m`, so
  every Exit reaches it through `scripts/run_checks.py` with `--base` set to
  the run branch and `--scope root`. Step 1 adds `--scope docs`. Steps 2 to 4
  add `--scope promise-machine`, which owns `scripts/portable_promise_machine.py`
  and `tests/test_skills_sh_package.py` and depends on `root` and `hexaemeron`,
  so those Exits also run `hexaemeron-suite`, `imprimatur-suite` and the two
  Hexaemeron forge checks. That suite holds
  `plugins/hexaemeron/tests/test_phylax_model_proxy.py`, which builds the
  package (study risk `other-suites`).
- Host baseline, observed on the run's starting tree `66f52785`: three
  checkpoint-authority tests in `hexaemeron-suite` refuse without `cosign`
  (`test_real_cosign_pinned_interoperability`, the `DemonstrationTests` class
  set-up in `test_checkpoint_authority_release`, and
  `test_actual_execution_is_complete_and_bound`). This host has none on
  `PATH`. It supplies `cosign` 3.1.3 through `CHECKPOINT_COSIGN`: 139,618,946
  bytes, SHA-256
  `5cf948c2f4dfe59687bdd0b8523709067383e03982cc543475c8a7dc70e92a76`, equal to
  the `darwin-arm64` pin in
  `plugins/hexaemeron/skills/fiat/checkpoint-authority/tool-profile.json`. With
  it set, those tests ran 6 of 6 green. Every Exit gate runs with
  `CHECKPOINT_COSIGN` set and the scope is never dropped. Step 2 runs its Exit
  gate once on its entry tree before any edit and records the outcome. Any red
  is reproduced on a detached snapshot of the step's base before it is called
  a baseline failure. Do not lower `--jobs` to work around load.
- `scripts/portable_promise_machine.py` is not a registered command interface.
  The registry in `plugins/hexaemeron/skills/protasis/scripts/gate_commands.py`
  names eight scripts and the generator is not one, so editing it owes no
  module-binding re-pin. For the same reason its commands, the design
  resolver, `design_evidence.py` and the Horos scanner appear below as
  hand-run deliverables and never inside an Exit command fence.
- `tests/run_tests.py` is registered below at its whole-file SHA-256 as the
  audit runner. No step edits it; an edit refuses later receipts with
  `registered-source-drift`. It runs the whole root suite, which holds every
  test this run writes.
- Digest pins, searched at the starting commit with `git grep` over the index:
  the SHA-256 of `scripts/portable_promise_machine.py`
  (`62336bd53ead80ebd14e63b43e81cd80c4689c16442bc9d4b8bf0e006f188d00`),
  `tests/test_skills_sh_package.py`
  (`14f33651b4dd387a6c3d272bac908ac623c7ea698231ab0711cd7b0bab8dbd29`) and
  `.agents/skills/promise-machine/PORTABLE.md`
  (`f3ed45f2b7b0f5252c1b08cf8811f8b33e2e42cfdf848dd89137a4f2cc3593f5`) appear
  in no tracked file, so editing them owes no re-pin. One neighbour is pinned:
  `tests/test_agent_instruction.py` at `tests/promise_machine_coverage.json`
  line 157. No step edits it; a step that must stops and asks first, because
  the edit owes that re-pin. Repeat the search for every file a step edits
  beyond its Files field.
- Stage every change, run `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`
  and `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`,
  stage `.horos/boundary.json`, `.horos/candidates.json` and
  `.horos/census.json` together, then commit. The census counts bytes across
  every tracked file, so every commit moves it, audit-fix and audit-record
  commits included. Never hand-edit a `.horos` artefact.
- Generated and pinned files stay with their owners. `SOURCES.md` is written by
  its generator and no step touches it. Files under `audit/` are byte-pinned:
  Warden appends this run's record and nothing else there changes.
- Decision records. The new record ships as an unnumbered draft under
  `docs/decisions/drafts/`; integration assigns its number. ADR-040, ADR-090 and
  the seven drafts already under `docs/decisions/drafts/` keep every byte; the
  new draft refers to them and edits none. This runbook and the study name
  records by path or ADR number only, never by stable-slug reference, because
  the docs copies are linted and an amendment cannot remove a finding.
- Package figures. Any figure written into a comment, `PORTABLE.md`, the draft
  or a pull-request body names its measure and its commit and comes from a
  fresh `measure` run (study risk `figure-prose`). Audits of the last two runs
  landed that fix three times; brief each Mason with it. Hand counterfactuals
  and measured figures go in the step's pull-request body.
- Every commit is signed locally. `.githooks/greenlight` is run from this
  worktree's own copy, never by absolute path from another checkout.
- The design record `.hexaemeron/design-evidence.json` is immutable. Four
  conformance cells of `example-payload-class` are pending. `measure-agrees`
  blocks `step:3` and Step 2 produces its report. `class-leaks`,
  `installed-gates-pass` and `room-on-step-tree` (at least 794,493 bytes) block
  `step:4` and Step 3 produces theirs. Each resolver is the exact string
  `python3 .hexaemeron/design/resolve.py conformance --root . --reports .hexaemeron/reports --candidate example-payload-class --criterion <id>`
  and writes `.hexaemeron/reports/example-payload-class--<id>.json`. Run each
  resolver once, from the run worktree root, on the step's final head after
  its audit loop closes and before its push receipt: the resolver refuses to
  overwrite a report whose bytes differ, and `room-on-step-tree` records a
  byte count that any later packaged-byte change would move. A refusal or a
  failing cell stops the run; no report is deleted or rewritten. No cell
  blocks `integration`, but that transition re-reads all four reports, so
  their bytes stay unchanged until the run integrates. The pending cells of
  the three unselected candidates are never resolved.

```command-interfaces
schema | protasis-command-interfaces/v1
tests/run_tests.py | report_target | aa577d63846e947944c04506ca9985b18bf3bac21c6d360bdbc18fd1f8360258
```

```design-lock
schema | protasis-design-evidence/v1
sha256 | b20a981525c9dd1b37dbc6bdb229d9ca56ab5ccae184b9888fa6445e27d43e04
candidate | example-payload-class
```

## Step 1: Scaffold the specification, the design evidence and the draft decision

**Goal.** Put the receipted study, this runbook, the design record, its
reports, the resolver and its two measurement files under
`docs/portable-payload-reserve/`, and author the draft decision the study's
design bridge names.
**Entry.** The run branch at `66f52785813a8453e7c7d54f2371aa8f6e465640` with a
clean tree. No conformance evidence is due at `step:1`. The root suite's state
at this commit was not measured while drafting; Mason runs the Exit gate once
before editing to fix the baseline.
**Exit.** Each command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1720-portable-payload-reserve-and-standing-measu --scope root --scope docs --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/portable-payload-reserve/study.md docs/portable-payload-reserve/runbook.md docs/decisions/drafts/omit-example-payloads-from-the-portable-runtime.md --max-defects 0
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/portable-payload-reserve/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/portable-payload-reserve/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/portable-payload-reserve docs/decisions
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study docs/portable-payload-reserve/study.md --design-evidence docs/portable-payload-reserve/design-evidence.json --repo-root .
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py docs/portable-payload-reserve/design
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py docs/portable-payload-reserve/design
```

- `docs/portable-payload-reserve/study.md`, `runbook.md` and
  `design-evidence.json` are byte-identical to `.hexaemeron/study.md`,
  `.hexaemeron/runbook.md` and `.hexaemeron/design-evidence.json`
  (`b20a981525c9dd1b37dbc6bdb229d9ca56ab5ccae184b9888fa6445e27d43e04`).
  `docs/portable-payload-reserve/reports/` holds byte-identical copies of the
  32 selection reports under `.hexaemeron/reports/`.
  `docs/portable-payload-reserve/design/` holds byte-identical copies of
  `resolve.py` (`9060bf1f6fd8a444315987b6ffcb5d7bf130f0c4855304b5f1d7d8f19d232de1`),
  `main-measurement.json` (`68aa491948d78473289c8864abe70af388d254691ecb5c6aa04d51369d0b8559`)
  and `selection-summary.json` (`de1338c4849f195edaddf9dd8648a94f5da1b42918b10d800f9f227c1ee9a99c`).
  A Phylax or Ephoros finding on the resolver is repaired in the
  `.hexaemeron/design/` original and recopied, so the copy stays exact; the
  record pins reports only, so that repair moves no receipted digest.
- `docs/decisions/drafts/omit-example-payloads-from-the-portable-runtime.md`
  exists with the heading `# Decision: ...`, the sections Status, Context,
  Decision, Alternatives and Consequences in that order, a dated status and no
  ADR number. It records the class, the five rows it replaces, the two
  exceptions, the three refused candidates with the study section 4 figures
  (each naming the resolver's simulation and the starting commit), the
  `portable-payload-measurement/v1` field list, and the reserve question left
  open for ADR-090's owner. It refers to ADR-040, ADR-090 and the draft
  `docs/decisions/drafts/keep-one-complete-lazarus-fixture-in-the-portable-runtime.md`
  by path and changes none of them.
- Hypomnema walks `docs/decisions`, not `docs/decisions/drafts` alone: observed
  at the starting commit, the narrower walk exits 1 with two H009 findings on
  an inherited draft whose references resolve only when the numbered records
  are indexed too.
- `git diff --stat` against the run branch names no path outside the Files
  field, and the three `.horos` artefacts equal a fresh scan.

**Files.** `docs/portable-payload-reserve/study.md`,
`docs/portable-payload-reserve/runbook.md`,
`docs/portable-payload-reserve/design-evidence.json`,
`docs/portable-payload-reserve/reports/` (32 files),
`docs/portable-payload-reserve/design/resolve.py`,
`docs/portable-payload-reserve/design/main-measurement.json`,
`docs/portable-payload-reserve/design/selection-summary.json`,
`docs/decisions/drafts/omit-example-payloads-from-the-portable-runtime.md`,
`.horos/boundary.json`, `.horos/candidates.json`, `.horos/census.json`.
**Tests.** None written; the root suite, the tree lints and the document checks
above are the gate.
Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`
**Disciplines.** hypomnema: the copies and the draft are the homes study
section 12 names, and the study's design bridge resolves once the draft
exists. phylax: the resolver copy enters the `lint-phylax` walk, spawns fixed
local argv with no shell and writes only report files (study section 9).
ephoros: none, nothing here runs unattended; the resolver copy still passes
the `lint-ephoros` walk. metron: none, no cost claim; the baseline measurement
is copied, not retaken. elenchus: none, no failure in hand.

## Step 2: Add the standing measurement and name the margin in the refusal

**Goal.** Build module `measure`: the `measure` action with its
`portable-payload-measurement/v1` output, a headroom refusal that names the
margin and the action, and the 1,600-file tripwire held as a generator
constant.
**Entry.** Step 1's exit tree. The Exit gate below is run once on this tree
before any edit and its outcome recorded, which fixes the host baseline for
`hexaemeron-suite`.
**Exit.** The command below exits 0 and reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1720-portable-payload-reserve-and-standing-measu --scope root --scope promise-machine --format json
```

- The interface is the one study section 4 fixes:
  `python3 scripts/portable_promise_machine.py measure [--json] [--top N] [--require-margin BYTES]`.
  Exit 0 when measured, including over the line; 1 when `--require-margin` is
  unmet or the tree cannot be read; 2 on bad usage. `--top` and
  `--require-margin` are non-negative integers. The action writes nothing.
- `--json` prints one object with `schema` `portable-payload-measurement/v1`,
  `source_commit`, `tree_clean`, `cap`, `reserve`, `line`, `file_tripwire`,
  `package` and `runtime` (each with `bytes`, `files` and `margin`),
  `manifest_bytes`, `outer_bytes`, `omission_classes`,
  `largest_default_included` and `kept_by_link`, the last two as lists of
  `path` and `bytes`. `kept_by_link` is empty until Step 3. The help text
  carries the field list. The text form prints bytes, line, margin, files
  against the tripwire and the largest default-included paths.
- `measure` and `package` read one code path, so the `package` figures equal a
  walk of `package --out` on the same tree and the `runtime` figures equal
  `total_bytes` and `file_count` in its `MANIFEST.json` (study risk
  `measure-drift`). On a tree over the line `measure` exits 0 with a negative
  margin and never raises the headroom refusal (`over-line-blind`).
- The refusal raised through `require_byte_headroom` and its callers names the
  bytes, the line, the margin and the `measure` action, and still refuses the
  first byte past the line for the runtime and for the complete package
  (`refusal-text`). A failed `--require-margin` names the margin and the
  requirement.
- The generator holds the 1,600-file tripwire as a module constant and
  `file_tripwire` reports it. `tests/test_skills_sh_package.py` keeps its own
  `MAX_FILES` as the independent mirror and asserts the two equal, as it does
  for the cap and the reserve. Generation's behaviour on file count is
  unchanged. The comment above those constants either keeps its figures bound
  to the commit it names or takes new ones from a fresh `measure` run.
- `package --out`, `check` and `sync` keep their interfaces, and
  `distribution/skills-runtime/sync.yml` keeps its bytes (`workflow-untouched`).
  No new subprocess, network call or dependency is added.
- By hand on the step head, `NO_COLOR=1 python3 scripts/portable_promise_machine.py measure`
  exits 0, and its `--json` figures are quoted in the pull-request body with
  the commit they describe.
- After the audit loop closes and before the push receipt, the `measure-agrees`
  resolver named in the conventions writes
  `.hexaemeron/reports/example-payload-class--measure-agrees.json` with value
  `true`, and `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3`
  exits 0.
- The new module fails by assertion on the parent of the commit that adds the
  action, shown by a hand counterfactual in the pull-request body. The three
  `.horos` artefacts equal a fresh scan.

**Files.** `scripts/portable_promise_machine.py`,
`tests/test_skills_sh_package.py`,
`tests/test_portable_payload_measurement.py` (new), `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.
**Tests.** New module `tests/test_portable_payload_measurement.py`, at least 10
tests: the JSON figures equal a walk of `package --out` and its manifest; line
equals cap minus reserve and margin equals line minus bytes; the exact schema
and key set; the text form's five parts and the `--top` bound, zero included;
`--require-margin` met exits 0 and unmet exits 1 naming the margin; a negative
or non-integer argument exits 2; a tree over the line measures at exit 0 with
a negative margin while `package` exits 1 with a refusal naming bytes, line,
margin and `measure`; the first byte past the line still refuses and the
boundary byte passes; the working tree's status is identical before and after
`measure`; a directory that is not a Git checkout exits 1. Each test that
builds a tree over the line states how it does so. In
`tests/test_skills_sh_package.py`, the tripwire equality case is added and the
two headroom cases follow the new refusal text. Expected root-suite count is
observed when run.
Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`
**Disciplines.** metron: this step ships the command that checks the byte
budget, the file budget and the 60,000 ms time budget of study section 10,
and the wall time of one `measure` run is recorded in the pull-request body.
ephoros: the refusal on the hourly job's standard error and `measure --json`
answer study section 8's questions 1 and 2. phylax: the action reuses the
generator's fixed-argv `git` and Horos calls, parses two integer arguments
through `argparse` and writes nothing (study section 9). elenchus: the module
is red on the parent of the action's commit and green after it, and every
audit fix lands with a test that fails without it (study section 11).
hypomnema: the output shape's record is the Step 1 draft and its field list
sits in the help text; the tripwire move and the refusal wording earn no
record (study section 12).

## Step 3: Omit example payloads as one class with link-kept exceptions

**Goal.** Build module `example-class`: one omission class for non-Markdown
files under `plugins/*/examples/`, with link-kept and Lazarus exceptions, its
manifest row, the installed notice in `PORTABLE.md` and the package test
updates.
**Entry.** Step 2's exit tree, with
`.hexaemeron/reports/example-payload-class--measure-agrees.json` present and
the `step:3` design transition clean.
**Exit.** Each command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1720-portable-payload-reserve-and-standing-measu --scope root --scope promise-machine --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py .agents/skills/promise-machine/PORTABLE.md --max-defects 0
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py .agents/skills/promise-machine/PORTABLE.md docs/decisions
```

- The predicate in `_omitted` matches only a non-Markdown file under
  `plugins/*/examples/`. Skills, scripts, schemas, plugin `docs/`, example
  Markdown and the named test files are untouched (study risk
  `class-overreach`).
- Two exceptions hold. The complete release under
  `plugins/lazarus/examples/aave-v4-spoke-v1-release/` stays packaged, and
  `check_duplicate_fixture_payload` still refuses a changed, missing,
  untracked or symlinked copy (`lazarus-retained`). Any example payload that a
  packaged Markdown document links is kept and listed by `measure` under
  `kept_by_link` (`link-pullback`). Links are read with one linear pattern
  over bounded file bytes, with no network; a link-kept target that is
  missing, a symlink or outside the tree refuses generation.
- `OMISSIONS` carries one row for the class, with its exceptions, in place of
  the five example-specific rows: the Lazarus duplicate payloads, the three
  Alexandria `compound-v3-phase0-v0` trees and the Tabularium `*-v1` payloads.
  The count moves from 14 rows to 10. `EXPECTED_OMISSIONS` in
  `tests/test_skills_sh_package.py` carries the same ten pattern strings
  (`manifest-truth`), and `omission_classes` reports 10.
- `.agents/skills/promise-machine/PORTABLE.md` names the class once, says
  which operations on example data need a full checkout of
  `wildcat-finance/skills`, keeps the Lazarus paragraph true, and replaces the
  sentence at line 72 that says Tabularium's v0 evidence remains in the
  package. It cites the Step 1 draft in the form the file already uses for
  the Lazarus draft. No packaged prose is shortened: apart from the portrait
  transform, every packaged Markdown file stays byte-identical to its source
  (`dangling-mentions`).
- Source files under `plugins/` keep their bytes. Every relative Markdown link
  that resolved in the package before this step still resolves, and
  `test_authoritative_runtime_links_close_inside_the_package` stays green.
- `tests/test_portable_duplicate_fixture.py`, `tests/test_portable_skills.py`,
  `tests/test_agent_instruction.py` and
  `plugins/hexaemeron/tests/test_phylax_model_proxy.py` stay green unedited
  (`other-suites`). If one needs an edit, stop and ask first: the third is
  digest-pinned and the fourth is a plugin file.
- By hand on the step head,
  `NO_COLOR=1 python3 scripts/portable_promise_machine.py measure --require-margin 794493`
  exits 0. For orientation only, the resolver's simulation at the starting
  commit gave a complete package of 17,790,545 bytes in 1,404 files, a margin
  of 3,180,975 bytes, and 146 files (2,545,267 bytes) leaving the install; the
  step head's own `measure` figures go in the pull-request body with their
  commit.
- After the audit loop closes and before the push receipt, the three resolvers
  named in the conventions write
  `.hexaemeron/reports/example-payload-class--class-leaks.json` (value 0),
  `.hexaemeron/reports/example-payload-class--installed-gates-pass.json`
  (value `true`) and
  `.hexaemeron/reports/example-payload-class--room-on-step-tree.json` (at
  least 794,493), and
  `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:4`
  exits 0.
- The new class cases fail by assertion on the parent of the class commit,
  shown by a hand counterfactual in the pull-request body. The three `.horos`
  artefacts equal a fresh scan.

**Files.** `scripts/portable_promise_machine.py`,
`tests/test_skills_sh_package.py`,
`tests/test_portable_payload_measurement.py`,
`.agents/skills/promise-machine/PORTABLE.md`, `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.
**Tests.** At least 8 cases added across `tests/test_skills_sh_package.py` and
`tests/test_portable_payload_measurement.py`: the manifest lists ten rows, the
class row carries its exceptions and the five replaced patterns are gone from
`OMISSIONS` and the manifest; the predicate leaves skills, scripts, schemas,
plugin `docs/`, example Markdown and the named test files alone; no packaged
file under `plugins/*/examples/` is non-Markdown unless it is link-kept or
inside the retained Lazarus release; a linked payload is kept, listed under
`kept_by_link` and named in the row's exceptions; a link-kept target that is
missing, a symlink or outside the tree refuses generation; an oversized or
hostile Markdown input is read in bounded time; the Lazarus release is
complete in the package; `PORTABLE.md` names the class and the full-checkout
direction. `test_declared_omissions_are_absent` and
`test_lazarus_keeps_the_complete_release_and_one_payload_copy` are updated to
the class. Expected root-suite count is observed when run.
Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`
**Disciplines.** phylax: link-kept exceptions make repository Markdown an
input to generation, closed by one linear pattern over bounded bytes, targets
normalised and refused when they leave the tree, and symlinks already refused
by `_source_candidates` (study section 9). ephoros: the `omissions` list in
the published `MANIFEST.json` answers study section 8's question 3. metron:
the step is held to the 794,493-byte room gate by the `room-on-step-tree`
cell and the `--require-margin` command of study section 10. elenchus: the
class cases are red on the parent of the class commit, and a failing design
cell stops the run with nothing rewritten to pass it (study section 11).
hypomnema: `PORTABLE.md` is the installed notice and points at the Step 1
draft; no second record is written (study section 12).

## Step 4: Record the delivered measurement and demonstrate the three observations

**Goal.** Commit one measurement of the delivered tree beside the study, copy
the four conformance reports, and run the demo path of study section 1 as
commands whose output is recorded.
**Entry.** Step 3's exit tree, with the three `step:4` reports present and the
`step:4` design transition clean.
**Exit.** Each command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1720-portable-payload-reserve-and-standing-measu --scope root --scope promise-machine --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py docs/portable-payload-reserve
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py docs/portable-payload-reserve
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/portable-payload-reserve docs/decisions
```

- `docs/portable-payload-reserve/measurement.json` is the exact standard output
  of `NO_COLOR=1 python3 scripts/portable_promise_machine.py measure --json`
  on a clean committed tree of this step. Its `source_commit` names that
  commit, which is an ancestor of the step head, and its `tree_clean` is
  `true`. Nothing under `docs/` is packaged, so committing the record moves
  no package byte. No test compares it with `HEAD` (study risk
  `record-currency`).
- `docs/portable-payload-reserve/demonstrate.py` runs the demo path with fixed
  local argv, no shell and no network, keeps its scratch under the system
  temporary directory, and writes only the caller-named `--out` file. By hand,
  `NO_COLOR=1 python3 docs/portable-payload-reserve/demonstrate.py --root . --out docs/portable-payload-reserve/demonstration.json`
  exits 0.
- `docs/portable-payload-reserve/demonstration.json` records, for each
  observation, the argv, the exit code and the output lines relied on. The
  positive run, on the delivered tree: `measure` exits 0; its `--json` figures
  equal a walk of `package --out` and that package's `MANIFEST.json`;
  `measure --require-margin 794493` exits 0; and in an isolated copy of the
  generated package `verify_runtime.py`, the installed Horos `check` and the
  packaged evaluation check each exit 0. First negative observation, on a
  disposable checkout pushed over the line by one staged filler file under
  `plugins/`: `measure --require-margin 794493` exits 1 and names the margin.
  Second negative observation, on the same checkout: `measure` exits 0 with a
  negative margin while `package --out` exits 1 with a refusal naming bytes,
  line, margin and the `measure` action.
- The record names its controller as Fiat and its source command as the
  generator, and claims those three observations and nothing further: no
  growth forecast, no claim that the room suffices, and no claim about the
  hourly publisher.
- `docs/portable-payload-reserve/reports/` gains byte-identical copies of the
  four conformance reports from `.hexaemeron/reports/`; the originals stay in
  place, unchanged, for the `integration` transition. No resolver is rerun in
  this step.
- The three `.horos` artefacts equal a fresh scan.

**Files.** `docs/portable-payload-reserve/measurement.json`,
`docs/portable-payload-reserve/demonstrate.py`,
`docs/portable-payload-reserve/demonstration.json`,
`docs/portable-payload-reserve/reports/example-payload-class--measure-agrees.json`,
`docs/portable-payload-reserve/reports/example-payload-class--class-leaks.json`,
`docs/portable-payload-reserve/reports/example-payload-class--installed-gates-pass.json`,
`docs/portable-payload-reserve/reports/example-payload-class--room-on-step-tree.json`,
`tests/test_portable_payload_measurement.py`, `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.
**Tests.** At least 3 cases added to
`tests/test_portable_payload_measurement.py`: the committed measurement parses
as `portable-payload-measurement/v1`, carries a 40-hex `source_commit` and a
true `tree_clean`, and its own arithmetic holds, with no comparison against
the live tree; each of the four committed report copies parses as a
`protasis-design-report/v1` object with exit 0 and a value that passes its
gate; the demonstration record holds exactly the three observations with exit
codes 0, 1 and the pair 0 and 1. No product code changes. Expected root-suite
count is observed when run.
Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-4.json`
**Disciplines.** metron: the committed measurement is the recorded reading of
the delivered tree, taken the same way as the baseline in
`docs/portable-payload-reserve/design/main-measurement.json` and bound to a
named commit (study section 10). phylax: `demonstrate.py` is Python under
`docs/`, enters the `lint-phylax` walk, spawns fixed argv and confines its
writes to scratch and one named file (study section 9). ephoros: none, no new
signal; the demonstration reads the two that Steps 2 and 3 emit. elenchus: the
two negative observations are refusals shown to fire, and a demo command that
fails is worked to its cause before any record is written (study section 11).
hypomnema: the measurement, the demonstration record and the report copies
live beside the study, outside the package, as study section 12 places them.
