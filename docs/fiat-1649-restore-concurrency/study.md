# Study: establish the archive restore concurrency boundary

Task: [wildcat-finance/skills#1649](https://github.com/wildcat-finance/skills/issues/1649)
(`Fiat-Required: 1`, carryover `none`). Surveyor: `fiat-1649-study-surveyor`.
Target: this repository at `main` `eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797`,
run branch `fiat/1649-establish-the-archive-restore-concurrency-b`. Every
`hexctl.py:N` below is a line of
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at that commit (33,724
lines). The issue cites `hexctl.py:2528` at `485a6c81`; every location here
is re-derived at the starting commit.

Assuming, unless corrected:

1. The competitors are `hexctl` processes run by the same account: two
   agents, or an agent and an operator, naming the same directory. The
   exclusion is cooperative integrity against accident, not a security
   boundary. A writer that takes no `hexctl` lock, including `checkpoint
   inspect --scratch` pointed at a restore destination, is outside it, as are
   root and administrators.
2. A permitted outcome is one of three. The restore completes and every
   competitor refuses without writing. A competitor wins and the restore
   refuses before it writes. Or the restore refuses after publication and
   leaves the residue the reference already defines: active state with its
   marker, which a retry finalizes. Partial active state is anything else: a
   ledger or state another writer changed during the restore, two restores'
   bytes in one destination, or active state with no marker and no
   completed restore.
3. `status`, `next` and `verify` stay lock-free, as the `MUTATING` docstring
   requires (`hexctl.py:2884`). A reader that stages a file under the
   restored state root during finalization can make the restore refuse with
   the residue in assumption 2. It cannot cause partial active state.
4. `cmd_checkpoint_restore` stays out of `MUTATING`. The restore takes its own
   locks. Section 2.1 shows `held_lock` would lock nothing for a fresh
   destination, and on a resume it would take the same lock file the marker
   transaction takes, from a second open file description, and refuse
   itself.
5. Lock contention refuses with existing vocabulary where it can: at archive
   admission it is `destination-occupied`, before any byte is written. Every
   other contention refuses through `die(..., 1)` with one fixed, path-free
   sentence, `checkpoint restore destination is held by another hexctl
   command`. That follows #1648's `CHECKPOINT_RESTORE_MOVED` precedent and
   is not a 25th class.
6. The design changes two relocation rules that the #1648 runbook listed as
   ask-first: the marker's allowed name set gains `lock`, and the
   closed-inventory recheck of the active tree excludes the live `lock`, the
   one exclusion `controller-checkpoint.md` already names (line 52). The
   driver accepts both by accepting this study.
7. Closing `held_lock`'s absent-root window changes no message. Every
   non-init mutating command already dies at `load_state`'s missing-state
   block (section 2.1); the fix moves that refusal ahead of the unlocked
   yield.
8. No known-failure inventory. The #861 round 4 lead is this run's subject;
   the `restore-contention-guarded` conformance cell holds its guard.
9. The interpreter is `.python-version`, 3.14.6, with stdlib `unittest`, on
   Darwin 25.5.0 arm64 with `/usr/bin/git` 2.50.1. Linux was measured in
   `python:3.14.6-slim-trixie` (kernel 6.8.0-117) for the lock primitives and
   for the whole selection model; real `hexctl` and Git on Linux are not
   measured.

Rejecting assumption 6 leaves no candidate that excludes `init` and a
resume together (section 4.3). Rejecting assumption 4 makes the resume path
refuse itself unless the marker transaction reuses `held_lock`'s descriptor.

## 1. Problem statement

`checkpoint restore` has no exclusion. It is absent from `MUTATING`
(`hexctl.py:2860-2883`), so `main` (`hexctl.py:33698-33716`) runs it
without `held_lock`. Adding the name would change nothing for a fresh
destination: `held_lock` (`hexctl.py:2927`) locks `<dir>/.hexaemeron/lock`,
and when that root is absent it yields without a lock for every command but
`init` (`hexctl.py:2941-2947`). Measured against the real base controller,
two processes entered `held_lock(<empty dir>, "cmd_checkpoint_restore")`
together and the directory stayed empty.

So competing operations reach the same destination and the same imported
state unexcluded. The #861 audit measured one interleaving (step 4, round 4:
two archive restores both passed admission and the loser exited 2) and
withheld a serialisation claim. Section 2.1 enumerates the rest.

Who it is for: an operator, or a driver agent, restoring a Fiat run while
another agent or tool may be acting on the same directory.

A working prototype means: for each competitor in section 2.1 the outcome is
one of assumption 2's three, shown by a test that starts real processes and
orders them with file barriers; an uncontended archive or `--from` restore
leaves exactly today's bytes; a restore killed at any point releases every
lock it held, and the reference's retry rules still resume it.

Demo path. The last step runs the four conformance resolvers of section 4.4
from the run worktree and records their output. Controller: the run tree's
`hexctl.py`. Source command: `python3 .hexaemeron/design/probe.py conform
--candidate admitted-fd-flock --criterion <id> --root . --out <path>`.
Bounded positive observations: two concurrent archive restores into one
destination give one restore and one refusal; a mutating command against
the worktree during finalization refuses and the ledger is unchanged; a
resume after a killed restore completes. Bounded negative observations: a
live restore's resume refuses; `init` against the origin during a restore
refuses or the restore refuses before it writes state; nothing is claimed
about writers that take no `hexctl` lock.

