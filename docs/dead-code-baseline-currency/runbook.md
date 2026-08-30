# Runbook: report dead-code baseline staleness instead of failing the check

This run starts from `main` at `7e97b5195d5b0e43146b4200f26cd41b89003413` on
branch `fiat/936-report-dead-code-baseline-staleness-instead`. Every command
below runs from the repository root under the interpreter pinned in
`.python-version`, CPython 3.14.6, with the standard library alone and no new
dependency. The delivery adds no Solidity, so the Pashov security suite is
waived and the waiver is recorded in the run's audit record at
`audit/rounds/fiat-936-report-dead-code-baseline-staleness-instead.md`.

The runbook derives from the receipted study and adds no design decision. Where
the study fixed a rendering, a refusal or a path, this page carries that text
down to the step rather than restating the reasoning behind it.

## Why this ships as one step

The study settled the sizing in its item 4, and the argument is a dependency
rather than a preference. Every step in this repository refreshes
`.horos/boundary.json` after `git add`, and `.github/workflows/dead-code.yml`
triggers on `.horos/**`. A step pushed before the fix landed would therefore run
the unfixed `baseline --check` against a checkout that has already moved past
the publication commit `41bea02dd9ea4cfe2ba32342f4e08de62b50ce0e`, and the run
would strand on the exact defect it exists to remove.

Shipping as one step puts the changed command in the first branch pushed. That
branch's own pull request then runs the fixed `baseline --check` in CI against a
genuinely stale tree, which is the acceptance demonstration rather than a way
around one. Nothing in the study's sizing argues for a second step, so the count
stays at one.

## Shared obligations

These hold for every commit the step produces.

**Commit identity and trailers.** Commits use the repository's configured
identity as it now stands, `Dr Laurence E. Day <laurence@wildcat.finance>` with
signing key `3BCD9EFDA6670A3F65AF679EB83B60AE16F5DD1A` and `commit.gpgsign`
true. Do not pass a per-command identity override. The message ends with exactly
one `Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` line and one
`Wildcat-Origin: shoggoth` line, in that order, with nothing after them.

**Boundary order.** Stage the change first, then regenerate the reading
boundary, then stage the boundary:

```bash
git add <changed paths>
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
git add .horos/boundary.json .horos/candidates.json .horos/census.json
```

The scan classifies the staged tree, so running it before `git add` leaves the
boundary describing a tree that no longer exists and the root suite fails on the
drift. Stage only the `.horos` files the deterministic scan actually changed.

**Ask first.** Adding a dependency. Changing `.dead-code/baseline.json`,
`.dead-code/suppressions.json` or either dead-code schema. Changing the
workflow's `paths` filter or its `permissions`. Making `dead-code / report` a
required status check. Editing `docs/dead-code/study.md`,
`docs/dead-code/runbook.md` or `docs/dead-code/measurement.md`.

**Never.** Weaken a refusal that establishes the record is valid. Republish the
baseline to make the check pass. Drop
`test_source_change_after_publication_is_stale` without replacing every case it
covered. Claim a command ran when it did not.

**The baseline is not republished.** `.dead-code/baseline.json` stays at its
published source commit `3c67a6e293accc9ea2c00b4231c32a4894d83c80`, written by
`41bea02dd9ea4cfe2ba32342f4e08de62b50ce0e`. Reading that record as stale is the
fixture the acceptance checks need, so a republication would delete the
demonstration.

## Step 1: Report baseline currency and keep validity gating

**Goal.** Split `baseline --check` into the validity question, which keeps the
exit status, and the currency question, which becomes a reported observation on
stdout and in the workflow summary.

**Entry.** Branch `fiat/936-report-dead-code-baseline-staleness-instead` at
`7e97b5195d5b0e43146b4200f26cd41b89003413`, with the study receipt verified and
no product change in the worktree. Before editing, confirm on `origin/main` that
`ADR-054` is still the next free decision-record identity; `ADR-053` is the
highest observed at the base ref, and a collision stops the step for a receipted
runbook amendment rather than a quiet renumber. Confirm that
`python3 scripts/dead_code.py baseline --check` refuses at the entry state with
`baseline is stale; source changed after publication:`, and record the wall time
of that run as the Metron before-measurement.

**Exit.** All of the following hold.

1. `require_baseline_publication` at `scripts/dead_code.py:3721` discovers the
   publication commit with `git rev-list -1 <current> -- .dead-code/baseline.json`,
   validates the returned object id before reusing it as an argument, and
   compares `source..publication` and `publication..current` separately. Every
   git call goes through the existing `run_git` path with fixed argv, no shell,
   the output ceiling and the timeout the file already applies.

