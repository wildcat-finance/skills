# Runbook: horos-33, evidence files readable by rule

Derived from the receipted study `.hexaemeron/study.md`, SHA-256
`97ba74025a6bb57b14b4405f69be6544f229b285076fd9258da1d084c1f2517e`, for
wildcat-finance/skills issue 1383. The run branch is
`fiat/1383-horos-33-evidence-files-readable-by-rule`, cut from `main` at
`9599fa46e8e2c5436a0dae4327c8e5b72f5159a9`. Step 1 branches from the run
branch and every later step from the step below it.

The selected design is `attribute-then-family` (study section 4). Git's
resolution of `linguist-generated` and `linguist-vendored` decides first, in
both directions. Then the exact basenames `manifest.json`, `statement.json`,
`SHA256SUMS` and `events.jsonl` stay readable against every Horos heuristic,
and a hard directory holding a readable file splits into per-file entries. The
operator confirmed study assumption 4, that a set attribute outranks a family
name, on 2026-09-17 before the study receipt.

Conventions for every step:

- Exits run from the run worktree root on the committed step head.
  `scripts/run_checks.py` freezes a snapshot without ignored files, so its root
  suite never reads the run's `.hexaemeron/`. A bare `unittest` run inside the
  run worktree fails the two tests issue 1228 names and is not an exit.
- Suites and the checks runner run with `NO_COLOR=1`, because this shell sets
  `FORCE_COLOR=3`, which reddens argparse tests.
- Stage every change, run
  `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and
  `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`,
  stage `.horos/boundary.json`, `.horos/candidates.json` and
  `.horos/census.json` together, then commit. Never hand-edit a `.horos`
  artefact.
- `plugins/horos/tests/test_boundary.py` is never edited, because Promise
  Machine fixtures pin it. `plugins/horos/tests/run_tests.py` is never edited,
  because the registration below pins it.
- No committed file, pull request body or audit record identifies the private
  archive target delivered under issue 1356 beyond what issues 1356 and 1483
  state publicly.
- The three conformance cells that block `integration` (study section 4) are
  resolved after the last step's pull request merges into the run branch and
  before that step's merge receipt, by the resolvers the study names. No step
  runs `.hexaemeron/design-reports/resolve.py`, and no existing report is
  rewritten.

```version-relations
horos | plugins/horos/skills/horos/EVOLUTION.md | next-generation-after-integration-base
```

```design-lock
schema | protasis-design-evidence/v1
sha256 | 297d62d1d270f02ec7fac097c2878225e2cbdd8becb841e3a8e7a552a56002b1
candidate | attribute-then-family
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/horos/tests/run_tests.py | report_target | 4aeff448d2c0963e15399de939f4dc29e3dab5d44b50af3cbf7b3c6b6ebbb9e4
```

## Step 1: Commit the spec copies

**Goal.** Put the receipted study and this runbook at
`plugins/horos/docs/readable-families/`, so the branch carries its own
specification.
**Entry.** The run branch at `9599fa46e8e2c5436a0dae4327c8e5b72f5159a9` with
a clean tree. At study time the Horos suite passed and `horos.py check .`
exited 0 (study section 3).
**Exit.** Each command below exits 0, and the checks runner reports outcome green:

```sh
python3 scripts/run_checks.py --base fiat/1383-horos-33-evidence-files-readable-by-rule --scope root --scope horos --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/horos/docs/readable-families/study.md plugins/horos/docs/readable-families/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/horos/docs/readable-families
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/horos/docs/readable-families/runbook.md
```

Each copy is byte-identical to its receipted artefact under `.hexaemeron/`, and
the three `.horos` artefacts equal a fresh scan.
**Files.** `plugins/horos/docs/readable-families/study.md`,
`plugins/horos/docs/readable-families/runbook.md`, `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.
**Tests.** None written; the root and Horos suites are the gate.
Elenchus command: `python3 plugins/horos/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`
**Disciplines.** hypomnema: the copies are the home study section 12 names for
the precedence and the refused candidates. phylax: none, documentation only.
ephoros: none, nothing here runs unattended. metron: none, no cost claim.
elenchus: none, no failure in hand.

## Step 2: Resolve attributes as Git does and keep the families readable

