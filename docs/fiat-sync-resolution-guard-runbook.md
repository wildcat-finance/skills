# Fiat sync resolution guard runbook

## Step 1: Implement and propagate the guard

### Scope and exit

**Goal.** Make every new Fiat integration sync expose and explicitly
acknowledge the two issue-891 silent-loss surfaces before the controller writes
a receipt.

**Entry.** Signed branch base
`83652238f9e22d6857bb0106681cb391438d1ddd`; accepted
`docs/fiat-sync-resolution-guard-study.md`; the focused issue-891 module is red
only because the production guard and CLI flag do not exist. Before editing,
confirm ADR-057, Fiat `5.40.1` and Hexaemeron `1.6.14` remain collision-free.

**Exit.** `done sync-run` derives `fiat-sync-resolution-guard/v1` from native
commit objects, refuses a risky sync without the exact sorted unique repeated
path flags, stores the normalized record, displays bounded counts, and replays
the record before integration. First-sync whole-side selection, semantic union,
supersession intersection, exact-set and parser cases pass. Existing sync tests
store an empty guard. Legacy active syncs without the field refuse and name a
fresh signed supersession as recovery. Fiat is `5.40.1`, Hexaemeron is
`1.6.14`, the held frontier is unchanged, canonical and portable copies agree,
and the current primer sources and rendered PDFs carry the new versions.

### Files and tests

**Files.** Change
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, Fiat `SKILL.md` and
`EVOLUTION.md`, `references/push-discipline.md`, the Hexaemeron plugin
manifests and marketplace entries,
Promise Machine coverage, version and evolution tests, primer builder/test and
current-version study sentence. Create the issue-891 focused test and ADR-057.
Update existing `test_hexctl.py`, its fake delivery-tool harness, and the
disposable-signing fixture matrix.
Regenerate the portable runtime and both primer PDFs. Update
`.horos/boundary.json` only through a deterministic scan. No dependency,
workflow, ruleset or Promise Machine contract change is in scope.

**Tests.** Preserve the parent-red focused result. Then run the issue-891
module, all direct sync and version tests, disposable-signing matrix, PDF source
and render checks, complete Hexaemeron suite, root suite, portable runtime
check, Promise Machine checks, audit-synopsis currency, applicable lints, Horos
currency, `git diff --check`, and the complete plugin graph. Run the hostile
Git-object edge cases at missing entries, unsafe acknowledgements, malformed
tree output, supersession without an old base, and an active legacy receipt.

### Discipline routing

**Disciplines.** phylax: fixed native Git argv, literal paths, bounded batches
and pre-mutation CLI validation. ephoros: receipt arrays, status counts and
recovery diagnostics answer what stopped. metron: no optimisation claim;
existing path, byte and time ceilings stay fixed. elenchus: parent-red incident
fixtures and mutation-order assertions guard the cause. hypomnema: ADR-057 owns
the expensive rule; the controller owns executable values; operator guidance
lives in Fiat `SKILL.md`.

## Step 2: Publish and prove the protected transition

### Scope and exit

**Goal.** Deliver the guarded controller as one signed pull request after #889
is on protected `main`.

**Entry.** Step 1 is green and clean; #889's exact signed head is on `main`;
the #891 branch has been checked against the current remote base; every
governed commit verifies under `B83B60AE16F5DD1A` with Shoggoth author and
Laurence committer identity.

**Exit.** The branch is pushed as `laurenceday`; its pull request closes #891,
is labelled `origin:ai`, is anonymously visible, and has successful current-head
`invariants` and `plugins` contexts. Protected `main` advances to the verified
signed head without bypass, the pull request reports merged, issue #891 is
closed, remote main equals the local object, and anonymous reads return HTTP
200.

### Files and tests

**Files.** No new product file is introduced during publication. If `main`
moved, compose it with a signed product-first merge and rerun every changed-path
closure. Refresh the report-only dead-code baseline in its required second
commit after the final product tree is fixed.

**Tests.** Verify every commit locally before first push; inspect GitHub's
author, committer and signature record; read the exact pull-request head and
required check rollup; read protected rules immediately before merge; compare
remote and local main afterwards; and fetch the pull request and issue without
credentials. A stale head, missing check, unverified commit, base movement or
visibility failure stops publication.

### Discipline routing

**Disciplines.** phylax: authenticated writes use Laurence's isolated GitHub
configuration and exact refs. ephoros: commit verification, check rollup,
ruleset readback and anonymous HTTP results are the receipts. metron: none.
elenchus: any stale or failed hosted context is a hard stop. hypomnema: the pull
request links ADR-057, study, runbook and issue rather than restating the rule.
