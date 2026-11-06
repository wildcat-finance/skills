# Decision: Bind the archive restore to its admitted directory

## Status

Accepted, 2026-11-06, for the skills#1648 study. Numberless until the integration composer assigns its number. It supersedes no decision record.

## Context

`checkpoint restore --archive` admits its destination in `_checkpoint_restore_archive_destination` ([`hexctl.py:28568`](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L28568-L28646)): absent (created `0700`) or an empty, non-symlink directory, checked through an `O_NOFOLLOW` descriptor. Every later operation in `_checkpoint_restore_from_archive` ([`hexctl.py:28747`](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L28747-L29022)) and the shared relocation transaction `_checkpoint_restore_relocate` ([`hexctl.py:28239`](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L28239-L28530)) resolves the destination by its absolute name, and `bounded_probe` starts every Git child with `cwd=os.path.realpath(base_dir)` ([`hexctl.py:22878`](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L22833-L22934)). The admission descriptor is held unused until the `finally` closes it.

A writer on the parent can swap the name between admission and any later operation, and the restore then writes into the replacement. For a swap before `git init`, the whole restore lands there and the admitted directory stays empty. The #861 audit (S4-R1-06) repaired the docstring's stronger claim and left the window open. [skills#1648](https://github.com/wildcat-finance/skills/issues/1648) asks to close it.

The defended actor can write the destination's parent directory and cannot write inside the admitted directory. Root, administrators and any process running as the restoring account are outside the claim.

## Decision

The archive restore binds every controller-performed write to the admitted directory through an anchored working directory and `dir_fd`, seals each Git child, and states Git's own absolute-path window rather than closing it.

1. Anchor. After admission and after the inspector returns, the restore seals the destination name against the admitted descriptor, saves the working directory and `fchdir`s to the admitted descriptor. The seal is `_checkpoint_directory_still_at_path(destination, admitted_descriptor)`.
2. Writes. From then on every controller-performed write is relative to that directory or uses `dir_fd` from the admitted descriptor: capsule extraction, the relocation marker and `.hexaemeron/.gitignore`, the worktree home, the private stage, state and ledger writes, criteria history under `.git/`, active-state publication, breadcrumb, marker retirement and capsule-root removal.
3. Git children. Every Git child inherits that working directory and receives relative arguments only. `bounded_probe` gains one keyword for this; every other caller keeps `cwd=os.path.realpath(base_dir)`. After `git worktree add`, the worktree's `.git` file must read `gitdir: <destination>/.git/worktrees/<id>`.
4. Seals. Seals bracket each Git child and precede state recording, marker publication, marker retirement and success. A created destination is removed only after a passing seal. The working directory is restored first on every exit.
5. Recorded values. State `config.git.origin` and `config.git.worktree`, the restore receipt, the marker record, the breadcrumb and the result are built from the admitted destination string, never from `getcwd()` or Git's report.
6. Relocation. `_checkpoint_restore_relocate` takes an optional anchor. Without one, as for `--from`, every operation, record and refusal stays byte-for-byte as today.
7. Refusal. A failed seal refuses with the fixed sentence `checkpoint restore destination no longer names the admitted directory` through `die(..., 1)`. No path, member or tool byte enters it, and it is not a class in `CHECKPOINT_ARCHIVE_REFUSALS`. A 25th class would move the reference table, the frozen #861 study comparison and the computed post-`git init` set, and the relocation family that performs most seals already refuses through `die` (S4-R1-02).

## Alternatives

The study's probe, `docs/fiat-1648-archive-restore-binding/probe.py`, measured four candidates on 2026-11-06 against a model of the restore's write sequence after admission, not `hexctl.py`, with Git configuration pinned to `/dev/null` and unsigned commits. All 36 selection cells are digest-bound in `docs/fiat-1648-archive-restore-binding/design-evidence.json`.

| Criterion | `path-unchanged` | `identity-recheck` | `anchored-cwd` | `private-build-adopt` |
| --- | --- | --- | --- | --- |
| `unswapped-restore-completes` | pass | pass | pass | pass |
| `directory-swap-writes-nothing` | fail | pass | pass | pass |
| `symlink-swap-writes-nothing` | fail | pass | pass | pass |
| `interrupted-cleanup-stays-bound` | fail | pass | pass | pass |
| `residue-follows-reference` | pass | pass | pass | fail |
| `transaction-race-leaked-trials` | 47 | 35 | 0 | 0 |
| `name-resolving-writes` | 14 | 14 | 0 | 0 |
| `identity-probes-per-restore` | 0 | 38 | 12 | 3 |
| `bytes-built-outside-destination` | 0 | 0 | 0 | 39800 |

