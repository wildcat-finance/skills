# The tracked hooks directory

This directory holds the commit gate scripts. Git does not install a hook when
you clone, so a fresh checkout carries these files on disk and never runs them
until you say so.

## Turn it on

```
git config core.hooksPath .githooks
```

Run that once per clone. The value is relative, so every linked worktree of the
clone resolves it against its own top level and runs its own tracked copy.

In a checkout where `core.hooksPath` is unset, or set to any directory other
than this one, `python3 -m unittest discover -s tests` fails and the failure
names this command, so an unactivated clone reports it on a suite run rather
than after the first unchecked commit. `ActivationTests` in
`tests/test_commit_gate.py` carries that assertion. Run it in the checkout
itself: it skips where `GITHUB_ACTIONS` or `WILDCAT_CHECK_CONTAINMENT` says
the execution is nobody's checkout, and `scripts/run_checks.py` sets the
second for the snapshot it runs the suite from, so neither the checked runner
nor a hosted runner tells you whether your clone is activated.

## Skip it for one commit

```
FIAT_SKIP_PRECOMMIT=1 git commit
```

That token is for a commit you mean to make without a recorded green: the gate
reads it and stands aside. It is a literal string so you can grep for it here
rather than hear about it from somebody. It is not the only way past. `git
commit --no-verify`, and the `-n` short form, tell git to run no pre-commit
hook at all, so the gate never executes and prints nothing; the commit lands as
it would in a checkout that was never activated.

## What lands here

Step 2 of the run behind this directory adds the gate scripts themselves: a
`pre-commit` hook that refuses a commit whose staged tree is not the tree a
recorded green names, and a `greenlight` command that runs the suite and records
the green when the suite passes.

The decision behind the layout is
[docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md](../docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md).
