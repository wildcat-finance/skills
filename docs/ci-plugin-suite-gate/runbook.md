# Complete plugin suite gate runbook

## Step 1: Make the complete graph green in a fresh checkout

### Scope and exit

**Goal.** Repair the measured baseline and complete-graph defects without
removing or weakening a check, and make the declarative graph total over all
sixteen plugins.

**Entry.** `main` at
`4fe374dd33d43b86d800abe9240d62e09ed7d395`, the accepted study in this
directory, and the observed Hexaemeron failures recorded there.

**Exit.** Homologia has one owned scope and suite command. The checkpoint JSON
reader refuses a documented nesting ceiling before decoding. The path-length,
issue-429 audit and release proof, issue-710 aggregate, Git-index, Synkrisis
memory-unit, Lazarus workflow and descriptor-capability, and concurrent `tmp/`
regressions are portable and retain the properties they were written to prove.
Fiat, Synkrisis and their plugin versions advance as required without moving a
held frontier; generated portable-runtime bytes and manifests agree. Each
targeted regression, the root suite, every plugin suite and
`python3 scripts/run_checks.py --full` finish green from a fresh checkout.

### Files and tests

**Files.** `tests/check-map-v1.json`; the check-map contract tests;
`plugins/hexaemeron/skills/fiat/{SKILL.md,EVOLUTION.md,scripts/hexctl.py}`;
Hexaemeron manifests and marketplace entries; generated portable-runtime
copies; `plugins/hexaemeron/tests/{test_hexctl_checkpoint.py,test_issue_429_recovery.py,test_hexctl_generator_aggregates.py}` and the issue-710 fixture;
`plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py` and its root currency
guard; Synkrisis benchmark code, skill records and memory-unit tests; Lazarus
Goldfinch and workflow-scaffold tests;
version-bound primer sources and PDFs if required by the existing propagation
contract; `.horos/boundary.json` if its deterministic scan changes.

**Tests.** Reproduce each named parent failure first. Add edge cases at and one
level beyond the JSON depth ceiling, keep punctuation inside JSON strings from
counting as structure, and prove malformed JSON still uses the existing strict
refusal. Assert plugin-directory, scope, check and owner parity. Run the exact
targeted cases, `python3 -m unittest discover -s tests`,
`TMPDIR=/private/tmp python3 plugins/hexaemeron/tests/run_tests.py --jobs 12`,
`python3 scripts/promise_machine.py check`, and the full graph. Produce focused
Elenchus old-parent reports for the behavioural repairs.

### Discipline routing

**Disciplines.** phylax: checkpoint bytes and Git fixtures are hostile bounded
inputs. ephoros: none in this step; it adds no unattended service. metron: no
performance claim; retain the measured full-suite duration. elenchus: every
observed baseline defect needs a parent-red, repaired-green guard. hypomnema:
ADR-055 owns the durable hosted-gate choice; fixture qualifications stay beside
the specimens.

## Step 2: Publish one unconditional aggregate gate

### Scope and exit

**Goal.** Make the complete local graph one stable GitHub status context.

**Entry.** Step 1 is green and the branch contains no uncommitted product
change.

**Exit.** `.github/workflows/plugins.yml` runs on every pull request and every
push to `main`, uses read-only permissions, fetches the history required by
historical release proofs, installs the locked Python dependencies, pins Node
26.6.0 and Forge 1.7.1, checks and imports the repository-pinned primary public
key for the issue-429 composition, runs `scripts/run_checks.py --full`, and
uploads its bounded report even when a check fails. Repository tests prove the
job is named `plugins`, has no path filter, uses a full checkout, fixes those
toolchain and trust inputs, and invokes the full graph rather than a copied
command list. The signed branch is pushed as `laurenceday`; its pull request
produces successful `invariants` and `plugins` checks.

### Files and tests

**Files.** `.github/workflows/plugins.yml`, workflow contract tests, this study
and runbook, and ADR-055.

**Tests.** Parse the workflow as text under the repository's dependency-free
root suite and assert its trigger, permissions, stable job name, fixed command,
report upload and absence of path filters. Run `git diff --check`, Promise
Machine checks, Protasis, Imprimatur, Vulgate comparison, Brevitas and the full
graph before signing. Verify every commit with `git verify-commit` before the
first push.

### Discipline routing

**Disciplines.** phylax: fixed argv, locked dependencies, exact toolchain
versions, a fingerprint-checked public key, read-only token and no event
interpolation. ephoros: the job and uploaded report answer commit, plan,
terminal result and failure-class questions. metron: no optimisation claim.
elenchus: a workflow contract mutation must turn its test red. hypomnema:
ADR-055 and the workflow are the decision and operational homes.

## Step 3: Require the observed contexts on current main

### Scope and exit

**Goal.** Turn successful hosted evidence into the protected-branch gate.

**Entry.** The pull request's exact head has successful `invariants` and
`plugins` contexts, and the live ruleset has been read immediately before its
update.

**Exit.** Ruleset `21830871` requires exactly `invariants` and `plugins`, keeps
its existing enforcement and conditions, has strict required-status checking
enabled, and adds no bypass. An immediate readback matches those fields. The
signed pull-request head fast-forwards `main`, the pull request is merged, issue
#889 is closed, remote `main` equals the verified local commit, and the pull
request and issue both return HTTP 200 without credentials.

### Files and tests

**Files.** No repository file changes in this step. The ruleset is live GitHub
state.

**Tests.** Read the exact pull-request check rollup; read, update and read back
the full ruleset document; verify the signed commit locally and through the
GitHub commit API; compare remote and local main; and perform anonymous HTTP
visibility checks. Stop without merging if any required context, signature,
strictness field or ref differs.

### Discipline routing

**Disciplines.** phylax: the authenticated ruleset payload is built from a
fresh full read and preserves fields outside the authorised change. ephoros:
the hosted check rollup and post-write ruleset document are the receipts.
metron: none. elenchus: a missing context or false strictness value is a hard
stop. hypomnema: ADR-055 names why both contexts are required; live GitHub owns
the enforcement record.
