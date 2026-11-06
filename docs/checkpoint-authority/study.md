# Publish checkpoint authority protocol and R2 storage amendments

Assuming, unless corrected:

1. The adopted #862 specification, SHA-256
   `8ee755c1f9e5c29703af30bd08caffb6fad80c8a0990ee0acecebef09b02f541`,
   governs this prerequisite. The adoption orders P-862 before service packets
   A, B and C. This run answers P-862 as issue #1676 in Skills.
2. The working prototype is a released protocol, verifier and conformance
   corpus. A local test authority proves the interfaces. It cannot authorize
   production decisions, storage or downloads.
3. Native anchor and checkpoint identity v1 remain closed. We consume the
   current controller through an adapter and preserve every refusal required
   by its pinned implementation.
4. Service construction belongs to `wildcat-finance/fiat-checkpoints`.
   Production signer, independent journal, accounts and deployment evidence
   belong to #863. No unavailable private dependency will be retrieved or
   replaced to make a checkpoint eligible.
5. Exact pinned Python and stdlib `unittest` remain the repository toolchain.
   Public-key verification may invoke a pinned OpenSSL executable with fixed
   arguments. Schema agreement uses the installed `jsonschema` for evidence;
   a skip cannot satisfy the final conformance gate.

Worker identity: `fiat-1676-study-surveyor`. Directive state SHA-256:
`e20e209e9fcf46f6d2389315403a9b0f2923bb658753835ee46bc696ce4d09df`.
This unreceipted refresh adopts the published prerequisite repair in #1681.
The original study and its directive remain in the preserved preimage.
This document states a design and future checks. It does not receipt a phase.

## 1. Problem, user and working prototype

The service needs portable evidence that distinguishes a valid historical
checkpoint from a currently authorized, completely published checkpoint.
CP-3 supplies archive inspection and restore. It does not supply contributor
enrollment, service authorization, a complete authority journal, current
denial knowledge, or proof that both storage copies were read back.

The users are the service implementer, the independent signer implementer,
and an operator verifying a saved receipt after losing the service database.
They need one released definition of each decision and a verifier that
refuses incomplete evidence. Ariadne will check registered evidence
bindings; external signature verification supplies authenticity.

Completion requires all of the following:

| Id | Checkable result |
| --- | --- |
| P01 | Closed schemas and byte rules cover every record in section 4. Every field, union variant and limit has passing and rejecting vectors. |
| P02 | Exact-byte DSSE verification checks the P-256 prehash/DER profile, trusted key history, scope and canonical payload. Real cosign verification agrees on the released fixtures. |
| P03 | The native adapter derives the complete required commit set from a verified producer boundary and checks exact coverage and approved signers. Claimed archive lists alone cannot pass. |
| P04 | Replay proves an unbroken complete journal through a signed head, decision uniqueness, cancellation exclusion, publication completion and ordered denial/permit behavior. |
| P05 | Offline output states historical validity separately from current eligibility. Missing freshness produces unknown or unavailable, never a current acceptance claim. |
| P06 | Ariadne registers the new predicate with actual evidence gates and a complete result vocabulary. Unknown predicates and unchecked gates cannot become a pass. |
| P07 | ADR-070/071 and programme documents carry dated R2 and ownership amendments; their historical text stays preserved. |
| P08 | A release manifest binds the full source commit, protocol, schemas, verifier, fixture corpus and supported native pin. A consumer can verify every component without a mutable branch lookup. |

The final proving path is the new offline conformance command
`python3 plugins/hexaemeron/tests/checkpoint_authority_conformance.py --candidate ordered-replay --criterion released-interoperability --report .hexaemeron/reports/ordered-replay-released-interoperability.json`.
It will exercise a complete accepted history, database-free reconstruction,
all declared hostile cases, and independent signature checks under network
denial. This command is a deliverable, not a result already obtained.

## 2. Prior art and source-bound limits

### Native checkpoint lineage

