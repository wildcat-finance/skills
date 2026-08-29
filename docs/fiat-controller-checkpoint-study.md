# Portable Fiat run state recovery

Assuming, unless corrected:

1. Issue [#557](https://github.com/wildcat-finance/skills/issues/557) owns
   native recovery of one Fiat controller run after its source clone or
   worktree is lost. It does not own the whole Wave Delta publication service.
2. The standing checkpoint procedure from pull requests
   [#669](https://github.com/wildcat-finance/skills/pull/669) and
   [#671](https://github.com/wildcat-finance/skills/pull/671) remains the
   required outer transport. This work replaces its manual controller-state
   relocation, not its Git bundle, signature proof, Drive upload, issue-note
   trust anchor, outer sidecar, or explicit waiver.
3. A restore starts from an already verified and extracted controller capsule
   in a fresh checkout where the standing procedure has restored the declared
   Git refs. Archive extraction, key import, commit verification, and network
   publication stay outside the new commands.
4. Export is allowed only at the two boundaries accepted by
   [ADR-028](../docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md):
   a `done:push` ledger tail before the next action, or an exhausted audit whose
   current directive is `audit-verdict`.
5. Restoring changes only the location of the same run. It verifies the exact
   imported state and ledger first, preserves that ledger as an exact prefix,
   appends one relocation receipt, and does not execute the restored `next`
   directive.
6. The successor run starts at `main` commit
   `66da3817761415f31bd467140ac1510f77b91b62`, works on
   `fiat/557-portable-run-state-recovery-r2`, uses Fiat `5.33.1`, and runs the
   repository's pinned Python 3.14.6 through `mise`. It adds no dependency
   outside the standard library and Git.
7. The capsule is a controller-state directory with an integrity manifest. It
   is not the canonical checkpoint identity proposed by #560, an acceptance
   receipt, or the deterministic outer archive owned by #561.
8. The halted predecessor is recovery evidence, not completed successor work.
   Its study, runbook, commit, audit and prose drafts may inform this study,
   but every build step in this run receives a new Mason commit and a fresh
   Warden round. In particular, the first build step records the accepted
   decision in ADR-028 before or with publishing the tracked study and runbook;
   neither run artefact is a standing decision record.

## 1. Problem statement

Fiat 5.33.1 keeps `state.json`, `ledger.jsonl`, receipted study and runbook
bytes, step evidence, and recovery markers under one ignored `.hexaemeron`
directory. `state.json` also records absolute `origin` and `worktree` paths.
`hexctl load_state` can point back to a live worktree through a breadcrumb, but
when that worktree is gone it can only say to restore it or clear the
breadcrumb. It has no command that validates copied controller bytes, moves
them to a different checkout, rewrites the two location fields, and rejoins
them to the same ledger.

PRs #669 and #671 reduced the loss surface: after `done push`, a contributor
packages the complete state beside a Git bundle and proof, uploads it, and a
successor verifies it before use. That procedure means #557 is no longer
wholly unaddressed. Its remaining defect is that successful pickup still
depends on a person reconstructing a path-bound worktree and deciding how to
alter controller state without a controller receipt.

The first attempt at this delivery stopped at Step 1 prose. It had published
the study and runbook into a signed local commit, then its prose pass found
that ADR-028 did not contain the accepted controller capsule and relocation
decision. The runbook was amended to mark Step 1's exit broken and the run was
halted because Fiat 5.33.1 has no phase rewind. Recovery therefore starts a
new run with the decision-record obligation in the first build step; it does
not reuse the predecessor's clean-audit claim.

Build two controller commands for Fiat contributors:

```text
hexctl --dir <run-worktree> checkpoint export --out <new-directory>
hexctl --dir <fresh-origin> checkpoint restore --from <capsule> \
  --manifest-sha256 <64-hex-digest>
```

`export` writes a deterministic, bounded directory containing
`MANIFEST.json` and the complete `.hexaemeron` tree except the transient lock.
`restore` accepts that directory as hostile input, proves its manifest,
controller tree, ledger prefix, expected directive, and local Git ref
boundary, creates the run's ordinary derived worktree, relocates only the
controller-owned path fields, appends one `checkpoint:restore` event, and
recreates the origin breadcrumb. It ends by running the same internal checks
behind `verify`, `status`, and `next`, but acts on no returned directive.

A working prototype passes this offline clone-loss demo:

```bash
mise exec python@3.14.6 -- python3 -m unittest \
  plugins.hexaemeron.tests.test_hexctl_checkpoint.HexctlCheckpointTests.test_restore_after_source_clone_loss -v
```

The test creates a source repository and a run at an accepted boundary,
exports the capsule, removes the source clone, restores the declared refs into
a fresh clone, imports the capsule, and proves that `hexctl verify` succeeds
and `hexctl next` returns the same semantic directive recorded before export.

## 2. Prior art

### Current repository behaviour

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` writes state only in the
  active worktree. `commit()` appends a hash-chained ledger entry carrying the
  state fingerprint and then saves `state.json`; `verify_run()` checks both.
  `MUTATING` has no checkpoint command.
- `run_worktree_path()`, `check_worktree_path()`, the breadcrumb helpers, the
  bounded Git runner, the no-follow audit reader, and the amendment
  write-ahead transaction are implementation prior art. Restore should reuse
  their path, subprocess, and interruption rules instead of adding another
  convention.
- `cmd_reset()` archives only a verified completed run under the origin
  checkout and removes only a clean worktree. That local retirement path does
  not export an active checkpoint, move a run between clones, or replace the
  new commands.
- ADR-028 accepts same-ledger continuation at successful end-of-step and
  exhausted-audit boundaries. It rejects fresh-ledger inoculation, arbitrary
  snapshots, and Git branches alone. Its consequence names the gap this run
  closes: current state records local paths and makes no native relocation
  claim without a checked export-and-restore transition.
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md`, section
  `Step checkpoint`, is the current operational protection. It packages the
  Git bundle, complete controller state, manifest, public key, proof transcript,
  inner and outer sidecars, README, Drive object, and issue-note digests. Those
  parts remain in force.
- `docs/a-child-or-a-golden-retriever.md` correctly permits another machine to
  resume after a completed step through a verified checkpoint.
  `docs/a-child-or-a-golden-retriever-study.md` records that the older warning
  in `docs/how-to-help-shoggoth.md` is stale. The latter still says Fiat has no
  checkpointing and must be corrected, with its generated PDF rebuilt.

### Recovery predecessor

The halted predecessor lives at
`/home/kethcode/wildcat/skills/tmp/fiat/fiat-557-portable-fiat-run-state-recovery`.
Its state and ledger were checked directly without mutating them. All nine
ledger entries form one valid hash chain ending at ledger hash
`08d90dd536c6d5b898bcefbb89c155313a67252235e5fb4e0cca54f3f2a29389`;
the canonical state fingerprint is
`92a9dcce5a9aec8c210e4da87cd64a1d35975ddc3b081df32714639b267d2810`
and matches the last ledger entry. The state is halted in Step 1 prose.

The predecessor's exact study is SHA-256
`cfd00b107d0b942810f33a616bb9b9d9b56a78ad91a21f384b8c9a515a25f4a5`.
Its amended runbook is SHA-256
`2a09faf82c057dcab7af84a2fd940eeb1fe38d90397e9c29654e9f28ff5383ac`;
the baseline runbook was
`a68fdc95f4c42ec231cfcb3c2e015ae076681292f410266a0216260e49c49644`
and its appended amendment is
`039ac67c3aa7459966399ca798a8d3060caec042b2bc9fec0c8d8002195ddc71`.
That amendment says Step 1's entry holds and exit is broken, while Steps 2-4
retain their entries and exits. Its exact halt says ADR-028 lacks the accepted
capsule and relocation decision and Fiat 5.33.1 has no rewind or re-audit
transition.

Commit `af7945c7bca42032d4d5eca45c14029e86476bbb` contains only tracked copies
of that study and runbook. It has a valid Dave Coleman
`<dave@wildcat.finance>` SSH signature and exactly one required provenance
trailer pair. The step branch was not pushed and no pull request exists. The
draft task-issue comment still contains integration-URL and final-status
placeholders and was not published. Its useful content is carried here as
open work, not presented as delivery evidence.

### Last merged pull requests

The last two merged pull requests that changed the controller file were read
in full:

- [#733, `fiat: retire completed runs locally after verification`](https://github.com/wildcat-finance/skills/pull/733),
  merged 28 August 2026. It made `reset` archive verified terminal evidence in
  the origin checkout after final status and verification. Portable recovery
  keeps that completed-run cleanup intact and exports only ADR-028's active
  checkpoint boundaries. The body carried no unfinished item for #557.
- [#740, `Require Fiat integration PRs to close task issues`](https://github.com/wildcat-finance/skills/pull/740),
  merged 28 August 2026. It bound issue-backed integration to one recognised
  closing reference and reported `## Carried forward` as `None`. This run must
  preserve that final integration gate and close #557 through the run-level
  pull request, not a step pull request.

The last two merged pull requests that changed the standing outer checkpoint
procedure were also read in full:

- [#669, `Adopt the step checkpoint standing rule`](https://github.com/wildcat-finance/skills/pull/669),
  merged 27 August 2026. It added the complete-state and Git-bundle package,
  proof and Drive hand-off until Wave Delta is complete. Its open need for a
  smoother solution is carried forward as the two controller commands; its
  proof and publication duties remain non-goals.
- [#671, `Require the checkpoint zip's sidecar on Drive and name the waiver`](https://github.com/wildcat-finance/skills/pull/671),
  merged 27 August 2026. It made the outer sidecar mandatory and allowed only
  an explicit, recorded waiver. Both rules remain unchanged and apply around
  the controller capsule.

The last two merged pull requests that changed the continuation decision were
read in full:

- [#681, `Make Fiat continuation checkpoint-only`](https://github.com/wildcat-finance/skills/pull/681)
  made a restored checkpoint the only continuation path and retired the
  service/DAG proposal in ADR-029 through ADR-032.
- [#683, `Correct Fiat continuation to start a new bounded audit loop`](https://github.com/wildcat-finance/skills/pull/683)
  corrected #681's unsupported rounds 9-16 claim. A restored exhausted-audit
  state remains halted until a separately checked new-loop transition exists.
  This run must not add that transition.

### Related Wave Delta work

- #558 remains a programme rather than an immediate service build.
- #560 owns a canonical semantic checkpoint identity and remains open and
  blocked on its reviewed decision and receipt boundaries.
- #561 owns the deterministic, hostile-inspected cumulative outer archive and
  clean-machine restore and remains open and blocked by #560. This study stops
  at a transport-neutral controller-state directory plus integrity digest, so
  it does not silently implement either issue.
- #682 asks every Fiat mutation to join a verified preimage, Promise,
  directive, command, evidence, and atomic write. That broad dispatcher is not
  part of #557. The new restore is nevertheless one named recovery transition:
  it verifies the imported preimage, accepts only `checkpoint:restore`, records
  its evidence, and never advances the restored directive.

### Outside prior art

- Git's `gitformat-bundle` and `git-bundle(1)` define the object-and-ref
  transport already used by the standing procedure. A Git bundle does not
  carry ignored controller state, so the controller capsule complements it.
- Python's `os.replace` supplies same-filesystem atomic replacement. The
  existing amendment recovery shows why a rename still needs a durable marker
  around the larger, multi-directory worktree operation.
- SHA-256 from FIPS 180-4 supplies content integrity. The manifest digest in
  this design identifies exact manifest bytes; it does not claim the semantic
  identity reserved for #560.

### Audit records

From the successor target root, the whole-set currency command exited 0 for
all 32 discovered source/synopsis pairs before a synopsis was used; every
committed synopsis matched a fresh render:

```bash
mise exec python@3.14.6 -- python3 \
  plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
```

The predecessor tree's same command also exited 0 for its 33 pairs, including
its uncommitted run record. These are the in-scope sources and the exact views
read:

| Authoritative source | View read | Source SHA-256 | Why in scope |
| --- | --- | --- | --- |
| `plugins/hexaemeron/audit/AUDIT.md` | verified `AUDIT_SYNOPSIS.md` | `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f` | controller state and ledger integrity |
| `audit/AUDIT.md`, `Fiat run worktree` sections | verified `AUDIT_SYNOPSIS.md` sections | `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa` | worktree path, breadcrumb and retirement behaviour |
| `audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md` | verified sibling synopsis | `aedafae71bf2e254d2f5cc37a40fcf150f80a17fa478bfec4c7a2d2d39a40213` | the clone-loss recovery that left #557 open |
| `audit/rounds/docs-a-child-or-a-golden-retriever.md` | verified sibling synopsis | `36fe9aaadd8debd562342958b8394497d2889b267d0c484564ab0183353a2c2f` | the current verified-checkpoint hand-off claim |
| predecessor `audit/rounds/fiat-557-portable-fiat-run-state-recovery.md` | verified sibling synopsis and authoritative 15-line source | `18266ab444a8fb26dc2c34383d040d933c2e9db3fadabf31502888a9dddb1fdc` | the failed first attempt's audit conclusion |

The Hexaemeron plugin audit records F-01 through F-09 as fixed and F-10 as
accepted. F-01 binds state to each ledger fingerprint; F-03 and F-04 give
corrupt state and ledger stable refusals. `Audit schema`, `Covered`, `Not
checked`, and `Elenchus verdict` are missing legacy fields and remain unknown.
Its unpursued leads remain the symlinked-state-directory limit on `os.replace`,
single-driver concurrency, and ANSI in machine-facing JSON.

The root `Fiat run worktree` sections carry no finding table. Their `Audit
schema`, `Covered`, `Not checked`, and `Elenchus verdict` fields are missing
legacy fields and remain unknown. Their retained leads are the check-to-create
race, which `git worktree add` closes by refusing an occupied path; a
pre-existing `tmp/fiat/.gitignore`, which the controller does not overwrite;
the archive-move/removal split, which can leave a harmless tree after state has
moved; and one shell-specific lint invocation warning unrelated to product
semantics.

The issue-429 recovery has S1-R1-01 and S2-R1-01 fixed; rounds 1.2 and 2.2
found none. Every round's `Covered` line retains `signed-lineage`,
`receipt-provenance`, `merge-parent-order`, `base-drift`,
`conflict-resolution`, `controller-regression`, `version-collision`,
`audit-prefix-divergence`, `audit-record-relocation`,
`synopsis-name-collision`, `schema-topology`, `synopsis-drift`,
`partial-write`, `path-boundary`, `attribution-loss`, `scope-creep`, and
`integration-key-defect`; `version-collision` was not applicable in Step 1 and
reviewed in Step 2. `Not checked` retains the waived Solidity suite, native
Windows, live integration, release allocation or propagation, final
publication, and hard-kill cross-file atomicity. Elenchus was `guarded` in
each finding-bearing round and null in each clean follow-up. The unpursued
leads retain required integration sync, the documented generator crash limit,
Horos synopsis candidates, inherited resource warnings, and #557 as separate
open work. Recovering #429's product did not recover its lost controller run.

The beginner-primer record has S1-R1-01, S1-R2-01, and S1-R3-01 fixed; round 4
found none. All four rounds' `Covered` line retains `role-confusion`,
`current-state-drift`, `mascot-identity`, `generated-text`,
`reference-leakage`, `binary-review`, `accessibility-gap`, `layout-overflow`,
`source-output-drift`, `toolchain-gap`, `horos-currency`, `link-decay`,
`branch-authority`, and `scope-creep`. `Not checked` retains the waived
Solidity passes, first-reader comprehension, PDF/UA conformance, hosted CI or
pre-publication links, and unauthorised publication; round 4 also records its
explicit checkpoint waiver. Elenchus was `guarded` for rounds 1-3 and null for
round 4. S1-R3-01 is the relevant finding: an absolute prohibition on moving a
run hid the supported completed-step checkpoint path. The final leads retain
the distinction between an in-progress hand move and verified checkpoint
pickup, plus the stated PDF, dependency and publication boundaries.

The predecessor #557 audit reviewed all 14 original risk ids:
`boundary-selection`, `capsule-input`, `path-traversal`, `file-kind`,
`resource-exhaustion`, `concurrent-mutation`, `partial-export`,
`partial-restore`, `ledger-continuity`, `path-relocation`, `ref-substitution`,
`replay-clobber`, `secret-output`, and `directive-overreach`. Its `Not checked`
field retains the waived Solidity suite, runtime checkpoint behaviour,
hostile-input execution, interruption injection, clone-loss recovery, Git ref
restoration, suite reruns, GitHub/Drive publication, and PDF/UA conformance.
Elenchus is null and its table records no finding. Its `Leads not pursued`
claims the two tracked files were byte-identical to their receipts and lists
the clean structure, prose, boundary and signature checks, while explaining
the Brevitas B010/B011 conflict with the required audit schema. The later prose
pass disproved that round's implicit decision-placement conclusion: ADR-028 was
outside the two-file diff. This successor therefore treats the zero-finding row
as authoritative only for the exact old diff and requires a fresh Warden round
over ADR-028 and both tracked run artefacts.

The fiat-377 synopsis was inspected for scope. It audits Horos marker
classification, not checkpoint transport; its checkpoint authority is the two
issue comments cited by #669. The four `fiat-622-*` source/synopsis pairs were
also inspected by inventory and verified view: they audit the parallel test
runner and historical carryover product, and explicitly leave controller
mutation untested or unauthorised. Their findings remain authoritative for
those products but do not enter this controller-state design. Other per-run
and non-Hexaemeron plugin audits do not touch controller recovery and are
excluded rather than treated as clean evidence.

## 3. Constraints and non-goals

The exact entry is `main@66da3817761415f31bd467140ac1510f77b91b62` on
`fiat/557-portable-run-state-recovery-r2`. Commands and tests use
`mise exec python@3.14.6 -- python3`. The implementation is standard-library
Python plus fixed-argument Git subprocesses through the existing bounded
runner. It changes the Fiat controller, tests, its contract and ledger prose,
ADR-028, the checkpoint reference, and the stale contributor guide. It does
not add a service, dependency, secret, CI job, or Solidity.

Before controller code changes, Step 1 must amend ADR-028 with the accepted
controller capsule, same-ledger relocation receipt, separation from the outer
checkpoint, and rejected designs. The same step publishes tracked copies of
the accepted study and runbook and receives new implementation and audit
receipts. The predecessor commit is not cherry-picked as a substitute, and
the tracked study and runbook do not become the standing decision home.

The controller directory format is:

```text
<capsule>/
  MANIFEST.json
  controller/
    .gitignore
    state.json
    ledger.jsonl
    ...the remaining regular .hexaemeron files...
```

`MANIFEST.json` uses schema `fiat-controller-checkpoint/v1`. It records the
sorted relative-file inventory with byte lengths and SHA-256 digests, total
files and bytes, source state and ledger digests, ledger count and tail hash,
controller version, topic, run branch, current ref-to-commit map, the semantic
`_next_directive` value, and the digest of its canonical JSON. It carries no
timestamp, source absolute path, credential, live agent handle, service
receipt, `snapshot_id`, or claim of acceptance.

Resource limits are 4,096 regular files, 256 MiB total, 64 MiB per file, 1 MiB
for the manifest, 1,024 UTF-8 bytes per relative path, and the existing bounded
Git timeout and output cap. The lock, symlinks, devices, sockets, FIFOs, hard
link aliases, unsafe path components, duplicate JSON keys, and files that move
during capture are refused.

Non-goals are: creating or extracting ZIP files; creating, fetching, or
verifying the Git bundle; signing; GitHub or Drive publication; canonical
checkpoint identity; service acceptance; object lock; fork resolution;
cross-platform path syntax beyond the repository's supported Python hosts;
moving an in-progress phase; starting a new audit loop; changing `init`,
`resume`, `audit.max_rounds`, `reset`, or any existing receipt meaning;
recovering a capsule whose Git refs are absent; deleting an existing worktree
to make restore fit; and repairing or continuing the halted predecessor ledger.

Always:

- Run the focused checkpoint test, the full Hexaemeron suite, and the root
  checked runner before a commit.
- Run Imprimatur on every shipped prose file and Phylax, Ephoros, and
  Hypomnema on the changed controller, tests, and records.
- Complete Step 1's ADR amendment, tracked artefacts, fresh Mason commit and
  fresh Warden review before an export implementation may depend on them.
- Hold the run lock during export, use no-follow bounded reads, and verify the
  source again before making the capsule visible.
- Verify an imported capsule and all named Git commits before creating active
  controller state.

Ask first:

- Add a dependency, change CI, write outside the operator-named capsule and
  derived run paths, widen either accepted checkpoint boundary, change an
  existing state or ledger field, rewrite a released digest, or absorb work
  owned by #560, #561, or #682.

Never:

- Commit or print key material, credentials, tokens, or arbitrary captured
  file contents.
- Follow a capsule symlink, overwrite an occupied path, delete a conflicting
  worktree, treat branches alone as a receipt chain, edit the imported ledger
  prefix, or run the restored directive automatically.
- Reuse the predecessor's implementation or clean-audit receipt as a successor
  build receipt, describe a run artefact as ADR-028's substitute, delete a
  failing test, or claim a command, restore, signature check, upload, or
  clean-machine proof ran when it did not.

## 4. Design options

### A. Controller-state capsule and relocation receipt

Add the two commands above. Export captures only the controller tree and the
local ref boundary. Restore requires separately restored Git refs, checks the
capsule, stages the relocated state, appends one receipt to the exact ledger
prefix, installs the state atomically, and recreates the breadcrumb.

Trade: this is the smallest controller-owned change that closes the path
relocation gap, but the manual Git, signature, archive, and publication
procedure remains necessary.

### B. Automate the complete standing checkpoint

Have one command build the Git bundle and ZIP, export the key and proof, upload
to Drive, publish the issue note, download, extract, and restore.

Trade: the contributor gets one operation, but it combines secret handling,
archive parsing, network mutation, GitHub/Drive authority, service identity,
and clean-machine proof. It overlaps #560 and #561 and would make #557 depend
on unsettled Wave Delta work. Rejected for this run.

### C. Put state on a branch or private Git ref

Commit or push the ledger and state under the run branch or
`refs/hexaemeron/...`, then teach restore to fetch it.

Trade: ordinary Git transports some bytes, but the state contains local paths,
special refs are not fetched by default, product branches gain controller
material, and branch existence still does not prove the receipt prefix or
checkpoint boundary. ADR-028 already rejects Git branches alone. Rejected.

### D. Reuse the predecessor Step 1 and add the ADR later

Cherry-pick `af7945c7bca42032d4d5eca45c14029e86476bbb`, treat its zero-finding
audit as complete, and append ADR-028 during export work.

Trade: this appears to save one documentation cycle, but it repeats the exact
record-placement fault that halted the predecessor and advances dependent work
on an audit that never examined the decision home. Rejected. The successor's
first step owns the ADR amendment, tracked run artefacts, and fresh Mason and
Warden evidence together.

### Choice

Choose A, with the Step 1 recovery rule from D's rejection. It introduces one
new data boundary and one recovery mutation, reuses the existing outer
transport, preserves the same ledger, and leaves the blocked identity/archive
work visibly open. Its accepted cost is that contributors still follow
`push-discipline.md` around the controller commands and this successor repeats
the specification publication step under a correct decision record.

The restore transaction uses a durable marker at the fresh origin before
`git worktree add`. It creates or reuses only the marker-owned derived
worktree, stages the complete relocated controller tree beside its final
`.hexaemeron` name, verifies the candidate, and renames the directory into
place. A rerun distinguishes marker only, worktree plus partial stage,
installed state without breadcrumb, and completed state with an uncleared
marker. It resumes or confirms those states and never removes an unowned path.

Success is testable:

1. The first build step adds a dated ADR-028 amendment naming option A, its
   outer-transport trade, and rejected options B-D before or with tracked copies
   of the accepted study and runbook. Byte identity, Protasis, Hypomnema,
   Imprimatur, repository suites and a fresh Warden round all pass; the focused
   `test_step_one_records_decision_before_controller_code` guard rejects the
   entry tree and accepts the complete Step 1 tree.
2. Two exports from unchanged state at either accepted boundary have identical
   manifests and file bytes, checked by
   `test_export_is_deterministic_at_both_boundaries`.
3. Export at every other ledger/directive combination refuses without an
   output directory or state change, checked by
   `test_export_refuses_every_unaccepted_boundary`.
4. The clone-loss demo passes offline and the restored `verify`, `status`, and
   `next` results are recorded by `test_restore_after_source_clone_loss`.
5. The imported ledger is byte-identical through its old tail; exactly one
   `checkpoint:restore` entry follows it and binds the manifest, source state,
   source ledger, old tail, and relocated state fingerprint, checked by
   `test_restore_preserves_prefix_and_appends_one_receipt`.
6. Only `origin` and `worktree` change in imported state before that receipt;
   opaque evidence files are copied, never rewritten. The semantic next
   directive is identical before and after relocation, checked by
   `test_restore_relocates_only_controller_paths`.
7. Manifest, inventory, state, ledger, ref, symlink, special-file, size,
   duplicate-key, path, second-restore, and every interruption-window guard
   refuses or recovers with no half-active run; the focused
   `HexctlCheckpointTests` module enumerates each specimen by name.
8. `docs/how-to-help-shoggoth.md` no longer says checkpoints are absent, its
   generated PDF agrees, and the beginner primer's verified-transfer rule
   remains unchanged, checked by the contributor-guide builder and
   `tests.test_child_or_golden_retriever_primer`.
9. The focused test, Hexaemeron suite, selected root checks, prose lints, and
   `git diff --check` all exit 0 under the pinned interpreter.

## 5. Risk register seed

```risk-register
decision-placement | ADR-028 versus the study and runbook artefacts | Step 1 records the accepted capsule, relocation receipt and rejected designs in ADR-028 before dependent code and receives a fresh Warden round
predecessor-reuse | the halted predecessor evidence versus successor receipts | old artefacts remain cited evidence only and no successor step receipts an old commit, audit or prose draft as new work
boundary-selection | the ledger tail and current directive accepted by export | only done:push-before-next-action or audit-verdict states export and all other phases leave no output
capsule-input | the operator-supplied controller directory and MANIFEST.json | bounded no-follow parsing rejects malformed UTF-8, duplicate keys, missing or extra inventory entries, and digest drift
path-traversal | every manifest path and operator path | components are relative and normalised, resolved targets stay inside their owner, and occupied destinations refuse
file-kind | the copied controller tree | only regular files and directories are accepted; symlinks, hard-link aliases, devices, sockets and FIFOs refuse
resource-exhaustion | manifest and recursive controller-tree reads | per-file, file-count, path-length, total-byte, Git-output and timeout caps apply before allocation or copy
concurrent-mutation | the live state while export reads it | the run lock is held and state, ledger tail and inventory are rechecked before atomic publication
partial-export | the operator-named output parent | a private sibling stage is fsynced and renamed once; interruption never leaves a valid-looking final capsule
partial-restore | the fresh origin, derived worktree, stage and breadcrumb | a durable marker makes every interruption window rerunnable without deleting an unowned tree
ledger-continuity | imported ledger prefix and relocation append | source bytes and tail verify first, the old prefix is unchanged, and one event carries the candidate state fingerprint
path-relocation | absolute origin and worktree fields in state.json | only those controller-owned fields change and verify/status/next run against the derived target paths
ref-substitution | Git refs restored separately from the capsule | every manifest ref resolves locally to the exact recorded commit before the state becomes active
replay-clobber | a capsule restored twice or into an occupied run | existing state, breadcrumb, checked-out branch or non-marker-owned path refuses without overwrite
secret-output | copied state files, diagnostics and manifest fields | no environment value or arbitrary file content enters the manifest or diagnostics and output permissions are private by default
directive-overreach | the recovery command versus the restored next action | restore records relocation only, compares the semantic directive, and never executes or authorises it
```

Warden should pay particular attention to the Step 1 decision home, any reuse
of predecessor evidence, the two multi-path interruption windows, hostile
filesystem entries, and whether a ref mismatch can be noticed only after state
becomes active.

## 6. Glossary seeds

- **Controller capsule:** the bounded directory containing the integrity
  manifest and copied `.hexaemeron` bytes; not the outer checkpoint archive.
- **Source prefix:** every imported ledger byte through the tail named by the
  manifest.
- **Relocation receipt:** the single `checkpoint:restore` event appended after
  the source prefix and bound to the new state fingerprint.
- **Semantic directive:** canonical JSON from `_next_directive`, before worker
  paths or delegation fields are added.
- **Ref boundary:** the sorted local Git ref names and exact commit ids required
  by the copied state.
- **Accepted boundary:** successful `done:push` before another action, or an
  exhausted audit currently returning `audit-verdict`.
- **Outer checkpoint:** the standing-rule ZIP, sidecar, Git bundle, proof, key,
  Drive object, and issue note outside the controller capsule.
- **Marker-owned worktree:** a derived path named by the durable restore marker
  and safe for that transaction to resume; every other path is unowned.
- **Standing decision record:** ADR-028 after Step 1's dated amendment; the
  study and runbook remain source-bound run artefacts.
- **Recovery predecessor:** the halted first attempt whose exact bytes explain
  the restart but authorise no successor receipt.

## 7. Sources

- Issue #557 and its 26 August 2026 Wave Atlas review:
  <https://github.com/wildcat-finance/skills/issues/557>
- PR #733: <https://github.com/wildcat-finance/skills/pull/733>
- PR #740: <https://github.com/wildcat-finance/skills/pull/740>
- PR #669: <https://github.com/wildcat-finance/skills/pull/669>
- PR #671: <https://github.com/wildcat-finance/skills/pull/671>
- PR #681: <https://github.com/wildcat-finance/skills/pull/681>
- PR #683: <https://github.com/wildcat-finance/skills/pull/683>
- Issue #558: <https://github.com/wildcat-finance/skills/issues/558>
- Issue #560: <https://github.com/wildcat-finance/skills/issues/560>
- Issue #561: <https://github.com/wildcat-finance/skills/issues/561>
- Issue #682: <https://github.com/wildcat-finance/skills/issues/682>
- Fiat-377 end-step checkpoint and clean-container proof:
  <https://github.com/wildcat-finance/skills/issues/377#issuecomment-5435028801>
  and
  <https://github.com/wildcat-finance/skills/issues/377#issuecomment-5435304048>
- `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`
- `plugins/hexaemeron/skills/fiat/SKILL.md`
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md`
- `docs/how-to-help-shoggoth.md`
- `docs/a-child-or-a-golden-retriever.md`
- `docs/a-child-or-a-golden-retriever-study.md`
- `.horos/boundary.json`
- The five audit sources and read views named in section 2.
- Predecessor `.hexaemeron/{state.json,ledger.jsonl,study.md,runbook.md,task-issue-comment.md}`
  and its audit source and synopsis at the absolute recovery path named above.
- Git bundle format: <https://git-scm.com/docs/gitformat-bundle>
- Python `os.replace`: <https://docs.python.org/3/library/os.html#os.replace>
- FIPS 180-4: <https://csrc.nist.gov/pubs/fips/180-4/upd1/final>

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) applies only to the
bounded command result. These commands are interactive and do not run as a
service, so they need no retained metrics, trace, dashboard, or alert.

1. **Was the source at an accepted boundary?** Export emits one stable result
   carrying the boundary kind, ledger count and tail, semantic directive,
   file count, byte count, manifest digest, and final destination.
2. **Did restore validate the exact controller and Git inputs?** Restore emits
   one stable result carrying the manifest digest, source state and ledger
   digests, verified ref count, old tail, new tail, and derived worktree.
3. **Where did an interrupted restore stop?** The durable marker records a
   bounded stage name and status; a rerun reports which known window it found
   and the one recovery action it took.
4. **What may happen next?** Successful restore prints the checked `verify`
   count, status summary, and semantic `next` directive without acting on it.

Default diagnostics use fixed messages and do not echo manifest-supplied
paths, file contents, exception payloads, or environment values. A `--json`
form carries the same bounded fields for tests and hand-off evidence.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) applies.

- **Predecessor evidence to successor work:** old files are trusted only as
  cited history and could be mistaken for current receipts. Exact digests,
  separate run identities, no cherry-pick shortcut, and fresh step commits and
  audits close this boundary.
- **Accepted design to durable record:** a study or runbook can be copied while
  the standing ADR remains silent. Step 1 puts the dated decision, rejected
  options and outer-transport separation in ADR-028 before any controller code
  depends on it; Hypomnema and a fresh Warden review close the boundary.
- **Live controller tree to export:** an accidental or raced filesystem entry
  could escape the copy or exhaust it. Descriptor-relative no-follow reads,
  stable pre/post metadata, regular-file checks, and the declared caps close
  this boundary.
- **Capsule to restore:** all manifest and file bytes are hostile even if their
  outer ZIP was verified. Exact schema, duplicate-key refusal, closed inventory,
  digest checks, path containment, file-kind checks, and an out-of-band
  manifest digest close it.
- **Capsule paths to filesystem writes:** path traversal or a symlink could
  redirect a stage. Existing worktree path validation, private sibling stages,
  final-component no-follow checks, exclusive creation, and refusal on any
  occupied unowned path close it.
- **Manifest refs to Git:** a crafted ref can become an option or select the
  wrong commit. Existing branch-name validation, fixed argument lists with no
  shell, `--` where supported, bounded Git, and exact commit comparison close
  it.
- **Multi-path restore mutation:** a kill can split marker, Git worktree,
  staged state, final state, and breadcrumb. Marker-first operation, an
  offline-complete candidate, atomic state-directory rename, fsync, and
  idempotent rerun rules close it.
- **Potentially sensitive controller evidence to output:** the capsule may
  contain PR drafts and audit diagnostics. Mode 0700 directories, mode 0600
  files, no content echo, no environment capture, and documentation that the
  operator must protect the outer package close the new disclosure path. The
  command does not claim to detect an already-written secret.

No dependency, URL fetch, model output, or credential enters either command.

## 10. The budget, or its absence

[Metron](../plugins/hexaemeron/skills/metron/SKILL.md) does not apply to a
performance change: the prototype makes no latency or throughput claim, and
the commands are bounded interactive copies. The 4,096-file and 256-MiB limits
are safety ceilings rather than performance targets. They are checked by the
focused suite:

```bash
mise exec python@3.14.6 -- python3 -m unittest \
  plugins.hexaemeron.tests.test_hexctl_checkpoint.HexctlCheckpointTests.test_resource_limits_refuse_before_publish -v
```

If a later change claims that export or restore is faster, it must record a
same-fixture baseline and result under Metron before that change is kept.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) applies to the
observed clone-loss failure, the predecessor's decision-placement failure, and
any failure found during the build.

Step 1 stops unless ADR-028, the tracked study and runbook, byte identity,
Protasis, Hypomnema, Imprimatur, both repository suites and a fresh Warden
round agree. A predecessor receipt cannot satisfy that guard.

Export stops before publication on a wrong boundary, pending controller
transaction, failed `verify`, moving input, unsafe file, cap, manifest error,
or occupied destination. Restore stops before active state on any digest,
inventory, state, ledger, directive, ref, repository path, worktree, or marker
mismatch. It never clears a conflict, falls back to `init`, reconstructs a
receipt, weakens a check, or advances `next`.

The principal implementation guard is
`test_restore_after_source_clone_loss`: it must fail on the entry controller
because no export/restore interface exists, then pass on the implementation.
The record-placement guard must fail if Step 1 omits ADR-028 or describes the
study or runbook as the durable home. Each audit fix follows the runbook's exact
Elenchus report command: first show the new focused test as an assertion failure
with zero infrastructure errors on the unfixed parent, then pass it and both
repository suites on the fixed tree. Interruption tests inject a stop after
each durable operation and rerun the same command, proving either a clean
refusal with no active state or one verified completed restore.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) applies.

- The expensive choice to ship a controller-state capsule while leaving the
  outer archive and semantic identity separate belongs in a dated amendment to
  existing ADR-028. That amendment must land in the successor's first build
  step, before or with the tracked study and runbook, and must name option A,
  its retained manual-transport trade, and rejected options B-D. A new ADR
  would duplicate the standing checkpoint decision.
- `docs/fiat-controller-checkpoint-study.md` and
  `docs/fiat-controller-checkpoint-runbook.md` are reviewed run artefacts. They
  point to ADR-028 and remain byte-identical to their receipted sources; they
  are never described as the standing decision record. Step 1 receives a fresh
  Mason commit and Warden round over all three documents.
- The public `fiat-controller-checkpoint/v1` manifest and command interface
  belongs in
  `plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`, with
  arguments, fields, caps, refusals, restore transaction states, and examples.
- The Fiat version, Promise, consequence, recovery rule, and rejected scope
  belong in the next generation row of
  `plugins/hexaemeron/skills/fiat/EVOLUTION.md` and the matching contract in
  `plugins/hexaemeron/skills/fiat/SKILL.md`. This run does not close or rename
  Fiat's held `state-shape-validation` frontier or issue 363 target.
- The operational hand-off belongs in
  `plugins/hexaemeron/skills/fiat/references/push-discipline.md`: it should use
  controller export before packaging and controller restore after outer
  verification, while retaining the sidecar, waiver, key, proof, Drive, and
  issue-note rules.
- The contributor-facing correction belongs in
  `docs/how-to-help-shoggoth.md` and its generated PDF. The beginner primer
  already states the right completed-step boundary and should change only if a
  test shows disagreement.
- The recovery-predecessor identity and failure are recorded in this study and
  its tracked copy, with exact state, ledger, study, runbook, amendment, commit
  and audit digests. They explain why the new run exists but do not replace
  ADR-028 or authorise a successor receipt.

No alert runbook is needed because section 8 adds no alert. Any decision made
after this study that changes these homes, caps, schema, accepted boundaries,
or predecessor-use rule requires a dated study amendment before implementation.
