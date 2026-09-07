# Study: outer checkpoint archive export and restore

Task issue: [skills#861](https://github.com/wildcat-finance/skills/issues/861).
Run branch `fiat/861-outer-checkpoint-archive-export-and-restore`, cut from
`main` at `0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`. Design record:
`.hexaemeron/design-evidence.json`, SHA-256
`101172ad264e56b0910cc64e8f11662da8b7f874ca030c3da76ba7cfacf6db91`, selected
candidate `native-subcommands`.

Assuming, unless corrected:

1. The archive stays a ZIP, as the issue's archive contract and ADR-028 both
   say. Tar was not considered a format change this run may make.
2. The three-identity model of ADR-071 governs: outer archive digest (carrier
   bytes), `fiat-controller-checkpoint/v1` manifest digest (capsule bytes) and
   `snapshot_id` (meaning). The archive carries all three and restore rejoins
   them; none stands in for another.
3. Per-member `.sha256` sidecars inside the zip, which ADR-028's 2026-08-30
   clause and the manual procedure list, are replaced by one closed content
   manifest that records every entry's digest and size. The outer `.sha256`
   beside the zip stays. Two homes for one digest set is the drift the manual
   archives already show (section 2). The new decision record states this.
4. A boundary directory that already exists is never replaced; the same
   boundary exported twice from unchanged state yields identical bytes, so a
   second export is refused as occupied rather than compared.
5. Both accepted ADR-028 boundaries are in scope: `step-<n>-<sha>` after
   `done push` and `audit-verdict-step-<n>-loop-<l>-<sha>` at an exhausted loop.
6. The clean machine is a Linux container started with `--network none`, an
   empty GNUPGHOME and a copy of the controller (`hexctl.py`, stdlib only) whose
   SHA-256 the transcript records. The controller is a tool like `git`; the
   issue's prohibition covers the producer's clone, paths, reflog, cache,
   credentials and delegation handle, not the program that reads the archive.
7. Restore sets `remote.origin.url` to `https://github.com/<repository>.git`,
   derived from the manifest's validated `owner/name`, and fetches nothing.
   `checkpoint identity` refuses without a bound origin, so the join in
   criterion C7 needs that string. It is not a credential.
8. Root-suite exits inside this run worktree are held against a clean detached
   snapshot of the committed head, because two
   `tests/test_agent_instruction_corpus*` tests read this run's own
   `.hexaemeron/design-evidence.json` (issue #1228).
9. Step numbering for the pending conformance evidence follows section 1's
   five-step shape. The runbook derives from it; renumbering the steps means
   amending the record's `blocks` values first.

## 1. Problem statement

Fiat saves a checkpoint at every accepted boundary, but `hexctl` builds only
the controller capsule. The Git bundle, signature proof, outer manifest,
sidecars and README around it are hand-assembled by the agent following
`push-discipline.md`, and the receiver verifies them by hand. Section 2
measures what that produces: no two runs' archives share a layout, entries
carry build-time metadata and unsorted order, one manifest leaks the
producer's absolute origin path, and no restore transcript from a machine
that did not write the archive exists.

This run gives `hexctl` the outer archive. The user is the Fiat controller
agent at an accepted boundary and the agent, on any machine, that continues
the run. A working prototype means three commands exist and their evidence
holds:

```text
hexctl --dir <run-worktree> checkpoint archive
hexctl checkpoint inspect --archive <zip> --sha256 <outer-hex> [--scratch <new-dir>]
hexctl --dir <empty-destination> checkpoint restore --archive <zip> --sha256 <outer-hex>
```

`archive` runs at an accepted boundary, builds beside the fixed boundary
directory and publishes with a no-replace rename:

```text
<origin>/.hexaemeron/checkpoints/<run-worktree-name>/
  step-<n>-<full-head-sha>/checkpoint.zip
  step-<n>-<full-head-sha>/checkpoint.zip.sha256
```

The sidecar is `<64 lowercase hex>  checkpoint.zip\n` (two spaces, relative
name; `shasum -a 256 -c` reads it). The zip is a pure container: every entry
stored (no compression), Unix mode `0100644`, DOS time 1980-01-01 00:00:00,
`create_system` 3, no directory entries, no ZIP64 records, entries sorted by
UTF-8 bytes, no comment, no extra fields. Layout, fixed:

```text
checkpoint.json                      fiat-checkpoint-archive/v1, canonical JSON
README.txt                           contents list and restore rule, fixed text
git/repository.bundle                complete-history bundle of exactly the capsule's refs
controller-capsule/MANIFEST.json     exact bytes from checkpoint export
controller-capsule/controller/...    exact capsule files
identity/checkpoint-identity.json    exact checkpoint identity stdout, or absent
proof/signatures.json                fiat-checkpoint-signature-proof/v1
proof/pubkey.asc                     OpenPGP signer key(s), or proof/allowed_signers for SSH
acceptance/prior/<n>.json            prior acceptance receipts when any exist
```

`checkpoint.json` is closed to: `schema`; `archive` (format `zip`, compression
`stored`, sorted `entries` of `path`, `bytes`, `sha256`); `boundary` (`kind`,
`step`, `loop` when exhausted, `working_commit_sha`, semantic `next`); `run`
(`repository`, `run_branch`, `worktree_name`, `task_issue`,
`initial_base_sha`, `run_anchor_sha256`); `refs` (name to full SHA, equal to
the capsule's map); `bundle` (`bytes`, `sha256`, `hash_algorithm`,
`complete_history`); `controller_capsule` (`manifest_sha256`, `state_sha256`,
`ledger_sha256`, `ledger_entries`, `ledger_tail`, `files`, `bytes`);
`identity` (`status` `bound` with `snapshot_id`, or `unavailable` with a closed
reason); `signer` (`format`, `fingerprints`, `key_path`); `proof` (`commits`,
`sha256`); `acceptance` (`current` is the literal `outside`, `prior` list);
`controller` (`hexctl`, Fiat version); `limits` (the ceilings below). No
timestamp, no absolute path, no environment value, no credential.

`inspect` reads the zip through the central directory under the ceilings
before any extraction, verifies every entry against the manifest and the
manifest against the out-of-band outer digest, verifies the bundle in a
disposable `git init` root, verifies every run commit's signature in a
disposable keyring pinned to the manifest fingerprints, and prints one
`fiat-checkpoint-inspect/v1` object of structured findings. It prints no entry
content. `restore --archive` runs the same inspection, refuses a destination
that is not new or empty, creates the repository from the bundle
(`git init`, `git fetch <bundle> +refs/heads/*:refs/heads/*`, checkout of the
integration branch), extracts the capsule into
`<destination>/.git/fiat-checkpoint-restore/<outer-sha256>/`, calls the
existing relocation transaction with the manifest digest, recomputes
`snapshot_id`, runs `verify`, `status`, `next`, prints one
`fiat-checkpoint-archive-restore/v1` object and executes nothing.

Ceilings (safety, not performance): 4,200 entries; 1,300 MiB expanded; bundle
1 GiB; every other entry 64 MiB; capsule ceilings as `controller-checkpoint.md`
already fixes; entry name 1,024 UTF-8 bytes, 255 per component, valid NFC
UTF-8, no C0 or C1 control, no empty, `.` or `..` component, no backslash, no
leading `/`, unique after NFC and `casefold()`; at most 64 prior acceptances.

The proving demo is the last step's clean-machine run:

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/checkpoint_clean_machine.py \
  --archive <origin>/.hexaemeron/checkpoints/<wt>/step-<n>-<sha>/checkpoint.zip \
  --sha256 <outer-hex> --image python:3.14-slim \
  --transcript .hexaemeron/clean-machine/transcript.json
```

It copies the archive, its sidecar and `hexctl.py` into a container started
with `--network none`, runs `inspect`, `restore --archive` into an empty
directory, `verify`, `status --json`, `next` and `checkpoint identity`, and
writes `fiat-checkpoint-restore-transcript/v1` with `network`, `keyring`,
`destination_was_empty`, `hexctl_verify_exit`, `next_matches_manifest`,
`snapshot_id_matches`, the controller SHA-256 and the six Metron measurements.
Exit 0 and every listed field true or zero is the demo.

Success criteria, each a command:

- C1 One archive recreates the committed repository and portable controller
  state in an empty directory:
  `test_restore_from_archive_recreates_repository_and_controller_state`
  (restored `hexctl verify` exit 0; `status` fingerprint equals the producer's
  after the two owned path fields; ref map equal; ledger is the exact prefix
  plus one `checkpoint:restore` entry).
- C2 Byte-identical repeated exports:
  `test_archive_export_is_byte_identical_across_two_exports_and_two_absolute_paths`
  (same state exported twice, the second from a copy of the origin at another
  absolute path; `checkpoint.zip` bytes equal).
- C3 No source dependence:
  `test_restore_from_archive_offline_after_source_clone_removed` (source clone
  deleted, `HOME` and `GIT_CONFIG_GLOBAL` pointed at empty scratch, no remote
  fetched; the container transcript adds `--network none`).
- C4 Acceptance stays outside: `test_archive_reserves_prior_acceptance_entries`
  and `test_hostile_self_referential_acceptance`.
- C5 Exporter refusals, one test per class:
  `test_archive_export_refuses_every_unaccepted_boundary`,
  `..._refuses_dirty_worktree`, `..._refuses_secret_shaped_member`,
  `..._refuses_oversized_bundle`, `..._refuses_ref_disagreement`,
  `..._refuses_occupied_boundary_directory`, `..._refuses_unsupported_signature`.
- C6 The inspector rejects every named hostile fixture before extraction can
  escape its disposable root: 35 tests `test_hostile_<id>` for the ids in
  section 5's `hostile-fixture-set` line, selected by
  `python3 -m unittest -k hostile plugins.hexaemeron.tests.test_hexctl_checkpoint_archive`.
- C7 Restore re-verifies signatures, receipts, identity and ancestry:
  `test_restore_from_archive_reverifies_signatures_receipts_identity_and_ancestry`
  (a proof line flipped from `G`, a ledger byte changed, a `snapshot_id`
  changed, a working commit outside the anchor's descendants, each refuses).
- C8 Empty destination and explicit resume:
  `test_restore_from_archive_refuses_non_empty_destination`,
  `test_restore_from_archive_executes_no_directive`.
- C9 Two absolute paths and a moved `main`:
  `test_restore_from_archive_after_main_advances_stays_anchored`.
- C10 Suites and gates: `python3 scripts/run_checks.py` exit 0 on the clean
  snapshot, the three lints exit 0, Horos current, `git diff --check` exit 0,
  each push receipt GitHub-verified.
- C11 Budgets:
  `python3 plugins/hexaemeron/skills/metron/scripts/metron.py check --budgets plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json --baseline plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-baseline.json --run .hexaemeron/metron/run.json`
  exit 0 (section 10).
- C12 Clean-machine transcript: the demo command above exit 0 and
  `python3 .hexaemeron/measure_design.py --conformance clean-machine-restore-transcript`
  writing `value: true`.

Intended shape, five steps: 1 scaffold (decision draft, reference, budgets
file, tracked study and runbook, fixture inventory test), 2 `checkpoint
archive`, 3 `checkpoint inspect` and the hostile fixtures, 4 `checkpoint
restore --archive`, 5 clean-machine demo, measurements, procedure and ledger
row.

## 2. Prior art

### In this repository

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (17,683 lines at
`0bc39f27`) has `checkpoint identity|export|restore`: constants at lines
433-479 (`CHECKPOINT_SCHEMA`, ceilings 4,096 files and directories, 256 MiB
total, 64 MiB per file, 1 MiB manifest, 1,024-byte paths, JSON depth 128,
`CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` = 19 versions `fiat-v5.35.1`
through `fiat-v5.53.1`) and 543-551 (identity schemas, domain
`wildcat-fiat-checkpoint-identity/v1\0`); functions `_checkpoint_stat_identity`
13746 through `cmd_checkpoint_restore` 16464; `bounded_tool`/`bounded_git`
11864-11890 (fixed argv, output cap `GIT_OUTPUT_MAX` 2 MiB, `GIT_TIMEOUT` 30 s);
`_checkpoint_refs` 13790 (the bounded ref set: base, run branch, receipted step
branches); `_checkpoint_boundary` 13798; `target_repository_binding` (one
credential-free `remote.origin.url`, unbound when absent). Export result schema
`fiat-controller-checkpoint-export/v1` reports `capsule`, `boundary`, `next`,
`refs`, `files`, `bytes`, `manifest_sha256`, `state_fingerprint`,
`ledger_entries`, `ledger_tail`. `cmd_reset` (17379) already preserves
`checkpoints` under `.hexaemeron` and archives completed runs under
`.hexaemeron/archive/<stamp>-<topic>`. The controller shells out in nine sites,
all through `bounded_run`; it imports neither `zipfile` nor `tarfile`. The only
`zipfile` users in the marketplace are Dokimasia's xlsx code and fixtures.

Tests: `plugins/hexaemeron/tests/test_hexctl_checkpoint.py` (55 tests, one
class `HexctlCheckpointTests(HexctlCase)`, drives `hexctl` as a subprocess and
in-process) and `test_hexctl_checkpoint_identity.py` (27 tests, golden fixture
`tests/fixtures/checkpoint-identity-v1.json`); root
`tests/test_fiat_checkpoint_decision_record.py` (5) and
`tests/test_wave_delta_reinstatement.py` (6). The fiat-860 record puts the
whole Hexaemeron suite at 2,360 and the root suite at 1,389.

References, read at `main`: `references/push-discipline.md` lines 296-386
(`## Step checkpoint`, the manual procedure this run replaces; it cites
issue-377 comment 5435028801, which returned HTTP 404 on 2026-09-06);
`references/controller-checkpoint.md` (capsule contract, read boundary,
relocation transaction, `## Outer recovery boundary`: "These commands do not
create or verify the Git bundle, package an archive, handle keys or mint a
semantic checkpoint identity"); `references/checkpoint-identity.md`
(`snapshot_id`, carrier fields excluded, transparent single restore tail).
`SKILL.md` lines 145-155 and 624-629 instruct the agent to follow that section
by hand; Promise Machine contract `fiat-controller-checkpoint` at line 897.

Decision records: ADR-028 (Accepted 2026-08-27; amended 2026-08-29 twice,
2026-08-30, 2026-09-02) fixes the checkpoint store path, the two boundaries,
the zip's contents "controller capsule, Git bundle, outer manifest, public
key, signature proof, member sidecars and restore README", the outer sidecar
beside the zip, unconditional saving, no upload, and rejects "Complete
standing-checkpoint automation" "for this controller generation because one
command would join controller mutation, archive parsing and key handling".
ADR-069 (2026-09-02) reinstates the distributed layer and names "the outer
archive assembly ADR-028 leaves to a manual procedure" as owed. ADR-070
carries the three-way ownership split (skills owns the protocol). ADR-071 binds
acceptance to three identities and sizes the artefact: "a step checkpoint on
this machine is about 94 MB". ADR-072: "The acceptance statement stays outside
the archive it signs". ADR-073 inherits the three identities for revocation.
ADR-029 to ADR-032 stay Retired with those successors.
`docs/wave-delta-checkpoint-programme-runbook.md` Step 2 (lines 49-75) is this
packet: exit "the Git bundle, the signature proof, the sidecars and their
order, with a restore transcript produced on a machine that did not write it";
disciplines phylax and ephoros. `docs/wave-delta-issue-estate-2026-09-02.md`
lines 54-68 hold the issue's live review block.
`docs/fiat-controller-checkpoint-study.md` section 4 rejected option B
"Automate the complete standing checkpoint" because it "combines secret
handling, archive parsing, network mutation, GitHub/Drive authority, service
identity, and clean-machine proof"; the network, Drive and service parts are
now #862-#867 and ADR-028's mandatory-local amendment, which is why the
remaining part fits one run. `docs/fiat-checkpoint-identity-study.md` lines
140-150 record the #557 checkpoint's four digests (outer zip, bundle, capsule
zip, inner manifest) as the reason the identities stay distinct; its glossary
names "Carrier digest. #561's future `archive_sha256`".

The manual archives on this machine, read with `zipinfo`, `unzip -p` and
`stat` on 2026-09-06 (paths under
`/Users/c0rtexzer0/Projects/wildcat-skills/.hexaemeron/checkpoints/`):

| run | boundaries | zip bytes | shape |
| --- | --- | --- | --- |
| fiat-1021 | steps 1-5 | 93,441,034 to 94,230,830 | 118 entries; bundle 93,760,205 bytes deflated; capsule 96 files, 3,212,143 bytes; 12 outer members plus 8 sidecars |
| fiat-395 | steps 1-6 | 92,610,621 to 93,039,233 | sidecar `<hex>  fiat-395-checkpoint-step-1.zip` (97 bytes) |
| fiat-dokimasia | step 1 | 93,177,353 | sidecar names the zip differently again (118 bytes) |
| fiat-anamnesis | steps 1-3 | bundles 92,666,693 to 92,762,275 | unzipped members with per-member sidecars |
| fiat-1086, fiat-admit | steps 1-3 | manifest sidecar only (128 bytes) | no zip |

The fiat-1021 step-5 archive carries entry mtimes `26-Sep-01 23:07`, modes
`0644` and `0600` mixed, `steps/1,4,3,2,5` in directory order, deflate for all
files, a 274-byte outer sidecar naming the absolute path, an outer
`MANIFEST.json` (`fiat-step-checkpoint/v1`) whose `run.origin` is
`/Users/c0rtexzer0/Projects/wildcat-skills`, a `bundle-verify.txt` transcript
naming the absolute stage path, and `proof_list` reduced to "git bundle
verify reports a complete history". Its `commits` list records
`local_signature: G`, `signing_key: B83B60AE16F5DD1A`, both trailer counts and
GitHub verification per commit; that per-commit shape is kept. Its bundle
lists 7 refs including `main` and reports a complete history.

Measured today on this repository at `0bc39f27` (git 2.50.1, 18 CPUs):
`git bundle create main fiat/861-...` with default threads gave 100,790,849
bytes three times and 100,791,737 bytes once (four runs); with
`-c pack.threads=1` it gave 100,790,361 bytes, one digest, four times, in
1.72 s at 328 MB RSS (default threads 1.03 s, 331 MB). `git clone --no-checkout`
from the bundle took 1.02 s at 126 MB RSS and `git fsck --connectivity-only`
exited 0; `git bundle verify` alone is a header read (0.00 s). Packing that
bundle with stdlib `zipfile` stored: 26 ms, 100,790,501 bytes, byte-identical
across a 2 s mtime shift; `zip -X -D -j` default deflate: 1,977 ms,
100,470,196 bytes (0.32 % smaller); `zip -X -D -j -0`: 335 ms and different
bytes after the mtime shift. Python 3.14.6 with zlib 1.2.12. These numbers are
the reports under `.hexaemeron/reports/`.

### The last two merged pull requests that changed the subject

PR #1413 (issue #860, "Preserve checkpoint identity across verified restore",
merged 2026-09-06T11:31:06Z, merge `0bc39f27`). Carried forward, disposition
here:

