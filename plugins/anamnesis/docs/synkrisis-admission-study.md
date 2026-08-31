# Admit the Anamnesis corpus projection into a Synkrisis cohort, or record its boundary

Assuming, unless corrected:

1. The starting ref is `main` at `9783e2631de1614716eda5043cd843768d3baa06`; the
   run branch was cut from it.
2. Python 3 with the standard library and `unittest`, matching the interpreter
   the repository already pins. No new dependency is introduced.
3. The Synkrisis suite runs from the plugin root as
   `cd plugins/synkrisis && python3 -m unittest discover -t . -s tests`; run from
   the repository root it raises `ImportError` on `tests.support` rather than
   reporting a result.
4. Anamnesis's held job is the authority on what counts as done here, and it
   admits two outcomes rather than one. Choosing between them is the work.
5. Synkrisis's own held frontier job is open and points elsewhere; this run does
   not advance it and does not silently retarget it.

## 1. Problem statement

Anamnesis emits a corpus projection under `anamnesis-synkrisis-observation/v1`.
Synkrisis admits exactly one producer identity,
`promise-machine-run-observation/v1`, at two enforcement sites. The projection
is therefore produced and not consumed, and Anamnesis's ledger holds that gap
as its next job.

What is being built is a decision and the record of it, for whoever next asks
why the Synkrisis view exists with nothing reading it. A working prototype here
is not a feature: it is a decision record that survives someone disagreeing with
it, plus the named reader that makes the projection useful without Synkrisis.

The held job accepts either outcome:

- a Synkrisis cohort built from an Anamnesis observation with its denominators
  and exclusions intact; or
- a decision record stating that corpus projections belong outside the cohort
  boundary, naming what reads them instead.

Done is checked by: the design record at `integration` exits zero; the decision
record exists and is linted; the named reader runs and its output is checked by
a test; and Anamnesis's ledger carries exactly one new row.

## 2. Prior art

**In this repository.**

- `plugins/synkrisis/references/cohort-v1.schema.json` declares
  `producer_contract` as a JSON Schema `const`, a single admissible value.
- `plugins/synkrisis/scripts/synkrisis.py:27` holds `PRODUCER_CONTRACT` as one
  module constant, enforced at `:372` (refusal `SK008`, manifest load) and
  `:916` (refusal `SK012`, cohort verification).
- `plugins/anamnesis/skills/anamnesis/schemas/synkrisis-observation-v1.json`
  declares the projection, and its own description already says that Synkrisis
  admitting it "is Synkrisis's own decision and has not happened".
- `plugins/anamnesis/specimens/pilot/projections/synkrisis-cohort.json` is the
  built projection: 41 findings, ten denominators, no exclusions, four unknown
  maps, and a `not_established` sentence.
- `plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py` exposes
  `observations`, which emits the view. Nothing downstream reads it.

**The decision that already drew this line.**
`plugins/synkrisis/docs/decisions/ADR-004-separate-run-and-reachability-evidence.md`
refused a different input class on the reasoning that "a disposition describes a
run, and a reachability candidate is not a run". Its Consequences section names
the seam for any future admission: "a new producer contract in the manifest, a
new rule kind, and a promise stating what the combination establishes and what
it refuses." That is the precedent this study is measured against, and it cuts
both ways: it names how admission would be done, and it names why the previous
admission was refused.

**The last run over this target.** Pull request #1024 landed Anamnesis and its
`## Carried forward` section states the position this run inherits: broadening
the gate "is a behaviour change to Synkrisis with its own evolution ledger, not
something to do inside another member's delivery." Its other six carried items
are dispositioned in section 3.

**Audit records.** The whole-set synopsis currency check
(`audit_synopsis.py --check .`) exits zero and every row reads
`committed=match`, so the verified synopses are the reading view. The in-scope
record is `audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.md`,
read through its synopsis. Step 3 round 1 lists among its unchecked items
"whether Synkrisis would accept this producer contract if asked, which is
Synkrisis's decision and has not been made". That is this question, recorded as a
deliberate non-check rather than an oversight. Synkrisis has no audit record in
this checkout: there is no `plugins/synkrisis/audit/` and no synkrisis run file
under `audit/rounds/`. That is an evidence gap, recorded rather than worked
around; the Synkrisis reasoning available to this study is its ADRs, its schemas
and its code.

