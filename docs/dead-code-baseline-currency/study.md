# Study: report dead-code baseline staleness instead of failing the check

Assuming, unless corrected:

1. The base is `wildcat-finance/skills` at `7e97b5195d5b0e43146b4200f26cd41b89003413`, and the run branch is `fiat/936-report-dead-code-baseline-staleness-instead`.
2. The interpreter is the pinned CPython in `.python-version`, which reads `3.14.6`, with the standard library only and `unittest`. No new dependency.
3. The delivery adds no Solidity, so the Pashov security suite is waived and that waiver is recorded in the run's audit record.
4. `.dead-code/baseline.json` stays at its published source commit `3c67a6e293accc9ea2c00b4231c32a4894d83c80`. This run does not republish it, because a stale-and-valid baseline is the fixture the acceptance checks need.
5. Issue #936's Required behaviour and Acceptance checks are the agenda. This study settles how to meet them, not whether to.

The rest of this document proceeds on those five.

## 1. Problem statement

`python3 scripts/dead_code.py baseline --check` exits non-zero whenever any commit has landed on top of the baseline's publication commit. The command refuses with `baseline is stale; source changed after publication:` and names the changed paths. Workflow run 33291365525 refused on five paths that every Fiat step 1 writes: `.horos/boundary.json`, `audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md`, its `.synopsis.md` sibling, `docs/fiat-step-branch-extensions-runbook.md` and `docs/fiat-step-branch-extensions-study.md`.

The refusal establishes nothing about the record. `command_baseline` at `scripts/dead_code.py:4062` builds its expected document at `source_commit`, not at the checkout, so the comparison the command exists to perform reads the exact tree the baseline names. A commit landing afterwards cannot change that answer.

The user is a Fiat run and the contributor reading its checks. Fiat's push discipline tells a run to wait for a step's gates before merging. `dead-code / report` is not a required status check, so the red result blocks no merge, but a delivery reading it waits for a green that never arrives, on every step it pushes.

A working prototype means: `baseline --check` separates whether the record is valid from whether the checkout has moved past it. Validity keeps its exit status. Currency becomes a reported observation.

Proving demo path, run from the repository root on the run branch:

```bash
python3 scripts/dead_code.py baseline --check; echo "exit=$?"
python3 -m unittest tests.test_dead_code -v
python3 scripts/run_checks.py --scope dead-code
```

The first command prints a `currency` line naming the paths that changed after publication and exits 0. The run's own pull request is the second half of the demonstration: its checkout has moved past the publication commit, so the hosted `dead-code` workflow runs the changed command against a genuinely stale tree and reports green with the currency result in its step summary.

## 2. Prior art

**In this repository.** `scripts/dead_code.py` is the whole command, 4200 lines of standard library Python. `require_baseline_publication` at line 3721 holds the defect. `BASELINE_PUBLICATION_PATHS` at line 79 is the single entry `.dead-code/baseline.json`. `_baseline_summary` at line 3763 renders the text result. `compare_baseline_documents` at line 3693 and `validate_baseline_document` at line 3596 hold the validity checks that stay. `.github/workflows/dead-code.yml` runs the four-command demonstration and writes a step summary. `docs/promise-machine/dead-code-v1.md` is the operator guide. `tests/check-map-v1.json` maps the `dead-code` scope to one check, `dead-code-suite`, whose argv is `python3 -m unittest tests.test_dead_code -v`; it does not invoke `baseline --check`. `scripts/run_checks.py` contains no reference to the dead-code command.

`docs/dead-code/study.md` and `docs/dead-code/runbook.md` are the receipted issue #437 artefacts. `tests/test_dead_code.py` pins their SHA-256 values as `EXPECTED_STUDY_SHA256` and `EXPECTED_RUNBOOK_SHA256` at lines 35 and 36, so neither file may change.

