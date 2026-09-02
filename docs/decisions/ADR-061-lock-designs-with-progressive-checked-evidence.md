# ADR-061: Lock designs with progressive checked evidence

## Status

Accepted, 2026-08-31. Implements
[framework-70](https://github.com/wildcat-finance/skills/issues/1000).

## Context

Protasis asked a study to compare two to four constructions and choose the one
cheapest to comprehend that still met the problem statement. Fiat repeated the
same rule at implementation. That rule is deterministic only when the options
are otherwise equal, but neither contract established equality. A locally
small construction could therefore win while using more time or memory,
breaking another plugin's boundary, or leaving no safe recovery path.

A prose rubric does not close the gap. The author still chooses the grade, and
the controller cannot tell a measured result from an expectation. Requiring
every result before design selection does not close it either: some facts exist
only after a scaffold, fixture, migration, or full composition can run. Treating
those facts as zero, acceptable, or not applicable would turn an honest unknown
into a silent pass.

The existing phase model already has useful stop points. `done study` is the
point at which the design becomes input to the runbook. A runbook opens steps in
order, and the completed stack enters integration once. The controller can
therefore refuse at the first transition that actually needs a result without
inventing another global phase.

## Decision

Protasis owns two closed JSON contracts:
`protasis-design-evidence/v1` for the design record and
`protasis-design-report/v1` for one measured result. The design record lives at
`.hexaemeron/design-evidence.json` and contains two to four candidates, one to
32 criteria, a complete candidate-by-criterion matrix, and one selection.

The criteria must cover correctness, time, space, compatibility, and recovery.
A hard gate compares a typed value with a threshold. A comparative metric is
numeric and declares minimise or maximise. Every resolved result binds a report
path and SHA-256; the report records its candidate, criterion, typed value,
unit, command, and zero exit. A pending result records the command that will
resolve it, its future report path, and the exact transition it blocks.

Selection evidence blocks `design-lock` and may not remain pending there.
Conformance evidence may block `step:N` or `integration`. Failed selection
gates remove candidates. The checker computes the non-dominated frontier from
the comparative metrics. One survivor uses `unique-frontier`. Several survivors
require either a bounded `user-policy` reference or
`exact-tie-simplicity`; the latter is valid only when every checked comparative
value is equal. Simplicity has no authority outside that exact tie.

Fiat records the contract only on new runs through
`contracts.design_evidence`. `done study` invokes Protasis at `design-lock` and
receipts the immutable record digest, selected candidate, and consumed report
digests. The runbook repeats those values in one closed `design-lock` block
before Step 1. Fiat checks evidence due for `step:1` before opening it, checks
`step:N` before opening each later step, and checks `integration` after the
last step merge assembles the stack on the run branch but before base
integration is authorised. Mason and Warden receive the fixed record path,
digest, and selected candidate. `verify` replays every transition and compares
the record, reports, state spine, ledger events, and runbook lock.

The record is immutable after design lock. A generic study or runbook amendment
cannot change its candidates, criteria, or selection. Such a change needs a
separate future design-amendment transition; until then the run halts and a new
run begins. States without `contracts.design_evidence` retain their old receipt
and packet shapes and gain no inferred evidence.

## Alternatives

- Keep the simplicity directive and add examples. Examples cannot make an
  unobserved tradeoff fail a controller transition.
- Use an A-to-F or weighted prose score. The author still supplies the grade,
  weights hide hard constraints, and a total lets one strong dimension erase a
  failed boundary.
- Require every report at study time. This prevents designs whose conformance
  can only be measured after an earlier step and rewards fabricated certainty.
- Add a global benchmark phase. One phase cannot express evidence first made
  possible by different steps, and it would delay a known blocker beyond the
  first transition that needs it.
- Let Mason choose again inside each step. That severs the runbook from the
  design decision and makes cross-step and cross-plugin constraints local
  suggestions.

## Consequences

Design selection gains a machine-verifiable boundary: complete coverage,
typed comparisons, hard-gate exclusion, non-dominance, exact tie handling, and
named unknowns are executable rather than reviewer impressions. Work can
proceed while later facts are honestly pending, but cannot cross the transition
they name without a passing report.

The record and reports add files and controller receipts. A design with four
candidates and 32 criteria has at most 128 matrix cells; the record is bounded
at 2 MiB, each report at 64 KiB, and JSON nesting at 64 containers. Transition
receipts retain only report identities and digests. Fiat gains one checker
subprocess at design lock, each step entry, and integration. Verification
deliberately repeats those checks to detect later tampering.

The five required concerns are coverage categories, not a claim that every
criterion set is sufficient. A green checker establishes the declared
measurements and selection rule, not that the commands measured the right
thing or that the chosen design is universally correct. Review still owns those
questions, now against exact evidence instead of an adjective.

Changing the design after lock is more expensive because this decision provides
no amendment transition. That cost is intentional: silently editing the record
would invalidate every runbook and step receipt derived from its digest. A
future amendment design must preserve that history rather than weakening this
lock.
