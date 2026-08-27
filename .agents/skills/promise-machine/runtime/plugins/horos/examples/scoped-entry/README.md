# Scoped entry, the example

A miniature repository with one boundary at its top and two package
directories under it. `packages/one/yarn.lock` and `packages/two/go.sum` are
lockfiles, so each is a hard entry; `src/app.py`, `packages/one/module.py` and
`packages/two/other.py` stay readable. The committed boundary lives at
`.horos/boundary.json` and covers all of it.

The point of the example is the difference between two answers: whether this
repository's boundary is current, and whether the boundary covering the
directory an agent is about to read is current. Run everything from the
repository root.

## Entering the repository

```bash
python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/scoped-entry
```

exits 0 with `boundary matches the tree`. That is the whole-tree answer, and
its wording is unchanged from before scoped entry existed.

## Entering one directory to work in it

```bash
python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/scoped-entry/packages/one
```

exits 0 and prints:

```text
boundary root: <your checkout>/plugins/horos/examples/scoped-entry
scope: packages/one
hard boundary: matches
candidates: 0 findings, advisory
outside-scope drift: not evaluated
counters: classified 2, listed outside scope 1, attribute files above scope 0
```

The first line names your checkout, so the test that pins this output compares
every line after it. `classified 2` is the whole cost: `module.py` and
`yarn.lock`, the two files in the scope. Nothing outside it was stat'd, opened
or classified.

## The drift that refuses one answer and not the other

Change a lockfile in the sibling package:

```bash
echo 'example.com/other v0.1.0 h1:2222222222222222222222222222222222222222=' >> plugins/horos/examples/scoped-entry/packages/two/go.sum
```

The whole-tree check now exits 1 and names it:

```text
drift: packages/two/go.sum: entry changed: ...
1 path(s) drifted
```

The scoped check on `packages/one` still exits 0 with `hard boundary:
matches`, because the drift is outside the scope it was asked about, and it
says as much on the `outside-scope drift` line rather than implying the
repository is clean.

Put it back:

```bash
git checkout -- plugins/horos/examples/scoped-entry/packages/two/go.sum
```

## Refusals

Each of these exits 2 rather than answering from the wrong boundary:

- a directory with no committed boundary at or above it
- a relative path that resolves out of the worktree, whether by `..` or
  through a symlink at any point in it
- a boundary document that cannot be read

`test_scoped_entry.py` and `test_demonstration.py` hold these as tests, so the
example cannot drift away from the behaviour it describes.
