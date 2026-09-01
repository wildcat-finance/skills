# Ariadne evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `ariadne-v3.2.0`
- Frontier status: `mature`
- Frontier revision: `grounded-agent-predicate`
- Current frontier: The grounded-agent predicate now ships as the fifth registered Ariadne predicate, with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path that binds an existing `berean-release/v1` tree without importing or running Berean, executing an agent, regrading evaluations or reaching a network.
- Next Fiat job: None -- mature
- Sources: [../../../../SOURCES.md](../../../../SOURCES.md)

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `ariadne-v0.1.0` | baseline | `dataset-predicate` | `0c0310a503de564b892e7206d6b8e88ec3acd4ad99a62d02f3f83cd16991bc20` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `ariadne-v1.1.0` | evolution | `state-fixture-predicate` | `ec925d3f57001ac32eb6d40ffdd7d43f130e360283ef40eb8fbbda724f262c2f` | [skills#200](https://github.com/wildcat-finance/skills/pull/200) | Closes the dataset-predicate frontier. The type is registered with its own gates 2 and 5, a coverage check that refuses an interval with no gaps block, an inputs check that refuses a locator on its own, a published schema held to the module by a drift test, nine conformance fixtures, and a capture path that refuses a release it cannot read whole. Eight audit rounds fixed 23 findings; three are recorded open and out of scope. |
| `ariadne-v2.1.0` | evolution | `grounded-agent-predicate` | `4ac9d0c052326b31082c98eed877ffe0a8abb4aa5a269c2ffadebfb681c8089e` | [skills#218](https://github.com/wildcat-finance/skills/pull/218) | Closes the state-fixture-predicate frontier. The type is registered with its own gates 2 and 5, an evidence check that refuses a proof-backed count with no state root to have proved it against, a replay check that refuses a boundary reaching a network or a claim about the canonical chain, a published schema held to the module by a drift test, sixteen conformance fixtures, and a capture path that reads a Lazarus fixture's counts rather than recomputing them. The gate 5 hole the dataset run recorded against the Solidity release predicate is closed. Sixteen audit rounds fixed 23 findings, six of them in code that had already shipped, including a deployment confirmation read for truthiness and a fifo that hung both capture paths. |
| `ariadne-v2.2.0` | generation | `grounded-agent-predicate` | `4ac9d0c052326b31082c98eed877ffe0a8abb4aa5a269c2ffadebfb681c8089e` | [state-fixture v2 guide](../../docs/state-fixture.md), [Ariadne public boundary](../../README.md) | State-fixture/v2 now ships in a fixed public Lazarus release whose local statement carries `receipts_root` and `receipt_trie_proved` without upgrading transaction hashes, canonical-chain membership or provider independence. Ariadne still reads the verified Lazarus manifest rather than reimplementing the receipt trie. The grounded-agent frontier revision, digest, status, current frontier and held job remain byte-identical. |
| `ariadne-v3.2.0` | evolution | `grounded-agent-predicate` | `b10c4ad6cea26758db83ad6ca08f833244d9a950849247cf984603c59b7e25ef` | [grounded-agent statement](../../examples/goldfinch-demo-v0-agent.json), [offline demonstration](../../examples/grounded_agent_demo.py) | Closes the grounded-agent-predicate frontier. Ariadne now ships its fifth registered predicate with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path over an existing `berean-release/v1` tree. The demonstration verifies the statement, changes one policy byte and proves the `release-digest` check refuses it. No evidenced predicate frontier remains, so the ledger closes mature. |
