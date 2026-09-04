# Estate record: the Wave Delta issues, 2 September 2026 grant

The maintainer authorised rewriting the operative verdict on nine issues on
2026-09-02, and this file is the durable home for what was published under that
grant. The file name carries the grant's date; the blocks carry the date they
were written.

The grant is bounded to #859, #860, #861, #862, #863, #864, #865, #866 and
#867. No other issue was edited. #899 and #901 were not edited, because they are
`hexctl` controller defects leaving the milestone for the Fiat frontier rather
than programme work.

Each block below is the exact text published, inserted after the body's
`wildcat-origin` marker and above the 26 August 2026 review, which is kept as
history. Every `wave-atlas-original` section was compared byte for byte before
and after publication and is unchanged. The readback column is the SHA-256 of
the body GitHub returned after the edit, compared against the SHA-256 of the
bytes sent.

## Published blocks

### Issue #859

```markdown
<!-- wave-atlas-review:start -->
## Current review: 3 September 2026

**Verdict:** Keep, and reopened. The programme is on, and this epic closes last.

**Checked against:** `wildcat-finance/skills@5e8bccd7d1a1`, the reinstatement records ADR-069 through ADR-073, and the programme study and runbook that govern.

**Current basis:** ADR-069 reopens the distributed checkpoint layer above the local store, and ADR-070 through ADR-073 carry the four retired decisions forward. The programme study and runbook that govern are `docs/wave-delta-checkpoint-programme-study.md` and `docs/wave-delta-checkpoint-programme-runbook.md`. This epic closes when its eight component packets close, not before.

The 26 August 2026 review below is superseded by this one and kept as history. The original filing under it is retained as historical evidence; its old versions, line numbers, measurements, wave names and host attribution are not current instructions.
<!-- wave-atlas-review:end -->
```

### Issue #860

```markdown
<!-- wave-atlas-review:start -->
## Current review: 3 September 2026

**Verdict:** Keep, and startable. The controller half has landed.

**Checked against:** `wildcat-finance/skills@5e8bccd7d1a1`, the reinstatement records ADR-069 through ADR-073, and the programme study and runbook that govern.

**Current basis:** #508 no longer gates this issue, by maintainer decision recorded 2026-09-02, and #508 stays open in its own lane inside the milestone. Commit `482172e7` on the default branch binds a run to one immutable starting commit through an init-owned `fiat-run-anchor/v1` receipt and adds `hexctl checkpoint identity`, which is this packet's controller half. What remains is stating what the anchor binds across a restore and what refuses.

The 26 August 2026 review below is superseded by this one and kept as history. The original filing under it is retained as historical evidence; its old versions, line numbers, measurements, wave names and host attribution are not current instructions.
<!-- wave-atlas-review:end -->
```

### Issue #861

```markdown
<!-- wave-atlas-review:start -->
## Current review: 3 September 2026

**Verdict:** Keep, and partly shipped. What remains is the outer archive.

**Checked against:** `wildcat-finance/skills@5e8bccd7d1a1`, the reinstatement records ADR-069 through ADR-073, and the programme study and runbook that govern.

**Current basis:** `hexctl checkpoint export` and `hexctl checkpoint restore` are live in `fiat-v5.49.1` and already supply controller-state capture, ref binding, ledger prefix verification and relocation under the `fiat-controller-checkpoint/v1` capsule contract. The outer archive around that capsule, its Git bundle, signature proof and sidecars, remains a manual procedure ADR-028 leaves in place, and a clean-machine restore transcript is still owed.

The 26 August 2026 review below is superseded by this one and kept as history. The original filing under it is retained as historical evidence; its old versions, line numbers, measurements, wave names and host attribution are not current instructions.
<!-- wave-atlas-review:end -->
```

### Issue #862

```markdown
<!-- wave-atlas-review:start -->
## Current review: 3 September 2026

**Verdict:** Keep, in a separately authorised service repository.

**Checked against:** `wildcat-finance/skills@5e8bccd7d1a1`, the reinstatement records ADR-069 through ADR-073, and the programme study and runbook that govern.

**Current basis:** ADR-070 keeps the split between this repository, which owns the portable protocol, and `wildcat-finance/fiat-checkpoints`, which owns the replaceable service. Creating that repository and choosing its visibility remain a separate authorisation nobody has taken, so this packet cannot start until it exists.

The 26 August 2026 review below is superseded by this one and kept as history. The original filing under it is retained as historical evidence; its old versions, line numbers, measurements, wave names and host attribution are not current instructions.
<!-- wave-atlas-review:end -->
```

### Issue #863

```markdown
<!-- wave-atlas-review:start -->
## Current review: 3 September 2026

**Verdict:** Keep, and still deferred. The rules exist; the deployment does not.

**Checked against:** `wildcat-finance/skills@5e8bccd7d1a1`, the reinstatement records ADR-069 through ADR-073, and the programme study and runbook that govern.

**Current basis:** ADR-071 carries the durability rules forward: retention at the version in an account separate from the compute, quarantine separate from primary, a replica in another account and region, a signer whose private half never leaves the key service, runtime roles without delete or bypass, and break glass behind two named approvers. It drops the provider commitments, so a deployment record picks the substrate and defends it, with the account, region and spend approvals that record needs and this one does not grant.

The 26 August 2026 review below is superseded by this one and kept as history. The original filing under it is retained as historical evidence; its old versions, line numbers, measurements, wave names and host attribution are not current instructions.
<!-- wave-atlas-review:end -->
```

