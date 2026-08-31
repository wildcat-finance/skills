# Programme runbook: portable Fiat checkpoints for distributed contribution

> **Historical proposal.** This runbook was never implemented and no longer
> governs. Accepted
> [ADR-028](decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
> replaces it with same-ledger checkpoint continuation at two explicit
> boundaries.

> **Issue renumbering, 31 August 2026.** The epic and component issues were
> re-filed under new numbers, and the links below point at the successors:
> #558 to #859, #560 to #860, #561 to #861, #563 to #862, #564 to #863, #565
> to #864, #566 to #865, #567 to #866, and #568 to #867. The `decision-chain`
> packet #559 has no successor. Those originals and #530, #539, and #562 no
> longer resolve on GitHub.

Derived from `docs/hexaemeron-checkpoint-programme-study.md`. The chosen design
is cumulative green-boundary archives, an independent locked authority, a
signed external-run publication fence, and explicit DAG resolution.

This is a programme sequencing record. Each step after Step 1 is a separate
delivery under the component issue named in that step, in the one target
repository named there. Each delivery writes its own current study/runbook and
runs one Fiat controller loop. No step below authorises one agent to write
Skills, the checkpoint service, and Atlas together.

The programme-level checks used wherever the target is
`wildcat-finance/skills` are:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
```

Every service-repository packet must create stable `make check` and named demo
targets as part of its Step 1 scaffold, whichever pinned implementation
toolchain its own study selects. Atlas packets use the scripts already owned by
that repository and add one named checkpoint-handoff demo there. A packet whose
target or exact command cannot be established at entry is blocked, not free to
borrow a nearby command.

## Step 1: Land the programme and proposed decisions

**Goal.** Put the Wave Delta study, sequencing record, and five proposed
decisions on a signed review branch while binding every component issue.

**Entry.** Branch `codex/wave-delta-checkpoint-epic` from `origin/main`
`5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`, after reading merged PR #562
and merged PR #539; accepted ADR-022 on `main`; milestone
[Wave Delta](https://github.com/wildcat-finance/skills/milestone/64); epic
[#859](https://github.com/wildcat-finance/skills/issues/859); component issues
#559 (retired, no successor), #860, #861, and #862 through #867; ADR-028
through ADR-032 collision-free.

**Exit.** The study and this runbook pass Protasis; ADR-028 through ADR-032
each pass Hypomnema with `Status: Proposed`; Imprimatur and Brevitas pass every
changed prose file; root and Hexaemeron suites pass; the commit has a valid
local Shoggoth signature and GitHub verification; one PR against `main` links
the epic and every child. No implementation, service repository, cloud
resource, Atlas change, merge, or frontier movement occurs.

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study docs/hexaemeron-checkpoint-programme-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  docs/hexaemeron-checkpoint-programme-runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  docs/hexaemeron-checkpoint-programme-study.md \
  docs/hexaemeron-checkpoint-programme-runbook.md \
  docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md \
  docs/decisions/ADR-029-separate-the-checkpoint-protocol-from-its-authority-service.md \
  docs/decisions/ADR-030-use-s3-object-lock-behind-replaceable-digitalocean-compute.md \
  docs/decisions/ADR-031-fence-external-fiat-transitions-on-signed-checkpoint-acceptance.md \
  docs/decisions/ADR-032-model-checkpoint-lineage-as-an-explicitly-resolved-dag.md
```

**Files.** Create `docs/hexaemeron-checkpoint-programme-study.md`,
`docs/hexaemeron-checkpoint-programme-runbook.md`, and the five ADR files named
in the exit command. Refresh `.horos/boundary.json` only if a fresh Horos scan
shows that one of these files earns a classified entry.

**Tests.** No executable checkpoint test exists in this planning packet. The
existing root decision/link/currency suites and the structural/prose commands
above guard the shipped document surface. Read back milestone #64, epic #859,
and every component issue through GitHub before push.

**Disciplines.** phylax: none, this step adds no executable or input path;
ephoros: none, documents do not run unattended; metron: none, no performance
change or claim; elenchus: any failing repository/prose check is reproduced and
repaired before signing; hypomnema: five expensive choices receive separate
proposed records and no issue body masquerades as accepted policy.

## Step 2: Fix run, snapshot, transport, and receipt identities

**Goal.** Deliver issue [#860](https://github.com/wildcat-finance/skills/issues/860)
so two clean machines derive the same checkpoint identity while `main` moves.

**Entry.** Step 1's PR is merged or its proposed ADR-028 and ADR-032 outcomes
are otherwise explicitly approved; issue #559 is closed with links to the
accepted decision result; the implementation run starts from fresh `main` and
records its exact base.

**Exit.** Versioned run-anchor, manifest, acceptance, revocation, and resolution
schemas exist; canonical golden vectors distinguish `snapshot_id` from
`archive_sha256`; starting commit cannot change within a run; parents determine
stage; current acceptance is outside its own snapshot/archive domain; movement
of integration `main` changes only informational fields. Focused identity tests
and all four Skills programme checks exit 0.

```bash
python3 -m unittest plugins.hexaemeron.tests.test_checkpoint_identity
python3 plugins/hexaemeron/tests/demo_checkpoint_identity.py
```

**Files.** Create versioned checkpoint schemas under `schemas/`; extend
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; create
`plugins/hexaemeron/tests/test_checkpoint_identity.py` and
`plugins/hexaemeron/tests/demo_checkpoint_identity.py`; update the Fiat
contract/version/ledger files selected by the component study.

**Tests.** Golden canonical bytes; key order/whitespace/Unicode/number/optional
field mutations; semantic versus informational mutations; immutable base;
same/cross run parents; stage; prior acceptance; unsupported versions; changed
policy/study/runbook/receipt digests. The component's Fiat runbook names the
exact Elenchus structured runner after its Step 1 scaffold creates it.

**Disciplines.** phylax: canonical manifests and receipt inputs are untrusted
and require closed schemas and bounded parsers; ephoros: status must print base,
working commit, execution class, parent and gate identities without secrets;
metron: none, hashing a bounded fixture makes no speed claim; elenchus: every
identity refusal gets a red-before-green guard; hypomnema: implements the
accepted results of ADR-028 and ADR-032 without changing their scope silently.

## Step 3: Export, inspect, and restore one cumulative archive

**Goal.** Deliver issue [#861](https://github.com/wildcat-finance/skills/issues/861)
with deterministic bytes and an offline clean-directory restore.

**Entry.** Step 2 is merged and released; #435 and #436 have landed safe,
receipt-bound observation persistence; the component study inventories every
controller file needed to decide the next action and classifies every other
file as derived, local-only, credential, or forbidden.

**Exit.** `hexctl checkpoint export`, `inspect`, and `restore` (or the exact
names fixed by the component study) create byte-identical archives from two
absolute paths, reject the full hostile ZIP/Git/state fixture set before unsafe
extraction, and restore into an empty directory with network disabled. The
restored controller verifies its receipt prefix and prior acceptance chain,
then prints but does not execute the next action. Focused archive tests, the
demo, and all four Skills programme checks exit 0.

```bash
python3 -m unittest plugins.hexaemeron.tests.test_checkpoint_archive
python3 plugins/hexaemeron/tests/demo_checkpoint_archive.py
```

**Files.** Extend the schemas and `hexctl.py`; create a deterministic archive
module under `plugins/hexaemeron/skills/fiat/scripts/`; create
`plugins/hexaemeron/tests/test_checkpoint_archive.py`, hostile fixtures under
the existing test-fixture convention, and
`plugins/hexaemeron/tests/demo_checkpoint_archive.py`; update the Fiat contract
and version/ledger records named by the component study.

**Tests.** Exact repeat bytes, complete Git bundle, portable controller state,
receipt prefix, prior acceptance, safe observation, content inventory, atomic
partial-write recovery, non-empty destination, traversal, links, special files,
duplicates, Unicode collisions, zip bomb/size/count/ratio ceilings, tampered
manifest, missing object, wrong signature, wrong run, and moving `main`.

**Disciplines.** phylax: this step opens ZIP, Git, filesystem, controller-state,
observation, secret, and subprocess boundaries; ephoros: exporter/inspector
findings are structured and bounded, while the offline library adds no page;
metron: record size, expanded size, export/inspect/restore time, and peak memory
before any optimisation; elenchus: deterministic-byte and hostile specimens are
seen fail before their controls; hypomnema: none, the format decision already
lives in ADR-028 and this step must implement it rather than broaden it.

## Step 4: Build quarantine, validation, and immutable publication

**Goal.** Deliver issue [#862](https://github.com/wildcat-finance/skills/issues/862)
in one explicitly authorised service repository.

**Entry.** Step 3 is released; the Creator has approved the exact service
repository owner/name/visibility; the repository's own instructions are read;
the service study pins the Skills protocol release and selects one pinned
language/framework/database/object-store toolchain.

**Exit.** The service repository has committed study/runbook, licence, locked
dependencies, CI stub, OpenAPI/schema pins, migrations, quarantine intake,
isolated validator, conditional state machine, immutable publication adapter,
signed-statement adapter, redacted reads, and index rebuild. `make check` and
`make demo-intake` are stable repository targets and both exit 0. The demo
accepts one golden archive, rejects every CP-3 hostile specimen, survives a
process kill at each mutable transition, and rebuilds the same index from
immutable test records.

**Files.** In the authorised service repository: `docs/study.md`,
`docs/runbook.md`, `LICENSE`, its pinned dependency/lock files,
`openapi/checkpoints-v1.yaml`, protocol pins, application source, migrations,
tests/fixtures, `Makefile`, and operator runbooks. Exact source paths are fixed
by that repository's Step 1 study before implementation.

**Tests.** `make check` covers schemas, authorisation, quotas, idempotency,
state transitions, validator sandbox, refusal codes, migrations, restart
points, index rebuild, output redaction, metrics, and API contracts.
`make demo-intake` runs one real quarantine-to-test-authority path. The service
runbook names the exact Elenchus reporter provided by its scaffold.

**Disciplines.** phylax: every API, archive, database, subprocess, object-store,
credential, and model/tool-output boundary is hostile; ephoros: API and workers
run unattended and need state progress, staleness, rate/error/duration, and
runbook-linked alerts; metron: establish route/dependency p95/p99, queue age,
validation time, and resource baselines on a fixed corpus; elenchus: kill/retry
and malicious specimens require causal guards; hypomnema: implements ADR-029
and hands the attestation predicate/signature profile to Ariadne's boundary.

## Step 5: Deploy and prove the locked authority

**Goal.** Deliver issue [#863](https://github.com/wildcat-finance/skills/issues/863)
so accepted state outlives its DigitalOcean compute and mutable index.

**Entry.** Step 4 is merged with non-production deployment support; exact
DigitalOcean project/region and separate AWS primary/replica accounts/regions
are approved; infrastructure state and secret custody have named homes; no
production action is inferred from issue filing.

**Exit.** Non-production infrastructure as code creates LON1 API/worker
compute, bounded encrypted scratch, Managed PostgreSQL, quarantine, a
governance-locked primary bucket, a separately controlled locked replica,
Roles Anywhere profiles, asymmetric KMS signing, audit trails, and alert paths.
Runtime permission tests prove delete, overwrite ambiguity, retention shortening,
bypass, authority-policy mutation, replication-policy mutation, and KMS
administration are refused. `make check-infra` and `make demo-authority` exit 0;
the latter destroys/recreates the Droplet/index and verifies the same object
versions and statement. Production remains ask-first.

**Files.** In the service repository: `infra/` with pinned providers/modules,
environment declarations without secrets, IAM/bucket/key policies,
`docs/runbooks/authority-outage.md`, `replication-lag.md`, `database-rebuild.md`,
`droplet-replacement.md`, `certificate-revocation.md`, `receipt-key-rotation.md`,
and `break-glass.md`; extend `Makefile` and infrastructure tests.

**Tests.** Policy/plan tests, retained specimen, refused runtime actions,
primary/replica checksum-version-retention equality, Roles Anywhere expiry and
revocation, wrong role/account/statement-domain signing, read-back before
acceptance, PostgreSQL rebuild, Droplet replacement, alerts, log review, and
non-production exact-version break glass with two approvers.

**Disciplines.** phylax: cloud identity, policies, certificates, keys, secrets,
backups, scratch, and deployment tools widen trust boundaries; ephoros: every
publication dependency and recovery state needs bounded events and symptom
alerts; metron: size the Droplet/scratch/database from Step 3/4 baselines and
re-measure the authority demo; elenchus: policy or recovery failures stop the
promotion and receive guards; hypomnema: this step makes ADR-030 real and must
not change its authority split through an operator shortcut.

## Step 6: Enforce the external-run publication fence

**Goal.** Deliver issue [#864](https://github.com/wildcat-finance/skills/issues/864)
so one externally completed transition is not complete until its signed
acceptance statement verifies locally.

**Entry.** Steps 3 through 5 are released in a reachable test environment;
the component run starts from current Skills `main`; the external execution
class and any allowed amendment are fixed in its study.

**Exit.** Run creation/status/resume carry `execution_class`; existing gates
lead to `checkpoint_ready`; export/publish is idempotent; the controller holds
at `publishing` through outages; exact statement, signer, policy, repository,
issue, run, step, role, parent, archive, primary, and replica identities verify;
one local acceptance append unlocks exactly the next action. Interruption tests
at every edge and a two-machine one-transition demo pass with all four Skills
programme checks.

```bash
python3 -m unittest plugins.hexaemeron.tests.test_checkpoint_fence
python3 plugins/hexaemeron/tests/demo_checkpoint_fence.py
```

**Files.** Extend checkpoint schemas, `hexctl.py`, Fiat contract/version/ledger
records, and existing push/receipt references; create
`plugins/hexaemeron/tests/test_checkpoint_fence.py` and
`plugins/hexaemeron/tests/demo_checkpoint_fence.py`; add bounded service-client
code under the Fiat scripts directory with exact dependency treatment from the
component study.

**Tests.** Explicit local/external/legacy class, attempted downgrade,
checkpoint-ready preconditions, forged/mismatched/rotated-key statements,
pending/rejected/revoked state, every client/server interruption, acceptance
after response loss, duplicate append, two siblings, moving `main`, fresh
delegation on restore, and machine-A-to-machine-B continuation.

**Disciplines.** phylax: authentication, service responses, grants, downloaded
statements, local state, and retry persistence cross boundaries; ephoros: status
must answer which side owns the next retry and how old the fence is; metron:
record publication latency and outage retry load without weakening a gate;
elenchus: every interruption and forged receipt is a red-before-green guard;
hypomnema: implements ADR-031 and may not widen mandatory publication beyond
the accepted execution classes without a new decision.

## Step 7: Preserve siblings and require signed resolution

**Goal.** Deliver issue [#865](https://github.com/wildcat-finance/skills/issues/865)
so concurrent useful checkpoints remain visible and preference is explicit.

**Entry.** Step 6 publishes valid siblings; the service target and resolver
identity/signature mechanism are explicitly approved; ADR-032 is accepted in
the form implemented by the component study.

**Exit.** Immutable parent edges, derived stage, advisory claims, frontier
reads, signed resolution, reconciliation, revocation poisoning, and clean-
ancestor salvage work under one append-only graph. Database rebuild yields the
same graph. `make check` and `make demo-lineage` exit 0; the demo publishes two
siblings in both arrival orders, keeps both visible, refuses forged resolution,
and accepts one union-of-work reconciliation checkpoint authorised by a valid
resolution.

**Files.** In the service repository: graph/resolution/revocation migrations
and source, protocol pins, fixtures, API descriptions, resolver/key-rotation
runbooks, `Makefile`, and tests. Skills schema changes, if the service study
finds one is required, are a separately filed Skills issue and run.

**Tests.** Roots/parents/cycles/cross-scope edges/stage, missing or revoked
parent, late sibling, stale/expired claim, clock skew, upload order, duplicate
and contradictory resolution, forged/rotated resolver key, reconciliation Git
or ADR-021 rewrite provenance, salvage, kill/retry at every resolution edge,
and index rebuild.

**Disciplines.** phylax: parent/resolver/revocation inputs and signatures are
untrusted; ephoros: frontier, claim, poison, and resolution state need bounded
queryable events; metron: measure ancestry/frontier/rebuild work against a
fixed graph before optimising; elenchus: cycles, contradictory decisions, and
revoked ancestry get causal guards; hypomnema: implements ADR-032 and keeps a
policy decision separate from a service index update.

## Step 8: Break and recover the complete authority path

**Goal.** Deliver issue [#866](https://github.com/wildcat-finance/skills/issues/866)
with preserved adversarial fixtures and measured recovery evidence.

**Entry.** Steps 3 through 7 are pinned by signed releases/commits in a
non-production environment; exact destructive targets and recovery roles are
approved; the golden corpus contains linear, sibling, reconciled, revoked, and
poisoned state.

**Exit.** `make check`, `make demo-adversarial`, and `make demo-recovery` exit
0. Every named hostile specimen fails at its owned boundary; every publication
edge resumes idempotently; revocation and salvage work; the non-production
Droplet and index are destroyed and rebuilt; replica-only read/verify/restore
finishes within 60 minutes; full intake/signing recovery finishes within four
hours; accepted-state RPO is zero for the test corpus. A missed objective stays
open with its measured result.

**Files.** In the service repository: adversarial fixture corpus, fault-injection
and recovery harnesses, measurement records, recurring-drill schedules, all
incident runbooks, and stable Make targets. Defects in other repositories are
filed separately and remain outside this step's write boundary.

**Tests.** The complete matrix from #866: canonicalisation, ZIP/Git/state,
identity/signatures, retries, siblings/resolutions, revocation/salvage,
database/Droplet/primary/replica/KMS/certificate failures, index tampering,
key transition, exact-version break glass, output redaction, alert delivery,
and repeatable recovery timing.

**Disciplines.** phylax: full boundary and secret-output review; ephoros:
exercise every page and reconstruct incidents by correlation id; metron: record
raw recovery/validation/resource measurements against fixed methods; elenchus:
stop on each failure, preserve it, repair the cause in a separate packet, and
show the guard fails without the fix; hypomnema: key transition or changed
recovery authority earns a new record rather than an edited incident report.

## Step 9: Add Atlas resume, redraw, and start routing

**Goal.** Deliver issue [#867](https://github.com/wildcat-finance/skills/issues/867)
without making Atlas an archive or resolution authority.

**Entry.** Step 8 proves the service and recovery path; issues #505 and #530
have supplied current source-freshness and handoff contracts; exact Atlas
repository, branch, actor, production commit/application id, and deployment
authority are reverified before any write.

**Exit.** Atlas consumes a versioned redacted response, shows immutable base,
working commit, current `main`, all accepted unrevoked siblings, claim freshness,
resolution, revocation, and independent source freshness. A resume selection is
bound and refreshed before handoff; changed state requires redraw; start creates
a separately acknowledged run anchor. Authorised download uses a short-lived
exact-version grant and the released Skills verifier/restorer. Atlas's existing
checks plus its named checkpoint-handoff demo pass locally and against the
approved deployed target.

**Files.** In `wildcat-finance/shoggoth-wave-atlas`: its target-owned study and
runbook, redacted checkpoint schema/client, API route/cache logic, routing UI,
auth/download handoff, fixtures/tests, accessibility evidence, diagnostics,
and deployment record. No archive, receipt private body, secret, or durable
object URL is checked in or rendered.

**Tests.** Linear/forked/preferred/revoked/poisoned states; live/cached/snapshot/
unavailable/unauthorised sources; selection changes; claim expiry; download
expiry/retry; public/private fields; keyboard/screen-reader/narrow-screen/
reduced-motion/colour-independent status; production page plus cache-busted
GitHub and checkpoint diagnostics; exact deployed commit.

**Disciplines.** phylax: external APIs, auth, grants, rendered data, cache, and
browser storage are boundaries; ephoros: source freshness and handoff failures
need bounded signals and symptom alerts; metron: measure route/render/download
handoff budgets before any optimisation; elenchus: stale healthy-page and
selection-race failures receive guards; hypomnema: Atlas remains a redacted
client under ADR-029 and cannot absorb checkpoint authority through convenience.

## Step 10: Demonstrate the programme and close the epic last

**Goal.** Run the study's full two-machine, moving-main, fork, reconciliation,
revocation, and recovery demonstration before closing #859.

**Entry.** Steps 1 through 9 are merged/deployed where authorised, every child
issue is still open or has its exit evidence linked, exact production/staging
targets are approved, and no unresolved high-consequence finding or stale
source is being treated as a pass.

**Exit.** One recorded script or operator transcript starts an external run on
machine A, publishes one green transition, advances `main`, discovers and
restores it on clean machine B, prints the exact next action, publishes two
siblings, accepts an authorised reconciliation, revokes one exact poisoned
version, refuses its descendants, salvages from a clean ancestor, destroys and
rebuilds replaceable service state, and restores through the replica path. All
identities, signatures, object versions, source states, alerts, and durations
are attached to #859. Component issues close only after their own criteria;
#859 closes last. No evidence gap is replaced with a summary claim.

**Files.** No product file is changed by programme closure. Store bounded
demonstration scripts and non-secret fixtures in the repository that owns them;
attach or link immutable evidence from #859 and update issue checklists without
rewriting earlier records.

**Tests.** Re-run every component's released check/demo target at its pinned
version, then the cross-system demonstration from the study. Verify the
milestone contains exactly the epic and intended component issues, all links
resolve, every merged commit and deployed version verifies, and no archive or
secret appears in public evidence.

**Disciplines.** phylax: final cross-boundary and secret-output review;
ephoros: confirm the whole path can be reconstructed from correlation and
freshness evidence; metron: compare measured recovery/publication results to
the recorded objectives without hiding misses; elenchus: any failure blocks
closure until its cause and guard are complete; hypomnema: record any changed
expensive decision before the demo is rerun, and keep all superseded evidence.
