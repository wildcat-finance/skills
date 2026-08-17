# Imprimatur evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `imprimatur-v1.1.0`
- Frontier status: `open`
- Frontier revision: `labelled-corpus-calibration`
- Current frontier: Imprimatur has deterministic tiered linting and regression tests, but no held-out labelled corpus that measures false positives and misses by enforcement tier.
- Next Fiat job: Build a held-out corpus of shipped human and model-assisted prose, report precision and recall by tier, tune only evidenced failures, and record whether another material calibration pass remains.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `imprimatur-v1.1.0` | baseline | `labelled-corpus-calibration` | `ed610953c08d982f939838315687b6672e19c2a20bdc0db6139fd4349e551535` | [skills#74](https://github.com/wildcat-finance/skills/issues/74) | Versioning starts here. Imprimatur has governed maturity handling and its own held frontier. |
