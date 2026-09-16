# P-862 checkpoint authority protocol runbook

## Source, boundary and design

This run implements Skills issue 1676, the P-862 prerequisite of the adopted
Skills issue 862 programme. The source specification is
`https://github.com/user-attachments/files/32263127/862-r2-service-specification.md`,
SHA-256 `8ee755c1f9e5c29703af30bd08caffb6fad80c8a0990ee0acecebef09b02f541`.
The complete receipted study is `.hexaemeron/study.md`, SHA-256
`1efc7bb7710f75cab7f824b8952ee08b668e2c3722dee6b834bccbe8bba36a62`.
Its requirements, risk register, exact source pins and limits govern every step.

The immutable init base is `5bf2675d64468c7ce43ace67b0bcf1d50d38bd8e`.
The entry product tree is the published prerequisite repair commit
`1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74`, tree
`7714026b1c0f7c097d1694324c06c47bd39d5cd3`. The branch was advanced to
that source before the study receipt. The controller update receipt preserves
the original init evidence. Python is exactly 3.14.6.

The fresh entry baseline passed all 14 selected checks. Its report digest is
`068a189a11c6919f534b563a44aab30a6320136f7ae5fdfbeba264f97b660b76`.
Ariadne's 14 optional-schema skips, the root snapshot-only skip, Hexaemeron's
one expected failure and truncated enclosing output, and degraded repository
dead-code analysis remain explicit in the study. These are baseline limits,
not exemptions from new protocol conformance. Historical failed runs remain
unchanged.

The output is a reusable offline protocol, verifier, schemas, fixtures,
capability manifest and release lock. Service HTTP behavior, production
identity, cloud configuration, keys, external signer deployment, full graph
selection and physical removal remain with their adopted owners. Native
checkpoint v1 identity and archive formats stay unchanged. Native issues
1647, 1648 and 1649 remain explicit containment obligations; this packet does
not claim their repair. No in-scope existing product failure is assigned for
parent inoculation. If a step must repair a known native defect, stop that
dependent edit and bring its source-bound inventory through the owning
study/runbook amendment path first.

The checked design is ordered replay. The two candidates, selection reports,
criteria, thresholds and transition deadlines remain exactly as receipted.

