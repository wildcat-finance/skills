# Runbook: gate Fiat effects and append checkpoint-bound audit loops

Derived from the receipted study at SHA-256
`836704800c9f03f9562b11c5e78b55702af6bd28c956e23a1dd7a339a08ca8b1`.
The record below fixes the selected design. No step may replace the append-only
loop layout, weaken the preimage-to-grant join, or move either conformance stop.

```design-lock
schema | protasis-design-evidence/v1
sha256 | afd5ff486f16aaab2799f8331e5b4efdeb3a3ec8c8d47ceb536a5e3a4115ca40
candidate | append-only-loop-kernel
```

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
```

The relation records that the new Promise, audit state, effect registry, and
operator interface are one Fiat generation after the eventual integration
base. No step predicts that version from this branch.

Across all steps, an audit fix uses the source-bound Elenchus command in that
step's `Tests` field. A report path must be fresh and remain inside the
worktree. Each step also runs the repository's affected check graph from the
repository root under the pinned Python and Node versions. A pre-existing red
check stops the step unless it is reproduced on the exact entry commit and
recorded through the runbook amendment process; it is never silently treated
as green.

## Step 1: Record the architecture and scaffold the delivery

**Goal.** Commit the receipted study, this runbook, and the standing ADR before
any controller behavior changes, while confirming that the repository's
existing layout, toolchain pins, CI check graph, and licence are the required
scaffold.

**Entry.** The clean Step 1 branch from the controller-recorded run base, with
the study receipt and immutable design record matching the two hashes above.

**Exit.** `docs/fiat-transition-gate-study.md` is byte-identical to
`.hexaemeron/study.md`; `docs/fiat-transition-gate-runbook.md` is byte-identical
to `.hexaemeron/runbook.md`; and
`docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md`
records `append-only-loop-kernel`, the two rejected candidates, the
write-ahead recovery trade, and the same-account limitation. The ADR is the
one home named by the study's design bridge. `.python-version`,
`pyproject.toml`, `LICENSE`, and `tests/check-map-v1.json` remain the scaffold;
the step adds no competing toolchain, licence, or CI entrypoint.

Run all of these successfully:

```bash
cmp -s .hexaemeron/study.md docs/fiat-transition-gate-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-transition-gate-runbook.md
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-transition-gate-study.md
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-transition-gate-runbook.md
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study docs/fiat-transition-gate-study.md --design-evidence .hexaemeron/design-evidence.json --repo-root .
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-transition-gate-study.md docs/fiat-transition-gate-runbook.md docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md
mise exec python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py
```

**Files.** `docs/fiat-transition-gate-study.md`,
`docs/fiat-transition-gate-runbook.md`, and
`docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md`.

**Tests.** No new behavior test. Existing decision-record, Protasis,
Hypomnema, Imprimatur, root, and Hexaemeron checks must remain green. The
source-bound audit-fix command is
`mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`.
Report format `elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-1.json`.

**Disciplines.** phylax: none, this step adds only repository prose and opens
no executable boundary. ephoros: none, no path runs unattended. metron: none,
there is no performance claim. elenchus: none, no implementation failure is in
hand. hypomnema: this step creates ADR-069, the single standing home for the
selected architecture and its rejected alternatives.

## Step 2: Append loop 2 through the checkpoint-bound Promise

**Goal.** Deliver the earliest usable safe continuation slice: one separate
Promise and guarded command that turns a verified exhausted-loop checkpoint
into loop 2 round 1 on the same ledger without changing loop 1.

**Entry.** Step 1's pushed head, the unchanged version-1 Fiat state contract,
and the design record's `checkpoint-loop-conformance` cell still pending for
`step:3`.

**Exit.** The canonical Fiat contract declares
`fiat-checkpoint-audit-loop-continuation`; `transition_gate.py` is a pure,
standard-library decision engine over closed typed values; and `hexctl
start-audit-loop --checkpoint <capsule-directory> --manifest-sha256 <sha256>
--authority-file <bounded-utf8-file> --max-rounds <1..8>` is the sole command
that Promise authorises. The command accepts only an active `audit-verdict`
whose current loop is exhausted with findings, verifies either the exact
checkpoint preimage or its unique controller-receipted restore lineage, proves
the current worktree and Git state, derives every carryover finding id and the
unresolved-leads digest from the checked final audit suffix, and records the
authority statement without claiming who authored it.

Legacy `steps[*].audit.rounds` remains the physical loop-1 list. Later loops
append as closed `audit.continuations` objects with one immutable maximum from
1 through 8, predecessor and checkpoint digests, authority, carryover, and a
new append-only rounds list. Audit schema v3, state validation, `next`,
`status`, checkpoint identity, last-commit lookup, audit-log offsets, and the
Warden brief all carry explicit loop and local-round identities. The existing
`new` or `same-agent` continuity field remains truthful across the loop
boundary. No accepted state, directive, receipt, log heading, filename, or
brief can encode round 9.

The state and ledger writer stages exact postimage files, the grant, and a
closed manifest in a private transaction directory. It publishes and fsyncs a
pending marker before replacing either live file. Every injected interruption
leaves exact preimage, exact postimage, or one named mixed window that the
staged bytes can complete. Ordinary transitions refuse while that marker is
present.

The exact #622 43-entry input is admitted only if its preserved bytes prove the
state and sidecar identities recorded by issue #871. If those bytes cannot be
recovered, the step stops and reports that blocker. A synthetic exhausted-loop
fixture is kept under a different identity for general positive, lower-limit,
relocation, and crash tests. It may not substitute for the incident fixture.

The Step 2 verifier writes the exact pending report:

```bash
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py conformance --case checkpoint-loop --candidate append-only-loop-kernel --report .hexaemeron/design-reports/append-only-loop-kernel--checkpoint-loop-conformance.json
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_audit_loop_continuation.py --elenchus-report .hexaemeron/test-reports/step-2-focused.json
mise exec python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py
```

The report is one closed `protasis-design-report/v1` object with candidate
`append-only-loop-kernel`, criterion `checkpoint-loop-conformance`, boolean
value `true`, unit `boolean`, the exact verifier command, and exit 0. A report
is not written on a skipped, synthetic-only, partial, or failing run.

**Files.** `plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/scripts/transition_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/references/audit-loop.md`,
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`,
`plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md`,
`plugins/hexaemeron/tests/test_transition_gate.py`,
`plugins/hexaemeron/tests/test_audit_loop_continuation.py`,
`plugins/hexaemeron/tests/fixtures/transition-gate-v1/`,
`tests/promise_machine_coverage.json`,
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`tests/fixtures/agent-instruction-v1/`, `tests/check-map-v1.json`, and
`.horos/boundary.json`. The exact report is
`.hexaemeron/design-reports/append-only-loop-kernel--checkpoint-loop-conformance.json`;
it is run evidence, not a product file.

