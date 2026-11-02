# G2 composition with the landed fee, native-state and routing adapters

## Version boundary

The composition combines the audited #2088 product
`dc3ea7c8f1b54bbee0e687b2aff169c0e9383cfb` with landed #2091 at
`59bef33488ce929ef625bb5fdb3e73b7bca7c5d7`, which includes #2089 and #2090.
Under Laurence's 2026-11-02 ruling the accrual and state-update meanings ship as
adapter `1.4.0`, cumulative over `1.3.0`. Adapters `1.0.0`, `1.1.0`, `1.2.0`
and `1.3.0` retain their prior interpretations and keep both events as
`unsupported-canonical-meaning`. Adapter `1.4.0` retains every `1.3.0` fee,
native-state and routing meaning and adds the four `.v1` accrual and
state-update rules. New builds default to `1.4.0`. The package is `0.7.2`; the
governed generation is `tabularium-v0.11.0`. The held Compound Phase 1 frontier
is unchanged.

Eight controls were executed against the exact landed runtime at
`59bef33488ce929ef625bb5fdb3e73b7bca7c5d7`: both constructed accrual specimen
raw releases under each of `1.0.0`, `1.1.0`, `1.2.0` and `1.3.0`. Their raw
manifest, mapping and four generated-file digests are in
[`wildcat-accrual-routing-parent.json`](../../../tests/fixtures/wildcat-accrual-routing-parent.json).
The composed runtime reproduces each control byte for byte.
[`test_wildcat_accrual_composition.py`](../../../plugins/tabularium/tests/test_wildcat_accrual_composition.py)
also checks that `1.4.0` adds only accrual and state-update rows to what `1.3.0`
maps from those raw releases. On the constructed fee, native-state and routing
inputs, it checks that `1.4.0` keeps the `1.3.0` rows, mapping records and
dispositions, changing only the version label. The two accrual specimens are
rebuilt under explicit `1.4.0`; every other committed example keeps its bytes
and its recorded version.

## Executed checks

The first complete Tabularium run on the composition ran 803 tests with 17
assertion failures and no errors. Existing tests assumed `1.3.0` was the latest
selector: some used `1.4.0` as an unknown version, the feature matrix
expected native rows only under `1.2.0` and `1.3.0`, one rebuilt a `1.3.0`
release under the default and compared its bytes, and one expected
`StateUpdated` to stay unsupported under the default. The repaired tests use
`1.5.0` as unknown, include `1.4.0` in the matrix, rebuild under the recorded
version and select `1.3.0` explicitly where an unsupported event is required;
independent positive controls cover `1.4.0`. That run remains red. The repair changes no production
mapper or schema.

The complete Tabularium suite then passed 806 tests with no skips. Promise
Machine `check` reports zero findings after the composition re-pinned the
ledger digest chain and re-tallied the recorded evaluation answers over the new
tree; no model benchmark ran. The Phylax, Ephoros and Hypomnema repository lints
passed, and Imprimatur and Brevitas report no defects on the changed prose.
Checks on the signed composition are recorded separately.

## Retained evidence and limits

The fresh [integration retained report](executed/integration-retained-conformance.json)
and its [bounded observations](executed/integration-retained-conformance.observations.json)
rebuild and verify both preserved raw releases under `1.4.0`. Both generations
passed and the report value is `true`. Wildcat V1 rebuilt to raw release
`sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`; its
canonical release has `events.jsonl` SHA-256
`2c0ddaf8bbcf28262f94a16051956fa1ea6957f7721246bade1f36bfab951f32` and
`coverage.json` SHA-256
`3638999063722c17556096a16ef89a93cdf643acaca2015c5db904716268273d`. Wildcat V2
rebuilt to raw release
`sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`; its
canonical release has `events.jsonl` SHA-256
`909fd266705331e665cfe132a7297348215d8f1ac6a5a2625c4ddc5c49ae1193` and
`coverage.json` SHA-256
`05d0a2950c4a1f9f356575d05ccdc379dfd49fffaa9243938eb3dbbb0c5165bc`. The check
now also requires every accrual and state-update row to declare `1.4.0`. The
Step 4 report, its digests in `reproduction.md` and the audit records remain
unchanged.

These are public identifiers, digests and pass or refuse results only. Historical
completeness, provider independence, finality, a chain proof, identity,
settlement, accounting and current standing remain unestablished. Final signed
composition checks, hosted checks, controller receipts and merge must be
recorded separately before completion is claimed.