| id | Criterion | Check |
| --- | --- | --- |
| SC-1 | Two archive restores into one destination, ordered at three fixed points (one holds admission through the inspector; the creator of an absent destination pauses before locking; one pauses between its emptiness scan and its first write), end with one exit 0, one refusal, and the destination holding exactly the winner's restore | test names containing `one_winner` in the new `plugins/hexaemeron/tests/test_checkpoint_restore_concurrency.py`; conformance `restore-contention-guarded` |
| SC-2 | A `--from` restore, or a resume through the relocation marker, against a destination a live restore holds refuses without writing, and the live restore completes | names containing `live_resume`; `restore-contention-guarded` |
| SC-3 | `init` against the restore's origin after the marker refuses; before the marker, one of the two refuses and a refused restore leaves no active state | names containing `origin_init`; `restore-contention-guarded` |
| SC-4 | A mutating command against the restored worktree, started after publication or paused inside `held_lock`'s absent-root window across publication, refuses, and the restored ledger and state are unchanged | names containing `imported_state`; `imported-state-guarded` |
| SC-5 | A restore killed with SIGKILL after the marker releases its locks; a resume then completes. One killed during the inspector leaves its destination admissible | names containing `killed`; `killed-restore-recovers` |
| SC-6 | Uncontended archive and `--from` restores, the #1648 binding cases and the run-lock tests are unchanged | `test_checkpoint_restore_binding.py`, `test_hexctl_checkpoint.py -k restore`, `test_hexctl.py -k TestRunLock`; `existing-restores-unchanged` |
| SC-7 | Repository gates stay green at every step exit | `python3 -m unittest discover -s tests`, `CHECKPOINT_COSIGN=<cosign> python3 plugins/hexaemeron/tests/run_tests.py`, `python3 scripts/run_checks.py`, with `FORCE_COLOR` unset |

## 2. Prior art

### 2.1 Current dispatch, locking, and who reaches what

The run lock:

- `MUTATING` (`hexctl.py:2860-2883`) lists 20 commands. It holds
  `cmd_checkpoint_export` and `cmd_checkpoint_archive`, not
  `cmd_checkpoint_restore`, `cmd_checkpoint_inspect` or
  `cmd_checkpoint_identity`. `status`, `next` and `verify` stay out by design.