**Tests.** Add a pure-gate module and a focused continuation module with 24 to
40 tests. Cover closed schemas, unknown Promise and command ids, stale state,
ledger, directive, controller, checkpoint, restore, ref and worktree evidence,
maxima 1 and 8, values outside that range, incomplete findings, duplicate ids,
changed leads, dirty work, pending transactions, exact #622 config and resume
refusals with byte equality, synthetic positive continuation, loop-1 canonical
and log-prefix equality, loop-local numbering, Warden brief continuity, and
each transaction interruption. The focused module implements the repository's
fresh Elenchus reporter. Command:
`mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_audit_loop_continuation.py --elenchus-report {report}`.
Report format `elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-2.json`.

**Disciplines.** phylax: checkpoint, state, ledger, audit-log, authority-file,
path, Git, and transaction bytes are hostile boundaries and receive no-follow,
cap, shape, containment, and fixed-argv controls. ephoros: grant, refusal, and
transaction records answer which Promise acted and where recovery stopped;
there are no metrics or alerts. metron: none, complete bounded postimage
staging is a recovery choice and carries no speed claim. elenchus: #622 is the
observed failure, and every refusal and crash boundary needs a parent-red guard
before a fix is receipted. hypomnema: the new Promise, state union, audit v3
shape, and command failures are documented beside their interfaces and point
back to ADR-069.

