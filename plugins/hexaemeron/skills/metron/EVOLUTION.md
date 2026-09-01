# Metron evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `metron-v1.1.0`
- Frontier status: `open`
- Frontier revision: `measured-before-and-after`
- Current frontier: Metron ships the budget check, so a declared budget is held mechanically, and nothing in the plugin produces the measurement it reads.
- Next Fiat job: Ship a recorder that produces a run file from a command it times, so a budget is measured by the same tool that holds it rather than by whatever a caller wrote. Accepted when a timed command yields a run the check reads unedited, a repeat count reports the spread the variance is meant to be set from, and both suites pass.
- Sources: [../../../../SOURCES.md](../../../../SOURCES.md)

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `metron-v0.1.0` | baseline | `measured-before-and-after` | `65eec7ac2fae18768bf4c6d041e5ca110675327159afb6e4f69fc23fdae364cc` | [hermes measured gas loop](../../../hermes/skills/hermes/SKILL.md) | Metron starts here, applying the measured-evidence discipline everywhere gas is not the unit. |
| `metron-v1.1.0` | evolution | `measured-before-and-after` | `5186746b189eea981393a052e8437de3a179d36d1afa88b38b18384cec881cff` | [skills#208](https://github.com/wildcat-finance/skills/pull/208), [skills#209](https://github.com/wildcat-finance/skills/pull/209) | Completes the held frontier. A budget declares a limit, a variance and a direction; the check compares a recorded run against both the limit and the stored baseline and reports one of six verdicts, failing on a regression past the variance, a value past the limit, a budget the run stopped reporting, and a name no budget declares. `record` keeps the ledger the skill already asked for, including the reverted attempts. Nothing here measures anything, which is what the new frontier is for. |
