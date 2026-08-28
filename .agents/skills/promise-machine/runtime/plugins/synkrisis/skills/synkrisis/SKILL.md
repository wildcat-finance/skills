---
name: synkrisis
description: >
  Build one checked cohort from validated Promise Machine run observations
  under an operator-declared comparison policy and infer bounded findings from
  a digest-bound rule catalogue, or inspect and continue the committed
  cross-run diagnosis runbook. Version 2.1.0 classifies every declared run as
  included, excluded or unknown with the responsible policy field and emits
  evidence-linked candidate findings; render and verify still refuse with the
  runbook step that lands each. Do not capture or redact observations, debug
  one failing run, judge a model, act on a finding, or report a relation as a
  cause.
metadata:
  version: "2.1.0"
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
from comparable agent runs. Version 2.1.0 implements the checked cohort and
the bounded rule catalogue over it; rendering and verification are held
runbook steps, and capture, redaction, receipt binding, causal triage, issue
filing, repository mutation, and Fiat dispatch stay with their own owners.

**Current frontier.** Synkrisis builds one checked cohort from declared run observations and infers bounded findings from a digest-bound rule catalogue, and its renderer and whole-path verifier have not yet landed.
<!-- marketplace-context:end -->

Synkrisis is named for comparison. The Promise Machine records what one run
observably did: issue 434 defined the record, issue 435 the capture gate, and
issue 436 the receipt binding. None of those steps reads a pattern across
runs. A maintainer still has to decide whether repeated orientation work,
unchanged retries, handoff friction or token movement amounts to an
improvement candidate. Synkrisis makes that comparison deterministic now, one
checked cohort and one catalogue of checked rules at a time, and holds the
presenting moves to their own runbook steps.

Ephoros designs what a step emits; Metron judges a controlled measurement;
Elenchus works one failure to its cause; Horos owns the reading boundary. A
Synkrisis finding suggests one of them, or `protasis`, `phylax` or
`human-review`, as its next owner, and the suggestion is the whole action: no
path files an issue, edits a repository, or dispatches a sibling.

## What this step is

This is Step 3 of
[the committed runbook](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/runbook.md),
built from
[the committed study](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/study.md)
on the Step 2 cohort. Cohort construction and diagnosis are landed and
tested; render and verify keep refusing with one stable code naming the
runbook step that implements each. Until those steps land, Synkrisis produces
no report and no verification.

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
for byte on every run. Every non-zero exit names one stable `SK` code, the
fault class, a safe path, the producer contract and a recovery. The held
operations refuse with `SK000`:

```text
python3 plugins/synkrisis/scripts/synkrisis.py render \
  build/synkrisis/findings.json --out build/synkrisis/report.md
```

## What it refuses

- No presented result past diagnosis. Render and verify refuse until their
  runbook steps land; a refusal is not a report or a verification.
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

### synkrisis-scaffold-refusal

- Promise: Every Synkrisis operation whose runbook step has not yet landed, at this version render and verify, exits non-zero with one stable code that names the committed runbook step implementing it, and writes nothing.
- Evidence: The command's declared argument surface, the emitted refusal code, fault class, producer contract and recovery, and the unchanged working tree after each held invocation.
- Evidence classes: checked
- Boundary: The refusal establishes only that a held operation cannot present a report or a verification; it says nothing about how the later steps will behave, and it does not describe the landed cohort and diagnose operations.
- Authorises: Selecting the committed runbook's named next step as the work that lands the refused operation.
- Consequence: 0
- Refuses: Reporting a report or a verification from a held operation, and writing any output through one.
- Recovery: Build the runbook step the refusal names, then rerun the operation.
- Exceptions: none