## Step 3: Gate every Fiat effect and close the legacy escape routes

**Goal.** Replace the name-based `MUTATING` allowlist and direct writer calls
with one discoverable effect registry, one verified dispatcher, and a guarded
writer API for every current Fiat effect.

**Entry.** Step 2's pushed head. Before the controller opens this step, the
immutable design checker consumes the successful
`checkpoint-loop-conformance` report at `step:3`; absence, false value, wrong
identity, or digest drift blocks entry.

**Exit.** Every parsed command is classified as read, projection, state-ledger
transition, or lifecycle effect. The registry binds each effect to its stable
Promise, consequence, evidence builder, gate rule, hostile specimen, and sole
writer API. `init` uses a proved-absence genesis preimage. Ordinary mutators
use the Step 2 write-ahead transaction. `next --brief-out`, checkpoint export,
checkpoint restore, reset, archive, breadcrumb, worktree, ref, and other
derived or lifecycle writes have separate exact grants and recovery rules.
`config get` is read-only. `config set` admits only named leaves in named
phases; whole `git` or `audit` replacement refuses; `audit.max_rounds` may be
set only before the first audit receipt and only from 1 through 8; and no
active or completed loop ceiling can change.

A new halt records the pre-halt directive and whether one exact resume is
allowed. `resume` accepts only that stored grant and cannot clear an exhausted
`audit-verdict` halt. Legacy halts without such evidence name checkpoint
restore as recovery. Every handler that can reach a filesystem, Git, state,
ledger, subprocess, or publication-capable write is discovered from parser
registration and a conservative call graph. A new effectful handler with no
mapping, negative specimen, or guarded writer path makes verification and CI
fail. The dispatcher holds the run lock from stable preimage capture through
postimage verification, and it rechecks the grant against the still-current
preimage immediately before the writer consumes it.

Run all of these successfully:

```bash
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py conformance --case effect-registry
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_transition_gate_dispatch.py --elenchus-report .hexaemeron/test-reports/step-3-focused.json
mise exec python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/transition_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`,
`plugins/hexaemeron/tests/test_transition_gate_dispatch.py`,
`plugins/hexaemeron/tests/test_fiat_config_write_gate.py`,
`plugins/hexaemeron/tests/test_hexctl.py`, the checkpoint, restore, audit-log,
and delegation test modules selected by the affected runner,
`tests/promise_machine_coverage.json`,
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`tests/fixtures/agent-instruction-v1/`, `tests/check-map-v1.json`, and
`.horos/boundary.json`.

**Tests.** Add 28 to 44 focused cases plus updates to every existing effect
fixture. Enumerate every parser handler, direct and indirect writer primitive,
registry row, Promise mapping, hostile specimen, and source-order constraint.
Exercise all existing valid study, runbook, implement, audit, prose, push,
merge, halt, approved resume, checkpoint, restore, done, and reset paths. Add
byte-equality refusals for wrong directives and config shape or phase; two
writer contention; grant replay; grant swap; output path replacement; and a
new unregistered writer specimen that makes discovery fail. Command:
`mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_transition_gate_dispatch.py --elenchus-report {report}`.
Report format `elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-3.json`.

