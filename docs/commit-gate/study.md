# Study: a commit gate that survives a fresh clone

Issue [#857](https://github.com/wildcat-finance/skills/issues/857).
Base: `main` at `8dc3aca54adeca49387a2bdfc174cf6e72d02a11`.
Design record: `.hexaemeron/design-evidence.json`,
sha256 `6e7a5ca5397d6b84951d79d6f5b1ea3a6cedd724824ba0f28434f82a72b36a44`,
selected candidate `hooks-path-plus-visibility`.

Assuming, unless corrected:

1. The interpreter is the one pinned in `.python-version`, 3.14.6, with
   `requires-python = "==3.14.*"` in `pyproject.toml:4`. Measurements below ran
   on that interpreter and on git 2.50.1 (Apple Git-155).
2. This upgrades no plugin skill. The gate is repository infrastructure, and it
   lands under `.githooks/`, `tests/`, `docs/decisions/` and `AGENTS.md`. No
   skill under `plugins/` owns a commit gate, so no `EVOLUTION.md` ledger row is
   owed. Section 12 records the reasoning.
3. The issue's boundary holds without reinterpretation: no ruleset change, no
   change to any existing test's assertions, no gate on pushes or merges.
4. Contributors run the repository from many worktrees at once. This clone had
   39 registered worktrees when the study was written, so a design that has to
   be activated once per checkout is a different proposition from one activated
   once per clone.
5. The gate keeps the tree-hash construction rather than running the suite from
   inside the hook. The suite costs 289.3 seconds; running it on every commit
   attempt is not a cost anyone will pay, and the original design avoided it for
   a second reason recorded in section 5.

Correct any of these and the affected section changes before the runbook is
derived.

## 1. Problem statement

The repository has no commit gate. The issue reported that one existed as two
untracked scripts in a single clone's `.git/hooks`; both are now gone. On
2026-09-04 the shared git directory of the primary checkout,
`/Users/c0rtexzer0/Projects/wildcat-skills/.git/hooks`, held fourteen files and
every one of them was a `.sample` shipped by `git init`. There is no
`pre-commit`, no `git-greenlight`, and no `LAST_GREEN` beside them. The tracked
tree carries nothing either: `git grep` for `hooksPath`, `LAST_GREEN`,
`greenlight` and `FIAT_SKIP_PRECOMMIT` returns no line, and `git ls-files |
grep -i hook` returns six paths, five of them Solidity under `plugins/janus`
and one the Claude Code session hook at
`plugins/hexaemeron/skills/imprimatur/scripts/hook_gate.py`, which is not a git
hook. The prediction in the issue has already come true: the discipline
evaporated with the clone that held it.

What is being built is a commit gate that a fresh clone can turn on with one
command, whose absence a contributor is told about rather than left to
discover, and which refuses a commit whose staged tree is not the tree the
suite passed on.

Who it is for: anyone who commits to this repository, including the automated
Fiat runs that operate it from disposable worktrees.

A working prototype means all five of the following hold on a clone that has
never seen the gate before.

| Acceptance condition | Criterion | Command that proves it |
| --- | --- | --- |
| 1, where the gate lives | `docs/decisions/ADR-074-*.md` exists, names the chosen home and states what each rejected option lost | `python3 -m unittest tests.test_decision_records -v` |
| 2, survives a clone and absence is visible | A fresh clone with no activation fails the root suite with a message naming the one activation command | `git clone <url> fresh && cd fresh && python3 -m unittest tests.test_commit_gate -v` exits 1 and its output contains `git config core.hooksPath .githooks` |
| 3, green tree against untested tree | With a green recorded for tree T, a commit staging tree T succeeds and a commit staging any other tree exits non-zero | `python3 -m unittest tests.test_commit_gate.GreenTreeTests -v` |
| 4, deliberate escape hatch | `FIAT_SKIP_PRECOMMIT=1` lets an untested tree through, and the literal token appears in the tracked gate | `FIAT_SKIP_PRECOMMIT=1 git commit` exits 0 in the fixture, and `git grep -c FIAT_SKIP_PRECOMMIT -- .githooks` is at least 1 |
| 5, index-mutation regression on the hook path | Running the gate with `GIT_INDEX_FILE` and `GIT_PREFIX` pointing at an outer repository leaves that repository's staged state byte-identical | `python3 -m unittest tests.test_commit_gate.HookIndexMutationTests -v` |

The demo path is the last step: clone the repository into a fresh directory,
run the root suite and read the refusal, run the one activation command, record
a green, commit, then edit a file and watch the next commit be refused.

## 2. Prior art

**In this repository.** Nothing implements a commit gate. What exists is the
adjacent machinery a gate would reuse.

- `scripts/run_checks.py` is the checked runner introduced by ADR-045. It
  writes a `wildcat.check-run.v1` report carrying `source_identity` and an
  `outcome` of `green` or `red`, and exits 0 on green and 1 on red
  (`scripts/run_checks.py:3091`, `:3128`). `source_identity` is a SHA-256 over
  `HEAD`, the zero-stage index entries, and the raw bytes of every tracked and
  relevant untracked path (`scripts/run_checks.py:1363-1418`). It is not the
  staged tree object. It changes when an unrelated untracked file appears, so a
  gate keyed on it would refuse commits for reasons that have nothing to do
  with the commit. `git write-tree` is the narrower key and is what section 4
  uses.
- `tests/test_boundary_currency.py:57-73` names the incident the issue
  describes and measures it at 1487 phantom deletions. The guard is the
  `GitEnvironmentIsolation` class at `:104-159`, whose end-to-end case
  `test_the_helper_leaves_the_outer_staged_state_alone` at `:126` pollutes
  `GIT_INDEX_FILE` and asserts the outer staged state is unchanged. The guard
  lives in the file that caused the defect, which is exactly the placement
  acceptance condition 5 refuses to accept on its own.
- `plugins/hexaemeron/tests/test_check_runner.py:868-872` holds
  `run_checks._git_env()` to dropping `GIT_DIR` and `GIT_INDEX_FILE` for child
  processes. That covers the runner's own subprocesses, not a hook.
- `tests/test_scratch_quiescence.py` refuses a `dir=` argument on a `tempfile`
  construction inside a test module unless it uses the vetted helpers. Its
  docstring cites audit finding S3-R1-01 on issue #622 for the same class of
  defect: scratch inside the tracked tree makes the repository transiently
  non-quiescent. A gate that compares tree objects inherits this concern.
- `.gitignore` already reserves `/tmp/` at the repository root and
  `**/tmp/check-runner/`, so a gate that needs scratch has a home.

**Hosted CI.** Twelve workflow files sit under `.github/workflows`.
`repo.yml` runs `python3 -m unittest discover -s tests -v` in a job named
`invariants`, unconditionally on every pull request, and its header states why
it carries no path filter. `plugins.yml` shards `scripts/run_checks.py` across
26 declared scopes behind an aggregate job named `plugins`. The GitHub Actions
API reports `plugins.yml` in state `disabled_manually`; every other workflow is
`active`.

Repository ruleset `21830871`, named "Required CI", targets the default branch.
Its enforcement is `evaluate`, not `active`. It requires two contexts,
`identity` and `invariants`, and lists no bypass actors. So the only hosted
check that currently speaks for the whole root suite is `invariants`, and even
that is advisory while the ruleset stays in evaluate mode. This matters for
section 4: adding a new required context would be a ruleset change, which the
issue's boundary forbids, but adding a test under `tests/` reaches the
`invariants` context with no workflow or ruleset edit at all.

**The last two merged pull requests on this subject.** Both changed the hosted
gate rather than a local one, because a local one has never shipped.

- [#1073](https://github.com/wildcat-finance/skills/pull/1073), merged
  2026-09-01, gave the plugin gate an explicit `--jobs 14` budget after the
  Hexaemeron suite was killed on the 1800-second per-check timeout at one
  worker. Its body carries four items forward. That `plugins` is still
  `disabled_manually` and re-enabling it belongs to #992: carried as a stated
  non-goal in section 3, and confirmed still true by the API read above. That
  ruleset `21830871` no longer lists `plugins` among its required contexts:
  carried into section 4 as the fact that eliminates the CI-only candidate.
  That `scope (promise-machine)` re-runs `hexaemeron-suite`: non-goal, this
  study changes no scope. That #992's route 1, a larger runner, is unsettled:
  non-goal.
- [#984](https://github.com/wildcat-finance/skills/pull/984), merged
  2026-08-30, sharded the plugin gate across the declared scopes. It carries
  forward that the root suite runs twice, once as `invariants` and once inside
  the `root` shard, which ADR-056 accepted deliberately, and that scope
  closures overlap. Both are non-goals here; neither is reopened.

Earlier and still relevant: [#938](https://github.com/wildcat-finance/skills/pull/938)
landed ADR-056 and planned to require both `invariants` and `plugins`, which
the live ruleset shows did not survive; [#913](https://github.com/wildcat-finance/skills/pull/913)
required the invariant gate on main; and [#537](https://github.com/wildcat-finance/skills/pull/537),
named by the issue, fixed the `GIT_INDEX_FILE` inheritance and added the
end-to-end guard cited above.

**Audit records.** `python3
plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` ran from
the target root and exited 0, so every synopsis in the set is current against
its source and the synopsis is the admitted reading view. The in-scope sources
and what was read:

| Source | Read | Evidence for the choice |
| --- | --- | --- |
| `audit/AUDIT.md` | `audit/AUDIT_SYNOPSIS.md` | whole-set check exit 0; `source_sha256=d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d`, 425 sections |
| `audit/rounds/fiat-622-carryover-inoculate-affected-scope-runner.md` | its `.synopsis.md` | whole-set check exit 0; `committed=match` |
| `audit/rounds/fiat-621-isolate-disposable-fixture-signing.md` | its `.synopsis.md` | whole-set check exit 0; `committed=match` |
| `audit/rounds/fiat-622-fix-disposable-fixture-signing-and-add-affec.md` | its `.synopsis.md` | whole-set check exit 0; `committed=match` |
| `audit/rounds/fiat-881-macos-path-repair-clean-run.md` | its `.synopsis.md` | whole-set check exit 0; `committed=match` |
| `plugins/hexaemeron/audit/AUDIT.md` | `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` | whole-set check exit 0; `committed=match` |

The source was not read directly for any of these; the synopsis was. Two
findings carry into section 5. The check-runner round records
`artifact-substitution`, `report-forgery` and `source-movement` as reviewed
concerns, and finding S1-R1-01 there is the class where a checked-in record
supplies its own expected digest, so a paired edit to a target and its record
passes verification. A gate whose green record is a file the committer can
write has exactly that shape. The disposable-signing round's finding S2-R1-02
records that `GIT_CONFIG_PARAMETERS` carries the same precedence as
`GIT_CONFIG_COUNT` and is the variable git itself propagates into every process
it spawns; a hook is such a process. Every legacy field in the root synopsis
reads `[missing legacy field: ...]` and stays unknown; no finding id or status
was dropped.

**Outside.** Git cannot install a hook on clone. `git clone` copies no hook
and sets no configuration, which is the security property that makes the
problem this issue names unavoidable rather than a defect. `core.hooksPath` has
been available since git 2.9. Third-party installers such as `pre-commit` and
`husky` solve the same problem by adding a dependency and a bootstrap step;
this repository pins no such dependency and section 3 rules one out.

## 3. Constraints and non-goals

**Starting point.** `main` at `8dc3aca54adeca49387a2bdfc174cf6e72d02a11`, on
branch `fiat/857-framework-16-the-commit-gate-lives-in-one-cl`.

**Toolchain.** Python 3.14.6 as pinned in `.python-version`, with
`requires-python = "==3.14.*"`. Git 2.50.1 on the measuring machine; the hook
uses only `write-tree`, `rev-parse` and `config`, all of which predate 2.9. No
new runtime dependency: the gate is POSIX shell and the visibility assertion is
stdlib `unittest`, matching every other test under `tests/`.

**Cost of the suite.** `python3 -m unittest discover -s tests` ran 1132 tests
in 289.3 seconds with exit 0 on this machine, and 206.3 seconds wall on a
quieter run of the same command. `python3 scripts/run_checks.py --full --plan`
selects 26 scopes and 28 checks at an automatic budget of 12 slots; the hosted
shard for the heaviest scope takes about 11.5 minutes at `--jobs 14` per
#1073. Neither is a per-commit cost anyone will accept, which is why the gate
compares a recorded tree rather than running anything.

**Ruled out by the issue.** Any change to ruleset `21830871`. Any change to
what an existing test asserts. Any gate on pushes or merges. Whether the gate
should also run lints or promise-machine checks.

**Ruled out here, with reasons.**

- A third-party hook manager. It adds a pinned dependency and a bootstrap step
  to a repository that installs nothing today, and it does not remove the one
  activation command.
- `init.templateDir`. It is per-machine global configuration outside the
  repository, so it does not travel with a clone either, and it silently
  affects every other repository on the machine.
- Re-enabling `plugins.yml` or changing its budget. That is #992's work and
  #1073 said so.
- Keying the gate on `run_checks.py`'s `source_identity`. Section 2 gives the
  reason: it moves when an unrelated untracked file appears.

**Deferred past the prototype.** Extending the gate to lints or promise-machine
checks. Any hosted check that reads a per-commit green record. Requiring a new
context in the ruleset once the gate is proven.

**Build order the design assumes.** Step 1 scaffolds the tracked hooks
directory and commits the study, runbook and decision record. Step 2 adds the
gate scripts and their own tests. Step 3 adds the visibility assertion under
`tests/`. Step 4 adds the hook-path index-mutation regression, which is the
stop point the design record's one pending criterion blocks. Step 5
demonstrates on a fresh clone.

### Always, ask first, never

**Always.** Run `python3 -m unittest discover -s tests` before any step closes,
and record its exit code; three lints are not that suite. Run
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` over every
document this run ships, then the Brevitas pass. Re-run
`plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` after any
change under `audit/`. Regenerate `.horos/boundary.json` with `python3
plugins/horos/skills/horos/scripts/horos.py scan . --write` in the same step
that adds a classified file, because the root suite fails until it matches.

**Ask first.** Editing `AGENTS.md`, whose sentences the router corpus quotes.
Adding any entry to `tests/check-map-v1.json`, because a changed path with no
declared owner makes `run_checks.py` refuse its own plan. Adding a dependency,
which this study has already ruled out but a later step could reach for.
Changing what the activation command is once ADR-074 records it. Touching any
file under `.github/workflows`.

**Never.** Change ruleset `21830871` or add a bypass actor to it. Change what
an existing test asserts. Gate a push or a merge. Commit the green record, or
any file under a git directory, into the tracked tree. Delete or weaken
`tests/test_boundary_currency.py`'s `GitEnvironmentIsolation` class to make the
new regression look sufficient. Claim a command ran when it did not.

## 4. Design options

Four constructions carry a full column in `.hexaemeron/design-evidence.json`.
A fifth, the recorded decision not to ship a gate, is evaluated in prose below
because the record admits at most four candidates and because it is not a
construction whose properties a fixture can measure.

Git cannot install a hook on clone. That was proved rather than assumed: a
fixture repository with a tracked `.githooks/pre-commit` was cloned, the clone
reported an empty `core.hooksPath`, carried the hook file on disk unused, and
committed with exit 0. So "survives `git clone`" cannot be met by making
installation automatic. It is met, or not met, by making the absence visible.
Each candidate below says exactly how.

**A, `installed-hooks`.** Commit the gate scripts and install them into the
shared hooks directory with one documented command. Activation was measured at
one command. It works across worktrees: `git rev-parse --git-path hooks` in a
linked worktree resolves to the common directory, and a hook placed there ran
from both the main and the linked worktree in the fixture. It leaves 497 bytes
of state per clone, because the scripts are duplicated out of the tracked tree
into the git directory, where they can drift from their tracked source with
nothing comparing them. **Absence is visible: not at all.** Nothing in the
repository can tell that the copy was never made. The trade A loses is the
whole of acceptance condition 2, and with it the single reason the issue was
filed.

**B, `hooks-path`.** Keep one tracked `.githooks` directory and activate it
with `git config core.hooksPath .githooks`. Activation was measured at one
command, and one command covers every worktree: `core.hooksPath` set in the
shared configuration was read back in a linked worktree, and because the value
is relative it resolved against each worktree's own top level, so the hook that
ran in the linked worktree was that worktree's own tracked copy. State per
clone is 40 bytes, the green record alone, and the scripts have one source of
truth. **Absence is visible: not at all**, by the same clone proof. The trade B
loses is the same as A's; it is a better mechanism failing the same condition.

**C, `ci-only`.** Ship no local gate and enforce the green-tree evidence from a
hosted check instead. It costs nothing per commit and nothing per clone.
**Absence is visible: trivially**, because a hosted check runs on every pull
request whether or not anything is installed locally. It fails four gates. It
cannot enforce anything without being a required context, and the live ruleset
requires only `identity` and `invariants`, so enforcement means a ruleset
change the boundary forbids. Its only enforcement point is the merge, which the
boundary reserves to the existing rulesets. It has no per-commit bypass variable a
contributor can set; the equivalent would be a ruleset bypass actor, and the
ruleset has none. And it does not do what acceptance condition 3 describes: it
re-runs the suite on the pushed tree rather than comparing the tree being
committed against a recorded green identity, so there is never a recorded hash
to be stale. The trade C loses is the discipline itself. It moves the feedback
from before the commit exists to after the push, and on a ruleset in `evaluate`
mode that feedback blocks nothing.

**D, `hooks-path-plus-visibility`.** B, plus an assertion in the root suite
that names the missing activation and the one command that fixes it. Every
measured property of B carries over: one activation command, 40 bytes of state,
both worktrees covered, the recorded-tree comparison, and the
`FIAT_SKIP_PRECOMMIT` bypass. **Absence is visible: in the root suite of the
checkout that lacks it.** The fixture confirmed the mechanism: after cloning,
reading the clone's own `core.hooksPath` reports it unset, which is the value
the assertion refuses. Because the assertion lives under `tests/`, it is inside
the `invariants` context that `repo.yml` already runs on every pull request, so
it reaches hosted CI with no workflow edit and no ruleset edit.

**E, the recorded decision not to ship.** Held in prose. Against the same
criteria it passes `no-ruleset-change`, `no-push-merge-gate` and
`test-assertions-unchanged` vacuously, costs zero on all three metrics, and
fails `worktree-activation`, `recorded-green-comparison`, `absence-visible` and
`explicit-bypass` for the same reason: there is nothing there. The trade E
loses is the one the issue's desired outcome names as acceptable only when a
gate cannot be had. D can be had, at a measured 22 milliseconds per commit and
40 bytes per clone, so the null option costs more than it saves.

**The selection.** The design checker eliminated A and B on `absence-visible`
and C on four gates, leaving one survivor, and `unique-frontier` selected
`hooks-path-plus-visibility`. `python3 design_evidence.py
.hexaemeron/design-evidence.json --transition design-lock` exits 0.

**The trade D accepts.** Hosted CI cannot see whether a contributor activated
the gate in their own checkout, because no evidence of a local hook reaches the
server. D's CI half therefore holds only the tracked bytes: that the hooks
directory exists, is executable, and names the bypass token. The activation
half is visible locally, in the suite run that must precede any commit under
the discipline. A contributor who never runs the suite gets no green record,
so their first commit is refused by the hook if it is on and passes silently if
it is off. D does not close that hole; it makes the hole announce itself the
first time the suite runs.

## 5. Risk register seed

The green record is a file a committer can write, which is the shape of audit
finding S1-R1-01 on the check runner: a record that supplies its own expected
value verifies against itself. Treat the record as a convenience, not as proof
that the suite ran, and say so where it is documented. The bypass is deliberate
and greppable for the same reason: the gate's honesty rests on nobody needing
to lie to it.

The hook runs while git has exported `GIT_INDEX_FILE`. That was measured, not
assumed: a `pre-commit` hook in the fixture saw `GIT_INDEX_FILE=.git/index` and
`GIT_PREFIX=` set, with `GIT_DIR` unset, and `git write-tree` inside the hook
returned the staged tree. Every process the hook starts inherits that variable,
and the disposable-signing round records that `GIT_CONFIG_PARAMETERS` travels
the same way.

```risk-register
green-record-self-evidence | the green record file in the git directory | the record is documented as a convenience rather than proof, and nothing claims the suite ran because the file exists
stale-green-different-tree | the comparison between the recorded identity and git write-tree | a record naming any tree other than the staged one refuses the commit
hook-index-inheritance | the environment the hook and its children run in | a test drives the gate with GIT_INDEX_FILE and GIT_PREFIX pointing at an outer repository and asserts that repository's staged state is byte-identical afterwards
hook-config-inheritance | GIT_CONFIG_PARAMETERS and GIT_CONFIG_COUNT reaching the hook | the gate reads no configuration that an inherited override could redirect, and the regression sets both variables
worktree-record-crossing | the green record path in a linked worktree | the record resolves through git rev-parse --git-dir, so one worktree's green cannot authorise another worktree's commit
bypass-token-drift | the FIAT_SKIP_PRECOMMIT token in the tracked gate | a test asserts the literal token is present, so the documented escape hatch cannot be renamed silently
scratch-quiescence | any temporary tree the gate's tests build | the tests use the vetted scratch helpers, so tests/test_scratch_quiescence.py stays green and the outer tree stays quiescent
hooks-path-absolute | the value written by the activation command | the value stays relative, because an absolute path would point every worktree at one worktree's copy
executable-bit-loss | the mode of the tracked gate scripts | a test asserts the tracked mode is executable, because a non-executable hook is skipped by git without a message
ci-cannot-see-activation | the boundary between a contributor checkout and a hosted runner | the hosted half asserts only the tracked bytes, and the study states plainly that activation is unobservable server-side
```

## 6. Glossary seeds

- **Green record.** The file holding the tree object identity of the last tree
  the suite passed on, written by the greenlight command and read by the hook.
- **Greenlight.** The tracked command that runs the root suite and, on exit 0,
  writes the staged tree identity into the green record.
- **Staged tree.** The tree object `git write-tree` produces from the current
  index. It is what a commit will contain, and it is the thing the gate
  compares.
- **Activation.** The single `git config core.hooksPath .githooks` a fresh
  clone runs. Set in the shared configuration, it reaches every worktree.
- **Bypass.** `FIAT_SKIP_PRECOMMIT=1`, the named environment variable that lets
  a deliberate commit through without touching `--no-verify`.
- **Visibility assertion.** The root-suite test that fails in a checkout where
  the gate is not activated and names the activation command in its message.

## 7. Sources

- Issue [#857](https://github.com/wildcat-finance/skills/issues/857), current
  review dated 26 August 2026, checked against `wildcat-finance/skills@ab611eb96a6a`.
- Pull requests [#1073](https://github.com/wildcat-finance/skills/pull/1073),
  [#984](https://github.com/wildcat-finance/skills/pull/984),
  [#938](https://github.com/wildcat-finance/skills/pull/938),
  [#913](https://github.com/wildcat-finance/skills/pull/913) and
  [#537](https://github.com/wildcat-finance/skills/pull/537).
- `docs/decisions/ADR-045-select-and-schedule-repository-checks-from-one-graph.md`,
  `ADR-056-require-the-complete-plugin-graph.md`,
  `ADR-063-separate-live-worktree-reports-from-baselines.md`.
- `.github/workflows/repo.yml` and `.github/workflows/plugins.yml`;
  `GET /repos/wildcat-finance/skills/rulesets/21830871` and
  `GET /repos/wildcat-finance/skills/actions/workflows`, both read 2026-09-04.
- `scripts/run_checks.py:1363-1418`, `:3091`, `:3128`;
  `tests/check-map-v1.json` check `root-suite`.
- `tests/test_boundary_currency.py:57-73` and `:104-159`;
  `plugins/hexaemeron/tests/test_check_runner.py:868-872`;
  `tests/test_scratch_quiescence.py`.
- `AGENTS.md:242-311`, the checks and lints section, which today documents the
  runner and the suites and says nothing about committing.
- Audit synopses named in section 2, admitted by
  `plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exit 0.
- Git behaviour measured in throwaway fixtures on git 2.50.1 by
  `.hexaemeron/design/evaluate_commit_gate.py`; the reports are under
  `.hexaemeron/reports/`.

## 8. Signals, and the questions behind them

The gate runs on a contributor's machine, interactively, so it has no
unattended operator. Three questions still get asked, and each is answered by
something the gate prints or a command returns rather than by a metric.

1. "Why was my commit refused?" Answered at the moment of refusal. The hook
   writes one line to standard error naming which of the two causes applies:
   no green record at all, or a record naming a different tree. Step 2 owns it.
2. "Is the gate on in this checkout?" Answered by the visibility assertion,
   whose failure message names the exact activation command. Step 3 owns it.
3. "Did the suite actually pass, or did somebody write the record by hand?"
   Not answerable, and the study says so rather than implying otherwise. The
   record carries no provenance and is not evidence; section 5 records this as
   `green-record-self-evidence` and the documentation states it plainly.

No counter, log stream or alert is added. [ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns
what a signal must carry; nothing here runs unattended, so nothing here emits
one.

## 9. Boundaries, per capability

Three boundaries open, each with the control that closes it.
[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and the controls.

- **The hook's inherited environment.** Git exports `GIT_INDEX_FILE`,
  `GIT_PREFIX` and, per the disposable-signing round, `GIT_CONFIG_PARAMETERS`
  into the hook. Worth taking at this boundary: another repository's index. The
  control is that the gate starts no process other than fixed-argv `git`
  invocations against its own repository, reads no configuration an inherited
  override could redirect, and is driven by the step 4 regression under a
  polluted environment.
- **The green record file.** Anyone who can write the git directory can write
  it. Worth taking: a commit that never ran the suite. The control is not
  cryptographic and the study does not pretend otherwise; the record is scoped
  to one worktree through `git rev-parse --git-dir`, compared against the exact
  staged tree, and documented as a convenience.
- **The tracked gate scripts.** They execute on every commit in every activated
  checkout, so a change to them is a change to code that runs on contributors'
  machines. The control is that they are tracked, reviewed like any other file,
  and covered by the root suite; and that the activation is relative, so no
  checkout can be pointed at another checkout's copy.

## 10. The budget, or its absence

One budget, because a gate that slows every commit will be turned off.

- **Budget.** The gate adds at most 200 milliseconds to a commit whose tree is
  already recorded green.
- **Measured now.** 22 milliseconds, the median of nine paired commits against
  an ungated control, on git 2.50.1 on this machine.
- **Command.** `python3 .hexaemeron/design/evaluate_commit_gate.py --candidate
  hooks-path-plus-visibility --criterion commit-overhead`, whose report is
  `.hexaemeron/reports/hooks-path-plus-visibility-commit-overhead.json`.

The root suite's own cost is not this study's budget: the gate never runs it.
The 289.3-second figure is recorded in section 3 as the reason for that
decision, not as a target. [metron](../../plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget
carries and how it is checked.

## 11. The fail-closed posture

The gate refuses by default. A missing green record, a record naming another
tree, an unreadable record and a failure of `git write-tree` all exit non-zero
and stop the commit. The only path through is the named bypass, which is why
the bypass is one literal token a reader can grep for rather than a
convention people pass around.

The visibility assertion fails closed in the other direction: a checkout with
no activation fails the suite rather than passing quietly, and the failure
names the fix.

Guard convention, per [elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md), which owns the triage
order and the guard rule: every fix in this run lands with a test that fails
without it. The two the runbook already knows it owes are the stale-record
refusal in step 2 and the hook-path index-mutation regression in step 4. The
second is deliberately not placed in `tests/test_boundary_currency.py`, because
acceptance condition 5 refuses a guard that lives only in the file that once
caused the defect; it goes in `tests/test_commit_gate.py`, alongside the path
it guards.

## 12. Decisions and their homes

Two decisions are expensive to reverse, and both go to
`docs/decisions/`, which [hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md)'s placement rules
give to a choice that cuts across the repository. `docs/decisions/` holds 72
records ending at ADR-073, so the next number is ADR-074.

- **Where the gate lives and how it is activated.** `docs/decisions/ADR-074-*.md`,
  recording `core.hooksPath` over a copied install and over a hosted check, with
  what each rejected option lost. The alternatives section is the part that
  pays here, because the issue's first acceptance condition asks for exactly
  that. `tests/test_decision_records.py` already checks the record shape.
- **That the green record is a convenience rather than proof.** The same ADR,
  in its consequences. Recording it once stops the next reader from building a
  claim on it.

No governed skill's `EVOLUTION.md` gains a row. Assumption 2 states the reading:
the gate is repository infrastructure with no owning plugin. If a reviewer
places it under a skill instead, ADR-074 moves to that skill's ledger and this
section is amended before the runbook is derived.

`AGENTS.md` gains the activation command and the bypass token in its checks
section. That file's sentences are quoted by the router corpus and pinned by
digest elsewhere in the repository, so the runbook step that edits it runs the
root suite before it closes, and adds rather than rewrites.
