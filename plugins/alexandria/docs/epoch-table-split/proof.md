# Epoch table split: rebuild proof

These runs record the proving path in the [study](study.md) for
[skills#1888](https://github.com/wildcat-finance/skills/issues/1888). Each ran
on 2026-09-24 from the run worktree's root on the Step 4 commit
`d97d3c5bd3055384e5df9ebfac23048ea79b4b5b`, whose parent is
`3ffc3d45469ddeacad1ae68723c9d0c005fce181`. That commit changes no script or
schema, and its one test edit is the Alexandria version pin in
`tests/test_version_propagation.py`. The step's audit fixes add
`RebuildProofRecordTests`, which checks this document's counts and figures, to
`plugins/alexandria/tests/test_release_limits.py`. The environment set
`NO_COLOR=1` and `PYTHONDONTWRITEBYTECODE=1`, and exported
`ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING` to the two
staging trees the study's section 3 locates. The host is an Apple M5 Max with
137,438,953,472 bytes of memory, running Python 3.14.6. Every build wrote into
a fresh directory.

## Demonstrations

`python3 plugins/alexandria/examples/<demo>/demo.py build --output <fresh directory>`,
then `verify` on that directory. Build and verify printed the same identifiers.

| Demonstration | Build exit | Verify exit | Release identifiers |
| --- | --- | --- | --- |
| `usdc-interval-v0` | 0 | 0 | `sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa` |
| `usdc-interval-epochs-v0` | 0 | 0 | synthetic `sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036`; live `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a`; historical `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32` |
| `usdc-interval-live-v0` | 0 | 0 | `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32` |
| `wildcat-estates-interval-v0` | 0 | 0 | Wildcat V1 `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`; Wildcat V2 `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`; Compound `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a` |

## Committed releases

`python3 plugins/alexandria/scripts/alexandria.py verify plugins/alexandria/examples/compound-v3-phase0-v0/release`
exited 0 and printed
`sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab`.
The same command on `plugins/alexandria/examples/proof-backed-state-v0/release`
exited 0 and printed
`sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f`.

## Pinned identifiers

The study's section 3 lists six distinct interval identifiers and two committed
releases. The runbook's Step 4 Exit and the study's section 6 call them seven
identifiers; section 3 holds no seventh value, so the table checks the six and
both committed releases. The epochs and estates demonstrations both build the
current Compound release, and the epochs and live demonstrations both build the
historical one.

| Study pin | Rebuilt by | Result |
| --- | --- | --- |
| `sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa` | `usdc-interval-v0` | match |
| `sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036` | `usdc-interval-epochs-v0` | match |
| `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a` | `usdc-interval-epochs-v0`, `wildcat-estates-interval-v0` | match in both |
| `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32` | `usdc-interval-live-v0`, `usdc-interval-epochs-v0` | match in both |
| `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69` | `wildcat-estates-interval-v0` | match |
| `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3` | `wildcat-estates-interval-v0` | match |
| `sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab` | committed, verified | match |
| `sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f` | committed, verified | match |

## Split fixture

`(cd plugins/alexandria && python3 -m unittest -v tests.test_release_limits.SplitReleaseTests)`
exited 0: 1 test, OK. The fixture's plan has 80 shards and 80 parts, and its
release has 327 components and 327 captures. It builds, checks under receipt
v4 and verifies offline to the identifier it built.

## Wildcat V2 check memory

The release is the preserved V2 release the design observations name through
`ALEXANDRIA_WILDCAT_V2_RELEASE`, the `step11-cli-v2-release` directory under
the evidence directory the study's section 3 locates. Before measuring,
`alexandria.py verify` on it exited 0 and printed
`sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`.

`/usr/bin/time -l python3 plugins/alexandria/scripts/usdc_interval.py check <preserved V2 release>`
ran three times on the Step 4 tree. The base commit
`17ea8d2ab5e52081370b13b92390b64849ed880d`, exported from Git, ran the same
command three times as a same-day control. Every run exited 0, and the base and
Step 4 reports are byte-identical.

| Tree | Date | Real seconds | Maximum resident set bytes |
| --- | --- | --- | --- |
| Base, recorded in `design/observations.json` | 2026-09-23 | 4.36 | 1,208,811,520 |
| Base, re-measured | 2026-09-24 | 4.03, 4.03, 4.03 | 1,229,324,288; 1,233,502,208; 1,228,619,776 |
| Step 4 | 2026-09-24 | 4.00, 3.99, 3.99 | 1,237,434,368; 1,237,581,824; 1,236,959,232 |

Against the recorded base the Step 4 runs are 2.33% to 2.38% higher. The same
base code re-measured the next day is already 1.64% to 2.04% higher, so most of
that gap is the host. Against the same-day base the Step 4 runs are 0.28% to
0.73% higher, a median of 8,110,080 bytes. The three same-day base runs
themselves spread by 4,882,432 bytes, 0.40%, so these runs do not resolve a
difference of that size or smaller. `check` still holds the whole
release in memory, as the study's scope decision keeps it, and no budget is
claimed.
