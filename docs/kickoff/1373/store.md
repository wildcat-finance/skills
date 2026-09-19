# Durable store inputs for #1373 and #1380

Status: blocked. This cross-target register prepares
[#1489](https://github.com/wildcat-finance/skills/issues/1489). The selected
capture, approved store policy and accepted rights handoff are missing.
Retrieval has not run, so this record does not complete #1489.

## Provenance

Observed on 2026-09-19 at 17:30:41 UTC against Skills revision
[`e2307ed5966e18727434b3e49bec89db736f7b17`](https://github.com/wildcat-finance/skills/tree/e2307ed5966e18727434b3e49bec89db736f7b17).
Producer: Codex, task `01a0bab4-76ef-71d3-923c-ea6001aa55bc`.
Review: producer self-review; independent reviewer and human storage
decision-maker are unassigned. The request to create and merge a PR supplies
no retention, access, migration or spending decision.

[`inputs.json`](inputs.json) preserves the source paths, file byte counts,
SHA-256 values, pinned links, recorded Dokimasia identities and unresolved
fields. [`source-SHA256SUMS`](source-SHA256SUMS) lists the input file digests;
[`SHA256SUMS`](SHA256SUMS) binds this document, that JSON file and the input list.
The inspection covers the cited Skills files and the linked issue records;
it does not establish that missing inputs are absent elsewhere.

## Verified release limits

At the pinned revision, `release.py:55-56` limits an Alexandria release to
128 components of at most 67,108,864 bytes each: 8,589,934,592 raw component
bytes, or 8 GiB. A larger capture needs multiple releases or a reviewed
format extension under
[#1373](https://github.com/wildcat-finance/skills/issues/1373).

`release.py:100` derives local paths as
`objects/sha256/<first-two-hex>/<sha256-hex>`. The `external-object` locator
at line 49 records a source reference. Ingest reads local component paths
and verification is offline; neither operation retrieves remote objects.
The store's namespace and retrieval identity convention remain undecided.

No accepted manifest or byte/component census identifies the larger-than-8-GiB
capture. The historical 343-component case in #1373 has no source linked in
this register. Neither a smaller demonstration nor a different local capture
can supply its identity.

## Dokimasia inputs

The committed scrutiny records the following identities. The primary inputs
have not been retrieved or re-hashed in this task.

| Input | Recorded identity | Remaining input |
| --- | --- | --- |
| Application | `wildcat-finance/wildcat-app-v2` at `bb9685fb7dbe9cd2f5b7683a9b3f164509dc2de9` | Exact checkout archive bytes, SHA-256 and destination |
| Reviewed workbook | `wildcat_v25_uat_v2-jack.xlsx`, SHA-256 `9da2f2e8bbdb0271fac8d9a71f3f4129ca2d4ad79a4c1ee2f46412e831212a25` | Authorised primary bytes and destination |
| Scrutiny | `dokimasia-scrutiny/v1`, tool version `3.1.0`; file SHA-256 `eb0ad475c7015c4ac6f08ebf6ab1cec2bed1de125bb8e472fd4fc850519fb920` | Rebuild from the stored primary inputs under #1380 |
| Confirmation rules | Projection SHA-256 `65d095d82b5e10c846fd189d00d51432775b219075f2f24879de825c503583d6` | Consumer review of this projection convention |

The rules digest above is computed for this register from the committed
dispositions file's `rules` object: UTF-8 JSON with sorted keys,
`ensure_ascii=False`, separators `(',', ':')`, then one LF. It is not an
identifier emitted by Dokimasia. The source file's digest is in `inputs.json`.

The raw XLSX digest, normalised workbook digest, scrutiny's logical digest
and scrutiny file digest identify different bytes. `inputs.json` keeps
them separate. A Git commit likewise does not supply a checkout archive's
SHA-256.

The pinned Dokimasia study states that the reviewed workbook's bytes are
not republished. This register contains only identities already committed
to Skills. It grants no access to the workbook or permission to publish it.
Dokimasia owns workbook reconstruction under
[#1380](https://github.com/wildcat-finance/skills/issues/1380); Alexandria's
lending-input contract does not make it a general workbook archive.

## Decisions still required

| Decision | Owner | Current evidence |
| --- | --- | --- |
| Capture manifest, source revision and complete byte/component census | Capture producer and storage operator | No accepted target or manifest supplied |
| Store provider, account/bucket or immutable namespace, object keys and retrieval identity | Storage operator | No named store or decision reference |
| Retention period, deletion conditions and retention owner | Storage operator | Undecided |
| Permitted audience, access owner and access policy | Source custodian and storage operator | No target-matched rights record |
| Credential rotation owner, interval and revocation procedure | Storage operator | Undecided; no credentials belong in this record |
| Retain or migrate existing split parts | Storage operator | Parts inventory and migration decision missing |
| Authorised cost and capacity, including local staging | Named human decision-maker | No budget or capacity authorised |
| Reviewer acceptance | Reviewer | Unassigned |

[#1364](https://github.com/wildcat-finance/skills/issues/1364) was open at
inspection. Its implementation discussion does not supply this capture's
accepted source-digest, rights-basis, disclosure and audience decisions.
Consume the actual target-matched record and its digest before storing
restricted inputs. Public visibility and issue closure supply neither
private custody permission nor public disclosure permission.

## Retrieval rehearsal

Status: not run. No target store, approved object or retrieval identity is
available, so there are no successful, missing, denied or corrupt-object
results to report. A local fixture would not establish access to the
operator's store.

After the missing inputs are accepted, the rehearsal must record the exact
tool/version, secret-free command, principal alias, immutable object key,
expected byte count and SHA-256, exit status and retrievable result evidence.
Keep credential values and signed retrieval URLs outside the record.

| Case | Required observation | Current result |
| --- | --- | --- |
| Present object | Fetch into a fresh, size-bounded staging directory; match byte count and SHA-256 before offline verification | Not run |
| Missing object | Named retrieval failure; no verified input or empty-dataset success | Not run |
| Denied object | Retrieval refused for the declared identity; no access-policy widening | Not run |
| Corrupt object | Digest mismatch rejected before consumption, using a rehearsal copy without changing the stored source | Not run |

The operator must choose the actual commands after naming the store and
identity. Then attach the accepted policy, source census, rights handoff,
rehearsal results and review to this register before claiming #1489 complete.
The full capture storage implementation remains in #1373, and the
byte-identical workbook reconstruction remains in #1380.

## Recheck the recorded bytes

From the repository root, verify the three output files:

```bash
(cd docs/kickoff/1373 && shasum -a 256 -c SHA256SUMS)
```

Against the pinned source revision, check the input file digests:

```bash
shasum -a 256 -c docs/kickoff/1373/source-SHA256SUMS
```

For each `sources` row in `inputs.json`, resolve its path at
`source_revision`, recompute the file length and SHA-256, and compare both
with the row. These checks establish record identity only. They do not
satisfy the storage or retrieval acceptance criteria.