**Merged pull requests.** The two most recent merges touching this subject are #929, `Establish a report-only dead-code baseline`, merged 2026-08-30T03:08:35Z, and #928, `Reconcile and publish the report-only dead-code baseline`, merged 03:05:03Z. Both bodies were read. #929 carries forward three items:

- The 435 candidates remain advisory and untriaged, and the run authorises no deletion. Carried here as a stated non-goal: this change touches exit status, not findings.
- Repository-family evidence remains `degraded@repository-graph/2`, and its incomplete graph supports no absence claim. Carried here as a constraint: the recorded analyser state must survive the change untouched, because `compare_baseline_documents` refuses on analyser status drift.
- The #437 run used installed `fiat-v5.37.1` for study through push and `fiat-v5.38.1` at integration. That is a controller-version observation about the previous run and it stays open; it is not this run's subject and this study makes no claim about it.

#928 records why the reconciliation existed: the original four stacked steps could not satisfy the controller's commit-bound baseline topology after `main` moved. That is the same class of problem this issue reports, one layer up, and it is the reason the two-commit publication rule exists at all.

**Audit records.** `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` ran from the target root and exited 0, so a committed synopsis is a valid reading view for every record it covers. Two in-scope records exist, and neither is in `main`'s tree; both live on unmerged remote audit branches, so the whole-set check does not cover them and both authoritative sources were read directly.

- `audit/rounds/fiat-437-establish-a-report-only-dead-code-baseline.md`, source read at `61f5ace9` on `origin/fiat/437-establish-a-report-only-dead-code-baseline-step-4-pin-the-baseline-check-suppressi--audit`. Twelve rounds across four steps. The register id `baseline-staleness` is `not-applicable` in the step 1 and step 2 rounds and `reviewed` in Step 4, round 1. That round records two findings, both fixed: `S4-R1-01` medium, baseline construction accepted an analyser in `failed` state, fixed in `fce72501`; `S4-R1-02` medium, the repository graph parsed the owned baseline and suppression records as declaration sources, fixed in the same commit and versioned `repository-graph/2`. Elenchus verdict `guarded`. Leads not pursued: the round explicitly considered a concurrent HEAD advance and declined to record it as a finding, reasoning that analysis reads exact commit blobs, the writer publishes only a confined record, and "the publication check rejects every intervening source diff". That last clause is the belief issue #936 overturns; the round treated the rejection as a safety property rather than as a cost. Not checked: the Pashov suite was waived for a delivery adding no Solidity, and hosted CI, push, merge and controller receipts were outside the round.
- `audit/rounds/fiat-437-dead-code-baseline-latest-main-reconciliatio.md`, source read at `5579e282` on `origin/fiat/437-dead-code-baseline-latest-main-reconciliatio-step-1-reconcile-and-publish-the-signed--audit`. One round, zero findings, canonical zero row, Elenchus verdict `null`. Its ten register ids are `history-loss`, `wrong-base`, `baseline-stale`, `decision-collision`, `boundary-drift`, `signature-drift`, `authorship-drift`, `ci-outage-as-authority`, `candidate-overclaim` and `controller-conflation`, all `reviewed`. Leads not pursued: none. It records that the publication delta is exactly `.dead-code/baseline.json`, that the baseline binds source `3c67a6e2` with 435 active candidates and zero suppressions, and that "the CI outage supplied no authority". Not checked: hosted CI, remote signature verification, push, merge, issue closure and integration had not occurred, and the installed controller was `fiat-v5.37.1` against a checked-in `fiat-v5.38.1` receipt shape.

The root `audit/AUDIT.md` and `audit/AUDIT_SYNOPSIS.md` were checked and contain no dead-code round; the root pair covers only the root source.

