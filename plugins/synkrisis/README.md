![Synkrisis](./assets/characters/synkrisis.png)

# Synkrisis

<!-- marketplace-context:start -->
## In one line

Synkrisis builds one checked cohort from validated Promise Machine run observations under an operator-declared policy, infers bounded findings over it from a digest-bound rule catalogue, renders the fixed-template report, and verifies that all three artefacts recompute from their original inputs.

**Current frontier.** Synkrisis ships two deterministic rule kinds proved on constructed example records, and no cohort built from captured production observations has yet exercised the catalogue.

**Next Fiat job.** Use /hexaemeron:fiat to build one cohort from captured production run observations under the shipped policy schema, run the rule catalogue over it, and reconcile every refusal or missed pattern into rule or schema repairs; accept it when the cohort, findings and report recompute from preserved inputs and each repair carries a red-to-green guard. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Start here

Use Synkrisis when several agent runs have already produced validated
observations and a person can declare which differences may be compared. It
checks the cohort, applies a digest-bound deterministic rule catalogue, renders
a fixed report, and verifies all three artefacts from the original inputs.

All four operations ship. The current two rule kinds have only been exercised
on constructed records, not a captured production cohort. Findings remain
bounded inferences: they do not establish cause, model quality, or permission
to act.

## Place in the collective

The Promise Machine records what one agent run observably did: the
run-observation contract defines the record, the capture gate keeps forbidden
material out of it, and the receipt binding ties a prefix of it to a Fiat
receipt. None of that interprets a repeated pattern across runs. Synkrisis
owns that comparison, and this release lands the whole reading path under a
measured work budget: a checked cohort that classifies every declared run, a
digest-bound catalogue of deterministic rules that infers bounded relations
over it, a fixed-template report, and a verification that recomputes all three
from the original inputs.
Ephoros designs what a step emits, Metron judges a controlled measurement,
Elenchus works one failure to its cause, and Horos sets the repository-reading
boundary. A finding suggests a next owner; a person still decides whether
anything happens.

## What it ships today

- `cohort` validates every declared run, recomputes its digest and accepted
  prefix, applies the operator's comparison policy, and keeps excluded and
  unknown runs visible;
- `diagnose` re-reads the included observations and applies only catalogue
  rules whose required dimensions, fields, and sample count are present;
- `render` produces the report from fixed templates, refusing causal language;
- `verify` rebuilds the cohort, findings, and report from the original inputs;
  and
- `scripts/bench_synkrisis.py` exercises a declared 100-run, 100,000-event
  universe and refuses when the slowest repetition exceeds 5.0 seconds or
  256 MiB on the runner it records.

The demonstration path is repeatable from clean inputs and has explicit
negative cases for an empty eligible cohort and a rule that claims cause. The
remaining evidence gap is field use: no captured production cohort has tested
the two current rule kinds.

## How it works

An operator declares two things: a manifest naming every run in the
comparison universe, with each record's digest, byte count, validation,
redaction and receipt-binding results; and a comparison policy classifying
every run-context dimension as match-with-this-value or may-differ, plus a
token accounting mode. `cohort` checks the producer contract, digests, bound
prefixes, caps and path form, then classifies every declared run, naming the
policy field responsible for each exclusion and keeping an unavailable
observer visible as unknown. A require-equal accounting policy refuses a
cohort whose included runs carry unlike token accounting identities, and a
policy that leaves no eligible run refuses rather than emitting an empty
comparison. `diagnose` then re-streams every record the cohort names, refuses
if any has drifted from the cohort's declaration, and applies the catalogue's
rules to what is left. `render` writes the report from fixed templates, and
`verify` recomputes all three artefacts from the original inputs rather than
trusting any of them, and `bench_synkrisis.py` holds the whole path to its
declared ceilings on the runner it records.

## Use

Synkrisis needs only the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).
Ask:

```text
Use $synkrisis to build one checked cohort from declared run observations, diagnose it against the committed rule catalogue, and verify the report recomputes.
```

The four operations, the caps and the refusals live in
[Synkrisis's `SKILL.md`](./skills/synkrisis/SKILL.md).