```design-lock
schema | protasis-design-evidence/v1
sha256 | a34e662db37cdfed1d3c82520402ffb41790b94c977ca99813a12ea25e3785b1
candidate | ordered-replay
```

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
ariadne | plugins/ariadne/skills/ariadne/EVOLUTION.md | next-generation-after-integration-base
```

Each declared skill receives its normal generation update for added behavior.
Preserve existing frontier status, frontier text and held job unless this
packet supplies separate authority to change them. Package versions follow
their existing owner rules. Resolve relations against the stable integration
base at the controller's named transition. The advanced base does not justify
rewriting the original run anchor or omitting required sync revalidation.

## Delivery and verification conventions

Always bind work to the exact physical worktree and controller directive.
Implement only the current step, preserve every existing behavioral guard,
and carry each completed step through independent audit, prose, signed commit,
stacked publication and native checkpoint archival. Leave the stack open
until every step is pushed. The parent owns controller receipts and external
publication; a worker reports its actual source, commands and results.

Always run the selected check entrypoint for each Exit. It includes actual
changed paths and their declared dependencies. Add ownership for new paths in
`tests/check-map-v1.json` and refresh generated runtime, package and Horos
records when their authoritative inputs change. Do not edit generated copies
independently. Preserve the activated commit hook and obtain staged-tree
greenlight before every product commit.

Ask first only for a changed provider or authority boundary, production access,
cloud resources, expenditure or destructive removal. The adopted programme
already authorizes local implementation, reviews, signed delivery and issue
closure by the integrating owner. Never claim deployment, current production
eligibility or cloud retention from local fixtures.

The fixed implementation homes are:
- protocol reference: `plugins/hexaemeron/skills/fiat/references/checkpoint-authority.md`;
- reusable implementation: `plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/`;
- local CLI: `plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority.py`;
- closed schemas and fixtures: `plugins/hexaemeron/skills/fiat/checkpoint-authority/`;
- conformance reporter: `plugins/hexaemeron/tests/checkpoint_authority_conformance.py`;
- protocol tests: `plugins/hexaemeron/tests/test_checkpoint_authority*.py`;
- public study, runbook and release evidence: `docs/checkpoint-authority/`;
- decision: `docs/decisions/drafts/verify-checkpoint-authority-by-ordered-replay.md`.

The conformance reporter is the exact resolver named by the immutable design
record. Step 1 supplies its closed report plumbing and refuses every unsupported
criterion; it never emits success for an unimplemented path. Later steps
resolve only the criteria they actually prove and write the exact report paths
under `.hexaemeron/reports/`. A report includes executed behavioral evidence,
source and fixture identities, real exit status and the declared result.

The selected pending gates are:
- `records-and-signatures`, completed in Step 2, blocks entry to Step 3;
- `native-boundary-coverage`, completed in Step 3, blocks entry to Step 4;
- `authority-replay`, completed in Step 4, blocks entry to Step 5;
- `released-interoperability`, completed in Step 5, blocks integration.

The declared Elenchus command runs the actual Hexaemeron unittest suite.
Step 4 adds an ordinary test-discovery adapter for the new Ariadne checkpoint
predicate cases so the same report also covers that new cross-plugin behavior.
Ariadne's full suite remains in every checked Exit. Report formats and counts
must describe observed execution. A parent failure, skipped fixture, discovery
result, interface-valid result or inconclusive Elenchus verdict cannot supply
a green behavioral claim. The runner's worker processes are not a proof of
Elenchus containment; preserve any raw containment limitation and verdict.

## Step 1: Establish the protocol layout and governing records

**Goal.** Commit the accepted protocol specification, ownership amendments and
executable conformance scaffold without claiming unimplemented authority.

**Entry.** The exact published repair tree above, green selected baseline,
receipted study and locked ordered-replay design; no product implementation
has started.

**Exit.** Public copies of the study and this runbook, the exact decision draft,
dated R2/ownership amendments to ADR-070, ADR-071 and the existing programme
study/runbook, protocol package layout and a refusing conformance scaffold.
The scaffold admits only the locked candidate and named criteria, reports
unsupported work as unresolved/refused and never writes a passing report for
it. Existing Python, license and CI conventions cover the new package and
tests; document their reuse rather than duplicate them. The checked Exit is
`python3 scripts/run_checks.py --scope hexaemeron --scope ariadne --jobs 26 --report .hexaemeron/reports/step-1-exit.json`.

**Files.** Create `docs/checkpoint-authority/study.md`,
`docs/checkpoint-authority/runbook.md`, the decision draft's committed copy,
the implementation/schema/fixture directories and conformance reporter named
above, and focused scaffold tests. Amend the actual ADR-070/071 files,
`docs/wave-delta-checkpoint-programme-study.md` and its sibling runbook by
dated suffix only. Extend `tests/check-map-v1.json` and generated census as
required. Preserve original programme and ADR bytes as exact prefixes.

**Tests.** Check candidate and criterion closure, unknown/unsupported
criterion refusal, report destination confinement, honest non-success output,
exact copied study/design identities, dated amendment prefix preservation and
check ownership. Count new tests from actual discovery. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/p862-step-1.json`.

**Disciplines.** phylax: bound local report reads and writes and reject unsafe
paths. ephoros: make refusal stage and report completion visible without
sensitive payloads. metron: none, the initial layout makes no performance claim.
elenchus: preserve each reproduced failure and earn a guard before claiming
its repair. hypomnema: commit the expensive decision and preserve historical
governance records through dated amendments.

## Step 2: Define closed records and verify exact signature bytes

**Goal.** Implement all protocol record shapes, identities, trust references
and the interoperable DSSE signature profile.