**Governing decision.** `docs/decisions/ADR-053-keep-dead-code-discovery-report-only.md`, Accepted 2026-08-29. Its Decision states that candidate count "never fails the command, blocks a merge or authorises source deletion". Its Consequences state that "CI fails on command, schema, discovery or analyser failure, not on findings". A baseline whose source commit is an ancestor of the checkout is none of those four. The workflow says the same thing in its own failure branch: "The command or report contract failed. This run established no dead-code result." ADR-053 also defers a diff gate to a separate decision, so whether a stale baseline should eventually expire remains outside this study.

**Outside.** The pattern is ordinary: `git rev-list -1 <commit> -- <path>` identifies the commit that last wrote a tracked file, and a two-commit publication is the standard way a record commits an identity it cannot contain. No external package is involved and none is proposed.

## 3. Constraints and non-goals

**Starting ref and toolchain.** Base `main` at `7e97b5195d5b0e43146b4200f26cd41b89003413`. CPython pinned by `.python-version` at 3.14.6, standard library only, `unittest` for tests. No Solidity, so the security suite is waived and the waiver is recorded in the audit record.

**Ruled out by the issue.** Republishing the baseline on every change is rejected: `command_baseline` refuses when the source commit equals the checkout, so republication needs a commit of its own, and one per step would tax every run in the repository. Narrowing the workflow's `paths` filter is rejected: `.horos/**` is in that filter because the boundary feeds the universe, and removing it would hide a real input.

**Ruled out by the code.** `TOOL_VERSION` stays `"1"`. `validate_baseline_document` at `scripts/dead_code.py:3610` refuses any record whose `tool` object is not `{"id": "dead-code", "version": "1"}`, so a version bump would refuse the published baseline on the first run. The recorded document, its `$defs.baseline` shape in `schemas/dead-code-report-v1.schema.json`, and `.dead-code/baseline.json` itself all stay byte-compatible. `docs/dead-code/study.md` and `docs/dead-code/runbook.md` stay byte-identical, because their digests are pinned in the suite.

**Ruled out by the recompute.** The change may not touch anything that feeds `build_report`, `load_suppressions` or `build_baseline_document`. Those rebuild the expected document at `source_commit`, and `compare_baseline_documents` refuses on any difference. A stray change to the universe, an analyser version or a finding identity would turn the published baseline into a hard refusal on the first CI run. The edit is confined to `require_baseline_publication`, `_baseline_summary` and the check branch of `command_baseline`.

**Non-goals.** No change to what the report finds, what a candidate means, or the rule that a candidate authorises no deletion. No expiry policy for a stale baseline; ADR-053 defers that. No change to the `dead-code` scope's check selection. No `--json` surface on the `baseline` subcommand; section 2 of the agenda is answered in item 4 below. No promotion of `dead-code / report` to a required status check.

**Always.** Both the focused suite and the affected-scope closure before a commit. The Imprimatur lint on every shipped document. A recorded `time` measurement of `baseline --check` before and after the change.

**Ask first.** Adding any dependency. Changing `.dead-code/baseline.json` or the schema. Changing the workflow's `paths` filter or its `permissions`. Making the check required in a ruleset. Editing `docs/dead-code/study.md` or `docs/dead-code/runbook.md`.

**Never.** Weaken a refusal that establishes the record is valid. Delete or skip `test_source_change_after_publication_is_stale` without replacing what it covered. Republish the baseline to make the check pass. Claim a command ran when it did not.

## 4. Design options

The problem is that one function conflates two questions: is the record valid, and has the checkout moved past it. Four constructions were considered.

**A. Discover the publication commit, then split the two questions.** Find the commit that wrote the checked-out `.dead-code/baseline.json` with `git rev-list -1 <current> -- .dead-code/baseline.json`. Verify that its record blob is byte-identical to the checkout's, so the discovered commit really is the one that published these bytes. Require `git diff --name-only <source>..<publication>` to be exactly `.dead-code/baseline.json`, which preserves today's "changed exactly its owned record" refusal against the commit it was always about. Then compute `git diff --name-only <publication>..<current>`: empty means current, non-empty is the currency observation and the paths to name. Trade: two extra `git` calls and one new failure mode, a publication commit that cannot be discovered or whose blob disagrees. Cost is milliseconds against a measured 43.6-second command.

