# The Horos live-evidence run, the runbook

Three steps, dependency order, one pull request each. The study committed
beside this runbook is the spec; both land in step 1.

## Step 1: Commit the frontier spec

**Goal.** The study and this runbook are in the tree the later steps build on.
**Entry.** The run branch, cut from `main` at `e17f8ce`.
**Exit.** Both suites green, three tree lints clean, imprimatur clean on both
documents.
**Files.** `plugins/horos/docs/live-evidence/study.md` and
`plugins/horos/docs/live-evidence/runbook.md`.
**Tests.** None new; the existing suites hold.

## Step 2: Record the evidence bundle

**Goal.** The wildcat-app-v2 capture is committed with its numbers
machine-checked.
**Entry.** Step 1's exit state.
**Exit.** Plugin suite green including the new consistency test; the demo
command from the study runs:
`python3 -m unittest plugins.horos.tests.test_evidence -v`.
**Files.** `plugins/horos/docs/evidence/wildcat-app-v2.md` (the bundle:
commit, date, tool version, totals, every entry, the misses, the criterion
check) and `plugins/horos/docs/evidence/wildcat-app-v2.boundary.json` (the
scan's boundary document, committed verbatim);
`plugins/horos/tests/test_evidence.py`.
**Tests.** The committed boundary parses with schema 1; its classified-byte
total, entry count and per-category totals equal the numbers the bundle
markdown quotes in its machine-readable lines; the bundle names the commit.
Expected count: about four.

## Step 3: Decide, reledger, reconcile

**Goal.** The TypeScript refusal is recorded, the ledger advances to
`horos-v1.1.0` with the new held job, and every marketplace surface agrees.
**Entry.** Step 2's exit state.
**Exit.** Study success criteria 1 through 4 all pass as written; the root
suite validates the new ledger row's digest and the surfaces' agreement.
**Files.** `plugins/horos/skills/horos/EVOLUTION.md` (evolution row, new
frontier and held job, script-computed digest);
`plugins/horos/skills/horos/SKILL.md` (metadata `1.1.0`, frontier text, the
recorded refusal with its reason); `plugins/horos/README.md` (context block:
frontier and Next Fiat job line); `.agents/skills/horos/SKILL.md` (frontier);
root `README.md` (the Horos frontier cell).
**Tests.** None new; the evolution and marketplace-prose contracts in the
root suite are the check.
