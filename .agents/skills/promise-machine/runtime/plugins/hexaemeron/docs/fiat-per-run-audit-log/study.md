# Give each Fiat run its own audit log path

Issue: [skills#576](https://github.com/wildcat-finance/skills/issues/576).
Base: `main` at `103fa90c444f35eb09e87b9d2ec29c43a6d34c1f`.
Controller driving this run: `fiat-v5.20.1`.

## Assumptions

Proceeding on these unless corrected:

1. Python 3.14.6 and stdlib `unittest`, matching every other suite here. No new
   dependency.
2. The run branch is the run's identity. `flattened_run_branch` already maps it
   to one directory name for the worktree, so it can supply one file name for
   the log.
3. A run whose state was written by an earlier controller keeps the
   `audit.log_path` its state holds. Nothing rewrites existing state, and the
   root log stays the configured path for every run already in flight.
4. `audit/AUDIT.md` stays tracked with its existing bytes untouched, so
   `tests/test_run_observation.py` keeps reading the history it was written
   for.
5. The existing 13,090-line log is not split by run. 67 of its 413 sections are
   headed `## Step <n>, round <r>` with no run named, so a split is not
   mechanical.
6. [skills#574](https://github.com/wildcat-finance/skills/issues/574) has
   landed, so `python3 -m unittest discover -s tests` is usable as a step gate
   from inside a run worktree. Measured on this run's entry state: 349 tests,
   `OK`, no skips.

## 1. Problem statement

`done sync-run` refuses an integration receipt unless every path in the
computed integration surface carries a green check. That surface includes the
overlap between what the run changed and what the base changed since their
merge base:

```python
overlap_paths = sorted(set(product_paths) & set(upstream_paths))
required_paths = sorted(set(composition_paths) | set(overlap_paths))
```

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:2733`, with the coverage
refusal at `:2804`.

Every run appends its rounds to one file, from a literal default at
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:88`:

```python
"log_path": "audit/AUDIT.md",
```

So the audit log sits on both sides of that intersection whenever anything else
merged during a run. In this repository that is the normal case: 374 of the last
thirty days' commits on `main` touch `audit/AUDIT.md`, against 79 for the next
path, `README.md`. It is the most-churned path in the tree by a factor of 4.7.

Two consequences. The merge conflicts textually, in a file whose earlier content
is append-only evidence. And the path enters `affected_paths` even when it
merges clean, so the run owes a green check over it before it may integrate.
`tests/test_run_observation.py:84` reads the root log, so that is a real
evidence dependency rather than a formality.

**What is built.** Three changes to the Fiat controller and the prose that
describes it. A run derives its own log path at `init`. An override stays
available but can no longer name another run's file. And the path a round
records is the path the round was told to write, rather than a free string.

**A working prototype.** A run initialised by the new controller writes its
rounds to a path no other run writes, with no operator action, and the
controller refuses the two ways that path could be subverted. The demo path is
step 5: initialise a scratch run in a temporary repository, read its
`config audit.log_path`, record a round against the derived path, and watch the
same command refuse a round that names a different file and a `config set` that
names another run's basename.

**This run's own evidence.** The controller driving this run is
`fiat-v5.20.1`, installed before the run started, so it cannot enforce what the
run is writing. It can still be pointed at the new path, because
`config set audit.log_path` is unconstrained today. This run sets it before its
first round, so every round it records lands in
`audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md`. A
controller change whose own evidence went to the old file would not have been
exercised.

## 2. Prior art

**In this repository.** Three plugins already keep their rounds out of the
shared file: `plugins/probitas/audit/AUDIT.md`,
`plugins/pandects/audit/AUDIT.md` and `plugins/ariadne/audit/AUDIT.md`. The
first of those records why, at `plugins/probitas/audit/AUDIT.md:71`: the log sat
at the repository root, the repository was about to hold several plugins, and a
top-level `audit/` belonged to none of them. That finding moved a log by
plugin. This one moves it by run, which is the axis the sync gate actually
intersects on.

**The last two merged pull requests touching Fiat.**
[#583](https://github.com/wildcat-finance/skills/pull/583) closed issue 574 by
rebinding five capture-receipt tests away from a path a live run owns.
[#579](https://github.com/wildcat-finance/skills/pull/579) implemented issue 436
and added the observation binding. Their carried-forward sections:

- #583 names this issue directly: "#576 owns the framework change this run's own
  sync demonstrates: every run appends to one `audit/AUDIT.md`, so that file
  lands in the sync's overlap set and owes a green check on every integration.
  This run did not touch it." Carried forward as this run's content.
- #583 records that its step 1 exit named a clean-checkout suite figure the run
  worktree could not meet, because writing a study and a runbook is what created
  the failures. Answered here: issue 574 removed that divergence, and this
  study's assumption 6 states the measured run-worktree figure rather than a
  clean-checkout one.
- #583 records a step 2 deviation, where a mutation proof ran against tracked
  copies rather than a temporary directory. Not reachable here; this run's
  proofs run in temporary repositories the controller itself creates.
- #583 removed `capture_receipts_are_current()`. Done, and out of scope.
- #583 leaves open whether other tests bind to a path a live run owns. Stated as
  a non-goal below: that is about tests that *read* a live path, where this
  issue is about a tracked file every run *writes*.
- #579 leaves [skills#508](https://github.com/wildcat-finance/skills/issues/508)
  open for exhausted-audit carryover, delegated-write and runbook-gate
  semantics. Untouched here and stated as a non-goal.

**In the audit record.** The rounds for the in-scope skill are in
`audit/AUDIT.md`, which is itself the subject. Two entries bear on the design.
`audit/AUDIT.md:5564` is the Protasis audit-record-source round, which settled
the wording other skills now use to name this file: "`config audit.log_path`,
default `audit/AUDIT.md`". That sentence is the one this change makes stale, and
it lives in a sibling skill. `audit/AUDIT.md:723` is a Pandects round that had
to add a "Leads closed since" section because a plugin's own log recorded an
open gap that another file had closed; the reader of one record met a question
that was already answered elsewhere. Splitting a record by run creates the same
hazard, which is why the root log keeps a pointer rather than being left silent.

No round in the log has previously proposed a per-run path, and none records a
lead about it that was left unpursued.

**Outside.** Nothing borrowed. The construction is a derived default and a
basename constraint, both stdlib string and path work.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref: `main` at `103fa90c444f35eb09e87b9d2ec29c43a6d34c1f`.
- Python 3.14.6, stdlib only. No new dependency, no new subprocess, no network.
- The controller driving this run is `fiat-v5.20.1` and cannot enforce this
  run's own rules. Every claim about the new behaviour rests on tests and on the
  step 5 demonstration, never on this run's own receipts.
- Existing `audit/AUDIT.md` bytes are append-only. No historical section is
  edited, reordered or removed.
- State written by an earlier controller is read, never rewritten.
- The three surfaces must not disturb `.horos/boundary.json` silently; the root
  suite fails on a stale boundary, and it is regenerated at the last step.

**Non-goals.**

- Splitting the existing log by run. Assumption 5 gives the reason: two thirds
  of the naming needed is not there to split on.
- A generated index over `audit/rounds/`. The root log gets a pointer saying
  where new records go. A generated listing is a separate capability, it would
  itself become a churned tracked file, and reintroducing a path every run
  writes is the defect this issue removes.
- Exempting prose paths from `sync-run` revalidation. The gate is right to ask;
  the issue says so and this study agrees.
- Rewriting `audit.log_path` in state that already exists.
- Whether other tests bind to a live run path, carried forward by #583. That is
  a read-side question about a different set of files.
- Issue 508's controller surface, carried forward by #579.

## 4. Design options

**Option A. Derive the default at `init`; constrain the override to the run's
own file name.** `DEFAULT_CONFIG` stops holding a literal log path.
`cmd_init` writes `audit/rounds/<flattened run branch>.md` into the run's
config after the deep copy. `config set audit.log_path` still works, but the
value must be a relative path, free of `..` and control characters, resolving
inside the target, whose basename equals the run's derived name.
Trade: an operator who deliberately wants two runs sharing one file can no
longer have it. That is the whole point, and a run with no recorded run branch
keeps the old free-string behaviour because there is nothing to derive from.

**Option B. Keep the shared log and exempt prose paths from revalidation.**
Cheapest diff. Rejected: it opens a hole exactly where the audit record lives,
and `tests/test_run_observation.py:84` proves the dependency is real rather
than notional.

**Option C. Derive the path at the first audit round instead of at `init`.**
Rejected: `next`, the warden packet and `config get` would each have nothing to
name before the first round, and a branch renamed between rounds would derive
two different files inside one run.

**Option D. One file per step, `audit/rounds/<run>/step-<n>.md`.** Rejected: it
removes nothing from the overlap set that A does not already remove, multiplies
files, and a run's rounds read better in one file than in five.

**Chosen: A.** It is the option that leaves the overlap set empty for this path
with the fewest moving parts, and both of its refusals are one comparison each.

## 5. Risk register seed

The two boundaries this opens are both string-to-path: a branch name reaching a
filesystem path at `init`, and an operator value reaching one at `config set`.
Neither adds a subprocess, a fetch, a credential or a dependency. The third
concern is not a boundary but a claim: the round's recorded log has never been
checked against anything, and the fix must not make it assert more than it
knows. The controller does not read the log file and does not attest its bytes,
before or after this change.

```risk-register
derived-path-injection | the run branch text reaching a filesystem path at init | the derived name comes from flattened_run_branch, which calls check_branch_name first, so no separator, no .. and no control byte reaches the path
override-escape | the operator value at config set audit.log_path | relative only, no .. component, no control character, resolves inside the target directory, and its basename equals the run's derived name
legacy-state-drift | a run whose state predates this change | existing log_path values are read and never rewritten, and a run with no recorded run branch keeps the unconstrained override
recorded-log-divergence | the --log value on audit-round and done audit | refused unless it equals the configured path, so a round cannot record a file it was never told to write
overclaimed-record | the round receipt's log field when --log is omitted | it records the configured path, which is the obligation the round was under, and the receipt still does not assert the bytes were written
history-mutation | the existing audit/AUDIT.md bytes | the change appends and never edits, and the root suite reader keeps passing on unchanged history
boundary-currency | .horos/boundary.json against the new audit/rounds tree | the boundary is regenerated and checked at the last step, after every other file is final
```

## 6. Glossary seeds

- **Run log.** The file one run's audit rounds append to, at
  `config audit.log_path`.
- **Derived name.** `<flattened run branch>.md`, the basename a run's log
  carries wherever the directory is moved to.
- **Flattened run branch.** The run branch with `/` replaced by `-`, already
  used to name the run's worktree directory.
- **Overlap set.** In `sync-run`, the intersection of the paths a run changed
  with the paths the base changed since their merge base.
- **Root log.** `audit/AUDIT.md`, the shared file every run appended to before
  this change.
- **Legacy run.** A run whose state was written by a controller that recorded no
  `run_branch`.

## 7. Sources

- [skills#576](https://github.com/wildcat-finance/skills/issues/576), the issue.
- [skills#583](https://github.com/wildcat-finance/skills/pull/583) and
  [skills#579](https://github.com/wildcat-finance/skills/pull/579), the last two
  merged pull requests touching Fiat.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, at `:88`, `:1312`,
  `:2288`, `:2354`, `:2733`, `:2804`, `:4924` and `:5006`.
- `plugins/hexaemeron/skills/fiat/references/audit-loop.md`, the round contract.
- `plugins/hexaemeron/README.md:195`, the config table.
- `plugins/hexaemeron/skills/protasis/SKILL.md`, item 2's naming of the file.
- `tests/test_run_observation.py:22` and `:84`, the only root-suite reader of
  the log.
- `audit/AUDIT.md:723` and `:5564`, the two rounds bearing on the design.
- `plugins/probitas/audit/AUDIT.md:71`, the earlier move by plugin.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, at `fiat-v5.20.1`.
- `AGENTS.md`, the suite and lint commands every step runs.

## 8. Signals, and the questions behind them

Fiat runs in front of somebody, not unattended, so the questions are asked at a
refusal rather than at three in the morning. Three arise:

- *Which file is this round supposed to write?* Today only the warden packet
  names it, so an inline caller learns the answer from a refusal. Step 3 adds
  `log_path` to the `audit-round` directive, so `hexctl next` states it before
  the round is recorded.
- *Why was my `config set audit.log_path` refused?* Step 2's refusal names the
  supplied value and the basename required, rather than reporting a bad path.
- *Where did this run's rounds go, read a year later?* The round and closure
  receipts carry the path, `status` shows the config, and the run's pull request
  body names the file.

[ephoros](../../skills/ephoros/SKILL.md) owns what a signal must carry.

## 9. Boundaries, per capability

Two, both string-to-path, both closed by validation before the value is used:

- **Run branch to log path, at `init`.** Worth taking: the run already has one
  identity and the worktree already derives a directory name from it. The
  control is `check_branch_name`, which `flattened_run_branch` calls first, so
  the derivation runs on a name git has accepted.
- **Operator value to log path, at `config set`.** Worth taking: a run may
  legitimately need its log somewhere else, as the three per-plugin logs show.
  The control is the four-part check in the risk register's `override-escape`
  line, with `scoped_path` for containment.

Nothing else opens: no subprocess, no fetch, no credential, no dependency, no
model output reaching a command. [phylax](../../skills/phylax/SKILL.md) owns the boundary
list and the controls.

## 10. The budget, or its absence

None. The change adds one string operation at `init` and two comparisons at
`config set` and `audit-round`. No claim is made that anything got faster, and
no step is taken in the name of speed, so [metron](../../skills/metron/SKILL.md) has
nothing to measure. If a step later proposes one, it owes a recorded before and
after.

## 11. The fail-closed posture

A refused `config set` leaves the state file and the ledger unchanged, because
`cmd_config` validates before it assigns and `commit` is the only writer. A
refused `audit-round` appends nothing, for the same reason: every check runs
before `rounds.append`. A run branch that `check_branch_name` rejects never
reaches `init`'s worktree creation, which is already true.

The guard-test convention each fix follows: one test per refusal, asserting the
exact non-zero exit and that the state file's bytes are unchanged afterwards,
written to fail against the entry state before the fix exists.
[elenchus](../../skills/elenchus/SKILL.md) owns the triage order and the guard rule.

## 12. Decisions and their homes

- **Splitting the audit record by run.** Expensive to reverse: once runs write
  to their own files, going back means a reader has to know both conventions.
  It gets a decision record under `docs/decisions/`, numbered against
  `main` immediately before the pull request merges, because two records took
  the same free number in this repository twice this month.
- **The generation row.** `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, one
  row, written at the last step for the same collision reason. The held issue
  363 job is untouched.
- **Where new rounds go.** `plugins/hexaemeron/skills/fiat/references/audit-loop.md`
  and `plugins/hexaemeron/README.md:195`, which state the contract and the
  default operators read.
- **The pointer in the root log.** Appended to `audit/AUDIT.md`, so a reader who
  opens the file this repository has always used is told where the rest is.

[hypomnema](../../skills/hypomnema/SKILL.md) owns which decisions earn a record and where
each one lives.

## Boundaries

**Always.** The root suite and the Hexaemeron suite before every commit. The
three bundled lints over `plugins` and `tests`, and Hypomnema over
`README.md AGENTS.md .agents plugins docs`. Imprimatur and Brevitas on every
shipped document. The Protasis checker over this study and the runbook.
Sapheneia's bounded pass on every audit record before it is appended.

**Ask first.** Adding a dependency. Editing a sibling skill's `SKILL.md`, which
this run does once, in Protasis, to remove a default that no longer exists.
Changing `tests/test_run_observation.py`. Touching CI. Any change to the
existing bytes of `audit/AUDIT.md` above the appended pointer.

**Never.** Edit a historical audit section. Rewrite `audit.log_path` in state
that already exists. Delete a failing test to make a suite pass. Claim a lint,
a suite or a round ran when it did not. Force-push over the signed stack.

## Success criteria

Each is a command, run from the run worktree:

1. A run initialised by the new controller derives its own log path with no
   operator action.
   `python3 plugins/hexaemeron/tests/run_tests.py`, the new
   `AuditLogPathTests`, which asserts `config get audit.log_path` equals
   `audit/rounds/<flattened run branch>.md` for a freshly initialised run.
2. `config set audit.log_path` refuses a value whose basename is not the run's
   derived name, and accepts one that only moves the directory. Same suite, same
   class, with the state file's digest unchanged across the refusal.
3. `audit-round --log` and `done audit --log` refuse a path that differs from
   the configured one, and a round with no `--log` records the configured path.
   Same suite, `AuditRoundLogBindingTests`.
4. `hexctl next` names `log_path` on an `audit-round` directive. Same suite.
5. A legacy run, with `run_branch` absent from state, keeps the unconstrained
   override and the log path its state holds. Same suite.
6. The whole tree stays green: `python3 -m unittest discover -s tests` at 349
   tests plus whatever this run adds, and
   `python3 plugins/hexaemeron/tests/run_tests.py` at 986 plus this run's, both
   from inside the run worktree.
7. This run's own rounds are in
   `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md` and
   `git log --oneline -- audit/AUDIT.md` shows this run's only commit to the
   root log is the appended pointer.
8. `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` leaves
   `.horos/boundary.json` unchanged, or the change is committed at the last
   step.
