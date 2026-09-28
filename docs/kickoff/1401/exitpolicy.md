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
[Policy](#policy) names the answer it rests on. P3 and P4 are the producer's
classification of the host's own guards and wait for review. The answers were:

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
Reviewer: **not yet assigned**. The issue asks Janus and Pandects to review the
conditions; that review has not happened, and this record claims none.

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
files by revision, SHA-256, byte count and permanent URL. Line references below
are to those bytes. A source pin does not prove the code at a given block.

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
  failing call counts as no credential rather than a revert
  (`BaseAccessControls.sol:484-516`). `validateCredential` runs only for a
  provider the caller names in the calldata suffix; a success with malformed
  return data reverts `InvalidCredentialReturned` (`:539-599`). Both calls
  forward all remaining gas.
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
  (`FixedTermHooks.sol:405-418`). After closure a new batch expires at once
  (`WildcatMarketWithdrawals.sol:94`). A batch is paid only from available
  liquidity. `repayAndProcessUnpaidWithdrawalBatches` pays unpaid batches in
  order and any caller may run it (`:279-313`). An expired batch with no paid
  share for the account reverts `NullWithdrawalAmount` (`:249`).
- **Outside the hooks.** Every exit carries `sphereXGuardExternal`. When the
  arch controller sets a SphereX engine on a market, that engine screens each
  guarded call and can refuse it (`spherex/SphereXProtectedRegisteredBase.sol:72-87`,
  `:113-117`, `:282-286`). The sentinel lookup and the underlying token's
  `transfer` can also refuse a call.

## Policy

**Required exits.** Within the search bounds, each of these must succeed:

- **R1.** A known lender queues after their credential expires, after its
  provider is removed, and after any provider fails, subject only to P2 to P4.
  Answer 1 limits the permitted refusal to holders who are not known lenders.
- **R2.** A queued withdrawal whose batch has expired and holds a non-zero paid
  share for the account executes, whatever credentials, providers and hooks do
  after it was queued. For a flagged account, execution to escrow satisfies R2.
  Answer 4.
- **R3.** A holder who is not a known lender queues while they hold a valid
  credential. Answer 1.
- **R4.** `nukeFromOrbit` quarantines a flagged account's balance once any
  fixed term has ended, whether or not the account is a known lender or holds a
  credential. Answers 2 and 5.
- **R5.** R1 holds after the market closes.

**Permitted reverts.** A run records these as expected, not as failures:

- **P1.** `NotApprovedLender` on a queue by a holder who is not a known lender
  and holds no valid credential. That covers expiry, provider removal and a
  failing provider. It does not cover `nukeFromOrbit` (R4). Answer 1.
- **P2.** `WithdrawBeforeTermEnd` before `fixedTermEndTime`, for a lender's
  queue and for `nukeFromOrbit`, and `ClosureDisabledBeforeTerm` on
  `closeMarket` before term end. Answer 2.
- **P3.** `AccountBlocked` on a queue by a flagged caller, whose balance R4
  quarantines instead. Producer classification, for review.
- **P4.** The host's own guards: `NullBurnAmount`, `WithdrawalBatchNotExpired`,
  `NullWithdrawalAmount` while liquidity has not paid the account's share, and
  `InvalidCredentialReturned` for a caller-named provider, provided the same
  exit then succeeds without the calldata suffix. Producer classification, for
  review.

**Out of scope.** These are not driven in #1401's runs and are named in the
consumer caveat: a SphereX engine refusal (**O1**), a sentinel lookup failure
(**O2**) and an underlying-token transfer refusal (**O3**). Answer 3.

## Scenario matrix

#1401 runs each condition separately. "Required" names the exit that must
succeed; "permitted" names the only reverts the run may accept for that cell.

| Actor | Credential expiry | Role-provider removal | Hook failure |
| --- | --- | --- | --- |
| Known lender, queue | Required (R1); permitted P2 to P4 | Required (R1); permitted P2 to P4 | Required (R1); permitted P2 to P4 |
| Non-known holder, queue | Required while a credential is valid (R3); P1 once none is | Required while another provider grants one (R3); P1 once none does | P1 when every provider fails; otherwise R3 |
| Any holder, execute a queued withdrawal | Required (R2); permitted P4 | Required (R2); permitted P4 | Required (R2); permitted P4 |
| Flagged account, `nukeFromOrbit` | Required after term (R4); P2 before | Required after term (R4); P2 before | Required after term (R4); P2 before |
| Known lender, queue after `closeMarket` | Required (R5) | Required (R5) | Required (R5) |

Hook failure means any revert the queue hook raises, including a provider that
fails or consumes gas. Execution cannot raise one on deployed markets, so R2
tests that it stays unhooked.

## Outcome classes

- **Success.** The required exit completed within the bounds: the queue was
  accepted, or execution moved the claim to the account or its escrow.
- **Failure.** A required exit reverted for a reason outside the permitted
  list, shown by a recorded trace. A failure against R4 is expected on deployed
  V2 for a flagged holder who is not a known lender and holds no credential on
  a queue-gated market.
- **Inconclusive.** The bounds ran out before the required exit completed and
  no failing trace was found, or an out-of-scope blocker (O1 to O3) fired. A
  bounded run never proves an exit always completes.

## Proposed search bounds

The producer proposes these for Janus to accept or change in #1401's runbook.
They are not host-maintainer decisions.

- Configurations: `OpenTermHooks` with the queue gate on and off;
  `FixedTermHooks` at both pins, with access on and off after the term.
- Actors: the borrower, a known lender, a holder who received tokens without a
  credential, a flagged known lender and a flagged holder who is not a known
  lender. One pull provider shaped like `OpenAccessRoleProvider` and one
  borrower push provider.
- At most 12 host actions per sequence and 256 recorded, seeded sequences per
  condition and configuration.
- Time advances drawn from 0, 1 second, `withdrawalBatchDuration`, credential
  time to live plus 1 second, and `fixedTermEndTime` minus and plus 1 second;
  in total at most `MaximumLoanTerm` plus three batch durations.
- Liquidity for the pending batch: none, partial and full.

## Consumer caveat

A consumer rendering a Wildcat exit record carries this text beside it:

> A queued withdrawal that was never executed does not by itself show the
> lender chose to wait. An unpaid batch waits for borrower liquidity. A
> fixed-term market refuses new withdrawals until its term ends. A holder who
> is not a known lender needs a valid credential to queue. SphereX screening,
> the sanctions sentinel or the underlying token can refuse a call outside the
> market's hooks. Events alone cannot say which occurred. A bounded run shows
> exits were live for the sequences it drove, not that every exit completes.

## What this record does not establish

It runs no search and demonstrates no failure, including the expected R4 one.
It makes no claim about V1, the v2.5 candidate, Plasma deployments, markets
deployed after block 26006289, or any market's live configuration flags. It
records no independent review.
