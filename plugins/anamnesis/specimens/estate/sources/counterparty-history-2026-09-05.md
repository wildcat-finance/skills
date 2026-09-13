# Counterparty-history programme note of 5 September 2026: the Silo halt and the open actions

Wildcat Labs wrote this record on 7 September 2026 from its
counterparty-history programme note of 5 September 2026, a document held by the
maintainer whose SHA-256 is
4349d5f93468acd0117b40765828a3ad974ab2295302a463239d23d85b5a8efa. Round 1
carries the capture-inventory finding of its section 2, lines 55 to 63; round 2
carries the three open actions of its section 9, lines 261 to 268. Every status
is `open`, because the note records no remediation. The file column names the
capture or service a row concerns, not a path. Nothing here names where the
captured data or the note are kept, and no credential value appears.

## Capture inventory, round 1 -- 5 September 2026

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| P1-R1-01 | unrated | silo | Silo halted with, verbatim, `refused: eth_getLogs: URLError` and `stopped at v2/markets/optimism.json`; the runner process is not alive, the releases directory is empty, the v3 raw capture is 0 B against 16 enumerated v3 chain configurations, and no handover note exists | open |

## Open actions carried from prior handovers, round 2 -- 5 September 2026

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| P1-R2-01 | unrated | graph-gateway | Rotate the Graph gateway key: a Growth-plan gateway key was used and sits in the operator's shell history, to be rotated in the studio when convenient; this record names the key's existence and carries no value | open |
| P1-R2-02 | unrated | compound-v3-and-euler-v2 | The Compound v3 and Euler V2 graph-capture releases carry a release id but no statement file: built, never sealed | open |
| P1-R2-03 | unrated | silo | Silo V2 from optimism onward is unresumed and unreleased | open |
