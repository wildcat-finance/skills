# Study: portable Fiat checkpoints for distributed contribution

> **Historical proposal.** This study records the service design considered in
> August 2026. It no longer governs Fiat continuation. Accepted
> [ADR-028](decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
> permits checkpoint continuation only at a successful end of step or an
> exhausted audit, on the same controller ledger.

Assuming, unless corrected:

1. This delivery records the programme, its proposed decisions, and its issue
   packets. It does not add checkpoint code, create the service repository,
   provision cloud resources, change Atlas, or start a Fiat implementation run.
2. An external contributor earns a checkpoint only at a green, committed,
   signed, pushed, and remotely verified Fiat transition. Version 1 does not
   capture an arbitrary dirty worktree or half-finished audit round.
3. Fiat `5.19.1` already distinguishes the immutable starting commit from the
   named integration base and retains bounded superseded integration-sync
   receipts. Checkpointing extends those distinctions rather than introducing
   another base or discarding an earlier failed composition record.
4. A checkpoint is cumulative and independently restorable. It carries a
   complete Git bundle for its declared base and working commit plus the
   bounded portable controller and evidence state. Earlier checkpoint archives
   are not needed to restore a later one.
5. Accepted ADR-022 and closed issue
   [#435](https://github.com/wildcat-finance/skills/issues/435) make run
   observations safe to persist. Open issue
   [#436](https://github.com/wildcat-finance/skills/issues/436) must still bind
   them to Fiat receipts before an observation can enter a portable archive.
6. Archive bytes stay private. Public issue and Atlas surfaces receive only a
   redacted discovery record and never a reusable object-store URL.
7. The proposed service source belongs in a separate, reviewable
   `wildcat-finance/fiat-checkpoints` repository. That repository does not
   exist by authority of this study; exact owner, name, visibility, actor, and
   cloud targets are ask-first entry gates in issue
   [#563](https://github.com/wildcat-finance/skills/issues/563).
8. The proposed first deployment uses replaceable DigitalOcean compute and
   Managed PostgreSQL in `LON1`, while locked S3 object versions and KMS-signed
   receipts in separate AWS accounts carry authority. PostgreSQL and the
   Droplet are rebuildable indexes and workers.
9. Checkpoint lineage is a graph. Concurrent valid children remain visible and
   no clock, upload order, or longest-chain rule chooses one silently.
10. This package was first drafted against `origin/main`
    `2b6848b95e9d90f4bc9995b8cd89106d1807e9a9` and rebased before publication
    to `5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`, after reading merged PR #562
    and merged PR #539. ADR-022 is now accepted on `main`; ADR-028 through
    ADR-032 remained free at the final check.
11. The held Fiat frontier remains issue
    [#363](https://github.com/wildcat-finance/skills/issues/363). Filing Wave
    Delta does not move, close, or replace it.

I will proceed on these assumptions unless corrected.

## 1. Problem statement

Fiat can now keep a long delivery honest inside one dedicated worktree. It can
pin the commit at which a run began, distinguish that from a later integration
base, preserve signed product evidence when `main` advances, and refuse a
rewritten stack. Those guarantees stop at the machine holding the ignored
`.hexaemeron/` directory. A branch transfers Git objects; it does not by itself
transfer the controller state, receipt prefix, bounded observation, exact next
directive, or the service decision that those bytes are safe to resume.

The contributor promise is narrower and more useful than general distributed
execution: if somebody completes one valid Fiat transition, somebody else can
discover, verify, restore, and continue that transition from another machine,
even while `main` keeps moving. The system must retain concurrent valid work
instead of turning arrival order into authority.

The programme is decomposed because protocol, archive handling, service
intake, storage authority, controller fencing, graph resolution, recovery, and
contributor routing can fail and ship separately:

| Module id | Responsibility | Issue | Target | Depends on |
| --- | --- | --- | --- | --- |
| `decision-chain` | Replace stale checkpoint prior art with the current contract and proposed records | [#559](https://github.com/wildcat-finance/skills/issues/559) | `wildcat-finance/skills` | #439, #434 |
| `checkpoint-identity` | Fix run anchors, semantic identity, transport identity, parents, stage, and receipt sidecars | [#560](https://github.com/wildcat-finance/skills/issues/560) | `wildcat-finance/skills` | `decision-chain` |
| `archive-core` | Export, inspect, and restore one cumulative deterministic archive | [#561](https://github.com/wildcat-finance/skills/issues/561) | `wildcat-finance/skills` | `checkpoint-identity`, #435, #436 |
| `checkpoint-service` | Quarantine hostile uploads, validate, publish immutably, and index accepted state | [#563](https://github.com/wildcat-finance/skills/issues/563) | future service repository | `archive-core` |
| `storage-authority` | Deploy locked primary and replica objects plus the receipt signer behind replaceable compute | [#564](https://github.com/wildcat-finance/skills/issues/564) | future service repository | `checkpoint-service` |
| `publication-fence` | Require a verified acceptance receipt before an external transition advances | [#565](https://github.com/wildcat-finance/skills/issues/565) | `wildcat-finance/skills` | `archive-core`, `checkpoint-service`, `storage-authority` |
| `lineage-resolution` | Preserve siblings, advisory claims, signed resolution, reconciliation, and salvage | [#566](https://github.com/wildcat-finance/skills/issues/566) | future service repository | `checkpoint-identity`, `publication-fence` |
| `recovery-proof` | Break hostile, concurrent, revoked, and lost-infrastructure paths and measure recovery | [#567](https://github.com/wildcat-finance/skills/issues/567) | future service repository | every service/controller module |
| `resume-routing` | Let Atlas offer resume, redraw, or start from redacted current state | [#568](https://github.com/wildcat-finance/skills/issues/568) | `wildcat-finance/shoggoth-wave-atlas` | #505, #530, `recovery-proof` |

Build order follows the table. Each row is a separate delivery with its own
study, runbook, clean worktree, audit loop, receipts, and pull request. The
programme runbook is a sequencing record; it is not permission to operate on
three repositories in one Fiat run.

A working programme means this demonstration succeeds from two clean machines:

1. Machine A starts an `external` Fiat run at an exact starting commit and
   completes one green transition.
2. `main` advances independently.
3. Machine A exports deterministic bytes, publishes them through quarantine,
   and verifies an acceptance statement covering locked primary and replica
   object versions.
4. Machine B discovers the accepted state, downloads it through a short-lived
   authenticated grant, verifies and restores it offline, and prints the exact
   next permitted action.
5. Two machines then publish siblings from one parent; both remain visible
   until a signed resolution authorises a reconciliation checkpoint.
6. The service loses its Droplet and PostgreSQL index and rebuilds the same
   accepted graph from locked records, with replica-only read/verify/restore
   available inside the objective recorded in #567.

The exact released commands are fixed by the component studies. The final
demonstration records every command, SHA-256, snapshot id, object version,
receipt signature, source freshness value, and recovery duration on
[epic #558](https://github.com/wildcat-finance/skills/issues/558).

## 2. Prior art

**The controller already has the anchor and repair split.** Fiat `5.19.1` is
the current contract. [PR #549](https://github.com/wildcat-finance/skills/pull/549)
keeps signed product evidence bound to its exact product head while a separately
receipted integration step composes it with a newer base.
[PR #550](https://github.com/wildcat-finance/skills/pull/550) keeps the exact
starting commit in `state.base` and the named integration branch in
`config.git.base`, then reports both through sync and terminal receipts.
[PR #562](https://github.com/wildcat-finance/skills/pull/562) retains a failed
integration-sync receipt, permits only a freshly signed and revalidated
replacement to become active, and keeps the supersession history bounded. PRs
#550 and #562 are the last two merged pull requests touching the controller and
were read before finalising the design. A checkpoint must preserve the starting
and integration identities plus active and superseded sync evidence; it may not
add a mutable `main` guess, discard a failed composition record, or reopen a
completed product audit after ordinary drift.

**Dedicated worktrees and signed landing already govern local work.**
[ADR-012](decisions/ADR-012-run-fiat-in-a-dedicated-worktree.md) gives every run
an isolated tree and keeps `.hexaemeron/` with it.
[ADR-021](decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md)
keeps original signed commits as the landing source when GitHub rewrites a
stack. A restored checkpoint must create a fresh dedicated worktree and retain
original-versus-rewritten provenance; it cannot pour state into the caller's
checkout or treat any GitHub-verified signature as the Shoggoth signature.

**The observation boundary is deliberately separate.**
[ADR-015](decisions/ADR-015-define-the-promise-machine-run-observation-record.md)
creates a host-neutral observation record but expressly leaves capture,
redaction, persistence, and Fiat receipt binding to later work. Issue #435 and
merged PR #539 have now landed bounded pre-persistence capture under accepted
[ADR-022](decisions/ADR-022-define-the-run-observation-capture-profile.md).
Issue #436 still owns receipt binding. This programme waits for that remaining
contract rather than packing host transcripts or hidden model reasoning.

**The earlier checkpoint run is prior art, not accepted policy.** PR
[#478](https://github.com/wildcat-finance/skills/pull/478) records a clean
Warden round over the scaffold at signed commit
`b490da51b0ed4f56208ae490cdd89348ec689934`. Its audit record reviewed all
fifteen study risks and found no scaffold defect. PR
[#479](https://github.com/wildcat-finance/skills/pull/479) then merged that
scaffold into its run branch and states plainly that the proposed ADR bytes
were added after the audit round. Nothing from that branch landed on `main`.
The old design contributes the cumulative format, complete Git evidence,
separate semantic and transport concerns, hostile ZIP boundary, parent-derived
stage, and visible fork refusal. This study changes four parts:

- version 1 captures only a completed green transition rather than arbitrary
  staged, unstaged, and untracked work;
- the starting-commit split now uses the shipped 5.18.1 state contract;
- accepted state waits for a locked cross-account replica and a service-signed
  statement rather than an ordinary object-store response; and
- forks are retained in a DAG and resolved by a signed decision rather than a
  `furthest` endpoint that can only return conflict.

**The relevant audit record was read.** The old branch's `audit/AUDIT.md`
entry, "Portable checkpoint design package, step 1, round 1", records a clean
scaffold and carries no unpursued lead. It also says the archive parser,
importer, service, and unattended paths did not exist and every risk remained
a later design constraint. Current root audit history contains no accepted
round establishing checkpoint export, storage, or resume. A clean scaffold
therefore authorises no implementation or operational claim here.

**Related live work stays separate.** Issue #508 binds delegated writes,
carryover, and runbook gates; restored state must retain those identities.
Issue #547 makes commit verification portable across clones, which strengthens
restore but does not publish controller state. Issue #437 establishes a
dead-code baseline on a separate introspection track and is not a transport
prerequisite. Issues #505 and #530 own Atlas source freshness and handoff tests.

**Standards and hosted capabilities.** Git bundle supplies a portable Git
object/ref container. RFC 8785 supplies a JSON canonicalisation scheme; the
checkpoint profile narrows it further by refusing floats and ambiguous optional
fields. RFC 9457 supplies bounded HTTP problem details and RFC 9530 supplies
HTTP content digests. Ariadne owns the organisation's in-toto/DSSE evidence
statement boundary; CP-2 must hand the acceptance predicate and its KMS signing
profile to Ariadne rather than inventing a second attestation grammar silently.

AWS documents that S3 Object Lock protects object *versions*, requires
versioning, permits governance bypass only to specially authorised callers,
and allows a new version at the same key. Its replication documentation says
locked source objects and retention metadata can be copied asynchronously to
another locked bucket. Those facts decide two rules: the signed acceptance
statement names exact primary and replica version ids, and runtime roles never
receive governance-bypass permission. AWS also documents IAM Roles Anywhere as
the X.509 route for temporary credentials on non-AWS workloads, and KMS
documents `ECC_NIST_P256` with `ECDSA_SHA_256` plus public-key verification
outside KMS. DigitalOcean documents `LON1` availability and managed PostgreSQL
backup/point-in-time restore. The database remains an index because destroying
a cluster also destroys its retained backups; locked object records must be
enough to rebuild it.

## 3. Constraints and non-goals

- **Starting ref.** Published planning branch base
  `5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`. Each later implementation run
  records its own exact base and current integration branch.
- **Controller and protocol.** Fiat `5.19.1`, Promise Machine
  `promise-machine/v1`, Python 3.11 and standard-library controller checks.
  Service dependencies are later ask-first choices with exact pins and a
  reviewed lockfile.
- **Checkpoint boundary.** Version 1 exports only after existing implementation,
  audit, prose, signing, push, and remote-verification gates are green. It does
  not rescue an uncommitted editor buffer or let a red step call itself useful.
- **Portable content.** One complete Git bundle, path-independent controller
  state, a verified receipt prefix, a schema-valid bounded observation, prior
  checkpoint acceptance statements, and a digest inventory. Credentials,
  delegation handles, locks, sockets, caches, build output, and raw host/model
  transcripts are excluded.
- **Identity.** SHA-256 names canonical semantic state and exact transport
  bytes separately. Parent edges and verified receipts establish lineage.
  Timestamps remain diagnostic.
- **Privacy.** Archives, observations, object locations, and download grants are
  private. Public discovery is a separate redacted response with an explicit
  source/freshness state.
- **First storage profile.** S3 Object Lock governance mode, at least 365 days
  for accepted archives and signed records, a locked cross-account/region
  replica, and KMS-signed acceptance. Retention can be extended, never shortened
  by a runtime role.
- **Non-goals.** General-purpose distributed builds, arbitrary work stealing,
  automatic merge/conflict resolution, a consensus protocol, Git replacement,
  public archives, checkpointing private/non-Git repositories in version 1,
  preserving arbitrary dirty worktrees, or making Atlas an authority.
- **Always.** Run the applicable repository suites before every commit; run
  Protasis on each study/runbook, Imprimatur and Brevitas on shipped prose,
  Hypomnema on decision records, Phylax on every external-input path, Ephoros
  on unattended code, and exact signature verification before push.
- **Ask first.** Create the service repository, choose its visibility or
  framework, add a dependency, create/change a cloud account or resource,
  change retention, change a public schema/CLI, widen archive contents,
  expose a download, change Atlas, rotate a receipt key, or perform break glass.
- **Never.** Commit a credential; give contributors AWS credentials; extract an
  archive member by its supplied path; restore over a non-empty checkout; make
  PostgreSQL or a Droplet disk the only accepted record; let runtime roles
  delete accepted versions or bypass retention; include current acceptance in
  the archive it signs; choose a fork by time; rewrite the run's starting
  commit; or claim acceptance while any required check is unknown.

## 4. Design options

**A. Cumulative checkpoints with a separate locked authority (chosen).** Every
green transition produces one self-contained archive with a complete Git bundle
and portable controller/evidence state. A service grants a bounded quarantine
upload, validates in isolation, writes exact object versions under Object Lock,
waits for a locked cross-account replica, and returns a KMS-signed acceptance
statement. The controller verifies that statement before an external run can
advance. Accepted checkpoints form a DAG and human/organisation resolver
signatures govern preference and reconciliation. The trade is repeated bytes,
two cloud providers, and more operations in exchange for independent restore,
separation from worker compromise, and visible concurrent work.

**B. Incremental patch objects in a content-addressed chain.** Each transition
stores only its delta from the previous checkpoint. Upload and storage are
smaller. Rejected for version 1 because restore must trust and process every
earlier object, one missing or revoked ancestor strands all descendants, and a
late contributor cannot verify one useful step from one package. The DAG may
deduplicate complete objects later without changing the portable contract.

**C. Git branches, pull requests, and release assets only.** This is already
available and keeps authorship visible. Rejected as the full solution because
ignored controller state, receipt prefix, observation binding, next directive,
revocation, and fork resolution remain local or informal. It remains the
fallback while the programme is unbuilt.

**D. A DigitalOcean API with local/Spaces storage as authority.** This is the
simplest deployment and makes one vendor own compute and bytes. Rejected
because a compromised host or project credential can change both the decision
and the only stored object, and local disk failure would turn restore into a
backup hunt. DigitalOcean remains a good replaceable compute/index location;
authority sits in locked, version-specific records elsewhere.

Option A is the smallest choice that meets the stronger-authority requirement
without pretending to solve general distributed scheduling. It trades storage
efficiency and a one-provider deployment for a checkpoint another person can
verify without trusting the machine that accepted it.

## 5. Risk register seed

```risk-register
base-drift | the immutable run start versus a moving integration branch | every manifest repeats the shipped starting commit field and a later main SHA is informational only
semantic-transport-split | canonical state versus exact ZIP bytes | snapshot_id and archive_sha256 are computed over distinct named byte domains and both are tested by golden vectors
receipt-cycle | the archive and the service statement that accepts it | current acceptance is a signed sidecar and only the next archive carries it as a prior receipt
observation-disclosure | the run observation entering a portable archive | #435 redaction and #436 receipt binding pass before export and the inspector enforces the bounded schema
delegation-revival | restored controller state containing a live local handle | delegation identity is retained as evidence but a new machine must obtain fresh scoped authority
archive-traversal | hostile ZIP names and filesystem types | inspect before extraction and reject absolute paths dot segments alternate separators links special files duplicates and ambiguous Unicode
archive-exhaustion | compressed input expanding in the validator or restorer | hard entry compressed expanded ratio memory CPU and wall-time limits stop before materialisation
git-object-substitution | a bundle that names the right SHA but supplies the wrong repository relation | verify bundle objects signatures base and working commit reachability with system and global Git configuration disabled
secret-disclosure | controller state observations logs or ignored files entering transport | allowlist members scan bounded bytes and exclude credentials grants raw transcripts caches locks and build output
partial-publication | client worker S3 replication or KMS failure between states | conditional idempotent transitions stay pending until exact primary replica statement and read-back checks complete
object-version-confusion | a later S3 version appearing at an accepted key | the signed statement binds bucket key version checksum retention and replica version rather than trusting a key name
runtime-deletion | a compromised API or worker trying to erase accepted evidence | runtime policies omit delete retention-shortening bypass bucket-policy replication-policy and KMS-admin actions
signer-custody | the service asking KMS to sign an unrelated or forged decision | a typed statement domain exact signing algorithm least-privilege role public verifier and hostile signature fixtures gate acceptance
database-authority | mutable PostgreSQL rows disagreeing with locked records | indexes rebuild from immutable manifests statements revocations and resolutions and comparison precedes reopened writes
lineage-fork | two contributors publishing from one parent | both valid children remain visible and no clock upload order or stage tie selects a winner
resolution-forgery | service code or an unauthorised user choosing a frontier | a separate resolver role signs the complete frontier and action before KMS records service acceptance
revoked-ancestor | a descendant relying on a poisoned accepted object | resume refuses the node and descendants until a signed salvage starts from the last clean ancestor
stale-discovery | Atlas or an API cache presenting old checkpoint state as current | each source reports live cached snapshot or unavailable plus freshness and selection redraws on change
cross-repository-authority | one programme step writing Skills service and Atlas together | every issue names one target and requires a separate study runbook worktree receipts and PR
```

The storage authority still has a human break-glass boundary because governance
mode permits a specially authorised bypass. Runtime roles never hold it. The
break-glass runbook requires MFA, two approvers, a bounded session, a reason,
and one exact object version; ordinary poison handling uses a signed revocation
and preserves the bytes.

## 6. Glossary seeds

- `Initial base`: the full commit SHA at which Fiat created the run; immutable
  for that run.
- `Integration base`: the named branch and current commit against which a
  completed product is later composed; allowed to move under Fiat's sync rules.
- `Run anchor`: repository, issue, run id, initial base, controller version,
  study/runbook/policy digests, and execution class fixed at start.
- `Green transition`: a runbook boundary whose implementation, audit, prose,
  signature, push, and remote-verification gates have all passed.
- `Snapshot`: the canonical semantic state at one green transition.
- `Snapshot id`: SHA-256 of the canonical typed snapshot payload, excluding
  transport metadata and its own id field.
- `Archive digest`: SHA-256 of the exact deterministic ZIP bytes.
- `Acceptance statement`: the typed, service-signed sidecar binding snapshot,
  archive bytes, validation policy, exact primary/replica versions, and result.
- `Prior acceptance`: an earlier checkpoint's verified statement carried in a
  later cumulative archive.
- `Stage`: root zero, otherwise one plus the maximum verified parent stage.
- `Frontier`: an accepted, unrevoked checkpoint with no accepted unrevoked child
  in the same run graph.
- `Claim`: a bounded advisory lease on one parent and next transition; useful
  for coordination but unable to erase a valid sibling.
- `Resolution`: a separately signed choice to continue, reconcile, supersede,
  salvage, or hold an exact frontier set.
- `Revocation`: an append-only signed record that makes one exact object version
  non-resumable without deleting its evidence.
- `Authority store`: locked primary and replica object versions plus signed
  decisions; not the service database or compute host.

## 7. Sources

- [Wave Delta epic #558](https://github.com/wildcat-finance/skills/issues/558)
  and component issues [#559](https://github.com/wildcat-finance/skills/issues/559),
  [#560](https://github.com/wildcat-finance/skills/issues/560),
  [#561](https://github.com/wildcat-finance/skills/issues/561),
  [#563](https://github.com/wildcat-finance/skills/issues/563),
  [#564](https://github.com/wildcat-finance/skills/issues/564),
  [#565](https://github.com/wildcat-finance/skills/issues/565),
  [#566](https://github.com/wildcat-finance/skills/issues/566),
  [#567](https://github.com/wildcat-finance/skills/issues/567), and
  [#568](https://github.com/wildcat-finance/skills/issues/568).
- `plugins/hexaemeron/skills/fiat/SKILL.md` version `5.19.1` and
  `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; PRs
  [#549](https://github.com/wildcat-finance/skills/pull/549) and
  [#550](https://github.com/wildcat-finance/skills/pull/550), plus the current
  [#562](https://github.com/wildcat-finance/skills/pull/562) repair path.
- [ADR-012](decisions/ADR-012-run-fiat-in-a-dedicated-worktree.md),
  [ADR-015](decisions/ADR-015-define-the-promise-machine-run-observation-record.md),
  and [ADR-021](decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md).
- Issues [#434](https://github.com/wildcat-finance/skills/issues/434),
  [#435](https://github.com/wildcat-finance/skills/issues/435),
  [#436](https://github.com/wildcat-finance/skills/issues/436),
  [#439](https://github.com/wildcat-finance/skills/issues/439),
  [#508](https://github.com/wildcat-finance/skills/issues/508),
  [#547](https://github.com/wildcat-finance/skills/issues/547),
  [#505](https://github.com/wildcat-finance/skills/issues/505), and
  [#530](https://github.com/wildcat-finance/skills/issues/530).
- PRs [#478](https://github.com/wildcat-finance/skills/pull/478) and
  [#479](https://github.com/wildcat-finance/skills/pull/479), commits
  `b490da51b0ed4f56208ae490cdd89348ec689934`,
  `ecd11fa46e45ca8b4ab11560447b3a9cdc1bca0d`, and
  `b689c5f235e17ae818cb4fccfde3d53c8c16a04f`, plus their branch-local
  `audit/AUDIT.md` checkpoint round.
- [Git bundle documentation](https://git-scm.com/docs/git-bundle),
  [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785),
  [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457), and
  [RFC 9530](https://www.rfc-editor.org/rfc/rfc9530).
- [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
  and [Object Lock replication/operations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html).
- [IAM Roles Anywhere](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/introduction.html)
  and its [trust model](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/trust-model.html).
- [AWS KMS key specifications](https://docs.aws.amazon.com/kms/latest/developerguide/symm-asymm-choose-key-spec.html)
  and [Sign API](https://docs.aws.amazon.com/kms/latest/APIReference/API_Sign.html).
- [DigitalOcean regional availability](https://docs.digitalocean.com/platform/regional-availability/)
  and [Managed PostgreSQL restore](https://docs.digitalocean.com/products/databases/postgresql/how-to/restore-from-backups/).
- `plugins/ariadne/skills/ariadne/SKILL.md`, the marketplace's canonical
  in-toto/DSSE evidence-statement contract.

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns the signal
contract. Four questions govern the unattended path:

1. **Where did this candidate stop?** CP-4 emits one structured state-change
   event for announce, upload, quarantine, validation, primary publication,
   replica confirmation, statement signing, acceptance, rejection, expiry, and
   revocation under one correlation id.
2. **Why can the controller not advance?** CP-6 reports the local transition,
   candidate, snapshot, last verified remote state, owner of the next retry,
   and bounded refusal code without printing grants or archive content.
3. **Can accepted state still be recovered without the live service?** CP-5
   reports primary/replica/statement read-back and CP-8 measures database,
   Droplet, and replica-only recovery.
4. **Is Atlas offering current state?** CP-9 reports GitHub and checkpoint
   source status/freshness separately and requires redraw when the bound
   snapshot, resolution, revocation, claim, or source state changes.

Metrics use small fixed state, route, dependency, and verdict label sets. Run
ids, snapshot ids, commits, issues, actors, URLs, and error text stay in bounded
events rather than metric labels. Every symptom alert links to the packet's
operator runbook and is fired once before the packet closes.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary review
and control standard.

- **Controller to archive.** Portable content is an allowlist assembled only
  at a green boundary. Exact sizes/digests, safe observation schema, clean
  worktree, signatures, receipt prefix, and excluded local state are checked
  before atomic export.
- **Archive to inspector.** ZIP and Git bytes are hostile. Parsing is bounded
  before extraction; paths and filesystem types are refused; Git runs with
  fixed argv, bounded output, hooks disabled, system/global configuration
  disabled, and no network.
- **Contributor to API.** Authentication and repository/run authorisation occur
  per request. The contributor receives one short-lived size/checksum-bounded
  quarantine grant, not AWS credentials or authority access.
- **Quarantine to validator.** The validator runs in disposable bounded
  compute with no signer or authority-write permission and no network while it
  inspects bytes.
- **Validator to authority.** Only a complete typed success becomes eligible
  for a version-specific locked write. Conditional/idempotent publication and
  exact read-back resolve ambiguous responses.
- **DigitalOcean to AWS.** Roles Anywhere exchanges a scoped X.509 workload
  certificate for short-lived role credentials. Trust-anchor, certificate,
  profile, session-policy, and revocation rules are explicit.
- **Publisher to signer.** KMS signs only the typed checkpoint statement domain
  with the pinned algorithm. The private key does not leave KMS; the public key
  and key-transition records make offline verification possible.
- **Mutable index to accepted truth.** PostgreSQL accelerates queries. Locked
  manifests, statements, revocations, resolutions, and object metadata rebuild
  it, and a comparison gates reopened writes.
- **Lineage to resolver.** A contributor can make a valid child but cannot
  choose a preferred frontier. The resolver signs the complete frontier and
  action; the service validates and records that decision.
- **Service to Atlas.** A separate redaction schema exposes routing facts and
  freshness only. Authenticated short-lived grants go directly to the selected
  verifier path and are not rendered as permanent links.

## 10. The budget, or its absence

This planning package makes no performance change, so there is no before/after
budget for this branch. [Metron](../plugins/hexaemeron/skills/metron/SKILL.md)
still gates the implementation packets: CP-3 records archive size, expanded
size, export/inspect/restore time, and peak memory on a fixed corpus before any
optimisation; CP-4 records route/dependency p95 and p99 plus validation queue
age under a fixed workload; CP-8 measures the 60-minute read-only and four-hour
full-recovery objectives from #567. Each target study must name the exact
measurement command and environment before code is kept. ZIP size and ratio
ceilings are security limits, not claims that the service is fast.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns reproduction,
cause, and guard evidence. Export stops on a dirty/unreceipted boundary, unsafe
observation, missing base/object/signature, identity mismatch, or nondeterministic
bytes. Intake stops on authentication, quota, checksum, schema, archive, Git,
receipt, parent, policy, replica, or signature uncertainty. The controller
keeps an external transition in `checkpoint_ready` or `publishing` while the
service is unavailable; outage is never an acceptance. Restore refuses a
non-empty destination, revoked or poisoned ancestry, missing exact object
version, invalid statement, or unsupported protocol version. Atlas disables or
redraws an action when its bound source facts are stale or changed.

Every observed defect follows the same rule: preserve exact command, bytes,
identity, state, and output; reproduce; name the causal boundary; add a guard
seen failing without the fix; run focused and full suites; then resume. After
three failed repair rounds on one belief, stop and ask the diagnostic question.
No fallback may skip a digest, signature, redaction, replica, or resolution
check to make the programme move.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns why these
choices earn durable records and where readers find them.

- Cumulative green-boundary checkpoints, immutable starting commit, semantic
  versus transport identity, and the acceptance sidecar:
  `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`.
- Protocol ownership in Skills, service ownership in a separate repository,
  and Atlas as a redacted client:
  `docs/decisions/ADR-029-separate-the-checkpoint-protocol-from-its-authority-service.md`.
- Replaceable DigitalOcean compute/index behind locked S3 primary/replica
  versions, Roles Anywhere, and KMS signing:
  `docs/decisions/ADR-030-use-s3-object-lock-behind-replaceable-digitalocean-compute.md`.
- Explicit external execution class and the signed publication fence:
  `docs/decisions/ADR-031-fence-external-fiat-transitions-on-signed-checkpoint-acceptance.md`.
- DAG lineage, advisory claims, signed resolution, revocation, reconciliation,
  and salvage:
  `docs/decisions/ADR-032-model-checkpoint-lineage-as-an-explicitly-resolved-dag.md`.

All five begin `Proposed, 2026-08-24`. The component issues carry operational
detail and their own runbooks; those details do not silently strengthen a
proposed record into accepted policy. ADR-022 remains owned by PR #539.
