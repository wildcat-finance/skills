# Wildcat V1 entry points and event linkage

Issue [#1963](https://github.com/wildcat-finance/skills/issues/1963) maps the historical Wildcat V1 estate for [#1378](https://github.com/wildcat-finance/skills/issues/1378) and [#1387](https://github.com/wildcat-finance/skills/issues/1387). This bundle holds the complete source map, the X-Ray reports and an independent review of the event linkage. Step 3 adds the offline demonstration and the consumer handoff.

## Scope

Seven concrete contexts share four accepted compiler inputs:

| Input | Accepted SHA-256 | Contexts |
| --- | --- | --- |
| `WildcatMarketControllerFactory` | `dbeb245c5fc0a44f8ca7d001ddf801ec00176e838eae9487c8d65f2b9bdc8706` | `WildcatMarket`, `WildcatMarketController`, `WildcatMarketControllerFactory` |
| `WildcatArchController` | `cb9136ec6740226c91e8d85268a0bbf7c8a5e81edb57b4bb332cc72a7e2b60db` | `WildcatArchController` |
| `WildcatSanctionsSentinel` | `45055f0b576dc6a607e4d8165711b144d1d1776d14939f74b46c4960273d8cb6` | `WildcatSanctionsSentinel`, `WildcatSanctionsEscrow` |
| `MarketLensMixed` | `fe06195c86502900d64692619da8e1275ebc7720087e59d81b2c8dd651648377` | `MarketLens` |

Every in-tree file of the first two inputs is byte-identical to `da74452aa7d1a0f024d99efd22cc6d950a8116b7`. The registry records four more commits with the same blobs, and on-chain evidence cannot tell the deployer's checkout among the five apart; `sources.json` lists all five. The sentinel input matches `6164ddd4c75ef6da2181e5623b99795b9829e31c`. The lens input matches no whole-tree commit: closest commit `488b30d08c73a93be3e4bf99128c774997411d3a` matches 40 of its 46 in-tree files, and `sources.json` names the six that differ. Every vendored library file equals the public submodule blob at the gitlink `da74452a` records. Contexts are not deployed-address counts: the accepted registry holds 16 V1 entries.

## Records

| File | Holds | Produced by |
| --- | --- | --- |
| `sources.json` | each input's files with SHA-256, size, line count, disposition and public binding; contexts, external dependencies and exclusions | `evidence/producers/build_sources.py` |
| `denominator-inputs.json` | the callable denominator and each context's ABI event catalogue, derived from the compiler outputs independently of the linkage | `scripts/kickoff_xray_1963.py derive` |
| `actions.json` | one row per identity with its flow families | `evidence/producers/build_linkage.py` |
| `linkage.json` | one row per state-changing or creation action: guards, state effects, value flows, events, dynamic callees, attribution, gaps and disposition | `evidence/producers/build_linkage.py` |
| `review.json` | the independent review, bound to the exact `linkage.json` and `actions.json` bytes | the reviewer, a separate agent from the linkage producer |
| `execution.json` | every command behind the bundle, with argv, exit, status and retained log | `evidence/producers/assemble_bundle.py` |
| `x-ray.md`, `entry-points.md`, `invariants.md`, `architecture.json`, `architecture.svg` | the X-Ray pre-audit reports; `entry-points.md` ends with a generated index of every scoped action id | the X-Ray skill; the index by `assemble_bundle.py` |
| `manifest.json` | the digest and size of every other file | `scripts/kickoff_xray_1963.py manifest` |

The denominator holds 217 identities: 148 read paths, 62 state-changing functions and 7 creation paths, including inherited functions and overloads. `WildcatMarket` has no ABI constructor row, so its creation path comes from the AST: the inherited `WildcatMarketBase` constructor. The seven ABIs declare 58 events.

## Reading the linkage

Each of the 69 scoped actions has one disposition: 38 `conditional`, 28 `mapped`, 3 `eventless` and none `unresolved`. `mapped` means every listed event fires on success; `conditional` means at least one needs the stated path condition; `eventless` means the action emits nothing and has no unresolved gap.

An event list is an unordered set of possible emissions, each with its own condition, not a sequence. A `direct` event is emitted in the action's own contract, including inherited and internal code. A `transitive` event is emitted by another V1 contract the action calls, and its source reference names that contract's input as `Input@path:line`. An emitter that is a context must use a signature from that context's ABI catalogue, which keeps interface-only variants such as `IWildcatArchController`'s `AssetBlacklisted()` out of the map.

Attribution stays at what the events carry. `DebtRepaid` names the payer, not the debtor. `Borrow` and `MarketClosed` carry no party. A market's borrower comes from the registry and its immutable fields by inference. When a market blocks a sanctioned account, the sentinel's `NewSanctionsEscrow` and `SanctionOverride` name the borrower as their key although the borrower did not act.

## Checking and reproduction

From the Skills repository root, with its pinned Python:

```sh
python3 scripts/kickoff_xray_1963.py check
python3 tests/emit_kickoff_xray_1963_report.py --report .elenchus/issue-1963.json
```

The checker compares every record with pins fixed in `scripts/kickoff_xray_1963_bundle.py`, not with the bundle's own manifest. The pins cover the four input digests, each input's source-file projection and public commits, the seven context bindings, the compiler identity, the external dependency subjects, the specification digests and the denominator. It reads no source text and runs nothing.

The producers under `evidence/producers/` rebuild the records. `derive` and `build_sources.py` need the private accepted corpus, and they publish only digests, sizes, line counts, signatures and locations. `build_linkage.py` needs only a public clone of `wildcat-finance/wildcat-protocol` with its `lib/solady` and `lib/openzeppelin-contracts` submodules; it finds every source location by a text anchor. `execution.json` shows local path prefixes as `<scratch>` and `<skills>`.

Both X-Ray coverage attempts failed and stay recorded as failures. `forge coverage` stopped at an unresolved `locals` symbol in `src/spherex/SphereXProtectedRegisteredBase.sol`; `forge coverage --ir-minimum` stopped on a stack-too-deep error in a test helper. No coverage figure is claimed. The test files and functions the X-Ray report counts were detected, not run.

## Limits and ownership

The checker establishes byte identity, membership and a recorded review binding. It cannot establish observed execution, capture completeness, source-to-bytecode identity, runtime emitter fidelity, reviewer identity or protocol safety. The review is recorded evidence from a named reviewer, not an authenticated identity.

The decision `adr/keep-v1-action-linkage-bound-to-component-inputs` records the shared input index, the separate denominator and review authority, and the private evidence boundary. X-Ray supplies the pre-audit reports; Tabularium owns adapter reconciliation in #1387. The completed V2 bundle in `docs/kickoff/1363/` is unchanged.
