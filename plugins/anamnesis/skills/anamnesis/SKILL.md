---
name: anamnesis
description: Preserve audit findings and the changes that answered them as a source-bound corpus. Admit a source only against an explicit rights basis, keep the producer's bytes and identifiers unchanged, curate submissions, adjudicated findings, occurrences, remediation attempts and verifications as separate records, and release checked read-only projections for Elenchus and Synkrisis. Use when someone asks to preserve, curate, release or query a corpus of audit findings and their remedies. Do not use it to judge whether a finding is real, to prove a fix correct, or to compare runs.
metadata:
  version: "3.1.0"
---

<p align="center">
  <img src="../../assets/characters/anamnesis.webp" width="1200">
</p>

# Anamnesis

From *anamnesis*, calling back to mind what was already known. An audit finding
and the change that answered it are recorded once, in one report, and then left
where they fell. Anamnesis keeps them, with the evidence that says where each
one came from and what may be done with it.

## Where this sits

Anamnesis owns one job: custody of audit findings and their remedies. It
admits sources, curates them into a graph, and releases that graph. Its
version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md). Read that ledger before starting work intended to
advance Anamnesis itself.

**Current frontier.** The whole seed path ships. Two fresh builds of the pilot agree on the release id, the file set and every component byte; the Elenchus view has no field a verdict could occupy; the Synkrisis view carries its cohort, denominators, policy, exclusions and unknowns; and restricted material reaches neither adapter.

Three siblings sit next to it and none of them is a substitute:

- **Warden** produces one audit-round record inside one run. Anamnesis
  preserves such records; it does not produce them.
- **Elenchus** starts from a failure in hand and proves a present cause and
  guard. Anamnesis can hand it a historical analogue. The analogue is a
  hypothesis, never a verdict: Elenchus still reproduces the current failure
  and still earns its own guard.
- **Synkrisis** builds checked cohorts from admitted run observations.
  Anamnesis can hand it a corpus projection. Synkrisis does not take custody
  of the source material, and Anamnesis does not infer relations between runs.

If a request crosses one of those boundaries, hand it to the named sibling
rather than widening this skill.

## What it does not do

Anamnesis does not decide whether a finding was real, rank auditors, estimate
how common a weakness is beyond the records it holds, train a model, scrape
arbitrary URLs, deploy a service, or write to a consumer's repository. Merged
is not fixed, applied is not verified, and similar is not the same.

## The three operations

Each operation is a separate promise, declared below. An operation whose
runbook step has not landed refuses by name rather than guessing.

### `admit` -- source admission

Read a pilot policy, resolve each declared source, and decide admission. A
source is admitted when its bytes match the digest the policy declares, its
size is within the declared cap, it is an ordinary file reached without
following a symlink, and it carries an explicit rights basis. Public
visibility is not a rights basis.

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py admit \
  --policy plugins/anamnesis/specimens/pilot/policy.json
```

`admit-seed` runs the same admission and writes the closed conformance report
the runbook names:

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py admit-seed \
  --policy plugins/anamnesis/specimens/pilot/policy.json \
  --report .hexaemeron/reports/anamnesis-member-seed-source-rights-admitted.json
```

### `ingest` -- read the admitted sources

Read each admitted source into the rounds and findings its producer wrote.
Nothing is normalised here.

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py ingest \
  --policy plugins/anamnesis/specimens/pilot/policy.json
```

### `curate` -- the finding-to-remedy graph

Build submissions, findings, occurrences, remediation attempts and
verifications as separate records joined by many-to-many edges, under a
versioned curation policy.

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py curate \
  --policy plugins/anamnesis/specimens/pilot/policy.json \
  --curation-policy plugins/anamnesis/specimens/pilot/curation-policy.json
```

A severity outside the policy's taxonomy is quarantined, not mapped to its
nearest neighbour. A duplicate cluster is a curator's decision and arrives in
the policy's `duplicates`; the mapper never invents one, and a duplicate keeps
its own submission record while sharing one canonical finding.

### `release` and `verify` -- the deterministic release

`release` writes a closed manifest naming every component by digest, the policy
that produced it, its counts with their denominators, its exclusions and its
unknowns. The release id is derived from the inputs and the policy, so the same
inputs under the same policy name the same release. `verify` recomputes every
component digest from the bytes on disk.

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py release \
  --policy plugins/anamnesis/specimens/pilot/policy.json \
  --curation-policy plugins/anamnesis/specimens/pilot/curation-policy.json \
  --out plugins/anamnesis/specimens/pilot/release

python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py verify \
  --release plugins/anamnesis/specimens/pilot/release
