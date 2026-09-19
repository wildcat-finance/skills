# Study: refuse a later step's commits carried into a lower waiting branch

Task issue: [wildcat-finance/skills#1480](https://github.com/wildcat-finance/skills/issues/1480). Packet handle `fiat-1480-study-surveyor`. Every repository line number below is read at the starting ref `f0fa0c6632bd5fbef7f35e731646c32741ef282a` unless a commit is named beside it.

Assuming, unless corrected:

1. The run builds from `main` at `f0fa0c6632bd5fbef7f35e731646c32741ef282a` on run branch `fiat/1480-refuse-a-later-step-s-commits-carried-into`, with hexaemeron package `1.6.51`, Fiat ledger `fiat-v6.65.1` (71 rows) and the three init contracts `protasis-design-evidence/v1`, `protasis-gate-commands/v1`, `protasis-success-criteria-execution/v1`.
2. The guard keeps the evidence split its neighbours use: bounded native Git reads over objects already fetched into the run clone at `next`; GitHub REST only where `done merge-step` already reads it. A missing local object is an unknown that refuses, not a reason to fetch.
3. A push receipt's `verified_commits` list is the exact statement of which commits a step owns. A receipt without that list (written before it existed) contributes only its `head_commit`.
4. No Solidity is produced; the security suite is waived in `.hexaemeron/state.json`.
5. The test harness's fake `git` needs a `rev-list` answer keyed by the queried range before a CLI-level test can drive the new query; the pure graph tests use real Git objects as `test_step_branch_extensions.py` does.

## 1. Problem statement

**Problem.** In the integrate phase, a later step's receipted commits can be merged into a lower step branch that has not merged yet, and the controller admits it. `refuse_rewritten_stack` (`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:18380`) admits any moved waiting tip whose receipted head is still an ancestor; a downward carry has that shape. `unreceipted_run_branch_movement` (`hexctl.py:18276`) watches the run branch alone. `done_merge_step` (`hexctl.py:18466`) passes `expected_head_sha=None` (`hexctl.py:18539`), and a tip unequal to `recorded_local[-1]` (`hexctl.py:18553`) takes the repair path `verify_local_range(pr_base, remote_head)` (`hexctl.py:18568`) instead of refusing, so the carried commits are verified and receipted as the lower step's work.

**Executable admission, today.** `python3 .hexaemeron/design/demonstrate_admission.py --hexctl plugins/hexaemeron/skills/fiat/scripts/hexctl.py` builds a disposable three-step stack, merges the step 3 branch into the waiting step 2 branch, and calls the tree's own `refuse_rewritten_stack` with the remote tip read pointed at the disposable refs and the native ancestry query unchanged. Observed at `f0fa0c66`: `admitted`. Step 2's recorded head `8ee730285d05792b3d965a5f6bfc6c3b3a7e3932`, observed tip `0ad5317e7acb39d061e47531a9f8b0836388041b`, step 3's recorded head `9b02af5f56f9296a58decb10b1974e931e57bab1` reachable from it. This settles the issue's "I did not build a run that demonstrates it".

**User.** The Fiat controller in `integrate`, and the operator who reads `next`, `status` and the `done merge-step` refusal.

**Working prototype.** Three things, all in `hexctl.py`:

1. `next`, when its directive is `merge-step`, refuses when any unmerged step's remote tip has gained a commit that another step's push receipt owns. Refusal is before the directive is printed, with state and ledger bytes unchanged.
2. `done merge-step` refuses the same movement before any mutation, and refuses when the exact repaired range `pr_base..remote_head` it is about to receipt contains a commit another step's receipt owns. The equality path (`recorded_local[-1] == remote_head`) needs no new check.
3. `status` reports the carry as one line, as it reports run-branch movement at `hexctl.py:29449`; `status` reports, it does not refuse.

**Admissible and refused movements.** For each unmerged step with recorded head `R` and observed tip `T`:

| movement | verdict | evidence |
| --- | --- | --- |
| `T == R` | admitted, no query | equality (unchanged) |
| waiting step, `R` not an ancestor of `T` | refused (unchanged) | one native `merge-base --is-ancestor`, status 1 |
| `T` gained only commits no other step's receipt owns (a fix pushed to a waiting branch; a merge of the run branch or of a lower branch's post-receipt commits) | admitted, topology only; merge-time verification still owed | one native `rev-list --max-count=501 R..T`, empty intersection with the ownership set |
| `T` gained a commit in another step's `verified_commits` (else `head_commit`), that step not adopted at push | refused as a carry | the same `rev-list`, non-empty intersection; the message names the step, branch, `R`, `T`, the first carried commit and its owning step |
| `T` gained a commit owned by a step whose push receipt records `early_merge` | admitted | fiat-1021's adoption: that step's landing inside the branch below is receipted, and its own `done merge-step` checks run-branch reachability |
| the `rev-list` fails, times out, exceeds the 2 MiB output cap or lists more than 500 commits | refused as unknown | the neighbour's unknown rule |
| a commit re-created under a new SHA (cherry-pick) | not detected | stated boundary; ownership is by exact SHA |
| a step merged into the run branch outside the loop | run-branch plane, unchanged | `refuse_unreceipted_run_branch_movement` (`hexctl.py:18347`) |

Direction needs no separate rule. A lower step's receipted commits are ancestors of every higher step's recorded head, so they never appear in a higher step's gained range `R..T`; only a higher step's commits, or the current step's, can appear in a lower tip's gained range. A lower step carried into a higher one is ordinary stacking and reads as admitted.