**Goal.** Build `attribute-then-family` in `horos.py`, with a guard for each
family that fails against the starting classifier.
**Entry.** Step 1's exit tree.
**Exit.** The command below exits 0 and reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1383-horos-33-evidence-files-readable-by-rule --scope root --scope horos --format json
```

- Resolution sits beside the unchanged set-only helpers, in the precedence of
  study section 4, "What attribute-then-family builds". Within one attribute
  file the last matching line decides, and the innermost file that decides
  wins. `attr` and `attr=true` set, `-attr` and `attr=false` unset, `!attr`
  and any other value leave the attribute unspecified, and a macro definition
  line is skipped.
- A set attribute makes a hard entry citing its deciding line in today's
  evidence format. An unset attribute keeps any file readable. Otherwise an
  exact family basename is readable, checked first in `classify_file` after its
  symlink refusal.
- A corroborated generated or vendored directory, or a directory a set pattern
  matches, that holds a readable tracked file becomes per-file hard entries.
  The directory evidence ends with `; split around readable <path>`, plus
  ` and <n> more` when there are more. Candidate directory entries and the
  census count each file once, as before.
- `plugins/horos/tests/test_readable_families.py` checks each family in the
  three placements of study section 1: a served `out/` directory, a
  maintainer's broad set pattern with a readable line, and a neighbouring
  `ledger.tar.part-aa` under `*.part-* linguist-generated`. It also checks the
  eight near-miss names, a set attribute excluding each family name, the
  attribute cases against `git check-attr` in temporary repositories with every
  `GIT_*` variable removed, and `check` scoped to a split directory. It imports
  only the standard library and `horos`, uses no name the starting classifier
  lacks, and at least 4 of its tests fail by assertion when copied beside the
  starting classifier, shown by a hand counterfactual.
- The regenerated root boundary changes no hard entry and no boundary field.
  `.horos/candidates.json` loses exactly two entries,
  `plugins/alexandria/examples/compound-v3-phase0-v0/release/manifest.json` and
  `plugins/tabularium/examples/aave-v4-v0/events.jsonl`. The fixture and
  scoped-entry boundaries still equal a fresh scan. Boundary schema 2, every
  existing evidence string, and the signatures of `parse_attribute_file`,
  `match_attribute_scopes`, `match_gitattributes`, `gitattributes_rules` and
  `classify_file` are unchanged.
- `python3 plugins/horos/tests/benchmark_scope.py --root . --scope plugins/horos --runs 5`
  reports `full_tree_median_ms` at or under 1,000, recorded before and after
  the change.

**Files.** `plugins/horos/skills/horos/scripts/horos.py`,
`plugins/horos/tests/test_readable_families.py` (new),
`.horos/boundary.json`, `.horos/candidates.json`, `.horos/census.json`.
**Tests.** New module `plugins/horos/tests/test_readable_families.py`; existing
Horos tests are unchanged.
Elenchus command: `python3 plugins/horos/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`
**Disciplines.** phylax: attribute files and family names come from untrusted
trees, so the 64 KiB attribute cap, the symlink refusal and fail-open decoding
stay, nothing is executed, and test subprocesses drop every `GIT_*` variable
(study section 9). ephoros: no on-call signal; the split evidence string is the
reader's signal (study section 8). metron: the 1,000 ms whole-tree budget is
measured before and after (study section 10). elenchus: each family guard fails
by assertion against the starting classifier (study section 11). hypomnema:
the reason for the precedence and the four names sits in a comment above the
resolution code and the family constant (study section 12).

## Step 3: Guard every committed boundary and extend the example

**Goal.** Hold every committed boundary to keeping family files readable, and
show both readable routes in the shipped fixture.
**Entry.** Step 2's exit tree.
**Exit.** The command below exits 0 and reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1383-horos-33-evidence-files-readable-by-rule --scope root --scope horos --format json
```

- `plugins/horos/tests/test_committed_family_retention.py` reads every
  `.horos/boundary.json` that `git ls-files` lists and fails when a hard entry
  covers a tracked family-named file that Git does not resolve set. It checks
  the five frozen copies under `plugins/horos/docs/evidence/` by entry path. A
  mutation case shows it failing when such an entry is added to a boundary copy.
- `plugins/horos/examples/fixture/out/` holds `statement.json` beside enough
  single-line bundles to corroborate `out/`. `plugins/horos/examples/fixture/releases/`
  holds a checksum file kept readable by an unset line under a set pattern,
  beside an archive part the set pattern still excludes. The fixture's existing
  entries and candidates stay byte-identical, and its three `.horos` artefacts
  are regenerated.
- `plugins/horos/examples/README.md` documents both routes and the mutation of
  study section 1: appending a line that sets `linguist-generated` on the
  checksum file makes `horos.py check plugins/horos/examples/fixture` exit 1
  and name the covering entry, and restoring `.gitattributes` returns exit 0.

**Files.** `plugins/horos/tests/test_committed_family_retention.py` (new),
`plugins/horos/examples/fixture/.gitattributes`,
`plugins/horos/examples/fixture/out/` (new),
`plugins/horos/examples/fixture/releases/` (new),
`plugins/horos/examples/fixture/.horos/boundary.json`,
`plugins/horos/examples/fixture/.horos/candidates.json`,
`plugins/horos/examples/fixture/.horos/census.json`,
`plugins/horos/examples/README.md`, `plugins/horos/tests/test_discipline.py`
only if its rule-class assertions need the new evidence,
`.horos/boundary.json`, `.horos/candidates.json`, `.horos/census.json`.
**Tests.** New module `plugins/horos/tests/test_committed_family_retention.py`.
Elenchus command: `python3 plugins/horos/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`
**Disciplines.** phylax: the guard reads committed JSON and runs `git` with
every `GIT_*` variable removed; it executes nothing from the tree. ephoros:
none, nothing runs unattended. metron: none, no cost claim. elenchus: the
mutation case shows the guard failing on an entry that covers a family file.
hypomnema: the example README is the adopter-facing record of both routes.

