# Study: let a step survive a pull request merged before integrate

Assuming, unless corrected:

1. The run targets `wildcat-finance/skills` and changes Fiat only. Protasis is
   named in issue 1021's opening line as the party that decides which skill the
   observation upgrades; this study reads the Required-behaviour section, finds
   it names `done push`, `merge-step` and the ledger, and concludes Fiat owns
   all of it. No Protasis file changes.
2. Python 3.14.6, the exact interpreter in `.python-version`, with stdlib
   `unittest` and the repository's own runner. No new dependency.
3. The starting base is `main` at `79072bef97360eff130410e2a767d47b936d414d`.
4. `plugins/hexaemeron/tests/hexctl_harness.py` remains the delivery harness a
   disposable-repository regression is built on, as issue 923's module does.
5. The frontier row this run owes is a generation entry, `fiat-v5.47.1` to
   `fiat-v5.48.1`, retaining frontier revision `state-shape-validation` and its
   digest, and leaving the held job `skills#363` untouched.

I will proceed on these unless corrected.

## 1. Problem statement

A Fiat step whose pull request is merged into its stacked base before the
integrate phase must still be receiptable, and the run must still reach
integration, without any published ref being rewritten.

Today the recovery is a maintainer force-pushing a published branch back to an
earlier head. Issue 1021 records that happening during the 972 run: step 1's
branch was moved back to `749c30f6` so step 2 regained a diff. An agent should
not need a human to rewrite a published ref to unstick a run.

A working prototype means all four of issue 1021's acceptance checks hold, and
the demo path is the last step's regression: against a disposable repository,
open a step pull request, merge it, then receipt the push and reach integrate,
with no ref rewritten. Proven by
`python3 plugins/hexaemeron/tests/run_tests.py --report {report}` over the new
module plus the existing Fiat suite.

## 2. Prior art

**The mechanism, read directly at the starting base.** The refusal is one line,
`hexctl.py:11330`, inside `inspect_pull_request` at `hexctl.py:11241`. Issue
1021's Cause section calls the mechanism `pull_request_topology`; no such
function exists. That string is the diagnostic prefix used by the neighbouring
`die` calls. The issue's quoted excerpt is otherwise byte-accurate.

Three call sites: `done_push` (`hexctl.py:6773`), `done_merge_step`
(`hexctl.py:8284`), `done_integrate` (`hexctl.py:8899`).

**Two claims in issue 1021 do not hold at this base, and the design turns on
them.**

`done push` does not always call with no merge SHA. It passes
`expected_merge_sha=args.merge_commit`, and `--merge-commit` is registered at
`hexctl.py:14480` on the shared `done` parser, so every `done` subcommand
accepts it. With it supplied, `inspect_pull_request` takes the
`merge_sha is not None` branch, requires the pull request to be merged at
exactly that commit, and never reaches line 11330. `done_push` then GitHub
verifies the merge commit and stores `merge_commit`, `github_merge_verified`
and the whole `pull_request` record in the push receipt.

The head evidence the issue argues survives an early merge is already enforced,
at `hexctl.py:11317`, before the early-merge refusal. A mismatched head refuses
first, whatever the merged state.

So the 972 run did not hit a missing mechanism. It hit an undocumented one.
`SKILL.md` gives the push receipt as `--pr-url`, `--head-commit` and
`--pr-base`, so there was nothing to tell the operator the flag existed. The
transition is therefore implicit, unauthorised and untested rather than absent,
which is what issue 1021's own Required-behaviour section asks to correct when
it says the transition has to be explicit and receipted.

**What is genuinely missing.** `done_merge_step` reads the integrate directive,
whose `into` is always the run branch (`_integrate_directive`,
`hexctl.py:6864`), and passes `expected_base=pending["into"]`. A step pull
request merged early merged into its *stacked* base, which for step N is step
N-1's branch, not the run branch. `expected_base` therefore mismatches and
`inspect_pull_request` refuses at `hexctl.py:11312`. Retargeting cannot fix it,
because a merged pull request's base is fixed. That is the dead end, one call
frame away from where the issue places it.

**The direct architectural precedent.** Issue 923, "honest step branch
extensions after push receipt", solved the sibling problem: a step branch that
moved after its push receipt. Its answer is the shape to follow. A bounded
native `merge-base --is-ancestor` admits topology only, a non-ancestor or an
unanswered query refuses without asserting a cause, and the current step still
earns complete live-range evidence under `effective_push` while the original
push receipt is never rewritten. Its module,
`plugins/hexaemeron/tests/test_step_branch_extensions.py`, keeps four outcomes
separate and states plainly that ancestry supplies no signature, identity or
cause.

