# Demonstration: the canonical event v3 path

This is the record that the demo path ran. It lists the commands of the study's
success criteria and of this step's exit in the order they were run, the exit
code observed for each, the test counts, the four conformance report digests
and the six rebuild digests. No command appears here that was not run.

## What this does not say

A Tabularium release verifies offline against the source bytes it preserves and
against the schema its `schema_version` names. That is a statement about
internal consistency. Nothing below says that a mapped credit event is a true
description of what happened on Ethereum mainnet, that a preserved capture
covers every event in its window, or that the publisher of a release is who the
release says. Each coverage manifest carries those limits in its `known_gaps`
list, including that the release is unsigned.

## Host

| item | value |
| --- | --- |
| interpreter | the one `.python-version` pins |
| working directory | the repository root of the run worktree |
| `TMPDIR` | `/private/tmp/fiat-1362-tmp` |
| starting commit | `1d131b98a78c888b571f302e5b4c899aa2e47caf` |

## The study's demo path

Each command was run from the repository root, in the order the study gives.
`<run>` stands for the absolute path of the run worktree; the four resolver
invocations used the exact strings the design record binds, with that prefix
spelled out.

| # | command | exit |
| --- | --- | --- |
| 1 | `python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium` | 0 |
| 2 | `python3 plugins/tabularium/examples/aave-v4-v1/rebuild.py` | 0 |
| 3 | `python3 plugins/tabularium/examples/euler-v1-v1/rebuild.py` | 0 |
| 4 | `python3 plugins/tabularium/examples/euler-v2-v1/rebuild.py` | 0 |
| 5 | `python3 plugins/tabularium/examples/aave-v4-v0/rebuild.py` | 0 |
| 6 | `python3 plugins/tabularium/examples/euler-v1-v0/rebuild.py` | 0 |
| 7 | `python3 plugins/tabularium/examples/euler-v2-v0/rebuild.py` | 0 |
| 8 | `python3 plugins/tabularium/scripts/tabularium.py verify plugins/tabularium/examples/aave-v4-v1/coverage.json` | 0 |
| 9 | `python3 plugins/tabularium/tests/prove_schema_v3.py --candidate superseding-releases --criterion rejection-parity --report <run>/.hexaemeron/reports/superseding-releases-rejection-parity.json` | 0 |
| 10 | `python3 plugins/tabularium/tests/prove_schema_v3.py --candidate superseding-releases --criterion shipped-ledgers-validate-v3 --report <run>/.hexaemeron/reports/superseding-releases-shipped-ledgers-validate-v3.json` | 0 |
| 11 | `python3 plugins/tabularium/tests/prove_schema_v3.py --candidate superseding-releases --criterion legacy-v0-verify --report <run>/.hexaemeron/reports/superseding-releases-legacy-v0-verify.json` | 0 |
| 12 | `python3 plugins/tabularium/tests/prove_schema_v3.py --candidate superseding-releases --criterion suite-wall-time --report <run>/.hexaemeron/reports/superseding-releases-suite-wall-time.json` | 0 |
| 13 | `python3 scripts/plugin_release.py --base 1d131b98a78c888b571f302e5b4c899aa2e47caf --head "$(git write-tree)"` | 0 |
| 14 | `python3 -m unittest discover -s tests` | 0 |

## The step's exit gates

| command | exit |
| --- | --- |
| `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/tabularium-schema-v3/demonstration.md --max-defects 0` | 0 |
| `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition integration` | 0 |
| `python3 plugins/tabularium/tests/run_tests.py --elenchus-report .elenchus/schema-v3-step-5-exit.json` | 0 |

Three further exit commands need a committed tree and are recorded in the next
section. `plugin_release.py --head HEAD` names a commit outright. Both
`run_checks.py` rows need one through the planner, which unions the requested
scope with the scope owning each changed path and then closes over consumers.
The three `.horos/` artefacts this step regenerates resolve to the `root`
scope, and `root` draws in `dead-code` as a consumer, so while they are
uncommitted `scripts/dead_code.py suppressions --check` is selected under
either `--scope` and refuses to analyse a checkout with modified tracked
files. On the committed tree no path has changed, and `--scope tabularium`
then selects four checks, the three lints and the Tabularium suite, while
`--scope schemas` selects nine.

The elenchus report at `.elenchus/schema-v3-step-5-exit.json` records 232
tests, zero failures, zero errors, zero skips, and a complete run.

## The gates that need a commit

| command | exit |
| --- | --- |
| `python3 scripts/run_checks.py --scope tabularium --format json` | 0 |
| `python3 scripts/run_checks.py --scope schemas --format json` | 0 |
| `python3 scripts/plugin_release.py --base 1d131b98a78c888b571f302e5b4c899aa2e47caf --head HEAD` | 0 |

Both scopes reported `green` with no check failing. `plugin_release.py` reported
`tabularium: 0.3.3 -> 0.4.1`, one changed package, against the run's starting
commit, and `0.4.0 -> 0.4.1` against the step 4 branch this step is stacked on.