2. The command's contract reads as follows, in the order it evaluates. Eleven
   cases refuse and exit 2:

   1. the checkout has modified tracked files, from `require_clean_tree` at
      `scripts/dead_code.py:494`, called first at line 4066;
   2. `.dead-code/baseline.json` at the current commit is unreadable, is not a
      regular blob, or exceeds `MAX_BASELINE_BYTES`;
   3. the record fails `validate_baseline_document` at line 3596, on any of its
      closed field set, schema id, tool identity, generating command, object
      ids, universe, analyser identity and state, finding shape or suppression
      digest shape;
   4. the record is not canonical JSON;
   5. the recorded source commit equals the current commit;
   6. the recorded source commit is not an ancestor of the current commit;
   7. no commit reachable from the current commit wrote
      `.dead-code/baseline.json`;
   8. the record blob at the discovered publication commit differs from the
      record blob at the current commit;
   9. `source..publication` is not exactly `.dead-code/baseline.json`, which is
      the former `baseline publication does not change exactly its owned record`
      refusal re-scoped from the checkout to the publication commit;
   10. `compare_baseline_documents` at line 3693 finds any drift between the
       recorded document and the document recomputed at the recorded source
       commit, across commit, Git tree, universe, analyser set, analyser
       version, analyser state, suppressions, finding identities and the whole
       document;
   11. `load_suppressions` raises any refusal at the source commit, covering
       broad identity, duplicate, unknown field, missing finding, excluded path,
       mismatched target and obsolete entry.

   One case reports and exits 0: `publication..current` is non-empty, so the
   command names the changed paths and returns success. Issue #936 listed four
   retained refusals; that list was incomplete against the code, and the
   eleven above govern.

3. `_baseline_summary` at `scripts/dead_code.py:3763` gains two lines. A
   `published <commit>` line follows the `source` line in the same block, and a
   `currency` line sits between the analyser line and `status`, as the study's
   item 4 renders it. A moved checkout reads
   `currency  stale; N path(s) changed after publication: <paths>` and an
   unmoved one reads `currency  current; no tracked path changed after
   publication`. The path list follows the convention `require_clean_tree`
   already uses: name at most five, then `and N more`. The `status` line keeps
   the wording `status    matched; candidate count did not gate this command`,
   because `matched` is the validity statement and it stays true in both cases.

4. Nothing serialised changes. `$defs.baseline` in
   `schemas/dead-code-report-v1.schema.json` is untouched, the recorded document
   gains no field, and `TOOL_VERSION` stays `"1"` because line 3610 refuses any
   record whose tool object is not `{"id": "dead-code", "version": "1"}`.
   `.dead-code/baseline.json` is byte-identical to the base ref at the end of
   the step.

5. `.github/workflows/dead-code.yml` redirects the check's stdout to a file
   under `$RUNNER_TEMP` and prints that file. The capture is a redirect rather
   than a pipe, so the command's exit status still reaches the job and a refusal
   still fails it. The summary step reads the captured file and prints the
   command's own `currency` and `status` lines where line 92 currently prints
   the hardcoded `- status: matched`. The four literal demo commands keep their
   present order and the summary keeps the field names `commit`, `git_tree`,
   `universe`, `status` and `analysers` along with the sentence "Candidates are
   reported, not gated", so
   `test_workflow_and_operator_guide_carry_the_exact_four_command_demo` and
   `test_workflow_summary_names_tree_universe_analyser_and_non_gating_state`
   both still pass.

6. `docs/promise-machine/dead-code-v1.md` keeps the same four commands in the
   same order, and its "Recover from refusal" entry for `baseline is stale`
   becomes an instruction to read the `currency` line rather than to repeat the
   two-commit refresh.

7. `docs/decisions/ADR-054-report-baseline-currency-without-failing-the-check.md`
   records three things: that currency is separated from validity in the exit
   status, that the publication commit is discovered and its blob identity
   checked rather than assumed, and that the currency result stays out of any
   machine-readable output. It points at ADR-053 rather than restating it, and
   ADR-053 stays Accepted and unedited.

8. `python3 scripts/dead_code.py baseline --check` exits 0 on the branch tip,
   prints a `published` line naming `41bea02dd9ea4cfe2ba32342f4e08de62b50ce0e`
   and a `currency  stale;` line naming the paths this run's own commit changed.

