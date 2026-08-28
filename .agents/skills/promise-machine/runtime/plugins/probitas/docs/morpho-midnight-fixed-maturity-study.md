# Study: fail-closed Morpho Midnight fixed-maturity coverage

Status: ready for runbook derivation under the assumptions below.

Assuming, unless corrected:

1. Issue [#390](https://github.com/wildcat-finance/skills/issues/390) is the whole product boundary: add Morpho Midnight evidence to a Probitas dossier so a reader can tell whether a fixed-maturity borrowing obligation was cleared by its due time. The broader cross-skill Morpho research target in [#655](https://github.com/wildcat-finance/skills/issues/655) is outside this run.
2. “Timely” means that, after applying every debt-unit increase and decrease whose API `created_at` is less than or equal to the market's immutable `maturity`, no debt units remain. The equality is intentional: the pinned contract permits debt increases while `block.timestamp <= maturity` and enters post-maturity liquidation mode only when `block.timestamp > maturity`.
3. Timeliness and settlement conduct are separate. A primary repay, a secondary close and a liquidation can each reduce debt, but the dossier must not call a liquidation voluntary repayment. The outcome therefore carries both obligation state at maturity and settlement mode.
4. The public Morpho Midnight v0 API on Base chain id 8453 is the prototype's source boundary. Exhausting that API's cursors establishes coverage of the API history returned at the observation boundary; it does not establish independent, archive-chain completeness.
5. The v0 API is explicitly evolving. Tests may pin observed response specimens, but a live response shape is never promoted to a contract merely because it answered once. Harmless extra fields are accepted; missing, malformed or semantically unknown required fields are refused.
6. This is one capability, not a decomposed programme: a dedicated Probitas adapter, its dossier rendering and its verification fixtures ship together. Alexandria, Tabularium, Lazarus, Berean and the other Morpho products remain separate boundaries.
7. The build keeps the existing evidence schema, stdlib-only Python approach and adapter protocol unless implementation proves that one cannot meet the criterion. A dependency, evidence-schema change, CI change or widened trust boundary is ask-first.
8. Repository commands use the exact Python 3.13.15 interpreter pinned by `.python-version`, presently `/Users/c0rtexzer0/.local/share/uv/python/cpython-3.13.15-macos-aarch64-none/bin/python3.13`; the ambient `python3` is 3.14.6 and is not a substitute.

Known unknowns retained rather than guessed:

- The API documentation does not publish an indexing start block, a chain-completeness guarantee or an availability SLA. Coverage prose must name that lower-bound limitation.
- The current transaction reference names `exit_borrow_secondary` but does not provide a concrete response example that independently establishes the account-attributed debt-unit field for that variant. The adapter must obtain a source-bound specimen or documented schema before translating it; absence or ambiguity is an error, not an inferred mapping.
- The position-list reference says closed positions are excluded. A live closed position detail returned zero debt, but the reference does not promise that behavior for every historical closed position. A non-200 or materially different detail response for a market with borrowing events remains an error until first-party evidence establishes another treatment.
- The transaction API orders by second-resolution `created_at` and calls the order deterministic, but the reviewed pages do not expose an intra-second execution index. The selected calculation groups equal-second deltas before checking for underflow; the final balance at a maturity second is independent of order inside that group.

## 1. Problem statement

Build a keyless, Base-only Morpho Midnight adapter inside Probitas for lenders and reviewers preparing a sourced counterparty dossier. A working prototype must turn the v0 user transaction history, immutable market maturity and current position state into cited borrowing events and an explicit per-market maturity outcome without allowing an incomplete or changed response to read as clean.

The request is restated as these testable conditions:

- `morpho-midnight` moves from `unimplemented` to an adapter registered by the existing CLI, while Morpho Blue, MetaMorpho and Vaults V2 keep their distinct identities and current scopes.
- For every subject address, the adapter exhausts the Base transaction cursor, validates the exact known economic-event vocabulary, discovers every market carrying borrowing-side activity, and reads that market's immutable configuration and loan-token metadata.
- For each borrowed market, exact integer debt units are reconstructed through the immutable maturity second. A zero balance is `cleared_by_maturity`; a positive balance is `outstanding_at_maturity`; an unmatured market is `not_due`. A post-maturity clearing event may add `settled_late`, but it never changes the earlier maturity verdict.
- Primary repayment, secondary close and liquidation remain distinguishable. A market cleared through liquidation is not rendered as voluntary repayment, and a pending maturity is not rendered as either timely or late.
- Unknown event variants, missing semantic fields, floats, invalid identifiers, wrong chain or subject attribution, repeated cursors, page/response ceilings, negative unit balances, impossible post-maturity debt increases, or disagreement between reconstructed final debt and a returned current position produce Morpho Midnight coverage `error` and a named gap. They never produce `empty`, `checked` or a timely claim.
- Every event record cites its transaction hash. A derived maturity record cites the transaction that determines the state and names the count of separately cited contributing records; the coverage row records cursor exhaustion and the observation/index boundary. Review must reject any derived sentence that cannot be reproduced from those records and the cited immutable market configuration.
- A fixture with debt cleared before maturity, a fixture with residual debt at maturity later liquidated to zero, a not-yet-due fixture, an empty fixture and hostile-shape mutations all pass their intended assertions. The late fixture must prove that a current debt of zero does not erase lateness at maturity.
- The shipped demo is regenerated, includes Morpho Midnight as checked rather than a gap, renders the maturity outcome in plain language, and passes all five Probitas gates.

The primary check is:

```bash
/Users/c0rtexzer0/.local/share/uv/python/cpython-3.13.15-macos-aarch64-none/bin/python3.13 -m unittest discover -s plugins/probitas/tests -t plugins/probitas
```

The repository-level marketplace-prose and integration check is:

```bash
/Users/c0rtexzer0/.local/share/uv/python/cpython-3.13.15-macos-aarch64-none/bin/python3.13 -m unittest discover -s tests
```

The controller packet and current held-job wording establish these criteria, so no literal clarification is required before the runbook is derived. If an implementation specimen disproves an assumption above, append a Protasis amendment before changing the code.

## 2. Prior art

### What already ships

- `plugins/probitas/scripts/probitas_lib/registry.py` registers fifteen venues. Morpho Midnight is presently unimplemented, keyless, Base-only and separate from Morpho Blue, MetaMorpho and Vaults V2.
- `plugins/probitas/scripts/probitas_lib/endpoints.py` already names `https://api.morpho.org/v0/midnight`, but no adapter uses it.
- `plugins/probitas/scripts/probitas.py` registers Wildcat, Morpho Blue, Euler v1 and Euler v2 adapters. `plugins/probitas/scripts/probitas_lib/adapters/__init__.py` converts any adapter exception into visible coverage `error`, preserving the rest of the dossier and adding a gap instead of silently dropping the venue.
- `plugins/probitas/scripts/probitas_lib/adapters/morpho.py` is the closest fail-closed precedent: exact integers only, explicit known-ignore event vocabulary, subject and market validation, a page ceiling, separate loan/collateral scales and unknown event types that raise. Its GraphQL model and Ethereum-mainnet semantics must not be reused as though they describe Midnight.
- `plugins/probitas/scripts/probitas_lib/evidence.py` supplies one source per record, scalar values only, exact integer wire values, bounded source/value lengths, distinct provenance tiers and a key-name accident guard against personal data. `plugins/probitas/scripts/probitas_lib/render.py` renders known claims explicitly and otherwise falls back to sorted values; a maturity verdict needs an explicit renderer path so it cannot become opaque key/value prose.
- `plugins/probitas/docs/adding-a-venue.md`, `plugins/probitas/tests/test_registry.py`, `test_cli.py`, `test_docs.py`, `test_demo.py`, `test_render.py`, and the adapter test modules establish the venue-addition path. Every aggregate fixture directory must acquire a `morpho-midnight.json`; the committed example dossier and the documented built/gap counts must be regenerated rather than hand-edited.
- `tests/test_marketplace_prose.py` defines the mutable first-party prose surface. Audit records and the three upstream Pashov skill roots are historical/third-party and immutable; all other shipped marketplace-context blocks are cold-read. Only Probitas's exact completed frontier may advance in this run. Other skills' current jobs remain unchanged.

### Merged work and unfinished-work carryover

The last two merged pull requests that changed the subject surface were read in full:

- [PR #65](https://github.com/wildcat-finance/skills/pull/65) added Euler coverage. It is the transaction-history precedent: exact integers, visible adapter failures, complete fixture integration and a regenerated dossier. Its body leaves no unfinished Midnight implementation item.
- [PR #66](https://github.com/wildcat-finance/skills/pull/66) reconciled rolling Fiat frontiers and mutable marketplace prose. It establishes that a run cold-reads all mutable first-party context before finishing and advances only the exact frontier it completed. Its body leaves no additional #390 implementation item.

Two older provenance points were also read:

- [PR #28](https://github.com/wildcat-finance/skills/pull/28) introduced Probitas and the Morpho Blue adapter, with the explicit distinction between liquidation and borrower conduct.
- [PR #80](https://github.com/wildcat-finance/skills/pull/80) introduced the evolution ledgers and adopted the Probitas Midnight held job unchanged. `plugins/probitas/skills/probitas/EVOLUTION.md` now records `probitas-v0.1.0`, open frontier revision `morpho-midnight-coverage`.

No reviewed PR body contains unfinished work that widens #390. Issue #655 remains a separately owned observation, not carryover into this run.

### Audit record carried forward

The whole-set synopsis check exited zero before the Probitas synopsis was used. The read view was `plugins/probitas/audit/AUDIT_SYNOPSIS.md`, covering `plugins/probitas/audit/AUDIT.md` at source SHA-256 `ba532815ae3abe13be3494b96044bf5d874cfb23842249d8e1cd867186e486c9`; the synopsis file SHA-256 was `5eab3774f4d66147e8a4fc18a1014b181f7b1f2309003a93a1dfffb0ff4891a1`.

Every finding and status in that view is retained here:

- `S1-R1-01` and `S1-R1-02`: fixed in `3d1b0f1`; `S1-R1-03`: accepted. `S1-R2-01` and `S1-R2-02`: fixed in `3ef025f`.
- `S2-R1-01` through `S2-R1-05`: fixed in `c316dc2`; `S2-R2-01` and `S2-R2-02`: fixed in `4c377b1`; `S2-R3-01` and `S2-R3-02`: fixed in `7038d88`.
- `S3-R1-01` through `S3-R1-04`: fixed in `c90d13c`; `S3-R2-01` through `S3-R2-03`: fixed in `f04e478`; `S3-R3-01`: fixed in `be54fdd`.
- `S4-R1-01` through `S4-R1-05`: fixed in `61a8444`; `S4-R2-01` and `S4-R2-02`: fixed in `498ae55`; `S4-R4-01`: fixed in `2bc32fc`.
- `S5-R1-01` through `S5-R1-03`: fixed in `9d961da`; `S5-R2-01`: fixed in `02eca61`.
- `VR-01`, `VR-02` and `VR-03`: fixed.
- `PP-01` through `PP-04`: fixed; `PP-05`: superseded, with both stale plan documents deleted.
- `RM-01` through `RM-04`: fixed. `DS-01` through `DS-03`: fixed. `PE-01`: fixed.

The synopsis's open or deliberately bounded leads govern this build:

- `S1-R1-03` remains accepted: GitHub Actions use floating major tags. The workflow is read-only, carries no secrets and publishes nothing; digest pinning belongs to later public-marketplace hardening, not #390.
- The personal-data guard remains a key-name accident guard, not a defence against a malicious first-party adapter. The new adapter remains first-party and must not introduce person-identifying value keys.
- A Wildcat expired withdrawal batch without an indexed expiry event remains cited to the market-creation transaction; that source identifies the market, not the expiry event. Midnight must not copy that exception to justify an uncited maturity outcome.
- Gate 3 still does not parse figures written in words, and a bare URL is sieved for figures but not matched to record sources. The renderer must keep machine-derived Midnight quantities in sourced records rather than prose workarounds.
- `S5-R1-01` is the direct guard precedent: an unknown Morpho transaction type must raise. `S5-R1-02` keeps each asset's decimal scale distinct. `S5-R1-03` requires the coverage row to say Base only rather than implying all Morpho chains.
- MetaMorpho, Vaults V2 and Midnight were deliberately registered as separate unimplemented surfaces so a checked Morpho Blue row could not imply protocol-wide coverage. This run closes only the Midnight gap.

Every one of the synopsis's 24 legacy sections carries `[missing legacy field: audit-schema]`, `[missing legacy field: covered]`, `[missing legacy field: not-checked]` and `[missing legacy field: elenchus-verdict]`; the after-audit section also lacks `leads-not-pursued`. Those fields remain unknown. They are not inferred from the fixed statuses or the clean synopsis check.

### External and upstream precedent

- Morpho's current market-mechanics page says a debt unit is an obligation to repay one loan token at maturity, distinguishes `exit_borrow_primary` repayment from `exit_borrow_secondary` early secondary closing, and treats maturity as immutable.
- The current v0 transaction reference is a cursor-paginated user-level economic ledger on Base. It distinguishes the account-bearing fields for trades, primary exits/collateral actions and liquidations, and distinguishes account-attributed assets from full-trade fields.
- The current market reference makes the market id globally unique, places immutable configuration under `data`, returns 404 for an unknown id, and sends dynamic state to a separate endpoint.
- Pinned upstream contract source at `morpho-org/midnight@c89663aeff053d480689aa082abbcd9254d9e0e9` confirms the equality boundary and event semantics: debt cannot increase only once `block.timestamp > maturity`; repayment itself is not maturity-restricted; liquidation reports repaid units, borrower and post-maturity mode.

## 3. Constraints and non-goals

**Starting state.** Base ref `main` and worktree `HEAD` both resolve to `7e449ba35e1519d28b33f06225c4c4137b548a23` on branch `fiat/390-add-fail-closed-morpho-midnight-fixed-maturi`. The worktree was clean before this study. The source repository is `https://github.com/wildcat-finance/skills.git`.

**Toolchain.** Python 3.13.15 from `.python-version`, stdlib `unittest`, current Probitas schema 1, no new runtime package. Repository instructions require the plugin suite, the root suite and prose/skill checks covering every changed surface.

**Always.** Run the focused adapter tests and full Probitas suite before a commit; run the root suite after mutable marketplace prose changes; run Imprimatur on every shipped prose file; use the exact pinned interpreter; record a baseline before making any performance claim; preserve fixture determinism and regenerate the example through the CLI.

**Ask first.** Add a dependency; change evidence schema 1, the public CLI, a stored release shape or a public interface; touch CI; widen the endpoint/chain or filesystem trust boundary; change another skill's frontier; rewrite a released digest; or turn #390 into the multi-skill #655 programme.

**Never.** Commit secrets, API keys, RPC credentials or identifying personal data; edit vendored/Pashov or audit-history prose as current copy; follow an API redirect to a new host; silently ignore a new transaction type or missing field; coerce a float into an integer; delete a failing test to make a suite pass; call liquidation repayment; claim on-chain completeness from an API-only observation; or claim a command ran when it did not.

**Non-goals.** This prototype does not implement Morpho Blue changes, MetaMorpho, Vaults V2, another chain, a general Morpho research release, archived RPC capture, chain replay, document chunking, protocol-agent evaluation, credit scoring, identity resolution, a production availability SLA, a stable wrapper for the evolving v0 API, or a performance optimisation. It does not close #655. It does not remediate unrelated accepted audit leads. It does not change the meaning of existing Probitas gates or the distinction between declared, linked and inferred addresses.

## 4. Design options

### Option A: dedicated strict REST adapter with event reconstruction and reconciliation (chosen)

Add `plugins/probitas/scripts/probitas_lib/adapters/morpho_midnight.py` and a small stdlib REST reader scoped to the configured `https://api.morpho.org/v0/midnight` origin. Fetch each subject's unfiltered economic transaction pages so an added event type cannot disappear behind a server-side borrowing filter. Enumerate the complete documented vocabulary: translate borrowing-side events, deliberately ignore named lending/collateral events, and raise on everything else. Fetch immutable market data and token metadata for each market with borrowing-side activity, then fetch current position/state evidence for an independent final-balance check.

For each address/market, group events by `created_at`, apply exact debt-unit deltas and reject a negative group-end balance. Borrow increases units. Primary exit and proven secondary exit decrease account-attributed units. Partial/full liquidation decreases `repaid_units`. Compute the maturity balance from every group at or before maturity and the observation balance from all groups. Reject any debt increase after maturity. Compare the observation balance with current position debt when the position endpoint returns its documented shape; any mismatch is coverage `error`.

Emit each economic event as its own transaction-cited record. Emit one explicit maturity-outcome record only when its values are reproducible from the separately cited event records and immutable market record. Its source is the state-determining transaction, not an invented URL or an uncited assertion. The renderer states both the obligation outcome and whether clearing came from primary repayment, secondary closing, liquidation or a mix. The coverage note says Base, cursor exhausted, API-history lower bound unpublished, observation time and the narrowest returned index boundary.

Trade: this is the smallest construction that fits Probitas and preserves the existing schema, but its completeness claim is deliberately API-scoped rather than an independent on-chain proof. It also makes response specimens and reconciliation tests part of the adapter's maintenance burden.

### Option B: add multi-source derived evidence to schema 2

Change a record from one source to a source set so a maturity verdict can cite immutable market configuration plus every contributing transaction directly.

Trade: provenance is cleaner for a derived aggregate, but the evidence format, renderer, gates, examples and downstream Alexandria translation would all change. That public storage boundary is much wider than #390 and requires separate authority, migration design and sibling review.

### Option C: reconstruct Midnight directly from Base logs or a preserved capture

Decode canonical contract events from an archive endpoint, bind the block range and derive maturity without depending on the evolving off-chain API. Lazarus could preserve the finite RPC evidence and Alexandria/Tabularium could own reusable captured records.

Trade: this offers a stronger chain-completeness claim, but it introduces RPC availability, deployment discovery, ABI/version and cross-skill release boundaries. That is the broader research target #655 preserves, not the smallest Probitas dossier change in #390.

**Choice.** Option A is cheapest to comprehend while meeting #390. Option B remains ask-first if audit concludes a one-source derived record cannot honestly support the rendered outcome. Option C stays a named #655 direction and must not be smuggled into this run.

## 5. Risk register seed

```risk-register
api-schema-drift | evolving v0 JSON at the Morpho Midnight origin | required semantic fields and types are strict while harmless extra fields are accepted and hostile mutations produce coverage error
cursor-incompleteness | the user transaction history across cursor pages | every cursor is exhausted once with repetition and page ceilings and an unfinished walk cannot return checked or empty
unknown-event | the economic transaction vocabulary | every documented type is translated or deliberately ignored and any other type raises before evidence is emitted
subject-misattribution | account-bearing fields in trade exit collateral and liquidation variants | the event-specific account equals the requested subject and account-attributed values are never replaced by full-trade values
maturity-boundary | created_at compared with immutable market maturity | all events at or before maturity are included and fixtures cover equality future maturity and post-maturity settlement
unit-accounting | integer debt units across borrow close repay and liquidation | floats and booleans are refused equal-second deltas are grouped balances never go negative and current debt reconciles
settlement-language | renderer distinction between obligation state and conduct | liquidation or secondary close cannot render as voluntary repayment and later zero debt cannot rewrite an overdue maturity verdict
derived-citation | a maturity outcome assembled from several records | every input event remains transaction-cited the determining source is explicit and the outcome is reproducible without an invented source
source-completeness | the boundary between API history and chain history | coverage names Base cursor exhaustion observation/index bounds and the unpublished lower bound without claiming archive-chain completeness
rest-origin | redirects status content type and URL construction | HTTPS and the configured host are locked redirects are refused statuses are explicit and user input never selects a host
response-bounds | untrusted JSON and long pagination | timeout byte depth page and cursor limits fail visibly without partial Midnight claims
fixture-fidelity | recorded response specimens used by an evolving API adapter | specimens carry source date and route tests mutate required fields and no one-time live shape is called the contract
partial-output | collection failure before the shared evidence writer | the adapter builds in memory and returns error coverage with no partial record set while existing whole-file writing semantics remain unchanged
marketplace-drift | mutable first-party descriptions after the frontier closes | the final step cold-reads every classified mutable context and advances only the completed Probitas frontier
```

The audit loop must cite each id as reviewed or not applicable. The accepted legacy action-tag pin, personal-key accident guard, Wildcat citation exception and gate-3 prose limitations remain visible but do not become new #390 work.

## 6. Glossary seeds

**Morpho Midnight.** Morpho's fixed-rate, fixed-maturity lending product on Base, separate from Morpho Blue and vault products.

**Market id.** The globally unique Midnight market identifier whose immutable configuration includes maturity and token terms.

**Maturity.** The immutable Unix-second due boundary. This study includes events whose `created_at <= maturity` in the due-time balance.

**Debt unit.** An exact integer obligation to repay one loan-token unit at maturity; it is the accounting quantity used for timeliness.

**Account-attributed value.** The amount or units assigned to the requested user, distinct from full-trade buyer/seller totals present in the same response.

**Primary repay.** `exit_borrow_primary`, a repayment that reduces debt units through the primary path.

**Secondary close.** `exit_borrow_secondary`, an early market trade that buys/retire debt units; it is clearing, not a primary repay.

**Liquidation.** Partial or full forced settlement that reduces `repaid_units`; it must remain labelled liquidation even when it clears debt before maturity.

**Cleared by maturity.** A market with prior borrowing and zero debt units after every debt-changing event at or before maturity.

**Outstanding at maturity.** A matured market with a positive debt-unit balance at the due boundary, regardless of whether it later reaches zero.

**Not due.** A market whose maturity is later than the adapter's observation time; no timely/late verdict is yet possible.

**Observation boundary.** The UTC collection time plus the narrowest index/block metadata returned by the checked API routes.

**API-scoped coverage.** Cursor-exhausted v0 history as returned at the observation boundary, with no claim that an unpublished indexing lower bound equals complete chain history.

## 7. Sources

### Governing task and boundary

- [Issue #390: probitas-next, add fail-closed Morpho Midnight fixed-maturity coverage](https://github.com/wildcat-finance/skills/issues/390), read 2026-08-28. Current issue is open with `origin:ai` and `held-job`; the 2026-08-26 review says keep it as the held frontier.
- `plugins/probitas/skills/probitas/EVOLUTION.md` at base `7e449ba35e1519d28b33f06225c4c4137b548a23`: open revision `morpho-midnight-coverage` and exact next-job wording.
- [Issue #655: framework observation on a reproducible Morpho target](https://github.com/wildcat-finance/skills/issues/655), read 2026-08-28. It is the explicit breadth boundary: Blue, MetaMorpho, Vaults V2 and Midnight cannot stand for each other, and its multi-skill research/developer target is not owned by #390.

### Creator-supplied official documentation, preserved exactly

- Literal supplied concepts/guides URL: [https://docs.morpho.org/build/midnight/concepts/market-mechanics/-](https://docs.morpho.org/build/midnight/concepts/market-mechanics/-). An independent `curl` observation on 2026-08-28 returned HTTP 404 for that exact URL. Removing only the terminal `-` path segment gives [https://docs.morpho.org/build/midnight/concepts/market-mechanics/](https://docs.morpho.org/build/midnight/concepts/market-mechanics/), which resolved to the 200 canonical page [https://docs.morpho.org/developers/midnight/concepts/market-mechanics/](https://docs.morpho.org/developers/midnight/concepts/market-mechanics/).
- Literal supplied API-examples URL: [https://docs.morpho.org/tools/offchain/api/morpho-midnight/-](https://docs.morpho.org/tools/offchain/api/morpho-midnight/-). An independent `curl` observation on 2026-08-28 returned HTTP 404 for that exact URL. Removing only the terminal `-` path segment gives [https://docs.morpho.org/tools/offchain/api/morpho-midnight/](https://docs.morpho.org/tools/offchain/api/morpho-midnight/), which resolved to the 200 canonical page [https://docs.morpho.org/developers/api/morpho-midnight/](https://docs.morpho.org/developers/api/morpho-midnight/). The canonical page says v0 routes/responses are evolving, Base 8453 is supported and list routes use cursor pagination.
- Supplied API-reference URL: [https://docs.morpho.org/api/midnight/markets/get-market/](https://docs.morpho.org/api/midnight/markets/get-market/), read 2026-08-28. It establishes global market-id uniqueness, immutable `data`, 404 for an unknown id and a separate dynamic-state endpoint.

### Additional official API references

- [List user transactions](https://docs.morpho.org/api/midnight/transactions/list-user-transactions/): cursor-paginated economic transactions for a user, documented event vocabulary, Base 8453, account attribution, Unix-second `created_at`, deterministic ordering and a null terminal cursor.
- [List positions](https://docs.morpho.org/api/midnight/positions/list-positions/): current positions only; closed positions are excluded, so this route alone cannot establish historical timeliness.
- [Get position](https://docs.morpho.org/api/midnight/positions/get-position/): current per-user/per-market state used only as a reconciliation source under the unknown noted above.
- [Get market state](https://docs.morpho.org/api/midnight/markets/get-market-state/): dynamic market/index state, separate from immutable market data.
- [Get token](https://docs.morpho.org/api/global/get-token/): token metadata and decimals for the loan asset.

### Pinned upstream implementation evidence

- [`morpho-org/midnight` commit `c89663aeff053d480689aa082abbcd9254d9e0e9`](https://github.com/morpho-org/midnight/commit/c89663aeff053d480689aa082abbcd9254d9e0e9), repository head observed 2026-08-28, commit timestamp 2026-08-27T15:01:03Z. Reviewed `src/libraries/EventsLib.sol` and the debt-increase, repay and liquidation paths in `src/Midnight.sol` at that commit.
- [`morpho-org/sdks` commit `b3c29c6aef6bb43c19714a400b30a025fdbb59d7`](https://github.com/morpho-org/sdks/commit/b3c29c6aef6bb43c19714a400b30a025fdbb59d7), head observed 2026-08-28. The SDK warning that API imports may change without ordinary semver reinforces the official v0-evolution statement; it does not define an adapter field.

### Repository and delivery history

- `plugins/probitas/AGENTS.md`; `plugins/probitas/skills/probitas/SKILL.md`; `plugins/probitas/README.md`; `plugins/probitas/skills/probitas/EVOLUTION.md`.
- `plugins/probitas/scripts/probitas.py`; `plugins/probitas/scripts/probitas_lib/{registry.py,endpoints.py,evidence.py,render.py}`; `plugins/probitas/scripts/probitas_lib/adapters/{__init__.py,morpho.py,wildcat.py,euler.py,euler_v1.py}`.
- `plugins/probitas/docs/adding-a-venue.md`; `plugins/probitas/tests/test_{registry,cli,docs,demo,evidence,render,adapter_morpho}.py`; `tests/test_marketplace_prose.py`; current aggregate fixtures and `plugins/probitas/docs/example-dossier.md`.
- [PR #28](https://github.com/wildcat-finance/skills/pull/28), [PR #65](https://github.com/wildcat-finance/skills/pull/65), [PR #66](https://github.com/wildcat-finance/skills/pull/66), and [PR #80](https://github.com/wildcat-finance/skills/pull/80), all read in full on 2026-08-28.
- `plugins/probitas/audit/AUDIT_SYNOPSIS.md`, used only after `/Users/c0rtexzer0/.local/share/uv/python/cpython-3.13.15-macos-aarch64-none/bin/python3.13 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited zero for the complete target set. Source/synopsis digests and every missing legacy field are recorded in item 2.

### Time-bound live observations, not API contracts

Read-only GET observations were made against `https://api.morpho.org/v0/midnight` at `2026-08-28T04:48:07Z`. These values are specimens for study and fixture design; they may drift and do not override the pages above.

- The Base markets list returned 100 entries and a non-null cursor. A sampled response carried an extra `market_family_id` not shown in the reference example, supporting tolerant handling of extra fields rather than exact-object rejection.
- Sample market `0xcc9418ea594c6e658650aedd205ce4544b266b69493f56fd2adc65c14bd06738` used WETH and had immutable maturity `1784300400`.
- For user `0x535690CB1330232dd4f2ac5B724040751bdF4C91`, four borrow events summed to `320136075232067` debt units. An `exit_borrow_primary` at `1784207151`, 93,249 seconds before maturity, removed `320000000000000`, leaving `136075232067` units at maturity.
- Partial liquidations at `1784300485` and `1784300771` and a full liquidation at `1785373313` removed the residual `136075232067` units. The current position detail then reported zero debt and `last_indexed_block` 50551562. This is the concrete guard specimen: current zero does not mean timely.
- The token route returned WETH with 18 decimals and USDC with 6. Those are observations of those token records, not a rule that every Midnight market uses either asset or scale.

## 8. Signals, and the questions behind them

This capability can run unattended as part of `probitas collect`, so four on-call questions apply. The signal ownership contract is `plugins/hexaemeron/skills/ephoros/SKILL.md`; this study only identifies the questions and emitting steps.

1. **Did the adapter finish the history it claims to have checked?** The REST collection step emits venue, Base chain id, subject address, page count, terminal-cursor result, UTC observation time and returned index boundary into the coverage note or error detail.
2. **Why did Midnight refuse coverage?** The validation/reconciliation step emits one bounded error naming the stage (`transactions`, `market`, `token`, `position` or `reconciliation`), event/market identifier when safe, and refusal class such as unknown type, missing field, cursor repeat or balance mismatch. It carries no response body or personal data.
3. **What made the maturity outcome?** The derivation step records market id, maturity, exact debt units at maturity, exact units at observation, settlement mode, contributing-record count and the determining transaction source in evidence; the renderer exposes the plain-language result.
4. **Did the rest of the dossier survive a venue failure honestly?** The shared adapter runner emits Morpho Midnight coverage `error` with zero Midnight records and the CLI adds the named gap. The full Probitas tests assert the venue cannot disappear or become `empty`.

No new logging framework, metrics backend or alert transport is proposed. Existing evidence, coverage and bounded stderr are the observable interface for this prototype.

## 9. Boundaries, per capability

The boundary/control owner is `plugins/hexaemeron/skills/phylax/SKILL.md`; the entries below apply it to this capability without copying that contract.

| Capability | Boundary and useful input | Closing control |
| --- | --- | --- |
| REST request | Fixed public Morpho origin, documented route fragments, validated address/market/token identifiers | HTTPS and exact-host lock, redirects refused, quoted URL construction rather than concatenated arbitrary paths, explicit timeout and status handling |
| JSON decode | Untrusted v0 response bytes | Content/byte/depth/item bounds, mapping/list/type checks, required-field accessors, no coercion of float or bool to integer, extra fields ignored only when semantically irrelevant |
| Cursor walk | Opaque cursor supplied by the server | Cursor treated only as data to the same route, repetition set, null-terminal requirement, page/item ceiling and no checked/empty result before terminal exhaustion |
| Event attribution | User-level economic transactions containing several parties and full-trade fields | Event-specific subject field must equal the requested address; account-attributed units/assets are used; undocumented variants error |
| Market enrichment | Immutable market, dynamic state, position and token routes | Returned ids and chain must match the request, maturity and decimals are exact integers, immutable/dynamic fields are not substituted for each other |
| Unit ledger | Exact external integers and second-resolution timestamps | Per-address/per-market isolation, equal-second grouping, checked non-negative arithmetic, no post-maturity increase, final position reconciliation |
| Fixture input | Operator-selected local fixture directory | Existing fixture-root convention, fixed filename, bounded JSON parser and hostile mutation tests; fixture name is sanitised before coverage output |
| Evidence output | Shared in-memory evidence object and caller-selected output path | Adapter returns no partial record set on failure; `Record`/`Coverage` constructors enforce the existing schema; the shared writer remains the only output path |
| Secrets and dependencies | None required by the keyless endpoint | No credential flag/env lookup, no new package, no response-body logging; any future credential or dependency is ask-first |

The existing whole-file writer can still be interrupted during its final write; changing it to atomic output is cross-adapter work and is not silently added to #390. The Midnight-specific control is that all network collection and derivation complete in memory before the shared writer receives records.

## 10. The budget, or its absence

No performance budget applies: #390 adds evidence correctness, not a speed or resource claim, and live network latency is outside the prototype's control. Therefore there is no Metron measurement command for this study. The timeout, response-byte, page and cursor ceilings are fail-closed safety bounds, not performance targets. If a later change claims faster collection, it must first record a comparable baseline under `plugins/hexaemeron/skills/metron/SKILL.md` and amend this section with the exact command.

## 11. The fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md` owns failure triage and the guard convention. For this capability, a Midnight refusal stops only the claim that Midnight was checked: `run_adapter` returns zero Midnight records, coverage `error` and a named gap so the broader dossier remains usable without reading the failure as clean.

The adapter refuses before a checked/empty result on: non-terminal or repeated pagination; page/byte/time ceiling; non-HTTPS or redirected origin; non-200 or non-JSON required route; unknown event type; absent or malformed required field; invalid chain, address, id, hash, timestamp or integer; unproved secondary-close mapping; negative unit balance; debt increase after maturity; maturity/config conflict; current-position mismatch; or a derived outcome that lacks reproducible cited inputs. An API response with no borrowing-side events is `empty` only after all cursors terminate and every returned non-borrow event belongs to the explicit known-ignore set.

The guard-test convention is: first preserve the smallest failing JSON fixture or mutate one required field in `plugins/probitas/tests/test_adapter_morpho_midnight.py`; prove that focused test fails for the observed reason; make the smallest cause-level fix; rerun that focused test; then run the complete Probitas suite. A schema-drift fix must retain the old hostile specimen if it represents a response still worth refusing. No fix begins from a live-only response that was not reduced to a source-dated fixture.

The exact full guard command is:

```bash
/Users/c0rtexzer0/.local/share/uv/python/cpython-3.13.15-macos-aarch64-none/bin/python3.13 -m unittest discover -s plugins/probitas/tests -t plugins/probitas
```

## 12. Decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` owns which choices earn durable records and where they live. One decision here is expensive enough to record: the due-time semantics and evidence boundary jointly determine every future Midnight verdict. At this base, its intended home is `docs/decisions/ADR-042-derive-midnight-timeliness-from-debt-units.md`. It will record:

- why debt units, not assets or current position alone, determine the maturity balance;
- why `created_at <= maturity` is included and equal-second deltas are grouped;
- why obligation state and settlement mode are separate;
- why the chosen prototype makes an API-scoped completeness claim and keeps on-chain preservation in #655; and
- why schema 1's separately cited event ledger plus determining source was chosen over a multi-source schema migration, including the ask-first escape if audit rejects that evidence model.

Reversible implementation details do not earn separate ADRs. The exact event-field mapping and reasons for ignored variants live beside the constants in `plugins/probitas/scripts/probitas_lib/adapters/morpho_midnight.py`; operator-visible API limits and source limitations live in `plugins/probitas/README.md` and `plugins/probitas/skills/probitas/references/venues.md`; response specimens and refusal behavior live in `plugins/probitas/tests/test_adapter_morpho_midnight.py` and its fixtures.

The completed frontier and its successor are historical state, not a code comment. The final runbook step must record them in `plugins/probitas/skills/probitas/EVOLUTION.md` and reconcile every mutable Probitas marketplace-context block. The successor job is not guessed in this study; it is chosen from evidence current at final reconciliation. No other skill's frontier changes merely because it was cold-read.

### Amendment -- 2026-08-28

**What changed.** Item 12's intended decision home changes from `docs/decisions/ADR-042-derive-midnight-timeliness-from-debt-units.md` to `docs/decisions/ADR-043-derive-midnight-timeliness-from-debt-units.md`. The decision content and every product criterion remain unchanged.

**Why.** Live `origin/main` at `4296f9f0b3eb03926d9b5b03258246dcab8c13ec` now owns ADR-042 as `docs/decisions/ADR-042-advance-the-python-suite-to-3-14.md`; ADR-043 is the smallest unused decision number in that tree.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** The Step 2 event mapping and hostile-input controls are corrected. Wherever the design or glossary says a partial or full liquidation decreases only `repaid_units`, the exact borrower-debt decrease is `repaid_units + bad_debt`, with both fields validated as `uint256`. A source-consistent pure bad-debt realization may therefore carry zero `repaid_units` and positive `bad_debt`; it remains labelled liquidation. `post_maturity_mode: true` is valid only strictly after maturity, but `false` may remain valid after maturity for an unhealthy borrower, so the timestamp and mode are not an equivalence. Known trade-shaped events validate full-trade `total_units_delta` as signed `int256` while account-attributed `data.units`, not that full-trade value, controls the subject's debt ledger.

The JSON and integer boundary now explicitly refuses duplicate object names, `NaN`, positive or negative infinity, non-ASCII integer text, and values outside `uint256` or `int256` before conversion. The same ASCII and pre-conversion size rules cover numeric HTTP metadata such as `Content-Length`. The time budget is checked before and after the response read, after decode and before a successful derived return. Requested subject identity remains in structured normal evidence, but bounded refusal strings do not echo requested or returned addresses, response bodies, fixture paths or malformed raw values. This completes the pinned-source statement, the JSON-decode and unit-ledger boundary rows, and Signals 1 and 2 without changing the API-scoped evidence boundary or due-time definition.

The source inventory also includes the [Python 3.13 JSON standard-compliance notes](https://docs.python.org/3.13/library/json.html#standard-compliance-and-interoperability), read 2026-08-28. They document that the default decoder accepts non-finite number tokens and repeated object names with the last value winning, which is why the adapter must override both behaviours.

**Why.** Warden round 1 compared the prototype with pinned `morpho-org/midnight@c89663aeff053d480689aa082abbcd9254d9e0e9`. `src/Midnight.sol` separately subtracts realized bad debt and repaid units, permits zero-transfer pure bad-debt realization, and makes post-maturity mode a one-way condition; `src/libraries/EventsLib.sol` declares `totalUnitsDelta` as `int256`. The earlier shorthand omitted or over-constrained those semantics. The same audit reduced permissive Python JSON and integer parsing, incomplete deadline checks and address-bearing refusal text to guarded causes. The product goal, maturity equality, chain, API source and settlement-language boundary do not change.

**Steps touched.** Step 2.

**Still holding.** Step 2: entry holds; exit broken. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-08-28

**What changed.** Item 12's intended decision home changes from `docs/decisions/ADR-043-derive-midnight-timeliness-from-debt-units.md` to `docs/decisions/ADR-045-derive-midnight-timeliness-from-debt-units.md`. The decision content and every product criterion remain unchanged.

**Why.** Live `origin/main` at `3b86d60b1aa55648f12d109e0422db8037f0df7a` now owns ADR-043 as `docs/decisions/ADR-043-record-corpus-provenance-beside-the-chunks.md` and ADR-044 as `docs/decisions/ADR-044-bind-sync-run-generator-aggregates.md`, so this run's number moved again. ADR-045 is the smallest unused decision number in that tree. The unused numbers ADR-026 and ADR-027 were considered and refused, because `docs/decisions/ADR-031-fence-external-fiat-transitions-on-signed-checkpoint-acceptance.md` and `docs/decisions/ADR-032-model-checkpoint-lineage-as-an-explicitly-resolved-dag.md` still record those two as their own former identifiers, and reusing either would point an existing provenance line at a different record.

**Steps touched.** Step 4.

**Still holding.** Step 4: entry holds; exit holds.
