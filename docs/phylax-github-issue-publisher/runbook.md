# Runbook: recover App issue publication behind a checked credential boundary

Derived from the receipted Study for
[skills#925](https://github.com/wildcat-finance/skills/issues/925). The run
starts from `b9f8e36b8b6210bcd023a68059ecb46da3e35769` on `main`, on branch
`fiat/925-app-publisher-recovery-r3` in worktree
`issue/16777233-521053050`. Its run id is
`fiat-b60d07cc4253a2d353c03d01d2ceff569037bb0f1c228e51296dc8ce7f778152`.
The controller is `fiat-v5.54.1`; the host package is Hexaemeron `1.6.32`,
the checked-in package is `1.6.33`, and their Fiat controller bytes match.
R3 uses the checked-in `in-repo-source` route.

```version-relations
phylax | plugins/hexaemeron/skills/phylax/EVOLUTION.md | next-generation-after-integration-base
```

```design-lock
schema | protasis-design-evidence/v1
sha256 | d74fd663f1ec76d8169fe3bfa536749d3440127b3e00ec3bd2c6894ae0280587
candidate | isolated-publisher
```

## Evidence binding

The receipted R3 Study is
`45981759eb011b4c82515127b3124d792342ab03903e7a0a8c8f53fc50f78706`.
The design record above binds 20 selection reports; their commands bind
`.hexaemeron/design-topology.json` at
`bf373194c7c1dae82bfbe5e6ccdfeca612677b0d59d02c268bb675542fa66716`.
The issue-contract receipt is
`b8f27e1823a882af6be152c4e04f9df6e7ecc705f9e7ac971097610fb50164e0`.
The current Runbook directive is bound to controller state SHA-256
`056a05811cd1924d66ce21a07c09b039b13841789b14cc2bd5d44f395693e628`.

The R2 Runbook at
`/Users/c0rtexzer0/Documents/GitHub/skills-925/.hexaemeron/archive/20260912T223435Z-halted-app-publisher-recovery-r2/runbook.md`
is source evidence at
`d27b34dcdbfdc6ccc0b4e7faaea0ed6ebb953783343b0016fbd2e0ee753044b1`.
The preserved Step 1 patch is source evidence at
`cef0b4ad9f9f3a123b590f5c59da984e77cc749a68b33018882fd2cde5bafe1e`.
Neither transfers a receipt, base, version, signature, or delivery claim.

## Shared boundaries

The three steps build and test a repository prototype. They do not read or
move the live PEM, mint a live token, call GitHub with App authority, install a
service, change an OS account or group, retire the live helper, or claim live
isolation. Those are separate privileged transitions.

Shoggoth remains author. Dr Laurence E. Day is the authorised committer,
signer, and publisher, using `laurenceday` and `B83B60AE16F5DD1A`. Codex is
none of those. Every Fiat commit carries the required Shoggoth provenance
trailers and passes local and GitHub signature verification before a receipt.

The halted #925 refs, archives, and preserved patch are source material only.
A donor file enters the product only after reconciliation with this base and
current tests. Generated portable copies come from their owner; they are not
hand-edited. Decision record numbering waits for the integration composer.

The design evidence becomes due after its producing step:

- Step 1 writes `ordered-admission-chain`, `request-work-bound`, and
  `request-byte-bound`; they block Step 2.
- Step 2 writes `signer-and-post-boundary`; it blocks Step 3.
- Step 3 writes `public-route-and-deployment-check`; it blocks integration.

Every step uses the exact audit-repair runner `python3
plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}` with report
format `unittest-json-v1`, expected schema `elenchus.unittest.v1`, and fresh
report path `.hexaemeron/reports/conformance/fiat-925-r3-step-<N>.json`. The
runner source is
`3c83bfaa7f067f00f304eeac64867f4710846caa913d6ce14e6eca7024b5d63f`.
The `{report}` placeholder occurs exactly once. Ordinary broad runs use 12 workers.
Before each commit, activate the tracked gate with `git config core.hooksPath
.githooks`, refresh only the Horos files its deterministic commands require,
run `.githooks/greenlight` on the exact staged tree, and never bypass the gate.

## Step 1: Preserve the contract and enforce publication admission

**Goal.** Put the receipted design in its durable homes and build the closed
request and policy layer that refuses unchecked prose before signer or GitHub
access.

**Entry.** The clean controller-created Step 1 branch starts at exact base
`b9f8e36b8b6210bcd023a68059ecb46da3e35769`. The Study and design record have
the receipts and digests above. The design-lock transition receipt binds all
20 selection reports, whose commands bind the topology. The current `step:1`
design transition exits zero and consumes no conformance report. None of the
new publisher paths exists on the base. The donor patch applies under
`git apply --check`, but remains unapplied and untested.

**Exit.** Tracked Study, Runbook, design evidence, topology, and selection
reports are exact copies of their receipted or digest-bound run files under
`docs/phylax-github-issue-publisher/`. The selected decision is recorded at
`docs/decisions/drafts/use-a-credential-owning-github-issue-publisher.md` with
stable identity `adr/use-a-credential-owning-github-issue-publisher`, all five
Hypomnema sections, the rejected helper, watcher, and same-UID options, and the
live-deployment limit. The Study design bridge passes against that draft.

The normative Phylax reference defines canonical title and body encoding,
request and judgement-record schemas, queue rules, protected inventory,
ordered digest joins, fixed limits, refusal codes, and evidence boundaries. A
standard-library parser rejects duplicate or unknown fields, invalid UTF-8 or
NFC, controls, excessive depth, count, and bytes, wrong queue structure,
missing or mismatched records, and mutated stages. It executes the pinned
Imprimatur checker over the Sapheneia and final candidates. Every refusal
records zero signer and POST attempts. No module added in this step can mint,
sign, open the PEM, send HTTP, or publish.

The exact public #855 title and body are a digest-pinned regression fixture and
refuse before authority. A clean synthetic request passes admission. The CLI
emits closed reports for the selected candidate: `ordered-admission-chain` is
`true`; `request-work-bound` is at most 256 operations; and
`request-byte-bound` is at most 1,048,576 bytes. Each is a zero-exit
`protasis-design-report/v1` at the path fixed by the design record, ready for
the `step:2` transition.

**Files.** Create the durable directory
`docs/phylax-github-issue-publisher/`, including `study.md`, `runbook.md`,
`design-evidence.json`, `design-topology.json`, and
`design-reports/*.json`; create the decision draft, normative Phylax
reference, `github_issue_publisher.py`, and
`github_issue_publisher_lib/{__init__,canonical,errors,policy}.py`; create the
version-1 request, queue, rejection, and #855 fixtures and
`plugins/hexaemeron/tests/test_phylax_github_issue_publisher.py`. Synchronise
only matching generated portable-runtime files. Update `.horos/boundary.json`,
`.horos/candidates.json`, and `.horos/census.json` only when their generators
require it. The configured Fiat audit record and synopsis are audit-phase
outputs, not Mason edits.

**Tests.** Add golden canonical request and candidate cases; the exact #855
refusal; duplicate, unknown, null, boolean-as-integer, floating, negative,
oversized, excessive-depth, invalid-UTF-8, non-NFC, and control-bearing input;
all four queue forms and their title, opening, label, and inventory refusals;
missing, duplicate, reordered, failed, wrong-version, wrong-subject, wrong-
digest, and mutated-stage records; Sapheneia and Vulgate judgement limits;
both in-service Imprimatur results; and zero signer and POST attempts for every
refusal. Preserve the first genuine parent-red result for each implemented
cause. The focused suite, 12-worker Hexaemeron suite, root suite, Promise
Machine checks, Protasis checks, Hypomnema study bridge, Phylax and Ephoros
lints, Horos check, Imprimatur, and `python3 scripts/run_checks.py` all exit
zero on the finished tree.

**Disciplines.** phylax: parse and cap every untrusted byte before use, keep
fields closed, recompute every subject, and expose no credential capability.
ephoros: refusal output contains only fixed codes, digests, versions, and
attempt counts. metron: the work and byte ceilings are safety limits, not a
speed claim. elenchus: each observed rejection is retained as a cause-level
guard. hypomnema: the draft holds the topology choice, the reference holds the
wire contract, and the tracked Study and Runbook remain specifications rather
than a second decision home.

## Step 2: Cross the signer and GitHub boundaries once

**Goal.** Put signing, token exchange, one issue POST, exact readback, and
terminal cleanup behind the admitted request without returning credential
authority to the caller.

**Entry.** The controller-created Step 2 branch starts at the signed Step 1
head. Step 1's three selected-candidate reports pass the receipted `step:2`
transition. The admission library, fixtures, decision draft, reference, and
tracked design records pass every Step 1 exit check.

**Exit.** The runtime keeps one immutable UTF-8 title and body pair from final
Imprimatur through one POST. It invokes the signer only after admission. The
production signer uses fixed `openssl` arguments and a service-owned PEM path,
sends non-secret JWT signing input on stdin, caps time and output, and returns
no raw error. Standard-library HTTPS fixes GitHub host, repository, API
version, App and installation ids, route, method, TLS validation, redirect
refusal, response limits, deadline, and `issues:write` scope. JWT and
installation token headers stay inside the service process.

A bounded length-prefixed Unix-socket server reads one closed request and
returns one closed result. Its client imports no signer or transport code and
offers no token-only, PEM, endpoint, or raw HTTP operation. A confirmed create
is never retried. An ambiguous create returns `create-indeterminate` with a
request digest for operator reconciliation. Authenticated and anonymous
readback must identify the returned issue and match exact title and body bytes
before `published`. Every terminal route closes responses and clears
credential references without claiming process-memory erasure.

The CLI emits a zero-exit `protasis-design-report/v1` for
`signer-and-post-boundary` with boolean value `true` at its fixed path, ready
for the `step:3` transition. Focused tests, the 12-worker Hexaemeron suite,
root suite, selected repository checks, Phylax and Ephoros lints, Hypomnema,
and `git diff --check` exit zero.

**Files.** Add
`github_issue_publisher_lib/{framing,signer,transport,receipts,runtime,server,client}.py`;
change the CLI, policy, normative reference, focused tests, and version-1
fixtures. Synchronise the matching portable-runtime sources. Update only
deterministically required Horos data and the configured audit outputs owned by
their later phases. No root instruction, skill ledger, plugin version, live
helper, service account, group, key, socket, or daemon is changed in this step.

**Tests.** Cover fragmented, concatenated, short, oversized, and trailing
frames; peer-policy and socket-path refusal; signer access only after
admission; fixed arguments, stdin, timeout, overflow, non-zero exit, malformed
signature, and sanitised errors; exact narrowed token request; missing,
malformed, expired, redirected, wrong-origin, wrong-status, duplicate-field,
and oversized responses; exact issue POST mapping; mutation after final check;
one create attempt; deadline boundaries; confirmed and indeterminate outcomes;
authenticated and anonymous readback mismatch; receipt and cleanup failures;
and canary absence from output, arguments, environment, files, diagnostics,
receipts, and retained events. Use injected clocks, signer, transport,
filesystem, and peer identity. Make no live network call and read no real PEM.

**Disciplines.** phylax: socket, peer, subprocess, PEM path, token, TLS,
response, receipt, and cleanup are separate boundaries with fixed failures.
ephoros: one correlation digest joins fixed admission, signer, transport,
readback, and cleanup events without content or credentials. metron: time and
byte caps are safety controls, with no optimisation claim. elenchus: every
signer, transport, timing, readback, receipt, and cleanup failure becomes a
parent-red and fixed-green guard. hypomnema: runtime semantics extend the one
decision draft and normative reference; no new ADR or live-deployment claim is
created.

## Step 3: Close hostile conformance and publish the deployment contract

**Goal.** Bind the complete component to one hostile offline manifest, ship a
distinct-identity macOS deployment kit and verifier, and make the checked
service the repository's documented App issue route without claiming it is
installed.

**Entry.** The controller-created Step 3 branch starts at the signed Step 2
head. The selected `signer-and-post-boundary` report passes the receipted
`step:3` transition. Admission, signer, transport, framing, server, client,
readback, receipt, and cleanup tests satisfy the Step 2 exit with injected
dependencies only.

**Exit.** A digest-bound conformance manifest runs one positive case and a
closed hostile case for every Study risk id, including exact #855 refusal. Its
content-free result reports case counts, zero unexpected outcomes, zero #855
signer and POST attempts, exact-byte positive POST and readback, no credential
surface hit, complete observed component cleanup, deployment-kit status, and
`live_isolation: not-established`.

The macOS kit fixes service user and group, socket, program, working, and key
paths plus resource limits. A credential-free client shim contains no mint or
token output. `check-deployment` verifies bounded regular files, distinct
service and caller identities, owner, group, and mode predicates, exact
program digest, and absence of a sourceable or token-only helper and any
agent-readable key path. It emits safe predicates only and never creates,
moves, changes, deletes, boots, or publishes anything.

Root `AGENTS.md` preserves the prose sequence and routes App issue creation
through the checked service, refusing when deployment evidence is absent. The
Phylax contract declares the publisher promise and its judgement, root,
administrator, and live-deployment limits. Its evolution ledger records one
next generation against the integration base while retaining the mature
frontier. Portable runtime, Promise Machine coverage, plugin metadata, version
tests, audit synopsis, and Horos data agree with their canonical sources.

The CLI emits a zero-exit `protasis-design-report/v1` for
`public-route-and-deployment-check` with boolean value `true` at its fixed path.
The exact design record passes `integration`; the decision-assignment planner
maps the stable draft only at composition; and `python3 scripts/run_checks.py`
passes on the complete product. Live service installation and live isolation
remain unestablished and unclaimed.

**Files.** Add
`github_issue_publisher_lib/{conformance,deployment}.py`, a closed manifest and
deployment fixtures, and
`plugins/hexaemeron/skills/phylax/deployment/macos/` containing the daemon
template and credential-free client shim. Change `AGENTS.md`, the Phylax
reference, `SKILL.md`, `EVOLUTION.md`, CLI, tests, Promise Machine coverage,
Hexaemeron plugin metadata and README, version tests, and marketplace records
only where current generators and contracts require them. Synchronise the
portable runtime. Include deterministic Horos outputs and the Fiat-owned audit
record and synopsis produced by their phases. Do not alter the live helper,
PEM, accounts, groups, service manager, App permissions, or GitHub issues.

**Tests.** Require one positive manifest row and hostile rows for every risk:
#855, same UID, readable PEM, wrong identity, group, mode, socket, daemon,
program digest, or helper; malformed queue or record; Imprimatur failure;
early signer use; token, destination, retry, readback, receipt, cleanup, and
credential-surface faults; donor drift; stale receipt; signer confusion; ADR
collision; and administrator bypass limits. Mutate each deployment predicate
and prove refusal without host mutation. Scan client and public CLI surfaces
for signer, PEM, JWT, installation-token, token-only, arbitrary-URL, raw-HTTP,
and shell-source capabilities. Assert App absence from `HOST_PR_LOGINS`,
stable decision identity, version relation, package parity, portable parity,
Promise Machine consequence, and component-versus-live claim separation.
Run focused tests, 12-worker Hexaemeron suite, root suite, portable and Promise
Machine checks, all selected tree lints, audit synopsis check, Horos check,
Imprimatur, `python3 scripts/run_checks.py`, and `git diff --check` to exit zero.

**Disciplines.** phylax: deployment is a separate trust transition and the
verifier proves only named identity, path, ownership, mode, helper, and program
predicates. ephoros: manifest and verifier output fixed case ids, safe
predicate names, short digests, counts, and explicit component, kit, and live
states. metron: conformance duration is observation only. elenchus: each
manifest row and deployment mutation is a cause-level specimen retained after
the guard lands. hypomnema: the draft keeps the topology reason, the Phylax
reference keeps the interface, deployment files keep operator actions, and
fixtures keep negative evidence.
