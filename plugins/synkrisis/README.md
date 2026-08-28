![Synkrisis](./assets/characters/synkrisis.png)

# Synkrisis

<!-- marketplace-context:start -->
## In one line

Synkrisis builds one checked cohort from validated Promise Machine run observations under an operator-declared policy and infers bounded findings over it from a digest-bound rule catalogue; its renderer and whole-path verifier are held runbook steps that still refuse.

**Current frontier.** Synkrisis builds one checked cohort from declared run observations and infers bounded findings from a digest-bound rule catalogue, and its renderer and whole-path verifier have not yet landed.

**Next Fiat job.** Use /hexaemeron:fiat to complete Step 4 of the committed runbook: ship the fixed-template renderer and the whole-path verifier behind synkrisis.py render and synkrisis.py verify, recomputing cohort, findings and report bytes from the original manifest, policy, records and catalogue; accept it when the committed example report is byte-recomputed in the suite and replacement, truncation, reordering, wrong-run association, a stale rule digest, an unsupported producer identity and an edited narrative each refuse with a stable code and recovery. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

The Promise Machine records what one agent run observably did: the
run-observation contract defines the record, the capture gate keeps forbidden
material out of it, and the receipt binding ties a prefix of it to a Fiat
receipt. None of that interprets a repeated pattern across runs. Synkrisis
owns that comparison, and this release lands the reading itself: a checked
cohort that classifies every declared run, and a digest-bound catalogue of
deterministic rules that infers bounded relations over it. The presenting
moves, the fixed-template report and the whole-path verification, are held
runbook steps whose operations still refuse. Ephoros designs what a step
emits, Metron judges a controlled measurement, Elenchus works one failure to
its cause, and Horos sets the repository-reading boundary. A finding suggests
a next owner; a person still decides whether anything happens.

## What this step ships

This is Step 3 of the committed
[runbook](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/runbook.md),
built from the committed
[study](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/study.md)
for [issue 449](https://github.com/wildcat-finance/skills/issues/449), on the
Step 2 cohort:

- `synkrisis.py diagnose`: validation of the digest-bound rule catalogue,
  application of only those rules whose required dimensions, fields and
  minimum samples hold, every refused rule recorded with its reason, and
  deterministic findings carrying the cohort and rule digests, exact matched
  and unknown runs, counterevidence, the inferred evidence class, the nearest
  forbidden claim, one handoff from the named owner set, and a fingerprint
  that survives harmless manifest reordering;
- the rule and findings schemas under `references/`, with the catalogue
  itself at `references/rules-v1.json` and the schema-compatibility record
  updated under `docs/`;
- two decision records, ADR-003 on checked rules and ADR-004 on separating
  run evidence from reachability evidence;
- the worked example's two findings, `late-boundary-consultation/v1` and
  `unchanged-retry-before-handoff/v1`, committed beside the expected cohort
  and recomputed byte for byte in the suite; and
- the diagnosis suite's negative fixtures: unknown kinds and fields,
  evidence strengthening, causal and model-quality language, template
  escapes, handoffs outside the named owner set, improper fractions,
  duplicate rule ids, tampered cohorts and drifted records.

Render and verify still refuse with one stable code naming the runbook step
that lands each.

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
rules to what is left. The held steps will render a fixed-template report and
recompute the whole path byte for byte.

## Use

Synkrisis needs only the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).
Ask:

```text
Use $synkrisis to build one checked cohort from declared run observations under my comparison policy, then diagnose it against the committed rule catalogue.
```

The cohort and diagnose operations, the caps and the refusals live in
[Synkrisis's `SKILL.md`](./skills/synkrisis/SKILL.md).
