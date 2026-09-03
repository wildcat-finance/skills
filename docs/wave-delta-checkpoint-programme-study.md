# Study: the Wave Delta distributed checkpoint programme

This study governs. It replaces the account in
`docs/hexaemeron-checkpoint-programme-study.md`, which recorded the service
design considered in August 2026 and kept its historical banner when
[ADR-028](decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
retired four of its five decisions.
[ADR-069](decisions/ADR-069-reinstate-the-distributed-checkpoint-layer-above-the-local-store.md)
reopened the programme on 2026-09-02, and ADR-070 through ADR-073 carry the four
retired decisions forward. What follows is the programme as it stands with those
records accepted and a controller that has shipped half of it.

Assuming, unless corrected:

1. The programme is records and documents until a delivery is separately
   authorised to write code. Nothing here creates a repository, provisions an
   account or changes Atlas.
2. A checkpoint is earned at a green, committed, signed, pushed and remotely
   verified transition, or at an exhausted audit loop. It is not an arbitrary
   dirty worktree.
3. The maintainer's decision of 2026-09-02 stands: #508 no longer gates #860,
   and #508 stays open in its own lane inside milestone 64.
4. #899 and #901 are `hexctl` controller defects. They leave milestone 64 for
   the Fiat frontier and are not programme work.

## 1. Problem statement

An outside contributor can finish real work on a Fiat run and have nowhere to
put it. The controller state that makes the work resumable is exact bytes on
one machine, and until somebody else can obtain and verify those bytes, the
next person starts again.

Half of that is now solved. `hexctl checkpoint export` writes a checked capsule
at an accepted boundary and `hexctl checkpoint restore` relocates it into a
fresh checkout on the same ledger. ADR-028's mandatory local hand-off makes the
save compulsory, so the bytes always exist. What does not exist is any way for
a second person to receive them: the transport is the local filesystem, and a
local archive helps only the machine holding it.

The programme's problem is therefore narrower than it was in August. It is no
longer "how do we capture a run" but "how does an accepted capture reach
somebody else, and how does the project decide which of several accepted
captures it carries forward".

## 2. Prior art

**What ships, in this repository.** Fiat is at `fiat-v5.49.1`.
`hexctl checkpoint export` and `hexctl checkpoint restore` supply controller
state capture, ref binding, ledger prefix verification and relocation under the
`fiat-controller-checkpoint/v1` capsule contract at
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`. That
contract fixes the canonical manifest, the closed file inventory with per-file
digests, the exact local ref-to-commit map, the appendable ledger prefix and
tail, a hostile-input read boundary with named refusal classes, atomic
no-replace publication, and a relocation transaction that appends one
`checkpoint:restore` entry to the same ledger. Export accepts exactly two
controller states: the ledger tail at `done:push` with no later mutating action,
and an exhausted audit loop where `next` returns `audit-verdict`.

On the default branch, commit `482172e7` adds two more pieces. Initialization
binds a run to one immutable starting commit through an init-owned
`fiat-run-anchor/v1` receipt, and `hexctl checkpoint identity` derives a semantic
checkpoint identity from that anchor and the accepted boundary, separately from
exact capsule and archive bytes. That commit reapplies pull request #1069 and is
the controller half of #860, which is still open.

**What the local hand-off already enforces.** ADR-028's amendment of 2026-08-30
makes a checkpoint compulsory at every accepted boundary. The destination is
derived from controller state, a save failure blocks the next directive, and the
agent may not ask whether to skip it. The outer archive around the capsule, its
Git bundle, its signature proof and its sidecars remain a manual procedure that
ADR-028 leaves in place.

**What the retired records proposed, and what carries them now.** ADR-029
through ADR-032 described a three-repository split, locked storage behind
replaceable compute, a signed publication fence and a lineage graph. All four
are Retired and keep their bodies. ADR-070 through ADR-073 carry each decision
forward rebased on `fiat-v5.49.1`, and each states which clauses it takes
verbatim, which it rebases and which it drops.

## 3. Constraints and non-goals

The programme adds records and documents. It does not create
`wildcat-finance/fiat-checkpoints`, stand up a service, touch a cloud account,
key, region or budget, or change Atlas. Each of those stays a separately
authorised delivery.

ADR-028 stays Accepted and every clause it holds stands. The local checkpoint
store under `<origin>/.hexaemeron/checkpoints/<run-worktree-name>/` remains the
only current transport, and no checkpoint operation uploads, posts, commits or
pushes until a later delivery accepts a transport that does.

The four retired records stay Retired. Their successors are additions, so a
reader arriving at a retired record finds a successor rather than an edited
body.

Nothing in this programme changes `hexctl`. A file under `plugins/` is outside
every step of the reinstatement delivery.

## 4. Design options

**Reopen by addition, with one successor per retired record.** Chosen, and
recorded as ADR-069. Five new files, no durable record rewritten, and each
reopened decision independently supersedable. The cost is the most prose of any
option and five ADR numbers held against a default branch other deliveries land
on.

**Reopen in place.** Flip four Status lines back to Accepted and rewrite
ADR-028's retirement paragraph. Rejected: it erases the retirement rather than
recording that it was undone, and rewrites five durable records to save writing
one.

**One composite record.** Reinstate the programme in a single record referencing
the four retired bodies. Rejected: four independent decisions could then only be
superseded together, and each retired record would still end with no successor.

**Overturn ADR-028.** Mark it Superseded and write its replacement. Rejected:
four shipped behaviours rest on ADR-028 alone, and overturning it leaves them
governed by a record that no longer stands.

## 5. Risk register seed

```risk-register
stale-shipped-claim | any statement here about what hexctl ships | every claim is read at a named commit and states that commit, because the default branch moved 58 commits during the delivery that wrote this study
banner-inversion | the historical study and runbook once this pair exists | the historical documents keep their banner and gain a dated forward pointer, and no governing document carries a no-longer-governs banner
pinned-digest-drift | docs/fiat-controller-checkpoint-study.md and its runbook | neither is in this programme's write set, and tests/test_fiat_checkpoint_decision_record.py holds their digests and runs at every step exit
estate-verdict-drift | the wave-atlas-review block on the nine estate issues | the block is drafted on disk, passes the prose gates there, and is published verbatim with a remote readback
dead-issue-links | every issue and pull-request number this study cites | each number is resolved against GitHub before the step citing it lands, and one that does not resolve is named as unresolved rather than linked
capsule-overclaim | any description of what the distributed layer still owes | nothing is described as absent that controller-checkpoint.md already specifies, and the capsule contract is cited rather than restated
scope-creep-to-code | the boundary between records and a hexctl change | no step opens a file under plugins/, and the step exit fails if git diff names one
```

## 6. Glossary seeds

- **Capsule.** The `fiat-controller-checkpoint/v1` directory `hexctl checkpoint
  export` writes: exact `.hexaemeron` bytes plus a closed manifest. Exact-byte
  evidence, not a semantic identity.
- **Outer archive.** The zip, Git bundle, signature proof and sidecars ADR-028
  keeps in a manual procedure around the capsule.
- **Local checkpoint store.** The fixed path
  `<origin>/.hexaemeron/checkpoints/<run-worktree-name>/`, the only current
  transport.
- **Semantic checkpoint identity.** What `hexctl checkpoint identity` prints: a
  name derived from the verified run anchor and the accepted boundary, which
  survives repacking the carrier.
- **Distributed layer.** What the programme adds above the local store: intake,
  signed acceptance, the external-run fence, and lineage resolution.
- **Standing successor.** A record carrying a retired record's decision forward
  and naming it, leaving the retired record in place as history.

## 7. Sources

- `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`, Accepted 2026-08-27 with amendments dated 2026-08-29 and 2026-08-30.
- `docs/decisions/ADR-069` through `ADR-073`, all Accepted 2026-09-02.
- `docs/decisions/ADR-029` through `ADR-032`, all Retired 2026-08-27, bodies preserved.
- `plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`, the capsule contract.
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md`, the mandatory step checkpoint and its derived destination.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `cmd_checkpoint_export`, `cmd_checkpoint_restore` and the `checkpoint` subparser block, read at `ff47f3070c8dce05c767b6c0dad65234c56870de`. The file has changed on the default branch since, so it is cited by symbol rather than by line.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, current `fiat-v5.49.1`.
- Commit `482172e7` on the default branch, which adds `cmd_checkpoint_identity` and amends ADR-028 with its run-anchor and checkpoint-identity section.
- Issues #859 through #867, #508, #899 and #901 in `wildcat-finance/skills`, each read on 2026-09-03. #547, #563, #564 and #569 do not resolve.

## 8. Signals, and the questions behind them

The programme emits nothing today, because nothing runs unattended. The signals
below belong to the first delivery that ships a service, and the questions are
the ones an on-call person would ask.

Is a checkpoint stuck, and on whose side? An external run waiting on acceptance
needs its waiting state, its idempotency key and the elapsed time visible, so
the answer is not a guess. Did an acceptance fail validation, or fail to reach
anybody? Those are different, and only the first is the contributor's problem.
Is the frontier ambiguous? A scope with two accepted siblings and no resolution
is a question for a resolver, and nobody sees it unless the count is reported.

Until then, one signal exists and is local: a step checkpoint that fails to save
blocks the next directive, which is a failure the operator sees immediately.

## 9. Boundaries, per capability

**Capture.** Reads the run worktree, writes one new directory. Refuses symlinks,
hard links, devices, duplicate JSON keys, non-finite numbers, oversized files
and a moving source. Specified and shipped.

**Local hand-off.** Writes under the origin checkout's `.hexaemeron/`, which is
self-ignored, so no checkpoint byte enters a product commit. Specified and
shipped.

**Upload.** Would cross the first real trust boundary: contributor bytes leaving
one machine for a service. Nothing is built. What it owes is authenticated,
size-bounded, checksum-bounded quarantine and an idempotency key, per ADR-070
and ADR-072.

**Acceptance.** Would hold the authority to say a checkpoint is real. Also
unbuilt, and the heaviest of the three: locked storage, replication, an
independent signer, and a statement naming the three identities ADR-071 binds.

**Discovery.** Would show a contributor what exists. Unbuilt. ADR-070 confines
it to a redacted view that helps somebody resume without learning archive
contents.

## 10. The budget, or its absence

There is no budget, because there is nothing to spend on: no account, no
region, no service. The one measured cost today is local disk. A step checkpoint
in this delivery is about 94 MB, and a run producing one per step accumulates
that per boundary in the origin checkout.

A deployment record is where a budget belongs, and ADR-071 says so: it drops the
provider commitments it inherited and requires whoever deploys to pick a
substrate and defend it.

## 11. The fail-closed posture

Capture already fails closed: an unaccepted boundary, a pending transaction, a
moving source or an occupied destination refuses before any output directory
appears, and a save failure blocks the next directive rather than advancing past
it.

The layer above inherits that posture by decision rather than by code. An
unavailable or ambiguous service leaves an external run waiting rather than
complete, with no offline bypass. A rejection preserves the refusal and the
archive identity. A revoked node and its descendants become non-resumable, and
salvage needs a signed resolution rather than a cleared flag. Two accepted
siblings hold the scope for a resolver instead of letting arrival order decide.

## 12. Decisions and their homes

The five accepted records are the programme's decisions, and they are in
`docs/decisions/`: ADR-069 for the reinstatement route, ADR-070 for the
protocol and service split, ADR-071 for storage authority, ADR-072 for the
publication fence, and ADR-073 for lineage. This study decides nothing that
those records do not.

The estate is nine issues under milestone 64, the Wave Delta distributed
checkpoints milestone. #859 is the epic. #860 binds portable runs to an
immutable base and checkpoint identity, and its controller half landed on the
default branch in `482172e7` while this delivery was open; the issue stays
open. #861 exports and
restores cumulative checkpoints. #862 builds intake, validation and publication.
#863 deploys the locked authority and signed receipt path. #864 fences external
runs. #865 represents and resolves concurrent descendants. #866 proves
reconciliation, revocation and disaster recovery. #867 routes contributors to
resume, redraw or start fresh.

Two decisions about the estate belong here rather than in a record. #508 no
longer gates #860: that is a maintainer decision recorded on 2026-09-02, not a
reading of the issue text, and #508 stays open in its own lane inside milestone
64, where its subject is exhausted-audit carryover and delegated writes rather
than checkpoint identity. #899 and #901 are `hexctl` controller defects by their
own titles; they leave milestone 64 for the Fiat frontier, because a controller
defect is not programme work and tracking it here would make the programme look
like it owns the controller.
