# Issue 594: bind a step merge to the pull request the directive names

Rounds for the run on branch
`fiat/594-bind-a-step-merge-to-the-pull-request-the-di`, off `main` at
`a79e663a136c446a6653ddbb14648782fef99173`. The controller derived this path at
`init` with no operator action, which is issue 576's change on its first live
run. Headings carry step and round alone, because the file names the run.

## Step 1, round 1 -- 2026-08-24

Non-Solidity round over the two Markdown documents step 1 commits, at
`1e1b157d6a2ffce108359a9a47a07545a6e6c310`. Zero findings.

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and `tests`,
Hypomnema over `README.md AGENTS.md .agents plugins docs`. Protasis accepts the
shipped study in `--study` mode and the shipped runbook in runbook mode.
Imprimatur scores both 100.0 with no defects and Brevitas is clean on both. Horos
reports that the boundary matches the tree. The root suite reports 349 tests OK
with no skips and the Hexaemeron suite 1,045/1,045. The commit's local signature
is good and it carries exactly one co-author trailer and one origin trailer.

Both shipped copies are byte-identical to the receipted ones, which the issue 576
run could not manage: its study cited the five discipline skills as
`../<name>/SKILL.md`, which resolves from a skill directory and nowhere else, and
Hypomnema H001 caught all five once the file reached
`plugins/hexaemeron/docs/`. This study was written with `../../skills/<name>/`
from the start, so the exit holds in bytes rather than in content.

Two register concerns are reachable at this step and both were checked.
`false-refusal`: the step changes no code, so no guard exists yet to fire on a
healthy run. `network-dependence`: likewise, `next` and `status` are unchanged and
still make no remote read in the integrate phase. The other four,
`premature-merge-undetected`, `retarget-drift`, `ancestry-unanswered` and
`printed-command`, sit in the step 2 and step 3 diffs and are not yet reachable.

One thing worth recording about this run's own evidence. The controller driving
it is `fiat-v5.22.1`, the generation issue 576 published hours earlier, so this
is the first run whose audit log path was derived rather than set by hand and the
first whose `audit-round` directive names that path. Both worked with no operator
action. That is not a claim about this run's subject; it is the previous run's
change being exercised.

Leads not pursued: none.

## Step 2, round 1 -- 2026-08-24

Non-Solidity round over the run-branch movement guard, at
`c72ed15a85e6843c59abfcbb2330677f234c670f`. Zero findings.

The three bundled lints exit 0. `scripts/promise_machine.py check` and
`coverage --check` are clean after the recorded `hexctl.py` digest moved to
`315cf29ff9d7`-prefixed bytes; no promise or field map changed, because the diff
adds no result field. Horos reports that the boundary matches the tree. The root
suite reports 349 tests OK with no skips and the Hexaemeron suite 1,057/1,057
with the twelve new cases in `test_stack_topology.py`. Seven of those assertions
fail against the step 1 tip. The commit's local signature is good and it carries
exactly one co-author trailer and one origin trailer.

Three things went wrong while building this and all three were fixed before the
commit. They are recorded because each one is a way the guard could have shipped
wrong, not because any of them survived.

The first draft refused every healthy merge. A receipt runs *after* its own merge
has landed, so at `done merge-step` the run branch legitimately already holds the
commit being receipted, and comparing it against the previous receipt makes every
correct run fail. The fix accepts the landing commit as well as the last
receipted one, and `test_a_healthy_stack_merges_unchanged` is the case that would
have caught it.

The second draft guarded `sync-run` and `integrate` as well as `merge-step`, and
broke `test_pinned_starting_commit_syncs_and_integrates_into_the_named_base`.
`_integrate_directive` returns `integrate` whether or not a sync has been
receipted, so after the stack lands the run branch may legitimately carry a merge
the controller has not recorded: that is what `done sync-run` exists to receipt.
The guard now stops when the stack does, which is also the honest scope, because
merge-step is where both issues' damage happens.

The third was in the test helper rather than the controller.
`self.fake_refs[self.state()["run_branch"]] = sha` binds the dictionary before
`state()` runs, and `state()` replaces it, so the write landed in a copy nothing
read afterwards and six cases passed against a guard that had not been given
anything to find. Named in the helper's docstring so the next reader does not
repeat it.

Four register concerns are reachable at this step and each was checked.
`premature-merge-undetected`: the movement check compares the remote tip against
this run's own receipts, and `test_it_refuses_at_next_rather_than_at_the_merge_after`
asserts it arrives at the directive rather than at the receipt after it.
`false-refusal`: `test_a_healthy_stack_merges_unchanged` merges three steps with
the guard live, `test_nothing_fires_before_the_first_merge` covers the state
where the controller has recorded no expectation, and the full suite passing at
1,057 is the wider evidence. `ancestry-unanswered`: not reachable as written,
because the final design compares recorded SHAs and asks git no ancestry question
at all, which is why it needs no local objects and works against an unfetched
remote. `network-dependence`: one `ls-remote` per merge-step directive, in a
phase that already makes several GitHub calls per receipt, and `status` reports
an unreadable remote as unknown rather than refusing. `retarget-drift` and
`printed-command` sit in step 3's diff.