| row | disposition here |
| --- | --- |
| `outer-archive-and-clean-machine-proof` duplicate #861 | this study |
| `service-intake-validation-and-publication` #862 | non-goal, by name |
| `locked-authority-and-signed-receipts` #863 | non-goal; `acceptance.current` is the literal `outside` and `acceptance/prior/` is reserved |
| `external-run-transition-fence` #864 | non-goal |
| `concurrent-descendant-lineage-and-resolution` #865 | non-goal; restore records nothing about siblings |
| `reconciliation-revocation-and-recovery-drills` #866 | non-goal |
| `atlas-resume-redraw-or-start-routing` #867 | non-goal |
| `same-account-post-read-mutation-exclusion` none | stays a stated boundary (section 11): stable-read checks, no OS lock claim |

PR #1069 (issue #560, moved to #860, "bind portable runs to an immutable
base", merged 2026-09-02T22:38:55Z, merge `f2770e00`, 1,201 controller lines).
Its body carries no `Carried forward` block; the run's unfinished work is in
its audit record (below) and its study's rejected option C, "let #561 invent
identity while building the outer archive", which this design keeps rejected:
the archive embeds the identity result and never derives one.

Also read: PR #1178 (issue #859, merged 2026-09-03T21:59:48Z) carries
`clean-machine-restore-transcript | duplicate | #861` (this study), #1175
adapter-timeout family (constraint 3.9), #1176 BSD `wc` (constraint 3.10),
#899 and #901 duplicates to the Fiat frontier. #899 (open, "`checkpoint
export` reads the next directive before deciding the boundary is acceptable")
is left open by name: `checkpoint archive` calls `_checkpoint_boundary`
unchanged and both accepted boundaries are `steps`-phase, so the integrate
branch is not reached; its fix belongs to #899, not here.

### Audit records read

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exited 0 with `committed=match` on every pair, so a synopsis was a permitted
view. Sources read directly where noted.

- `audit/rounds/fiat-860-restore-identity-continuation-r2.md` (source, 47
  lines). S1-R1-01 medium, fixed in `21faa1b0` (transparent restore recomputes
  the producer state digest and refuses any prior `checkpoint:restore`);
  S1-R2-01 low, fixed (Horos count). Round 3 none. Not checked: "the outer
  archive, signature, service, clean-machine, lineage, and routing work
  assigned to issues #861 through #867" and "exclusion of same-account mutation
  after the final userspace read". Leads not pursued: "the capsule manifest is
  unavailable to a later identity read, so its digest remains a recorded
  restore receipt field ... outer carrier proof belongs to #861" -- carried:
  `checkpoint.json.controller_capsule.manifest_sha256` and the capsule member
  make that digest independently replayable at inspect and restore (C7).
- `audit/rounds/fiat-560-bind-portable-runs-to-an-immutable-base-and.md`
  (source, 81 lines). S1-R1-01 low, S1-R2-01 low, S2-R1-01 medium, S2-R1-02
  medium (hostile source path echoed to stderr), S2-R1-03 low
  (`__pycache__` from a read-only command); all fixed and guarded (`c44550a1`).
  Leads not pursued: process-scoped Git config supplying the effective origin,
  reviewed and closed in round 2. Both S2-R1-02 and S2-R1-03 become
  risk-register lines here (`diagnostic-leak`, `read-only-bytecode`).
- `audit/rounds/fiat-557-portable-run-state-recovery-r2.md` (synopsis, plus
  the source's finding rows and Not-checked fields). 27 findings S2-R1-01
  through S4-R1-01, all fixed on their stacked branches; the ones this design
  inherits as boundaries: S2-R1-03 replaced output parent redirecting a
  capsule, S2-R2-01 refusal cleanup deleting an unowned replacement, S3-R1-02
  receipt path read outside the capsule, S3-R2-04 ledger scans materialising
  19,294,150 bytes, S3-R2-07 non-appendable ledger prefix, S3-R3-01 to 03 moved
  homes redirecting writes, S4-R1-01 a fresh destination falling through to
  `init`. Not checked, every round: "the outer archive ... not exercised" --
  this run exercises it.
- `audit/rounds/fiat-859-reinstate-the-wave-delta-distributed-checkpo.md`
  (synopsis, plus source rounds Step 7). 24 findings across 21 rounds, all
  fixed or dispositioned in PR #1178; S6-R1-01 and S6-R3-01 (audit records
  misreporting suite runs) are why every count in this study names the command
  it came from.
- `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md`
  (synopsis and source rows). S1-R1-01, S1-R2-01, S2-R1-01, all fixed; Horos
  classifier work; nothing checkpoint-bearing except that this run produced the
  first manual checkpoint note, now unresolvable.
- `plugins/hexaemeron/audit/AUDIT.md` via `AUDIT_SYNOPSIS.md`: F-01 to F-06
  fixed 15 August 2026; `[missing legacy field: audit-schema]`, `covered`,
  `not-checked`, `elenchus-verdict` remain unknown. Leads not pursued: the
  Pashov skills were not exercised (Python plugin). `audit/AUDIT.md` (root
  shared log) mentions checkpoint zero times (`grep -c -i checkpoint`).

### In the organisation and outside

`wildcat-finance/fiat-checkpoints` does not exist; ADR-070 assigns it the
service half and `wildcat-finance/shoggoth-wave-atlas` the discovery half;
neither is touched. Outside: the ZIP format (PKWARE APPNOTE 6.3.10) fixes the
central directory, general-purpose flags (bit 0 encryption, bit 11 UTF-8),
method 0 stored and the ZIP64 records this design refuses; Python 3.14
`zipfile` (`ZipInfo.date_time`, `external_attr`, `ZIP_STORED`,
`allowZip64=False`); `git-bundle(1)` (`verify`, prerequisites, "complete
history"), `git-verify-commit(1)` with `gpg.format` `openpgp` or `ssh` and
`gpg.ssh.allowedSignersFile`, `pack.threads`; reproducible-builds practice of
fixed timestamps and sorted entries; in-toto and DSSE via Ariadne for the
acceptance statements #862-#863 will add outside the archive.

## 3. Constraints and non-goals

1. Starting ref `main` at `0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`, equal
   to `origin/main` and to `state.base`; run anchor SHA-256
   `60739d6b5185d9152b29ee26ea55f2d0d75b9cce71887d1cc051e13a6318c155`; run
   branch `fiat/861-outer-checkpoint-archive-export-and-restore`; origin
   `/Users/c0rtexzer0/Projects/wildcat-skills/.claude/worktrees/fiat-861-fdb3a2`.
2. Toolchain: the `.python-version` interpreter 3.14.6 (`pyproject.toml`
   declares the minor); stdlib only, no dependency added; git 2.50.1 (Apple
   Git-155); `gpg` 2.x at `/opt/homebrew/bin/gpg`; docker 29.5.2 with colima
   running for the demo. Local signing config is `gpg.format=openpgp`,
   `commit.gpgsign=true`; `main`'s merge commits are signed by
   `B5690EEEBB952194` and verify locally as `E` (key absent), run commits by
   `B83B60AE16F5DD1A` as `G`; `git verify-commit HEAD` exits 1 on `main`. The
   proof therefore scopes to the run's receipted commits
   (`push.verified_commits`), never to merges on the integration branch.
3. Fiat is `fiat-v5.53.1`; this change alters the controller, so under
   `plugins/hexaemeron/skills/VERSIONING.md` it is a `generation`. The runbook
   carries Protasis's `version-relations` block naming
   `plugins/hexaemeron/skills/fiat/EVOLUTION.md` and no concrete Fiat version
   token outside it; the ledger row lands in the last step.
4. Suites: `python3 scripts/run_checks.py` is the entry point
   (`tests/check-map-v1.json`; root `python3 -m unittest discover -s tests`,
   Hexaemeron `python3 plugins/hexaemeron/tests/run_tests.py [--jobs N]`, never
   bare discover inside the plugin); `python3 scripts/portable_promise_machine.py
   check` (the portable runtime is absent in this tree and the check exits 0).
5. Every commit that adds or edits files runs
   `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` after
   `git add` (#1063); `.githooks/pre-commit` refuses a staged tree that
   `$GIT_DIR/LAST_GREEN` does not name; `core.hooksPath` is `.githooks` here.
6. Lints on changed prose and code: imprimatur, brevitas, `phylax.py plugins
   tests`, `ephoros.py plugins tests`, `hypomnema.py README.md AGENTS.md
   .agents/skills/promise-machine/SKILL.md
   .agents/skills/promise-machine/PORTABLE.md plugins docs`.
7. The security suite is waived (no Solidity); the mechanical audit set per
   round is Phylax, Ephoros and Hypomnema.
8. Controller invariants kept: `checkpoint export` and `restore` semantics,
   schema, ceilings and the compatibility set are unchanged; `checkpoint
   archive` takes the run lock through `verify_run` exactly as export does and
   appends no ledger entry; the store path is derived from state, never
   supplied; an existing boundary directory refuses.
9. Root-suite runs are held on a clean detached snapshot (assumption 8), and
   `tests/test_agent_instruction.py`'s adapter-timeout family is
   non-deterministic under load (#1175): a red root run with only
   `WAI-E-ADAPTER.TIMEOUT` failures is rerun once, not fixed here.
10. Runbook exit commands are BSD and GNU neutral: no `wc -l | grep -qx`
    (#1176); counts go through `python3 -c` or `grep -c`.
11. Decision numbering: the new record is drafted as
    `docs/decisions/draft-build-the-outer-checkpoint-archive-natively.md` and
    numbered at sync by `decision_assignments.py plan/apply/replay` from the
    integration base (Hypomnema "Assign the number from the integration base").
12. Determinism rule for the bundle: `git -c pack.threads=1 bundle create`,
    measured (section 2); default threads produced two different bundles.

Non-goals, from the issue and ADR-028: no network upload, service,
authentication, object retention, acceptance signing or publication fencing
(#862-#867); no restore over a non-empty directory; no restoring uncommitted
work or credentials; no reliance on the source clone, reflog, cache or
contributor delegation handle; no service repository or cloud resource; no
change to `snapshot_id` derivation or the capsule schema; no compression (a
stored container is the design, section 4); no per-member sidecars inside the
zip (assumption 3); no second restore of the same archive into an occupied
destination; no Drive or issue-note publication (retired by ADR-028); no
resume: the restored run waits for the operator's explicit `hexctl next`.

Boundaries the build holds:

- Always: `run_checks.py` and the Hexaemeron runner green on the clean
  snapshot before a commit; imprimatur then brevitas on every shipped document;
  Horos scan after `git add`; a recorded Metron measurement before any change
  that claims speed; `pack.threads=1` on every bundle build.
- Ask first: adding a dependency; changing `fiat-controller-checkpoint/v1`,
  the compatibility set, `snapshot_id`, or the store path; touching CI or the
  check map beyond adding owned paths; widening a ceiling.
- Never: commit a key, keyring or token; write outside the private stage or
  the disposable restore root before verification; replace an existing
  checkpoint directory; delete a failing test; print entry content or gpg
  output in a diagnostic; call `init` for a restored run; follow a symlink in
  any path the archive or capsule names.

## 4. Design options

### A. `native-subcommands` (selected)

`hexctl checkpoint archive|inspect|restore --archive` inside the controller.
Packing through stdlib `zipfile` with fixed metadata and stored entries; bundle,
signature and key handling through `bounded_tool` (`git`, `gpg`) with fixed
argv; a disposable `GNUPGHOME` (mode 0700, `--no-autostart`, removed after
use) seeded only from `proof/pubkey.asc` and pinned to the manifest
fingerprints; SSH signatures verified with `gpg.ssh.allowedSignersFile`
pointing at `proof/allowed_signers` built from the same manifest. Export calls
the existing capsule exporter in-process, then `checkpoint identity` in-process
for the identity member, builds the bundle from exactly `_checkpoint_refs`,
joins bundle heads, capsule `boundary.refs` and manifest `refs` three ways,
writes every member to a hidden sibling stage, computes digests, writes
`checkpoint.json` last, packs in sorted order, re-reads and re-verifies the
packed zip through the inspector, writes the sidecar, and publishes the
boundary directory by no-replace rename. Restore runs the inspector, creates
the repository, extracts the capsule under the git directory, calls the
existing relocation transaction and reads back identity.

Trade: the controller grows by one archive parser and one key-handling path,
which is the join ADR-028 declined for the previous generation. The cost is
accepted because the parser is a bounded reader of a format the controller
itself wrote, the mutation it feeds is the already-audited relocation
transaction, and every refusal happens before that transaction. One process
means one compatibility set, one read boundary, one test harness.

### B. `sidecar-script`

`plugins/hexaemeron/skills/fiat/scripts/checkpoint_archive.py` drives `hexctl
checkpoint export` and `restore` as subprocesses and packs with `zipfile`.

Trade: archive parsing leaves the controller process, but the script needs
the controller's path-safety, stable-read and bounded-tool helpers, so it
either imports `hexctl` (the same process after all) or duplicates them; two
entry points then agree on the compatibility set, the boundary rule and the
identity join by convention. Measured identical to A on packing; one more
spawned program per export.

### C. `inspector-only`

Keep the manual procedure and add `checkpoint inspect` for whatever the agent
built by hand.

Trade: the cheapest change, but the procedure fixes no timestamp, order or
mode rule (measured: the section contains none of `mtime`, `timestamp`,
`sorted entries`, `normalis`, `deterministic`), so two exports of one state
are not byte-identical, and it names no restore command, so a receiver still
needs the prose. Fails the issue's criteria 2 and 3.

### D. `external-archiver`

The three subcommands as in A, but packing and unpacking by spawning `zip(1)`
and `unzip(1)` with pinned flags.

Trade: `zip -X -D -0` reads entry times from the filesystem, so a rebuild
after any mtime change differs (measured), determinism would rest on
normalising the staging tree instead of the writer, and the inspector would
trust `unzip`'s path handling at the exact boundary the hostile fixtures
attack. Info-ZIP 3.0 (2008) and UnZip 6.00 (2009) also become clean-machine
dependencies.

### The record

`.hexaemeron/design-evidence.json` (`protasis-design-evidence/v1`), produced by
`python3 .hexaemeron/measure_design.py` from `.hexaemeron/design-model.json`;
24 resolved reports under `.hexaemeron/reports/`, 24 pending cells.

| criterion | concern, owner | A | B | C | D |
| --- | --- | --- | --- | --- | --- |
| `byte-identical-rebuild` gate | correctness, elenchus | pass | pass | fail | fail |
| `restore-without-source-clone` gate | recovery, elenchus | pass | pass | fail | pass |
| `capsule-contract-reused` gate | compatibility, hypomnema | pass | pass | pass | pass |
| `pack-wall-milliseconds` minimise | time, metron | 26 | 26 | 1,977 | 335 |
| `carrier-bytes` minimise | space, metron | 100,790,501 | 100,790,501 | 100,470,196 | 100,790,483 |
| `subprocess-boundaries-per-export` minimise | compatibility, phylax | 2 | 3 | 4 | 3 |

C and D fail a selection gate; A dominates B on the third metric with the
other two equal (both use the same writer, measured once). `unique-frontier`
selects A; `design_evidence.py --transition design-lock` exits 0.

Pending conformance, all `native-subcommands`, resolver
`python3 .hexaemeron/measure_design.py --conformance <criterion>`:

| criterion | gate | blocks |
| --- | --- | --- |
| `existing-checkpoint-suites-green` | the 82 existing checkpoint and identity tests pass | `step:3` |
| `hostile-fixtures-refused` | 35 `test_hostile_*` tests pass | `step:4` |
| `offline-empty-directory-restore` | `-k restore_from_archive` tests pass | `step:5` |
| `fixture-export-wall-milliseconds` | at most 15,000 | `integration` |
| `fixture-archive-bytes` | at most 201,581,002 | `integration` |
| `clean-machine-restore-transcript` | transcript fields hold | `integration` |

### Details the runbook binds

- Refusal classes, each one bounded stderr line and exit 1, no entry content:
  `boundary-unaccepted`, `worktree-dirty`, `boundary-occupied`,
  `ref-disagreement`, `bundle-incomplete`, `bundle-oversized`,
  `signature-unverified`, `signature-format-unsupported`,
  `identity-unavailable` (export continues with `status: unavailable` only for
  a legacy symbolic base; any other identity refusal stops export),
  `secret-shaped-member`, `entry-name-policy`, `entry-limit`, `entry-mode`,
  `entry-compressed`, `entry-encrypted`, `zip64-present`, `trailing-data`,
  `manifest-mismatch`, `outer-digest-mismatch`, `sidecar-mismatch`,
  `destination-occupied`, `schema-unsupported`, `identity-mismatch`,
  `acceptance-self-reference`.
- Secret scan at export over every outer member and over `state.json`,
  `ledger.jsonl` and every opaque controller file: PEM private-key blocks,
  `-----BEGIN OPENSSH PRIVATE KEY-----`, `ghp_[A-Za-z0-9]{36}`,
  `github_pat_[A-Za-z0-9_]{22,}`, `AKIA[0-9A-Z]{16}`, `xox[baprs]-`. A hit
  refuses with `secret-shaped-member`; nothing is redacted in place.
- Export result `fiat-checkpoint-archive-export/v1`: `archive`, `sidecar`,
  `outer_sha256`, `manifest_sha256`, `snapshot_id` or `null`, `bundle_sha256`,
  `entries`, `bytes`, `boundary`, `next`, `timing_ms` per stage (`export`,
  `identity`, `bundle`, `proof`, `pack`, `inspect`, `publish`).
- Inspect result `fiat-checkpoint-inspect/v1`: `outer_sha256`, `entries`,
  `bytes`, `findings` (list of class names, empty on success), `bundle`,
  `signatures` (per commit: `sha`, `status`, `fingerprint`, `trailers`),
  `identity`, `refs`.
- Signature proof `fiat-checkpoint-signature-proof/v1`: per receipted commit
  `sha`, `format`, `status` (`G` required), `fingerprint`, counts of
  `Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` and `Wildcat-Origin:
  shoggoth` (exactly one each), and the recorded GitHub verification from the
  push receipt. No raw `gpg` output.
- Restore creates `remote.origin.url` from `run.repository` (assumption 7),
  checks out `config.git.base`, refuses if the working commit does not descend
  from `run.initial_base_sha`, and leaves the relocation transaction to the
  existing code including its marker, retry and refusal rules.

## 5. Risk register seed

The Python register concerns: hostile input, subprocess and filesystem
handling, secret material, partial writes and a killed long run, plus the
three-identity join this archive exists to carry.

```risk-register
zip-slip | entry names read from the central directory | traversal, absolute, backslash, drive-letter and control-character names refuse before any path is formed
name-collision | case-insensitive and Unicode-normalising filesystems | duplicate, casefold-equal and non-NFC names refuse before extraction
special-entries | external_attr modes and general-purpose flags | symlink, device, FIFO, socket, directory, non-0644, compressed, encrypted and ZIP64 entries refuse
zip-bomb | declared and actual sizes | entry count, per-entry and total expanded ceilings are enforced from the central directory and re-enforced while streaming; stored-only makes ratio 1
trailing-data | bytes outside the ZIP structures | a prefix, gap or suffix outside the central directory and local headers refuses
manifest-join | checkpoint.json against members, capsule MANIFEST and bundle heads | every entry digest and size, the capsule manifest digest and the three ref maps agree or restore refuses before the marker
outer-digest | the --sha256 argument and the sidecar | the digest is recomputed over the exact zip bytes; a digest found inside the archive is never used
bundle-completeness | git bundle verify in a disposable root | prerequisites, a hash algorithm other than the recorded one, or a head not in the manifest refuse
bundle-nondeterminism | pack-objects threading | every bundle is built with pack.threads=1 and export re-reads the packed bundle digest into the manifest
signature-scope | which commits the proof covers | only receipted run commits are verified, each must be G under the pinned fingerprints, trailer counts exactly one each; merges on main are never claimed
keyring-handling | the disposable GNUPGHOME and allowed_signers | created 0700 under the scratch root, seeded only from the archive's key member, agent never started, removed after use, never the operator's keyring
identity-join | snapshot_id in identity/ against the restored state | restore recomputes identity from relocated state and refuses a mismatch or a claimed unavailable when identity can be minted
remote-url-derivation | remote.origin.url written at restore | derived only from a validated owner/name, never fetched, never carries credentials
source-path-leak | checkpoint.json, README, proof | no absolute path, environment value or hostname appears; the export scans its own members
secret-shaped-member | controller files entering the capsule | the named secret patterns refuse export; nothing is redacted silently
diagnostic-leak | stderr on refusal | one class name, no entry name, content, gpg output or JSON value
subprocess-argv | git and gpg invocations | fixed argv through bounded_tool, no shell, paths validated before they become arguments, dash-prefixed refs impossible
partial-publish | the boundary directory and sidecar | build in a hidden sibling stage, publish by no-replace rename, sidecar written before the rename, an occupied path never replaced
interrupted-restore | the disposable restore root and the relocation marker | the existing marker rules govern; a killed run leaves the destination without active state or with the marker that resumes it
destination-emptiness | the restore destination | must be absent or an empty directory, checked through an opened descriptor, never a symlink
read-only-bytecode | inspect and identity imports | no __pycache__ or other file is written outside the scratch root
concurrent-mutation | state, ledger and refs during export | stable stat and re-read before publication as export already does; same-account mutation after the last read is a stated boundary, not a claim
version-compatibility | controller version in checkpoint.json and MANIFEST | both must be in the compatibility set; unknown archive schema refuses before extraction
acceptance-self-reference | entries under acceptance/ | acceptance/current refuses; prior receipts are carried unverified as bytes with digests and counted
hostile-fixture-set | the inspector test module | one test per id: traversal-dotdot absolute-path backslash-separator drive-letter duplicate-name case-fold-collision non-utf8-name control-character-name nfc-mismatch-name directory-entry symlink-entry special-mode-entry setuid-or-executable-mode compressed-entry encrypted-entry zip64-record entry-count-over-limit expanded-size-over-limit bundle-over-limit size-mismatch trailing-data tampered-manifest unmanifested-member missing-member wrong-outer-digest tampered-sidecar wrong-receipt missing-object ref-map-mismatch secret-shaped-member self-referential-acceptance identity-mismatch unknown-schema-version signature-proof-mismatch absolute-source-path-in-manifest
```

Around the block: `wrong-receipt` is the capsule ledger prefix altered so the
capsule manifest digest no longer matches `checkpoint.json`; `missing-object`
is a bundle rebuilt with a prerequisite so `git bundle verify` names it;
`identity-mismatch` is an `identity/` member whose `snapshot_id` differs from
the recompute. Each fixture is a byte-level specimen built by the test, not a
checked-in binary.

## 6. Glossary seeds

- **Outer archive:** the `checkpoint.zip` carrier and its beside-it sidecar; identified by the outer digest, a carrier identity.
- **Content manifest:** `checkpoint.json`, the closed `fiat-checkpoint-archive/v1` object listing every entry's path, bytes and SHA-256 and joining the three identities.
- **Controller capsule:** the `fiat-controller-checkpoint/v1` directory `checkpoint export` writes; carried byte-exact under `controller-capsule/`.
- **Semantic identity:** `snapshot_id` from `checkpoint identity`; unchanged by repacking; carried under `identity/`.
- **Signature proof:** `proof/signatures.json`, per-commit verification results under the pinned fingerprints; the transcript the receiver recomputes.
- **Boundary directory:** `step-<n>-<sha>` or `audit-verdict-step-<n>-loop-<l>-<sha>` under the checkpoint store; new per boundary, never replaced.
- **Disposable root:** the scratch directory inspect and restore write to before any verification passes; `<destination>/.git/fiat-checkpoint-restore/<outer-sha256>/` at restore.
- **Stored entry:** ZIP method 0; the only method the archive writes or the inspector accepts.
- **Hostile fixture:** a byte-level specimen the inspector must refuse; ids in section 5.
- **Clean machine:** a container with no network, an empty keyring and only the archive, sidecar and controller copied in.
- **Refusal class:** the single kebab-case token a command prints on exit 1.

## 7. Sources

- Issue #861 body (read 2026-09-06 via `gh issue view 861 --json body`): review
  block 3 September 2026, original filing archive contract, acceptance
  criteria, budget and failure sections.
- PR #1413 and PR #1069 bodies (`gh pr view`); PR #1178 body for its
  `carryover` block; merges located with `git log --merges --first-parent --
  plugins/hexaemeron/skills/fiat/scripts/hexctl.py`.
- `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`,
  `ADR-069-` to `ADR-073-`, `ADR-029-` to `ADR-032-` (status lines).
- `plugins/hexaemeron/skills/fiat/references/push-discipline.md` lines
  296-386, `controller-checkpoint.md`, `checkpoint-identity.md`;
  `plugins/hexaemeron/skills/fiat/SKILL.md` lines 145-155, 624-629, 897-903.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at `0bc39f27`, lines
  cited in section 2; `plugins/hexaemeron/tests/test_hexctl_checkpoint.py`,
  `test_hexctl_checkpoint_identity.py`; `tests/check-map-v1.json`; `AGENTS.md`
  lines 263-358; `plugins/hexaemeron/skills/VERSIONING.md` lines 20-35,
  107-165; `plugins/hexaemeron/skills/fiat/EVOLUTION.md` current frontier.
- `docs/fiat-controller-checkpoint-study.md` sections 4, 10, 12;
  `docs/fiat-checkpoint-identity-study.md` lines 140-160, 585-596;
  `docs/fiat-checkpoint-restore-identity-study.md`;
  `docs/wave-delta-checkpoint-programme-runbook.md` lines 49-75;
  `docs/wave-delta-issue-estate-2026-09-02.md` lines 54-68.
- Audit records named in section 2; `audit_synopsis.py --check .` output.
- Manual archives under `/Users/c0rtexzer0/Projects/wildcat-skills/.hexaemeron/checkpoints/`
  (fiat-1021, fiat-395, fiat-dokimasia, fiat-anamnesis, fiat-1086, fiat-admit)
  read with `zipinfo`, `unzip -p`, `stat -f %z`, `git bundle list-heads`.
- Measurements: `.hexaemeron/measure_design.py`, `.hexaemeron/design-model.json`,
  `.hexaemeron/reports/*.json`; the bundle-determinism runs in section 2
  (`git bundle create` four times each with default and single threads).
- Protasis `SKILL.md` and `scripts/design_evidence.py` (record-directory
  copies match the plugin root byte for byte: `protasis.py` `2ff1f6d3...`,
  `design_evidence.py` `4f38e555...`).
- Discipline contracts: `plugins/hexaemeron/skills/{ephoros,phylax,metron,elenchus,hypomnema}/SKILL.md`,
  `metron/references/budget-check.md`.
- Outside: PKWARE APPNOTE 6.3.10; Python 3.14 `zipfile` documentation;
  `git-bundle(1)`, `git-verify-commit(1)`, `git-config(1)` `pack.threads`,
  `gpg.ssh.allowedSignersFile`.

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) applies to steps 2,
4 and 5: the commands run unattended inside the controller loop and their
failure blocks the next directive. The questions:

1. Was this boundary's checkpoint saved, where, and under which three
   identities? Answered by the `fiat-checkpoint-archive-export/v1` object on
   stdout (`archive`, `outer_sha256`, `manifest_sha256`, `snapshot_id`) and by
   the sidecar's existence at the derived path; `hexctl next` after a boundary
   names the same path.
2. When a save fails, which stage refused? Answered by the single refusal
   class on stderr and by `timing_ms` naming the stages that completed; no
   stage writes a partial boundary directory.
3. When a restore on another machine fails, which check refused and at which
   member, without printing the member? Answered by
   `fiat-checkpoint-inspect/v1.findings` (class names, entry index, never
   content) and by the relocation marker the existing transaction leaves.
4. Did the restore finish, and what is the one permitted next action? Answered
   by `fiat-checkpoint-archive-restore/v1` carrying the native restore object,
   `verify` exit, `status` digest and semantic `next`.

No persistent telemetry, metric or alert is added: the commands are
interactive, the fiat-860 record set the same rule for read-only checkpoint
commands, and the transcript file is the durable record for the demo.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) applies to every step
that reads an archive, spawns a program or touches key material.

- Archive bytes from elsewhere: everything in the zip is hostile until the
  outer digest, central-directory limits, name policy, entry digests and the
  three-way ref join pass; extraction happens only into the disposable root
  and only after the central-directory checks. Control: the inspector runs
  first in both `restore --archive` and `archive` (self-check of the packed
  bytes).
- Subprocesses: `git` and `gpg` through `bounded_tool` with fixed argv, cap
  and timeout; `pack.threads=1`, `--no-tags`, explicit refspecs; no shell; a
  bundle or destination path is validated and opened before it is an argument.
- Key material: public keys only; a disposable `GNUPGHOME` under the scratch
  root, never the operator's; `allowed_signers` built from the manifest, never
  from the archive's free text; the fingerprints pinned from the manifest and
  compared to what `gpg --import` reports.
- Secrets and personal data: the export scan (section 4) refuses secret-shaped
  members; the manifest carries no path, hostname or environment value;
  committer addresses already in Git history are carried as Git carries them,
  nothing more.
- Filesystem writes: hidden sibling stage for export, `.git/fiat-checkpoint-restore/<sha>/`
  for restore, both opened by descriptor and never through a symlink; the
  destination must be new or empty; no write to `.hexaemeron` before the
  existing relocation transaction owns it.
- Network: none; `remote.origin.url` is written, not used.
- Dependencies: none added; Info-ZIP tools are not required by A.
- Model output: none enters these commands.

## 10. The budget, or its absence

[Metron](../plugins/hexaemeron/skills/metron/SKILL.md) applies: the issue
requires measured limits, and section 2 recorded the baselines. Named
fixture: this repository at `0bc39f27` bundled as `main` plus the run branch
with `pack.threads=1` (100,790,361 bytes), and, from step 2 onward, this run's
own `step-<n>` checkpoint of the same repository. Baseline components measured
2026-09-06 on this machine: bundle build 1,720 ms at 328 MB RSS, clone from
bundle 1,020 ms at 126 MB, stored pack 26 ms, total 2,766 ms; export limit is
set at 15,000 ms (about 5.4 times the component sum, leaving room for the
capsule export, identity and proof stages that are not yet measured).

Budgets, declared in
`plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json`
(step 1), all `lower_is_better`, variance 0.25:

| name | unit | limit | derivation |
| --- | --- | --- | --- |
| `checkpoint.archive.export_wall_ms` | ms | 15000 | 5.4 x 2,766 ms |
| `checkpoint.archive.inspect_wall_ms` | ms | 10000 | 10 x a 1 s digest-and-verify pass over 100 MB |
| `checkpoint.archive.restore_wall_ms` | ms | 20000 | clone 1,020 ms plus the audited relocation, x10 |
| `checkpoint.archive.bytes` | bytes | 201581002 | 2 x 100,790,501 measured |
| `checkpoint.archive.expanded_bytes` | bytes | 209715200 | 2 x (bundle plus 3,212,143-byte capsule) |
| `checkpoint.archive.export_peak_rss_bytes` | bytes | 1073741824 | 3.3 x 328 MB measured |

The measuring command, run in step 5 against the step-4 checkpoint and
written to `.hexaemeron/metron/run.json` then copied to the baseline:

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/checkpoint_measure.py \
  --archive <origin>/.hexaemeron/checkpoints/<wt>/step-4-<sha>/checkpoint.zip \
  --sha256 <outer-hex> --out .hexaemeron/metron/run.json
python3 plugins/hexaemeron/skills/metron/scripts/metron.py check \
  --budgets plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json \
  --baseline plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-baseline.json \
  --run .hexaemeron/metron/run.json
```

`checkpoint_measure.py` wraps `/usr/bin/time -l` (macOS) or `-v` (Linux)
around `archive`, `inspect` and `restore --archive` and reads `timing_ms`
from their results. Two of the six are also design-record conformance gates
(section 4). Service-facing p95 budgets are deferred to #862, as the issue
says. Any speed change that weakens a digest, signature, redaction or size
check is refused by the risk register, not traded.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) applies.

What stops the run: any refusal class in section 4 exits 1 before the
boundary directory, the sidecar, the destination repository or active
controller state exists; a killed export leaves at most a hidden sibling stage
and no `checkpoint.zip`; a killed restore leaves the disposable root and the
existing relocation marker, which the existing retry rules resume or refuse.
The controller is left at the same accepted boundary and `next` repeats the
save. `inspect` never writes outside its scratch root. A refusal names one
class, never a member, path fragment, JSON value or `gpg` line.

Guard convention: every fix lands with a test that fails on the parent and
passes on the fixed tree, named `test_<class>_refuses_before_<boundary>` for
refusals and `test_<behaviour>` otherwise, in
`plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py`; the Elenchus
runner report comes from
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
which the runbook's `Tests` field names for every step. Stated boundary,
carried from #860: stable stat-and-reread checks cover the named mutation
windows and claim no operating-system lock against another process of the
same account.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) applies.

- Building the outer archive natively reverses ADR-028's "Complete
  standing-checkpoint automation. Rejected for this controller generation".
  Home: a new record drafted as
  `docs/decisions/draft-build-the-outer-checkpoint-archive-natively.md`
  (numbered at sync, constraint 3.11) stating the three commands, the stored
  container, the single content manifest replacing member sidecars, the
  fixed layout, the `pack.threads=1` rule, the disposable keyring, the
  no-fetch remote URL, and the rejected options B, C and D with the measured
  reasons; plus one dated amendment appended to ADR-028 after its 2026-09-02
  amendment, pointing at the new record and changing no operative clause.
  Both land in step 1 before controller code.
- The archive contract (`fiat-checkpoint-archive/v1`, results, proof,
  ceilings, refusal classes, restore transaction) lives in a new
  `plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`;
  `controller-checkpoint.md`'s `## Outer recovery boundary` and
  `checkpoint-identity.md`'s carrier sentence point at it.
- The operational rule lives in `push-discipline.md` `## Step checkpoint`,
  rewritten to the three commands and the direct hand-off values, dropping the
  404 comment link; `SKILL.md` steps 3 and the post-push paragraph point at it;
  a `fiat-checkpoint-archive` Promise Machine contract joins
  `fiat-controller-checkpoint`.
- The Fiat version, promise, boundary and rejected scope live in the next
  generation row of `plugins/hexaemeron/skills/fiat/EVOLUTION.md` and in
  `SKILL.md`'s metadata; the frontier stays `state-shape-validation` with the
  issue 363 job untouched.
- Budgets and baseline live beside the controller:
  `plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json`
  and `checkpoint-archive-baseline.json`.
- This study and its runbook are run artefacts, committed byte-identical as
  `docs/fiat-checkpoint-archive-study.md` and
  `docs/fiat-checkpoint-archive-runbook.md`, pointing at the record and never
  described as the decision.
- The clean-machine transcript is committed as
  `docs/fiat-checkpoint-archive/clean-machine-transcript.json` and its text
  log beside it; the design record's `clean-machine-restore-transcript`
  report binds it.
- Deferred, by name, to #862 and #863: acceptance statements, the `prior`
  receipt schema and who signs; the archive reserves their entry prefix and
  nothing else.

No alert runbook is needed because section 8 adds no alert. A decision made
after this study that changes the layout, ceilings, refusal classes, store
path or step shape is a dated study amendment before implementation.

### Amendment -- 2026-09-07

**What changed.** Constraint 3.4 loses `python3
scripts/portable_promise_machine.py check` and its claim that the check exits 0
with the portable runtime absent: the check exits 1 in every checkout since
`493d7c72` ("Stop carrying the payload here", issue #949) removed
`.agents/skills/promise-machine/runtime`, nothing in `tests/check-map-v1.json`
or the hosted workflows runs it, and the `AGENTS.md` suites list that names it
is stale. Constraint 3.11 and the first item of section 12 move the new
record's home from
`docs/decisions/draft-build-the-outer-checkpoint-archive-natively.md` to
`docs/decisions/drafts/build-the-outer-checkpoint-archive-natively.md` in
Hypomnema's authoring shape (`# Decision:` heading, dated `## Status`, `##
Context`, `## Decision`, `## Alternatives`, `## Consequences`), cited from
ADR-028 and from `checkpoint-archive.md` by its stable slug reference rather
than a relative path, because `decision_assignments.py` indexes drafts only
below `docs/decisions/drafts/` (`DRAFTS`, line 49) and Hypomnema's "Write the
record when reversing gets expensive" fixes that directory; a Markdown file
directly under `docs/decisions/` that is neither numbered nor a draft is
tolerated only while inherited unchanged from the base. The design record, its
candidates, criteria and selection are untouched.
**Why.** Both facts were taken from `AGENTS.md` and from the two inherited
`docs/decisions/draft-*.md` files instead of from the scripts that enforce
them. Found in Step 1 when the check exited 1 at the entry commit `0bc39f27`
and the draft's numbering path was compared with the allocator's.
**Steps touched.** Step 1 Exit and Files; Steps 2, 3, 4 and 5 Exit.
**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds; exit
broken. Step 3: entry holds; exit broken. Step 4: entry holds; exit broken.
Step 5: entry holds; exit broken.
