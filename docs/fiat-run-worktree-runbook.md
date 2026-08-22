# Runbook: a dedicated run worktree, created before preflight

Derived from the committed study. The chosen design is option A: `init` creates the run's worktree at a path derived from the run branch, puts the run's state in it, leaves one breadcrumb in the operator's checkout, and refuses by name when it cannot. Five steps, dependency order, one pull request each, every step green at both ends.

Every step's suite commands, run from the repository root with Foundry's bin directory on `PATH`. The Hexaemeron suite is green except the two pinned-toolchain assertions the study's amendment names:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
```

## Step 1: Commit the specification

**Goal.** Land the study and runbook in the repository so every later step has a committed yardstick.
**Entry.** The run branch `fiat/439-dedicated-run-worktree-before-preflight` at `main` `2eca5b90cb1bd90b7794e8e2295d1619b3172271`, with the study receipted.
**Exit.** `docs/fiat-run-worktree-study.md` and `docs/fiat-run-worktree-runbook.md` exist and match the receipted artefacts; `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-run-worktree-study.md` and `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-run-worktree-runbook.md` both exit 0; `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` reports zero defects on both; all four suite commands exit 0.
**Files.** `docs/fiat-run-worktree-study.md`, `docs/fiat-run-worktree-runbook.md`.
**Tests.** None new. The four suite commands run unchanged as the both-ends-green check.
**Disciplines.** phylax: none, this step adds no boundary and no executable path. ephoros: none, documents emit no signal. metron: none, no performance claim. elenchus: none, no failure in hand. hypomnema: none, the decisions this run records land with their content in steps 3 and 5.

## Step 2: Derive and validate the worktree path

**Goal.** Turn a run branch into one refusable path, with no filesystem mutation and no state change.
**Entry.** Step 1's green exit.
**Exit.** `hexctl` holds a path deriver that flattens the run branch's separators and places it under `tmp/fiat/`, plus a validator that resolves the candidate, requires it to be a descendant of the repository worktree root, refuses when any component is a symlink leaving that root, and refuses a path that already exists as anything other than this run's registered worktree; every refusal is one value-free line naming the path, exits non-zero, and writes nothing; `python3 -m unittest plugins.hexaemeron.tests.test_hexctl -k Worktree` passes; all four suite commands exit 0.
**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_hexctl.py`.
**Tests.** Positive: a plain run branch derives the expected path, and an issue-backed branch keeps its leading number. Negative, each observed failing before its guard: a target that is not a Git repository, a computed path that already exists as a file, a path that already exists as an unrelated directory, a component symlink pointing outside the repository root, a path escaping the root by `..`, and a refusal leaving no state, no ledger and no breadcrumb. Expected minimum: 10 new cases.
**Disciplines.** phylax: this step opens the path-validation boundary, closed by canonical descendant checks, symlink refusal following the Horos S4-R1-01 finding, and no shell interpolation. ephoros: the stable refusal lines are what a three in the morning reader gets, so they land here with their exact wording. metron: none, one path computation makes no performance claim. elenchus: every refusal class is captured red before its guard. hypomnema: none, the path choice is recorded with the creation behaviour in step 3.

## Step 3: Create the worktree at init and put the run's state in it

