# Review of the #1495 host withdrawal policy

Janus and Pandects accept the revised [policy](exitpolicy.md) as an input
specification after the corrections below. This is a source review. It records
no liveness search, observed failure, deployed execution or credit-law result.

## Reviewer and subject

Reviewer: Codex in task `01a0e56b-7d09-7121-87c6-32568c46a8f7`, on 2026-09-28.
The same agent performed the Janus and Pandects passes against their canonical
skills. These are two discipline reviews by one reviewer, not two independent
reviewers. The original producer was Claude; the host decision-maker remains
`laurenceday`.

The reviewed original is `docs/kickoff/1401/exitpolicy.md` from
[PR #1951](https://github.com/wildcat-finance/skills/pull/1951), merged at
`2dbfe40e08ee41429c521e0089a31ed872a1890d`, with SHA-256
`665d6067af5fbdd3e1bb6ea7eb250fcaec00db880e004ed33e14efca0dab3ce1`.
Its `evidence/sources.json` has SHA-256
`f65da5a0784f9336bfa02bc4286ace9450ba6dc90c6f571376e9323623cd8bfc`.
The [closing comment](https://github.com/wildcat-finance/skills/issues/1495#issuecomment-5857240725)
records maintainer acceptance on 2026-09-27 before either review. That acceptance
and the five answers are preserved; this review adds no human decision.

The Skills references were read at
`51241ad9d9925d96ec527d00854adbe35ccc3836`. The host source remains V2 at
`a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`, with the second fixed-term
template and public role provider at
`5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa`.
[Review inputs](evidence/review-inputs.json) binds each file's repository,
revision, path, byte count, SHA-256 and permanent URL.
[Review evidence](evidence/review.json) binds the revised policy and this
review to those inputs and records the validation commands and results.

The follow-up preserves #1880's public-provider source correction from
`bdcf124b933a37a820d89e29e1d7b81413488150`. The provider file at the registry's
`e1f77540fef65736374de6c847743d8ca2233fb4` pin was retrieved and is
byte-identical to the already reviewed `5838b2f3` file. The merged policy and
registry are also bound as inputs; the Janus and Pandects references did not
change in that merge.

## Janus review

The pass checked whether R1 to R5 and P1 to P4 identify the host action,
credential state, permitted refusal and required completion before a run.
Source locations below resolve through the input record at the V2 pins above.

| Finding | Source and reason | Disposition |
| --- | --- | --- |
| J1495-1: P1 omitted the withdrawal access flag and surviving cached credentials. | `src/access/OpenTermHooks.sol:251`, `src/access/FixedTermHooks.sol:305`, `src/access/BaseAccessControls.sol:668`. Known lenders bypass validation; a current cached credential from a registered provider passes before provider calls. The fixed-term hook's access check depends on `withdrawalRequiresAccess`. | Corrected R3, P1, every non-known-holder matrix cell and the consumer caveat. Provider failure alone cannot justify `NotApprovedLender`; an ungated queue cannot use P1. |
| J1495-2: matrix cells could count guard reverts or empty-account calls as exit evidence. | `src/market/WildcatMarketWithdrawals.sol:134`, `src/market/WildcatMarket.sol:298`, `src/access/FixedTermHooks.sol:305`. The queue requires a valid amount; `nukeFromOrbit` does nothing to an empty balance; term and sanction conditions still matter. | Added explicit setup and eligible-attempt requirements. Restored applicable guards to the non-known and post-closure rows. A guard observation cannot stand in for a completed required exit. |
| J1495-3: the proposal omitted equality boundaries, recorded gas limits and the scope of injected hook failures. | `src/libraries/MarketState.sol:130`, `src/types/LenderStatus.sol:48`, `src/types/HooksConfig.sol:321`, `src/market/WildcatMarketBase.sol:43`. Batch expiry is strict, credential expiry inclusive, calls forward remaining gas and the hook binding is immutable. | Retained the 12-action, 256-sequence and elapsed-time caps. Added boundary targets, cached/refresh alternatives, gas and coverage requirements. Hook replacement stays labeled as a model mutation. Exact run configuration remains #1401's work. |

P2 remains supported by the fixed-term queue and close guards. Execution-hook
flags remain disabled in both pinned templates. Known-lender status is set at
`src/access/BaseAccessControls.sol:752` and no clearing assignment appears in
that source. These source observations support the input conditions; they do
not establish that the exits ran.

Janus verdict: accepted with J1495-1 to J1495-3 corrected in the revised policy.
The search limits are an accepted proposal for the runbook, not evidence that
the limits were sufficient or a claim under `janus-bounded-conformance`.

## Pandects review

The pass checked the quantities and queue states behind the exit conditions,
then compared the four claim laws with their catalogue applicability contracts.
The reduced Wildcat integration was read for its limits; its results were not
transferred to deployed V2.

| Finding | Source and reason | Disposition |
| --- | --- | --- |
| P1495-1: a non-zero paid share did not specify the remaining collectible integer amount. | `src/market/WildcatMarketWithdrawals.sol:236`, `src/libraries/MathUtils.sol:184`. Execution floors the account's proportional allocation, subtracts earlier collections and rejects zero. Pending status also matters; `src/market/WildcatMarket.sol:242` can process a batch during closure before its original expiry. | R2 now states the formula and the post-update pending-state condition. P4 covers rounded-zero and previously collected shares without excusing a failed positive claim. |
| P1495-2: P3/P4 had no reviewed scope for their economic meaning. | `src/market/WildcatMarketBase.sol:244`, `src/market/WildcatMarketWithdrawals.sol:256`, `src/access/BaseAccessControls.sol:539`. An ordinary sanctioned queue may revert; execution can pay escrow; a successful credential call returning fewer than 32 bytes reverts. | Accepted P3 with R4 still required. Accepted P4 only under each guard's stated precondition and a recorded suffix-free retry where required. Escrow payment establishes the specified host exit, not lender receipt. |
| P1495-3: the policy did not state the queue-law mapping preconditions. | `plugins/pandects/src/IWithdrawalQueueObservables.sol`, the four claim-law components and `plugins/pandects/catalogue/pandects.json`; `src/libraries/Withdrawal.sol:45`, `src/market/WildcatMarketBase.sol:650`. Batch funding, account collection, unpaid scaled liabilities and reserved normalized assets are different quantities. | Added a per-law conditional disposition. Batch order is not collection order; fixed-claim equality cannot be imported across a changing batch; partial funding cannot declare a whole batch payable. No deployed projection or law run is claimed. |

Two arithmetic examples show why the R2 qualification changes classification:
with batch paid 1, total scaled amount 3, account scaled amount 1 and prior
collections 0, `floor(1 * 1 / 3) - 0` is 0. With batch paid 9 and prior
collections 3, `floor(9 * 1 / 3) - 3` is also 0. Neither state owes another
integer unit to that account. These are formula examples, not EVM executions.

The closure description also retains the one-second successor batch created
when the pending expiry equals the closure timestamp
(`src/market/WildcatMarket.sol:269-276`). Zero configured duration alone does
not establish that an exit can execute at that timestamp.

Answer 3 excludes sanctions-sentinel failures. O2 now includes the host's
escrow-creation call as well as its lookup (`src/market/WildcatMarketBase.sol:754`);
a role provider's credential lookup remains within the provider-failure case.
This preserves the maintainer's exclusion while identifying both host calls.

Pandects verdict: accepted with P1495-1 to P1495-3 corrected in the revised
policy. The four law applications remain conditional on a target projection
and execution evidence; this review does not supply `pandects-search-record`.

## Validation and remaining boundary

All 13 originally bound source files were retrieved from their pinned public
revisions and matched their recorded byte counts and SHA-256 values. Five
supporting source files and the provider file at the registry's revision were
pinned for the reviewed conditions. The two
fixed-term source files differ only in `MaximumLoanTerm`, 365 versus 730 days.
The exact source-binding, arithmetic and prose validation results are in
[review evidence](evidence/review.json). Repository checks are reported in the
follow-up PR and its hosted checks, separately from these policy checks.

The expected R4 failure remains a source-derived prediction: a sanctioned,
non-known holder with a positive balance and no credential should encounter
the access check on a queue-gated market after term end. No trace was produced
and no observed failure is claimed. P1 and P3 cannot reclassify that required
quarantine path as an allowed refusal.

The deployment inventory, Sourcify match and private-provider equivalence
assertion are inherited from the policy and #1880 registry correction and were
not requalified here. The public source pins do not establish deployed code or
live flags. The Janus v2.5 model and reduced Pandects Wildcat model remain
separate subjects.

#1495 supplies a reviewed policy input. #1401 still owns exact execution
configuration, target-compatible adapter and law evidence, the three separate
bounded runs and their consumer caveat. Missing execution evidence stays
missing; these reviews do not close those dependencies or authorise a deployed
liveness claim.
