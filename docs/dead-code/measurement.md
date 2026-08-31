# Dead-code static report measurement

## Method

- command: `python3 scripts/dead_code.py report --analyser python,repository --json`
- budget: each warm run below 60 seconds
- repository: clean tracked tree, one fixed commit and Git tree for all runs
- interpreter: exact repository pin in `.python-version`
- host: Darwin arm64
- timing: `/usr/bin/time -p`; three sequential warm runs after one unrecorded
  warm-up; stdout redirected to a fresh temporary file outside the repository

## Observation

| field | observation | boundary |
| --- | --- | --- |
| commit | `6fe9602659c89ac2eefdb0b467d5f83a8def8984` | fixed across runs |
| Git tree | `f64be556c8285a35c641ebe4b95ad908178e7de5` | fixed across runs |
| run 1 real seconds | 22.16 | below 60 seconds |
| run 2 real seconds | 22.15 | below 60 seconds |
| run 3 real seconds | 21.99 | below 60 seconds |
| median real seconds | 22.15 | descriptive only |
| spread | 0.17 seconds | maximum minus minimum |
| stable report identity | matched | commit, tree, universe, analyser identity/state/version and 411 findings |
| analyser state | `python=ran`, `repository=degraded` | incomplete repository families remain visible |
| result | pass | all three runs met the budget |

## Interpretation

No implementation change in this step is motivated by speed. This observation
checks the study's existing ceiling; it does not claim a performance
improvement or predict another host's runtime. Per-record duration telemetry is
expected to vary and is not part of the stable report identity.

## Live worktree observation

This observation was taken on 2026-08-31 before this record was written. The
checkout was dirty at `HEAD` `1c1137898bce9086c34310bd29b5cf8a889f800c`.
The live report bound Git tree `e78b3f5d8e81de01c2efb16a06dc3ff226bd22c3`
and worktree identity
`sha256:a3c95c707f51dd8046bb6e2f08ea44a3bc0ed6433fe4283f1fd7e6beb1b984f9`.

Snapshot construction used alternating isolated and shared-object runs, with
one warm-up for each mode and three recorded samples. Every sample verified
the captured source and removed its disposable tree. The general checked
runner still defaults to isolated objects; only the dead-code read path asks
for shared content-addressed objects.

| snapshot mode | samples in seconds | median | spread |
| --- | --- | --- | --- |
| isolated objects | 3.290, 2.874, 2.892 | 2.892 | 0.416 |
| shared objects | 2.922, 2.452, 2.483 | 2.483 | 0.470 |
| paired saving | 0.368, 0.422, 0.409 | 0.409 | 0.054 |

The shared mode saved 0.409 seconds at the observed median and avoided copying
the repository's 200 MB object store into each temporary report tree. The
no-analyser live command completed in 4.071 seconds and emitted a
baseline-ineligible schema-v2 report.

The full `python,repository` live command was also run once as a warm-up and
three times for observation. Its recorded times were 37.597, 78.905 and
87.167 seconds. Source, universe, analyser identities and states, and all 439
findings matched across the three runs, but concurrent full check runners made
the 49.570-second spread too wide for a performance comparison. Those timings
neither replace the clean-tree measurement above nor establish a regression.

The live mode removes commit or stash choreography. It does not promise a
faster analysis than the committed mode.
