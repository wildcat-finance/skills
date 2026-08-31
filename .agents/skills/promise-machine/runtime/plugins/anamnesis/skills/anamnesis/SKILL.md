---
name: anamnesis
description: Preserve audit findings and the changes that answered them as a source-bound corpus. Admit a source only against an explicit rights basis, keep the producer's bytes and identifiers unchanged, curate submissions, adjudicated findings, occurrences, remediation attempts and verifications as separate records, and release checked read-only projections for Elenchus and Synkrisis. Use when someone asks to preserve, curate, release or query a corpus of audit findings and their remedies. Do not use it to judge whether a finding is real, to prove a fix correct, or to compare runs.
metadata:
  version: "0.1.0"
---

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

**Current frontier.** Source admission ships as the member's first promise: a closed pilot policy, no-follow regular-file reads under a declared byte cap, exact digest checks, and a closed rights and disclosure enumeration in which public visibility is not a rights basis. Curation and release are declared boundaries that refuse by name and say which runbook step owes them.

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

Each operation is a separate promise, declared below. This version implements
source admission only. `curate` and `release` refuse by name and say which
runbook step owes them; an operation whose step has not landed refuses rather
than guessing.

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

### `curate` -- the finding-to-remedy graph

Not implemented in this version. Runbook step 2 owes it.

### `release` -- the deterministic release

Not implemented in this version. Runbook step 3 owes it.

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

- Promise: Reserved. A successful `curate` will establish that admitted sources produced source-linked finding, remediation, verification and relationship assertions without strengthening any native evidence state.
- Evidence: Not yet earned. Runbook step 2 owes the mapper catalogue, the closed assertion and relation schemas, and their specimens.
- Evidence classes: checked, recorded
- Boundary: The promise is declared so the boundary is visible; this version establishes nothing about curation.
- Authorises: Nothing in this version.
- Consequence: 0
- Refuses: Every invocation, by name, stating that runbook step 2 owes the operation.
- Recovery: Land runbook step 2 and its evidence, then invoke `curate`.
- Exceptions: none

### anamnesis-corpus-release

- Promise: Reserved. A successful `release` will establish that a declared cohort and its projections rebuilt to identical digests from named inputs while preserving exclusions, unknowns, policy versions and source digests.
- Evidence: Not yet earned. Runbook step 3 owes the release manifest, the rebuild comparison, and the consumer projection schemas.
- Evidence classes: checked, recomputed, recorded
- Boundary: The promise is declared so the boundary is visible; this version establishes nothing about release.
- Authorises: Nothing in this version.
- Consequence: 0
- Refuses: Every invocation, by name, stating that runbook step 3 owes the operation.
- Recovery: Land runbook step 3 and its evidence, then invoke `release`.
- Exceptions: none
