# Wildcat subgraph retirement inventory

This record lists every caller, chain and field of the Probitas Wildcat
subgraph route that [#1896](https://github.com/wildcat-finance/skills/issues/1896)
retires, and what replaces each one. It was read from `main` at
`182bf2c8de5ebf0573e9bfaf13c9af30542fbd6c` on 2026-09-28, and every line
reference is to that commit. It removes nothing and restores no field. #1896
stays open until #1924, #1925 and #1926 are accepted and the open items at the
end are settled.

## Callers

| Surface | Location | At retirement |
| --- | --- | --- |
| CLI adapter table | `plugins/probitas/scripts/probitas.py:44-50`, `"wildcat": wildcat.adapter` at `:49` | Remove the entry. |
| Route selection | `probitas.py:69-84` (`routes_for`) and `:100-112` (adapter loop) | The adapter runs under `--live`, under `--fixtures`, or whenever no archive input is given. `:102` skips it only when `--wildcat-release` is present. Afterwards a Wildcat answer comes from `--wildcat-release` alone. |
| Venue registry | `plugins/probitas/scripts/probitas_lib/registry.py:38-47` | Keep the venue. Drop "or the public Goldsky subgraph" from the note at `:44`. |
| Adapter | `plugins/probitas/scripts/probitas_lib/adapters/wildcat.py`, 482 lines | Remove. Its `seconds_delinquent` helper (`:428-431`) is read only by its own suite. |
| Endpoints | `plugins/probitas/scripts/probitas_lib/endpoints.py:11-32` | Remove `WILDCAT_DEPLOYMENTS` and `DEFAULT_WILDCAT_NETWORK`. Only the adapter and its suite read them. |
| GraphQL client | `plugins/probitas/scripts/probitas_lib/graphql.py` | Keep. `adapters/morpho.py:25` also imports `post`. |

No module outside Probitas imports a Probitas adapter.
`plugins/alexandria/tests/test_index.py:470-509` runs `collect --fixtures` over
Probitas's `empty` fixture and asserts at `:487` that Wildcat coverage came
from `fixtures`, so it changes with the route.

## Chains

- `mainnet` (Ethereum), the default: Goldsky `subgraphs/mainnet/v2.0.26/gn`,
  reached by `--live` or by any `collect` without an archive input. The V1 and
  V2 archive releases replace it, through `--wildcat-release`.
- `plasma-mainnet`: Goldsky `subgraphs/plasma-mainnet/v2.0.22/gn`, reached only
  by a direct `adapter()` call with `config["wildcat_network"]`. The CLI config
  at `probitas.py:100` sets no such key, and only `test_adapter_wildcat.py:369`
  passes one. Nothing replaces it.

The archive route covers Ethereum only, so retiring the subgraph route ends
Plasma coverage. #1896's comment of 2026-09-26 requires a separate maintainer
decision for any reduced retirement scope. laurenceday made it on 2026-09-28:
Plasma is retired with no replacement
([decision](https://github.com/wildcat-finance/skills/issues/1896#issuecomment-5878881470)).

## Fields

The old side is what `adapters/wildcat.py:244-413` emits. The archive side is
`plugins/tabularium/scripts/tabularium_lib/wildcat_view.py`, whose unsupported
table is at `:45-72`, as `plugins/probitas/scripts/probitas_lib/wildcat_archive.py`
loads it.

| Claim | Fields | Archive route today | Replacement owner |
| --- | --- | --- | --- |
| Every record | `observed_at`, the block timestamp | `None` on every record (`wildcat_archive.py:95`); the dossier prints `--` (`render.py:428`) | [#1997](https://github.com/wildcat-finance/skills/issues/1997) |
| `market_terms` | `market`, `market_name`, `reserve_ratio_bips`, `annual_interest_bips`, `grace_period_seconds`, `delinquency_fee_bips` | Supplied as deployment terms, with `terms_at: deployment` | #1895, closed |
| `market_terms` | `token_symbol`, `token_decimals` | Unsupported (`:50-51`) | #1924 |
| `market_standing` | `is_closed`, `is_delinquent_now`, `incurring_penalties_now`, `total_borrowed`, `total_repaid`, `penalty_interest_accrued` | Unsupported (`:55-59`) | #1924 |
| `market_closed` | `market` | Supplied from `MarketClosed` | #1895, closed |
| `borrow` and `repayment` | `market`, `amount` | Supplied from native logs | #1895, closed |
| `delinquency_entered` | `market`, `liquidity_required`, `assets_held` | No record emitted; fields unsupported (`:60-63`) | #1925 |
| `delinquency_cured` | `market`, `liquidity_required`, `assets_held`, `seconds_delinquent`, `past_grace_period` | No record emitted; fields unsupported (`:64-67`) | #1925 |
| `withdrawal_batch_expired_unpaid` | `market`, `expiry`, `requested`, `paid` | No record emitted; fields unsupported (`:68-71`) | #1926, using [withdrawal-definitions.md](withdrawal-definitions.md) |

The view also lists `current_annual_interest_bips` and
`current_reserve_ratio_bips` as unsupported (`:52-53`). The old route never
emitted them; #1924 binds the current rates where a consumer claim uses them.

Two old-route readings should not carry forward. `market_standing` is cited to
the deployment transaction (`wildcat.py:288-306`), not to its observation. And
`annual_interest_bips` reads the subgraph's `annualInterestBips` while the
reserve ratio reads `originalReserveRatioBips` (`:279-280`). Whether that
subgraph field holds the current or the original rate was not checked.

## Tests and fixtures

| Item | Location | At retirement |
| --- | --- | --- |
| Adapter suite, 40 tests | `plugins/probitas/tests/test_adapter_wildcat.py` | Remove. |
| Subgraph fixtures with markets | `plugins/probitas/tests/fixtures/{clean,cured,defaulted,demo}/wildcat.json` | Remove, or replace with constructed archive releases. |
| Subgraph fixtures with no market | `fixtures/{empty,morpho-bad-debt,morpho-clean,morpho-empty,morpho-liquidated}/wildcat.json` | Remove. |
| Gate evidence builder | `test_gates.py:25-37` builds every gate case from this adapter over those fixtures | Move to the archive route. |
| Load-path equivalence | `test_statement.py:163` selects cases by `wildcat.json` | Re-anchor. |
| Documentation anchors | `test_docs.py:49` (`AGGREGATE_FIXTURE_ANCHORS`) and `:185` (the demo directory listing) | Update. |
| Route comparison | `test_wildcat_archive.py:18` and `:90-110` import `wildcat._market_records` as the comparison source | Remove the comparison. |
| Example dossier check | `test_demo.py:20` and `:124` hold `docs/example-dossier.md` to the demo path | Regenerate. |
| Aggregate-route suites | `test_cli.py`, `test_demo.py`, `test_render.py`, `test_union.py`, `test_evidence.py`, `test_registry.py`, with 8, 2, 15, 3, 11 and 11 `wildcat` mentions | Each drives `--fixtures` and so runs this adapter; not yet read line by line. |
| Alexandria | `plugins/alexandria/tests/test_index.py:487` | Update. |
| GraphQL client suite | `test_graphql.py` | Keep. |

## Documents

Update these, which describe the subgraph as a live Wildcat route:

- `plugins/probitas/README.md:122` and `:296`;
- `plugins/probitas/AGENTS.md:73-75`;
- `plugins/probitas/skills/probitas/SKILL.md:148` and `references/venues.md:22`;
- `plugins/probitas/docs/adding-a-venue.md:54`;
- `plugins/probitas/docs/example-dossier.md`, Wildcat rows at `:44` and `:74-86`, regenerated from the demo path;
- the `"subgraph"` keyword in `plugins/probitas/.claude-plugin/plugin.json:19` and `.codex-plugin/plugin.json:17`, unless another route still earns it; and
- `plugins/tabularium/docs/wildcat-archive.md:6` and `:12`.

Keep these as history, since they describe superseded work rather than an
active route:

- the `plugins/probitas/audit/AUDIT.md` and `AUDIT_SYNOPSIS.md` rows naming `adapters/wildcat.py`;
- `docs/kickoff/1368/observedpolicy.json:476`, which names `tests/fixtures/demo/wildcat.json`; no test reads that record; and
- `plugins/tabularium/skills/tabularium/SKILL.md:257`, whose "subgraph substitution" refusal stays true.

## Open before retirement

1. #1924, #1925 and #1926 must restore the fields assigned to them above.
2. [#1997](https://github.com/wildcat-finance/skills/issues/1997) must bind `observed_at` on every archive record.
