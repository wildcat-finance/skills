# Demonstration: the bound archive restore

This records the skills#1648 demo path as it ran on 2026-11-07: the four
conformance resolvers the design record binds, the test module they select
from, and the design check that consumes their reports at integration. Every
command below was run once, from the run worktree, with `FORCE_COLOR` unset.
No command appears here that was not run.

## Host and tree

- Commit under test: `555b2864aef42331fb712b20d736fd5d3d5a81b2`, the Step 2
  head. Step 3 changes no byte under `plugins/`.
- Working tree: clean before each resolver.
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

1. `python3 .hexaemeron/design/probe.py conform --candidate anchored-cwd --criterion replacement-regression-guarded --root . --out .hexaemeron/design/reports/conformance/anchored-cwd-replacement-regression-guarded.json`
2. `python3 .hexaemeron/design/probe.py conform --candidate anchored-cwd --criterion nonempty-symlink-still-refuse --root . --out .hexaemeron/design/reports/conformance/anchored-cwd-nonempty-symlink-still-refuse.json`
3. `python3 .hexaemeron/design/probe.py conform --candidate anchored-cwd --criterion interrupted-restore-stays-bound --root . --out .hexaemeron/design/reports/conformance/anchored-cwd-interrupted-restore-stays-bound.json`
4. `python3 .hexaemeron/design/probe.py conform --candidate anchored-cwd --criterion from-mode-unchanged --root . --out .hexaemeron/design/reports/conformance/anchored-cwd-from-mode-unchanged.json`

| # | criterion | exit | `value` | report SHA-256 | wall time |
| --- | --- | --- | --- | --- | --- |
| 1 | `replacement-regression-guarded` | 0 | `true` | `30e285cc52d351b47b258ab20343df06608c99e8ec919a73585270059d0f550f` | 17 s |
| 2 | `nonempty-symlink-still-refuse` | 0 | `true` | `8eceef4b21a7d30fa412d4a826b4e305f9df46352cf9fb8eb07114eaefdfcf5f` | 24 s |
| 3 | `interrupted-restore-stays-bound` | 0 | `true` | `250eeea848e2b8044dec161b6d12b3d3d430a2bb5b12505576f8509d0dd52955` | 8 s |
| 4 | `from-mode-unchanged` | 0 | `true` | `47f45054014e44eafd316003810f8174c65cebcfa7dba11b7e26cfbca3ba5bc1` | 177 s |

Each resolver ran once and none was retried. The copies under
`reports/conformance/` beside this file equal the bytes the resolvers wrote;
`cmp` reported no difference for each of the four.

## The tests the resolvers select

The resolvers do not record test counts, so the same selections were run again
by hand, writing no report:

| module | `-k` pattern | tests | result |
| --- | --- | --- | --- |
| `test_checkpoint_restore_binding.py` | none (whole module) | 26 | OK, 31.9 s |
| `test_checkpoint_restore_binding.py` | `replacement` | 9 | OK |
| `test_hexctl_checkpoint_archive.py` | `test_restore_from_archive_refuses_non_empty_destination` | 1 | OK |
| `test_hexctl_checkpoint_archive.py` | `test_archive_restore_accepts_a_symlinked_destination_parent` | 1 | OK |
| `test_checkpoint_restore_binding.py` | `symlink_destination` | 9 | OK |
| `test_checkpoint_restore_binding.py` | `interrupted` | 4 | OK |
| `test_hexctl_checkpoint.py` | `restore` | 33 | OK, 169.6 s |

None of them skipped a test.

## The integration design check

The controller checks the `integration` transition by running Protasis's
checker on a copy of `.hexaemeron/design-evidence.json` placed beside it, so the
record's paths `design/reports/conformance/anchored-cwd-<criterion>.json`
resolve under `.hexaemeron/`. Only the selected candidate's pending cells are
due; the other twelve pending cells are not read. The same checker, run on the
record in place, writes nothing:

`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition integration --format receipt`

It exited 0 with no findings, selected `anchored-cwd`, and consumed the four
reports at the digests in the table above. Run from the 1.6.106 plugin cache,
which the run's controller uses, it gave the same output. The record's own
SHA-256 stayed `815abd409e5d7031407d9c4104884e47814da7798e8891917625fa7a18ab9742`.

## What this does not cover

- Git's own absolute-path window. Git turns the relative arguments it receives
  into absolute paths, so a swap and restore of the name completed within one
  Git child's lifetime can redirect that child's writes. The study measured it
  for `git init` and `git worktree add`. The seals bracket each child and
  refuse afterwards; they do not close the window, and no test here races a
  Git child.
- Linux Git behaviour. Every command above ran on Darwin. The study measured
  Linux primitives in a container with no Git.
- A racing writer. The binding tests swap the name at fixed points through
  `mock.patch` seams, so each run is deterministic. They prove the refusal at
  those points, not race freedom.
- Three leads from the Step 2 audit, none of them fixed here:
  1. The pinned interpreter's `mkstemp` builds the path of verify's
     design-evidence copy from `getcwd()`, which names the admitted inode's
     current location rather than the destination string. A parent writer racing a second rename inside
     that call is not covered, the same class as Git's window.
  2. `leave()` suppresses a failed `fchdir` back to the saved directory, for
     example after search permission is removed from the caller's directory.
     The process then stays in the admitted directory with no signal.
  3. A swap after the post-`git worktree add` seal and before `repository_root`
     refuses with `checkpoint restore derived worktree changed after Git
     created it` instead of the fixed sentence. Nothing is written.
- The rest of the study's section 9 list: processes running as the restoring
  account, root and administrators, a principal who can write inside the
  admitted directory, reused readers between seals, the window between the
  cleanup seal and its `rmdir`, two concurrent restores (skills#1649) and the
  origin of a `--from` restore.
