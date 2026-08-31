# Pull-request identity gate runbook

## Step 1: Build and test the base-owned identity policy

### Scope and exit

**Goal.** Reject known runtime-host attribution across every identity surface
without executing candidate code.

**Entry.** `main` equals the signed #891 head
`b3f7de8742f4e69a61a7ae969e23b73d728e9473`, and the study in this directory
is accepted.

**Exit.** `scripts/check_commit_identity.py` validates the pull-request login,
reads every commit in `base..head` from a non-shallow repository, and rejects a
known host author, committer, co-author, generated-by line, malformed identity,
or malformed Shoggoth provenance. Git config, replacement objects, command
time, command output, commit count, object size, and total bytes are bounded.
Focused tests cover each refusal, a human-authored commit, the authorised
Shoggoth-author/Laurence-publisher split, an offending middle commit, base
exclusion, malformed objects, and every ceiling.

### Files and tests

**Files.** `scripts/check_commit_identity.py`,
`tests/test_commit_identity.py`, this study and runbook, and ADR-058.

**Tests.** First show a fixture with `Claude <noreply@anthropic.com>` passes the
signed-only premise and fails the new identity predicate. Run the complete
focused module, the existing contributor and Fiat attribution modules, root
invariants, policy lints, and `git diff --check`.

### Discipline routing

**Disciplines.** phylax: hostile Git objects, path identity, fixed subprocesses,
and byte/time ceilings. ephoros: bounded JSON success and role-specific
refusals. metron: no performance claim. elenchus: one red fixture for every
accepted role and boundary. hypomnema: ADR-058 owns the repository decision;
the script owns mechanics.

## Step 2: Bootstrap the immutable hosted context

### Scope and exit

**Goal.** Publish one stable GitHub Actions job without giving candidate bytes
execution authority.

**Entry.** Step 1 is green and the branch is current with protected `main`.

**Exit.** `.github/workflows/identity.yml` runs unconditionally for pull
requests to `main`, has a job and status context named `identity`, read-only
contents permission, only commit-status write permission, no repository secret,
no cache, no persisted checkout credential, and a five-minute timeout. It marks
the validated event head pending before fallible work. It checks out the exact
base SHA as the workspace, fetches `main` and the decimal-validated pull ref
from the fixed public URL into a fresh bare repository, verifies the fetched
head, invokes only the base script, and publishes success only for a successful
evaluation step. Tests prove no candidate checkout, import, dependency, event
interpolation, or path filter exists. The signed pull request is hosted-green
for existing required checks and fast-forwards `main` without rewriting its
commits.

### Files and tests

**Files.** `.github/workflows/identity.yml` and its root contract tests.

**Tests.** Mutate each protected workflow clause and show the contract test
fails. Run the root suite, complete plugin graph, Promise Machine checks,
Protasis, Imprimatur, Vulgate comparison, Brevitas, Phylax, Ephoros,
Hypomnema, Horos, and local signature verification before push. Do not add
`identity` to a ruleset in this step.

### Discipline routing

**Disciplines.** phylax: base-owned execution, bare candidate objects,
read-only token, fixed remote and argv, and no untrusted interpolation.
ephoros: stable job name plus exact base, head, count and refusal logs. metron:
no claim. elenchus: workflow contract mutations. hypomnema: workflow procedure
and ADR-058.

## Step 3: Prove the exact-head context with a signed canary

### Scope and exit

**Goal.** Establish that the base-owned workflow publishes `identity` where the
required-check rule will look for it.

**Entry.** Step 2 is on `main`; the live required-check set is still
`invariants` and `plugins`.

**Exit.** A separate public canary pull request carries one machine-key-signed
Shoggoth-authored commit, uses `laurenceday` as publisher, and receives a green
`identity` status. The commit-status API names `identity`, the GitHub Actions
creator and integration `15368`, the linked workflow run, and the canary's exact
current head SHA. A deliberately forbidden local fixture remains red. The
canary may be closed unmerged after this evidence; its commit, status, and run
URL remain inspectable.

If the explicit status is absent from the exact head, comes from another
source, lacks the run link, or is not green, stop. Do not create the required
context or raise the review count; repair and re-review publication first.

### Files and tests

**Files.** No protected repository bytes are required. The canary branch may
carry a temporary documentation specimen that is never merged.

**Tests.** Query the pull request, exact head, combined status, context, creator,
integration ID, target run, workflow event, and anonymous visibility. Verify
the canary commit locally and through GitHub before its first push.

### Discipline routing

**Disciplines.** phylax: the base-owned token writes only commit statuses to the
validated event head. ephoros: exact status and run-URL receipt. metron: none.
elenchus: forbidden fixture stays red. hypomnema: external run and status
objects are the receipt.

## Step 4: Require identity and one independent approval

### Scope and exit

**Goal.** Make the observed identity check and a human review mandatory for
`main`.

**Entry.** Step 3 proves `identity` on the exact canary head. Fresh reads show
ruleset `21830871` still requires strict `invariants` and `plugins`, ruleset
`16257211` still requires zero approvals with no bypass, and signed-commit
rules remain active.

**Exit.** Ruleset `21830871` requires exactly `identity`, `invariants`, and
`plugins` from GitHub Actions integration `15368`, retains strict current-base
policy, its conditions and enforcement, and has no bypass. Ruleset
`16257211` requires one approving review while preserving signatures,
deletion, non-fast-forward, merge methods, unattributed-change handling, all
other pull-request fields, and no bypass. Immediate full readbacks match. Issue
#893 is closed only after both documents agree and all public objects return
anonymous HTTP 200.

### Files and tests

**Files.** No repository file change in this step.

**Tests.** Read, minimally transform, update, and read back each full ruleset.
Query current `main`, the bootstrap pull request, canary status, issue state,
signatures, and anonymous visibility. Any changed field outside the declared
contexts or approval count is a stop.

### Discipline routing

**Disciplines.** phylax: authenticated writes derive from fresh full reads and
preserve every unowned field. ephoros: post-write rule documents and public
objects. metron: none. elenchus: absent context, wrong integration, lost
strictness, wrong approval count, or bypass is red. hypomnema: ADR-058 explains
the choice; GitHub rulesets own enforcement.
