# Fiat evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `fiat-v1.2.0`
- Frontier status: `open`
- Frontier revision: `installed-path-and-maturity-proof`
- Current frontier: Fiat's receipt-backed controller is thoroughly unit-tested, but its installed-path resolution and terminal maturity rule have not been proved together in a published delivery from a packaged plugin.
- Next Fiat job: Run one bounded delivery from an installed Hexaemeron plugin, record the resolved controller path and receipts, and close with an evidenced decision on whether any material Fiat frontier remains.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `fiat-v1.1.0` | baseline | `installed-path-and-maturity-proof` | `a30bea33332e20c6780a77f5d82bc899d7004b8d09321628777d36289bd128d0` | [skills#74](https://github.com/wildcat-finance/skills/issues/74) | Versioning starts here. Fiat has explicit active-skill path resolution, a mature-frontier refusal, and its own held frontier. |
| `fiat-v1.2.0` | generation | `installed-path-and-maturity-proof` | `a30bea33332e20c6780a77f5d82bc899d7004b8d09321628777d36289bd128d0` | [skills#74](https://github.com/wildcat-finance/skills/issues/74) | Made publish terminal only after final staging, push, merge, branch cleanup where permitted, and closure of any recorded task issue. |
