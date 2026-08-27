# The three-repository marking, the runbook

Four steps, dependency order, one pull request each in this repository plus
one per product repository.

## Step 1: Commit the frontier spec

**Goal.** The study and runbook are in the tree the later steps build on.
**Entry.** The run branch, cut from `main` at `be07cb8`.
**Exit.** Both suites green, three tree lints clean, imprimatur clean on
both documents.
**Files.** `plugins/horos/docs/marking/study.md` and
`plugins/horos/docs/marking/runbook.md`.
**Tests.** None new; the existing suites hold.

## Step 2: Mark the skills repository

**Goal.** This repository carries its own committed boundary, candidates
and census under the tracked universe, and the adoption stanza sits in
`AGENTS.md`.
**Entry.** Step 1's exit state.
**Exit.** `python3 plugins/horos/skills/horos/scripts/horos.py check .`
passes from the root; both suites green; the root suite's prose contracts
hold with the stanza in place.
**Files.** `.horos/boundary.json`, `.horos/candidates.json`,
`.horos/census.json`, `AGENTS.md`.
**Tests.** None new; check from the root is the proof, run in the step and
again by the demo criterion.

## Step 3: Mark the product repositories and record the evidence

**Goal.** v2-protocol and wildcat-app-v2 each carry a branch and pull
request adding their three artefacts and stanza; the recaptures are
recorded as a machine-checked bundle beside the schema-1 captures.
**Entry.** Step 2's exit state.
**Exit.** Both pull requests open with the house markers; the bundle's
machine lines checked by the suite;
`python3 -m unittest plugins.horos.tests.test_evidence -v` green.
**Files.** In this repository:
`plugins/horos/docs/evidence/three-repository-marking.md`, copies of the
product boundaries at
`plugins/horos/docs/evidence/v2-protocol.boundary.json` and
`plugins/horos/docs/evidence/wildcat-app-v2.boundary.json.v2`;
`plugins/horos/tests/test_evidence.py` extended. In each product
repository: `.horos/boundary.json`, `.horos/candidates.json`,
`.horos/census.json`, `AGENTS.md`.
**Tests.** Bundle-consistency checks over the recapture copies. Expected
count: about three.

## Step 4: Reledger, reconcile, close

**Goal.** The ledger advances to `horos-v9.2.2`, the frontier closes
mature with the open pull requests named, and every surface agrees.
**Entry.** Step 3's exit state.
**Exit.** Study success criteria 1 through 4 all pass as written.
**Files.** `EVOLUTION.md`; `SKILL.md` (metadata `9.2.2`, frontier text);
`plugins/horos/README.md`; `.agents/skills/horos/SKILL.md`; root
`README.md`.
**Tests.** None new; the evolution and marketplace-prose contracts are the
check.
