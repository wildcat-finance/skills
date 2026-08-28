---
name: synkrisis
description: >
  Inspect or develop the specified boundary for comparing validated Promise
  Machine run observations across one declared cohort. Version 0.1.0 is a
  refusing scaffold: cohort, diagnose, render, and verify all stop with SK000
  and write nothing. Use it to read that contract or continue its held
  runbook, not to claim a cohort or finding. Do not capture or redact
  observations, debug one failing run, judge a model, act on a finding, or
  report a relation as a cause.
metadata:
  version: "0.1.0"
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

Synkrisis reserves the comparison and bounded-inference boundary for validated
observations from comparable agent runs. Version 0.1.0 implements only the
refusal surface; capture, redaction, receipt binding, causal diagnosis, issue
filing, repository mutation, and Fiat dispatch stay with their own owners.

**Current frontier.** Synkrisis is a committed specification with a refusing command stub, and none of its runbook's cohort, diagnosis, render or verification steps has yet landed behaviour.
<!-- marketplace-context:end -->

Synkrisis is named for comparison. The Promise Machine records what one run
observably did: issue 434 defined the record, issue 435 the capture gate, and
issue 436 the receipt binding. None of those steps reads a pattern across
runs. A maintainer still has to decide whether repeated orientation work,
unchanged retries, handoff friction or token movement amounts to an
improvement candidate. Synkrisis has a committed design for making that
comparison deterministic and honest about what recorded events can say, but
the current command does not yet perform it.

Ephoros designs what a step emits; Metron judges a controlled measurement;
Elenchus works one failure to its cause; Horos owns the reading boundary. A
future Synkrisis finding is specified to suggest one of them as its next owner,
and the suggestion is the whole action: no path files an issue, edits a
repository, or dispatches a sibling.

## What this step is

This is Step 1 of
[the committed runbook](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/runbook.md),
built from
[the committed study](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/study.md): the
plugin shell, its packaging and marketplace surfaces, this canonical
instruction document, the evolution ledger, the first decision record, and a
command stub. The stub declares the complete specified surface and refuses
every operation with one stable code naming the runbook step that implements
it. Until those steps land, Synkrisis produces no cohort, finding, report or
verification.

## The specified surface

One standard-library command, `scripts/synkrisis.py`, with four operations:

- `cohort` reads an operator-declared manifest of run-observation records and
  one comparison policy, checks producer identity, declared validation,
  redaction and binding results, digests, caps, path form and equality
  dimensions, and writes a cohort classifying every declared run as included,
  excluded or unknown with the exact policy field responsible. Lands with
  Step 2.
- `diagnose` applies a digest-bound catalogue of deterministic rules to one
  checked cohort and emits findings carrying exact event references,
  counterevidence, unknown runs, the nearest forbidden claim and one
  suggested handoff. A rule is data over closed shipped kinds; no rule
  supplies an expression, an import, a shell command or a regular
  expression. Lands with Step 3.
- `render` writes a fixed-template report that cannot add a number, run id,
  causal verb or evidence class absent from the findings. Lands with Step 4.
- `verify` recomputes the cohort, the findings and the report byte for byte
  from the original inputs. Lands with Step 4.

The study fixes the caps the implementation must hold: one cohort at a time,
at most 100 runs and 100,000 events, 8 MiB per file and 64 MiB of declared
input in aggregate, with a 5.0-second, 256 MiB work budget measured in Step 5.

## Run it

From a checkout, with the exact interpreter in the suite's
[`.python-version`](../../../../.python-version):

```text
python3 plugins/synkrisis/scripts/synkrisis.py --help
python3 plugins/synkrisis/scripts/synkrisis.py cohort \
  --manifest manifest.json --policy policy.json --out cohort.json
```

The first command prints the specified surface. The second, like every
operation at this step, exits 1 with code `SK000`, the fault class, the
producer contract `promise-machine-run-observation/v1`, and a recovery naming
the runbook step to build; it creates no file.

## What it refuses

The scaffold refuses everything except describing itself: no operation
produces a result, and nothing is written. The specification the later steps
must hold is already fixed:

- No inferred comparability. A person declares the comparison policy;
  Synkrisis checks the declaration and never decides that unlike tasks,
  models, hosts, repositories or tokenizers are comparable.
- No evidence strengthening. Findings stay at the inferred class, carry their
  counterevidence and unknowns, and state the nearest forbidden claim rather
  than making it.
- No cause and no model judgement, in a rule, a finding or a report.
- No token comparison across unlike accounting identities.
- No autonomous transition. A handoff is a named suggestion; the command has
  no network, GitHub, Git or controller mutation path.

If an operation, a check or a suite did not run, say so plainly and do not
describe its result.

## Promise Machine contract

### synkrisis-scaffold-refusal

- Promise: Every specified Synkrisis operation invoked on this scaffold exits non-zero with one stable code that names the committed runbook step implementing it, and writes nothing.
- Evidence: The command's declared argument surface, the emitted refusal code, fault class, producer contract and recovery, and the unchanged working tree after each invocation.
- Evidence classes: checked
- Boundary: The refusal establishes only that the scaffold cannot present a cohort, finding, report or verification; it says nothing about how the later steps will behave.
- Authorises: Selecting the committed runbook's named next step as the work that lands the refused operation.
- Consequence: 0
- Refuses: Reporting any analytical result from the scaffold, and writing any output file.
- Recovery: Build the runbook step the refusal names, then rerun the operation.
- Exceptions: none