**B. Split the existing diff in place.** Keep the `source..current` diff, require `.dead-code/baseline.json` to be in the changed set, report the rest as currency. Cheapest possible edit. Rejected: once the outside-paths refusal is relaxed, the remaining set can no longer distinguish a publication commit that also changed source from a later commit that did, so the "publication commit changed a path other than its own record" refusal is silently lost. Issue #936 keeps that refusal by name.

**C. An opt-in flag, `baseline --check --allow-stale`.** Keep the default refusal and let CI opt out. Rejected: the default stays the broken one, every caller has to remember the flag, and the issue asks for the exit status to reflect the contract rather than for an opt-out around it. It also leaves the command unusable by hand on any moved checkout, which is the ordinary local case.

**D. Move the currency test into the workflow.** Let `.github/workflows/dead-code.yml` compute the changed set in YAML and keep the command refusing. Rejected: it copies the contract into a file with no tests, the command stays unusable locally, and the acceptance checks are written against the command.

**Chosen: A.** It is the option that keeps every existing refusal meaning what it meant, because it re-scopes the publication check to the commit it was always describing rather than deleting it. B is cheaper to write and more expensive to comprehend afterwards, since a reader would have to reconstruct which guarantee went missing. What A trades away is a small amount of git surface: the command now depends on `rev-list` path history, which is subject to history simplification, and the blob-identity check is the price of trusting its answer. On the real repository the discovery is exact: `git rev-list -1 HEAD -- .dead-code/baseline.json` returns `41bea02dd9ea4cfe2ba32342f4e08de62b50ce0e`, and `git diff --name-only 3c67a6e2..41bea02d` returns exactly `.dead-code/baseline.json`.

**The new contract for `baseline --check`.** Issue #936 names four retained refusals. That list is incomplete against the code. The complete contract, in the order the command evaluates it:

Hard refusals, exit 2:

1. The checkout has modified tracked files. `require_clean_tree` at `scripts/dead_code.py:494`, called first at line 4066. Not named in the issue.
2. `.dead-code/baseline.json` is unreadable at the current commit, is not a regular blob, or exceeds `MAX_BASELINE_BYTES`. Not named in the issue.
3. The record fails `validate_baseline_document`: closed field set, `dead-code-baseline/v1` schema id, tool identity `dead-code 1`, generating command, object ids, universe, analyser identity with state restricted to `ran` or `degraded`, finding shape, suppression digest shape. Not named in the issue.
4. The record is not canonical JSON. Named in the issue.
5. The recorded source commit equals the current commit, so the record would have to contain its own object identity. Not named in the issue.
6. The recorded source commit is not an ancestor of the current commit. Named in the issue.
7. No commit reachable from the current commit wrote `.dead-code/baseline.json`. New, implied by the issue's required behaviour.
8. The record blob at the discovered publication commit differs from the record blob at the current commit. New, implied by the issue's required behaviour.
9. `source..publication` is not exactly `.dead-code/baseline.json`. This is the issue's "publication commit that changed a path other than its own record", re-scoped from the checkout to the publication commit, and it absorbs today's `baseline publication does not change exactly its owned record` refusal.
10. Any drift between the recorded document and the document recomputed at the recorded source commit: commit, Git tree, universe, analyser set, analyser version, analyser state, suppressions, finding identities, whole document. `compare_baseline_documents`. Named in the issue.
11. Any suppression refusal raised by `load_suppressions` at the source commit: broad identity, duplicate, unknown field, missing finding, excluded path, mismatched target, obsolete entry. Not named in the issue.

Reported, exit 0:

12. `publication..current` is non-empty. The command names the changed paths and exits 0. This is the only status change.

So the issue's four are 4, 6, 9 and 10. The study adds 1, 2, 3, 5 and 11 as retained, and 7 and 8 as new.