9. The Metron no-regression budget holds. The same command on the same host
   completes within 46 seconds, measured before and after the change with
   `time python3 scripts/dead_code.py baseline --check` and both figures
   recorded in the step's implementation notes. The study's before-measurement
   on this worktree is 43.6 seconds under CPython 3.14.6. A larger figure means
   the edit reached into the recompute and the step stops.

10. These commands exit 0 from the repository root:

    ```bash
    cmp -s .hexaemeron/study.md docs/dead-code-baseline-currency-study.md
    cmp -s .hexaemeron/runbook.md docs/dead-code-baseline-currency-runbook.md
    python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/dead-code-baseline-currency-study.md
    python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/dead-code-baseline-currency-runbook.md
    python3 -m unittest tests.test_dead_code -v
    python3 tests/emit_dead_code_report.py .elenchus/fiat-936-step-1.json
    python3 scripts/run_checks.py --scope dead-code --base 7e97b5195d5b0e43146b4200f26cd41b89003413
    python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py --strict docs/dead-code-baseline-currency-study.md docs/dead-code-baseline-currency-runbook.md docs/decisions/ADR-054-report-baseline-currency-without-failing-the-check.md docs/promise-machine/dead-code-v1.md
    python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/decisions/ADR-054-report-baseline-currency-without-failing-the-check.md
    python3 plugins/horos/skills/horos/scripts/horos.py check .
    python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
    git diff --check
    ```

    `--scope dead-code` selects the `dead-code-suite` check, whose argv in
    `tests/check-map-v1.json` is `python3 -m unittest tests.test_dead_code -v`,
    and closes over the consumer scope `repo-lints`, giving `lint-phylax`,
    `lint-ephoros` and `lint-hypomnema`. Passing `--base` unions that request
    with the committed diff, so the owner entries for `.horos`, `audit`, `docs`
    and `tests/promise_machine_coverage.json` also pull in `root`, `docs`,
    `promise-machine` and `hexaemeron`, and `root-suite` runs. Run the closure
    with `--base` rather than bare, because a bare invocation after the commit
    sees an empty diff and silently narrows to the two scopes.

**Files.** Change `scripts/dead_code.py`, `tests/test_dead_code.py`,
`.github/workflows/dead-code.yml`, `docs/promise-machine/dead-code-v1.md` and
`tests/promise_machine_coverage.json`. Create
`docs/decisions/ADR-054-report-baseline-currency-without-failing-the-check.md`,
`docs/dead-code-baseline-currency-study.md` and
`docs/dead-code-baseline-currency-runbook.md`. The two tracked copies sit
directly under `docs/` rather than in `docs/dead-code/`, because the suite pins
the SHA-256 of `docs/dead-code/study.md` and `docs/dead-code/runbook.md` at
`tests/test_dead_code.py:35` and `:36` and those two files belong to issue #437.
Regenerate `.horos/boundary.json`, and `.horos/candidates.json` and
`.horos/census.json` if the deterministic scan changes them, last of all.
`.dead-code/baseline.json`, `.dead-code/suppressions.json`,
`schemas/dead-code-report-v1.schema.json`,
`schemas/dead-code-suppressions-v1.schema.json`, `tests/check-map-v1.json`,
`docs/decisions/ADR-053-keep-dead-code-discovery-report-only.md`,
`docs/dead-code/study.md`, `docs/dead-code/runbook.md` and
`docs/dead-code/measurement.md` stay unchanged; a change to any of them needs a
receipted runbook amendment first. The run's audit record and its derived
synopsis under `audit/rounds/` are written by the audit loop, not by
implementation.

The `dead_code` object in `tests/promise_machine_coverage.json` is refreshed in
the same commit as the code it binds. Its `runtime.sha256` for
`scripts/dead_code.py`, `tests.sha256` for `tests/test_dead_code.py` and
`documentation.sha256` for `docs/promise-machine/dead-code-v1.md` all change,
and its `tests.selectors` list names
`test_source_change_after_publication_is_stale`, so the list is updated to the
replacement selectors. The study recorded that nothing in the repository
enforces those digests today, which is why they are refreshed by hand here
rather than by a check.

**Tests.** `tests/test_dead_code.py:2824`,
`test_source_change_after_publication_is_stale`, asserts the refusal this step
removes and is replaced. The replacement set covers the reported case, the two
new refusals and the three retained refusals the acceptance checks name, giving
at least six cases against the existing synthetic fixture repository:

- a checkout moved past the publication commit reports stale, names the changed
  paths and exits 0;
