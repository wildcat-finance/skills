# Decision: Build and check an interval release one component at a time

## Status

Accepted, 2026-09-30.

## Context

[#1891](https://github.com/wildcat-finance/skills/issues/1891) asks
`usdc_interval.py build` and `check` to hold one journal or part component in
memory at a time, so a release at the limits
[#1888](https://github.com/wildcat-finance/skills/issues/1888) published can be
built and checked on the 137,438,953,472-byte collecting host.

At base `150943da240837040478a76c3611d150fa04f2b6` both commands hold the
whole release. `Builder.build` builds every component's document before
writing any. `_check_interval` keeps every component's bytes and parsed
document, every shard's parsed logs and every boundary header, parses every
log again for the opening replay and derives every attribution row in one
list. Measured three times on the preserved Wildcat V2 release of 242,722,051
bytes, base `check` peaked at a median 1,240,547,328 bytes, 5.11 times the
release, so the host checks at most about 26.9 GB a release.

The design record
`plugins/alexandria/docs/bounded-memory-interval/design-evidence.json`,
SHA-256 `b495f9819f62fa7380434db6bc14c29b47812927492288c92bf51e4301666a47`,
graded four candidates. Three fail a selection gate, so `range-streamed-logs`
is selected under `unique-frontier`. The study beside it,
`plugins/alexandria/docs/bounded-memory-interval/study.md`, holds the
measurements and the per-unit costs.

## Decision

This record holds four decisions.

1. The memory model. Between two journal or part components, `build` and
   `check` keep the manifest and the four control components (plan,
   registry, reconciliation, epoch table), per-shard scalars, the opening
   logs a venue declares, and one 8-byte key per distinct transaction: the
   first 8 bytes of its hash, in 256 `array("Q")` buckets by first byte. That
   key is the only state that grows with the preserved logs. A repeated key
   costs one more read of the logs, collecting full hashes for those keys
   alone, and never admits a log. `check` reads each attribution part twice
   and `build` reads each staged logs journal twice, and every second read is
   bound again to the manifest or to the reconciliation record's journal
   digest.
2. The held-refusal rule. A refusal `check` finds early is held and raised
   where the base raises it: position refusals just before the opening
   replay, the code-digest refusal after it, then the epoch comparison, any
   row mismatch, the first-code rows, the venue gaps, the scopes and the
   journal bindings. A release with more than one defect keeps the base's
   first message.
3. The venue opening-log declaration. Each venue declares the logs its
   opening phase and evidence gaps read: `Upgraded` announcements for the
   single-proxy plan, the factory's `MarketDeployed` logs for Wildcat V2,
   none for Wildcat V1. The shared log walk hands only those logs to the
   opening phase, `epochs_from_opening` and `evidence_gaps`. A release whose
   declared opening logs number more than 1,048,576 (`MAX_SUBJECTS` times
   `MAX_EPOCHS`) refuses by name. The Aave V3 venue of
   [#1872](https://github.com/wildcat-finance/skills/issues/1872) adopts the
   declaration at whichever run's integration sync comes second.
4. Superseding the third decision of
   `docs/decisions/drafts/split-interval-log-attributions-across-components.md`,
   which kept `build` and `check` on the base memory model. That draft is not
   edited, because `HostileManifestRecordTests` pins its phrases.

No release format, receipt, schema or #1888 limit changes, and every release
that builds today keeps its bytes.

## Alternatives

- `plan-sized-releases` changes no code and ships as many releases as the host
  can check. Its model of 5.11 times a release projects 411,903,222,444 bytes
  for #1888's whole Aave interval, so it fails `aave-interval-checks-on-host`.
- `stream-bytes-hold-logs` reads and writes one component at a time but keeps
  every parsed log and row: 3,259 bytes a log, about 1.34 TB at the format's
  limits. It fails `format-limit-release-checks-on-host`.
- `compact-log-index` keeps a 219-byte index entry per log and passes both
  host gates, about 92.2 GB at the format's limits. It fails only
  `one-component-at-a-time`, the literal reading of the issue, whose ceiling
  is 16 bytes a log.

The selected design costs the most: 27 edit sites, 14 of them shared with
#1872's Step 7 head `5d5ec5e142d83140a0967fe13ad3498df3df2015`, and about
28.4 GB of extra reads on the Aave interval.

## Consequences

- The model projects about 2.66 GB for `check` of #1888's whole Aave interval
  and about 5.78 GB at the format's limits, against 8 bytes a log of
  per-log state.
- A hostile release whose logs are nearly all declared opening logs can make
  `check` hold up to 1,048,576 of them, about 1.34 GB at 1,280 bytes a
  parsed log, before the new limit refuses. That is outside the stated peak.
- `collect`, `reconcile`, `derive`, `index` and `statement` keep the base
  memory model.
- Once a venue sizes its releases to this model, each decision is expensive to
  reverse.
