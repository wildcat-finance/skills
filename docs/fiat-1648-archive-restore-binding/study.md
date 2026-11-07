# Study: keep archive restore bound to its admitted destination

Task: [wildcat-finance/skills#1648](https://github.com/wildcat-finance/skills/issues/1648)
(`Fiat-Required: 1`, carryover `none`). Surveyor: `fiat-1648-study-surveyor`.
Target: this repository at `main` `076add19439c163be266374eb671a1c9a234c12c`,
run branch `fiat/1648-keep-archive-restore-bound-to-its-admitted`. Every
`hexctl.py:N` below is a line of
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at that commit (33,363
lines). The issue cites `audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md`
at `485a6c81`; every location is re-derived here at the starting commit.

Assuming, unless corrected:

1. The defended actor is a principal who can write the destination's parent
   directory and cannot write inside the admitted directory. It may rename the
   destination away and put a directory, a symlink or nothing at the name, at
   any moment after admission, any number of times.
2. A process running as the restoring account is outside the security claim.
   It can already write inside the admitted directory, change the controller,
   its scratch root or its environment, and trace `hexctl` or `git`. Against
   such a process the binding is integrity against accident (a concurrent tool
   moving the directory), not authority. Root and administrators are outside
   it too.
3. "Bound to the admitted destination" means every write the controller
   performs itself resolves through the admitted descriptor or the working
   directory fixed to it, and never through the destination's name. Git is a
   separate program: binding a Git child means it starts in the admitted
   directory and receives only relative path arguments. Git's own conversion
   of those into absolute paths is outside what the controller can bind
   (section 4.3 measures it), so each Git child is bracketed by identity
   checks and the residue is stated in section 9, not hidden.
4. A restore that finds the name no longer naming the admitted directory
   refuses. It never records controller state naming a path that does not
   name the inode it wrote, and it never tears down the admitted directory's
   contents.
5. The refusal for a moved destination is one fixed, path-free sentence
   through `die(..., 1)`, the family the relocation transaction already uses
   for its own identity checks, not a new class in the closed table. Section
   12 records why; the alternative is a 25th class, which moves three
   existing pins.
6. No known-failure inventory. S4-R1-06 is this run's own subject; its guard
   is the run's deliverable and the `replacement-regression-guarded`
   conformance cell holds it. If the driver wants Fiat's inoculation path for
   it instead, the study needs the inventory block before `done runbook`.
7. The interpreter is the `.python-version` value, 3.14.6, with stdlib
   `unittest`. Git is `/usr/bin/git` 2.50.1 (Apple Git-155) on Darwin 25.5.0
   arm64. Linux primitives were measured in a `python:3.14.6-slim-trixie`
   container (kernel 6.8.0) that has no Git, so Linux Git behaviour is not
   measured by this study.

The study proceeds on these unless corrected. Rejecting assumption 3's Git
reading leaves no in-place candidate that passes (section 4.3). Rejecting
assumption 5 adds a class to the reference and moves the three pins listed in
section 3.3.

## 1. Problem statement

`checkpoint restore --archive` admits its destination in
`_checkpoint_restore_archive_destination` (`hexctl.py:28568`): absent (created
`0700`) or an empty, non-symlink directory, checked through an `O_NOFOLLOW`
descriptor with `fstat` and `scandir`. Every later operation in
`_checkpoint_restore_from_archive` (`hexctl.py:28747`) and the shared
relocation transaction `_checkpoint_restore_relocate` (`hexctl.py:28239`)
resolves the destination by its absolute name: `git init` at
`hexctl.py:28819` or `git clone --bare --local` at `hexctl.py:28807`, capsule
extraction, `git checkout`, the origin URL, the relocation marker, the worktree
home, `git worktree add` at `hexctl.py:28377`, the private stage at
`hexctl.py:28400`, active-state publication, breadcrumb, marker retirement,
removal of the capsule root at `hexctl.py:28998` and removal of a created
destination at `hexctl.py:29022`. `bounded_probe` starts every Git child with
`cwd=os.path.realpath(base_dir)` (`hexctl.py:22878`), which resolves the name
again. The admission descriptor is held unused until the `finally` closes it.

A writer on the parent can therefore swap the name between admission and any
later operation, and the restore then writes into the replacement: for a swap
before `git init`, the whole restore lands there and the admitted directory
stays empty. The #861 audit (S4-R1-06) repaired the docstring's stronger claim
and left the window open, unguarded, because closing it "needs `dir_fd`
threaded through every later operation".

Who it is for: an operator, or the driver agent acting for one, restoring a
Fiat run from an archive or directory checkpoint into a directory whose parent
another principal can write.

A working prototype means: after admission, every controller-performed write,
interruption residue and cleanup operation stays on the admitted inode; every
Git child starts in it with relative arguments and is sealed before and after;
a name that no longer names the admitted directory at any seal refuses with
nothing written into the replacement; nonempty and symlink destinations still
refuse `destination-occupied`; `--from` restores behave exactly as today.

Demo path. The last step runs the four conformance resolvers of section 4.4
against the built tree from the run worktree and records their output with
the new module's run. The controller is the run tree's `hexctl.py`; the source
command is `python3 .hexaemeron/design/probe.py conform --candidate anchored-cwd --criterion <id> --root . --out <path>`.
Bounded positive observations: an unswapped archive restore still completes
with `verify`, `status` and `next` unchanged; a `--from` restore is unchanged.
Bounded negative observations: a directory or symlink swapped in at each seam
after admission refuses, the replacement holds zero entries, the symlink
target holds zero entries, and the admitted directory holds whatever the
restore had written before the seal; an interrupted restore after a swap
leaves its marker and disposable root in the admitted directory and nothing
in the replacement; the process working directory is restored on every exit
path. The demonstration does not claim race freedom for Git's own absolute
paths (section 9).

Success criteria, each checked by a command:

| id | Criterion | Check |
| --- | --- | --- |
| SC-1 | A destination swapped for an empty directory after admission, at each seam (before `git init`, after the repository exists, after the marker, after `git worktree add`, before publication, before marker retirement), refuses with the fixed sentence and leaves the replacement with zero entries | test names containing `replacement` in the new `plugins/hexaemeron/tests/test_checkpoint_restore_binding.py`; conformance cell `replacement-regression-guarded` |
| SC-2 | The same swaps with a symlink to a sentinel directory leave the sentinel empty and the symlink in place | test names containing `symlink_destination` in the same module; `nonempty-symlink-still-refuse` |
| SC-3 | A nonempty destination and a symlink destination still refuse `destination-occupied`; a symlinked parent is still admitted | `test_restore_from_archive_refuses_non_empty_destination` and `test_archive_restore_accepts_a_symlinked_destination_parent` in `test_hexctl_checkpoint_archive.py`; `nonempty-symlink-still-refuse` |
| SC-4 | An interruption after a swap leaves the relocation marker and disposable root in the admitted directory, nothing in the replacement, no removal of the replacement, and the process working directory restored | test names containing `interrupted` in the new module; `interrupted-restore-stays-bound` |
| SC-5 | `checkpoint restore --from` is unchanged | `python3 -m unittest discover -s plugins/hexaemeron/tests -t plugins/hexaemeron/tests -p test_hexctl_checkpoint.py -k restore` (33 tests, 178.7 s at the base); `from-mode-unchanged` |
| SC-6 | The post-`git init` refusal-class set stays the four the reference names | `test_refusals_after_git_init_are_the_four_in_reference` in `test_hexctl_checkpoint_archive.py` |
| SC-7 | Repository gates stay green at every step exit | `python3 -m unittest discover -s tests`, `CHECKPOINT_COSIGN=<cosign> python3 plugins/hexaemeron/tests/run_tests.py`, `python3 scripts/run_checks.py`, `python3 scripts/promise_machine.py check`, `python3 scripts/plugin_release.py --base <PR base> --head HEAD`, with `FORCE_COLOR` unset |

## 2. Prior art

### 2.1 The code at the base

- Admission, `_checkpoint_restore_archive_destination` (`hexctl.py:28568-28646`):
  resolves the parent with `realpath` (S4-R1-05), `lstat`, `mkdir 0700` when
  absent, `open(O_RDONLY|O_DIRECTORY|O_NOFOLLOW)`, `fstat`, a
  `realpath(destination) == destination` check and `scandir` on the
  descriptor. It returns `(destination, descriptor, created)` and removes a
  directory it created on its own refusals by `rmdir` only (S4-R3-03).
- The archive restore, `_checkpoint_restore_from_archive`
  (`hexctl.py:28747-29022`): admission first, then the inspector into a
  `tempfile.mkdtemp` scratch root, then `git clone --bare --local` (directory
  carrier) or `git init` plus `git fetch <bundle>` (ZIP carrier), capsule
  extraction under `.git/fiat-checkpoint-restore/<outer-sha256>/`, the base
  checkout, `remote.origin.url`, ancestry and ref joins, the relocation
  transaction with a deferred marker (S4-R4-02), identity recompute, marker
  retirement, removal of the capsule root, and a `finally` that closes the
  descriptor, removes scratch and `rmdir`s a created destination.
- The relocation transaction, `_checkpoint_restore_relocate`
  (`hexctl.py:28239-28530`), shared unchanged with `--from`. Several of its
  helpers already open a directory by path and then work through `dir_fd`:
  `_checkpoint_restore_marker` (`hexctl.py:27442`),
  `_checkpoint_restore_prepare_worktree_home` (`hexctl.py:27531`),
  `_checkpoint_retain_criteria_history` (`hexctl.py:27820`),
  `_checkpoint_restore_write_files`, `_checkpoint_restore_breadcrumb`,
  `_checkpoint_restore_retire_marker`, and the publish block, which
  `fchdir`s into the worktree descriptor and renames with
  `_checkpoint_atomic_publish` (`hexctl.py:26887`, `renameat2`
  `RENAME_NOREPLACE` or `renamex_np` `RENAME_EXCL`). Each one compares its
  freshly opened descriptor with the same path,
  `_checkpoint_directory_still_at_path` (`hexctl.py:26594`), never with the
  admitted inode, so a swap before the relocation is consistent with itself
  and passes.
- Subprocesses: `bounded_probe` (`hexctl.py:22833`) runs `Popen(...,
  cwd=os.path.realpath(base_dir))` (`hexctl.py:22878`); `bounded_run`,
  `bounded_tool` and `bounded_git` wrap it.
- The closed refusal table `CHECKPOINT_ARCHIVE_REFUSALS` (`hexctl.py:925`) has
  24 classes; `_checkpoint_archive_refuse` rewrites an unknown class to
  `manifest-mismatch`. `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` starts at
  `hexctl.py:488`; `fiat-v6.87.1` is at `hexctl.py:543`.
- Tests: `CheckpointArchiveRestoreTests` in
  `plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py` (223,753 bytes)
  restores real signed archives through a subprocess. Three tests pin the
  refusal vocabulary to the frozen #861 study
  `docs/fiat-checkpoint-archive-study.md`: the reference table holds exactly
  those 24 classes, `CHECKPOINT_ARCHIVE_REFUSALS` holds exactly those 24, and
  `test_refusals_after_git_init_are_the_four_in_reference` computes, by AST
  closure from the first `"init"` literal in `_checkpoint_restore_from_archive`,
  that exactly `manifest-mismatch`, `ref-disagreement`, `identity-mismatch` and
  `identity-unavailable` are reachable after `git init`.
- Reference: `plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`
  "Restore transaction" step 2 requires the destination "checked through an
  opened descriptor and never through a symlink", and says a killed restore
  "leaves the disposable root and the existing relocation marker, which the
  existing retry rules resume or refuse". `checkpoint-directory.md` defers its
  destination and residue rules to that reference.

### 2.2 Merged pull requests

The last two merged pull requests that changed the restore code
(`git log -G '_checkpoint_restore|checkpoint restore' -- hexctl.py`):

- [#2073](https://github.com/wildcat-finance/skills/pull/2073), merged
  2026-10-04 (`223fff90`), "Replay checkpoint criteria after relocation". It
  added `_checkpoint_retain_criteria_history` inside the relocation. Its body
  has no carryover block and leaves "Published canonical acceptance remains
  pending" for #1378, which is outside this run. Carried as content: the
  criteria retention is one more destination-rooted write the binding must
  cover (section 4.4, table row W5).
- [#1975](https://github.com/wildcat-finance/skills/pull/1975), merged
  2026-09-28 (`769a6383`), Fiat run #1944. It moved which branch a bound run's
  restore checks out. Its carryover rows (#1967 to #1972, two `none`) concern
  gate commands, criteria relocation and test headroom; none concerns the
  destination name. Nothing carried.

The run-level PR of #861,
[#1652](https://github.com/wildcat-finance/skills/pull/1652) (`69827933`),
filed this issue as `destination-name-swap` and #1649 as
`restore-concurrency`. Its `operator-environment` row ("Git inherits the
operator environment ... same-account mutation and hostile operator
configuration remain outside the stated isolation claim") is kept as a stated
non-goal in section 3.2.

### 2.3 Audit history

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root at the base and exited 0: 127 sources, every one
`budget=pass` and `committed=match`, so every synopsis is a verified view.

In-scope sources were chosen by a case-insensitive scan for `checkpoint
restore`, `_checkpoint_restore`, `restore --archive` and `restore destination`
over `audit/rounds/*.md`, `audit/AUDIT.md` and `plugins/*/audit/AUDIT.md`.
Eight match.

| Source | Read | Bearing |
| --- | --- | --- |
| `audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md` | source by grep: lines 358-363, 380-386, 403-409, 424-429, 445-447, 463-465, 483 (Step 4 rounds 1 to 7 finding rows and `Leads not pursued`) | S4-R1-06 (low): open at `b4464fbd`; round 2 "fixed ... as a claim repair with no behaviour change" at `2e28e69c`, "No guard"; every later round's `Leads not pursued` keeps it "open and unguarded because closing it needs `dir_fd` threaded through every later operation". S4-R2-01 (low): a refusal after `git init` leaves the repository; round 4 adds that tearing a destination down by path "inherits S4-R1-06's open name-swap window". S4-R1-04, S4-R3-03: admission creates the destination and removes it by `rmdir` only. S4-R1-05: the parent is resolved, not required to be its own `realpath`. S4-R1-02 (medium): reused readers refuse through `die` outside the closed table. S4-R4-02 (medium): marker retirement deferred past identity. S4-R5-01 (medium): the post-`git init` class set is computed by test. Round 3 and 4 lead: `cmd_checkpoint_restore` absent from `MUTATING`, two concurrent restores both pass admission (now #1649). Round 4 lead: "the restore path holding no parent descriptor where the export sibling `_checkpoint_destination` re-checks parent identity" |
| `audit/rounds/fiat-1944-gate-commands-for-a-repository-with-no-runn.md` | grep lines 96, 112, 128 | leads on which branch a bound run restores onto and criteria replay; no destination finding |
| `audit/rounds/fiat-1273-settle-declared-study-criteria-with-recorde.md`, `fiat-1135-retire-the-shoggoth-cosignature-and-host-au.md`, `fiat-1264-rebind-runbook-amendments-across-a-study-am.md`, `fiat-1345-route-a-zero-decision-and-gate-the-line-tha.md`, `fiat-363-bind-delegated-task-identity-to-step-and-rol.md`, `fiat-859-reinstate-the-wave-delta-distributed-checkpo.md` (all under `audit/rounds/`) | grep match lines only (1 to 3 each) | restore named as a later step, a moved line number, or a version-bump surface (#1264 line 67: restore refuses an unlisted controller version); no destination finding |

Only grep-selected lines of each source were read; no whole file and no
synopsis body was read. `Covered`, `Not checked` and `Elenchus verdict` were
not reviewed beyond the lines named.

## 3. Constraints and non-goals

### 3.1 Starting point and toolchain

- Starting commit `076add19439c163be266374eb671a1c9a234c12c` (merge of #2160,
  2026-11-06). Controller under test: the run tree's `hexctl.py`. Driving
  controller: hexaemeron 1.6.106, `fiat-v6.87.1`.
- Python 3.14.6 (`.python-version`); stdlib only. Git 2.50.1 (Apple Git-155).
- Platform facts, `python3 .hexaemeron/design/probe.py platform`:

| Fact | Darwin 25.5.0 | Linux 6.8.0 container |
| --- | --- | --- |
| `os.supports_dir_fd` | access, chmod, chown, link, lstat, mkdir, mkfifo, mknod, open, readlink, rename, rmdir, stat, symlink, unlink, utime | same set |
| `O_DIRECTORY`, `O_NOFOLLOW` | yes, yes | yes, yes |
| libc `renameat`, `mkdirat`, `unlinkat` | yes | yes |
| `renameat2` (`RENAME_NOREPLACE`) | no | yes |
| `renamex_np`, `renameatx_np` | yes, yes | no, no |
| child started after `fchdir` writes into the admitted inode when the name was swapped | yes | yes |
| `getcwd()` after the swap names the inode's new location | yes | yes |
| `/dev/fd/N` traversable as a directory | no (`Not a directory`) | yes |
| `/proc/self/fd/N` | absent | yes |

### 3.2 Non-goals

- Serialising restore against competing operations, adding restore to
  `MUTATING`, or any lock: #1649. The design must leave room for one (section
  4.4).
- Lineage (#865) and the external fence (#864).
- The `--from` mode's own origin binding. `--from` admits an existing clean
  Git origin through `_checkpoint_restore_origin`; it is untouched here and
  keeps today's path behaviour.
- Ownership or mode of a pre-existing empty destination. Admission does not
  check that the directory belongs to the restoring account or lacks group and
  other write. A principal who can write inside the admitted directory is
  outside the claim (section 9). Proposed carryover row
  `destination-interior-writers`.
- Git's own absolute-path derivation inside one child (section 4.3), and the
  operator's Git environment, hooks and templates (#1652 `operator-environment`).
- Changing the refusal vocabulary's 24 classes, the inspector, the capsule
  reader, or the relocation transaction's marker, retry and refusal rules.
- Do not touch `~/Projects/fiat-checkpoints`.

### 3.3 Repository traps the runbook carries

- Version surfaces for any `hexctl.py` change: a `fiat` generation row in
  `plugins/hexaemeron/skills/fiat/EVOLUTION.md` through a runbook
  `version-relations` block
  (`fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base`),
  the `- Current version:` line, the package version above 1.6.106 and above
  every ref's claim in `plugins/hexaemeron/.claude-plugin/plugin.json`,
  `plugins/hexaemeron/.codex-plugin/plugin.json`,
  `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json`;
  `metadata.version` in `plugins/hexaemeron/skills/fiat/SKILL.md`; the new
  `fiat-v...` in `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS`; the pins
  `plugins/hexaemeron/tests/test_phylax_model_proxy.py:5684`,
  `tests/test_version_propagation.py:47` and
  `tests/test_evolution_contract.py:418,424`. The last runs (#2093 at 1.6.105,
  #2160 at 1.6.106 / `fiat-v6.87.1`) each bumped.
- Digest pins of the files the steps change, by full SHA-256 at the base
  (`git grep -F <sha256> 076add19`):

| File | SHA-256 at base | Pinned in |
| --- | --- | --- |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `b8c40d3e9b85cd75d6dc0e48097096f0f84b3ae2f2a10367cb7779d6998b6de2` | `tests/promise_machine_coverage.json:4653` |
| `plugins/hexaemeron/skills/fiat/SKILL.md` | `190b391c5cff054e60b2195264993f51fe76b426ad58fbf502978bcdaebe5012` | `tests/fixtures/agent-instruction-v1/manifest.json`; `fiat-study-runbook-phase/compact.wai`, `model.json`, `source-spans.json` |
| `plugins/hexaemeron/skills/fiat/EVOLUTION.md` | `defb155cefe3bfbfbb29d0bb186a626991fe6b7368d92c843be32599b194399c` | `tests/fixtures/promise-machine/runtime/fiat-final-integration.json` |
| `plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py` | `238105acf35e412fabb8e3267c63504312683a801dd1c31659d045fda505650f` | `tests/fixtures/promise-machine/runtime/fiat-checkpoint-archive.json` (10 sites), `tests/promise_machine_coverage.json:5305` |
| `references/checkpoint-archive.md`, `references/checkpoint-directory.md`, `scripts/checkpoint_directory.py`, the four version JSON files, `test_phylax_model_proxy.py`, `test_version_propagation.py`, `test_evolution_contract.py`, `test_disposable_git_signing.py` | (no hit) | none |

  Downstream of those: `docs/promise-machine/obligation-gates/evaluation-run.json`
  `tree_sha256` and the integration projection, re-pinned by the cascade.
  `INTEGRATED_CONTROLLER_SHA256` no longer exists at the base. Leave
  `test_hexctl_checkpoint_archive.py` unchanged if the design allows, so its
  ten fixture pins do not move.
- `plugins/hexaemeron/tests/test_hexctl.py` is 261,346 bytes against the
  262,144-byte Promise Machine read ceiling: new tests go in the new module.
- New Hexaemeron test method names are at most 60 characters
  (`tests/test_hexaemeron_manifest_headroom.py`).
- A new module that builds disposable Git history joins
  `FIXTURE_COMMIT_MATRIX` (`plugins/hexaemeron/tests/test_disposable_git_signing.py:15`);
  fixture commits use `--no-gpg-sign`.
- `test_refusals_after_git_init_are_the_four_in_reference` finds `git init` as
  the first `"init"` literal inside `_checkpoint_restore_from_archive`. Moving
  that call into a helper makes `min()` empty and the test errors; keep the
  literal in the function or update the test with the reference.
- Gates run with `FORCE_COLOR` unset (this shell sets 3, which reddens argparse
  tests) and `CHECKPOINT_COSIGN=~/.claude/tools/bin/cosign-3.1.3-darwin-arm64`
  for `run_tests.py`.
- A `.hexaemeron/design/*.py` copy committed under `docs/` enters the
  `lint-phylax` walk; run `phylax.py` on it before Step 1 publishes it.

### 3.4 Boundaries

- Always: both test suites and `run_checks.py` before a commit; the Imprimatur
  lint on the study, runbook, reference and decision draft; restore the
  process working directory on every exit path.
- Ask first: adding a refusal class; changing the relocation transaction's
  marker, retry or refusal rules; changing `--from`; adding an admission
  ownership or mode rule.
- Never: tear down an operator-named destination; follow a symlink at the
  destination; claim race freedom for Git children; edit a receipted audit
  record.

## 4. Design options

### 4.1 Candidates

1. `path-unchanged`. Today's restore. Trade: no change; S4-R1-06 stays open.
2. `identity-recheck`. Keep absolute paths. Before and after every write and
   every Git child, prove with `_checkpoint_directory_still_at_path(destination,
   admitted_descriptor)` that the name still names the admitted inode. Trade:
   smallest diff and no working-directory change, but each operation keeps a
   check-to-use window in which the name can move.
3. `anchored-cwd`. After the inspector returns, save the working directory,
   `fchdir` to the admitted descriptor, and run every destination-rooted
   operation by a path relative to it (`dir_fd` where a helper already holds a
   descriptor). Git children inherit that working directory, with relative
   arguments only. Identity seals bracket each Git child and each step whose
   recorded output names the absolute path. Trade: a process-wide working
   directory change for the restore's duration, two descriptors held, and a
   parameterised relocation transaction; Git's own absolute paths stay exposed.
4. `private-build-adopt`. Build the repository, capsule, marker, worktree and
   state in a private scratch directory, then move each entry into the
   admitted directory by descriptor-relative rename and rewrite Git's two
   worktree links. Trade: no operation touches the destination name, but a
   killed restore leaves nothing in the destination, a cross-filesystem scratch
   root forces a full copy, and Git's worktree files are written by hand.

Considered and not carried: `/dev/fd/N` or `/proc/self/fd/N` as a path prefix
(Darwin cannot traverse `/dev/fd/N` and has no `/proc`; Linux can, but the
recorded paths would then be descriptor aliases); `git worktree add
--relative-paths` (sets `extensions.relativeWorktrees`, which needs Git 2.48
or later to read the restored repository, and does not cover `git init`).

### 4.2 Criteria

Every selection cell runs a fresh model from `.hexaemeron/design/probe.py`.
The model is not `hexctl.py`: it repeats the restore's write sequence after
admission (`git init`, bundle fetch, base checkout, origin URL, three capsule
members under `.git/`, `.hexaemeron/.gitignore` and the marker, the worktree
home, `git worktree add`, a stage published by rename, a breadcrumb, marker
retirement, capsule-root removal), each candidate under its own binding rule,
with Git configuration pinned to `/dev/null` and unsigned commits.

Selection gates (each `boolean`, `equals true`, blocks `design-lock`):

- `unswapped-restore-completes` (compatibility, protasis): the layout is
  complete, `git rev-parse --show-toplevel` in the worktree names it, and `git
  worktree list --porcelain` lists it without `prunable`.
- `directory-swap-writes-nothing` (correctness, phylax): the name is swapped
  for an empty directory right after admission; the candidate refuses and the
  replacement holds zero entries.
- `symlink-swap-writes-nothing` (correctness, phylax): the same with a
  symlink to a sentinel directory; the candidate refuses, the symlink stays,
  the sentinel holds zero entries.
- `interrupted-cleanup-stays-bound` (recovery, elenchus): after `git worktree
  add` the name is swapped and the restore is interrupted; created-destination
  cleanup runs; the replacement still exists with zero entries.
- `residue-follows-reference` (compatibility, protasis): in the same scenario
  the relocation marker is in the admitted directory, as the reference's
  residue rule requires.

Selection metrics (all `minimise`):

- `transaction-race-leaked-trials` (correctness, phylax, count): 100 trials;
  a racer process starts after the origin URL is set and repeatedly renames
  the admitted directory away, puts an empty replacement at the name for 0.2
  to 2 ms, parks it, and renames the admitted directory back. Value: trials in
  which any parked replacement holds an entry.
- `name-resolving-writes` (correctness, phylax, count): controller-performed
  writes, in one unswapped restore, whose path traverses the destination name.
- `identity-probes-per-restore` (time, metron, count): no-follow open, `fstat`
  and `realpath` probes of the destination in one unswapped restore.
- `bytes-built-outside-destination` (space, metron, bytes): bytes the
  candidate builds outside the admitted directory before moving them in.

Conformance gates (each `boolean`, `equals true`, blocks `integration`; built
in the controller step, so no `step:N` cell is due before that step pushes):
`replacement-regression-guarded` (correctness, elenchus),
`nonempty-symlink-still-refuse` (compatibility, protasis),
`interrupted-restore-stays-bound` (recovery, elenchus),
`from-mode-unchanged` (compatibility, protasis). Section 4.4 names their
resolvers.

### 4.3 Results and selection

Every selection report is a closed `protasis-design-report/v1` object with
exit 0 under `.hexaemeron/design/reports/selection/`, produced on 2026-11-06
by `python3 .hexaemeron/design/probe.py select --candidate <id> --criterion <id> --out <path>`
(probe SHA-256 `1a58475494dc832535497d9947dfc3a59fc28ba20043c45737e48f7207c13b57`).

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

Observed facts behind the table:

- `path-unchanged` restores into the replacement: the swapped-in directory
  receives the whole repository, and its created-destination cleanup `rmdir`s
  the empty replacement after an interruption.
- `identity-recheck` leaks in 35 of 100 transaction-phase trials. In a rerun
  with 38 leaking trials, 34 leaked files were `tmp/fiat/fiat-run/.git`,
  written by `git worktree add` through the absolute worktree argument the
  candidate passes.
- `anchored-cwd` recorded 0. Three earlier runs of the same measurement, made
  while the probe was being written, gave 1, 1 and 0; the one leak inspected
  held directories only, from `git worktree add`.
- `private-build-adopt` leaves its marker in the private build, so a killed
  restore leaves nothing the reference's retry rules can see.
- Git's own absolute paths. A separate race over each Git command in an
  anchored working directory (300 trials each, racer active only during that
  command) leaked for `git init` (3), `git init .` (1), `git init --bare .git`
  (1) and `git worktree add` (5, the files `.git/worktrees/fiat-run/ORIG_HEAD`
  and its directories), and never for `git fetch`, `git checkout` or `git
  config` (0 each). The whole-sequence race (racer from the first operation,
  `python3 .hexaemeron/design/probe.py observe`) gave `path-unchanged` 10,
  `identity-recheck` 13, `anchored-cwd` 11 and `private-build-adopt` 0 of 100;
  every leaked file in the `anchored-cwd` and `identity-recheck` runs was a
  `git init` template file or `.git/config`. That phase is the same Git
  command under every in-place candidate, so it is reported here and not used
  to rank them.
- The model's Linux behaviour is unmeasured: the container has no Git.

Selection. `path-unchanged` fails three gates and `private-build-adopt` fails
`residue-follows-reference`. Of the two survivors, `anchored-cwd` is lower on
`transaction-race-leaked-trials`, `name-resolving-writes` and
`identity-probes-per-restore` and equal on `bytes-built-outside-destination`,
so it dominates `identity-recheck`. The non-dominated frontier is one
candidate and the rule is `unique-frontier`. The record is
`.hexaemeron/design-evidence.json`, SHA-256
`815abd409e5d7031407d9c4104884e47814da7798e8891917625fa7a18ab9742`; the
Protasis checker exits 0 at `design-lock`, `step:1`, `step:2` and `step:3`, and
refuses `integration` with D008 until the four conformance reports exist.

The trade named: `anchored-cwd` changes the process working directory for the
restore's duration and threads a relative form through the relocation
transaction, and in return no controller-performed write resolves the
destination name; it does not close Git's own absolute-path window, which
only `private-build-adopt` closes, at the cost of the reference's residue and
retry contract.

### 4.4 The chosen design

**The anchor.** One restore-scoped object made from admission: the absolute
`destination` string, the admitted descriptor, its `(st_dev, st_ino)`, the
`created` flag, and a saved working-directory descriptor. Its seal is
`_checkpoint_directory_still_at_path(destination, admitted_descriptor)`, which
already does a no-follow open, a `realpath` equality and an identity
comparison. A failed seal refuses with the fixed sentence
`checkpoint restore destination no longer names the admitted directory`
through `die(..., 1)`. No path, member or tool byte enters it.

**Order.**

1. Admission unchanged (absent or empty, no symlink, `destination-occupied`).
2. The inspector runs unchanged into its scratch root, before any working
   directory change, so an operator-relative archive path still resolves.
3. Seal, then `fchdir(admitted_descriptor)`. From here the restore never
   names the destination by path for an operation.
4. On every exit, `fchdir` back to the saved descriptor before anything else
   in the `finally`, then close both descriptors.

**Operations and their binding.**

| Row | Operation | Base form | Bound form |
| --- | --- | --- | --- |
| G1 | `git init` / `git clone --bare --local <scratch> .git` | `bounded_git(destination, ...)`, child `cwd=realpath(destination)` | child inherits the anchored working directory, argument `.git`; seal before and after |
| G2 | `git fetch <bundle>`, `git config` (three), `git checkout`, `git rev-parse` | same | inherited working directory; seal after the checkout |
| G3 | `git worktree add <worktree> <branch>` | absolute worktree argument from `origin` | relative `tmp/fiat/<name>`; after it, read the worktree's `.git` file relative and require `gitdir: <destination>/.git/worktrees/<id>`; seal |
| W1 | capsule extraction under `.git/fiat-checkpoint-restore/<sha>/` | `os.makedirs` and `os.open` by absolute path | relative paths |
| W2 | relocation marker and `.hexaemeron/.gitignore` | origin opened by path, compared with path | `dir_fd` from a duplicate of the admitted descriptor; seal before publication |
| W3 | worktree home `tmp/fiat/.gitignore` | origin opened by path | `dir_fd` from the admitted descriptor |
| W4 | private stage, snapshot copy, state and ledger writes, directory `fsync` | absolute `stage` | relative stage path |
| W5 | criteria history under `.git/` (#2073) | `.git` opened by path | `.git` opened by `dir_fd` from the admitted descriptor |
| W6 | active-state publication (`fchdir` into the worktree, no-replace rename) | worktree and stage opened by path | opened relative; it already restores `.` afterwards, which is now the anchor; seal before |
| W7 | breadcrumb, marker retirement (deferred or not) | `state_root(origin)` by path | relative `.hexaemeron`; seal before retirement |
| C1 | capsule-root removal | `shutil.rmtree(restore_root)` absolute | relative path |
| C2 | created-destination removal on refusal | `os.rmdir(destination)` by path | only when a seal says the name still names the admitted inode, then `rmdir`; otherwise leave it |
| R1 | reused readers: capsule reader, `_checkpoint_refs`, `verify`, `status`, `next`, identity recompute | absolute paths | called with relative directories where they take one; readers that read absolute paths from recorded state run between seals; their Git children inherit the anchor |

`bounded_probe` gains one keyword so a restore call starts its child with the
inherited working directory or a relative `cwd`, never `realpath`. Every
other caller keeps today's `cwd=os.path.realpath(base_dir)`.

**Recorded values.** Every value the restore records (state
`config.git.origin` and `config.git.worktree`, the restore receipt, the marker
record, the breadcrumb, the result) is built from the admitted `destination`
string, never from `getcwd()` or Git's report. A seal before the relocation
records state, and one before success, makes those strings true of the inode
the restore wrote.

**Relocation transaction.** `_checkpoint_restore_relocate` takes an optional
anchor. With one, it records the absolute strings above and performs every
operation in rows G3, W2 to W7 in the relative form. Without one (`--from`),
every operation, record and refusal is byte-for-byte today's.

**Seals.** Before `fchdir`; before and after G1; after the base checkout;
before the relocation records state and before marker publication; after G3;
before W6; after the internal checks and identity recompute; before marker
retirement; before returning success; and in C2. A seal is also the check C2
uses. Each is one probe; `identity-probes-per-restore` measured 12 in the
model.

**Room for #1649.** The anchor holds the admitted descriptor from admission to
the end of the restore. A lock that #1649 adds (an exclusive `flock` on that
descriptor, or a lock file created through `dir_fd` under it, plus restore in
`MUTATING`) is taken right after admission and covers every bound operation
without changing them. This run adds no lock.

**Conformance resolvers,** run from the run worktree before the final
`done merge-step` checks `integration`:

```text
python3 .hexaemeron/design/probe.py conform --candidate anchored-cwd --criterion <criterion> --root . --out .hexaemeron/design/reports/conformance/anchored-cwd-<criterion>.json
```

Each runs `python3 -m unittest discover -s plugins/hexaemeron/tests -t plugins/hexaemeron/tests -p <module> -k <pattern>`
with `FORCE_COLOR` removed and requires exit 0, at least one test run and no
skip: `replacement-regression-guarded` runs `test_checkpoint_restore_binding.py`
with `-k replacement`; `nonempty-symlink-still-refuse` runs the two
`test_hexctl_checkpoint_archive.py` tests in SC-3 and the new module with
`-k symlink_destination`; `interrupted-restore-stays-bound` runs the new module
with `-k interrupted`; `from-mode-unchanged` runs `test_hexctl_checkpoint.py`
with `-k restore`. The signed fixture skips without `gpg`, which fails the
cell. Each writes only to an `--out` path that must not exist.

### 4.5 Step outline for the runbook

1. Scaffold. Commit copies of the study, runbook, design record, probe,
   builder and the 36 selection reports under
   `docs/fiat-1648-archive-restore-binding/`, and the decision draft named in
   section 12. No `plugins/` path changes, so no package bump.
2. Controller. The anchor, the `bounded_probe` keyword, rows G1 to R1 in
   `_checkpoint_restore_from_archive` and the anchored relocation, the
   reference paragraph, the new module
   `plugins/hexaemeron/tests/test_checkpoint_restore_binding.py` (in-process
   restores of the existing signed archive fixture with `mock.patch` seams
   that swap the name at each SC-1 point; symlink swaps; interruption; a
   working-directory restoration check; one `--from` no-change case), its
   `FIXTURE_COMMIT_MATRIX` row if it builds history, and the version bump,
   generation row and digest cascade, all in this one step so the cascade is
   walked once.
3. Demonstrate. Run the four conformance resolvers and the module, and commit
   the output and commands to `docs/fiat-1648-archive-restore-binding/demonstration.md`.
   No `plugins/` path changes.

## 5. Risk register seed

```risk-register
anchor-before-write | the gap between admission and the first destination write | the working directory is fixed to the admitted descriptor before git init or clone and no destination write runs before it
controller-writes-relative | every controller write after admission: capsule, marker, worktree home, stage, state, ledger, breadcrumb, criteria history, publication, retirement | none opens or creates a path that starts with the destination string; each uses a cwd-relative path or dir_fd from the admitted descriptor
git-child-cwd | bounded_probe for restore calls | a restore child starts with the inherited or a relative cwd, never realpath of the destination; every other caller keeps realpath
git-absolute-paths | git init, clone and worktree add deriving absolute paths internally | each is bracketed by seals and the residual window is stated, not claimed closed
recorded-paths | state config.git.origin and worktree, restore receipt, marker record, breadcrumb, result | each is built from the admitted destination string and a seal precedes recording and success
worktree-link | the gitdir line Git writes into the new worktree's .git file | it names the destination's .git/worktrees entry, or the restore refuses
seal-coverage | every seal point in section 4.4 | each uses the admitted descriptor's identity, not a fresh open compared with itself
cwd-restored | the process working directory on success, refusal, SystemExit and exception | it is restored before cleanup and equals the caller's on every exit; tests assert it
relative-operator-paths | operator-supplied archive or scratch paths that are relative | they are consumed by the inspector before the working directory changes
cleanup-by-name | created-destination removal and capsule-root removal | rmdir runs only after a seal passes; rmtree is relative; neither reaches a replacement or a symlink target
refusal-text | the moved-destination refusal | one fixed sentence, exit 1, no path, member or child byte
refusal-table-pins | CHECKPOINT_ARCHIVE_REFUSALS, the reference table and the post-git-init class test | the 24 classes and the four post-init classes are unchanged; the git init literal stays in _checkpoint_restore_from_archive
from-mode-unchanged | checkpoint restore --from through the shared relocation | without an anchor every operation, record and refusal is unchanged and the existing restore tests pass
admission-unchanged | nonempty, symlink and symlinked-parent destinations | destination-occupied still refuses the first two and the third is still admitted
interruption-residue | a refusal or kill after a swap | the marker and disposable root stay in the admitted directory and nothing is written into or removed from the replacement
directory-carrier | git clone --bare --local into .git for the directory carrier | it gets the same anchored cwd, relative target and seals as git init
lock-composition | the anchor's descriptor lifetime | it spans admission to the end, so a later #1649 lock on it covers every bound operation
version-surface | the hexaemeron package version and the fiat ledger row | the package version exceeds the PR base and every ref's claim on all surfaces, CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS gains the new fiat version, and the row comes from the version-relations block
digest-cascade | fixtures pinning hexctl.py, fiat SKILL.md, EVOLUTION.md and any edited pinned test file | the step re-pins its own cascade and the root suite, the Hexaemeron suite and promise_machine.py check pass at its exit
test-ceiling | plugins/hexaemeron/tests/test_hexctl.py at 261346 bytes and the 60-character name cap | no new test lands there and every new name fits
killed-mid-restore | a controller killed between the anchor and success | nothing outside the admitted directory and the scratch root is written, and the residue matches the reference's rule
```

`killed-mid-restore` holds by construction for controller writes; Git
children killed mid-write leave whatever Git leaves, inside the admitted
directory unless the window in `git-absolute-paths` was open at that moment.

## 6. Glossary seeds

- **Admitted directory:** the inode `_checkpoint_restore_archive_destination`
  opened, identified by `(st_dev, st_ino)`, whatever its name later becomes.
- **Destination name:** the absolute path the operator supplied, after the
  parent is resolved once; the only string the restore records.
- **Anchor:** the restore-scoped object holding the admitted descriptor, its
  identity and the saved working directory.
- **Seal:** one check that the destination name still names the admitted
  directory, through `_checkpoint_directory_still_at_path`.
- **Replacement:** whatever a parent writer puts at the destination name
  after admission: a directory, a symlink, or nothing.
- **Bound operation:** one that resolves through the admitted descriptor or
  the anchored working directory and never through the destination name.
- **Git absolute-path window:** the lifetime of a Git child that converts its
  relative arguments to absolute paths, during which a swap-and-restore of the
  name can redirect that child.

## 7. Sources

- [`hexctl.py` at the base, admission](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L28568-L28646)
- [`hexctl.py`, archive restore](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L28747-L29022)
- [`hexctl.py`, relocation transaction](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L28239-L28530)
- [`hexctl.py`, `bounded_probe`](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/fiat/scripts/hexctl.py#L22833-L22934)
- [`checkpoint-archive.md`, restore transaction](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md#L327-L356)
- [`checkpoint-directory.md`](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/fiat/references/checkpoint-directory.md)
- [#861 audit record, Step 4 rounds](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md#L345)
- [Refusal-class pins in `test_hexctl_checkpoint_archive.py`](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py#L789-L1346)
- [#1652 run PR and carryover](https://github.com/wildcat-finance/skills/pull/1652),
  [#2073](https://github.com/wildcat-finance/skills/pull/2073),
  [#1975](https://github.com/wildcat-finance/skills/pull/1975),
  [#1649](https://github.com/wildcat-finance/skills/issues/1649)
- [POSIX `rename`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html),
  [POSIX `fchdir`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/fchdir.html),
  [Linux `renameat2`](https://man7.org/linux/man-pages/man2/rename.2.html),
  [Python `os` dir_fd support](https://docs.python.org/3.14/library/os.html#os.supports_dir_fd)
- [Git `init_db` and `set_git_dir` in `setup.c`](https://github.com/git/git/blob/v2.50.1/setup.c),
  [`git worktree` relative paths](https://git-scm.com/docs/git-worktree#Documentation/git-worktree.txt---relative-paths)
- The design probe, builder, record and 36 selection reports under `.hexaemeron/`.

## 8. Signals, and the questions behind them

[Ephoros](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal carries. Restore runs when an operator or driver invokes
it, not unattended, so there is no alert. Two questions an operator will ask:

1. "Did this restore stop because the destination moved?" Answered by the
   fixed refusal sentence on stderr and exit 1.
2. "Where is what the refused restore wrote?" In the admitted directory,
   wherever its name now is. The refusal cannot name the path (the path-free
   rule), so the reference paragraph says so and tells the operator to look in
   the parent directory.

No new structured event, metric or ledger entry: a refused restore writes no
ledger.

## 9. Boundaries, per capability

[Phylax](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the boundary list and controls.

| Boundary | What is worth taking | Control |
| --- | --- | --- |
| The destination name in a parent another principal can write | redirecting the restored run's repository and controller state into an attacker-chosen directory, or through a symlink into a victim directory | anchored working directory and `dir_fd` for controller writes; seals before recording and success; refusal on any moved name |
| Git children started for the restore | the same, through Git's own paths | inherited cwd, relative arguments, seals around each child, recorded worktree link checked |
| Cleanup after a refusal | deleting a directory the restore did not create | `rmdir` only after a passing seal; relative `rmtree` |

Defended: the actor of assumption 1. Against that actor, no controller write
lands outside the admitted directory, and a moved name at any seal refuses
before state is recorded or success is printed.

Not defended, stated:

- Root, administrators, and any process running as the restoring account,
  including one with `ptrace` or debugger rights over `hexctl` or `git`.
- A principal who can write inside the admitted directory: a pre-existing
  destination owned by another account, or carrying group or other write, or
  one an attacker created empty for the operator to name.
- Git's absolute-path window: a swap and restore of the name completed within
  one Git child's lifetime can redirect that child's writes. Measured for `git
  init` (template files and `.git/config`) and `git worktree add`
  (`ORIG_HEAD` under `.git/worktrees/<id>/`); not observed for fetch, checkout
  or config in 300 trials each; Linux unmeasured.
- Reused readers between seals may read the replacement. They write nothing
  there that the controller controls; a reused Git reader can take Git's own
  optional index lock in a replacement that is itself a repository.
- The window between C2's seal and its `rmdir` can remove an empty directory
  a parent writer placed at the name.
- Two concurrent restores (#1649) and `--from`'s origin.

## 10. The budget, or its absence

[Metron](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/metron/SKILL.md)
owns budgets. None new: the existing `checkpoint.archive.restore_wall_ms`
budget of 20,000 ms in
`plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json` is
unchanged and this run makes no performance claim. The added cost is the seal
count, 12 probes in the model against 0 at the base, each one no-follow
`open`, `fstat`, `realpath` and `close`, beside Git children that dominate the
restore's time.

## 11. The fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns the triage order and the guard rule.

What stops the restore: any failed seal, any recorded worktree link that does
not name the destination, any failed bound operation, and every existing
refusal. Each exits before success and before state names a path it did not
write. The process working directory is restored on every exit.

Guard convention: each SC-1, SC-2 and SC-4 case is a test in
`test_checkpoint_restore_binding.py` that swaps the name through a
`mock.patch` seam at a fixed point, so the order is deterministic. At the base
the before-`git init` case restores into the replacement and fails, and the
step's audit records that counterfactual on the parent commit. Test names
carry `replacement`, `symlink_destination` or `interrupted` so the
conformance resolvers select them, and stay within 60 characters.

## 12. Decisions and their homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/076add19439c163be266374eb671a1c9a234c12c/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record.

1. Bind the archive restore by an anchored working directory and `dir_fd`,
   with seals around Git children, and state Git's absolute-path window
   rather than adopt a private build that changes the residue and retry
   contract. Expensive to reverse: it fixes the relocation transaction's
   two-form interface and the restore's threat statement. Record:
   `docs/decisions/drafts/bind-archive-restore-to-its-admitted-directory.md`,
   numbered at the merge that lands it; Step 1 creates the draft.
2. Refuse a moved destination with one fixed `die(..., 1)` sentence outside
   the closed class table. A 25th class would move the reference table, the
   frozen #861 study comparison and the computed post-`git init` set, and the
   relocation family that performs most seals already refuses through `die`
   (S4-R1-02). Same record.
3. The Fiat generation row lives in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
   bound by the runbook's `version-relations` block.
4. The operator-facing rule lives in the "Restore transaction" section of
   `plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`, which
   `checkpoint-directory.md` already defers to.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | anchored-cwd
record | docs/decisions/drafts/bind-archive-restore-to-its-admitted-directory.md
```
