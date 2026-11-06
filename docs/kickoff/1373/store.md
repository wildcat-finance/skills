# Durable store inputs for #1373 and #1380

Status: awaiting the capture/store handoff from
[#1731](https://github.com/wildcat-finance/skills/issues/1731) for the Wildcat
V1 and V2 Ethereum mainnet estate. This cross-target register prepares
[#1489](https://github.com/wildcat-finance/skills/issues/1489). Approved store
location and operating policy, capture declarations and retrieval results
remain pending. The Creator has directed internal use for the initial
Miskatonic material; merging this register does not complete #1489.

## Provenance

Observed on 2026-09-19 at 17:30:41 UTC against Skills revision
[`e2307ed5966e18727434b3e49bec89db736f7b17`](https://github.com/wildcat-finance/skills/tree/e2307ed5966e18727434b3e49bec89db736f7b17).
Producer: Codex, task `01a0bab4-76ef-71d3-923c-ea6001aa55bc`.
Review: producer self-review; independent reviewer is unassigned. The
Creator supplied the initial Miskatonic audience decision recorded below.
Retention, migration, storage account and spending decisions remain pending.

[`inputs.json`](inputs.json) preserves the source paths, file byte counts,
SHA-256 values, pinned links, recorded Dokimasia identities and unresolved
fields. [`source-SHA256SUMS`](source-SHA256SUMS) lists the input file digests;
[`SHA256SUMS`](SHA256SUMS) binds this document, that JSON file and the input list.
The inspection covers the cited Skills files and the linked issue records;
it does not establish that missing inputs are absent elsewhere.

## Capture/store handoff

The Creator clarified on 2026-09-19 in this task that #1731 is handling
the Wildcat V1/V2 capture/store input. The selected targets are
`wildcat-v1-ethereum-mainnet` and `wildcat-v2-ethereum-mainnet`, already
recorded in [`../1374/capture.md`](../1374/capture.md) and
[`../1374/capture.json`](../1374/capture.json). Their pinned source digests
are included in `inputs.json`.

The current #1731 scope authorises one bounded interval per estate and
refuses a completeness claim. Its open step PRs
[#1747](https://github.com/wildcat-finance/skills/pull/1747) and
[#1753](https://github.com/wildcat-finance/skills/pull/1753) preserve the
design and registry-dispatch work. Their exact heads are recorded in
`inputs.json`; neither PR is a delivered capture or approved storage policy.

Consume #1731's handoff when it supplies the manifest and component digests,
byte/component census, capture revision, interval/coverage limits and
verification results for both estates. Attach the store namespace, retrieval
identity, operator decisions and permissions for the files being stored before
the retrieval rehearsal. These inputs are pending from their owning work; this
register does not ask the maintainer to produce a second capture.

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

The selected Wildcat targets have no accepted manifest or byte/component
census linked here yet. Their bounded captures under #1731 do not establish
a size above 8 GiB; #1373 needs the delivered census before making that
claim. The historical 343-component case remains separately unidentified.
A smaller demonstration or a different local capture cannot supply its identity.

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

## Where decisions and test results go

Record both the storage decisions and the retrieval test results here, with
file identities and unresolved fields in `inputs.json`. The decision-maker
can supply choices in the task or a linked decision record; the producer
writes them into this register. There is no separate approval form.

The storage operator chooses the location, permitted readers, retention,
credential ownership and spending limit. The capture producer supplies the
files and their manifest. The delivery agent runs the retrieval tests and
records the commands, results and file digests. The reviewer checks that the
results meet the issue's acceptance criteria. A decision to store a file is
separate from evidence that the storage works.

Here, an input is a file or dataset the named job uses: a Wildcat capture for
Alexandria, application code and a testing spreadsheet for Dokimasia, or an
audit report for Anamnesis. A Fiat runbook is the delivery plan; it is not the
Dokimasia workbook, which is an Excel file of reviewed application test cases.
An Anamnesis corpus is a collection of audit sources.

## Initial Miskatonic use decision

On 2026-09-19 in this task, the Creator directed internal use for the initial
Miskatonic material: selected contract source, chain data captured through
RPC such as the #1731 Wildcat captures, internal query schemas and the
relationships derived across venues. These files and results stay internal;
no external sharing or public release is authorised by this decision.

This records the intended use and audience. The storage account, named reader
accounts, retention, credential ownership and budget are still to be named.
The decision does not identify the Dokimasia workbook's permissions or admit
future third-party integrations such as Plaid.

## Decisions still required

| Decision | Owner | Current evidence |
| --- | --- | --- |
| Capture manifest, source revision and complete byte/component census | #1731 capture producer and storage operator | Wildcat V1/V2 selected; manifests and census pending from #1731 |
| Store provider, account/bucket or immutable namespace, object keys and retrieval identity | Storage operator through the #1731 handoff | Pending policy and decision reference |
| Retention period, deletion conditions and retention owner | Storage operator | Undecided |
| Permitted readers, access owner and access policy | Source custodian and storage operator | Initial Miskatonic material stays internal by Creator decision; named reader accounts and access owner are pending; workbook permissions remain separate |
| Credential rotation owner, interval and revocation procedure | Storage operator | Undecided; no credentials belong in this record |
| Retain or migrate existing split parts | Storage operator | Parts inventory and migration decision missing |
| Authorised cost and capacity, including local staging | Named human decision-maker | No budget or capacity authorised |
| Reviewer acceptance | Reviewer | Unassigned |

## Source permissions

A source permission record answers who may keep, read or share a particular
file, and identifies the licence, permission or other declared basis for that
use. It records a decision and its reference; it does not certify legal
sufficiency. A file's presence on a public website does not by itself answer
these questions.

Alexandria records each component's `access` as `public`, `restricted` or
`private`, and `redistribution` as `permitted`, `restricted`, `prohibited` or
`unknown`. Its release validator checks these declarations. It does not
require an Anamnesis rights record or establish whether the declaration is
correct. The delivered #1731 manifests must supply the declarations for the
Wildcat capture components and reflect the internal audience decision above.
That decision is not a declaration of a third party's licence terms.

The Dokimasia workbook has a separate source and permission decision. Its
committed study says that the raw workbook bytes are not republished. Keeping
it internally and publishing it are different uses; record the authorised
use and readers before moving its primary bytes.

#1489 names [#1364](https://github.com/wildcat-finance/skills/issues/1364) as a
prerequisite. That issue targets the Anamnesis audit corpus selected in #1351.
It requires a declared `rights_basis`, a `disclosure` class and an intended
audience for each source in that corpus. No inspected record establishes that
those sources are the Wildcat V1/V2 captures or the Dokimasia workbook.
The dependency is retained, with its applicability unresolved. Its existence
alone supplies no permission for these different inputs.

If a file here is also a source governed by #1364, consume its actual
source-matched decision and digest. The initial chain-capture scope does not
establish that match, so this register requests no generic Anamnesis sign-off
for it. The issue owner must resolve the dependency's scope before claiming
#1489 complete.

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

After the #1731 handoff names the store and identity, the delivery agent
chooses and runs the commands within the authorised policy. Attach that
policy, source census, applicable source permissions, rehearsal results and
review here before claiming #1489 complete.
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
