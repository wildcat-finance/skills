# Decision: Cover Wildcat V2 protected types by anchor baselines

## Status

Accepted, 2026-09-23.

## Context

Issue 1355 asks for a sealed Hermes Gate 1 whose storage layouts and method
maps cover every protected type in the Wildcat V2 Ethereum estate. The 137
registry addresses fall into 17 types deployed from eight source states. Under
Forge 1.7.1, four of those states have red suites after excluding files that
run zero passing tests. Sealing each one would need a signed test-only harness
commit. Five upstream commits are green: v2-protocol `c7be4039`,
wildcat-protocol `488b30d0`, and the fee recipient, role provider and
collateral repositories at their recorded commits.

The design record `docs/kickoff/1355/design-evidence.json` compared three
constructions. `anchor-and-inspect` needs 5 Gate 1 runs against 8, 1,971,599
source-snapshot bytes against 5,886,010, and no authored harness tree against
3 or 4. It is the unique frontier. The operator confirmed on 2026-09-23 that a
type may share an anchor's snapshot when its canonical layout and method map
are byte-equal to the anchor's.

## Decision

Seal one Hermes Gate 1 per green anchor. Cover each other deployed state by
equivalence: the type's canonical storage layout and method map at its
deployed state, computed with Hermes's own canonicaliser, must be byte-equal
to the anchor's sealed files. A study-time inspect does not count.

An anchor may exclude a test file with `--no-match-path` only when Forge 1.7.1
runs zero passing tests in it, so the excluded run's pass count equals the
unexcluded one. Two files qualify: `test/vault/Wildcat4626WrapperStandard.t.sol`
at `c7be4039` and `test/market/WildcatMarketToken.t.sol` at `488b30d0`. No
test source is edited.

## Alternatives

Sealing every deployed state natively (`every-deployed-state`) covers each
type without equivalence but needs four harness commits. Sealing every state
under a pre-1.0 Forge that still runs `testFail*` cases
(`legacy-forge-every-state`) adds a second toolchain and still needs three
harness commits for real assertion failures.

## Consequences

Eleven of the 17 types are covered by equivalence rather than by their own
Gate 1. A later gas candidate made in a non-anchor tree needs a new Gate 1 in
that tree first. The checker `scripts/kickoff_hermes_1355.py` refuses a type
whose anchor is not an anchor tree, a coverage mode that does not follow from
its deployed state and anchor, and an exclusion on a tree that is not an
anchor. The byte-equality check for each equivalence lands with the sealed
anchors, before `sealed-coverage` passes. The `profile-invariance` evidence shows the default and deployed build profiles
give the same layouts and method maps for all 17 types. Reversing this
decision means sealing the eight deployed states and authoring their harness
commits.
