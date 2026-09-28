# Wildcat V1 entry points and event linkage

Issue [#1963](https://github.com/wildcat-finance/skills/issues/1963) maps the historical Wildcat V1 estate for [#1378](https://github.com/wildcat-finance/skills/issues/1378) and [#1387](https://github.com/wildcat-finance/skills/issues/1387). This bundle is incomplete. It holds the receipted [study](study.md), [runbook](runbook.md) and [design record](design-evidence.json) with the ten selection reports under `design-reports/`. The checker refuses it until Step 2 adds the map.

## Scope

Seven concrete contexts share four accepted compiler inputs:

| Input | Accepted SHA-256 | Contexts |
| --- | --- | --- |
| `WildcatMarketControllerFactory` | `dbeb245c5fc0a44f8ca7d001ddf801ec00176e838eae9487c8d65f2b9bdc8706` | `WildcatMarket`, `WildcatMarketController`, `WildcatMarketControllerFactory` |
| `WildcatArchController` | `cb9136ec6740226c91e8d85268a0bbf7c8a5e81edb57b4bb332cc72a7e2b60db` | `WildcatArchController` |
| `WildcatSanctionsSentinel` | `45055f0b576dc6a607e4d8165711b144d1d1776d14939f74b46c4960273d8cb6` | `WildcatSanctionsSentinel`, `WildcatSanctionsEscrow` |
| `MarketLensMixed` | `fe06195c86502900d64692619da8e1275ebc7720087e59d81b2c8dd651648377` | `MarketLens` |

The first two inputs bind to core commit `da74452aa7d1a0f024d99efd22cc6d950a8116b7`, the sentinel to `6164ddd4c75ef6da2181e5623b99795b9829e31c`. The lens input has no matching whole-tree commit; closest commit `488b30d08c73a93be3e4bf99128c774997411d3a` matches 40 of its 46 in-tree files. Contexts are not deployed-address counts: the accepted registry holds 16 V1 entries.

Step 2 adds `sources.json`, `denominator-inputs.json`, `actions.json`, `linkage.json`, `review.json`, `execution.json`, `manifest.json` and the five X-Ray reports. Step 3 adds the offline demonstration record and the consumer handoff.

## Checking

From the Skills repository root, with its pinned Python:

```sh
python3 scripts/kickoff_xray_1963.py check
python3 tests/emit_kickoff_xray_1963_report.py --report .elenchus/issue-1963.json
```

`check` exits 1 on this bundle today, naming the first absent artifact. The checker compares each record with pins fixed in `scripts/kickoff_xray_1963_bundle.py`, not with the bundle's own manifest. The pins are the four input digests, each input's source-file projection (path, SHA-256, size and line count), the seven context bindings, the compiler identity, the specification digests and, from Step 2, the independent callable denominator. A rebound manifest cannot hide an omitted artifact, file or action.

With the private accepted inputs available locally, `admit --inputs <dir> --report <new path>` checks their bytes, compiler settings and source projections. Its report holds digests and counts only.

The checker cannot establish observed execution, capture completeness, source-to-bytecode identity, runtime emitter fidelity, reviewer identity or protocol safety. The accepted corpus stays private; this bundle publishes identifiers, digests, locations and analysis only.

## Ownership

The decision `adr/keep-v1-action-linkage-bound-to-component-inputs` records the shared input index, the separate denominator and review authority, and the private evidence boundary. X-Ray supplies the pre-audit reports; Tabularium owns adapter reconciliation in #1387. The completed V2 bundle in `docs/kickoff/1363/` is unchanged.