- `path-unchanged` is today's restore. Rejected: it fails three gates. The swapped-in directory receives the whole repository, and its created-destination cleanup `rmdir`s the empty replacement after an interruption.
- `identity-recheck` keeps absolute paths and re-proves the name before and after every operation and Git child. Rejected: each operation keeps a check-to-use window, and it leaked in 35 of 100 transaction-phase trials. In a rerun with 38 leaking trials, 34 leaked files were `tmp/fiat/fiat-run/.git`, written by `git worktree add` through the absolute worktree argument. `anchored-cwd` is lower on three metrics and equal on the fourth, so it dominates. Its own 0 is one run: three earlier runs of the same measurement, made while the probe was being written, gave 1, 1 and 0, and the one leak inspected held directories only, from `git worktree add`.
- `private-build-adopt` builds everything in a private scratch directory and adopts each entry by descriptor-relative rename. It is the only candidate that closes Git's absolute-path window. Rejected: it fails `residue-follows-reference`, because its marker stays in the private build and a killed restore leaves nothing the reference's retry rules can see. It also builds 39,800 bytes outside the destination, forces a full copy across filesystems and writes Git's worktree files by hand.
- Not carried: `/dev/fd/N` or `/proc/self/fd/N` as a path prefix (Darwin cannot traverse `/dev/fd/N` and has no `/proc`; on Linux the recorded paths would be descriptor aliases), and `git worktree add --relative-paths` (it sets `extensions.relativeWorktrees`, which needs Git 2.48 or later to read the restored repository, and does not cover `git init`).

Two candidates fail a selection gate and `anchored-cwd` dominates the other survivor, so the selection rule is `unique-frontier`.

## Consequences

1. Git's absolute-path window stays open and is stated, not claimed closed. A swap and restore of the name completed within one Git child's lifetime can redirect that child's writes. In 300 trials per command with the racer active only during that command, the window leaked for `git init` (3), `git init .` (1), `git init --bare .git` (1) and `git worktree add` (5, under `.git/worktrees/fiat-run/`), and never for `git fetch`, `git checkout` or `git config`. The whole-sequence race, with the racer active from the first operation (`probe.py observe`), leaked in 11 of 100 trials for `anchored-cwd`, against 10 for `path-unchanged`, 13 for `identity-recheck` and 0 for `private-build-adopt`; every `anchored-cwd` and `identity-recheck` leak was a `git init` template file or `.git/config`. Linux Git behaviour is unmeasured: the Linux container had no Git.
2. The process working directory changes for the restore's duration, and the restore holds two descriptors: the admitted directory and the saved working directory.
3. The model counted 12 identity probes per restore against 0 at the base, each one no-follow `open`, `fstat`, `realpath` and `close`. The `checkpoint.archive.restore_wall_ms` budget of 20,000 ms is unchanged, and no performance claim is made.
4. A refused restore leaves what it wrote in the admitted directory, wherever its name now is. The refusal cannot name that path, so the reference tells the operator to look in the parent directory. A refused restore writes no ledger entry.
5. Not defended: any process running as the restoring account, a principal who can write inside the admitted directory, reused readers between seals reading the replacement, the window between the cleanup seal and its `rmdir`, two concurrent restores ([skills#1649](https://github.com/wildcat-finance/skills/issues/1649)) and the origin of a `--from` restore.
6. The anchor holds the admitted descriptor from admission to the end of the restore, so a lock #1649 adds on that descriptor covers every bound operation without changing it. This decision adds no lock.
7. The 24 classes in `CHECKPOINT_ARCHIVE_REFUSALS`, the four post-`git init` classes the reference names and the `"init"` literal in `_checkpoint_restore_from_archive` are unchanged.
8. In `hexctl.py` the anchor is `_CheckpointRestoreAnchor`, built from admission's three return values. While it is active, `bounded_run` seals before and after every child and passes `bounded_probe`'s new `inherit_cwd` keyword for a relative directory, so the readers the restore reuses start their children in the anchor too. That brackets every child, not only the points the model sealed: an unswapped ZIP restore ran 119 seals around 51 children, against the model's 12. The restore budget is unchanged and no speed claim is made.
9. Three behaviours the model did not carry. The worktree link check also accepts `gitdir: ../../../.git/worktrees/<id>`, the spelling Git writes under `worktree.useRelativePaths`, because it names no destination. `_checkpoint_archive_guarded` seals again before it translates a reader's refusal, so a seal that fails inside a guarded reader reaches the operator as the fixed sentence, not as `ref-disagreement` or `identity-unavailable`. A caller whose working directory cannot be opened gets one more fixed `die(..., 1)` sentence, `checkpoint restore could not save its working directory`, which is not a class either.
10. The guards are `plugins/hexaemeron/tests/test_checkpoint_restore_binding.py`: 25 in-process restores of a real signed archive, swapping the name for an empty directory or a symlink at seven points, and for an empty directory before the directory carrier's clone, interrupting after a swap, and checking the working directory, the worktree link, the directory carrier's clone and an unchanged `--from` restore. On the parent commit 21 of them fail, among them the swap before `git init`, which restores into the replacement.

The operator rule goes in the "Restore transaction" section of `plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`, and the Fiat generation row in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`. Until integration assigns the number, the standing home is `adr/bind-archive-restore-to-its-admitted-directory`.
