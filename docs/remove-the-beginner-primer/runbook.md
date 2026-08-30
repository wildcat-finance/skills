# Runbook: remove the beginner primer and its generator

Derived from the receipted study at `.hexaemeron/study.md`, sha256
`2cfc803c15640541608e9d8e9c42942e3a711906732a5e9a321360a488f3dedb`. The run
starts at `840d8dd3596fd6394901ba85a693bea00c69bf25` on run branch
`fiat/975-remove-the-child-or-golden-retriever-primer`.

## Why there is one step

The study settles this in section 4 and the runbook carries the reasoning
rather than re-deriving it. `require_baseline_publication` at
`scripts/dead_code.py:3722-3760` requires `git diff --name-only source..HEAD`
to equal exactly `{".dead-code/baseline.json"}`, so a baseline may only be
published in a commit that changes nothing else. At the removal commit that set
also holds the fifteen deleted paths, `README.md` and the decision records, so
`dead_code.py baseline --check` refuses there with `baseline is stale; source
changed after publication`. The removal commit is red for the dead-code scope by
construction. A step must be green at both ends, so removal and republication
cannot be two steps. They are two commits inside one step, and the step's exit
runs at the tip where both gates pass. The precedent commit `38345929` on the
base has the same two-commit shape.

Option A, one commit, is impossible for the same reason. Option D, three steps
with the records first, would mark `ADR-039` superseded and add a record saying
the primer was removed while the primer still sat in the tree, and would triple
the audit loop for one boundary.

## Shared obligations

These hold for every command and every commit in this run.

**`TMPDIR` must resolve to a real path.** The host default sits under
`/var/folders`, `/var` is a symlink, and several suites refuse a path with a
symlinked lexical parent. Export `TMPDIR` to something under `/private/tmp`
before the first command. This is a property of the host, not a defect in the
repository; three audit records, `fiat-390`, `fiat-557` and `fiat-774`, already
record it. A suite failure observed without this set is not evidence about the
change.

**`run_checks.py` exit status is not its verdict.** Read the `outcome` line.
`unstable-source` sets exit 3 independently of what the checks found, and the
study reproduced `outcome red` at exit 0 while measuring the current tree. A
green exit status with a red outcome is a failure.

**Scope selection.** `scripts/run_checks.py` unions the requested scopes with
the observed diff, then closes over consumers. `--base <ref>` adds
`git diff --name-only <ref>..HEAD` to the observed set; without it, a clean
tip at this step reports `changed 0 path(s)` and selects nothing, which is why
the exit passes the base explicitly. Ownership is by directory in
`tests/check-map-v1.json`: `README.md`, `audit/`, `scripts/`, `tests/` and
`.horos/boundary.json` belong to `root`; `docs/` to `docs`;
`.dead-code/baseline.json` to `dead-code`. The dependency closure adds
`repo-lints`. Selecting from this step's diff yields four scopes, `dead-code`,
`docs`, `repo-lints` and `root`, and five checks: `dead-code-suite`,
`lint-ephoros`, `lint-hypomnema`, `lint-phylax`, `root-suite`. Verified by
driving `build_selection` with this step's exact path list.

**The Horos scan runs after `git add`.** `horos.py` scans with
`git ls-files -z --cached --others --exclude-standard`. `--cached` reads the
index, so an unstaged deletion is still counted and the boundary comes out
describing files that are on their way out. Stage the deletions first, scan
second, stage `.horos/boundary.json` into the same commit.

**Re-confirm the decision-record number before writing the record.**
`origin/main`'s highest record is `ADR-058`, but
`origin/fiat/936-report-dead-code-baseline-staleness-instead` already carries
`ADR-059` at commit `6a7baf1a`, so this run allocates **`ADR-060`**. Verified
directly against a fetched `origin/main` and against that branch's tree. Run
`git fetch origin` and re-read `docs/decisions/` on `origin/main` immediately
before the record file is created. A collision found at integration means
renumbering the file, its heading and every reference to it. It never means
reusing a number quietly.

**The superseded status is a house convention, not a checked one.**
`tests/test_decision_records.py` checks the filename pattern, number uniqueness
within the tree, agreement between filename and first heading, and
non-collision with `origin/main`. It never reads the status line. Follow
`ADR-011` and `ADR-038`: `## Status` becomes `Superseded, <date>.`, then a
Markdown link to the superseding record and one sentence saying what it retains
and what it replaces. Everything from `## Context` down is untouched.

