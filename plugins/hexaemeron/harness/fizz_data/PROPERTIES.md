# Emitter-fidelity properties

The suite in `test/EmitterFidelity.t.sol` compares, for each of the 27
assembly emitters vendored from `wildcat-finance/v2-protocol` at
`f5a26146987926f4811b72a795d662813dedfe85`, the log the emitter records
against the log the compiler's `emit` of the same declared event records.
Each property below carries a stable identifier and a guarantee tag.
`SHOULD-HOLD` means the declaration fixes the answer, so a violation is a
divergence between emitter and declaration. `EXPLORATORY` means the property
is inferred from how the emitters are written rather than from a declaration.

`campaign.json` beside this file records the run that exercised them: engine,
seed, run length, the commit compiled, the protocol ref, the emitter count and
the per-test result, every value parsed from the run's own output.

## Properties

| Id | Tag | Property | Tests |
| --- | --- | --- | --- |
| EF-01 | SHOULD-HOLD | topic0 of the recorded log equals the declared event's selector. | the 27 `test_emit_*` cases, `test_edge_every_emitter_at_zero`, `test_edge_every_emitter_at_max`; rejection proved by `test_rejects_wrong_topic0_specimen` |
| EF-02 | SHOULD-HOLD | The topic count equals one plus the declared number of indexed parameters, compared before any topic. | the 27 `test_emit_*` cases, both `test_edge_*` cases; rejection proved by `test_rejects_wrong_topic_count_specimen` |
| EF-03 | SHOULD-HOLD | Each indexed topic `topic1`, `topic2`, ... equals the declared indexed argument, compared in order after topic0. | the 27 `test_emit_*` cases, both `test_edge_*` cases; rejection proved by `test_rejects_wrong_indexed_topic_specimen` |
| EF-04 | SHOULD-HOLD | The data region length equals the ABI-encoded length of the non-indexed arguments, compared before the data bytes. | the 27 `test_emit_*` cases, both `test_edge_*` cases; rejection proved by `test_rejects_wrong_data_length_specimen` |
| EF-05 | SHOULD-HOLD | The data bytes equal the ABI encoding of the non-indexed arguments. | the 27 `test_emit_*` cases, both `test_edge_*` cases; rejection proved by `test_rejects_wrong_data_bytes_specimen` |
| EF-06 | EXPLORATORY | The free memory pointer at `0x40` reads the same value immediately before and after each emitter call. | `test_memory_free_pointer_unchanged_across_every_emitter` |
| EF-07 | EXPLORATORY | The zero slot at `0x60` still holds zero after each emitter call. | `test_memory_free_pointer_unchanged_across_every_emitter` |
| EF-08 | EXPLORATORY | Scratch space `0x00` to `0x3f` dirtied before a call, with the `0x40` word moved one word up, does not change the recorded log. | `test_memory_dirtied_scratch_does_not_change_the_recorded_log` |

EF-01 to EF-05 are the five fields `src/LogComparison.sol` asserts, in the
order it asserts them. Each rejection specimen under `src/specimens/` fails on
its named field and on no earlier one.

## Input domain

Each fuzz case draws its arguments from the emitter's own parameter types, so
every word reaching an emitter is ABI-clean: an `address` holds 160 bits, a
`bool` is 0 or 1, and a `uint32` is below 2^32. The fidelity claim holds over
that domain.

One emitter narrows its declaration. `emit_SanctionedAccountAssetsQueuedForWithdrawal`
takes `uint32 expiry` (`src/vendor/libraries/MarketEvents.sol:69`) where
`IMarketEventsAndErrors.sol:101` declares `uint256 expiry`. The suite fuzzes
the emitter's `uint32` domain and widens the value explicitly for the
reference. Under the pinned profile (solc 0.8.25, optimizer 200 runs, cancun),
a `uint32` produced by narrowing a wider value with `uint32(wide)` reaches the
emitter uncleaned, and its log diverges from the declaration exactly when
`wide` did not fit in 32 bits. At the protocol ref the one call site that
narrows is `uint32(block.timestamp + duration)` at
`src/market/WildcatMarketWithdrawals.sol:95`, so that log's `expiry` word would
carry the untruncated sum only once `block.timestamp + withdrawalBatchDuration`
reaches 2^32. That is a stated limit of the explored domain, not a
counterexample: the suite does not drive the emitter with a dirty word.

## What a green campaign establishes

A green campaign is the absence of a counterexample in the explored space under
the declared harness: the 27 emitters, the ABI-clean domain above, the seed and
run length in `campaign.json`, forge's stateless fuzzer with its default
dictionary, plus the two fixed companion cases at all-zero and all-maximum
arguments.

It does not establish:

- completeness of the event set. `AccountSanctioned`
  (`src/vendor/interfaces/IMarketEventsAndErrors.sol:127`) is declared and has
  no assembly emitter in the vendored closure, so it is out of scope; whether
  the protocol emits it elsewhere was not checked;
- anything about off-chain capture or decoding;
- fidelity for a dirty `uint32` or `bool` word, per the domain above;
- exhaustive enumeration of any argument domain;
- anything about gas, which Hermes owns.

## Run length

The profile in `foundry.toml` sets 256 runs. The campaign ran 1,000,000 runs
per fuzz case, 3,906 times the profile. The length was chosen from four timed
runs of the whole suite on the same host, seed `0x1`, each once except the
first: 256 runs in 0.16 s (three samples, no spread), 4,096 in 0.89 s, 32,768
in 6.26 s and 131,072 in 33.98 s, so the cost grows linearly at about 0.26 ms
per run. One foreground invocation had to finish inside a 600 s cap, and every
fuzz case lives in one test contract, so the suite cannot be split by
contract; 1,000,000 was the largest power-of-ten length that fitted with room
for load from other processes. The campaign itself took 371.89 s. These
numbers chose the length; no timing claim about the emitters follows from
them.

The seed is the SHA-256 of the text
`fiat-1354-fizz-4-emitter-fidelity-differential-suite step 4 campaign`, chosen
once and recorded; nothing depends on how it was chosen.
