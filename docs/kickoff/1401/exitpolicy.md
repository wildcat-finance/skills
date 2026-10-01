# Wildcat V2 host withdrawal policy for exit liveness

This record answers [#1495](https://github.com/wildcat-finance/skills/issues/1495)
for [#1401](https://github.com/wildcat-finance/skills/issues/1401). It states
which exits deployed Wildcat V2 must keep open under credential expiry,
role-provider removal and hook failure. It also gives the scenario matrix, the
outcome classes, the proposed search bounds and the caveat a consumer carries.
It runs no search and claims no liveness result; #1401 owns the runs.

## Decision and roles

Host maintainer and decision-maker: **laurenceday**. On 2026-09-27 they
answered five questions stated against the deployed source, in the Claude Code
session `https://claude.ai/code/session_01GCCywtCU4WjqBzE2k1moE9`. Each row in
[Policy](#policy) names the answer it rests on. P3 and P4 were the producer's
classification of the host's own guards when the maintainer accepted the record
without Janus/Pandects review on 2026-09-27. The
[acceptance comment](https://github.com/wildcat-finance/skills/issues/1495#issuecomment-5857240725)
retains that history. The answers were:

1. A holder who is not a known lender may be refused a queue once no valid
   credential exists: a permitted revert.
2. The fixed-term lock is a permitted revert until term end, for lenders and for
   `nukeFromOrbit` alike.
3. SphereX screening, sanctions-sentinel failure and token-level transfer
   failure are outside the #1401 runs and named in the consumer caveat.
4. A queued withdrawal must stay executable whatever credentials, providers and
   hooks do afterwards.
5. `nukeFromOrbit` refused because a sanctioned holder is not a known lender
   and holds no credential is a liveness failure.

Producer: **Claude, in the session above**, reading the deployed source.
Reviewer: **Codex**, applying Janus and Pandects in separate review passes on
2026-09-28. Both accept this revised policy as an input specification with the
conditions below. One agent performed both reviews; no second reviewer or new
host-maintainer decision is claimed. The [review record](policy-review.md)
names the findings and their dispositions. [Review evidence](evidence/review.json)
binds the original record, source inputs, revised outputs and command results.

## Host, adapter and model status

The host is deployed Wildcat V2 on Ethereum mainnet, at the source pins the
[kickoff registry](../1359/targets.json) records:

- Markets, `HooksFactory`, `OpenTermHooks` and the 365-day `FixedTermHooks`
  template: `wildcat-finance/v2-protocol` at
  `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`.
- The 730-day `FixedTermHooks` template: `5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa`.
  Its `src/access/FixedTermHooks.sol` differs from `a70f297f` only in
  `MaximumLoanTerm`.
- `OpenAccessRoleProvider`: the public `src/OpenAccessRoleProvider.sol` at
  `5838b2f3`, which is byte-identical to the Sourcify-verified source and to
  the file at `e1f77540` the registry names
  ([#1880](https://github.com/wildcat-finance/skills/issues/1880)). The private
  `chainalysis-ofac-role-provider` copy at
  `5d7f8c889a8d29935838a3906172feb8d9861807` has the same declarations.

At the registry's observed block 26006289 the host held 42 hooks instances: 28
`OpenTermHooks`, 3 `FixedTermHooks` on the 365-day template and 11 on the
730-day one. 37 share the `OpenAccessRoleProvider` pull provider, whose
credential lasts 90 days, and 5 carry no pull provider. The instances' other
31 distinct providers are their borrowers, each installed as a push provider
with an unbounded time to live.

[evidence/sources.json](evidence/sources.json) binds the 13 inspected source
files by revision, SHA-256, byte count and permanent URL. Their bytes were
rechecked during review. [Review inputs](evidence/review-inputs.json) add five
supporting files for rounding, batch expiry, liquidity and credential expiry,
the public provider file at the registry's revision, and the Janus and Pandects
references. Line references below are to those bytes.
A source pin does not prove the code at a given block.

The Janus harness under `plugins/janus/harness` models the v2.5 candidate at
`9716e78`. It is not deployed code. A run on it reports a modeled result under
[#1376](https://github.com/wildcat-finance/skills/issues/1376)'s label and never
stands in for the deployed host.

## What the deployed code does

Paths are under `src/` at `a70f297f` unless marked otherwise.

- **The hook binding is fixed at deployment.** The factory stores the flags the
  hooks instance returns from `onCreateMarket` (`HooksFactory.sol:507`) and the
  market keeps them immutable (`market/WildcatMarketBase.sol:43`, `:207`). Each
  template's flags are the market's requested flags masked by its optional
  flags, plus its required flags (`types/HooksConfig.sol:127-144`). Uninstall
  is therefore out of scope, as the Janus manifest's `liveness.uninstall`
  already states.
- **A hook revert reverts the exit.** `onQueueWithdrawal` and
  `onExecuteWithdrawal` call the hook with all remaining gas and re-raise its
  revert data (`types/HooksConfig.sol:321-368`, `:382-426`). The market calls
  the queue hook before it moves any balance
  (`market/WildcatMarketWithdrawals.sol:101`).
- **Execution is never hooked on deployed markets.** Both templates set
  `useOnExecuteWithdrawal: false` as an optional flag and do not require it
  (`access/OpenTermHooks.sol:69`, `access/FixedTermHooks.sol:86`, `:96-99`), so
  the mask above leaves it off. Both implementations are empty
  (`OpenTermHooks.sol:270`, `FixedTermHooks.sol:331`).
- **The queue gate.** `OpenTermHooks` enables the queue hook only if the market
  asked for it (`OpenTermHooks.sol:68`). `FixedTermHooks` always requires it
  (`FixedTermHooks.sol:99`) and refuses every queue before `fixedTermEndTime`
  with `WithdrawBeforeTermEnd` (`:315`). After the term it checks access only
  where the market asked for the queue hook (`:192`). Where the gate applies,
  a lender passes if they are a known lender on that market or can present a
  valid credential (`OpenTermHooks.sol:261`, `FixedTermHooks.sol:321`).
- **Known lenders stay known.** `isKnownLenderOnMarket` (`access/BaseAccessControls.sol:78`)
  is set when a deposit or received transfer arrives with a valid credential
  (`:752`), and no code clears it. A known lender reaches the gate without any
  credential or provider call. A holder is not known if they received tokens
  without a credential where transfers need none (`OpenTermHooks.sol:307-322`),
  or deposited without one where deposits need none.
- **Credentials.** The access check tries, in order, an unexpired credential
  from a still-registered provider, the caller's calldata suffix, a refresh from
  the last pull provider, and every other pull provider
  (`BaseAccessControls.sol:668-710`). `removeRoleProvider` empties the
  provider's entry at once (`:206-222`), so its credentials stop counting. A
  push credential cannot be refreshed by pulling. `OpenAccessRoleProvider`
  issues a fresh credential to any address the Chainalysis oracle does not
  flag, and none to one it flags (`OpenAccessRoleProvider.sol` at `5838b2f3`).
- **Provider failure.** A pull provider is read with `staticcall`, and a
  failed call supplies no credential if the caller can finish processing it
  (`BaseAccessControls.sol:484-516`). `validateCredential` runs only for a
  provider the caller names in the calldata suffix; a success returning fewer
  than 32 bytes reverts `InvalidCredentialReturned` (`:539-599`). Both calls
  forward all remaining gas. A current cached credential from a registered
  provider passes before either call, even when that provider is failing.
- **Sanctions.** A flagged caller cannot queue: `_getAccount` reverts
  `AccountBlocked` (`WildcatMarketBase.sol:244-247`), and the sentinel lookup
  reverts if its call fails (`:254-273`). Executing for a flagged account sends
  the claim to an escrow rather than to the account
  (`WildcatMarketWithdrawals.sol:256-272`); that is an executed exit, not the
  lender's receipt. `nukeFromOrbit` quarantines a flagged account's balance
  through the ordinary queue path (`market/WildcatMarketConfig.sol:82-88`,
  `market/WildcatMarket.sol:298-320`), so the queue hook runs on it.
- **Closure and liquidity.** `closeMarket` calls `onCloseMarket`
  (`WildcatMarket.sol:212-230`); `FixedTermHooks` refuses it before term end
  unless the market allows early closure or term reduction
  (`FixedTermHooks.sol:405-418`). A new batch on a closed market normally uses
  zero duration (`WildcatMarketWithdrawals.sol:94`). Closing with a pending
  expiry equal to the current timestamp creates a successor expiring one
  second later (`WildcatMarket.sol:269-276`). A batch is paid only from
  available liquidity. `repayAndProcessUnpaidWithdrawalBatches` pays unpaid batches in
  order and any caller may run it while the market is open (`:279-313`).
  Execution with no remaining integer amount for the account reverts
  `NullWithdrawalAmount` (`:243-249`), including a rounded-zero share or a
  share already collected.
- **Outside the hooks.** Every exit carries `sphereXGuardExternal`. When the
  arch controller sets a SphereX engine on a market, that engine screens each
  guarded call and can refuse it (`spherex/SphereXProtectedRegisteredBase.sol:72-87`,
  `:113-117`, `:282-286`). The sentinel lookup, its escrow-creation call
  (`WildcatMarketBase.sol:754-771`) and the underlying token's `transfer` can
  also refuse a call.

## Policy

**Scenario preconditions.** A queue attempt uses a positive scaled amount no
larger than the holder's balance. R4 uses a sanctioned holder with a positive
scaled balance; a no-op on an empty account is not an exit. A closed-market
case starts after a successful borrower-authorised `closeMarket`, including
its funding and term checks. Record the market's withdrawal access flag, known
lender status, registered providers, credential timestamps and time to live,
fixed-term end, batch state, available assets and prior collections before
applying each condition. Provider failure does not invalidate an otherwise
current cached credential. Establish credential validity from the fixture and
source rules; a failed exit alone cannot establish that no credential existed.
O1 to O3 remain outside the search.

**Required exits.** Within the search bounds, each eligible exit must succeed:

- **R1.** A known lender queues after their credential expires, after its
  provider is removed, and after any provider fails, subject only to P2 to P4.
  Answer 1 limits the permitted refusal to holders who are not known lenders.
- **R2.** A queued withdrawal executes once its batch is no longer pending
  and its remaining withdrawable amount is positive, whatever credentials,
  providers and hooks do after it was queued. Normal expiry requires time
  strictly greater than the batch expiry; closing a market can process a batch
  earlier. Use the state after the host's update and compute
  `floor(batch.normalizedAmountPaid * status.scaledAmount / batch.scaledTotalAmount)
  - status.normalizedAmountWithdrawn`. A positive total paid to the batch alone
  is insufficient. For a flagged account, execution to escrow satisfies R2.
  Answer 4; `WildcatMarketWithdrawals.sol:236-271`, `WildcatMarket.sol:242-267`.
- **R3.** A holder who is not a known lender queues while they hold a valid
  credential. P1 applies only when withdrawal access is enabled; with that
  check disabled, credential absence cannot justify a refusal. P2 to P4 still
  apply where their stated preconditions hold. Answer 1 and the queue gate.
- **R4.** `nukeFromOrbit` quarantines a flagged account's balance once any
  fixed term has ended, whether or not the account is a known lender or holds a
  credential. Answers 2 and 5.
- **R5.** R1 holds after the market closes.

**Permitted reverts.** A run records these as expected, not as failures:

- **P1.** `NotApprovedLender` on a queue with withdrawal access enabled by a
  holder who is not a known lender and has neither a valid registered cached
  credential nor another valid credential route. Expiry, provider removal or
  provider failure may leave that state; none alone establishes it. P1 does
  not cover an ungated queue or `nukeFromOrbit` (R4). Answer 1.
- **P2.** `WithdrawBeforeTermEnd` before `fixedTermEndTime`, for a lender's
  queue and for `nukeFromOrbit`, and `ClosureDisabledBeforeTerm` on
  `closeMarket` before term end when both `allowClosureBeforeTerm` and
  `allowTermReduction` are false. Answer 2 and the fixed-term close guard.
- **P3.** `AccountBlocked` on an ordinary queue by a flagged caller, whose
  balance R4 requires to be queued through `nukeFromOrbit` instead. Accepted by
  the Janus and Pandects reviews as a classification of
  `WildcatMarketBase.sol:244-246`; it never excuses an R4 failure.
- **P4.** Each host guard has its own precondition. `NullBurnAmount` is expected
  for a zero scaled request. `WithdrawalBatchNotExpired` is expected while
  the batch remains pending. `NullWithdrawalAmount` is expected only when the
  formula in R2 is zero, including insufficient funding, rounding or an
  already collected share. `InvalidCredentialReturned` is permitted for a
  caller-selected provider that succeeds with fewer than 32 return bytes only
  if the same exit succeeds without that suffix from the same starting state.
  The retry must be recorded. The Janus and Pandects reviews accept these
  classifications; none permits failure of an eligible positive exit.

**Out of scope.** These are not driven in #1401's runs and are named in the
consumer caveat: a SphereX engine refusal (**O1**), a host sentinel lookup or
escrow-creation failure (**O2**) and an underlying-token transfer refusal
(**O3**). Answer 3. O2 does not exclude a role provider's failed credential
lookup; that remains part of the provider-failure condition.

## Scenario matrix

#1401 runs each condition separately. The setup and permitted guards above
apply to every cell. A guard is accepted only when its own precondition holds;
an expected guard revert is not a successful exit. R3 includes an ungated
queue's lack of a credential requirement. Record a cached credential separately
from the ability to obtain another one.

| Actor | Credential expiry | Role-provider removal | Hook failure |
| --- | --- | --- | --- |
| Known lender, queue | R1; applicable P2 to P4 | R1; applicable P2 to P4 | R1; applicable P2 to P4 |
| Non-known holder, queue | R3; P1 only if gated and no valid credential route; applicable P2 to P4 | R3; P1 only if gated and no valid credential route; applicable P2 to P4 | R3, including a current cached credential; P1 only if gated and no valid credential route; applicable P2 to P4 |
| Any holder, execute a queued withdrawal | R2 once eligible; P4 only outside its positive preconditions | R2 once eligible; P4 only outside its positive preconditions | R2 once eligible; P4 only outside its positive preconditions |
| Flagged account, `nukeFromOrbit` | R4 after term; P2 before | R4 after term; P2 before | R4 after term; P2 before |
| Known lender, queue after `closeMarket` | R5; applicable P2 to P4 | R5; applicable P2 to P4 | R5; applicable P2 to P4 |

Hook failure includes a queue-hook revert, a provider revert, a short response
and gas exhaustion; record them separately. Execution has no hook on the
pinned templates, so R2 tests that it stays unhooked. A known lender or a valid
cached credential can bypass provider calls; do not claim that a failing
provider was exercised when it was not. Replacing an immutable hook or changing
its code in a fixture is a modeled mutation, not deployed execution.

## Outcome classes

- **Success.** An eligible required exit completed within the bounds: the
  queue was accepted, or execution transferred the positive amount in R2 to
  the account or its escrow. Record the state change and amount.
- **Failure.** An eligible required exit failed outside the applicable
  permitted guards, with a recorded trace. A failure against R4 is expected on
  deployed V2 for a flagged holder who is not a known lender and holds no
  credential on a queue-gated market. This remains a source-derived prediction;
  this record demonstrates no failure.
- **Inconclusive.** The bounds ran out before the required exit completed and
  no failing trace was found, an eligible case was never exercised, or an
  out-of-scope blocker (O1 to O3) fired. A bounded run never proves an exit
  always completes. Expected guard reverts remain guard observations; they
  cannot supply a missing success.

## Reviewed search proposal

Janus accepts these limits as a finite proposal for #1401's runbook. They remain
reviewer recommendations, not host-maintainer decisions or evidence of a run.
The runbook must pin the adapter, manifest, recorder, seeds, gas budgets, amount
vectors and coverage obligations before execution. Missing configuration or a
required case that cannot be reached within the limits remains inconclusive.

- Configurations: `OpenTermHooks` with the queue gate on and off;
  `FixedTermHooks` at both pins, with access on and off after the term.
- Actors: the borrower, a known lender, a holder who received tokens without a
  credential, a flagged known lender and a flagged holder who is not a known
  lender. One pull provider shaped like `OpenAccessRoleProvider` and one
  borrower push provider. Cover a current cached credential, expiry with and
  without refresh, removal with and without an alternative, and no credential.
- After setup, at most 12 host/provider actions per sequence and 256 recorded,
  seeded sequences per condition and configuration. Reverted attempts count.
  Include an eligible attempt for every required matrix case; a collection of
  permitted reverts does not cover it. Keep a positive control beside each
  adverse case, and record the known R4 case separately.
- Time advances include 0, 1 second, `withdrawalBatchDuration` and credential
  time to live plus 1 second. Also target one second before, exactly at and
  one second after the batch expiry, credential expiry and effective
  `fixedTermEndTime`. These are absolute targets relative to the fixture's
  timestamps, never negative advances. Credential validity includes its expiry
  second; normal batch processing requires a later timestamp. Total elapsed
  time stays at most `MaximumLoanTerm` plus three batch durations.
- Liquidity for the pending batch: none, partial and full. Include an older
  unpaid batch, two lenders in one batch, a share rounded to zero, a partially
  collected share and an already collected share. Pin gas limits for ordinary
  execution and each failing-provider case; separate budget exhaustion from a
  captured exit failure. A closed-market case starts after closure has funded
  and processed the queue, rather than assuming closure preserves an arbitrary
  illiquid starting state.

## Pandects queue-law preconditions

The Pandects review accepts these input conditions without claiming that any
law has run on deployed V2. Amounts must retain their scaled or normalized unit
and the scale factor used at each observation. Pin the mapping before #1401
consumes a law result; the reduced Wildcat model is not that mapping.

| Law | Required mapping | Review disposition |
| --- | --- | --- |
| `claims/queue-order-preserved/v1` | Order batch allocations by expiry; distinguish funding a batch from a lender collecting an allocated share. Lenders in one batch share funding pro rata. | Conditional; no per-lender collection-order claim. |
| `claims/recorded-claim-never-shrinks/v1` | Preserve claim identity and prior payments. Establish a fixed owed amount before using the equality check; pending batches can gain requests and unburned scaled claims can accrue. | Conditional; neither expiry nor the reduced model alone proves applicability. |
| `claims/reserves-cover-payable/v1` | Map the declared payable amount and reserved assets in the same units; partial funding does not declare the entire batch payable. | Conditional; do not derive a payable declaration solely from the reserves being tested. |
| `claims/pooled-claims-cover-open-batches/v1` | Keep unpaid claims, funded but uncollected amounts and collected amounts distinct, without dropping or double-counting any liability. | Conditional; deployed projection and law execution remain unperformed. |

P3 permits a sanctioned account's ordinary queue refusal while R4 retains its
required quarantine path. For R2, a transfer to escrow counts as the host exit
specified by answer 4; it does not establish receipt by the lender or release
from escrow. P4's lack of a payable amount is not evidence of voluntary delay,
and the allowance cannot hide a positive payable exit that fails.

## Consumer caveat

A consumer rendering a Wildcat exit record carries this text beside it:

> A queued withdrawal that was never executed does not by itself show the
> lender chose to wait. An unpaid batch needs available liquidity. A
> fixed-term market refuses new withdrawals until its term ends. A holder who
> is not a known lender needs a valid credential to queue where withdrawal
> access is enabled. SphereX screening,
> the sanctions sentinel or the underlying token can refuse a call outside the
> market's hooks. Events alone cannot say which occurred. A bounded run shows
> exits were live for the sequences it drove, not that every exit completes.

## What this record does not establish

It runs no search and demonstrates no failure, including the expected R4 one.
It makes no claim about V1, the v2.5 candidate, Plasma deployments, markets
deployed after block 26006289, or any market's live configuration flags. The
Janus and Pandects reviews are source-based assessments by one Codex reviewer;
they establish no executed conformance or credit-law result.
