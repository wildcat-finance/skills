# Cumulative carryover packet

Step 4 exports and validates inert evidence from an exhausted audit. It can
also bind an already uploaded GitHub attachment by reading back the packet's
exact bytes. These custody commands preserve the open findings and audit verdict;
export and attachment binding append receipts without closing the audit.
Step 5 introduces a separate replacement operation after complete reconstruction
and execution of explicitly mapped current guards.

## Export from the archived boundary

First use [controller checkpoint export](controller-checkpoint.md) at the true
`audit-verdict` boundary. Keep that archive and its separately reported manifest
SHA-256. The archive must contain the current controller state and ledger before
carryover export adds its receipt. A checkpoint from an earlier boundary refuses.

Run from the target repository with the supported Python interpreter:

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <run-worktree> checkpoint export --out <new-archive-directory>
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <run-worktree> carryover-export --request <export-request.json>
```

The export request is a closed JSON object. Its required fields are shown here:

```json
{
  "archive": "/absolute/path/to/checkpoint",
  "manifest_sha256": "<checkpoint-manifest-sha256>",
  "fixed_ref": "<locally-verified-signed-fixed-ref>",
  "previous": null,
  "out": "/absolute/path/to/508-CARRYOVER.md"
}
```

Request files are limited to 64 KiB. `archive` is an absolute checkpoint
capsule path. `fixed_ref` must resolve locally to the archived step's last
receipted commit and pass the controller's signature and provenance checks.
The output must have a new name under an existing absolute parent directory.
An optional `proof_repository` field names an absolute, separately prepared native
Git repository holding all required prior and current objects and signed fixed
refs. Omit it to retain the original Step 4 source-root behavior and receipt
shape. When supplied, the export receipt also binds that repository's path,
device and inode, and cumulative validation and receipt replay read the required
objects there. The current pass still comes from the actual live exhausted
archive and fixed tree, which must match the proof repository. Export neither
fetches nor modifies the proof repository or imports its refs into the live run.
For issue 508, names progress from `508-CARRYOVER.md` to `508-CARRYOVER-2.md`
and onward. The filename uses the bound issue number and cumulative pass count.

For a later pass, replace `previous: null` with
`{"path":"/absolute/path/to/508-CARRYOVER.md","sha256":"<prior-packet-sha256>"}`.
The archived source must already carry the matching parent receipt. A supplied
packet alone cannot create that lineage; the separate replacement operation must
establish its parent binding. Every earlier pass remains in the new packet, and every
prior packet digest is reconstructed from its exact cumulative prefix.

Export verifies the source, constructs and replays the complete packet, checks
for observed controller and fixed-ref drift, then creates the output exclusively.
Its detached `fiat-carryover-export/v1` receipt records the final Markdown digest,
source and archive identities, fixed commit and tree, sequence and occurrence
inventory. `attachment` remains null and `attachment_status` remains `unbound`.
A packet never contains its own digest or a provider URL that does not yet exist.

An interruption can leave an exclusive output without a controller receipt.
Inspect that output and the ledger before retrying. Occupied output names refuse;
the command does not remove independent bytes. The path checks and held directory
descriptor do not establish namespace atomicity or a lock against later changes.

## Packet format and replay

The exact envelope is `# Cumulative carryover packet`, a blank line, one JSON
fence, canonical JSON, and the closing fence. Canonical JSON has sorted keys,
compact separators and ASCII escapes. Its closed outer object contains:

| Field | Meaning |
| --- | --- |
| `schema` | `fiat-carryover-packet/v1` |
| `issue` | Canonical GitHub issue URL |
| `sequence` | Number of cumulative passes, from 1 through 32 |
| `filename` | Issue number plus `-CARRYOVER[-N].md` |
| `previous_sha256` | Null for pass 1; otherwise the exact preceding packet digest |
| `passes` | Every source pass, in order, with archive, Git identities, rounds and file dispositions |
| `files` | Sorted final disposition of every path inherited or changed across those passes |