**Disciplines.** phylax: this is the central hostile-input, filesystem, Git,
subprocess, and model-output authority boundary; closed typed data and fixed
argument lists are mandatory. ephoros: structured grant and refusal fields
must correlate every effect with its ledger or external receipt; no alert is
added to this interactive tool. metron: none, no throughput or latency claim.
elenchus: the legacy max-rounds and resume path is the incident mechanism, so
the old behavior must fail under the new guards and the complete valid fixture
set must remain green. hypomnema: the registry and resume rules are public
interfaces whose reason stays in ADR-069 and the Fiat references.

## Step 4: Generate checkpoint handovers from verified controller evidence

**Goal.** Replace hand-written continuation instructions with one checked JSON
handover and a human paste block rendered only from that JSON.

**Entry.** Step 3's pushed head, with every controller effect classified and
the checkpoint-bound continuation already available through the guarded
dispatcher.

**Exit.** `handover.py` reads a checkpoint and sidecar through bounded
descriptor-based no-follow operations, verifies them with the installed
controller and gate, and emits one closed JSON envelope. The envelope binds
repository, active and source worktree identities, controller version and
digest, checkpoint and sidecar digests, state fingerprint, ledger count and
tail, exact `verify`, `status`, and `next` commands, current directive,
Promise, consequence, permitted transition if one exists, finding carryover,
unresolved recovery, and the grant digest. The human paste block is a pure
rendering of the accepted object and has no separately supplied fields.

An unsupported controller, wrong checkpoint, changed sidecar, symlink, special
file, cap breach, unverified restore lineage, absent Promise, manually supplied
new-loop command, widened maximum, or any round-9 representation refuses. A
fresh disposable operator can restore the synthetic checkpoint, run the three
read-only commands exactly, reproduce the envelope's state digest and
directive, and cannot advance with a command absent from the envelope.

Run all of these successfully:

