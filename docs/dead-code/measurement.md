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
