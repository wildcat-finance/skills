# Transaction-position epochs: proof

This is the final-step proof for issue
[#1503](https://github.com/wildcat-finance/skills/issues/1503). The
[study](study.md), [runbook](runbook.md) and
[design evidence](design-evidence.json) select `position-boundary`. The
compatibility decision is the "Transaction-position design decision" section of
the [Alexandria ledger](../../skills/alexandria/EVOLUTION.md), which also holds
the frontier row this proof supports.

## The guard fails on the parent

The regression is `ProductionConformanceTests.test_before_and_after_upgrade` in
[`tests/test_epoch_positions.py`](../../tests/test_epoch_positions.py). It runs
the real collect and build path over an upgrade block with a proxy log in an
earlier transaction and asserts that log's owner.

Replayed on a detached worktree of `7cfb7a55`, the parent before the
implementation, with the test file from `1609b86d` copied in, from
`plugins/alexandria`:

```bash
python3.14 -m unittest tests.test_epoch_positions.ProductionConformanceTests.test_before_and_after_upgrade
```

It ran one test and exited 1 with one assertion failure and no errors. The
before-upgrade owner came back as the replacement,
`0x8b3e1f2a4c5d6e7f8091a2b3c4d5e6f708192a3b`, where the test expects
`0x42f9505a376761b180e27a01ba0554244ed1de7d`. That matches the failure step 2
preserved. The same test passes at `1609b86d` inside `production-attribution`.

## Production conformance

Each resolver runs its named assertions and writes a report only when every one
ran and passed with nothing skipped. On a clean detached worktree of `1609b86d`
all 16 assertions passed. The four commands below were then rerun at step 3 as
separate commands. Each exited 0, and each rerun reproduced the report step 2
had written byte for byte; the resolver refuses to replace differing evidence.

| Criterion | Assertions | Report | SHA-256 |
| --- | --- | --- | --- |
| `production-attribution` | 8 of 8 | [report](reports/conformance/position-boundary-production-attribution.json) | `197578d608d0f29c1d9b999287773b44d6006f066d6bb797c413e8f7243fe6c2` |
| `legacy-release-identity` | 3 of 3 | [report](reports/conformance/position-boundary-legacy-release-identity.json) | `51c02442ba0b43f21518e429c3fb4a6e0019224d5842fce47c54ad044903c547` |
| `offline-rederivation` | 3 of 3 | [report](reports/conformance/position-boundary-offline-rederivation.json) | `44bc4661555d42fb4cf2b9251a027bb0fcd6655f36cf7ea9d6d4033c36ba0081` |
| `resume-and-refusal` | 2 of 2 | [report](reports/conformance/position-boundary-resume-and-refusal.json) | `1c4718bc7e81e0fed1c8c834edf53b7c92b02c693e17321d3311714db1a62eec` |

The command for each is `python3.14 .hexaemeron/design/conformance.py
<criterion>`, run from the run worktree's root, where the controller keeps the
working copy of [design/conformance.py](design/conformance.py).
`design_evidence.py --transition integration` reports `clean` over the
controller's record and over the committed copy beside this file. The rejected
`block-only` candidate's conformance stays pending and was never run.

## Demonstrations

| Example | Receipt | Release |
| --- | --- | --- |
| [`usdc-interval-v0`](../../examples/usdc-interval-v0/README.md) | v1, synthetic | `sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa`, unchanged |
| [`usdc-interval-live-v0`](../../examples/usdc-interval-live-v0/README.md) | v1, live | `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32`, unchanged |
| [`usdc-interval-epochs-v0`](../../examples/usdc-interval-epochs-v0/README.md) | v2, synthetic upgrade block | `sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036` |
| the same, from the live staging bytes | v2, live | `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a` |

The v2 demonstration pins each log's owner literally, and its `verify` re-runs
the hostile cases offline. A release re-ingested under fresh digests with the
before-upgrade log moved to the replacement, or with the boundary moved one log
later, is refused by `check` on ownership rather than on a digest. An ordinary
log inside the upgrade transaction is refused at collection, before or after
the announcement. Every `verify` result names its receipt semantics:
`v1-block-only` for the two historical examples and `v2-positional` for both
new releases.

One compatibility fact surfaced there. The `usdc-interval-v0` fixture answers
its first block with a hash its own first log does not carry. V1 never compared
the two, so its release still reproduces; a v2 build of that fixture refuses.
The v2 demonstration answers the first block with the log's hash and records
the refusal.

## Frontier evidence

The v2 receipt publishes a transaction index for every log, but reconciliation
compares `(blockHash, transactionHash, logIndex, address, topics, data)`. In the
demonstration, a second provider that differs only in one log's transaction
index, `0x3` against `0x7`, reconciles as `agreed` with no dispute. Both streams
pass coordinate validation, so no refusal hides the difference. That observation
is the next Fiat job in the ledger.

## Carryover

| Item | Disposition |
| --- | --- |
| `epoch-attribution-by-transaction` | Delivered by this run. |
| `untestable-release-labels`, `unconsumed-release-components`, `refusal-receipt-status-field`, `socket-confinement-evidence` | Stay with [#1442](https://github.com/wildcat-finance/skills/issues/1442), [#1443](https://github.com/wildcat-finance/skills/issues/1443), [#1444](https://github.com/wildcat-finance/skills/issues/1444) and [#1445](https://github.com/wildcat-finance/skills/issues/1445). |
| `sources-coverage-refresh` | Refreshed through its generator at step 3; the manifest and ledger links were already current. |
| `second-transport-independent-derivation`, `epoch-boundary-headers-not-re-asked` | Unchanged: the boundaries of the earlier collector design still hold. |
| `runbook-files-field-accuracy`, `brevitas-signals-on-changed-markdown` | Earlier records; this run names its own files. |
| Transaction index absent from reconciliation | New gap, held as the next Fiat job. |

## What this does not establish

An owner is an inference from a preserved announcement and log positions, not a
proof of which implementation executed or emitted a log. The live capture has
no proxy log earlier in its upgrade block, so only the synthetic release
instantiates that case. Multiple upgrades in one block, an upgrade in the
interval's first block and ordinary logs in the upgrade transaction still
refuse. No duration or memory figure was measured, and the native and Linux
checkpoint proofs belong to the controller rather than to this record.
