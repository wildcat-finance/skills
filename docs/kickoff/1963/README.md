# Wildcat V1 entry points and event linkage

Issue [#1963](https://github.com/wildcat-finance/skills/issues/1963) maps the historical Wildcat V1 estate for [#1378](https://github.com/wildcat-finance/skills/issues/1378) and [#1387](https://github.com/wildcat-finance/skills/issues/1387). This bundle holds the complete source map, the X-Ray reports, an independent review of the event linkage, an offline demonstration, the private input admission and the consumer handoff.

## Scope

Seven concrete contexts share four accepted compiler inputs:

| Input | Accepted SHA-256 | Contexts |
| --- | --- | --- |
| `WildcatMarketControllerFactory` | `dbeb245c5fc0a44f8ca7d001ddf801ec00176e838eae9487c8d65f2b9bdc8706` | `WildcatMarket`, `WildcatMarketController`, `WildcatMarketControllerFactory` |
| `WildcatArchController` | `cb9136ec6740226c91e8d85268a0bbf7c8a5e81edb57b4bb332cc72a7e2b60db` | `WildcatArchController` |
| `WildcatSanctionsSentinel` | `45055f0b576dc6a607e4d8165711b144d1d1776d14939f74b46c4960273d8cb6` | `WildcatSanctionsSentinel`, `WildcatSanctionsEscrow` |
| `MarketLensMixed` | `fe06195c86502900d64692619da8e1275ebc7720087e59d81b2c8dd651648377` | `MarketLens` |

Every in-tree file of the first two inputs is byte-identical to `da74452aa7d1a0f024d99efd22cc6d950a8116b7`. The registry records four more commits with the same blobs, and on-chain evidence cannot tell the deployer's checkout among the five apart. `sources.json` lists all five. The sentinel input matches `6164ddd4c75ef6da2181e5623b99795b9829e31c`. The lens input matches no whole-tree commit: closest commit `488b30d08c73a93be3e4bf99128c774997411d3a` matches 40 of its 46 in-tree files, and `sources.json` names the six that differ. Every vendored library file equals the public submodule blob at the gitlink `da74452a` records. Contexts are not deployed-address counts: the accepted registry holds 16 V1 entries.

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
| `manifest.json` | the digest and size of every other file except the two records below | `scripts/kickoff_xray_1963.py manifest` |
| `demonstration.json` | one offline demonstration: the positive check, each hostile specimen's observed refusal, the manifest digest it checked, command, exit and duration | `scripts/kickoff_xray_1963.py demo` |
| `admission.json` | the private input admission: each input's digest, source projection and file count, command, exit and duration | `scripts/kickoff_xray_1963.py admit` |

The denominator holds 217 identities: 148 read paths, 62 state-changing functions and 7 creation paths, including inherited functions and overloads. `WildcatMarket` has no ABI constructor row, so its creation path comes from the AST: the inherited `WildcatMarketBase` constructor. The seven ABIs declare 58 events.

## Reading the linkage

Each of the 69 scoped actions has one disposition: 38 `conditional`, 28 `mapped`, 3 `eventless` and none `unresolved`. `mapped` means every listed event fires on success; `conditional` means at least one needs the stated path condition; `eventless` means the action emits nothing and has no unresolved gap.

An event list is an unordered set of possible emissions, each with its own condition, not a sequence. A `direct` event is emitted in the action's own contract, including inherited and internal code. A `transitive` event is emitted by another V1 contract the action calls, and its source reference names that contract's input as `Input@path:line`. Every emitter must be one of the seven contexts, use a signature from that context's ABI catalogue and cite an emit site in that context's own input. This keeps interface-only variants such as `IWildcatArchController`'s `AssetBlacklisted()` out of the map.

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

## Offline demonstration

`demonstration.json` records one run of `python3 scripts/kickoff_xray_1963.py demo --bundle docs/kickoff/1963 --report docs/kickoff/1963/demonstration.json`, with network use disabled inside the command. The positive check passed over 48 artifacts and 217 actions: 148 read, 62 state-changing and 7 creation. Each of the seven named hostile specimens ran on its own copy of the bundle and refused with its expected code:

| Specimen | Edit | Expected refusal |
| --- | --- | --- |
| `altered-source-identity` | an input digest in `sources.json` | `source-identity` |
| `omitted-action` | the last identity dropped from `actions.json` | `action-membership` |
| `mismatched-signature` | one state-changing signature renamed in `actions.json` | `signature` |
| `missing-disposition` | one disposition removed from `linkage.json` | `disposition` |
| `stale-source-reference` | one source reference in `linkage.json` pointed past its file's end | `source-reference` |
| `stale-review-digest` | one action's reason edited in `linkage.json` after review | `review-binding` |
| `incomplete-review` | one reviewed action removed from `review.json` | `review-coverage` |

Each edit also rewrites the manifest, so no refusal rests on a stale manifest. An unexpected acceptance or a specimen error fails the run. The record binds the SHA-256 of the manifest it checked and records its duration without a performance claim. The network guard replaces `socket.socket`, `socket.create_connection` and `socket.getaddrinfo` for the run; code that bound them earlier or calls `_socket` directly is not covered.

## Private input admission

`admission.json` records `python3 scripts/kickoff_xray_1963.py admit --inputs .hexaemeron/research/accepted-corpus --report docs/kickoff/1963/admission.json`, run locally against the private accepted corpus. All four inputs were admitted: each digest, compiler setting and source projection matched its pin. The inputs hold 50 (`MarketLensMixed`), 10 (`WildcatArchController`), 40 (`WildcatMarketControllerFactory`) and 7 (`WildcatSanctionsSentinel`) source files. The record holds digests and counts only, and the command needs a local copy of the corpus.

Both records sit beside the bundle the way `manifest.json` does. The checker's inventory skips them only as regular files, and the focused tests compare `demonstration.json` with a fresh offline run.

## Recovery

After any change to a record, rebuild in this order. A change to `README.md` alone starts at step 3.

1. Rerun the producer for the changed record to a new path and copy its output into the bundle. Replace its log, `evidence/derive.log`, `evidence/build-sources.log` or `evidence/build-linkage.log`, with the run's output and a final `exit N` line: the assembler records whatever log it finds there. Then run `python3 docs/kickoff/1963/evidence/producers/assemble_bundle.py --xray XRAY_DIR`. `XRAY_DIR` holds the five X-Ray outputs and `evidence/commands.json` with the X-Ray commands' logs; it is not in this repository.
2. When one of the ten files `review.json` binds has changed, obtain an independent re-review that rebinds it.
3. Delete `manifest.json` and run `python3 scripts/kickoff_xray_1963.py manifest`, then `check`.
4. Delete `demonstration.json` and rerun the demonstration command above.

A stale `demonstration.json` fails `tests.test_kickoff_xray_1963`, because its manifest digest no longer matches.

## Consumer handoff

For [#1387](https://github.com/wildcat-finance/skills/issues/1387), the reconciliation gate between entry points and each adapter, `actions.json` is the denominator: every identity with its kind and flow families. `linkage.json` gives each scoped action's events, conditions and disposition. Reconciling each adapter against them belongs to #1387.

For [#1378](https://github.com/wildcat-finance/skills/issues/1378), the adapter that declares unattributable events unsupported, the attribution limits above apply. `Borrow` and `MarketClosed` carry no party, `DebtRepaid` names the payer, a market's borrower is inferred from the registry, and the sentinel's escrow events name the borrower as key although the borrower did not act.

Neither consumer may read the map as observed execution, capture completeness, source-to-bytecode identity, runtime emitter fidelity or protocol safety.

## Limits and ownership

The checker establishes byte identity, membership and a recorded review binding. It cannot establish observed execution, capture completeness, source-to-bytecode identity, runtime emitter fidelity, reviewer identity or protocol safety. The review is recorded evidence from a named reviewer, not an authenticated identity.

The decision `adr/keep-v1-action-linkage-bound-to-component-inputs` records the shared input index, the separate denominator and review authority, and the private evidence boundary. X-Ray supplies the pre-audit reports; Tabularium owns adapter reconciliation in #1387. The completed V2 bundle in `docs/kickoff/1363/` is unchanged.
