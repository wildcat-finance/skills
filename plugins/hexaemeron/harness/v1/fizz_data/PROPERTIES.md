# V1 emitter-fidelity properties

The suite in `v1/test/EmitterFidelity.t.sol` is the V1 counterpart of the V2
suite in `test/EmitterFidelity.t.sol`, for
[#1964](https://github.com/wildcat-finance/skills/issues/1964). For each of
the 26 assembly emitters in `wildcat-finance/wildcat-protocol` at
`da74452aa7d1a0f024d99efd22cc6d950a8116b7`, it compares the log the emitter
records with the log the compiler's `emit` of each same-named declaration
records. The source is fetched by `fetch_protocol.py` and checked against
`v1/PROVENANCE.json`. Each property carries a stable identifier and a
guarantee tag. `SHOULD-HOLD` means the declaration or the harness fixes the
answer, so a violation is a divergence. `EXPLORATORY` means the property is
inferred from how the emitters and their call sites are written.

`campaign.json` beside this file records the run that exercised them. It
names the engine, seed, run length, the commit compiled, the protocol ref,
the emitter count and each test's result, every value parsed from the run's
own output. That output is committed byte for byte as `campaign-output.txt`
and named by `output_sha256`.

## Compiler profile

The suite builds under the `v1` profile in `foundry.toml`: solc 0.8.22, the
IR pipeline, `shanghai`, 200 optimizer runs and no metadata hash. Those are
the settings the registry row `wildcat-v1-ethereum-mainnet` records for every
V1 build, and `tests/test_harness_v1.py` holds the profile to that record.
The V2 suite keeps its own profile.

## Scope

The inventory is the #1962 table, `docs/kickoff/1962/emitters.json`: 26
emitters and 37 rows, one row per pair of an emitter and a same-named
declaration. The mirror contract has one reference function per row, and
each emitter's fuzz case holds its assembly log to every one of them.
`tests/test_harness_v1.py` fails if a row has no reference, a reference has
no row, or an emitter's pairing helper skips one of its references.

| Disposition | Emitters | Rows |
| --- | --- | --- |
| Exercised, every same-named declaration compared | 26 | 37 |
| Unsupported | 0 | 0 |
| Unreachable from a deployed V1 build | 0 | 0 |
| Unreviewed in #1962 | 0 | 0 |

No scoped event is anonymous and no scoped event name is overloaded, so no
case for either exists. `IWildcatArchController.sol` declares event variants
that disagree with the arch controller's own declarations. #1962 records
them. Those events are emitted with Solidity `emit`, not by an assembly
emitter, so they are outside this suite.

## Properties

| Id | Tag | Property | Tests |
| --- | --- | --- | --- |
| EF-01 | SHOULD-HOLD | topic0 of the assembly log equals the selector of every same-named declaration. | the 26 `test_emit_*` cases and the five `test_edge_*` cases; rejection proved by `test_rejects_wrong_topic0_specimen` |
| EF-02 | SHOULD-HOLD | The topic count equals one plus the declared number of indexed parameters, compared before any topic. | as EF-01; rejection proved by `test_rejects_wrong_topic_count_specimen` |
| EF-03 | SHOULD-HOLD | Each indexed topic equals the declared indexed argument, compared in order after topic0. | as EF-01; rejection proved by `test_rejects_wrong_indexed_topic_specimen` |
| EF-04 | SHOULD-HOLD | The data region length equals the ABI-encoded length of the non-indexed arguments, compared before the data bytes. | as EF-01; rejection proved by `test_rejects_wrong_data_length_specimen` |
| EF-05 | SHOULD-HOLD | The data bytes equal the ABI encoding of the non-indexed arguments. | as EF-01; rejection proved by `test_rejects_wrong_data_bytes_specimen` |
| EF-06 | EXPLORATORY | The free memory pointer at `0x40` reads the same value immediately before and after each emitter call. | `test_memory_free_pointer_unchanged_across_every_emitter` |
| EF-07 | EXPLORATORY | The zero slot at `0x60` still holds zero after each emitter call. | `test_memory_free_pointer_unchanged_across_every_emitter` |
| EF-08 | EXPLORATORY | A dirtied scratch space, `0x00` to `0x3f` overwritten and the `0x40` word moved one word up, does not change the recorded log. | `test_memory_dirtied_scratch_does_not_change_the_recorded_log` |
| EF-09 | SHOULD-HOLD | A window holds exactly one assembly log, from the wrapper, then exactly one reference log per same-named declaration, each from the mirror. | every case that compares an assembly log with a reference |
| EF-10 | EXPLORATORY | A value narrowed with `uint32(wide)` and passed to a `uint256` emitter parameter reaches the log as the truncated `uint32`. | `test_narrowing_call_site_reaches_the_log_truncated` |

EF-01 to EF-05 are the five fields `v1/src/LogComparison.sol` asserts, in the
order it asserts them. Each rejection specimen under `v1/src/specimens/`
fails on its named field and on no earlier one. EF-06 and EF-07 matter more
for V1 than for V2: `emit_WithdrawalBatchExpired` and
`emit_SanctionedAccountWithdrawalSentToEscrow` write their third data word
over `0x40` and restore it afterwards.

## Input domain

Each fuzz case draws its arguments from the emitter's own parameter types, so
every word reaching an emitter is ABI-clean: an `address` holds 160 bits, a
`bool` is 0 or 1 and a `uint32` is below 2^32. `AuthRole` is drawn as a
`uint8` and folded onto the enum's four members, so every drawn value is a
member. The fidelity claim holds over that domain. The fixed companion cases
add, on every run, all-zero, all-one, top-bit and all-maximum arguments, and
`AuthorizationStatusUpdated` at each `AuthRole` member.

No V1 emitter narrows its declaration. Where the #1962 table notes a
sub-word parameter, the emitter's type equals the declaration's.

## Call-site restrictions and narrowing

The domain above is wider than what the protocol passes. At the protocol ref
the sub-word values reaching an emitter come from these sites:

| Emitter parameter | Call site | Value passed |
| --- | --- | --- |
| `StateUpdated.isDelinquent` (`bool`) | `src/market/WildcatMarketBase.sol:556` | a comparison result, `state.liquidityRequired() > totalAssets()` |
| `AuthorizationStatusUpdated.role` (`AuthRole`) | `src/market/WildcatMarketBase.sol:162`, `:203` | the constants `AuthRole.Blocked` and `AuthRole.DepositAndWithdraw` |
| `AuthorizationStatusUpdated.role` (`AuthRole`) | `src/market/WildcatMarketConfig.sol:106`, `:134` | `account.approval`, read from storage |
| `SanctionedAccountWithdrawalSentToEscrow.expiry` (`uint32`) | `src/market/WildcatMarketWithdrawals.sol:212` | the `uint32 expiry` argument of `executeWithdrawal` or `executeWithdrawals`, decoded from calldata |
| `SanctionedAccountWithdrawalSentToEscrow.escrow` (`address`) | `src/market/WildcatMarketWithdrawals.sol:212` | the `address` returned by the sentinel's `createEscrow`, decoded from returndata |
| `Transfer.to` and `SanctionedAccountAssetsSentToEscrow.escrow` (`address`) | `src/market/WildcatMarketBase.sol:171`, `:173` | the `address` returned by the sentinel's `createEscrow`, decoded from returndata |
| the SphereX old-value, current-admin and old-admin arguments (`address`) | `src/spherex/SphereXConfig.sol:116`, `:127`, `:134`, `:146`; `src/spherex/SphereXProtectedRegisteredBase.sol:116` | `_getAddress(slot)`, which loads the slot's raw word into an `address` with assembly `sload` |

The SphereX reads are not cleaned. Their words are clean only because every
write to those slots is `_setAddress` of a typed `address`
(`SphereXConfig.sol:180`, `SphereXProtectedRegisteredBase.sol:293`), and
nothing else under `src/` names the slots. Every other `address` argument is
`msg.sender`, `address(this)`, `address(0)`, a typed function or constructor
argument, or a typed storage read.

One site narrows. `src/market/WildcatMarketWithdrawals.sol:106` stores
`uint32(block.timestamp + withdrawalBatchDuration)` in a `uint32`, then
passes it to `emit_WithdrawalBatchCreated` at `:107` and `emit_WithdrawalQueued`
at `:118`, whose `expiry` parameter is `uint256`. EF-10 exercises that
pattern over the full `uint256` domain of the wide value: under the `v1`
profile the log carries the truncated value, the same `uint32` the market
stores. Once `block.timestamp + withdrawalBatchDuration` reaches 2^32 the
stored expiry wraps. That is protocol behaviour, which this suite records and
does not repair, and the log agrees with the stored value.

## What a green campaign establishes

A green campaign is the absence of a counterexample in the explored space
under the declared harness. That space is the 26 emitters against their 37
declarations, the ABI-clean domain above, the seed and run length in
`campaign.json`, forge's stateless fuzzer with its default dictionary, and
the fixed companion cases.

It does not establish:

- that the harness build's bytecode equals the deployed bytecode. The
  profile matches the registry's compiler record, but the harness compiles
  the emitters into its own wrapper, not into the deployed contracts;
- completeness of the event set or of any capture, or anything about
  off-chain decoding;
- fidelity for a dirty `uint32`, `bool`, `address` or enum word, per the
  domain above;
- exhaustive enumeration of any argument domain;
- protocol safety, or anything about gas, which Hermes owns.

## Run length

The profile sets 256 runs. The campaign ran 1,000,000 runs per fuzz case,
3,906 times the profile and the same length as the V2 campaign. Three timed
runs of the whole suite on the same 4-core host, seed `0x1`, one sample
each, took 0.56 s at 256 runs, 6.65 s at 4,096 and 58.0 s at 32,768, about
1.8 ms per run, most of it in the two memory cases. At that rate 1,000,000
runs fitted a background job. The campaign itself took 2,118.99 s while
other suites shared the host. These numbers chose the length; no timing
claim about the emitters follows from them.

The seed is the SHA-256 of the text
`wildcat-finance/skills#1964 V1 emitter-fidelity campaign`, chosen once and
recorded. Nothing depends on how it was chosen.
