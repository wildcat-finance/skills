# Decision: Build the outer checkpoint archive natively

## Status

Proposed, 2026-09-07.

Unnumbered on purpose. The number is assigned from the integration base at
sync by
`python3 plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py plan|apply|replay`,
which indexes drafts below `docs/decisions/drafts/`; before and after that
assignment the record is cited by its stable slug reference
`adr/build-the-outer-checkpoint-archive-natively`.

Once accepted and numbered, this record reverses one rejected alternative of
ADR-028, "Complete standing-checkpoint automation", for the next controller
generation. ADR-028 stays Accepted, and its amendment of 2026-09-07 points
here.

## Context

ADR-028 fixes the checkpoint store, the two accepted boundaries, the zip's
contents and the mandatory local hand-off. It rejects complete
standing-checkpoint automation "for this controller generation because one
command would join controller mutation, archive parsing and key handling".
`hexctl` therefore builds only the controller capsule through
`checkpoint export`, and the agent assembles the Git bundle, signature proof,
outer manifest, sidecars and README by hand from `push-discipline.md`.

The manual archives on this machine, read on 2026-09-06, show what that
produces. No two runs share a layout. Entries carry build-time mtimes, mixed
modes `0644` and `0600`, directory order and deflate compression. One outer
manifest records the producer's absolute origin path. The sidecar names the
zip three different ways across runs. No restore transcript exists from a
machine that did not write the archive. Issue #861 requires byte-identical
rebuilds, restore without the source clone and a clean-machine transcript,
none of which that procedure can give.

The network, Drive, service, authority and lineage parts of the automation
ADR-028 declined now belong to issues #862 through #867 and to ADR-028's
mandatory-local amendment. What remains is one archive writer, one reader and
one restore path around the already audited capsule exporter and relocation
transaction.

## Decision

`hexctl` gains three subcommands inside the controller, with their contract in
`plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`:

```text
hexctl --dir <run-worktree> checkpoint archive
hexctl checkpoint inspect --archive <zip> --sha256 <outer-hex> [--scratch <new-dir>]
hexctl --dir <empty-destination> checkpoint restore --archive <zip> --sha256 <outer-hex>
```

The carrier is a stored ZIP written with the standard library `zipfile`:
method 0, Unix mode `0100644`, DOS time 1980-01-01 00:00:00, `create_system`
3, entries sorted by UTF-8 bytes, no directory entries, no ZIP64 records, no
comment, no extra fields.

One content manifest, `checkpoint.json` with schema
`fiat-checkpoint-archive/v1`, records every entry's path, size and SHA-256 and
joins the outer digest, the capsule manifest digest and `snapshot_id`. It
replaces the per-member `.sha256` sidecars inside the zip. The outer sidecar
beside the zip stays.

The layout is fixed at nine entry paths: `checkpoint.json`, `README.txt`,
`git/repository.bundle`, `controller-capsule/MANIFEST.json`,
`controller-capsule/controller/...`, `identity/checkpoint-identity.json`,
`proof/signatures.json`, `proof/pubkey.asc` or `proof/allowed_signers`, and
`acceptance/prior/<n>.json`. `acceptance.current` is the literal `outside`.

Every bundle is built with `git -c pack.threads=1 bundle create` from exactly
the controller's bounded ref set. Default threading gave two different bundles
from one state (100,790,849 bytes three times and 100,791,737 bytes once);
single threading gave one digest four times.

Signatures are verified in a disposable keyring: a `GNUPGHOME` created with
mode 0700 under the scratch root, started with `--no-autostart`, seeded only
from `proof/pubkey.asc`, pinned to the manifest fingerprints and removed after
use, or `gpg.ssh.allowedSignersFile` pointing at `proof/allowed_signers` built
from the same manifest. The operator's keyring is never read.

Restore writes `remote.origin.url` as `https://github.com/<owner>/<name>.git`
from the manifest's validated `owner/name` and fetches nothing. The value is
not a credential; `checkpoint identity` refuses without a bound origin.

## Alternatives

Four candidates were measured on this repository at `0bc39f27` under the
`protasis-design-evidence/v1` record with SHA-256
`101172ad264e56b0910cc64e8f11662da8b7f874ca030c3da76ba7cfacf6db91`. Three
selection gates (byte-identical rebuild, restore without the source clone,
capsule contract reused) and three metrics decided it.

| candidate | pack ms | carrier bytes | spawned programs | gates |
| --- | ---: | ---: | ---: | --- |
| A `native-subcommands`, selected | 26 | 100,790,501 | 2 | three pass |
| B `sidecar-script` | 26 | 100,790,501 | 3 | three pass |
| C `inspector-only` | 1,977 | 100,470,196 | 4 | byte-identical rebuild and restore without the source clone fail |
| D `external-archiver` | 335 | 100,790,483 | 3 | byte-identical rebuild fails |

B, a `checkpoint_archive.py` beside `hexctl` driving `checkpoint export` and
`restore` as subprocesses, lost because it needs the controller's path-safety,
stable-read and bounded-tool helpers, so it either imports `hexctl` and is the
same process after all or duplicates them, and two entry points then agree on
the compatibility set, the boundary rule and the identity join by convention.
It packs identically to A and spawns one more program per export.

C, keeping the manual procedure and adding only `checkpoint inspect`, lost
because the procedure fixes no timestamp, order or mode rule, so two exports
of one state differ, and it names no restore command, so a receiver still
needs the prose. It fails the issue's criteria 2 and 3.

D, the same three subcommands packing with `zip(1)` and `unzip(1)`, lost
because `zip -X -D -0` reads entry times from the filesystem and a rebuild
after a 2 s mtime shift differed, because the inspector would trust `unzip`'s
path handling at the exact boundary the hostile fixtures attack, and because
Info-ZIP 3.0 and UnZip 6.00 would become clean-machine dependencies.

## Consequences

The controller grows by one archive parser and one key-handling path, the
join ADR-028 declined for the previous generation. The cost is accepted
because the parser is a bounded reader of a format the controller itself
wrote, the mutation it feeds is the already audited relocation transaction,
and every refusal happens before that transaction. One controller means one
compatibility set, one read boundary and one test harness.

Two exports of one state are byte-identical, so a receiver compares digests
rather than archives. The acceptance statement stays outside the archive:
`acceptance/prior/` is reserved for issues #862 and #863 and nothing else is
claimed for them. No network, upload, service or resume is added; a restored
run waits for the operator's explicit `hexctl next`.

The change alters the controller, so under
`plugins/hexaemeron/skills/VERSIONING.md` it is a Fiat `generation`. Its
ledger row, version and compatibility-set entry land with the last step of the
delivering run, and the tracked study `docs/fiat-checkpoint-archive-study.md`
and runbook `docs/fiat-checkpoint-archive-runbook.md` are run artefacts that
point here rather than a second home for this decision.
