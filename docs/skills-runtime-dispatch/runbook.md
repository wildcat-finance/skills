# Runbook: trigger the skills-runtime rebuild without depending on its schedule

The receipted study is `.hexaemeron/study.md`, SHA-256
`8eafe99dcf39efe4a8213b27a936ec6fcf7b2e4296b58a02e688cd328922e60c`. Its four
criteria (C1 to C4) and selected candidate `source-dispatch` govern these four
steps. Base `main` at `9182d0adcb7e9a5330c259d9dc1e044b511711c2`; run branch
`fiat/1053-trigger-the-skills-runtime-rebuild-without`; task issue
[skills#1053](https://github.com/wildcat-finance/skills/issues/1053). Take
every step branch, parent and receipt from the controller's current directive.

## Operating boundaries

- **Always:** run the checked runner and the root Elenchus runner named in each
  Exit on a committed tree before the implement receipt; re-run the Horos
  boundary and census scans after staging any tracked-file edit and stage
  their outputs before the commit; run the imprimatur lint on every document
  that ships; keep `git diff --name-only 9182d0adcb7e9a5330c259d9dc1e044b511711c2..HEAD -- distribution/`
  empty at every step exit; append audit rounds only to
  `audit/rounds/fiat-1053-trigger-the-skills-runtime-rebuild-without.md`.
- **Ask first:** creating `RUNTIME_DISPATCH_TOKEN` and choosing its expiry;
  running the demonstration dispatch, which consumes a destination runner and
  may publish a new package; adding any file under `.github/workflows/`;
  pushing anything to `wildcat-finance/skills-runtime`; widening the token
  beyond Actions read and write on that one repository; falling back to a
  GitHub App.
- **Never:** write a token value into any file, log, marker, report or
  transcript; edit `distribution/skills-runtime/sync.yml`; use `schedule` as
  the only trigger; use `repository_dispatch`; let the dispatch job succeed
  when the secret is absent; rewrite ADR-066, the split study, a merged pull
  request body or an audit record; relax an assertion to pass a step; edit a
  written conformance report; claim a dispatch happened without the
  destination run id.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 96d0624f9f2822b42ec2c0f13b9221ec2d9cc97b7aaeea9c30eae3da5ba3e0ba
candidate | source-dispatch
```

```command-interfaces
schema | protasis-command-interfaces/v1
tests/run_tests.py | report_target | aa577d63846e947944c04506ca9985b18bf3bac21c6d360bdbc18fd1f8360258
```

## Step 1: Scaffold the record

**Goal.** Publish the receipted study, this runbook, the design record with its
selection reports, the conformance resolver and the decision draft, so the
repository holds the design before any product changes.

**Entry.** The controller's Step 1 branch, cut from the run branch at
`9182d0adcb7e9a5330c259d9dc1e044b511711c2`; the study and runbook receipts
exist and no conformance cell is due at `step:1`.

**Exit.** The committed copies are byte-identical to the receipted artefacts and the decision draft resolves from the study's design bridge. Run:

```sh
python3 scripts/run_checks.py --base fiat/1053-trigger-the-skills-runtime-rebuild-without --scope root --scope repo-lints --scope docs --format json --report .hexaemeron/reports/step-1-checked.json
python3 tests/run_tests.py --elenchus-report .hexaemeron/reports/step-1-exit.json
```

Both exit 0. `cmp` of `docs/skills-runtime-dispatch/study.md` against
`.hexaemeron/study.md`, of `docs/skills-runtime-dispatch/runbook.md` against
`.hexaemeron/runbook.md`, of `docs/skills-runtime-dispatch/design-evidence.json`
against `.hexaemeron/design-evidence.json`, and of
`docs/decisions/drafts/dispatch-the-skills-runtime-rebuild-from-the-source.md`
against `.hexaemeron/design/draft-decision.md` each report no difference.

**Files.** Create `docs/skills-runtime-dispatch/study.md`,
`docs/skills-runtime-dispatch/runbook.md`,
`docs/skills-runtime-dispatch/design-evidence.json`,
`docs/skills-runtime-dispatch/conformance.py` (a copy of
`.hexaemeron/design/conformance.py`; the record's resolver command keeps
naming the `.hexaemeron/design/` path), the twenty selection reports under
`docs/skills-runtime-dispatch/reports/selection/`, and
`docs/decisions/drafts/dispatch-the-skills-runtime-rebuild-from-the-source.md`.
Update `.horos/boundary.json` and `.horos/census.json` by rescanning. Change
`tests/check-map-v1.json` only if the ownership resolver refuses the new paths;
`docs` owns them as it stands. The audit log named above and its generated
synopsis are written by the round.

**Tests.** No new test; the root suite's boundary, census and decision-record
tests must stay green with the new files present, and the decision draft must
satisfy the draft shape Hypomnema checks. Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`.

**Disciplines.** phylax: none, this step adds documents and a read-only
resolver copy and opens no input path. ephoros: none, nothing here runs
unattended. metron: none, no performance claim. elenchus: none, no failure in
hand. hypomnema: the decision draft is the one standing record and the study's
design bridge must resolve to it once published.

## Step 2: Add the dispatch workflow and its test

**Goal.** Add `.github/workflows/dispatch-skills-runtime-rebuild.yml`, pinned
by a root test, so every push to `main` starts the destination's
`workflow_dispatch` job.

**Entry.** Step 1 is pushed and checkpointed; the design checker passes at
`step:2` (no cell is due there); the controller supplies the Step 2 branch
and parent.

**Exit.** The workflow exists with the seven narrow properties below, the new root test asserts each of them, and the absent-secret resolver report exists with value true. Run:

```sh
python3 scripts/run_checks.py --base fiat/1053-trigger-the-skills-runtime-rebuild-without --scope root --scope ci --scope repo-lints --scope docs --format json --report .hexaemeron/reports/step-2-checked.json
python3 tests/run_tests.py --elenchus-report .hexaemeron/reports/step-2-exit.json
```

Both exit 0. The seven properties: `permissions: {}`; the guard
`if: github.repository == 'wildcat-finance/skills'`; no checkout step; no
`github.token` or `secrets.GITHUB_TOKEN`; an explicit `::error::` refusal with
`exit 1` when `secrets.RUNTIME_DISPATCH_TOKEN` is empty; one
`gh api --method POST` step against
`repos/wildcat-finance/skills-runtime/actions/workflows/sync.yml/dispatches`
with `-f ref=main`; triggers on `push` to `main` and on `workflow_dispatch`
only. The resolver is
`python3 .hexaemeron/design/conformance.py absent-secret-fails-loudly --candidate source-dispatch`,
run once from the run worktree root after the workflow file is written and
before the push receipt, because the record blocks `step:3` on it. Its report
`.hexaemeron/reports/conformance/source-dispatch-absent-secret-fails-loudly.json`
must hold value `true`, and its copy sits under
`docs/skills-runtime-dispatch/reports/conformance/`.

**Files.** Create `.github/workflows/dispatch-skills-runtime-rebuild.yml` from
`.hexaemeron/design/candidates/source-dispatch/dispatch-skills-runtime-rebuild.yml`.
Extend `tests/test_skills_sh_package.py` with
`test_dispatch_workflow_stays_narrow`. Change `tests/test_python_contract.py`
only if its workflow classification sets require the new file; it invokes no
Python, so `PYTHON_WORKFLOWS` is unchanged. Add the resolver report copy under
`docs/skills-runtime-dispatch/reports/conformance/`. Rescan `.horos/`. The
audit log and synopsis are written by the round.

**Tests.** `test_dispatch_workflow_stays_narrow` reads the workflow text and asserts the seven properties in the Exit plus the trigger set; it fails against the file with any one of them removed. Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`.

**Disciplines.** phylax: this step opens the credential boundary; the token
is used only as `GH_TOKEN` for one dispatch call, the job checks nothing out
and declares `permissions: {}`. ephoros: the job runs unattended on every
merge; it prints `dispatching a rebuild for wildcat-finance/skills@<sha>` and
fails red with a named error when the secret is absent. metron: none, no
performance claim. elenchus: none unless the new test or a suite goes red,
then reproduce and guard before the next round. hypomnema: the two cheap
choices (no checkout; `workflow_dispatch` over `repository_dispatch`) live in
the workflow's header comment; the standing record is already published.

## Step 3: Correct the currency claims

**Goal.** Make every current-tense statement of the rebuild trigger true and
refuse the stale phrases by test.

**Entry.** Step 2 is pushed and checkpointed; the design checker passes at
`step:3`, consuming the `absent-secret-fails-loudly` report; the controller
supplies the Step 3 branch and parent.

**Exit.** The four current-tense documents carry none of the three stale phrases, the generated README describes the push-driven trigger, the phrase-refusing test exists, and the two Step 3 resolver reports exist with value true. Run:

```sh
python3 scripts/run_checks.py --base fiat/1053-trigger-the-skills-runtime-rebuild-without --scope root --scope repo-lints --scope docs --format json --report .hexaemeron/reports/step-3-checked.json
python3 tests/run_tests.py --elenchus-report .hexaemeron/reports/step-3-exit.json
```

Both exit 0. `scripts/portable_promise_machine.py` (the `_package_readme`
text only), `docs/skills-runtime-publication.md`, `INSTALL.md` and
`README.md` contain none of `hourly`, `an hour behind` or `up to an hour`. The
generated README says the package is rebuilt when the source `main` moves,
names the dispatch workflow and keeps the source commit line and the
destination name. `docs/skills-runtime-publication.md` states the expected gap
as about one minute and names the dispatch workflow, the secret and the
recovery command. The two resolvers are
`python3 .hexaemeron/design/conformance.py readme-claims-match-trigger --candidate source-dispatch`
and
`python3 .hexaemeron/design/conformance.py destination-workflow-untouched --candidate source-dispatch`,
run once each from the run worktree root after the edits are committed and
before the push receipt, because the record blocks `step:4` on them. Their
reports `source-dispatch-readme-claims-match-trigger.json` and
`source-dispatch-destination-workflow-untouched.json` under
`.hexaemeron/reports/conformance/` must hold value `true`, and their copies
sit under `docs/skills-runtime-dispatch/reports/conformance/`.

**Files.** Edit `scripts/portable_promise_machine.py`,
`docs/skills-runtime-publication.md`, `INSTALL.md`, `README.md` and
`tests/test_skills_sh_package.py`. Add the two report copies. Rescan
`.horos/`. The audit log and synopsis are written by the round.

**Tests.** Extend `tests/test_skills_sh_package.py` with `test_no_document_claims_an_hourly_rebuild`, which reads the four files and the generated README bytes and refuses the three phrases, and extend the existing generated-README assertions to require the dispatch workflow name and the source commit line. Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`.

**Disciplines.** phylax: none, the README text is a string literal and no
input path changes. ephoros: `docs/skills-runtime-publication.md` carries the
currency check and the new expected gap, which is the on-call answer to "is
the package current". metron: none, no performance claim. elenchus: none
unless a suite goes red. hypomnema: the documents change with the published
record so no current-tense text contradicts it; ADR-066's bytes stay.

## Step 4: Demonstrate the dispatch

**Goal.** Prove C4: a `workflow_dispatch` run of the destination job, started
with `RUNTIME_DISPATCH_TOKEN` by the exact command the workflow carries,
concludes `success`.

**Entry.** Step 3 is pushed and checkpointed; the design checker passes at
`step:4`, consuming the two Step 3 reports; `gh secret list -R wildcat-finance/skills`
names `RUNTIME_DISPATCH_TOKEN` (an operator action, asked for and confirmed in
chat before this step opens); the controller supplies the Step 4 branch and
parent.

**Exit.** The dispatch marker exists without any token value, the dispatched-run resolver report exists with value true, and the demonstration document records the observation. Run:

```sh
python3 scripts/run_checks.py --base fiat/1053-trigger-the-skills-runtime-rebuild-without --scope root --scope repo-lints --scope docs --format json --report .hexaemeron/reports/step-4-checked.json
python3 tests/run_tests.py --elenchus-report .hexaemeron/reports/step-4-exit.json
```

Both exit 0. `.hexaemeron/design/dispatch-marker.json` holds the UTC time and
the command of the operator's dispatch and no token value. The resolver is
`python3 .hexaemeron/design/conformance.py dispatched-run-succeeds --candidate source-dispatch`,
run once from the run worktree root after the destination run concludes and
before the push receipt, because the record blocks `integration` on it and the
final merge-step consumes it. Its report
`source-dispatch-dispatched-run-succeeds.json` under
`.hexaemeron/reports/conformance/` must hold value `true`, and its copy sits
under `docs/skills-runtime-dispatch/reports/conformance/`.
`docs/skills-runtime-dispatch/demonstration.md` records the marker time, the
destination run id, its `created_at` and `updated_at`, its conclusion, the
published source commit and the source `main` head at observation, and states
that the post-merge `push`-event firing is recorded in the task-issue closing
comment.

**Files.** Create `docs/skills-runtime-dispatch/demonstration.md` and the
report copy plus its observation file under
`docs/skills-runtime-dispatch/reports/conformance/`. Write
`.hexaemeron/design/dispatch-marker.json` (controller evidence, not
committed). Rescan `.horos/`. The audit log and synopsis are written by the
round.

**Tests.** No new test; the demonstration document passes the imprimatur and Hypomnema lints and the root suite stays green. Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-4.json`.

**Disciplines.** phylax: the token value never enters the marker, the report,
the observation file or the demonstration; the resolver reads GitHub and
dispatches nothing. ephoros: the demonstration records the correlation the
study's section 8 relies on, the destination run id beside the marker time.
metron: none, the observed run time is recorded, not targeted. elenchus: if
the destination run fails, read its log, name the cause in the demonstration
and stop; do not re-dispatch to hide it. hypomnema: none beyond the record
already published; the demonstration is evidence, not a decision.
