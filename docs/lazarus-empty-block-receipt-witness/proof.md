# Empty-block receipt witness delivery proof

## Result

Fiat issue 1360, Step 3, closes the `empty-block-receipt-witnesses` frontier.
Plan v3 and receipt-witness/v1 keep the existing scoped shape and add one
exclusive empty shape. The verifier accepts that shape only when the verified
header carries Ethereum's empty trie root. It derives zero receipts and zero
`receipt_trie_proved` relations. Missing receipt evidence remains different
from verified emptiness.

The implementation began at signed parent
`8cbfd5f666001fdb5fef4280a3126769ce4385e3` on
`fiat/1360-empty-block-receipt-witness-step-2-carry-verified-emptiness-through`.
The Step 3 packet state is
`7dc5603ec3a7bec592c1056c469181f368fb34209b84203fedbf3bb2b02e404a`.
This worker performed no capture, controller receipt, push, pull request,
merge, issue comment, or issue closure.

## Offline demonstration

Run from the repository root:

```bash
python3 plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1/demo.py
```

The checked-in Ethereum genesis fixture verifies with both socket connection
entry points patched to refuse use. Its one canonical JSON event reports
`network=denied`, block `0x0`, the genesis block hash, empty witness mode, zero
receipts, zero proved relations, and the canonical empty trie root
`0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421`.

| Identity | SHA-256 |
| --- | --- |
| Fixture | `da15f6d08676c826d36564e59c5ebc2e9388d7dc5bd5f8f3e5a6d31e376bd044` |
| Manifest file | `924a75fb58bb5f2045d725c28e4889886bb486b4f646cac809615888e4300fcb` |
| State-fixture/v2 statement | `a01d28bc205896bc1073f9ce443e3eb5886bb13dca65a23ee561f226ec257bd9` |
| Release-v2 | `ada99a120f0f7f1cc3900319a4fc7d948153ffe24f7c7ebbecc64a3e3fe0b650` |

Five hostile copies change fixture or release bytes and are rejected:

| Mutation | Guarded boundary |
| --- | --- |
| Non-empty root | An empty witness requires Ethereum's empty trie root. |
| Mixed shape | Empty and scoped fields cannot coexist. |
| Count inflation | Recomputed zero cannot become one by manifest assertion. |
| Component digest | Changed component bytes fail their manifest binding. |
| Release count | Release-v2 cannot change the verified zero count. |

## Existing-format compatibility

The unchanged Aave v4 demonstration remains network-denied and green:

```bash
python3 plugins/lazarus/examples/aave-v4-spoke-v1/demo.py
```

It retains 177 ordered receipts, target index `0x3f`, four target logs, the
two-log projection, and two proved relations. Its receipt, index, log, root,
count, and release mutations are rejected. Historical fixture bytes remain
fixed at these digests:

| Historical identity | SHA-256 |
| --- | --- |
| Fixture | `986287699f6e327be412b1503b7dfacec34faeff77b3bbb763215f274dc6f59f` |
| Manifest file | `1be58bdeb2312b24ab7958fcdd7a5304a902d81ec7b6491d9cc5d7a0efff8bb3` |
| Statement file | `cb5cfae539f91d814dcee0ddddf13f4fb60a03f2b17c1b7581f330a8353438ef` |
| Release file | `de4eb122aa84c589bdd0c7370f43e01845d4b733bcf61599f6b9893d41c5be4e` |

## Guards and governed state

The two new demonstration tests fail at the Step 2 parent because the demo is
absent. They pass with this implementation. The full Lazarus resolver runs
650 tests and is recorded in
`.hexaemeron/reports/conformance/shape-discriminated-existing-formats-stay-green.json`.

The owned source refresh completed with 92 rows across 32 chains and repaired
no ledgers. The Lazarus skill advances exactly once from `lazarus-v2.2.0` to
`lazarus-v3.2.0`. Its frontier row digest is
`28eda7875d079d615279db2f8f39d72b78aa5746ba9d92b3da6bb3a3f65a4df6`.
No evidenced material follow-on remains, so the ledger records
`None -- mature`. The installable Lazarus plugin advances independently from
1.1.2 to 1.1.3.

## Evidence boundary

The empty witness proves that the verified header commits to the empty receipt
trie and therefore to no receipt relation. It does not prove canonical-chain
membership, provider independence, transaction-hash attribution, calls,
traces, or unrelated RPC fields. Those fields remain recorded evidence where
present. Zero relations are a verified result, not positive evidence about a
transaction or log.
