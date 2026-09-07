# Runbook: outer checkpoint archive export and restore

Derived from `.hexaemeron/study.md`, whose study receipt binds SHA-256
`d410ae1ca0008a45befe01df8f79f08027ab9199eaebaa11a004da4760611411`. The run
starts from `main` at `0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a` on run branch
`fiat/861-outer-checkpoint-archive-export-and-restore` for task issue
[skills#861](https://github.com/wildcat-finance/skills/issues/861). Five steps,
in the order the receipted design record's pending conformance cells name
(`step:3`, `step:4`, `step:5`, `integration`). Renumbering them means a new
run, because the receipted record is immutable.

Assuming, unless corrected:

1. `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` (`hexctl.py` lines 448-470)
   gains the new generation's own version in Step 5, as each of its 19 members
   did at its own generation; `hexctl.py` lines 15754-15755 refuse export and
   restore when the running version is absent from the set. Nothing is
   removed, so this is the ledger row's consequence, not the ask-first change
   the study names.
2. Every step's exit suites run on a clean detached snapshot of the step's
   head commit (`git worktree add --detach <scratch> <head-sha>`), because two
   `tests/test_agent_instruction_corpus*` tests read this run's own
   `.hexaemeron/design-evidence.json` (issue #1228, study assumption 8). A red
   root run whose only failures are `WAI-E-ADAPTER.TIMEOUT` is rerun once
   (issue #1175).
3. From Step 2's post-push boundary onward this run's own step checkpoints are
   produced by the new `checkpoint archive`. Step 4's boundary run is wrapped
   in `/usr/bin/time -l` with its stdout kept at
   `.hexaemeron/metron/step-4-export.json` and the time output at
   `.hexaemeron/metron/step-4-export.time.txt`, because `_checkpoint_boundary`
   accepts only a `done:push` or active `audit-verdict` ledger tail, so export
   wall time and peak RSS cannot be re-measured from a restored copy later.
4. The clean-machine image is built once, with network, from `python:3.14-slim`
   plus the `git` and `gnupg` packages the controller shells out to; the demo
   container itself starts with `--network none`. The study fixes the base
   image, the network rule and the empty keyring; the two tools are what the
   controller, not the archive, needs.
5. Every controller refusal named below exits 1 with one stderr line carrying
   only the refusal class. Every Elenchus report path is fresh, because
   `run_tests.py` refuses an existing `--elenchus-report` target.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 101172ad264e56b0910cc64e8f11662da8b7f874ca030c3da76ba7cfacf6db91
candidate | native-subcommands
```

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
```

The relation is not a reservation: the ledger row, the `SKILL.md` metadata and
the compatibility-set entry are written in Step 5 and resolved against the
exact integration base at `done resolve-versions`. The held issue #363
frontier `state-shape-validation` and its digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa` stay
unchanged.

## Step 1: Scaffold the archive contract, decision draft, budgets and tracked specification

**Goal.** Put every document the controller change is built against into the
tree before controller code: the archive contract, the decision draft with its
ADR-028 amendment, the Metron budgets, the tracked study and runbook, and the
inventory tests that pin their agreement.

**Entry.** Run branch `fiat/861-outer-checkpoint-archive-export-and-restore`
at `0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`, with the study, design record
and runbook receipted, `hexctl status --field phase` printing `steps`, and no
tracked change in the worktree.

**Exit.** Six documents and five tests exist and every command below exits 0.
`docs/decisions/draft-build-the-outer-checkpoint-archive-natively.md` carries
`## Status` reading `Proposed, <date written>`, is unnumbered on purpose
(numbered at sync by
`python3 plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py plan|apply|replay`
from the integration base), and states the three commands, the stored
container, the single content manifest replacing member sidecars, the fixed
nine-entry layout, the `pack.threads=1` rule, the disposable keyring, the
no-fetch `remote.origin.url`, and the rejected options B, C and D with their
measured readings (pack 26, 26, 1,977 and 335 ms; carrier 100,790,501,
100,790,501, 100,470,196 and 100,790,483 bytes; 2, 3, 4 and 3 spawned
programs).
`docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`
gains one `## Amendment: Native outer archive (<date written>)` after
`## Amendment: distributed layer reinstated (2026-09-02)`, pointing at the
draft record and changing no operative clause; its status stays Accepted.
`plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md` states the
contract: schemas `fiat-checkpoint-archive/v1`,
`fiat-checkpoint-archive-export/v1`, `fiat-checkpoint-inspect/v1`,
`fiat-checkpoint-archive-restore/v1`, `fiat-checkpoint-signature-proof/v1`
and `fiat-checkpoint-restore-transcript/v1` with their closed fields from
study sections 1 and 4; the store path and both boundary names; the nine
entry paths; the zip metadata rule (stored, mode `0100644`, DOS time
1980-01-01 00:00:00, `create_system` 3, no directory entries, no ZIP64, sorted
by UTF-8 bytes, no comment, no extra fields); the ceilings (4,200 entries,
1,300 MiB expanded, bundle 1 GiB, every other entry 64 MiB, entry name 1,024
UTF-8 bytes and 255 per component, at most 64 prior acceptances); the 24
refusal classes; the six secret patterns; the 35 hostile fixture ids; the
restore transaction; and a pointer to the budgets file.
`plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json`
declares `checkpoint.archive.export_wall_ms` 15000,
`checkpoint.archive.inspect_wall_ms` 10000,
`checkpoint.archive.restore_wall_ms` 20000, `checkpoint.archive.bytes`
201581002, `checkpoint.archive.expanded_bytes` 209715200 and
`checkpoint.archive.export_peak_rss_bytes` 1073741824, all
`lower_is_better`, variance 0.25. `cmp .hexaemeron/study.md
docs/fiat-checkpoint-archive-study.md` and `cmp .hexaemeron/runbook.md
docs/fiat-checkpoint-archive-runbook.md` exit 0. Then
`python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_archive tests.test_fiat_checkpoint_archive_record -v`
exits 0 with `Ran 5 tests`. Then, on the clean detached snapshot of the step
head: `python3 scripts/run_checks.py --base 0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`,
`python3 plugins/hexaemeron/tests/run_tests.py` and
`python3 -m unittest discover -s tests`, each exit 0. Then, in the run
worktree: `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`,
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`,
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <path>`
and `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py <path>` for
every changed Markdown file other than the two byte-identical run artefacts,
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
after `git add` followed by
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
`python3 scripts/portable_promise_machine.py check` and `git diff --check`,
each exit 0.

**Files.** Create
`docs/decisions/draft-build-the-outer-checkpoint-archive-natively.md`,
`plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`,
`plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json`,
`docs/fiat-checkpoint-archive-study.md`,
`docs/fiat-checkpoint-archive-runbook.md`,
`plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py` and
`tests/test_fiat_checkpoint_archive_record.py`. Amend
`docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`,
`.horos/boundary.json` and `.horos/census.json`. No controller code changes.

**Tests.** In `plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py`:
`test_archive_reference_names_every_refusal_class_and_fixture_id` (the
reference's 24 classes and 35 ids equal the sets in
`docs/fiat-checkpoint-archive-study.md` sections 4 and 5) and
`test_archive_budgets_declare_the_six_measured_limits`. In
`tests/test_fiat_checkpoint_archive_record.py`:
`test_run_artefacts_point_to_the_draft_record_and_adr_028_and_are_not_the_decision`,
`test_adr_028_amendment_points_at_the_draft_record_and_stays_accepted` and
`test_draft_record_states_the_three_commands_and_the_rejected_designs`, with
a dead-relative-link check over both tracked artefacts. Five new tests;
existing suites unchanged. For any audit repair, run
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected schema `elenchus.unittest.v1`;
report file `.elenchus/fiat-861-step-1.json`. A missing, stale, empty,
malformed, zero-test or infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: none, this step opens no input path, spawns no
program and holds no key material; it writes documents and one JSON file.
ephoros: none, nothing in this step runs unattended. metron: the budgets file
declares the six limits derived in study section 10 from the measured
baselines; no performance claim is made or changed. elenchus: none, no failure
is in hand; the five tests are the guards later steps build against.
hypomnema: the draft record and the ADR-028 amendment are the decision homes
for reversing ADR-028's rejected standing-checkpoint automation, and the
reference is the contract home; both land before controller code.

## Step 2: Build `checkpoint archive`

**Goal.** Give `hexctl` the export half: at an accepted boundary, build the
stored zip, its content manifest, bundle, signature proof, identity member and
sidecar in a hidden sibling stage, and publish the boundary directory by
no-replace rename.

**Entry.** The receipted head of Step 1, the commit the controller names as
this step's `branch_from`, with Step 1's exit holding: the reference, the
budgets file, the draft record, the tracked artefacts and the five inventory
tests present.

**Exit.** `python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <run-worktree> checkpoint archive`,
run immediately after `done push` or at an active `audit-verdict`, writes
`<origin>/.hexaemeron/checkpoints/<run-worktree-name>/<boundary>/checkpoint.zip`
and `checkpoint.zip.sha256` (`<64 lowercase hex>  checkpoint.zip\n`), prints
one `fiat-checkpoint-archive-export/v1` object (`archive`, `sidecar`,
`outer_sha256`, `manifest_sha256`, `snapshot_id` or `null`, `bundle_sha256`,
`entries`, `bytes`, `boundary`, `next`, `timing_ms` for `export`, `identity`,
`bundle`, `proof`, `pack`, `inspect`, `publish`), appends no ledger entry and
holds the run lock through `verify_run` exactly as `checkpoint export` does.
The layout and metadata are exactly the reference's; `checkpoint.json` is
closed to the fields in study section 1 and written last; the bundle is built
by `git -c pack.threads=1 bundle create` from exactly `_checkpoint_refs` with
`--no-tags`, and its heads, the capsule's `boundary.refs` and the manifest's
`refs` agree three ways; the proof runs `git verify-commit` for every commit in
`push.verified_commits` inside a disposable `GNUPGHOME` (mode 0700,
`--no-autostart`, removed after use) and requires status `G` and exactly one
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` and one
`Wildcat-Origin: shoggoth` trailer each; `proof/pubkey.asc` is exported for
the pinned fingerprints, or `proof/allowed_signers` for `gpg.format ssh`; the
identity member is the in-process `checkpoint identity` result; the six secret
patterns are scanned over every member and over `state.json`, `ledger.jsonl`
and every opaque controller file; the self-check re-reads the packed zip's
central directory and every entry digest against `checkpoint.json` before the
sidecar is written (Step 3 replaces this self-check with the inspector). The
export refusal classes exist: `boundary-unaccepted`, `worktree-dirty`,
`boundary-occupied`, `ref-disagreement`, `bundle-incomplete`,
`bundle-oversized`, `signature-unverified`, `signature-format-unsupported`,
`identity-unavailable` (export continues with `status: unavailable` only for a
legacy symbolic base), `secret-shaped-member` and `manifest-mismatch`. Then
`python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_archive -v`
exits 0 with `Ran 17 tests`. Then
`python3 .hexaemeron/measure_design.py --conformance existing-checkpoint-suites-green --candidate native-subcommands`
exits 0 and
`.hexaemeron/reports/native-subcommands-existing-checkpoint-suites-green.json`
carries `"value": true` (both existing modules, 82 tests, pass); Fiat checks
this `step:3` transition at this step's `done push`. Then, on the clean
detached snapshot of the step head:
`python3 scripts/run_checks.py --base 0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`,
`python3 plugins/hexaemeron/tests/run_tests.py` and
`python3 -m unittest discover -s tests`, each exit 0. Then, in the run
worktree: `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`,
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`,
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <path>`
and `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py <path>` for
every changed Markdown file,
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
after `git add` followed by
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
`python3 scripts/portable_promise_machine.py check` and `git diff --check`,
each exit 0.

**Files.** Amend `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`: archive
constants beside the checkpoint constants at lines 433-479, the
`_checkpoint_archive_*` functions and `cmd_checkpoint_archive` after
`cmd_checkpoint_restore`, and the `checkpoint` subparser. Amend
`plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py`. Amend
`plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md` only where
the implementation corrects a stated value, and then through a dated study
amendment first. Regenerate `.horos/boundary.json` and `.horos/census.json`.
`checkpoint export`, `checkpoint restore`, `fiat-controller-checkpoint/v1`,
the compatibility set and `snapshot_id` derivation do not change.

**Tests.** Fifteen new tests in
`plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py`:
`test_archive_export_is_byte_identical_across_two_exports_and_two_absolute_paths`
(C2), `test_archive_reserves_prior_acceptance_entries` (C4),
`test_archive_export_refuses_every_unaccepted_boundary`,
`test_archive_export_refuses_dirty_worktree`,
`test_archive_export_refuses_secret_shaped_member`,
`test_archive_export_refuses_oversized_bundle`,
`test_archive_export_refuses_ref_disagreement`,
`test_archive_export_refuses_occupied_boundary_directory`,
`test_archive_export_refuses_unsupported_signature` (C5),
`test_archive_layout_and_entry_metadata_are_fixed`,
`test_archive_manifest_carries_no_path_hostname_or_environment_value`,
`test_archive_export_appends_no_ledger_entry_and_reports_timing_stages`,
`test_archive_export_self_check_refuses_manifest_mismatch`,
`test_archive_bundle_is_built_single_threaded_from_exactly_the_checkpoint_refs`
and
`test_archive_signature_proof_requires_good_status_and_exactly_one_trailer_each`.
Signing tests generate an ephemeral OpenPGP key in a temporary `GNUPGHOME`;
none touches the operator's keyring. The 82 existing checkpoint and identity
tests stay green. For any audit repair, run
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected schema `elenchus.unittest.v1`;
report file `.elenchus/fiat-861-step-2.json`. A missing, stale, empty,
malformed, zero-test or infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: this step spawns `git` and `gpg` through
`bounded_tool` with fixed argv, cap and timeout, creates and removes the
disposable keyring, scans members for the six secret patterns, and writes only
to the hidden sibling stage opened by descriptor before the no-replace rename.
ephoros: the export result's `timing_ms` stages and the single refusal class
answer study section 8 questions 1 and 2; no telemetry is added. metron:
`pack.threads=1` is the measured determinism rule from study section 2; the
export wall and peak RSS budgets are measured in Step 5, not claimed here.
elenchus: the seven C5 refusal tests and the self-check test are parent-red
guards; an audit repair lands with a test named
`test_<class>_refuses_before_<boundary>`. hypomnema: the Step 1 reference is
the contract home; a value the implementation must change is a dated study
amendment before the code.

## Step 3: Build `checkpoint inspect` and refuse the hostile fixtures

**Goal.** Give `hexctl` the reader: verify an archive from its central
directory under the ceilings before any extraction, then the bundle and the
signatures in disposable roots, print structured findings without entry
content, and make `archive` self-check through it.

**Entry.** The receipted head of Step 2, the commit the controller names as
this step's `branch_from`, with
`.hexaemeron/reports/native-subcommands-existing-checkpoint-suites-green.json`
carrying `"value": true` and this run's step-2 checkpoint present at
`<origin>/.hexaemeron/checkpoints/<run-worktree-name>/step-2-<sha>/checkpoint.zip`.

**Exit.** `python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py checkpoint inspect --archive <zip> --sha256 <outer-hex> [--scratch <new-dir>]`
prints one `fiat-checkpoint-inspect/v1` object (`outer_sha256`, `entries`,
`bytes`, `findings`, `bundle`, `signatures` per commit with `sha`, `status`,
`fingerprint`, `trailers`, `identity`, `refs`), exits 0 with empty `findings`
on the step-2 checkpoint, exits 1 with one class on every hostile fixture,
writes nothing outside a scratch root created 0700 and removed unless
`--scratch` names it, and prints no entry content. Checks run in this order
and stop at the first refusal: the outer digest recomputed over the exact zip
bytes against `--sha256` and, when present, the sidecar (`outer-digest-mismatch`,
`sidecar-mismatch`); the central directory under the ceilings, the name
policy, uniqueness after NFC and `casefold()`, method 0, no encryption flag,
mode `0100644`, no ZIP64 record, no prefix, gap or trailing bytes
(`entry-limit`, `entry-name-policy`, `entry-mode`, `entry-compressed`,
`entry-encrypted`, `zip64-present`, `trailing-data`); `checkpoint.json` parsed
bounded at depth 128 against the closed schema with a supported `schema` and a
controller version inside the compatibility set (`schema-unsupported`); every
entry's digest and size streamed against the manifest with the ceilings
re-enforced (`manifest-mismatch`); the capsule `MANIFEST.json` digest equal to
`controller_capsule.manifest_sha256`; the three-way ref join over `git bundle
list-heads`, the capsule's `boundary.refs` and the manifest's `refs`
(`ref-disagreement`); `git bundle verify` in a disposable `git init` root with
complete history, the recorded hash algorithm and no prerequisite
(`bundle-incomplete`, `bundle-oversized`); `proof/pubkey.asc` imported into a
disposable `GNUPGHOME` whose reported fingerprints equal `signer.fingerprints`,
then `git verify-commit` for each `proof.commits` sha in the bundle clone with
status `G` and trailer counts exactly one each, or `gpg.ssh.allowedSignersFile`
from `proof/allowed_signers` for `ssh` (`signature-unverified`,
`signature-format-unsupported`); `identity/checkpoint-identity.json` shape and
`snapshot_id` equal to the manifest's (`identity-mismatch`); `acceptance/current`
refused and `acceptance/prior/<n>.json` counted at most 64 and digested, never
read for authority (`acceptance-self-reference`); the six secret patterns over
every member (`secret-shaped-member`). `archive` now runs this inspector over
the packed bytes before writing the sidecar and renaming, recorded as
`timing_ms.inspect`. Then
`python3 -m unittest -k hostile plugins.hexaemeron.tests.test_hexctl_checkpoint_archive`
exits 0 with `Ran 35 tests`, and
`python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_archive -v`
exits 0 with `Ran 55 tests`. Then
`python3 .hexaemeron/measure_design.py --conformance hostile-fixtures-refused --candidate native-subcommands`
exits 0 and
`.hexaemeron/reports/native-subcommands-hostile-fixtures-refused.json`
carries `"value": true`; Fiat checks this `step:4` transition at this step's
`done push`. Then, on the clean detached snapshot of the step head:
`python3 scripts/run_checks.py --base 0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`,
`python3 plugins/hexaemeron/tests/run_tests.py` and
`python3 -m unittest discover -s tests`, each exit 0. Then, in the run
worktree: `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`,
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`,
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <path>`
and `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py <path>` for
every changed Markdown file,
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
after `git add` followed by
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
`python3 scripts/portable_promise_machine.py check` and `git diff --check`,
each exit 0.

**Files.** Amend `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`: the
`_checkpoint_inspect_*` functions and `cmd_checkpoint_inspect`, the
`checkpoint` subparser, and the `archive` self-check call. Amend
`plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py`. Amend
`plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md` only through
a dated study amendment. Regenerate `.horos/boundary.json` and
`.horos/census.json`.

**Tests.** Thirty-eight new tests in
`plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py`: one
`test_hostile_<id>` for each of `traversal-dotdot`, `absolute-path`,
`backslash-separator`, `drive-letter`, `duplicate-name`,
`case-fold-collision`, `non-utf8-name`, `control-character-name`,
`nfc-mismatch-name`, `directory-entry`, `symlink-entry`,
`special-mode-entry`, `setuid-or-executable-mode`, `compressed-entry`,
`encrypted-entry`, `zip64-record`, `entry-count-over-limit`,
`expanded-size-over-limit`, `bundle-over-limit`, `size-mismatch`,
`trailing-data`, `tampered-manifest`, `unmanifested-member`,
`missing-member`, `wrong-outer-digest`, `tampered-sidecar`, `wrong-receipt`,
`missing-object`, `ref-map-mismatch`, `secret-shaped-member`,
`self-referential-acceptance`, `identity-mismatch`,
`unknown-schema-version`, `signature-proof-mismatch` and
`absolute-source-path-in-manifest` (with hyphens as underscores), plus
`test_inspect_reports_clean_findings_on_a_good_archive`,
`test_inspect_writes_nothing_outside_scratch` and
`test_inspect_prints_no_entry_content`. Each hostile test builds its
byte-level specimen from a good archive inside the test, asserts the refusal
class, exit 1, one stderr line, no file outside scratch and no extraction of
the hostile entry; the three over-limit specimens declare their sizes in the
central directory and write under 2 MiB. For any audit repair, run
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected schema `elenchus.unittest.v1`;
report file `.elenchus/fiat-861-step-3.json`. A missing, stale, empty,
malformed, zero-test or infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: this step is the ingestion path; every check above
runs before extraction into the disposable root, `git` and `gpg` run through
`bounded_tool`, and the keyring is disposable and seeded only from the
archive's key member pinned to the manifest fingerprints. ephoros:
`findings` with class names and entry indexes answers study section 8 question
3 without printing a member. metron: the inspect wall budget is measured in
Step 5. elenchus: the 35 hostile tests are the guards; a class found missing
in audit lands as `test_<class>_refuses_before_<boundary>`. hypomnema: none
new; the contract home exists and changes only by dated study amendment.

## Step 4: Build `checkpoint restore --archive`

**Goal.** Restore a run from one archive into a new or empty directory on any
machine: inspect, create the repository from the bundle, extract the capsule,
run the existing relocation transaction, re-verify identity and ancestry,
report the next directive and execute nothing.

**Entry.** The receipted head of Step 3, the commit the controller names as
this step's `branch_from`, with
`.hexaemeron/reports/native-subcommands-hostile-fixtures-refused.json`
carrying `"value": true` and this run's step-3 checkpoint present.

**Exit.** `python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <empty-destination> checkpoint restore --archive <zip> --sha256 <outer-hex>`
(mutually exclusive with `--from` and `--manifest-sha256`) requires the
destination to be absent or an empty directory checked through an opened
descriptor and never a symlink (`destination-occupied`); runs the Step 3
inspector first and refuses on any finding before any write; runs `git init`,
`git fetch <bundle> +refs/heads/*:refs/heads/*` with `--no-tags` through
`bounded_tool`, and checks out `config.git.base`; writes `remote.origin.url`
as `https://github.com/<owner>/<name>.git` from the validated
`run.repository` and fetches nothing; refuses unless the working commit
descends from `run.initial_base_sha` and every ref equals the manifest map
(`ref-disagreement`); extracts the capsule into
`<destination>/.git/fiat-checkpoint-restore/<outer-sha256>/`; calls the
existing relocation transaction with `controller_capsule.manifest_sha256`,
leaving its marker, retry and refusal rules unchanged; recomputes identity from
the relocated state and refuses a `snapshot_id` mismatch or a claimed
`unavailable` when identity can be minted (`identity-mismatch`); runs
`verify`, `status` and `next`; prints one `fiat-checkpoint-archive-restore/v1`
object carrying the native restore object, the `verify` exit, the `status`
digest, the semantic `next`, `outer_sha256` and `snapshot_id`; and executes no
directive. Then
`python3 -m unittest -k restore_from_archive plugins.hexaemeron.tests.test_hexctl_checkpoint_archive`
exits 0 with `Ran 6 tests`, and
`python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_archive -v`
exits 0 with `Ran 61 tests`. Then
`python3 .hexaemeron/measure_design.py --conformance offline-empty-directory-restore --candidate native-subcommands`
exits 0 and
`.hexaemeron/reports/native-subcommands-offline-empty-directory-restore.json`
carries `"value": true`; Fiat checks this `step:5` transition at this step's
`done push`. Then, on the clean detached snapshot of the step head:
`python3 scripts/run_checks.py --base 0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`,
`python3 plugins/hexaemeron/tests/run_tests.py` and
`python3 -m unittest discover -s tests`, each exit 0. Then, in the run
worktree: `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`,
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`,
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <path>`
and `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py <path>` for
every changed Markdown file,
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
after `git add` followed by
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
`python3 scripts/portable_promise_machine.py check` and `git diff --check`,
each exit 0. After this step's `done push`, Fiat produces the step checkpoint
under `/usr/bin/time -l` exactly as assumption 3 states; Step 5's entry
depends on those two files.

**Files.** Amend `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`:
`cmd_checkpoint_restore` gains the archive mode through
`_checkpoint_restore_from_archive`, and the `checkpoint restore` subparser
gains `--archive` and `--sha256`. Amend
`plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py`. Amend
`plugins/hexaemeron/tests/test_hexctl_checkpoint.py` only if a shared fixture
helper moves. Regenerate `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Six new tests in
`plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py`:
`test_restore_from_archive_recreates_repository_and_controller_state` (C1:
restored `hexctl verify` exit 0, `status` fingerprint equal to the producer's
after the two owned path fields, ref map equal, ledger the exact prefix plus
one `checkpoint:restore` entry),
`test_restore_from_archive_offline_after_source_clone_removed` (C3: source
clone deleted, `HOME` and `GIT_CONFIG_GLOBAL` pointed at empty scratch, no
remote fetched),
`test_restore_from_archive_reverifies_signatures_receipts_identity_and_ancestry`
(C7: a proof status flipped from `G`, a ledger byte changed, a `snapshot_id`
changed and a working commit outside the anchor's descendants each refuse),
`test_restore_from_archive_refuses_non_empty_destination` and
`test_restore_from_archive_executes_no_directive` (C8), and
`test_restore_from_archive_after_main_advances_stays_anchored` (C9). For any
audit repair, run
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected schema `elenchus.unittest.v1`;
report file `.elenchus/fiat-861-step-4.json`. A missing, stale, empty,
malformed, zero-test or infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: archive bytes cross into controller state here;
inspector first, descriptor-checked destination, derived URL never fetched,
capsule under the git directory, and the already audited relocation
transaction as the only mutation. ephoros: the
`fiat-checkpoint-archive-restore/v1` object answers study section 8 question 4
and the relocation marker the second half of question 3. metron: the restore
wall budget is measured in Step 5. elenchus: a killed restore leaves the
disposable root and the existing marker under the existing retry rules; the
six tests are the guards. hypomnema: none new; the decision home is the Step 1
draft record and the relocation transaction's record stays ADR-028's
2026-08-29 amendment.

## Step 5: Demonstrate on a clean machine, measure the budgets, rewrite the procedure and record the generation

**Goal.** Run the demo path from study section 1 in a network-less container,
take the six Metron measurements against the step-4 checkpoint, replace the
manual procedure with the three commands, add the Promise Machine contract and
land the Fiat generation row.

**Entry.** The receipted head of Step 4, the commit the controller names as
this step's `branch_from`, with
`.hexaemeron/reports/native-subcommands-offline-empty-directory-restore.json`
carrying `"value": true`; this run's step-4 checkpoint at
`<origin>/.hexaemeron/checkpoints/<run-worktree-name>/step-4-<sha>/checkpoint.zip`
with its sidecar, produced by
`/usr/bin/time -l python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <run-worktree> checkpoint archive > .hexaemeron/metron/step-4-export.json 2> .hexaemeron/metron/step-4-export.time.txt`;
and docker 29.5.2 with colima running.

**Exit.** `python3 plugins/hexaemeron/skills/fiat/scripts/checkpoint_clean_machine.py --archive <origin>/.hexaemeron/checkpoints/<run-worktree-name>/step-4-<sha>/checkpoint.zip --sha256 <outer-hex> --image python:3.14-slim --transcript .hexaemeron/clean-machine/transcript.json`
exits 0: it builds the derived image of assumption 4, copies only the
archive, its sidecar and `hexctl.py` into a container started with
`--network none` and an empty `GNUPGHOME`, runs `checkpoint inspect`,
`checkpoint restore --archive` into an empty directory, `verify`,
`status --json`, `next` and `checkpoint identity`, and writes
`fiat-checkpoint-restore-transcript/v1` with `network` `none`, `keyring`
`empty-at-start`, `destination_was_empty` true, `hexctl_verify_exit` 0,
`next_matches_manifest` true, `snapshot_id_matches` true, the controller
SHA-256, both image digests and the six measurements, with its text log
beside it. Then
`python3 plugins/hexaemeron/skills/fiat/scripts/checkpoint_measure.py --archive <origin>/.hexaemeron/checkpoints/<run-worktree-name>/step-4-<sha>/checkpoint.zip --sha256 <outer-hex> --out .hexaemeron/metron/run.json`
exits 0: it reads the export wall time from `timing_ms` in
`.hexaemeron/metron/step-4-export.json` and the maximum resident set size
from `.hexaemeron/metron/step-4-export.time.txt`, times `checkpoint inspect`
and `checkpoint restore --archive` into a scratch destination under
`/usr/bin/time -l` (macOS) or `-v` (Linux), reads `bytes` and the expanded
size from the archive manifest, and writes `measurements` with the six keys
`checkpoint.archive.export_wall_ms`, `checkpoint.archive.inspect_wall_ms`,
`checkpoint.archive.restore_wall_ms`, `checkpoint.archive.bytes`,
`checkpoint.archive.expanded_bytes` and
`checkpoint.archive.export_peak_rss_bytes` as non-negative integers. Then
`cp .hexaemeron/metron/run.json plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-baseline.json`
and
`python3 plugins/hexaemeron/skills/metron/scripts/metron.py check --budgets plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json --baseline plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-baseline.json --run .hexaemeron/metron/run.json`
exits 0 (C11). Then
`cmp .hexaemeron/clean-machine/transcript.json docs/fiat-checkpoint-archive/clean-machine-transcript.json`
exits 0 and `docs/fiat-checkpoint-archive/clean-machine-transcript.log` is
the text log. Then
`python3 .hexaemeron/measure_design.py --conformance fixture-export-wall-milliseconds --candidate native-subcommands`,
`python3 .hexaemeron/measure_design.py --conformance fixture-archive-bytes --candidate native-subcommands`
and
`python3 .hexaemeron/measure_design.py --conformance clean-machine-restore-transcript --candidate native-subcommands`
each exit 0, their reports carrying a wall time at most 15000, a size at most
201581002 and `"value": true`; Fiat checks this `integration` transition at
the final `done merge-step`. Then the procedure:
`plugins/hexaemeron/skills/fiat/references/push-discipline.md` `## Step
checkpoint` names the three commands and the direct hand-off values (absolute
archive path, outer SHA-256, manifest SHA-256, `snapshot_id`, step, loop when
applicable, full head SHA, expected next directive) and
`grep -c issuecomment-5435028801 plugins/hexaemeron/skills/fiat/references/push-discipline.md`
prints 0; `plugins/hexaemeron/skills/fiat/SKILL.md` step 3 and its post-push
paragraph point at that section and the commands;
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md` `## Outer
recovery boundary` and the carrier sentence at
`plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md` line 186
point at `checkpoint-archive.md`; `SKILL.md` carries
`### fiat-checkpoint-archive` after `### fiat-controller-checkpoint` with a
matching row and bindings in `tests/promise_machine_coverage.json`. Then the
generation: one row appended to `plugins/hexaemeron/skills/fiat/EVOLUTION.md`
of kind `generation` on frontier `state-shape-validation` with digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`, evidence
naming issue #861, the draft record, the study and the runbook, and text
stating the three commands, the stored container, the single content
manifest, the clean-machine transcript and the rejected options; `SKILL.md`
metadata `version` and the ledger's `Current version` advanced to that same
next generation; that version appended to
`CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS`; `tests/test_evolution_contract.py`
lines 354 and 362 updated to it; `python3 -m unittest tests.test_evolution_contract`
exits 0. Then
`python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_archive tests.test_fiat_checkpoint_archive_record -v`
exits 0 with `Ran 68 tests`. Then, on the clean detached snapshot of the step
head: `python3 scripts/run_checks.py --base 0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`,
`python3 plugins/hexaemeron/tests/run_tests.py` and
`python3 -m unittest discover -s tests`, each exit 0. Then, in the run
worktree: `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`,
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`,
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <path>`
and `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py <path>` for
every changed Markdown file,
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
after `git add` followed by
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
`python3 scripts/portable_promise_machine.py check` and `git diff --check`,
each exit 0.

**Files.** Create
`plugins/hexaemeron/skills/fiat/scripts/checkpoint_clean_machine.py`,
`plugins/hexaemeron/skills/fiat/scripts/checkpoint_measure.py`,
`plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-baseline.json`,
`docs/fiat-checkpoint-archive/clean-machine-transcript.json` and
`docs/fiat-checkpoint-archive/clean-machine-transcript.log`. Amend
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`,
`plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (the compatibility set
only), `tests/promise_machine_coverage.json`, `tests/test_evolution_contract.py`,
`plugins/hexaemeron/tests/test_fiat_skill.py`,
`plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py`,
`tests/test_fiat_checkpoint_archive_record.py`, and
`plugins/hexaemeron/README.md` only where it describes the manual procedure.
Regenerate `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Four new tests and one updated:
`test_clean_machine_script_assembles_the_transcript_schema_from_a_recorded_log`
and `test_checkpoint_measure_reads_the_saved_export_result_and_writes_six_integers`
in `plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py` (neither
starts docker);
`test_transcript_is_committed_and_binds_the_step_4_archive_digest` and
`test_push_discipline_names_the_three_commands_and_no_comment_link` in
`tests/test_fiat_checkpoint_archive_record.py`;
`test_step_checkpoint_is_unconditional_local_agent_work` in
`plugins/hexaemeron/tests/test_fiat_skill.py` updated to the rewritten
section's sentences. For any audit repair, run
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected schema `elenchus.unittest.v1`;
report file `.elenchus/fiat-861-step-5.json`. A missing, stale, empty,
malformed, zero-test or infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: the two scripts spawn `docker`, `/usr/bin/time` and
`hexctl.py` with fixed argv, copy only the archive, sidecar and controller
into the container, and start it with `--network none`; no secret enters the
transcript. ephoros: the transcript is the durable record of the demo and
answers all four study section 8 questions from a machine that did not write
the archive; no alert is added. metron: the six measurements are taken against
the named fixture and checked against the budgets before the baseline is
committed; a speed change that weakens a check is refused, not traded.
elenchus: the transcript fields are the guard the
`clean-machine-restore-transcript` gate reads; a demo failure is reproduced
from the transcript log, never patched around. hypomnema: the ledger row, the
procedure rewrite, the Promise Machine contract and the two reference pointers
are the decision homes study section 12 names; the draft record takes its
number at sync through `decision_assignments.py`.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: Six documents and five tests exist
and every command below exits 0.
`docs/decisions/drafts/build-the-outer-checkpoint-archive-natively.md` opens
with `# Decision: Build the outer checkpoint archive natively`, carries `##
Status` reading `Proposed, <date written>` followed by `## Context`, `##
Decision`, `## Alternatives` and `## Consequences`, is unnumbered on purpose
(numbered at sync by `python3
plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py
plan|apply|replay` from the integration base, which indexes drafts only below
`docs/decisions/drafts/`), and states the three commands, the stored container,
the single content manifest replacing member sidecars, the fixed nine-entry
layout, the `pack.threads=1` rule, the disposable keyring, the no-fetch
`remote.origin.url`, and the rejected options B, C and D with their measured
readings (pack 26, 26, 1,977 and 335 ms; carrier 100,790,501, 100,790,501,
100,470,196 and 100,790,483 bytes; 2, 3, 4 and 3 spawned programs).
`docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`
gains one `## Amendment: Native outer archive (<date written>)` after `##
Amendment: distributed layer reinstated (2026-09-02)`, pointing at the draft
record by its stable slug reference, as Hypomnema prescribes for a record whose
number arrives at sync, and changing no operative clause; its status stays
Accepted. `plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`
states the contract: schemas `fiat-checkpoint-archive/v1`,
`fiat-checkpoint-archive-export/v1`, `fiat-checkpoint-inspect/v1`,
`fiat-checkpoint-archive-restore/v1`, `fiat-checkpoint-signature-proof/v1` and
`fiat-checkpoint-restore-transcript/v1` with their closed fields from study
sections 1 and 4; the store path and both boundary names; the nine entry paths;
the zip metadata rule (stored, mode `0100644`, DOS time 1980-01-01 00:00:00,
`create_system` 3, no directory entries, no ZIP64, sorted by UTF-8 bytes, no
comment, no extra fields); the ceilings (4,200 entries, 1,300 MiB expanded,
bundle 1 GiB, every other entry 64 MiB, entry name 1,024 UTF-8 bytes and 255
per component, at most 64 prior acceptances); the 24 refusal classes; the six
secret patterns; the 35 hostile fixture ids; the restore transaction; and a
pointer to the budgets file.
`plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json`
declares `checkpoint.archive.export_wall_ms` 15000,
`checkpoint.archive.inspect_wall_ms` 10000,
`checkpoint.archive.restore_wall_ms` 20000, `checkpoint.archive.bytes`
201581002, `checkpoint.archive.expanded_bytes` 209715200 and
`checkpoint.archive.export_peak_rss_bytes` 1073741824, all `lower_is_better`,
variance 0.25. `cmp .hexaemeron/study.md docs/fiat-checkpoint-archive-study.md`
and `cmp .hexaemeron/runbook.md docs/fiat-checkpoint-archive-runbook.md` exit
0. Then `python3 -m unittest
plugins.hexaemeron.tests.test_hexctl_checkpoint_archive
tests.test_fiat_checkpoint_archive_record -v` exits 0 with `Ran 5 tests`. Then,
on the clean detached snapshot of the step head: `python3 scripts/run_checks.py
--base 0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`, `python3
plugins/hexaemeron/tests/run_tests.py` and `python3 -m unittest discover -s
tests`, each exit 0. Then, in the run worktree: `python3
plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3
plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, `python3
plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md
.agents/skills/promise-machine/SKILL.md
.agents/skills/promise-machine/PORTABLE.md plugins docs`, `python3
plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <path>` and `python3
plugins/brevitas/skills/brevitas/scripts/brevitas.py <path>` for every changed
Markdown file other than the two byte-identical run artefacts, `python3
plugins/horos/skills/horos/scripts/horos.py scan . --census --write` after `git
add` followed by `python3 plugins/horos/skills/horos/scripts/horos.py check .`
and `git diff --check`, each exit 0. Complete replacement Files: Create
`docs/decisions/drafts/build-the-outer-checkpoint-archive-natively.md`,
`plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`,
`plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json`,
`docs/fiat-checkpoint-archive-study.md`,
`docs/fiat-checkpoint-archive-runbook.md`,
`plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py` and
`tests/test_fiat_checkpoint_archive_record.py`. Amend
`docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`,
`.horos/boundary.json` and `.horos/census.json`. No controller code changes.
**Why.** The study amendment of 2026-09-07 corrected constraints 3.4 and 3.11:
the portable Promise Machine check exits 1 wherever the portable runtime is
absent, so an exit naming it cannot be proved, and `decision_assignments.py`
indexes drafts only below `docs/decisions/drafts/`, so the record moves there
in Hypomnema's authoring shape.
**Steps touched.** Step 1 Exit and Files.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
broken. Step 3: entry holds; exit broken. Step 4: entry holds; exit broken.
Step 5: entry holds; exit broken.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `python3
plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <run-worktree>
checkpoint archive`, run immediately after `done push` or at an active
`audit-verdict`, writes
`<origin>/.hexaemeron/checkpoints/<run-worktree-name>/<boundary>/checkpoint.zip`
and `checkpoint.zip.sha256` (`<64 lowercase hex> checkpoint.zip\n`), prints one
`fiat-checkpoint-archive-export/v1` object (`archive`, `sidecar`,
`outer_sha256`, `manifest_sha256`, `snapshot_id` or `null`, `bundle_sha256`,
`entries`, `bytes`, `boundary`, `next`, `timing_ms` for `export`, `identity`,
`bundle`, `proof`, `pack`, `inspect`, `publish`), appends no ledger entry and
holds the run lock through `verify_run` exactly as `checkpoint export` does.
The layout and metadata are exactly the reference's; `checkpoint.json` is
closed to the fields in study section 1 and written last; the bundle is built
by `git -c pack.threads=1 bundle create` from exactly `_checkpoint_refs` with
`--no-tags`, and its heads, the capsule's `boundary.refs` and the manifest's
`refs` agree three ways; the proof runs `git verify-commit` for every commit in
`push.verified_commits` inside a disposable `GNUPGHOME` (mode 0700,
`--no-autostart`, removed after use) and requires status `G` and exactly one
`Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` and one `Wildcat-Origin:
shoggoth` trailer each; `proof/pubkey.asc` is exported for the pinned
fingerprints, or `proof/allowed_signers` for `gpg.format ssh`; the identity
member is the in-process `checkpoint identity` result; the six secret patterns
are scanned over every member and over `state.json`, `ledger.jsonl` and every
opaque controller file; the self-check re-reads the packed zip's central
directory and every entry digest against `checkpoint.json` before the sidecar
is written (Step 3 replaces this self-check with the inspector). The export
refusal classes exist: `boundary-unaccepted`, `worktree-dirty`,
`boundary-occupied`, `ref-disagreement`, `bundle-incomplete`,
`bundle-oversized`, `signature-unverified`, `signature-format-unsupported`,
`identity-unavailable` (export continues with `status: unavailable` only for a
legacy symbolic base), `secret-shaped-member` and `manifest-mismatch`. Then
`python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_archive
-v` exits 0 with `Ran 17 tests`. Then `python3 .hexaemeron/measure_design.py
--conformance existing-checkpoint-suites-green --candidate native-subcommands`
exits 0 and
`.hexaemeron/reports/native-subcommands-existing-checkpoint-suites-green.json`
carries `"value": true` (both existing modules, 82 tests, pass); Fiat checks
this `step:3` transition at this step's `done push`. Then, on the clean
detached snapshot of the step head: `python3 scripts/run_checks.py --base
0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`, `python3
plugins/hexaemeron/tests/run_tests.py` and `python3 -m unittest discover -s
tests`, each exit 0. Then, in the run worktree: `python3
plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3
plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, `python3
plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md
.agents/skills/promise-machine/SKILL.md
.agents/skills/promise-machine/PORTABLE.md plugins docs`, `python3
plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <path>` and `python3
plugins/brevitas/skills/brevitas/scripts/brevitas.py <path>` for every changed
Markdown file, `python3 plugins/horos/skills/horos/scripts/horos.py scan .
--census --write` after `git add` followed by `python3
plugins/horos/skills/horos/scripts/horos.py check .` and `git diff --check`,
each exit 0.
**Why.** The study amendment of 2026-09-07 withdrew `python3
scripts/portable_promise_machine.py check` from constraint 3.4; the check exits
1 wherever the portable runtime is absent, so an exit naming it cannot be
proved.
**Steps touched.** Step 2 Exit.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit broken. Step 4: entry holds; exit broken. Step
5: entry holds; exit broken.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `python3
plugins/hexaemeron/skills/fiat/scripts/hexctl.py checkpoint inspect --archive
<zip> --sha256 <outer-hex> [--scratch <new-dir>]` prints one
`fiat-checkpoint-inspect/v1` object (`outer_sha256`, `entries`, `bytes`,
`findings`, `bundle`, `signatures` per commit with `sha`, `status`,
`fingerprint`, `trailers`, `identity`, `refs`), exits 0 with empty `findings`
on the step-2 checkpoint, exits 1 with one class on every hostile fixture,
writes nothing outside a scratch root created 0700 and removed unless
`--scratch` names it, and prints no entry content. Checks run in this order and
stop at the first refusal: the outer digest recomputed over the exact zip bytes
against `--sha256` and, when present, the sidecar (`outer-digest-mismatch`,
`sidecar-mismatch`); the central directory under the ceilings, the name policy,
uniqueness after NFC and `casefold()`, method 0, no encryption flag, mode
`0100644`, no ZIP64 record, no prefix, gap or trailing bytes (`entry-limit`,
`entry-name-policy`, `entry-mode`, `entry-compressed`, `entry-encrypted`,
`zip64-present`, `trailing-data`); `checkpoint.json` parsed bounded at depth
128 against the closed schema with a supported `schema` and a controller
version inside the compatibility set (`schema-unsupported`); every entry's
digest and size streamed against the manifest with the ceilings re-enforced
(`manifest-mismatch`); the capsule `MANIFEST.json` digest equal to
`controller_capsule.manifest_sha256`; the three-way ref join over `git bundle
list-heads`, the capsule's `boundary.refs` and the manifest's `refs`
(`ref-disagreement`); `git bundle verify` in a disposable `git init` root with
complete history, the recorded hash algorithm and no prerequisite
(`bundle-incomplete`, `bundle-oversized`); `proof/pubkey.asc` imported into a
disposable `GNUPGHOME` whose reported fingerprints equal `signer.fingerprints`,
then `git verify-commit` for each `proof.commits` sha in the bundle clone with
status `G` and trailer counts exactly one each, or `gpg.ssh.allowedSignersFile`
from `proof/allowed_signers` for `ssh` (`signature-unverified`,
`signature-format-unsupported`); `identity/checkpoint-identity.json` shape and
`snapshot_id` equal to the manifest's (`identity-mismatch`);
`acceptance/current` refused and `acceptance/prior/<n>.json` counted at most 64
and digested, never read for authority (`acceptance-self-reference`); the six
secret patterns over every member (`secret-shaped-member`). `archive` now runs
this inspector over the packed bytes before writing the sidecar and renaming,
recorded as `timing_ms.inspect`. Then `python3 -m unittest -k hostile
plugins.hexaemeron.tests.test_hexctl_checkpoint_archive` exits 0 with `Ran 35
tests`, and `python3 -m unittest
plugins.hexaemeron.tests.test_hexctl_checkpoint_archive -v` exits 0 with `Ran
55 tests`. Then `python3 .hexaemeron/measure_design.py --conformance
hostile-fixtures-refused --candidate native-subcommands` exits 0 and
`.hexaemeron/reports/native-subcommands-hostile-fixtures-refused.json` carries
`"value": true`; Fiat checks this `step:4` transition at this step's `done
push`. Then, on the clean detached snapshot of the step head: `python3
scripts/run_checks.py --base 0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`,
`python3 plugins/hexaemeron/tests/run_tests.py` and `python3 -m unittest
discover -s tests`, each exit 0. Then, in the run worktree: `python3
plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3
plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, `python3
plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md
.agents/skills/promise-machine/SKILL.md
.agents/skills/promise-machine/PORTABLE.md plugins docs`, `python3
plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <path>` and `python3
plugins/brevitas/skills/brevitas/scripts/brevitas.py <path>` for every changed
Markdown file, `python3 plugins/horos/skills/horos/scripts/horos.py scan .
--census --write` after `git add` followed by `python3
plugins/horos/skills/horos/scripts/horos.py check .` and `git diff --check`,
each exit 0.
**Why.** The study amendment of 2026-09-07 withdrew `python3
scripts/portable_promise_machine.py check` from constraint 3.4; the check exits
1 wherever the portable runtime is absent, so an exit naming it cannot be
proved.
**Steps touched.** Step 3 Exit.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit broken. Step
5: entry holds; exit broken.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `python3
plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <empty-destination>
checkpoint restore --archive <zip> --sha256 <outer-hex>` (mutually exclusive
with `--from` and `--manifest-sha256`) requires the destination to be absent or
an empty directory checked through an opened descriptor and never a symlink
(`destination-occupied`); runs the Step 3 inspector first and refuses on any
finding before any write; runs `git init`, `git fetch <bundle>
+refs/heads/*:refs/heads/*` with `--no-tags` through `bounded_tool`, and checks
out `config.git.base`; writes `remote.origin.url` as
`https://github.com/<owner>/<name>.git` from the validated `run.repository` and
fetches nothing; refuses unless the working commit descends from
`run.initial_base_sha` and every ref equals the manifest map
(`ref-disagreement`); extracts the capsule into
`<destination>/.git/fiat-checkpoint-restore/<outer-sha256>/`; calls the
existing relocation transaction with `controller_capsule.manifest_sha256`,
leaving its marker, retry and refusal rules unchanged; recomputes identity from
the relocated state and refuses a `snapshot_id` mismatch or a claimed
`unavailable` when identity can be minted (`identity-mismatch`); runs `verify`,
`status` and `next`; prints one `fiat-checkpoint-archive-restore/v1` object
carrying the native restore object, the `verify` exit, the `status` digest, the
semantic `next`, `outer_sha256` and `snapshot_id`; and executes no directive.
Then `python3 -m unittest -k restore_from_archive
plugins.hexaemeron.tests.test_hexctl_checkpoint_archive` exits 0 with `Ran 6
tests`, and `python3 -m unittest
plugins.hexaemeron.tests.test_hexctl_checkpoint_archive -v` exits 0 with `Ran
61 tests`. Then `python3 .hexaemeron/measure_design.py --conformance
offline-empty-directory-restore --candidate native-subcommands` exits 0 and
`.hexaemeron/reports/native-subcommands-offline-empty-directory-restore.json`
carries `"value": true`; Fiat checks this `step:5` transition at this step's
`done push`. Then, on the clean detached snapshot of the step head: `python3
scripts/run_checks.py --base 0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`,
`python3 plugins/hexaemeron/tests/run_tests.py` and `python3 -m unittest
discover -s tests`, each exit 0. Then, in the run worktree: `python3
plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3
plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, `python3
plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md
.agents/skills/promise-machine/SKILL.md
.agents/skills/promise-machine/PORTABLE.md plugins docs`, `python3
plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <path>` and `python3
plugins/brevitas/skills/brevitas/scripts/brevitas.py <path>` for every changed
Markdown file, `python3 plugins/horos/skills/horos/scripts/horos.py scan .
--census --write` after `git add` followed by `python3
plugins/horos/skills/horos/scripts/horos.py check .` and `git diff --check`,
each exit 0. After this step's `done push`, Fiat produces the step checkpoint
under `/usr/bin/time -l` exactly as assumption 3 states; Step 5's entry depends
on those two files.
**Why.** The study amendment of 2026-09-07 withdrew `python3
scripts/portable_promise_machine.py check` from constraint 3.4; the check exits
1 wherever the portable runtime is absent, so an exit naming it cannot be
proved.
**Steps touched.** Step 4 Exit.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step
5: entry holds; exit broken.

### Amendment -- 2026-09-07

**What changed.** Complete replacement Exit: `python3
plugins/hexaemeron/skills/fiat/scripts/checkpoint_clean_machine.py --archive
<origin>/.hexaemeron/checkpoints/<run-worktree-name>/step-4-<sha>/checkpoint.zip
--sha256 <outer-hex> --image python:3.14-slim --transcript
.hexaemeron/clean-machine/transcript.json` exits 0: it builds the derived image
of assumption 4, copies only the archive, its sidecar and `hexctl.py` into a
container started with `--network none` and an empty `GNUPGHOME`, runs
`checkpoint inspect`, `checkpoint restore --archive` into an empty directory,
`verify`, `status --json`, `next` and `checkpoint identity`, and writes
`fiat-checkpoint-restore-transcript/v1` with `network` `none`, `keyring`
`empty-at-start`, `destination_was_empty` true, `hexctl_verify_exit` 0,
`next_matches_manifest` true, `snapshot_id_matches` true, the controller
SHA-256, both image digests and the six measurements, with its text log beside
it. Then `python3 plugins/hexaemeron/skills/fiat/scripts/checkpoint_measure.py
--archive
<origin>/.hexaemeron/checkpoints/<run-worktree-name>/step-4-<sha>/checkpoint.zip
--sha256 <outer-hex> --out .hexaemeron/metron/run.json` exits 0: it reads the
export wall time from `timing_ms` in `.hexaemeron/metron/step-4-export.json`
and the maximum resident set size from
`.hexaemeron/metron/step-4-export.time.txt`, times `checkpoint inspect` and
`checkpoint restore --archive` into a scratch destination under `/usr/bin/time
-l` (macOS) or `-v` (Linux), reads `bytes` and the expanded size from the
archive manifest, and writes `measurements` with the six keys
`checkpoint.archive.export_wall_ms`, `checkpoint.archive.inspect_wall_ms`,
`checkpoint.archive.restore_wall_ms`, `checkpoint.archive.bytes`,
`checkpoint.archive.expanded_bytes` and
`checkpoint.archive.export_peak_rss_bytes` as non-negative integers. Then `cp
.hexaemeron/metron/run.json
plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-baseline.json` and
`python3 plugins/hexaemeron/skills/metron/scripts/metron.py check --budgets
plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json
--baseline
plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-baseline.json --run
.hexaemeron/metron/run.json` exits 0 (C11). Then `cmp
.hexaemeron/clean-machine/transcript.json
docs/fiat-checkpoint-archive/clean-machine-transcript.json` exits 0 and
`docs/fiat-checkpoint-archive/clean-machine-transcript.log` is the text log.
Then `python3 .hexaemeron/measure_design.py --conformance
fixture-export-wall-milliseconds --candidate native-subcommands`, `python3
.hexaemeron/measure_design.py --conformance fixture-archive-bytes --candidate
native-subcommands` and `python3 .hexaemeron/measure_design.py --conformance
clean-machine-restore-transcript --candidate native-subcommands` each exit 0,
their reports carrying a wall time at most 15000, a size at most 201581002 and
`"value": true`; Fiat checks this `integration` transition at the final `done
merge-step`. Then the procedure:
`plugins/hexaemeron/skills/fiat/references/push-discipline.md` `## Step
checkpoint` names the three commands and the direct hand-off values (absolute
archive path, outer SHA-256, manifest SHA-256, `snapshot_id`, step, loop when
applicable, full head SHA, expected next directive) and `grep -c
issuecomment-5435028801
plugins/hexaemeron/skills/fiat/references/push-discipline.md` prints 0;
`plugins/hexaemeron/skills/fiat/SKILL.md` step 3 and its post-push paragraph
point at that section and the commands;
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md` `## Outer
recovery boundary` and the carrier sentence at
`plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md` line 186
point at `checkpoint-archive.md`; `SKILL.md` carries `###
fiat-checkpoint-archive` after `### fiat-controller-checkpoint` with a matching
row and bindings in `tests/promise_machine_coverage.json`. Then the generation:
one row appended to `plugins/hexaemeron/skills/fiat/EVOLUTION.md` of kind
`generation` on frontier `state-shape-validation` with digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`, evidence
naming issue #861, the draft record, the study and the runbook, and text
stating the three commands, the stored container, the single content manifest,
the clean-machine transcript and the rejected options; `SKILL.md` metadata
`version` and the ledger's `Current version` advanced to that same next
generation; that version appended to
`CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS`; `tests/test_evolution_contract.py`
lines 354 and 362 updated to it; `python3 -m unittest
tests.test_evolution_contract` exits 0. Then `python3 -m unittest
plugins.hexaemeron.tests.test_hexctl_checkpoint_archive
tests.test_fiat_checkpoint_archive_record -v` exits 0 with `Ran 68 tests`.
Then, on the clean detached snapshot of the step head: `python3
scripts/run_checks.py --base 0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`,
`python3 plugins/hexaemeron/tests/run_tests.py` and `python3 -m unittest
discover -s tests`, each exit 0. Then, in the run worktree: `python3
plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`, `python3
plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`, `python3
plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md
.agents/skills/promise-machine/SKILL.md
.agents/skills/promise-machine/PORTABLE.md plugins docs`, `python3
plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <path>` and `python3
plugins/brevitas/skills/brevitas/scripts/brevitas.py <path>` for every changed
Markdown file, `python3 plugins/horos/skills/horos/scripts/horos.py scan .
--census --write` after `git add` followed by `python3
plugins/horos/skills/horos/scripts/horos.py check .` and `git diff --check`,
each exit 0.
**Why.** The study amendment of 2026-09-07 withdrew `python3
scripts/portable_promise_machine.py check` from constraint 3.4; the check exits
1 wherever the portable runtime is absent, so an exit naming it cannot be
proved.
**Steps touched.** Step 5 Exit.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step
5: entry holds; exit holds.