**Historical records are left alone.** Nine surviving documents and four audit
records from other runs cite the primer as evidence for decisions taken at the
time. They keep saying what they said. That includes
`plugins/hexaemeron/docs/fiat-author-publisher-separation/runbook.md:17`, whose
`Files` line names the primer study and the builder: it is a delivery record of
the same class, so it stays. Its `.agents/` mirror is byte-identical, so the
portable sync over an unchanged source is a no-op and the mirror needs no
action. `python3 scripts/portable_promise_machine.py check` is clean at the
base and stays clean.

**`tests/check-map-v1.json` needs no edit.** Ownership is by directory, no
per-file `owners` entry names either primer file, and no scope becomes newly
empty: `root` keeps 38 other test modules. Five scopes already carry zero
checks, so an empty scope is a normal state in that manifest rather than
something this change could introduce.

**Commits.** Each commit uses the repository's configured identity with the
author overridden:

```bash
GIT_AUTHOR_NAME="Shoggoth" GIT_AUTHOR_EMAIL="shoggoth@wildcat.finance" \
  git commit -F <message file>
```

Committer and signer come from config, `Dr Laurence E. Day` and key
`B83B60AE16F5DD1A`, with `commit.gpgsign` already true. Each message ends with
exactly one `Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` line and
exactly one `Wildcat-Origin: shoggoth` line, and nothing after them. Nothing
under `.hexaemeron/` is ever staged.

**What stops the run.** Any exit-command failure, plus two failures that read
as success and are refused by name: a red `outcome` under a zero exit status,
and a suite failing for `TMPDIR` reasons rather than for what this change did.
The current error in `tests/test_child_or_golden_retriever_primer.py` is not a
failure to triage. It is the subject, and removing the file removes it.

## Step 1: Remove the beginner primer and republish both manifests

**Goal.** Delete the fifteen tracked primer files, drop the three `README.md`
links without replacing them, supersede `ADR-039` with a new record, and
republish the Horos boundary and the dead-code baseline so both manifests
describe the tree as it now is.

**Entry.** `840d8dd3596fd6394901ba85a693bea00c69bf25` on run branch
`fiat/975-remove-the-child-or-golden-retriever-primer`, with the study
receipted. At that ref `git ls-files` matches the fifteen paths below and
nothing else; `horos.py check .` prints `boundary matches the tree`;
`dead_code.py baseline --check` exits 0 with source `8cc85686`;
`promise_machine.py check`, `promise_machine.py coverage --check`,
`portable_promise_machine.py check` and `audit_synopsis.py --check .` all exit
0; and `python3 -m unittest discover -s tests` reports `Ran 765 tests` and
`FAILED (errors=1)`, that one error being the primer test's `setUpClass`
raising `AssertionError: deterministic primer check failed` after
`deterministic-rebuild` mismatched on
`docs/assets/a-child-or-a-golden-retriever-whos-who.png`,
`docs/assets/a-child-or-a-golden-retriever-fiat-flow.png` and
`docs/pdf/a-child-or-a-golden-retriever.pdf`. The module contributes nothing to
`testsRun`, because the class error precedes every test method, so the count
after removal is the same 765 with no error. That is why the root suite changes
colour without any test being rewritten.

**Exit.** Two commits on the step branch. The first stages the fifteen
deletions, edits `README.md`, marks `ADR-039` superseded, adds
`docs/decisions/ADR-060-remove-the-beginner-primer-and-its-generator.md`, adds
the tracked copies of the study and this runbook, then runs the Horos scan
after `git add` and stages `.horos/boundary.json`. The second republishes
`.dead-code/baseline.json` and nothing else. At the tip: no tracked path names
the primer; the boundary carries 128 entries and `bytes_binary` 43,883,426,
down from 135 and 54,685,567 by the seven `grade: hard` binaries totalling
10,802,141 bytes; the baseline sits directly on the commit it was computed
from; the `README.md` diff adds no line; `ADR-039` keeps its body; nothing
under `audit/` is modified; and every selected scope is green. Prove it with:

