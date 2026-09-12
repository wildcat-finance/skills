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

## When a worktree runs another tree's hooks

A linked worktree can carry a `core.hooksPath` of its own, and git reads that
ahead of the shared value whenever `extensions.worktreeConfig` is true. Tooling
outside this repository writes one, an absolute path to the main checkout:

```
[core]
	hooksPath = /Users/<user>/Projects/wildcat-skills/.githooks
```

The tracked relative value never applies there, so git runs another directory's
`pre-commit` against this worktree's staged tree and `ActivationTests` fails.
Running the activation command above from inside such a worktree does not
repair it: that writes the shared config, which was already correct, and leaves
the override where it is.

Clear it in the worktree that carries it:

```
git config --worktree --unset core.hooksPath
```

The repair does not hold by itself. On 6 September 2026 four worktrees of one
clone were unset together; the one whose session was active had the absolute
value written back twenty-three seconds later, and the other three stayed
repaired. A second unset on that worktree was still intact ninety seconds on,
with its `config.worktree` untouched. So the override arrives at a discrete
moment rather than continuously, and what evidence there is points at worktree
creation or session start. Read it again when work resumes in a worktree rather
than once:

```
git config core.hooksPath
```

That prints `.githooks` in a worktree that will run its own copy. Which tool
writes the override is not established here.

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