```bash
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py conformance --case handover
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_fiat_handover.py --elenchus-report .hexaemeron/test-reports/step-4-focused.json
mise exec python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/handover.py`,
`plugins/hexaemeron/skills/fiat/scripts/transition_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py`,
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`,
`plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md`,
`plugins/hexaemeron/tests/test_fiat_handover.py`,
`plugins/hexaemeron/tests/fixtures/transition-gate-v1/`,
`tests/check-map-v1.json`, and `.horos/boundary.json`.

**Tests.** Add 16 to 24 tests for closed schema, duplicate and unknown fields,
no-follow reads, file and JSON caps, changed-during-read inputs, exact command
rendering, JSON-to-text parity, absent transition, active transition, inherited
findings and leads, relocation, stale controller and gate, unsupported manual
handover, round 9, fresh restore, and read-only replay. Command:
`mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_fiat_handover.py --elenchus-report {report}`.
Report format `elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-4.json`.

**Disciplines.** phylax: checkpoint, sidecar, path, JSON, and rendered model
context are untrusted inputs, so stable bounded reads and a closed envelope
precede rendering. ephoros: the handover is the retained answer to what state,
Promise, and recovery a successor received; its correlation is the grant and
checkpoint identity. metron: none, no performance claim. elenchus: every
unsupported recipe and changed-input case is a refusal guard, while fresh
restore proves the supported path. hypomnema: the handover schema and failure
modes are documented beside the script and linked from the checkpoint
reference.

## Step 5: Protect the installed enforcement path

**Goal.** Make the checked execution path verify its gate, controller,
manifest, call order, tests, and workflow references before any Fiat writer can
run.

**Entry.** Step 4's pushed head, with the pure gate, complete effect registry,
transaction writer, continuation, and handover behavior present but not yet
claimed as privilege isolation.

**Exit.** `verify_transition_gate.py` checks the gate, controller, handover,
publication entrypoint reservation, transaction code, manifest, launcher,
required tests, and workflow references as ordinary no-follow files under
explicit caps. It checks executable bits where required, exact SHA-256 pins,
the complete parser-handler and writer inventory, and source order from
integrity check through preimage verification and Promise decision to writer.
`transition-gate-manifest.json` is closed and pins every governed component.
`run-fiat-guarded.sh` uses `set -eu`, invokes integrity verification first,
and exits before `hexctl` on any failure.

The canonical Fiat contract states the bootstrap boundary: this run installs
and pins the first gate but cannot claim the gate governed its own creation.
After integration, a delivery governed by the gate may not alter, rename,
delete, disable, repin, or bypass the gate, verifier, launcher, manifest,
required call sites, or integrity tests. A gate upgrade is a separate
human-maintainer change with a new controller and manifest digest. The claim
remains tamper evidence in the checked path, not protection from a process with
the same account and write authority.

Run all of these successfully:

```bash
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py verify
sh -n plugins/hexaemeron/skills/fiat/scripts/run-fiat-guarded.sh
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_transition_gate_integrity.py --elenchus-report .hexaemeron/test-reports/step-5-focused.json
mise exec python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/transition-gate-manifest.json`,
`plugins/hexaemeron/skills/fiat/scripts/run-fiat-guarded.sh`,
`plugins/hexaemeron/skills/fiat/scripts/transition_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/scripts/handover.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/references/transition-gate.md`,
`plugins/hexaemeron/tests/test_transition_gate_integrity.py`,
`tests/promise_machine_coverage.json`,
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`tests/fixtures/agent-instruction-v1/`, `tests/check-map-v1.json`, and
`.horos/boundary.json`.

**Tests.** Add 20 to 32 tests for modified, missing, renamed, symlinked,
hard-linked, oversized, non-executable, unpinned, stale, reordered, and
unreferenced components; a missing hostile specimen; a new parser mutator; a
direct writer call; launcher failure propagation; verification-first source
order; manifest duplicate keys and path traversal; and one clean installed
path. Each hostile case proves that the writer was not invoked. Command:
`mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_transition_gate_integrity.py --elenchus-report {report}`.
Report format `elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-5.json`.

**Disciplines.** phylax: integrity files, modes, paths, digests, the shell
launcher, and spawned controller argv form the boundary; regular-file checks,
caps, fixed argv, and fail-hard ordering control it. ephoros: verification
prints one bounded structured component inventory and stable refusal code;
there is no alert. metron: none, digest work has no performance target.
elenchus: every hostile integrity mutation must reproduce a bypass on the
unfixed parent or be labelled a conformance specimen rather than a historical
failure. hypomnema: the bootstrap and same-account limits are expensive trust
decisions recorded in ADR-069 and the new transition-gate reference.

## Step 6: Bind published mutation recipes to the same grant

**Goal.** Refuse an ADR, handover, issue comment, or pull-request body that
teaches a live Fiat mutation unsupported by the named fixture and installed
gate before any allowed GitHub command starts.

**Entry.** Step 5's pushed head, with the integrity verifier and guarded
launcher complete and the publication entrypoint still absent.

**Exit.** `publication_gate.py` reads one bounded regular body file, extracts
only the documented controller-command grammar outside quoted specimens,
classifies each command as read-only or effectful, and evaluates every
effectful command against one named verified fixture through the installed
transition gate. It emits a closed receipt binding repository and action,
target number where applicable, body digest, fixture state and ledger
identities, accepted command set, and grant digests. The human text is not
treated as evidence beyond those commands.

The executable wrapper admits exactly `gh issue create`, `gh issue comment`,
`gh pr create`, and `gh pr edit` through fixed argument lists. Unknown GitHub
actions, inline body strings, shell syntax, command substitutions, unsafe
paths, missing fixtures, manual handover fields, changed body bytes, widened
maxima, generic exhausted-loop resume, and controller-unsupported continuation
recipes refuse before the injected or real `gh` runner is called. Tests use a
recording fake and make no network request. Manual GitHub use remains outside
the claim, as the study states.

Run all of these successfully:

```bash
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py conformance --case publication
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_transition_publication.py --elenchus-report .hexaemeron/test-reports/step-6-focused.json
mise exec python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/publication_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/transition-gate-manifest.json`,
`plugins/hexaemeron/skills/fiat/scripts/run-fiat-guarded.sh`,
`plugins/hexaemeron/skills/fiat/references/transition-publication.md`,
`plugins/hexaemeron/tests/test_transition_publication.py`,
`plugins/hexaemeron/tests/fixtures/transition-gate-v1/publication/`,
`tests/check-map-v1.json`, and `.horos/boundary.json`.

**Tests.** Add 16 to 24 tests across the four admitted GitHub actions, read-only
commands, one valid loop continuation, each unsupported recipe from #871,
quoted examples, fenced decoys, duplicate and unclosed structures, changed
body and fixture bytes, path and size boundaries, fake-runner call counts, and
clean receipt replay. The focused module implements the fresh reporter.
Command:
`mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_transition_publication.py --elenchus-report {report}`.
Report format `elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-6.json`.

**Disciplines.** phylax: repository prose, fixture bytes, paths, model output,
and GitHub argv cross the trust boundary; bounded parsing, closed actions, and
fixed argument lists keep them data. ephoros: the publication receipt answers
which body, fixture, commands, and grants reached the runner; no operational
alert is added. metron: none, no latency or throughput claim. elenchus: every
unsupported recipe must leave the fake runner at zero calls, and fixes need a
parent-red guard. hypomnema: the publication interface and its limited claim
live in the transition-publication reference and point to ADR-069.

## Step 7: Demonstrate the complete hostile and recovery path

**Goal.** Run all ten #871 acceptance families as one disposable end-to-end
proof, reconcile the public Fiat contract and generated identities, and emit
the full-acceptance report that integration must consume.

**Entry.** Step 6's pushed head, with all product capabilities present and the
design record's `full-acceptance-conformance` cell still pending for
integration.

**Exit.** One bounded acceptance driver executes the ten numbered issue cases:
the exact #622 max-round and generic-resume refusals; stale, forged, changed,
missing, and widened grant evidence; unsupported and round-9 handovers; every
integrity mutation; every transaction crash boundary; all existing valid
controller transitions; synthetic exhausted-loop continuation to loop 2 round
1 with loop 1 and its log prefix byte-identical; fresh restore and handover
replay; and complete mutator discovery. It also runs the publication wrapper
with a recording fake and proves zero calls on every refused recipe. No case
uses or opens #1155 evidence.

The final public contract names the separate Promise, loop-local maximum,
legacy loop-1 rule, grant and refusal evidence, transaction recovery,
handover, integrity bootstrap, publication boundary, and same-account limit.
ADR-069 is accepted. The Fiat ledger receives one new generation row without
rewriting its prior frontier, and the governed skill version, compatible
checkpoint-version set, evolution pins, Promise coverage map, controller
digest fixtures, agent-instruction corpus, both plugin manifests, both root
marketplace manifests, portable Promise Machine output, audit synopsis view,
check map, and Horos boundary are reconciled wherever the changed bytes require
it. The held frontier job remains unchanged unless this issue is itself its
declared owner.

Run the sealed resolver and integration check exactly:

```bash
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py conformance --case full-acceptance --candidate append-only-loop-kernel --report .hexaemeron/design-reports/append-only-loop-kernel--full-acceptance-conformance.json
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition integration
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_transition_gate_acceptance.py --elenchus-report .hexaemeron/test-reports/step-7-focused.json
mise exec python@3.14.6 node@26.6.0 -- python3 scripts/portable_promise_machine.py check
mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
mise exec python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py
```

The design report is a closed `protasis-design-report/v1` object with candidate
`append-only-loop-kernel`, criterion `full-acceptance-conformance`, boolean
value `true`, unit `boolean`, the exact resolver command, and exit 0. The
verifier withholds it if the exact incident fixture is absent, any acceptance
family skips or fails, any expected hostile row is absent or reordered, the
existing valid-transition inventory is incomplete, or a required repository
check is red. The last demo starts from a disposable exhausted checkpoint and
finishes at a verified loop 2 round 1 directive; it does not deploy into a
live run.

**Files.** `plugins/hexaemeron/tests/test_transition_gate_acceptance.py`,
`plugins/hexaemeron/tests/fixtures/transition-gate-v1/manifest.json`,
`plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/transition-gate-manifest.json`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/references/audit-loop.md`,
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`,
`plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md`,
`plugins/hexaemeron/skills/fiat/references/transition-gate.md`,
`plugins/hexaemeron/skills/fiat/references/transition-publication.md`,
`docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md`,
`tests/promise_machine_coverage.json`,
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`tests/test_evolution_contract.py`, `tests/fixtures/agent-instruction-v1/`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/check-map-v1.json`, `.horos/boundary.json`, and any verified synopsis
whose authoritative audit source changes. The conformance report at
`.hexaemeron/design-reports/append-only-loop-kernel--full-acceptance-conformance.json`
is run evidence and is not copied into product source.

