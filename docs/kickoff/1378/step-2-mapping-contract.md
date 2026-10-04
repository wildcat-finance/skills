# Fiat 1378 Step 2 mapping contract

Step 2 adds Wildcat V1/V2 native-log mappings under canonical and coverage schema 3. The selected design remains `role-qualified`; its decision digest is `80282666266db259f1afb600ee981f28928fde0b077cf333967501672a04bb50`. Step 1's historical specification, selection reports and registered reporter bytes stay fixed.

## Dispatch and meaning

Generation, registered emitter role and concrete ABI variant must agree before a topic is decoded. The 17 primary contexts comprise 7 market actions per generation and 3 V2 wrapper actions. [The mapping inventory](step-2-mappings.json) records their exact signatures, roles, units and mapping-rule identifiers. The 17 concrete source variants retain 156 event associations from normalized historical ABI inspection; they establish no fresh compiler run or runtime-code agreement.

Borrow names the pool because its log has no borrower. DebtRepaid records its observed payer and pool; inferred debtor context remains separate. WithdrawalExecuted records its beneficiary, with executor and cash recipient gaps. A sanctions companion can add an escrow recipient only through a unique same-market, transaction, account, expiry and amount join. It supports the one withdrawal row and contributes no second cash amount.

Market Transfer amounts are market-token claims. Wrapper assets are market tokens and wrapper shares are a separate unit. Queue records hold normalized and scaled claims. MarketClosed has no financial amounts; its timestamp is state. These rows establish neither settlement nor underlying-asset look-through.

## Source classes and dispositions

Each native log receives exactly one disposition: `primary`, `supporting-routing`, `unsupported-canonical-meaning` or `unsupported-decode`. Known malformed ABI data refuses the release. A decoded administration or lifecycle event retains its concrete declaration but has no admitted canonical meaning. Attribution gaps remain separate from omitted-event counts.

The journal reference binds component digest, capture ID, evidence class, journal-response selector and digest, and result selector. Context references bind the complete classified source record. Registry, positional epoch, deployment asset, constructor and inferred debtor context keep separate classes. A borrower inference cannot become a payer, beneficiary or sender.

Constructed positives use a verified generic Alexandria raw release with the explicit `constructed-fixture` source label and preserved limitations. Both captures must declare `subject-scoped` coverage for exactly the context emitter addresses; the request filter binds the same set. Their declared context establishes neither historical origin, interval epochs nor runtime code. It adds no entry to either retained interval registry.

## Complete offline reconstruction

`wildcat-canonical` verifies the raw release before copying every raw file into `source/raw-release`. It writes a fresh complete directory after semantic verification, using native atomic publication that refuses an occupied output. Linked, aliased, non-regular, over-budget or inconsistent inputs refuse the build. Staging and cleanup bind the output-parent and stage identities.

`verify` rechecks the copied Alexandria release and rebuilds source context, decoded records, sanctions joins, canonical rows, qualified counts, gaps and all output bytes. Rehashed unsupported changes to a descriptor, capture, ledger or coverage still refuse. The verifier needs no original capture path or network access.

The due design resolvers execute `SemanticConformanceTests` and `SchemaParityTests` through the unchanged registered entrypoint. Schema parity requires the locked jsonschema distributions; an unavailable oracle refuses the proof. JSON Schema accepts integral floats as integers; Python separately rejects float metadata at its strict input boundary.

## Retained-input limits

The V1 capture contains 1,941 logs; V2 contains 74,088. V2 retains 14 wrapper-factory bindings and 172 market-token transfers with wrapper counterparties, with zero wrapper instance registry entries, epochs or native journal coverage. Neither capture contains a sanctions-routing companion.

Seven recorded V1 constructor returns join to market creation and deployment but contain no decimals field. Eighty recorded V2 returns contain constructor decimals 6, 8, 9 or 18. Those values remain recorded constructor context. The 14 V2 `decimals()` calls target market tokens and supply no blanket underlying-token metadata proof.

Schema 2 bytes, old adapter/mapping tuples and all six Aave/Euler release trees remain fixed. The Tabularium generation becomes 0.5.0 and its package becomes 0.5.1; the Compound Phase 1 frontier, revision, history and evolution counter retain their prior values. Historical accounting replay and function reconciliation remain with [#1386](https://github.com/wildcat-finance/skills/issues/1386) and [#1387](https://github.com/wildcat-finance/skills/issues/1387).