**Entry.** Step 1's audited, receipted and checkpointed exit. Unsupported
protocol behavior still refuses; the design record and native v1 formats are
unchanged.

**Exit.** Complete canonical JSON, closed record/schema parsing and exact-byte
signature verification for the study's full record inventory. Cover policy,
enrollment/rotation/revocation, grant, run registration, upload endorsement,
validation, copy, parent, acceptance, cancellation, finalization, denial,
authorized removal, journal/head and stream permit records. Distinguish
domain-separated acceptance identity from exact randomized envelope digest
and all three native identities. Use explicit external trust, supported
key-format tags and production/test root separation. Implement the specified
P-256 SHA-256 DSSE PAE/DER profile with empty emitted keyid, strict base64
decoding and immutable verified payload handoff. Complete
`records-and-signatures` through the exact resolver and report named in the
design record. The checked Exit is
`python3 scripts/run_checks.py --scope hexaemeron --scope ariadne --jobs 26 --report .hexaemeron/reports/step-2-exit.json`.

**Files.** Add modules beneath `checkpoint_authority/` for canonical bytes,
closed records, identity and signature verification; publish corresponding
schemas, golden/hostile fixtures and protocol reference sections. Extend
conformance and `test_checkpoint_authority*.py`. Update Fiat's governed
behavior/version records and authoritative package/runtime inputs when the
new behavior lands; regenerate their derived copies.

**Tests.** Exercise every required field, tagged variant and boundary; reject
duplicates, unknown fields, bool-as-int, floats, nonfinite numbers, invalid
UTF-8, depth/byte/count overflow, malformed identifiers/timestamps, unsupported
version/type, foreign scope and self/cyclic references. Prove domain and
digest-role separation, canonical bytes and exact payload retention. Use real
independent cryptographic verification, including the released cosign tool
pin, and hostile altered PAE/type/payload, double-hash, wrong key/curve,
invalid DER and malformed/mixed base64 cases. Verify every declared trust
predecessor and enrollment challenge scope/expiry without trusting a carried
key. Add no skipped schema conformance dependency. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/p862-step-2.json`.

**Disciplines.** phylax: hostile bytes, trust inputs and fixed public-key
subprocess boundaries. ephoros: bounded typed refusal output with no private
keys, raw archive data or record-carried paths. metron: exercise declared
record and aggregate bounds without claiming a new timing comparison.
elenchus: reproduce signature/parser defects and preserve rejecting guards.
hypomnema: document exact byte, key, identity and schema compatibility rules
at their authoritative homes.

## Step 3: Bind native verification and derive complete commit coverage

**Goal.** Admit only exact current native results and independently complete
governed-commit signature coverage under approved historical keys.

**Entry.** Step 2 exit and the controller's passing
`records-and-signatures` transition. The pinned native toolchain, producer
schema and the three open containment obligations are explicit.

**Exit.** The adapter accepts only the study's inspect, exclusive-scratch
restore, verify/observations and identity sequence with every exit zero and
every result bound to the same attempt/input. Parse actual nested native
restore schemas, prove the returned worktree is a fresh private descendant,
use the native canonical manifest-plus-LF digest, and seed only independently
approved historical public keys. Derive the required commit denominator from
verified producer ledger/ranges and actual Git ancestry, then check exact
coverage and key history. Initial bases and platform-only merges retain
separate evidence classes. Publish the complete 35-fixture/24-refusal
capability mapping, external-custody support profile and named unavailability
results. Complete `native-boundary-coverage` at its exact design report path.
The checked Exit is
`python3 scripts/run_checks.py --scope hexaemeron --scope ariadne --jobs 26 --report .hexaemeron/reports/step-3-exit.json`.

**Files.** Add the native adapter and complete-coverage modules under
`checkpoint_authority/`, synthetic native boundary fixtures, the capability
manifest, exact supported source/tool pins and conformance cases. Extend
`test_checkpoint_authority*.py` and the protocol reference. Change no native
v1 record shape and no unrelated native repair.

**Tests.** Run real pinned inspect/restore/verify/identity paths for supported
synthetic archives. Exercise missing, stale, swapped or contradictory outputs,
nonzero restore followed by successful verify, scratch/path swaps, missing
trust, wrong manifest and identity digests, omitted/duplicate/extra governed
commits, unapproved historical signer, uploader/authorship mismatch, platform
evidence class mismatch and unsupported private custody. Prove that no
carried locator fetch or historical worker/guard/replacement command repairs
admission. Preserve immediate restore-tail semantics and reject nested
unsupported histories. Map each inherited hostile id to its actual producer,
inspect or restore stage. Report command execution separately from
interface-only replay. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/p862-step-3.json`.

