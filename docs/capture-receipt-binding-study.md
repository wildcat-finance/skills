# Study: Bind the capture-profile receipt test to its artefact

Assuming, unless corrected:

1. Issue 435's tracked copies under `docs/promise-machine/` and the two digests pinned in the test are correct and stay as they are. This run changes where the test looks, not what it claims.
2. Python 3.11 or later with stdlib unittest, matching the module and every other suite here.
3. The run starts from `main` at `7f4264ecc26ac2149ddb99834433bee3b5dd9fdc`.
4. `CARRYOVER_GUARDS` keeps binding every carryover id to a test that exists, so a rename updates that map in the same commit.

## 1. Problem statement

Five tests in `tests/test_run_observation_capture.py` assert that `.hexaemeron/study.md` and `.hexaemeron/runbook.md` under the repository root are byte-identical to issue 435's tracked copies, two of them against the hard-coded digests `6858aaeadb12f204538b9120e51390b9c940fa995c8edb1471815d89aaa7f404` and `56df27b7faae2af8f7ba16ec89526413038def6a0bbf86ff0274dc566f8bf9c5`. Each skips only when those two files are absent. But `.hexaemeron/study.md` is not a fixture: Fiat's `init` cuts a worktree and every run owns that path, so the module skips five tests on a clean checkout and fails five inside any run worktree except issue 435's. The cost is not a red suite. It is that `python3 -m unittest discover -s tests` stops being usable as a step gate from inside a run, and every round has to establish by hand that its five failures belong to somebody else. Working prototype: the same five claims, established from the artefacts under test, passing inside a run worktree whose `.hexaemeron/study.md` belongs to that run. Demo path: `python3 -m unittest tests.test_run_observation_capture` in this run's own worktree, where that file is this study, with the five named tests reported as run and passed rather than skipped, and `python3 -m unittest discover -s tests` green in the same worktree.

## 2. Prior art

