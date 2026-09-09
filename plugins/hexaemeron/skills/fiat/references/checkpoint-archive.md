# Fiat checkpoint archive

This reference specifies the outer checkpoint archive that `hexctl` builds,
inspects and restores: a stored ZIP carrier around the controller capsule of
[controller-checkpoint.md](controller-checkpoint.md), the Git bundle, the
signature proof and the identity result of
[checkpoint-identity.md](checkpoint-identity.md). The decision behind it is
the record `adr/build-the-outer-checkpoint-archive-natively`, drafted under
`docs/decisions/drafts/`, numbered at integration and pointed at by the
2026-09-07 amendment of
[ADR-028](https://github.com/wildcat-finance/skills/blob/main/docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md).
Every value here comes from the study committed as
`docs/fiat-checkpoint-archive-study.md` and its runbook; a value the study
leaves open is listed under `## Open items` rather than filled in.

## Commands

```text
hexctl --dir <run-worktree> checkpoint archive
hexctl checkpoint inspect --archive <zip> --sha256 <outer-hex> [--scratch <new-dir>]
hexctl --dir <empty-destination> checkpoint restore --archive <zip> --sha256 <outer-hex>
```

`archive` runs at an accepted boundary, takes the run lock through the
controller's ordinary verification exactly as `checkpoint export` does,
appends no ledger entry, builds every member in a hidden sibling stage and
publishes the boundary directory by no-replace rename. `inspect` reads an
archive and writes nothing outside a scratch root created with mode 0700.
`restore --archive` runs the inspector, creates the repository and the
controller state in a new or empty directory, and executes no directive.

## Store path and boundaries

The store path is derived from controller state and never supplied:

```text
<origin>/.hexaemeron/checkpoints/<run-worktree-name>/
  step-<n>-<full-head-sha>/checkpoint.zip
  step-<n>-<full-head-sha>/checkpoint.zip.sha256
```

The two boundary directory names are ADR-028's: `step-<n>-<full-head-sha>`
after `done push`, and `audit-verdict-step-<n>-loop-<l>-<full-head-sha>` at an
exhausted audit loop. The sidecar is `<64 lowercase hex>  checkpoint.zip\n`,
two spaces and the relative name, so `shasum -a 256 -c` reads it. An existing
boundary directory is never replaced: the same boundary exported twice from
unchanged state yields identical bytes, so the second export refuses as
occupied rather than compared.

## Container

The zip is a pure container. Every entry is stored, method 0, with Unix mode
`0100644`, DOS time 1980-01-01 00:00:00 and `create_system` 3. The archive
carries no directory entries, no ZIP64 records, no comment and no extra
fields, and its entries are sorted by UTF-8 bytes. The outer digest is SHA-256
over the exact zip bytes. It names the carrier, not the capsule manifest digest
and not `snapshot_id`; the archive carries all three identities and restore
rejoins them.

## Layout

Nine entry paths, fixed:

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

No `acceptance/current` entry is ever written. The bundle is built by
`git -c pack.threads=1 bundle create` from exactly the controller's bounded ref
set. No `--no-tags` argument is passed: bundle creation has no such option, and
the explicit ref list already excludes tags. Default threading produced two
different bundles from one state, single threading produced one digest four
times. `checkpoint.json` is written last, after every other member's digest is
known.

## Content manifest

`checkpoint.json` uses schema `fiat-checkpoint-archive/v1` in canonical JSON:
sorted keys, `,` and `:` separators, one trailing LF. Its top-level object is
closed to these fields.

| field | closed to | joined against |
| --- | --- | --- |
| `schema` | `fiat-checkpoint-archive/v1` | the inspector's supported set |
| `archive` | `format` `zip`, `compression` `stored`, sorted `entries` of `path`, `bytes`, `sha256` | every member |
| `boundary` | `kind`, `step`, `loop` when exhausted, `working_commit_sha`, semantic `next` | the capsule boundary |
| `run` | `repository`, `run_branch`, `worktree_name`, `task_issue`, `initial_base_sha`, `run_anchor_sha256` | the run anchor |
| `refs` | name to full SHA, equal to the capsule's map | the bundle heads and capsule `boundary.refs` |
| `bundle` | `bytes`, `sha256`, `hash_algorithm`, `complete_history` | `git/repository.bundle` |
| `controller_capsule` | `manifest_sha256`, `state_sha256`, `ledger_sha256`, `ledger_entries`, `ledger_tail`, `files`, `bytes` | `controller-capsule/MANIFEST.json` |
| `identity` | `status` `bound` with `snapshot_id`, or `unavailable` with a closed reason | `identity/checkpoint-identity.json` |
| `signer` | `format`, `fingerprints`, `key_path` | `proof/pubkey.asc` or `proof/allowed_signers` |
| `proof` | `commits`, `sha256` | `proof/signatures.json` |
| `acceptance` | `current` is the literal `outside`, `prior` list | `acceptance/prior/<n>.json` |
| `controller` | `hexctl`, Fiat version | the compatibility set |
| `limits` | the ceilings below | the inspector |

No timestamp, absolute path, environment value or credential appears in the
manifest, the README or the proof.

## Ceilings

The ceilings are safety limits, not performance targets. The inspector enforces
them from the central directory before any extraction and again while
streaming each entry.

- 4,200 entries.
- 1,300 MiB expanded.
- 1 GiB for `git/repository.bundle`; 64 MiB for every other entry.
- The capsule ceilings that `controller-checkpoint.md` fixes.
- Entry names of at most 1,024 UTF-8 bytes and 255 bytes per component, valid
  NFC UTF-8, no C0 or C1 control character, no empty, `.` or `..` component,
  no backslash, no leading `/`, unique after NFC and `casefold()`.
- At most 64 prior acceptance receipts.

## Results and proof

Each command prints one canonical JSON object on stdout.

`fiat-checkpoint-archive-export/v1`, from `archive`: `archive`, `sidecar`,
`outer_sha256`, `manifest_sha256`, `snapshot_id` or `null`, `bundle_sha256`,
`entries`, `bytes`, `boundary`, `next`, and `timing_ms` per stage `export`,
`identity`, `bundle`, `proof`, `pack`, `inspect`, `publish`.

`fiat-checkpoint-inspect/v1`, from `inspect`: `outer_sha256`, `entries`,
`bytes`, `findings` (refusal class names, empty on success), `bundle`,
`signatures` (per commit `sha`, `status`, `fingerprint`, `trailers`),
`identity`, `refs`. It prints no entry content.

`fiat-checkpoint-archive-restore/v1`, from `restore --archive`: the native
`fiat-controller-checkpoint-restore/v1` object, the `verify` exit, the `status`
output digest, the semantic `next`, `outer_sha256` and `snapshot_id`.

`fiat-checkpoint-signature-proof/v1`, the `proof/signatures.json` member: per
receipted commit `sha`, `format`, `status` (`G` required), `fingerprint`, the
counts of `Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` and
`Wildcat-Origin: shoggoth` trailers (exactly one each), and the GitHub
verification recorded by the push receipt. No raw `gpg` output. Only the run's
receipted commits (`push.verified_commits`) are covered; merges on the
integration branch are never claimed.

`fiat-checkpoint-restore-transcript/v1`, written by the clean-machine demo:
`network`, `keyring`, `destination_was_empty`, `hexctl_verify_exit`,
`next_matches_manifest`, `snapshot_id_matches`, the controller SHA-256 and the
six budget measurements.

## Refusal classes

Every refusal exits 1 with one bounded stderr line carrying the class name and
nothing else: no entry name, entry content, `gpg` output or JSON value. The
stage column names the command that raises the class; `restore --archive`
also inherits every inspector class because it runs the inspector first.

| class | stage | condition |
| --- | --- | --- |
| `boundary-unaccepted` | archive | the ledger tail is neither `done:push` nor an active `audit-verdict` |
| `worktree-dirty` | archive | the run worktree carries a tracked change |
| `boundary-occupied` | archive | the boundary directory already exists |
| `ref-disagreement` | archive, inspect, restore | bundle heads, capsule `boundary.refs` and manifest `refs` disagree, or a restored ref differs from the map |
| `bundle-incomplete` | archive, inspect | `git bundle verify` names a prerequisite, another hash algorithm or a head outside the manifest |
| `bundle-oversized` | archive, inspect | the bundle exceeds 1 GiB |
| `signature-unverified` | archive, inspect | a receipted commit is not `G` under the pinned fingerprints, or its trailer counts are not exactly one each |
| `signature-format-unsupported` | archive, inspect | `gpg.format` is neither `openpgp` nor `ssh` |
| `identity-unavailable` | archive | identity cannot be minted; export continues with `status: unavailable` only for a legacy symbolic base |
| `secret-shaped-member` | archive, inspect | a member or a scanned controller file matches one of the six secret patterns |
| `entry-name-policy` | inspect | an entry name breaks the name ceilings or the uniqueness rule |
| `entry-limit` | inspect | the entry count, an entry size or the expanded size exceeds its ceiling |
| `entry-mode` | inspect | an entry's mode is not `0100644` |
| `entry-compressed` | inspect | an entry's method is not 0 |
| `entry-encrypted` | inspect | an entry carries the encryption flag |
| `zip64-present` | inspect | a ZIP64 record is present |
| `trailing-data` | inspect | bytes sit before, between or after the ZIP structures |
| `manifest-mismatch` | archive, inspect | an entry's digest or size disagrees with `checkpoint.json`, or the capsule manifest digest disagrees with `controller_capsule.manifest_sha256` |
| `outer-digest-mismatch` | inspect, restore | the digest recomputed over the zip bytes differs from `--sha256` |
| `sidecar-mismatch` | inspect, restore | the sidecar beside the zip names another digest |
| `destination-occupied` | restore | the destination is neither absent nor an empty directory |
| `schema-unsupported` | inspect, restore | `checkpoint.json` carries an unknown schema or a controller version outside the compatibility set |
| `identity-mismatch` | inspect, restore | the identity member's `snapshot_id` differs from the manifest's or from the recompute, or `unavailable` is claimed where identity can be minted |
| `acceptance-self-reference` | inspect, restore | an `acceptance/current` entry is present |

## Secret patterns

Export scans every outer member and, inside the capsule, `state.json`,
`ledger.jsonl` and every opaque controller file for six patterns. The scan
reads in bounded chunks and carries between them the longest header the six can
match, so a header lying across a chunk boundary still refuses; that carry is
derived from the patterns rather than fixed. A hit refuses with
`secret-shaped-member`; nothing is redacted in place.

- A PEM private-key block, whose armour label also matches the OpenSSH header.
- The OpenPGP private-key header, `-----BEGIN PGP PRIVATE KEY BLOCK-----`.
- `ghp_[A-Za-z0-9]{36}`.
- `github_pat_[A-Za-z0-9_]{22,}`.
- `AKIA[0-9A-Z]{16}`.
- `xox[baprs]-`.

## Hostile fixtures

The inspector test module holds one `test_hostile_<id>` per id below, hyphens
written as underscores. Each fixture is a byte-level specimen the test builds
from a good archive, never a checked-in binary, and the inspector refuses it
before extraction can leave the disposable root. The 35 ids:

- `traversal-dotdot`
- `absolute-path`
- `backslash-separator`
- `drive-letter`
- `duplicate-name`
- `case-fold-collision`
- `non-utf8-name`
- `control-character-name`
- `nfc-mismatch-name`
- `directory-entry`
- `symlink-entry`
- `special-mode-entry`
- `setuid-or-executable-mode`
- `compressed-entry`
- `encrypted-entry`
- `zip64-record`
- `entry-count-over-limit`
- `expanded-size-over-limit`
- `bundle-over-limit`
- `size-mismatch`
- `trailing-data`
- `tampered-manifest`
- `unmanifested-member`
- `missing-member`
- `wrong-outer-digest`
- `tampered-sidecar`
- `wrong-receipt`
- `missing-object`
- `ref-map-mismatch`
- `secret-shaped-member`
- `self-referential-acceptance`
- `identity-mismatch`
- `unknown-schema-version`
- `signature-proof-mismatch`
- `absolute-source-path-in-manifest`

`wrong-receipt` is the capsule ledger prefix altered so the capsule manifest
digest no longer matches `checkpoint.json`; `missing-object` is a bundle
rebuilt with a prerequisite so `git bundle verify` names it;
`identity-mismatch` is an `identity/` member whose `snapshot_id` differs from
the recompute.

## Restore transaction

`restore --archive` is mutually exclusive with `--from` and
`--manifest-sha256`. In order:

1. Run the inspector over the archive; any finding refuses before any write.
2. Require a destination that is absent or an empty directory, checked
   through an opened descriptor and never through a symlink.
3. Create the repository: `git init`, `git fetch <bundle>
   +refs/heads/*:refs/heads/*` with `--no-tags`, then checkout of
   `config.git.base`. Every ref must equal the manifest map and the working
   commit must descend from `run.initial_base_sha`.
4. Write `remote.origin.url` as `https://github.com/<owner>/<name>.git`,
   derived from the validated `run.repository`, and fetch nothing. It is not a
   credential; `checkpoint identity` refuses without a bound origin.
5. Extract the capsule into
   `<destination>/.git/fiat-checkpoint-restore/<outer-sha256>/` and call the
   existing relocation transaction with `controller_capsule.manifest_sha256`.
   Its marker, retry and refusal rules are unchanged.
6. Recompute identity from the relocated state and compare `snapshot_id` with
   the identity member.
7. Run `verify`, `status` and `next`, print the restore result, and execute
   nothing. The restored run waits for the operator's explicit `hexctl next`.

A killed restore leaves the disposable root and the existing relocation
marker, which the existing retry rules resume or refuse. `git` and `gpg` run
through `bounded_tool` with fixed argv, output cap and timeout; the disposable
`GNUPGHOME` is created with mode 0700 under the scratch root, seeded only from
`proof/pubkey.asc`, started with `--no-autostart` and removed after use.

## Budgets

[checkpoint-archive-budgets.json](../scripts/checkpoint-archive-budgets.json)
declares six Metron budgets, all `lower_is_better` with variance 0.25, derived
in study section 10 from baselines measured on 2026-09-06 (bundle build 1,720
ms at 328 MB RSS, clone from bundle 1,020 ms, stored pack 26 ms).

| name | unit | limit | derivation |
| --- | --- | ---: | --- |
| `checkpoint.archive.export_wall_ms` | ms | 15000 | 5.4 x 2,766 ms |
| `checkpoint.archive.inspect_wall_ms` | ms | 10000 | 10 x a 1 s digest-and-verify pass over 100 MB |
| `checkpoint.archive.restore_wall_ms` | ms | 20000 | clone 1,020 ms plus the audited relocation, x10 |
| `checkpoint.archive.bytes` | bytes | 201581002 | 2 x 100,790,501 measured |
| `checkpoint.archive.expanded_bytes` | bytes | 209715200 | 2 x (bundle plus 3,212,143-byte capsule) |
| `checkpoint.archive.export_peak_rss_bytes` | bytes | 1073741824 | 3.3 x 328 MB measured |

The measured run is compared with
`python3 plugins/hexaemeron/skills/metron/scripts/metron.py check --budgets plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json --baseline plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-baseline.json --run .hexaemeron/metron/run.json`.
The baseline file lands with the measurements.

## Open items

The study fixes none of these; each is settled by a dated study amendment
before the code that needs it, not by an edit to this reference.

- The key spellings of the restore result's members other than
  `outer_sha256` and `snapshot_id`, and of the trailer counts and GitHub
  verification inside the signature proof.
- The fixed text of `README.txt`.
- The closed reason vocabulary behind `identity.status` `unavailable`.
- The schema of `acceptance/prior/<n>.json` and who signs it, deferred by name
  to issues #862 and #863.
- The refusal class each hostile fixture maps to, beyond the classes the
  runbook names per inspector check.