```

The build stages beside its destination and promotes it only once every
component is written, so a killed run leaves nothing that could be mistaken for
a release.

### `analogues` and `observations` -- the consumer projections

Each consumer reads one closed, versioned, read-only view.

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py analogues \
  --release plugins/anamnesis/specimens/pilot/release \
  --kind severity --value high

python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py observations \
  --release plugins/anamnesis/specimens/pilot/release \
  --cohort-rule "every public finding in the release"
```

The Elenchus view has no field a verdict could occupy, so a past `guarded`
result cannot travel through it into a present case. Elenchus still reproduces
the present failure and still earns its own guard.

The Synkrisis view carries its cohort, every denominator, the policy that
produced it, its exclusions and its unknowns, so an included count cannot be
read as a share of anything the corpus did not see.

Restricted material crosses neither. A source whose disclosure class is not
`public` reaches no analogue and no cohort member, and the withholding is
counted rather than left silent.

**Synkrisis does not admit this producer, and that is a decision rather than a
gap.** Its manifest gate requires `promise-machine-run-observation/v1`, and a
manifest declaring `anamnesis-synkrisis-observation/v1` refuses `SK008`.
[ADR-005](../../docs/decisions/ADR-005-corpus-projections-outside-the-cohort-boundary.md)
records why the projection stays outside that boundary: a cohort member is a run,
six of its nine required fields have no source in a finding, and a cohort
partitions one population where this view carries ten denominators over ten. What
reads the projection instead is the projection, read directly under its own
schema. Synkrisis may still take the seam its own ADR-004 named; nothing here
obliges it.

### `demo` and `verify-rebuild` -- the whole path

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo \
  --specimen plugins/anamnesis/specimens/pilot
