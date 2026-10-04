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

For the original matrix, ROOT ran the frozen executor from 2026-10-04T07:39:19.030793+00:00 and measured
387.44477445888333 seconds for its outer process. This is one demonstration's
duration, with no speedup, memory-use or performance claim. Independent review
checked all 332 custody references, 52 file inventories, 62 consumed source
files, 1,220 runtime resources and 9,626 loaded-module origin rows. Source
disposition counts were recomputed with the same frozen streaming utility;
that counter calculation is common code. Exact mutation field semantics require reviewed strict saved admission and a successful focused proof in addition to ROOT's stream/inventory review.

After the round 1 executor input-validation repair, ROOT ran a fresh matrix on signed
`3f1fff8552951a4205ebb0c87d4540761ab590fc` from 2026-10-04T10:13:02.614841+00:00.
Its outer process returned 0 in 393.04862775001675 seconds;
independent verification returned 0 in 16.0732615001034 seconds. It again
accepted 32 operations, refused 20 mutations for their specific semantic reasons
and retained four separate diagnostics, with zero operation network attempts.
The fresh review checked 332 references, 52 inventories, 62 source files,
1,220 runtime resources and 9,626 loaded-module origin rows. That round's public summary bound its private inventory. Both that matrix and
anchor are now historical; they remain preserved with the original matrix.
The fresh selected saved-admission proof ran 4 tests with failures, errors,
skips, expected failures and unexpected successes all 0. Its repeated scalar
and sidecar digests do not establish freshness: the actual command, UTC and
create-only writes do. These timings make no performance claim.

After the round 2 serialized source-root repair, ROOT ran the current matrix on
signed `692fc60e1d4c175c7e3959680a72963549fb43c4` from
2026-10-04T11:06:24.715826+00:00. Its outer process returned 0 in
416.02843795903027 seconds. Independent verification returned 0 and checked
332 references, 52 inventories, 62 source files, 1,220 runtime resources and
9,626 loaded-module origin rows. The same four inputs again produced 32 accepts,
20 specific semantic refusals, four separate diagnostics and zero operation
network attempts. Their row counts and all twelve summary limits are unchanged.
The current 333,976-byte private inventory has SHA-256
`53fd5dd545922f13634df3febfcc4494d020135ba3523f97c94a72960cee8210`;
the current 7,360-byte public summary has SHA-256
`ee86f1bcf9596bb432ea9b9b080ff265bf0796c4f49b5cd59135389287caffaf`.

ROOT's current selected saved-admission proof ran 4 tests, returned 0 and had
failures, errors, skips, expected failures and unexpected successes all 0.
It began at 2026-10-04T15:50:18.040338+00:00 and took
16.84935620916076 seconds. The repeated scalar and sidecar digests still do not
prove freshness; actual UTC, the exact command and create-only writes do.
Five old summary, locator, custody and selected-report targets were preserved
externally before replacement. The earlier signed `3f1fff8552951a4205ebb0c87d4540761ab590fc`
matrix remains historical evidence. These durations make no performance claim.

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