### Issue #864

```markdown
<!-- wave-atlas-review:start -->
## Current review: 3 September 2026

**Verdict:** Keep. The local half of the fence already ships.

**Checked against:** `wildcat-finance/skills@5e8bccd7d1a1`, the reinstatement records ADR-069 through ADR-073, and the programme study and runbook that govern.

**Current basis:** ADR-072 states the fence as the external half of a rule ADR-028 already enforces: a checkpoint save that fails blocks the next directive. What this packet adds is the execution class recorded at run creation, publication compulsory for an external run, an idempotency key that survives a client crash, and a service that can accept anything. Until one exists, an external run completes on the existing gates and the mandatory local checkpoint.

The 26 August 2026 review below is superseded by this one and kept as history. The original filing under it is retained as historical evidence; its old versions, line numbers, measurements, wave names and host attribution are not current instructions.
<!-- wave-atlas-review:end -->
```

### Issue #865

```markdown
<!-- wave-atlas-review:start -->
## Current review: 3 September 2026

**Verdict:** Keep, as two packets with a pinned interface.

**Checked against:** `wildcat-finance/skills@5e8bccd7d1a1`, the reinstatement records ADR-069 through ADR-073, and the programme study and runbook that govern.

**Current basis:** ADR-073 carries the lineage graph forward and its scope keys now exist: `fiat-run-anchor/v1` binds the immutable starting commit and `hexctl checkpoint identity` names a node. The fork this graph handles has a concrete local cause, because two restores of one capsule each continue the same imported ledger prefix. The protocol half belongs here and the index half in the service repository, and this issue closes when both have landed.

The 26 August 2026 review below is superseded by this one and kept as history. The original filing under it is retained as historical evidence; its old versions, line numbers, measurements, wave names and host attribution are not current instructions.
<!-- wave-atlas-review:end -->
```

### Issue #866

```markdown
<!-- wave-atlas-review:start -->
## Current review: 3 September 2026

**Verdict:** Keep, as the programme's destructive rehearsal.

**Checked against:** `wildcat-finance/skills@5e8bccd7d1a1`, the reinstatement records ADR-069 through ADR-073, and the programme study and runbook that govern.

**Current basis:** ADR-073 requires revocation to be append-only and salvage to need a signed resolution naming the last clean ancestor rather than a cleared flag, and ADR-071 requires a rebuild from immutable records that cannot decide acceptance. Neither can be rehearsed before a deployment exists, so this packet stays behind #863.

The 26 August 2026 review below is superseded by this one and kept as history. The original filing under it is retained as historical evidence; its old versions, line numbers, measurements, wave names and host attribution are not current instructions.
<!-- wave-atlas-review:end -->
```

### Issue #867

```markdown
<!-- wave-atlas-review:start -->
## Current review: 3 September 2026

**Verdict:** Keep, in the Atlas repository, with its maintainers' agreement.

**Checked against:** `wildcat-finance/skills@5e8bccd7d1a1`, the reinstatement records ADR-069 through ADR-073, and the programme study and runbook that govern.

**Current basis:** ADR-070 confines Atlas to redacted discovery and hand-off: it reads versioned summaries, reports each source's freshness, binds a contributor's resume, redraw or start choice, and requests a short-lived download grant. It does not validate archives as authority, sign decisions, select a fork or retain a durable object URL. Atlas is a separate repository, so this packet needs its maintainers as well as the programme.

The 26 August 2026 review below is superseded by this one and kept as history. The original filing under it is retained as historical evidence; its old versions, line numbers, measurements, wave names and host attribution are not current instructions.
<!-- wave-atlas-review:end -->
```

## Readback

Each body was published from the bytes above and read back from GitHub
immediately afterwards. The readback digest is the SHA-256 of the body GitHub
returned; the sent digest is the SHA-256 of the bytes sent. They agree on all
nine, every `wave-atlas-original` section survived, and the 26 August 2026
review is still present under the new one.

| issue | bytes | sent sha256 | readback sha256 | agree |
| --- | ---: | --- | --- | --- |
| #859 | 10639 | `0747121a2df55814` | `0747121a2df55814` | yes |
| #860 | 10371 | `95ea0a4941970799` | `95ea0a4941970799` | yes |
| #861 | 11538 | `a9c175d0186f0282` | `a9c175d0186f0282` | yes |
| #862 | 12847 | `7be4c6b7e844d194` | `7be4c6b7e844d194` | yes |
| #863 | 13822 | `1ece38958980955a` | `1ece38958980955a` | yes |
| #864 | 11797 | `8cc07ddc565cf817` | `8cc07ddc565cf817` | yes |
| #865 | 11616 | `4275ddbebcaed6a9` | `4275ddbebcaed6a9` | yes |
| #866 | 12470 | `1b1a7691bf132243` | `1b1a7691bf132243` | yes |
| #867 | 12387 | `81b233d816828811` | `81b233d816828811` | yes |

The digests are truncated to sixteen hex characters for reading; the full
values are in the controller state under this step. #899 and #901 were not
edited and carry no block from this grant.