## Step 4: Document the precedence, record the generation and re-pin

**Goal.** State the precedence in the skill and the README, add the generation
row, move the skill version, and re-pin the chain that binds `SKILL.md`.
**Entry.** Step 3's exit tree.
**Exit.** The command below exits 0 and reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1383-horos-33-evidence-files-readable-by-rule --scope root --scope horos --format json
```

- `plugins/horos/skills/horos/SKILL.md` rule 4 gains one sentence stating the
  precedence, placed before the `### horos-boundary-check` span, which covered
  bytes 12,450 to 13,468 at the starting commit. Its frontmatter `version`
  names the ledger's new current version. No promise's semantic fields change,
  and `No reading boundary applies during security review.` stays
  byte-identical, as does the adoption stanza in `horos.py`.
- `plugins/horos/skills/horos/EVOLUTION.md` gains exactly one row on the
  `generation` axis, and its header names the same version. The row keeps
  frontier revision `markdown-outline-extractor`, frontier SHA-256
  `7d19b7476565d3eb54bc2adb0118f1fde2d86f751819c6c5e43ba77ced7b1556`, status
  `mature` and next job `None -- mature` byte for byte, and its evidence points
  at the committed study and runbook copies. The version is fixed by the
  version-relations block above; no label is written here.
- `plugins/horos/README.md` states the precedence in its limits paragraph,
  including that readability says nothing about content.
- The same commit re-pins the agent-instruction chain with the recorded token
  counts and parity responses carried across the offset delta:
  `tests/fixtures/agent-instruction-v1/manifest.json`, the
  `horos-boundary-check` fixture's `compact.wai`, `model.json` and
  `source-spans.json`, `evidence/measurement.json`, `evidence/parity.json` and
  `tests/promise_machine_coverage.json`. No measurement, parity run, tokenizer
  or model process runs, and `tests/promise_machine_id_history.json` is
  unchanged.

**Files.** `plugins/horos/skills/horos/SKILL.md`,
`plugins/horos/skills/horos/EVOLUTION.md`, `plugins/horos/README.md`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/horos-boundary-check/compact.wai`,
`tests/fixtures/agent-instruction-v1/horos-boundary-check/model.json`,
`tests/fixtures/agent-instruction-v1/horos-boundary-check/source-spans.json`,
`tests/fixtures/agent-instruction-v1/evidence/measurement.json`,
`tests/fixtures/agent-instruction-v1/evidence/parity.json`,
`tests/promise_machine_coverage.json`, `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.
**Tests.** None written; the root suite's evolution-contract,
version-propagation, agent-instruction and Promise Machine tests are the gate.
Elenchus command: `python3 plugins/horos/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-4.json`
**Disciplines.** hypomnema: the generation row is the decision's home and the
rule 4 sentence its summary (study section 12). elenchus: a red pin test is
traced to the exact digest it names before anything is re-pinned. phylax: none,
no new boundary. ephoros: none, nothing runs unattended. metron: none, the
fixture's recorded counts are carried rather than measured.

## Step 5: Demonstrate the readable families

**Goal.** Run the study's demo path on the finished tree and record it where a
reader can check it.
**Entry.** Step 4's exit tree.
**Exit.** Each command below exits 0, and the checks runner reports outcome green:

```sh
python3 scripts/run_checks.py --base fiat/1383-horos-33-evidence-files-readable-by-rule --scope root --scope horos --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/horos/docs/evidence/skills-readable-families.md
```

- `plugins/horos/docs/evidence/skills-readable-families.md` records the demo
  path of study section 1 with exact exits: `horos.py check .` exit 0, the
  Horos suite result, `horos.py check plugins/horos/examples/fixture` exit 0,
  the appended `linguist-generated` line giving exit 1 with the drifted entry
  named, the restore giving exit 0, and the benchmark median against the
  1,000 ms budget. It ends with machine-readable capture lines in the form
  `<!-- readable:<key> <value> -->` for the tracked family-named files, those a
  root hard entry covers, and the root candidates naming one.
- `plugins/horos/tests/test_evidence.py` gains one test that recomputes those
  capture values from the committed tree and requires the covered and candidate
  counts to be 0.

**Files.** `plugins/horos/docs/evidence/skills-readable-families.md` (new),
`plugins/horos/tests/test_evidence.py`, `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.
**Tests.** One test in `plugins/horos/tests/test_evidence.py` binds the bundle's
capture lines.
Elenchus command: `python3 plugins/horos/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-5.json`
**Disciplines.** hypomnema: the bundle is the demonstration's record, bound by a
test. metron: the benchmark median is recorded against the 1,000 ms budget.
phylax: none, no new boundary. ephoros: none, nothing runs unattended.
elenchus: none, no failure in hand.
