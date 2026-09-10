# Archive verification of 31 August 2026: priority findings and family verdicts

Wildcat Labs wrote this record on 7 September 2026 from its archive
verification of 31 August 2026, a report held by the maintainer whose SHA-256 is
f8d3391b031ac6eced37a02f3757515198f71490a843bc1e5d8dedf559b6350e. Round 1
carries the report's twelve priority findings in its own order and with its own
ratings; round 2 carries its verdict. Every status is `open`, because the
report records no remediation. The file column names the capture family a
finding sits in, not a path. Nothing here names where the captured data or the
report are kept.

## Priority findings, round 1 -- 31 August 2026

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| V1-R1-01 | high | maple | Maple omits data that the pinned schema and live API can return: the kit skips argument-bearing, list and embedded fields, 68 indexed-type fields are omitted, and a pinned live query returned non-empty allowed-LP arrays of 9, 6 and 1 entries, so all three Maple archives are incomplete relative to their "complete grabbable surface" claim | open |
| V1-R1-02 | high | euler | Euler Earn histories are missing under a false discovery rationale: the official factory exposes the vault list, the archive contains 46 creation logs and the pinned factory list returns the same 46 vaults, but no Earn-vault logs were captured, so the v2-chain mainnet archive omits a known, discoverable protocol surface | open |
| V1-R1-03 | high | aave | Aave v3 and v4 captures do not establish their advertised schema surface: v3 skips list and argument fields including dependentAssets, usdDependentAssets and tokensWithFallback, v4 Avalanche retained a null connectedHubs and made zero hub-spoke requests, and current Stable Vault queries are uncaptured, so declared rows are intact while the configuration interpretation is incomplete | open |
| V1-R1-04 | high | euler | Euler's raw-source and block-scope descriptions contradict the archived method: HTTP and RPC JSON is decoded and canonically reserialised, and eleven API releases aggregate per-vault ranges into one union interval, so "every response preserved as returned" and "a block-scoped capture" are false and exact transport provenance is not reproducible | open |
| V1-R1-05 | medium | aave-and-maple-archives | Five archives contain undeclared AppleDouble files: 93 in Aave v3 mainnet, 60 in Aave v4 mainnet, 71 in Maple v1, 65 in Maple v2-institutional and 76 in Maple Syrup, 365 members outside the declared inventory, so Aave v4 mainnet and every Maple release verification fail closed | open |
| V1-R1-06 | medium | compound | Compound v3 Arbitrum is globally out of order and the collector can jump past a failed range: parallel futures are written in completion order, the archive has 61 descending block transitions, the first from 99,328,657 to 93,345,139, and the captured-through boundary can advance past an earlier failure | open |
| V1-R1-07 | medium | compound | Compound v2 mislabels eight structurally inapplicable calls as state gaps: implementation and underlying are called uniformly after the cToken class information is discarded, so six legacy implementations, the cETH implementation and the cETH underlying read as missing state although the bytes are present | open |
| V1-R1-08 | medium | euler | Euler schema interpretation is stale in several checkable places: the current OpenAPI default is visible and warning, documented fields and valuation states are omitted, three EVC topics are identifiable, and the canonical registry has 15 production networks rather than 11, so the dictionary, topic labels and deployment claim are wrong | open |
| V1-R1-09 | medium | wildcat | Wildcat records a subgraph hash check as passed when no hash was supplied: the archived meta hash is null, the code compares only when a hash is present and then emits a passed cutoff-matches-chain-hash result, so the provider-side equality the check claims was not performed | open |
| V1-R1-10 | medium | maple | Maple's published provenance cannot reproduce normalised rows: the archives hold normalised JSONL, manifests and notes but omit raw responses, request bytes, the SDL and the referenced baseline archive, so the 652,281-row union is verified while its derivation from exact provider bytes is not | open |
| V1-R1-11 | medium | all-kits | Present checks are stronger than several bundled future-release gates: non-exhaustive checksum sets, trusted status strings, skipped schema validation, an Aave v4 layout incompatibility and Clearpool release verification that proves custody without replaying semantic capture rules, so an altered future corpus can pass the shipped gate | open |
| V1-R1-12 | medium | all-kits | No kit automatically establishes that its registry is still current: hard-coded generations, sources, chain configs, deployment allowlists, chain lists, resolver lists and routes each need a reviewed update when upstream adds a surface, and several silently skip or merely disclose unknowns, so a clean rerun can be internally valid yet incomplete | open |

## Family verdicts, round 2 -- 31 August 2026

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| V1-R2-01 | unrated | all-families | Families proved futureproof: 0/6. Every kit has a drift, discovery, resume or verifier boundary; four of six families, Aave, Compound, Euler and Maple, carry a demonstrated data, schema or interpretation defect; 51 of 51 archives reassemble to their declared digests and 5 hold undeclared members; the requested absolute assurance is not established | open |
