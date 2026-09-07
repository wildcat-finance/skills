# Study: preserve immutable Fiat checkpoint identity across restore

Assuming, unless corrected:

1. Issue #860 is limited to the remainder in its 3 September 2026 review. The
   immutable init anchor and `hexctl checkpoint identity` shipped in commit
   `482172e7`; this run closes only the restore join and its refusals.
2. A semantic checkpoint has one identity before and immediately after a
   verified relocation. Host paths and the appended relocation receipt describe
   transport, not new progress.
3. Version 1 keeps exactly the two accepted checkpoint boundaries: immediately
   after `done:push`, and an exhausted audit loop whose next directive is
   `audit-verdict`. The user's decision in this run explicitly excludes
   arbitrary intra-step, between-round, or mid-audit distributed checkpoints.
4. The existing `fiat-controller-checkpoint/v1` capsule, restore transaction,
   `fiat-run-anchor/v1`, and `fiat-checkpoint-identity/v1` stay version 1. This
   work adds no outer archive, service, acceptance, revocation, or lineage
   protocol.
5. The exact starting commit is
   `66f43a0e07865daf526036ad1efbf98e3e27deac`. No later movement of `main`
   changes that anchor or this study's entry state.

## 1. Problem statement

Fiat already gives a newly created run an immutable anchor and can print one
semantic identity at either accepted checkpoint boundary. It also relocates a
verified controller capsule into a fresh checkout while preserving the same
ledger and appending one `checkpoint:restore` receipt. Those two shipped halves
do not yet compose: the identity classifier accepts a tail event of
`done:push` or `audit-round`, while a successful restore necessarily leaves
`checkpoint:restore` at the tail. The restored run verifies and returns the
same next directive, but `checkpoint identity` refuses it as though relocation
had changed checkpoint meaning.

The user is a contributor receiving a checked local capsule. A working
prototype restores that capsule through the existing command, verifies the
same run anchor, reconstructs the immediately preceding accepted boundary from
the exact imported ledger prefix, and prints byte-identical identity JSON and
the same `snapshot_id` as the producer printed. No controller action is
executed by identity or restore.

The proving path is one focused round trip in a fresh checkout:

```text
producer checkpoint identity -> producer checkpoint export
fresh checkout checkpoint restore -> verify -> checkpoint identity
```

The check compares both identity result byte strings. Negative cases alter the
restore receipt, imported prefix, allowed relocation fields, anchor, refs, and
boundary, and require refusal before stdout without changing state, ledger, Git,
or filesystem bytes. A non-exhausted audit round remains a refusal. The
integration conformance report is produced by the exact resolver recorded in
`.hexaemeron/design-evidence.json`.

## 2. Prior art

### Repository

