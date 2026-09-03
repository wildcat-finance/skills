# Programme runbook: the Wave Delta distributed checkpoint layer

This runbook governs. It derives the programme's step sequence from
[the programme study](wave-delta-checkpoint-programme-study.md) and replaces the
sequence in `docs/hexaemeron-checkpoint-programme-runbook.md`, which keeps its
historical banner.

Each step below is one packet: one issue, one authorised delivery, one target
repository. Two rules hold for every one of them.

**No packet authorises one agent to write Skills, the service and Atlas
together.** A packet names exactly one target repository. Work that spans two is
two packets with a pinned interface between them, per
[ADR-070](decisions/ADR-070-separate-the-checkpoint-protocol-from-its-authority-service.md).

**Creating `wildcat-finance/fiat-checkpoints` is a separate authorisation.** No
step below creates it, and no step below approves its visibility, a cloud
account, a dependency or a deployment. A packet whose target is that repository
cannot start until it exists by someone's explicit decision.

#860 is startable once the reinstatement records land, which is this delivery.
Its controller half already landed on the default branch in `482172e7`, and the
issue stays open for the rest.

## Step 1: Bind portable runs to an immutable base and checkpoint identity

**Goal.** Close #860: a run's identity, its immutable starting commit and its
semantic checkpoint identity are one bound set the controller can check.

**Entry.** The reinstatement records are on the default branch. Target
repository `wildcat-finance/skills`. Authority gate: none beyond the ordinary
Fiat run, because the work is controller-local. Commit `482172e7` already
supplies the `fiat-run-anchor/v1` receipt and `hexctl checkpoint identity`.

**Exit.** The remaining half of #860 is stated and closed: what the anchor binds
across a restore, what an identity means when the carrier is repacked, and what
refuses. The capsule contract at
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md` states each
of those, and `hexctl verify` remains green on a restored run.

**Files.** `plugins/hexaemeron/skills/fiat/`, its reference documents and tests.

**Tests.** The Hexaemeron runner and the root suite, both green, plus a case
that restores a capsule into a fresh checkout and re-reads the identity.

**Disciplines.** phylax applies, restore reads a capsule from outside the
process. elenchus applies, a refusal path is the subject.

## Step 2: Export and restore cumulative checkpoints

**Goal.** Close #861: a checkpoint carries what a second machine needs, and a
restore on that machine continues the same ledger.

**Entry.** Step 1 closed. Target repository `wildcat-finance/skills`. Authority
gate: none beyond the ordinary Fiat run.

**Exit.** The outer archive around the capsule is specified rather than a manual
procedure: the Git bundle, the signature proof, the sidecars and their order,
with a restore transcript produced on a machine that did not write it.

Its exit commands:

```bash
hexctl --dir <fresh-origin> checkpoint restore \
  --from <capsule> --manifest-sha256 <digest>
hexctl --dir <fresh-origin> verify
```

**Files.** `plugins/hexaemeron/skills/fiat/`, its references and tests.

**Tests.** A clean-checkout restore, run on a second machine or a container with
an empty keyring, whose transcript is the evidence.

**Disciplines.** phylax applies, the archive arrives from elsewhere. ephoros
applies, a restore that half-succeeds has to say so.

## Step 3: Build intake, validation and publication

**Goal.** Close #862: a service accepts candidate bytes, validates them against
a pinned protocol release, and publishes what passes.

**Entry.** Steps 1 and 2 closed, and `wildcat-finance/fiat-checkpoints` exists
by explicit authorisation. Target repository `wildcat-finance/fiat-checkpoints`.
Authority gate: repository creation and its visibility decision, neither of them
this programme's to take.

**Exit.** Quarantine accepts bounded candidates and expires the rest, validation
runs against one pinned release, and publication is immutable. The service
widens no schema locally to accept a failing upload.

Its exit commands:

```bash
<service>/scripts/check.sh
<service>/scripts/reject-case.sh
```

**Files.** The service repository only. No file in `wildcat-finance/skills`
changes in this packet; a protocol change is its own packet here first.

**Tests.** The service's own suite, plus a rejection case that leaves the
transition unadvanced.

**Disciplines.** phylax applies throughout. ephoros applies, this is the first
component that runs unattended.

## Step 4: Deploy the locked authority and the signed receipt path

**Goal.** Close #863: accepted bytes sit in versioned locked storage with a
replica, and an independent signer states what was accepted.

**Entry.** Step 3 closed. Target repository `wildcat-finance/fiat-checkpoints`.
Authority gate: a deployment record that picks the substrate and defends it,
plus the account, region and spend approvals
[ADR-071](decisions/ADR-071-hold-checkpoint-authority-in-locked-storage-behind-replaceable-compute.md)
requires and does not grant.

**Exit.** The rules ADR-071 carries hold in a running deployment: retention at
the version, quarantine separate from primary, a replica in another account,
runtime roles without delete or bypass, break glass behind two approvers, and a
statement binding the outer archive digest, the capsule manifest digest and the
semantic checkpoint identity.

Its exit commands:

```bash
<service>/scripts/permission-test.sh
<service>/scripts/rebuild-index-drill.sh
```

**Files.** The service repository and its infrastructure definitions.

**Tests.** A permission test that proves the runtime role cannot delete a
version, and a recovery drill that rebuilds the index from immutable records.

**Disciplines.** phylax and ephoros both apply. metron applies if any latency
claim is made.

## Step 5: Fence external-run transitions

**Goal.** Close #864: an external run does not advance past a transition nobody
has accepted.

**Entry.** Step 4 closed and a service is reachable. Target repository
`wildcat-finance/skills`, because the fence is controller behaviour. Authority
gate: none beyond the ordinary Fiat run, once the service exists.

**Exit.** The execution class is recorded at run creation and never inferred,
publication is compulsory for an external run, the idempotency key survives a
client crash, and an unavailable service leaves the run waiting rather than
complete, per
[ADR-072](decisions/ADR-072-fence-external-fiat-transitions-on-signed-checkpoint-acceptance.md).

Its exit commands:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
```

