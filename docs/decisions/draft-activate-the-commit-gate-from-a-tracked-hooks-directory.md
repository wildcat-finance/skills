# Activate the commit gate from a tracked hooks directory

## Status

Proposed, 2026-09-04. Unnumbered on purpose, and nothing assigns the number
yet. The arithmetic against this base gives ADR-074, and run #856 is open on the
same base with a runbook that claims the same number. `tests/test_decision_records.py`
compares against `origin/main`, so it sees a collision only once the other
number has landed. The second run to merge would renumber its record and every
reference to it after review. Issue #888 proposes that records take their
number at merge, and records why: ADR-050 collided at authoring time, and the
ADR-024 duplicate turned `main` red until #582 renumbered the Wave Delta chain.
Whoever merges this record gives it a number by hand, or leaves it unnumbered
knowingly.

The filename carries no `ADR-` prefix because `tests/test_decision_records.py`
globs `ADR-*.md` and then requires digits, so a prefixed draft fails
`test_every_filename_follows_the_convention`. That check is left exactly as it
is. `tests/test_commit_gate.py` holds this record's required sections instead,
and also asserts that no `ADR-074-*.md` file appears here, so the run cannot
drift back into the collision it is avoiding.

## Context

The repository had a commit gate and lost it. It existed as two untracked
scripts in one clone's `.git/hooks`, and both are gone: on 2026-09-04 that
directory held fourteen files and every one was a `.sample` shipped by
`git init`. The tracked tree carried nothing either, so nothing could be
restored from it. The discipline evaporated with the clone that held it, which
is what issue #857 was filed to stop happening again.

Git cannot install a hook on clone. That was measured rather than assumed: a
fixture repository with a tracked `.githooks/pre-commit` was cloned, the clone
reported an empty `core.hooksPath`, carried the hook file on disk unused, and
committed with exit 0. So a gate cannot be made to arrive by itself. It can only
be made to announce that it is missing.

Contributors run this repository from many worktrees at once; this clone had 39
registered worktrees when the study was written. A design activated once per
checkout is therefore a different proposition from one activated once per clone.

## Decision

**The gate lives in a tracked `.githooks/` directory and is activated by one
command, `git config core.hooksPath .githooks`.** The scripts have one source of
truth, in the tree, where a review sees them.

**One command covers every worktree.** `core.hooksPath` set in the shared
configuration was read back in a linked worktree, and because the value is
relative it resolved against each worktree's own top level, so the hook that ran
in the linked worktree was that worktree's own tracked copy.

**The absence of the activation is a root-suite failure.** A checkout whose
`core.hooksPath` is unset, or points anywhere other than the tracked directory,
fails the suite with a message naming the one command that fixes it. Because the
assertion lives under `tests/`, it is inside the `invariants` context that
`repo.yml` already runs on every pull request, so it needs no workflow edit and
no ruleset edit.

**The gate compares tree identities rather than running the suite.** It refuses
a commit whose staged tree is not the tree a recorded green names. The suite
costs 289.3 seconds, and a gate that spends that on every commit attempt gets
turned off.

**The escape hatch is one literal token, `FIAT_SKIP_PRECOMMIT=1`,** so a reader
can grep for it rather than learn it from somebody.

**Nothing here gates a push or a merge, and ruleset `21830871` is not touched.**

## Alternatives

- **`installed-hooks`, committed scripts copied into the git directory by a
  documented command.** Rejected because it loses the whole of acceptance
  condition 2: a fresh clone commits with exit 0 and nothing in the repository
  can tell that the copy was never made. It also duplicates the scripts out of
  the tracked tree, where the copy can drift from its source with nothing
  comparing them. Measured at 497 bytes of state per clone.
- **`hooks-path` without the visibility assertion.** Rejected because it loses
  the same condition by the same clone proof. It is the better mechanism, with
  one source of truth and 40 bytes of state per clone, failing the identical
  gate. Adding the assertion is what separates it from the choice above.
- **`ci-only`, no local gate and a hosted check instead.** Rejected because it
  loses the discipline itself. Enforcement would need a new required context on
  ruleset `21830871`, which the issue's boundary forbids; the live ruleset
  requires only `identity` and `invariants`. Its only enforcement point is the
  merge, which the boundary reserves to the existing rulesets. It has no
  per-commit bypass a contributor can set, because the equivalent is a ruleset
  bypass actor and the ruleset has none. And it re-runs the suite on the pushed
  tree instead of comparing the staged tree against a recorded green identity,
  so there is never a stale record for it to catch.
- **The null option, shipping no gate at all.** Rejected because it loses the
  discipline the issue exists to preserve. It passes the boundary criteria
  vacuously and costs nothing, and it fails every criterion about a working gate
  for the same reason: there is nothing there. The chosen design was measured at
  22 milliseconds per commit and 40 bytes per clone, so the null option costs
  more than it saves.

## Consequences

**The green record is a convenience rather than proof that the suite ran.**
Anyone who can write the git directory can write it. It carries no provenance,
and nothing should build a claim on its existence. It is the shape of audit
finding S1-R1-01 on the check runner: a record that supplies its own expected
value verifies against itself. Read it as a note to the committer, not as
evidence to a reviewer.

**The visibility assertion is `tests.test_commit_gate.ActivationTests`.** Three
of its four cases settle wording and tracked bytes and hold wherever the suite
runs. The fourth reads the checkout's own `core.hooksPath` and fails when it is
unset or names another directory, with `git config core.hooksPath .githooks` in
the failure. Nothing else in a fresh clone runs before the first commit, so the
root suite is where the absence has to be said.

**Hosted execution cannot see whether a contributor activated the gate
locally,** because no evidence of a local hook reaches the server. The CI half
of this decision therefore holds only the tracked bytes: that the hooks
directory exists, that its scripts are tracked and executable, and that they
name the bypass token. The activation half is visible locally, in the suite run
that must precede any commit under the discipline. The fourth case is therefore
skipped where the environment names a hosted runner, and says so in the skip
reason. `repo.yml` runs the root suite on every pull request, and a case
asserting local activation there would report on the runner's own checkout,
which nobody commits from, while turning a required check red for every change
in the repository.

A contributor who never runs the suite gets no green record, so their first
commit is refused if the gate is on, and passes silently if it is off. This
decision does not close that hole. It makes the hole announce itself the first
time the suite runs.

Where the gate lives is expensive to reverse. Once contributors have set
`core.hooksPath` in their own clones, moving the directory leaves every one of
those settings pointing at nothing, and the failure they get names a path that
no longer exists.