**Output.** The `currency` line goes into `_baseline_summary` between the analyser line and the `status` line, and the source block gains the publication commit:

```text
source    3c67a6e293accc9ea2c00b4231c32a4894d83c80
published 41bea02dd9ea4cfe2ba32342f4e08de62b50ce0e
...
currency  stale; 5 path(s) changed after publication: .horos/boundary.json, audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md, audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.synopsis.md, docs/fiat-step-branch-extensions-runbook.md, docs/fiat-step-branch-extensions-study.md
status    matched; candidate count did not gate this command
```

When nothing changed, the line reads `currency  current; no tracked path changed after publication`. The `status` line keeps its wording, because `matched` is the validity statement and it stays true in both cases. Path lists follow the convention already used by `require_clean_tree` and the current refusal: name at most five, then `and N more`. The reproduction fixture has exactly five paths, so it names all five.

**Text only, no JSON.** The `baseline` subparser at `scripts/dead_code.py:4200` has no `--json` argument, only the mutually exclusive `--write` and `--check`. Adding one would create an output contract with no schema, no version and no consumer: `scripts/run_checks.py` never invokes the command, `tests/check-map-v1.json` maps the scope to the unit suite alone, and the workflow renders prose. The currency result is therefore printed in the text summary and nowhere else. What would change this reading: a consumer that has to gate or route on currency. There is none today, and one would need its own schema decision.

**Not a schema change.** `dead-code-baseline/v1` names the recorded document. Currency is not a property of that document; it is a relation between the document and a checkout that moves after the document is written, so it cannot be stored in the record at all. The record gains no field, `validate_baseline_document`'s closed field set is unchanged, `schemas/dead-code-report-v1.schema.json` `$defs.baseline` is unchanged, and `TOOL_VERSION` stays `"1"` because line 3610 refuses any other tool identity. Nothing decides in favour of a new schema version, because no serialised shape changes.

**Workflow.** The demonstration step redirects the command's stdout to a file under `$RUNNER_TEMP` and prints it, without a pipe, so the command's own exit status still reaches the job. The summary step then reads that file and prints the command's `currency` and `status` lines instead of the hardcoded `- status: matched` at line 92. The four literal demo commands keep their current order, so `test_workflow_and_operator_guide_carry_the_exact_four_command_demo` still passes, and the summary keeps `commit`, `git_tree`, `universe`, `status`, `analysers` and the sentence "Candidates are reported, not gated", so `test_workflow_summary_names_tree_universe_analyser_and_non_gating_state` still passes.

**Dependents on the current non-zero exit.** Four places were checked. `scripts/run_checks.py` contains no reference to `dead_code`. `tests/check-map-v1.json` maps the `dead-code` scope to `dead-code-suite` only, whose argv is the unit suite. `.github/workflows/dead-code.yml:63` is the single caller that observes the exit status, and it is changed here. `tests/test_dead_code.py:2824`, `test_source_change_after_publication_is_stale`, asserts the refusal on a synthetic fixture repository and is replaced. Nothing else in the repository depends on the refusal.

**Promise and coverage.** `PROMISE_MACHINE.md` declares no `### promise-machine-dead-code-baseline` block; the promise id appears only in the `dead_code` object of `tests/promise_machine_coverage.json`. Its `transition` reads "record and verify one report-only static candidate baseline over an exact clean source commit, with only exact current suppressions accepted and no finding count treated as deletion or merge authority". That sentence stays true, because recording and verifying are what the command still does. The change therefore rides the existing declaration and needs no new promise block. It does need the binding refreshed in the same commit: `runtime.sha256` for `scripts/dead_code.py`, `tests.sha256` for `tests/test_dead_code.py`, `documentation.sha256` for `docs/promise-machine/dead-code-v1.md`, and the `tests.selectors` list, which names `test_source_change_after_publication_is_stale` by name. All four values were verified current at the base ref. No Python file outside `scripts/dead_code.py`, `tests/test_dead_code.py` and `tests/emit_dead_code_report.py` reads that `dead_code` object, so nothing enforces those digests today and they would go stale in silence. That gap is real but separate from this issue, and it is recorded here rather than fixed.

