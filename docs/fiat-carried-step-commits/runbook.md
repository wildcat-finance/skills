# Runbook: refuse a later step's commits carried into a lower waiting branch

Derived from the receipted study `.hexaemeron/study.md`, SHA-256
`386b9ff689270da6ef04bb3d0bba45e47b6907cf97ea19e78aa6be03d743ae72` at its
receipt, for [wildcat-finance/skills#1480](https://github.com/wildcat-finance/skills/issues/1480).
The run branch is `fiat/1480-refuse-a-later-step-s-commits-carried-into`, cut
from `main` at `f0fa0c6632bd5fbef7f35e731646c32741ef282a`. Step 1 branches
from the run branch and every later step from the step below it.

The selected design is `gained-range-ownership` (study section 4). For each
unmerged step whose observed tip differs from its recorded head, one bounded
native `git rev-list --max-count=501 <recorded>..<tip>` lists the gained range,
and the step refuses when that range contains a commit another step's push
receipt owns: the union of every other step's `verified_commits`, else its
`head_commit`, excluding steps whose push receipt records `early_merge`. The
same set is intersected with the repaired range at `done merge-step`. A
refusal names the step, branch, recorded head, observed tip, the first carried
commit and its owning step, claims no cause, and changes no state or ledger
byte. A read that does not answer refuses as unknown.

Conventions for every step:

- Exits run from the run worktree root on the committed step head, with
  `NO_COLOR=1` in the environment because this shell sets `FORCE_COLOR=3`.
  `scripts/run_checks.py` freezes a snapshot without ignored files, so its
  suites never read the run's `.hexaemeron/`. A bare `unittest` run inside the
  run worktree is not an exit.
- Every step touches `plugins/hexaemeron/`, so every step raises the package
  version on its six surfaces together: `plugins/hexaemeron/.claude-plugin/plugin.json`,
  `plugins/hexaemeron/.codex-plugin/plugin.json`, the hexaemeron entry in
  `.claude-plugin/marketplace.json` and in `.agents/plugins/marketplace.json`,
  the pin in `tests/test_version_propagation.py` and the pin in
  `plugins/hexaemeron/tests/test_phylax_model_proxy.py`. The number exceeds the
  step's own pull request base and every version any local or remote ref
  claims at the moment of the bump, re-scanned with `git ls-remote` and
  `git show <ref>:plugins/hexaemeron/.claude-plugin/plugin.json`. At study
  time the highest claim was `1.6.51`, so Step 1 starts at `1.6.52` unless the
  re-scan says otherwise. `python3 scripts/plugin_release.py --base <pull request base> --head HEAD`
  exits 0 before the push.
- Every edit to `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` re-pins, in
  the same step: its SHA-256 at `tests/promise_machine_coverage.json`
  (`run_observation_binding.controller.sha256`), then
  `docs/promise-machine/obligation-gates/evaluation-run.json` `tree_sha256`
  through `tests/promise_evaluation_driver.py` `emit`, `tally` and `verify`
  with the recorded model and date kept, then
  `docs/promise-machine/obligation-gates/integration-projection.json` and
  `integration-projection.md`. No model, tokenizer or measurement process
  runs. `plugins/hexaemeron/tests/test_hexctl.py` and
  `plugins/hexaemeron/tests/hexctl_harness.py` digests are not re-pinned:
  the first is never edited (study section 3, constraint 3) and the second has
  no pin.
- Stage every change, run `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`
  and `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`,
  stage `.horos/boundary.json`, `.horos/candidates.json` and
  `.horos/census.json` together, then commit. Never hand-edit a `.horos`
  artefact.
- The design record `.hexaemeron/design-evidence.json` is immutable. Its one
  due conformance cell, `gained-range-ownership` against
  `product-refuses-specimen-stack`, blocks `step:4`; Step 3 resolves it by
  running `python3 .hexaemeron/design/conform_carry.py --candidate gained-range-ownership --out .hexaemeron/design/reports/gained-range-ownership-product-refuses-specimen-stack.json`
  before its push receipt. No existing report is rewritten and no other
  resolver runs after Step 1's copies are taken.
- New tests go in `plugins/hexaemeron/tests/test_carried_step_commits.py`;
  the conformance resolver pins that module name and `test_hexctl.py` sits at
  the bounded-read ceiling.
- The study is amended once, in Step 1, through `hexctl amend study`, to add
  the `design-bridge` fence Hypomnema study mode requires. The committed study
  copy is taken after that receipt and stays byte-identical to it.

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
```

The relation is not a reservation. The ledger row, the `SKILL.md` metadata
version, the compatibility-set entry and the evolution-contract test pins are
written in Step 4 and resolved against the exact integration base at
`done resolve-versions`. The held frontier revision `delegated-task-identity`,
its digest `a54452aef0e415d7d17a548751178de0804d22af4829255b3c5d8bfe289581f1`,
the `Current frontier` line and the `Next Fiat job` line stay unchanged.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 06f801ea6d139d7554d01170d523eaf6fd40311d9d256906e9b2debd72aaefb1
candidate | gained-range-ownership
```

## Step 1: Commit the specification, the draft decision and the admission demonstration

**Goal.** Put the receipted study, this runbook, the design record, its
reports and the four resolvers under `docs/fiat-carried-step-commits/`, author
the draft decision record, bind the study to it, and record what the starting
controller answers for a downward carry.
**Entry.** The run branch at `f0fa0c6632bd5fbef7f35e731646c32741ef282a` with a
clean tree. At study time `python3 .hexaemeron/design/demonstrate_admission.py --hexctl plugins/hexaemeron/skills/fiat/scripts/hexctl.py`
printed `admitted` (study section 1).
**Exit.** Each command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1480-refuse-a-later-step-s-commits-carried-into --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-carried-step-commits/study.md docs/fiat-carried-step-commits/runbook.md docs/decisions/drafts/refuse-receipted-commits-carried-into-a-lower-step-branch.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-carried-step-commits/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-carried-step-commits/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-carried-step-commits docs/decisions/drafts
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study docs/fiat-carried-step-commits/study.md --design-evidence docs/fiat-carried-step-commits/design-evidence.json --repo-root .
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py docs/fiat-carried-step-commits/design
```

- `docs/decisions/drafts/refuse-receipted-commits-carried-into-a-lower-step-branch.md`
  exists with the heading `# Decision: ...`, the sections Status, Context,
  Decision, Alternatives and Consequences in that order, a dated status, no
  ADR number, and the three decisions of study section 12 with the three
  rejected constructions of study section 4 as its alternatives. No inherited
  decision record changes.
- The receipted study carries one dated amendment whose `design-bridge` fence
  names schema `hypomnema-design-bridge/v1`, decision `gained-range-ownership`
  and that draft's path, receipted through `hexctl amend study` with every
  step holding.
- `docs/fiat-carried-step-commits/study.md`, `runbook.md` and
  `design-evidence.json` are byte-identical to `.hexaemeron/study.md`,
  `.hexaemeron/runbook.md` and `.hexaemeron/design-evidence.json`;
  `docs/fiat-carried-step-commits/reports/` holds byte-identical copies of the
  32 reports under `.hexaemeron/design/reports/`; and
  `docs/fiat-carried-step-commits/design/` holds byte-identical copies of
  `resolve_carry.py`, `build_record.py`, `conform_carry.py` and
  `demonstrate_admission.py`.
- `docs/fiat-carried-step-commits/admission-at-starting-ref.txt` holds the
  exact standard output of `demonstrate_admission.py` run against the
  starting controller, whose verdict line reads `admitted`.
- The six package surfaces name one version above every claim, and the three
  `.horos` artefacts equal a fresh scan.

**Files.** `docs/fiat-carried-step-commits/study.md`,
`docs/fiat-carried-step-commits/runbook.md`,
`docs/fiat-carried-step-commits/design-evidence.json`,
`docs/fiat-carried-step-commits/reports/` (32 files),
`docs/fiat-carried-step-commits/design/resolve_carry.py`,
`docs/fiat-carried-step-commits/design/build_record.py`,
`docs/fiat-carried-step-commits/design/conform_carry.py`,
`docs/fiat-carried-step-commits/design/demonstrate_admission.py`,
`docs/fiat-carried-step-commits/admission-at-starting-ref.txt`,
`docs/decisions/drafts/refuse-receipted-commits-carried-into-a-lower-step-branch.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `tests/test_version_propagation.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`, `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.
**Tests.** None written; the root and Hexaemeron suites and the lints above
are the gate.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`
**Disciplines.** hypomnema: the copies and the draft record are the homes study
section 12 names, and the design bridge joins them. phylax: the four resolver
copies enter the `lint-phylax` walk and write only a caller-named `--out`
(study section 9). elenchus: the admission text is the red observation at the
starting ref that Step 2's guard test turns green (study section 11). ephoros:
none, nothing here runs unattended. metron: none, no cost claim.

## Step 2: Refuse a carried commit before `next` offers the merge

**Goal.** Build the `next`-time guard of `gained-range-ownership` in
`hexctl.py`, with a test module that is red on the parent of the guard commit.
**Entry.** Step 1's exit tree.
**Exit.** The command below exits 0 and reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1480-refuse-a-later-step-s-commits-carried-into --scope root --scope hexaemeron --format json
```

- A new function beside `refuse_rewritten_stack` builds the ownership set from
  push receipts only, reads each unmerged step's remote tip including the
  current step's, skips an equal tip without a query, and for a moved tip runs
  one `rev-list --max-count=501 <recorded>..<tip>` through
  `_native_relation_git` with the scrubbed environment, no lazy fetch, the
  30 s timeout and the 2 MiB cap. A gained range that intersects the set
  refuses through `die` naming the step number, branch, recorded head,
  observed tip, the first carried commit and its owning step, and stating that
  which operation moved the branch is not claimed. A failed start, timeout,
  cap, non-zero status, more than 500 listed commits, a line that is not a
  full SHA, or a missing object refuses as unknown naming the exact pair. An
  adopted step's commits are outside the set.
- `cmd_next` calls the new function after `refuse_rewritten_stack` when the
  directive is `merge-step`, before the directive is printed.
  `refuse_rewritten_stack` itself is unchanged, and
  `test_the_step_being_merged_is_never_queried` still passes.
- The fake `git` in `plugins/hexaemeron/tests/hexctl_harness.py` answers
  `rev-list` for a range named in a new environment map keyed by the exact
  `<base>..<head>` pair, and keeps every mode-keyed answer it has today.
- `plugins/hexaemeron/tests/test_carried_step_commits.py` holds real-object
  graph cases for the eight specimens of the design record (whole carry into
  the current step, whole carry into a waiting step, partial carry of one
  non-head commit, honest extension, healthy stack, adopted early merge,
  unknown object, legacy head-only receipt) and CLI cases through
  `HexctlCase` proving that `next` prints no directive on a carry and that
  `.hexaemeron/state.json` and `.hexaemeron/ledger.jsonl` are byte-identical
  before and after each refusal. `python3 -m unittest plugins.hexaemeron.tests.test_carried_step_commits -v`,
  run by hand from the run worktree, reports at least 12 tests and `OK`.
- The module fails by assertion when run against the parent of the guard
  commit, shown by a hand counterfactual recorded in the pull request body.
- The `hexctl.py` digest cascade, the package bump and the three `.horos`
  artefacts are current.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/hexctl_harness.py`,
`plugins/hexaemeron/tests/test_carried_step_commits.py` (new),
`tests/promise_machine_coverage.json`,
`docs/promise-machine/obligation-gates/evaluation-run.json`,
`docs/promise-machine/obligation-gates/integration-projection.json`,
`docs/promise-machine/obligation-gates/integration-projection.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `tests/test_version_propagation.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`, `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.
**Tests.** New module `plugins/hexaemeron/tests/test_carried_step_commits.py`,
at least 12 tests: 8 graph cases and at least 4 CLI cases. Existing Hexaemeron
tests are unchanged.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`
**Disciplines.** phylax: the `rev-list` read is one new bounded native child
with the scrubbed environment, no lazy fetch, the 30 s timeout, the 2 MiB cap
and the 500-commit limit, and nothing is fetched (study section 9). ephoros:
the refusal text answers study section 8's questions 1, 3 and 4. elenchus: the
module is red on the parent of the guard commit and green after it (study
section 11). metron: none, the recorded cost is 1 added native process per
`next` on a healthy stack (study section 10) and no performance claim is
made. hypomnema: the reason sits in the new function's docstring and points at
the draft record by path.

## Step 3: Refuse the carry at `done merge-step` and report it in `status`

**Goal.** Close the receipt path and the operator's view: `done merge-step`
refuses a carry before any mutation and refuses a repaired range holding an
owned commit, and `status` reports a carried step.
**Entry.** Step 2's exit tree.
**Exit.** The command below exits 0 and reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1480-refuse-a-later-step-s-commits-carried-into --scope root --scope hexaemeron --format json
```

- `done_merge_step` calls the Step 2 function after `refuse_rewritten_stack`
  and before `inspect_pull_request`, so a carry refuses before any GitHub
  evidence is recorded. When the current tip is unequal to the recorded head,
  the repaired range `pr_base..remote_head` that `verify_local_range` already
  enumerates is intersected with the ownership set before `effective_push` is
  built; a non-empty intersection refuses naming the first carried commit and
  its owning step. The equality path is unchanged and adds no process.
- `cmd_status` in the integrate phase prints one `CARRY:` line per carried
  step beside the existing `STACK:` line, using the same reader as `next`,
  printing an unknown answer as unknown, and refusing nothing.
- `plugins/hexaemeron/tests/test_carried_step_commits.py` gains CLI cases
  proving that `done merge-step` refuses a whole and a partial carry with
  `.hexaemeron/state.json` and `.hexaemeron/ledger.jsonl` byte-identical, that
  an equal tip still receipts, that a repaired range holding an owned commit
  refuses, and that `status` prints the `CARRY:` line and exits 0.
  `python3 -m unittest plugins.hexaemeron.tests.test_carried_step_commits -v`,
  run by hand from the run worktree, reports at least 18 tests and `OK`.
- `.hexaemeron/design/reports/gained-range-ownership-product-refuses-specimen-stack.json`
  exists, written once by `conform_carry.py`, and reads `true`; its
  byte-identical copy sits at
  `docs/fiat-carried-step-commits/reports/gained-range-ownership-product-refuses-specimen-stack.json`.
- The `hexctl.py` digest cascade, the package bump and the three `.horos`
  artefacts are current.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_carried_step_commits.py`,
`docs/fiat-carried-step-commits/reports/gained-range-ownership-product-refuses-specimen-stack.json`
(new), `tests/promise_machine_coverage.json`,
`docs/promise-machine/obligation-gates/evaluation-run.json`,
`docs/promise-machine/obligation-gates/integration-projection.json`,
`docs/promise-machine/obligation-gates/integration-projection.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `tests/test_version_propagation.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`, `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.
**Tests.** `plugins/hexaemeron/tests/test_carried_step_commits.py` grows by at
least 6 CLI cases to at least 18 tests. Existing Hexaemeron tests are
unchanged.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`
**Disciplines.** phylax: no new child process; the merge-time check reads the
range `verify_local_range` already enumerated (study section 9). ephoros: the
`CARRY:` line answers study section 8's question 2. elenchus: each new case is
red on the parent of its fixing commit (study section 11). metron: none,
`done merge-step` adds no process and no performance claim is made (study
section 10). hypomnema: none new; the draft record from Step 1 already holds
the three decisions.

## Step 4: Document the guard, record the generation and re-pin

**Goal.** State the rule where operators and the controller's own skill text
describe the stack coming down, add the generation row, move the skill version
and re-pin every digest that binds those files.
**Entry.** Step 3's exit tree.
**Exit.** Each command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1480-refuse-a-later-step-s-commits-carried-into --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/references/push-discipline.md plugins/hexaemeron/skills/fiat/SKILL.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/hexaemeron/skills/fiat
```

- `plugins/hexaemeron/skills/fiat/references/push-discipline.md` gains one
  paragraph after the evidence-boundary paragraph in "Bringing the stack
  down" stating the gained-range rule, the ownership set, the adoption
  exclusion, the unknown rule, the merge-time intersection and the `CARRY:`
  status line, and that a cherry-picked copy is not detected.
- `plugins/hexaemeron/skills/fiat/SKILL.md` gains one or two sentences in the
  Integrate paragraph that starts "Before each merge, an unchanged waiting
  head passes", after byte 29736 of the starting file. Nothing between bytes
  18784 and 29736 changes except the frontmatter version line, which keeps
  its byte length.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md` gains exactly one row on the
  `generation` axis and its `Current version` line names the same version.
  The row keeps frontier revision `delegated-task-identity` and frontier
  SHA-256 `a54452aef0e415d7d17a548751178de0804d22af4829255b3c5d8bfe289581f1`,
  names issue 1480, the draft record path and the committed study and runbook
  copies as evidence, and states the rule, the evidence split and that the
  held target is unchanged. The version is fixed by the version-relations
  block above; no label is written here.
- `plugins/hexaemeron/skills/fiat/SKILL.md` frontmatter `version` names that
  same version, `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` in `hexctl.py`
  gains it as its last entry, and `tests/test_evolution_contract.py` moves the
  starting head's assertions into a by-version block and asserts the new head.
- The re-pins land in the same commit: the ledger digest in
  `tests/fixtures/promise-machine/runtime/fiat-final-integration.json`, the
  agent-instruction chain in `tests/fixtures/agent-instruction-v1/manifest.json`
  and the `fiat-study-runbook-phase` fixture's `compact.wai`, `model.json` and
  `source-spans.json` with the recorded counts carried across the offset delta,
  the rows in `tests/promise_machine_coverage.json` that name `SKILL.md`,
  `EVOLUTION.md` or `hexctl.py`, and the `hexctl.py` digest cascade. No
  measurement, parity run, tokenizer or model process runs.
- The demo path of study section 1 holds on the finished tree: the test module
  reports at least 18 tests and `OK` by hand, the conformance report copy
  equals the receipted report, and the checks runner above is green.
- The package bump and the three `.horos` artefacts are current.

**Files.** `plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (the compatibility set
only), `tests/test_evolution_contract.py`,
`tests/fixtures/promise-machine/runtime/fiat-final-integration.json`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`,
`tests/promise_machine_coverage.json`,
`docs/promise-machine/obligation-gates/evaluation-run.json`,
`docs/promise-machine/obligation-gates/integration-projection.json`,
`docs/promise-machine/obligation-gates/integration-projection.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `tests/test_version_propagation.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`, `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.
**Tests.** None written; `tests/test_evolution_contract.py` is updated, and the
root suite's evolution-contract, version-propagation, agent-instruction and
Promise Machine tests are the gate.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-4.json`
**Disciplines.** hypomnema: the generation row is the decision's ledger home,
and the two prose homes are where an operator and the controller's skill text
read the rule (study section 12). elenchus: a red pin test is traced to the
exact digest it names before anything is re-pinned. phylax: none, no new
boundary. ephoros: none, nothing runs unattended. metron: none, the fixture's
recorded counts are carried rather than measured.

### Amendment -- 2026-09-18

**What changed.** Complete replacement Exit: The command below exits 0 and reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/1480-refuse-a-later-step-s-commits-carried-into --scope root --scope hexaemeron --format json
```

- `refuse_rewritten_stack` returns the map of waiting-branch tips it read,
  branch name to observed tip, and keeps every refusal it has today;
  `test_the_step_being_merged_is_never_queried` still passes. `cmd_next` and
  `done_merge_step` hand that map to `refuse_carried_step_commits`, which reads
  only the tips the map lacks, so on a healthy stack `next` adds exactly one
  native process to today's cost: the current step's tip read. This settles
  audit finding S2-R1-01.
- An unknown gained range refuses with exactly one `hexctl: error:` line,
  naming the `<recorded>..<tip>` pair and claiming no cause; the read stays a
  bounded native child with the scrubbed relation environment,
  `--no-replace-objects`, no lazy fetch, the 30 s timeout, the 2 MiB cap and
  the 500-commit limit (audit finding S2-R1-02).
- `done_merge_step` calls the carry guard after `refuse_rewritten_stack` and
  before `inspect_pull_request`, so a carry refuses before any GitHub evidence
  is recorded. When the current tip is unequal to the recorded head, the
  repaired range `pr_base..remote_head` that `verify_local_range` already
  enumerates is intersected with the ownership set before `effective_push` is
  built; a non-empty intersection refuses naming the first carried commit and
  its owning step. The equality path is unchanged and adds no process.
- `cmd_status` in the integrate phase prints one `CARRY:` line per carried
  step beside the existing `STACK:` line, using the same reader as `next`,
  printing an unknown answer as unknown, and refusing nothing.
- `plugins/hexaemeron/tests/test_carried_step_commits.py` gains CLI cases
  proving that `done merge-step` refuses a whole and a partial carry with
  `.hexaemeron/state.json` and `.hexaemeron/ledger.jsonl` byte-identical, that
  an equal tip still receipts, that a repaired range holding an owned commit
  refuses, that `status` prints the `CARRY:` line and exits 0, and that on the
  healthy three-step fixture `next` reads each unmerged branch's tip once
  across both guards. `python3 -m unittest plugins.hexaemeron.tests.test_carried_step_commits -v`,
  run by hand from the run worktree, reports at least 19 tests and `OK`.
- `.hexaemeron/design/reports/gained-range-ownership-product-refuses-specimen-stack.json`
  exists, written once by `conform_carry.py`, and reads `true`; its
  byte-identical copy sits at
  `docs/fiat-carried-step-commits/reports/gained-range-ownership-product-refuses-specimen-stack.json`.
- `docs/fiat-carried-step-commits/runbook.md` is byte-identical to the
  receipted `.hexaemeron/runbook.md`, this amendment included.
- The `hexctl.py` digest cascade, the package bump and the three `.horos`
  artefacts are current.

Complete replacement Files: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_carried_step_commits.py`,
`docs/fiat-carried-step-commits/reports/gained-range-ownership-product-refuses-specimen-stack.json`
(new), `docs/fiat-carried-step-commits/runbook.md`,
`tests/promise_machine_coverage.json`,
`docs/promise-machine/obligation-gates/evaluation-run.json`,
`docs/promise-machine/obligation-gates/integration-projection.json`,
`docs/promise-machine/obligation-gates/integration-projection.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `tests/test_version_propagation.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`, `.horos/boundary.json`,
`.horos/candidates.json`, `.horos/census.json`.

Complete replacement Tests: `plugins/hexaemeron/tests/test_carried_step_commits.py`
grows by at least 7 cases, 6 CLI cases for `done merge-step` and `status` and
one tip-read count case, to at least 19 tests. Existing Hexaemeron tests are
unchanged except `refuse_rewritten_stack`'s callers reading its return value.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`

Complete replacement Disciplines: phylax: no new child process; the merge-time
check reads the range `verify_local_range` already enumerated, and the shared
tip map removes the repeated `ls-remote` reads (study section 9). ephoros: the
`CARRY:` line answers study section 8's question 2, and the single-line unknown
refusal answers question 4. elenchus: each new case is red on the parent of
its fixing commit (study section 11). metron: the study's recorded cost of one
added native process per healthy `next` (study section 10) is now checked by
the tip-read count case rather than claimed. hypomnema: none new; the draft
record from Step 1 already holds the three decisions.
**Why.** Step 2, round 1 recorded two accepted findings. S2-R1-01: the carry
guard re-read every unmerged tip through `git ls-remote` after
`refuse_rewritten_stack` had read the waiting ones, three reads against the
study's one added process on the three-step fixture; Step 2's receipted Exit
bound `refuse_rewritten_stack` unchanged, so the shared read lands here.
S2-R1-02: an unknown range printed two error lines; round 2 fixed it on the
Step 2 stacked branch and this Exit keeps that property. The runbook copy joins
Files because this amendment makes the Step 1 copy trail.
**Steps touched.** Step 3.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