- The five tests are `test_receipted_copies_are_byte_identical_and_relocatable`, `test_receipted_copies_have_exactly_one_terminal_newline`, `test_receipted_sources_and_copies_are_digest_equal`, `test_receipted_copies_have_no_literal_newline_escape` and `test_receipted_sources_are_never_modified`, guarding carryover ids C1-04, R3-01, R4-01, R5-01 and R9-03. A sixth, `test_detached_receipt_test_skips_only_absent_receipts` (R9-01), asserts the skip reason is present in the module source, so it moves with them. `test_complete_union_manifest_covers_paths_and_carryover_guards` (R2-01) checks every id in `CARRYOVER_GUARDS` names a real test, which is what makes a rename a two-place edit.
- The audit record was read before design options were drawn. `audit/AUDIT.md` under `H003 quoted specimen, step 1, round 1` carries this as a lead not pursued, with both digests, the failure count, and the clean-checkout evidence at `5d6fc67bb6c861f2be631eef2d7bef3c01c73e84` that places the cause on `main` rather than in that step. The same run repeated the finding in its later rounds. Issue 500 declined it as another delivery's evidence binding, outside its files. This run is that lead.
- This run changes repository tests rather than a skill, so no plugin audit file is in scope. The root log is the only audit record over the target, and it is the one read above.
- The last two merged pull requests that changed the target: [skills#539](https://github.com/wildcat-finance/skills/pull/539), the issue 435 integration that introduced the module, whose carried-forward section names issues 436, 437 and 508 and says nothing about the receipt binding; and the `5550a5a` supersede merge over the same delivery, which repaired a shallow-checkout-only integration guard and left the binding untouched. Neither carried this forward, which is consistent with the record: the fault only shows from inside another run's worktree, and issue 435's own worktree was the one place it could not show.
- `ADR-022-define-the-run-observation-capture-profile.md` holds the capture-profile decision, and `test_capture_adr_has_the_repository_form` reads it. The ADR is not in scope here.
- The container clears both suites at the entry state: the root suite reports 345 tests, `OK (skipped=5)`, and those five skips are the target; the Hexaemeron suite reports 962/962.

## 3. Constraints and non-goals

- Starting ref: `main` at `7f4264ecc26ac2149ddb99834433bee3b5dd9fdc`.
- Non-goal: issue 435's tracked copies and the two pinned digests, which are correct and stay as they are.
- Non-goal: Fiat's controller, its state directory, and where a run's audit log lives. Issue 576 owns the related overlap-surface question and this run does not touch it.
- Non-goal: the twenty-four other tests in the module, which read tracked paths and pass in every worktree.
- Non-goal: widening the change to every test in the repository that reads an untracked path. The union manifest bounds this run to the module named in issue 574.

## 4. Design options

1. **Assert the tracked copies against the pinned digests and drop the `.hexaemeron` reads.** The original claim, that issue 435's receipted sources and their published copies were byte-identical, becomes the durable half of the same equality: the published copies still hash to the digests recorded from those receipted sources. Chosen: no live path, no skip, no environment dependence, and the guarantee is the same for all time because both halves are now recorded in the repository. Trades away detection of drift in the untracked source, which is unreachable in every checkout and became unreachable the moment issue 435's worktree was archived.
2. **Preserve a fixture of the receipted bytes under `tests/fixtures/`.** Rejected: the tracked copies already are those bytes, and a second copy adds a third artefact to keep in step for no additional claim.
3. **Condition the class on the root receipts actually being issue 435's, and skip with a reason otherwise.** Rejected: it keeps a live-path read and makes the skip permanent, because no checkout anywhere holds issue 435's receipts. A guard that skips in every environment is a guard that never checks anything, which is the state the five tests are in today.

## 5. Risk register seed

The audit loop should look hardest at a claim quietly weakened while its test still passes. The rewrite moves five assertions off a path they should never have read, and the way that goes wrong is a test passing because it now asserts less, not because the binding was fixed. The map from carryover id to test name is the second concern: `CARRYOVER_GUARDS` and the union-manifest test are the only things keeping a prior round's finding attached to a live test, and a rename that updates one and not the other breaks that attachment silently. Two of the five run `git show` through a subprocess; that argv stays pinned with no shell. No secret, socket or partial write is involved, and the module writes nothing outside a temporary directory.

```risk-register
weakened-claim | the five rewritten assertions | each still fails when a tracked copy's bytes change
guard-map-drift | CARRYOVER_GUARDS and the union-manifest test | every id still names a test that exists
dormant-skip | the rewritten tests | no skip path remains that can hide the claim in every environment
digest-transcription | the two pinned digests | each still equals the recomputed hash of its tracked copy
untracked-path-read | the module's repository reads | no assertion depends on a path a live run owns
subprocess-argv | the `git show` calls the module keeps | inputs stay pinned and no shell is used
```

## 6. Glossary seeds

- Receipted source: the `.hexaemeron/study.md` and `.hexaemeron/runbook.md` bytes Fiat pinned in issue 435's study and runbook receipts.
- Tracked copy: `docs/promise-machine/run-observation-capture-study.md` and its runbook sibling, the committed publication of those bytes.
- Carryover guard: an id in `CARRYOVER_GUARDS` bound to the test that keeps a prior round's finding fixed.
- Live-run path: a path Fiat's `init` gives to whichever run holds the worktree, `.hexaemeron/` being the one at issue here.

## 7. Sources

- `tests/test_run_observation_capture.py`, the five tests and `CARRYOVER_GUARDS`
- `docs/promise-machine/run-observation-capture-study.md` and its runbook sibling
- `audit/AUDIT.md`, the `H003 quoted specimen` sections of 2026-08-24
- [skills#574](https://github.com/wildcat-finance/skills/issues/574) and [skills#539](https://github.com/wildcat-finance/skills/pull/539)
- `plugins/hexaemeron/skills/fiat/SKILL.md`, on the run worktree and where state lives

## 8. Signals, and the questions behind them

One question, and it is the one that let this sit for a day: did the five tests run, or did they skip? A skip reads as a pass in every summary line the suite prints, so the step's exit requires the five named tests reported as run and passed, not merely an `OK` line. That is the whole signal surface: the module is a unittest invoked from a terminal, it runs nothing unattended, and [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal content where a deployed path exists.

## 9. Boundaries, per capability

The module reads repository files under `ROOT` and shells `git show HEAD:<path>` in two of the five tests. This run opens no boundary and closes one: an assertion that reads `.hexaemeron/` reaches into state another process owns and mutates during a run, and after this run nothing in the module reads it. The `git show` argv stays pinned with no shell, and the temporary-directory writes stay inside `tempfile` targets. [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary rules and its lint runs in every audit round. Always: both suites before a commit, the Imprimatur lint on every shipped document, the five named tests reported as run. Ask first: touching issue 435's tracked copies or its pinned digests, changing a carryover id, editing CI. Never: delete or skip a failing test to make the suite pass, edit receipted evidence to fit a test, claim a suite ran when it did not.

## 10. The budget, or its absence

None, and here is why: the module runs in under a second and this run removes work rather than adding it. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns budgets where a performance claim exists, and no step here makes one.

## 11. The fail-closed posture

What stops the run: a rewritten test that passes for a reason other than the binding, a failure the entry state also shows, or a carryover id left naming a test that no longer exists. A failure surfaced mid-step follows [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md): reproduce, reduce, fix the mechanism, guard it. The guard convention here is a source-level test, `test_receipt_assertions_never_read_a_live_run_path`, which fails at the entry state and passes after the rewrite. It is the same shape as the existing `test_detached_receipt_test_skips_only_absent_receipts`, which asserts against the module's own source, so the convention is already in the file.

## 12. Decisions and their homes

None owed, and here is why: this restores an existing intent rather than deciding anything new. Issue 435's claim was that its receipted sources and published copies were byte-identical, and the rewrite keeps exactly that claim against the artefacts that still exist. The reason the binding is to tracked bytes goes where [hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) puts a why: a comment at the binding site, so the next reader does not restore the live-path read, plus this study committed under `docs/` and the audit record of the round that checks it. No ADR is owed, because no decision here is expensive to reverse; the whole change is five assertions and one guard.