**Pull requests read.** The last two merged pull requests that changed
`plugins/hexaemeron/skills/fiat/` are 1040, landed as `c148ab9a` and merged
2026-08-31T13:02:49Z, and 1017, landed as `08a1024c` and merged
2026-08-31T05:42:09Z. Read them by commit rather than by merge commit: this
repository mostly squash-merges, so a pull request that changed the skill arrives
as a direct commit and never appears in `git log --merges`, which surfaces
base-sync merges instead and answers a different question. Neither carries an
unfinished item bearing on this topic. The second matters most: 1017 is the pull
request whose early merge into step 1's branch produced issue 1021, so it is both
the prior art and the failure. The 972 run's own carried work is issue 1021
itself.

**Audit records.** The whole-set currency check,
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`,
run from the target root, exits 0 and reports `committed=match` for every
source it covers, 54 of them when this study was written: 48 under
`audit/rounds/`, five plugin `audit/AUDIT.md` files and the root `audit/AUDIT.md`.
The count rises as other runs record rounds, so it is stated as observed rather
than as a fixed property. A verified synopsis is therefore the authoritative
reading view. In-scope
sources and what was actually read:

- `audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md` --
  read as its verified synopsis, `source_sha256`
  `f53c30389a08d6008962707e54ad0802d64c5b957dead057f3bc3893e63f3ad5`. Three
  rounds, one finding S2-R1-01, medium, fixed in round. Elenchus verdict
  `passed` on both step 2 rounds, `null` on step 1.
- `audit/rounds/fiat-972-let-a-prose-phase-survive-a-large-generated.md` --
  read as its verified synopsis, `source_sha256`
  `343d1baae8a6ff152e6a208a2b5058fb0f9f747bb62e7623090b5d0f47e61db4`. Two
  rounds, zero findings, Elenchus verdict `null` on both.
- `plugins/hexaemeron/audit/AUDIT.md` -- read as its verified synopsis,
  `source_sha256`
  `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f`.
- `audit/rounds/fiat-710-give-sync-run-one-checked-transition-across.md` --
  read as its verified synopsis, `source_sha256`
  `16e702588384e3c4ef0020082c14b11f3f395249117bb6d38ada32572cbbbc50`. Read as
  the precedent for adding one checked transition.

Nothing was read as source-only, and no source is claimed as read where only
its synopsis was read. No `[missing legacy field: ...]` appears in any of the
four.

**Leads carried forward from issue 923, each answered.** Its record leaves four
amended-entry census events unpursued. All four are stated non-goals here, with
the reason: `test_resource_limits_refuse_before_publish` is a macOS `Errno 63`
path-length limit; `test_root_audit_is_the_exact_pinned_base_blob` is a stale
pin; `test_duplicate_state_and_ledger_keys_refuse` is a Python 3.14.6
deep-nesting assertion; `test_every_tracked_path_has_exactly_one_owner` counts
14 Homologia paths. None touches the push, merge-step or integrate transitions,
and none is repaired or suppressed by this run. The 972 record's own unpursued
lead, the `_checkpoint_ref_names` diagnostic from issue 774, is likewise
outside this run and stands.

**Outside this repository.** GitHub offers no way to unmerge a pull request and
no atomic expected-base lock on merge, so both the irreversibility the issue
describes and the post-check base-move gap Fiat already documents are
properties of the host, not of this design.

## 3. Constraints and non-goals

The starting ref is `main` at `79072bef97360eff130410e2a767d47b936d414d`. The
run branch is `fiat/1021-let-a-step-survive-a-pull-request-merged-be`. Python
is pinned at 3.14.6 and no dependency is added. The controller driving this run
is byte-identical to the Fiat at that base.

The controller gate ships inside the artefact it gates, so nothing this run
writes governs this run. Any early merge during this delivery still takes the
manual recovery.

Non-goals, each stated because issue 1021 names it or the frontier forbids it:

- Whether merging a stacked pull request early is good practice. Stack
  discipline is unchanged and the loop still brings the stack down in
  integrate.
- The base-drift work the 972 run needed afterwards. The sync and
  version-resolution transitions behaved as specified.
- The held frontier job `skills#363`, delegated task identity. Untouched, and
  the generation row must leave its target and acceptance condition byte-identical.
- The four issue 923 census leads and issue 774's `_checkpoint_ref_names`
  diagnostic, per item 2.
- Any change to `done integrate`'s existing gates. They keep every requirement
  they have now.
- Rewriting a published ref, under any candidate. This is the failure the issue
  exists to remove, not a fallback.

## 4. Design options

