# Metron evolution ledger

Policy: [../VERSIONING.md](../VERSIONING.md)

- Current version: `metron-v2.1.0`
- Frontier status: `open`
- Frontier revision: `same-conditions-comparison`
- Current frontier: Metron measures a command and holds a budget, and the check compares a run against a baseline without reading the conditions the recorder wrote beside each.
- Next Fiat job: Hold a comparison to the conditions it was taken under: the check reads the recorder block both files carry and names a run compared against a baseline taken on a different platform, interpreter or command. Accepted when a run and a baseline that disagree on a recorded condition produce a named verdict rather than a silent comparison, a run carrying no recorder block still compares as it does today, and both suites pass.
- Sources: [../../../../SOURCES.md](../../../../SOURCES.md)

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `metron-v0.1.0` | baseline | `measured-before-and-after` | `65eec7ac2fae18768bf4c6d041e5ca110675327159afb6e4f69fc23fdae364cc` | [hermes measured gas loop](../../../hermes/skills/hermes/SKILL.md) | Metron starts here, applying the measured-evidence discipline everywhere gas is not the unit. |
| `metron-v1.1.0` | evolution | `measured-before-and-after` | `5186746b189eea981393a052e8437de3a179d36d1afa88b38b18384cec881cff` | [skills#208](https://github.com/wildcat-finance/skills/pull/208), [skills#209](https://github.com/wildcat-finance/skills/pull/209) | Completes the held frontier. A budget declares a limit, a variance and a direction; the check compares a recorded run against both the limit and the stored baseline and reports one of six verdicts, failing on a regression past the variance, a value past the limit, a budget the run stopped reporting, and a name no budget declares. `record` keeps the ledger the skill already asked for, including the reverted attempts. Nothing here measures anything, which is what the new frontier is for. |
| `metron-v2.1.0` | evolution | `same-conditions-comparison` | `47bdfb4689306d63fe8ba0d220b1c920613d2331d04ec7efabf109917a32c228` | [skills#1410](https://github.com/wildcat-finance/skills/pull/1410), [skills#1432](https://github.com/wildcat-finance/skills/pull/1432), [skills#1434](https://github.com/wildcat-finance/skills/pull/1434) | Completes the held frontier. `time` runs one fixed argv, never through a shell, in its own process group under a timeout and an output cap, and writes the run file `check` reads unedited. `--repeat` keeps up to 1000 samples and reports the spread the variance is set from as `min`, `p50`, `p95`, `max` and `relative_spread`, which is `(max - min) / p50`; `--aggregate` names the median or the p95 and there is no mean. A failed repetition exits 1, names the repetition and the cause, and writes no run file. The recorder now produces the measurement the check reads. The audit found and fixed an aggregation-naming defect: every rule other than `median` returned the p95 while the run file recorded the name it was handed, so a caller outside the command line could write a file whose `aggregation` its number was not; the aggregator now refuses a rule outside the two names it accepts. |