**Tests.** Add exactly ten top-level acceptance families corresponding to the
numbered issue contract, with bounded subtests for each hostile variant. The
module refuses a zero-test, skipped, synthetic-only, stale, malformed,
oversized, duplicated, missing, reordered, or partly executed manifest and
implements the fresh reporter. Command:
`mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/test_transition_gate_acceptance.py --elenchus-report {report}`.
Report format `elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-7.json`.

**Disciplines.** phylax: the final proof composes every hostile local input,
filesystem, subprocess, model-prose, fixture, and fake-publication boundary and
must keep all runners fixed-argv and offline. ephoros: the acceptance manifest
correlates every expected row to its grant, refusal, transaction, handover, or
publication receipt and refuses missing rows; no alert is warranted. metron:
none, the suite records completeness and correctness rather than speed.
elenchus: the end-to-end case must fail without the causal changes in Steps 2
through 6 and pass only on their combined tree. hypomnema: this step accepts
ADR-069, updates the canonical contract and references, and records the new
Fiat generation in its established ledger.

### Amendment -- 2026-09-03

**What changed.** Complete replacement Exit: `docs/fiat-transition-gate-study.md` preserves every receipted study byte except seven deterministic link-prefix rebases required by its tracked location: the two occurrences of `../../../docs/` become `../docs/`, and the five occurrences of `../../../plugins/` become `../plugins/`. `docs/fiat-transition-gate-runbook.md` is byte-identical to the amended `.hexaemeron/runbook.md`; and `docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md` records `append-only-loop-kernel`, the two rejected candidates, the write-ahead recovery trade, and the same-account limitation. The ADR is the one home named by the study's design bridge. `.python-version`, `pyproject.toml`, `LICENSE`, and `tests/check-map-v1.json` remain the scaffold; the step adds no competing toolchain, licence, or CI entrypoint. Run every command in the complete replacement Tests successfully. Complete replacement Files: `docs/fiat-transition-gate-study.md`, `docs/fiat-transition-gate-runbook.md`, and `docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md`. Complete replacement Tests: No new behavior test. Verify the published study's exact seven link-prefix rebases with `mise exec python@3.14.6 node@26.6.0 -- python3 -c 'from pathlib import Path; source = Path(".hexaemeron/study.md").read_bytes(); candidate = Path("docs/fiat-transition-gate-study.md").read_bytes(); assert source.count(b"../../../docs/") == 2; assert source.count(b"../../../plugins/") == 5; expected = source.replace(b"../../../docs/", b"../docs/").replace(b"../../../plugins/", b"../plugins/"); assert candidate == expected'`. Run `cmp -s .hexaemeron/runbook.md docs/fiat-transition-gate-runbook.md`; `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-transition-gate-study.md`; `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-transition-gate-runbook.md`; `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study docs/fiat-transition-gate-study.md --design-evidence .hexaemeron/design-evidence.json --repo-root .`; `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-transition-gate-study.md docs/fiat-transition-gate-runbook.md docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md`; and `mise exec python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py`. The source-bound audit-fix command remains `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`. Report format `elenchus.unittest.v1`. Report file `.hexaemeron/test-reports/step-1.json`.

