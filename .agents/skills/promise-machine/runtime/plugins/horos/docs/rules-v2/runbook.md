# The Horos rule-classes run, the runbook

Four steps, dependency order, one pull request each. The study committed
beside this runbook is the spec; both land in step 1.

## Step 1: Commit the frontier spec

**Goal.** The study and this runbook are in the tree the later steps build on.
**Entry.** The run branch, cut from `main` at `d474d75`.
**Exit.** Both suites green, three tree lints clean, imprimatur clean on
both documents.
**Files.** `plugins/horos/docs/rules-v2/study.md` and
`plugins/horos/docs/rules-v2/runbook.md`.
**Tests.** None new; the existing suites hold.

## Step 2: The two rule classes

**Goal.** The classifier evidences SVG text assets and migration SQL, and
the shipped example proves both.
**Entry.** Step 1's exit state.
**Exit.** Plugin suite green; each rule has a positive and two near-miss
cases; the example fixture's regenerated boundary is reproduced byte for
byte.
**Files.** `plugins/horos/skills/horos/scripts/horos.py`;
`plugins/horos/tests/test_classify.py` extended;
`plugins/horos/examples/fixture/icons/logo.svg` and
`plugins/horos/examples/fixture/prisma/migrations/0001_init/migration.sql`
added; `plugins/horos/examples/fixture/.horos/boundary.json` regenerated;
`plugins/horos/examples/README.md` and
`plugins/horos/tests/test_discipline.py` updated for the new categories.
**Tests.** SVG with root element earns `asset`; `.svg` without the root and
an `<svg` fragment under another name stay readable. `.sql` under a
`migrations` segment earns `generated`; SQL outside the segment and non-SQL
inside it stay readable. Expected count: about six new.

## Step 3: The second capture

**Goal.** The improvement is recorded against the same tree, machine-checked
like the first capture, with zero false exclusions held.
**Entry.** Step 2's exit state.
**Exit.** `python3 -m unittest plugins.horos.tests.test_evidence -v` proves
both captures; the second's classified share exceeds 80.3%; the entries
added relative to the first capture are only `.svg` and
migrations-segment `.sql` paths.
**Files.** `plugins/horos/docs/evidence/wildcat-app-v2-rules.md` and
`plugins/horos/docs/evidence/wildcat-app-v2-rules.boundary.json`;
`plugins/horos/tests/test_evidence.py` extended.
**Tests.** The consistency checks parametrised over both bundles, plus the
delta check that new entries are only the two rule families. Expected
count: about four new.

## Step 4: Reledger and reconcile

**Goal.** The ledger advances to `horos-v2.1.0` holding the
maintainer-directed outline-extractor job, and every surface agrees.
**Entry.** Step 3's exit state.
**Exit.** Study success criteria 1 through 4 all pass as written.
**Files.** `plugins/horos/skills/horos/EVOLUTION.md` (evolution row,
script-computed digest); `plugins/horos/skills/horos/SKILL.md` (metadata
`2.1.0`, frontier text, the refusal paragraph superseded in place, dated,
naming the maintainer direction); `plugins/horos/README.md` (context block
and job line); `.agents/skills/horos/SKILL.md`; root `README.md` (frontier
cell).
**Tests.** None new; the evolution and marketplace-prose contracts are the
check.
