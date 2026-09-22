# Decision: Prepare signed source groups for Hermes estate baselines

## Status

Accepted, 2026-09-22, for kickoff issue #1355. Number assignment belongs to
final integration. This record has no ADR number.

## Context

The Wildcat V2 Ethereum estate maps 137 registered addresses and two explicit
factory dependencies to nine repository commit and compiler-profile
identities. Historical V1 and V2 tests fail under the installed Forge version:
six V1 tests use the retired `testFail` convention, one V1 escrow test has a
stale sanction oracle, and one V2 test reads `block.timestamp` in a form the
via-IR optimiser may treat as constant across a warp. Later fixed-seed runs
also found the retired convention in two V2 source groups, a stale 366-day
boundary against a 730-day maximum, and two inherited `testFail` methods in a
pinned ERC4626 test submodule.

Hermes Gate 1 requires a green source tree. Calling the original pins green
would discard those failures. Running a baseline per deployed address would
repeat the same source snapshot and suite for addresses that share one build.

## Decision

Keep each original source pin immutable. Create one signed child commit per
source and compiler-profile group. A changed child may alter only the admitted
test files; every production source, build setting, dependency pin and
submodule remains identical to its parent. An unchanged group receives a
signed empty child commit so its prepared identity is explicit.

Run one fixed-seed full suite per prepared source group. Retain the failing
parent evidence for each repaired oracle and verify every prepared signature,
parent relation, test result and source-parity comparison before Hermes Gate 1.
Map estate addresses and factory dependencies to these nine group records in a
later reviewed step.

Use the installed Forge release for eight groups. The wrapper group keeps its
source, configuration and nested submodule pins unchanged and runs through one
isolated Foundry 0.3.0 binary, which predates removal of `testFail`. Record the
release identity plus the archive and binary SHA-256 values before accepting
its result.

Public Skills records contain identities, counts and digests. Complete source
snapshots and logs for private repositories remain in restricted local
evidence until an authorised destination is recorded.

## Alternatives

- **Run one baseline per address.** Rejected because 137 jobs repeat nine
  source records and suites without adding source or compiler separation.
- **Use the original red trees.** Rejected because a failed prerequisite
  cannot establish a sealed green baseline.
- **Change production code or weaken tests.** Rejected because the observed
  failures are test-harness compatibility and oracle defects. Production
  changes would break the source equality this delivery must preserve.
- **Use a historical Forge release for every group.** Rejected because it
  would retain the stale escrow, timestamp and fixed-term oracles and would
  replace the current runner without need. The wrapper exception is limited to
  unchanged vendored tests and is accepted only with release and binary
  digests.

## Consequences

Gate 1 remains bound to the original production bytes and to a separate signed
harness identity. Reviewers can distinguish preparation from deployment
source, reproduce one group independently and see exactly which test files
changed.

The preparation does not approve the protected inventory, prove deployment
mapping, seal a Hermes baseline or permit public redistribution of private
source. Those transitions keep their later owner and evidence gates.
