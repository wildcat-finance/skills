# Study: trigger the skills-runtime rebuild without depending on its schedule

Task issue: [skills#1053](https://github.com/wildcat-finance/skills/issues/1053),
`framework-130: The skills-runtime rebuild has never run on its schedule`.
Run branch `fiat/1053-trigger-the-skills-runtime-rebuild-without`, cut from
`main` at `9182d0adcb7e9a5330c259d9dc1e044b511711c2`. Design record:
`.hexaemeron/design-evidence.json`, SHA-256
`96d0624f9f2822b42ec2c0f13b9221ec2d9cc97b7aaeea9c30eae3da5ba3e0ba`, selected
candidate `source-dispatch`.

Assuming, unless corrected:

1. The starting ref is `main` at `9182d0adcb7e9a5330c259d9dc1e044b511711c2`.
   The interpreter is the one in `.python-version` (`3.14.6`), with stdlib
   `unittest`. The root suite is `python3 -m unittest discover -s tests`.
2. The cause of the missing schedule runs is GitHub-side and stays unproven.
   Section 2 rules out the organisation policy, the repository policy, the
   workflow state, the committer's access and the sixty-day inactivity rule.
   The chosen design does not depend on the cause: it adds a trigger that the
   `schedule` event plays no part in, and leaves the schedule in place as a
   fallback that is not relied on.
3. One operator step exists and the run cannot perform it. An operator creates
   the Actions secret `RUNTIME_DISPATCH_TOKEN` in `wildcat-finance/skills`
   (repository settings, Secrets and variables, Actions). Its value is a
   fine-grained personal access token whose resource owner is
   `wildcat-finance`, whose repository access is `wildcat-finance/skills-runtime`
   only, and whose only repository permission is Actions: read and write.
   GitHub's permission table for the dispatch endpoint requires exactly that.
   Steps 1 to 3 do not need the secret. Step 4 does, as its entry condition.
4. This run does not change `distribution/skills-runtime/sync.yml`, so no
   workflow-scope push to `wildcat-finance/skills-runtime` is made and the
   drift guard is not touched. The canonical file stays at SHA-256
   `0d2ba3377e1a75b44395122b77836af8d1cabbbe3608c5e9700c18f3ae63f9ee`, the
   digest of the file at the starting ref, which `diff` shows byte-identical
   to the published copy at skills-runtime commit `f5a6076b`.
5. `gh` is present on GitHub's `ubuntu-latest` runner image, which is where
   the new workflow runs. If a runner image ever drops it, the same request
   is one `curl` call to the same endpoint and the workflow changes one step.
6. Step numbering for the pending conformance evidence follows the four-step
   shape in section 1. The runbook derives from it; renumbering the steps
   means rebuilding the record's `blocks` values first with
   `python3 .hexaemeron/design/build_design_evidence.py`.
7. A `workflow_dispatch` run of a workflow can be started only once the
   workflow file exists on the default branch, so the new source workflow
   cannot be fired from the run branch before the run PR merges. The
   pre-merge demonstration therefore has the operator run the exact command
   the workflow carries, from their own shell with the token they created,
   and the run observes the result read-only. The first `push`-driven firing
   is observed after the merge and recorded where section 8 says.
8. The organisation may restrict fine-grained personal access tokens or
   require their approval. That is not readable from here. If the operator
   cannot mint one, the fallback is a GitHub App installed on
   `wildcat-finance/skills-runtime` with Actions write, whose installation
   token is minted per run; that changes one step of the new workflow and
   nothing else in this study, and would be a study amendment.
9. Historical records keep their bytes: ADR-066,
   `docs/skills-runtime-split-study.md`, the #949 audit rounds and the two
   merged PR bodies describe what was true when written. The hourly claim
   is corrected where it is still presented as current, listed in section 3.

## 1. Problem statement

`wildcat-finance/skills-runtime` publishes the installable Promise Machine
package. Its only rebuild path is the destination workflow's `schedule`
trigger, `cron: "17 * * * *"`, and that trigger has never fired. Checked at
2026-09-17T21:09Z:

```text
$ gh api 'repos/wildcat-finance/skills-runtime/actions/runs?event=schedule&per_page=1' --jq .total_count
0
```

The workflow has three runs since the repository was created on
2026-08-30T06:39:26Z, all `workflow_dispatch`: 2026-08-30T11:31Z failure,
2026-08-31T17:50Z success, 2026-08-31T18:37Z success. Roughly 430 hourly
firings have been missed. The published package names source commit
`51fb586e41f67bff1cd53bed8414e3fc63ff48cb` while `main` is at
`9182d0adcb7e9a5330c259d9dc1e044b511711c2`, so every install since
2026-08-31T18:37Z has received a package built by a seventeen-day-old
generator from seventeen-day-old bytes, under a README that says it is
rebuilt hourly.

**Who this is for.** The person installing with
`npx skills add wildcat-finance/skills-runtime --skill promise-machine`, who
must be able to trust the package's currency claim; and the maintainer of
`wildcat-finance/skills`, who should not have to dispatch the job by hand.

**What is built.** A workflow in `wildcat-finance/skills`,
`.github/workflows/dispatch-skills-runtime-rebuild.yml`, that runs on every
push to `main` and on manual dispatch and starts the destination's existing
`workflow_dispatch` job with `RUNTIME_DISPATCH_TOKEN`; a test that pins the
new workflow's narrow shape; corrected wording in the generated `README.md`
and the three documents that repeat the hourly claim; and one decision record
that amends ADR-066's hourly statement. The destination job is not changed.

**Working prototype.** The four criteria below hold, each by a command.

- C1, the workflow. `.github/workflows/dispatch-skills-runtime-rebuild.yml`
  exists on the run branch with `permissions: {}`, the guard
  `if: github.repository == 'wildcat-finance/skills'`, no checkout step, no
  use of `github.token`, an explicit `::error::` refusal with `exit 1` when
  `secrets.RUNTIME_DISPATCH_TOKEN` is empty, and one
  `gh api --method POST repos/wildcat-finance/skills-runtime/actions/workflows/sync.yml/dispatches -f ref=main`
  step. Proved by a new test in `tests/test_skills_sh_package.py` under the
  root suite, and by `python3 .hexaemeron/design/conformance.py absent-secret-fails-loudly`.
- C2, the claims. `scripts/portable_promise_machine.py`,
  `docs/skills-runtime-publication.md`, `INSTALL.md` and `README.md` no longer
  contain `hourly`, `an hour behind` or `up to an hour`, and the generated
  README describes the trigger that exists. Proved by a new test in
  `tests/test_skills_sh_package.py` under the root suite, and by
  `python3 .hexaemeron/design/conformance.py readme-claims-match-trigger`.
- C3, the boundary. `git diff --name-only 9182d0adcb7e9a5330c259d9dc1e044b511711c2..HEAD -- distribution/`
  prints nothing: the destination job's permissions, drift guard and schedule
  are untouched and no workflow-scope push was needed. Proved by
  `python3 .hexaemeron/design/conformance.py destination-workflow-untouched`.
- C4, the dispatch. After the operator runs the exact dispatch command with
  `RUNTIME_DISPATCH_TOKEN` from their own shell, a `workflow_dispatch` run of
  `.github/workflows/sync.yml` in `wildcat-finance/skills-runtime` is created
  within fifteen minutes of the recorded marker and concludes `success`, which
  by the destination job's own logic means the published README now names
  the source `main` head or already did. Proved by
  `python3 .hexaemeron/design/conformance.py dispatched-run-succeeds`, which
  reads `.hexaemeron/design/dispatch-marker.json` and GitHub, dispatches
  nothing, and records the published source commit beside `main` in its
  observation file.

**Demo path.** Step 4 runs it. Entry: `gh secret list -R wildcat-finance/skills`
names `RUNTIME_DISPATCH_TOKEN`. The operator runs
`gh api --method POST repos/wildcat-finance/skills-runtime/actions/workflows/sync.yml/dispatches -f ref=main`
with `GH_TOKEN` set to that token in their own shell (an `Ask first` action;
the run never sees the value), the step writes
`.hexaemeron/design/dispatch-marker.json` with the UTC timestamp, and the
resolver observes C4. Then C1 to C3 by their commands and the root suite.
After the run PR merges, the operator confirms the first `push`-event run with
`gh run list --repo wildcat-finance/skills --workflow dispatch-skills-runtime-rebuild.yml --limit 3`
and the destination run that follows it; section 8 says where that goes.

**Step shape** (the runbook derives from this; the record's `blocks` values
name these numbers):

1. Scaffold: commit this study and the runbook under
   `docs/skills-runtime-dispatch/`, publish the decision record at
   `docs/decisions/drafts/dispatch-the-skills-runtime-rebuild-from-the-source.md`
   byte-for-byte from `.hexaemeron/design/draft-decision.md`, and add the
   `check-map` scope entries the new paths need. Root suite green.
2. The workflow and its test: `.github/workflows/dispatch-skills-runtime-rebuild.yml`
   and the pinning test. Earns `absent-secret-fails-loudly` (blocks `step:3`).
3. The claims: the generator's README text, `docs/skills-runtime-publication.md`,
   `INSTALL.md`, `README.md`, and the test that refuses the stale phrases.
   Earns `readme-claims-match-trigger` and `destination-workflow-untouched`
   (both block `step:4`).
4. Demonstrate: the demo path above. Earns `dispatched-run-succeeds` (blocks
   `integration`; its report is due before the last merge-step).

**Reading chosen.** The optional `success-criteria` declaration is not
written. It binds each criterion to the exact effective Exit command of a
step the runbook has not yet derived, and a mismatch there refuses the runbook
receipt; the four criteria above already name their commands, and the design
record carries the ones that gate transitions.

## 2. Prior art

**The canonical workflow.**
[`distribution/skills-runtime/sync.yml`](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/distribution/skills-runtime/sync.yml)
is 90 lines and 3,377 bytes. Triggers: `schedule` at `17 * * * *` and
`workflow_dispatch`. Permissions `contents: write`. Concurrency group
`rebuild-published-package`, `cancel-in-progress: false`. Job guard
`if: github.repository == 'wildcat-finance/skills-runtime'`. It checks itself
out with `persist-credentials: false`, clones the public source over a literal
URL, refuses when it differs from the canonical copy, generates, verifies,
replaces the tree and commits only when bytes changed, pushing with
`x-access-token:${GITHUB_TOKEN}`. Its header records that `GITHUB_TOKEN`
cannot write under `.github/workflows/`, so a change to the file needs a
person with `workflow` scope. The published copy at
[skills-runtime `f5a6076b`](https://github.com/wildcat-finance/skills-runtime/blob/f5a6076b42cedb0ebc3f6885b44ff381f0e82563/.github/workflows/sync.yml)
is byte-identical (`diff` exits 0). Both triggers this run needs already
exist in it: `workflow_dispatch` is what the new source workflow fires.

**The destination's run history.** Workflow id `345741143`, state `active`,
`created_at` and `updated_at` both `2026-08-30T06:43:49Z`. Runs of
`.github/workflows/sync.yml`: `33309124188` (2026-08-30T11:31:08Z, failure,
23 s, stopped at the drift guard because the canonical copy had not reached
`main`; every later step skipped), `33421722485` (2026-08-31T17:50:14Z to
17:50:38Z, success, 24 s) and `33426056654` (2026-08-31T18:37:34Z to
18:38:01Z, success, 27 s). GitHub's own CodeQL `Scheduled` runs, event
`dynamic`, do fire in the repository: 2026-09-04, 2026-09-10 and 2026-09-17.
Commits: `0bf04c5e` (2026-08-30T06:43:43Z) and `f5a6076b`
(2026-08-30T06:54:49Z) by `laurenceday`, both GitHub-verified; `fefb05c6` and
`c08b88cb` by the job, rebuilding from `a2b634d8` and `51fb586e`. Commands:
`gh api repos/wildcat-finance/skills-runtime/actions/workflows`,
`gh api 'repos/wildcat-finance/skills-runtime/actions/runs?per_page=10'`,
`gh api repos/wildcat-finance/skills-runtime/actions/runs/<id>/jobs`,
`gh api repos/wildcat-finance/skills-runtime/commits`.

**What is ruled out.** The organisation Actions policy: unreadable from here
(`gh api orgs/wildcat-finance/actions/permissions` returns 403, needs
`admin:org`), but sibling repositories in the same organisation run
`schedule` events: `skills` 3,666, `skills-marketplace` 2,904 (private,
`*/5 * * * *`), `wildcat-app-v2` 136, `v2-app-private` 100,
`shoggoth-wave-atlas` 75 (public, created 2026-08-23, first schedule run
2026-08-30T06:39:35Z, nine seconds after skills-runtime was created),
`governance-ui` 10. Command per repository:
`gh api "repos/wildcat-finance/<repo>/actions/runs?event=schedule&per_page=1" --jq .total_count`.
The repository policy: `{"enabled":true,"allowed_actions":"all","sha_pinning_required":false}`.
The committer's access: `laurenceday` is still an organisation member and
repository admin, so the "last committer lost access" explanation fails.
The repository is not a fork, not archived, `pushed_at` 2026-08-31T18:37:58Z,
inside GitHub's sixty-day inactivity window. GitHub documents that the
`schedule` event "can be delayed during periods of high loads" and that
scheduled workflows run only on the default branch; neither explains 430
consecutive misses. What remains is GitHub-side: the trigger was never
registered for this workflow, and only a firing could prove otherwise.

**The claim sites.** The generator writes the README in `_package_readme` at
[`scripts/portable_promise_machine.py`](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/scripts/portable_promise_machine.py)
lines 770 to 805: "A scheduled workflow in this repository clones the public
source hourly, regenerates the package, verifies it, and commits only when
the bytes changed."
[ADR-066](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/docs/decisions/ADR-066-publish-the-skills-sh-payload-from-its-own-repository.md)
records "An install can therefore be up to an hour behind this repository's
`main`. That lag is the accepted cost of the split." and rejects "Push from
this repository on merge" because it "Needs a fine-grained token stored as a
secret, and buys latency below the hour already accepted."
[`docs/skills-runtime-split-study.md`](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/docs/skills-runtime-split-study.md)
section 4 option B is the same rejection and section 8 states the two on-call
questions: is the package current, and is the job failing silently.
[`docs/skills-runtime-publication.md`](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/docs/skills-runtime-publication.md)
says the workflow "runs hourly and on manual dispatch" and documents the
currency check (README source commit against `skills` `main`). `INSTALL.md`
lines 157 to 160 and `README.md` lines 153 to 155 repeat "rebuilds the package
hourly" and "up to an hour behind". All four current-tense sites change in
Step 3; ADR-066 and the split study are historical and stay.

**Tests that pin the subject.**
[`tests/test_skills_sh_package.py`](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/tests/test_skills_sh_package.py)
holds 20 tests, all passing at the starting ref (`Ran 20 tests`, `OK`).
`test_published_workflow_copy_stays_narrow` (lines 686 to 716) pins the
canonical workflow: `permissions:\n  contents: write\n`; none of `actions:`,
`packages:`, `id-token:`, `pull-requests:` anywhere in the file; the
repository guard; the literal clone URL; no `cp|mv|rm|tee|>` write under
`.github/workflows`; `persist-credentials: false`;
`x-access-token:${GITHUB_TOKEN}`; the README-parse refusal string. Because
the new source workflow is a different file, those assertions are not
disturbed, and the new test for it follows the same shape.
`test_package_action_writes_a_complete_installable_tree` (around line 570)
asserts the generated README names `wildcat-finance/skills-runtime` and the
source commit; the Step 3 wording keeps both. `tests/check-map-v1.json:409`
maps `distribution/skills-runtime` to scope `root` and line 375 maps
`.github` to scope `ci`.

**Push-to-main workflows here.** Every workflow under `.github/workflows/`
that runs on merge uses `on: push: branches: [main]` with `workflow_dispatch`,
for example
[`repo.yml`](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/.github/workflows/repo.yml)
and `plugins.yml`. The new workflow uses the same trigger pair.
[`sync-skills-marketplace.yml`](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/.github/workflows/sync-skills-marketplace.yml)
is the organisation's precedent for a cross-repository credential: it runs
in the mirror under `if: github.repository == 'wildcat-finance/skills-marketplace'`,
declares `permissions: {}`, and pushes with `MARKETPLACE_SYNC_TOKEN`, a
fine-grained token holding Contents and Workflows write on the mirror. The
new workflow copies the empty permissions and the guard, and needs a far
narrower token: Actions write, one repository, no contents access.

**Secrets today.** `gh secret list -R wildcat-finance/skills` lists none;
`-R wildcat-finance/skills-runtime` lists none;
`-R wildcat-finance/skills-marketplace` lists `MARKETPLACE_SYNC_TOKEN`. Any
source-driven trigger therefore needs a new secret in `wildcat-finance/skills`
that only an operator can create (assumption 3).

**Outside the organisation.** GitHub's REST reference for
[Create a workflow dispatch event](https://docs.github.com/en/rest/actions/workflows?apiVersion=2022-11-28#create-a-workflow-dispatch-event)
requires the workflow to declare `workflow_dispatch`, takes `ref` and optional
`inputs`, and its fine-grained permission table lists "Actions" repository
permissions (write). The sibling
[Create a repository dispatch event](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#create-a-repository-dispatch-event)
needs "Contents" (write), which is why `repository_dispatch` is not used: it
would hand the source a token that can write the destination's tree. The
[events reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
records the schedule delay note, the sixty-day rule for public repositories,
and that `workflow_dispatch` "will only trigger a workflow run if the workflow
file exists on the default branch", which is assumption 7.

**The last two merged pull requests, per subject.** For the generator,
[#1628](https://github.com/wildcat-finance/skills/pull/1628) (merged
2026-09-14T16:05Z, "Complete publisher conformance and the macOS deployment
kit") and [#1550](https://github.com/wildcat-finance/skills/pull/1550)
(2026-09-12T21:51Z, "Restore the main corpus and portable package checks");
neither body carries a `## Carried forward` section (checked with
`gh api repos/wildcat-finance/skills/pulls/<n> --jq .body`), so there was
nothing to carry from them. For the canonical workflow, the only merged
change is the #949 run: its run PR
[#1038](https://github.com/wildcat-finance/skills/pull/1038) (2026-08-31T11:10Z)
and its step PR [#959](https://github.com/wildcat-finance/skills/pull/959)
(2026-08-31T07:54Z). #959 has no `## Carried forward` section. #1038's ten
items, each answered:

- #854 closed by #961; nothing to do here.
- #971, the stale generator-aggregate entry in `hexctl.py`: still open, still
  outside this run's files; named as a non-goal.
- #888, ADR-number allocation: since resolved by ADR-077's draft path, which
  this run uses for its record; nothing else carried.
- #881, Lazarus and macOS temporary paths: unrelated, not carried.
- "The destination's first green hourly rebuild after these bytes reach
  `main` has not been observed": this is the problem statement. It has still
  not been observed and, on the evidence above, will not be by schedule.
- A person-assembled directory carrying the manifest path is treated as a
  prior package: unchanged, no generator behaviour changes here.
- Package construction holds roughly 21 MB in memory: unchanged, non-goal.
- The destination job trusts the generator at the source tip: unchanged, and
  restated in section 9 because the new trigger does not widen it.
- The copy order (empty, then copy) has no runner test: unchanged; the
  destination job is not edited.
- The package carries no signature: unchanged, non-goal.

**Audit records.** `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
run from the target root exits 0 and reports `committed=match` for all 95
source and view pairs, so the committed synopses are the current reading view.
In-scope sources, which view was read, and why:

- `audit/rounds/fiat-949-move-the-skills-sh-payload-to-its-own-reposi.md`
  (source SHA-256 `6558e8c809cd2a054ed89e405fb61e4786b43d0e7895fa9143a03c14a54c4c4b`),
  read as its synopsis `audit/rounds/fiat-949-move-the-skills-sh-payload-to-its-own-reposi.synopsis.md`.
  It is the predecessor run for this subject. Six rounds. Step 1 round 1:
  S1-R1-01 high, `scripts/portable_promise_machine.py`, `package --out`
  destroyed a populated destination, fixed and guarded in `69b3180c`;
  S1-R1-02 low, a symlink guard that could never fire, removed in the same
  commit; Elenchus verdict `guarded`; Covered
  `generator-output-escape=reviewed; suite-coverage-loss=reviewed; authored-file-loss=reviewed`,
  five destination concerns `not-applicable`; Not checked: the destination
  and its job, and `npx skills add` against a published repository. Step 1
  round 2: no findings, verdict `null`, three mutations driven and each
  failed. Step 2 round 1: S2-R1-01 medium, `distribution/skills-runtime/sync.yml`,
  `actions/checkout@v4` persisted a push-capable token beside code cloned
  from another repository, fixed and guarded in `dda3330f`; S2-R1-02 low, an
  empty source SHA committed as a success, fixed in the same commit; verdict
  `guarded`; Covered
  `token-scope=reviewed; publish-unverified=reviewed; workflow-drift=reviewed; stale-destination=reviewed; broken-install-window=reviewed; generator-output-escape=reviewed`,
  two `not-applicable`; Not checked: "whether the scheduled job runs green
  ... No scheduled or dispatched run has therefore been observed". Step 2
  round 2: verdict `null`, four mutations each failed one case, a fifth was
  redriven after a quoting fault; Not checked repeats that no scheduled or
  dispatched run has been observed. Step 3 round 1: S3-R1-01 low,
  `INSTALL.md`, a relative link to the publication guide resolved to
  nothing, fixed in `3b9ce1e1`; S3-R1-02 medium,
  `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, the generator-aggregate
  registry names an emptied prefix, not fixed here, filed as #971; verdict
  `guarded`; Not checked: "whether the published package stays current once
  this stack merges. The destination job has never completed a publish".
  Step 3 round 2: verdict `null`; Not checked: the same two boundaries.
  Leads not pursued across the rounds: the manifest-marker sentinel, the
  21 MB in-memory build, the unsigned package, the untested copy order, the
  trust in the source tip, the historical documents left naming removed
  paths, and `check` failing on a clean checkout by design. Every one of
  those leads is unchanged by this run, because it edits neither the
  generator's package logic nor the destination job. The three "no scheduled
  run observed" entries are the observation this run turns into a trigger.
- `audit/AUDIT.md` (14,172 lines), read as `audit/AUDIT_SYNOPSIS.md`. Zero
  lines match `skills-runtime` or `sync.yml` in either file
  (`grep -c`), so no finding there bears on this subject.
- `audit/rounds/fiat-shoggoth-front-door-derived.synopsis.md` and
  `audit/rounds/fiat-1275-elenchus-emits-the-fixed-and-guarded-result.synopsis.md`
  each name `wildcat-finance/skills-runtime` once, as a link checked for
  shape and as the reason the runtime prefix is untracked. Neither carries a
  finding on the trigger, the generator's README text or the workflow.

No known-failure inventory is carried. Every finding in the in-scope records
is fixed and guarded, removed, or owned by #971 in a file this run does not
touch; none names a failure the files in section 3 must guard before product
work starts.

## 3. Constraints and non-goals

Starting ref `main` at `9182d0adcb7e9a5330c259d9dc1e044b511711c2`. Interpreter
per `.python-version` (`3.14.6`), stdlib `unittest`, root suite
`python3 -m unittest discover -s tests`. The scoped runner
`python3 scripts/run_checks.py --base origin/main` is the pre-commit gate the
repository documents; a dirty worktree reddens its dead-code check, so it runs
on a committed tree.

Files this run changes, all in `wildcat-finance/skills`:
`.github/workflows/dispatch-skills-runtime-rebuild.yml` (new),
`tests/test_skills_sh_package.py`, `scripts/portable_promise_machine.py`
(the `_package_readme` text only), `docs/skills-runtime-publication.md`,
`INSTALL.md`, `README.md`, `tests/check-map-v1.json` (scope entries for the
new paths), `docs/decisions/drafts/dispatch-the-skills-runtime-rebuild-from-the-source.md`
(new), `docs/skills-runtime-dispatch/study.md` and
`docs/skills-runtime-dispatch/runbook.md` (new, committed copies), and
`audit/rounds/fiat-1053-trigger-the-skills-runtime-rebuild-without.md`, the
run's audit log. Any edit to a tracked file changes the Horos census byte
counts, so each step re-runs the census the suite compares against. No plugin
package is touched, so the plugin-release gate does not fire.

Actions on other repositories: none by the run. The operator creates one
secret in `wildcat-finance/skills` and runs one dispatch command from their
own shell (assumptions 3 and 7). Nothing is pushed to
`wildcat-finance/skills-runtime`.

Non-goals:

- Changing `distribution/skills-runtime/sync.yml` in any way, including
  re-registering or removing its schedule, adding `inputs` to its
  `workflow_dispatch`, or the `[ -f ... ]` precheck #1052 asks for. Each of
  those needs a person with `workflow` scope to push the destination, and
  #1052 records that its change is not self-contained. This run's design
  leaves the drift guard alone, so #1052 stays open as its own coordinated
  change and is not absorbed. A later run that does edit the file may fold
  the precheck in; this one states the coupling and does not take it.
- Proving why the schedule never fired. Assumption 2.
- Rebuilding on pull requests, forks or branches other than `main`. The
  package is published from `main` only.
- Passing the source commit into the destination job. The destination has no
  `inputs` and adding one is the non-goal above; correlation uses the source
  commit the package already records (section 8).
- Signing the published package, verifying the marketplace mirror (#836),
  the moved-branch plugin report (#1171), the registry entry (#971) or the
  plugin update re-pin (#895). Named because they share the milestone bundle.
- Writing the ADR under a number. ADR-077 assigns numbers at integration;
  the record is authored as a numberless draft.
- Rewriting ADR-066, the split study, the #949 audit rounds or the merged PR
  bodies. Assumption 9.

## 4. Design options

The question is which event starts the rebuild and which credential, if any,
crosses the repository boundary. Four candidates were drawn; the record at
`.hexaemeron/design-evidence.json` selects one from checked gates and two
measurements, and `python3 .hexaemeron/design/build_design_evidence.py`
regenerates it from the declared trigger facts and measured YAML under
`.hexaemeron/design/candidates/`.

**`source-dispatch`.** A new workflow in `wildcat-finance/skills` on `push`
to `main` and `workflow_dispatch`, `permissions: {}`, no checkout, guarded to
the source repository, that refuses loudly when `RUNTIME_DISPATCH_TOKEN` is
empty and otherwise runs
`gh api --method POST repos/wildcat-finance/skills-runtime/actions/workflows/sync.yml/dispatches -f ref=main`.
The destination job keeps its `GITHUB_TOKEN`, `contents: write`, drift guard,
verification and schedule. Trade: one operator-created secret, and the source
repository now holds a credential that can start, and only start, a job in
another repository. Draft: `.hexaemeron/design/candidates/source-dispatch/dispatch-skills-runtime-rebuild.yml`,
1,913 bytes.

**`reregister-schedule`.** Change the cron expression in the canonical copy
and push the published copy with `workflow` scope, so GitHub re-registers the
schedule. Trade: rests on an unproven cause, cannot be verified until the
next firing, keeps up to an hour of lag, and leaves the README claim
unverifiable until then. Draft delta: one changed line, 25 bytes.

**`destination-poll-faster`.** Keep the pull model and add a second cron
entry, `*/10 * * * *`, in the destination. Trade: depends on the very
`schedule` event that never fired, and still needs the workflow-scope push.
Draft delta: one added line, 27 bytes.

**`source-push`.** Generate in `wildcat-finance/skills` on push to `main` and
push the tree into the destination with a contents-write token, ADR-066's
rejected option B. Trade: a credential that can write the published tree
crosses the boundary, and the destination's self-contained token story, drift
guard and verify-before-commit are replaced rather than kept. Draft:
`.hexaemeron/design/candidates/source-push/publish-skills-runtime.yml`,
2,411 bytes.

**Criteria.** Three selection gates, boolean `equals true`, each blocking
`design-lock`: `trigger-independent-of-schedule` (correctness, from the
candidate's declared trigger: does the path from a source merge to a rebuild
pass through the `schedule` event), `destination-permissions-unchanged`
(compatibility: the destination job keeps `contents: write` only and no
credential able to write its tree is created), and
`credential-loss-leaves-package-intact` (recovery: an absent or revoked
credential leaves the last published package where it is). Two selection
metrics, both minimised: `worst-case-trigger-wait` in milliseconds, derived
from the trigger definition and excluding runner queue time (3,600,000 for an
hourly cron, 600,000 for a ten-minute cron, 0 for an event fired by the push
itself), and `workflow-yaml-bytes-added`, the bytes of workflow YAML each
candidate adds across both repositories, measured from the drafts.

**Matrix.** `reregister-schedule` and `destination-poll-faster` fail
`trigger-independent-of-schedule`. `source-push` fails
`destination-permissions-unchanged`. `source-dispatch` passes all three gates
and, against the one other candidate that passes the schedule gate, ties on
wait (0 ms) and adds fewer bytes (1,913 against 2,411). The frontier under
`unique-frontier` is `source-dispatch` alone;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition design-lock`
prints `clean` and exits 0.

**Conformance, pending.** Four gates the build earns, each resolved by
`python3 .hexaemeron/design/conformance.py <criterion> --candidate source-dispatch`,
which writes `reports/conformance/source-dispatch-<criterion>.json` below
the record directory, refuses to overwrite an existing report, and dispatches
nothing: `absent-secret-fails-loudly` (recovery, blocks `step:3`),
`readme-claims-match-trigger` (correctness, blocks `step:4`),
`destination-workflow-untouched` (compatibility, blocks `step:4`) and
`dispatched-run-succeeds` (correctness, blocks `integration`). The record
carries the same four cells for the three removed candidates so the matrix is
complete; the resolver refuses to resolve them because no step of theirs is
built.

## 5. Risk register seed

The run adds a workflow that holds a cross-repository credential and runs on
every merge, and it changes prose that readers rely on for currency. That is
where the audit loop should look.

```risk-register
dispatch-token-scope | RUNTIME_DISPATCH_TOKEN as created and as used | the token grants Actions read and write on wildcat-finance/skills-runtime only; the workflow never checks code out, never uses github.token, and cannot write the destination tree
absent-secret-silent | the dispatch job when the secret is missing or revoked | the job fails with an explicit ::error:: and exit 1 rather than dispatching nothing and going green
source-job-permissions | the new workflow's permissions block | it declares permissions: {} and the test refuses any scope string
fork-or-mirror-firing | the job in a fork or in skills-marketplace | if: github.repository == 'wildcat-finance/skills' keeps it from running anywhere else
destination-untouched | distribution/skills-runtime/sync.yml and its published copy | git diff against the starting ref shows nothing under distribution/, so no workflow-scope push and no change to the drift guard, permissions or schedule
stale-claim-remains | every current-tense statement of the rebuild trigger | scripts/portable_promise_machine.py, docs/skills-runtime-publication.md, INSTALL.md and README.md contain none of hourly, an hour behind, up to an hour, and the generated README still names the destination and the source commit
dispatch-burst | several merges to main inside one destination run | the destination's concurrency group queues one pending run and cancels the older pending one, and every run clones the tip, so the newest merge is always built
demo-never-dispatches | the conformance resolver and the run's own actions | conformance.py only reads GitHub and the marker file; the dispatch is the operator's command, recorded with its timestamp
report-overwrite | a rerun of the resolver after a report is receipted | conformance.py refuses when the report path exists
```

## 6. Glossary seeds

- **Destination.** `wildcat-finance/skills-runtime`, the repository that
  publishes the package.
- **Destination job.** `.github/workflows/sync.yml` in the destination, whose
  canonical copy is `distribution/skills-runtime/sync.yml` here.
- **Dispatch workflow.** `.github/workflows/dispatch-skills-runtime-rebuild.yml`
  in `wildcat-finance/skills`, added by this run.
- **Dispatch token.** `RUNTIME_DISPATCH_TOKEN`, the operator-created secret
  with Actions write on the destination only.
- **Source commit.** The `wildcat-finance/skills` commit a published package
  records in its `README.md`.
- **Marker.** `.hexaemeron/design/dispatch-marker.json`, the UTC timestamp
  and command of the operator's demonstration dispatch, written by Step 4 and
  read by the resolver.
- **Trigger wait.** The time between a source merge and the destination job
  starting, excluding runner queue time; zero for an event-driven trigger,
  the cron interval for a schedule.

## 7. Sources

- Issue [#1053](https://github.com/wildcat-finance/skills/issues/1053);
  issues #1052, #836, #1171, #971, #895 (milestone 90) and #854, #888, #881
  (carried in #1038).
- Pull requests [#1038](https://github.com/wildcat-finance/skills/pull/1038),
  [#959](https://github.com/wildcat-finance/skills/pull/959),
  [#1628](https://github.com/wildcat-finance/skills/pull/1628),
  [#1550](https://github.com/wildcat-finance/skills/pull/1550).
- At `9182d0adcb7e9a5330c259d9dc1e044b511711c2`:
  `distribution/skills-runtime/sync.yml`, `scripts/portable_promise_machine.py`,
  `tests/test_skills_sh_package.py`, `tests/check-map-v1.json`,
  `.github/workflows/sync-skills-marketplace.yml`, `.github/workflows/repo.yml`,
  `docs/decisions/ADR-066-publish-the-skills-sh-payload-from-its-own-repository.md`,
  `docs/decisions/ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md`,
  `docs/skills-runtime-publication.md`, `docs/skills-runtime-split-study.md`,
  `INSTALL.md`, `README.md`, `audit/AUDIT_SYNOPSIS.md`,
  `audit/rounds/fiat-949-move-the-skills-sh-payload-to-its-own-reposi.synopsis.md`.
- `wildcat-finance/skills-runtime`: workflow `345741143`, runs `33309124188`,
  `33421722485`, `33426056654`, commits `0bf04c5e`, `f5a6076b`, `fefb05c6`,
  `c08b88cb`; the `gh api` commands in section 2 re-fetch each.
- GitHub docs: the workflow dispatch and repository dispatch endpoints, the
  fine-grained token permission table at
  [permissions required for fine-grained personal access tokens](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens?apiVersion=2022-11-28),
  and the events reference, all linked in section 2.
- The plugin's contracts at `plugins/hexaemeron/skills/protasis/SKILL.md`,
  `plugins/hexaemeron/skills/hypomnema/SKILL.md` and the four other
  disciplines cited below.

## 8. Signals, and the questions behind them

The dispatch workflow runs unattended on every merge, so it owes answers to
three questions; [ephoros](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what each signal must carry.

Did the merge reach the destination? The dispatch run's log prints
`dispatching a rebuild for wildcat-finance/skills@<sha>`, and the destination
run that follows commits `Rebuild from wildcat-finance/skills@<sha>` with the
same value; the source commit is the correlation key across both repositories
and needs no new plumbing. Emitted by Step 2.

Is the token gone? A missing or revoked `RUNTIME_DISPATCH_TOKEN` turns the
dispatch run red on the next merge with `::error::RUNTIME_DISPATCH_TOKEN is
not set` or an HTTP 401 or 403 from the endpoint; a red run on `main` is
visible in the Actions tab and mailed to watchers. Recovery is to recreate the
secret and rerun with `gh workflow run dispatch-skills-runtime-rebuild.yml`.
Emitted by Step 2.

Is the published package current? Unchanged from the split study:
`gh api repos/wildcat-finance/skills-runtime/contents/README.md --jq .content | base64 -d | grep -o '[0-9a-f]\{40\}'`
against `gh api repos/wildcat-finance/skills/commits/main --jq .sha`. What
changes is the expected gap: about one minute after a merge (the observed
destination run takes 24 to 27 seconds plus queue time), not an hour. Step 3
rewrites that expectation in `docs/skills-runtime-publication.md`.

The run pull request carries `Closes wildcat-finance/skills#1053`, as
Fiat's push discipline requires, so GitHub closes the issue when that pull
request merges into `main`. The merge is also the first `push` event the
dispatch workflow sees, so the run's closing comment on #1053, posted after
the merge, names both run ids: the `push`-event dispatch run and the
destination run it started. If neither has appeared within fifteen minutes
of the merge, the comment says so and the failure is filed as its own issue.

## 9. Boundaries, per capability

The run opens one boundary: a workflow in the source that holds a credential
for another repository. [phylax](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the boundary list and the controls.

What is worth taking at it is the token. The controls: its scope is Actions
write on one repository, so the most it can do is start the destination job,
which then runs only what its own `main` holds; the job that uses it checks
nothing out, so no code from this tree executes beside it; the job declares
`permissions: {}`, so `GITHUB_TOKEN` grants nothing; the guard keeps the job
out of forks and the marketplace mirror; and the test in Step 2 refuses any
scope string, any checkout, and any `github.token` reference in the file.

The destination's boundary is unchanged: it still trusts the generator at the
source tip, still verifies before committing, still cannot write its own
workflow, and still publishes nothing on failure. Its `schedule` entry stays,
unrelied on.

Inside this repository the run adds no input path: the generator's README text
is a string literal, the tests read files under the tree, and the resolver
runs fixed `git` and `gh api` argv with no shell.

Tiers this study binds the build to:

- **Always.** Root suite and `python3 scripts/run_checks.py --base origin/main`
  on a committed tree before each step's exit. The imprimatur lint on every
  document that ships. The Horos census re-run after any tracked-file edit.
  `git diff --name-only 9182d0adcb7e9a5330c259d9dc1e044b511711c2..HEAD -- distribution/`
  empty at every step exit.
- **Ask first.** Creating `RUNTIME_DISPATCH_TOKEN`, and choosing its expiry.
  Running the demonstration dispatch, which consumes a destination runner and
  may publish a new package. Adding any workflow under `.github/workflows/`,
  which is CI. Pushing anything to `wildcat-finance/skills-runtime`. Widening
  the token beyond Actions write on one repository. Falling back to a GitHub
  App (assumption 8).
- **Never.** Commit a token or write its value into any file, log, marker or
  report. Widen the destination job's permissions or edit
  `distribution/skills-runtime/sync.yml`. Use `schedule` as the only trigger
  again. Use `repository_dispatch`, which needs Contents write. Let the
  dispatch job go green when the secret is absent. Rewrite ADR-066, the split
  study or an audit record. Claim a dispatch happened without the destination
  run id.

## 10. The budget, or its absence

None, and here is why. Nothing here is changed in the name of speed and no
performance claim is made about code. The one time figure, the worst-case
trigger wait, is a property of the trigger definition (0 ms for a push-driven
dispatch, 3,600,000 ms for the hourly cron) and is recorded as a selection
metric in the design record, not as a budget the build must hold or
re-measure. The destination job's 24 to 27 second run time is observed, not
targeted. [metron](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/plugins/hexaemeron/skills/metron/SKILL.md)
owns what a budget would carry if one were set; none is.

## 11. The fail-closed posture

In this repository the stop condition is the root suite,
`python3 -m unittest discover -s tests`, exiting non-zero, or a red
`invariants` check on the pull request. In the dispatch workflow it is an
empty secret or a non-2xx response from the dispatch endpoint, either of which
exits 1 and turns the run red; the job never dispatches nothing and reports
success. In the destination nothing changes: verification failure publishes
nothing and the last good package stays. At the design gates it is a
conformance report whose value is `false` or a missing report at its stop
point, which refuses the step or the integration rather than being scored.

A failure is worked under
[elenchus](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/plugins/hexaemeron/skills/elenchus/SKILL.md)
to its cause. The guard convention: a fix to the workflow lands with an
assertion in `tests/test_skills_sh_package.py` that fails against the
unfixed file, in the shape `test_published_workflow_copy_stays_narrow`
already uses; a fix to prose lands with the phrase-refusing test extended to
name the phrase. An assertion is never relaxed to pass a step, and a `false`
conformance report is never edited; a fresh observation replaces it only
after the old file is removed on purpose.

## 12. Decisions and their homes

One decision is expensive to reverse: the rebuild is started from the source
on merge, with a cross-repository Actions-write credential, and the hourly
schedule is no longer the mechanism the documents describe. It amends
ADR-066's "up to an hour behind" statement and its rejection of a
source-held token, while ADR-066 stays accepted for the split itself.
[hypomnema](https://github.com/wildcat-finance/skills/blob/9182d0adcb7e9a5330c259d9dc1e044b511711c2/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record and where each lives.

Its home is `docs/decisions/drafts/dispatch-the-skills-runtime-rebuild-from-the-source.md`,
a numberless draft under ADR-077, numbered at integration. The text is
written and linted at `.hexaemeron/design/draft-decision.md` (Hypomnema and
Imprimatur both exit 0 on it) and Step 1 publishes it byte-for-byte. Until
Step 1 lands, `hypomnema.py --study` reports H008 for the missing record, by
design. The generated README text, `docs/skills-runtime-publication.md`,
`INSTALL.md` and `README.md` change with it in Step 3, so no current-tense
document contradicts the record.

Two smaller choices are recorded in the workflow's own header comment rather
than a record: why the job checks nothing out, and why `workflow_dispatch`
rather than `repository_dispatch`. Both are cheap to reverse and the comment
is where the next reader meets them.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | source-dispatch
record | docs/decisions/drafts/dispatch-the-skills-runtime-rebuild-from-the-source.md
```
