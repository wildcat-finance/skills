# The classifier refinement, the runbook

Five steps, dependency order, one pull request each. The study committed
beside this runbook is the spec; the maintainer's specification it maps is
already in the tree.

## Step 1: Commit the frontier spec

**Goal.** The study and runbook are in the tree the later steps build on.
**Entry.** The run branch, cut from `main` at `9b8301e`.
**Exit.** Both suites green, three tree lints clean, imprimatur clean on
both documents.
**Files.** `plugins/horos/docs/refinement/study.md` and
`plugins/horos/docs/refinement/runbook.md`, beside the maintainer's
specification.
**Tests.** None new; the existing suites hold.

## Step 2: Independent signals

**Goal.** Nested gitattributes classify through a rule stack pushed and
popped during the walk (64 KiB per-file cap), and file signatures name
common binary formats as hard evidence.
**Entry.** Step 1's exit state.
**Exit.** Plugin suite green; the frozen fixture boundary unchanged (both
signals only add evidence the fixture does not exercise yet).
**Files.** `plugins/horos/skills/horos/scripts/horos.py`;
`plugins/horos/tests/test_classify.py` extended.
**Tests.** A nested attributes file classifying its own subtree; a sibling
directory unaffected; a deeper file overriding nothing outside its scope;
PNG, ZIP, PDF, WebAssembly and WOFF signatures each classified binary with
the signature named; a text file starting with none staying readable.
Expected count: about eight.

## Step 3: The graded pipeline

**Goal.** The specification's pipeline lands whole: corroborated directory
exclusions, the selective second sampling pass, hard and candidate grades,
boundary schema 2 with hard entries only, and the candidates artefact.
**Entry.** Step 2's exit state.
**Exit.** Plugin suite green; the fixture boundary regenerated at schema 2
and reproduced byte for byte, its candidates artefact likewise; `check`
fails on hard drift and, at this historical step, reports candidate drift
without failing. Under the current contract, candidate classification or
content drift itself remains advisory, while root raw canonical metadata stays
hard: adding or removing a tracked candidate changes `files_walked` and can
fail on that independent drift. Scoped checks remain entry-only.
**Files.** `horos.py`; `plugins/horos/examples/fixture/.horos/boundary.json`
regenerated; `plugins/horos/examples/fixture/.horos/candidates.json`;
`plugins/horos/tests/test_boundary.py`, `test_classify.py`,
`test_discipline.py` and `plugins/horos/examples/README.md` updated.
**Tests.** A build directory with hand-written source walked file-by-file;
the same name corroborated by a marker sample excluding hard with quoted
corroboration; a large unresolved file classified from a middle or end
window; geometry staying candidate wherever found; the grade lists in both
artefacts; check's split behaviour. Expected count: about twelve.

## Step 4: The universe

**Goal.** Scanning a git repository covers exactly the tracked files by
default, `--include-untracked` widens it, a non-git tree walks the
filesystem, and the boundary records which universe produced it.
**Entry.** Step 3's exit state.
**Exit.** Plugin suite green; the git subprocess is fixed-argv, shell-free
and pinned to the scan root, with the phylax allow comment naming exactly
that.
**Files.** `horos.py`; `plugins/horos/tests/test_universe.py`.
**Tests.** A temp git repository where an untracked build product is
outside the default universe and inside the widened one; a non-git tree
falling back to the walk; git absence falling back cleanly; the universe
recorded in the artefact. Expected count: about six, skipped cleanly where
git is unavailable.

## Step 5: Reledger and reconcile

**Goal.** The ledger advances to `horos-v8.2.2` holding the
three-repository marking as the next job, and every surface agrees.
**Entry.** Step 4's exit state.
**Exit.** Study success criteria 1 through 4 all pass as written.
**Files.** `EVOLUTION.md`; `SKILL.md` (metadata `8.2.2`, grades and
universe documented, candidates advisory); `plugins/horos/README.md`;
`.agents/skills/horos/SKILL.md`; root `README.md`.
**Tests.** None new; the evolution and marketplace-prose contracts are the
check.
