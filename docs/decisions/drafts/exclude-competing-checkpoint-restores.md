# Decision: Exclude competing checkpoint restores

## Status

Accepted, 2026-11-07, for the skills#1649 study. Numberless until the integration composer assigns its number. It supersedes no decision record.

## Context

`checkpoint restore` has no exclusion. It is absent from `MUTATING` ([`hexctl.py:2860`](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L2860-L3047)), so `main` ([`hexctl.py:33698`](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L33698-L33716)) runs it without `held_lock`. Adding the name would change nothing for a fresh destination: `held_lock` locks `<dir>/.hexaemeron/lock`, and when that root is absent it yields without a lock for every command but `init`. Two processes entered `held_lock(<empty dir>, "cmd_checkpoint_restore")` together against the real base controller and the directory stayed empty.

Competing `hexctl` processes therefore reach one destination and its imported state unexcluded: two archive restores, an archive and a `--from` restore, a live restore and a resume through its marker, `init` on the origin, and a mutating command on the restored worktree, including one paused in `held_lock`'s absent-root window across publication. The #861 audit measured one interleaving (step 4, round 4: both restores passed admission and the loser exited 2) and withheld a serialisation claim. #1648 left room for this lock: its anchor holds the admitted descriptor from admission to the end of the restore. [skills#1649](https://github.com/wildcat-finance/skills/issues/1649) asks to close the gap.

## Decision

The restore excludes competitors with a kernel lock on the origin directory's descriptor, holds the origin's and the worktree's ordinary run locks, and closes `held_lock`'s absent-root window. It does not join `MUTATING`, create a lock at admission, or take an exclusive entry.

1. L1, the directory lock. `_checkpoint_restore_archive_destination` takes `fcntl.flock(descriptor, LOCK_EX | LOCK_NB)` on the admitted no-follow descriptor before `fstat`, the `realpath` check and `scandir`. `--from` opens the origin `O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`, locks it before its `realpath`, top-level and clean checks, and holds it to the end. Both modes lock the origin directory's inode. A restore that did not obtain L1 never removes the destination, even one its own `mkdir` created.
2. L2, the origin's run lock. Inside `_checkpoint_restore_marker`, before the root's names are read, the restore creates `<origin>/.hexaemeron/lock` exclusively in a fresh root, or opens it `O_CREAT|O_NOFOLLOW` in an existing one and checks it regular with one link. It takes the lock and writes `held_lock`'s holder JSON with `command` `cmd_checkpoint_restore`. The marker's allowed set becomes `.gitignore`, the marker, `worktree` and `lock`.
3. L3, the worktree's run lock. After the stage's inventory check and before the fsync and the publishing rename, the restore creates `lock` in the private stage through the stage descriptor, locks it and writes the holder. The lock travels with the rename. `_checkpoint_restore_opaque_evidence` excludes a root-level, regular, single-link `lock` from the active-tree recheck; the capsule and stage snapshots stay strict. An interrupted-publication retry locks the existing worktree `lock` before its finalization reads.
4. L4, the absent-root window. In `held_lock`, a non-init command that finds no state root refuses at once through the missing-state message `load_state` prints, moved into one shared helper. A root that appears after the `isdir` check is locked like any other.
5. Release. Every lock descriptor is `O_CLOEXEC`. On every exit the restore unlinks each lock file it created while still holding it, then truncates and unlocks the rest, then closes. An uncontended restore leaves no `lock` in the origin root or the worktree's state root.
6. Order. L1, then L2, then L3, each `LOCK_NB`. No acquisition waits, so no cycle can form.
7. Refusal. Admission contention refuses `destination-occupied` before any byte is written. Every other contention, and any `flock` error, refuses with `checkpoint restore destination is held by another hexctl command` through `die(..., 1)` before any write. No path enters the sentence, and it is not a class in `CHECKPOINT_ARCHIVE_REFUSALS`, following #1648's moved-destination precedent.

## Alternatives

The study's probe, `docs/fiat-1649-restore-concurrency/probe.py`, measured four candidates on 2026-11-07 against a model of the restore's competing points, not `hexctl.py`. Each actor is a separate process ordered by ready and go files, never by timing. All 40 selection cells are digest-bound in `docs/fiat-1649-restore-concurrency/design-evidence.json`. The grid gave identical values in three runs on Darwin and one in a Linux container.

| Criterion | `mutating-set` | `destination-kernel-lock` | `exclusive-entry` | `admitted-fd-flock` |
| --- | --- | --- | --- | --- |
| `uncontended-restore-completes` | pass | pass | pass | pass |
| `competing-restores-one-winner` | fail | pass | pass | pass |
| `live-resume-refused` | pass | pass | pass | pass |
| `killed-holder-resumes` | fail | pass | pass | pass |
| `killed-before-write-readmits` | pass | fail | fail | pass |
| `imported-state-excluded` | fail | pass | pass | pass |
| `origin-init-excluded` | fail | pass | fail | pass |
| `concurrent-holders-after-crash` | 1 | 1 | 2 | 1 |
| `lock-acquisitions-per-restore` | 0 | 2 | 2 | 3 |
| `entries-left-after-early-kill` | 0 | 3 | 1 | 0 |