These three were first run against the commit made from the tree above. This
section was then written and the commit amended, and all three were run again
against the amended commit, which is the one these bytes belong to. The
imprimatur row in the previous section was likewise re-run against these bytes,
since it reads this file.

## Test counts

| suite | tests | result |
| --- | --- | --- |
| `plugins/tabularium/tests` | 232 | OK, no failure, error or skip |
| `tests` (root) | 2049 | OK |

The Tabularium count was 228 at the end of step 4. The four added here are the
three that hold the `suite-wall-time` criterion and the one that holds the
committed conformance report copies to their digests.

## Conformance reports

The four conformance criteria of the design record, each resolved by the run
recorded above.

| criterion | unit | value | SHA-256 of the report |
| --- | --- | --- | --- |
| `rejection-parity` | boolean | true | `da92d014e421bd534e3ea0750499049e38e9c190a194fda93372db3aa54b8dd7` |
| `shipped-ledgers-validate-v3` | boolean | true | `16e7134219006bdcff6f6846dd1c8e017d1cf54be5bce6d344d7a2638300f037` |
| `legacy-v0-verify` | boolean | true | `89abec0fcd2c656f37354e8be767248083bcaa22462198a6898c15292b534008` |
| `suite-wall-time` | milliseconds | 5090 | `fe312a7d7ac84f6973f87e6f4cc52393ff079a7c29103a5737a955b57607ddff` |

Each resolver writes its report under the run worktree's `.hexaemeron/`, which
Git ignores. The copies in `reports/` beside this file are byte-identical to
what the resolvers wrote, and `plugins/tabularium/tests/test_schemas.py` holds
each copy to the digest above, so an edited copy fails the suite.

## Rebuild digests

Each `rebuild.py` rebuilds its release from the preserved `source.json` and
compares the result with the published `events.jsonl`. All six matched.

| release directory | schema | events | SHA-256 of `events.jsonl` |
| --- | --- | --- | --- |
| `examples/aave-v4-v1` | 3 | 500 | `81d416a10b70ab0f3d9a3bd41c0680e235b3b64f4f06cc36b4f4292c81136492` |
| `examples/euler-v1-v1` | 3 | 1 | `5b1016a9bc143f42e9bea46de71b3d1917bf6731d93b4c49f974df3660bc8595` |
| `examples/euler-v2-v1` | 3 | 2 | `f2b227058f53cd644c11359e911c8494924d6fef7da7072e8a33a4baf952d02a` |
| `examples/aave-v4-v0` | 2 | 500 | `490d3f6399f84af8a81a5401b3cc92bf7ecfbe98a6bb02f07215b9099625ccf7` |
| `examples/euler-v1-v0` | 2 | 1 | `4034622f8b34147dead8a87d7c16b2a7c7197ed6417809fec41716a8028552aa` |
| `examples/euler-v2-v0` | 2 | 2 | `f563baa00c737384a3901f1bb3a7ae977f68f52a813eae9d02071eb2f4d0a5fe` |

The three v0 digests are the ones the study recorded at the starting commit, so
the superseding releases changed none of their bytes.

## The suite budget

`suite-wall-time` is the one criterion of the design record that blocks
integration. It times `python3 -m unittest discover -s plugins/tabularium/tests
-t plugins/tabularium` in a subprocess with `time.monotonic` and records the
elapsed milliseconds.

| item | milliseconds |
| --- | --- |
| observed | 5090 |
| budget | 60000 |
| study baseline at `1d131b98`, 137 tests | 3650 |

The budget has one figure behind it and one run behind that figure. A second
run of the same command on the same host took 4898 ms. Neither number is a
distribution, and the value recorded is the longest of the observations a run
collects rather than their mean.

## What the selection evidence does not reproduce

`docs/tabularium-schema-v3/design-probe.py` produced the 25 selection-stage
files in `reports/`. It cannot be run from the path it is committed at:
`ROOT = Path(__file__).resolve().parents[1]` resolves to `docs/`, so the import
of `tabularium_lib` fails and the script exits 1 with `ModuleNotFoundError: No
module named 'tabularium_lib'`. Its committed bytes are the preserved evidence
of what produced those reports, not a copy anyone can run in place.

Twenty-four of those 25 files are criterion reports, one per candidate and
selection criterion, and each names as its `command` an absolute path to a copy
of that script under the run worktree's `.hexaemeron/`, which Git ignores. The
twenty-fifth, `selection-observations.json`, is the aggregate the same run
wrote and carries no `command` field at all, so it names nothing that could be
run again either. No tracked artefact therefore reproduces the selection stage.
The files are readable and their inputs were the tree at
`1d131b98a78c888b571f302e5b4c899aa2e47caf`, but re-deriving them needs a
worktree this repository does not carry. That is a limitation of this record,
recorded here because step 1's accepted finding S1-R1-02 asked for it and step
4's Files field never reached this directory.
