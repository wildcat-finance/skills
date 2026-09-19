# Decision: Remove the aggregate plugin gate and record the suites as local

## Status

Accepted, 2026-09-19. Numberless until the merge that lands it, under the
draft path [ADR-077](../ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md)
set out.

## Context

`.github/workflows/plugins.yml` declared one shard per scope in
`tests/check-map-v1.json`, 27 of them, each running
`python3 scripts/run_checks.py --scope <id> --jobs 14`, with an aggregate
`plugins` job that passed only when every shard succeeded. Its header called
itself "the required aggregate plugin gate" and said "a required context must
exist on every pull request".

Neither half of that was true on the day of this record. The workflow had been
`disabled_manually` since its last run on 2026-08-30, so it produced no context
at all. And nothing required it: the branch protection on `main` lists one
required status check, `invariants`, and the "Required CI" ruleset is in
`evaluate` mode naming the same single check.

[#1260](https://github.com/wildcat-finance/skills/issues/1260) recorded the gap
on 2026-09-05 and named the two shapes that would close it: the workflow
re-enabled and shown green, or an explicit record that the plugin suites are a
local gate. It observed that three consecutive Horos runs had refused a
workflow lead on the false reassurance the declared map supplied.
[#1472](https://github.com/wildcat-finance/skills/issues/1472) is what the gap
costs: a `declared-inputs` block merged in `12cbe2e6` broke a snapshot
assertion in `plugins/hexaemeron/tests`, both halves passed every check their
pull requests ran, and the red reached `main` unobserved.

The first shape was tried before choosing the second. The gate was enabled for
about thirty seconds, dispatched, and re-disabled. Run
[35404964160](https://github.com/wildcat-finance/skills/actions/runs/35404964160)
took 2428 seconds of wall-clock and 141 runner-minutes, against roughly 29
minutes and 93 runner-minutes on 2026-08-30, and its conclusion was failure. 25
of 27 shards were green in 41 to 411 seconds. The two reds, `hexaemeron` at
2416s and `promise-machine` at 2143s, both exited 3 from
`plugins/hexaemeron/tests/run_tests.py`, which returns 3 when `scheduler_errors`
is non-empty and 1 for test failures, so a worker failed to deliver a complete
result and no test failed. `termination: not-required` in both, so nothing timed
out.

Two structural findings came out of that run. `run_checks` closes each requested
scope over its consumers, so `hexaemeron-suite` executed in 2 of the 27 shards
and `root-suite` in 9; the seven non-Hexaemeron shards in the 332 to 411 second
band were all paying for a `root-suite` that `repo.yml` already runs. And the
failure did not reproduce locally: CI's exact command,
`run_checks.py --scope hexaemeron --jobs 14`, is green on an 18-core host with
the suite at 1443.3s under the same contention, while every failing run had four
cores.

## Decision

Delete `.github/workflows/plugins.yml`. Record in `AGENTS.md`, beside the
check-map documentation, that the map declares what a check is and says nothing
about what hosted CI runs, and name what CI does cover.

The alternative considered was keeping cheap per-scope workflows for the
thirteen uncovered plugin suites, modelled on `janus.yml`. It is not taken here
because it is a larger change than the removal and does not depend on it: the
removal can land first and those workflows can follow if someone wants them.

## Consequences

About 7,000 test methods across thirteen plugin suites, and most of Hexaemeron,
run only where a contributor runs them. That was already true; what changes is
that the repository now says so instead of implying the opposite.

The condition #1472 demonstrated is unaddressed and can recur. The Hexaemeron
suite's cost, 2681 child CPU seconds and about 40 minutes on a four-core runner,
and the scheduler error that appears only there, are both untouched by this
record.

`tests/check-map-v1.json` keeps every scope. The runner is the local entrypoint
and the map stays the single definition of a check; only the claim that a hosted
job ran them goes away.