- `mutating-set` adds `cmd_checkpoint_restore` to `MUTATING` and keeps `held_lock` unchanged. Rejected: it fails four gates. It locks nothing for a fresh destination. It passes `live-resume-refused` by accident: the resumer's `lock` in the origin root trips the marker's allowed set, and the same accident makes a resume after a kill refuse for good. Against a mutating command it lets the ledger change and the restore then refuses with that ledger in place.
- `destination-kernel-lock` creates and locks `<destination>/.hexaemeron/lock` right after admission. Rejected: it fails `killed-before-write-readmits`. A restore killed in the inspector leaves `.hexaemeron/`, `.gitignore` and `lock`, so a retry refuses `destination-occupied` where the base admits it.
- `exclusive-entry` creates one `O_EXCL` entry and reclaims it when the recorded pid is dead. Rejected: it fails two gates. Two resumers after a crash read the same dead pid and both proceed, and `init` takes the origin's run lock, which this candidate never holds, so it rewrites the breadcrumb and the restore refuses after publication.
- Not carried: a lock keyed on the destination's parent, which serialises unrelated restores and does not follow a renamed destination; a lock keyed on the imported run identity, which needs a lock directory outside every destination and addresses two destinations of one archive, a #865 and #864 question; POSIX `lockf` on a directory, which both kernels refuse with `EBADF`.

`admitted-fd-flock` passes all seven gates and is the one survivor, so the selection rule is `unique-frontier`. Its trade is three non-blocking acquisitions per restore, the most of the four, and two relocation rule changes.

## Consequences

1. The exclusion is cooperative integrity against accident among `hexctl` processes run by one account: two agents, or an agent and an operator, naming the same directory. It is not a security boundary. A writer that takes no `hexctl` lock, including `checkpoint inspect --scratch` pointed at a restore destination, Git, editors and `rm`, is outside it, as are root, administrators and a process that deletes or replaces a lock file and then races.
2. Each competitor ends in one of three permitted outcomes. The restore completes and every competitor refuses without writing; a competitor wins and the restore refuses before it writes; or the restore refuses after publication and leaves the residue the reference already defines, active state with its marker, which a retry finalizes. Partial active state is anything else: a ledger or state another writer changed during the restore, two restores' bytes in one destination, or active state with no marker and no completed restore.
3. `status`, `next` and `verify` stay lock-free, as the `MUTATING` docstring requires. A reader that stages a file under the restored state root during finalization can make the restore refuse with the residue in consequence 2. It cannot cause partial active state.
4. `cmd_checkpoint_restore` stays out of `MUTATING` and takes its own locks. In `MUTATING`, `held_lock` would lock nothing for a fresh destination, and on a resume it would take the lock file the marker transaction takes, from a second open file description, and refuse itself.
5. Contention refuses `destination-occupied` at admission and `checkpoint restore destination is held by another hexctl command` elsewhere, exit 1, so the 24 classes in `CHECKPOINT_ARCHIVE_REFUSALS` are unchanged. A competitor that meets the restore's L2 or L3 refuses with `held_lock`'s existing message, naming `cmd_checkpoint_restore`, its pid and its start time. No `held_lock` message changes.
6. Two relocation rules change, which the #1648 runbook listed as ask-first and this study's acceptance approves. The marker's allowed set gains `lock` and nothing else. The active-tree recheck excludes the live `lock`, the one exclusion `controller-checkpoint.md` already names; `test_restore_rejects_unmanifested_lock_before_marker` still requires a `lock` inside a capsule to refuse.
7. SIGKILL leaves lock files with stale holder JSON. The kernel has released every lock, the allowed set admits `lock`, and `read_live_holder` already ignores a dead pid, so a resume completes. A restore killed in the inspector leaves its destination admissible.
8. Network filesystems are not measured. Linux emulates `flock` over NFS with byte-range locks, which need a writable descriptor, so a directory lock there is expected to fail and the restore refuses. The lock primitives and the selection model were measured on Darwin 25.5.0 and Linux 6.8.0; real `hexctl` and Git on Linux are not.
9. The #1648 anchor, seals and moved-destination sentence are unchanged. Two restores of one archive into two destinations stay with #865 and #864. The #2168 leads and #1648's stated residue stay open.
10. The `checkpoint.archive.restore_wall_ms` budget of 20,000 ms is unchanged and no performance claim is made. The added work per restore is three non-blocking `flock` calls, two exclusive creates, two holder writes and two unlinks.

The operator rules go in the "Restore transaction" section of `plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`, which today lists two concurrent restores as not defended, and the "Relocation transaction" section of `plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`. The Fiat generation row goes in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`. Until integration assigns the number, the standing home is `adr/exclude-competing-checkpoint-restores`.
