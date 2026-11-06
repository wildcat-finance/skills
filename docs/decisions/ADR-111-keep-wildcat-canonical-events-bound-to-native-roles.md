# ADR-111: Keep Wildcat canonical events bound to native roles

## Status

Accepted, 2026-10-03

Acceptance concerns implementation. Semantic conformance and schema parity remain required before Step 3; release reproduction remains required before integration.

## Context

Issue [#1378](https://github.com/wildcat-finance/skills/issues/1378) requires deployed Ethereum-mainnet Wildcat V1/V2 canonical events. The existing bounded archive view omits eleven of the seventeen primary contexts. Event signatures alone collapse generation and emitter role: market-token and wrapper-share `Transfer(address,address,uint256)` have different instruments. Amount-only draw/closure logs expose the pool; repayment exposes a payer who may differ from the debtor.

The [receipted study](https://github.com/wildcat-finance/skills/blob/7268f3bdfa4f828de7efe12662a1aa3be1fd1ab9/docs/kickoff/1378/study.md), [runbook](https://github.com/wildcat-finance/skills/blob/7268f3bdfa4f828de7efe12662a1aa3be1fd1ab9/docs/kickoff/1378/runbook.md) and [design evidence](https://github.com/wildcat-finance/skills/blob/7268f3bdfa4f828de7efe12662a1aa3be1fd1ab9/docs/kickoff/1378/design-evidence.json) select `role-qualified`. Fifteen selection probes leave it as the unique candidate meeting the scope and role/generation gates. Measured dispatch times and encoded table sizes describe that experiment only. They establish no full-release performance or implemented conformance.

## Decision

Dispatch full preserved native journals by generation, verified emitter role and concrete deployed ABI/source epoch, and build a self-contained release that reproduces native records, mapping evidence and coverage from its copied raw inputs.

Canonical-v3 provenance keeps its closed fields. A digest-bound source descriptor preserves recorded classes, inferred context, concrete ABI/source locations, class-qualified supporting selectors and limitations. Verification rechecks Alexandria's copied raw release and rebuilds rows and coverage; rebinding hashes cannot strengthen evidence classes or parties.

Keep native parties and units. Pool-only draw/closure never gains a factual borrower; repayment retains its emitted payer. Deposit assets/scaled claims, exit requests/payments, market-token transfers and wrapper assets/shares remain distinct. Transfer retains zero-address mint/burn and queue-custody endpoints without independent funding or settlement inference. Wrapper assets are market tokens, shares are wrapper units, and counterparties receive no shareholder look-through. Only `wildcat-v1.market-closed` and `wildcat-v2.market-closed` permit `amounts: []`; closure timestamps remain native state. Every other financial action and all older tuples retain their quantity rules.

Join `SanctionedAccountWithdrawalSentToEscrow(address,address,uint32,uint256)` to a withdrawal only on an unambiguous same-market/transaction/account/expiry/amount match. Preserve the beneficiary, actual escrow recipient, both selectors and the explicit join-inference class. The companion supports routing and creates no second cash count. Missing or ambiguous routing remains qualified.

Mapped-primary, supporting-routing, unsupported-canonical-meaning and unsupported-decode dispositions partition scoped native logs. Qualified attribution gaps may overlap mapped pool/payer rows and remain separate from omitted-event counts. Decode known unsupported topics only through accepted concrete ABI; malformed bytes claiming a supported topic refuse. Preserve original capture coverage and gaps.

## Alternatives

Projecting the existing bounded view offered reuse, but its selection probe dropped eleven required contexts. Signature-only dispatch offered a smaller table, but failed the generation/role gate. The selected role-qualified table retained all seventeen contexts and recoverable source identities; it requires explicit epoch, ABI, party and disposition validation.

Adding factual borrower parties from registry context would strengthen inference into an event observation. Converting every token transfer into financing would collapse market claims, wrapper shares and underlying cash. Both choices conflict with the accepted native-source distinctions and are excluded by the study.

## Consequences

The new `wildcat-v1` and `wildcat-v2` adapters extend only their qualified v3 tuples. Existing schema-2 paths, older v3 tuples and the six shipped Aave/Euler releases stay byte-identical and are rechecked. The build copies verified raw bytes into `source/raw-release/`, binds `source.json`, and writes `capture.json`, `events.jsonl` and `coverage.json` through fresh atomic completion. Offline verification needs no original absolute input path. Aggregate raw components remain capped at 512 MiB, records at 500,000 per journal class and canonical output at 256 MiB.

The retained V2 capture supplies fourteen recorded factory bindings and 172 market transfers with wrapper counterparties. It supplies zero wrapper instance registry entries/epochs and no wrapper-native journal coverage. Preserve those bindings at recorded evidence strength without inventing runtime-code checks or epochs. Neither capture contains sanctioned-withdrawal companions; source-bound constructed fixtures exercise those semantics with explicit synthetic labels.

Private captures, corpus/compiler members and detailed outputs remain outside Git. Public reports contain bounded digests, counts and limitations. Finality, complete historical activity, settlement, identity, current standing and accounting conclusions remain unestablished; [#1386](https://github.com/wildcat-finance/skills/issues/1386) owns accounting replay and [#1387](https://github.com/wildcat-finance/skills/issues/1387) owns function reconciliation. The [runbook](https://github.com/wildcat-finance/skills/blob/7268f3bdfa4f828de7efe12662a1aa3be1fd1ab9/docs/kickoff/1378/runbook.md) governs implementation and executed acceptance gates.
