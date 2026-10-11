# Wildcat archive timestamp reproduction

Opted-in captures preserve exact selected-event block headers. Tabularium dates
`market_terms`, `market_closed`, `borrow` and `repayment` from the recorded event
block number and hash; Probitas carries each supported date and its source.
Legacy releases remain readable, with an explicit reason on every undated row.
These are provider-recorded observations. They do not establish independent
Ethereum proof, current standing or a fleet-wide recapture.

## Constructed production demonstration

From this repository root, use the interpreter recorded in `.python-version`:

```sh
python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case demonstration --report .hexaemeron/steps/4/demonstration.json
python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case integration --report .hexaemeron/reports/collector-journal-timestamp-demo.json
```

The first command executes five tests across V1 and V2. The second executes
those production paths again and writes the separate closed design report for
`collector-journal` / `timestamp-demo`. Its adjacent `.details.json` records
module and fixture hashes, executed counters, controls and bounded measurements.
A nonzero test result or missing executed observation refuses conformance.
Report outputs are confined outside retained releases; identical repeat reports
are admitted, while differing bytes require a fresh report destination.

The fixtures inject constructed RPC envelopes into Alexandria's real collector,
reconciler and builder. Offline interval verification, view rebuild and byte
comparison, Probitas evidence serialization, rendering and all five dossier
gates execute with socket creation denied. All four families are dated in each
new capture. Each constructed generation has three selected block identities,
one reused header and two added header requests: 1,056 journal bytes and 834
request/response bytes. These are fixture measurements, without a latency claim.
The suite also refuses a wrong hash during new collection and incomplete header
inventory during offline verification. Mixed legacy releases retain one dated
row and three explained gaps; absence never becomes timestamp zero. The native
`MarketClosed` argument remains separate from the header date.

## Inspect an available retained release

Supply your own verified raw release directory and a new view path outside it:

```sh
python3 plugins/tabularium/scripts/tabularium.py wildcat-view --alexandria-release RAW_RELEASE_DIR --out VIEW_JSON
python3 plugins/tabularium/scripts/tabularium.py verify-wildcat-view --alexandria-release RAW_RELEASE_DIR --out VIEW_JSON
```

Both commands operate offline. Read `timestamp_coverage` and each record's
`timestamp_support` in the resulting JSON. Neither rewrites the raw release.
To collect new headers, an otherwise valid V1/V2 interval plan must opt in with
`"wildcat_event_headers": "selected-event-blocks/v1"`; follow the existing
Alexandria [collector instructions](../../../plugins/alexandria/docs/usdc-interval-collector.md).

Current complete read-only projections of the two located retained raw releases
at Step 3 source `d1ed0cc2443c711b24be5910d0e8fc71d9e53b52` found:

- V1: 144 archive rows in 117 distinct event blocks; 8 dated and 136 header-missing.
- V2: 1,997 archive rows in 1,940 distinct event blocks; 82 dated and 1,915 header-missing.

[Current census](supplement/current-retained-census.json) binds raw release
identities and family counts. It is a sanitized measurement of local retained
inputs, without payloads or custody paths. Its portable commands explain how to
repeat the projection when those inputs are available; the original local
measurement command is retained privately. The original study's native-log
population (390 / 15,155 blocks) and matching preserved headers (8 / 95) are a
separate census. Those header counts are not dated archive-row counts.
No Lazarus payload was located or verified. Its planned block anchors are
metadata only. Other venue families and canonical schema 3 timestamps remain
outside this change.

## Recovery and specification history

The installed producer controller remains Fiat 6.78.1 under the recorded currency
waiver while repository sibling runtime source is 6.84.1. A default mixed-version
Linux receiver refused controller identity; the newer receiver refused gate
receipt drift. Actual Step 3 archive recovery passed in isolated Linux arm64,
with network disabled, no host mounts, an initially empty keyring and an empty
destination. The entire exact historical producer runtime at
`7bacf7af704530ced0f1dc90ffae254b9af36772` came from the verified archive's Git
bundle. Native inspect, restore, verify, status, next and identity checks remained
unchanged; expected next and snapshot identity matched. This is the recorded
pinned-runtime proof variant, without a claim that the default mixed-version
helper passed. Controller archives remain private; the constructed demonstration
above needs neither one nor an installation key.

The Step 1 [bundle](bundle.json), specification and source pins retain their
original bytes. The additive [supplement](supplement/manifest.json) binds this
reproduction, current census, executed production result and the four accepted
Step 2 scope amendments. The amendments corrected the staging-owner path and
admitted optional plan/checkpoint schema fields. The selected design, source
bound parser and Step 4 contract stayed fixed.
