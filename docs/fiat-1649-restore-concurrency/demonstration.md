# Demonstration: excluding competing restores

This records the skills#1649 demo path as it ran on 2026-11-07: the four
conformance resolvers the design record binds, the tests they select, and the
design check that consumes their reports at integration. Every command below
was run once, from the run worktree, with `FORCE_COLOR` unset. No command
appears here that was not run.

## Host and tree

- Commit under test: `ed0e0c064b8480e18df47f55d8a8020fa8715777`, the Step 2
  head. Step 3 changes no byte under `plugins/`.
- Working tree: `git status --porcelain` printed nothing before the first
  resolver and after each one.
- Platform: Darwin 25.5.0 arm64 (macOS 26.5.1).
- Interpreter: the one `.python-version` pins.
- Git: `/usr/bin/git` 2.50.1 (Apple Git-155).
- `gpg`: GnuPG 2.5.21, which the signed archive fixture needs.

## The four conformance resolvers

Each resolver runs `python3 -m unittest discover -s plugins/hexaemeron/tests -t plugins/hexaemeron/tests -p <module> -k <pattern>`
for each module and pattern it binds, and reports `true` only when every run
exits 0, runs at least one test and skips none. It writes its report to an
`--out` path that must not exist. The commands, exactly as each report records
them:

1. `python3 .hexaemeron/design/probe.py conform --candidate admitted-fd-flock --criterion restore-contention-guarded --root . --out .hexaemeron/design/reports/conformance/admitted-fd-flock-restore-contention-guarded.json`
2. `python3 .hexaemeron/design/probe.py conform --candidate admitted-fd-flock --criterion imported-state-guarded --root . --out .hexaemeron/design/reports/conformance/admitted-fd-flock-imported-state-guarded.json`
3. `python3 .hexaemeron/design/probe.py conform --candidate admitted-fd-flock --criterion killed-restore-recovers --root . --out .hexaemeron/design/reports/conformance/admitted-fd-flock-killed-restore-recovers.json`
4. `python3 .hexaemeron/design/probe.py conform --candidate admitted-fd-flock --criterion existing-restores-unchanged --root . --out .hexaemeron/design/reports/conformance/admitted-fd-flock-existing-restores-unchanged.json`

| # | criterion | exit | `value` | report SHA-256 | wall time |
| --- | --- | --- | --- | --- | --- |
| 1 | `restore-contention-guarded` | 0 | `true` | `8707818b5ee0be41457f46c8cc54401e109c137bea79efba98012564e803c427` | 39 s |
| 2 | `imported-state-guarded` | 0 | `true` | `7d5f30b67c698b2381b58853ba63f93c773321f848d8dacd7ffa2478afb7a67f` | 10 s |
| 3 | `killed-restore-recovers` | 0 | `true` | `9b67ebe22e7fc44fe6becc40a48bbc5a1a4c13b10155c876d7421b434a8d2a6c` | 11 s |
| 4 | `existing-restores-unchanged` | 0 | `true` | `2c22da30f5afb55bc9edd36f407ea1c7e46f443e9f7aec7df1a0fbcd8af7fe94` | 197 s |

Each resolver ran once and none was retried. The copies under
`reports/conformance/` beside this file equal the bytes the resolvers wrote;
`cmp` reported no difference for each of the four.

## The tests the resolvers select

The resolvers do not record test counts, so the same selections were run again
by hand on the same commit, writing no report:

| module | `-k` pattern | tests | result |
| --- | --- | --- | --- |
| `test_checkpoint_restore_concurrency.py` | none (whole module) | 18 | OK, 45.1 s |
| `test_checkpoint_restore_concurrency.py` | `one_winner` | 4 | OK |
| `test_checkpoint_restore_concurrency.py` | `live_resume` | 3 | OK |
| `test_checkpoint_restore_concurrency.py` | `origin_init` | 2 | OK |
| `test_checkpoint_restore_concurrency.py` | `imported_state` | 2 | OK |
| `test_checkpoint_restore_concurrency.py` | `killed` | 3 | OK |
| `test_checkpoint_restore_binding.py` | `test_` | 26 | OK, 27.9 s |
| `test_hexctl_checkpoint.py` | `restore` | 33 | OK, 163.5 s |
| `test_hexctl.py` | `TestRunLock` | 5 | OK |

None of them skipped a test. Criterion 1 selects the first three patterns, 9
tests; criteria 2 and 3 select 2 and 3 tests; criterion 4 selects the last
three rows, 64 tests. Four tests in the new module carry no resolver word and
ran only in the whole-module row: the absent-root refusal, the stage `lock`
that stays refused, and the two uncontended restores that leave no `lock`
file.

## The integration design check

The controller checks the `integration` transition by running Protasis's
checker on a copy of `.hexaemeron/design-evidence.json` placed beside it, so the
record's paths `design/reports/conformance/admitted-fd-flock-<criterion>.json`
resolve under `.hexaemeron/`. Only the selected candidate's pending cells are
due; the other twelve pending cells are not read. The same checker, run on the
record in place, writes nothing:

`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition integration --format receipt`

It exited 0 with no findings, selected `admitted-fd-flock`, and consumed the
four reports at the digests in the table above. Run from the 1.6.107 plugin
cache, which the run's controller uses, it gave byte-identical output. The
record's own SHA-256 stayed
`c727d18a199026f12914c4fd22289e4dab5d66a8a57e1fe6647b2c6c5958cfc2`.

## What this does not cover

- A writer that takes no `hexctl` lock. `checkpoint inspect --scratch` pointed
  at a restore destination, Git, editors and `rm` are outside the exclusion.
  So are root and administrators, and a process that deletes or replaces a
  lock file and then races. Advisory locks bind only cooperating callers, and no
  test here runs such a writer.
- Network filesystems. None was measured. Linux emulates `flock` over NFS with
  byte-range locks, which need a writable descriptor, so a directory lock there
  is expected to fail and the restore to refuse. No command here ran on one.
- Real `hexctl` and Git on Linux. Every command above ran on Darwin. The study
  measured the lock primitives and the selection model in a Linux 6.8.0
  container; it did not run `hexctl` or Git there.
- Every interleaving. The concurrency tests start real `hexctl` processes and
  order them with ready and go files at named seams, so each run is
  deterministic. They prove the outcome at those seams, not race freedom.
- `O_CLOEXEC` release under a live Git child. It is read from the open flags
  and the study's primitive measurement; no test kills a restore while a child
  runs.
- Two audit leads, neither fixed here:
  1. Step 2, round 1: an unopenable, non-regular or multi-link `lock`, and a failed holder
     write, refuse with `checkpoint restore destination is held by another
     hexctl command`, which names a holder that is absent. The refusal still
     precedes the guarded write. Different words need a study amendment.
  2. Step 1, round 1: `conform` runs its suites before `write_report`'s create-only check, so a
     resolver pointed at an existing report runs every suite first and then
     refuses, writing nothing.
- Two restores of one archive into two destinations, which stay with skills#865
  and skills#864, the skills#2168 leads, and the residue skills#1648 already
  states.
