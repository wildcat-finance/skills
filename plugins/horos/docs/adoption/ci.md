# Holding an adopted boundary current in CI

A committed boundary goes stale the moment the tree it describes changes,
and an agent that consults it does not know that. `horos check` re-derives
the boundary and names every drifted path, so running it on every push is
what makes the committed copy worth consulting.

This is the workflow, written for a repository that has adopted a
boundary and does not carry the skill. It was run against
wildcat-app-v2 at `564a189bb9cdc9394b3fd4f444531a261ada99b3` with the
artefacts regenerated, and reported `boundary matches the tree` at exit 0.

```yaml
name: horos

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    branches: ['**']
  push:
    branches: ['**']
    tags-ignore: ['**']

permissions:
  contents: read

env:
  HOROS_REPO: wildcat-finance/skills
  HOROS_REF: 12cbe2e6ed95decd6d9d355740f2dbd052956abe
  HOROS_SCRIPT: .horos-classifier/plugins/horos/skills/horos/scripts/horos.py

jobs:
  boundary:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout this repository
        uses: actions/checkout@v4

      - name: Checkout the pinned Horos classifier
        uses: actions/checkout@v4
        with:
          repository: ${{ env.HOROS_REPO }}
          ref: ${{ env.HOROS_REF }}
          path: .horos-classifier

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Print tool versions
        run: |
          python3 --version
          git -C .horos-classifier rev-parse HEAD

      - name: Check the committed reading boundary
        run: python3 "$HOROS_SCRIPT" check .
```

## What it needs

**The pin.** `HOROS_REF` is a commit, not a branch. The classifier decides
what counts as evidence, so an unpinned classifier turns an unrelated
Horos change into a red build in somebody else's repository. `12cbe2e6`
is `horos-v12.3.3`. Moving the pin is a deliberate commit, and the same
commit regenerates the artefacts.

**The checkout path.** The classifier lands inside the workspace at
`.horos-classifier`, which is untracked there. `check` walks the
git-tracked universe by default, so the checkout is invisible to the
scan and needs no ignore rule.

**Python and nothing else.** `horos.py` imports only the standard library
and its own `languages` package, so there is no install step and no
lockfile to keep current.

**A green start.** `check` fails until the committed artefacts match the
tree the workflow runs against. Regenerate both before the first run:

```sh
python3 horos.py scan . --write
python3 horos.py scan . --census --write
```

## What it costs

`counts.files_walked` is one of the compared fields, so adding or removing
any tracked file drifts the boundary and reddens the check until the
author commits a regenerated one. That is the gate working: a boundary
that survived a file arriving is a boundary nobody can trust. On an
active repository it is a real recurring cost, paid by whoever adds the
file, and it is worth naming to the people who will pay it before the
workflow lands.

The check itself is cheap. Horos reads a bounded prefix of each file, and
a whole-tree scan of a 17 MB repository takes tens of milliseconds.
