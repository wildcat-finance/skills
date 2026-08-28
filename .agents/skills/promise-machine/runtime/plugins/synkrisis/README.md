![Synkrisis](./assets/characters/synkrisis.png)

# Synkrisis

<!-- marketplace-context:start -->
## In one line

Synkrisis builds one checked cohort from validated Promise Machine run observations under an operator-declared policy; its diagnostic catalogue, renderer and verifier are held runbook steps that still refuse.

**Current frontier.** Synkrisis builds one checked cohort from declared run observations, and its diagnostic rule catalogue, renderer and verifier have not yet landed.

**Next Fiat job.** Use /hexaemeron:fiat to complete Step 3 of the committed runbook: ship the digest-bound deterministic rule catalogue behind synkrisis.py diagnose, emitting findings with exact event references, counterevidence, unknown runs, the nearest forbidden claim and one named handoff; accept it when the example cohort yields the late-boundary-consultation/v1 and unchanged-retry-before-handoff/v1 findings, fingerprints survive harmless manifest reordering, and every named negative fixture refuses. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

The Promise Machine records what one agent run observably did: the
run-observation contract defines the record, the capture gate keeps forbidden
material out of it, and the receipt binding ties a prefix of it to a Fiat
receipt. None of that interprets a repeated pattern across runs. Synkrisis
owns that comparison, and this release lands its first move: a checked cohort
that classifies every declared run before anything reads a pattern. The
interpreting moves, the rule catalogue, the report and the whole-path
verification, are held runbook steps whose operations still refuse. Ephoros
designs what a step emits, Metron judges a controlled measurement, Elenchus
works one failure to its cause, and Horos sets the repository-reading
boundary. A future finding is specified to suggest a next owner; a person
will still decide whether anything happens.

## What this step ships

This is Step 2 of the committed
[runbook](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/runbook.md),
built from the committed
[study](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/study.md)
for [issue 449](https://github.com/wildcat-finance/skills/issues/449), on the
Step 1 scaffold:

- `synkrisis.py cohort`: fail-closed admission of declared run-observation
  records, recomputed digests and bound prefixes, caps of 100 runs, 100,000
  events, 8 MiB per file and 64 MiB aggregate, and one deterministic
  classification of every declared run as included, excluded with the exact
  policy field responsible, or unknown, written atomically with no partial
  output behind a refusal;
- the policy and cohort schemas under `references/`, with the
  schema-compatibility record under `docs/`;
- the comparability decision record, ADR-002, beside ADR-001;
- a worked example under `examples/cross-run-v0/` whose five records pass
  the suite's run-observation validator, with the expected cohort committed
  beside the inputs and recomputed byte for byte in the suite; and
- the cohort suite's positive and hostile fixtures: a refused transition
  retained, an unavailable observer kept unknown, recorded token accounting,
  replaced and truncated records, prefix digest and count mismatches,
  duplicate keys and run ids, unsafe paths, cap breaches, unlike token
  accounting, empty eligibility and partial-output discipline.

Diagnose, render and verify still refuse with one stable code naming the
runbook step that lands each.

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
comparison. The held steps will apply a digest-bound catalogue of
deterministic rules, render a fixed-template report and recompute the whole
path byte for byte.

## Use

Synkrisis needs only the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).
Ask:

```text
Use $synkrisis to build one checked cohort from declared run observations under my comparison policy.
```

The cohort operation, the caps and the refusals live in
[Synkrisis's `SKILL.md`](./skills/synkrisis/SKILL.md).
