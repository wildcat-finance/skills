# Runbook: bind a step merge to the pull request the directive names

Derived from `.hexaemeron/study.md`. Four steps. The two surfaces are separate
steps because they close separate routes into the same state: one is an ancestry
fault the controller has to notice, the other is a command the operator has to
be handed. The prose, the ledger row and the demonstration come last, after both
guards exist, so no document describes a refusal the tree does not make.

Every step runs from the run worktree. `<entry>` is that step's entry commit.

## Step 1: Commit the study and the runbook

**Goal.** Put the specification in the repository before any controller code
changes.

**Entry.** Run branch `fiat/594-bind-a-step-merge-to-the-pull-request-the-di` at
`a79e663a136c446a6653ddbb14648782fef99173`, study receipt recorded, no tracked
changes in the run worktree.

**Exit.** `plugins/hexaemeron/docs/fiat-bound-step-merge/study.md` and
`runbook.md` exist and carry the receipted content, differing from the run's
`.hexaemeron` copies only where a relative link has to resolve from the
committed location. Prove it with:

```bash
diff .hexaemeron/study.md plugins/hexaemeron/docs/fiat-bound-step-merge/study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/fiat-bound-step-merge/runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/hexaemeron/docs/fiat-bound-step-merge/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/fiat-bound-step-merge/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `plugins/hexaemeron/docs/fiat-bound-step-merge/study.md` and
`plugins/hexaemeron/docs/fiat-bound-step-merge/runbook.md`.

**Tests.** None new; the step adds no code. Expect the suites unchanged at 349
root and 1,045 Hexaemeron. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-1.json`.

**Disciplines.** phylax: none, the step adds no code and opens no boundary.
ephoros: none, two committed documents emit nothing at runtime. metron: none, no
performance claim. elenchus: none, no failure in hand at this step. hypomnema:
this step is the record of what the run intends; the study's item 12 states why
no decision record is earned.

## Step 2: Refuse a step merged out of order

**Goal.** The controller notices a waiting step that is already reachable from
the run branch, or whose pull request has been retargeted away from it, while
the stack can still be repaired.

**Entry.** Step 1's exit state, on branch
`fiat/594-bind-a-step-merge-to-the-pull-request-the-di-step-1-commit-the-study-and-the-runbook`.

**Exit.** The walk that `refuse_rewritten_stack` performs answers three questions
per waiting step rather than one: has the branch moved since its push, is its
recorded head already reachable from the run branch's remote tip, and is its
recorded pull request still based on the run branch. Each fault refuses by name,
naming the step and its branch. The walk runs at `done merge-step` as it does
today, and at `next` and `status` while the phase is `integrate`. Already-merged
steps and the step being merged are skipped, exactly as today. An ancestry call
that answers neither 0 nor 1 refuses. An unreadable remote refuses at `next` and
at the receipt and is reported as undetermined at `status`. A refused receipt
leaves the state file byte-identical. Prove it with:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl.py` or a new sibling module if that file is
near its bounded-read ceiling, and `tests/promise_machine_coverage.json` for the
recorded controller digest.

**Tests.** A new `PrematureStackMergeTests` class. Cases: a waiting step
reachable from the run branch refuses at `done merge-step`; the same refuses at
`next`; `status` reports it; a retargeted pull request refuses; a healthy stack
merges unchanged; the step being merged is not flagged against itself; an
already-merged step is skipped; an unanswerable ancestry call refuses; an
unreadable remote refuses at the receipt and reports undetermined at `status`;
and a refused receipt leaves the state digest unchanged. Expect about 10 new
tests, so roughly 1,055 Hexaemeron and 349 root. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-2.json`.

**Disciplines.** phylax: this step reads the remote and a pull request payload
inside a refusal path, so both bounded readers and the fail-closed ancestry rule
are what the study's item 9 names. ephoros: the refusal is the whole signal, so
it names the step, the branch and which fault was found rather than reporting a
topology mismatch. metron: none, at most one extra remote read per waiting step
in a phase that already makes several, and no performance claim. elenchus: the
failure in hand is the issue 576 integration recorded in
`audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md`, and the
guard is the reachability test, which fails against this step's entry state.
hypomnema: none here; the study's item 12 states why the ledger row is the
record.