**This run's own ordering.** Every step here refreshes `.horos/boundary.json` after `git add`, and the dead-code workflow triggers on `.horos/**`, so any step pushed before the fix lands would run the unfixed command against a checkout that has moved past `41bea02d` and would strand the run at the exact defect it is fixing. The run therefore ships as one step: the first branch pushed already carries the changed command, so its own pull request runs the fixed `baseline --check` against a genuinely stale tree. That is not a workaround; it is the acceptance demonstration, run in CI, on this run's own commits. The run does not republish the baseline, so the record stays at `3c67a6e2` and the reported currency stays honest.

## 5. Risk register seed

The change removes an exit status, so the register concentrates on what could be lost with it, and on the two new git reads.

```risk-register
currency-as-validity | the baseline --check exit status | every refusal listed in item 4 still exits 2 and only the moved-checkout case exits 0
recompute-invariance | the expected document rebuilt at source_commit | the diff touches only publication currency and the summary, and compare_baseline_documents still matches the published record
publication-commit-identity | the commit discovered for .dead-code/baseline.json | the discovered commit's record blob equals the checkout's or the check refuses
git-argv | the new git rev-list and git diff invocations | fixed argv, no shell, bounded output, and the discovered commit is validated as an object id before it is reused as an argument
path-report-rendering | the currency path list on stdout and in the CI step summary | paths pass validate_repository_path and are printed without shell or markdown interpretation
pipefail-masking | the workflow shell that captures the command output | the command's exit status reaches the job without passing through a pipe
workflow-silence | the dead-code workflow step summary | the summary states the currency result from the command's own output rather than a fixed status line
schema-stability | .dead-code/baseline.json and dead-code-baseline/v1 | the recorded document gains no field, its schema definition is unchanged and the tool identity stays dead-code 1
suppression-path | load_suppressions at the source commit | every suppression refusal still exits non-zero and no suppression becomes advisory
coverage-binding-drift | the dead_code object in tests/promise_machine_coverage.json | the runtime, tests and documentation digests and the selector list are refreshed in the same commit
receipted-artefact-immutability | docs/dead-code/study.md and docs/dead-code/runbook.md | their pinned SHA-256 values are unchanged at the end of the step
self-hosting-order | this run's own pushed branch | the branch that changes the command is the first one pushed, so its own CI runs the fixed command
```

## 6. Glossary seeds

- **Validity.** Whether the recorded baseline document matches the document recomputed at its own source commit. Unchanged by this work.
- **Currency.** Whether the checkout is still at the baseline's publication commit. Reported, not gated, after this work.
- **Source commit.** `document["tree"]["commit"]`, the commit whose tree the baseline describes.
- **Publication commit.** The commit that wrote the checked-out `.dead-code/baseline.json`. Discovered, not recorded.
- **Owned record.** `.dead-code/baseline.json`, the only path a publication commit may change.
- **Stale.** At least one tracked path changed between the publication commit and the checkout.
- **Two-commit publication.** The rule that a baseline records one commit and is written by the next, because a commit cannot contain its own object identity.
- **Report-only.** ADR-053's standing rule that candidate count never fails a command, blocks a merge or authorises deletion.

## 7. Sources