Commit `482172e79c281149b8f565cc21f6dc6ffb5aa14a` and merged pull request
[#1069](https://github.com/wildcat-finance/skills/pull/1069) are the shipped
controller half. They resolve the init base once, bind the closed
`fiat-run-anchor/v1` receipt into the initial ledger entry, add the pure captured
bytes helper and read-only `checkpoint identity` command, and separate semantic,
capsule-manifest, and future archive identities. The implementation reference is
`plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md`; its classifier
currently accepts only a literal `done:push` or `audit-round` tail.

Merged pull request
[#1178](https://github.com/wildcat-finance/skills/pull/1178) is the second and
most recent subject-changing delivery. It reinstates the Wave Delta distributed
programme, records that #860's controller half landed, and commits the governing
programme study and runbook. Its Step 1 requires a fresh-checkout capsule restore,
an identity reread, and a green `hexctl verify`, while leaving the outer archive
to #861.

`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md` specifies the
existing hostile-input capsule and same-ledger relocation. Restore appends exactly
one `checkpoint:restore` receipt, changes only admitted local path fields, verifies
the imported prefix, refs, source artefacts, state, and next directive, and does
not run that directive. `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`
already decides that continuation restores the same run and ledger, that
checkpoint meaning is separate from transport bytes, and that arbitrary
mid-phase checkpoints are not continuation checkpoints.

### Organisation and programme

ADR-069 through ADR-073 retain the distributed layer above the local store.
ADR-073 treats two restores of one accepted parent as a later lineage concern;
it does not make relocation itself a new child. Issue #861 owns the outer archive,
Git bundle, signature proof, sidecars, and a clean-machine transcript. Issues
#862 through #867 own service intake, authority, fencing, lineage, and routing.
This run consumes none of their future evidence.

The last two relevant controller deliveries and every in-scope audit view were
read. `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
reported every committed synopsis current before they were used:

- `audit/rounds/fiat-560-bind-portable-runs-to-an-immutable-base-and.synopsis.md`
  is the verified view of the #1069 audit. Findings S1-R1-01, S1-R2-01, and
  S2-R1-01 through S2-R1-03 are all fixed and guarded; the final rounds report
  no findings. They remain required negative shapes for integration-branch
  visibility, tag peeling, exact integer identity, safe diagnostics, and
  read-only observation validation.
- `audit/rounds/fiat-557-portable-run-state-recovery-r2.synopsis.md` is the
  verified view of the native export and restore audit. Its path, resource,
  partial-publication, ref, relocation, ledger, and replay findings are fixed.
  Its explicit negative evidence remains: no userspace check proves exclusion
  of a same-account mutation after the last read, and the outer archive and
  clean-machine proof stay outside that delivery. This run carries the first as
  a stated boundary and leaves the second to #861.
- `audit/rounds/fiat-859-reinstate-the-wave-delta-distributed-checkpo.synopsis.md`
  is the verified view of the programme reinstatement. It records the landed
  `482172e7` half and disposes of the clean-machine restore as existing issue
  #861. Its #1175 adapter-timeout item, #1176 BSD `wc` item, #899 and #901
  controller defects, and one cosmetic wrap remain outside #860 by name.
- `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` is the verified plugin-level view.
  Its second round reports no findings; it adds no open checkpoint work.

### Outside both

[RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) is prior art for deriving a
stable digest from canonical JSON rather than from a carrier's formatting.
Fiat retains its already shipped, narrower canonical JSON rules and domain
separator instead of importing a new dependency or silently claiming full RFC
8785 conformance. Git's documented bundle and object identity model remains the
outer repository transport used by #861; a Git object id or capsule digest does
not replace the semantic checkpoint identity.

No prior work supports treating a relocation-only receipt as new work, and none
supports opening a checkpoint during a partially applied controller action.

## 3. Constraints and non-goals

The exact starting ref is commit
`66f43a0e07865daf526036ad1efbf98e3e27deac` on branch
`fiat/860-bind-portable-runs-to-an-immutable-base-and`. The repository pins
Python 3.14.6 in `.python-version`; the observed host is macOS 26.5.1 with Apple
Git 2.50.1. Implementation stays in the standard library and uses the existing
bounded Git, JSON, hashing, stable-read, and controller verification helpers.

The version-1 public schemas and domain separator remain unchanged. A successful
restore may change only the controller paths already admitted by the restore
contract and may append only its one closed receipt. The semantic projection
uses the imported prefix's count, digest, tail, boundary event, and state
fingerprint; it does not hash the relocation receipt as new progress. Current
state still has to verify against that receipt and the live fresh checkout.

Non-goals are the outer archive and clean-machine distribution proof in #861;
service, storage, signatures, acceptance, revocation, and DAG resolution in
#862 through #866; Atlas routing in #867; any re-anchor of a legacy run; any
identity for uncommitted work; and any new checkpoint boundary. In particular,
an ordinary audit round, a finding repair, a prose pass, a local commit, or any
other point inside a step is not checkpointable under v1. The accepted exhausted
audit boundary remains the already checked `audit-verdict` only.

## 4. Design options

The closed candidate-by-criterion record is
`.hexaemeron/design-evidence.json`. All selection cells have reports under
`.hexaemeron/reports/`; the design-lock checker, not this prose, selects the
candidate.

### Candidate: `transparent-relocation`

Recognise one exact `checkpoint:restore` tail as a transparent relocation layer.
Validate its receipt against current relocated state and the immediately
preceding ledger bytes, reconstruct the allowed old-path state fingerprint, and
feed that verified imported prefix to the existing boundary and semantic
projection. The identity bytes are therefore the producer's bytes. The trade is
extra care in the identity parser: it must distinguish an owned relocation from
an arbitrary extra ledger event without weakening ordinary verification.

### Candidate: `restored-child`

Treat restore as a new boundary and hash the appended receipt and relocated state
into a child identity. This is mechanically simple and preserves all existing
schemas. It fails the core semantic requirement because moving the same capsule
to a different absolute path would mint a different checkpoint meaning and make
carrier location authoritative.

### Candidate: `manifest-carries-identity`

Compute identity during export, add it to the capsule manifest or restore
receipt, and replay that stored value after relocation. This can retain a stable
identifier, but it changes a closed version-1 transport schema, adds a persistent
field, requires identity computation in the export path, and risks treating a
claimed value as evidence instead of recomputing it. It also intrudes on #861's
archive boundary.

The selected candidate is `transparent-relocation`. It is the only candidate
that passes stable identity, version-1 compatibility, post-restore use, zero
additional identity passes, and zero new persistent fields. Its conformance
cell remains pending while Step 1 implements and audits the round-trip and
hostile refusal proof; the report is due at the recorded `integration` stop.

## 5. Risk register seed

```risk-register
restore-tail-spoof | the final ledger entry presented as relocation evidence | only one closed checkpoint:restore shape joined to the exact preceding tail digest count and state is transparent
prefix-truncation | the imported ledger prefix used for semantic identity | source count digest tail and newline-terminated exact bytes agree before projection
path-delta-smuggling | reconstruction of the producer state from relocated state | only config.git.origin config.git.worktree and admitted portable source paths may differ and every difference matches the restore receipt
anchor-substitution | fiat-run-anchor/v1 across producer and receiver | repository task run id branches controller version and immutable initial base match the init digest and current verified checkout
boundary-widening | restore-tail handling beside the existing boundary classifier | the underlying prefix ends only at done:push or an exhausted audit-verdict and non-exhausted or mid-step audit state still refuses
multiple-relocations | more than one restore event or a restore followed by another ledger event | transparency applies only to the one immediate owned restore tail and never skips arbitrary suffix entries
semantic-transport-confusion | snapshot id beside manifest archive and path identities | repacking or relocation changes transport evidence only while any semantic field changes snapshot_id
source-or-policy-drift | study runbook observation and behavior policy evidence | current verified digests still equal the imported semantic projection before identity prints
ref-or-ancestry-drift | commits and refs recreated in the fresh checkout | every recorded ref is stable the working commit descends from the immutable base and movement during the read refuses
diagnostic-leak | hostile restored fields reaching stderr | refusal names a fixed class and emits no path credential JSON value or partial identity
concurrent-read | state ledger source or Git evidence changes while identity is derived | bounded stable rereads refuse a mixed producer and receiver view
legacy-reanchor | runs without the init-owned immutable anchor | post-restore identity refuses rather than guessing which historical branch tip was the base
```

Warden must enumerate every id. The register deliberately keeps the audit-loop
boundary separate from restore-tail mechanics: a restored exhausted loop is
identifiable, but a checkpoint inside one of its rounds is not.

## 6. Glossary seeds

- **Run anchor.** The init-owned `fiat-run-anchor/v1` receipt joining repository,
  task, run, controller, branch identities, and immutable starting commit.
- **Accepted boundary.** The producer ledger ending at `done:push`, or at the
  exhausted audit round whose active next directive is `audit-verdict`.
- **Imported prefix.** The exact producer ledger bytes ending at the accepted
  boundary and verified by the restore receipt.
- **Relocation tail.** The one `checkpoint:restore` entry appended after that
  prefix to bind the old and new controller locations without recording progress.
- **Transparent relocation.** A verified relocation tail omitted from the
  semantic checkpoint projection while remaining mandatory verification evidence.
- **Semantic identity.** The domain-separated digest of the verified run anchor,
  accepted boundary, and controller evidence; it is not a capsule or archive id.
- **Carrier identity.** A digest of exact capsule-manifest or future archive
  bytes, which may change when packaging changes without changing checkpoint meaning.
- **Mid-audit state.** Any audit-loop state before the existing exhausted
  `audit-verdict` boundary; it remains outside v1 checkpoint identity.

## 7. Sources

- Issue [#860](https://github.com/wildcat-finance/skills/issues/860), current
  review dated 3 September 2026; read 6 September 2026.
- Pull requests [#1069](https://github.com/wildcat-finance/skills/pull/1069)
  and [#1178](https://github.com/wildcat-finance/skills/pull/1178), including
  bodies, merge commits, and changed-file inventories; read 6 September 2026.
- Commit `482172e79c281149b8f565cc21f6dc6ffb5aa14a` and its changes to
  `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, the two checkpoint
  references, ADR-028, focused tests, and fixtures.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, symbols
  `_checkpoint_identity_working_commit`, `_checkpoint_identity_semantics`,
  `_checkpoint_restore_state`, `_checkpoint_restore_write_files`,
  `_checkpoint_restore_active_state`, and `cmd_checkpoint_restore`, read at the
  exact starting commit.
- `plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md` and
  `plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`, read at
  the exact starting commit.
- `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`,
  `docs/decisions/ADR-072-fence-external-fiat-transitions-on-signed-checkpoint-acceptance.md`,
  and `docs/decisions/ADR-073-model-checkpoint-lineage-as-an-explicitly-resolved-dag.md`.
- `docs/wave-delta-checkpoint-programme-study.md` and
  `docs/wave-delta-checkpoint-programme-runbook.md`, especially programme Step 1.
- The four verified audit views named in section 2, with whole-set currency
  established by `audit_synopsis.py --check .` before reading.
- RFC 8785, JSON Canonicalization Scheme, RFC Editor, June 2020:
  <https://www.rfc-editor.org/rfc/rfc8785>.

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal shape. This
is a read-only command rather than an unattended service, so it needs no metric,
trace, or alert pipeline. Its bounded stdout and fixed refusal classes answer
the operational questions directly:

1. Which immutable run and base did the receiver restore? The successful
   identity result carries the complete verified run anchor.
2. Did relocation change checkpoint meaning? The round-trip test and demo record
   producer and receiver result digests and exact equality.
3. Which accepted boundary is being continued? The identity result retains
   boundary kind, step, and working commit from the imported prefix.
4. Why did the reread stop? The command emits one fixed refusal class and no
   partial identity; the test record names the hostile specimen that caused it.

Step 1 emits the demonstration record. No new production logging is justified
because persistent telemetry would widen a local read-only operation and could
leak hostile paths or controller content.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the controls at these
capability boundaries.

| Capability boundary | Worth taking | Closing control |
| --- | --- | --- |
| Captured controller bytes to semantic parser | Exact state and appendable ledger prefix | Existing byte, depth, duplicate-key, type, count, chain, and stable-read limits |
| Restore tail to prior boundary | Only the closed relocation receipt and the exact immediately preceding prefix | Exact receipt fields, prior tail and digest join, allowed state-delta reconstruction, no suffix skipping |
| Fresh checkout and Git objects to identity | Repository identity, stable refs, immutable base, working commit, ancestry | Fixed-argument bounded Git, two stable reads, exact anchor join, no shell |
| Source and observation artefacts to evidence | Digests and closed availability status only | Existing source ceilings, receipt paths, validation, redaction, and observation joins |
| Identity or refusal to terminal | Closed result or fixed refusal class | No raw state, source text, absolute path, credential, Git output, or partial identity |

No network, secret, dependency, subprocess shell, archive extraction, or service
authority is added. The same-account mutation window remains a stated userspace
limit rather than an OS-lock claim.

## 10. The budget, or its absence

There is no new wall-time or memory budget and therefore no Metron timing
command. The selected design adds no extra identity pass, persistent field,
network call, archive read, or unbounded collection; it reclassifies the already
captured final ledger entry and projects the already bounded prefix. Existing
controller file and Git-output ceilings remain the enforceable resource budgets.

The selection reports measure the relevant structural budget with
`additional-identity-passes = 0` and `new-persistent-fields = 0`. If
implementation adds another complete read or materialises a second ledger, that
changes the design and requires a Metron baseline before it can replace this
selection.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns triage and guard
shape. Missing, malformed, mismatched, legacy, moved, oversized, non-canonical,
or unstable anchor, prefix, receipt, state, source, observation, ref, commit, or
ancestry evidence stops before stdout. A tail outside the two accepted producer
boundaries or the single immediate verified relocation wrapper also stops. The
command writes nothing, and restore remains independently responsible for its
own transaction and recovery.

The implementation guard is parent-red and branch-green. It first demonstrates
that an exact successful restore makes current `checkpoint identity` refuse;
after the fix, producer and receiver output bytes must match. Mutations then
cover every risk-register id, especially a non-exhausted audit round, a second
suffix entry, an altered old/new path join, prefix truncation, and anchor or ref
substitution. The exact conformance resolver and report path are the selected
`roundtrip-and-refusals` cell in `.hexaemeron/design-evidence.json`. Step 1 may
open with that cell pending; integration refuses unless its report exists and
passes.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns durable
decision placement. The expensive-to-reverse decision already lives in
`docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`:
continuation restores the same run and ledger, semantic meaning is separate from
transport, and arbitrary mid-phase checkpoints are rejected. This run does not
create a competing ADR or reopen the rejected boundary.

The implementable mechanics live in
`plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md`: one verified
restore tail is transparent to semantic identity, the imported prefix supplies
the identity evidence, and every mismatch refuses. The corresponding restore
join remains documented in
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`. Tests live
beside the existing focused checkpoint and checkpoint-identity modules.

If implementation discovers that exact producer identity cannot be reconstructed
from the current v1 ledger and receipt without adding a field, implementation
stops and returns to design. A
schema change would be an expensive protocol decision and must return to
Hypomnema rather than being smuggled into a compatibility repair.