```bash
export TMPDIR=/private/tmp/fiat-975 && mkdir -p "$TMPDIR"
BASE=840d8dd3596fd6394901ba85a693bea00c69bf25
test -z "$(git ls-files | grep -iE 'child.or.a.golden.retriever|child_or_golden_retriever|child-or-a-golden')"
test "$(git diff --name-only --diff-filter=D $BASE..HEAD | wc -l | tr -d ' ')" = 15
test -z "$(git diff --name-only --diff-filter=D $BASE..HEAD | grep -ivE 'child.or.a.golden.retriever|child_or_golden_retriever')"
test -z "$(git diff $BASE..HEAD -- README.md | grep '^+[^+]')"
diff <(git show $BASE:docs/decisions/ADR-039-keep-one-source-for-the-beginner-primer.md | sed -n '/^## Context/,$p') <(sed -n '/^## Context/,$p' docs/decisions/ADR-039-keep-one-source-for-the-beginner-primer.md)
test -z "$(git diff --name-only --diff-filter=MRT $BASE..HEAD -- audit/)"
test -z "$(git diff --name-only $BASE..HEAD -- docs/fiat-controller-checkpoint-study.md docs/fiat-controller-checkpoint-runbook.md docs/fiat-integration-path-bound-study.md docs/fiat-integration-path-bound-runbook.md docs/fiat-step-branch-extensions-runbook.md docs/fiat-sync-run-generator-aggregates-runbook.md docs/protasis-amendment-block-check-runbook.md docs/ci-plugin-suite-gate/runbook.md docs/fiat-sync-resolution-guard-runbook.md plugins/hexaemeron/docs/fiat-author-publisher-separation/runbook.md)"
cmp .hexaemeron/study.md docs/remove-the-beginner-primer/study.md
cmp .hexaemeron/runbook.md docs/remove-the-beginner-primer/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/remove-the-beginner-primer/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/remove-the-beginner-primer/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py --strict docs/remove-the-beginner-primer/study.md docs/remove-the-beginner-primer/runbook.md docs/decisions/ADR-060-remove-the-beginner-primer-and-its-generator.md README.md
test "$(python3 -c "import json;d=json.load(open('.horos/boundary.json'));print(len(d['entries']),d['counts']['bytes_binary'])")" = "128 43883426"
python3 plugins/horos/skills/horos/scripts/horos.py check .
test "$(git diff --name-only HEAD~1..HEAD)" = ".dead-code/baseline.json"
python3 scripts/dead_code.py baseline --check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 scripts/portable_promise_machine.py check
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
RUN="$(python3 scripts/run_checks.py --base $BASE --jobs 2 --format json)"; printf '%s\n' "$RUN"
test "$(printf '%s' "$RUN" | python3 -c 'import json,sys; print(json.load(sys.stdin)["outcome"])')" = green
git diff --check
git verify-commit <each-local-commit-sha>
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>')" -eq 1
test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Wildcat-Origin: shoggoth')" -eq 1
```

`horos.py check .` must print `boundary matches the tree`. The
`run_checks.py` line reads the `outcome` field out of the JSON record rather
than trusting the exit status, for the reason the shared obligations give; the
human format pads that line as `outcome    green`, so a literal-space grep on
it would never match.

**Files.** Deleted, fifteen paths, 10,946,434 bytes:
`audit/rounds/docs-a-child-or-a-golden-retriever.md`;
`audit/rounds/docs-a-child-or-a-golden-retriever.synopsis.md`;
`docs/a-child-or-a-golden-retriever.md`;
`docs/a-child-or-a-golden-retriever-runbook.md`;
`docs/a-child-or-a-golden-retriever-source-note.md`;
`docs/a-child-or-a-golden-retriever-study.md`;
`docs/assets/a-child-or-a-golden-retriever-cover.png`;
`docs/assets/a-child-or-a-golden-retriever-fiat-flow.png`;
`docs/assets/a-child-or-a-golden-retriever-mascot-fiat.png`;
`docs/assets/a-child-or-a-golden-retriever-mascot-roles.png`;
`docs/assets/a-child-or-a-golden-retriever-whos-who.png`;
`docs/pdf/a-child-or-a-golden-retriever.pdf`;
`docs/pdf/a-child-or-a-golden-retriever-quick-start.pdf`;
`scripts/build_child_or_golden_retriever_primer.py`;
`tests/test_child_or_golden_retriever_primer.py`. Changed: `README.md`, where
lines 29 to 33 go, a complete paragraph plus its trailing blank line, so no
surrounding text is re-flowed and nothing is written in its place;
`docs/decisions/ADR-039-keep-one-source-for-the-beginner-primer.md`, `## Status`
only; `.horos/boundary.json`, by scan; `.dead-code/baseline.json`, by
`baseline --write`, alone in the second commit. Added:
`docs/decisions/ADR-060-remove-the-beginner-primer-and-its-generator.md`;
`docs/remove-the-beginner-primer/study.md`;
`docs/remove-the-beginner-primer/runbook.md`;
`audit/rounds/fiat-975-remove-the-child-or-golden-retriever-primer.md` and its
`.synopsis.md`, only when Warden records a round. No other tracked path is
touched. The `files_walked` counter in the boundary is measured rather than
predicted: the study's figure of 2,117 assumed a pure deletion, and this step
adds files, so read what the scan writes.

