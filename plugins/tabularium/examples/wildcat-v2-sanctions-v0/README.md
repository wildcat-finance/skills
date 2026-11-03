# Constructed Wildcat V2 routing specimen

This unsigned schema-3 fixture uses adapter `1.3.0`. Every input log is synthetic. The fixture proves no historical emission, runtime equivalence, sanction status, identity, underlying cash movement, settlement or independent chain boundary.

## Scope

The positive transaction exercises V2 queued-claim and market-token escrow routing. A separate overlap transaction retains both the existing batch-burn relation and the new routing relation on one transfer. Separate missing-primary, duplicate-primary and duplicate-companion transactions leave named gaps. Each companion remains `supporting-routing` and emits no second canonical action. Queue scaled and normalized claims and market-token transfer units remain separate.

## Rebuild

From the repository root:

```bash
python3 plugins/tabularium/examples/wildcat-v2-sanctions-v0/rebuild.py
python3 plugins/tabularium/scripts/tabularium.py verify plugins/tabularium/examples/wildcat-v2-sanctions-v0/release/coverage.json
```

The builder reconstructs the raw release through Alexandria, builds a fresh canonical root, compares every file with [expected.json](expected.json), removes disposable original inputs and verifies the moved read-only root. It changes no published specimen file.

## Interpretation

Keep `release/` together with `source/raw-release/`. The [mapping guide](../../docs/wildcat-canonical.md#versioned-sanctioned-account-routing) defines complete native keys, one-to-one cardinalities, reciprocal selectors and the consumer limits. The repository bundle `docs/kickoff/2091/reproduction.md` records the source commands and conditional retained-coverage boundary. Verified retained absence supplies no positive historical join.