**Disciplines.** phylax: no-follow files, fixed bounded subprocesses, approved
key injection and hostile native outputs. ephoros: correlated attempt/stage
results and explicit coverage/unavailability reasons. metron: prove native
output and archive work budgets; no inferred speed claim. elenchus: preserve
counterexamples for every repaired adapter defect and keep upstream
containment limits visible. hypomnema: document the native pin, denominator
derivation, capability mapping and supported relocation boundary.

## Step 4: Replay complete authority and register Ariadne evidence gates

**Goal.** Verify ordered authority, finite publication, minimal parents and
denial closure while separating historical validity from current eligibility.

**Entry.** Step 3 exit and passing `native-boundary-coverage` transition,
with complete admitted native evidence and closed authenticated records.

**Exit.** Ordered replay checks complete policy/key history and decision
journal from explicit bootstrap to exact signed count/tail commitments.
Enforce durable authorization versus cancellation, decision uniqueness,
exact-envelope retry, finite archive/receipt/finalization copy sequence and
fresh eligibility after finalization. Enforce registered-root permission or
one immediate accepted producer-prefix parent, all bounded prior references,
descendant poison and authorized-removal outcomes. Check challenge/time/head
floor for current eligibility; absent freshness stays unknown/unavailable.
Verify stream permits in their journal order with exact one-use scope and
state the gateway cancellation contract without claiming to execute it.
Publish private discovery/status/grant wire shapes and disabled capabilities.

Register Ariadne's checkpoint predicate, schema, real evidence gates and
complete result vocabulary. Keep signature authentication and live authority
outside Ariadne's promise, use isolated local constants/schemas and enforce
source parity with the owner. Complete `authority-replay` at the locked
report path. The checked Exit is
`python3 scripts/run_checks.py --scope hexaemeron --scope ariadne --jobs 26 --report .hexaemeron/reports/step-4-exit.json`.

**Files.** Add replay, parents, eligibility and portable wire modules beneath
`checkpoint_authority/`, positive/hostile history fixtures and conformance
cases. Add `plugins/ariadne/scripts/ariadne_lib/predicates/checkpoint_authority.py`,
its schema, registry entry and focused tests following existing Ariadne
layout. Add `plugins/hexaemeron/tests/test_checkpoint_authority_ariadne.py`
as an ordinary discovery adapter for those exact new Ariadne cases. Update
Ariadne's governed behavior/version records, both plugins' references and
generated runtime/package/census records.

