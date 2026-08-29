# Bind a step merge to the pull request the directive names

Issues: [skills#594](https://github.com/wildcat-finance/skills/issues/594) and
[skills#555](https://github.com/wildcat-finance/skills/issues/555).
Base: `main` at `a79e663a136c446a6653ddbb14648782fef99173`.
Controller driving this run: `fiat-v5.22.1`.

## Assumptions

Proceeding on these unless corrected:

1. Python 3.14.6 and stdlib `unittest`. No new dependency, no new subprocess
   beyond the bounded `git` and `gh` readers already here.
2. This run delivers both halves and closes both issues. They are one mechanism:
   detection without command binding leaves the mistyped command open, and
   binding without detection leaves the GitHub-interface click open. Fiat closes
   only the issue bound at `init`, so #555 is closed by hand at integration.
3. The checks run only while `state["phase"] == "integrate"`. Nothing else in the
   loop is affected, and a run that merges its stack in order sees no change.
4. `next` and `status` may read the remote during that phase. They already cost a
   subprocess; the trade is stated in item 4 and the fail-open decision for
   `status` in item 11.
5. No receipt already on a ledger changes shape.

## 1. Problem statement

The controller refuses the operations it performs and cannot refuse the one that
does the damage.

`_integrate_directive` emits the pull request it means:

```json
{"do": "merge-step", "step": 3, "pr_url": ".../pull/589", "into": "fiat/576-..."}
```

Nothing binds the merge to that URL. The operator reads it and types
`gh pr merge <n>`, and `done merge-step` then checks that the pull request the
*receipt* names was merged. The merge itself is unguarded, and neither issue's
failure surfaces until integration, by which time the stack cannot be repaired.

Two routes into the same state, one per issue.

**#594.** During the issue 576 run a shell loop passed an empty argument.
`gh pr merge` with no argument falls through to the current branch's pull
request, which was step 5's, so #591 merged while the directive asked for step 3.
A Fiat stack chains, so the topmost branch holds every commit in the run and one
merge landed all of them.

**#555.** In #429, #542 merged step 2 into the step-1 branch rather than the run
branch, from the GitHub interface. Step 2's range became empty and step 1's grew
to 32 commits and swallowed a GitHub-signed merge. That run lost two receipted
steps.

**Why neither is repairable afterwards.** After #576's misordered merge, #589 and
#590 had no route back. `done merge-step` requires
`baseRefName` to equal the run branch; `gh pr edit --base <run branch>` is refused
by GitHub with "There are no new commits between base branch and head branch",
because the heads are already ancestors of it; and a pull request can neither
merge into a base it is an ancestor of nor be opened with no diff. The run
finished by hand with no terminal receipt.

**What is built.** Two changes. The controller refuses when a step still waiting
to merge is already reachable from the run branch, or when its recorded pull
request's base is no longer the run branch, at `next`, at `status` and at
`done merge-step`. And the `merge-step` directive carries the exact merge
invocation, pinned to the recorded URL, so the operator copies rather than
retypes.

**A working prototype.** A scratch run whose stack is merged out of order is
refused at the next directive, by name, with the fault and the step named. The
demo path is the last step: build that run in a temporary repository, merge the
wrong branch, and show `next`, `status` and `done merge-step` each refusing, then
show the directive carrying its own merge command on a healthy run.

## 2. Prior art

**In this repository.** `refuse_rewritten_stack`
(`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`) is the shape both issues
point at. It walks every step still waiting, compares its remote tip against the
head its push receipt names, and refuses by name rather than letting a downstream
symptom surface. It skips the current step and the merged ones, and reports an
unreadable branch rather than passing it. #555 says so explicitly: "the same
treatment applied earlier in the loop would have caught #542 at the next
directive". This run reuses that walk rather than adding a second one.

`commit_is_ancestor` already answers the ancestry question fail-closed: only exit
0 and 1 count as answers, because reading an unexpected status as "no" would turn
a broken call into a finding about a person. `remote_branch_tip` already reads one
ref with a bounded `ls-remote` and refuses a malformed or duplicated answer.
`inspect_pull_request` already reads a pull request's base, head and state.

**The last two merged pull requests touching Fiat.**
[#593](https://github.com/wildcat-finance/skills/pull/593) is the #576 delivery,
whose own integration is the evidence for #594; its carried-forward names this
gap in the words the issue repeats.
[#585](https://github.com/wildcat-finance/skills/pull/585) delivered #554's
runbook amendment receipts and carried forward four issues, of which #555 is one
and is answered here. #556, #557 and #508 stay open and are stated as non-goals.

**In the audit record.** `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md`
holds this run's own reason for existing, under `## Integration`: the full
account of the misordered merge, why each repair route was closed, and the lead
recorded as the maintainer's. #555's body carries the #429 account, and
[#551](https://github.com/wildcat-finance/skills/issues/551) records that case in
full. No round in either log has previously proposed a guard for this, and none
records a lead about it that was left unpursued.

**Outside.** Nothing borrowed. Both surfaces are ancestry arithmetic and one
formatted string.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref: `main` at `a79e663a136c446a6653ddbb14648782fef99173`.
- Python 3.14.6, stdlib only. No new dependency and no new external command.
- The controller driving this run is `fiat-v5.22.1`, so it cannot enforce what
  this run writes. Every claim rests on tests and on the last step's
  demonstration.
- No receipt already on a ledger changes shape, and a run that merges in order
  sees no difference.
- The emitted merge command is printed, never executed. This run does not make
  the controller merge anything.

**Non-goals.**

- Making the controller perform the merge. It closes the gap completely and it
  widens what the controller does on the operator's behalf. Item 4 records the
  trade and rejects it for this run.
- Repairing a run already in the broken state. There is no repair; that is the
  finding. The refusals name the state and say so.
- #556's dynamic target-version resolution, #557's lost-ledger recovery and
  #508's executable runbook-command validation, all carried forward by #585.
- The read-side question from [#583](https://github.com/wildcat-finance/skills/pull/583),
  whether other tests bind to a path a live run owns.

## 4. Design options

**Option A. Extend the existing waiting-step walk, and print the command.**
`refuse_rewritten_stack` becomes one walk that answers three questions per
waiting step: has its branch moved since its push, is its head already reachable
from the run branch, and is its recorded pull request still based on the run
branch. It runs at `done merge-step` as now, and at `next` and `status` while the
phase is `integrate`. Separately, the `merge-step` directive gains the exact
`gh pr merge` invocation built from the recorded URL.
Trade: `next` and `status` read the remote during integration, so both cost a
network call in a phase where they were local. Bounded by the phase and by the
readers already in place.

**Option B. Detection only, at `done merge-step`.** The smallest change and it
catches nothing earlier than today. Rejected: #555's whole point is that the
refusal has to arrive while the stack is still repairable, and #576's arrived
three steps late.

**Option C. The controller performs the merge.** `done merge-step` already reads
the pull request; a verb that merges the recorded URL and receipts it would close
the gap with no operator step to get wrong. Rejected for this run: it turns a
receipt into an action, which is a different promise, and it removes the operator
from a publication step. Worth its own study if the guard proves insufficient.

**Option D. Print the command, no detection.** Fixes #594's route and leaves
#555's, since a click in the GitHub interface never reads the directive.
Rejected.

**Chosen: A.** It closes both routes, reuses a walk that already exists for a
neighbouring fault, and its two refusals are one ancestry call and one field
comparison each.

## 5. Risk register seed

Both boundaries are reads: the remote refs the walk consults, and the pull
request payload it already reads. The emitted command is a string the controller
prints and never runs. The concern that is not a boundary is a false refusal: a
guard that fires on a healthy run would block every integration, so the walk has
to skip exactly what it skips today.

```risk-register
premature-merge-undetected | the run branch tip against each waiting step's recorded head | a waiting step already reachable from the run branch refuses at next, at status and at the receipt
retarget-drift | each waiting step's recorded pull request base | a base that is no longer the run branch refuses by name
false-refusal | the set of steps the walk inspects | already-merged steps and the step being merged are skipped, exactly as the existing walk skips them, and a healthy stack reaches integrate unchanged
ancestry-unanswered | the exit status of git merge-base --is-ancestor | only 0 and 1 count as answers and anything else refuses rather than reporting no
network-dependence | next and status during the integrate phase | the reads happen only in that phase, and an unreadable remote refuses at the mutating receipt while status reports it as undetermined
printed-command | the merge invocation the directive carries | it is built from the recorded URL and the repository the controller already resolves, both already validated, and it is printed rather than executed
```

## 6. Glossary seeds

- **Waiting step.** A step with a push receipt that the integrate phase has not
  yet recorded as merged.
- **Premature merge.** A waiting step whose head is already reachable from the
  run branch without a merge receipt naming it.
- **Retarget drift.** A waiting step whose recorded pull request no longer has
  the run branch as its base.
- **The walk.** The pass over waiting steps that `refuse_rewritten_stack`
  performs today and this run extends.

## 7. Sources

- [skills#594](https://github.com/wildcat-finance/skills/issues/594) and
  [skills#555](https://github.com/wildcat-finance/skills/issues/555).
- [skills#593](https://github.com/wildcat-finance/skills/pull/593) and
  [skills#585](https://github.com/wildcat-finance/skills/pull/585).
- `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md`,
  `## Integration`.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`: `refuse_rewritten_stack`,
  `_integrate_directive`, `done_merge_step`, `inspect_pull_request`,
  `commit_is_ancestor`, `remote_branch_tip`, `cmd_status`.
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md`, the retarget
  order.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md` at `fiat-v5.22.1`.
- `AGENTS.md`, the suite and lint commands.

## 8. Signals, and the questions behind them

Three, all asked at a refusal rather than at three in the morning.

- *Why can I not merge step 3?* The refusal names the step, the branch, and
  which of the two faults it found, rather than reporting a topology mismatch.
- *When did this happen?* The walk runs at every `next` during integration, so
  the first directive after the mistake carries it, which is what #555 asked for.
- *What do I type to merge this step?* The directive carries the exact
  invocation, so the answer is a copy rather than a number retyped from a URL.

[ephoros](../../skills/ephoros/SKILL.md) owns what a signal must carry.

## 9. Boundaries, per capability

Two reads and one string:

- **The remote refs the walk consults.** Worth taking: the fault is only visible
  against the published branch. The control is `remote_branch_tip`, which refuses
  a malformed or duplicated ref, and `commit_is_ancestor`, which treats anything
  but exit 0 or 1 as unanswered.
- **The recorded pull request payload.** Worth taking: retarget drift is only
  visible there. The control is `inspect_pull_request`, already bounded.
- **The printed merge command.** Built from the recorded URL and the resolved
  repository, both already validated by the controller, and printed rather than
  executed, so no argv is assembled from it.

Nothing else opens: no new dependency, no credential, no model output reaching a
command. [phylax](../../skills/phylax/SKILL.md) owns the boundary list.

## 10. The budget, or its absence

None. The walk adds at most one `ls-remote` and one `merge-base` per waiting step,
in a phase that already makes several GitHub calls per receipt, and no step is
taken in the name of speed. [metron](../../skills/metron/SKILL.md) has nothing to
measure here; a step that later claims one owes a recorded before and after.

## 11. The fail-closed posture

A refused `done merge-step` mutates nothing: every check runs before the receipt
is written, as the existing walk does. `next` refusing means the loop stops with a
named fault rather than emitting a directive that cannot be completed. `status`
is the exception and is deliberate: it is the command someone runs to find out
what is wrong, so an unreadable remote makes it report the question as
undetermined rather than refuse to answer at all.

The guard-test convention: one test per refusal, asserting the exact non-zero
exit, the named step in the message, and that the state file is unchanged
afterwards, each written to fail against the entry state.
[elenchus](../../skills/elenchus/SKILL.md) owns the triage order and the guard
rule.

## 12. Decisions and their homes

- **Refusing a topology fault before it is unrecoverable.** The ledger row is the
  record. It is a guard of the same kind as `refuse_rewritten_stack`, which
  earned no decision record, and no earlier decision is reversed, so no ADR is
  earned. Said here so the absence is a judgement rather than an omission.
- **Rejecting option C.** Recorded in item 4 and repeated in the ledger row,
  because a later reader asking why the controller still does not merge should
  find the reason rather than assume nobody considered it.
- **Where the two refusals are described.**
  `plugins/hexaemeron/skills/fiat/references/push-discipline.md`, which already
  owns the retarget order the faults violate.

[hypomnema](../../skills/hypomnema/SKILL.md) owns which decisions earn a record.

## Boundaries

**Always.** The root suite and the Hexaemeron suite before every commit. The
three bundled lints. Imprimatur and Brevitas on every shipped document. The
Protasis checker over this study and the runbook. Sapheneia's bounded pass on
every audit record before it is appended.

**Ask first.** Adding a dependency. Making the controller execute anything it
currently prints. Changing a receipt already on a ledger. Touching CI.

**Never.** Weaken an existing refusal to make a new one fit. Claim a lint, a
suite or a round ran when it did not. Force-push over the signed stack. Merge a
step pull request out of order, which is the fault this run exists to catch.

## Success criteria

Each is a command, run from the run worktree:

1. A waiting step already reachable from the run branch is refused, by name, at
   `next`, at `status` and at `done merge-step`.
   `python3 plugins/hexaemeron/tests/run_tests.py`, the new
   `PrematureStackMergeTests`.
2. A waiting step whose recorded pull request base is no longer the run branch is
   refused the same way. Same class.
3. A healthy stack reaches integration unchanged, with every existing merge-step
   test still passing. Same suite.
4. An unanswerable ancestry call refuses rather than reporting no; an unreadable
   remote refuses at the receipt and reports undetermined at `status`. Same class.
5. The `merge-step` directive carries the exact merge invocation for the recorded
   pull request. Same suite, `MergeCommandDirectiveTests`.
6. The whole tree stays green: `python3 -m unittest discover -s tests` at 349 plus
   this run's, and `python3 plugins/hexaemeron/tests/run_tests.py` at 1,045 plus
   this run's, both from inside the run worktree.
7. The demonstration in `plugins/hexaemeron/docs/fiat-bound-step-merge/proof.md`
   builds a scratch run, merges the wrong branch, and shows all three refusals.
8. `python3 plugins/horos/skills/horos/scripts/horos.py check .` reports the
   boundary matches the tree.
