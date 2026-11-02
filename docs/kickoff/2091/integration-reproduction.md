# G5 composition with the landed fee and native-state adapters

## Version boundary

The composition combines the audited #2091 product
`0ea91485e1c5e6eace6e9945160fb1dcafd0d8fe` with landed #2090 at
`87142b40decb64f1c430847838ee8b5c1ab5475f`, which includes #2089.
Adapters `1.0.0`, `1.1.0` and `1.2.0` retain their prior interpretations.
Adapter `1.3.0` retains fee and native parameter/access meanings and adds
supporting sanctioned-account queue and escrow relations. Companions create
no canonical action. Complete native keys, unique groups, reciprocal selectors,
native units, singular joins and named unmatched gaps retain their declared
boundaries. The package is `0.6.9`; the governed generation is `tabularium-v0.10.0`.
The held Compound Phase 1 frontier is unchanged.

Six controls were executed against the exact landed #2090 runtime: both full
public sanctions specimens under each of `1.0.0`, `1.1.0` and `1.2.0`.
They include the simultaneous batch-burn case and missing or duplicate groups.
Their input, mapping and four generated-file digests are in
[`wildcat-routing-native-parent.json`](../../../tests/fixtures/wildcat-routing-native-parent.json).
The composed runtime reproduces each control byte for byte.
[`test_wildcat_routing_composition.py`](../../../plugins/tabularium/tests/test_wildcat_routing_composition.py)
also checks that `1.3.0` retains fee and native-state rows with empty routing
relations where no companion is present. The original examples retain their
committed bytes and recorded version defaults.

## Executed checks

The complete Tabularium suite passed 719 tests. Promise Machine coverage,
evaluation and runtime checks report zero findings, including 11 evaluation
cases and 55 runtime bindings. These checks recompute repository evidence;
no model benchmark ran. The Phylax, Ephoros and Hypomnema repository lints
also passed.

The first full suite ran 719 tests with 59 assertion failures and no errors.
Two existing tests assumed `1.2.0` was the latest selector: 58 subtests called
the latest default while expecting `1.2.0`, and one rejection test treated
`1.3.0` as unknown. The unchanged test module reproduced that failure.
The repaired tests select `1.2.0` explicitly and use `1.4.0` as unknown;
independent positive controls cover `1.3.0`. The complete fresh rerun passed.
The failed run remains red. This correction changes no production mapper or
schema and establishes no formal parent guard.

The first staged-tree commit gate ran 2,648 tests with four failures and eight
skips. Its Horos boundary and census had been generated before the assigned ADR
rename was staged, so their tracked-file counts omitted that record. The existing
currency test reproduced the mismatch. Regeneration now scans the complete
staged assigned tree; a fresh canonical assignment report preserves those owner
outputs. The failed gate remains retained. This repair changes generated metadata
and this explanation, with no production mapper or schema change.

The selected run on signed composition
`82bf16f3fef2afcf15b4c212f6527135dba82863` passed 16 checks, including
Hexaemeron and both Forge profiles. Tabularium ran 719 tests with one error:
its scaffold test still opened the draft ADR path after canonical assignment
moved that record. All 6,270 snapshot entries stayed intact; cleanup removed
the snapshot and every group drained cleanly. The unchanged test reproduced
the missing-file error. The repair requires exactly one standing record at
the stable draft slug or its assigned ADR path, retaining every receipted
source hash and required section. That selected run remains red. The repair
changes the scaffold test, this record and owner-generated metadata; fresh
checks and unchanged-component continuity are recorded separately.

## Retained evidence and limits

The fresh [integration retained report](reports/integration-retained-coverage.json)
and [bounded observations](reports/integration-retained-coverage.observations.json)
rebuild and verify both preserved raw releases under `1.3.0`. Both report
`checked-absence`: they supply no positive historical routing join.
Constructed public specimens establish branch coverage. Earlier consumed
reports, observations and audit records remain unchanged.

The original Step 3 formal Elenchus remains inconclusive: 16 executed tests,
zero assertion failures, four infrastructure errors, zero skips and no digest
rebinds. Its v1 report supplies no per-error attribution. Separate parent
fixture-absence checks and passing owned-environment controls do not reclassify
that report or establish a formal parent guard.

Historical positive joins, global absence, provider completeness, compiler
reproduction, runtime-bytecode equivalence, sanction status, identity,
underlying cash movement and settlement remain unestablished. Final signed
composition checks, hosted checks, controller receipts and merge must be
recorded separately before completion is claimed.