**Tests.** Cover omission, sequence gaps/duplicates, forks, reordering,
foreign scope, unknown events, contradictory decisions, late cancellation,
lease expiry after authorization, incomplete copies, stale head and rollback
below a remembered floor. Prove first accepted representation remains
canonical; a different carrier needs real semantic equivalence and gains no
invented acceptance or child. Test parent omission/extras, base/run mismatch,
poison closure, authorized versus unexplained absence, permit-before-denial
and denial-before-permit, nonce scope and offline freshness limits. Cover
100-item/256-KiB inventory and 64-KiB control bounds, fixed exact-object
responses and disabled frontier/resolution/public discovery. Test Ariadne
unknown predicates, missing/unchecked gates, role/digest substitutions,
schema parity and isolated import. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/p862-step-4.json`.

**Disciplines.** phylax: authenticated event ordering, scoped references,
bounded replay and independent plugin imports. ephoros: closed historical,
publication and current-eligibility results with explicit incomplete states.
metron: measure one-body-at-a-time replay and retained decision state against
the study's declared budgets without replacing original comparison reports.
elenchus: retain counterexamples for gaps, forks, rollback and false passes.
hypomnema: document ordering, finite copies, parent limits, fresh-head trust
and Ariadne's precise evidence boundary.

## Step 5: Release and demonstrate the complete portable protocol

**Goal.** Publish a digest-bound protocol release that an independent service
consumer can verify and reproduce offline.

**Entry.** Step 4 exit and passing `authority-replay` transition. All
implemented records, signatures, native coverage, replay and Ariadne gates
are present and audited.

**Exit.** Complete the bounded local CLI and public API, released schema and
fixture inventory, capability manifest, real signature interoperability and
consumer lock example. Component digests are reproducible; the immutable
source commit is externally pinned without a self-referential file hash.
The release separates authority and native toolchain pins and refuses
mutable branch names or mixed components.

Run the exact problem-statement demonstration and
`released-interoperability` resolver from the immutable design record. It
must prove a complete accepted history and database-free reconstruction,
every declared hostile case and independent signature agreement under
network denial. Its successful historical result must still refuse to
invent current permission without fresh external evidence. Record actual
work/time/memory observations and supported resource limits. Finish the
public release guide and exact dependency handoff for service A, Skills 862
and Skills 863. The checked Exit is
`python3 scripts/run_checks.py --scope hexaemeron --scope ariadne --jobs 26 --report .hexaemeron/reports/step-5-exit.json`.

**Files.** Finalize `checkpoint_authority.py`, the protocol implementation,
schemas, fixture corpus, capability and release manifests,
`docs/checkpoint-authority/release.md`, consumer `protocol.lock.json`
example, offline demo and package installation smoke tests. Finish Fiat and
Ariadne canonical skill/reference surfaces, version/evolution and generated
distribution records. Preserve original design reports, measured values and
the exact selected candidate. Allocate a numbered ADR only after checking
the current base; preserve the draft's decision content and update real
references through their owner.

**Tests.** Rebuild release digests twice from the same tree; reject altered,
missing, extra or stale components, unsupported native pins and mutable
source references. Execute the full golden/hostile corpus and real cosign
agreement under network denial. Prove fixed bounded CLI inputs/outputs,
symlink and special-file refusal, no record-carried execution or fetching,
isolated installed plugin behavior and no signature/authenticity upgrade
from Ariadne alone. Run the complete reconstruction and eligibility
demonstration, then all required generated-record and prose gates. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/p862-step-5.json`.

**Disciplines.** phylax: release input confinement, explicit trust, subprocess
pins and offline operation. ephoros: complete machine-readable demo outcomes
and honest freshness/availability limits. metron: measure final replay and
resource ceilings against the same declared workload; record contention and
avoid unsupported performance claims. elenchus: preserve every final hostile
counterexample and verify each repair on the exact release tree. hypomnema:
publish reproducible usage, release identity, compatibility and recovery
instructions with the accepted decision.

## Pre-receipt assessment

The study establishes the selected construction, complete requirement and
risk inventory, source boundary and green repaired baseline. Production
issuer roots, cloud retention, live storage independence and service runtime
enforcement remain external obligations; their local fixtures prove only
their stated contract. The prototype boundary requires no new user decision.

The Protasis pre-receipt checklist has 22 items. Each is addressed by the
receipted study and this five-step plan. Audit currency and read modes are
preserved in the study evidence. There is no known-failure inventory marker
or assignment because this packet adds a new protocol and carries native
repairs outside its scope. All step exits and Elenchus commands use registered
local interfaces; conformance resolvers remain owned by the immutable design
record. Actual structural, command-interface, design-lock and prose check
results are recorded beside this runbook before its receipt.