**Files.** `plugins/hexaemeron/skills/fiat/` and its tests.

**Tests.** A crash between service acceptance and local append that appends
exactly once on retry.

**Disciplines.** phylax applies, the controller now trusts a remote statement.
elenchus applies to every refusal path.

## Step 6: Represent and resolve concurrent descendants

**Goal.** Close #865: two accepted siblings are visible, and a named resolver
decides what the project carries.

**Entry.** Step 5 closed. Target repository `wildcat-finance/skills`. This
packet is the protocol half of #865: the graph, its refusals and the typed
resolution record. The index half is a dependent packet in
`wildcat-finance/fiat-checkpoints` with the pinned protocol release between
them, and #865 closes when both have landed. One packet, one repository, as the
rule above requires. Authority gate: none beyond the ordinary Fiat run for this
half; the dependent index packet inherits step 3's gate.

**Exit.** The graph refuses what
[ADR-073](decisions/ADR-073-model-checkpoint-lineage-as-an-explicitly-resolved-dag.md)
says it refuses, siblings stay visible before and after a resolution, and a
claim can flag duplicate effort without invalidating a valid checkpoint.

Its exit commands:

```bash
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** The protocol schemas in this repository. The dependent index packet
touches no file here.

**Tests.** Two restores of one capsule, each publishing a valid sibling, and a
resolution record that selects one without deleting the other.

**Disciplines.** phylax applies to the resolver signature. hypomnema applies,
the resolution record is a durable decision.

## Step 7: Prove reconciliation, revocation and recovery

**Goal.** Close #866: the paths nobody wants to exercise are exercised on
purpose.

**Entry.** Step 6 closed. Target repository `wildcat-finance/fiat-checkpoints`.
Any protocol fixture the drills need is a dependent packet in
`wildcat-finance/skills`, landing there first under the pinned release, so this
packet stays one repository wide. Authority gate: the deployment record from
step 4 covers the drills; one that touches production data needs its own
approval.

**Exit.** A revoked node blocks its descendants, salvage from a clean ancestor
produces a new checked checkpoint, and a rebuild from immutable records restores
the index without deciding acceptance.

Its exit commands:

```bash
<service>/scripts/revocation-drill.sh
<service>/scripts/salvage-drill.sh
hexctl --dir <salvaged-run> verify
```

**Files.** The service repository, its drills, and protocol fixtures here.

**Tests.** The drills themselves, with their transcripts kept.

**Disciplines.** ephoros applies, a drill nobody can read afterwards proves
nothing. elenchus applies to each failure the drill induces.

## Step 8: Route contributors to resume, redraw or start

**Goal.** Close #867: somebody arriving at the work finds out what exists and
what to do next.

**Entry.** Steps 5 and 6 closed. Target repository
`wildcat-finance/shoggoth-wave-atlas`. Authority gate: Atlas is a separate
repository with its own maintainers, so this packet needs their agreement as
well as the programme's.

**Exit.** Atlas reads versioned summaries, reports each source's freshness,
binds a contributor's choice and requests a short-lived download grant. It does
not validate archives as authority, sign decisions, select a fork or retain a
durable object URL.

Its exit commands:

```bash
<atlas>/scripts/check.sh
```

**Files.** The Atlas repository only.

**Tests.** Atlas's own suite, plus a case where the graph changes underneath a
bound choice and the display redraws honestly.

**Disciplines.** phylax applies, Atlas handles contributor bytes it must not
retain. ephoros applies to the freshness reporting.

## Closing the epic

#859 closes last, when the eight packets above are closed and the programme
demonstrably does what this runbook says. Closing it earlier would mean closing
an epic whose components are open, which is how the previous programme ended up
with a study that disclaimed itself.
