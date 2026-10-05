# Constructed Wildcat V2 canonical specimens

These unsigned fixtures exercise deployed V2 ABI shapes and the local mapping.
All log, trace, header and code responses are synthetic. They establish no
historical activity, runtime equivalence, independent finality or borrower identity.

## Fixture scope

`release/` contains 10 canonical rows from 13 native logs: deposit, withdrawal queue
and execution, market-token transfer, draw, repayment and closure.
V2 also includes wrapper wrap, unwrap and share transfers. Its wrapper assets are market tokens; its shares are wrapper claims.
One sanctions companion supports the withdrawal recipient without adding
another cash row. Decoded Approval and an unknown topic remain unsupported.

`registry-context/release/` contains two canonical rows from 3 native logs.
It exercises Borrow and third-party DebtRepaid through authentic full registry
bytes and constructed deployment evidence. The inferred debtor differs from
the emitted payer. V1 uses NewController followed by MarketDeployed; V2 uses a
successful factory call return matched to MarketDeployed. Registered addresses
do not establish that these synthetic relationships occurred.

Both directories are independent closed releases. The auxiliary owner route
retains `recorded-interval` scope and its mandatory `constructed-staging` gap.
Those fields describe its source shape and limitation. They provide no
historical-origin or independent-provider evidence.

## Rebuild

From the repository root:

```bash
python3 plugins/tabularium/examples/wildcat-v2-v0/rebuild.py
python3 plugins/tabularium/scripts/tabularium.py verify plugins/tabularium/examples/wildcat-v2-v0/release/coverage.json
python3 plugins/tabularium/scripts/tabularium.py verify plugins/tabularium/examples/wildcat-v2-v0/registry-context/release/coverage.json
```

The builder uses fresh temporary inputs and native Alexandria and Tabularium
operations. It compares every release file with this fixture and
[expected.json](expected.json), moves both complete roots, removes disposable
original inputs and verifies each moved root offline. It changes no public file.

## Consumer boundary

Keep each complete root together, including `source/raw-release/`.
[DATA-DICTIONARY.md](DATA-DICTIONARY.md) describes its fields.
The [mapping guide](../../docs/wildcat-canonical.md) gives the refusal rules.
On a mismatch, preserve the published fixture and rebuild in a fresh directory.

The main release has declared constructed context. The auxiliary release's
registry, positional epoch, deployment asset and debtor classes are derived
from its copied synthetic evidence. Neither release supplies accounting replay,
current balances, complete settlement, canonical-chain proof or an address-to-person
link. Real retained captures' wrapper-instance and sanctions coverage remain
separate gaps.
