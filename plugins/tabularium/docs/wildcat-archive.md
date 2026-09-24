# Wildcat archive mapping

Issue [#1895](https://github.com/wildcat-finance/skills/issues/1895) adds an
offline replacement for the fields preserved evidence can support. It uses
the [#1493 value map](../../../docs/kickoff/1384/values.md). Retirement of the
existing subgraph route remains
[#1896](https://github.com/wildcat-finance/skills/issues/1896); the parent
[#1493](https://github.com/wildcat-finance/skills/issues/1493) stays open.

Alexandria verifies the raw interval release. Tabularium interprets its native
logs and deployment calls. Probitas selects facts for the addresses supplied
by the caller. Selecting `--wildcat-release` suppresses Wildcat's subgraph
adapter, including beside `--live` or `--fixtures`. No missing archive field
is filled from that adapter. Other venues retain their selected route.

## Run offline

From the repository root, using absolute paths without symlink components:

```bash
python3 plugins/tabularium/scripts/tabularium.py wildcat-view \
  --alexandria-release <verified-release-directory> --out <new-view.json>
python3 plugins/tabularium/scripts/tabularium.py verify-wildcat-view \
  --alexandria-release <verified-release-directory> --out <new-view.json>

python3 plugins/probitas/scripts/probitas.py collect \
  --entity "<counterparty>" --address 0x... \
  --wildcat-release <v1-release-directory> \
  --wildcat-release <v2-release-directory> --out evidence.json
python3 plugins/probitas/scripts/probitas.py render evidence.json --out dossier.md
python3 plugins/probitas/scripts/probitas.py verify dossier.md evidence.json
```

One release per generation is accepted. A repeated generation is refused.
The view is `tabularium-wildcat-view/v1`, separate from canonical event schema
3. Outputs must sit outside the raw release. An existing output with different
bytes is refused. Verification rebuilds every output byte from the verified
source. Probitas invokes that same mapper directly; it does not trust a view
file supplied by a caller. R2 supplies custody of the preserved input; these
commands read local releases and make no R2 or RPC requests.
Probitas refuses output inside any input release or through a linked path,
and replaces its evidence output atomically.

## Field dispositions

`directly-observed` means decoded from a recorded native log, with its capture
evidence class retained. `derived-from-recorded-evidence` means a documented
join or interpretation of those bytes. No EVM state replay occurs here.
`unsupported` fields remain absent and enter the gap inventory. These classes
do not authenticate the provider or prove Ethereum state.

| Consumer family | Preserved meaning | Unsupported meaning |
| --- | --- | --- |
| `market_terms` | `MarketDeployed`: market, market name and symbol, asset, maximum supply, initial annual interest and reserve ratio, fee, batch duration, grace period; V2 hooks word | Current annual interest or reserve ratio; underlying token symbol and decimals |
| `market_standing` | No row emitted | Current closure, delinquency or penalty flags; lifetime borrowed, repaid or penalty-interest totals |
| `market_closed` | `MarketClosed` occurrence and its emitted timestamp | Who closed it; present standing; repayment completion |
| `delinquency_entered` | No row emitted | Required liquidity and held assets; a complete episode boundary |
| `delinquency_cured` | No row emitted | Required liquidity, held assets, seconds delinquent and grace-period outcome |
| `borrow` | `Borrow.assetAmount`, as raw integer units | Current debt or a complete lifetime total |
| `repayment` | `DebtRepaid.assetAmount` and indexed `from`, retained separately as `payer` | Repayment by the borrower personally; settlement of every obligation |
| `withdrawal_batch_expired_unpaid` | No row emitted | Present unpaid status, normalized requested amount and paid amount under the old consumer claim |

Every row retains the complete native log and a field-class map. The emitting
market on a borrow, repayment or closure row is joined through the verified
registry. `terms_at=deployment` is derived context and is printed as "At
deployment" in the dossier. Initial APR must not be presented as current APR.
The reserve ratio is the original deployment ratio. An expiry log's scaled
amounts must not become normalized requests without the required scale and
state. A `StateUpdated` flag alone supplies neither the liquidity operands nor
the elapsed delinquency needed by the old claims.

Block number, block hash, transaction hash and log index come from the recorded
log. `observed_at` remains absent: the selected log journals do not supply
timestamps for every event. Market-token metadata does not supply underlying
token metadata. Probitas prints raw units when decimals are unsupported.

## Borrower attribution

The source rules are pinned to V1 commit
`da74452aa7d1a0f024d99efd22cc6d950a8116b7` in
[wildcat-protocol](https://github.com/wildcat-finance/wildcat-protocol/tree/da74452aa7d1a0f024d99efd22cc6d950a8116b7)
and V2 commit `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` in
[v2-protocol](https://github.com/wildcat-finance/v2-protocol/tree/a70f297fbd1b1ab597e0e9a3458a2d13a34b4657).
Alexandria checks each registry against its pinned digest; the mapper checks
the source commit of every interpreted market, controller and factory.

V1 joins `WildcatMarketControllerFactory.NewController(borrower,controller)`
to the controller emitting `MarketDeployed`. The controller's `deployMarket`
caller is insufficient: both borrower and factory may call it. The factory
source assigns its temporary borrower from `msg.sender` and emits
`NewController`; the controller source uses those parameters for the market.

V2 joins a factory `MarketDeployed` log to one successful recorded
`deployMarket` or `deployMarketAndHooks` call in the same transaction and block
hash whose returned market equals the event's market. `HooksFactory._deployMarket`
sets the borrower from that call's `msg.sender`. The caller remains a derived
binding, with the complete call and its selector retained. Multiple candidate
calls are refused. Failed calls and calls with a recorded failed ancestor do
not supply bindings. Filtered traces may omit ancestors; this is a bounded
interpretation of recorded call and log agreement, not a complete execution
proof. A missing binding remains unsupported and cannot be replaced by a
repayment sender.

## Resolve the evidence

Each source reference names the release, capture, component digest and
`/records/N/response` journal selector. That member holds a JSON string.
Hash its UTF-8 bytes against `response_sha256`, parse it, then resolve
`/result/M`. A single JSON Pointer through the outer journal cannot address
the nested string. Borrower bindings retain their own reference and the
deployment reference. Probitas carries these references as flat evidence
values and cites the release and event selectors as a document reference.

All original capture coverage remains in `raw_capture_coverage`. Mapping
coverage is independently `partial`; successful decoding does not upgrade a
raw capture. Selected and unattributed markets are listed explicitly. Probitas
reports one archive coverage row with both release identities and their
separate intervals. Zero attributed records still mean a checked partial
selection, never a complete clean history. Original producer gaps remain
visible alongside semantic gaps.

Inputs are limited to 512 MiB across components and 500,000 records per journal
class. Alexandria also enforces its component and JSON limits. Views are
limited to 128 MiB. Readers refuse changed digests, symlink paths, unsupported
registries, duplicate log identities, ambiguous bindings and malformed event
ABI. Loaded sibling APIs must resolve inside the installed sibling plugin.

## Validation

Public tests construct provider responses, build real Alexandria releases,
and run the same verification path as the preserved archives. They compare
supported consumer values for both generations, preserve third-party payers,
exercise missing and ambiguous bindings, and check changed bytes, ABI bounds,
offline operation and all five dossier gates. Private archive bytes are not
included in the tests or this document.

On 24 September 2026, local builds and byte-for-byte rebuilds
passed for both preserved interval releases:

| Measure | V1 | V2 |
| --- | ---: | ---: |
| First block | 18743513 | 21866550 |
| Last block | 22074622 | 26022093 |
| Deployment terms | 7 | 80 |
| Borrows | 60 | 962 |
| Repayments | 72 | 925 |
| Closures | 5 | 30 |
| Borrower bindings | 7 of 7 markets | 80 of 80 markets |

The input release identities were
`sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`
and `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`.
The respective view digests were
`sha256:07d49764c2f0d79094f4d4e4b2406a36020f297c3660cab4b2a3860d5964f2cd`
and `sha256:158dabc0ed1afdbfdf014acf86fd15ca88918b09ac317391cf6101bca6311886`.
One representative borrower dossier per release passed all five Probitas
gates. This checks the consumer path for those two selections; it does not
establish complete historical credit coverage for every borrower.
