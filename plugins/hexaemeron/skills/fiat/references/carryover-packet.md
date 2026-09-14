# Cumulative carryover packet

Step 4 exports and validates inert evidence from an exhausted audit. It can
also bind an already uploaded GitHub attachment by reading back the packet's
exact bytes. Replacement admission remains unavailable until Step 5. These
commands preserve the open findings and audit verdict; export and attachment
binding append custody receipts without closing the audit.

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

The export request is a closed JSON object:

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
For issue 508, names progress from `508-CARRYOVER.md` to `508-CARRYOVER-2.md`
and onward. The filename uses the bound issue number and cumulative pass count.

For a later pass, replace `previous: null` with
`{"path":"/absolute/path/to/508-CARRYOVER.md","sha256":"<prior-packet-sha256>"}`.
The archived source must already carry the matching parent receipt. A supplied
packet alone cannot create that lineage; Step 4 supplies no replacement-run
admission command. Every earlier pass remains in the new packet, and every
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
