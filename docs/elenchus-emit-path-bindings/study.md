# Study: Elenchus binds guard.test and repair.files to emit-path evidence

Topic: `Elenchus binds guard.test and repair.files to emit-path evidence`.
Task issue: [skills#1318](https://github.com/wildcat-finance/skills/issues/1318).
Starting ref: `944277d7d60d25e52110bb82115804695307d3d3` on `main`.

## Assumptions

Proceeding on these unless corrected.

1. The interpreter is the exact version in `.python-version`, `3.14.6` at the
   starting ref, and the emitter stays standard-library only.
2. The axis is generation. `elenchus-v1.4.0` becomes `elenchus-v1.5.0`; the
   frontier revision `observed-failure-root-cause`, its digest
   `08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b`,
   `Frontier status: mature` and `Next Fiat job: None -- mature` are retained
   byte for byte, as rows `elenchus-v1.2.0` to `elenchus-v1.4.0` did.
3. `Fiat-Required: 1` on the issue is authoritative. The run owes the ledger
   row and, because `SKILL.md` changes, the Hexaemeron package re-pin from
   `1.6.26` in the six places the #1275 run established.
4. The issue's shape and boundary are the design: one emit-path rule per
   field, neither decided by `--check`. The design record below holds three
   rejected constructions against it rather than reopening the question.
5. No Solidity is in scope, so the Pashov suite and `fizz` are waived for
   every step.
6. The record schema `elenchus-fixed-and-guarded/v1`, its nine fields and its
   closed key set do not change. Both new rules read inputs the emitter
   already holds at emit time and add no field.

## 1. Problem statement

`plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py` refuses
eleven contradictions between the fields a record carries and checks two
operator-supplied fields for shape alone although it holds evidence to check
them against at emit time.

`guard.test` is read once, in `_guard_findings` at line 344, and held to
`_text` within `MAX_PATH_BYTES` and `TEST_NAME.fullmatch`. Its own `F002`
message says it "must name the regression test inside that file"; nothing
tests that. Step 3 round 2 of the #1275 run emitted a draft whose `guard.test`
was `NoSuchClass.test_this_test_does_not_exist_anywhere` at exit 0, and
`--check` read it back `clean`. The control that separates the halves: the same
record with a wrong `guard.file` is refused at `F016`.

`repair.files` is validated for shape in `_repair_findings` at line 316 and
read against `guard.file` at `F016`, but never against `result["tests"]`, the
git-derived changed test files the emitter parses at `result_findings` line
525. Step 1 round 6 of the same run, finding S1-R6-02, emitted a repair
touching `src/widget.py`, `tests/test_widget.py` and `tests/test_other.py`
with two files declared, at exit 0, and `--check` called it clean.

**What is built.** Two emit-path refusals, `F018` and `F019`, in `emit()`,
each checked where the emitter already holds the evidence; the boundary
between the emit path and `--check` stated wherever the refusals are
documented; one `generation` ledger row.

**For whom.** Whoever emits a record: Mason when implementation breaks, Warden
inside an audit round, a person at a terminal. And whoever reads `clean` from
`--check` and needs to know what it excludes.

**What a working prototype means here.** Against a scratch repository with a
real repaired failure, the two hostile drafts the #1275 audit constructed are
refused at emit with the rule and the field named and no file written; the
genuine draft still emits a record `--check` accepts; every record `--check`
accepted before is accepted after, byte for byte in behaviour.

**Demo path.** The last step runs both refusals end to end in the shape
`EndToEnd.test_the_demo_path_emits_a_record_and_refuses_the_ones_it_should`
already runs the acceptance:

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py \
  --draft inputs/guard-test-absent.json --result inputs/result.json \
  --out records/guard-test-absent.json      # exit 1, F018 guard.test
python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py \
  --draft inputs/repair-files-short.json --result inputs/result.json \
  --out records/repair-files-short.json     # exit 1, F019 repair.files
python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py \
  --check records/fixed-and-guarded.json    # exit 0, clean
```

**Success criteria.** Each names a command.

1. A draft whose `guard.test` names no test in the guard file's bytes at the
   repair commit is refused `F018 guard.test` at exit 1 with no file written:
   a named case in `plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py`,
   run by `python3 -m unittest plugins.hexaemeron.tests.test_elenchus_fixed_and_guarded`.
2. A draft whose `repair.files` omits any path in `result["tests"]` is refused
   `F019 repair.files` at exit 1 with no file written: a named case in the
   same module.
3. `--check` is byte-identical in behaviour for existing records: every
   `--check` case in the module at the starting ref passes unedited, proved by
   `git diff --numstat 944277d7d60d25e52110bb82115804695307d3d3..HEAD -- plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py`
   reporting zero deleted lines, and by one new case asserting that a record
   carrying an unbound `guard.test` and a short `repair.files` still reads
   `clean` under `--check`, which is the stated boundary and not a defect.
4. The genuine draft still emits, and the emitted record validates:
   `EndToEnd` passes and the demo path's third command exits 0.
5. `elenchus.py` is unchanged: `git diff 944277d7d60d25e52110bb82115804695307d3d3..HEAD -- plugins/hexaemeron/skills/elenchus/scripts/elenchus.py` is empty and
   `python3 -m unittest plugins.hexaemeron.tests.test_elenchus_checker` passes.
6. The ledger row is a generation row: `python3 -m unittest plugins.hexaemeron.tests.test_evolution` passes and
   `python3 .hexaemeron/reports/resolve.py frontier-retained-byte-for-byte`
   reports `True`.
7. The root check graph is green:
   `python3 scripts/run_checks.py --base origin/main` exits 0 on the committed
   tree.
8. Every shipped document scores no defect:
   `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <file>`.

## 2. Prior art

### In this repository

`fixed_and_guarded.py`, 790 lines at the starting ref, is the whole subject.
Where the four values this run binds are read:

| Value | Read at | Rule today |
| --- | --- | --- |
| `guard.file` | `_guard_findings` line 340; `emit` line 700 (`F007`, against `result["tests"]`); `_relation_findings` line 416 (`F016`, against `repair.files`) | bound on both paths |
| `guard.test` | `_guard_findings` line 344 | shape: printable, at most 512 bytes, matches `TEST_NAME` |
| `repair.files` | `_repair_findings` line 316; `_relation_findings` line 416 | shape: 1 to 256 relative paths; contains `guard.file` |
| `result["tests"]` | `result_findings` line 525; `emit` line 700 | shape: 1 to 256 relative paths; contains `guard.file` |

`TEST_NAME` at line 97 is
`^[A-Za-z_][A-Za-z0-9_]*(?:[.:][A-Za-z_][A-Za-z0-9_]*)*$`: one or more ASCII
identifier segments joined by `.` or `:`. It admits a Python
`Class.test_method`, a Forge `Contract:testMethod`, a bare `test_method`, and a
module-qualified `tests.test_widget.Class.test_method`.

Eighteen codes ship, `F000` to `F017`, listed in the module docstring. `F000`
to `F006`, `F008` and `F009` refuse inputs, derivation and the destination.
`F007` and `F010` are emit-path rules that read the result against the draft
and the repository. Eleven of the eighteen are, by `SKILL.md`'s own count, the
carried-field enumeration `--check` decides; `record_findings` at line 456 is
the only function `check()` calls.

`emit()` runs, in order: `read_json` on both inputs (`F000`); `draft_findings`
and `result_findings` (`F002` to `F006`); `F007`; `commit_and_parent` (`F008`);
`F010`; `compose`; `record_findings`; `prepare_output_path` and `write_staged`
(`F009`). The emit path starts two fixed-argv `git` subprocesses:
`git rev-parse <ref>^{commit} <ref>^` and `git ls-files --error-unmatch -- <path>`.

`elenchus.py` derives `tests` in `changed_tests` at line 67:
`git diff-tree --no-commit-id --name-only --diff-filter=AM -r <ref>`, filtered
by `is_test` at line 60, sorted. It overlays each such file onto the detached
parent with `git show <ref>:<path>` at line 301. So a path in `result["tests"]`
names a blob that exists at the fix commit, and `repair.files` is the draft's
claim about the same commit's changed files.

`plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py`, 970 lines, 55
tests: a `Fixture` class building a real two-commit repository, a `Scratch`
class with a real defect, `draft_for` and `result_for` builders, one class per
refusal family, and `EndToEnd` driving the demo path through subprocesses.
`GuardBinding` is where `F018` cases belong; `RecordRelations` and
`GuardBinding` already pair an emit-path case with its `--check` counterpart,
which is the shape a boundary case follows.

`docs/elenchus-fixed-and-guarded-record/study.md`, section 11 as amended
2026-09-05, states the carried-field rule with a closed enumeration: a record
is refused when the fields it already carries contradict the Promise's
Evidence or Boundary clauses, decided only from those fields. Adding a member
takes an amendment to that study. Neither rule here is a member: `guard.test`
needs the guard file, `repair.files` needs `result["tests"]`, and the record
carries neither. This run adds a second family, emit-path rules beside `F007`
and `F010`, and leaves the enumeration at eleven.

`docs/elenchus-fixed-and-guarded-record/demonstration.md`, section
`## What this run does not establish`, says the emit path adds four things
`--check` cannot and that `guard.test` "is checked for shape alone". Both
sentences become false when step 1 lands, so step 2 rewrites that section.

### The last two merged pull requests that changed the subject

[PR #1321](https://github.com/wildcat-finance/skills/pull/1321), merged
2026-09-06, is the #1275 run's integration; [PR #1317](https://github.com/wildcat-finance/skills/pull/1317),
merged 2026-09-06, is its step 3. `git log --oneline -- plugins/hexaemeron/skills/elenchus/`
finds nothing later. PR #1321's `carryover` block carries eight items:

1. `guard-test-unbound`, filed as #1318. Answered here: `F018`.
2. `repair-files-unbound`, duplicate of #1318. Answered here: `F019`.
3. `plugin-version-collision`, filed as
   [#1319](https://github.com/wildcat-finance/skills/issues/1319), `OPEN`.
   Stays open; this run applies its mitigation. The re-pin number is a
   checked property: a scan of all 253 `origin` refs at the starting ref found
   `1.6.26` on `main` and this run's branch and nothing above it, so `1.6.27`
   is free now and is re-checked before the integration push.
4. `run-documents-drift`, filed as
   [#1320](https://github.com/wildcat-finance/skills/issues/1320), `OPEN`.
   Stays open; step 3's exit re-runs `cmp` on both committed copies.
5. `emitter-docstring-drift`, "repaired by whoever takes that job". Carried
   forward: step 1 corrects `result_findings`'s docstring, which says four
   values are read where five are, and `F007`'s message, which says the guard
   "names a test" where the field read is `guard.file`.
6. `skill-section-establishes-claim`, none. Refused: register choice, three
   rounds found no wrong belief.
7. `study-path-not-portable`, none. Refused: the package test passes and the
   inline path is not a link.
8. `demonstration-has-no-pointer`, none. Refused: step 2 adds a pointer only
   because it rewrites the section the pointer would sit beside; the item
   itself stays a non-defect.

PR #1317's body names `guard.test` as the one field no rule binds and says
closing it edits the file that step's exit froze. Answered here.

### Audit records read

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exits 0 at the starting ref with every reported source `committed=match`, so a
verified synopsis is the normal reading view.

In scope is the one skill this run changes, Elenchus, whose records are the
per-run file the #1275 run wrote and the plugin record its directory sits
under. The other 123 files under `audit/rounds/` belong to deliveries this run
neither changes nor reads.

| In-scope source | Read | Evidence for the choice |
| --- | --- | --- |
| `audit/rounds/fiat-1275-elenchus-emits-the-fixed-and-guarded-result.md` | synopsis `audit/rounds/fiat-1275-elenchus-emits-the-fixed-and-guarded-result.synopsis.md`, grepped for headings, verdicts, finding rows, `guard.test`, `repair.files` and `Leads not pursued` | `committed=match`, `h2_count=11`, source SHA-256 `35a2cebbaa34a2b46c1edd82918dd13eccc62f6f669652a89dc6e798bb35ef8a`; the two leads this run closes are quoted in full there |
| `plugins/hexaemeron/audit/AUDIT.md` | synopsis `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` | `committed=match`; both rounds are Step 0 plugin rounds on `hexctl.py` and `hook_gate.py` |

Retained from the #1275 record: eleven rounds, 29 findings `S1-R1-01` to
`S3-R1-01`, every one `fixed` except `S1-R4-03` and `S1-R6-02`, which are the
two this run closes. Elenchus verdicts by round: `passed`, then `guarded` for
step 1 rounds 2 to 6, `unguarded` for step 2 rounds 1 to 3 and step 3 round 1,
`null` at step 3 round 2. Every risk id was `reviewed` except `frontier-drift`
in step 1, `not-applicable`. `S1-R6-02` is the `repair.files` lead, `low`,
left open as an emit-path rule "too large to add at its own round six". The
`guard.test` demonstration is in `S3-R1-01`'s finding text, `low`, fixed in
the document alone at `f760622dc32af1b2ffa4ea567220ee803d062bec`. Standing
leads carried across those rounds and untouched here: issue 453's report-byte
binding; whether issue 1222's producer adopts the key names; `repair.files`
and `fixed_tree.report` being operator assertions never checked against a
rerun, of which this run closes the `repair.files` half against
`result["tests"]` and leaves `fixed_tree.report` alone. The plugin record's ten
findings `F-01` to `F-10`, nine `fixed` and `F-10` `accepted`, predate the
schema, so `Covered`, `Not checked` and `Elenchus verdict` read
`[missing legacy field: ...]` and stay unknown.

### In the organisation

[skills#1275](https://github.com/wildcat-finance/skills/issues/1275), `CLOSED`
by PR #1321, is the producer this run tightens. [skills#1222](https://github.com/wildcat-finance/skills/issues/1222)
and [skills#453](https://github.com/wildcat-finance/skills/issues/453) are
`OPEN` and unaffected: neither reads `guard.test` or `repair.files`.

### Outside the organisation

`git diff-tree --name-only` is the mechanism `result["tests"]` already comes
from, and `git cat-file` reads a blob at a commit without touching the
worktree; both are documented in `git-diff-tree(1)` and `git-cat-file(1)`.
Reading the blob at the commit rather than the worktree file is the same
choice `elenchus.py` makes with `git show <ref>:<path>`, so `F018` reads the
bytes the comparison overlaid.

## 3. Constraints and non-goals

### Constraints

1. Starting ref `944277d7d60d25e52110bb82115804695307d3d3`, branch
   `fiat/1318-elenchus-binds-guard-test-and-repair-files`, base `main`.
2. Python `3.14.6` from `.python-version`, standard library only, stdlib
   `unittest`.
3. The generation axis of `plugins/hexaemeron/skills/VERSIONING.md`. Row
   `elenchus-v1.5.0` retains the frontier revision, digest, `mature` and
   `None -- mature` byte for byte; `SKILL.md` frontmatter moves to `1.5.0`.
   The runbook carries no `version-relations` block, so the token is literal,
   as the three previous generation rows were.
4. Hexaemeron re-pins from `1.6.26` to `1.6.27` in six places:
   `plugins/hexaemeron/.claude-plugin/plugin.json`,
   `plugins/hexaemeron/.codex-plugin/plugin.json`,
   `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
   `tests/test_version_propagation.py` line 47 and
   `plugins/hexaemeron/tests/test_phylax_model_proxy.py` line 5679. The number
   must exceed every hexaemeron version claimed by any local or remote ref and
   is re-checked immediately before the integration push; a collision moves
   all six to the next free number.
5. `elenchus.py`, `test_elenchus_checker.py` and every existing case in
   `test_elenchus_fixed_and_guarded.py` are unchanged.
6. The record schema, its nine fields, the closed key sets, `F000` to `F017`
   and their messages are unchanged, except the two docstring corrections
   item 5 of the carryover names.
7. No Solidity; the Pashov suite and `fizz` are waived on every step.
8. The root suite is `python3 scripts/run_checks.py --base origin/main`, run
   on the committed tree. Per-step audit rounds use
   `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
   the runner whose discovery root contains the emitter's module.

### Non-goals

1. `--check` does not decide either binding. It opens no repository and reads
   no result, before or after this run.
2. Nothing verifies that the named guard fails on the parent. The verdict and
   `unfixed_parent.report` already carry `elenchus.py`'s account; `F018`
   establishes that the name occurs in the file, not that the runner
   collected it.
3. What an emitted record establishes does not change. `clean` still means
   internal coherence.
4. No twelfth carried-field member, no schema `v2`, no new record field.
5. No change to `elenchus.py`, its adapters, or its `tests` derivation.
6. `fixed_tree.report` stays an operator assertion.

### Explicit unknowns

1. Whether another run re-pins Hexaemeron to `1.6.27` before this one
   integrates is unknowable now; constraint 4's re-check is the control.
2. Whether a guard file under `forge-junit-v1` or `node-test-json-v1` names
   its test as one `TEST_NAME` token is the operator's choice; `F018` reads
   whatever segments the operator supplied.

## 4. Design options

Four constructions were compared. The prose explains each; the selection is
made by `.hexaemeron/design-evidence.json` from checked gates and measured
values.

### Candidate `emit-path-rules`

Two refusals in `emit()`. `F019 repair.files` runs directly after `F007`, from
the same two inputs: every path in `result["tests"]` must be in
`repair.files`, compared as exact strings, both lists having already passed
`_relative_path` so no `.`/`..`/empty segment, backslash, root or drive
survives to compare. The message names every missing path. `F018 guard.test`
runs after `F010`, once the result's ref has resolved to `repair.commit`: the
emitter reads the blob `<repair.commit>:<guard.file>` with
`git cat-file -s` then `git cat-file blob`, refuses a blob over
`MAX_INPUT_BYTES`, splits `guard.test` on `[.:]`, and requires each segment to
occur in the bytes as a whole word, `(?<![A-Za-z0-9_])segment(?![A-Za-z0-9_])`
over bytes. The message names the first segment absent. Neither reaches
`check()`.

The trade: whole-word occurrence, not a parsed definition. A name that occurs
only in a comment passes; a module-qualified name whose module segments do not
occur in the file is refused, and the operator drops the prefix. Against that,
one rule covers all three runner formats `elenchus.py` accepts, where an
`ast.parse` of the guard file would bind Python only and refuse every Forge or
Node guard. Two more fixed-argv `git` subprocesses on the emit path, four in
all.

### Candidate `carried-field-members`

Widen the record to a `v2` that carries the compared test files, so both
bindings become carried-field members and `--check` decides them. The trade:
`--check` refuses every existing `v1` record at `F001`, and `guard.test` is
still undecidable from the record, because the guard file is not in it.

### Candidate `check-time-repository-read`

`--check` gains `--repo`, opens the repository, reads the guard file and
re-runs `git diff-tree` for the changed test files. The trade: `--check` stops
being a read of the record alone, which the issue's boundary excludes, and a
record arriving without its repository is refused or unchecked rather than
clean.

### Candidate `separate-verifier-script`

A new script reads a written record with its draft and result and reports the
two bindings; the emitter is unchanged. The trade: the hostile draft still
emits at exit 0 and the record exists afterwards, so the verifier reports a
defect it cannot unwrite.

### The record

`.hexaemeron/design-evidence.json` holds four candidates, eight criteria and
the complete 32-cell matrix under `protasis-design-evidence/v1`. Five criteria
are selection evidence, resolved; three are conformance evidence, pending
against `step:2` and `integration`.

Resolved by `python3 .hexaemeron/reports/resolve.py <criterion>` at the
starting ref, on this host:

| Criterion | `emit-path-rules` | `carried-field-members` | `check-time-repository-read` | `separate-verifier-script` |
| --- | --- | --- | --- | --- |
| `refused-at-emit` (= true) | true | false | true | false |
| `check-path-unchanged` (= true) | true | false | false | true |
| `refusal-leaves-no-record` (= true) | true | true | true | false |
| `published-surface-bytes` (min) | 6359 | 10152 | 6359 | 6359 |
| `obliged-existing-suite-ms` (min) | 14810 | 14810 | 14810 | 287 |

Each rejected candidate fails one selection gate and leaves the frontier
before any measurement is weighed, so the frontier holds one candidate and the
rule is `unique-frontier`. The three gates are the issue's own boundary read
as conditions: both drafts refused before a write, `--check` unchanged, and no
accepted file left behind a refusal.

The three gate enumerations are declared from each candidate's stated shape
and bound by `resolve.py` to two sentences in `SKILL.md`: the `--check`
definition at line 354 and the `guard` row of the field table. The script
refuses to write a report when either sentence has left the tree.

`published-surface-bytes` sums the already-published sections each candidate
must rewrite: `## Emit the result as a record` in `SKILL.md`, 4533 bytes, and
`## What this run does not establish` in the #1275 demonstration, 1826 bytes,
for every candidate; `carried-field-members` also rewrites `## Decision` in
the numberless #1275 decision draft, 3793 bytes.

`obliged-existing-suite-ms` times the existing modules bound to the files each
candidate changes, once each on this host: the emitter suite 13981 ms,
`test_evolution` 82 ms, the Imprimatur lint on `SKILL.md` 192 ms. Three
candidates edit the emitter and owe all three; the verifier owes the last two.
This host is a 2026 Darwin 25.5.0 machine reporting 18 CPUs; the values are
host-bound and the ordering is not close.

## 5. Risk register seed

```risk-register
guard-test-unbound | guard.test against the guard file's bytes at the repair commit | a segment absent from the blob is refused F018 at emit and no file is written; the blob is read at repair.commit, not from the worktree
repair-files-short | repair.files against result.tests | a result.tests path absent from repair.files is refused F019 at emit with every missing path named; the converse direction is not a rule
check-path-drift | --check on a record that already exists | check() still calls record_findings alone, every existing --check case passes unedited, and one case asserts an unbound guard.test and a short repair.files still read clean
blob-read-bounded | the guard file blob the emitter reads | git cat-file -s is read first and a blob over MAX_INPUT_BYTES is refused before git cat-file blob runs; both calls are fixed argv with no shell
git-argv-injection | the guard.file and repair.commit values that reach git argv | guard.file has passed _relative_path and is joined after a 40-or-64-hex commit and a colon, so no operand can begin with a dash
partial-record-write | the emitter's output path during a write | unchanged: staged and renamed; a refusal from F018 or F019 happens before prepare_output_path and creates no directory
refusal-order | the position of F018 and F019 in emit() | F019 runs after F007 from the same inputs; F018 runs after F010 so the blob read names the commit both halves agree on; a malformed input never reaches either
frontier-drift | the elenchus EVOLUTION.md row this run adds | the frontier revision, digest, status and next job are byte-identical to elenchus-v1.4.0 and test_evolution passes
package-repin-collision | the hexaemeron version in six files | 1.6.27 exceeds every version on every local and remote ref, re-checked before the integration push
checker-interface-drift | elenchus.py and test_elenchus_checker.py | both files are byte-identical to the starting ref
docs-copy-drift | the committed study and runbook copies under docs/ | cmp against the controller artefacts at step 3's exit; issue 1320 owns the check that does not yet exist
```

## 6. Glossary seeds

- **Emit-path rule.** A refusal decided from evidence the emitter holds only
  at emit time, the draft against the result or the repository. `F007`,
  `F010`, `F018` and `F019` are the family; `--check` runs none of them.
- **Carried-field member.** One of the eleven refusals `--check` decides from
  the record's own fields, under the #1275 study's closed enumeration.
- **Guard file blob.** The bytes of `guard.file` at `repair.commit`, the same
  bytes `elenchus.py` overlaid onto the parent.
- **Segment.** One `[A-Za-z_][A-Za-z0-9_]*` run of `guard.test`, split on `.`
  or `:`.
- **Whole-word occurrence.** A segment found in the blob with no identifier
  byte on either side.
- **Generation row.** An `EVOLUTION.md` row that changes behaviour and retains
  the prior frontier revision and digest byte for byte.

## 7. Sources

1. `plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py` at
   `944277d7`, lines 11 to 31, 97, 316, 336 to 349, 456 to 481, 498 to 556,
   679 to 751.
2. `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py` at `944277d7`,
   `TEST_NAMES` line 27, `is_test` line 60, `changed_tests` line 67, the
   overlay at line 301.
3. `plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py` at
   `944277d7`, classes `Fixture`, `Scratch`, `GuardBinding`,
   `RecordRelations`, `EndToEnd`.
4. `plugins/hexaemeron/skills/elenchus/SKILL.md`, `## Emit the result as a
   record` and the `### elenchus-fixed-and-guarded` contract.
5. `plugins/hexaemeron/skills/elenchus/EVOLUTION.md`, rows `elenchus-v1.2.0`
   to `elenchus-v1.4.0`; `plugins/hexaemeron/skills/VERSIONING.md`.
6. `docs/elenchus-fixed-and-guarded-record/study.md` section 11 and its five
   amendments; `runbook.md` amendments of 2026-09-06 on the six-place re-pin;
   `demonstration.md` `## What this run does not establish`.
7. `docs/decisions/drafts/emit-the-fixed-and-guarded-result-as-a-closed-record.md`.
8. `audit/rounds/fiat-1275-elenchus-emits-the-fixed-and-guarded-result.synopsis.md`,
   findings `S1-R4-03`, `S1-R6-02`, `S2-R2-02`, `S3-R1-01`.
9. [skills#1318](https://github.com/wildcat-finance/skills/issues/1318),
   [skills#1319](https://github.com/wildcat-finance/skills/issues/1319),
   [skills#1320](https://github.com/wildcat-finance/skills/issues/1320);
   [PR #1321](https://github.com/wildcat-finance/skills/pull/1321) and
   [PR #1317](https://github.com/wildcat-finance/skills/pull/1317) bodies.
10. `AGENTS.md`, the check graph and `scripts/run_checks.py`;
    `plugins/hexaemeron/tests/run_tests.py --elenchus-report`.
11. `git-cat-file(1)` and `git-diff-tree(1)`.

## 8. Signals, and the questions behind them

The emitter runs once at a terminal or inside an audit round, holds no state
and runs nothing unattended, so it has no alert and no metric. Two questions
remain, both answered by what it prints rather than logs.

1. *Why was this draft refused, and which value was wrong?* Answered by the
   refusal line: `F018 guard.test: <segment> does not occur in <file> at
   <commit>` or `F019 repair.files: omits <paths> from result.tests`. Emitted
   by step 1, covered by its named cases.
2. *This record reads clean; which bindings did that check?* Answered by the
   documentation, not the record: `--check` ran none of the emit-path family,
   and a record carries no evidence of which path produced it. Step 2 states
   that where the refusals are listed.

`plugins/hexaemeron/skills/ephoros/SKILL.md` owns what a signal must carry;
its condition, an unattended path nobody can reconstruct, is absent.

## 9. Boundaries, per capability

`plugins/hexaemeron/skills/phylax/SKILL.md` owns the boundary list and the
controls. Two boundaries open here, one widens.

1. **Reading the guard file blob.** A new read of repository bytes chosen by
   two draft values. Worth taking: a name bound to bytes the comparison used.
   Controls: the commit is the one `git rev-parse` returned and `F010`
   matched to the draft, the path has passed `_relative_path`, the two
   `git cat-file` calls are fixed argv with no shell, `-s` bounds the read to
   `MAX_INPUT_BYTES` before `blob` runs, and the bytes are searched, never
   decoded as code, executed or printed.
2. **Comparing two path lists.** `result["tests"]` against `repair.files`,
   both already bounded to 256 relative paths. Control: exact string
   comparison after the same normalisation rule; no filesystem read.
3. **The refusal message.** It now carries a segment of `guard.test`, a path
   and a commit, all values that passed the printable-text rule; no blob
   bytes reach stderr.

The write boundary, the draft and result reads and the reproduction-output
digest are unchanged. No network, no dependency.

## 10. The budget, or its absence

No budget. The emit path gains two `git cat-file` reads bounded by 1 MiB and
one set comparison over at most 256 strings; `--check` gains nothing. The
baseline a later run would declare against is
`python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py --draft ... --result ... --out ...`
timed over the scratch repository. `plugins/hexaemeron/skills/metron/SKILL.md`
owns what a budget carries; nothing here changes `elenchus.py`, where the
expensive work is. The design record's `obliged-existing-suite-ms` values are
selection evidence, not a budget.

## 11. The fail-closed posture

What stops the run: any refusal exits 1, names its code and field on stderr,
and writes nothing. `F018` and `F019` refuse before `prepare_output_path`, so
no directory is created for a refused draft. A blob that cannot be read, is
over the cap, or is not a blob is refused `F018` rather than skipped.

Two rule families now exist, and the boundary between them is part of the
posture. The carried-field enumeration of the #1275 study stays closed at
eleven and is what `--check` decides. The emit-path family, `F007`, `F010`,
`F018`, `F019`, is decided only with the producer's inputs and repository, and
`--check` on a record arriving without them cannot decide any of the four.
`clean` therefore excludes them by construction, and every place the refusals
are listed says so: the module docstring, `## Emit the result as a record`,
and the #1275 demonstration's boundary section.

The guard-test convention every fix in this delivery follows is Elenchus's
own: the test fails on the old code, passes on the new, is run against the
unfixed tree first, and is named after the failure. Each new case here is that
shape by construction: the hostile drafts emitted at exit 0 at the starting
ref. Audit rounds use the runner contract each runbook step declares. Because
the skill under change is Elenchus, `test_elenchus_checker.py` is left alone
so the classifier the guard check depends on is never modified beside a guard
that depends on it. `plugins/hexaemeron/skills/elenchus/SKILL.md` owns the
triage order and the guard rule.

## 12. Decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` owns which decisions earn a
record and where each lives. None here earns a new decision record, and each
has a named home.

1. **Emit-path rules are a second family, never carried-field members.** This
   follows from the issue's boundary and from the nine-field shape the
   numberless #1275 draft at
   `docs/decisions/drafts/emit-the-fixed-and-guarded-result-as-a-closed-record.md`
   already fixes: reversing it means a `v2` schema, which is that record's
   decision to supersede. Home: `## Emit the result as a record` in
   `SKILL.md` and the module docstring, where the boundary is read.
2. **Whole-word occurrence is what "names the test inside that file" means.**
   Cheap to reverse: tightening it later refuses more drafts and touches no
   existing record, because `--check` never reads it. Home: the `F018`
   docstring and the skill section.
3. **The generation row.** The ledger's own record; not an ADR.

## Boundaries this study states

**Always.** `python3 scripts/run_checks.py --base origin/main` on the
committed tree before a commit is pushed;
`python3 -m unittest plugins.hexaemeron.tests.test_elenchus_fixed_and_guarded`
before every commit touching the emitter;
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` on every
shipped document; every new case seen red at the starting ref before it is
kept.

**Ask first.** Adding a dependency. Changing `elenchus.py`, its flags or its
four states. Adding a record field or a carried-field member. Changing a
refusal message `F000` to `F017` beyond the two carryover corrections.
Touching CI.

**Never.** Commit an RPC credential or key material. Edit an existing audit
record. Delete or weaken an existing test case. Print blob bytes on stderr.
Claim a command ran when it did not.