**Tests.** Write no new test. The regression net is the root suite plus the
five selected checks, and the removal's own evidence is the deleted-set,
`README.md`, `ADR-039` and audit-tree assertions in the exit block, each of
which fails if the boundary is crossed. Expected counts: `Ran 765 tests` and
`OK` from `python3 -m unittest discover -s tests`, against `Ran 765 tests` and
`FAILED (errors=1)` at entry. The Elenchus runner contract for this step is
test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`unittest-json-v1`, report file
`.elenchus/fiat-975-remove-the-beginner-primer-step-1.json`. That runner emits
the `elenchus.unittest.v1` schema, and `/.elenchus/` is gitignored so the
report never becomes an unowned changed path. The report target must not
already exist, so remove a stale one before a rerun. A real failure found in a
round is reduced to a minimal case and guarded before the command is run again;
for this delivery a guard is most likely an assertion that something was not
touched, since the plausible defects are over-deletion and an edited historical
record.

**Disciplines.** protasis: this step is the whole runbook, so its exit carries
the study's demo path unchanged and adds the boundary assertions the risk
register named. phylax: none opened. The step accepts no outside data, fetches
no URL, reads no credential and adds no dependency; the two subprocess-spawning
commands, the Horos scan and the baseline build, already run in the root suite
and are invoked with no new argument. Two boundaries narrow instead, which the
`over-deletion` and `generated-artefact-orphan` checks measure. ephoros: none.
Nothing added here executes unattended, holds a queue or serves a request, so
there is no three-in-the-morning question and no signal to emit. metron: none,
no performance claim; the root suite losing its one error is a correctness
change and is already an exit criterion. elenchus: the existing red in the
primer test is the subject rather than a failure to triage, and the guard
convention above applies to anything a round finds. hypomnema: removing the
primer without a replacement is expensive to reverse, and its record is
`ADR-060`, with `ADR-039` marked superseded and pointing at it.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Exit: Two commits on the step branch. The first stages the fifteen deletions, edits `README.md`, marks `ADR-039` superseded, adds `docs/decisions/ADR-060-remove-the-beginner-primer-and-its-generator.md`, adds the tracked copies of the study and this runbook, then runs the Horos scan after `git add` and stages `.horos/boundary.json`. The second republishes `.dead-code/baseline.json` and nothing else. At the tip: no tracked path names the primer; the boundary carries 128 entries and `bytes_binary` 43,883,426, down from 135 and 54,685,567 by the seven `grade: hard` binaries totalling 10,802,141 bytes; the baseline sits directly on the commit it was computed from; the `README.md` diff adds no line; `ADR-039` keeps its body; nothing under `audit/` is modified; and every selected scope is green. Prove it with: export TMPDIR=/private/tmp/fiat-975 && mkdir -p "$TMPDIR" BASE=840d8dd3596fd6394901ba85a693bea00c69bf25 test -z "$(git ls-files | grep -iE 'child.or.a.golden.retriever|child_or_golden_retriever|child-or-a-golden')" test "$(git diff --name-only --diff-filter=D $BASE..HEAD | wc -l | tr -d ' ')" = 15 test -z "$(git diff --name-only --diff-filter=D $BASE..HEAD | grep -ivE 'child.or.a.golden.retriever|child_or_golden_retriever')" test -z "$(git diff $BASE..HEAD -- README.md | grep '^+[^+]')" diff <(git show $BASE:docs/decisions/ADR-039-keep-one-source-for-the-beginner-primer.md | sed -n '/^## Context/,$p') <(sed -n '/^## Context/,$p' docs/decisions/ADR-039-keep-one-source-for-the-beginner-primer.md) test -z "$(git diff --name-only --diff-filter=MRT $BASE..HEAD -- audit/)" test -z "$(git diff --name-only $BASE..HEAD -- docs/fiat-controller-checkpoint-study.md docs/fiat-controller-checkpoint-runbook.md docs/fiat-integration-path-bound-study.md docs/fiat-integration-path-bound-runbook.md docs/fiat-step-branch-extensions-runbook.md docs/fiat-sync-run-generator-aggregates-runbook.md docs/protasis-amendment-block-check-runbook.md docs/ci-plugin-suite-gate/runbook.md docs/fiat-sync-resolution-guard-runbook.md plugins/hexaemeron/docs/fiat-author-publisher-separation/runbook.md)" the tracked study copy is the receipted study carrying exactly two declared rewrites and nothing else. Every discipline link of the form `(../<name>/SKILL.md)` becomes `(../../plugins/hexaemeron/skills/<name>/SKILL.md)`, which touches lines 497, 503, 529, 552 and 574 of the receipted study; and the inline code span that opens on line 313 and closes on line 314 is reflowed onto a single line. Prove it by applying that transformation to `.hexaemeron/study.md` with one deterministic command recorded in the step's implementation notes, requiring its output to equal `docs/remove-the-beginner-primer/study.md` byte for byte, and by `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/remove-the-beginner-primer/study.md` reporting no finding cmp .hexaemeron/runbook.md docs/remove-the-beginner-primer/runbook.md python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/remove-the-beginner-primer/study.md python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/remove-the-beginner-primer/runbook.md python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py --strict docs/remove-the-beginner-primer/study.md docs/remove-the-beginner-primer/runbook.md docs/decisions/ADR-060-remove-the-beginner-primer-and-its-generator.md README.md test "$(python3 -c "import json;d=json.load(open('.horos/boundary.json'));print(len(d['entries']),d['counts']['bytes_binary'])")" = "128 43883426" python3 plugins/horos/skills/horos/scripts/horos.py check . test "$(git diff --name-only HEAD~1..HEAD)" = ".dead-code/baseline.json" python3 scripts/dead_code.py baseline --check python3 scripts/promise_machine.py check python3 scripts/promise_machine.py coverage --check python3 scripts/portable_promise_machine.py check python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check . RUN="$(python3 scripts/run_checks.py --base $BASE --jobs 2 --format json)"; printf '%s\n' "$RUN" test "$(printf '%s' "$RUN" | python3 -c 'import json,sys; print(json.load(sys.stdin)["outcome"])')" = green git diff --check git verify-commit <each-local-commit-sha> test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>')" -eq 1 test "$(git show -s --format=%B <each-local-commit-sha> | grep -Fxc 'Wildcat-Origin: shoggoth')" -eq 1 `horos.py check .` must print `boundary matches the tree`. The `run_checks.py` line reads the `outcome` field out of the JSON record rather than trusting the exit status, for the reason the shared obligations give; the human format pads that line as `outcome green`, so a literal-space grep on it would never match.

**Why.** The receipted study writes its five discipline links as `(../<name>/SKILL.md)`, which resolve only from a directory holding those skills as siblings. No location under `docs/` makes them resolve, so unlike the sibling runs this cannot be repaired by choosing the copy's depth. `tests/test_shipped_tree_lints.py:52` walks `docs/` through hypomnema, which reported five `H001` findings on the tracked copy, and a sixth on line 314 where an inline code span opening on line 313 crosses a line break that `_code_spans` at `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py:163` pairs per line. Removing that one file returned `lint-hypomnema` and the root suite to exit 0, so the finding is isolated to it. A receipted study cannot be corrected and an appended amendment cannot retract a link, so byte-identity and a clean record lint were unsatisfiable together. The Creator chose a derived copy over dropping the study from the repository or hiding it from the lint: the transformation is declared, bounded to six lines, and checked by re-derivation rather than asserted.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds.