- `held_lock` (`hexctl.py:2927-3047`) opens `state_root(base_dir)/lock`
  (`O_CREAT|O_RDWR|O_CLOEXEC|O_NOFOLLOW`, regular, one link), takes
  `flock(LOCK_EX|LOCK_NB)`, and on contention dies 1 naming the holder from
  the JSON it wrote (`pid`, `command`, `ts`). It is keyed on the path
  `--dir`/.hexaemeron, not on an inode, and exists only once that directory
  does. Without the root it yields unlocked unless the command is `cmd_init`,
  which creates the root and on teardown removes it again if it holds only
  the lock (#1345, S2-R1-02 and S2-R1-03).
- The absent-root window. `main` calls `held_lock` and only then
  `load_state` (`hexctl.py:33703-33715`). If a restore publishes the
  worktree's state root between `held_lock`'s `isdir` and that read, the
  command runs with no lock against the imported state. `cmd_halt`,
  `cmd_resume`, `cmd_reset` and `cmd_amend_runbook` read state first thing
  (`hexctl.py:32484`, `32493`, `33194`, `22561`), so every non-init mutating
  command dies at `load_state` when no state exists.
- Restore's own paths. Archive admission, `_checkpoint_restore_archive_destination`
  (`hexctl.py:28873-28951`), creates an absent destination `0700` or admits an
  empty non-symlink one through an `O_NOFOLLOW|O_CLOEXEC` descriptor that
  `_CheckpointRestoreAnchor` (`hexctl.py:27469`) keeps until the restore's
  `finally` (`hexctl.py:29359-29377`). For an absent destination there is no
  `.hexaemeron/` to lock until the marker transaction creates one, after `git
  init`, fetch and checkout. `--from` admits a clean top-level Git origin in
  `_checkpoint_restore_origin` (`hexctl.py:27608`) and holds no descriptor.
  The marker transaction, `_checkpoint_restore_marker` (`hexctl.py:27650`),
  `mkdir`s the origin's `.hexaemeron` and exclusively creates `.gitignore` and
  the marker; when the root exists it allows only `.gitignore`, the marker
  and `worktree` (`hexctl.py:27671`) and treats a matching marker as a resume.
  Publication renames the private stage to `<worktree>/.hexaemeron` without
  replacement (`hexctl.py:26926`). Finalization rechecks the closed inventory
  with `exclude_live_lock=False` (`hexctl.py:28272-28289`), so any `lock` in
  the active tree refuses (`hexctl.py:25479-25481`).

Competitors, from the code and the model of section 4 (`m` measured with
real processes in the model, `r` measured against the real controller, `a`
read from the code only):

| # | Competitor | Shared resource | Unexcluded outcome at the base | Source |
| --- | --- | --- | --- | --- |
| C1 | Two archive restores, existing empty destination | the admitted inode from admission to `git init` | both pass admission and both write; in the model the later writer replaces the earlier one's `.git` and refuses at the marker, leaving two restores' bytes | m; #861 step 4 round 4 measured the real loser exiting 2 at `git init` |
| C2 | Two archive restores, absent destination | the same, once one has created it | the creator's `mkdir` wins; the other admits the empty directory during the creator's inspector and both write | m |
| C3 | The loser of C2 removing what it created | the created destination | `finally` `rmdir`s a still-empty created destination another restore has admitted, so that restore later fails its seal | a |
| C4 | Archive restore and `--from` restore of one destination | the origin after checkout | `--from` admits the archive's repository once it is clean and both run the relocation | a |
| C5 | A live restore and a resume through the marker | `.hexaemeron/checkpoint-restore.json` | a same-digest marker reads as a resume, so the resumer runs the transaction beside the live restore; the live one can then refuse after a complete restore | m |
| C6 | Restore and a mutating command (`done`, `record`, `checkpoint archive`, `checkpoint export`, `reset`) on the restored worktree after publication | `<worktree>/.hexaemeron` | the command creates `lock` and appends to the ledger; finalization refuses on the extra `lock` and the changed ledger, leaving active state another writer changed | m |
| C7 | The same command paused in `held_lock`'s absent-root window across publication | the same | the command runs unlocked; locking the stage alone does not close it | m |
| C8 | Restore and `init` on the origin, after the marker | the origin's `.hexaemeron` and breadcrumb | `init` creates `lock`, rewrites `worktree`; the restore's breadcrumb check refuses after publication | m |
| C9 | Restore and `init` on the origin, before the marker | the same | `init` creates the root; the marker transaction refuses "requires an empty fresh origin" with no active state: already a permitted outcome | m |
| C10 | Restore and `init` on the derived worktree before publication | `<worktree>/.hexaemeron` | publication finds the path occupied and refuses before active state | a |
| C11 | A stray `lock` in the origin root, from any mutating command naming the origin while the marker exists | the marker's allowed set | it stays after that command dies at `load_state`, and every later resume refuses "requires an empty fresh origin" | a |
| C12 | `verify`, `status`, `next` on the worktree during finalization | the active tree | `verify` stages `checked-design-evidence-*` under the state root (`hexctl.py:8506`) and `next --brief-out` can write there (`hexctl.py:31865-31880`); the closed-inventory recheck may refuse, leaving assumption 2's residue | a |
| C13 | `checkpoint inspect --scratch <destination>` | the destination | `_checkpoint_inspect_scratch` accepts an existing directory (`hexctl.py:30213`) and writes into it, taking no lock | a; outside, assumption 1 |
| C14 | Two restores of one archive into two destinations | none on disk | both succeed; two live copies of one run are #865 and #864's question | a; non-goal |

### 2.2 Merged pull requests

The last two merged pull requests that changed the restore
(`git log -G '_checkpoint_restore|checkpoint restore' eab25fcd -- hexctl.py`):

- [#2169](https://github.com/wildcat-finance/skills/pull/2169), merged
  2026-11-07 (`eab25fcd`), the #1648 run, with step 2 as `2f22c538`. It bound
  every archive-restore write to the admitted descriptor and left "Room for
  #1649": a lock on that descriptor covers every bound operation. Its
  carryover rows: `archive-restore-concurrency` is `duplicate` of #1649, this
  run, carried as content. `restore-leave-refusal-and-link-form` is #2168 and
  out of scope. `git-absolute-path-window`, `mkstemp-getcwd-path`,
  `linux-git-behaviour` and `destination-interior-writers` stay non-goals
  (section 3.2).
- [#2073](https://github.com/wildcat-finance/skills/pull/2073), merged
  2026-10-04 (`9c5fab69`), replay of restored criteria history. No carryover
  block; nothing it left concerns locking.

### 2.3 Audit history

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root at the base and exited 0, with 128 sources at
`committed=match`, so every synopsis is a verified view.

In-scope sources were chosen by a case-insensitive scan for `checkpoint
restore`, `_checkpoint_restore`, `restore --archive`, `restore destination`,
`held_lock`, `flock`, `run lock` and `MUTATING` over `audit/rounds/*.md`,
`audit/AUDIT.md` and `plugins/*/audit/AUDIT.md`. Only grep-selected lines of
each source were read, never a whole file or a synopsis body. `Covered`, `Not
checked` and `Elenchus verdict` were not reviewed beyond those lines.

| Source | Read | Bearing |
| --- | --- | --- |
| `audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md` | source by grep: lines 409, 429, 447, 465, 473, 483 | Step 4 round 3 lead: `cmd_checkpoint_restore` absent from `MUTATING`, two archive restores naming one empty directory both pass admission, the absent case serialised by `os.mkdir` alone. Round 4 measured one interleaving (loser exit 2, "could not initialise the destination", winner's tree with no marker) and named it "not a serialisation proof". Section 11 of that study declines any operating-system lock claim. Rounds 5 to 7 carry the lead unchanged |
| `audit/rounds/fiat-1648-keep-archive-restore-bound-to-its-admitted.md` | source by grep: lines 5, 15, 47, 63 | `lock-composition` reviewed at each round; S2-R1-01 (verify's staged copy under the worktree state root, fixed `fe4b261a`); round 2 lead (2) a SIGKILL at each seam left the marker and disposable root in the admitted directory |
| `audit/rounds/fiat-1345-route-a-zero-decision-and-gate-the-line-tha.md` | source by grep: lines 84, 90-92, 99, 113-115 | `held_lock`'s teardown: unlink under the flock, then `rmdir`; two inits both set `root_was_absent` and exclusion still holds because only the flock winner reaches the teardown; the "went away" refusal (`8b176610`) |
| `audit/AUDIT.md` | source by grep: lines 8261-8268, 13728-13731 | the origin keeps `.gitignore`, the kernel lock and the breadcrumb (ADR-012); `held_lock`'s directory creation is init-only |
| `audit/rounds/fiat-1944-...`, `fiat-1273-...`, `fiat-1135-...`, `fiat-1264-...`, `fiat-363-...`, `fiat-859-...`, `fiat-2042-...`, `fiat-556-...`, `fiat-857-...` (all under `audit/rounds/`) | grep match lines only | a moved line number, a version-bump surface, or "mutating" in another sense; no lock or destination finding |

## 3. Constraints and non-goals

### 3.1 Starting point and toolchain

- Starting commit `eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797` (merge of #2169,
  2026-11-07). Driving controller: hexaemeron 1.6.107, `fiat-v6.88.1`.
- Python 3.14.6, stdlib only; Git 2.50.1 (Apple Git-155).
- Platform facts, `python3 .hexaemeron/design/probe.py platform`:

| Fact | Darwin 25.5.0 | Linux 6.8.0 container |
| --- | --- | --- |
| `flock(LOCK_EX)` on an `O_RDONLY\|O_DIRECTORY` descriptor | yes | yes |
| a second open of the same directory, same or other process | blocked, `EAGAIN` | blocked, `EAGAIN` |
| POSIX `lockf` write lock on a directory descriptor | `EBADF` | `EBADF` |
| a lock on a directory follows it across `rename`; a new directory at the old name is free | yes; yes | yes; yes |
| a lock on a file follows its parent's `rename` (stage to `.hexaemeron`) | yes | yes |
| holder killed with SIGKILL releases the lock | yes | yes |
| holder killed while a child it started is alive: `O_CLOEXEC` descriptor released; inherited descriptor still held | released; held | released; held |

  Network filesystems are not measured. Linux emulates `flock` over NFS with
  byte-range locks, which need a writable descriptor, so a directory lock
  there is expected to fail; the design refuses on any `flock` error other
  than contention.

### 3.2 Non-goals

- Lineage (#865) and the external acceptance fence (#864), including two
  restores of one archive into two destinations (C14).
- The three #2168 leads: `leave()` hiding a failed `fchdir`, the
  `repository_root` refusal sentence, and the relative `gitdir:` test.
- #1648's stated residue: Git's absolute-path window, the `mkstemp`
  `getcwd()` path, Linux Git behaviour, and writers inside the admitted
  directory.
- Locking `status`, `next` or `verify` (assumption 3), and any writer that
  takes no `hexctl` lock (C13).
- Waiting for a lock. Every acquisition is non-blocking; a contended one
  refuses.
- Do not touch `~/Projects/fiat-checkpoints`.

### 3.3 Repository traps the runbook carries

- Version surfaces for any `hexctl.py` change: one `fiat` generation row in
  `plugins/hexaemeron/skills/fiat/EVOLUTION.md` through a runbook
  `version-relations` block
  (`fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base`),
  with its `- Current version:` line; `metadata.version` in
  `plugins/hexaemeron/skills/fiat/SKILL.md`; the new Fiat version appended to
  `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` (`hexctl.py:488-544`); the
  package version above 1.6.107 and above every ref's claim in
  `plugins/hexaemeron/.claude-plugin/plugin.json`,
  `plugins/hexaemeron/.codex-plugin/plugin.json`,
  `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json`;
  the pins `tests/test_version_propagation.py:47`,
  `plugins/hexaemeron/tests/test_phylax_model_proxy.py:5684` and
  `tests/test_evolution_contract.py:418,424`.
- Digest pins, by full SHA-256 at the base (`git grep -F <sha256> eab25fcd`):

| File | SHA-256 at base | Pinned in |
| --- | --- | --- |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `0f0784474a7ed2f97f6741a529fcc9d387c8d16ded93d96bd33a79f97815dcb1` | `tests/promise_machine_coverage.json` (1 site) |
| `plugins/hexaemeron/skills/fiat/SKILL.md` | `5343c93f86a34b4e9fe90f278f30f3e14b857dbc5046690e4d1e5d9ef0592247` | `tests/fixtures/agent-instruction-v1/manifest.json`; `fiat-study-runbook-phase/compact.wai`, `model.json`, `source-spans.json` |
| `plugins/hexaemeron/skills/fiat/EVOLUTION.md` | `17a6efbc9670c7c48a6b0840405c805f84448f9393225e746c94713011ca6b7f` | `tests/fixtures/promise-machine/runtime/fiat-final-integration.json` (4 sites) |
| `plugins/hexaemeron/tests/test_hexctl_checkpoint.py` | `5a5adf285c76449216bc5163aac33907a2c2b394557e64946da1beb9b52811a9` | `fiat-controller-checkpoint.json` runtime fixture and `tests/promise_machine_coverage.json` (11 sites); do not edit |
| `plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py` | `238105acf35e412fabb8e3267c63504312683a801dd1c31659d045fda505650f` | `fiat-checkpoint-archive.json`, `tests/promise_machine_coverage.json`, `docs/fiat-1648-archive-restore-binding/study.md` (12 sites); do not edit |
| `references/checkpoint-archive.md`, `references/controller-checkpoint.md`, `test_checkpoint_restore_binding.py`, `test_disposable_git_signing.py`, the four version JSON files, `test_phylax_model_proxy.py`, `test_version_propagation.py`, `test_evolution_contract.py`, `tests/check-map-v1.json`, the #1648 decision draft | (no hit) | none |

  Downstream: `docs/promise-machine/obligation-gates/evaluation-run.json`
  `tree_sha256` and the integration projection, the portable runtime copy
  (`python3 scripts/portable_promise_machine.py sync`) and both Horos scans.
  `INTEGRATED_CONTROLLER_SHA256` exists only in audit prose at the base.
- `plugins/hexaemeron/tests/test_hexctl.py` is 261,346 of 262,144 bytes: new
  tests go in the new module. New Hexaemeron test method names are at most 60
  characters (`tests/test_hexaemeron_manifest_headroom.py`). A module that
  builds disposable Git history with commits joins `FIXTURE_COMMIT_MATRIX` in
  `plugins/hexaemeron/tests/test_disposable_git_signing.py`.
- `test_restore_rejects_unmanifested_lock_before_marker`
  (`test_hexctl_checkpoint.py:1521`) requires a `lock` inside a capsule to
  refuse. Only the active-tree recheck may exclude the live lock; the capsule
  and stage snapshots stay strict.
- Gates run with `FORCE_COLOR` unset and
  `CHECKPOINT_COSIGN=~/.claude/tools/bin/cosign-3.1.3-darwin-arm64` for
  `run_tests.py`. Runbook Exit lines put only real gate commands in code
  spans; P008 reads every Exit code span as a command.
- An audit pull request whose base already carries the package bump fails
  `invariants` on `plugin-release`. That is a stacking artefact of the step
  layout, expected and not fixed.
- A `.hexaemeron/design/*.py` copy committed under `docs/` enters the
  `lint-phylax` walk; both pass Phylax and Ephoros now.

### 3.4 Boundaries

- Always: both test suites and `run_checks.py` before a commit; Imprimatur on
  the study, runbook, references and decision draft; every lock acquisition
  non-blocking; every lock descriptor `O_CLOEXEC`.
- Ask first: a class in `CHECKPOINT_ARCHIVE_REFUSALS`; locking `status`,
  `next` or `verify`; a blocking or waiting acquisition; editing
  `test_hexctl_checkpoint.py` or `test_hexctl_checkpoint_archive.py`.
- Never: remove a destination this restore does not hold the lock on; unlink a
  lock file this process did not create; claim exclusion against a writer
  that takes no `hexctl` lock; edit a receipted audit record.

## 4. Design options

### 4.1 Candidates

1. `mutating-set`. Add `cmd_checkpoint_restore` to `MUTATING`; `held_lock`
   unchanged. Trade: one line, and the issue's own warning applies. It locks
   nothing for a fresh destination, and on a resume it creates `lock` in the
   origin root, which the marker's allowed set refuses.
2. `destination-kernel-lock`. Right after admission, create
   `<destination>/.hexaemeron/lock` through the admitted descriptor, `flock`
   it, re-scan, and hold it to the end, so `init` and every mutating command
   naming the origin contend on the ordinary run lock. The worktree's lock is
   carried in the stage (below), and the absent-root window is closed. Trade:
   one lock object for the origin, but the destination stops being empty
   before `git init`, so a restore killed in the inspector leaves
   `.hexaemeron/` and a retry refuses `destination-occupied`.
3. `exclusive-entry`. Exclusively create one entry relative to the admitted
   descriptor, record the holder's pid, re-scan, and reclaim the entry when
   its pid is dead; stage lock and window fix as above. Trade: no kernel lock
   on the destination, but a crash leaves the entry, liveness by pid lets two
   reclaimers both proceed, and `init` takes a different lock.
4. `admitted-fd-flock`. `flock` the admitted descriptor before the emptiness
   scan (archive) or an `O_NOFOLLOW` origin descriptor before the clean check
   (`--from`); take the origin's run lock inside the marker transaction; carry
   the worktree's run lock in the private stage through publication; close
   the absent-root window. Trade: three non-blocking acquisitions per restore
   and two relocation rule changes (assumption 6). The destination gains no
   entry before `git init`, and every lock is the kernel's.

Considered and not carried: a lock keyed on the destination's parent, which
serialises unrelated restores in one parent and does not follow a renamed
destination; a lock keyed on the imported run identity, which would need a
lock directory outside every destination and excludes C14, which is not a
local conflict but #865 and #864's question; POSIX `lockf` on the directory,
which both kernels refuse with `EBADF`.

### 4.2 Criteria

Every selection cell runs the model in `.hexaemeron/design/probe.py`. It is
not `hexctl.py`. Each actor is a separate process (`probe.py actor`) running
one of four operations: an archive restore, a resume of an existing origin,
a mutating command with `held_lock` as at the base, and `init` with the same.
An actor told to pause at a named point creates `<role>.<point>.ready` and
waits for `<role>.<point>.go`. The parent releases or kills an actor only
after seeing its ready file. Order is therefore fixed by the files, not by
timing, and an unanswered barrier exits 97 and fails the probe. The model
restore writes stand-in `.git` files, publishes the relocation marker, creates
the worktree, writes and publishes the stage, rechecks the closed inventory
and ledger, creates the breadcrumb and retires the marker. Each candidate
runs its own exclusion in its best form: a loser removes only what it
created, and a lock file the restore created is unlinked while still held.

Selection gates (`boolean`, `equals true`, block `design-lock`):

- `uncontended-restore-completes` (compatibility, protasis): an absent and an
  existing empty destination each restore to the complete layout; a full one
  refuses unchanged.
- `competing-restores-one-winner` (correctness, phylax): C1 and C2, ordered
  three ways (SC-1). Pass when one exits 0, one exits 1, and the destination
  holds exactly the winner's restore.
- `live-resume-refused` (correctness, phylax): C5 with a restore paused after
  its marker.
- `killed-holder-resumes` (recovery, elenchus): SIGKILL after the marker,
  then a resume completes.
- `killed-before-write-readmits` (recovery, elenchus): SIGKILL during the
  inspector of a created destination, then a new restore into it completes.
- `imported-state-excluded` (correctness, phylax): C6 and C7. Pass when the
  command refuses, the ledger is unchanged, and the restore completes.
- `origin-init-excluded` (correctness, phylax): C8 must end with `init`
  refused and the restore complete; C9 must end with one refusal and no
  active state from a refused restore.

Selection metrics (all `minimise`):

- `concurrent-holders-after-crash` (correctness, phylax, count): a restore is
  killed after its marker; two resumers each pause just before their
  acquisition step (for `exclusive-entry`, after reading the dead holder) and
  are released one at a time. Value: actors holding the exclusion at once.
- `lock-acquisitions-per-restore` (time, metron, count): `flock` calls and
  exclusive creates in one uncontended restore.
- `entries-left-after-early-kill` (space, metron, count): entries a restore
  killed during the inspector leaves in its destination.

Conformance gates (`boolean`, `equals true`, block `integration`):
`restore-contention-guarded` (correctness, elenchus),
`imported-state-guarded` (correctness, elenchus), `killed-restore-recovers`
(recovery, elenchus), `existing-restores-unchanged` (compatibility,
protasis). Section 4.4 names their resolvers.

### 4.3 Results and selection

Every selection report is a closed `protasis-design-report/v1` object with
exit 0 under `.hexaemeron/design/reports/selection/`, produced on 2026-11-07
by `python3 .hexaemeron/design/probe.py select --candidate <id> --criterion <id> --out <path>`
(probe SHA-256 `53f307d1f7b4b40d569d48efb51d58c660a93fd5a91f0afedff4198684c51a5d`).

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

The whole grid gave identical values in three runs on Darwin and one in the
Linux container.

Observed facts behind the table:

- `mutating-set` passes `live-resume-refused` by accident: the resumer's
  `held_lock` creates `lock` in the origin root, and the marker's allowed set
  then refuses it. The same accident fails `killed-holder-resumes`: a resume
  after a kill refuses for good. In C6 it appends to the ledger and the
  restore refuses with that ledger in place.
- `destination-kernel-lock` and `exclusive-entry` leave `.hexaemeron/`,
  `.gitignore` and `lock` (3 entries), or the entry (1), in a destination
  killed during the inspector, so a retry refuses `destination-occupied`
  where the base admits it.
- `exclusive-entry` lets two resumers proceed after a crash: both read the
  same dead pid, and the second unlinks the first one's new entry. `init`
  takes the origin's run lock, which this candidate never holds, so C8
  rewrites the breadcrumb and the restore refuses after publication.
- C7 is reachable at the base: the command paused in the absent-root window
  ran unlocked after publication. Only a fix in `held_lock` closes it; a
  stage lock alone does not.
- Real `hexctl` at the base: two processes held
  `held_lock(<empty dir>, "cmd_checkpoint_restore")` at once (section 1).

Selection. `mutating-set` fails four gates, `destination-kernel-lock` one,
`exclusive-entry` two. `admitted-fd-flock` passes all seven and is the one
survivor, so the non-dominated frontier is one candidate and the rule is
`unique-frontier`. The record is `.hexaemeron/design-evidence.json`, SHA-256
`c727d18a199026f12914c4fd22289e4dab5d66a8a57e1fe6647b2c6c5958cfc2`. The
Protasis checker exits 0 at `design-lock`, `step:1`, `step:2` and `step:3`,
and refuses `integration` with D008 until the four conformance reports exist.

The trade named: `admitted-fd-flock` costs three non-blocking acquisitions
per restore, the most of the four, and changes two relocation rules: the
marker's allowed set and the live-lock exclusion in the active-tree recheck.
In return the destination gains no entry before `git init`, a crash releases
every lock, and each competitor in section 2.1 meets a lock it already
honours.

### 4.4 The chosen design

**L1, the directory lock.** In `_checkpoint_restore_archive_destination`,
`fcntl.flock(descriptor, LOCK_EX | LOCK_NB)` runs right after the no-follow
`os.open` and before `fstat`, the `realpath` check and `scandir`. Contention
refuses `destination-occupied`. A call that loses the lock never removes the
destination, even one it created (C3); a call that holds it keeps today's
`rmdir`-only cleanup. The anchor keeps that descriptor, so the lock lasts
until the restore's `finally` closes it. For `--from`,
`_checkpoint_restore_origin` opens the origin `O_RDONLY|O_DIRECTORY|
O_NOFOLLOW|O_CLOEXEC`, locks it, then runs its `realpath`, top-level and
clean checks, and `cmd_checkpoint_restore` holds the descriptor to the end.
Both modes lock the same object, the origin directory's inode, so C1, C2, C4
and C5 meet one lock.

**L2, the origin's run lock.** Inside `_checkpoint_restore_marker`, before
the root's names are read: a fresh root is `mkdir`ed as today and `lock` is
created in it exclusively; an existing root has `lock` opened
`O_CREAT|O_NOFOLLOW` and checked regular with one link. Either way the
restore takes `flock(LOCK_EX|LOCK_NB)` and writes `held_lock`'s holder JSON
with `command` `cmd_checkpoint_restore`, so a refused `init` or other command
names the restore. The allowed set becomes `.gitignore`, the marker,
`worktree` and `lock`. This closes C8 and C11; C9 keeps its permitted
outcome.

**L3, the worktree's run lock.** After the stage's own inventory check and
before `_checkpoint_fsync_directories` and publication, the restore creates
`lock` in the stage exclusively through the stage descriptor, locks it and
writes the holder. Publication renames the stage, and the lock goes with it
(measured on both kernels), so from the first instant `<worktree>/.hexaemeron`
exists its `lock` is held. `_checkpoint_restore_opaque_evidence` excludes a
root-level, regular, single-link `lock`, which is the same rule
`checkpoint export` applies. The capsule and stage snapshots stay strict. An
interrupted-publication retry opens and locks the existing worktree `lock`
before its finalization reads. This closes C6 and C10.

**L4, the absent-root window.** In `held_lock`, a non-init command that finds
no state root refuses at once through the same missing-state message
`load_state` prints, which moves to one shared helper. If the state file
exists by then, the root appeared after the `isdir` check, and the command
takes the lock like any other. Every path now either refuses or locks. This
closes C7 and changes no message (assumption 7).

**Release.** Every lock descriptor is `O_CLOEXEC`, so no Git child holds it
after the restore dies (measured). On every exit the restore unlinks each
lock file it created while still holding it, as `held_lock`'s teardown
already does, then truncates and unlocks the rest, then closes. An
uncontended restore therefore leaves exactly today's bytes: no `lock` in the
origin root and none in the worktree's state root. SIGKILL leaves lock files
with stale holder JSON; the kernel has released the locks, the allowed set
admits `lock`, and `read_live_holder` already ignores a dead pid.

**Order and deadlock.** L1, then L2, then L3, each `LOCK_NB`. No acquisition
waits, so no cycle can form.

**Refusals.** Admission contention: `destination-occupied`. Any other
contention: `die("checkpoint restore destination is held by another hexctl
command", 1)`. A `flock` error other than contention (for example a
filesystem without `flock`) refuses through the same sentence before any
write.

**Conformance resolvers,** run from the run worktree before the final
`done merge-step` checks `integration`:

```text
python3 .hexaemeron/design/probe.py conform --candidate admitted-fd-flock --criterion <criterion> --root . --out .hexaemeron/design/reports/conformance/admitted-fd-flock-<criterion>.json
```

Each runs `python3 -m unittest discover -s plugins/hexaemeron/tests -t plugins/hexaemeron/tests -p <module> -k <pattern>`
with `FORCE_COLOR` removed, and requires exit 0, at least one test run and no
skip. `restore-contention-guarded` runs `test_checkpoint_restore_concurrency.py`
with `-k one_winner`, `-k live_resume` and `-k origin_init`;
`imported-state-guarded` with `-k imported_state`; `killed-restore-recovers`
with `-k killed`; `existing-restores-unchanged` runs
`test_checkpoint_restore_binding.py` with `-k test_`, `test_hexctl_checkpoint.py`
with `-k restore` and `test_hexctl.py` with `-k TestRunLock`. The signed
archive fixture skips without `gpg`, which fails the cell.

**Test determinism.** The new module restores the existing signed archive
fixture through real `hexctl` processes. Each competitor runs a short
wrapper that loads `hexctl.py` by path, wraps one named function so that
crossing it creates a ready file and waits for a go file, then calls
`main()` with the competitor's argv. The seams are the inspector
(`_checkpoint_inspect_carrier_verified`), admission before the lock, the
marker transaction's return, the atomic publish's return, and the
missing-state check inside `held_lock`. The test starts, releases or kills
each process only after seeing its ready file, and a bounded wait fails the
test rather than reordering it. No sleep orders anything.

### 4.5 Step outline for the runbook

1. Scaffold. Commit copies of the study, runbook, design record, probe,
   builder and the 40 selection reports under
   `docs/fiat-1649-restore-concurrency/`, the numberless decision draft named
   in section 12, and a root scaffold test that pins each copy. No
   `plugins/` path changes, so no package bump.
2. Controller. L1 to L4, the fixed sentence, the cleanup rule, the
   live-lock exclusion and the allowed set in `hexctl.py`; the operator rule
   in `checkpoint-archive.md` "Restore transaction" and the relocation
   paragraph of `controller-checkpoint.md`; the new module
   `plugins/hexaemeron/tests/test_checkpoint_restore_concurrency.py`; its
   `FIXTURE_COMMIT_MATRIX` row if it commits; the version bump, generation
   row and digest cascade, walked once.
3. Demonstrate. Run the four conformance resolvers and the module, and
   commit their output to `docs/fiat-1649-restore-concurrency/demonstration.md`.
   No `plugins/` path changes.

## 5. Risk register seed

```risk-register
lock-before-scan | archive admission between the no-follow open and the emptiness scan | flock on the admitted descriptor precedes fstat, the realpath check and scandir, so no restore admits a directory another holds
loser-never-removes | the created-destination cleanup after a lost lock | a restore that did not obtain L1 never rmdirs the destination, even one its own mkdir created
from-origin-lock | the --from origin admission | the origin descriptor is no-follow, locked before the clean check, and held to the end of the restore
marker-lock | the marker transaction in the origin's state root | L2 is created or opened no-follow, regular with one link, locked before the names are read, and the allowed set gains only lock
stage-lock-published | the private stage and its rename to the worktree state root | lock is created in the stage and held before the rename, so the published state root never exists without a held lock
live-lock-exclusion | the active-tree closed-inventory recheck | only a root-level regular single-link lock is excluded; the capsule and stage snapshots stay strict and test_restore_rejects_unmanifested_lock_before_marker still passes
absent-root-window | held_lock with no state root for a non-init command | every path refuses or locks; no mutating command reads state it did not lock; messages are unchanged
nonblocking-only | every acquisition | LOCK_NB everywhere, so no wait and no lock-order cycle
cloexec-locks | lock descriptors across Git and gpg children | each is O_CLOEXEC and none is passed to a child, so a dead restore holds nothing through a live child
release-and-unlink | lock files at every exit | only files this process created are unlinked, each while still held; an uncontended restore leaves today's bytes
killed-mid-restore | SIGKILL at any seam | every lock is released by the kernel, the residue is the reference's, and a resume completes
holder-metadata | the holder JSON the restore writes | it carries pid, command and ts only, no path, and held_lock's refusal names the restore
refusal-text | contention and flock failure | destination-occupied at admission, one fixed path-free sentence elsewhere, exit 1, no new class
reader-residue | verify, status and next during finalization | they stay lock-free; a refusal they cause leaves marker plus active state, which a retry finalizes
from-mode-unchanged | uncontended --from restores | same bytes, refusals and receipts as at the base
binding-unchanged | the #1648 anchor, seals and fixed moved sentence | every binding case still passes and the lock adds no name-resolving write
test-determinism | the competing-process tests | ordering comes from ready and go files at named seams, never from sleeps; a bounded wait fails the test
version-surface | the hexaemeron package version and the fiat ledger row | above the PR base and every ref's claim on all surfaces; CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS gains the new fiat version; the row comes from the version-relations block
digest-cascade | fixtures pinning hexctl.py, fiat SKILL.md and EVOLUTION.md | the step re-pins its cascade and the root and Hexaemeron suites pass at its exit
test-ceiling | test_hexctl.py at 261346 bytes and the 60-character name cap | no new test lands there and every new name fits
```

## 6. Glossary seeds

- L1 is the exclusive `flock` on the origin directory's descriptor, admitted
  (archive) or opened (`--from`), held for the whole restore.
- L2 is the restore's hold on the origin's ordinary run lock,
  `<origin>/.hexaemeron/lock`, from the marker transaction to the end.
- L3 is the restore's hold on the worktree's run lock, created in the private
  stage and published with it.
- The absent-root window is the interval in which `held_lock` has found no
  state root and the command has not yet read state.
- A competitor is any `hexctl` process naming the restore's origin,
  destination or derived worktree while the restore runs.
- A permitted outcome is one of the three in assumption 2.
- Partial active state is controller state a restore published and another
  writer changed, two restores' bytes in one destination, or active state
  with neither marker nor completed restore.

## 7. Sources

- [`hexctl.py` at the base, `MUTATING` and `held_lock`](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L2860-L3047)
- [`hexctl.py`, `main`](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L33698-L33716)
- [`hexctl.py`, anchor, origin and marker](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L27469-L27752)
- [`hexctl.py`, relocation transaction](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L28491-L28834)
- [`hexctl.py`, archive admission and restore](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L28836-L29377)
- [`checkpoint-archive.md`, restore transaction](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md#L327-L379)
- [`controller-checkpoint.md`, relocation transaction](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md#L193-L257)
- [#861 audit record, step 4 leads](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md#L409)
- [#1345 audit record, `held_lock` teardown](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/audit/rounds/fiat-1345-route-a-zero-decision-and-gate-the-line-tha.md#L84)
- [#2169](https://github.com/wildcat-finance/skills/pull/2169),
  [#2073](https://github.com/wildcat-finance/skills/pull/2073),
  [#2168](https://github.com/wildcat-finance/skills/issues/2168),
  [#865](https://github.com/wildcat-finance/skills/issues/865),
  [#864](https://github.com/wildcat-finance/skills/issues/864)
- [Linux `flock(2)`](https://man7.org/linux/man-pages/man2/flock.2.html),
  [macOS `flock(2)`](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html),
  [Python `fcntl.flock`](https://docs.python.org/3.14/library/fcntl.html#fcntl.flock),
  [PEP 446, non-inheritable descriptors](https://peps.python.org/pep-0446/)
- The #1648 package `docs/fiat-1648-archive-restore-binding/` and its draft
  `docs/decisions/drafts/bind-archive-restore-to-its-admitted-directory.md`
  (consequence 6: room for this lock).
- The probe, builder, record and 40 selection reports under `.hexaemeron/`.

## 8. Signals, and the questions behind them

[Ephoros](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal carries. Restore runs when an operator or driver invokes
it, not unattended, so there is no alert. Two questions:

1. "Why did my restore or command refuse?" Answered on stderr with exit 1:
   `destination-occupied` at admission, the fixed held sentence elsewhere,
   and, for a competitor, `held_lock`'s existing message naming pid
   `cmd_checkpoint_restore` and its start time from the holder JSON.
2. "Is a restore still running here?" A live restore holds a lock a
   non-blocking probe can see; after a kill the holder JSON names a dead pid,
   which `read_live_holder` already treats as no holder.

No new event, metric or ledger entry: a refused restore writes no ledger.

## 9. Boundaries, per capability

[Phylax](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the boundary list and controls.

| Boundary | What is worth taking | Control |
| --- | --- | --- |
| The restore's destination or origin | a second restore writing into it, or removing it | L1 before the scan; a loser never removes |
| The origin's state root and breadcrumb | `init` or any mutating command rewriting them mid-restore | L2 and the allowed set |
| The derived worktree's state | a mutating command changing imported state before the restore finishes | L3 published with the stage; L4 |
| Lock files themselves | a symlink or hard link planted at `lock` | no-follow open, regular, one link, as `held_lock` already checks |

Defended: concurrent `hexctl` processes of the same account. Not defended,
stated: writers that take no `hexctl` lock (C13, Git, editors, `rm`); root
and administrators; a process that deletes or replaces a lock file and then
races (advisory locks bind only cooperating callers); `flock` on filesystems
that lack it, which refuses; and everything #1648 already lists as outside
its binding.

## 10. The budget, or its absence

[Metron](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/metron/SKILL.md)
owns budgets. None new: `checkpoint.archive.restore_wall_ms`, 20,000 ms in
`plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json`, is
unchanged and no performance claim is made. The added cost is three
non-blocking `flock` calls, two exclusive creates, two holder writes and two
unlinks per restore, against Git children that dominate its time.

## 11. The fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns the triage order and the guard rule.

What stops the restore: any contended or failed acquisition, a lock path that
is not a regular single-link file, and every existing refusal. Each exits
before the operation the lock guards. A competitor that meets a held lock
stops before it reads or writes state.

Guard convention: each SC-1 to SC-5 case is a test in
`test_checkpoint_restore_concurrency.py` that orders real processes with
ready and go files at a named seam. On the parent commit the C1, C2, C5, C6,
C7 and C8 cases fail, which is the controller step's counterfactual; the
step's audit records it. Test names carry `one_winner`, `live_resume`,
`origin_init`, `imported_state` or `killed` so the conformance resolvers
select them, and stay within 60 characters.

## 12. Decisions and their homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/eab25fcdce2ca4424ab9aa9f778bf29ca6ad9797/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record.

1. Exclude competing restores with a kernel lock on the origin directory's
   descriptor, the origin's and the worktree's ordinary run locks, and a
   closed absent-root window, rather than `MUTATING` membership, a lock
   created at admission, or an exclusive entry. Expensive to reverse: it
   fixes the marker's allowed set, the live-lock exclusion in the active-tree
   recheck, and what every competitor sees. Record:
   `docs/decisions/drafts/exclude-competing-checkpoint-restores.md`,
   numbered at the merge that lands it; Step 1 creates the draft.
2. Refuse contention with `destination-occupied` at admission and one fixed
   `die(..., 1)` sentence elsewhere, adding no class to the closed table.
   Same record.
3. The Fiat generation row lives in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
   bound by the runbook's `version-relations` block.
4. The operator rules live in the "Restore transaction" section of
   `plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`, which
   today lists "two concurrent restores" as not defended, and the
   "Relocation transaction" section of
   `plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | admitted-fd-flock
record | docs/decisions/drafts/exclude-competing-checkpoint-restores.md
```
