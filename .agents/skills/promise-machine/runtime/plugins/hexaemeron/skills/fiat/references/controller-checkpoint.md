# Fiat controller checkpoint

This reference specifies the controller-owned capsule accepted by
[ADR-028](../../../../../docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md).
The capsule moves exact `.hexaemeron` bytes. It does not replace the standing
Git bundle, signature proof, checkpoint archive, outer sidecar, Drive object or
issue note.

## Export command

Run export from the live run worktree:

```text
hexctl --dir <run-worktree> checkpoint export --out <new-directory>
```

The output path may be absolute or relative to `--dir`. Its parent must already
exist and must not resolve through a symlink. The named directory must not
exist. It cannot sit beneath the live `.hexaemeron` directory.

Export takes the run lock and calls the controller's ordinary verification
before it reads any source byte. It does not append a receipt or change
`state.json` or `ledger.jsonl`.

## Accepted boundaries

Export accepts exactly two controller states:

1. The ledger tail is `done:push`. No later mutating controller action has
   happened, so the run is at the successful end of one step before the next
   directive is acted on.
2. The ledger tail is `audit-round` and `next` is `audit-verdict`. The current
   audit loop is exhausted with findings still open.

`status`, `verify` and `next` do not change either boundary. Any later ledger
entry closes it. Every other global or step phase refuses before an output
directory appears. A pending amendment or `state.json.tmp` transaction also
refuses.

## Directory format

```text
<capsule>/
  MANIFEST.json
  controller/
    .gitignore
    state.json
    ledger.jsonl
    ...every remaining regular .hexaemeron file...
```

The live `lock` file is the sole file exclusion. Empty source directories are
omitted, so every capsule directory is implied by a recorded file. Capsule
directories use mode `0700`; files use mode `0600`.

`MANIFEST.json` is canonical UTF-8 JSON: keys are sorted, separators are `,`
and `:`, and one LF follows the object. Its SHA-256 covers those exact bytes and
is reported outside the capsule. The manifest contains no timestamp or source
filesystem path.

The top-level object is closed to these fields:

| field | value |
| --- | --- |
| `schema` | `fiat-controller-checkpoint/v1` |
| `controller` | controller name, state schema version and Fiat version |
| `boundary` | `kind`, the semantic `next` object and the exact local ref-to-commit map |
| `source` | exact state and ledger SHA-256 values, semantic state fingerprint, ledger entry count and tail hash |
| `resources` | controller file count, byte count and every enforced ceiling |
| `files` | sorted `controller/<relative-path>` records containing `path`, `bytes` and `sha256` |

The manifest digest identifies exact manifest bytes. It is not the semantic
checkpoint identity, service acceptance or outer archive identity owned by
the remaining Wave Delta work.

## Read boundary

Every source component must be a UTF-8 path no longer than 1,024 bytes. Empty,
dot, parent, slash, backslash and control-character components refuse. The
source tree may contain at most 4,096 regular files and 4,096 directories, with
these byte ceilings:

| resource | ceiling |
| --- | ---: |
| one controller file | 64 MiB |
| all controller files | 256 MiB |
| `MANIFEST.json` | 1 MiB |

Each directory and file is opened without following symlinks. A regular file
must have one link. Devices, sockets, FIFOs, symlinks and hard-linked files
refuse. The exporter compares device, inode, mode, link count, size, mtime and
ctime before and after each read. It then reads and hashes the complete source
tree a second time and compares the sorted inventory before publication.

`state.json` and every non-empty ledger line must be strict UTF-8 JSON with no
duplicate object key. The captured state must equal the verified live state.
The captured ledger must reproduce its full hash chain, end at that state's
fingerprint, and agree with the manifest's count and tail.

Each ref already named by the state is resolved with fixed-argument, bounded
Git. The base, run branch and every receipted implementation branch are
resolved before capture and again before publication. A missing, malformed or
moved ref refuses.

Refusals name the failed class, not source filenames, file content, Git output
or JSON values. This keeps a hostile controller entry from entering a
diagnostic.

## Publication

The exporter builds a mode-`0700` sibling directory whose name starts with a
dot. It copies and verifies the controller tree, writes `MANIFEST.json` last,
flushes files and directories, and publishes with an atomic no-replace
directory rename. A platform without that primitive refuses. An occupied path,
including one that appears during finalisation, is never replaced.

An ordinary refusal removes its private stage. A process killed before the
rename can leave that hidden sibling, but the requested output path remains
absent. It is not a published capsule and may be inspected and removed before
retrying the same command.

Success writes one JSON object to stdout using schema
`fiat-controller-checkpoint-export/v1`. It names the destination, boundary,
semantic directive, ref map, resource totals, manifest SHA-256, state byte and
semantic identities, and ledger byte, count and tail identities. Keep the
reported manifest digest outside the capsule; restore requires that value.

## Current recovery boundary

This generation exports only. It does not create or verify the Git bundle,
package an archive, publish to GitHub or Drive, import a capsule, rewrite
controller paths or append a relocation receipt. Until `checkpoint restore`
lands, a missing source worktree still requires the standing manual recovery
procedure. Do not call a fresh Fiat ledger a continuation of this capsule.
