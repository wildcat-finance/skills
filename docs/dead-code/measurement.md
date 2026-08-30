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

The values below are filled from the committed source measurement before the
baseline record is published.

| field | observation | boundary |
| --- | --- | --- |
| commit | pending | fixed across runs |
| Git tree | pending | fixed across runs |
| run 1 real seconds | pending | below 60 seconds |
| run 2 real seconds | pending | below 60 seconds |
| run 3 real seconds | pending | below 60 seconds |
| median real seconds | pending | descriptive only |
| spread | pending | maximum minus minimum |
| result | pending | all runs must meet budget |

## Interpretation

No implementation change in this step is motivated by speed. This observation
checks the study's existing ceiling; it does not claim a performance
improvement or predict another host's runtime.
