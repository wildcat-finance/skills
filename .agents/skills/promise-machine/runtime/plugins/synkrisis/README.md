![Synkrisis](./assets/characters/synkrisis.png)

# Synkrisis

<!-- marketplace-context:start -->
## In one line

Synkrisis builds one checked cohort from validated Promise Machine run observations under an operator-declared policy, infers bounded findings over it from a digest-bound rule catalogue, renders the fixed-template report, and verifies that all three artefacts recompute from their original inputs.

**Current frontier.** Synkrisis builds one checked cohort, infers bounded findings from a digest-bound rule catalogue, renders the fixed-template report and verifies the whole path, and its measured work budget and demonstration path have not yet landed.

**Next Fiat job.** Use /hexaemeron:fiat to complete Step 5 of the committed runbook: land the benchmark that materialises the 100-run, 100,000-event universe from the committed fixture specification and holds cohort, diagnose and verify to 5.0 seconds and 256 MiB on the recorded runner, and the complete demonstration path; accept it when the benchmark prints interpreter, platform, specification digest, repetitions and observed maxima, the demonstration path exits 0 twice with byte-identical outputs, the two negative demonstrations exit non-zero, and every earlier gate stays green. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

The Promise Machine records what one agent run observably did: the
run-observation contract defines the record, the capture gate keeps forbidden
material out of it, and the receipt binding ties a prefix of it to a Fiat
receipt. None of that interprets a repeated pattern across runs. Synkrisis
owns that comparison, and this release lands the whole reading path: a checked
cohort that classifies every declared run, a digest-bound catalogue of
deterministic rules that infers bounded relations over it, a fixed-template
report, and a verification that recomputes all three from the original inputs.
Ephoros designs what a step emits, Metron judges a controlled measurement,
Elenchus works one failure to its cause, and Horos sets the repository-reading
boundary. A finding suggests a next owner; a person still decides whether
anything happens.

## What this step ships

This is Step 4 of the committed
[runbook](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/runbook.md),
built from the committed
[study](https://github.com/wildcat-finance/skills/blob/main/docs/synkrisis/study.md)
for [issue 449](https://github.com/wildcat-finance/skills/issues/449), on the
Step 2 cohort and the Step 3 catalogue:

- `synkrisis.py render`: the fixed-template report, refusing findings that
  carry causal language, a strengthened evidence class or unknown fields, so
  the renderer cannot introduce a claim the findings do not hold;
- `synkrisis.py verify`: independent recomputation of the cohort, the findings
  and the report bytes from the original manifest, policy, records and
  catalogue, refusing replacement, truncation, reordering, wrong-run
  association, a stale rule digest, an unsupported producer identity and an
  edited narrative, each with a stable code and a recovery;
- the worked example's report, committed beside the expected cohort and
  findings and byte-recomputed in the suite; and
- the three delivered promises, `synkrisis-cohort-construction`,
  `synkrisis-bounded-diagnosis` and `synkrisis-report-verification`, each
  bound to positive, missing-evidence, stale, overclaim and recovery evidence.
  They replace the scaffold refusal promise, which no longer has a held
  operation to be true about.

Step 5 is held: the measured work budget and the demonstration path have not
landed, so nothing here claims a runtime or memory ceiling.

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
trusting any of them.

## Use

Synkrisis needs only the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).
Ask:

```text
Use $synkrisis to build one checked cohort from declared run observations, diagnose it against the committed rule catalogue, and verify the report recomputes.
```

The four operations, the caps and the refusals live in
[Synkrisis's `SKILL.md`](./skills/synkrisis/SKILL.md).