Each pass preserves its controller run identity, archive location and complete
checkpoint evidence, original and fixed commits and trees, fixed ref, every
archived audit-round receipt, producer bytes and selected round bytes. Finding
occurrences retain the raw physical row, byte offset, ordinal and identity tuple
`[source_run, step, round, raw_id]`. Repeated rows remain separate occurrences.
Guard and family values are copied only from uniquely named producer-table
columns. They remain source assertions; export does not prove a guard executed.
Absent, ambiguous or empty guard/family values remain null, and the round
records their missing identity class in `unknown`, alongside legacy omissions. Replay does not infer a missing identity, merge repeated findings
or replace producer evidence with a synopsis.

Changed files carry complete bytes, SHA-256 and base64, with `100644`, `100755`
or `delete` disposition. Every inherited path receives its current fixed-tree
bytes and mode or an explicit deletion, including a path absent from the latest
diff. The final inventory is recomputed from all passes. Symlinks, submodules and
other special modes refuse.

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <repository-with-source-objects> carryover-validate --packet <packet.md> --sha256 <exact-packet-sha256>
```

Validation checks the envelope and digest, replays each archived controller and
ledger, rereads native local Git objects, verifies the signed fixed commit and
reconstructs the round, occurrence, lineage and file inventories. Git reads
disable replacement objects, inherited Git configuration and lazy fetching.
Missing objects or moved fixed refs refuse. Controller verification also derives
the export receipt from the packet and checks its ledger entry; matching JSON
fields alone are insufficient.

Only archived controller evidence is materialized, in a temporary private
directory for replay. Changed-file payloads are never installed or executed.
A successful result reports `status: validated` and
`replacement_admission: unavailable`. It establishes the checked custody and
source relationships, not the truth of audit judgements, test summaries or
historical model answers. No new model run occurs.

## Bind an uploaded attachment

Uploading is a separate operator action. After the provider supplies the final
URL, submit a closed request containing the export digest and provider identity:

```json
{
  "packet_sha256": "<exact-packet-sha256>",
  "attachment": {
    "identity": "<numeric-provider-id>",
    "url": "https://github.com/user-attachments/files/<numeric-provider-id>/508-CARRYOVER.md"
  }
}
```

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <run-worktree> carryover-bind --request <attachment-request.json>
```

Binding requires the same exhausted audit, one recorded export and no prior
binding. The URL's numeric identity and packet filename must match the request
and export. An unauthenticated GET must return the exact packet size and digest.
The reader accepts either HTTP 200 from that URL or one HTTP 302 redirect to the
restricted repository-file path on `objects.githubusercontent.com`, followed by
HTTP 200. It sends no caller credentials, cookies or headers across either
connection. It neither uploads the file nor proves that the attachment appears
in an issue comment.

The detached `fiat-carryover-attachment/v1` receipt joins the provider identity to
the completed packet digest without changing packet bytes. Later controller
verification checks this recorded observation and its ledger binding; it does
not repeat the GET or establish continued provider availability.

## Replacement reconstruction and inoculation