- a source commit that is not an ancestor of the checkout still exits non-zero;
- a recorded document differing from the document recomputed at its own source
  commit still exits non-zero with the drift named as it is today;
- a publication commit that changed a path other than the owned record still
  exits non-zero;
- a checkout whose record blob differs from the discovered publication commit's
  still exits non-zero;
- a record whose publication commit cannot be found still exits non-zero.

Name the first of these `test_source_change_after_publication_is_stale` so the
selector list in `tests/promise_machine_coverage.json` keeps naming a case that
exists. `test_check_is_read_only_and_does_not_sweep_temporary_files` at line
2810 stays green unchanged, and the two workflow tests at lines 2940 and 2965
stay green against the edited YAML.

The Elenchus runner contract for any audit repair on this step is exact: test
command `python3 tests/emit_dead_code_report.py {report}`; report format
`unittest-json-v1`; expected report schema `elenchus.unittest.v1`; report file
`.elenchus/fiat-936-step-1.json`. The report path must be fresh. A missing,
stale, empty, malformed or infrastructure-failed report is `inconclusive`, not
evidence that a repair is guarded. Warden uses these three inputs and does not
substitute a nearby suite.

After the prose pass, and as part of this step, commit the tracked copies of the
study and the runbook. Copy `.hexaemeron/study.md` to
`docs/dead-code-baseline-currency-study.md` and `.hexaemeron/runbook.md` to
`docs/dead-code-baseline-currency-runbook.md` without rewriting either, prove
the copies with the two `cmp -s` commands and the two `protasis.py` invocations
above, then stage them with the rest of the change and regenerate the boundary
last.