**Why.** The receipted study was authored with link prefixes that resolve only from a file three directories below the repository root, while the original Step 1 exit placed its exact copy directly under `docs/`. Hypomnema and the root suite therefore reject the copy. Rebasing only those seven link prefixes keeps the tracked study readable without weakening either gate or changing any claim, and follows the repository's established treatment of receipted studies whose tracked location changes link resolution.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-09-03

**What changed.** Complete replacement Exit: `docs/fiat-transition-gate-study.md` preserves every receipted study byte except seven deterministic link-prefix rebases required by its tracked location: the two occurrences of `../../../docs/` become `../docs/`, and the five occurrences of `../../../plugins/` become `../plugins/`. `docs/fiat-transition-gate-runbook.md` is byte-identical to the twice-amended `.hexaemeron/runbook.md`; and `docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md` records `append-only-loop-kernel`, the two rejected candidates, the write-ahead recovery trade, and the same-account limitation. The ADR is the one home named by the study's design bridge. `.horos/boundary.json` matches a fresh deterministic scan of the tracked tree containing those three documents. `.python-version`, `pyproject.toml`, `LICENSE`, and `tests/check-map-v1.json` remain the scaffold; the step adds no competing toolchain, licence, or CI entrypoint. Run every command in the complete replacement Tests successfully. Complete replacement Files: `docs/fiat-transition-gate-study.md`, `docs/fiat-transition-gate-runbook.md`, `docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md`, and `.horos/boundary.json`. Complete replacement Tests: Preserve `test_agent_instruction.AgentInstructionScaffoldTests.test_horos_boundary_is_current_for_the_scaffold` and `test_boundary_currency.BoundaryCurrencyTests.test_the_committed_boundary_matches_a_fresh_scan` as guards that fail on the signed parent and pass after deterministic regeneration. Verify the published study's exact seven link-prefix rebases with `mise exec python@3.14.6 node@26.6.0 -- python3 -c 'from pathlib import Path; source = Path(".hexaemeron/study.md").read_bytes(); candidate = Path("docs/fiat-transition-gate-study.md").read_bytes(); assert source.count(b"../../../docs/") == 2; assert source.count(b"../../../plugins/") == 5; expected = source.replace(b"../../../docs/", b"../docs/").replace(b"../../../plugins/", b"../plugins/"); assert candidate == expected'`. Run `cmp -s .hexaemeron/runbook.md docs/fiat-transition-gate-runbook.md`; `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-transition-gate-study.md`; `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-transition-gate-runbook.md`; `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study docs/fiat-transition-gate-study.md --design-evidence .hexaemeron/design-evidence.json --repo-root .`; `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-transition-gate-study.md docs/fiat-transition-gate-runbook.md docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md`; `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/horos/skills/horos/scripts/horos.py check .`; and `mise exec python@3.14.6 node@26.6.0 -- python3 scripts/run_checks.py --base 01a17bed45058a1fc20875bb19765fdf91cb293a`. The source-bound audit-fix command remains `mise exec python@3.14.6 node@26.6.0 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`. Report format `elenchus.unittest.v1`. Report file `.hexaemeron/test-reports/step-1.json`.

**Why.** The first amended implementation passed while its three document paths were untracked, but the signed commit made them part of Horos's tracked-tree inventory. The committed-snapshot root run then failed exactly the two existing boundary-currency guards because the stored count still described the parent tree. Regenerating the governed boundary is the cause-level repair required by the repository contract; omitting the file or waiving the committed-snapshot check would leave the published inventory stale.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.
