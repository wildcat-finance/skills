# Affected-scope test runner benchmark

Measured demonstration for step 3 of issue #622: three serial-control and
three automatic-policy samples of the Hexaemeron suite runner on one frozen
revision, and the keep-or-revert verdict for the automatic scheduling policy.

## Method

Source digest: commit `cb3c147d759a88d39c19ab0e4b774b94228fe33a`, tree `55bf25644e0ec58d17e88a23bd21f70008049ead`, with a clean
tracked worktree. Every sample runs the complete suite through
`plugins/hexaemeron/tests/run_tests.py` with a fresh manifest discovered from
its own disposable snapshot. The serial control passes `--jobs 1`; the
automatic policy passes no override and derives its budget from CPU and quota
signals. The six samples alternate serial, automatic, serial, automatic,
serial, automatic, in that recorded order, on an otherwise idle machine.

Manifests are compared by digest and membership across all six samples, never
against a repository constant. The keep rule is the runbook's: the automatic
policy stays only when its median wall-clock gain exceeds the sum of the two
median absolute deviations, no concurrency-only failure class appears, and
observed resource growth stays within measured capacity.

## Samples

| # | mode | wall s | child CPU s | testsRun | failures | errors | fixture-blocked | queue HW | live-child HW | peak child RSS MiB | shards | cache |
| - | ---- | ------ | ----------- | -------- | -------- | ------ | --------------- | -------- | ------------- | ------------------ | ------ | ----- |
| 1 | serial | 592.6 | 471.7 | 1648 | 3 | 0 | 5 | 1 | 1 | 159 | 1 | hit |
| 2 | automatic | 78.4 | 724.5 | 1648 | 3 | 0 | 5 | 12 | 12 | 117 | 12 | hit |
| 3 | serial | 665.2 | 544.2 | 1648 | 3 | 0 | 5 | 1 | 1 | 154 | 1 | hit |
| 4 | automatic | 85.8 | 771.2 | 1648 | 3 | 0 | 5 | 12 | 12 | 122 | 12 | hit |
| 5 | serial | 667.4 | 546.1 | 1648 | 3 | 0 | 5 | 1 | 1 | 160 | 1 | hit |
| 6 | automatic | 81.3 | 752.1 | 1648 | 3 | 0 | 5 | 12 | 12 | 121 | 12 | hit |

Every sample discovered the identical manifest: digest `a4edf1abaa369a5146114a5e143a5e9cc4de7f5ef969e14129edb16d408b9c9f`,
`1653` identities, and identical membership byte for byte. Every
sample recorded the same verdict set: exactly the three inherited issue-429
subTest failures, zero errors and one skip, so no concurrency-only failure
class appeared in either mode.

## Verdict

| statistic | serial | automatic |
| --------- | ------ | --------- |
| median wall s | 665.2 | 81.3 |
| median absolute deviation s | 2.2 | 2.9 |

Median gain: 583.9 s. Sum of the two median absolute deviations: 5.0 s.
The gain exceeds that sum, so the automatic scheduling policy is
kept.

Resource growth stayed within measured capacity: the automatic samples' queue
and live-child high-water marks never exceeded the derived budget of
12 processes on 18 usable CPUs, and peak child memory topped out at
160 MiB against 128 GiB of host memory.

## Boundary

These numbers hold for this revision on this machine: Darwin 25.5.0,
18 logical CPUs, Python 3.14. They claim nothing about other
operating systems, quota regimes or hosted CI, and hosted workflows are
unchanged. Timing history remains scheduling advice only; it selects no test
and retains no verdict.
