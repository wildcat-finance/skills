# Directory checkpoints for large repositories

Use the native directory carrier when complete Git history exceeds the ZIP
carrier's 1 GiB bundle limit:

```text
hexctl --dir <run-worktree> checkpoint archive --format directory
hexctl checkpoint inspect --archive <checkpoint.directory> --sha256 <manifest-hex>
hexctl --dir <empty-destination> checkpoint restore --archive <checkpoint.directory> --sha256 <manifest-hex>
```

The default remains `--format zip`. Its schema and limits are unchanged.
Both formats use the accepted boundaries, fixed local store, occupied-boundary
refusal and mandatory local hand-off in
[push-discipline.md](push-discipline.md). Neither publishes to a host.

## What the digest names

The directory contains the same member paths as
[the ZIP carrier](checkpoint-archive.md), with `checkpoint.json` at its root.
Its schema is `fiat-checkpoint-directory/v1`; `archive.format` is `directory`
and `archive.compression` is `stored`. Every other member has one exact path,
byte count and SHA-256 in the manifest. Canonical JSON and the closed field
sets remain mandatory.

For this carrier, `outer_sha256` is **SHA-256 of the exact `checkpoint.json`
bytes**, including its final newline. It equals `manifest_sha256`. It is not
the digest of a ZIP file or a concatenation of directory entries. Preserve it
outside the directory and hand it over explicitly. The adjacent
`checkpoint.directory.sha256` sidecar names the directory and repeats that
digest; a present sidecar must agree, but it supplies no independent trust.

Export and inspection return `fiat-checkpoint-directory-export/v1` and
`fiat-checkpoint-directory-inspect/v1`. Restore retains
`fiat-checkpoint-archive-restore/v1`, including its `restore.worktree`,
`snapshot_id` and semantic `next`. A rebuild of unchanged input preserves
member bytes and the manifest digest; filesystem timestamps are not identities.

## Verification and limits

The complete-history bundle may contain at most 256 GiB. All members together,
including the manifest, may contain at most 256 GiB plus 300 MiB. The existing
limits of 4,200 files, 64 MiB per non-bundle member, 1,024 bytes per path and
255 bytes per component still apply, as do the capsule's smaller limits.
These are acceptance limits; bundle creation can consume temporary storage
before its resulting size is checked.

Inspection opens the root and each path component without following symlinks.
It requires exactly the manifest's files and their parent directories and
rejects hard-linked, executable, set-id, special, missing and extra members.
Each file is captured into private scratch, hashed and scanned in bounded
chunks; observed source mutation refuses. Subsequent readers use only those
captured bytes. Ref joins, complete history, isolated signature verification,
capsule, identity, acceptance and secret checks are shared with the ZIP reader.
An altered manifest needs a different out-of-band digest; an altered member
fails its manifest join.

## Storage and restore

The bundle capture first attempts an independent filesystem clone from its
open descriptor: Apple's `fclonefileat`, or Linux `FICLONE`. A supported clone
uses copy-on-write storage; otherwise the reader streams a private copy. It
never hard-links the supplied bundle. See the
[Apple APFS APIs](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/APFS_Guide/ToolsandAPIs/ToolsandAPIs.html)
and [Linux FICLONE contract](https://man7.org/linux/man-pages/man2/FICLONE.2const.html).

Directory bundle creation, capture and import each have a six-hour limit.
Creating a run worktree and materialising a restored checkout also have a
six-hour limit; ordinary controller queries retain their 30-second limit.
Inspection needs space for its captured bundle and reconstructed Git objects.
Restore also needs the origin checkout and run worktree. Filesystem clones
can reduce physical storage, but callers must allow for stream-copy fallback.

Restore locally clones the already verified scratch repository, preserving
its objects after scratch cleanup, then uses the existing capsule relocation
transaction. It fetches nothing from the network and executes no directive.
Destination and interrupted-restore residue rules remain those in the ZIP
reference. Keep `checkpoint_directory.py` beside the supplied `hexctl.py`;
both belong to the controller runtime.
