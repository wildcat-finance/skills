# Wildcat canonical events

`wildcat-canonical` writes schema 3 events for deployed Wildcat V1/V2 from a
verified local Alexandria release. It preserves native records, actual parties,
financial units and unsupported coverage. All commands operate offline.

## Build and reproduce

From the repository root:

```bash
python3 plugins/tabularium/scripts/tabularium.py wildcat-canonical \
  --alexandria-release <raw-release-dir> \
  --release <release-id> --out <new-release-dir>
python3 plugins/tabularium/scripts/tabularium.py verify <new-release-dir>/coverage.json
```

The output directory must be fresh. It contains `source/raw-release/` with
every preserved raw-release file, plus `source.json`, `capture.json`,
`events.jsonl` and `coverage.json`. Moving that directory preserves verification:
`verify` rechecks Alexandria, rederives context and compares every generated
byte. Rebinding descriptor or coverage digests cannot bless changed parties,
selectors, financial units or evidence classes. Links, input/output aliases,
undeclared files, duplicate identities and malformed supported ABI are refused.

## Native meaning

Seven market contexts per generation and three V2 wrapper contexts make
seventeen primary mappings. The action and instrument stay generation-qualified.

| Native event / scope | Actual parties | Financial units |
| --- | --- | --- |
| Deposit / V1-V2 market | depositor and minted-token account | underlying assets; assetless scaled claims |
| WithdrawalQueued / V1-V2 market | withdrawing account | normalized market claims; assetless scaled claims; no payment |
| WithdrawalExecuted / V1-V2 market | beneficiary account; escrow recipient only after a unique routing join | underlying assets paid |
| Transfer / V1-V2 market | from and to, including zero and queue-custody endpoints | market-token claims; no fresh capital inference |
| Borrow / V1-V2 market | pool only | underlying assets; borrower actor absent |
| DebtRepaid / V1-V2 market | emitted payer and pool | underlying assets; payer need not be debtor |
| MarketClosed / V1-V2 market | pool only | empty `amounts`; timestamp stays native state |
| Deposit / V2 wrapper | caller and owner | market-token assets; wrapper shares |
| Withdraw / V2 wrapper | caller, receiver and owner | market-token assets; wrapper shares |
| Transfer / V2 wrapper | from and to | wrapper shares |

Withdrawal execution observes the claim account, not its executor. A unique
`SanctionedAccountWithdrawalSentToEscrow(address,address,uint32,uint256)`
companion matches generation, market, transaction, account, expiry and amount.
It preserves beneficiary, escrow recipient and both selectors with
`join-inference`; it adds no second cash withdrawal. Missing or ambiguous
companions leave the recipient gap. Wrapper assets are market tokens, with no
shareholder look-through or underlying pool cash-flow inference.

## Evidence and coverage

Dispatch uses generation, admitted emitter role and concrete ABI before topic.
Pinned declarations establish ABI layout; the retained normalized inspections
do not establish a new compiler run or runtime-bytecode equivalence. Raw native
references keep their recorded class. Context distinguishes
`checked-registry-context`, `checked-positional-epoch-context`,
`inferred-deployment-asset`, `recorded-constructor-context`,
`registry-inferred-debtor` and `declared-constructed-context`.

Each scoped native log has exactly one disposition: `primary`,
`supporting-routing`, `unsupported-canonical-meaning` or `unsupported-decode`.
The descriptor preserves this closed denominator and all native records.
Coverage counts mapped actions and qualified gaps separately. Keys are
`attribution:<action>:<role>`, `canonical:<role>:<signature>` and
`decode:<role>:<topic>`. Attribution gaps can overlap mapped rows; adding them
to omitted-log counts would overcount. Malformed accepted ABI is fatal.

Underlying amounts remain exact base-unit strings. Unknown asset context stays
null with a gap. V1 constructor evidence supplies no decimals; V2 decimals
retain only the recorded constructor context. No display scaling is inferred.

## Capture limits and recovery

Constructed raw releases remain `constructed-fixture` inputs with declared
context and an explicit origin limitation. Each capture must be `subject-scoped`,
with CAIP-10 subjects matching the declared emitter set; this comparison ignores
order. Digest agreement proves those local bytes and declarations; it does not
turn a fixture into historical capture or
prove deployed runtime code. The retained V2 capture has factory wrapper
bindings and market-token counterparties, with no established wrapper-instance
registry, epoch or native-journal coverage.

Components are capped at 64 MiB, aggregate component bytes at 512 MiB, each
journal class at 500,000 records and each generated artefact at 256 MiB.
These finite journals establish neither lifetime activity, canonical-chain
finality, current credit standing, identity nor complete settlement. V1 closure
can leave an expired, unprocessed withdrawal batch unpaid. Releases are unsigned;
offline verification does not authenticate a publisher.

On refusal, preserve the input and inspect the named field or byte mismatch.
Correct the source or interpretation in a new release directory, then rerun
`wildcat-canonical` and `verify`. Schema 2 and all six published Aave/Euler
example releases remain unchanged; Wildcat canonical output requires schema 3.