**`push-adopts-merge`.** `done push` gains an explicit, documented early-merge
path. It accepts an already-merged step pull request when the recorded head
equals the pull request head and the merge commit is reachable from the
recorded `pr_base`, records a distinct `early_merge` block in the push receipt
naming the merge commit, and `done merge-step` for that step is satisfied from
that record without asking GitHub to merge again. The trade: two existing
receipt shapes change, and `done push` carries a second meaning.

**`separate-adopt-transition`.** A new `hexctl adopt-early-merge --step N
--merge-commit <sha>` transition runs before `done push`, records the early
merge as its own ledger event, and leaves `done push` and `done merge-step`
reading that record. The trade: the cleanest audit trail and the clearest
ledger, against the largest new surface, a new subcommand, a new state key and
a new verify replay branch.

**`merge-step-ancestry`.** `done push` keeps today's behaviour with
`--merge-commit` merely documented, and `done merge-step` is extended to admit
a pull request whose merge commit is already reachable from the run branch,
mirroring issue 923's bounded `merge-base --is-ancestor` admission. The trade:
the smallest diff and the closest fit to an established precedent, against a
push receipt that records the early merge only implicitly, so a reader still
cannot tell an early merge from an ordinary one without inference.

The prose above explains the candidates. `.hexaemeron/design-evidence.json`
selects one from checked gates and comparative measurements.

## 5. Risk register seed

The audit loop should look hardest at whether a relaxed gate still refuses the
rewrite case it exists for, and at whether recorded evidence is being reused
where fresh evidence is owed. Issue 923's register is the seed; the concerns
below are its members that survive into this topic plus the ones this topic
adds. Prose carries what a line cannot: `head-mismatch-admitted` and
`unreachable-merge-admitted` are the two that turn a fix into a hole, because
each would let a genuinely rewritten branch pass as an early merge.

```risk-register
head-mismatch-admitted | the recorded head against the pull request head at push | a pull request head unequal to the receipted head still refuses, merged or not
unreachable-merge-admitted | the merge commit against the recorded pr_base | a merge commit not reachable from the recorded base refuses without asserting a cause
ancestry-unanswered | the bounded native merge-base query | an unanswered or failing graph query refuses as unknown rather than passing
second-merge-suppressed | merge-step for a step with a recorded early merge | the step is satisfied from the record only when that record is complete and verified
early-merge-indistinguishable | the push receipt and ledger event | a reader can tell an early merge from an ordinary push without inference
state-mutation-on-refusal | every new refusal path | a refused transition leaves state and ledger bytes unchanged
diagnostic-overclaim | the new refusal messages | a message names what was observed, never an unobserved cause
github-verification-gap | the merge commit adopted at push | the adopted merge SHA earns verified true and reason valid like any other
integration-gates-intact | done integrate after an adopted step | every gate integrate required before is still required
verify-replay-drift | hexctl verify over a run carrying an early merge | replay accepts the new receipt shape and still refuses a malformed one
legacy-run-compatibility | a run initialised before this change | its receipts keep their old shape and no early-merge evidence is inferred
regression-uses-disposable-repo | the acceptance regression | it drives the real sequence against a disposable repository, not a mock of the answer
```

## 6. Glossary seeds

- **Early merge.** A step pull request merged into its stacked base before the
  integrate phase, by someone other than this run.
- **Adopted merge.** An early merge that a checked Fiat transition has
  recorded, so later phases read it instead of merging again.
- **Stacked base.** The `pr_base` a step's pull request targets: the run branch
  for step 1, step N-1's branch for step N.
- **Reachable.** True when a bounded native `git merge-base --is-ancestor`
  answers that the merge commit is in the named ref's history.
- **Waiting head.** Issue 923's term for a step branch tip observed at merge
  time rather than at push time.

## 7. Sources

