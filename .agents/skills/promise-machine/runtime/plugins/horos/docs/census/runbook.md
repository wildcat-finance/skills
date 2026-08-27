# The filetype census, the runbook

Four steps, dependency order, one pull request each. The study committed
beside this runbook is the spec; both land in step 1.

## Step 1: Commit the frontier spec

**Goal.** The study and runbook are in the tree the later steps build on.
**Entry.** The run branch, cut from `main` at `751a552`.
**Exit.** Both suites green, three tree lints clean, imprimatur clean on
both documents.
**Files.** `plugins/horos/docs/census/study.md` and
`plugins/horos/docs/census/runbook.md`.
**Tests.** None new; the existing suites hold.

## Step 2: The census

**Goal.** `scan --census` prints the per-filetype rows and `--write`
commits `.horos/census.json`, sharing the boundary's walk exactly; scan
without the flag is byte-for-byte unchanged.
**Entry.** Step 1's exit state.
**Exit.** Plugin suite green; the fixture census committed and reproduced
byte for byte; the frozen fixture boundary still reproduced byte for byte.
**Files.** `plugins/horos/skills/horos/scripts/horos.py`;
`plugins/horos/examples/fixture/.horos/census.json`;
`plugins/horos/tests/test_census.py`; `plugins/horos/examples/README.md`
gains the census commands.
**Tests.** Suffix bucketing including `(no suffix)`; a vendored-directory
file attributed to its suffix row with bytes in the boundary column; rows
sum to the total and the boundary column never exceeds its row; symlinks
and skipped directories in neither walk; determinism; the frozen boundary;
atomic write. Expected count: about nine.

## Step 3: The recorded census

**Goal.** The wildcat-app-v2 census is recorded as a machine-checked
evidence bundle naming the biggest readable-but-unmappable filetypes.
**Entry.** Step 2's exit state.
**Exit.** `python3 -m unittest plugins.horos.tests.test_evidence -v` green
over all four bundles.
**Files.** `plugins/horos/docs/evidence/wildcat-app-v2-census.md` and
`wildcat-app-v2-census.json`; `plugins/horos/tests/test_evidence.py`
extended.
**Tests.** Consistency checks in the shape of the other bundles. Expected
count: about three.

## Step 4: Reledger and reconcile

**Goal.** The ledger advances to `horos-v4.2.0` with the next job decided
from the census evidence, and every surface agrees.
**Entry.** Step 3's exit state.
**Exit.** Study success criteria 1 through 4 all pass as written.
**Files.** `EVOLUTION.md`; `SKILL.md` (metadata `4.2.0`, the census verb
documented, frontier text); `plugins/horos/README.md`;
`.agents/skills/horos/SKILL.md`; root `README.md`.
**Tests.** None new; the evolution and marketplace-prose contracts are the
check.
