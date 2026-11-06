# Hermes review of the emitter-fidelity reference

## Decision

Accepted for CMP-10's executable-reference obligation, limited to the 27 assembly emitters and ABI-clean arguments described below. This is Hermes's recorded review judgement for [#1597](https://github.com/wildcat-finance/skills/issues/1597), dated 2026-09-14.

The [CMP-10 rule](reference-solidity-0.8.25.md#cmp-10--require-semantic-equivalence-testing) also requires validation of outputs, storage, logs, reverts, calls, value movement and protocol invariants. This suite addresses logs alone. It supplies no gas measurement, accepted optimisation candidate or `hermes-candidate-acceptance` result. Future candidates still owe Hermes's baseline and all applicable verification gates.

## Evidence reviewed

Paths below are relative to `plugins/hexaemeron/harness/` unless qualified otherwise. The delivered subject is [PR #1601](https://github.com/wildcat-finance/skills/pull/1601), merge commit `01691bbc896927eb964a8c8b37c9a0dcba523544`.

| Subject | Identity | Review result |
| --- | --- | --- |
| Protocol source | `wildcat-finance/v2-protocol` at `f5a26146987926f4811b72a795d662813dedfe85` | All 11 files, 46,799 bytes, fetched and checked against `PROVENANCE.json`; their digests also match the historical campaign source. |
| Historical campaign | Commit `c2b2dc03f69327f980a2a84174184538af2fdc27`; `src/` tree `4aa524cc8c0875d3d882f7fe276ad1f29209cbdd`; `test/` tree `3dd9589ff53be6969dfc7d346f7c57c9295bc805` | Git tree identities recomputed. Apart from removal of the fetched source from Git, only three comments differ in the delivered harness sources. |
| Delivered harness | `src/` tree `bab9cfbe88438bcc3d1f5635a49dbbf30d9f5f56`; `test/` tree `75b8d56a5c51bfedcd95e3f12eda88ded5c4c9e2` | 27 emitter names match the assembly wrappers, declaration-based reference functions and individual fuzz cases. |
| Preserved campaign output | `fizz_data/campaign-output.txt`; SHA-256 `177bf35c326e6c8f318aeea0d40bb48671460ba3d0963f6224144b22c6d0f4b4` | Digest recomputed. `campaign.json` records 39 passed, 0 failed, 0 skipped and 0 counterexamples at 1,000,000 runs for each of 29 fuzz cases; this review did not repeat that campaign length. |
| Review rerun | Forge 1.7.1, commit `4072e48705af9d93e3c0f6e29e93b5e9a40caed8`; solc 0.8.25, Cancun, optimiser 200 runs | 39 passed, 0 failed, 0 skipped at 4,096 runs per fuzz case; [preserved output](emitter-fidelity-1597-output.txt). All 21 Python harness tests also passed. |

The campaign and review rerun use seed `0x95e2c90e3908b78cd1b11217b69762250840acba7fc9c22f3a30ab92d7fcb55a`. Reproduce the review from the harness directory:

```sh
python3 fetch_protocol.py
forge test --fuzz-seed 0x95e2c90e3908b78cd1b11217b69762250840acba7fc9c22f3a30ab92d7fcb55a --fuzz-runs 4096
python3 -m unittest discover -s ../tests -t ../tests -p 'test_harness_*.py'
```

`MirrorEmitReference.sol` imports the event declarations and uses the compiler's `emit`; it does not copy assembly selectors or offsets. `EmitterFidelity.t.sol` requires exactly two logs with the expected producer addresses and ordering. `LogComparison.sol` compares topic count, topic0, every indexed topic, data length and the Keccak-256 hashes of the data bytes, in that order. The five wrong specimens must fail with the expected field name. Fixed zero and maximum cases exercise every emitter independently of the fuzz seed.

## Accepted limits and reuse

The [EF-01 to EF-08 properties and limits](../../plugins/hexaemeron/harness/fizz_data/PROPERTIES.md) remain attached to this acceptance. EF-01 to EF-05 concern the log comparison; EF-06 to EF-08 are exploratory memory observations. They do not establish memory safety in every calling context. `AccountSanctioned` has no assembly emitter in the fetched emitter files and remains outside this denominator.

The ABI-clean restriction is acceptable for retaining this executable reference. It is insufficient to accept a candidate whose internal callers can supply dirty narrow values. The external wrappers clean or reject arguments before the emitter runs; the reference explicitly widens the clean `uint32 expiry` to the declaration's `uint256`.

`PROPERTIES.md` records a divergence for an uncleaned narrowing into `emit_SanctionedAccountAssetsQueuedForWithdrawal` once the wider value reaches 2^32 under the pinned profile. The upstream `src/market/WildcatMarketWithdrawals.sol:95` contains `uint32(block.timestamp + duration)`. This review inspected that cast but did not reproduce the dirty-word experiment or establish its reachability through the complete production call path. Neither claim is strengthened by the green rerun.

This acceptance establishes the reference's suitability for the stated comparison, with observed absence of a counterexample in the explored domain. It establishes neither exhaustive equivalence nor off-chain capture or decoding correctness. Reuse for changed source, declarations, compiler settings or input domains requires a new review and run. A candidate involving narrow internal values also needs direct call-site tests that preserve the potentially dirty words; the current acceptance does not waive that evidence.