- Issue 1021, `https://github.com/wildcat-finance/skills/issues/1021`, and its
  filing contract added this run.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at
  `79072bef97360eff130410e2a767d47b936d414d`, lines 6705, 6773, 6844, 8260,
  8284, 8818, 8899, 11241, 11312, 11317, 11330, 14480.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, the push and integrate phase
  notes.
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md`.
- `plugins/hexaemeron/tests/test_step_branch_extensions.py` and
  `plugins/hexaemeron/tests/hexctl_harness.py`.
- The four audit sources named in item 2, with their digests.
- `plugins/hexaemeron/skills/VERSIONING.md` and
  `plugins/hexaemeron/skills/fiat/EVOLUTION.md` at `fiat-v5.47.1`.
- `docs/decisions/ADR-067-gate-a-run-on-what-its-issue-filed.md`.

## 8. Signals, and the questions behind them

Two questions get asked once this runs unattended, and
[ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what each signal must carry.

*Why did this step not need a merge?* The step that records the adopted merge
emits it, naming the step number, the merge commit and the ref it was reachable
from, so the integrate phase's silence about that step is explained rather than
merely absent.

*Was this an early merge or a rewritten branch?* The refusal path emits which
of the two checks failed, head equality or reachability, and what it observed,
so the two cases are told apart from the record alone.

## 9. Boundaries, per capability

[phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and the controls.

The change opens one boundary: a previously closed gate now admits a class of
GitHub-reported state it used to refuse. What is worth taking there is a merge
this run did not perform; the controls that close it are the two hard gates in
item 5, head equality and reachability, both refusing before any state is
written.

It also adds one bounded subprocess boundary, the native `merge-base
--is-ancestor` query, whose control is issue 923's established form: fixed
argv, no shell, and an unanswered query treated as unknown rather than true.

No new network boundary. The merge commit is verified through the existing
`verify_github_commits` path, and no new REST endpoint is read.

## 10. The budget, or its absence

None, and here is why: the change adds at most one bounded graph query per step
and reuses the GitHub reads `done push` already performs. There is no
performance claim, so [metron](../plugins/hexaemeron/skills/metron/SKILL.md) has nothing to measure
before and after. The one number worth holding is that no candidate adds a
network round-trip, which item 4's design record measures as a selection
criterion rather than a budget.

## 11. The fail-closed posture

[elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule.

What stops the run: any receipt command exiting non-zero; a head mismatch or an
unreachable merge commit at the new gate; an unanswered graph query; a GitHub
verification that does not report verified true and reason valid; `hexctl
verify` failing over a run carrying an adopted merge.

Every fix in an audit round follows the guard convention: a test that fails
without the fix and passes with it, added to the module the fix touches, named
in the round's record with its finding id.

## 12. Decisions and their homes

[hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where
each one lives.

Two decisions are expensive to reverse. The first is which transition owns the
adopted merge, because it fixes the receipt shape and the ledger event name,
and a receipt shape is append-only once a run has used it. Its record is a new
ADR under `docs/decisions/`, numbered at the time it is written.

The second is that a step with an adopted merge is satisfied from its record
rather than by a second merge, because it makes one recorded fact stand in for
an action. That belongs in the same ADR, since separating the two would leave
each half readable without its reason.

The correction to issue 1021's Cause section is not a decision and earns no
record beyond item 2 of this study.

## Boundaries this study states

**Always.** Both test suites before a commit. The `imprimatur` lint on every
shipped document. `python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py
verify` before any receipt that depends on earlier state. A recorded
measurement before any performance change.

**Ask first.** Adding a dependency. Changing an existing receipt shape a prior
run has already written. Touching CI. Widening the class of GitHub state a gate
admits. Editing an `EVOLUTION.md` frontier field other than the one generation
row this run owes.

**Never.** Rewrite a published ref, force-push over someone else's work, or
bypass a merge gate. Commit key material or an RPC credential. Edit a vendored
directory. Delete a failing test to make a suite pass. Claim a command ran when
it did not. Change the held `Next Fiat job` or its acceptance condition.

### Amendment -- 2026-09-01

**What changed.** Item 2's first claim is withdrawn. `done push` is merge-blind
for a step, and issue 1021 was right. `--merge-commit` is registered at
`hexctl.py:14480` on the shared `done` parser and does reach `done_push` as
`args.merge_commit`, but for a stacked step `done_push` refuses it at
`hexctl.py:6722` with "a step pull request does not merge during the run", and
that refusal sits inside `if stacked:` at line 6711, well before the call to
`inspect_pull_request` at line 6773. `stacked` is true whenever
`run_branch_of(state)` returns a branch, which is every run since 3.4, so the
`merge_sha is not None` branch inside `inspect_pull_request` is unreachable from
a step push and the refusal at line 11330 is the only outcome. Item 2's second
claim stands unchanged: the head check at `hexctl.py:11317` is enforced before
the merged state is consulted, so a mismatched head refuses first whatever the
merged state. The `done merge-step` base mismatch stands unchanged as an
independent gap.
**Why.** The first claim was drawn from reading `inspect_pull_request` and the
argument registration without reading `done_push`'s own guard clauses, so it
described a code path that exists but cannot be entered for the only case this
topic is about. Found while implementing step 2, which is where the code path
had to be entered. The correction removes a flag from the design's vocabulary
rather than changing the design: the selected candidate never named one, so
adoption is detected from the merged state itself, which also removes the exact
failure that trapped the 972 run, an operator who could not know a flag existed.
**Steps touched.** None. Item 2's description of the current mechanism only. No
step's entry, exit, files, tests or disciplines change, and the design record's
candidates, criteria and selection are untouched.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.
