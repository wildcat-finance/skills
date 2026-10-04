# Wildcat V1 specimen data dictionary

Each closed root holds schema 3 events and a complete copied Alexandria raw
release. [expected.json](expected.json) binds all files, byte counts, digests,
release identities, actions and native dispositions.

## Release files

| File | Fields | Evidence boundary |
| --- | --- | --- |
| `source.json` | `raw_release`, `scope`, `contexts`, `mapping_records`, `dispositions` | Rebuilt from copied raw bytes; one mapping record and disposition per native log |
| `capture.json` | adapter, generation, capture time, request and scope | Local capture shape and fixture qualification |
| `events.jsonl` | transaction, instrument, parties, amounts, native_record and provenance | One row per primary native selector; supporting routing adds no cash row |
| `coverage.json` | source/capture/canonical claims, versions, included actions and unsupported counts | Counts and digests are rederived during verification |
| `source/raw-release/` | Alexandria manifest and every declared content-addressed object | Exact copied raw source; no external staging path is needed |

## Event units

| Event or context | Party meaning | Amount meaning |
| --- | --- | --- |
| Borrow | Pool only; no actor inferred from the log | Underlying base units |
| DebtRepaid | Emitted payer; inferred debtor stays separate in context | Underlying base units; no settlement verdict |
| WithdrawalQueued / WithdrawalExecuted | Claim account / beneficiary, with escrow only after a unique companion join | Queued market claims / paid underlying assets |
| Transfer | Emitted from and to | Market claims or V2 wrapper shares; no new-capital claim |
| MarketClosed | Pool only | Empty amounts; native closure timestamp is not cash |
| V2 wrapper Deposit / Withdraw | Caller, owner and receiver as emitted | Market-token assets and wrapper shares |

## Evidence classes

The main source class is `declared-constructed-context`; raw log references use
`recorded-rpc`. The capture source kind is `constructed-fixture`; its local-fixture
locator, scope, limitations and gaps retain the synthetic qualification.
The auxiliary roots carry
`checked-registry-context`, `checked-positional-epoch-context`,
`inferred-deployment-asset` and `registry-inferred-debtor`, while their raw captures
retain the owner-generated constructed-staging limitation.
`primary`, `supporting-routing`, `unsupported-canonical-meaning` and
`unsupported-decode` keep omitted meanings visible. Rebinding hashes cannot
validate changed parties, units, selectors, mapping classes or disposition rows.
