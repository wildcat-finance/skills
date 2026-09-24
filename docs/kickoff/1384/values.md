# Wildcat credit values and replay inputs

This record answers [#1493](https://github.com/wildcat-finance/skills/issues/1493)
for Wildcat V1 and V2 on Ethereum mainnet. It supplies a field inventory and
finite requests to [#1384](https://github.com/wildcat-finance/skills/issues/1384)
and states which projection fields remain unsupported for
[#1386](https://github.com/wildcat-finance/skills/issues/1386). It contains no
new captured state values, completed projection or law-campaign result.

Producer: **Codex, acting as Surveyor**. Reviewer: **Codex in this task**, checking
the consumer contract, Pandects interfaces, Tabularium source boundaries and
Lazarus request relations. This is one agent's source review; it is not an
independent review or new human approval. The existing human decisions remain
Dave Coleman's accepted deployment scope in [#1482](https://github.com/wildcat-finance/skills/issues/1482)
and laurenceday's consumer selection in [#1491](https://github.com/wildcat-finance/skills/issues/1491).
The accepted decision evidence stays in [targets.md](../1359/targets.md) and
[consumer.md](../1389/consumer.md).

## Bound inputs

The Skills source revision is `25597406e72cdb502fcbaba6f285f4ae20fe0d21`.
[inputs.json](evidence/inputs.json) binds each inspected repository input by
revision, SHA-256, byte count and permanent URL. [sources.json](evidence/sources.json)
does the same for the 20 inspected Solidity files. Source pins are V1
`da74452aa7d1a0f024d99efd22cc6d950a8116b7` in `wildcat-finance/wildcat-protocol`
and V2 `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` in
`wildcat-finance/v2-protocol`. A source pin does not prove code at another block.

The accepted Miskatonic consumer pin is
`54f86d2bed44f6b9f71edda8a883805f4b409b39`. It declares the CLI contract but has
no implemented numeric display fields. Inspection of
`a04f2fb22c3d37d4f93c5f4a35a86197061582b2` found no implementation to extend
that denominator. The native values below are proposed inputs, not assertions
that Miskatonic already prints them. New output fields need new rows before
their answers can be accepted. The address-query envelope must keep coverage,
source observations and release identity with any derived number.

The older [capture selection](../1374/capture.md) has no selected release in
its original record. The subsequent delivery in
[#1731 / PR #1838](https://github.com/wildcat-finance/skills/pull/1838), merged at
`104f6f82c390003fb61039d3023d07c1abe05086`, supplies both accepted captures.
This record binds that delivery without rewriting the historical selection.

| Generation | Captured interval, inclusive | Finalized boundary reported by the capture | Release SHA-256 |
| --- | --- | --- | --- |
| V1 | 18743513 to 22074622 | `22074622 / 0x8250ddca64f965fb77cb75a42d2054f9fcd3e4fd13aa657e1dcbfa04e4807a47` | `eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69` |
| V2 | 21866550 to 26022093 | `26022093 / 0x1cfd09b6dfaa2af921e367d94f24e2b1e6b7f910a7a6f4276576f09aeb3f5cb9` | `2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3` |

[scope.json](scope.json) lists every concrete address, role, source pin and
anchor: seven V1 markets among 16 subjects; 80 V2 markets among 137 subjects.
Registry observations may be later than a capture boundary. Recheck code at
the selected boundary; retain absence as a result. The requests include each
registry subject for code/account evidence, but field rows apply only to
subjects whose role is `market`. They do not assign market semantics to the
V2 collateral-contract specimens.

The private staging archives are retrievable at
[the accepted archive revision](https://github.com/wildcat-finance/skills-secretsauce/tree/32aca579219e5be4c89dfb23c4de76457fe86d03/data-sources/wildcat).
V1 is `v1/mainnet/interval-18743513-22074622/wildcat-v1-interval-18743513-22074622-staging.tar.zst`,
SHA-256 `25322e603679a24a4d9410f24aca07696cdf83ed0349b9f86b900d246b76a687`.
V2 is `v2/mainnet/interval-21866550-26022093/wildcat-v2-interval-21866550-26022093-staging.tar.zst`,
SHA-256 `0407fecac64ff15c23d298044cd2498180ceea2900bb6807330c104b348bd90a`.
Retrieval requires existing access. Both archive digests and all 232 extracted
manifest entries were checked. This task checked preserved metadata and
staging bytes; it did not rebuild either Alexandria release or prove the logs.

## Reading the field inventory

[values.json](values.json) is the row-level record. Each of its 61 rows names
meaning, units, rounding, generation, chain, concrete address/anchor references,
source function or interface, exact request family, initial-state needs,
producer, consumer, support status and the existing issue that owns acquisition.
The table below is a compact view of that inventory. Its shared coordinates
are `chain_id=1`, the matching generation's markets in `scope.json`, and that
generation's selected boundary. There is no moving `latest` block.

`previousState()` returns stored fields. `currentState()` computes accrued
state and can simulate a pending batch. Proving the stored words alone does
not prove the current view result. ABI indices in `values.json` are return-word
indices, **not storage slots**: V1 returns 13 words; V2 returns 14, inserting
`protocolFeeBips` at index 9. `scaledTotalSupply()` also runs the current-state calculation; it can include
simulated burning for an expired pending batch. `scaledBalanceOf(account)` reads
the stored account balance. `getUnpaidBatchExpiries()` reads the stored unpaid
FIFO; the pending batch is tracked separately.

Absolute storage slots have not been established
here and must not be inferred from those indices or from a reduced model.

All monetary roles use raw units of that market's underlying asset. Scaled
tokens use the ray multiplier `10**27`; basis points use `10000`. Rendering
may divide by `10**decimals` only after binding the denomination. Use integer
arithmetic in source order: `rayMul(a,b)=(a*b+10**27/2)//10**27`,
`rayDiv(a,b)=(a*10**27+b//2)//b`, `bipMul(a,b)=(a*b+5000)//10000`, and
`mulDiv(a,b,d)=(a*b)//d`. Annual linear accrual uses 31536000 seconds and
floors its division. Preserve the source's overflow checks, casts and reverts.
Do not substitute floating-point arithmetic, zero on error, or one rounding
step for several nested steps.

| Field | Meaning and units | Source request or unsupported boundary |
| --- | --- | --- |
| `state.isClosed` | Market has been closed. bool. | `previousState()`, `currentState()`; ABI words v1=0, v2=0; requires-capture |
| `state.maxTotalSupply` | Maximum normalized market supply. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `previousState()`, `currentState()`; ABI words v1=1, v2=1; requires-capture |
| `state.accruedProtocolFees` | Accrued protocol fee liability before or after view accrual. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `previousState()`, `currentState()`; ABI words v1=2, v2=2; requires-capture |
| `state.normalizedUnclaimedWithdrawals` | Processed withdrawal funds not yet executed. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `previousState()`, `currentState()`; ABI words v1=3, v2=3; requires-capture |
| `state.scaledTotalSupply` | Scaled supply including queued amounts not yet burned. scaled token units; ray scaleFactor is 10**27; never pass scaled units to Pandects. | `previousState()`, `currentState()`; ABI words v1=4, v2=4; requires-capture |
| `state.scaledPendingWithdrawals` | Unburned queued scaled withdrawals across batches. scaled token units; ray scaleFactor is 10**27; never pass scaled units to Pandects. | `previousState()`, `currentState()`; ABI words v1=5, v2=5; requires-capture |
| `state.pendingWithdrawalExpiry` | Expiry of the current pending batch; zero means no pending batch in a decoded state. uint32 Unix seconds. | `previousState()`, `currentState()`; ABI words v1=6, v2=6; requires-capture |
| `state.isDelinquent` | Delinquency flag carried by the selected stored or calculated state. bool. | `previousState()`, `currentState()`; ABI words v1=7, v2=7; requires-capture |
| `state.timeDelinquent` | Delinquency timer in the selected stored or calculated state. uint32 seconds. | `previousState()`, `currentState()`; ABI words v1=8, v2=8; requires-capture |
| `state.protocolFeeBips` | V2 mutable protocol fee rate. uint16 basis points; 10000=100%. | `previousState()`, `currentState()`; ABI words v2=9; requires-capture |
| `state.annualInterestBips` | Annual base interest rate. uint16 basis points; 10000=100%. | `previousState()`, `currentState()`; ABI words v1=9, v2=10; requires-capture |
| `state.reserveRatioBips` | Reserve ratio for supply outside queued withdrawals. uint16 basis points; 10000=100%. | `previousState()`, `currentState()`; ABI words v1=10, v2=11; requires-capture |
| `state.scaleFactor` | Accumulated normalization multiplier. uint112 ray; 10**27=1. | `previousState()`, `currentState()`; ABI words v1=11, v2=12; requires-capture |
| `state.lastInterestAccruedTimestamp` | Timestamp of the last stored or simulated accrual. uint32 Unix seconds. | `previousState()`, `currentState()`; ABI words v1=12, v2=13; requires-capture |
| `credit.asset` | Underlying denomination address. address. | `asset()`; requires-capture |
| `credit.totalAssets` | Underlying tokens held at the market. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `totalAssets()`; requires-capture |
| `credit.totalDebt` | Principal plus accrued interest owed by the borrower. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `totalDebts()`, `totalAssets()`, `currentState()`; unsupported-role-allocation |
| `credit.totalLenderClaims` | Accrued supply plus processed, unexecuted withdrawals. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `totalSupply()`, `currentState()`; requires-capture |
| `credit.reservedAssets` | Held assets earmarked for recorded withdrawal claims. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `currentState()`, `totalAssets()`, `coverageLiquidity()`; unsupported-role-allocation |
| `credit.borrowableAssets` | Assets the borrower may currently take. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `borrowableAssets()`, `currentState()`; unsupported-permission-bound |
| `credit.accruedFees` | Protocol fees accrued and not collected. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `currentState()`; requires-capture |
| `credit.observedAt` | Time all fields in this observation describe. uint256 Unix seconds. | `eth_getBlockByHash`; requires-header |
| `withdrawal.claimCount` | All historical claims, including settled entries at stable indices. uint256 count. | `getUnpaidBatchExpiries()`, `getWithdrawalBatch(uint32)`, `getAccountWithdrawalStatus(address,uint32)`; unsupported-history |
| `withdrawal.claimAt.owed` | Amount fixed when a recorded claim was made. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `getUnpaidBatchExpiries()`, `getWithdrawalBatch(uint32)`, `getAccountWithdrawalStatus(address,uint32)`; unsupported-claim-definition |
| `withdrawal.claimAt.paid` | Amount handed over against that same recorded claim. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `getUnpaidBatchExpiries()`, `getWithdrawalBatch(uint32)`, `getAccountWithdrawalStatus(address,uint32)`; unsupported-claim-definition |
| `withdrawal.payableThrough` | Exclusive stable-index prefix the system declares payable now. uint256 exclusive index. | `getUnpaidBatchExpiries()`, `getWithdrawalBatch(uint32)`, `getAccountWithdrawalStatus(address,uint32)`; unsupported-host-declaration |
| `withdrawal.queueObserved` | Whether the complete queue observation was read. bool. | `getUnpaidBatchExpiries()`, `getWithdrawalBatch(uint32)`, `getAccountWithdrawalStatus(address,uint32)`; unsupported-until-queue-mapped |
| `native.supply` | Accrued token supply; queued unburned supply remains included. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `totalSupply()`; requires-capture |
| `native.scaledSupply` | Scaled total supply from currentState, including simulated pending-batch burning. scaled token units; ray scaleFactor is 10**27; never pass scaled units to Pandects. | `scaledTotalSupply()`; requires-capture |
| `native.liabilities` | Supply plus unclaimed withdrawals plus protocol fees. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `totalDebts()`; requires-capture |
| `native.requiredLiquidity` | Reserve ratio applied outside the queue, plus all queued, unclaimed and fee requirements. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `coverageLiquidity()`; requires-capture |
| `native.arithmeticBorrowable` | max(held assets minus required liquidity,0). raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `borrowableAssets()`; requires-capture |
| `native.collectableFees` | Fee amount cash can cover after unclaimed withdrawals. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `withdrawableProtocolFees()`; requires-capture |
| `native.depositCapacity` | max(maxTotalSupply minus accrued supply,0). raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `maximumDeposit()`; requires-capture |
| `native.assetDecimals` | Decimal exponent used only for rendering the underlying unit. uint8 exponent. | `decimals()`; requires-capture |
| `native.delinquencyFee` | Penalty rate after the grace condition applies. basis points; 10000=100%. | `delinquencyFeeBips()`; requires-capture |
| `native.gracePeriod` | Time allowance used by delinquency accrual. seconds. | `delinquencyGracePeriod()`; requires-capture |
| `native.batchDuration` | Interval used to form withdrawal batches. seconds. | `withdrawalBatchDuration()`; requires-capture |
| `native.unpaidExpiries` | Stored unpaid-batch FIFO; the current pending batch is tracked separately. array of uint32 Unix seconds. | `getUnpaidBatchExpiries()`; requires-capture |
| `native.scaledBalance` | Account scaled token balance. scaled token units; ray scaleFactor is 10**27; never pass scaled units to Pandects. | `scaledBalanceOf(address)`; requires-capture |
| `native.balance` | Account balance normalized at current scale. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `balanceOf(address)`; requires-capture |
| `native.batch.scaledTotalAmount` | Scaled amount queued into the expiry batch. scaled token units; ray scaleFactor is 10**27; never pass scaled units to Pandects. | `getWithdrawalBatch(uint32)`; requires-capture |
| `native.batch.scaledAmountBurned` | Scaled amount burned against batch funding. scaled token units; ray scaleFactor is 10**27; never pass scaled units to Pandects. | `getWithdrawalBatch(uint32)`; requires-capture |
| `native.batch.normalizedAmountPaid` | Underlying reserved against burned shares in the batch. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `getWithdrawalBatch(uint32)`; requires-capture |
| `native.account.scaledAmount` | Account participation in an expiry batch. scaled token units; ray scaleFactor is 10**27; never pass scaled units to Pandects. | `getAccountWithdrawalStatus(address,uint32)`; requires-capture |
| `native.account.normalizedAmountWithdrawn` | Underlying already executed against account participation. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `getAccountWithdrawalStatus(address,uint32)`; requires-capture |
| `native.availableWithdrawal` | floor(batch funds * account shares / total shares) minus already withdrawn. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `getAvailableWithdrawalAmount(address,uint32)`; requires-capture |
| `native.outstandingDebt` | Outstanding settlement deficit including fees. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | `outstandingDebt()`, `totalDebts()`, `totalAssets()`; requires-capture |
| `config.protocolFeeBips` | V1 immutable protocol fee rate. basis points; 10000=100%. | `protocolFeeBips()`; requires-capture |
| `config.borrower` | Contract binding for borrower. address. | `borrower()`; requires-capture |
| `config.feeRecipient` | Contract binding for feeRecipient. address. | `feeRecipient()`; requires-capture |
| `config.sentinel` | Contract binding for sentinel. address. | `sentinel()`; requires-capture |
| `config.controller` | Contract binding for controller. address. | `controller()`; requires-capture |
| `config.factory` | Contract binding for factory. address. | `factory()`; requires-capture |
| `config.hooks` | Contract binding for hooks. packed 256-bit HooksConfig value; decode with the pinned hook library. | `hooks()`; requires-capture |
| `display.principal` | Borrower principal without accrued interest or fees. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | no complete direct getter/consumer definition; unsupported |
| `display.interest` | Accrued lender interest separate from principal. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | no complete direct getter/consumer definition; unsupported |
| `display.repaid` | Recorded gross repayment flow in a declared interval. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | no complete direct getter/consumer definition; unsupported |
| `display.repaymentRatio` | A ratio over a declared repayment denominator. dimensionless rational. | no complete direct getter/consumer definition; unsupported |
| `display.portfolioValue` | Value aggregated across markets or assets. unsupported until valuation denomination is selected. | no complete direct getter/consumer definition; unsupported |
| `display.withdrawalCash` | Amount an end account can spend after withdrawal execution. raw underlying asset units; display divisor 10**decimals only after asset and decimals reads. | no complete direct getter/consumer definition; unsupported |

`totalDebts()` is supply plus unclaimed withdrawals plus protocol fees.
It is not a direct implementation of Pandects' borrower principal-plus-interest
role. The V1 `outstandingDebt()` getter and the analogous V2 settlement formula
also include fee obligations. The reduced Pandects model keeps principal,
interest and fees separately; it supplies no deployed storage layout or proof
that an allocation of production balances has those semantics.

For lender claims, the proposed total is accrued supply plus unclaimed
withdrawals. Unburned queued tokens are already in supply. For reservations,
`coverageLiquidity()` is a requirement that may exceed cash; it cannot be
reported as assets already held and reserved. The native `borrowableAssets()`
getter reports an arithmetic ceiling; closure, sanctions and hooks can still
prevent borrowing.

Batch funding and account execution are separate stages. Batch
`normalizedAmountPaid` means funds reserved in the market. Account
`normalizedAmountWithdrawn` records execution, which may send funds to sanctions
escrow. Neither establishes that the lender can spend the proceeds. An open
batch also changes size. A persistent claim index, recording point, paid
definition and host-declared payable prefix remain explicit adapter work.

## Finite request handoff

Run from the repository root, choosing fresh output filenames:

```bash
python3 docs/kickoff/1384/verify.py
python3 -m unittest discover -s docs/kickoff/1384 -p 'test_*.py' -v
python3 docs/kickoff/1384/capture_requests.py v1 --out /tmp/wildcat-v1-values-requests.jsonl
python3 docs/kickoff/1384/capture_requests.py v2 --out /tmp/wildcat-v2-values-requests.jsonl
```

The generator writes **431 V1 requests and 14558 V2 requests** and contacts no
provider. [request-spec.json](request-spec.json) binds the exact expanded bytes
by digest and count. Each line has the Lazarus request shape: name, method,
params, required flag and evidence class. `eth_call` includes concrete calldata,
address and an EIP-1898 block-hash selector. Methods without arguments are in
the specification; [selectors.json](selectors.json) fixes their ABI selectors.
Parameterized requests expand the finite keys in [population.json](population.json).

Every declared request uses `evidence: recorded-rpc`, as Lazarus capture
requires. Account/code proofs come from `proof_targets`, and header verification
comes from the fixture's header component. Those separate components may establish
the supported relations below; changing an RPC record's label does not establish
one. The plan schema alone accepts labels that live capture refuses, so the
offline checks also exercise the capture path's plan acceptance function.

Getter probes use `required: false` so Lazarus preserves a revert as an error
record. Code, account-proof and header requests stay required. Optional capture
does not make a failed value optional to its consumer: any field depending on
that result stays unsupported. A plan v3 owner may require a selected successful
read after reviewing the resulting coverage; record that new plan's own digest.

That population comes only from market logs in the checked archives:
55 V1 and 1549 V2 expiry keys; 30 V1 and 2312 V2 market/account keys;
61 V1 and 3175 V2 market/account/expiry keys. Withdrawal events supply expiry
and account keys; ERC-20 Transfer supplies additional nonzero account keys.
They are observed participants, not a proved complete population. Neither
an absent key nor an empty decoded list establishes zero initial state.

The inventory is an input to a **plan v3** owned by #1384, not that completed
plan. The capture owner must select bounds, including `max_elapsed_seconds`, and
provider authority, add the ordered
receipt witness, bind the same header, and complete storage layouts and token
subjects before claiming value proofs. The empty-slot
[V1](proof-targets-v1.json) and [V2](proof-targets-v2.json) target lists cover
account/code checks only. They prove no storage quantity.

| Request with a possible separate relation | What the owning verifier must establish | Limit |
| --- | --- | --- |
| `eth_getProof(address,[],block)` | EIP-1186 account proof against the captured header's `stateRoot` | No storage slots requested; no monetary value proved |
| `eth_getCode(address,block)` | Keccak of returned code equals that proved account's `codeHash` | Source/immutable interpretation still needs its own binding |
| `eth_getBlockByHash(hash,false)` | Header encoding hashes to the selected anchor | Does not establish canonical-chain membership |
| Any `eth_call` | Preserve exact request, response or error at the selected block | `recorded-rpc` only, even inside a verified fixture |

No request has been executed in this task. A declared proof target is not
evidence that verification happened. A reverted getter remains an error;
the consumer must report unsupported coverage or refuse the dependent field.
`requireCanonical` is a provider request, not an independent finality proof.

## Opening state and omitted repayment

Replay needs the state just before the selected interval, or deployment and
constructor evidence that establishes a later market's initial state. Capture
the stored market tuple, immutable configuration, asset balances, existing
account balances, full batch history and account/batch records. Bind timestamp,
code/layout epoch, token implementation and the event ordering. Replay must
include balance changes without market logs, fee collection, rate changes,
batch funding and withdrawal execution. The twelve unknown V1 deployment
heights prevent an unconditional constructor-zero assumption.

[repayment-specimens.json](evidence/repayment-specimens.json) names one actual
repayment per generation, retaining its raw log and archive journal/line/index,
response digest and amount:

| Generation | Market | Transaction | Block | Raw event amount |
| --- | --- | --- | --- | --- |
| V1 | `0xd6440bd3c97e8bfbdc311cbbb50ada03ade4810a` | `0x102d0300976dc4db7b6b393ff8f7d27c7f219681f56105430b192ebf2cdbb33e` | 18823239 | 10000000 |
| V2 | `0xc9499006a149c553d18171747ed19aa7c6dd19e2` | `0x2bbc8def3a451f33a3bac912d00aaf8780c40702e82ce4335d93aaaa7c853dca` | 21989956 | 1000000000 |

The independent oracle is **proved underlying-token balance and relevant market
storage at the preceding and repayment block boundaries**, with the token and
market code/layout fixed. It is independent of the event stream being mutated;
provider independence is not claimed. A corresponding captured view may be a
recorded control but must retain that weaker evidence class. Pre-block hashes,
asset contracts, balance slots and those state proofs are not yet acquired.
The main #1384 fixtures stay at the final boundaries above; these two earlier
control windows are additional campaign evidence for #1393.

The positive control must replay the entire control block, in transaction and
log order, from verified opening state and equal the independent end state.
Account for every other balance-affecting action in that block; do not attribute
the whole block delta to the selected transaction. The mutation removes exactly
the selected repayment's contribution from the replay input while holding the
opening state and independent end-state oracle fixed. It must produce a named
observable mismatch. Preserve native token transfer behaviour and any difference
between the logged amount and actual assets received. If the required state or
complete transition set is unavailable, the test is unsupported.

`DebtFallsOnlyAgainstPayment` alone does not establish that this mutation is
caught: an omitted payment can leave reconstructed debt unchanged, so that law
can hold without exercising a decrease. #1393 must record the control equality,
the broken replay's concrete mismatch, and each applicable law's actual result
separately. No such campaign ran here.

## Acquisition ownership and review

These are concrete additions to existing kickoff work, deduplicated against the
open queue. They do not create circular prerequisites back into #1493, and this
mapping does not mark their work complete. [acquisitions.json](acquisitions.json)
names the required output and acceptance evidence for each handoff.

| Existing owner issue | Required acquisition or decision |
| --- | --- |
| [#1384](https://github.com/wildcat-finance/skills/issues/1384) | Execute the finite final-boundary reads; bind compiled storage layouts, underlying token/code subjects, exact slots, proofs, header and ordered receipt witness in plan v3. Keep calls recorded. |
| [#1386](https://github.com/wildcat-finance/skills/issues/1386) | Acquire opening snapshots or constructor evidence, including earlier accounts and settled batches; resolve borrower-debt, reserves, borrowability and claim/payable-prefix semantics; refuse incomplete observations. |
| [#1393](https://github.com/wildcat-finance/skills/issues/1393) | Acquire the two exact repayment control windows, bind pre-block hashes and token balance slots, and run complete versus omitted-payment replay against independent state. |
| [#1378](https://github.com/wildcat-finance/skills/issues/1378) | Preserve native repayment/withdrawal meaning, ordered source selectors, token units and per-interval coverage in the Wildcat canonical adapter. |
| [#1495](https://github.com/wildcat-finance/skills/issues/1495) | Supply the attributed withdrawal policy for expiry, provider removal and hook failure; #1386 separately owns the payable-prefix projection. |
| [#1497](https://github.com/wildcat-finance/skills/issues/1497) | Bind wrapper, destination and end-account attribution before making spendable-cash claims. |
| [#1389](https://github.com/wildcat-finance/skills/issues/1389) | Select any aggregate's population, membership, exclusions, interval, asset/valuation basis and denominator; extend the field inventory when implementation adds displays. |

The consumer review found no implemented numeric field omitted from the accepted
pin. Pandects review covers all eight credit fields, four queue value fields
and the `queueObserved` discriminator, while preserving production/model and
batch/account distinctions. Tabularium review retains gross event amounts,
source selectors and coverage without claiming repayment completion. Lazarus
review assigns only supported account/code/header relations and keeps every call
recorded. None of those source reviews supplies missing runtime evidence.

[commands.json](evidence/commands.json) records executed checks and their
results. [outputs.json](evidence/outputs.json) binds the delivered files, excluding
itself to avoid a self-reference. `verify.py` checks those digests, field
coverage, concrete populations, anchors and deterministic request bytes. It
does not certify economic applicability, source completeness or captured state.