```

Two fresh builds, compared byte for byte; the committed release verified
against them; both views read; and duration and peak resident memory printed as
baselines with no budget declared for either. See
[docs/demo.md](../../docs/demo.md).

## Rights, disclosure and egress

Every source carries a `rights_basis` and a `disclosure` class. The rights
basis is a licence, a written permission, a contract, or the digest-only rule
that admits an identifier and a hash while refusing the bytes. The disclosure
class controls what may leave: `public` admits derived text, `restricted`
admits identifiers and digests alone, and `embargoed` is refused at admission.
Default is deny. A missing, unknown or unrecognised basis is a refusal, not a
warning.

## Reading the records

Unknown is not none, and neither is not applicable. A field the source never
established stays `unknown`. A normalised assertion never replaces the native
record it came from, and never strengthens its state: `proposed`, `applied`,
`released`, `deployed`, `reverted` and `verified` are independent, and none of
them implies another.

## Signals

Refusals are durable. Each one emits a closed JSONL event carrying the rule
that fired, the record it fired on, the policy version, and a correlation id,
so an operator can answer why a source was refused without rerunning the
command. No remote telemetry is added.

## Boundaries and paths

- Resolve `$PLUGIN_ROOT` to this `plugins/anamnesis/` directory.
- Run `skills/anamnesis/scripts/anamnesis.py` from that fixed plugin path.
- The interpreter is the exact version in the repository's `.python-version`.
- No network is reached. Sources are read from the local filesystem as regular
  files, without following symlinks, under a declared byte cap.
- Names such as `$anamnesis`, `/anamnesis:anamnesis` and `anamnesis:anamnesis`
  are invocation aliases, not shell commands.

A non-zero exit means the requested admission did not succeed. If a command
did not run, say so plainly and do not describe its result as successful.

## Promise Machine contract

### anamnesis-source-admission

- Promise: A successful `admit` establishes that every source the named policy declares was resolved as an ordinary file within its declared byte cap, matched the exact digest the policy records, and carried a recognised rights basis and disclosure class.
- Evidence: The parsed closed policy, the no-follow regular-file resolution, the observed byte count against the declared cap, the recomputed SHA-256 against the declared digest, the closed rights-basis and disclosure enumerations, and the per-source admission record.
- Evidence classes: checked, recomputed, recorded
- Boundary: Admission establishes source identity, bounds and permission. It does not establish that the source is accurate, that its findings are real, that its remedies worked, or that redistribution is lawful beyond the recorded basis.
- Authorises: Preserving the admitted bytes under their recorded rights basis and disclosure class, and passing them to curation.
- Consequence: 2
- Refuses: A missing, unknown or embargoed rights basis, a digest mismatch, a size above the declared cap, a symlink or non-regular path, a path escaping the policy root, a duplicate source id, an unknown policy key, or a policy schema this version does not implement.
- Recovery: Inspect the refusal event's rule, record and policy version, correct the policy or re-acquire the exact declared bytes, and rerun `admit`.
- Exceptions: none

### anamnesis-corpus-curation

- Promise: A successful `curate` establishes that every admitted source produced source-linked submission, finding, occurrence, remediation and verification assertions under the named policy, joined by many-to-many edges, with no native evidence state strengthened and every severity outside the policy taxonomy quarantined rather than mapped.
- Evidence: The admitted sources and their digests, the closed curation policy, the named mapper and its version, per-assertion source locators and verbatim native fields, the closed state enumerations, the deterministic assertion and relation ids, the quarantine list and the counted unknowns.
- Evidence classes: checked, recomputed, recorded
- Boundary: Curation establishes what the sources said and how the policy joined it. It does not establish that a finding was real, that a remediation worked, that a duplicate cluster is correct, or that the taxonomy is the right one. `applied` is as far as any status string reaches; a verification state comes only from a verdict the source declared.
- Authorises: Building a release from the graph, and passing it to the consumer projections runbook step 3 owes.
- Consequence: 2
- Refuses: A duplicate naming itself or another duplicate, a policy outside its closed shape, an unknown disclosure class, a severity outside the taxonomy reaching a finding record, derived text from a source whose disclosure class the policy does not admit, and any state value outside the closed enumeration.
- Recovery: Inspect the quarantine list and the policy that produced it, correct the taxonomy, the duplicate map or the disclosure classes, and rerun `curate`.
- Exceptions: none

### anamnesis-corpus-release

- Promise: A successful `release` followed by `verify` establishes that one closed manifest names every component by exact digest, the policy that produced it, its counts with their denominators, its exclusions and its unknowns, and that those components rebuild byte-for-byte from the same inputs under the same policy.
- Evidence: The release id derived from the policy and the source digests, the canonical byte form of every component, the recomputed component digests, the exact directory contents against the manifest, the staged build promoted only when complete, and the measured release byte total against the declared cap.
- Evidence classes: checked, recomputed, recorded
- Boundary: The release establishes its own bytes and what it excluded. It does not establish that the corpus is complete, that its counts describe anything outside the sources it names, or that an excluded record was rightly excluded.
- Authorises: Publishing the release under its recorded rights bases, and measuring it for the conformance report the design record names.
- Consequence: 2
- Refuses: An existing destination, a component whose digest or byte count differs from the manifest, a release directory holding a file the manifest does not name or missing one it does, a manifest declaring another schema, a non-regular entry in the release, and a total above the byte cap.
- Recovery: Inspect the failing component named by the refusal, rebuild the release from the same inputs and compare the release id, or correct the inputs and build a new release rather than editing one in place.
- Exceptions: none

### anamnesis-consumer-projection

- Promise: A successful `analogues` or `observations` establishes that one closed, versioned, read-only view was read from a verified release, carrying only the fields its schema declares, with no verification state in an analogue and every denominator beside every count in an observation, and with no record from a source whose disclosure class is not public.
- Evidence: The verified release and its recomputed manifest, the public-source set taken from the manifest's disclosure classes, the closed field set checked against the declared schema, the closed remediation-state enumeration an analogue admits, the counted withholding, and the stated not-established text.
- Evidence classes: checked, recomputed, recorded
- Boundary: A projection establishes what the corpus recorded and what it withheld. An analogue does not establish a cause for any present failure, that the present failure is the same defect, or that a recorded remedy would work again. An observation does not establish how common anything is outside the records it counted. Emitting the Synkrisis view does not establish that Synkrisis admits its producer contract; it does not.
- Authorises: Handing Elenchus a starting point it must still reproduce and guard, and handing a declared consumer a cohort it may compare within the stated denominators.
- Consequence: 1
- Refuses: An unknown query kind, an empty query value or unstated cohort rule, a remediation carrying a verification state, a payload whose field set differs from its schema, a payload declaring another schema or producer, and any record from a non-public source.
- Recovery: Inspect the refusal's rule, correct the query or the release it reads, and rerun the adapter; a projection is never edited after it is emitted.
- Exceptions: none

### anamnesis-deterministic-rebuild

- Promise: A successful `verify-rebuild` establishes that two builds of the same specimen under the same policy, into fresh directories, produced the same release id, the same file set and byte-identical components, and that each build verified on its own.
- Evidence: Two independent builds in separate temporary directories, the compared release ids, the compared directory listings, the byte comparison of every component, and both verification results.
- Evidence classes: checked, recomputed
- Boundary: The rebuild establishes that the build is a function of its declared inputs and policy on this machine at this commit. It does not establish that the inputs are the right ones, that the corpus is complete, or that a different interpreter or platform agrees.
- Authorises: Recording the deterministic-rebuild conformance result the design record names, and treating the committed release as reproducible from its inputs.
- Consequence: 2
- Refuses: Two builds disagreeing on the release id, on the file set, or on any component byte, a build that does not verify, and a destination that already exists.
- Recovery: Compare the two builds' components to find which one drifted, remove any non-deterministic input the diff exposes, and rerun the rebuild.
- Exceptions: none
