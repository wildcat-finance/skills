# Wildcat release reproduction

## Result

The four-input offline demonstration accepted 32 owner CLI operations and refused
20 independent mutations for their expected semantic reasons. The public
[summary](reproduction-summary.json) records exact raw-release and canonical
digests, bytes, contexts, actions and dispositions for every input.

| Input | Native logs / mapping records | Canonical rows | Unsupported canonical meaning |
| --- | ---: | ---: | ---: |
| Public constructed V1 | 10 / 10 | 7 | 1 |
| Public constructed V2 | 13 / 13 | 10 | 1 |
| Retained/R2-recovered V1 | 1,941 / 1,941 | 609 | 1,332 |
| Retained/R2-recovered V2 | 74,088 / 74,088 | 26,485 | 47,603 |

Each public input also has one supporting-routing and one unsupported-decode
record. Its native reference classes do not establish historical origin.
Auxiliary public registry roots are outside this four-input denominator.

## Execution evidence

The 52 operations are four builds, four verifies, four moved-release verifies,
twenty pristine controls and twenty mutation verifies. Each input was altered
independently in party, amount shape, selector, mapping class and raw component.
All twenty mutation verifies returned status 1 with the required semantic reason;
all other operations returned 0. No operation timed out, truncated its streams
or reported an infrastructure exception. Four compatibility/denial diagnostics
have their own denominator. Every operation recorded zero network attempts.

ROOT ran the frozen executor from 2026-10-04T07:39:19.030793+00:00 and measured
387.44477445888333 seconds for its outer process. This is one demonstration's
duration, with no speedup, memory-use or performance claim. Independent review
checked all 332 custody references, 52 file inventories, 62 consumed source
files, 1,220 runtime resources and 9,626 loaded-module origin rows. Source
disposition counts were recomputed with the same frozen streaming utility;
that counter calculation is common code. Exact mutation field semantics require reviewed strict saved admission and a successful focused proof in addition to ROOT's stream/inventory review.

## Coverage limits

Python socket instrumentation covers the demonstrated process path. It supplies
no OS containment, provider authenticity or hermetic macOS dynamic-library
claim. Full private streams and payloads remain outside Git and survive controller
reset. The public inventory digest binds saved admission to those retained bytes;
it is not a cryptographic execution attestation. The [recovery record](recovery.md)
describes the required custody and preparation failures.

Saved positive admission is bound to the original checkout fingerprint. If controller reset removes that worktree, retained custody remains inspectable but cannot transfer positive admission to another checkout. A new checkout or fingerprint requires a new actual four-input matrix, independent verification and public anchor.

Both retained captures lack sanctions-routing companions. Retained V2 has
fourteen factory bindings and 172 market transfers with wrapper counterparties,
but zero wrapper-instance registry entries/epochs and no wrapper-native journals.
Constructed specimens exercise those missing branches without extending capture
coverage. Recorded/inferred context, provider independence, finality, lifetime
coverage, historical completeness, compiler reruns, runtime-bytecode equivalence,
borrower identity, settlement and accounting conclusions remain unestablished.

Accounting replay belongs to [#1386](https://github.com/wildcat-finance/skills/issues/1386);
same-SHA function/event/adapter reconciliation belongs to
[#1387](https://github.com/wildcat-finance/skills/issues/1387).
Use the [consumer guide](../../../plugins/tabularium/docs/wildcat-canonical.md)
to build a fresh release and verify its coverage file.