## 3. Constraints and non-goals

- Starting ref `9783e2631de1614716eda5043cd843768d3baa06` on `main`.
- No new runtime dependency; standard library only.
- **Synkrisis's frontier is not this run's to move.** Its ledger is open at
  `synkrisis-v4.2.0` on `captured-cohort-validation`, a job about captured *run*
  observations. The versioning contract forbids changing a held target outside a
  completed frontier job for that skill, so a second cohort algebra added here
  would either collide with that target or require retargeting it from outside.
- Non-goal: judging whether the pilot's 41 findings are the right 41. Carried
  from #1024 and still open; it is a curation question, not an admission one.
- Non-goal: the unknowns map's recomputability, the two `rename` promotions, and
  the out-of-release path rule. All three are carried from #1024, all three are
  boundaries on what Anamnesis's verification establishes, and none is touched
  by an admission decision. They stay open under their existing wording.
- Non-goal: `lazarus-suite` and the payload cap accommodation, both carried from
  #1024 and both explicitly not this run's.

## 4. Design options

Three candidate constructions were drawn and scored in
`.hexaemeron/design-evidence.json`. Every value there is computed from artefacts
present at this commit: the two schemas, the enforcement sites, the governed
ledgers, and measured runs of checks that exist today. None describes an
implementation that has not been written.

**`widen-const`.** Add the Anamnesis identity to Synkrisis's producer constant
and map corpus findings onto the existing `runs[]` array. The trade is that it
is the cheapest edit and the largest lie: `synkrisis-cohort/v1` requires nine
fields per member, and six of them (`reason_code`, `record`, `sha256`,
`bytes`, `events`, `binding_status`) have no source in a finding. `events` has a
declared minimum of 2 and a finding has none. The projection's ten denominators
have nowhere to go in a closed object that declares none, so the shape that
carries them is dropped at the boundary, which is exactly what the held job says
must stay intact.

**`sibling-contract`.** Add a second Synkrisis cohort kind with its own producer
contract, rule kinds and promise, along the seam ADR-004 names, leaving
`synkrisis-cohort/v1` untouched. The trade is that it is the architecturally
clean admission and it is not this run's to make: it is a frontier-scale change
to a skill whose own frontier is open on a different target.

**`boundary-record`.** Change no Synkrisis schema. Record the decision that
corpus projections sit outside the cohort boundary, and name what reads the
projection instead. The trade is that the projection stays unconsumed by
Synkrisis, and anyone later wanting corpus comparison inside Synkrisis must do
the `sibling-contract` work under Synkrisis's own ledger, with this record
telling them why it was not done here.

**Selection.** `widen-const` fails four gates: `denominator-homes` 0 against a
floor of 10, `fabricated-run-fields` 6 against 0, `frontier-collision` 1
against 0, and `release-components-rebuilt` 1 against 0. `sibling-contract`
fails `frontier-collision`. `boundary-record` passes every gate and is the sole
survivor, so the rule is `unique-frontier`. The checker exits zero at
`design-lock`.

The numbers rest on a simpler point. Synkrisis's cohort is a partition of
one population: every run appears exactly once as included, excluded or unknown,
and the digest binds rule evaluation to exactly that classification. Anamnesis's
projection carries ten denominators describing ten different populations:
engagements, findings, occurrences, relations, remediations, rounds, rounds with
no findings, submissions, verifications, and findings withheld by disclosure.
There is no single population to partition. That is not an awkward mapping; it
is the same category difference ADR-004 already refused, with findings in place
of reachability candidates.

## 5. Risk register seed

