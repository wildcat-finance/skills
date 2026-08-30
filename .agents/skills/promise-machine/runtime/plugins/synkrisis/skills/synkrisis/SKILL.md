---
name: synkrisis
description: >
  Build one checked cohort from validated Promise Machine run observations
  under an operator-declared comparison policy, infer bounded findings from a
  digest-bound rule catalogue, render the fixed-template report, and verify
  that all three artefacts recompute from their original inputs. Version 4.2.0
  delivers all four operations under a measured work budget. Do not capture or
  redact observations, debug one failing run, judge a model, act on a finding,
  or report a relation as a cause.
metadata:
  version: "4.2.0"
---

<p align="center">
  <img src="../../assets/characters/synkrisis.png" width="1200">
</p>

# Synkrisis

## Frontier

Synkrisis owns the cross-run comparison frontier. Its version, held target,
next job, and maturity state live in [EVOLUTION.md](EVOLUTION.md). Do not
recommend or run another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Synkrisis owns comparison and bounded inference over validated observations
from comparable agent runs. Version 4.2.0 implements the checked cohort, the
bounded rule catalogue over it, the fixed-template report and the whole-path
verification, all held to a measured work budget, while capture, redaction,
receipt binding, causal triage, issue filing, repository mutation, and Fiat
dispatch stay with their own owners.

**Current frontier.** Synkrisis ships two deterministic rule kinds proved on constructed example records, and no cohort built from captured production observations has yet exercised the catalogue.
<!-- marketplace-context:end -->

Synkrisis is named for comparison. The Promise Machine records what one run
observably did: issue 434 defined the record, issue 435 the capture gate, and
issue 436 the receipt binding. None of those steps reads a pattern across
runs. A maintainer still has to decide whether repeated orientation work,
unchanged retries, handoff friction or token movement amounts to an
improvement candidate. Synkrisis makes that comparison deterministic, one
checked cohort and one catalogue of checked rules at a time, and stops at the
verified report rather than acting on it.

Ephoros designs what a step emits; Metron judges a controlled measurement;
Elenchus works one failure to its cause; Horos owns the reading boundary. A
Synkrisis finding suggests one of them, or `protasis`, `phylax` or
`human-review`, as its next owner, and the suggestion is the whole action: no
path files an issue, edits a repository, or dispatches a sibling.

## What this step is

This is Step 5 of
[the committed runbook](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/runbook.md),
built from
[the committed study](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/study.md),
and it completes that runbook. All four operations are landed and tested, and
`scripts/bench_synkrisis.py` holds the whole path to 5.0 seconds and 256 MiB
over the committed 100-run, 100,000-event scale specification, recording the
interpreter and platform it measured. The next frontier job is outside this
runbook: the catalogue has been proved on constructed records alone, and no
cohort built from captured production observations has exercised it.

## The cohort operation

`cohort` reads two operator-declared inputs, both repository-relative under
the working root:

- a manifest (`synkrisis-manifest/v1`) naming every run in the comparison
  universe, each with its record path, SHA-256 digest, byte count, declared
  validation and redaction results under the producer and capture contracts,
  and its receipt binding: a bound prefix with receipt, byte and event counts
  and prefix digest, or an unavailable state with a bounded reason; and
- a policy (`synkrisis-policy/v1`, schema under `references/`) classifying
  every run-context dimension as `match` with the expected value or `differ`,
  plus a token accounting mode.

Admission is fail-closed: the producer identity must be
`promise-machine-run-observation/v1` on the manifest and on every event; the
record bytes must match their declared digest and count; a bound prefix must
recompute its digest and close exactly its declared event count; records
stream with contiguous sequences, unique event ids, one `run.started` opening
context and one `run.finished` close; and the caps hold, at most 100 runs,
100,000 events, 8 MiB per file and 64 MiB of declared input in aggregate.
The output (`synkrisis-cohort/v1`) classifies every declared run as included,
excluded with the exact policy field responsible, or unknown when its binding
is unavailable, and carries manifest, policy and cohort digests. Outputs are
written atomically, never overwrite different bytes, and no partial output
survives a refusal. A require-equal accounting policy refuses a cohort whose
included runs carry unlike token accounting identities, and a policy that
leaves no eligible run refuses rather than emitting an empty comparison.

## The diagnose operation

`diagnose` reads one checked cohort and one rule catalogue
(`synkrisis-rules/v1`, schema under `references/`) and re-streams every record
the cohort names, refusing if any record's bytes or event count have drifted
from the cohort's declaration. Each rule declares its kind, parameters,
required context dimensions, required event fields, minimum samples, evidence
class, a narrative template, the nearest forbidden claim and one handoff
target. A rule applies only when the cohort carries every dimension and field
it requires and the included runs meet its minimum samples; a rule that does
not apply is recorded in `refused_rules` with the reason, so a reader can tell
a rule that found nothing from a rule that never ran.

The output (`synkrisis-findings/v1`) carries the cohort and rules digests and,
for each finding, the rule id and digest, the exact matched and unknown runs,
its counterevidence, the `inferred` evidence class, the nearest forbidden
claim, one handoff naming `ephoros`, `metron`, `elenchus`, `protasis`,
`phylax`, `horos` or `human-review`, and a fingerprint that survives harmless
reordering of the manifest. The catalogue itself is checked before it is
applied: an unknown kind or field, a strengthened evidence class, causal or
model-quality language in any prose, a template escape, a handoff outside the
named owner set, an improper fraction and a duplicate rule id each refuse.

## Run it

From a checkout, with the exact interpreter in the suite's
[`.python-version`](../../../../.python-version):

```text
python3 plugins/synkrisis/scripts/synkrisis.py cohort \
  --manifest plugins/synkrisis/examples/cross-run-v0/manifest.json \
  --policy plugins/synkrisis/examples/cross-run-v0/policy.json \
  --out build/synkrisis/cohort.json
```