The last two merged checkpoint pull requests were
[CP-3, #1652](https://github.com/wildcat-finance/skills/pull/1652) and
[CP-2, #1413](https://github.com/wildcat-finance/skills/pull/1413).
Their preserved API bodies and current carryover issues are hashed in
`.hexaemeron/study-evidence/external-evidence-inventory.json`. CP-3 merged
as `6982793334003dc0a441d6e90e753a143e3f2a6c`; CP-2 merged as
`0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`. Current source is newer.

The implementation is in the large `hexctl.py`, not a separate archive
module. At the adopted pin, `_checkpoint_archive_proof` at line 26175
copies the current boundary step's `push.verified_commits`, or the last
audit round's list for an unfinished boundary. It excludes integration
merges. `_checkpoint_inspect_signatures` at line 27285 verifies that claimed
list with carried public material. Neither proves that the list is the
complete historical set or that its keys belong to an approved contributor.
`_checkpoint_inspect_acceptance` at line 27432 bounds prior receipt entries
without parsing or authenticating them. These are inputs to additional
checks, not service authority.

Full restore and identity verification still matter. CP-2 removes one
immediate verified restore tail when reconstructing the producer prefix;
it refuses an earlier restore inside that prefix. Legacy or symbolic-base
identity can remain unavailable. The service must refuse those cases.
The run anchor's repository slug and restored origin are descriptive
bindings, not proof of an externally registered numeric repository identity.

The current controller also replays gate and custody receipts. A receipt
with `operation_ran:false` proves an interface check, not execution of the
named operation. Missing private evidence can therefore make a valid local
archive ineligible for this service. Verification must not fetch recorded
private paths, install dependencies, or run worker, replacement or guard
commands to repair admission.

### Audit boundary

The whole-set synopsis currency check ran at the adopted source pin and
exited zero. Its log is
`.hexaemeron/study-evidence/refresh-1681/audit-synopsis-check.log`.
The original inventory `.hexaemeron/study-evidence/audit-source-inventory.json`
preserves exact selected view records, source and view hashes, line numbers,
scope and exclusions. A view was read; this is not a claim to have read the
full underlying audit source. Missing legacy fields remain unknown.
The refresh's `source-refresh.json` proves all 20 selected source/view files
and all 60 archive/inspect function bodies are byte-identical to the
original pin. Shared gate-recovery dependencies changed; equality of those
function bodies does not prove equality of their transitive behavior.

| Authoritative source and view | Records read and use |
| --- | --- |
| `plugins/hexaemeron/audit/AUDIT.md`, sibling `AUDIT_SYNOPSIS.md` | Entire legacy view; inherited delivery and hook limits. |
| `plugins/ariadne/audit/AUDIT.md`, sibling `AUDIT_SYNOPSIS.md` | Entire view; parser, role, schema and evidence-gate limits. |
| `audit/AUDIT.md`, sibling `AUDIT_SYNOPSIS.md` | All 35 Ariadne records; other skills' records are outside this predicate change. |
| `audit/rounds/fiat-860-restore-identity-continuation-r2.md`, sibling `.synopsis.md` | Entire view; producer prefix, digest and one-restore limit. |
| `audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md`, sibling `.synopsis.md` | All Step 3 inspection, Step 4 restore and Step 5 demonstration records. Export construction and retired design rounds are outside this adapter change; their PR carryovers remain binding. |
| `audit/rounds/fiat-859-reinstate-the-wave-delta-distributed-checkpo.md`, sibling `.synopsis.md` | Steps 2, 5 and 7; ADR and programme ownership, preservation and handoff. |
| `audit/rounds/fiat-402-implement-the-grounded-agent-predicate.md`, sibling `.synopsis.md` | All Step 2 corpus records. Grounded-agent domain code and capture execution are not reused. |
| `audit/rounds/fiat-508-restudy-residual-carryover-confinement-and-g.md`, sibling `.synopsis.md` | Released Step 7 interface record; no worker or controller implementation claim. |
| `audit/rounds/fiat-1135-retire-mandatory-shoggoth-co-signature-and.md`, sibling `.synopsis.md` | Entire earlier signature-only retirement view, preserved as history. |
| `audit/rounds/fiat-1135-retire-the-shoggoth-cosignature-and-host-au.md`, sibling `.synopsis.md` | Step 1 rounds 1/2, Step 3 round 1 and Step 6 round 2; signature-gate findings and dispositions, structural checker boundary and final limits. |

The selected view strings retain every finding id/status, Covered, Not
checked, Elenchus verdict and Leads not pursued. This bounded read excludes
unmodified archive construction, unrelated controller/worker internals,
Berean capture and other predicates' domain algorithms. If implementation
crosses that boundary, the additional audit records must be read before
the scope changes. Earlier CP-3 recovery history preserved outside the
current view was not independently fetched; its public PR account is the
evidence used here.

The signature-only history also prevents a misleading shortcut: native
`git verify-commit` can accept a GitHub web-flow signature when its public
key is present. Its status alone does not classify a commit as governed
work. The adapter must derive the commit's role from verified boundary
evidence and apply its explicit approved key history. Historical attribution
and hosted structural checks do not replace that proof.

The following inherited limits remain visible in the capability report:

- #1647: a native signing-key diagnostic may disclose an archive-derived key
  identifier. The service supervisor must publish fixed private reason codes
  and retain raw diagnostics only inside its bounded private evidence.
- #1648: an opened destination descriptor pins an inode, while later native
  operations resolve its pathname. The service must own the destination's
  parent and exclude competing writers.
- #1649: native restore does not serialize all concurrent restores into a
  pre-existing empty directory. One observed interleaving is not an exclusion
  proof. The supervisor owes per-attempt exclusive scratch ownership.
- #1586: the earlier process-group test had a load-sensitive failure. This
  packet does not infer its cause or turn a timeout into a pass.
- #1524, #1130 and #1433 remain their existing design-amendment, Horos and
  diagnostic carryovers; this packet does not close them incidentally.
- CP-3 scans raw archive member bytes for its declared secret patterns. That
  does not scan decompressed Git objects. Its accepted pattern bounds,
  expected failure and OpenPGP demonstration do not prove a broader secret
  or SSH safety claim. Existing scratch symlinks and unexpected tracebacks
  remain supervisor containment concerns.

CP-3's historical count and refusal-text findings were resolved or qualified
in that run; their old open rows are not newly open defects. This study does
not repair the three open native restore issues. It therefore has no native
repair phase or claim that a new guard closed them. Future service packets
must build their own source-bound known-failure inventory for containment.

### Ariadne and external standards

The last two merged pull requests changing Ariadne code were
[#1639](https://github.com/wildcat-finance/skills/pull/1639), closing a
multi-`@` URL and duplicate-pair parser gap, and
[#1183](https://github.com/wildcat-finance/skills/pull/1183), migrating the
Aave v4 demonstration. #1639 carries #1640 and #1641; neither is repaired
here. Authority identifiers use closed ASCII forms and never depend on the
URL scrubber. Existing demonstration and schema-limit claims stay bounded.

The grounded-agent predicate supplies a useful registration precedent:
wire constants are copied deliberately, checkout tests detect drift, and
isolated Ariadne installs do not import another plugin at runtime. Its
corpus audit found filename-only coverage, empty-container minimality and
DSSE-wrapper gaps. New fixtures will bind exact ordered failure vectors,
one typed structural change and outer transport state. None of this lends
Ariadne an authenticity promise.

DSSE defines signing the exact payload and type through PAE. The study's
public DSSE v1.0.2 vector passed `cryptography` 43.0.3 and OpenSSL 3.6.3 with
SHA-256/P-256 and DER; hashing the digest again failed. The report is
`.hexaemeron/reports/crypto-probe.json`. The parent's pinned cosign 3.1.3
probe, read from `evidence/cosign-probe-fixed/results.json`, passed the valid
case and refused changed payload, wrong trusted key and double hashing
under network denial. Its initial arbitrary nonempty `keyid` failed;
changing that hint to the empty string passed. The published profile will
use empty DSSE key hints and authenticated policy key identities. SPKI and
OpenSSH fingerprints are separate representations. These study probes use generic
fixtures. Production-format fixtures remain unproved until the release gate.

## 3. Constraints, pins and non-goals

The immutable initial base is
`5bf2675d64468c7ce43ace67b0bcf1d50d38bd8e`. The adopted source and target
HEAD are now `1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74`, tree
`7714026b1c0f7c097d1694324c06c47bd39d5cd3`. The target is
`/Users/c0rtexzer0/Documents/ChatGPT/fiat-862/skills-delivery/tmp/fiat/fiat-1676-publish-checkpoint-authority-protocol-and-r`.
Python is 3.14.6, Fiat 6.61.1, Protasis 5.12.0 and Ariadne 3.3.0.
The controller runtime is
`/Users/c0rtexzer0/Documents/ChatGPT/fiat-862/skills-source-1681/plugins/hexaemeron`.
The recorded runtime update preserves the initial base and ledger history;
its evidence is under `.hexaemeron/study-evidence/controller-update-1681/`.
Study-only measurement packages are `cryptography` 43.0.3 and `jsonschema`
4.25.1. Product verification must declare executable and crypto-profile
pins in its release; the ambient path does not establish production authorization.

The cosign study binary is 3.1.3, darwin/arm64, SHA-256
`5cf948c2f4dfe59687bdd0b8523709067383e03982cc543475c8a7dc70e92a76`.
The native CP-3 release and this authority release receive separate pins.
New governed Fiat and Ariadne behavior earns their normal version updates
and generated runtime/marketplace propagation; no draft version is a
consumer release pin.

Non-goals are service HTTP/SQL/upload code, live R2 or KMS access, creating
accounts or credentials, a production signer, cloud deployment, physical
removal, controller fencing, public discovery, full graph/frontier choice,
fork resolution and DR drills. Those remain #863 through #867 and the
adopted service packets. Public discovery endpoints stay unavailable until
their separately versioned protocol exists. Native anchor and identity
schemas, their signature semantics and receipt replay rules are unchanged.

### Inherited baseline and prerequisite repairs

The untouched starting tree's selected baseline is red: 13 of 14 checks
passed; `hexaemeron-suite` failed. Evidence is
`.hexaemeron/baseline-checks.json`, `.hexaemeron/baseline-checks.log` and
the isolated `.hexaemeron/baseline-gate-reproduction.log`. Their hashes and
the exact scope are recorded in
`.hexaemeron/study-evidence/baseline-reference.json`. The isolated test
reproduces `unregistered-cli-module-bindings` for Brevitas without changing
the source. Ariadne's selected suite passed with 14 optional-schema skips;
those skips are not schema-agreement evidence for this protocol.
The original red report's embedded Hexaemeron output is truncated. Its
visible failure headers also name frontier, version-relation and
confined-replacement cases; this study did not independently localize every
downstream failure or claim that the two issues exhausted every cause.

The diagnosed inherited failure families were tracked by
[#1674, stale or unsupported CLI interfaces](https://github.com/wildcat-finance/skills/issues/1674)
and [#1673, four no-known inoculation recovery failures](https://github.com/wildcat-finance/skills/issues/1673).
The controller's preserved readback records
[#1671](https://github.com/wildcat-finance/skills/pull/1671) merged at
2026-09-15T22:50Z, commit
`1d113c8255a86176808393bacb87d0c6c9754e5a`; that fix covers Hypomnema
only. The subsequent prerequisite [PR #1681](https://github.com/wildcat-finance/skills/pull/1681)
merged at 2026-09-16T00:41:06Z as the adopted commit above; #1673 and #1674
closed one second later. Its anonymous readback verifies the merge signature
and is preserved in `repair-evidence/pr-1681-merged-readback.json` under
the programme directory. It refreshes reviewed CLI interface bindings and
admits only the exact sealed no-known recovery edge for `done inoculate`.
Other commands and mismatched evidence still refuse.

The final direct repair checks passed: the local root gate ran 1,996 tests;
Hexaemeron ran 3,345 tests with zero failures/errors, five skips and one
expected failure. The clean suppression check exited zero with its repository
analyser degraded. These reports do not turn either the original study
baseline or the earlier aggregate repair report green.

The fresh selected baseline completed with exit zero on the untouched
published `1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74` source:
`python3 scripts/run_checks.py --scope hexaemeron --scope ariadne --jobs 26 --report .elenchus/p862-baseline-after-1681.json`.
All 14 selected checks passed. Exact report, log and source binding are in
`.hexaemeron/study-evidence/baseline-after-1681/reference.json`; report
SHA-256 is `068a189a11c6919f534b563a44aab30a6320136f7ae5fdfbeba264f97b660b76`.

Fresh Hexaemeron execution started and completed all 3,345 tests exactly
once, with zero failures, errors, unexpected successes, blocked fixtures or
skips and one expected failure. The complete execution object precedes the
manifest in the outer `HEXAEMERON-RUN` record. The enclosing suite output is
truncated, so this is complete counter evidence without a claim to have
read every embedded test log. The earlier direct repair run's five skips
remain recorded against that separate execution.

Fresh Ariadne ran 890 tests with 14 optional-schema skips; root ran 1,996
with one snapshot-only check skipped. The suppression check exited zero
with 273 report-only findings, no suppressions and its repository analyser
degraded. These limits stay explicit. The new baseline establishes the
published source's selected checks; it does not satisfy the four future
protocol conformance gates or rewrite either historical red report.
Current evidence is under `.hexaemeron/study-evidence/final-1681/`; the
earlier `refresh-1681/` evidence remains unchanged.

Always verify the exact worktree, source and tool pins, preserve negative
evidence, and run the applicable checks before claiming a transition.
Ask first only for a change to the adopted provider or authority boundary,
cloud resource creation, spending, deployment, access changes or physical
removal; none is authorized by this protocol packet. Never access private
credentials for research, execute record-carried commands, widen native v1
schemas or turn a test authority into production trust.

## 4. Designs, evidence and selected construction

### Compared replay constructions

`eager-index` decodes every bounded journal body, retains those bodies, then
replays their order. It makes random inspection convenient but retains data
that replay no longer needs. `ordered-replay` decodes one body at a time,
checks its sequence and predecessor, and retains only the decision state
needed by later entries. It sacrifices random body access; a caller can
retain the original immutable journal separately.

Both research implementations used the same closed synthetic model, corpus,
decision index and hostile cases at the original study pin. Their exact
reports, criteria, values and selected design are preserved during the
runtime refresh; no new execution is claimed for those measurements.
The command was
`python3 .hexaemeron/study-evidence/design_probe.py --out .hexaemeron/reports`.
It exited zero. The model has 1,280 records and 512 decisions; corpus SHA-256
is `cf56704482a20f2d7d7d03d26c1eed8f54d9bf9d5d2d45bb64c18c1d3e8474ae`.

| Selection criterion | Eager index | Ordered replay |
| --- | ---: | ---: |
| Valid model and eight hostile histories handled as expected | true | true |
| JSON decodes, count | 1,280 | 1,280 |
| Peak traced Python allocation, bytes | 5,578,310 | 266,697 |
| Same complete projection | true | true |
| Old complete head stays historical, current eligibility false | true | true |

Both reject omission, duplication, reordering, a foreign environment, an
unknown field, a duplicate key, authorization after cancellation and a
permit after denial. Both produce projection digest
`3e51e417e044849260c320091812df58257cdf79ce112470e16eca2c3e2e54f8`.
Measured medians were 111.363541 ms and 111.5205 ms while other checks ran;
they support no speed claim. Decode count is the selection's time-work
measure. The memory measure is traced Python allocation, not process RSS.

The closed record `.hexaemeron/design-evidence.json` selects
`ordered-replay` by `unique-frontier`: equal measured decode work and lower
measured memory, with every selection gate passed. Ten digest-bound reports
hold the actual values. These are replay-model comparisons, not schema,
signature, storage, native compatibility or production security passes.

| Pending selected-candidate gate | Resolver report | Refuses before |
| --- | --- | --- |
| `records-and-signatures` | `reports/ordered-replay-records-and-signatures.json` | Step 3 |
| `native-boundary-coverage` | `reports/ordered-replay-native-boundary-coverage.json` | Step 4 |
| `authority-replay` | `reports/ordered-replay-authority-replay.json` | Step 5 |
| `released-interoperability` | `reports/ordered-replay-released-interoperability.json` | Integration |

Each resolver is exactly
`python3 plugins/hexaemeron/tests/checkpoint_authority_conformance.py --candidate ordered-replay --criterion <criterion-id> --report .hexaemeron/reports/ordered-replay-<criterion-id>.json`.
The JSON record spells out every full command. Step 1 creates this reporting
interface with unsupported criteria refusing. Step 2 supplies records and
signatures, Step 3 native boundary coverage, Step 4 replay and Ariadne gates,
and Step 5 the released corpus, documentation and independent demonstration.
This dependency order is the input to the runbook, not permission to report
future success.

Every future conformance report must bind its actual source and fixture
manifest, executed case ids, exit and output hashes. Empty selection,
skipped mandatory crypto/schema cases, stale report reuse and incomplete
execution refuse. A stub reporting interface cannot satisfy a conformance
criterion.

### Portable record and byte contract

The authority protocol is a new versioned family. Each tagged record has a
closed field set, exact scalar types, finite array/string limits and a
single explicit version. All authenticate environment, service, protocol
version and record type. Required variants are:

| Record | Binding it owns |
| --- | --- |
| Authority policy | Trust bootstrap, allowed protocol/tool profiles, storage identities, key-history rules and freshness policy. |
| Contributor enrollment, rotation and revocation | Numeric GitHub user, exact public-key encoding and fingerprint, proof of possession, issuer, scope, validity, sequence and predecessor. |
| Run grant | Numeric actor/repository, native run, allowed actions, validity and policy predecessor. |
| Service run registration | Exact native anchor digest, immutable initial base, source/controller identity, owner, allowed protocol and initial parent authorization. |
| Upload endorsement | Enrolled key, actor, run, candidate, nonce, expiry, all three checkpoint digests, carrier length and parent evidence digest. |
| Validation evidence | Exact attempt/lease/input, native pins/results, complete commit/signature coverage, authorization/parent checks, times, resource counts and trusted supervisor identity. |
| Storage copy claim | Logical location, exact hash key, operation result, full GET digest and length, configuration-policy digest, verification time and verifier identity; no provider URL. |
| Parent link | Ordered authenticated prior acceptance references, one immediate parent for continuation, native producer-prefix relation and source pins. |
| Acceptance | The adopted specification's complete acceptance inventory: three identities, semantic subject, actor/enrollment/endorsement/grant/key-history references, exact validated representation, parents, transition, policy, validation and both copy claims. |
| Cancellation | A decision that was never authorized, its scope and predecessor; mutually exclusive with authorization. |
| Publication finalization | Acceptance id, exact envelope digest, verified archive/receipt copies and authorization policy head. |
| Denial, revocation or poison | Typed snapshot/representation/run/key target, reason enum, effective order, predecessor and descendant policy. |
| Authorized-removal outcome | Exact removed digests, scope, prior signed denial and operator-authorized incident references; distinguishes authorized absence during replay without restoring eligibility. |
| Journal entry and signed head | Ordered event, prior commitment, count, tail commitment and trusted freshness binding. |
| Stream-admission permit | One exact representation and requesting scope, one-use nonce, expiry, finalization, head and order relative to denials. |

Canonical JSON is a named protocol encoding: UTF-8 of sorted object keys,
compact separators, ASCII escapes, exact integers and no floating point,
NaN, duplicate keys or trailing data. It is not advertised as RFC 8785.
Identifiers use defined ASCII grammars, timestamps one UTC form, digests
64 lowercase hexadecimal characters. Schema parity must reject Python's
boolean-as-integer ambiguity. Limits are protocol choices: 64 KiB per
control record, nesting depth 32, 128 bytes per opaque identifier, signed
63-bit positive sequence numbers, at most 64 prior receipt references,
and at most 65,536 journal entries or 256 MiB per verification invocation.
Exceeding a supported transport or replay budget is a named limit refusal.
A partial replay cannot produce a complete-head verdict.

Authority signatures use in-toto Statement v1 in DSSE with
`application/vnd.in-toto+json`. Verify the exact decoded payload bytes;
then require canonical encoding and closed statement/predicate content.
The producer emits standard padded base64. Verification accepts the standard
and URL-safe alphabets, with valid optional padding, while rejecting mixed
alphabets and malformed encodings. The application receives the same decoded
bytes that passed verification; it never reparses the envelope for them.
The signature is ECDSA P-256 over SHA-256 of DSSE PAE, represented as ASN.1
DER. A KMS adapter uses DIGEST mode; a message verifier applies SHA-256 once.
This follows the [DSSE byte contract](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md) and [KMS digest mode](https://docs.aws.amazon.com/kms/latest/APIReference/API_Sign.html).
The selected producer profile writes `keyid` as the empty string. Trust is
chosen from explicit public roots and authenticated policy key history,
never from that unauthenticated hint. Canonical SPKI fingerprints identify
authority keys; OpenPGP/SSH contributor fingerprints retain their own
explicit format tags. Rotation and revocation cannot silently reassign old
commit authorship or authorize an untrusted replacement root.

The acceptance id hashes a domain-separated canonical unsigned decision
payload. It contains no self hash. Exact envelope SHA-256 is a separate
external locator, allowing equivalent randomized signatures without two
logical decisions. The statement gives each digest an explicit role:
`snapshot_id` is semantic state, `controller_manifest_sha256` is native
controller evidence, and `outer_sha256` is one exact carrier. Substitution
between these roles refuses. Every record reference carries its expected
type and digest; cycles and self-reference refuse.

Enrollment challenges bind actor, key, service/environment and nonce, expire
after five minutes and require proof of possession in a supported native
key format plus signed operator approval. Run grants name only the declared
contributor permissions: `announce`, `upload`, `read_status`, `read_receipt`
and `download`. Administrative permissions are separate. Current grant and
key state are checked at each protected request and before signing or
exposing acceptance; an enrollment proof cannot endorse a later upload.

For each service/repository/run/snapshot, the first fully accepted
representation is canonical. A different ZIP must complete native restore
and prove equality of reconstructed semantic identity before
`equivalent_snapshot` can return the existing canonical archive and receipt
digests. The submitted alternate is explicitly unaccepted, creates no child
and receives no invented receipt. Conflicting semantics under one identity
are an integrity failure. Signer retries preserve exact envelope bytes and
decision timestamps; an equivalent randomized signature is one decision,
never a second acceptance.

### Native verification and complete commit coverage

The adapter accepts only a current-attempt result from the pinned native
sequence: inspect, restore into exclusive disposable scratch, verify with
observations, then reconstruct identity. Every exit must be zero and every
result/log digest must join that exact attempt and input. A stale success
file or untrusted worker `ok` cannot satisfy this sequence. Production
supervisor authentication is an external issuer contract, with test issuer
roots explicitly segregated.

The adapter parses `fiat-checkpoint-archive-restore/v1`, its nested
`fiat-controller-checkpoint-restore/v1` and literal top-level `verify: "ok"`.
Before using `restore.worktree`, it proves that the returned path is a fresh
private descendant of the allowed job root. It binds `outer_sha256`,
`snapshot_id`, `restore.manifest_sha256`, status digest and semantic next
directive to this attempt. The archive summary must report
`identity.status=bound`; the full reconstructed identity uses its actual
closed schema, without an invented status field.

The controller manifest digest uses the native implementation's original
canonical MANIFEST JSON plus LF, not a guessed state digest. A failed restore
cannot be rescued by a later successful verify. The sequence uses no live
GitHub filing-decision option. Before restore, the trusted supervisor seeds
only independently approved historical public keys into the isolated
per-job GPG keyring or SSH allowed-signers file, records their exact trust
digest and refuses missing keys. Inspection's own temporary keyring is not
assumed to survive. Structured stdout is bounded at 64 KiB; private stderr
at 16 KiB. Truncation or malformed output refuses.

After this boundary verifies, derive the required local governed-commit set
from its producer ledger, push/audit ranges and actual Git DAG. Do not
trust an embedded `verified_commits` array as the denominator. Check that
the native proof list equals its expected current-boundary subset, then
independently verify every remaining required historical governed commit
against the approved run key history. The authority adapter reports the
complete derived set and exact results under the native inspection pin.
Missing, duplicate, unexpected or unsupported coverage refuses. Initial
base objects and platform-only integration merges have explicit evidence
classes; they are never presented as locally signed governed commits.
If a required class has no supported verification path, admission refuses.
No author or trailer filter excludes a required commit, and the uploader
need not have authored every historical commit.

The capability manifest maps each of the 35 native hostile fixture ids and
24 native refusal names to its actual source stage. Authority-only failures
get their own vocabulary. It records every relevant coverage boolean and
the three open native containment obligations. It must not claim that all
native classes originate in inspection or that a syntax check executed a
historic guard. Missing private custody evidence is an unavailable result.

### Ordered authority, parent and publication rules

Replay verifies every entry from the trusted bootstrap through the signed
head's exact count and tail commitment. Hashes commit exact event envelope
bytes and their predecessor. The verifier rejects gaps, duplicate sequence
numbers, order changes, forks in the presented chain, foreign scope,
unrecognized variants and contradictory decisions. Head commitments cover
both policy/key history and the decision journal; omission from either is
incomplete. The decision index
outlives each decoded body. PostgreSQL, a newest timestamp and a cached
boolean are never authority.

Authorization and cancellation are exclusive. Authorization is durable:
lease expiry cannot erase it. A complete acceptance requires authenticated
validation and approved archive and prerequisite copies, its receipt
signature, receipt copies, an independently signed finalization and both exact finalization
copies. Finalization claims the prior copies only; it makes no recursive
claim about its own future replication. Incomplete copies remain pending
or unavailable during reconstruction.
Exposing acceptance also requires a current ordered eligibility response
after finalization. Signed historical copies alone cannot establish current
availability or the absence of later denial.

The minimal parent profile admits a registered root with signed permission,
or one immediate accepted parent with the same registered run, immutable
base and verified producer-prefix continuation. Every carried prior receipt
reference is bounded, ordered, digest-checked and authenticated; omission,
extra references, incompatible history and unsupported resolution evidence
refuse. Denial and required descendant poison are checked through the same
complete head. This does not choose a newest sibling or a canonical fork;
full frontier and resolution operations remain #865.

A download grant binds actor/session, run, environment, exact archive and
receipt digest, and a 60-second start expiry. The gateway verifies the whole
object into bounded trusted staging before requesting a one-use stream
permit from the external control service. Admission takes effect when that
service journals the permit against its current head. Effective denial
blocks every later permit. A permit already ordered before denial counts
as active admission even if its first byte has not yet been sent.

The consuming gateway contract requires cancellation push, a current-head
check at most every two seconds and before each 8 MiB sent, and cancellation
when channel freshness is lost for more than five seconds. These deployment
targets do not promise recall of delivered bytes. Interrupted clients need
a new grant; v1 has no range or resumable multipart download. Offline
verification can prove a past permit and head; it cannot prove that a nonce
is unused or that no newer denial exists.
Current eligibility requires an authenticated fresh head bound to the
caller challenge, trusted time and remembered head floor. Without that
external input, historical verification may succeed while
`current_eligibility` remains unknown.

Reconstruction applies signed authorized-removal outcomes after their prior
denials. Such an outcome explains authorized absence; it cannot make missing
bytes available or restore an acceptance's eligibility. Operator procedure,
lock changes, deletion and the incident drill remain #866. Missing outcomes
leave absence unexplained, and contradictory authority stops the affected
scope.

### Minimal private discovery and exact retrieval

The released contract names authenticated acceptance lookup, a private
accepted-record inventory, status and exact-object download grants. Lookup
binds run, snapshot, accepted representation and receipt digest under the
requester's current scope. Status returns eligible, denied or unavailable
with the policy-head identity. Inventory uses stable opaque pagination with
at most 100 items and 256 KiB per page; other control responses are at most
64 KiB. It does not select a frontier or rank progress.

Unknown and unauthorized resources have indistinguishable public responses.
No request accepts an arbitrary URL, filesystem path, bucket, signer key or
executable. Only the authenticated binary route releases staged verified
archive bytes, with `private, no-store`, a fixed binary MIME type and a
digest-derived filename. No provider redirect or permanent URL is returned.
Frontier, resolution and public discovery return `capability_not_enabled`
until their separate protocol is enabled. Protocol fixtures prove these
wire rules; service HTTP, authentication and streaming enforcement belong
to the service packets.

### Ariadne, packaging and R2 amendments

Ariadne's registered checkpoint predicate checks explicit subject roles,
evidence reference types/digests, closed result vocabulary and required
coverage. It does not execute native commands, contact stores or authenticate
signatures. Its report keeps those claims unchecked unless the separate
authority verifier established them. An isolated Ariadne installation uses
its own schema/constants with checkout parity tests against the protocol
owner; no cross-plugin runtime import is introduced.

The reusable authority verifier belongs under Fiat, in a separate module
and CLI from controller mutation. Its public API accepts bounded bytes,
explicit trust and declared native results. The CLI reads caller-selected
local files without following record-carried locators, invokes only pinned
fixed public-key verification commands, and emits a closed result.

Permanent storage claims use `sha256/<exact-object-sha256>`, conditional
creation, full read-back length/digest and indefinite R2 bucket locks.
Each permanent write uses one conditional destination PUT. Automatic
multipart authority publication remains disabled unless its final
conditional semantics have their own conformance proof. Matching metadata,
ETag or HEAD cannot replace full GET/hash verification. Copy observations
attest bytes at their recorded time, not continuing availability.
Primary and recovery logical locations map to separate Cloudflare accounts
in the EU. Shared-provider failure remains a risk; geographic independence
within the EU is not proved. R2 has no S3 version-id retention contract here.
Coarse write credentials are not described as a delete-deny IAM guarantee:
the effective lock supplies overwrite/delete protection, and runtime
credentials cannot change that lock. Upload and retrieval stay service
mediated, with no permanent provider URLs or presigned bypass.
[R2 lock semantics](https://developers.cloudflare.com/r2/buckets/bucket-locks/) and
[its S3 compatibility table](https://developers.cloudflare.com/r2/api/s3/api/)
support these provider distinctions; deployed configuration remains unproved.

Dated amendments to ADR-070, ADR-071 and the current programme study/runbook
replace only the conflicting provider, retention, permission and ownership
clauses. Ordinary revocation appends denial; emergency physical removal
requires the separately governed prefix/bucket lock-removal procedure, global
freeze, two operators and collateral inventory in #866. External signer
and complete control journal production implementation remain #863.

The release contains schemas, verifier, fixtures, capability manifest and
protocol documentation with component hashes. Its source commit is pinned
externally without a self-referential file hash. `protocol.lock.json`
examples require the consumer to recompute every digest and pin the native
and authority releases separately. No mutable `main` or `latest` is accepted
as a runtime compatibility decision.

## 5. Risk register

```risk-register
record-closure | untrusted JSON to typed records | duplicates unknown fields wrong scalar types oversized nesting and unsupported versions refuse
canonical-byte-confusion | payload bytes to identity and signature | exact payload survives verification and canonical domain hashes cannot substitute digest roles
dsse-prehash | PAE to P256 verification | published DER vectors pass independent verifiers and double hashing altered type or payload refuses
key-hint-trust | envelope hint to trusted key | empty emitted hint cannot enroll a key and SPKI SSH and OpenPGP identities remain distinct
key-history | enrollment rotation and revocation | issuer proof of possession sequence validity scope and compromise policy are verified
actor-run-confusion | upload endorsement to registered run | numeric actor repository grant anchor base nonce expiry and input digests agree
commit-denominator | native boundary to signature coverage | derive complete required set independently and refuse missing duplicate extra or unsupported claims
native-private-evidence | archive to controller replay | unavailable custody dependencies refuse without reading carried paths or executing historic commands
native-containment | native restore to host | capability limits retain issues 1647 1648 and 1649 and no protocol result claims their repair
prior-receipts | carried receipt bytes to parent authority | every bounded reference authenticates and continuation plus denial closure is complete
journal-completeness | supplied events to signed head | count predecessor sequence exact bytes and scope catch omission reordering forks and rollback
decision-exclusivity | authorization to cancellation | a decision cannot take both paths and lease expiry cannot erase an authorization
publication-cycle | acceptance to finalization and copies | finite acyclic evidence requires exact two-location readbacks without claiming future self copies
copy-claim-trust | publisher observation to authority | trusted verifier identity and exact length digest and logical location replace publisher booleans
denial-stream-order | current policy to stream permit | deny-before-admit and one-use ordering require live trusted state and offline limits remain explicit
freshness | historical head to current eligibility | challenge trusted time and remembered floor are required and stale missing heads cannot authorize
test-production-separation | fixture issuer to production trust | test roots and test evidence refuse under production policy without a fallback switch
ariadne-promise | predicate binding to authenticity | registered gates stay evidence checks and cannot authenticate signatures or read arbitrary locators
subprocess-files | local CLI inputs to verifier process | fixed pinned argv bounded output no shell no record-carried execution and symlink-safe bounded reads
resource-exhaustion | record stream to decision index | per-record aggregate count depth time memory and output limits produce explicit incomplete refusals
r2-governance | old storage clauses to released protocol | dated amendments preserve history and distinguish lock protection separate accounts and shared-provider limits
fixture-oracle | named hostile case to pass report | exact typed mutation transport and ordered failure vector are independently checked
release-drift | component bundle to consumer lock | full immutable pins and recomputed component hashes refuse stale schema verifier or corpus combinations
```

## 6. Glossary seeds

- **Semantic snapshot:** native `snapshot_id`, independent of a ZIP's layout.
- **Representation:** exact outer carrier digest and byte length.
- **Acceptance id:** domain hash of the unsigned canonical decision payload.
- **Envelope digest:** SHA-256 of exact signed envelope bytes, held externally.
- **Producer prefix:** verified controller history before the permitted restore tail.
- **Coverage denominator:** independently derived set of commits requiring proof.
- **Journal head:** signed count and commitment for one complete ordered history.
- **Finalization:** signed evidence that acceptance and prior copies were verified.
- **Freshness floor:** trusted remembered head below which rollback is refused.
- **Current eligibility:** a live authorization result requiring fresh denial state.
- **Copy observation:** authenticated read-back evidence at a stated time.
- **Test authority:** fixture public key that production policy must reject.

## 7. Sources and reproducibility

The controlling issue is [#1676](https://github.com/wildcat-finance/skills/issues/1676).
The adopted specification is bound by
[the #862 adoption](https://github.com/wildcat-finance/skills/issues/862#issuecomment-5688850333)
and the SHA-256 above. The exact local adopted bytes remain
`/Users/c0rtexzer0/Documents/ChatGPT/fiat-862/specification.md`.

Repository sources at the adopted commit:

- [Native controller](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/plugins/hexaemeron/skills/fiat/scripts/hexctl.py), functions and adopted line numbers in section 2.
- [Archive study](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/docs/fiat-checkpoint-archive-study.md) and [CP-3 audit view](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.synopsis.md).
- [ADR-070](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/docs/decisions/ADR-070-separate-the-checkpoint-protocol-from-its-authority-service.md) and [ADR-071](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/docs/decisions/ADR-071-hold-checkpoint-authority-in-locked-storage-behind-replaceable-compute.md).
- [Programme study](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/docs/wave-delta-checkpoint-programme-study.md) and [programme runbook](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/docs/wave-delta-checkpoint-programme-runbook.md).
- [Ariadne contract](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/plugins/ariadne/skills/ariadne/SKILL.md), [grounded-agent precedent](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/plugins/ariadne/scripts/ariadne_lib/predicates/grounded_agent.py) and [Ariadne audit view](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/plugins/ariadne/audit/AUDIT_SYNOPSIS.md).

External primary references are [DSSE v1.0.2](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md),
[in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md),
[KMS Sign](https://docs.aws.amazon.com/kms/latest/APIReference/API_Sign.html),
[R2 bucket locks](https://developers.cloudflare.com/r2/buckets/bucket-locks/),
[R2 S3 compatibility](https://developers.cloudflare.com/r2/api/s3/api/),
and [cosign 3.1.3](https://github.com/sigstore/cosign/releases/tag/v3.1.3).
The release must preserve exact fixture bytes and tool digests because these
documentation URLs can evolve.

Research artifacts are under `.hexaemeron/study-evidence/` and
`.hexaemeron/reports/`. They include the executable model, deterministic
corpus digest, ten design reports, raw comparison, public signature probe,
audit source inventory and external evidence inventory. The refresh directory
preserves new source checks, the original protected evidence hashes, repair
evidence and the adopted-specification crosswalk. The model schema
`p862-study-journal/v0` has no authority and is not the final wire schema.

## 8. Ephoros questions and signals

Apply [Ephoros](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/plugins/hexaemeron/skills/ephoros/SKILL.md).
The verifier is an offline command, but service operators will consume its
results. It needs four answers:

1. Which exact input and tool/policy pins produced this result? Steps 2 and 3
   emit a bounded result with attempt id and input, source and policy digests.
2. Which evidence is missing or refused? Steps 2 through 4 emit fixed stage,
   code and coverage fields, with historical validity and current eligibility
   separated. They do not return arbitrary child output.
3. Was the complete head replayed and publication complete? Step 4 emits
   count, commitment, head/finalization identity and completeness fields.
4. Did a budget prevent a decision? Steps 3 and 5 record measured bytes,
   duration and limit code. Partial work remains incomplete.

Correlation identifiers and digests belong in access-controlled result
records, not unbounded metric labels. This packet adds no background daemon,
alert channel or live telemetry system; those belong to the service.

## 9. Phylax boundaries and controls

Apply [Phylax](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/plugins/hexaemeron/skills/phylax/SKILL.md).
Untrusted boundaries are record bytes, envelope bytes, public-key material,
native archive/results, local file descriptors and subprocess output.
Closed parsing, explicit roots, exact-byte hashes, bounded reads, nofollow
regular-file admission, fixed argv and output caps cover those inputs.
No record can supply a command, executable, fetch URL or authority root.

The native subprocess adapter must use a caller-controlled isolated
environment: no ambient Git hooks, templates, prompts, helpers or credential
configuration. No private key, production token, cloud client or service
credential enters the offline verifier. The service supervisor must prove
its own sandbox and exclusive directory ownership later; a protocol fixture
does not prove a host boundary.

Trust crosses separately from evidence binding. Operator-approved roots
authorize policy; policy authorizes enrollment, grants and validation
issuers; current complete control history supplies denial state. Neither a
SQL row, an uploaded public key nor an Ariadne pass can replace those joins.

## 10. Metron budget and measurement

Apply [Metron](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/plugins/hexaemeron/skills/metron/SKILL.md).
The executed model comparison establishes memory and decode work only.
It does not establish production latency, archive validation time, total
RSS, filesystem overhead or provider cost.

The final protocol-only benchmark is part of the conformance reporter:
`python3 plugins/hexaemeron/tests/checkpoint_authority_conformance.py --candidate ordered-replay --criterion released-interoperability --report .hexaemeron/reports/ordered-replay-released-interoperability.json`.
It records hardware/runtime, exact corpus, repetitions, median/p95, peak
RSS, traced allocation and decoded-record count. The initial acceptance
budget is complete replay of the 1,280-record study workload with no
retained body collection, at most one JSON decode per record and under
512 MiB peak process RSS. That ceiling is a chosen limit to test, not a
measured current result. Native archive work keeps the lower of native and
service caps and the adopted service benchmark obligation. Network latency
and storage throughput remain deployment measurements in #863.

## 11. Elenchus posture and guards

Apply [Elenchus](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/plugins/hexaemeron/skills/elenchus/SKILL.md).
Malformed or contradictory evidence refuses. Missing pins, trust, complete
history, native private dependencies, supported coverage or freshness
prevents the dependent authority claim. Refusal does not silently downgrade
a schema, waive a signature, run uploaded instructions or choose a fork.
Historical inspection can return bounded facts while eligibility remains
unknown; it cannot issue an acceptance or stream permit.

Every implementation failure keeps its original bytes and result, is
reproduced at the named boundary, and earns a guard asserting the violated
property. Guards use exact fixture ids, typed one-change mutations and
ordered failure vectors. A test count, filename, caught generic exception
or vacuous false value is not a coverage oracle. Crash/replay tests prove
that no partial report is mistaken for a current successful attempt.

The three native carryovers remain open and unmodified. This run may test
that the capability report and consuming contract preserve their limits;
that is not a parent-red proof repairing native restore. Product changes
that repair an inherited failure must first amend scope and add the
source-bound known-failure inventory and required guard phase.

## 12. Hypomnema decisions and homes

Apply [Hypomnema](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/plugins/hexaemeron/skills/hypomnema/SKILL.md).
The expensive decisions are the record identity/DSSE profile, ordered replay
with explicit freshness limits, exact native coverage, and separation of
Ariadne binding from authority. Their draft is prepared under
`.hexaemeron/authority-protocol-decision.md`; its intended repository home is
`docs/decisions/drafts/verify-checkpoint-authority-by-ordered-replay.md`.
The exact draft was materialized at that home after baseline execution
finished. It remains uncommitted for the parent's governed Step 1. The design
bridge checker requires this existing record before study receipt.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | ordered-replay
record | docs/decisions/drafts/verify-checkpoint-authority-by-ordered-replay.md
```

Step 1 commits the study, runbook, decision and dated amendments. The
eventual public protocol reference lives under
`plugins/hexaemeron/skills/fiat/references/checkpoint-authority.md`;
schemas and verifier remain beside Fiat, and Ariadne's predicate, schema and
conformance inventory stay in its plugin. A release inventory names each
file and hash. ADR allocation is checked against current main at integration;
the draft path avoids guessing a numbered ADR now.

The runbook must preserve the four pending design gates and assign source,
schema, tests, documentation and generated-copy checks to each step. It
must not copy future shell commands into a success report. Changes to byte
identity, trust, coverage, parent semantics or a limit require the applicable
study and runbook transitions before implementation.

After `done study`, the receipted design record is immutable. An ordinary
study or runbook amendment cannot replace its candidates, criteria or
selection. Pending evidence is supplied at the record's named report paths
without rewriting that record. If the candidate, criterion set or selection
must change, halt and start a new run; the current Fiat contract has no
design-amendment transition. This follows the
[Fiat design-lock contract](https://github.com/wildcat-finance/skills/blob/1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74/plugins/hexaemeron/skills/fiat/SKILL.md#phase-notes).
