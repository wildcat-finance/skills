# Study: portable Hexaemeron checkpoint archives and handover service

Assuming, unless corrected:

1. This Fiat run ships the design package, its standing decision records,
   executable document checks, and the contributor-guide correction. It does
   not deploy a service or add checkpoint commands.
2. Wildcat Labs originated this checkpointing design: preserve a contributor's
   complete Fiat delta and controller evidence at a stopping point so another
   contributor can resume it.
3. Every checkpoint in one run is measured from the exact commit used to create
   that run's first worktree. A later commit, push, patch, or merge from `main`
   never changes that anchor.
4. The first implementation supports issue-bound Fiat runs in public GitHub
   repositories. A run without a receipted task issue cannot enter the remote
   store.
5. Issue [#439](https://github.com/wildcat-finance/skills/issues/439) must land
   before portable import or controller integration. The format can be specified
   now, but no importer may restore into the caller's checkout.
6. The service is private by default. A public Atlas may reveal that an accepted
   checkpoint exists; it does not reveal archive bytes or a reusable download
   URL.
7. Python 3.11 and the standard library remain the controller baseline. Any
   service framework, database driver, object-store client, or authentication
   library is a later ask-first dependency with an exact pin and lockfile review.
8. The current run began at local `main`
   `346c1223e86d07635ebbdfc4d09850c6b865b136`. The run branch and its remote
   still point at that commit. `origin/main` later advanced to
   `65a514ed6699a5c9a81e49bbdee0b94b8f1cb563`; existing Fiat sync rules, not a
   rewritten base, handle that movement at integration.

I will proceed on these assumptions unless corrected.

## 1. Problem statement

Fiat deliberately keeps its state and hash-chained ledger under the ignored
`.hexaemeron/` directory. That protects ordinary Git history from controller
state, but it means a branch or pull request cannot carry a partly completed run
to another machine. Committed work transfers; the exact state, staged changes,
unstaged changes, untracked contribution files, current directive, and local
receipts do not.

Build a design package for a portable checkpoint. A contributor can stop after
any stable snapshot, including partway through a step. The checkpoint preserves
the complete contribution since the immutable initial base commit, the Git
history that retains authorship, the real index and unfinished worktree state,
and the verified controller state. A later contributor asks for the furthest
valid checkpoint for the issue, restores it into a fresh isolated worktree, and
receives the same next Fiat directive without any completed-phase claim being
invented.

The implementation topic is several capabilities and must decompose before
code:

| Module id | Responsibility | Depends on |
| --- | --- | --- |
| `run-anchor` | Record the immutable initial base SHA and isolated run identity at `init` | issue #439 |
| `archive-core` | Export, validate, and import one cumulative checkpoint package | `run-anchor` |
| `checkpoint-store` | Accept immutable packages, validate lineage, and return the furthest valid candidate | `archive-core` |
| `resume-routing` | Ask the store before new work, preserve Atlas random choice, and direct contributors to resume, redraw, or start | `checkpoint-store` |

Build order: `run-anchor`, `archive-core`, `checkpoint-store`, then
`resume-routing`. Each follow-up implementation is independently shippable and
gets its own Fiat study and runbook. This run fixes their common interface and
records the order; it does not combine their code into one unauditable step.

A working design-package prototype means these checks all exit 0:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study docs/hexaemeron-checkpoint-archive-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  docs/hexaemeron-checkpoint-archive-runbook.md
python3 -m unittest tests.test_checkpoint_archive_spec
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  docs/hexaemeron-checkpoint-archive-study.md \
  docs/hexaemeron-checkpoint-archive-runbook.md \
  docs/hexaemeron-checkpoint-archive-spec.md \
  docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md \
  docs/runbooks/hexaemeron-checkpoint-store.md \
  docs/how-to-help-shoggoth.md
```

The document tests must prove the Wildcat Labs provenance statement, immutable
base rule, package members, API routes, lineage refusal, #439 dependency, and
the difference between a live random Atlas route and a future checkpoint store.

## 2. Prior art

**The current controller.** The active branch contains Fiat `v5.10.1`. Its
state records `base: main`, the run branch, task receipts, phase, steps, and
configuration, but it does not record the commit to which `main` resolved at
initialization. Its three-entry ledger verifies at state digest
`eba57fc823464c41a81f42f4ad5ba23f2c742e33956c1bc81a81de20f5a6f599`.
The controller source is
`adf0fc24d650fdbb9d38b5b7ccb52320e5d76c1fbed0f3e9f303fa79a4d48167`.
These facts decide `run-anchor`: the checkpoint base cannot be reconstructed
from the mutable name `main` later.

**Dedicated-worktree work in flight.** Issue #439 specifies one worktree per
run, state inside that worktree, fail-closed creation, and no silent removal of
dirty work. It remains open. PR
[#467](https://github.com/wildcat-finance/skills/pull/467) is open against the
issue's run branch. Remote step branches hold the accepted worktree study,
path validator, and `init` implementation, but none is in this run's base or
in `origin/main` at the time of this study. The latest reviewed branch examined
here is
`ae834375df6c5bd3e6a9e5142840f80e94eed49c`; its state adds an absolute
`worktree` path but still stores only the base ref name. Its audit found and
fixed a dangling-symlink occupancy error and a breadcrumb design that blocked a
second concurrent run. It leaves two leads: the validation-to-create race
closes into Git's refusal, and a pre-existing `tmp/fiat/.gitignore` with
different content is not overwritten. The checkpoint design inherits those
facts instead of treating the branch as merged.

**Local design prior art.** Signed commit
`df48e05d60deece0953890f88b83345f76e7568e` on local branch
`codex/hexaemeron-checkpoint-archives` contains a checkpoint specification,
ADR-014, a service runbook, contributor-guide edits, and five document tests.
It established the cumulative package, Git bundle, separate index and worktree
patches, bounded ZIP profile, content-addressed store, and visible lineage
conflict. It was never pushed or accepted. This study keeps those useful
choices and corrects four gaps:

- stage was caller-supplied, so a large number could pretend to be progress;
- the state did not yet carry the exact initial base SHA;
- export, service acceptance, and an archive digest were not separated enough
  to avoid a receipt/digest cycle; and
- the contributor guide assumed the Atlas change rather than reading the live
  route and current checked-in guide together.

**Contributor route already shipped.** PR
[#459](https://github.com/wildcat-finance/skills/pull/459) added the contributor
guide's checkpoint page and recorded that only pushed work transfers today. It
carried forward that the guide still told a contributor to choose work they
could finish, and that its Markdown copies had no enforced canonical source.
PR [#469](https://github.com/wildcat-finance/skills/pull/469) made the root
README point to the public Shoggoth Wave Atlas and state that contributors can
stop at checkpoints. Its README now says the Atlas draws randomly from every
open Wave issue whose recorded hard dependencies are closed.

The live `GET https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/api/job`
response uses `wildcat-wave-job/v1`, reports random selection, and currently
draws from 73 eligible issues. Its prompt already asks the assistant to start
or resume, announce each checkpoint, and let the contributor stop. The checked-
in `docs/how-to-help-shoggoth.md` still says to pick an issue one can finish and
still describes an earliest-open-Wave selector as proposed. The design package
must reconcile that stale guide without implying the checkpoint service exists.

**Recent controller work.** PR
[#445](https://github.com/wildcat-finance/skills/pull/445) bound task issue URLs
to the initial state, ledger, and branch name. That is the issue identity the
checkpoint store must match. PR
[#474](https://github.com/wildcat-finance/skills/pull/474) merged after this run
was initialized and adds receipted append-only study amendments. Its carried-
forward list leaves runbook repair and general transaction rewrites open. A
checkpoint preserves those amendment events as ledger history; it does not
invent a general state-rewrite route. Existing Fiat integration sync is the
only route for taking the later `main` into this run.

**Audit sources.** The configured source is `audit/AUDIT.md`. The Fiat
state-shape rounds establish the refusal standard: state-backed commands share
one bounded diagnosis, failed mutation leaves state and ledger bytes unchanged,
and archived version-1 containers still verify. The task-issue rounds establish
that malformed identity is refused before state exists. The worktree branch's
rounds establish the path and concurrency findings above. The contributor-guide
rounds establish that a selector must be described as live or proposed
accurately and that a dated issue census is not a permanent priority claim. No
accepted round establishes portable checkpointing or a remote service.

**Formats and standards.** Git's bundle format carries refs, objects, and
explicit prerequisites; `git bundle verify` checks that the receiver has them.
Git binary full-index patches are made to be consumed by `git apply`. PKWARE
APPNOTE 6.3.10 defines the ZIP records but leaves application manifest meaning
to this profile. RFC 9530 supplies `Content-Digest` for HTTP message-content
integrity. RFC 9457 supplies machine-readable HTTP problem details. These
standards supply containers and fields; none proves that a Fiat checkpoint is
valid.

## 3. Constraints and non-goals

- **Starting ref.** Local `main` and the pushed run branch at
  `346c1223e86d07635ebbdfc4d09850c6b865b136`. The later remote-main SHA is
  evidence of ordinary base drift, not permission to change the run anchor.
- **Controller state.** Version-1 container and existing hash-chained ledger.
  Checkpoint fields are additive. Legacy runs without a recorded initial base
  SHA may keep running, but cannot export a version-1 portable checkpoint by
  guessing the base.
- **Format.** UTF-8 canonical JSON, SHA-256 content identities, Git bundle plus
  binary full-index patches, and one constrained ZIP profile. No pickle, shell
  archive extractor, or platform-specific filesystem record.
- **First repository boundary.** Issue-bound runs in public Git repositories.
  Private repositories, non-Git targets, submodule working-tree changes,
  shallow histories missing the base, and sparse-checkout semantics are
  refused in the first implementation.
- **Service boundary.** The API validates and stores checkpoints. It does not
  run implementation, merge branches, resolve divergent work, choose an
  author, or decide an issue is safe to work on.
- **Atlas boundary.** Random selection remains useful because it spreads new
  work across the eligible graph. It is not a claim lock. The assistant still
  checks live issue, assignment, branch, pull-request, and checkpoint state
  before starting.
- **Non-goals for this run.** Controller code, deployed API, object-store or
  database choice, service account creation, credentials, DNS, CI changes,
  PDF regeneration, Atlas deployment, retention policy, billing, and public
  archive access.
- **Always.** Both applicable suites before a commit; Imprimatur on shipped
  prose; Protasis on the study and runbook; exact member digests; negative
  archive specimens; no overwrite of an accepted object.
- **Ask first.** Add a dependency, choose the service repository, touch CI,
  create cloud resources, widen accepted repository types, expose downloads,
  alter state or ledger shapes, or change the Atlas API.
- **Never.** Commit a credential; archive a credential knowingly; extract an
  untrusted member by its supplied path; apply into the caller's checkout;
  rewrite the original base; force-remove dirty work; choose a lineage by
  upload time; edit a vendored Pashov tree; or claim a service or command is
  live when it is not.

## 4. Design options

**A. Cumulative controller package, immutable object store, and explicit
lineage (chosen).** Each archive is independently restorable from the exact
initial base. It contains a Git bundle for authored commits, patches for the
real index and unfinished worktree, a separately recomputable cumulative
base-to-snapshot patch, and verified `.hexaemeron` state. The service stores the
ZIP under its SHA-256, derives stage from parent-chain depth, and refuses a
forked furthest result. This repeats some bytes, but one missing earlier upload
cannot strand every later checkpoint.

**B. Incremental patch chain.** Store only the difference from the previous
checkpoint. It saves storage and upload bytes. Rejected because restore must
execute every earlier untrusted object in order, one missing object destroys
all descendants, and retention cannot delete an old object independently.

**C. Git branches and pull requests only.** Already deployed, preserves
authored commits, and needs no new service. Rejected as the complete solution
because it cannot preserve ignored controller state, index state, uncommitted
files, or the exact current directive. It remains the fallback until the
checkpoint modules ship.

**D. Complete worktree archive.** Simple to explain and likely to capture the
visible state. Rejected because it duplicates Git objects, includes ignored
build output, widens secret exposure, and weakens the exact relation to the
initial base.

**E. Store checkpoints as Git commits on a service branch.** Easy to host and
inspect. Rejected because committing unfinished index/worktree state changes
its meaning, `.hexaemeron` is intentionally ignored, and synthetic commits
confuse authorship with the uploader.

Option A is the smallest construction that preserves all three independent
truths: repository history, unfinished filesystem state, and controller
evidence. It trades storage efficiency for isolated verification and recovery.

### Package interface fixed by the design package

The display name is
`.hexaemeron-<issue>-step-<N>-stage-<M>.zip`. `N` is derived from controller
state. `M` is the verified parent-chain depth, starting at 1; it is never a
free caller claim. Before service acceptance the local file may use the suffix
`.pending.zip`. The accepted response returns the final display name.

Every ZIP contains only:

```text
manifest.json
git/commits.bundle
patches/cumulative.patch
patches/index.patch
patches/worktree.patch
state/.gitignore
state/ledger.jsonl
state/state.json
state/...
```

`git/commits.bundle` is absent only when the snapshot has no commit beyond the
initial base. `state/` excludes the lock, sockets, devices, FIFOs, earlier
checkpoint archives, and service credentials. Exclusions are named in the
manifest. Ignored repository bytes are excluded unless the runbook names them
as contribution input; an ignored path referenced by controller evidence is a
refusal, not a silent omission.

`manifest.json` uses schema
`wildcatlabs.hexaemeron.checkpoint/v1`. It records `design_origin` as
`Wildcat Labs`; canonical repository and issue identities; initial base ref and
full SHA; run branch, task-issue receipt, ledger genesis, and derived run id;
parent archive digest; derived step, stage, phase, and exact next directive;
controller identity, version, and source digest; head and status summary;
state digest, ledger length, and tail; and a sorted member table carrying path,
bytes, media type, SHA-256, and purpose. Creation time is recorded and never
used for ordering.

The archive is read-only with respect to the captured state. This avoids a
digest cycle in which a ledger event tries to contain the digest of an archive
that contains that event. Service acceptance records the archive digest and
authenticated uploader externally. Import appends one controller-owned event
binding the archive digest, old worktree identity, new worktree identity, and
the accepted manifest. A later export uses that digest as its parent.

### Service and data interfaces fixed by the design package

The first routes are:

```http
POST /v1/checkpoints
GET /v1/repos/{owner}/{repo}/issues/{issue}/checkpoints
GET /v1/repos/{owner}/{repo}/issues/{issue}/checkpoints/furthest
GET /healthz
GET /v1/operator/dependencies
```

Uploads use `Content-Type: application/zip`, RFC 9530 `Content-Digest`, an
idempotency key equal to the lowercase archive SHA-256, and a short-lived bearer
identity. `201` means newly accepted, `200` an exact idempotent repeat, `409` a
lineage or progress conflict, `413` a bounded-size refusal, and `422` malformed
or unverifiable evidence. Error bodies use RFC 9457 and a stable
`checkpoint/<code>` type.

The metadata store has four logical records: immutable object identity and
size; lineage identity keyed by repository, issue, initial base, run id, and
ledger genesis; accepted checkpoint keyed by archive digest with parent,
derived progress, validator version, and manifest; and upload attempt keyed by
request id with status and bounded refusal code. Rejected payload bytes are
deleted after the recorded refusal. Accepted object keys are content digests
and the ordinary service role has no delete permission.

The furthest route returns one candidate only when accepted checkpoints form
one unambiguous parent chain. A fork returns `409` with the competing manifests.
The operator cannot choose by timestamp. Stage is lineage depth, so a caller
cannot jump ahead by writing a large number.

### Resource profile

The first validator refuses more than 64 MiB of compressed request content,
256 MiB total declared or observed expanded bytes, 32 MiB in one member, 10,000
members, or 4 MiB in `manifest.json`, `state.json`, or `ledger.jsonl`. It
refuses encryption, duplicate or Unicode-normalisation-colliding names,
absolute paths, dot segments, backslashes, NUL, symlink or special-file ZIP
members, mismatched local and central headers, unsupported compression, and a
size count that changes while streamed. Repository symlinks remain representable
inside Git patches; they are not extracted as ZIP symlink members.

The service validates without materialising supplied paths. Import uses a fresh
temporary repository with system and global Git configuration disabled, hooks
disabled, no shell, fixed argv, bounded output, and no network until the named
origin and base are checked. It verifies the bundle prerequisites, runs Git
object checks, applies patches only after `--check`, extracts controller state
through fixed destinations, and promotes the restored worktree only after the
cumulative patch and next directive match.

## 5. Risk register seed

```risk-register
base-ref-drift | the mutable base name between init and a later checkpoint | init records the full initial base SHA in state and ledger, every package repeats it, and no export can derive it from current main
worktree-dependency | portable import against the unmerged issue 439 isolation work | archive implementation waits for accepted dedicated-worktree semantics and import refuses the caller checkout
state-repository-split | the controller ledger and repository bytes it describes | one manifest binds state, ledger, bundle, index patch, worktree patch, and cumulative patch by digest
caller-progress-claim | issue step and stage supplied by an uploader | issue and step derive from verified state while stage derives from accepted parent-chain depth
lineage-fork | two contributors continue the same checkpoint independently | both children remain visible and furthest returns 409 until a new explicit resolution checkpoint exists
archive-traversal | ZIP names and attributes crossing the validator boundary | streaming validation refuses path ambiguity, links, special files, duplicate names, header disagreement, and extraction by supplied name
archive-exhaustion | compressed input expanding or multiplying beyond service capacity | compressed, expanded, member, count, time, and temporary-space ceilings fail before publication
git-object-injection | bundle and patch bytes entering a restored repository | verify prerequisites, disable inherited Git configuration and hooks, run object checks, apply-check first, and use a fresh isolated worktree
changing-snapshot | files or controller state changing during export | hold the run lock and compare state, status, ledger tail, and member digests before and after package construction
secret-disclosure | repository delta or ignored controller state entering remote storage | fixed exclusions, secret-pattern refusal, private downloads, bounded logs, and an explicit statement that scanning does not prove absence
partial-upload | service failure between receiving bytes and publishing metadata | stream to a temporary object, verify digest, publish immutable object then metadata atomically, and never acknowledge droplet-only bytes
object-metadata-drift | accepted metadata naming a missing or replaced blob | immutable digest keys, no-delete runtime role, inventory checks, backups, and a restore rehearsal
controller-version-drift | exporter and importer disagree about state or directive semantics | manifest pins controller source, compatibility is explicit, and an unsupported importer refuses before state promotion
duplicate-work | Atlas random selection reaches an issue already being worked | client checks issue assignment, issue-number branches, pull requests, and furthest checkpoint before starting or offers a redraw
authorship-confusion | authenticated uploader differs from commit authors | uploader identity and commit authors are separate fields and neither rewrites the other
```

The secret scan is a guard, not a confidentiality proof. The service therefore
keeps downloads private even after the scan passes. The cumulative package is
also not a safety proof: a valid package can contain wrong code, an open audit,
or a study whose assumptions later changed.

## 6. Glossary seeds

- `Initial base`: the full commit SHA used to create the first run worktree,
  immutable for the run.
- `Snapshot`: the Git and controller bytes observed while the run lock is held.
- `Checkpoint`: an accepted snapshot package with a verified manifest and
  service record.
- `Cumulative patch`: a binary full-index patch from the initial base to the
  complete snapshot, including contribution files that were not yet committed.
- `Run id`: a digest of repository identity, task issue, initial base, run
  branch, and ledger genesis.
- `Lineage`: accepted checkpoints with one run id and an explicit parent chain.
- `Stage`: the accepted checkpoint's one-based depth in its lineage, not a
  completion claim.
- `Furthest valid`: the unique verified leaf of one lineage; no result exists
  when leaves conflict.
- `Uploader`: the authenticated account that submitted bytes, distinct from
  authors recorded in Git commits.
- `Promotion`: the point after which a validated temporary restore becomes the
  new run worktree and may receive controller commands.
- `Atlas redraw`: discard no work; request a different eligible issue when the
  selected one is already claimed and has no checkpoint to resume.

## 7. Sources

- `PROMISE_MACHINE.md`; `.agents/skills/promise-machine/SKILL.md`;
  `plugins/hexaemeron/AGENTS.md`.
- `plugins/hexaemeron/skills/fiat/SKILL.md`, `EVOLUTION.md`, and
  `scripts/hexctl.py`; `.hexaemeron/state.json` and `ledger.jsonl` at controller
  digest `eba57fc823464c41a81f42f4ad5ba23f2c742e33956c1bc81a81de20f5a6f599`.
- `plugins/hexaemeron/skills/protasis/SKILL.md` and the linked Phylax, Ephoros,
  Metron, Elenchus, and Hypomnema contracts.
- `audit/AUDIT.md`, including the Fiat state-shape, task-issue, contributor-guide,
  and issue-439 worktree rounds.
- [Issue #439](https://github.com/wildcat-finance/skills/issues/439), [PR
  #467](https://github.com/wildcat-finance/skills/pull/467), and remote worktree
  heads `2925c55`, `e2a4cdc`, `ae83437`, and `f7db227` observed on 22 August
  2026. These are in-flight evidence, not accepted base behaviour.
- Signed local prior-art commit
  `df48e05d60deece0953890f88b83345f76e7568e`.
- Merged PRs [#459](https://github.com/wildcat-finance/skills/pull/459),
  [#469](https://github.com/wildcat-finance/skills/pull/469),
  [#445](https://github.com/wildcat-finance/skills/pull/445), and
  [#474](https://github.com/wildcat-finance/skills/pull/474), including each
  carried-forward section.
- Live Shoggoth Wave Atlas `GET /api/job` and `GET /api/job?all=true`, schema
  `wildcat-wave-job/v1`, observed with 73 eligible issues on 22 August 2026.
- [Git bundle format](https://git-scm.com/docs/bundle-format), [git-bundle](https://git-scm.com/docs/git-bundle),
  [git-diff](https://git-scm.com/docs/git-diff),
  [git-apply](https://git-scm.com/docs/git-apply), and
  [git-worktree](https://git-scm.com/docs/git-worktree).
- [PKWARE APPNOTE 6.3.10](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT),
  [RFC 9530](https://www.rfc-editor.org/rfc/rfc9530.html), and
  [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html).

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal shape. The
follow-up modules run unattended and must answer four questions:

1. **Was this checkpoint accepted or refused, and why?** Export and upload emit
   one correlation id, archive digest when known, validator version, result,
   and stable refusal code. They never emit package content, credentials, or a
   signed download URL.
2. **Can an accepted checkpoint still be discovered and read?** A reconciliation
   job compares accepted metadata with object existence and digest, emitting
   missing-object and unowned-object counts.
3. **Has validation stopped making progress?** Upload events carry received
   bytes and validator phase; bounded metrics record queue depth, validation
   duration histograms, temporary bytes, and age of the oldest pending upload.
4. **Why could a contributor not resume?** Import emits controller schema and
   source identity, base availability, package verification result, next-
   directive comparison, and whether promotion occurred.

Metric labels are limited to route template, status class, validator version,
refusal code, and deployment region. Repository, issue, run id, account,
archive digest, request id, and error text stay in bounded events, not labels.
The service runbook owns alerts for readiness, dependency failure, missing
accepted objects, stalled validation, temporary-space pressure, failed backup,
and controller-version incompatibility.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and
controls.

- **Git repository to exporter.** Worth taking: authored history, exact delta,
  initial-base identity, and controller receipts. Control: a held run lock,
  exact base SHA from `init`, fixed-argv Git commands, bounded output, and
  before/after snapshot equality.
- **Controller state to package.** Worth taking: ledger authority and next
  directive. Control: current `hexctl verify`, manifest member digests, fixed
  exclusions, and no mutation during export.
- **Contributor package to service.** Worth taking: CPU, disk, parser behavior,
  metadata integrity, and stored secrets. Control: authentication, streaming
  byte caps, constrained ZIP profile, no supplied-path extraction, secret
  refusal, temporary object lifecycle, and stable problem codes.
- **Service metadata to object storage.** Worth taking: accepted-object
  durability and discovery truth. Control: digest keys, publish ordering,
  least-privilege roles, no-delete runtime permission, inventory comparison,
  and tested restore.
- **Service response to importer.** Worth taking: filesystem write, Git object
  store, run branch, and controller authority. Control: download digest,
  bounded revalidation, clean Git configuration, hooks disabled, fresh isolated
  worktree, apply checks, object checks, controller verification, and promotion
  only after all comparisons pass.
- **Atlas assignment to contributor action.** Worth taking: inference time and
  duplicate work. Control: random selection is only a candidate; live issue,
  branch, pull-request, and checkpoint discovery run before new work. An
  accepted checkpoint offers resume. Claimed work without a checkpoint offers
  redraw or explicit coordination, never a silent second run.
- **Identity to authorship.** Worth taking: credit and merge provenance.
  Control: authenticated uploader, Git authors, commit signatures, and later
  merge verification remain separately named evidence.

## 10. The budget, or its absence

This design-package run makes no performance change, so no before-and-after
measurement applies. [Metron](../plugins/hexaemeron/skills/metron/SKILL.md)
governs any later speed claim.

The byte and member ceilings in item 4 are security limits, not service-level
objectives. Before `checkpoint-store` chooses latency or throughput targets it
must record at least twenty representative exported archives, their compressed
and expanded sizes, member counts, validation times, and upload times. The
follow-up study then fixes one replayable command and p95/p99 thresholds. Until
that evidence exists, the runbook alerts on stopped progress, dependency
failure, and capacity percentage rather than invented latency numbers.

The design package itself is bounded by the commands in item 1. A document
test or lint without a zero exit leaves the package unready for a runbook
receipt.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns failure triage and
the guard rule.

Export stops without a package when the initial base SHA is absent or
unreachable, task issue is absent or mismatched, controller verification fails,
the index is unmerged, a submodule is dirty, an ignored evidence path would be
lost, the worktree changes during capture, a secret-shaped input is found, a
Git command exceeds its bound, or any package limit is crossed.

Upload stops before accepted metadata when content digest, canonical manifest,
member digest, ZIP profile, controller compatibility, parent, lineage, derived
progress, repository, or issue validation fails. An earlier accepted
checkpoint remains discoverable. A request interruption leaves only a temporary
object eligible for later deletion, never an accepted record.

Import stops before promotion when the package digest or any member fails,
the exact base cannot be fetched, bundle prerequisites fail, Git object checks
fail, a patch does not apply cleanly, state extraction crosses its fixed
destination, controller verification fails, the next directive differs, or the
recomputed cumulative patch differs. The caller's checkout, branch, index,
untracked files, and `.hexaemeron/` remain byte-identical.

Furthest discovery stops with `409` when two valid leaves cannot be ordered.
It does not pick the newest. Atlas routing stops or redraws when a live issue
is assigned, has an issue-number branch or pull request, or has an unresolved
dependency. It offers resume when one accepted checkpoint exists.

Every failure class above gets a named test first observed red on the unfixed
parent, then green with the control. Required positive specimens include
committed, staged, unstaged, deleted, renamed, executable, binary, symlink, and
untracked paths; a partial implementation with no phase receipt; a run that
merged newer `main` while keeping the original base; authored commits; twenty
idempotent concurrent uploads; one visible lineage fork; and restore on a
second machine-shaped fixture with the same next directive.

Required negative specimens include traversal and Unicode path collisions,
duplicate headers, encrypted and special members, archive bombs, digest drift,
broken ledger, edited state, missing base, dirty submodule, changing snapshot,
secret-shaped bytes, wrong issue, missing and stale parents, controller drift,
object loss, partial database publication, and an import aimed at the caller's
checkout. No test is deleted, weakened, or made to accept an infrastructure
error as a guard.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns placement.

- The cross-repository package, cumulative-base rule, lineage ordering, and
  no-last-write-wins choice belong in
  `docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md`.
  The record stays Proposed until #439 lands and `archive-core` proves its red
  specimens.
- The complete manifest, ZIP profile, export/import protocol, service API, data
  model, and acceptance matrix belong in
  `docs/hexaemeron-checkpoint-archive-spec.md`.
- The operational deployment, refusal handling, divergence response, backup,
  restore, and wake-up path belong in
  `docs/runbooks/hexaemeron-checkpoint-store.md`.
- The present contributor truth, random Atlas entrance, availability recheck,
  stop-anywhere promise, and explicit not-live checkpoint boundary belong in
  `docs/how-to-help-shoggoth.md`. The PDF is deferred because this run has no
  reproducible checked-in PDF build path.
- The common implementation order belongs in this study and its runbook. Each
  module's later design change gets its own study amendment or follow-up study;
  controller behavior goes in Fiat's `EVOLUTION.md` only when that behavior
  ships.
- Wildcat Labs design provenance appears once near the start of the standing
  specification and once in ADR-014's context. It is not inferred from the
  uploader, commit author, or service operator.

The design package is ready for runbook derivation when all twelve sections,
the module dependency order, chosen trade, service and data interfaces, risk
register, and exact checks above survive Protasis and Imprimatur. It establishes
that the package can be implemented from a recorded design. It does not
establish that checkpoint commands, the store, Atlas resume routing, or public
handover exist.