- Issue #936, `framework-58: the dead-code baseline check fails CI on ordinary work`, `wildcat-finance/skills`, read with `gh issue view 936`.
- Workflow run 33291365525, quoted in issue #936 as the reproduction.
- `scripts/dead_code.py` at the base ref: lines 35 to 37 for tool identity, 79 for `BASELINE_PUBLICATION_PATHS`, 494 for `require_clean_tree`, 3596 for `validate_baseline_document`, 3610 for the tool identity refusal, 3693 for `compare_baseline_documents`, 3721 for `require_baseline_publication`, 3763 for `_baseline_summary`, 4062 for `command_baseline`, 4200 for the `baseline` subparser.
- `.github/workflows/dead-code.yml`, path filters and the two summary steps at lines 63 and 92.
- `tests/test_dead_code.py`: lines 19 to 36 for the pinned paths and digests, 2824 for `test_source_change_after_publication_is_stale`, 2933, 2940 and 2965 for the three workflow tests.
- `tests/check-map-v1.json`, `dead-code-suite` at line 13 and the `dead-code` scope at line 191.
- `schemas/dead-code-report-v1.schema.json`, `$defs.baseline` and its four sibling definitions.
- `tests/promise_machine_coverage.json`, the `dead_code` object with promise id `promise-machine-dead-code-baseline`.
- `docs/decisions/ADR-053-keep-dead-code-discovery-report-only.md`.
- `docs/promise-machine/dead-code-v1.md`, the operator guide, including its "Refresh the baseline" and "Recover from refusal" sections.
- `audit/rounds/fiat-437-establish-a-report-only-dead-code-baseline.md` at commit `61f5ace9`, on `origin/fiat/437-establish-a-report-only-dead-code-baseline-step-4-pin-the-baseline-check-suppressi--audit`.
- `audit/rounds/fiat-437-dead-code-baseline-latest-main-reconciliatio.md` at commit `5579e282`, on `origin/fiat/437-dead-code-baseline-latest-main-reconciliatio-step-1-reconcile-and-publish-the-signed--audit`.
- Pull requests #929 and #928, bodies read with `gh pr view`.
- Measured on the run worktree: `python3 scripts/dead_code.py baseline --check` exits 0 in 43.6 seconds under CPython 3.14.6, reporting 435 candidates, `python=ran@1` and `repository=degraded@repository-graph/2`.

## 8. Signals, and the questions behind them

The command runs unattended in the `dead-code` workflow on every push to `main` and every matching pull request, so it needs answers on the page rather than in someone's memory. Three questions, and where each is answered.

- *The check is green. Did it verify anything, or did it pass because nothing ran?* Answered by the retained `status matched; candidate count did not gate this command` line, which is emitted only after `compare_baseline_documents` returns, and by the analyser line naming each analyser's state and version. The workflow step summary carries both.
- *The check is green but the baseline is old. How far behind is it, and what moved?* Answered by the new `currency` line, which names the publication commit and the changed paths. Before this change there is no green-and-stale state to ask about, which is the point.
- *The check is red. Which of the eleven refusals fired?* Answered by the existing `dead_code.py: <refusal>` line on stderr, one distinct message per refusal, and by the workflow's failure branch, which states that no dead-code result was established.