```risk-register
decision-overreach | the decision record's claim about Synkrisis | the record states Anamnesis's position and does not assert a decision on Synkrisis's behalf
reader-unnamed | the "what reads them instead" clause | the named reader exists, runs, and is checked by a test rather than only described
frontier-drift | plugins/synkrisis/skills/synkrisis/EVOLUTION.md | the run leaves Synkrisis's held target and its digest byte-identical
ledger-arithmetic | plugins/anamnesis/skills/anamnesis/EVOLUTION.md | exactly one new row, evolution incremented once, generation and epoch retained, prior revision and digest preserved
projection-drift | the committed pilot projection | the projection's bytes and release id are unchanged by this run
stale-prose | mutable first-party marketplace prose | every governed skill's README and SKILL.md claim about this boundary is cold-read and reconciled before the run is done
```

## 6. Glossary seeds

- **Producer contract.** The identity string a consumer checks before admitting
  a record. Synkrisis holds one; Anamnesis emits another.
- **Cohort.** In Synkrisis, a partition of one declared run set into included,
  excluded and unknown, bound by a digest.
- **Corpus projection.** In Anamnesis, a read-only view of a release carrying
  counts beside the denominators that give them meaning.
- **Denominator.** The count a share is read against. Ten of them here, over
  different populations.
- **Held job.** The `Next Fiat job` line in a skill's `EVOLUTION.md`; a target,
  not a writing prompt.

## 7. Sources

- `plugins/synkrisis/references/cohort-v1.schema.json`
- `plugins/synkrisis/scripts/synkrisis.py` lines 27, 372, 916
- `plugins/synkrisis/docs/decisions/ADR-004-separate-run-and-reachability-evidence.md`
- `plugins/synkrisis/skills/synkrisis/EVOLUTION.md`
- `plugins/anamnesis/skills/anamnesis/schemas/synkrisis-observation-v1.json`
- `plugins/anamnesis/skills/anamnesis/EVOLUTION.md`
- `plugins/anamnesis/specimens/pilot/projections/synkrisis-cohort.json`
- `audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.synopsis.md`
- Pull request wildcat-finance/skills#1024, `## Carried forward`
- `plugins/hexaemeron/skills/VERSIONING.md`

## 8. Signals, and the questions behind them

This run ships a decision record and a checked reader, not a service. There is
no unattended process and no on-call question, so items that would normally
carry signals carry none. The one question a person will ask later is "why does
the Synkrisis view exist with nothing reading it", and the answer is the
decision record itself rather than an emitted signal. The reader the run names
runs from a terminal and reports through its exit status and output;
[ephoros](../ephoros/SKILL.md) owns what a signal must carry, and none is owed
here.

## 9. Boundaries, per capability

The run reads repository files and writes Markdown and, for the reader's guard,
a test. It opens no network boundary, spawns no subprocess over untrusted input,
reads no credential and adds no dependency. The one boundary worth naming is the
reader: it reads a release projection that a policy declared, and it must not
read anything the projection's disclosure rules withheld. That control already
exists in Anamnesis and is not reimplemented here.
[phylax](../phylax/SKILL.md) owns the boundary list and its controls.

## 10. The budget, or its absence

No performance budget. The run adds prose, one decision record and a guard test.
The measured `acceptance-check-ms` figures in the design record are selection
evidence comparing candidates, not a budget this run must hold.
[metron](../metron/SKILL.md) owns what a budget carries; none is declared, and
no change here is made in the name of speed.

## 11. The fail-closed posture

What stops the run: the design checker refusing at a step boundary; the ledger
row failing the versioning arithmetic; the Synkrisis frontier tuple changing;
the named reader failing its guard. A fix follows the guard convention: the
test fails against the parent commit and passes against the fixed tree, and the
guard names the exact specimen.
[elenchus](../elenchus/SKILL.md) owns the triage order and the guard rule.

## 12. Decisions and their homes

Two decisions here are expensive to reverse and each earns a record.

- **Corpus projections sit outside the Synkrisis cohort boundary.** This is the
  run's substance. Its home is a new ADR under
  `plugins/anamnesis/docs/decisions/`, because it is Anamnesis stating where its
  own projection stands and what reads it. It records Anamnesis's position and
  does not purport to decide for Synkrisis; the seam ADR-004 named stays open
  for Synkrisis to take under its own ledger.
- **What reads the projection instead.** Named in the same record, with the
  reader existing and guarded rather than only described.

[hypomnema](../hypomnema/SKILL.md) owns which decisions earn a record and where
each one lives.