## Step 3: Carry the exact merge command in the directive

**Goal.** The operator copies the merge invocation rather than retyping a number
from a URL.

**Entry.** Step 2's exit state, on branch
`fiat/594-bind-a-step-merge-to-the-pull-request-the-di-step-2-refuse-a-step-merged-out-of-orde`.

**Exit.** The `merge-step` directive carries the exact `gh pr merge` invocation
for the pull request it names, built from the recorded URL and the repository the
controller already resolves, beside the `then` it already carries for the
receipt. The command is printed and never executed. A directive whose recorded
pull request URL is missing or malformed refuses rather than emitting a command
built from nothing. Prove it with:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 scripts/promise_machine.py coverage --check
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, its test module,
and `tests/promise_machine_coverage.json`.

**Tests.** A new `MergeCommandDirectiveTests` class. Cases: the directive carries
the invocation and it names the recorded pull request; the invocation names the
resolved repository; a missing recorded URL refuses; a malformed one refuses; the
receipt command the directive already carried is unchanged; and no other
directive gains a command. Expect about 6 new tests, so roughly 1,061 Hexaemeron
and 349 root. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-3.json`.

**Disciplines.** phylax: the step formats a command string from recorded values,
so the study's `printed-command` concern is exactly this diff; nothing is
executed and no argv is assembled from it. ephoros: the command is the signal
that answers what to type. metron: none, one string. elenchus: the failure in
hand is the empty `gh pr merge` argument from the issue 576 integration, and the
guard is the test that the directive names the recorded pull request. hypomnema:
none here.

## Step 4: Reconcile the prose, record the row and demonstrate

**Goal.** Say what the two refusals are, record the generation, and show the
guard catching the fault that caused it.

**Entry.** Step 3's exit state, on branch
`fiat/594-bind-a-step-merge-to-the-pull-request-the-di-step-3-carry-the-exact-merge-command-in`.

**Exit.** `plugins/hexaemeron/skills/fiat/references/push-discipline.md` states
both refusals beside the retarget order they protect.
`plugins/hexaemeron/docs/fiat-bound-step-merge/proof.md` records a scratch run in
a temporary repository, built by this branch's controller, whose stack is merged
out of order: `next`, `status` and `done merge-step` each refuse by name, and a
healthy run's directive carries its own merge command. The ledger carries one new
generation row, read against `main` immediately before it is written, retaining
`state-shape-validation` and its digest, with `SKILL.md` frontmatter matching.
`.hexaemeron/run-pr.md` carries a `## Carried forward` section.
`.horos/boundary.json` matches the tree. Prove it with:

```bash
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/docs/fiat-bound-step-merge/proof.md plugins/hexaemeron/skills/fiat/references/push-discipline.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
```

**Files.** `plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`plugins/hexaemeron/docs/fiat-bound-step-merge/proof.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`, `tests/test_evolution_contract.py`,
`.horos/boundary.json` if the scan earns an entry, and `.hexaemeron/run-pr.md`.

**Tests.** None new. `tests/test_evolution_contract.py` and
`plugins/hexaemeron/tests/test_evolution.py` check the row's arithmetic, digest
and header agreement, `tests/test_version_propagation.py` checks the frontmatter
against the ledger, and `tests/test_boundary_currency.py` checks the boundary.
Expect the counts unchanged from step 3. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-4.json`.

**Disciplines.** phylax: none, the step writes documents and a ledger row.
ephoros: none at runtime; the operator-facing signals shipped in steps 2 and 3.
metron: none, no performance claim. elenchus: none, no failure in hand; the proof
demonstrates rather than reproduces, though the scenario it builds is the one
that caused the run. hypomnema: this is the step the study's item 12 names, and
it decides that the ledger row and `push-discipline.md` are the record and no
decision record is earned.
