# Statement parts: demonstration proof

This document records the runs of the proving path in the [study](study.md)
for [skills#1892](https://github.com/wildcat-finance/skills/issues/1892). Each
ran on 2026-09-30 from the run worktree's root, with a clean tree, on the Step 4
commit `e3d38ff92e118835b77b147d6896780aa0068944`, whose parent is
`c9eb708e260093fb2043c938e2dfa40a4e4ed092`. That commit changes no script or
schema, and its one test edit is the Alexandria version pin in
`tests/test_version_propagation.py`. The step's next commit adds this document
and `ProofRecordTests`, which checks its figures and digests against the tree
and the study, to `plugins/alexandria/tests/test_statement_parts_records.py`.
The environment set `NO_COLOR=1` and `PYTHONDONTWRITEBYTECODE=1`, left
`FORCE_COLOR` unset, and exported `ALEXANDRIA_WILDCAT_V1_RELEASE` and
`ALEXANDRIA_WILDCAT_V2_RELEASE` to the two preserved release builds the
study's section 3 names. The host is an Apple M5 Max with 137,438,953,472
bytes of memory, running Python 3.14.6. Every output went to a fresh
directory.

## Heavy fixture

The release is the 16,384-component, 16,384-capture fixture that
`heavy_manifest` in `plugins/alexandria/tests/test_statement_parts.py` builds:
every component names one shared three-byte object, and every capture carries
seven 941-character gaps. It was written as a release directory, its manifest
in Alexandria's canonical encoding, and has identifier
`sha256:5a64aa73b2257b1b77e02d2c00efa634f922954499c799eb4f0279e62d0c59e4`.
Its single statement would encode to 121,356,890 bytes.

`statement <release> --output <file>` exited 1, wrote no file, and printed:

```text
alexandria: release statement encodes to 121356890 bytes, above Ariadne's 8388608-byte input limit
alexandria: write this release as an index and parts with --parts <directory>
```

`/usr/bin/time -l python3 plugins/alexandria/scripts/alexandria.py statement
<release> --parts <directory>` exited 0. Its receipt reported `part_count`
20, `component_count` 16,384 and `capture_count` 16,384, with the index and
part predicate types.

- Parts: 20.
- Largest part: 6,222,563 bytes.
- Key characters in each full part: 184,093.
- Components in each full part: 840.
- Last part: 3,141,251 bytes, 92,989 key characters, 424 components.
- Index: 3,017 bytes, 221 key characters.
- Largest unsigned DSSE envelope: 8,296,840 bytes.

Each of the 19 full parts closed on the 6,225,920-byte bound, with 78,051 key
characters to spare. Each key-character count equals the count taken with
Ariadne's own `gates.scanned` walk.

## Ariadne

`python3 plugins/ariadne/scripts/ariadne.py verify <file>` ran once on each
file bare, and once on the same bytes inside an unsigned DSSE envelope built
with Ariadne's `envelope.Envelope`, each with the default bounds.

| File | Bytes | Key characters | Components | Bare exit | DSSE bytes | DSSE exit |
| --- | --- | --- | --- | --- | --- | --- |
| `index.json` | 3,017 | 221 | index | 0 | 4,112 | 0 |
| `part/part-00000.json` | 6,222,558 | 184,093 | 840 | 0 | 8,296,832 | 0 |
| `part/part-00001.json` | 6,222,560 | 184,093 | 840 | 0 | 8,296,836 | 0 |
| `part/part-00002.json` | 6,222,561 | 184,093 | 840 | 0 | 8,296,836 | 0 |
| `part/part-00003.json` | 6,222,561 | 184,093 | 840 | 0 | 8,296,836 | 0 |
| `part/part-00004.json` | 6,222,561 | 184,093 | 840 | 0 | 8,296,836 | 0 |
| `part/part-00005.json` | 6,222,561 | 184,093 | 840 | 0 | 8,296,836 | 0 |
| `part/part-00006.json` | 6,222,561 | 184,093 | 840 | 0 | 8,296,836 | 0 |
| `part/part-00007.json` | 6,222,561 | 184,093 | 840 | 0 | 8,296,836 | 0 |
| `part/part-00008.json` | 6,222,561 | 184,093 | 840 | 0 | 8,296,836 | 0 |
| `part/part-00009.json` | 6,222,561 | 184,093 | 840 | 0 | 8,296,836 | 0 |
| `part/part-00010.json` | 6,222,562 | 184,093 | 840 | 0 | 8,296,840 | 0 |
| `part/part-00011.json` | 6,222,562 | 184,093 | 840 | 0 | 8,296,840 | 0 |
| `part/part-00012.json` | 6,222,563 | 184,093 | 840 | 0 | 8,296,840 | 0 |
| `part/part-00013.json` | 6,222,563 | 184,093 | 840 | 0 | 8,296,840 | 0 |
| `part/part-00014.json` | 6,222,563 | 184,093 | 840 | 0 | 8,296,840 | 0 |
| `part/part-00015.json` | 6,222,563 | 184,093 | 840 | 0 | 8,296,840 | 0 |
| `part/part-00016.json` | 6,222,563 | 184,093 | 840 | 0 | 8,296,840 | 0 |
| `part/part-00017.json` | 6,222,563 | 184,093 | 840 | 0 | 8,296,840 | 0 |
| `part/part-00018.json` | 6,222,563 | 184,093 | 840 | 0 | 8,296,840 | 0 |
| `part/part-00019.json` | 3,141,251 | 92,989 | 424 | 0 | 4,188,424 | 0 |

All 21 files exited 0 in both forms. Each part's SHA-256 equalled its
`part/part-<k>.json` subject in the index, 20 of 20, and the index's
`count` was 20. The stranger's check in
[release-statements.md](../release-statements.md#a-strangers-check) ran as
written on the set and exited 0.

## Emission cost

`/usr/bin/time -l` for `statement --parts` on the heavy fixture, recorded as
an observation with no threshold, as the study's section 10 sets out. The
host was not reserved for the run, so other sessions' work may have shared
it.

The command took 11.15 seconds of real time, 7.14 of user time and 3.69 of
system time. Its maximum resident set size was 1,507,606,528 bytes, and its
peak memory footprint 1,374,848,560 bytes.

## Pinned statements

`python3 plugins/alexandria/scripts/alexandria.py statement <release> --output
<fresh file>` ran on each release in the study's section 3 table. The
demonstrations were built with `demo.py build --output <fresh directory>`, the
fixture was ingested from a copy of `plugins/alexandria/tests/fixtures`, and
the Wildcat releases were read from the two exported variables. Every run
exited 0 and printed the pinned identifier.

| Release | Identifier | Statement bytes | Statement SHA-256 | Result |
| --- | --- | --- | --- | --- |
| test fixture (`tests/fixtures/capture-plan.json`) | `sha256:e86550e59baba75258093ed4b67c144d1dd520c68f0411d23ba59af050f3fed6` | 2,570 | `041c699bdefc8be359c88d738a8c5b45002e044b6226534d52bace7c09796c43` | match |
| `credit-history-v0` raw | `sha256:6117658c59c96e9ca32594ffe09e994d478dc7d9f2d3799c64bb25050c7fe0e2` | 2,792 | `d4846fd64852e5a8e34615679a252a7729976d1278b3be1ec177e1bc2da92fd2` | match |
| `credit-history-v0` derived | `sha256:fccc014cd400f553814b58911bb06cd450f395e6145e21c0071a06b092b181ec` | 2,792 | `3b12aa332fcf45cff14fb9a7d1c5f379852d3858c6cf56dcea57c26fc78523e6` | match |
| `usdc-interval-v0` | `sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa` | 11,026 | `c92e6cbb3b953acc3ad11e456cf5ca4715b5b2e8dbc98872a15e0c7c455716cf` | match |
| `usdc-interval-live-v0` | `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32` | 10,302 | `64df112deab0c91fe3da1aef1196a3a9226adee0cebc977468b3a609b4bc921f` | match |
| `usdc-interval-epochs-v0` synthetic | `sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036` | 11,026 | `656e225fbd67321230f58ff943a9dea3fc6ac265af8dc88beacbae2ba8b81bdd` | match |
| `usdc-interval-epochs-v0` live (current Compound) | `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a` | 10,303 | `76334510a1434645e0f249f4015c0c5d0065c17d0eea5f9814a7c9d12cc53527` | match |
| Compound Phase 0 (committed) | `sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab` | 71,339 | `4ebe969c40dbe77eacbe8848e530454596ecbb8ba9a07b3e6c49b11b41ca7a93` | match |
| proof-backed state (committed) | `sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f` | 3,689 | `faaff30f38025379781f35a7289af80cb0e15c9c0ff9c3efd0b9c09f1c77efa5` | match |
| Wildcat V1 | `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69` | 510,772 | `679277a2a3367d16a4cb462a12c805c6580291bbaaf7c3a6aa5b4d4e177c00ca` | match |
| Wildcat V2 | `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3` | 213,104 | `c891c9d510da6cf02136b082766792d520823beb98b79781c4f8cbcbaec7feae` | match |

All eleven statements keep the bytes the base emitted, so each stays on the
unchanged single path.
