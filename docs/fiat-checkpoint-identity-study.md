# Bind portable Fiat runs to an immutable base and checkpoint identity

Assuming, unless corrected:

1. Issue [#560](https://github.com/wildcat-finance/skills/issues/560) now owns
   only the minimum run anchor and checkpoint identity needed by
   [#561](https://github.com/wildcat-finance/skills/issues/561). It does not
   revive the retired checkpoint service, fork graph, acceptance, revocation,
   parent, or publication design.
2. [ADR-028](../docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
   settles the former CP-1 question: one run continues from a cumulative
   same-ledger checkpoint at a post-push or exhausted-audit boundary.
3. Open issues [#508](https://github.com/wildcat-finance/skills/issues/508)
   and [#547](https://github.com/wildcat-finance/skills/issues/547) remain
   boundaries. This delivery binds only controller-owned receipts and already
   verified commits; it neither makes delegated state portable nor turns a
   clone-local green check into a portable claim.
4. [#557](https://github.com/wildcat-finance/skills/issues/557), pull request
   [#772](https://github.com/wildcat-finance/skills/pull/772), and the amended
   ADR-028 are predecessor evidence. Their
   `fiat-controller-checkpoint/v1` manifest digest identifies the exact inner
   manifest bytes, whose inventory binds the controller capsule files. It is
   neither the capsule ZIP digest nor the semantic checkpoint identity
   specified here.
5. New runs may be anchored. A legacy run whose `state.base` is a symbolic ref
   cannot be re-anchored after that ref has moved; identity generation must
   refuse rather than infer history.
6. The present #560 delivery itself was initialized by the predecessor
   controller with symbolic base `main`. Its source-bound entry is
   `main@8c4073ed5db91986e74c4500867ba630cecce15b`; it cannot claim that the
   new run-anchor receipt existed at its own initialization.
7. Work starts from exact commit
   `8c4073ed5db91986e74c4500867ba630cecce15b` on
   `fiat/560-bind-portable-runs-to-an-immutable-base-and`, using the
   repository's Python 3.14.6 through `mise`, Fiat 5.35.1, and Hexaemeron
   1.6.10. The implementation adds no dependency beyond the Python standard
   library and Git.
8. A checkpoint identity is a digest over a closed, path-free projection of
   one verified controller checkpoint. An outer archive digest identifies the
   exact packed bytes. Equal checkpoint identity does not mean equal archive
   bytes, and #560 does not create those archive bytes.

## 1. Problem statement

Fiat currently starts a worktree from the operator's `--base` value and stores
that same value in `state.base`. The ordinary value is `main`. A later
checkpoint export calls `_checkpoint_ref_names()` and resolves that stored
name again. If `main` advances between initialization and export, the capsule
can name a different base commit from the one that created the run.

Pull request #772 added native export and restore for the ignored controller
directory. Its `MANIFEST.json` binds exact state bytes, ledger bytes, local
refs, and the file inventory. That digest is useful for exact relocation, but
it deliberately makes no claim that two carriers hold the same checkpoint
meaning. #561 therefore has no stable value to put beside an outer archive,
check during hostile inspection, and compare again after restore.

Build one controller capability for future runs:

- `init` resolves the requested starting ref to one full commit before its
  first filesystem mutation, creates the worktree from that commit, stores the
  commit in `state.base`, retains the named integration branch separately, and
  records a versioned `fiat-run-anchor/v1` receipt in the initial state and
  ledger event;
- `hexctl --dir <run-worktree> checkpoint identity` verifies the run at one of
  ADR-028's two checkpoint boundaries and prints a versioned, canonical JSON
  identity plus `snapshot_id`, without changing state or taking a mutation
  lock; and
- one pure identity builder accepts already captured state and ledger bytes so
  #561 can compute and inspect the same value inside its own bounded archive
  operation without a second, drifting read.

The working prototype is proved by this demo path:

```bash
mise exec python@3.14.6 -- python3 -m unittest \
  plugins.hexaemeron.tests.test_hexctl_checkpoint_identity.HexctlCheckpointIdentityTests.test_identity_survives_named_base_movement_and_separates_transport -v
```

The demonstration creates a run from `main`, advances `main`, reaches an
accepted checkpoint boundary, and proves all of the following:

1. `state.base`, the worktree parent, and the run anchor still name the commit
   resolved before initialization mutated the repository.
2. Re-running the read-only identity command over unchanged controller and Git
   evidence returns byte-identical identity JSON and the same `snapshot_id`
   after the named branch moves.
3. Changing only an outer carrier label or proposed archive digest does not
   change `snapshot_id`; changing the working commit, ledger prefix, receipted
   study or runbook digest, policy digest, or observation binding does.
4. A symbolic-base legacy state, a mismatched run anchor, an unreceipted
   working commit, a non-ancestor working commit, or a non-checkpoint phase
   refuses without writing state.

The focused module and complete affected checks are also success criteria:

```bash
mise exec python@3.14.6 -- python3 -m unittest \
  plugins.hexaemeron.tests.test_hexctl_checkpoint_identity -v
mise exec python@3.14.6 -- python3 scripts/run_checks.py
```

## 2. Prior art

### Current controller and predecessor delivery

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:1694` implements `cmd_init`.
  It currently runs `git worktree add ... args.base` and later stores
  `"base": args.base`. It does not freeze the ref first.
- The same file's `resolved_commit()` already resolves `<ref>^{commit}` through
  the bounded, fixed-argument Git runner and requires one full commit SHA.
  Initialization can reuse that boundary before mutation.
- `integration_base_of()` already distinguishes a full starting commit in
  `state.base` from the named branch in `config.git.base`. Pull request
  [#550](https://github.com/wildcat-finance/skills/pull/550) introduced that
  distinction for pinned-starting-base sync. A run begun from a named branch
  must copy that branch name into `config.git.base`; a run begun from a commit
  retains the configured integration branch.
- `controller_run_id()` already gives one stable run identifier from controller
  state. Once `state.base` is a commit, it can be recorded in the run anchor
  without introducing a second run-id convention.
- `_checkpoint_boundary()` already admits only a `done:push` ledger tail or an
  `audit-round` tail whose next directive is `audit-verdict`. The identity
  command must reuse it.
- `_checkpoint_manifest()` already checks exact captured state and ledger
  bytes, the ledger chain and tail fingerprint, bounded refs, and a sorted file
  inventory. Its SHA-256 identifies the exact inner `MANIFEST.json` bytes,
  whose inventory binds the controller files; it is not the digest of a ZIP
  carrier. The new identity builder may reuse its validated inputs but must
  not rename that manifest digest `snapshot_id`.
- `done_implement`, `audit-round`, and `done_push` already retain full SHAs in
  `verified_commits`. The last such SHA is the only working commit the new
  identity may accept. It must also be a descendant of the immutable starting
  base.
- `receipted_source()` verifies the exact study and runbook bytes against their
  phase receipts. `verify_observation_bindings()` verifies optional cumulative
  observation bindings. The identity binds their digests without claiming the
  observations are complete or externally true.

The #557 end-of-Step-4 checkpoint is
[issue comment 5462964518](https://github.com/wildcat-finance/skills/issues/557#issuecomment-5462964518).
It records outer ZIP digest
`f3506ee8c29f9f22fec92ae9559463e427d79395bc47b4b8ec6a5cf523e642ea`,
Git-bundle digest
`5804694dbb22434251d32d9309dadd5398adcf46d8e2d6ac5620b164718340dc`,
native capsule ZIP digest
`70b3874fd304694a83a6f8ad91c7b6f48ad453872c8184db9e5c369d988c53c3`,
and inner native manifest digest
`a954273f70dffad87f31f4cdbaa785035fa610eb3158fb7dfc51bf7c19b1b457`.
The separately published
[final #557 record](https://github.com/wildcat-finance/skills/issues/557#issuecomment-5463073498)
records completion. The four checkpoint values show why semantic identity,
inner manifest integrity, capsule carrier integrity, and outer carrier
integrity remain distinct.

### Last two merged pull requests touching the controller

The last two merged pull requests that changed
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` were read in full:

- [#772, `Add portable Fiat run-state recovery`](https://github.com/wildcat-finance/skills/pull/772),
  merged as `d8f9952682a25b437b476c78af7fea13af27ae97` on 29 August 2026. It shipped
  native controller capsule export and restore, amended ADR-028, and carried
  #560, #561, and #682 forward by name. Its body states that the new commands
  do not mint a canonical semantic checkpoint identity or deterministic outer
  archive. This study preserves that exact-byte contract and supplies only the
  missing identity layer.
- [#778, `Say when a remote branch is absent rather than miscounted`](https://github.com/wildcat-finance/skills/pull/778),
  merged at current base
  `8c4073ed5db91986e74c4500867ba630cecce15b` on 29 August 2026. It separates
  an absent remote branch from malformed `ls-remote` output. It changes no
  checkpoint, initialization, or identity decision and carries no additional
  #560 work.

### Current issue and decision boundaries

- #560 remains open. Its 26 August review said to rebase the proposed schemas
  on current receipts and wait for CP-1 plus the #508/#547 boundaries. ADR-028
  now settles CP-1. This study treats #508 and #547 as explicit exclusions,
  not as evidence that portable identity must wait.
- #561 remains open and says it is blocked by #560. It owns a deterministic
  cumulative archive, closed content manifest, `archive_sha256`, hostile ZIP
  inspection, export, empty-directory restore, Git bundle, proof material,
  and the issue comment that publishes its digest. None enters this build.
- #508 remains open and currently needs narrowing. Its delegated-write,
  exhausted-audit carryover, and executable-runbook-gate questions do not
  enter the identity projection. An agent handle, unreceipted carryover
  packet, or live delegation state cannot become identity evidence.
- #547 remains open. Its no-green-no-commit evidence is clone-local. This
  design binds signed commits and audit receipts already in the ledger but
  does not say that a prior green environment remains green after transport.
- #682 remains open. Current `CONFIG_SET_EXACT_PATHS` and
  `CONFIG_SET_PREFIXES` already refuse changing `audit.max_rounds`; this issue
  supplies no mutation dispatcher and does not weaken that refusal.
- ADR-029 through ADR-032 are retired historical records. Their service,
  authority, object-store, acceptance, revocation, stage, parent, and fork
  fields are not imported into the new schema.
- `docs/hexaemeron-checkpoint-programme-study.md` is marked historical. It is
  useful vocabulary for the distinction between a starting base, checkpoint,
  and carrier, but not current authority for a service or checkpoint DAG.

### Audit records

The whole-set synopsis currency check ran from the target root before any
synopsis was used and exited zero for all 36 source/view pairs:

```bash
mise exec python@3.14.6 -- python3 \
  plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
```

The in-scope authoritative sources and actual reading views are:

| Authoritative source | View read | Source SHA-256 | Reason in scope |
| --- | --- | --- | --- |
| `plugins/hexaemeron/audit/AUDIT.md` | verified sibling `AUDIT_SYNOPSIS.md` | `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f` | Fiat state, ledger, and controller baseline |
| `audit/AUDIT.md`, only the `Fiat run worktree` sections | verified sibling `AUDIT_SYNOPSIS.md` sections | `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa` | initialization worktree and path behavior |
| `audit/rounds/fiat-557-portable-run-state-recovery-r2.md` | verified sibling synopsis | `be675778f185cc625ade09826c153c08d98ba69fe92434422d6413eaafc3c856` | the immediately preceding checkpoint implementation |

The plugin audit records F-01 through F-09 as fixed and F-10 as accepted.
F-01 is directly relevant: every ledger entry now binds a state fingerprint.
F-03 and F-04 give malformed state and ledger stable refusals. The source has
missing legacy fields for `Audit schema`, `Covered`, `Not checked`, and
`Elenchus verdict`; each remains unknown. Its leads not pursued remain a
symlinked state directory across filesystems, concurrent invocations against a
single-driver state directory, ANSI in machine-facing JSON, and the unexercised
vendored Solidity audit skills. This delivery does not convert any of those
unknowns or accepted limits into a clean result.

The root `Fiat run worktree` sections contain no finding table. Their `Audit
schema`, `Covered`, `Not checked`, and `Elenchus verdict` fields are missing
legacy fields and remain unknown. Their leads not pursued are: the
check-to-create race, which `git worktree add` closes by refusing an occupied
path; a pre-existing `tmp/fiat/.gitignore`, which initialization does not
overwrite; a successful archive move followed by failed worktree removal,
which leaves a harmless tree after its state was archived; and zsh's lack of
implicit word splitting in one lint command. Base resolution must remain
before `git worktree add`, and the add still owns the occupied-path refusal.

The #557 run audit has ten rounds. Its complete finding/status inventory is:

- Step 1 round 1: no finding; Elenchus `null`.
- Step 2 round 1: S2-R1-01, S2-R1-02, and S2-R1-03 fixed in
  `38c12eb9b8085d6226503d88acfc3671d440e209`; Elenchus `guarded`.
- Step 2 round 2: S2-R2-01 fixed in
  `c0f79861272c4e0002130070ba18e592dcb2c5cf`; Elenchus `guarded`.
- Step 2 round 3: no finding; Elenchus `null`.
- Step 3 round 1: S3-R1-01 through S3-R1-11 fixed in
  `e89511281d15266075fb718493ede310a4052c4e`; Elenchus `guarded`.
- Step 3 round 2: S3-R2-01 through S3-R2-07 fixed in
  `dc776ee87d92f27c0603cc2107407820f0d3e284`; Elenchus `guarded`.
- Step 3 round 3: S3-R3-01 through S3-R3-03 fixed in
  `1cd7259ec4fdef34ea9d43ab8077f43b5988095a`; Elenchus `guarded`.
- Step 3 round 4: no finding; Elenchus `null`.
- Step 4 round 1: S4-R1-01 fixed in
  `dd0fa1e37c16c1dc94182c650e46cfa6d443b924`; Elenchus `guarded`.
- Step 4 round 2: no finding; Elenchus `null`.

Step 1 marked `decision-placement` and `predecessor-reuse` reviewed and the
other fourteen #557 risks not applicable. Step 2 marked `partial-restore`,
`path-relocation`, and `replay-clobber` not applicable and reviewed the other
thirteen. Steps 3 and 4 marked all sixteen risks reviewed. These exact
classifications remain authoritative for that source; the current run starts a
new register rather than inheriting them as current coverage.

The #557 `Not checked` fields retain: the non-Solidity waiver; outer archive,
GitHub, Drive, issue-note, key and proof publication; hosted CI and
GitHub-side signature verification; native macOS no-replace behavior;
same-account mutation after the final userspace identity check; integration-
time base sync and free-version selection; and PDF/UA or optional PDF text
extraction. Earlier rounds also deferred restore, hostile manifest parsing,
clone loss, and interruption injection until later #557 steps; those later
steps exercised the named cases and fixed the findings above. They did not
exercise the retained outer and host boundaries.

Its leads not pursued retain those same outer, host, macOS, accessibility, and
same-account limits; the fact that a userspace sequence cannot lock out another
process with the same account; Horos's post-audit synopsis candidate outside
the product file closure; and Brevitas diagnostics on mandatory one-row audit
tables. The final clean rounds confirmed the cumulative fixed trees, generated
copy equality, focused and affected test suites, signatures, provenance, and
lint results. They do not establish a semantic identity or outer archive.

Other root and per-run audits were excluded after inventory because they do
not change initialization, controller checkpointing, or checkpoint identity.
Their findings remain authoritative for their own products; exclusion is not a
clean verdict.

### Outside prior art

- Git's `rev-parse --verify <ref>^{commit}` resolves a ref to a commit object;
  a full Git commit id is immutable within the object model. The existing
  bounded Git reader is the implementation boundary.
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) records the wider JSON
  Canonicalization Scheme. This design does not claim full RFC 8785 support.
  It uses the controller's existing sorted-key, no-whitespace encoder over a
  deliberately smaller ASCII/string/integer object language.
- [FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final) defines
  SHA-256. A fixed domain prefix prevents an identity payload from being
  confused with another JSON digest in the repository.

## 3. Constraints and non-goals

The exact build entry is
`8c4073ed5db91986e74c4500867ba630cecce15b`. Python commands use
`mise exec python@3.14.6 -- python3`. The work stays in the canonical Fiat
controller, its generated portable copy, focused tests and fixtures, the Fiat
contract/reference/version records, ADR-028, and tracked study/runbook copies
selected by the runbook. Existing repository CI, license, and toolchain files
are reused.

The delivery is one capability. Base pinning supplies the run anchor that the
checkpoint identity requires; neither part can meet the problem statement
alone. They are ordered implementation steps, not separate studies.

The identity boundary covers only future anchored runs. Native #557 export and
restore remain available to legacy states, but `checkpoint identity` refuses a
legacy symbolic base, absent anchor, or inconsistent anchor. There is no
automatic migration and no operator flag that relabels old evidence.

The following stay out of scope:

- #561's ZIP or other archive construction, file-content manifest, archive
  byte digest, hostile archive parser, Git bundle, proof transcript, key,
  empty-directory restore, Drive upload, issue digest, and publication;
- #508's delegated agent confinement, executable runbook gates, and
  exhausted-audit carryover;
- #547's portable green-gate or no-green-no-commit claim;
- #682's mutation dispatcher or any new controller transition;
- service accounts, daemons, queues, object stores, KMS, acceptance,
  revocation, fork resolution, parent graphs, checkpoint stages, or
  cross-repository trust;
- changing ADR-028's two checkpoint boundaries;
- changing `fiat-controller-checkpoint/v1`, native restore semantics, or the
  exact controller-capsule manifest digest; and
- a performance claim, Solidity, dependency, CI, storage-layout, or public ABI
  change.

The build boundary is:

- **Always.** Resolve the base and controller version before the first init
  mutation; use fixed-argument bounded Git; verify state, ledger, receipts,
  anchor, boundary, working commit, and ancestry before printing an identity;
  keep the command read-only; run the focused and affected suites before each
  commit; run Imprimatur on every shipped document; sign and verify each commit
  with the repository identity and required provenance.
- **Ask first.** Add a dependency; change the state version, native capsule
  schema, storage layout, public CLI beyond the named read-only command, CI,
  checkpoint boundary, trust boundary, or released digest meaning; admit a
  legacy re-anchor or any #508/#547/#561/#682 work.
- **Never.** Hash a moving ref as the starting base; infer a legacy base;
  include an absolute path, credential, live agent handle, timestamp, observed
  branch tip, archive digest, or service/fork field in `snapshot_id`; mutate
  state from the identity command; weaken a verification to make a fixture
  pass; edit vendored files; commit a credential; delete a failing test; or
  claim a command ran when it did not.

## 4. Design options

### Option A -- pinned init anchor plus a closed semantic projection (chosen)

Resolve the starting ref once, store the full SHA in `state.base`, retain the
named integration branch in `config.git.base`, and place a versioned run anchor
under the init-owned receipts. At an accepted checkpoint boundary, derive a
small identity object from verified controller evidence and hash its canonical
bytes with a fixed domain prefix. Expose that computation through a read-only
command and a pure helper that #561 can call over one captured snapshot.

This is the cheapest design that meets #561's dependency. It reuses the
controller's existing Git, receipt, ledger, boundary, and observation checks.
The trade is a hard legacy refusal and one new schema: old symbolic-base runs
can still relocate through #557, but they cannot acquire an identity they did
not record at initialization.

### Option B -- call the #557 manifest digest `snapshot_id`

This adds almost no code. It loses because the manifest is an exact transport
record: it includes file inventory, state bytes, resource limits, and path-
affected controller state. It cannot express the required distinction between
one checkpoint meaning and differently packed outer carriers. It would also
rewrite the claim already shipped by #557.

### Option C -- let #561 invent identity while building the outer archive

This keeps #560 empty. It loses because identity would exist only inside one
carrier implementation, and inspection could not distinguish a changed
checkpoint from harmless carrier repacking without understanding archive
policy. It would also leave initialization based on a moving ref.

### Option D -- revive the original service and checkpoint-DAG schema family

This could model parents, forks, stages, acceptance, revocation, authority,
and object-store publication. It loses because ADR-029 through ADR-032 retired
that programme, #561 needs none of it, and each field would add an authority
claim this local controller cannot prove.

### Chosen schema and computation

Initialization records this closed receipt, with no null values:

```json
{
  "schema": "fiat-run-anchor/v1",
  "controller": {
    "name": "hexctl",
    "state_version": 1,
    "version": "fiat-v5.36.1"
  },
  "initial_base_sha": "<full-commit-sha>",
  "integration_branch": "main",
  "repository": "wildcat-finance/skills",
  "run_branch": "fiat/560-bind-portable-runs-to-an-immutable-base-and",
  "run_id": "fiat-<sha256>",
  "task": {
    "kind": "github-issue",
    "number": 560
  }
}
```

Under `VERSIONING.md`, `fiat-v5.36.1` is the valid isolated generation target
from current `fiat-v5.35.1`; integration must still choose the next free Fiat
version rather than blindly retaining the example. For a canonical GitHub issue, initialization derives
`repository` from the credential-free target origin and requires the issue
repository to match it. A non-GitHub task uses
`{"kind":"external","sha256":"<digest-of-exact-url>"}`. No task uses
`{"kind":"unbound"}`. If a GitHub repository cannot be derived, the run may
still initialize with an explicit unbound repository status, but checkpoint
identity refuses until a future separately specified binding exists; #560
does not add a post-init binding mutation.

The initial ledger event carries `run_anchor_sha256`, calculated over the
receipt's canonical bytes. `run_anchor` joins `study`, `runbook`, and
`run_observations` in the reserved receipt namespace. Verification accepts
legacy absence but checks any present anchor against `state.base`,
`config.git.base`, `run_branch`, task receipt, repository, controller, and
`controller_run_id(state)`.

The identity command prints one object:

```json
{
  "schema": "fiat-checkpoint-identity-result/v1",
  "identity": {
    "schema": "fiat-checkpoint-identity/v1",
    "run": "<the exact fiat-run-anchor/v1 object>",
    "boundary": {
      "kind": "post-push",
      "step": 2,
      "working_commit_sha": "<full-commit-sha>"
    },
    "evidence": {
      "ledger_entries": 31,
      "ledger_sha256": "<sha256>",
      "ledger_tail": "<sha256>",
      "observation_bindings": 0,
      "observation_sha256": "<sha256-of-canonical-empty-status>",
      "observation_status": "absent",
      "policy_sha256": "<sha256>",
      "run_anchor_sha256": "<sha256>",
      "runbook_sha256": "<sha256>",
      "state_fingerprint": "<sha256>",
      "study_sha256": "<sha256>"
    }
  },
  "snapshot_id": "<sha256>"
}
```

The exact field contract is:

- `run` is the verified anchor object, not a fresh observation of the named
  branch.
- `boundary.kind` is exactly `post-push` or `audit-verdict`.
  `boundary.step` comes from the verified tail receipt, and
  `working_commit_sha` comes from the final full entry in that step's
  `verified_commits`. It must exist locally and descend from
  `run.initial_base_sha`.
- `ledger_sha256` hashes the exact verified appendable ledger prefix;
  `ledger_entries`, `ledger_tail`, and `state_fingerprint` make the joined
  evidence explicit. Relocation later appends a new receipt and therefore
  creates a later checkpoint identity rather than rewriting this one.
- `study_sha256` and `runbook_sha256` are the current verified phase-receipt
  digests, including any receipted amendments.
- `policy_sha256` hashes a closed projection of `config.skills`,
  `config.audit.max_rounds`, `config.audit.fold`,
  `config.audit.stacked_suffix`, `config.solidity`, and
  `config.git.draft_pr`. It excludes `git.origin`, `git.worktree`,
  `audit.log_path`, and values already fixed by the run anchor. The projection
  schema and exact fields live in the identity reference and fixtures.
- If observation bindings are present, `observation_status` is `bound`, the
  count is exact, and `observation_sha256` hashes their canonical ordered
  array after the existing verifier succeeds. If absent, the status is
  `absent`, the count is zero, and the digest hashes the fixed object
  `{"schema":"fiat-checkpoint-observations/v1","status":"absent"}`.
  An unavailable observation receipt remains a bound receipt; the identity
  does not promote it to an accepted capture.

The identity language is a closed JSON subset: ASCII field names and enum
values, lowercase hexadecimal digests, non-negative decimal integers, exact
objects, and the already validated ASCII branch and repository forms. It has
no floats, null, timestamps, unordered sets, or unvalidated strings. The
controller's existing `canonical()` function supplies sorted keys and no
insignificant whitespace. The hashed bytes have no trailing newline:

```text
snapshot_id = sha256(
  b"wildcat-fiat-checkpoint-identity/v1\0" + canonical(identity).encode("utf-8")
)
```

The result wrapper, indentation used for display, proposed `archive_sha256`,
outer filename, compression, file order, permissions, timestamps, absolute
paths, current `main` tip, and #557 capsule manifest digest are outside those
hashed bytes. #561 may bind them beside `snapshot_id`; it may not insert them
into the identity object.

The command takes one stable read of state and ledger, runs the ordinary
verification, derives the identity, and checks that the source bytes and refs
did not change before it prints. The reusable helper consumes already bounded
bytes and validated ref values rather than reopening paths. It returns data or
raises a fixed refusal; it never writes. This lets #561 join identity to one
archive capture without a gap between two independent reads.

### Recommended runbook shape

1. **Record and pin the run anchor.** Commit the tracked study/runbook copies
   and ADR-028 amendment, add the init-time anchor schema and base-resolution
   change, reserve and verify the receipt, and guard named-base movement plus
   legacy behavior. Existing license, toolchain, and CI files are reused;
   schema fixtures and the focused test module are created here.
2. **Build the checkpoint identity provider.** Add the closed projection,
   policy and observation digests, boundary/working-commit checks, domain-
   separated encoder, pure captured-bytes helper, read-only CLI, hostile and
   differential fixtures, reference contract, generated runtime copies, and
   version/evolution records.
3. **Demonstrate the #561 hand-off.** Run the problem-statement demo with a
   moved `main`, prove carrier-only changes are excluded and semantic changes
   alter the digest, prove every legacy or mismatched case refuses, then run
   the focused and affected checked suites. This step does not create an outer
   archive.

## 5. Risk register seed

```risk-register
base-resolution-race | init between operator ref input and worktree creation | the ref is resolved before mutation and the worktree is created from that exact commit
integration-branch-loss | split between immutable starting commit and named delivery branch | a named input branch is retained in config.git.base and commit inputs retain the configured integration branch
legacy-reanchor | symbolic-base states created before the anchor schema | identity refuses absence or a symbolic base without guessing a historical commit
anchor-mismatch | init receipt against mutable controller state | verification joins repository task run branch integration branch controller run id and initial base to the reserved anchor
repository-substitution | target origin and task issue repository | canonical GitHub identities match before the anchor is recorded and unbound repositories cannot mint an identity
boundary-substitution | controller phase and ledger tail | only the existing post-push and audit-verdict boundary classifier supplies identity input
working-commit-substitution | receipted step head against local Git history | the full verified commit exists and descends from the immutable base
ledger-prefix-substitution | state and append-only ledger at identity time | chain tail count exact bytes and state fingerprint agree and remain stable through the read
canonical-json-drift | semantic object at the hashing boundary | the closed schema has golden bytes duplicate-type refusals and one domain-separated encoder
policy-projection-drift | mutable and path-bound controller config | a versioned closed projection includes behavior policy and excludes relocation paths with differential tests
observation-overclaim | optional run-observation receipts | absence and binding are distinct and bound observations pass their existing verifier without claiming completeness or truth
semantic-transport-confusion | checkpoint identity beside capsule and future archive digests | carrier fields cannot enter the hashed projection and semantic mutations always change snapshot_id
path-or-secret-leak | identity JSON and refusal output | absolute paths credentials task URLs and unvalidated input are absent or reduced to fixed identifiers and digests
concurrent-read | state refs or ledger changing during identity generation | the command rereads bounded source identities and refuses rather than printing a mixed snapshot
scope-bleed-508-547 | open delegation and clone-local green-gate work | tests and prose bind only existing receipts and commits and make no portable execution or green claim
scope-bleed-561-682 | future archive and dispatcher work | no archive bytes publication restore dispatcher or mutation authority enters this delivery
schema-compatibility | new anchor and identity beside legacy state and checkpoint v1 | legacy verify export and restore remain available while identity requires the new exact schema
```

Audit must enumerate every id as reviewed or not applicable in every round.
The original #557 risks remain relevant historical evidence but are not aliases
for this register.

## 6. Glossary seeds

- **Starting ref.** The operator's branch or commit input to `init`, used only
  long enough to resolve one starting commit.
- **Immutable base.** The full Git commit SHA resolved before initialization
  mutates the repository and stored in `state.base`.
- **Integration branch.** The named branch a completed run targets; its name is
  recorded separately from the immutable starting commit, and its moving tip
  is not part of checkpoint identity.
- **Run anchor.** The init-owned `fiat-run-anchor/v1` receipt joining repository,
  task, run, controller, branch, and immutable starting commit.
- **Checkpoint boundary.** One of ADR-028's two accepted controller states:
  immediately after `done:push`, or at an active exhausted-audit verdict.
- **Working commit.** The last full commit SHA already verified and receipted
  for the boundary's step.
- **Semantic identity.** The closed, canonical, path-free evidence projection
  whose domain-separated SHA-256 is `snapshot_id`.
- **Native manifest digest.** #557's SHA-256 over exact inner
  `fiat-controller-checkpoint/v1` `MANIFEST.json` bytes; the manifest inventory
  binds the controller files.
- **Native capsule ZIP digest.** SHA-256 over the exact ZIP carrier around the
  native capsule; it is distinct from the inner manifest digest.
- **Carrier digest.** #561's future `archive_sha256` over exact outer archive
  bytes; it is not `snapshot_id`.
- **Policy projection.** The versioned subset of controller configuration that
  can change how the run proceeds and is stable across relocation.
- **Legacy run.** A state created before `fiat-run-anchor/v1`, especially one
  whose `state.base` is a symbolic ref.

## 7. Sources

- [Issue #560](https://github.com/wildcat-finance/skills/issues/560), including
  its 26 August 2026 review.
- [Issue #557](https://github.com/wildcat-finance/skills/issues/557), its
  [end-of-Step-4 checkpoint](https://github.com/wildcat-finance/skills/issues/557#issuecomment-5462964518),
  its [final record](https://github.com/wildcat-finance/skills/issues/557#issuecomment-5463073498),
  and [pull request #772](https://github.com/wildcat-finance/skills/pull/772).
- [Issue #561](https://github.com/wildcat-finance/skills/issues/561), including
  its current `blocked by #560` review.
- [Issue #508](https://github.com/wildcat-finance/skills/issues/508),
  [issue #547](https://github.com/wildcat-finance/skills/issues/547), and
  [issue #682](https://github.com/wildcat-finance/skills/issues/682).
- [Pull request #778](https://github.com/wildcat-finance/skills/pull/778) and
  [pull request #550](https://github.com/wildcat-finance/skills/pull/550).
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at
  `8c4073ed5db91986e74c4500867ba630cecce15b`.
- `plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`.
- `docs/fiat-controller-checkpoint-study.md` and
  `docs/fiat-controller-checkpoint-runbook.md`.
- `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`.
- Retired `docs/decisions/ADR-029-*.md` through `ADR-032-*.md` and historical
  `docs/hexaemeron-checkpoint-programme-study.md`, read only to keep their
  retired boundaries out.
- The three audit sources and verified views named in item 2.
- [Protasis](../plugins/hexaemeron/skills/protasis/SKILL.md),
  [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md),
  [Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md),
  [Metron](../plugins/hexaemeron/skills/metron/SKILL.md),
  [Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md), and
  [Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md), active plugin
  contracts versioned with this run.
- Git `rev-parse` documentation, RFC 8785, and FIPS 180-4 as identified in
  item 2.

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) governs signal design.
This is an interactive, read-only command rather than an unattended service,
so it adds no retained log, metric, trace, alert, or runbook. Its stable JSON
stdout and fixed refusal stderr answer these operator questions:

1. **Which immutable base and run does this checkpoint claim?** The `run`
   anchor names the repository, task, run id, branches, controller, and full
   starting SHA.
2. **Which boundary and product commit does it bind?** `boundary.kind`,
   `boundary.step`, and `working_commit_sha` answer together.
3. **Which evidence prefix produced the digest?** The evidence object names
   state, ledger, study, runbook, policy, and observation digests and counts.
4. **Why was no identity printed?** Fixed refusal classes name legacy anchor,
   boundary, receipt, Git ancestry, source-drift, or schema failure without
   echoing hostile values.

The implementation and final demonstration steps emit those outputs. #561
owns any retained export/inspect/restore events and their correlation.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) governs these off-chain
boundaries.

| Capability | Boundary and value at risk | Control | Evidence status at study time |
| --- | --- | --- | --- |
| Init base pinning | operator ref crosses into Git argv; starting-history integrity | conservative ref/commit validation, fixed argv, bounded Git, full-SHA result before mutation, worktree created from SHA | existing primitives verified; new composition asserted pending tests |
| Repository/task anchor | target origin and task receipt cross into persistent identity; repository substitution | credential-free canonical GitHub parser, origin/issue match, closed fallback status, init-only reserved receipt | existing parsers verified; anchor join asserted pending tests |
| Checkpoint identity | state, ledger, receipts, config, and Git objects cross into digest authority | ordinary verification, closed schema, exact types and caps, ancestry check, stable reread, no shell, no write | asserted pending hostile and differential tests |
| Observation binding | optional companion record crosses into semantic evidence | existing observation verifier, explicit absent/bound status, digest only, no truth or completeness promotion | existing verifier shipped; new projection asserted pending tests |
| #561 helper hand-off | captured bytes cross from a future archive inspector into identity computation | pure bounded-byte interface, no path reopen, same schema and golden fixtures as CLI | interface asserted pending implementation; archive remains unbuilt |
| Output | identity or refusal crosses to terminal and future archive | fixed field set, no absolute paths or credentials, unvalidated values not echoed | asserted pending sample-output and hostile-refusal review |

No dependency, host fetch, secret, model output, network service, personal data,
or destructive path enters the new capability. The Git subprocess remains the
only command boundary and uses an argument list.

## 10. The budget, or its absence

[Metron](../plugins/hexaemeron/skills/metron/SKILL.md) governs performance
claims. None is made. Initialization adds one bounded `rev-parse` and local
metadata projection; identity reads the already bounded state, ledger,
receipts, observation bindings, and a small fixed set of Git objects. Existing
controller caps and timeouts remain the resource limits. There is no
performance change to keep or revert and therefore no benchmark command or
numeric budget. A later measurement showing this path is slow would require a
recorded baseline before optimization.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) governs failure
triage and guard evidence.

Initialization refuses before its first mutation if the starting ref does not
resolve to exactly one full commit, the integration branch is unsafe, the
controller version cannot be read, or the anchor cannot be constructed. The
identity command prints no result and writes nothing when verification,
anchor consistency, boundary classification, receipt digests, observation
validation, working-commit resolution, ancestry, schema validation, or the
final stable reread fails. There is no legacy fallback and no partial identity.

The observed defect is mechanistic: `cmd_init` stores a symbolic ref and
`_checkpoint_ref_names` resolves it again at export time, so a moved branch can
change the recorded base. The first guard must demonstrate that behavior on
the unfixed parent. Every repair commit then uses the runbook's source-bound
Elenchus runner; its new test must fail by assertion on the parent, pass on the
fixed tree, and leave both focused and affected suites green. A missing,
zero-test, infrastructure-error, or mixed report is `inconclusive`, not a
guard.

Recovery from a refusal is explicit: restore the receipted state/ledger or Git
object, return to an accepted checkpoint boundary, or start a fresh anchored
run. Re-anchoring a legacy run is not a recovery path.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) governs record
placement.

The expensive-to-reverse choice is the split between an init-owned immutable
run anchor, a semantic checkpoint identity, the existing native manifest and
capsule-carrier digests, and #561's future outer carrier digest. It extends the accepted
cross-repository checkpoint decision, so the standing home is a dated
amendment to ADR-028. That amendment must state the chosen design, the hard
legacy refusal, and why manifest reuse, archive-owned identity, and the retired
service schema lost.

The callable schema and failures belong beside the interface in
`plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md`, with its
generated portable copy. The governed Fiat version and behavior change belong
in `plugins/hexaemeron/skills/fiat/EVOLUTION.md` and the matching generated
copy. The public invocation and boundary belong in the canonical Fiat
`SKILL.md`. The tracked study and runbook are delivery inputs, not standing
decision records. No second ADR or service record is created.
