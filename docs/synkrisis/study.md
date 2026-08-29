# Study: Synkrisis, bounded diagnosis across agent runs

This is the committed form of the study attached to
[issue #449](https://github.com/wildcat-finance/skills/issues/449),
reconfirmed against the landed run-observation surface before the build
started. The original filing is preserved in the issue; this copy is the
anchor the evolution ledger cites, and it records the assumptions as they
resolved and the design the runbook's steps must hold.

## Assumptions, as they resolved

1. "Domain agent" means a separately installable Wildcat Labs skill and one
   deterministic standard-library command, not an always-on process or an
   agent allowed to change its own instructions.
2. Issues 434, 435 and 436 landed first with stable checked identities:
   `promise-machine-run-observation/v1`
   (`docs/promise-machine/run-observation-v1.md`, schema under `schemas/`),
   `promise-machine-run-observation-capture/v1`
   (`docs/promise-machine/run-observation-capture-v1.md`) and
   `fiat-run-observation-binding/v1`
   (`docs/fiat-run-observation-binding-v1.md`). A manifest row pins the
   first, names the capture profile for its declared redaction result, and
   carries the run's receipt binding as a bound prefix or a reasoned
   unavailable state.
3. Issue 437 stays out. Reachability candidates and run observations say
   different things about different subjects; admitting the former needs its
   own study and promise
   (`plugins/synkrisis/docs/decisions/ADR-001-keep-cross-run-diagnosis-separate.md`
   records the standalone boundary, and a later record fixes the exclusion
   when the schemas it protects exist).
4. Offline, standard library only, on the exact interpreter in the suite's
   `.python-version`. No model call, no URL fetch, no raw transcript, no
   execution of anything an observation names.
5. A person declares the comparison policy. Synkrisis checks that the
   selected runs satisfy it; it does not infer that unlike tasks, models,
   hosts, repositories or tokenizers are comparable.
6. Findings are bounded inferences from named observations. They remain
   candidates for human selection and cannot file issues, edit a repository,
   change a skill, dispatch Fiat, judge model quality, or state a cause.
7. The build starts from current `main` under the repository owner's direct
   instruction of 2026-08-27, which also closes the study's dependency gate:
   the owner approved the assumptions and the new CI surface.

## The chosen design

Option A of the proposal: a standalone `plugins/synkrisis/` package owning
cohort construction, rule evaluation, report rendering and verification,
with three specified promises:

- `synkrisis-cohort-construction`: checked producer identities, manifest
  completeness, declared equality dimensions, exclusions and a cohort digest
  authorise rule evaluation over that cohort only.
- `synkrisis-bounded-diagnosis`: a rule match recomputed from exact event
  references authorises a candidate finding with inferred evidence and
  visible conflicts and unknowns.
- `synkrisis-report-verification`: recomputation of the exact cohort,
  findings and renderer bytes authorises handing the report to a person; it
  does not authorise the recommended handoff itself.

Each promise is declared in the canonical `SKILL.md` when the step that
implements it lands, so coverage always binds a declared promise to passing
evidence. Until then the scaffold declares one promise of its own,
`synkrisis-scaffold-refusal`: every specified operation refuses with a
stable code naming the runbook step that implements it, and writes nothing.

Design commitments the steps must hold:

- **Explicit comparability.** A policy classifies every run-context
  dimension as match-with-this-value or may-differ, plus a token accounting
  mode; a mismatching run is excluded with the field named, and an
  incompletely classified policy refuses.
- **Rules are data over closed kinds.** The catalogue is schema-checked and
  digest-bound; a rule names one shipped deterministic kind and closed
  integer parameters. No expression, import, shell, regular expression or
  format specification enters from input, and thresholds are integer
  fractions so no floating-point comparison decides a verdict.
- **Bounded admission.** One cohort at a time; at most 100 runs and 100,000
  events; 8 MiB per file and 64 MiB of declared input in aggregate; one
  descriptor per read; atomic outputs that never overwrite different bytes;
  no partial output behind a refusal. Records stream into compact per-run
  features so admission holds the memory budget.
- **Honest narratives.** Findings carry counterevidence, unknown runs and
  the nearest forbidden claim; rule and finding prose is held against a
  fixed list of causal and model-quality word sequences; the renderer adds
  no field absent from the findings.
- **A measured budget.** On a deterministic 100-run, 100,000-event generated
  scale fixture, cohort, diagnose and verify together finish within 5.0
  seconds and 256 MiB peak resident memory on the recorded runner. The
  committed artefact is the small fixture specification; the benchmark
  materialises the universe from it and records the specification digest.

## The first proof

The runbook's demonstration path is fixed now so the steps build toward it:
an example cohort under `plugins/synkrisis/examples/cross-run-v0/` whose
records pass `scripts/run_observation.py check`, emitting one finding for
each shipped rule kind, `late-boundary-consultation/v1` and
`unchanged-retry-before-handoff/v1`, with byte-identical outputs across two
runs, plus two negative demonstrations: an incompatible cohort refuses, and
a finding whose narrative strengthens association into cause refuses.

## Boundaries, unchanged from the proposal

Capture, redaction, storage, dashboards, causality, hidden reasoning, safety
or quality scoring, automatic issue filing, repository mutation, skill
editing, Fiat or Kronos dispatch, controlled performance verdicts, and
issue-437 dead-code triage all stay outside Synkrisis, with their owners as
the proposal named them. The nearest forbidden claim is part of every
specified finding so a reader sees the line rather than trusting that it was
drawn.