**Disciplines.** phylax: the step opens two new subprocess reads,
`git rev-list -1 <current> -- .dead-code/baseline.json` and
`git diff --name-only -z <publication>..<current>`, and prints repository paths
into stdout and a GitHub step summary, so register ids `git-argv`,
`path-report-rendering` and `pipefail-masking` are the controls to hold.
ephoros: the command runs unattended in the `dead-code` workflow on every push
to `main` and every matching pull request, and this step changes both the
summary it emits and the workflow that renders it, so the three on-call
questions in the study's item 8 have to be answerable from the step summary
alone. metron: the change touches a command measured at 43.6 seconds, and the
46-second no-regression budget in exit item 9 is the check that the edit stayed
out of the recompute. elenchus: the failure in hand is workflow run
33291365525, and every case in the replacement test set fails against the entry
tree and passes after the fix. hypomnema: separating currency from validity in
the exit status changes when CI goes red for the whole repository and is
expensive to reverse, so ADR-054 owns that decision together with the
publication-commit discovery and the choice to leave currency out of any
machine-readable output.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Entry: Branch `fiat/936-report-dead-code-baseline-staleness-instead` at `7e97b5195d5b0e43146b4200f26cd41b89003413`, with the study receipt verified and no product change in the worktree. Before editing, confirm on `origin/main` that `ADR-054` is still the next free decision-record identity; `ADR-053` is the highest observed at the base ref, and a collision stops the step for a receipted runbook amendment rather than a quiet renumber. Confirm that `python3 scripts/dead_code.py baseline --check` exits 0 at the entry state: `git diff --name-only 3c67a6e2..7e97b519` is exactly `.dead-code/baseline.json`, so the entry checkout sits at the publication commit and the command reports a matched baseline rather than refusing. Record the wall time of that run as the Metron before-measurement. Complete replacement Exit: All of the following hold. 1. `require_baseline_publication` at `scripts/dead_code.py:3721` discovers the publication commit with `git rev-list -1 <current> -- .dead-code/baseline.json`, validates the returned object id before reusing it as an argument, and compares `source..publication` and `publication..current` separately. Every git call goes through the existing `run_git` path with fixed argv, no shell, the output ceiling and the timeout the file already applies. 2. The command's contract reads as follows, in the order it evaluates. Eleven cases refuse and exit 2: 1. the checkout has modified tracked files, from `require_clean_tree` at `scripts/dead_code.py:494`, called first at line 4066; 2. `.dead-code/baseline.json` at the current commit is unreadable, is not a regular blob, or exceeds `MAX_BASELINE_BYTES`; 3. the record fails `validate_baseline_document` at line 3596, on any of its closed field set, schema id, tool identity, generating command, object ids, universe, analyser identity and state, finding shape or suppression digest shape; 4. the record is not canonical JSON; 5. the recorded source commit equals the current commit; 6. the recorded source commit is not an ancestor of the current commit; 7. no commit reachable from the current commit wrote `.dead-code/baseline.json`; 8. the record blob at the discovered publication commit differs from the record blob at the current commit; 9. `source..publication` is not exactly `.dead-code/baseline.json`, which is the former `baseline publication does not change exactly its owned record` refusal re-scoped from the checkout to the publication commit; 10. `compare_baseline_documents` at line 3693 finds any drift between the recorded document and the document recomputed at the recorded source commit, across commit, Git tree, universe, analyser set, analyser version, analyser state, suppressions, finding identities and the whole document; 11. `load_suppressions` raises any refusal at the source commit, covering broad identity, duplicate, unknown field, missing finding, excluded path, mismatched target and obsolete entry. One case reports and exits 0: `publication..current` is non-empty, so the command names the changed paths and returns success. Issue #936 listed four retained refusals; that list was incomplete against the code, and the eleven above govern. 3. `_baseline_summary` at `scripts/dead_code.py:3763` gains two lines. A `published <commit>` line follows the `source` line in the same block, and a `currency` line sits between the analyser line and `status`, as the study's item 4 renders it. A moved checkout reads `currency stale; N path(s) changed after publication: <paths>` and an unmoved one reads `currency current; no tracked path changed after publication`. The path list follows the convention `require_clean_tree` already uses: name at most five, then `and N more`. The `status` line keeps the wording `status matched; candidate count did not gate this command`, because `matched` is the validity statement and it stays true in both cases. 4. Nothing serialised changes. `$defs.baseline` in `schemas/dead-code-report-v1.schema.json` is untouched, the recorded document gains no field, and `TOOL_VERSION` stays `"1"` because line 3610 refuses any record whose tool object is not `{"id": "dead-code", "version": "1"}`. `.dead-code/baseline.json` is byte-identical to the base ref at the end of the step. 5. `.github/workflows/dead-code.yml` redirects the check's stdout to a file under `$RUNNER_TEMP` and prints that file. The capture is a redirect rather than a pipe, so the command's exit status still reaches the job and a refusal still fails it. The summary step reads the captured file and prints the command's own `currency` and `status` lines where line 92 currently prints the hardcoded `- status: matched`. The four literal demo commands keep their present order and the summary keeps the field names `commit`, `git_tree`, `universe`, `status` and `analysers` along with the sentence "Candidates are reported, not gated", so `test_workflow_and_operator_guide_carry_the_exact_four_command_demo` and `test_workflow_summary_names_tree_universe_analyser_and_non_gating_state` both still pass. 6. `docs/promise-machine/dead-code-v1.md` keeps the same four commands in the same order, and its "Recover from refusal" entry for `baseline is stale` becomes an instruction to read the `currency` line rather than to repeat the two-commit refresh. 7. `docs/decisions/ADR-054-report-baseline-currency-without-failing-the-check.md` records three things: that currency is separated from validity in the exit status, that the publication commit is discovered and its blob identity checked rather than assumed, and that the currency result stays out of any machine-readable output. It points at ADR-053 rather than restating it, and ADR-053 stays Accepted and unedited. 8. `python3 scripts/dead_code.py baseline --check` exits 0 on the branch tip, prints a `published` line naming `41bea02dd9ea4cfe2ba32342f4e08de62b50ce0e` and a `currency stale;` line naming the paths this run's own commit changed. 9. The Metron no-regression budget holds. The same command on the same host completes within 46 seconds, measured before and after the change with `time python3 scripts/dead_code.py baseline --check` and both figures recorded in the step's implementation notes. The study's before-measurement on this worktree is 43.6 seconds under CPython 3.14.6. A larger figure means the edit reached into the recompute and the step stops. 10. These commands exit 0 from the repository root: cmp -s .hexaemeron/study.md docs/dead-code-baseline-currency/study.md cmp -s .hexaemeron/runbook.md docs/dead-code-baseline-currency/runbook.md python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/dead-code-baseline-currency/study.md python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/dead-code-baseline-currency/runbook.md python3 -m unittest tests.test_dead_code -v python3 tests/emit_dead_code_report.py .elenchus/fiat-936-step-1.json python3 scripts/run_checks.py --scope dead-code --base 7e97b5195d5b0e43146b4200f26cd41b89003413 python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py --strict docs/dead-code-baseline-currency/study.md docs/dead-code-baseline-currency/runbook.md docs/decisions/ADR-054-report-baseline-currency-without-failing-the-check.md docs/promise-machine/dead-code-v1.md python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/decisions/ADR-054-report-baseline-currency-without-failing-the-check.md python3 plugins/horos/skills/horos/scripts/horos.py check . python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check . git diff --check `--scope dead-code` selects the `dead-code-suite` check, whose argv in `tests/check-map-v1.json` is `python3 -m unittest tests.test_dead_code -v`, and closes over the consumer scope `repo-lints`, giving `lint-phylax`, `lint-ephoros` and `lint-hypomnema`. Passing `--base` unions that request with the committed diff, so the owner entries for `.horos`, `audit`, `docs` and `tests/promise_machine_coverage.json` also pull in `root`, `docs`, `promise-machine` and `hexaemeron`, and `root-suite` runs. Run the closure with `--base` rather than bare, because a bare invocation after the commit sees an empty diff and silently narrows to the two scopes. Complete replacement Files: Change `scripts/dead_code.py`, `tests/test_dead_code.py`, `.github/workflows/dead-code.yml`, `docs/promise-machine/dead-code-v1.md` and `tests/promise_machine_coverage.json`. Create `docs/decisions/ADR-054-report-baseline-currency-without-failing-the-check.md`, `docs/dead-code-baseline-currency/study.md` and `docs/dead-code-baseline-currency/runbook.md`. The two tracked copies sit in a new `docs/dead-code-baseline-currency/` directory rather than in `docs/dead-code/`, because the suite pins the SHA-256 of `docs/dead-code/study.md` and `docs/dead-code/runbook.md` at `tests/test_dead_code.py:35` and `:36` and those two files belong to issue #437. They sit two levels below the repository root rather than directly under `docs/` because the receipted study links its disciplines as `../../plugins/hexaemeron/skills/<name>/SKILL.md`, which resolves above the repository from a file directly under `docs/` and makes `tests/test_shipped_tree_lints.py` report five `H001` findings. Regenerate `.horos/boundary.json`, and `.horos/candidates.json` and `.horos/census.json` if the deterministic scan changes them, last of all. `.dead-code/baseline.json`, `.dead-code/suppressions.json`, `schemas/dead-code-report-v1.schema.json`, `schemas/dead-code-suppressions-v1.schema.json`, `tests/check-map-v1.json`, `docs/decisions/ADR-053-keep-dead-code-discovery-report-only.md`, `docs/dead-code/study.md`, `docs/dead-code/runbook.md` and `docs/dead-code/measurement.md` stay unchanged; a change to any of them needs a receipted runbook amendment first. The run's audit record and its derived synopsis under `audit/rounds/` are written by the audit loop, not by implementation. The `dead_code` object in `tests/promise_machine_coverage.json` is refreshed in the same commit as the code it binds. Its `runtime.sha256` for `scripts/dead_code.py`, `tests.sha256` for `tests/test_dead_code.py` and `documentation.sha256` for `docs/promise-machine/dead-code-v1.md` all change, and its `tests.selectors` list names `test_source_change_after_publication_is_stale`, so the list is updated to the replacement selectors. The study recorded that nothing enforces those digests; that reading is wrong. `tests/test_unique_identifiers.py:165` recomputes every bound capability digest, so a stale entry fails the root suite. They are refreshed by hand because no command writes them, not because nothing checks them. Issue #939 covers the separate gap that the entry's `promise_id` resolves to no declared promise.

**Why.** The receipted study links its disciplines as `../../plugins/hexaemeron/skills/ephoros/SKILL.md`, which resolves only from a file two levels below the repository root. Copied to `docs/dead-code-baseline-currency-study.md` those links leave the repository, and `tests/test_shipped_tree_lints.py` fails `test_hypomnema_record_pointers_all_resolve` with five `H001` findings at lines 191, 195, 210, 216 and 229 of the copy. That test is green at `7e97b5195d5b0e43146b4200f26cd41b89003413` and red on the step branch, so the flat path and a green closure were unreachable together. `docs/dead-code/` is not available because `tests/test_dead_code.py:35` and `:36` pin the two files already there for issue #437, so the copies move to a new `docs/dead-code-baseline-currency/` directory at the same depth. A study amendment cannot repair it, because an amended study keeps the receipted bytes as an exact prefix and only appends. The Entry field is corrected in the same amendment: `baseline --check` exits 0 at the entry state rather than refusing, because `3c67a6e2..7e97b519` changes exactly the owned record. The Files field is corrected because the study's claim that nothing enforces the coverage digests is wrong; `tests/test_unique_identifiers.py:165` recomputes them.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds.