**Success criteria and demo path.**

1. `python3 -m unittest plugins.hexaemeron.tests.test_carried_step_commits -v` exits 0 with at least one test. The module name is fixed here because the design record's conformance resolver pins it. It holds: real-object graph cases for the eight specimens in the design record (whole carry into the current step, whole carry into a waiting step, partial carry of one non-head commit, honest extension, healthy stack, adopted early merge, unknown object, legacy head-only receipt), and CLI cases through `HexctlCase` (`plugins/hexaemeron/tests/hexctl_harness.py:140`) proving `next` withholds the directive, `done merge-step` refuses before mutation with state and ledger byte-identical, and `status` reports.
2. The same module fails on the parent of the guard commit (Elenchus guard convention, section 11), through `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`.
3. `python3 .hexaemeron/design/conform_carry.py --candidate gained-range-ownership --out .hexaemeron/design/reports/gained-range-ownership-product-refuses-specimen-stack.json` writes a true report; that cell blocks `step:4` in the design record.
4. `python3 scripts/run_checks.py --base fiat/1480-refuse-a-later-step-s-commits-carried-into --scope root --scope hexaemeron --format json` is green at every step exit.
5. The existing `RewrittenStackRefusal` (`plugins/hexaemeron/tests/test_hexctl.py:5941`), `AbbreviatedReceiptsStillIntegrate` (`plugins/hexaemeron/tests/test_push_receipt_identity.py`), `NativeGraphCase` (`plugins/hexaemeron/tests/test_step_branch_extensions.py:52`), `test_stack_topology.py` and `test_early_step_merge.py` cases stay green unchanged.

The study carries no `success-criteria` fence; the criteria above are commands, and binding them to runbook Exits stays with the runbook.

## 2. Prior art

### Current source