Start from a fresh, already initialized run at the exact current base. It must
still be in the study phase with no steps, replacement or carryover-parent receipt,
and its clean HEAD must equal the recorded base. The bound issue must match the
packet. Supply one complete cumulative packet and an explicit read-only
`proof_repository`.

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <new-run-worktree> replacement-begin --request <replacement-request.json>
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir <new-run-worktree> replacement-resume
```

The replacement request is a closed object with these fields:

| Field | Required value |
| --- | --- |
| `schema` | `fiat-replacement-request/v1` |
| `packet` | Object containing `path` and the exact packet `sha256` |
| `proof_repository` | Absolute native repository path holding the archived source objects and signed refs |
| `attachment` | Existing provider object containing `identity` and `url` |
| `files` | One mapping for every path in the packet's final file inventory |
| `occurrences` | One mapping for every raw finding occurrence across every source pass |
| `execution` | Closed `fiat-inoculation-request/v1` object with `schema`, `guards` and `dependencies` |

`replacement-begin` validates the packet against the proof repository and reads
back the attachment using the same URL, size, digest and transport limits as
custody binding. It records a prepared pending transaction; it does not yet
execute guards or promote candidate files. `replacement-resume` takes no request
argument: it uses that recorded request and checks its exact bytes.

The packet embeds archived controller evidence, not a Git bundle. Its signed
historical refs and native Git objects must remain available in that proof
repository; missing provenance refuses before candidate guard execution.

Every supported tracked current-base file is reconstructed privately before any
candidate guard runs. Each carried file has one explicit unchanged, transformed
or conflicted mapping, with complete result bytes and mode or a deletion.
Its `base` object binds source and target preimages on the new base: each is
null or an exact Git mode and blob object ID. The controller derives those
preimages from the actual base and rejects a mismatch. If the new base differs
from the archived source-base preimage and is not already identical to the
intended result, the mapping must declare the conflict. Independent originals
stay available. A partial mapping, destination collision,
unsupported path or mode, missing source occurrence or changed evidence refuses.

A file mapping contains exactly `source`, `target`, `disposition`, `result`,
`reason` and `base`. `target` and `result` are both null for a deletion. Otherwise,
`result` contains `mode` (`100644` or `100755`) and `payload`, whose closed object
contains `bytes`, `sha256` and canonical `base64`. An unchanged mapping must retain
the packet's path and exact result. The `base` object's `source` and `target`
preimages each contain `mode` and `oid`, or are null when absent.

Each raw finding occurrence is mapped by its exact identity tuple, byte offset,
ordinal and raw-row SHA-256. Repeated finding identifiers do not collapse into
one occurrence. A current mapping names its guard and family and retains the
source's previous values. The canonical historical audit header has no guard or
family columns, so those source values remain null and unknown. Newly declared
mappings establish current coverage only; they cannot prove that a historical
guard existed or ran.

An occurrence mapping contains exactly `occurrence`, `guard`, `family`,
`previous_guard`, `previous_family` and `reason`. Its `occurrence` object carries
`identity`, `offset`, `ordinal` and `raw_sha256`; `identity` is
`[source_run, step, round, raw_id]`. The previous guard and family values must
match the preserved occurrence, including nulls. Missing producer bytes, selected
span, finding-count evidence or archived entry digest blocks admission.

The fixed adapter validates a restricted Python source form, then compiles and
executes the accepted guard and dependency bodies unchanged. Descriptors bind
source files, selected methods, body digests and explicit dependency module
names. The adapter owns the assertion observer and result file. A guard must
enter, finish and execute a supported assertion; discovery or a selected name
alone cannot pass. Arbitrary unittest behavior, lifecycle hooks, decorators,
unsupported imports and reflective or dynamic dispatch refuse. This restriction
is an executable subset, not a substitute implementation of a guard's logic.

Each guard descriptor contains `id`, `family`, `source`, `class`, `method` and
`body_sha256`. `source` and each dependency descriptor contain `path` and
`sha256`. Dependency module names must match the source paths and the explicit
imports used by the guard; arbitrary module loading and aliases are unsupported.
Source files are capped at 1 MiB and 20,000 AST nodes, with at most 128 dependency
files and 4,096 guards. The fixed observer supports equality, inequality,
truth/falsehood and the four ordered-comparison assertion methods. A return
without an observed assertion refuses.

The internal native worker receives a read-only copy of the complete reconstructed
input. This input API is not added to the public worker request. The active
reservation is twice the image bytes, twice the original backup bytes and the
largest simultaneously live candidate temporary, together bounded by 256 MiB.
Each file is limited to 64 MiB, and each inventory to 4,096 files; internal driver
and request files count toward the inventory. An independently grown destination
moved into custody is retained as evidence rather than copied under that active
reservation. Retired attempts, retired temporaries and displaced independent
bytes remain preserved, so this is not a total history or global disk quota.
Packet and decoded evidence retain their separate 64 MiB limits; historical
native Git proof reads retain the 2 MiB per-call cap.

The complete reconstructed image and retained originals live in preserved
private storage outside `.hexaemeron`. The controller archive keeps the bounded
request, packet, plan, capture, report and private-directory identity. Replay
requires both that storage and the read-only native proof repository; a copied
controller archive alone supplies neither dependency. This keeps the complete
base copy out of the later cumulative packet's 64 MiB evidence budget.

Pending work and resume retain partial output, staging and originals. Recovery
checks the recorded source and destination identities before continuing. These
checks observe drift; they do not provide atomic namespace rollback. The admitted
replacement still requires a fresh independent audit and inherits no clean
verdict from the old run. It is a new transition, distinct from restoring a
checkpoint.
Historical custody results that report `replacement_admission: unavailable`
remain unchanged.

The pending `fiat-replacement-pending/v1` record moves through `prepared`,
`guarded` and `promoting`. Here `guarded` names passed replacement guards; it is
not Elenchus's verdict from a failing Git-parent test and repaired-source pass.
A failed prepared attempt remains available while a
retry reconstructs and executes in a new private stage. A guarded or promoting
retry verifies the stored image, plan and report before continuing. Promotion
moves the actual destination into a preserved private displaced slot and checks
its bytes and mode against the bound preimage. It installs the candidate
exclusively; a concurrent destination cannot be overwritten by that installation.
On refusal, the old backup and displaced independent bytes remain preserved,
but the destination can be absent. Original Git modes remain in `plan.original`;
the backup files themselves have mode `0400`. Admission and replay bind and verify
the original backup and displacement inventories. Recovery must inspect those
retained files. Some interruptions during promotion require explicit operator
restoration or cleanup of retired temporaries before resume; there is no atomic
rollback. Ordinary acceptance is blocked
while the replacement remains pending. `status`, `verify`, `halt --reason` and
the ordinary `resume` command remain available for inspection and recovery.
A halted run must clear its halt with ordinary `resume` before
`replacement-resume` can continue.

A successful `fiat-replacement-admission/v1` receipt reports `status: admitted`,
`fresh_independent_audit_required: true` and `historical_audit_reused: false`.
It establishes the separate `carryover_parent` binding for any later cumulative
export. Controller verification rereads the native provenance, retained stage,
report and ledger bindings; it does not repeat attachment GETs or execute the
guards again. Preserve the transaction's recorded storage locations and any
interrupted unreceipted files for inspection. Editing a bound request, implementation file or report invalidates the recorded
transition; resume cannot accept substituted evidence.

## Bounds and refusals

The packet's Markdown bytes and its total decoded blob inventory each have a
64 MiB budget. Repeated embedded blobs count each time. Producer reads first reserve space
for the full producer, selected span and raw occurrence copies. Cumulative
reservations also account for prior passes and the final file view; they can
refuse a packet below 64 MiB. JSON depth is limited to
32, each container and relevant inventory to 4,096 items, and lineage to 32
passes. Native Git calls have a separate 2 MiB output cap, so an individual
changed blob larger than that refuses even when the packet budget has room.

Paths are relative and ASCII-only. Absolute paths, backslashes, empty or dot
components, colons, surrounding component whitespace, case aliases and ancestor
collisions refuse. Changed-file paths also exclude `.git` and `.hexaemeron`
components. Regular-file reads refuse symlinks, hard links, special files and
observed identity or content drift.

GitHub documents a **25 MB limit for nonmedia attachments** in its
[attachment guide](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files).
The reader separately caps an attachment at `25 * 1024 * 1024` bytes. Passing the
internal 64 MiB packet checks does not establish provider upload eligibility.

Attachment readback has a 30-second acceptance deadline and socket timeouts of
at most 15 seconds, reduced to the remaining budget. Late responses are rejected.
These checks do not guarantee a hard total return time: DNS resolution,
trickling response headers and detached response sockets, including
`Connection: close` cases, can outlive that deadline.

On refusal, inspect the named code, preserve the source archive, packet and
independent edits, and repair the missing or mismatched evidence before retrying.
Export, validation and binding do not close pull requests, delete branches,
merge code or admit a replacement run.
