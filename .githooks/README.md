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

The root suite is to fail and name this command in a checkout where it is unset.
That assertion arrives with step 4 of the run behind this directory; until it
lands, an unactivated checkout is silent.

## Skip it for one commit

```
FIAT_SKIP_PRECOMMIT=1 git commit
```

That token is the only way past the gate. It is a literal string so you can grep
for it here rather than hear about it from somebody.

## What lands here

Step 2 of the run behind this directory adds the gate scripts themselves: a
`pre-commit` hook that refuses a commit whose staged tree is not the tree a
recorded green names, and a `greenlight` command that runs the suite and records
the green when the suite passes.

The decision behind the layout is
[docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md](../docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md).