The step that emits all three is the single step in section 11's plan; it changes both the command's summary and the workflow that renders it. [ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal must carry, and the wording above is held to that contract rather than restating it.

## 9. Boundaries, per capability

Two boundaries open here, and both are extensions of surfaces the command already crosses. This feeds item 5 rather than replacing it; [phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and the controls.

- **Subprocess argv and output, at the two new git reads.** `git rev-list -1 <current> -- .dead-code/baseline.json` and `git diff --name-only -z <publication>..<current>` are worth taking because they are the only way to learn which commit published the record and what has landed since. The controls are the ones already applied to every git call in this file: fixed argv through `run_git`, no shell, `MAX_GIT_OUTPUT_BYTES` on the output, `GIT_TIMEOUT_SECONDS` on the call, and the repository descriptor as `cwd_fd`. The commit id returned by `rev-list` is validated with `_require_oid` before it is used as an argument to the next call, so a surprising `rev-list` result cannot become an argument-shaped string. Register id `git-argv`.
- **Path bytes reaching a rendered surface.** The currency path list is printed to stdout and then copied into a GitHub step summary, which is markdown. Paths already pass `validate_repository_path`, which is what today's refusal uses on the same list, and the summary prints the command's captured lines as plain text rather than interpolating them into shell. Register id `path-report-rendering`. The related control is `pipefail-masking`: the capture uses a redirect rather than a pipe, so a refusal still fails the job.

No new network, credential, filesystem write or untrusted-input boundary opens. The check branch of `command_baseline` writes nothing, and that property is already guarded by `test_check_is_read_only_and_does_not_sweep_temporary_files`.

## 10. The budget, or its absence

There is a budget, and it is a no-regression budget rather than a target. The measured baseline on the run worktree is 43.6 seconds wall for `python3 scripts/dead_code.py baseline --check` under CPython 3.14.6, almost all of it in the recompute at the source commit. The change adds two git reads that return one commit id and a short path list. The budget: the same command on the same host stays at or under 46 seconds after the change, measured the same way, before and after, with

```bash
time python3 scripts/dead_code.py baseline --check
```

recorded in the step's implementation notes. A larger regression means the change reached into the recompute, which is also what `recompute-invariance` guards against, so the measurement doubles as a check that the edit stayed where it was supposed to. [metron](../../plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget carries and how it is checked.

## 11. The fail-closed posture

What stops the run: any of the eleven hard refusals in item 4. The posture is that validity fails closed and currency does not, and the register id `currency-as-validity` exists so a round can enumerate that claim rather than take it on trust. A refusal that becomes reportable without being listed in item 4 is a defect in this change, not a scope adjustment.

The failure in hand is workflow run 33291365525. The guard convention follows [elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md): each case gets a test that fails against the tree before the fix and passes after it, written into `tests/test_dead_code.py` beside the existing fixture helpers. The set replaces `test_source_change_after_publication_is_stale` at line 2824 and covers the reported case, the two new refusals and the three retained refusals the acceptance checks name:

- a checkout moved past the publication commit reports stale, names the changed paths and exits 0;
- a source commit that is not an ancestor of the checkout still exits non-zero;
- a recorded document differing from the document recomputed at its own source commit still exits non-zero with the drift named as it is today;
- a publication commit that changed a path other than the owned record still exits non-zero;
- a checkout whose record blob differs from the discovered publication commit's still exits non-zero;
- a record whose publication commit cannot be found still exits non-zero.

The runner for the step's audit rounds is `python3 -m unittest tests.test_dead_code -v`, and the affected-scope closure is `python3 scripts/run_checks.py --scope dead-code`. Both are green at the base ref and must be green at the step's exit.

## 12. Decisions and their homes

Three decisions here are expensive to reverse, and [hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which earn a record and where each lives.

- **Separating currency from validity in the exit status.** This changes when CI goes red for the whole repository, and reversing it would break every run that has learned to read a green-and-stale check. It earns a decision record of its own under `docs/decisions/`, unnumbered in the branch and numbered when it enters `main`. It does not edit ADR-053, which stays Accepted; it records that a currency observation is not one of the four failure classes ADR-053 named, and points at ADR-053 rather than restating it.
- **Discovering the publication commit rather than assuming the checkout is it.** This is the design trade from item 4 and it introduces a git-history dependency the command did not have. It belongs in the same decision record, as the mechanism the first decision needs, together with the blob-identity check that makes the discovery trustworthy.
- **Leaving the currency result out of any machine-readable output.** Reversing this later means designing a schema, so the reason is worth writing down where the next reader will look for it. Home: the same decision record, and the operator guide `docs/promise-machine/dead-code-v1.md`, whose "Recover from refusal" entry for `baseline is stale` becomes an instruction to read the currency line rather than to repeat the two-commit refresh.

The step's own audit record lives at the run's configured `audit.log_path` under `audit/rounds/`, with its derived synopsis beside it, and carries the twelve register ids from item 5.