- `refuse_rewritten_stack` (`hexctl.py:18380-18463`): equality is the zero-query path; a moved waiting tip gets one `_native_ancestry_status` (`hexctl.py:4002`), status 0 admits topology, 1 refuses, anything else is unknown. It skips the current step and merged steps. `test_the_step_being_merged_is_never_queried` (`test_hexctl.py:5992`) pins that only waiting branches are read, so the current-step tip read of this design lives in a new function, not inside this one.
- `unreceipted_run_branch_movement` (`hexctl.py:18276`) and `directed_merge_landing` (`hexctl.py:18222`, PR [#1721](https://github.com/wildcat-finance/skills/pull/1721), merged 2026-09-18): the run-branch plane, including the directed merge awaiting its receipt.
- `done_merge_step` (`hexctl.py:18466`): calls both guards at `hexctl.py:18486-18487`, then `inspect_pull_request` (`hexctl.py:22077`) with `expected_head_sha=None`, then repairs a moved tip through `verify_local_range` (`hexctl.py:21724`), which enumerates `pr_base..head` with `rev-list --max-count=501` (`exact_commit_range`, `hexctl.py:21505`). That enumerated list is where the merge-time disjointness check reads from at no added cost.
- `cmd_next` (`hexctl.py:28883-28884`) runs both guards only when the directive is `merge-step`; `cmd_status` reports movement at `hexctl.py:29449`.
- `done_push` (`hexctl.py:15862`) writes `verified_commits` (`hexctl.py:15980`), `head_commit` and, for a pull request merged before integrate, `early_merge` with `reachable_from` (`hexctl.py:15951-15978`). `recorded_adoption` (`hexctl.py:21565`) reads it back.
- Native reading discipline: `_native_relation_environment` (`hexctl.py:3939`) scrubs `GIT_*`, sets `GIT_NO_LAZY_FETCH=1`, `PATH=os.defpath`, C locale; `_native_relation_git` (`hexctl.py:3976`) adds `--no-replace-objects`; `bounded_probe` (`hexctl.py:20708`) caps output at `GIT_OUTPUT_MAX` 2 MiB (`hexctl.py:293`) and time at `GIT_TIMEOUT` 30 s (`hexctl.py:307`); `GIT_PATHS_MAX` is 500 (`hexctl.py:294`).
- Tests and harness: `hexctl_harness.py` fakes `ls-remote` from `FAKE_GIT_REFS` (line 439), `merge-base --is-ancestor` from `FAKE_GIT_MODE`/`FAKE_GIT_NOT_ANCESTOR` (line 456), and `rev-list` by mode only (line 510: `intermediate`, `malformed-range`, `range-confusion`); `fake_pr` (line 382), `finish_step` (line 1179), `merge_stack` (line 971). `test_early_step_merge.py` `AdoptionHarness` (line 102) drives an adopted step end to end. `test_hexctl.py` is 262,133 bytes against the Promise Machine's 262,144-byte bounded read, so new tests cannot go there.

### The abandoned branch `fiat/555-refuse-misdirected-step-merges`

Fetched at `0b5d5fc5f2c58ac2b824033cd7be44a43c7b5266` (merge of PR #597, 2026-08-24; five commits `eec7e9d081e5df44e84226c0dc035f378297fd9e..8c678715704e325db812b21a6ac1ac31dd43db17`). Its [study](https://github.com/wildcat-finance/skills/blob/0b5d5fc5f2c58ac2b824033cd7be44a43c7b5266/docs/fiat-misdirected-step-merge-guard-study.md) and one-step [runbook](https://github.com/wildcat-finance/skills/blob/0b5d5fc5f2c58ac2b824033cd7be44a43c7b5266/docs/fiat-misdirected-step-merge-guard-runbook.md) were read whole. Its specimen is PR #542 on the issue 429 run: step 2 head `4b78dfa8b35efe4da794a200096682eb7495c3b3` became an ancestor of step 1 tip `d86fcf922cbc1ca2c6b43b3b738211ddd2c1010e` while the step 2 tip stayed put. Its chosen Option D combined receipt-owned commit lists, remote refs read twice, and live pull-request metadata into a four-valued verdict. Its own audit round recorded a 500-step fixture with 249,500 local ancestry pairs, which is the cost of per-commit ancestry. Disposition of its fourteen specimens, by number:

- Carried into this study: 1 (exact direction), 3 (partial carry), 4 (healthy upward stack), 12 (legacy receipt, as bounded degradation to `head_commit` rather than "unavailable"), 13 (no new remote call outside `integrate`), 14 (version arithmetic, now `fiat-v6.66.1`).
- Already on `main`: 7 (rewritten later branch, `refuse_rewritten_stack`), 8 (missing branch and malformed remote output, `remote_branch_tip` at `hexctl.py:21456`), 6 (correct merge awaiting receipt, `directed_merge_landing`).
- Refused by name: 2, 5, 9, 10, 11. Each needs a GitHub read or a double ref snapshot at `next`; this design reads no GitHub at `next` (design criterion `no-new-github-reads`), and the merge-time check over the exact receipted range is the second look. A wrong pull-request base stays with `inspect_pull_request`'s retarget refusal (issue 1085) at `done merge-step`.
- Refused: its 49-line addendum to ADR-021. Inherited decision records are not edited; section 12 names a draft record instead.

Not cherry-picked; the branch is 2,513 insertions on a `fiat-v5.22.1` controller and its tracking issue no longer resolves.

### Last two merged pull requests touching the guards

- [#1418](https://github.com/wildcat-finance/skills/pull/1418) (`8f3a491bfc2f90db0eb4d59774b480a126c04c32`, merged 2026-09-14, "Bind guard evidence before product edits") last changed `refuse_rewritten_stack`. Its boundary names run 453's pending steps 4 and 5 and unchecked hosted surfaces; nothing on this plane. Nothing to carry.
- [#963](https://github.com/wildcat-finance/skills/pull/963) (`18824900b7cff53c733295f5df1e27acf27dd599`, merged 2026-08-30, issue 923 "Classify descendant step tips and reverify their complete range") introduced the status-0 admission this study narrows. Its boundary, "does not establish why a branch moved", is carried as the `diagnostic-overclaim` rule.
- [#1721](https://github.com/wildcat-finance/skills/pull/1721) (`f0fa0c66`, merged 2026-09-18) last changed `refuse_unreceipted_run_branch_movement` and is the tree's head. No carryover block; nothing open on this plane.
- Origins: `b934f9ba9502f083ce049ee6a4dd81bb1b2a1088` (PR #545, `refuse_rewritten_stack`) and `c72ed15a85e6843c59abfcbb2330677f234c670f` (PR #599, run 594, `unreceipted_run_branch_movement`); `f0675b26bf462ddef39e00250205835bf952bea9` (PR #364) introduced the `expected_head_sha=None` repair path.

### Related studies on `main`

`docs/fiat-step-branch-extensions-study.md` (issue 923: honest extension admitted on status 0), `docs/fiat-early-step-merge-study.md` (issue 1021: adoption at push, `early_merge`), `docs/fiat-integrate-base-head-study.md` and `docs/fiat-integration-path-bound-study.md` (integrate receipt bindings). None names the downward carry; `grep -n -i "downward\|carried into\|lower step\|later step"` over the four returns no hit.

### Audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited 0 from the target root, so every synopsis view is current and was the reading view. In-scope sources: `audit/AUDIT.md` (view `audit/AUDIT_SYNOPSIS.md`, 389,658 bytes) and the 89 `audit/rounds/<run>.md` sources with their `.synopsis.md` views.

- Root view, grepped for `rewritten stack`, `rewritten-stack`, `waiting branch`, `waiting step`, `carried into`, `downward`: 0 hits each. `merge-step`: 3 hits, in "Fiat delegation packets, step 1, round 1" and "step 3, round 1" (finding `I320-S3-R1-02`, high: `merge-step` and `integrate` required only a valid GitHub verification response; the round marks it open there and later rounds bound it) and "Fiat merged attribution, step 2, round 1". None names this plane.
- `audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.synopsis.md` (3 rounds, `fiat-audit-round/v2`): all seventeen register ids `reviewed` by step 2 round 2, including `current-step-scope-drift` and `nonancestor-accepted`; no lead on downward carry.
- `audit/rounds/fiat-1021-adopt-an-early-step-merge.synopsis.md` (7 rounds): twelve ids `reviewed` by step 5; Not checked: the sequence against a live GitHub. Its `legacy-run-compatibility` and `second-merge-suppressed` ids are the adoption rules this design excludes from ownership.
- `audit/rounds/fiat-594-bind-a-step-merge-to-the-pull-request-the-di.synopsis.md` (4 rounds; `[missing legacy field: audit-schema]`, `covered`, `not-checked`, `elenchus-verdict` remain unknown): Leads not pursued, step 3: "Retarget drift ... one GitHub call per waiting step per directive". That lead stays open by name; this design does not add the GitHub read it prices.
- `audit/rounds/fiat-576-*.synopsis.md`: no hit for the terms above.

No audit source names a failure this implementation must guard before product work, so the study carries no known-failure inventory block.

### Outside the repository

`git merge-base --is-ancestor` and `git rev-list --max-count` are documented Git 2.x interfaces; GitHub's REST `pulls/{n}` shape is what `inspect_pull_request` already reads. No external standard applies.

## 3. Constraints and non-goals

**Starting ref and toolchain.** `main` at `f0fa0c6632bd5fbef7f35e731646c32741ef282a`; Python 3.14.6 (`.python-version`), stdlib `unittest`; git 2.50.1 (Apple Git-155); `gh` for the merge-time GitHub reads the controller already makes. `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` SHA-256 `644cb46db244a966b9c20aaf07fa6ba66ef59b9e7ea70fdf2e7dfa8f2e46d34d`, 30,722 lines.

**Constraints that shape the runbook.**

1. Plugin release gate. `.github/workflows/repo.yml` job `invariants` runs `scripts/plugin_release.py --base <PR base> --head <sha>` (line 56), so every step PR that touches `plugins/hexaemeron/` raises the package above its own base. Six surfaces move together: `plugins/hexaemeron/.claude-plugin/plugin.json`, `plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json` (hexaemeron entry, line 35), `.agents/plugins/marketplace.json` (line 21), `tests/test_version_propagation.py:47`, `plugins/hexaemeron/tests/test_phylax_model_proxy.py:5684`. The highest version any ref claims is `1.6.51`: 369 remote heads scanned with `git ls-remote` plus `git show <ref>:plugins/hexaemeron/.claude-plugin/plugin.json`, every local branch, and 43 worktrees; the next-highest remote claim is `1.6.50`. Start at `1.6.52`, one bump per step, and re-scan before each bump: the sibling run in `.claude/worktrees/fiat-issue-1676-c51b9d` is on `1.6.51` and may bump concurrently.
2. Frontier row. `done integrate` requires exactly one new generation row `fiat-v6.66.1` in `plugins/hexaemeron/skills/fiat/EVOLUTION.md` (71 rows, current `fiat-v6.65.1` at line 9 and row line 91), keeping frontier revision `delegated-task-identity` and digest `a54452aef0e415d7d17a548751178de0804d22af4829255b3c5d8bfe289581f1`, with `- Current version:` moved. The bump also moves `metadata.version: "6.65.1"` at `plugins/hexaemeron/skills/fiat/SKILL.md:10` (same byte length), which re-pins `tests/fixtures/agent-instruction-v1/manifest.json` and the `fiat-study-runbook-phase` fixtures (`compact.wai`, `model.json`, `source-spans.json`; `~/.claude/tools/repin_fixture.py`); `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` at `hexctl.py:471` (13 entries ending `fiat-v6.65.1`) gains `fiat-v6.66.1`; `tests/fixtures/promise-machine/runtime/fiat-final-integration.json` pins the ledger digest `3db3ac5e793bdd55b07226dcb9ab0c49460a7eb9830f77e8e22ab3946434c7e3`.
3. Digest cascade on every `hexctl.py` edit. Its SHA-256 is pinned once, at `tests/promise_machine_coverage.json` `run_observation_binding.controller.sha256`; then `docs/promise-machine/obligation-gates/evaluation-run.json` `tree_sha256` (`fa13e1380051d0f0cd54d4c054901f6e6da64cdbec260c63976f1f9bd60d42d8`, re-tallied with `tests/promise_evaluation_driver.py emit`, `tally`, `verify` keeping model `ollama/qwen3.8-uncensored:Q6_K@sha256:79b2ee09...` and date `2026-08-31`), `docs/promise-machine/obligation-gates/integration-projection.json` and `.md`, and `.horos/census.json` (35 suffix rows, 4,176 files, 123,594,007 bytes; `HorosCensusCurrencyTests`). `~/.claude/tools/fiat_digest_cascade.py <worktree> <entry-commit>` re-pins the first and last stages. `plugins/hexaemeron/tests/test_hexctl.py` (SHA-256 `149ad2344aa3706c9109eb3e569cd085909c57802d41d9f5e51cbb161a53cb33`) is pinned at `tests/fixtures/promise-machine/composition/cases.json`, `tests/fixtures/promise-machine/runtime/fiat-final-integration.json`, `fiat-receipted-delivery.json`, `fiat-study-amendment.json` and three places in `tests/promise_machine_coverage.json`; steps 2 and 3 leave that file unedited by putting new tests in `plugins/hexaemeron/tests/test_carried_step_commits.py`, and any harness edit re-pins nothing (`hexctl_harness.py` has no digest pin).
4. Governed SKILL.md range. `tests/fixtures/agent-instruction-v1/manifest.json` fixture `fiat-study-runbook-phase` governs bytes 18784 to 29736 of `plugins/hexaemeron/skills/fiat/SKILL.md` (`source.sha256` `a5de2a5da176365db6d695bf5d7b37e3e3bc87ac699a94702dd50164c3fba2d3`, `span_sha256` `73b8c169309b3ec0881642dbf57dd435cce8fe324faf7562ca22f6b79b29d45e`). The phase table row for `merge-step` at line 364 sits at byte 20739, inside the range, and stays. Prose goes after byte 29736: the paragraph at lines 860-861 (byte 53991, "Before each merge, an unchanged waiting head passes without a relation process") is the natural place, and `plugins/hexaemeron/skills/fiat/references/push-discipline.md:362-374` is the operator-facing home.
5. Gate-command grammar (`contracts.gate_commands` recorded at init). Exit commands are literal `python3` plus a registered script: `scripts/run_checks.py` (`build_parser`) and `plugins/hexaemeron/tests/run_tests.py` (`argument_parser`) are registered in `plugins/hexaemeron/skills/protasis/scripts/gate_commands.py` `MODULE_BINDINGS`; `tests/check-map-v1.json` declares `root-suite` (`python3 -m unittest discover -s tests`) and `hexaemeron-suite` (`python3 plugins/hexaemeron/tests/run_tests.py`, `--jobs`), and scope `hexaemeron` exists. The suites run as `python3 scripts/run_checks.py --base fiat/1480-refuse-a-later-step-s-commits-carried-into --scope root --scope hexaemeron --format json`. Each step's Elenchus line is one physical line: `Elenchus command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}; format: unittest-json-v1; report file: .hexaemeron/elenchus-step-N.json`. `run_tests.py` refuses a report path that already exists or leaves the worktree.
6. Decision record. A new decision is authored at `docs/decisions/drafts/refuse-receipted-commits-carried-into-a-lower-step-branch.md` with heading `# Decision: ...`, five sections and a dated status, numbered only at integration; no inherited record is edited.
7. Resolver hygiene. `.hexaemeron/design/resolve_carry.py`, `build_record.py`, `conform_carry.py` and `demonstrate_admission.py` write only a caller-named `--out` that must not exist (or nothing), never a controller path, spawn no shell and open no socket; `phylax.py` over all four exits 0. Step 1 copies them under `docs/design/` where `lint-phylax` runs.
8. Audit. Warden audits each step with `--phylax-exit`, `--ephoros-exit`, `--hypomnema-exit` and the Imprimatur lint; the security suite is waived. Four steps keep each audit loop bounded: (1) scaffold: study, runbook and resolver copies, the draft decision record, the admission demonstration; (2) the `next`-time guard and its graph and CLI tests; (3) the `done merge-step` refusals, `status` line, conformance report; (4) prose in `push-discipline.md` and SKILL.md after the governed range, ledger row, version bump, digest cascade.
9. Links. Repository files are cited by path in code spans or by URL pinned to `f0fa0c66`; `done study` refuses any other Markdown link or `runbook:` pointer.

**Non-goals.** Detecting a cherry-picked copy of another step's commit. Reading GitHub at `next`. Refusing a wrong pull-request base earlier than `done merge-step` (fiat-594's retarget-drift lead stays open). Any new receipt field or ledger event: refusals leave state untouched. Changing `refuse_rewritten_stack`'s status-0 admission for commits nobody owns (issue 923 stands). Landing the 555 branch. Repairing a stack already carried; the refusal names the commits and stops.

**Boundaries.** Always: both suites before a commit; Imprimatur on every shipped document; `hexctl verify` before a receipt that depends on earlier state; a recorded measurement before any performance claim. Ask first: a new dependency; a change to an existing receipt shape; touching CI; a GitHub read on a path that has none; editing an `EVOLUTION.md` field other than the one generation row. Never: rewrite a published ref; import GitHub's public key to pass a signature check; edit an inherited decision record; delete a failing test; claim a command ran when it did not; edit bytes 18784 to 29736 of the Fiat SKILL.md except the version line.

## 4. Design options

Four constructions were evaluated. `.hexaemeron/design-evidence.json` (SHA-256 `06f801ea6d139d7554d01170d523eaf6fd40311d9d256906e9b2debd72aaefb1`) selects one from checked gates and one comparative metric; the prose explains them.

**`gained-range-ownership` (selected).** For each unmerged step whose tip differs from its recorded head, after the existing ancestry admission for a waiting step, run one bounded native `git rev-list --max-count=501 <recorded>..<tip>` through `_native_relation_git`. Refuse when the listed commits intersect the ownership set: the union of every other step's `verified_commits` (else `head_commit`), excluding steps whose push receipt records `early_merge`. The current step is read too, in a new function beside `refuse_rewritten_stack`. At `done merge-step`, the already-enumerated repaired range `pr_base..remote_head` is intersected with the same set before any mutation. Trade: one added native process per `next` on a healthy stack (the current-step tip read) and one `rev-list` per moved tip; ownership is by exact SHA, so a cherry-picked copy passes.

**`owned-commit-ancestry`.** The 555 branch's predicate: for each unmerged lower step, one `merge-base --is-ancestor` per commit owned by every higher step against the lower tip. Same refusals, same adoption exclusion. Trade: the process count grows with the commit count, measured 7 on the healthy three-step fixture against 1, and the 555 audit round's 500-step fixture reached 249,500 pairs.

**`pull-request-merge-state`.** Read each unmerged step's pull request from GitHub at `next` and refuse when it reports merged into a base other than the run branch. Trade: catches only a carry made through the recorded pull request; a plain merge pushed to the branch, and a fabricated tip, both read as clear; it adds one GitHub read per unmerged step per directive, the cost fiat-594 declined to pay.

**`merge-time-only`.** Leave `next` unchanged and intersect the repaired range at `done merge-step` only. Trade: zero added reads at `next`, but the carry is admitted until the receipt, which is after the merge the directive asked for has landed.

**Criteria and measured values.** Nine criteria: `refuses-whole-carry`, `refuses-partial-carry`, `admits-honest-extension` (correctness gates, owner elenchus), `admits-adopted-early-merge` and `no-new-github-reads` (compatibility gates), `added-native-processes-per-next` (time metric, count, minimise, owner metron, measured on the healthy stack because a carry ends at the first hit), `max-child-output-bytes` (space gate, at most 2,097,152), `unknown-refuses-as-unknown` (recovery gate), and `product-refuses-specimen-stack` (conformance gate blocking `step:4`). Every selection cell is resolved by `python3 .hexaemeron/design/resolve_carry.py --candidate <id> --criterion <id> --out .hexaemeron/design/reports/<id>-<id>.json`, which builds a real three-step stack per specimen and runs the candidate's reference procedure over it:

| candidate | whole | partial | honest | adopted | no GitHub | processes | max bytes | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gained-range-ownership` | pass | pass | pass | pass | pass | 1 | 205 | pass |
| `owned-commit-ancestry` | pass | pass | pass | pass | pass | 7 | 41 | pass |
| `pull-request-merge-state` | fail | fail | pass | pass | fail | 0 | 0 | fail |
| `merge-time-only` | fail | fail | pass | pass | pass | 0 | 0 | fail |

Gates remove `pull-request-merge-state` and `merge-time-only`. Between the two survivors the one metric decides: 1 against 7, so `gained-range-ownership` is the unique frontier. `python3 <plugin-root>/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition design-lock` exits 0. The conformance cell is pending for all four candidates; only the selected candidate's cell is due, before step 4 opens, through `conform_carry.py`, which runs the fixed test module and records `true` only on a green run with at least one test.

The resolver's procedures are reference models of each construction, not the product controller; the conformance cell is where the product answers.

## 5. Risk register seed

The audit loop should look hardest at whether the ownership set is derived only from receipts, whether the adoption exclusion re-opens the hole it exists to leave open, and whether every refusal happens before a byte of state changes.

```risk-register
carry-direction | the gained range of each unmerged tip against the ownership set | a higher step's receipted commits in a lower tip refuse; a lower step's receipted commits never appear in a higher tip's gained range, proven on real objects
ownership-source | verified_commits and head_commit read from push receipts | the set is built from receipts only, never from a mutable branch, and a step without verified_commits contributes exactly its head_commit
adopted-step-exclusion | early_merge on a push receipt | an adopted step's commits are admitted only inside the branch its receipt names as reachable_from, and the carrier step's own commits still refuse further down
current-step-at-next | the current step's tip read in the new function | next withholds the merge-step directive for a carried current step, and test_the_step_being_merged_is_never_queried still passes for refuse_rewritten_stack
receipt-range-disjointness | the repaired range pr_base..remote_head at done merge-step | the range is intersected with the ownership set before inspect_pull_request evidence is recorded and before any state write
gained-range-bound | the native rev-list --max-count=501 output | more than 500 commits, a failed start, a timeout, the 2 MiB cap or a non-zero status all refuse as unknown naming step, branch, recorded head and tip
unknown-relation | a missing object for an observed tip | the refusal says unknown, names the exact pair and claims no cause; no fetch is attempted
honest-extension-regression | issue 923's status-0 admission | a waiting tip that gained only unowned commits still passes topology, and the merge-time repair still verifies the full live range
state-mutation-on-refusal | every new refusal path in next, status and done merge-step | state.json and ledger.jsonl are byte-identical across whole, partial and unknown refusals
diagnostic-overclaim | the refusal and status text | names the observed commits and their owning step; names no GitHub mechanism, person or intent
github-read-scope | the next path | no GitHub REST or GraphQL call is added; done merge-step keeps exactly the reads it has
run-branch-guard-regression | test_stack_topology and the directed-merge landing | PR 1721's pending-receipt directive and the issue 576 refusal are unchanged
fake-git-rev-list | the harness fake git | the new range-keyed rev-list answer cannot make an unrelated existing test pass differently; mode-keyed answers stay
digest-cascade | every hexctl.py edit | coverage, evaluation-run tree digest, integration projection and census are re-pinned in the same step PR that edits the file
version-collision | the six package surfaces | each bump exceeds every remote and local claim at the moment of the bump, re-scanned per step
governed-skill-range | SKILL.md bytes 18784 to 29736 | only the version line changes inside the range and keeps its length; new prose sits after byte 29736
```

## 6. Glossary seeds

| term | meaning |
| --- | --- |
| carry | a commit owned by one step's push receipt becoming reachable from another step's branch tip after that receipt was written |
| downward carry | a carry whose carrier branch belongs to a lower-numbered step; the fault this study refuses |
| gained range | `git rev-list <recorded>..<tip>`, the commits an unmerged step's tip holds that its receipted head does not |
| ownership set | for one step, the union of every other step's `verified_commits` (else `head_commit`), excluding steps with a recorded `early_merge` |
| honest extension | a gained range disjoint from the ownership set (issue 923) |
| adopted step | a step whose pull request merged before integrate and whose push receipt records `early_merge` with `reachable_from` (issue 1021) |
| unknown | a native read that did not answer; it refuses and claims nothing about cause |
| repaired range | `pr_base..remote_head` as `done merge-step` enumerates it for a moved current tip |

## 7. Sources

- Issue: [wildcat-finance/skills#1480](https://github.com/wildcat-finance/skills/issues/1480), read whole on 2026-09-18; body SHA-256 recorded by init as `e084cc93f8000c6fdb7d10ec0729eb76254330860cd2d02083b88bb9c376d799`.
- Controller at the starting ref: [`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/plugins/hexaemeron/skills/fiat/scripts/hexctl.py).
- Tests: [`test_hexctl.py`](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/plugins/hexaemeron/tests/test_hexctl.py), [`test_push_receipt_identity.py`](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/plugins/hexaemeron/tests/test_push_receipt_identity.py), [`test_step_branch_extensions.py`](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/plugins/hexaemeron/tests/test_step_branch_extensions.py), [`test_stack_topology.py`](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/plugins/hexaemeron/tests/test_stack_topology.py), [`test_early_step_merge.py`](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/plugins/hexaemeron/tests/test_early_step_merge.py), [`hexctl_harness.py`](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/plugins/hexaemeron/tests/hexctl_harness.py).
- Prose homes: [`push-discipline.md`](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/plugins/hexaemeron/skills/fiat/references/push-discipline.md), [Fiat `SKILL.md`](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/plugins/hexaemeron/skills/fiat/SKILL.md), [`EVOLUTION.md`](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/plugins/hexaemeron/skills/fiat/EVOLUTION.md), [ADR-021](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md).
- Prior studies: [step branch extensions](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/docs/fiat-step-branch-extensions-study.md), [early step merge](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/docs/fiat-early-step-merge-study.md), [integrate base head](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/docs/fiat-integrate-base-head-study.md), [integration path bound](https://github.com/wildcat-finance/skills/blob/f0fa0c6632bd5fbef7f35e731646c32741ef282a/docs/fiat-integration-path-bound-study.md).
- Abandoned branch: [study](https://github.com/wildcat-finance/skills/blob/0b5d5fc5f2c58ac2b824033cd7be44a43c7b5266/docs/fiat-misdirected-step-merge-guard-study.md), [runbook](https://github.com/wildcat-finance/skills/blob/0b5d5fc5f2c58ac2b824033cd7be44a43c7b5266/docs/fiat-misdirected-step-merge-guard-runbook.md), [audit record](https://github.com/wildcat-finance/skills/blob/0b5d5fc5f2c58ac2b824033cd7be44a43c7b5266/audit/AUDIT.md).
- Pull requests: [#1721](https://github.com/wildcat-finance/skills/pull/1721), [#1418](https://github.com/wildcat-finance/skills/pull/1418), [#963](https://github.com/wildcat-finance/skills/pull/963), [#599](https://github.com/wildcat-finance/skills/pull/599), [#545](https://github.com/wildcat-finance/skills/pull/545), [#364](https://github.com/wildcat-finance/skills/pull/364).
- Audit views: `audit/AUDIT_SYNOPSIS.md`, `audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.synopsis.md`, `audit/rounds/fiat-1021-adopt-an-early-step-merge.synopsis.md`, `audit/rounds/fiat-594-bind-a-step-merge-to-the-pull-request-the-di.synopsis.md`.
- Repository gates: `.github/workflows/repo.yml`, `scripts/plugin_release.py`, `tests/check-map-v1.json`, `tests/fixtures/agent-instruction-v1/manifest.json`, `tests/promise_machine_coverage.json`, `docs/promise-machine/obligation-gates/evaluation-run.json`, `.horos/census.json`.
- Design record and resolvers: `.hexaemeron/design-evidence.json`, `.hexaemeron/design/resolve_carry.py`, `.hexaemeron/design/build_record.py`, `.hexaemeron/design/conform_carry.py`, `.hexaemeron/design/demonstrate_admission.py`, reports under `.hexaemeron/design/reports/`.
- Contracts cited, not restated: `plugins/hexaemeron/skills/protasis/SKILL.md`, `references/gate-commands.md`, and the five discipline skills named in sections 8 to 12.

## 8. Signals, and the questions behind them

This is an interactive command path, not a service, so no metric or alert is proposed; the questions are answered from the command output. The observation contract is `plugins/hexaemeron/skills/ephoros/SKILL.md`.

1. **Why did `next` stop offering the merge?** The refusal on stderr names the step number, branch, recorded head, observed tip, the first carried commit and the step whose receipt owns it, and says what is not claimed: which operation moved the branch. Emitted by step 2.
2. **Is the stack carrying anything right now?** `hexctl status` in `integrate` prints one `CARRY:` line per carried step, or nothing, beside the existing `STACK:` line; it reports and does not refuse. Emitted by step 3.
3. **Did a refusal change anything?** Nothing: no ledger event, no state field. An operator compares `state.json` and `ledger.jsonl` digests before and after, and the CLI tests assert it. Steps 2 and 3.
4. **Was the answer unknown rather than clean?** The unknown refusal says so and names the exact pair; a clean `next` prints the directive. Step 2.

## 9. Boundaries, per capability

The boundary list and controls belong to `plugins/hexaemeron/skills/phylax/SKILL.md`; this names how the change fits them.

| capability | boundary | control |
| --- | --- | --- |
| Read a remote branch tip | `git ls-remote --refs origin refs/heads/<branch>` through `bounded_git` | existing `remote_branch_tip`: one ref, full SHA, exact ref name, else refuse |
| Enumerate a gained range | native `git rev-list --max-count=501 <R>..<T>` through `_native_relation_git` | scrubbed environment, `--no-replace-objects`, no lazy fetch, 30 s timeout, 2 MiB cap, full-SHA lines only, more than 500 refuses as unknown |
| Read ownership | `verified_commits`, `head_commit`, `early_merge` from `state.json` | `load_state` validation; values must be full SHAs; nothing is read from a branch |
| Refuse | `die` before any state or ledger write | tests compare bytes before and after |
| Report in `status` | one line per carried step | same reader as `next`; unknown prints as unknown |
| GitHub | `inspect_pull_request`, `verify_github_commits`, attribution at `done merge-step` | unchanged; no read added at `next` |
| Test fixtures | temporary directories, real Git objects, the fake `git` script | the fake answers `rev-list` from an environment map keyed by the exact range; no network |
| Resolvers | `.hexaemeron/design/*.py` and their `docs/design/` copies | write only `--out`, refuse an existing path, no shell, no socket; `phylax.py` exit 0 |

## 10. The budget, or its absence

No performance budget: the path is interactive and the defect is a wrong admission, so under `plugins/hexaemeron/skills/metron/SKILL.md` no Metron gate is incurred. The cost is measured, not estimated: the design report `.hexaemeron/design/reports/gained-range-ownership-added-native-processes-per-next.json` records 1 added native process per `next` on a healthy three-step stack (the current-step tip read), and a moved tip adds one `rev-list` whose output is at most 501 lines (205 bytes on the carry specimen, `max-child-output-bytes` report). `done merge-step` adds no process; it reads the range `verify_local_range` already enumerated. If a step claims a cost above this, it records a before-and-after measurement with the same resolver first.

## 11. The fail-closed posture

What stops the run: a carried commit in any unmerged tip's gained range at `next` or `done merge-step`; a carried commit in the repaired receipt range; a `rev-list` that fails, times out, overflows or lists more than 500 commits; a missing object. Each refuses before mutation and names the exact commits; none names a cause. What does not stop it: an unowned extension, an adopted step's commits inside its recorded base, an equal tip. The triage order and guard rule are `plugins/hexaemeron/skills/elenchus/SKILL.md`'s.

Guard convention: every fix lands with a test in `plugins/hexaemeron/tests/test_carried_step_commits.py` that is red on the parent of the fixing commit and green after it; `demonstrate_admission.py` is the red observation at `f0fa0c66`. Warden's Elenchus replay runs `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}` in `unittest-json-v1` and must read `guarded`. The existing `RewrittenStackRefusal` cases pin that a status-1 waiting tip still refuses with "no longer contains its receipted head" and that equal tips ask Git nothing; the new function runs after them and must not change those answers.

## 12. Decisions and their homes

Which decisions earn a record and where each lives is `plugins/hexaemeron/skills/hypomnema/SKILL.md`'s rule. Three are expensive to reverse, and they share one draft record, `docs/decisions/drafts/refuse-receipted-commits-carried-into-a-lower-step-branch.md` (`# Decision: ...`, Status, Context, Decision, Alternatives, Consequences; dated status; numbered at integration; cited by that path until then):

1. Admissibility is by receipt ownership, not by direction or by pull-request state: a gained commit refuses when another step's push receipt owns it, an adopted step is excluded, and a cherry-picked copy is out of scope.
2. The evidence split: one bounded native `rev-list` per moved tip at `next`, no GitHub read there, and the exact repaired range checked again at `done merge-step`.
3. No new receipt field or ledger event: a refusal leaves state untouched, so legacy runs need no migration and `verify` replays nothing new.

Not edited: `docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md`, which still owns the genuine-rewrite landing; the 555 branch's addendum plan is refused above.

Other homes: the predicate and refusal text in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; tests in `plugins/hexaemeron/tests/test_carried_step_commits.py` and the fake `rev-list` map in `plugins/hexaemeron/tests/hexctl_harness.py`; the operator rule after `plugins/hexaemeron/skills/fiat/references/push-discipline.md:374`; one paragraph in `plugins/hexaemeron/skills/fiat/SKILL.md` after byte 29736; the generation row `fiat-v6.66.1` in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`; committed copies `docs/fiat-1480-carried-step-commits-study.md`, `docs/fiat-1480-carried-step-commits-runbook.md` and the four resolvers under `docs/design/`.

### Amendment -- 2026-09-18

**What changed.** Section 12 gains the design bridge that Hypomnema study mode requires, binding the selected candidate to the draft decision record Step 1 creates:

```design-bridge
schema | hypomnema-design-bridge/v1
decision | gained-range-ownership
record | docs/decisions/drafts/refuse-receipted-commits-carried-into-a-lower-step-branch.md
```

**Why.** `hypomnema.py --study` reported H008 on the receipted study; the controller's own study gate runs the ordinary walk, which does not require the bridge, so the receipt passed without it. The record the bridge names is authored in Step 1, so the bridge is added in Step 1 rather than before the receipt.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-09-18

**What changed.** The copy homes named in section 3 item 7, the section 9 Resolvers row and section 12 are superseded by the runbook's: the four resolvers are copied to `docs/fiat-carried-step-commits/design/`, the study to `docs/fiat-carried-step-commits/study.md` and the runbook to `docs/fiat-carried-step-commits/runbook.md`, beside `design-evidence.json` and `reports/` in the same directory. The names `docs/design/`, `docs/fiat-1480-carried-step-commits-study.md` and `docs/fiat-1480-carried-step-commits-runbook.md` no longer apply.

**Why.** Audit finding S1-R1-01 (Step 1, round 1): the receipted runbook Step 1, its Files list and the first amendment's `design-bridge` record path put every copy under `docs/fiat-carried-step-commits/`, and Step 1 committed them there at `5da736c405421b59fe539f42ce9516f31d23a034`. The study copy is byte-identical to this receipted study, so the correction is an amendment, not an edit.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
