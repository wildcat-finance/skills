# Study: a dedicated run worktree, created before preflight

Assuming, unless corrected:

1. Python 3.11 and the standard library, matching every other script in this repository. No new dependency.
2. The run's tree lives inside the repository under the already-ignored scratch root, at `tmp/fiat/<run branch>/`. A sibling directory outside the repository was offered and declined during this run, so it is recorded as rejected rather than left as an option.
3. Fail-closed is the chosen fallback. A target that is not a Git repository, or where `git worktree add` fails, refuses the run rather than continuing in place. This is a breaking change for anyone relying on an in-place run and is stated as one.
4. `.hexaemeron/` moves into the run's worktree, so `--dir` points at the worktree for the whole run. The operator's checkout keeps one breadcrumb naming the run's tree, so a resume can find it without being told.
5. The kernel lock stays exactly as it is. Worktrees make collision rarer; they do not remove the need for the guard when two writers share one state directory.
6. The held frontier job at [skills#363](https://github.com/wildcat-finance/skills/issues/363) is untouched, and this run's ledger row is a generation row retaining `state-shape-validation` and its digest.
7. This run began from `main` at `2eca5b90cb1bd90b7794e8e2295d1619b3172271`, with Fiat at `fiat-v5.10.1`.

I will proceed on these assumptions unless corrected.

## 1. Problem statement

A Fiat run takes over the checkout it starts in. The contract has the model cut the run branch with `git checkout -b` and every step branch the same way, so `HEAD` moves under whoever is standing in that directory, repeatedly, for the length of the run. Preflight then refuses to start when the tree is dirty, which is correct in itself and means an operator holding uncommitted work cannot start a run at all.

Fiat already knows the answer and only says so after the collision. The word `worktree` appears in the controller exactly once, at `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:507`, inside the refusal printed when the kernel lock is already held: it advises `git worktree add ../<name> main` and to run there instead. `SKILL.md:80` repeats that advice. Advice at the point of collision is not a run that cannot collide.

Build the isolation instead. `hexctl init` creates a dedicated worktree for the run before preflight work touches any branch, cuts the run branch in it, puts the run's state there, and refuses by name when it cannot. The operator's checkout is never checked out, never branched, and never left on a branch the run created.

Proved by this demo path, from a repository whose own tree is deliberately dirty:

```bash
cd <repo> && echo scratch > dirty-file.txt          # the operator's uncommitted work
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir . \
  init --topic "worktree demo" --base main
git rev-parse --abbrev-ref HEAD                      # unchanged: still the operator's branch
git status --short                                   # still shows only dirty-file.txt
git worktree list --porcelain                        # names tmp/fiat/fiat-worktree-demo
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py \
  --dir tmp/fiat/fiat-worktree-demo status
```

Exit 0 with the operator's `HEAD` and `git status` unchanged, the run branch checked out only in the new tree, and `status` answering from that tree, is what a working prototype means here. A second demonstration refuses: a directory that is not a Git repository produces one named refusal and creates no state.

## 2. Prior art

**The observation.** [skills#439](https://github.com/wildcat-finance/skills/issues/439) is the source, and it carries two costs from one session. A clone sitting on `codex/issue-19-general-github-resolver` had a run fast-forward that branch to `origin/main`, commit onto it, and report the commit as being on `main`; `git push origin main` then failed non-fast-forward because local `main` was a stale ref the run had never touched. The commit was correct and the report was wrong. Separately, two agents worked this repository in the same period; one happened to be in a worktree, so `main` moved 29 commits under it and the reconcile was an ordinary merge, where two agents in one checkout would have fought over `HEAD` and the index.

**The sibling that already does this.** Elenchus creates and removes worktrees today: `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py:299` runs `git worktree add --quiet --detach`, and `:361` removes it with `git worktree remove --force`. Its report path is held to the worktree at `:197` and `:254`, and `plugins/hexaemeron/tests/test_elenchus_checker.py:436` and `:460` capture `git worktree list --porcelain` before and after a check and assert the two are equal. That is the create, bound, remove, and prove-you-cleaned-up shape this study copies rather than invents.

**The path machinery to reuse.** Horos resolves and bounds worktree paths at `plugins/horos/skills/horos/scripts/horos.py:859`, and refuses with `leaves the worktree at ...` at `:901` and `:905`. Its audit round S4-R1-01 in `audit/AUDIT.md` is the reason the check has to be careful: an escape control that inspected only the given path refused a final-component symlink while allowing one mid-path, and because `git -C` resolves symlinks before answering, `check bridge/sub` reported a far repository as its own worktree. Any path this run accepts gets the same treatment.

**Two facts that decide the location.** `plugins/horos/tests/test_universe.py:240` proves a nested worktree is invisible to a scan of the parent even when nothing ignores it, because git reports it as a single opaque directory, and `:253` asserts `.claude/worktrees` is not ignored in that fixture. So ignoring the home is not needed to keep a scan honest. It is still needed for a different reason: Fiat's own preflight refuses a dirty tree, and an unignored directory in the repository root would show as untracked and block the next run. [PR #460](https://github.com/wildcat-finance/skills/pull/460) already established the root-anchored ignored scratch root `/tmp/`, whose stated purpose is that nothing under it is a deliverable, and [PR #463](https://github.com/wildcat-finance/skills/pull/463) closed that PR's one deferred item by holding the Horos candidates pass to the boundary's universe, noting no extra handling is needed for `.claude/worktrees/`. Placing the run's tree under `tmp/fiat/` therefore needs no new ignore rule.

**The advice in the contract is wrong as written.** `docs/hermes-rule-corpus-study.md:164` records a real run finding that "the local `main` is checked out in another worktree and cannot be fast-forwarded from here without disturbing it". Git refuses to check out a branch that is already checked out in another worktree, so `git worktree add ../<name> main`, the exact command at `hexctl.py:507`, fails in the ordinary case where the operator is standing on `main`. The fix creates the run branch in the new tree instead of borrowing the base.

**Merged work read before the design options.** The last two merged pull requests touching Fiat are [PR #457](https://github.com/wildcat-finance/skills/pull/457), which corrected the git-backed update route in `references/plugin-currency.md` and carries no unfinished material, and [PR #445](https://github.com/wildcat-finance/skills/pull/445), which bound task issues to run and step branches and shipped `fiat-v5.10.1`. PR #445 carries a `## Carried forward` section naming two items: the held job for [skills#363](https://github.com/wildcat-finance/skills/issues/363) remains byte-identical and out of scope, and an upstream merge and closure of [skills#438](https://github.com/wildcat-finance/skills/issues/438) require a Wildcat maintainer. Both stay open here. This run does not touch the #363 job, and #438's maintainer action is not something a run can do for itself.

**Audit records read.** Every Fiat round in `audit/AUDIT.md` was read: the installed-path proof, the delegation-packets family, state-shape validation, and task-issue branch names. No Fiat round mentions a worktree, so nothing accepted there governs this change, and every Fiat round's leads line says none. Four findings shape the work anyway. The delegation family's post-push merge incident cost a hard stop mid-run with the controller stuck in `integrate` and a whole out-of-band repair round that produced no forward transition, which is the cost profile of getting filesystem and branch identity wrong. Its integration sync closure records that rebasing would have rewritten 22 signed commits, so nothing here may rewrite a stack. State-shape validation's three rounds found nothing and established the standard this change is held to: a refusal is value-free, leaves state and ledger bytes identical, and `status`, `next`, `verify` and mutations share one diagnosis; its `legacy-state-rejection` check passed against all 11 archived runs, so existing `.hexaemeron/` state must keep resuming. Task-issue branch names contributes the refuse-before-state-creation discipline that a bad path must follow. The plugin-level `plugins/hexaemeron/audit/AUDIT.md` has no Fiat round; its Step 0 round 1 leaves one relevant lead unpursued, `os.replace` atomicity across filesystems if a user symlinks the state directory elsewhere, which is an argument for keeping the run's tree on the same filesystem as the repository.

**External standard.** [git-worktree](https://git-scm.com/docs/git-worktree) supplies the semantics this leans on: one branch may be checked out in one worktree at a time, `add -b` creates a branch and its tree in one step, `list --porcelain` is the machine-readable inventory, and `remove` refuses a tree holding modifications unless forced.

## 3. Constraints and non-goals

- **Starting ref and versions.** `main` at `2eca5b90cb1bd90b7794e8e2295d1619b3172271`, Fiat `fiat-v5.10.1`, frontier revision `state-shape-validation` with digest `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`. Promise Machine `promise-machine/v1`.
- **Toolchain.** Python 3.11 and the standard library. Git invoked through the existing bounded, fixed-argv, no-shell reader with its timeout and output cap. No new dependency, no network call.
- **Scope.** One run, one worktree, one deterministic path derived from the run branch. The worktree stays on the same filesystem as the repository.
- **Non-goals.** The kernel lock, which the issue puts out of scope and which stays as the guard for two writers sharing one state directory. Receipt shapes and ledger arithmetic, which do not change. The held #363 delegation-identity job. Concurrency beyond what isolation gives for free. Any change to `gh` verification, CI, or the audit and prose phases.
- **Always.** Both suites before a commit, the Imprimatur lint on every shipped document, the Promise Machine check and coverage check, and a fresh Horos boundary scan before a commit.
- **Ask first.** Adding a dependency. Touching CI. Changing a receipt shape or the state schema beyond the additive worktree fields. Widening what a path may point at. Removing the in-place path for callers who depend on it, which assumption 3 already flags as breaking.
- **Never.** Delete or force-remove a tree holding uncommitted work. Follow a symlink out of the repository. Interpolate a caller value into a shell. Rewrite a signed stack. Claim a check ran when it did not.

## 4. Design options

**A. `init` creates the worktree, and the path is derived from the run branch (chosen).** `hexctl init` validates the target is a Git repository, computes `tmp/fiat/<run branch with slashes flattened>/`, refuses if that path exists as anything other than this run's own tree, runs `git worktree add -b <run branch> <path> <base>` through the bounded reader, writes `.hexaemeron/` inside the new tree, leaves a one-line breadcrumb in the operator's checkout naming it, and prints the exact directory to use. Cleanup happens at `integrate`: remove the tree when it is clean, keep it and say so when it is not. The trade is that `init` now mutates the filesystem beyond its own state directory and owns a failure path it did not have before, in exchange for isolation that a run cannot forget to arrange.

**B. Contract text only.** Tell the model in `SKILL.md` to create a worktree before preflight. Cheapest to write and it changes no code. Rejected because it is the same shape as the defect: the current advice is also contract text, and it is both unenforced and, as `docs/hermes-rule-corpus-study.md:164` shows, wrong in the common case. A rule with no mechanism leaves no trace when it is skipped.

**C. A separate `hexctl worktree` command run before `init`.** Composable, and it keeps `init` free of filesystem work. Rejected because a run can simply not call it, which puts us back at option B with more surface, and because responsibility for isolating the run would then be split across two commands, either of which can be run without the other.

**D. An opt-in `--worktree` flag.** Smallest blast radius and no breaking change. Rejected because the default stays broken, and every incident in the issue happened on the default path. The fail-closed refusal in assumption 3 is the honest version of this choice: state the breaking change rather than hide behind a flag nobody sets.

Option A is the least construction that makes the isolation a property of the run rather than a thing an operator remembers.

The Promise Machine surface gains one promise:

- `fiat-run-isolation`: a recorded worktree path, its validated containment inside the repository, and the `git worktree add` result authorise running the loop in that tree and nothing else. It does not establish that the operator's checkout was clean, that the run's work is correct, or that a tree removed at integrate held nothing of value.

## 5. Risk register seed

```risk-register
path-escape | the computed worktree path and any caller-supplied override | the resolved path is a descendant of the repository worktree root, no component is a symlink leaving it, and refusal names the path without echoing its contents
branch-already-checked-out | the base ref and the run branch across worktrees | the run branch is created in the new tree with add -b rather than borrowing the base, and an existing checkout of that branch refuses by name
operator-head-mutation | the operator's checkout during init and every step | no command checks out, branches, or resets in the origin checkout, and a test captures HEAD and status before and after
stale-tree-reuse | an existing directory at the computed path | a path that exists and is not this run's registered worktree refuses before any state is written
uncommitted-work-loss | worktree removal at integrate | removal is never forced; a tree with modifications is kept, named, and reported rather than deleted
resume-orphan | a resumed run looking for its tree | the breadcrumb in the origin checkout and git worktree list agree, and a missing tree refuses with the recorded path rather than silently starting a new one
partial-write | state creation split across the origin checkout and the new tree | the worktree exists before any state byte is written, and a failed add leaves no state, no ledger, and no breadcrumb
cross-filesystem-atomicity | os.replace over the state directory | the worktree is created under the repository root so state writes stay on one filesystem
subprocess-control | argv passed to git worktree add and remove | fixed argv through the existing bounded no-shell reader with its timeout and output cap, and no caller value reaches a shell
legacy-state-resume | .hexaemeron directories from earlier runs | an existing state directory in the origin checkout still resumes, and the archived-run fixtures keep passing
dirty-origin-tree | preflight's refusal to start against uncommitted work | the dirty-tree check applies to the run's own tree, and a demonstration starts a run from a deliberately dirty checkout
```

Two things the block cannot carry. The first is that this change deliberately trades a smaller invariant for a larger one: `init` gains filesystem side effects, which is exactly the kind of widening the audit rounds are strict about, and the compensation is that every one of those effects is refusable before any state exists. The second is that removal at integrate is the only place work can be lost, so the rule is asymmetric on purpose: a clean tree goes, a dirty tree stays and gets named, and no flag in this change forces the other behaviour.

## 6. Glossary seeds

- `Origin checkout`: the repository directory the operator started the run from, which the run must leave untouched.
- `Run worktree`: the dedicated Git worktree created for one run, holding the run branch, every step branch, and the run's state.
- `Worktree home`: the ignored parent directory the run worktree is created under, `tmp/fiat/` at the repository root.
- `Breadcrumb`: the single line in the origin checkout naming the run worktree, so a resume can find it without being told.
- `Flattened run branch`: the run branch name with path separators replaced, used as the worktree directory name so one run maps to one path.
- `Clean removal`: worktree removal that git accepts without force, meaning nothing uncommitted was discarded.

## 7. Sources

- [skills#439](https://github.com/wildcat-finance/skills/issues/439), the observation and its two recorded costs.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at `:341`, `:426`, `:507`, `:645`, `:690`; `plugins/hexaemeron/skills/fiat/SKILL.md` at `:80` and its base-sync section.
- `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py` at `:197`, `:254`, `:299`, `:361`; `plugins/hexaemeron/tests/test_elenchus_checker.py` at `:436` and `:460`.
- `plugins/horos/skills/horos/scripts/horos.py` at `:859`, `:901`, `:905`; `plugins/horos/tests/test_universe.py` at `:240` and `:253`.
- `audit/AUDIT.md`: every Fiat round, plus the Horos rounds S3-R1-01 and S4-R1-01; `plugins/hexaemeron/audit/AUDIT.md` Step 0 round 1 for the atomicity lead.
- `docs/hermes-rule-corpus-study.md:164`; `tests/test_marketplace_prose.py:251`.
- [PR #445](https://github.com/wildcat-finance/skills/pull/445), [PR #457](https://github.com/wildcat-finance/skills/pull/457), [PR #460](https://github.com/wildcat-finance/skills/pull/460), [PR #463](https://github.com/wildcat-finance/skills/pull/463).
- [git-worktree documentation](https://git-scm.com/docs/git-worktree).

## 8. Signals, and the questions behind them

`hexctl` runs unattended in a loop, so [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) applies. Four questions someone will ask at three in the morning:

1. **Where is this run actually working?** `init` prints the worktree path, `status` reports it, and the state records it, so nobody has to infer it from a prompt.
2. **Why did the run refuse to start?** Each failure class emits one stable, value-free line naming the path and the fault: not a repository, path occupied, branch already checked out, add failed.
3. **Did the run touch my checkout?** The origin checkout keeps its branch and its `HEAD`, and the breadcrumb is the only file the run writes there. A test asserts both.
4. **What happened to the tree at the end?** The integrate receipt records whether the worktree was removed cleanly or kept because it held modifications, and names it either way.

No dashboard and no new telemetry ships here. The refusal lines, the recorded path, and the integrate outcome are the signals.

## 9. Boundaries, per capability

[phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and the controls.

- **Path computation and validation.** The one new untrusted surface. The run branch is already name-checked, and the derived path is resolved, required to be a descendant of the repository worktree root, and refused if any component is a symlink leaving it, following the Horos S4-R1-01 finding that `git -C` resolves symlinks before answering.
- **Worktree creation and removal.** Two new git invocations, both fixed argv through the existing bounded no-shell reader with its timeout and output cap. No caller value is interpolated into a shell, and no output path is exported into a child environment.
- **State placement.** State moves to the run's tree, staying on the same filesystem as the repository so the existing atomic-replace behaviour is unchanged. The self-ignoring nested `.gitignore` the controller already writes keeps git blind to it.
- **The origin checkout.** Write access is narrowed to one breadcrumb line. Nothing in this change checks out, branches, resets, or stages anything there.
- **Cleanup.** Removal never forces. A tree with modifications is reported and left, so the worst outcome is a directory somebody has to look at rather than uncommitted work that vanished.

## 10. The budget, or its absence

None, and here is why. The change adds one `git worktree add` at `init` and at most one `git worktree remove` at `integrate`, both bounded by the existing reader's timeout, and neither sits in a loop or scales with repository size. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) governs performance claims and this change makes none. Nothing here is done in the name of speed, so there is no before and after to record.

## 11. The fail-closed posture

[elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule. `init` stops before writing any state, ledger entry, or breadcrumb when: the target is not a Git repository; the computed path exists and is not this run's registered worktree; the resolved path is not a descendant of the repository worktree root, or a component symlink leaves it; the run branch is already checked out in another worktree; or `git worktree add` fails for any reason. A resume stops when the recorded worktree is absent, naming the recorded path rather than silently creating a second tree. Integrate stops short of removal when the tree holds modifications, and says so.

Every one of those classes gets a named negative test, observed failing before its guard lands. Refusals stay value-free and leave state and ledger bytes identical, which is the standard the state-shape rounds already set. Recovery names the exact path or branch to clear and reruns the same command.

## 12. Decisions and their homes

[hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where each lives.

- The worktree home and the fail-closed refusal, including the breaking change for in-place runs, is a cross-cutting choice: `docs/decisions/ADR-fiat-run-worktree.md`.
- The Fiat generation row recording this change belongs in `plugins/hexaemeron/skills/fiat/skills`-adjacent ledger at `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, one row, generation axis, retaining `state-shape-validation` and its digest, with the held #363 job unchanged.

The state schema addition and the breadcrumb format are documented in `SKILL.md` beside the controller invocation, which is where a reader already looks for `--dir`. No second home.

### Amendment -- 2026-08-22

**What changed.** Two corrections to the runbook's suite commands. The Hexaemeron suite is `python3 plugins/hexaemeron/tests/run_tests.py`, as `AGENTS.md:132` lists it, not the `unittest discover -s plugins/hexaemeron/tests` form the runbook first stated, which fails with `Start directory is not importable` because that directory carries no `__init__.py`. Separately, every step's exit condition now reads the Hexaemeron suite as green except two pinned-toolchain assertions, and requires Foundry's own bin directory on `PATH` so a round reproduces the same result.

**Why.** The first form does not run at all, so it could not have proved any step's exit. The two exceptions are `test_elenchus_checker.ForgeReports.test_fixture_exercised_the_declared_forge_version`, which asserts `1.7.1` against this container's `forge 1.5.1-stable`, and `test_elenchus_checker.NodeReports.test_fixture_exercised_the_declared_node_version`, which asserts `v26.6.0` against this container's `v22.22.2`. Both compare a live tool's version against a string literal in `plugins/hexaemeron/tests/test_elenchus_checker.py`, a file this run does not modify, and both fail for the same reason on the run's base commit. Recording them once here keeps every later audit round from rediscovering them and stops the run from reporting a green suite it did not get. Without `forge` on `PATH` the Forge case fails earlier still, as a `setUpClass` error rather than a version assertion. The directory itself is deliberately not named here, because a path under one machine's home directory is not a fact about this repository.

**Steps touched.** The suite command in the runbook preamble, and the suite clause in the exit condition of steps 1 through 5.

**Still holding.** Steps 2, 3, 4 and 5 re-confirmed: each unbuilt step's entry and exit hold as written, with the suite clause read as amended above. Step 1's entry and exit hold on the same reading. No goal, file list, test expectation or discipline changes.

**A note on where this block lives.** The receipted artefacts at `.hexaemeron/study.md` and `.hexaemeron/runbook.md` stay byte-identical, because `hexctl` refuses every later directive when a receipted artefact's digest moves (`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:1746`). The amendment therefore lands on the shipped copies, which are the live spec, while the frozen run artefacts remain the record of what was believed at receipt time. That split is the friction [skills#446](https://github.com/wildcat-finance/skills/issues/446) already reports, met here rather than worked around silently.