The worked example's five records pass `scripts/run_observation.py check`,
and the command classifies them as three included, one excluded on
`context.selected_skill` and one unknown, reproducing the committed
`examples/cross-run-v0/expected/cohort.json` byte for byte on every run.
Diagnosis runs on that cohort against the committed catalogue:

```text
python3 plugins/synkrisis/scripts/synkrisis.py diagnose \
  --cohort build/synkrisis/cohort.json \
  --rules plugins/synkrisis/references/rules-v1.json \
  --out build/synkrisis/findings.json
```

On the worked example that yields two findings,
`late-boundary-consultation/v1` and `unchanged-retry-before-handoff/v1`,
reproducing the committed `examples/cross-run-v0/expected/findings.json` byte
for byte on every run. Rendering and verification close the path:

```text
python3 plugins/synkrisis/scripts/synkrisis.py render \
  build/synkrisis/findings.json --out build/synkrisis/report.md

python3 plugins/synkrisis/scripts/synkrisis.py verify \
  --manifest plugins/synkrisis/examples/cross-run-v0/manifest.json \
  --policy plugins/synkrisis/examples/cross-run-v0/policy.json \
  --cohort build/synkrisis/cohort.json \
  --rules plugins/synkrisis/references/rules-v1.json \
  --findings build/synkrisis/findings.json \
  --report build/synkrisis/report.md
```

`verify` recomputes all three artefacts from the original manifest, policy,
records and catalogue rather than trusting any of them. Every non-zero exit
names one stable `SK` code, the fault class, a safe path, the producer
contract and a recovery.

## What it refuses

- No work claim beyond the recorded runner. The benchmark bounds this
  implementation on the interpreter and platform it prints, over the committed
  scale specification; it says nothing about another machine or a larger
  cohort.
- No claim from captured production observations. Every rule is proved on
  constructed example records, which is what the open frontier names.
- No inferred comparability. A person declares the comparison policy;
  Synkrisis checks the declaration and never decides that unlike tasks,
  models, hosts, repositories or tokenizers are comparable.
- No silent promotion of an unknown. A run whose binding is unavailable stays
  visible as unknown and cannot satisfy any sample.
- No token cohort across unlike accounting identities under a require-equal
  policy.
- No evidence strengthening. A finding stays at the inferred class, carries
  its counterevidence and unknowns, and states the nearest forbidden claim
  rather than making it.
- No cause and no model judgement, in a rule, a finding or a report.
- No autonomous transition. A suggested handoff is the whole action; the
  command has no network, GitHub, Git or controller mutation path.

If an operation, a check or a suite did not run, say so plainly and do not
describe its result.

## Promise Machine contract

### synkrisis-cohort-construction

- Promise: A successful `synkrisis.py cohort` establishes that every run in the declared manifest was classified as included, excluded or unknown under one named comparison policy, with producer identity, declared validation, redaction and binding results, digests, caps, path form and equality dimensions checked before any field entered the cohort.
- Evidence: The exact manifest and policy bytes, the recomputed record digests and bound prefixes, the per-run classification with its reason, and the emitted cohort with its digest.
- Evidence classes: checked
- Boundary: Cohort construction does not establish that the declared universe is complete, that the policy's task class is comparable in any scientific sense, or that a recorded event describes what actually happened.
- Authorises: Rule evaluation with `synkrisis.py diagnose` over exactly this cohort and the records it names.
- Consequence: 1
- Refuses: Building a cohort from an unsupported producer identity, a missing or failed validation, redaction or binding result, an undeclared or duplicate run, an unsafe path, a cap breach, unlike token accounting under a require-equal policy, or a policy that leaves no eligible run.
- Recovery: Repair the named manifest row, record, or policy field and rerun cohort construction over the complete declared universe.
- Exceptions: none

### synkrisis-bounded-diagnosis

- Promise: A successful `synkrisis.py diagnose` establishes that every emitted finding is a deterministic rule match recomputed from named events in the checked cohort, carrying its rule and cohort digests, exact event references, counterevidence, unknown runs, the nearest forbidden claim and one suggested handoff, and that every rule that did not run is recorded with its reason.
- Evidence: The digest-bound rule catalogue, the checked cohort, the re-streamed record bytes and the emitted findings with stable fingerprints.
- Evidence classes: checked, inferred
- Boundary: A finding is a bounded inferred relation between recorded events; it is not a cause, a model-quality judgement, a completeness claim, or a decision to act.
- Authorises: Rendering and verification of exactly these findings, and their presentation to a person as improvement candidates.
- Consequence: 1
- Refuses: Evaluating a malformed, unknown-kind or digest-drifted input, a rule that strengthens the evidence class, causal or quality language, a template outside the kind's plain placeholders, and any autonomous action on a finding.
- Recovery: Repair the named rule, cohort or record input and rerun diagnosis from the checked cohort.
- Exceptions: none

### synkrisis-report-verification

- Promise: A successful `synkrisis.py verify` establishes that the named cohort, findings and report recompute byte for byte from the original manifest, policy, records and rule catalogue.
- Evidence: The recomputed cohort, findings and report digests, the manifest and policy digests, and the final verification status.
- Evidence classes: recomputed
- Boundary: Verification establishes recomputability only; it does not establish external truth, cause, completeness, or the merit of any suggested handoff.
- Authorises: Handing the verified report to a person. It does not authorise the suggested handoff itself.
- Consequence: 1
- Refuses: Verifying artefacts whose bytes, digests or event references differ from recomputation, and describing a verification that did not run.
- Recovery: Regenerate the artefact from its original inputs or restore those inputs, then rerun the complete verification.
- Exceptions: none