One deliberate limit. The `ancestry-unanswered` concern was written against a
design that asked `git merge-base --is-ancestor` whether a waiting step's head
was reachable from the run branch. That design needs both objects present
locally, which an unfetched clone does not guarantee, and would have turned a
stale checkout into a refusal about a person. Comparing recorded SHAs answers the
same question with no objects and no fetch. The concern stays in the register
because the study is receipted; this is the record of why it is not reachable.

Leads not pursued: none.

## Step 3, round 1 -- 2026-08-24

Non-Solidity round over the merge command in the directive, at
`0bd4521194805290e9a214894046b27cd90156ae`. Zero findings.

The three bundled lints exit 0, `scripts/promise_machine.py check` and
`coverage --check` are clean after the recorded controller digest moved, Horos
reports that the boundary matches the tree, the root suite reports 349 tests OK
with no skips and the Hexaemeron suite 1,063/1,063. Four of the six new
assertions fail against the step 2 tip.

The `printed-command` register concern is the whole of this diff and was checked
against what it warns about. The string is built from the pull request URL the
push receipt recorded, which `GITHUB_PR_RE` has to match in full before the
command exists at all, and from nothing else: no repository flag, no number, no
value the operator supplies. It reaches `json.dumps` and a terminal, never
`subprocess`, and `test_no_other_directive_gains_a_command` asserts that no other
directive carries one. A receipt with no usable URL refuses, which
`test_a_missing_recorded_url_refuses_rather_than_guessing` and its malformed
companion cover, because a directive that guesses a merge target is the fault
this run exists to remove rather than a smaller version of it.

`retarget-drift` was reachable at this step and is not addressed. The study's
option A named it as a third question the walk could answer, and the delivered
walk answers two: has the branch moved since its push, and did the run branch
move outside the loop. Reading each waiting step's pull request base costs a
GitHub call per step at every directive, and the fault it would catch already
refuses at that step's own `done merge-step`, where `inspect_pull_request`
requires the base to be the run branch. The difference is when, not whether, and
the two checks that did ship already move the refusal to the directive. Recorded
as a lead rather than done quietly.

`false-refusal` was re-checked: the full suite passes at 1,063 with the command
live on every merge-step directive in every existing test.

Leads not pursued: one. Retarget drift, above. A waiting step whose pull request
base has been changed away from the run branch is still only caught at its own
merge-step receipt rather than at the directive before it. Catching it earlier
means one GitHub call per waiting step per directive, which is a real cost in a
phase that already makes several per receipt, and the study's chosen option did
not price it. Worth its own filing if a run ever loses a step to it; #429 lost
its steps to the branch-moved fault, which does refuse at the directive now.

## Step 4, round 1 -- 2026-08-24

Non-Solidity round over the prose, the ledger row and the demonstration, at
`c6db32ab733998d852acc27e3c0da33b455fc6bd`. Zero findings.

The three bundled lints exit 0. Imprimatur scores `proof.md`,
`push-discipline.md` and `.hexaemeron/run-pr.md` 100.0 with no defects. Horos
reports that the boundary matches the tree, so the new document earned no entry.
The root suite reports 349 tests OK with no skips and the Hexaemeron suite
1,063/1,063. `tests/test_evolution_contract.py` and
`plugins/hexaemeron/tests/test_evolution.py` both pass on the new row.

The row was checked against the contract rather than against the previous row's
shape. `fiat-v5.23.1` is a generation from `fiat-v5.22.1`, it retains
`state-shape-validation` and the digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa` byte for byte,
the header and the newest row name one version, and the held issue 363 job is
untouched. `main` was re-read immediately before the row was written: it had
advanced to `8e64802` for an unrelated change and its Fiat ledger was still at
`fiat-v5.22.1`, so the arithmetic is against the real predecessor rather than a
guess. That is the check the issue 576 run could not make from its own branch,
and it is why that row went in at the sync instead.

The proof was read against what it claims. Every line in it is `hexctl`'s own
output, driven through the same fake `git` and `gh` the suite uses, and the
document says that first rather than in a footnote. Both faults only exist in the
integrate phase, which needs a pushed stack and a GitHub that answers, so a bare
scratch repository cannot reach them; saying so is more useful than a transcript
that quietly used the harness. Its closing section states the three things it does
not establish: that anything prevents a person merging a pull request, that
retarget drift is covered, and that a run already in the broken state can be
recovered.

`push-discipline.md` was checked for agreeing with the tree. The `merge` field it
documents is the one `_integrate_directive` emits, the two refusals it names are
the two that ship, and the recovery it gives is the one the issue 576 run
actually took.

No register concern is newly reachable at this step; the four that ship were
closed in steps 2 and 3 and were re-checked against the final tree.

Leads not pursued: none new. Step 3's retarget-drift lead stands.