**Goal.** Make isolation a property of `init`, so no run can forget to arrange it.
**Entry.** Step 2's deriver and validator, green.
**Exit.** `hexctl init` validates the path, runs `git worktree add -b <run branch> <path> <base>` through the existing bounded fixed-argv reader, writes `.hexaemeron/` inside the new tree, writes one breadcrumb line at `.hexaemeron/worktree` in the origin checkout, prints the exact `--dir` to use next, and refuses before writing any state when the branch is already checked out elsewhere or `git worktree add` fails; a run started from a deliberately dirty origin checkout succeeds; the origin checkout's `HEAD` and `git status --short` are identical before and after; `python3 -m unittest plugins.hexaemeron.tests.test_hexctl -k Worktree` passes; all four suite commands exit 0.
**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_hexctl.py`, `docs/decisions/ADR-fiat-run-worktree.md`.
**Tests.** Positive: `init` creates the tree and the run branch, state lands in the tree, the breadcrumb names it, `git worktree list --porcelain` shows exactly one new entry, and a dirty origin checkout still starts. Negative, each observed failing first: the run branch already checked out in another worktree, `git worktree add` failing, and a failed creation leaving no state, no ledger, no breadcrumb and no directory. Invariant: origin `HEAD` and `git status --short` unchanged across a successful `init`. Expected minimum: 12 new cases.
**Disciplines.** phylax: this step opens filesystem creation and two git invocations, closed by fixed argv with no shell, the step 2 validator ahead of any mutation, and write access in the origin checkout narrowed to one breadcrumb line. ephoros: `init` prints the worktree path and `status` reports it, which answers where the run is working. metron: none, one `git worktree add` outside any loop. elenchus: creation and refusal faults are guarded red to green, and a refusal leaves state and ledger bytes identical. hypomnema: the ADR lands here, recording the worktree home, the fail-closed refusal, and the breaking change for in-place runs, because that choice becomes real in this step.

## Step 4: Resume into the recorded worktree, and clean up at integrate

**Goal.** Let a resumed run find its tree, and let a finished run put the tree away without ever discarding uncommitted work.
**Entry.** Step 3's creation path and breadcrumb, green.
**Exit.** A `status` or `next` run in the origin checkout that finds a breadcrumb and no state prints the recorded worktree path and the exact `--dir` to use, exits non-zero, and changes nothing; a resume whose recorded worktree is absent refuses naming that path rather than creating a second tree; `done integrate` removes the worktree without force when it is clean and records that, keeps it and records it as kept when it holds modifications, and never forces; existing `.hexaemeron/` state in an origin checkout still resumes, and the archived-run fixtures still pass; `python3 -m unittest plugins.hexaemeron.tests.test_hexctl -k "Worktree or Resume"` passes; all four suite commands exit 0.
**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_hexctl.py`.
**Tests.** Positive: breadcrumb resolution prints the path and the `--dir` form; a clean tree is removed at integrate and the receipt records the removal; a tree holding a modified file is kept and the receipt records it as kept. Negative, observed failing first: a recorded worktree that has been deleted, a breadcrumb naming a path outside the repository root, and an integrate that would need force. Regression: a legacy state directory in the origin checkout resumes unchanged, and the archived runs keep verifying. Expected minimum: 10 new cases.
**Disciplines.** phylax: resume reads an on-disk path written earlier, so the step 2 validator runs on it again rather than trusting it. ephoros: the integrate receipt names the cleanup outcome, which answers what happened to the tree. metron: none, no performance claim. elenchus: absent-tree and force-needed cases are guarded red to green. hypomnema: none, this step implements the behaviour the step 3 ADR already records.

## Step 5: Correct the contract, record the ledger row, and run the demo

**Goal.** Make the written contract match the built behaviour, replace the advice that cannot work, and prove the whole path from clean inputs.
**Entry.** Step 4's complete behaviour, green.
**Exit.** `SKILL.md` states that the run works in a dedicated worktree created before preflight, where it lives, that `--dir` points at it, the cleanup rule, and the fail-closed fallback; the kernel-lock refusal at `hexctl.py` no longer advises `git worktree add ../<name> main`, which fails when the base is already checked out, and names a command that works; `plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries exactly one new generation row retaining `state-shape-validation` and its digest `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`, with the held [skills#363](https://github.com/wildcat-finance/skills/issues/363) job byte-identical; the study's demo path runs from a dirty checkout and leaves the operator's `HEAD` and `git status` unchanged; the not-a-repository demonstration refuses and creates no state; `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` reports zero defects on every changed document; `python3 plugins/horos/skills/horos/scripts/horos.py check` exits 0; all four suite commands exit 0.
**Files.** `plugins/hexaemeron/skills/fiat/SKILL.md`, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_hexctl.py`, `plugins/hexaemeron/tests/test_fiat_skill.py`, `plugins/hexaemeron/README.md`, `.horos/boundary.json`.
**Tests.** The contract test asserts `SKILL.md` states the worktree behaviour and no longer carries the unusable advice; a lock-refusal test asserts the new command text; the demo path runs as a test from a dirty fixture checkout; the ledger row is held by the existing `tests/test_evolution_contract.py`. Expected minimum: 6 new cases plus every earlier test.
**Disciplines.** phylax: full boundary review over path validation, creation, resume and cleanup, with anything unresolved stated. ephoros: review the refusal lines and the recorded path and cleanup outcome from the demo run. metron: none, the change makes no speed claim and the demo measures nothing. elenchus: any failing demonstration is worked to its cause and guarded before the row is written. hypomnema: the ledger row records this generation and leaves the held frontier job untouched.
