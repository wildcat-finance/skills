# Fiat controller checkpoint

This reference specifies the controller-owned capsule accepted by
[ADR-028](https://github.com/wildcat-finance/skills/blob/main/docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md).
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
duplicate object key or non-finite number. The captured state must equal the
verified live state. The captured ledger must reproduce its full hash chain,
end at that state's fingerprint, terminate with LF so the exact prefix remains
appendable, and agree with the manifest's count and tail.

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

## Restore command

Restore the Git boundary with the standing outer procedure first. The fresh
checkout must be a clean top-level worktree, and every local ref named by the
manifest must already resolve to its recorded commit. Then run:

```text
hexctl --dir <fresh-origin> checkpoint restore \
  --from <capsule-directory> \
  --manifest-sha256 <sha256-reported-by-export>
```

The digest is mandatory out-of-band evidence. Restore recomputes it over the
exact canonical manifest bytes; a digest found inside the capsule would not
establish the same boundary.

Restore treats the capsule as hostile. Before it creates active state, it
checks the schema and closed object shapes, canonical manifest encoding,
resource declarations, sorted inventory, every file digest, state identity,
the exact ledger prefix and tail, a controller version in the restoring
controller's explicit compatibility set, accepted boundary, semantic next
directive and local Git refs. Capsule reads use the export ceilings and
no-follow, stable-file rules. The controller inventory is closed: an excluded
live `lock` appearing in a capsule is an extra entry and refuses.

New study and runbook receipts store a relative path with no empty, dot,
parent or backslash segment. A legacy absolute receipt is accepted only when
its recorded old origin, derived worktree and run branch agree and the source
is an exact safe descendant of that worktree; restore converts it to the same
portable relative form. A `.hexaemeron/` source is verified from its capsule
copy before the worktree exists; other sources are verified from the fresh Git
tree. Both use the ordinary 2 MiB source cap.

## Relocation transaction

The new origin's `.hexaemeron/checkpoint-restore.json` is published before the
derived worktree or its sibling private stage is created. It binds the
manifest digest, run branch and exact owned paths. An existing controller
directory, occupied derived worktree, conflicting marker, symlink or changed
ref refuses without replacing or deleting it. Creation pins the origin and new
controller directory and writes both private files relative to those open
directories, so moving the new directory cannot redirect either write. The
derived worktree home is traversed component by component without following a
link, and its exact ignore file is read or created through the pinned home.

The private stage receives the verified controller tree. All files other than
`state.json` and `ledger.jsonl` remain byte-identical. Fiat changes
`config.git.origin`, `config.git.worktree`, and any admitted legacy study or
runbook artifact path, then appends one `checkpoint:restore` entry to the exact
imported ledger prefix. That entry binds the manifest, source state and ledger
digests, prior tail, full ref map and relocated state fingerprint. The
completed controller directory is
published with an atomic no-replace rename. State and ledger replacements are
written relative to the pinned private-stage directory and stop if its named
identity changes. The relocated state remains under the controller-source cap
and the appended ledger remains under the capsule file cap. The closed
inventory and every opaque file digest are rechecked from the active tree
around finalization. Local refs are checked before publication, after the
rename and again after the internal checks and breadcrumb write. The
worktree's directory identity and symbolic `HEAD` must remain unchanged across
the internal checks and the same finalization boundaries, including an
interrupted-publication retry.

A retry after an interruption never guesses ownership. A marker with no owned
path may resume. A marker whose private stage or incomplete worktree remains
refuses and preserves both for inspection. If active state was published
before the breadcrumb and marker retirement, a retry verifies the single
restore entry, the exact relocated state bytes, the imported prefix and the
full bound receipt, then completes those two final operations without
appending a second entry. The breadcrumb is created without following or
replacing another entry; a retry accepts only its exact, stable single-link
bytes. Marker retirement likewise rechecks the marker's stable single-link
identity and exact transaction bytes before unlinking it. Once the marker is
retired, another restore is a replay and the occupied derived worktree refuses
it.

On success Fiat recreates the origin breadcrumb, runs its internal ledger
verification and status reader, recomputes the semantic next directive and
executes no directive. Stdout is one bounded JSON object using schema
`fiat-controller-checkpoint-restore/v1`. It reports the manifest and state
identities, new ledger digest/count/tail, ref count, worktree, verification
result, status-output digest, semantic next object and whether it completed a
new or interrupted publication.

## Outer recovery boundary

These commands do not create or verify the Git bundle, package an archive,
publish to GitHub or Drive, handle keys or mint a semantic checkpoint
identity. ADR-028 retains those jobs in the standing manual outer procedure.
Restore accepts a directory already obtained and verified by that procedure;
it does not extract an archive or fetch a remote object. Continuation means
the imported ledger plus its one relocation entry, never a fresh Fiat ledger.
