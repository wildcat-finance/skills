# #862 replacement specification: R2 checkpoint authority service

Date: 15 September 2026

Target: `wildcat-finance/fiat-checkpoints`  
Programme tracking issue: `wildcat-finance/skills#862`, CP-4 of #859  
Status: proposed replacement implementation contract; no infrastructure is provisioned by this document.

## 1. Mandate, assumptions and meaning of completion

#862 SHALL implement the R2 service described here. Historical S3 implementation directions in its original filing are superseded by this proposal once the replacement is adopted. The original filing remains historical evidence. This document does not claim to amend an accepted ADR by itself.

Assumptions used to close the design, unless the maintainer corrects them:

1. R2 remains the chosen store. Primary and recovery buckets are in separate Cloudflare accounts, both restricted to the EU jurisdiction. This is account separation, not provider diversity or a guarantee of different physical regions.
2. The initial compute profile is Linux on DigitalOcean in London, with a PostgreSQL database. Specific host/account/project identifiers are deployment inputs, never inferred from an existing login. The service is portable to another Linux host.
3. Contributor identity comes from a dedicated GitHub App's user authorization flow. A GitHub login alone grants no run access. Signed operator records establish contributor keys and permissions for an exact repository and run.
4. The production signing profile is a policy-enforcing service outside Cloudflare using an AWS KMS asymmetric signing key. KMS holds the private key; the API and validator never receive it or generic KMS signing permission. CP-5 provisions that service.
5. #862 owns all application code for upload, validation, publication, replication, signer invocation, receipts, authenticated reads, denial enforcement and index reconstruction. CP-5 owns deployment and production proof of those interfaces. #865 owns selection between competing descendants and fork resolution.
6. New portable schemas and amendments land in Skills through a separately governed prerequisite packet. #862 changes no file in Skills. Creating the service repository layout does not authorize consuming a draft schema as a released protocol.
7. This is an implementation specification, not a Fiat study receipt, design-lock result, audit closure, deployment approval or evidence that any future acceptance test has passed.

The useful outcome is: an authorized contributor uploads one bounded checkpoint; the service inspects the exact bytes using a pinned Skills release; it stores and verifies primary and recovery copies; an independent signer approves a precisely bound acceptance; the exact signed receipt is stored and verified in both accounts; another authorized client can retrieve the checkpoint by identity. Killing processes, retrying requests or rebuilding PostgreSQL cannot change the accepted decision.

The end-to-end demonstration is `./scripts/demo.sh --scenario end-to-end --profile local`. It must exercise the real HTTP API, PostgreSQL migrations, the actual pinned inspector, the production publication algorithm and a cryptographically verifying test signer. Local stores and keys are explicitly test substitutes. Production mode refuses those substitutes.

## 2. Source baseline and precedence

The supplied constraint note is the scope input. The live issue was read on 15 September: open, title `fiat-wish: build the checkpoint intake, validation, and publication state machine`, last body update 12 September. Its current review chooses R2 and states that the signer remains outside Cloudflare.

Service baseline: `61b8dc4be1587d1c6ef46f2f228833214965e7f1`, public repository, containing only `README.md` and `docs/deployment-substrate.md`. The substrate already chooses three buckets, conditional publication, second-account replication and a derived database. It also contains claims about direct grants and runtime deletion permissions that this specification tightens.

Source order for implementation:

1. The adopted replacement contract and its explicitly accepted ADR amendments.
2. A digest-pinned, released Skills protocol bundle satisfying the prerequisite in section 4.
3. The service's accepted design records and deployment profile.
4. Historical issue text and the August S3 plan, used only to account for prior requirements.

An unresolved conflict between levels 1 through 3 blocks the affected work. A service-side compatibility workaround cannot settle a protocol conflict.

The archived S3 proposal's 64 MiB compressed, 256 MiB expanded and 512 MiB base limits SHALL NOT be copied into this implementation. CP-3's current contract and measurements govern. Full source evidence and the required refresh are recorded in section 23.

## 3. Scope and responsibility split

| Capability | #862 implementation | Other owner / boundary |
|---|---|---|
| R2 client, conditional immutable publication, GET-and-hash verification | Complete production adapter and failure tests | #863 supplies real buckets and credentials and proves policies |
| Second-account copy and retry worker | Complete implementation; no native replication assumption | #863 provisions recovery account and tests real separation |
| Canonical receipt construction, signer client, signature verification, read-back | Complete implementation against the released protocol | Skills owns schemas; #863 owns production signer and key |
| Contributor login and per-run authorization | Complete implementation and hostile tests | #863 configures a dedicated login App and initial operator authority |
| Contributor key registration and run grant enforcement | Consume and verify signed records; registration workflow | Skills owns record semantics; operator approves grants |
| Candidate state, quarantined uploads, inspection | Complete implementation | CP-3 supplies pinned inspector and fixtures |
| Exact-identity status, receipt and download APIs | Complete implementation | #864/#867 consume them later |
| Revocation/poison denial and durable record ingestion | Complete verifier, deny checks, propagation and rebuild | Skills defines records; #863 supplies privileged issuance; #866 drills incidents |
| Private accepted-record listing | Bounded inventory only; no selected frontier | #865 supplies lineage index and signed resolution APIs |
| Public discovery | No public checkpoint metadata in v1 | Skills defines allowlist; #865 implements projection; #867 integrates Atlas |
| Database reconstruction and policy replay | Complete code and synthetic failure demonstration | #866 owns operational disaster-recovery exercises |
| Infrastructure, cloud accounts, DNS, paid resources, production launch | Configuration contract and conformance tools only | #863, with exact deployment authority |
| External-run publication fence and controller changes | None | #864 in Skills |

#862 cannot be closed by implementing only intake and leaving replication and signing calls as TODOs. It can close with the complete service demonstrated locally, production adapters implemented and their live proof explicitly assigned to #863. It cannot claim production `accepted` operation before #863 passes.

The service starts in `intake_closed` production mode. P-862 must supply the initial denial/ancestry verifier before activation. #865 gates only the later full graph/frontier/resolution capabilities; it is not a prerequisite for this initial profile, avoiding a programme dependency cycle. No absence of lineage support is interpreted as permission to download.

## 4. Prerequisite packet and required document changes

### 4.1 P-862: publish the authority protocol in Skills

Create a separately governed Skills packet, linked as a prerequisite to #862's protocol-consuming steps. `P-862` is a planning identifier, not an invented GitHub issue number. It must land before production receipt or grant semantics are implemented against a supposedly final release.

Deliverables:

- Closed schemas for acceptance, publication finalization, authority-journal checkpoints, stream-admission permits, validation-result references, revocation, key enrollment/rotation/revocation, service run registration bound to native run anchors, immutable authority policy and storage-location claims.
- Minimal private discovery and exact-object retrieval contract; separately versioned public discovery and fork-resolution schemas may remain in #865, with endpoints unavailable until released.
- Precise canonical serialization, domain-separated signature input, algorithm identifiers, integer/string bounds, duplicate-key and unknown-field rejection, timestamp rules and verifier code.
- The binding between outer ZIP digest, controller manifest digest and semantic `snapshot_id`, including the exact subject a client uses as checkpoint meaning.
- Rules for `acceptance/prior/<n>.json`, including ordering, signature trust anchors, version allowlist, duplicate handling and the evidence that permits each parent transition.
- Contributor-key enrollment, a signed upload endorsement and attribution rules. An embedded public key is not an external identity anchor. The endorsement binds actor, candidate, service/environment, run and all three digests to this submission.
- External parent-link records and a verifier result that reports verified parent acceptance IDs and ancestry/denial coverage. Native v1 semantic identity remains unchanged; graph/frontier/resolution behavior remains with #865.
- Golden fixtures and hostile fixtures for each schema, algorithm and trust transition, including offline verification and explicit limits of offline revocation knowledge.
- A machine-readable capability manifest assigning each refusal to inspector or service, with no claim that the inspector raises classes it does not implement.
- A verifier/report contract deriving the exact required receipted-commit SHA set from the verified producer boundary. Inspector signature results must cover that set exactly, without omissions, duplicates or extra claims. The archive's own claimed list cannot define the whole required coverage.
- Amend ADR-071 and the programme runbook to the R2 semantics and ownership table below. Link this spec and #863/#865's exact handoffs.

The service SHALL pin repository, full commit, protocol version, artifact SHA-256, inspector executable/image digest, schema-set digest, verifier digest and fixture-corpus digest in `protocol.lock.json`. Pin the CP-3 archive release separately from the subsequent authority-protocol release if they are not the same commit. Fetching a release by mutable branch or accepting `latest` at runtime is forbidden.

This document's field inventory is the required meaning of that packet, not authority to ship a service-only wire format. Any schema correction after the pin requires a protocol release and explicit service compatibility update.

### 4.2 Specific amendments, not silent contradictions

| Current requirement or ambiguity | Replacement decision | Record that must carry it |
|---|---|---|
| Retention on an S3 object version; bucket versioning | Exact hash-addressed R2 key; conditional PUT; indefinite lock; full-byte verification; no version IDs | Skills ADR-071 and service substrate |
| Separate account and region | Separate Cloudflare accounts, EU jurisdiction on both; physical region separation unproven; provider-wide failure shared | Skills ADR-071 and service deployment record |
| Runtime has no delete permission | Runtime cannot effectively delete/overwrite locked authority bytes or change locks; coarse R2 write permissions are not falsely described as a PUT-only IAM role | Skills ADR-071 and service permission matrix |
| One exact poisoned version removed by breaking a lock | Global freeze and controlled removal and restoration of prefix/bucket lock rules; revoke first; collateral exposure measured and recorded | Service incident design; #866 drill |
| Presigned PUT/temporary credentials ensure bounded correct upload | Service-issued upload capability to a streaming gateway; no contributor R2 credentials or direct URLs | Service substrate and API contract |
| Presigned GET remains safe after revocation | Service-issued, identity-bound download capability; streaming gateway checks current denial state | Service substrate and API contract |
| #862 vs #863 signer/replica code ownership | #862 owns adapters and orchestration; #863 provisions external policy signer and live substrate | Programme runbook and both issues |
| Inspector signature proves contributor identity | Inspector verifies claimed receipted Git-commit signatures; service verifies signed upload endorsement and approved receipted-commit key history separately | Skills authority protocol and service auth ADR |
| Last blocker #861 alone | Archive prerequisite satisfied when verified; P-862 protocol/document reconciliation remains a distinct gate | Current review block for #862 |

No edits to these records occur as part of delivering this local specification. When adopted, add a dated current replacement block and retain historical filing bytes. Preserve `Fiat-Required: 1` and update carryover/dependencies explicitly.

## 5. Selected construction and alternatives

The selected v1 is a Python service, PostgreSQL transactional index/outbox, a streaming HTTPS gateway, disposable Linux validation sandboxes, R2 primary/recovery storage and an external policy signer.

| Candidate | Correctness and compatibility | Time / resource trade | Recovery |
|---|---|---|---|
| Direct R2 upload and presigned downloads | Does not by itself enforce the complete byte-bound grant contract or immediate request-time revocation | Lowest gateway bandwidth | Requires accepting weaker grant/revocation semantics |
| Service-mediated transfers, isolated validator, R2 | Chosen: service controls exact length/hash, permissions and denial checks; preserves CP-3 | Additional gateway I/O and host bandwidth costs; stream to bounded disk | Explicit verified copies; database reconstructible |
| Return to S3 authority | Supports the previous provider-specific model | Reopens the maintainer's R2 decision and its cost model | Provider machinery differs; not selected for #862 |

These are reasoned design choices, not measured performance wins. The future Fiat study must produce the current Protasis design-evidence record and conformance reports; this specification supplies no invented scores or successful test results.

### Reference deployment profile

- Linux Ubuntu 24.04 LTS, Python 3.12, FastAPI/ASGI API, psycopg 3 and PostgreSQL 16. Exact supported patches, wheels, system packages and container digests are committed with hashes at scaffold time; floating production installs are prohibited.
- API and transfer gateway on replaceable DigitalOcean Linux compute in `lon1`; PostgreSQL 16 managed database in the same operational region, private connectivity and TLS. This is a proposed deployment profile, not a claim those resources exist.
- Validator worker on a separate Linux host or security boundary, using a pinned gVisor `runsc` sandbox. No Docker socket, host service credentials or ordinary API process share its sandbox.
- DNS-only, direct TLS transfer hostname, or a proxy whose tested body limit exceeds the configured upload ceiling. Do not put the measured 100,790,501-byte CP-3 example behind a default 100 MB proxy limit.
- R2 buckets created with EU jurisdiction; use the corresponding endpoint. Account and bucket identity mapping is deployment-private.
- AWS KMS `SIGN_VERIFY`, `ECC_NIST_P256`, `ECDSA_SHA_256`, in `eu-west-2`, behind the CP-5 policy signer. It signs the digest of the protocol's domain-separated canonical payload. Sign and offline verification must agree on digest-vs-message mode and DER encoding. No KMS encryption feature is required for the R2 store.
- Local profile uses PostgreSQL and fault-injectable stores plus test keys. Test trust roots have a different environment identifier and cannot validate in production.

Cloudflare documents bucket locks and editable rules, and excludes S3 versioning and replication APIs. These support the R2 choice but do not prove deployed IAM or bucket configuration: [locks](https://developers.cloudflare.com/r2/buckets/bucket-locks/), [S3 compatibility](https://developers.cloudflare.com/r2/api/s3/api/). The AWS signature profile is documented by [KMS Sign](https://docs.aws.amazon.com/kms/latest/APIReference/API_Sign.html).

## 6. Components, data flow and credential boundaries

```text
contributor -> login/API -> upload gateway -> quarantine
                                  |
                         credentialed staging broker
                                  |
                         immutable local staged file
                                  v
                      credential-free inspector sandbox
                                  |
                         verified bounded result
                                  v
                      publisher -> locked authority
                                  |
                     replication worker -> locked recovery
                                  |
                     external policy signer -> signed receipt
                                  |
                   receipt stored and verified in both accounts
                                  v
                  derived accepted index -> download gateway
```

| Component | Allowed authority | Prohibited authority |
|---|---|---|
| Login/API | User login exchange, session/grant records, enqueue commands | Authority write, signing, lock administration |
| Upload gateway | Bounded quarantine write and staged-file creation | Authority/recovery access, signer access |
| Staging broker | Read one quarantined object; provide immutable local input | Run archive code, give credentials to sandbox |
| Inspector sandbox | Read mounted input and pinned toolchain; bounded scratch; bounded result | Network, secrets, other jobs, host sockets, storage or signer API |
| Publisher | Read verified staging; conditional authority write/read | Lock/token administration; issue acceptance without signer evidence |
| Replication worker | Read approved primary objects; conditional recovery write/read | Recovery account administration, lock changes |
| Signer client | Submit one canonical decision request | Generic signing permission or access to private key |
| CP-5 policy signer | Verify evidence/policy and sign permitted typed records | Modify checkpoint bytes, manufacture validation success, alter R2 locks |
| Download gateway | Read approved exact objects and current denial projection | Writes, signature issuance, public object URLs |
| Quarantine sweeper | Delete expired temporary keys only | Authority/recovery buckets |
| Break-glass operator | Explicit temporary administrative session under two-person procedure | Routine unattended service use |

R2 object-write tokens are not assumed to exclude delete. Provider-enforced indefinite locks must reject deletion/overwriting on all authority/recovery keys. The runtime has no credential capable of altering those rules. This is a deliberate replacement for the old stronger capability-grant wording. CP-5 must test actual token behavior. If a PUT-only broker is added later, it is a separate trust boundary and must not be advertised as provider IAM equivalence.

## 7. Identities and normative record content

### Three checkpoint identities

| Identity | Meaning | Comparison |
|---|---|---|
| `archive_sha256` | SHA-256 of every byte of the uploaded ZIP | Transport integrity and R2 key `sha256/<hex>` |
| `controller_manifest_sha256` | Exact controller manifest digest defined by CP-3 | Binding to the inspected controller checkpoint, using the protocol's own computation |
| `snapshot_id` | Semantic state identity defined by CP-2/CP-3 | Checkpoint meaning and duplicate state detection |

Never reimplement the semantic or controller-manifest digest from a guessed JSON canonicalization. Use the pinned implementation and golden vectors. Repacking may change the archive digest without changing the snapshot; this creates an alternate representation, not a new progress event.

Service-private IDs (`candidate_id`, upload attempt ID, lease ID and row IDs) are opaque random values, never protocol identities. SHA-256 values are exactly 64 lowercase hexadecimal characters. Unknown schema fields, duplicate JSON keys, invalid UTF-8, oversized values and unsupported versions refuse.

### Required authority records

The P-862 schema release must cover the following meaning. Field names below are proposed field names until that release locks them.

**Acceptance payload:** environment/service identity; repository numeric identity and display slug; issue reference; run ID; immutable initial base; all three checkpoint identities; exact carrier length; accepted representation; protocol/inspector/fixture/policy digests; actor numeric identity; upload-endorsement digest, enrolled contributor key and enrollment-record digest; approved receipted-commit signing history references; run-grant digest; validation-result digest; verified parent acceptance IDs; typed transition evidence; primary/recovery logical storage IDs and exact key/length/digest; verified-copy evidence digests; decision time; signer policy identity. Its stable acceptance ID is derived externally from the unsigned canonical payload; the payload does not contain its own hash. The semantic subject is explicitly `snapshot_id`; neither manifest digest nor ZIP digest is silently substituted. No caller-supplied or v1-absent stage is invented.

**Statement and signature envelope:** use in-toto Statement v1 inside the standard DSSE envelope, as ADR-070 requires. P-862 defines and registers the checkpoint predicate and its evidence gates; do not borrow a dataset predicate or declare an unknown predicate fully checked. Subjects and predicate bind all three digests with explicit roles, and identify `snapshot_id` as the semantic checkpoint subject.

DSSE carries `payloadType`, base64 payload and signatures with key hints. The signed bytes are DSSE PAE over the payload type and the exact serialized statement bytes. The KMS adapter signs SHA-256 of those PAE bytes with the stated digest mode; verification uses the same prehash/DER profile. Environment, service, protocol version and record type are authenticated inside the statement. Key hints only select candidate trusted keys; trust comes from successful verification and the authorized key policy. Preserve the exact verified payload; never reserialize it before signature verification.

Use pinned cosign-compatible signing/verification tooling outside Ariadne and cross-check fixtures with its verifier. Ariadne validates evidence bindings and registered predicate gates; it neither signs nor authenticates a signature. Envelope SHA-256 is an external locator over exact bytes and is not included inside itself. [DSSE protocol](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md), [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md).

**Revocation:** target semantic snapshot or exact accepted representation as explicitly typed; affected run; reason code; descendant-poison policy; effective sequence/time; previous policy-head reference; issuer and signatures. Revocation is an additional record, never an edit to an acceptance.

**Key and grant records:** numeric GitHub user ID; fingerprint of canonical public key bytes; key format/algorithm; proof-of-possession challenge digest; run/repository scope; permissions; validity interval; issuer; sequence; predecessor; enrollment/rotation/revocation signatures. A key update does not retroactively change the signer of old archives.

**Service run registration:** references the exact existing native `fiat-run-anchor/v1` digest, immutable initial base and source/controller identity; adds permitted protocol versions, run ownership, initial parent evidence and service authorization policy in a separate record. It never redefines the closed native anchor schema. Only an operator-authorized signed registration can introduce a run. A contributor cannot claim someone else's run ID merely by uploading an internally consistent archive.

**Validation result:** candidate and all identities, pinned input/artifact digests, inspector structured result and refusal classification, service authorization/ancestry checks, exact input length, start/end time, resource measurements, attempt/lease identity and output digest. A JSON `ok` field from an untrusted worker is not sufficient provenance.

**Policy/key transitions and authority journal:** ordered, signed, predecessor-bound control records with an increasing sequence number and environment scope. The independent signer/control service durably journals every authorized decision with its semantic identity, payload digest and exact envelope digest, plus cancellations, finalizations, grants, keys and denials. Its signed current head commits record count and a cryptographic journal commitment. A trusted freshness checkpoint outside PostgreSQL binds that head and denies omission/rollback during rebuild. A timestamp or newest database row cannot supply it.

**Publication finalization:** a separately signed journal record binding acceptance ID, exact receipt-envelope digest, verified archive/receipt copies and authorization policy head. It states that those copies were verified; it makes no claim about its own future replication. Its bytes are also stored and verified in both R2 accounts. The journal must support authenticated one-use stream-admission permits ordered with denial events. These requirements belong in P-862 and the CP-5 signer/control interface.

Raw private observations, archive contents, access credentials and permanent provider URLs are excluded from these records. Private storage IDs resolve through protected deployment configuration; public responses never disclose that mapping.

### Duplicate semantic state

The acceptance identity is derived from the canonical unsigned decision payload according to the protocol, independent of signature randomness. The service serializes publication for a `(service, repository, run, snapshot_id)` decision and never issues two contradictory accepted representations.

The first fully accepted representation is canonical. A later different ZIP with the same semantic identity runs the complete section 10 pipeline, including successful restore and equality of the reconstructed canonical semantic identity. It returns `equivalent_snapshot` with the existing canonical archive and receipt digests only when equivalence is proved, and explicitly reports the submitted alternate ZIP as unaccepted. It is not a new accepted child, and no receipt is fabricated for it. Conflicting semantics under the same identity are an integrity incident.

Same-payload signature envelopes may differ if the signing algorithm is nondeterministic. The signer interface must retain/replay the exact envelope for a decision idempotency key. If a duplicate valid envelope nevertheless exists, reconstruction treats it as an equivalent signature of one decision, not a second acceptance; conflicting payloads for one decision ID fail closed.

## 8. Authentication, key enrollment and run authorization

Use a dedicated GitHub App for contributor login, separate from the repository-publication App. Its user authorization flow uses state, fixed redirect allowlists and current GitHub-recommended protections. Exchange the callback server-side, call authenticated `GET /user`, and use the returned immutable numeric user ID. Never trust a caller's login string, email, pasted PAT or App installation token as the contributor identity. See [GitHub App user authorization](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app).

Browser sessions use Secure, HttpOnly, SameSite cookies and CSRF protection; CLI pairing issues a 15-minute opaque service access token following completed user login. Initial registration/login state expires after 5 minutes, is single-use and cannot authorize a different browser session. Access-token renewal requires an unrevoked login session and current run grants. Logout revokes service sessions; identity-provider tokens are discarded after identity establishment unless an explicitly encrypted renewal design is required.

For each protected request, authenticate the actor, validate the service token audience/environment/expiry, and load the current signed authorization projection. Repository identity uses the GitHub numeric repository ID, verified against an operator allowlist. Renames cannot create a new scope or transfer authority.

Enrollment requires all of:

1. Authenticated GitHub numeric identity.
2. A service challenge binding actor, requested key fingerprint, service/environment, nonce and five-minute expiry.
3. Proof of possession verified using the key format/algorithm permitted by the pinned archive contract.
4. Operator approval expressed as a signed enrollment/run-grant record.

The outer ZIP has no native authenticated transport signature. P-862 therefore defines a separate upload endorsement signed by the enrolled contributor key: actor ID, candidate ID, service/environment, repository/run identity, the three checkpoint digests, carrier length, requested parent-link digest, nonce and expiry. A candidate returned by announce includes the challenge to sign; content transfer and completion require the verified endorsement. A key enrollment proof alone cannot endorse an arbitrary later ZIP.

The inspector verifies signatures on claimed receipted Git commits. The service checks every such required signer against the run's approved signing-key history and the authority policy, separately from verifying the current upload endorsement. An archive's embedded key can demonstrate a matching commit signature but cannot enroll itself. Historical commits need not all belong to the current uploader; authorize the appropriate historical actors/keys rather than rewriting CP-3's signature semantics.

No ambient organization membership grants contribution rights. Initial pilot is allowlisted per run, with permissions `announce`, `upload`, `read_status`, `read_receipt`, `download`. Administrative registration, revocation and resolution are separate permissions. Permission removal is effective at each new request and before acceptance/signing.

The policy signer independently checks the current signed grant and key state. Possession of a publisher credential alone is insufficient to obtain an acceptance signature. The API cannot send arbitrary bytes to KMS for signing.

## 9. Upload grants, quotas and immutable staging

### Limits

The initial service outer-archive/carrier ceiling is **1 GiB (1,073,741,824 bytes)**, subject to any stricter pinned CP-3 limit. It intentionally accommodates the reported 100,790,501-byte measurement. The pinned carrier accepts stored ZIP members (method 0), not ZIP compression. “Expanded bytes” below is CP-3's extracted-member budget, not permission to accept compressed ZIP entries. This is a transport admission ceiling, not permission to relax any member or extracted-size limit.

| Resource | Initial service limit | Enforcement |
|---|---|---|
| Announce/complete request JSON | 64 KiB | Gateway bytes then strict parser |
| Archive carrier bytes | 1 GiB, or lower protocol cap | Declared Content-Length, streaming counter, actual staged-file length |
| ZIP entries | 4,200, or lower protocol cap | Inspector preflight and extraction checks |
| Expanded bytes | 1,300 MiB, or lower protocol cap | Inspector measured totals and sandbox scratch limit |
| Git bundle entry | 1 GiB, or lower protocol cap | Inspector member policy |
| Any other archive entry | 64 MiB, or lower protocol cap | Inspector member policy |
| Outstanding candidates | 5 per actor; 20 per run; 100 global | Transactional reservations, including active uploads |
| Outstanding reserved bytes | 5 GiB per actor; 20 GiB per run; 100 GiB global | Reserve declared size before grant |
| Concurrent transfer streams | 2 per actor, 8 global initially | Admission semaphore plus DB reservation |
| Upload capability | 15-minute start expiry | Service clock and token record |
| Upload duration | 30-minute absolute; 60-second idle | Gateway termination |
| Pre-signing candidate lifetime | 24 hours from announce | Conditional cancellation vs signer authorization; then logical expiry |
| Quarantine bytes | Cleanup after candidate completion/expiry, with 24-hour lifecycle age | Signed publication retries use verified authority bytes, not expiring quarantine |
| Completed metadata/validation retention | Bounded by documented privacy policy | Store only necessary private audit metadata |

Values are initial ceilings and targets. CP-3 caps are authoritative; configuration may lower them but cannot increase them beyond the pin. A supported archive exceeding the service transport cap gets an explicit refusal, never a misleading malformed-protocol diagnosis. Cap changes require measured deployment evidence and policy versioning.

### Transfer protocol

Announce reserves size and quota, returns candidate ID and an endorsement challenge. After the actor submits a valid signed endorsement to `POST /v1/candidates/{id}/endorsement`, the service returns an opaque, actor-bound upload capability. The capability is conveyed in an Authorization header to a fixed same-origin route; logs never contain it. It names one candidate/attempt, exact declared size and archive SHA-256, endorsement digest, environment and expiry. It grants no read/list/delete operation or provider credentials.

The gateway requires an exact Content-Length, no Content-Encoding and no ambiguous request framing. It handles early disconnect, extra bytes and proxy smuggling defensively. It streams through a byte counter and SHA-256 calculation to an exclusive, no-follow temporary file on a quota-limited filesystem. It never buffers the whole archive in RAM. Unknown-length bodies are refused in v1.

Only after exact EOF length and digest match does the trusted gateway conditionally publish to a unique quarantine attempt key. This can use bounded multipart staging for the maximum object; incomplete multipart uploads are aborted and swept. The committed final object is subsequently read back, counted and hashed. Provider metadata and ETag do not stand in for full-byte validation.

The upload capability is single-use for committing an attempt. While one stream owns the attempt lease, another returns conflict. A failed/incomplete stream cannot resume arbitrary ranges; the client asks for a new attempt under the same candidate after the prior lease expires. Already completed identical attempts return the same completion result. The uploader never gets overwrite access to a sealed attempt.

The staging broker reads the completed quarantine object by the recorded key and digest into an immutable job file. Inspection and later publication use the same descriptor-bound bytes or a fresh independently verified copy. A mutable quarantine object cannot be swapped between inspection and publication. Confirmed pre-signing candidate expiry blocks new work even if R2 lifecycle cleanup has not physically removed bytes. Signer-authorized publication survives that deadline and resumes from already verified locked authority bytes under section 11, without relying on quarantine retention.

The current substrate's direct grants are explicitly replaced. Cloudflare documents reusable presigned URLs; temporary credentials do not by themselves establish every service-required size/checksum condition. [Presigned URLs](https://developers.cloudflare.com/r2/api/s3/presigned-urls/), [temporary credentials](https://developers.cloudflare.com/r2/api/s3/temporary-credentials/).

## 10. Validation: exactly what is proved

At the inspected CP-3 baseline, `checkpoint inspect` alone is insufficient for service admission. Its semantic-identity helper checks the carried identity digest/summary; its prior-acceptance helper counts prior receipts without validating their contents. Embedded signature consistency does not establish an enrolled contributor. Its output does not expose every field the service needs. The service SHALL NOT describe an inspector exit of zero as complete authorization, lineage or acceptance verification.

Validation runs in this order:

1. Verify sealed staged input length and outer SHA-256 against the announced request and staging evidence.
2. Run the pinned `checkpoint inspect` against that exact archive/digest. Preserve exact stable refusal codes through a bounded mapping; unexpected exceptions become a service error, never raw traceback output.
3. Restore into a new empty, private sandbox destination using the pinned restore operation. Run controller verification and recompute checkpoint identity using the pinned controller implementation. Compare the reconstructed identity to both the carried identity and the announced identity.
4. Extract and verify the exact controller-manifest digest according to the released contract. Read only the allowlisted structured result produced by the trusted adapter, not a caller-supplied summary or arbitrary output path.
5. Verify the upload endorsement against signed enrollment records, actor identity and current run grant. Derive the exact required receipted-commit SHA set using P-862's pinned verifier/report; require exact coverage by inspector signature results and verify all required signers against the permitted run key history. Refuse omitted/duplicated/extra signature claims. Preserve CP-3's historical Git-signature semantics without assigning all commits to the uploader.
6. Verify run anchor, immutable base, controller/protocol pin, allowed transition/boundary, receipt prefix and observation rules. Use pinned rules; never execute repository tests, hooks, dependency installs, builds or user-authored scripts to decide admission.
7. Verify every prior acceptance and external parent link with the newly released authority verifier, trusted key history and current denial head. Reject unknown/revoked parents, wrong run/base, contradictory archive references or unsupported parent semantics.
8. Apply service redaction policy to information the archive inspector does not cover, including a bounded walk of decompressed Git objects if the service claims that coverage. Raw ZIP-member scanning alone does not inspect compressed Git object contents. No scanner proves absence of secrets.
9. Emit a bounded structured validation result, including coverage booleans and exact protocol/tool/policy digests. The trusted supervisor authenticates the job/result binding and signs or attests it to the independent signer under the released evidence contract.

Native v1 `snapshot_id` does not contain service parent fields. The current exporter emits an empty prior-acceptance list. P-862 therefore supplies an external signed parent-link/receipt contract without modifying v1 identity semantics. #865 later owns graph indexing, frontier selection and fork-resolution decisions. Until that contract is released, the service cannot silently accept arbitrary parent lists; test roots may use the released root-anchor profile only.

The exact pinned validation command sequence is:

```sh
python3 /opt/skills/plugins/hexaemeron/skills/fiat/scripts/hexctl.py checkpoint inspect --archive /input/checkpoint.zip --sha256 "$outer" --scratch /job/inspect
python3 /opt/skills/plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir /job/restored-origin checkpoint restore --archive /input/checkpoint.zip --sha256 "$outer"
python3 /opt/skills/plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir "$validated_worktree" verify --observations
python3 /opt/skills/plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir "$validated_worktree" checkpoint identity
```

These show fixed argv, not shell execution requirements; the implementation invokes argv arrays without a shell. Require current-attempt zero exit from every command. Parse restore output as `fiat-checkpoint-archive-restore/v1`, nested `fiat-controller-checkpoint-restore/v1`, with top-level `verify` equal to the literal string `ok`. Validate returned `restore.worktree` is a fresh private descendant of the allowed job root before using it. Bind returned `outer_sha256`, `snapshot_id`, `restore.manifest_sha256`, status digest and semantic next directive to the attempt. Restore already compares controller verification/status/next and remints identity; the additional calls provide explicit independently consumed admission evidence.

The controller-manifest digest is SHA-256 of the original capsule's exact canonical MANIFEST JSON plus LF, as defined by the pinned implementation. It is not the hash of checkpoint state JSON or concatenated capsule bytes. A failed restore can leave valid-looking local state; later `verify` success must never rescue that failed attempt. No stale output or partial restore is accepted. Do not use a live-GitHub filing-decision option inside the network-denied sandbox.

### Sandbox contract

- Pinned Linux/gVisor runtime; rootless workload; read-only toolchain and input mounts; dedicated private writable job root; no writable parent shared with another job.
- No network namespace connectivity, DNS, host sockets, cloud metadata, credentials, SSH agent, GPG agent or inherited cloud/Git environment.
- Construct an explicit environment allowlist. Set isolated HOME/XDG/Git configuration, disable interactive prompts, hooks and external helpers, and preserve only protocol-required controlled Git operations. No shell command built from archive fields.
- Before restore, seed only independently approved historical public verification keys into a per-job ephemeral GPG keyring and/or controlled SSH allowed-signers file required by the pinned verifier. No private keys/agents enter the sandbox. Inspector destroys its own temporary keyring, so later restore/verification must not rely on that keyring surviving. Record the exact injected public-trust digest and reject missing required keys.
- Require the archive summary's `identity.status=bound`, plus successful full reconstructed identity output under its actual pinned schema. Do not invent a `status` field in the full identity result. Symbolic-base/legacy `unavailable` archives are transportable locally but are not eligible for distributed service acceptance. Do not infer support for unlimited repeat restorations: the pin allows one immediate verified restore tail and refuses a prefix containing an earlier restore. Broader proven portability needs a separate Skills release; #862 preserves the current refusal and never bypasses it.
- Whole-job limits: 2 vCPUs, 4 GiB memory including swap disabled, 8 GiB scratch, 256 processes, 100,000 created filesystem nodes, 300 CPU seconds and 900 seconds wall time. Descriptor, output, path and recursion limits are explicit. The supervisor kills the entire process group/sandbox, not only the parent process.
- Structured stdout is at most 64 KiB; captured stderr is at most 16 KiB and remains private. Truncation or malformed output refuses. No raw diagnostic string returns to contributors.
- The sandbox has no authority-write or signer credential. The trusted broker retrieves prerequisites first. Restore may not fetch missing Git objects or packages from the network.
- Destroy job files after result capture and policy retention; preserve only minimized failure metadata. A filesystem-node/memory/disk limit refusal is classified as a resource failure, not proof the archive is malicious.

Current restore diagnostic leakage, destination-name races and concurrent local restore concerns require wrapper containment tests. A unique private job root and no untrusted sibling processes reduce those service exposure paths; this does not close the underlying Skills findings. If a fixture can still escape or violate identity under this profile, admission stops until the prerequisite is fixed upstream.

## 11. Durable model, concurrency and state transitions

PostgreSQL is a transactional index and work coordinator. It is never the source of accepted truth. Use migrations, foreign keys, explicit unique constraints and state/version compare-and-swap. Store timestamps as UTC, lengths/sequences as bounded integers, and hashes in exact constrained fields.

Required tables include actors, sessions, grants, run registrations, candidates, upload attempts, validation attempts, publication intents, object copies, authority records, accepted representations, denial projections, audit events, outbox jobs and rebuild checkpoints. Future graph/resolution tables belong to #865. Private session/upload state is disposable; losing it can expire a candidate, not manufacture acceptance.

Uniqueness includes `(actor_id, API operation, idempotency_key)`, `(candidate_id, attempt_number)`, `(service_id, repository_id, run_id, snapshot_id)` for the accepted decision, `(store_id, object_key)` and immutable `(record_type, record_id)`. Do not make the archive digest globally unique across unrelated authorized scopes and accidentally leak private cross-run deduplication.

The idempotency key is a 16 to 128 character opaque ASCII token. Its request fingerprint binds the endpoint, actor, scope and all canonical body fields, including size/digests/parents. A matching replay returns the existing operation; a different fingerprint returns 409 with a fixed code and no information about other actors. Candidate mappings survive the candidate's 24-hour life plus seven days. Acceptance decision mappings are rebuilt from signed records and do not expire.

Workers claim jobs with expiring leases and strictly increasing fencing numbers. Every completion checks the current state version and fencing number. An expired worker may leave a content-addressed orphan but cannot advance the candidate, sign a newer decision or overwrite an object. Retry jobs use exponential backoff with jitter, capped at five minutes; dependency outages retain the same candidate and recorded subphase until expiry or operator intervention.

```text
announced -> uploading -> quarantined -> validating
                                      -> publishing -> awaiting_replica
                                      -> awaiting_signature -> publishing_receipt
                                      -> finalizing -> publishing_finalization -> accepted

before durable signer authorization -> rejected | expired
after durable signer authorization  -> complete publication | signed denial
accepted -> revoked        (derived from a separate signed denial record)
```

The diagram abbreviates sequential publication: after validating, the candidate proceeds through publishing, awaiting_replica, awaiting_signature, publishing_receipt, finalizing and publishing_finalization. It never skips a phase because a database field says a downstream object exists. Dependency failure preserves the current phase plus a fixed retry reason. A signer outage is not rejection of the contributor's work.

The 24-hour candidate expiry applies only until the signer durably authorizes the decision. After authorization, publication is durable unfinished work: it must reconcile to complete publication or a signed denial and cannot receive a temporary expiry/rejection. Resolve an ambiguous signing call by its external idempotency/journal entry before expiring local state. Cancellation and authorization are mutually exclusive conditional journal operations; expiry cannot race a still-valid signing request and then be reversed by reconstruction.

| Transition | Required evidence | Durable action / retry behavior |
|---|---|---|
| announce -> uploading | Current run grant, quota reservation, exact size/digest | Attempt lease and opaque capability; duplicate returns existing candidate |
| uploading -> quarantined | EOF count/hash match and sealed quarantine read-back | Commit exact attempt pointer; release transfer reservation |
| quarantined -> validating | Unexpired candidate and available isolated worker | Fenced validation lease; same input on retry |
| validating -> publishing | Complete protocol, reconstruction, identity, auth and denial checks | Persist immutable decision intent; no acceptance yet |
| publishing -> awaiting_replica | Primary exact key/full-byte hash verified under correct lock policy | Record primary copy evidence |
| awaiting_replica -> awaiting_signature | Recovery exact key/full-byte hash verified under correct lock policy | Record recovery copy evidence |
| awaiting_signature -> publishing_receipt | External signer checks complete evidence and current policy, returns valid envelope | Persist exact envelope/intent before publication |
| publishing_receipt -> finalizing | Exact envelope in both stores; full reads/signature checks and referenced copies verified | Submit typed finalization to external control service |
| finalizing -> publishing_finalization | Ordered journal finalization, current grant/denial check, verified evidence | Persist exact signed finalization response and retry by journal identity |
| publishing_finalization -> accepted | Finalization fully read/verified in both accounts and complete accepted predicate | Project durable acceptance and release reservation |
| pre-authorization -> rejected | Deterministic protocol/policy refusal, no signer authorization | Bounded private rejection record; cleanup temporary state |
| pre-authorization -> expired | Deadline elapsed and external intent cancellation wins against authorization | Abort leases, deny grants, sweep quarantine; keep locked orphans unreachable |
| accepted -> revoked | Valid signed record and poison policy | Update deny projection, cancel active transfers and prevent new admission |

Linearize policy changes and decision authorization at the independent policy signer's ordered control head. The signer and service recheck grants/revocations before issuing or exposing acceptance. A later revocation may deny a historically valid acceptance; it does not rewrite its signature. Contradictory control histories quarantine the run and stop acceptance/downloads.

## 12. Conditional publication, replication and signing

### Object store protocol

All permanent objects use `sha256/<sha256-of-exact-object-bytes>` within their configured authority bucket. Archives and signed records can share the hash namespace: record type comes from verified content, never from mutable metadata alone. Raw run anchors/base material follow the pinned archive protocol; do not invent a new 512 MiB base-bundle contract from the August plan.

Configure an indefinite whole-bucket lock on both authority buckets before the first write. No lifecycle deletion or administrative credential is available to the runtime. CP-5 proves and monitors the effective configuration.

For every archive, signed record and prerequisite object:

1. Calculate exact byte length and SHA-256 locally over the already verified bytes.
2. Issue one destination `PutObject` with `If-None-Match: *`. Disable automatic multipart upload in the authority adapter unless its exact final conditional semantics have a separate conformance proof. The 1 GiB v1 cap fits a single streaming PUT.
3. On success, conflict or ambiguous timeout, GET the exact key, count bytes and recompute SHA-256. Missing means retry; matching means idempotent success; any mismatch means storage-integrity failure and stop.
4. Write the recovery copy through GET plus conditional destination PUT. Do not assume an S3 CopyObject source condition protects the destination from overwrite.
5. GET and hash the recovery copy independently. Store copy evidence including logical account/bucket identity, operation result, length/hash, configuration-policy digest and verification time.

Matching metadata, ETag, successful job status, provider redundancy or a HEAD response do not clear `awaiting_replica`. Different account IDs are mandatory; region independence is not claimed. Both copies depend on Cloudflare, an accepted limitation of this R2 profile.

An exact-key collision with different bytes is never repaired by deleting/replacing the occupied key. Freeze the affected store/run, preserve evidence and investigate. A locked object written before later signing failure is an orphan, not accepted data; reconstruction ignores it unless a complete valid authority decision refers to it.

### Signer boundary owned by CP-5, client owned by #862

The external policy signer exposes a typed, authenticated interface, not a raw signing oracle. Request parameters include decision idempotency key, canonical payload digest, validation evidence, independently checkable primary/recovery copy claims, current run/key grants and expected control-head sequence. Response contains the exact signed envelope and its digest, or a bounded typed refusal/retry.

The signer checks record type/schema, environment, pinned protocol/policy, trusted validation issuer, decision uniqueness, current authorization, verified storage evidence and key/denial freshness. It independently verifies object-copy claims through read-only storage access or a separately trusted read-back verifier. It cannot trust a publisher's boolean `replicated=true`.

The signer persists the exact response and decision-authorized journal entry for an idempotency key before acknowledging it. The service verifies the returned envelope with the pinned public key, compares every payload field to its own intent, and stores the exact response bytes. Neither service nor signer may change decision timestamps/fields on a retry. Finalization, denial and cancellation use the same ordered durable journal. CP-5 must implement journal backup/replay and fresh-head evidence; a stateless KMS wrapper is insufficient.

The service then conditionally publishes and fully reads back the exact envelope in both accounts. It requests finalization from the independent control service, which verifies evidence and current denial state and journals the exact signed finalization record. The service publishes and verifies that record in both accounts before exposing `accepted`. No further record signs its own replication. Signer unavailability has no local-key fallback. Production refuses test roots, unsigned receipts and generic cloud SDK mocks.

### Acceptance predicate and self-reference

`accepted` means all of the following are established:

- The decision payload is valid under the pinned protocol and trusted signer policy.
- Its validation, actor/key/run binding and three checkpoint identities match.
- The exact archive and required prerequisites are fully verified in primary and recovery.
- The exact signed acceptance envelope is fully verified in primary and recovery.
- A valid publication finalization is present in the externally committed authority journal, and its exact signed bytes are verified in primary and recovery.
- No effective revocation, poisoned ancestor or contradictory policy applies, and current control-head freshness is established.

A receipt does not include its own digest or claim to have observed its own future replication. The payload describes archive-copy evidence; finalization describes verified archive/receipt publication; the service/rebuild predicate separately establishes publication of finalization bytes. This finite sequence has no self-reference. Signed receipt bytes prove an authorized decision; the finalization proves its publication decision. Neither alone proves current availability or absence of later revocation.

There is no database-only final commit flag that changes authority. If a process dies after both envelope copies land, reconciliation queries the committed journal and completes finalization and its copies. If it dies after finalization copies land but before SQL commits, reconstruction projects the complete accepted predicate. A missing copy remains explicit incomplete/unavailable work, including after a historical finalization; it never vanishes from history because SQL was lost. An authorized but unfinished signer response must never be handed to a client as an accepted result.

## 13. API and client behavior

All routes use TLS, strict schema/version negotiation, bounded bodies and responses, fixed refusal codes and request correlation IDs. Unknown resources and unauthorized resources have indistinguishable public responses. No endpoint accepts an arbitrary URL, filesystem path, bucket, signer key or executable from a caller.

| Method / route | Request | Response and authorization |
|---|---|---|
| `POST /v1/candidates` | Run reference, three identities/summary, carrier length, typed parent-link references, idempotency header | 201/200 candidate and endorsement challenge; contributor grant required |
| `POST /v1/candidates/{id}/endorsement` | Signed exact-submission endorsement | 200 upload capability after signature/scope checks |
| `POST /v1/candidates/{id}/upload-attempts` | Retry of expired failed attempt, idempotency header | One new leased capability or existing completed result |
| `PUT /v1/candidates/{id}/content` | Exact binary body, length and opaque service capability | 202 when sealed/quarantined; 4xx on integrity/permission refusal |
| `POST /v1/candidates/{id}/complete` | Exact observed length/digest and attempt ID | 202/200 existing state; never trusts declaration without gateway evidence |
| `GET /v1/candidates/{id}` | None | Owner/operator-only bounded state, stable code, retry-after, accepted reference if eligible |
| `GET /v1/runs/{run}/snapshots/{snapshot}/acceptance` | None | Authenticated signed receipt after full accepted predicate; typed unavailable/denied otherwise |
| `GET /v1/runs/{run}/accepted` | Opaque page cursor, limit <=100 | Private record inventory, stable pagination; no `furthest` or selected frontier |
| `POST /v1/runs/{run}/snapshots/{snapshot}/download-grants` | Accepted representation/receipt digest | Identity-bound, exact-object capability; fresh denial check |
| `GET /v1/downloads/{grant_id}` | Access token plus opaque grant secret in header | Authenticated binary stream; no redirect/provider URL |
| `GET /v1/runs/{run}/snapshots/{snapshot}/status` | None | Current eligible/denied/unavailable state with policy-head identity and bounded reason |
| `POST /internal/v1/authority-records` | Already signed, typed enrollment/grant/key/revocation records | Privileged ingestion only, verify before replay; never accepts arbitrary signer assertions |
| `GET /health/live` | None | Process liveness only, minimal public response |
| `GET /health/ready` | None | Ready/unready, no internal secrets; detailed diagnostics operator-only |

Frontier/resolution/public-discovery routes return `501 capability_not_enabled` if requested before their owning packet is enabled. Generic HTTP authentication/authorization semantics still apply. Do not return an empty frontier as if no work exists.

Responses include `request_id`, `candidate_id` where authorized, `state`, `code` and bounded `retry_after_seconds` where appropriate. No human diagnostic is used for program logic. Control responses are <=64 KiB; a paginated inventory is <=256 KiB. No permanent R2 URL, credential-bearing URL, bucket account ID, archive contents, observations or raw tool output is included in JSON.

The authenticated binary download is the explicit exception to “no archive contents in API responses.” A service that literally prohibited bytes in every response could not implement retrieval. Only this permission-gated streaming endpoint emits archive bytes.

Clients retain their local checkpoint until acceptance verifies. They compare all three identities, environment, run, protocol and signer trust. They obtain current denial status immediately before resuming. Offline signature verification proves historical acceptance only; #864/#867 must not turn an offline signature into a claim of current authorization.

## 14. Revocation, poisoned ancestry and downloads

Revocation does not delete the archive or mutate its acceptance. The service ingests signed denial records, verifies their ordered policy chain, updates the derived denial set, and checks them before accepting new candidates, granting downloads or starting a stream.

The minimal parent-link protocol supplies exact ancestral acceptance references. The service can verify those references and propagate an ancestor poison denial without choosing a winning fork. Recompute denial closure from signed records on rebuild. Cache it only with a bound policy-head sequence; an unavailable/stale head makes the run unavailable for acceptance/downloads.

Downloads require exact accepted representation, valid archive/receipt pair, current actor scope, complete copy evidence, supported protocol and unrevoked key/authority decision according to the released compromise policy. Any requirement that cannot be established produces retryable unavailable, not success. Historical receipt inspection may remain available to authorized operators with `eligible=false`; it must not masquerade as resumable state.

A download grant is bound to one actor/session, exact archive and receipt digest, run, environment and a 60-second start expiry. It is one-use for starting a stream; interrupted clients request a fresh grant. Range requests and resumable multipart download are disabled for v1. No presigned R2 URL, redirect, shared cache or public bucket is used. Return `Cache-Control: private, no-store`, fixed binary MIME type and a filename generated from the digest.

Before streaming, fetch and verify the complete object into bounded trusted staging or use an already verified immutable local cache entry. This prevents corrupt provider bytes being released before the final hash check. After staging, obtain a one-use stream-admission permit from the linearizable external control service, bound to actor/session, grant, acceptance and exact representation. Admission linearizes when that service records the permit against its current head. Revocation blocks all later permits. A cached denial generation alone cannot admit a stream; control-service unavailability refuses.

Revocation denies all admissions ordered after its commit at the authoritative control service. Permits already ordered before that event count as active admissions, even if their first byte has not yet been sent. The control channel pushes cancellation to gateways; each gateway rechecks the current head at most every two seconds and before every 8 MiB sent. If that channel loses freshness for more than five seconds, cancel streams and refuse new ones. These are measurable cancellation targets, not a promise to recall delivered bytes. Previously downloaded data cannot be erased remotely. Clients must recheck status before treating any cached archive as resumable. Acceptance exposure similarly obtains a current ordered eligibility response after finalization rather than relying on a cached head.

### Emergency physical removal

Emergency removal is exceptional and separate from ordinary revocation:

1. Commit signed denial/poison records; stop intake, signing, downloads and every writer/replicator; invalidate service sessions/capabilities and preserve the control head.
2. Two named operators authorize exact digest(s), affected buckets/prefixes, reason and session duration. Enumerate everything a lock-rule change would expose.
3. Isolate all runtime credentials and prove traffic/writers stopped. Permission propagation is not assumed instantaneous.
4. Perform the explicit administrative lock-rule removal, object deletion and lock-rule restoration under the deployment runbook, including both copies and any quarantined/staged copies in scope.
5. Verify locks are restored, verify all unrelated retained objects against the pre-incident inventory, record unavoidable exposure windows and rotate compromised credentials.
6. Record a signed tombstone/incident outcome so rebuild distinguishes authorized removal from unexplained data loss. Restore service only after the CP-8 drill's criteria pass.

Whole-bucket locks do not supply S3's exact-version bypass. No automated procedure weakens a lock merely because a deletion request names one digest. The recovery design retains same-provider/administrator compromise limitations explicitly.

## 15. Reconstruction, outages and anti-rollback

Rebuild uses verified immutable records, not trusted PostgreSQL rows or object metadata. It runs into a new database and cannot mutate the live index until its comparison report passes.

1. Stop intake, signing and downloads, and obtain a current signed authority-head checkpoint from the independent control/signer service, including committed counts/digests for both policy history and the decision journal. If freshness cannot be obtained, operate only an offline forensic reader.
2. Enumerate primary/recovery objects with bounded pagination and a restart cursor. Metadata is a routing hint; content hash, parsed type and signature establish meaning. Apply resource limits when reading unknown objects.
3. Verify trusted bootstrap keys and every key/grant/policy transition from the pinned root through the fresh head. Missing sequence, forked head, unauthorized rotation or rollback is a refusal.
4. Enumerate and verify every journal entry through its committed head; reconcile every authorized/cancelled/denied/finalized decision with both R2 stores. Rebuild run registrations, authorizations and acceptance predicates. Missing signed envelopes or copies become explicit incomplete/unavailable decisions, never silently omitted history. Identical equivalent envelopes collapse to one logical decision; contradictory identities stop that run.
5. Apply revocations, key-compromise policy, poisoned ancestor closure and authorized-removal tombstones. An archive without a valid complete acceptance remains an orphan. A receipt without required bytes/copies is historically signed but operationally unavailable.
6. Rebuild query indexes/outbox repair work. Temporary sessions and candidate grants are invalidated. Only pre-authorization candidates whose inputs/state cannot be recovered need reannouncement/revalidation. Reconstruct every signer-authorized unfinished decision from its exact journaled payload/envelope and resume publication, finalization or signed denial without changing decision identity or reauthorizing it. Discarding temporary state cannot erase accepted or signer-authorized work.
7. Compare counts and a deterministic sorted digest over accepted decisions, representations, revoked/poisoned targets, active grants, key history and current head against the pre-loss reference where available. Report every missing object and repair; absence of a prior reference is stated.
8. Rerun offline verification and denial/download fixtures. Only then swap the index, with fresh policy-head verification before writes/downloads resume.

An independent signer-held authority checkpoint is necessary because two restored buckets plus an old database snapshot cannot prove absence of a later acceptance or revocation if account history was rolled back. Its decision-journal commitment covers acceptance-history completeness as well as policy/key history. Signatures on isolated records establish authenticity, not completeness or freshness. Loss of the external journal/checkpoint service causes unavailable, not an assertion that an older view is current.

Ordinary outages:

- API failure: clients retry idempotently; they retain local archives.
- Worker failure: fenced lease expires; retry uses sealed bytes and a fresh sandbox.
- Primary or recovery ambiguity: exact GET/hash resolves success vs absence; mismatched bytes freeze publication.
- Signer failure: remain `awaiting_signature`; never use an API-local key.
- Receipt-copy failure: remain `publishing_receipt`; never expose an incomplete receipt as accepted.
- Database failure: stop operational transitions and downloads until denial freshness and indexes are reconstructed.
- R2 provider-wide outage: both copies may be unavailable. The profile offers no provider-diverse restoration guarantee.
- Full account compromise: separate recovery credentials reduce exposure to compromise of the primary account; an administrator or shared control-plane compromise remains a risk. Do not convert “two accounts” into an independent-copy claim.

## 16. Refusal taxonomy and retry contract

The API distinguishes invalid input, denied scope, dependency unavailability and service failure. It carries an allowlisted `protocol_code` when the pinned tool actually emits one. Do not collapse every exception into an invalid-archive verdict or claim all 24 CP-3 classes originate in inspect.

| Class | HTTP / example code | Client behavior |
|---|---|---|
| Authentication missing/expired | 401 `auth_required` | Log in again; do not replay a different actor's key |
| Hidden or forbidden target | 404 `not_found` | No resource-existence leak |
| Invalid bounded JSON/field/version | 400/422 `request_invalid`, `protocol_unsupported` | Correct the request; no automatic schema downgrade |
| Identity/key/run mismatch | 422 `identity_mismatch`, `endorsement_invalid`, `signer_not_enrolled` | New valid evidence required |
| Size/framing failure | 411/413/422 `length_required`, `upload_too_large`, `upload_integrity` | Correct bytes/size; no partial acceptance |
| Quota/rate limit | 429 `quota_exceeded` | Retry only after bounded `Retry-After` |
| Conflicting idempotency/lease | 409 `idempotency_conflict`, `upload_in_progress` | Query existing operation; never create a competing overwrite |
| Expired candidate/capability | 410 `candidate_expired` | Reannounce under current policy |
| Protocol refusal | 422 `protocol_refused` plus exact allowlisted upstream code | Fix the named contract failure |
| Revoked/poisoned scope | 409 `checkpoint_ineligible` | Do not resume; operator-only reason details |
| Dependency or freshness unavailable | 503 `replica_unavailable`, `signer_unavailable`, `policy_unavailable` | Retain local work, retry same operation |
| Sandbox/tool failure | 503 `validation_failed` | Bounded retry; operator investigation after retry cap |
| Unsupported graph capability | 501 `capability_not_enabled` | No inferred empty frontier |
| Storage-integrity or contradictory authority | 503 `authority_unavailable` | Freeze affected scope; incident handling |

Rejection is a bounded authenticated service result, not a newly invented signed portable statement. A future portable signed rejection would require a published schema and consumer need. No status code or retry message substitutes for a signed accepted receipt.

## 17. Security risks, observability and resource evidence

```risk-register
actor-confusion | identity provider to run grant | numeric identity, current grant and exact upload endorsement agree
grant-replay | contributor to gateway | attempt leases, size/hash binding, actor binding and expiry hold
quarantine-swap | staged bytes to validator | descriptor-bound immutable input and publish-time digest agree
archive-escape | hostile carrier to sandbox | no host/network/credential escape and resource ceilings hold
false-inspect-success | inspector to admission | restore, observations, reminted identity and service trust checks all pass
untrusted-key | carried commit key to contributor policy | enrollment and approved historical keys cannot self-authorize
prior-receipt-gap | external parent link to authority | pinned schema verifies complete prior evidence and denial closure
publication-race | service workers to R2 | conditional destination writes, leases and read-back prevent contradictory acceptance
signing-oracle | publisher to independent signer | signer independently verifies typed policy and copy evidence
receipt-cycle | archive decision to receipt copies | no self-hash or premature signed-acceptance claim
policy-rollback | stored history to current eligibility | external fresh control head prevents stale revocation view
revocation-race | accepted grant to streaming response | no new admission after denial and bounded active cancellation
admin-unlock | control plane to retained objects | scoped operator procedure acknowledges collateral exposure
rebuild-drift | immutable records to SQL index | deterministic replay preserves decisions and poisons
diagnostic-leak | child output to API/logs | fixed codes and bounded private output suppress secrets
cost-exhaustion | admitted uploads to host/storage | reservations, disk ceilings, concurrency and expiry stop unbounded work
provider-correlation | primary to recovery | same-provider and unproved region separation remain explicit
```

Four on-call questions and the signals answering them:

| Question | Structured event / metric | Action |
|---|---|---|
| Why has this candidate stopped advancing? | Candidate transition events with request/job/lease IDs; state-age histogram and retry-reason counts | Inspect bounded stage result; recover expired lease or failing dependency |
| Can an accepted checkpoint still be verified? | Full-byte verification failures, missing-copy counts, receipt-signature failures | Freeze scope; repair from verified copy; never serve corrupt bytes |
| Are we using current authority? | Control-head sequence, freshness age, policy-chain conflicts, denied-grant counts | Refuse admission; recover signer/control channel |
| Will the service exhaust capacity or leak data? | Reserved vs used scratch/bytes, queue age, sandbox kills, cleanup lag, redaction check failures | Stop new grants before capacity exhaustion; investigate refusal/cleanup |

Event fields are bounded and schema-versioned: timestamp, request/job/candidate opaque IDs, state before/after, fixed reason code, result digest, policy head, service version and duration/byte counts. Keep identity/digest correlation in access-controlled logs, not metric labels. Never log tokens, authorization headers, query credentials, object bodies, observation text or arbitrary subprocess output. Access attempts, refusals, retries and administrative operations get events.

Page/alert conditions: any invalid receipt/corrupt accepted object or conflicting authority is immediate; freshness over five seconds makes gateways unready; candidate stage age over its measured target for five minutes warns; quarantine cleanup over 48 hours alerts; scratch below two maximum-job reservations closes admission. Detailed thresholds become deployment policy after the baseline; changing a threshold cannot change accepted truth.

R2 Data Access Logs are not the decision ledger. Current Cloudflare documentation says they are unavailable for jurisdictional buckets and omit some failures/events. EU deployment must rely on service/adapter events plus available control-plane auditing, and state that coverage. Lifecycle cleanup is asynchronous, so application expiry is immediate while physical deletion is measured separately. [Data Access Logs](https://developers.cloudflare.com/r2/buckets/data-access-logs/), [object lifecycles](https://developers.cloudflare.com/r2/buckets/object-lifecycles/).

### Performance contract

`./scripts/benchmark.sh --profile local --corpus protocol.lock.json` writes raw samples and a machine-readable report with hardware, kernel/sandbox/runtime/image pins, fixture digests, command, concurrency, repetitions, median/p95, CPU, peak RSS, scratch peak and upload/download/provider request counts. Measure first; any optimization is one recorded change followed by the same workload.

Initial acceptance gates: no API buffering proportional to carrier size; gateway incremental memory <=64 MiB per stream; inspector job within section 10 ceilings; metadata p95 <=500 ms on the declared local profile excluding identity-provider calls; current CP-3 valid fixture completes local validation within 900 seconds. Verify reference fixtures at their actual current size, including the latest reported 111,860,548-byte carrier and the earlier 100,790,501-byte measurement. These are admission/performance targets to prove, not results claimed here.

Provider throughput and monthly total cost are measured in #863. R2 egress pricing does not make gateway bandwidth, DigitalOcean outbound traffic, API operations, repeated full-object read-backs, scratch, database or KMS free. No cost estimate is a deployment permission.

## 18. Implementation layout and configuration contract

Proposed service layout:

```text
src/fiat_checkpoints/
  api/ auth/ grants/ domain/ persistence/
  validation/ storage/ replication/ signing/ records/
  downloads/ denial/ recovery/ telemetry/
schemas/                 # API-only schemas; protocol imports are pinned artifacts
migrations/
protocol.lock.json
pyproject.toml + dependency lock
containers/              # API and isolated validation images pinned by digest
config/                  # non-secret schema and test defaults
scripts/                 # check, reject-case, demo, benchmark, rebuild, conformance
tests/                   # unit, contract, hostile, concurrency, crash, recovery
docs/                    # specification, study/runbook, decisions, operator runbooks
```

Configuration is validated at startup. Required production values include service/environment IDs, canonical issuer/audiences, allowed GitHub App callback and repository IDs, primary/recovery logical storage mapping, EU endpoints, credential references, signer endpoint/trust roots, control-head freshness source, protocol lock, database connection secret reference, sandbox profile and all quotas. Unknown keys, equal primary/recovery account IDs, non-EU endpoints for an EU profile, test trust roots, missing pins or unavailable sandbox isolation fail readiness.

Secrets arrive through protected runtime secret mounts or the host secret service. No credential values, deployed environment values, production archive/observation or private evidence enters this public repository. Tests generate synthetic archives in ignored temporary paths. CI has no production storage or signer secrets. CI must run untrusted PR tests without release credentials.

Configuration changes that affect authority/compatibility/limits are signed policy revisions. Application deployment cannot silently replace trusted keys, broaden supported protocol versions or reduce retention. Public build/version metadata is safe; private actor/object inventory is not a health endpoint.

## 19. Implementation runbook for #862

The following commands are deliverables to implement. They have not run against a service that does not yet exist. Every step must leave its current test set green. Each exit includes `./scripts/check.sh`; group arguments add focused evidence. The final script emits JSON with command, exit, case IDs, exact source/protocol/tool digests and artifact hashes.

The eventual Fiat study must separately read current applicable audit sources, build its source-bound known-failure inventory and design-evidence record, and obtain normal receipts. This specification does not fabricate either record. P-862 may proceed in parallel with service scaffolding; step 2's protocol contract exit is blocked until the prerequisite release and document amendments land.

### Step 1: scaffold the isolated service repository

**Goal.** Establish a reproducible empty service and exact specification provenance.
**Entry.** Service target, current instructions, branch and creator/publisher identities verified; no shared dirty worktree used.
**Exit.** `./scripts/check.sh --group scaffold` proves locked dependencies, configuration parser, CI, license and repository hygiene; no live deployment.
**Files.** Toolchain/lock files, containers, CI, `docs/specification.md`, `docs/study.md`, `docs/runbook.md`, source manifest and configuration schema.
**Tests.** Dependency-lock drift, missing config, production test-root refusal, no secrets/real archives in tracked tree.
**Disciplines.** Phylax: dependencies/process boundary; Ephoros: initial health/event shape; Metron: record reference host; Elenchus: guard any observed build failure; Hypomnema: specification and architecture homes.

### Step 2: pin portable records and domain transitions

**Goal.** Consume the final P-862/CP-3 contracts and model decisions without network side effects.
**Entry.** P-862 released with adopted R2/ownership amendments, schemas, parent-link rules, enrollment/endorsement and signer profile.
**Exit.** `./scripts/check.sh --group protocol,domain` verifies lock digests, golden/hostile records and complete legal/illegal transition matrix.
**Files.** `protocol.lock.json`, protocol artifact loader, record verifiers, domain types and state transition rules.
**Tests.** Wrong protocol/environment/predicate, three-digest substitutions, unknown fields, untrusted keys, absent parent verification, DSSE vectors and signature-byte preservation.
**Disciplines.** Phylax: hostile records; Ephoros: typed refusal shape; Metron: bounded parser limits; Elenchus: fixture-based regression guards; Hypomnema: protocol/identity/DSSE decision record.

### Step 3: persist candidates, work leases and immutable decision intent

**Goal.** Make coordination retryable without making SQL authoritative.
**Entry.** Step 2 green; empty/migrated PostgreSQL profile available.
**Exit.** `./scripts/check.sh --group persistence,concurrency` proves migrations, quotas, idempotency scope, leases and transactional outbox.
**Files.** Migrations, persistence adapters, reservations, leases/outbox and replay types.
**Tests.** Concurrent announces, key reuse with changed bytes, stale worker completion, migration restart and unique-decision contention.
**Disciplines.** Phylax: queries/transactions; Ephoros: state and lease events; Metron: contention baseline; Elenchus: crash/race guards; Hypomnema: persistence/rebuild contract.

### Step 4: authenticate contributors and enroll keys

**Goal.** Bind an authorized human and approved key history to one submission.
**Entry.** Pinned identity/endorsement contracts and state persistence green.
**Exit.** `./scripts/check.sh --group auth,endorsement` proves login, expiry/CSRF, per-run grants, proof of possession and exact-upload endorsement.
**Files.** Login/session adapters, signed grant projection, key registration, endorsement and authorization middleware.
**Tests.** Actor/repository rename vs numeric ID, login token substitution, replay, expired endorsement, altered ZIP digest, unauthorized historical signer, revoked scope.
**Disciplines.** Phylax: identity/secrets; Ephoros: authentication/refusal events; Metron: request bounds; Elenchus: hostile identity guards; Hypomnema: credential and key-custody ADR.

### Step 5: implement bounded quarantine transfer

**Goal.** Seal exact candidate bytes without exposing provider credentials.
**Entry.** Current auth/endorsement and quota policy available.
**Exit.** `./scripts/check.sh --group upload,quarantine` proves framing, counts/hash, expiry, sealed attempts, cleanup and crash retry.
**Files.** Streaming gateway, trusted staging, quarantine R2 adapter, sweeper and upload routes.
**Tests.** Missing/extra/truncated body, changed hash, replay/concurrent grant, slow client, disk full, expiry during stream, proxy-size deployment guard and swap attempt.
**Disciplines.** Phylax: untrusted bytes/files; Ephoros: upload/cleanup state; Metron: bounded-memory/disk measurement; Elenchus: transfer failure guards; Hypomnema: grant and staging contract.

### Step 6: integrate isolated semantic validation

**Goal.** Produce complete evidence from inspect, restore, verify, identity and service trust checks.
**Entry.** Sealed input and the complete pinned protocol/runtime image; no archive-carried executable trusted.
**Exit.** `./scripts/check.sh --group validation,sandbox` and `./scripts/reject-case.sh --all` prove the actual CP-3 corpus plus wrapper containment and service refusal cases.
**Files.** Sandbox launcher, typed command/output adapter, historical signer checks, parent/prior verifier, bounded Git-object scan, resource policy.
**Tests.** Section 10 sequence and residues; #1647/#1648/#1649 containment; OOM/time/disk/PID limits; inherited Git settings; failed restore followed by successful verify; stale output; self-consistent false carried identity.
**Disciplines.** Phylax: subprocess/archive/Git boundary; Ephoros: measured validation outcomes; Metron: fixture resource baseline; Elenchus: each source-bound failure guard; Hypomnema: validation coverage and exclusions.

### Step 7: implement R2 publication and recovery copy

**Goal.** Publish exact verified bytes with no overwrite and prove both copies.
**Entry.** Complete validation evidence, configured local object-store fault profile.
**Exit.** `./scripts/check.sh --group storage,replication` proves conditional writes, full-byte read-back, lease fencing and ambiguous-write recovery.
**Files.** Production R2 adapters, publisher, replication worker, copy evidence and configuration drift checks.
**Tests.** Competing PUTs, occupied matching/mismatching key, timeout after write, GET corruption, same-account misconfig, recovery outage and object-lock conformance command contracts.
**Disciplines.** Phylax: storage credentials and integrity; Ephoros: copy/failure events; Metron: I/O and memory baseline; Elenchus: fault-injection guards; Hypomnema: R2 lock/replication trade record.

### Step 8: implement signer orchestration and durable acceptance

**Goal.** Make acceptance derive only from the complete publication predicate.
**Entry.** Step 7 green and CP-5 signer interface/fixtures frozen under P-862.
**Exit.** `./scripts/check.sh --group signing,acceptance` proves DSSE/cosign-compatible verification, idempotent signer responses and receipt publication in both stores.
**Files.** Signer client, exact envelope persistence, acceptance verifier/projector and internal authority-record ingestion.
**Tests.** Wrong subject/key/environment, malformed DER, accidental double hashing, signer changes retry payload, stale grant/head, missing receipt replica, every crash point around sign/publish/index commit, production mock refusal.
**Disciplines.** Phylax: signing boundary; Ephoros: acceptance/signing signals; Metron: bounded signer work and retries; Elenchus: receipt fault guards; Hypomnema: accepted-predicate and signer ownership ADR.

### Step 9: implement reads, denial enforcement and index rebuild

**Goal.** Serve only eligible exact identities and reconstruct the same authority after SQL loss.
**Entry.** Golden test acceptance exists; signed denial/key transition fixtures available.
**Exit.** `./scripts/check.sh --group download,revocation,recovery` and `./scripts/rebuild-check.sh --profile local` prove current-policy reads, cancellation and deterministic reconstruction.
**Files.** Authenticated inventory/receipt/download routes, denial projection, stream cancellation, replay engine, swap procedure and recovery runbook.
**Tests.** Wrong actor, poisoned ancestor, missing replica, policy rollback, revoked grant race, lost update, stale cache, prior-stream cancellation, missing/contradictory authority records and restartable rebuild.
**Disciplines.** Phylax: private retrieval and replay; Ephoros: availability/freshness alerts; Metron: bounded streaming and replay; Elenchus: loss/rollback guards; Hypomnema: revocation, restore and break-glass runbooks.

### Step 10: demonstrate and hand off production proof

**Goal.** Deliver a complete reviewable service and an exact #863 conformance handoff.
**Entry.** All earlier checks pass with pinned source/protocol/toolchain and no unresolved acceptance-impacting failure.
**Exit.** `./scripts/check.sh`, `./scripts/reject-case.sh --all`, `./scripts/demo.sh --scenario end-to-end --profile local`, `./scripts/crash-matrix.sh --profile local`, `./scripts/rebuild-check.sh --profile local`, and `./scripts/benchmark.sh --profile local --corpus protocol.lock.json` all emit successful evidence reports.
**Files.** Final demonstration, evidence index, production conformance harness, operator runbooks, README, example config and #863 handoff.
**Tests.** Full matrix below, including repeated-node handoff limits, negative production startup and exact protocol mismatch.
**Disciplines.** Phylax: final boundary review; Ephoros: alert/event drill; Metron: recorded baseline; Elenchus: unresolved failure review; Hypomnema: complete deployment/recovery handoff.

The run's step-level Elenchus reporter command and `{report}` path must be supplied in the receipted runbook for each step, using real tests from that step. Do not invent test counts before the corpus exists, and do not replace a required hostile guard with a test that merely mirrors implementation.

## 20. Acceptance and hostile-input matrix

`./scripts/check.sh` is the stable all-tests entry point. `./scripts/reject-case.sh --case ID` replays one negative case; `--all` runs the declared corpus and reports expected/observed stage, refusal and artifact digests. All 35 upstream hostile fixture IDs remain present at their actual producer/inspect/restore phase, accounting for all 24 refusal classes without claiming the inspector emits all of them.

| ID | Demand / hostile case | Required proof |
|---|---|---|
| AC-01 | Authorized exact-byte upload only | Valid endorsement and grant accepted; wrong actor/key/run/bytes/size/expiry refuse before validation |
| AC-02 | Bounded intake | Oversize, slow stream, abandoned attempts and concurrent reservations cannot exceed configured disk/memory/quota |
| AC-03 | No contributor storage powers | No provider credential/URL emitted; read/list/delete/overwrite attempts cannot use an upload capability |
| AC-04 | Inspector is not overclaimed | Carried identity forgery, invalid restored controller and unread prior acceptance cannot pass complete admission |
| AC-05 | Validator isolation | Network/metadata/hooks/config/other-job/symlink escapes fail; all resource kills leave no authority write/signature |
| AC-06 | External contributor trust | Unenrolled key, endorsement replay and unauthorized receipted-commit history refuse despite internal signature consistency |
| AC-07 | Three identities remain distinct | Repacking returns proved equivalent state; identity/manifest/archive substitutions refuse; canonical accepted representation is stable |
| AC-08 | Conditional immutable publication | Concurrent and ambiguous primary/recovery writes resolve only to matching exact bytes or refusal |
| AC-09 | Replica requirement | Missing, wrong-account, corrupt or unverified replica never clears `awaiting_replica` |
| AC-10 | Independent signing | Publisher cannot sign arbitrary payload; wrong evidence/policy/key refuses; test signer cannot activate production |
| AC-11 | Durable accepted predicate | Kill before/after each write, read-back, sign and SQL transaction; rebuild exposes no premature acceptance |
| AC-12 | Receipt verifier interoperability | Registered Ariadne predicate gates and external DSSE signature verification agree; unknown predicate/gate is not success |
| AC-13 | Current denial enforcement | Revoked snapshot, poisoned ancestor and stale control head prevent new grant/stream/acceptance; active cancellation meets target |
| AC-14 | Safe private reads | No cache/public URL/redirect, unauthorized existence leak or unverified binary output; page and response caps hold |
| AC-15 | Rebuild invariance | Destroy PostgreSQL, reconstruct from records/copies/fresh head, compare deterministic authority/denial digest |
| AC-16 | No stale authority rollback | Old signed but incomplete/stale history refuses; missing policy head or conflicting key chain stops online operation |
| AC-17 | Redacted diagnostics | Inject tokens, paths and private text into failures; logs/API return only bounded allowed data |
| AC-18 | Operational evidence | Health separates liveness/readiness; metrics avoid actor/digest labels; symptom alerts link working runbooks |
| AC-19 | Performance and cleanup | Baseline report proves stated ceilings; expiry denies immediately and cleanup lag is observable |
| AC-20 | Packet ownership | No Skills file change; no full frontier/resolution claim; service adapters complete; #863 live proofs enumerated |

The crash matrix covers each adjacent pair of state transitions and each individual external operation, plus lease loss, DB restart, signer retry randomness, equal semantic/different ZIP races, revoked authority during signing, stale download grants and recovery during partial receipt publication. Every case asserts absence of authority advancement as well as the correct error.

## 21. #863 deployment proof and later packets

#863 receives complete service code, pinned schemas/fixtures, signer interface, exact acceptance predicate, all configuration schemas and the conformance commands. It supplies the external signer/control-head implementation, real identities/accounts/buckets/credentials and deployment evidence. Its implementation must meet the protocol/profile specified here; it cannot substitute a raw KMS signing oracle.

Its required live proofs are:

1. Exact primary/recovery accounts and EU bucket jurisdictions; whole-bucket indefinite locks; no runtime configuration power; every runtime token's overwrite/delete behavior tested; administration and signing isolated.
2. Real conditional PUT contention and ambiguous response recovery using the exact production SDK version; full primary and recovery read-backs.
3. Independent policy-signer rejection tests, KMS key custody and algorithm/DSSE interoperability; idempotent exact-envelope/finalization replay; key rotation, revocation, decision-journal completeness and fresh external authority-head recovery; linearizable stream-admission permits.
4. Direct transfer hostname and body limits large enough for configured maximum; TLS, access controls and per-host resource reservations verified.
5. Full real-provider flow including signer/replica outage, receipt-copy failure, request-time denial and database rebuild. Record exact digests/commands/configuration IDs without secrets.
6. Production startup/readiness refuse test roots, missing protocol pin, same-account replica, absent lock evidence or stale denial head.

#864 consumes exact acceptance and status APIs; it must reverify current denial state before advancing an external run. #865 adds the full lineage query/resolution service after its own Skills protocol packet; acceptance never selects a frontier. #866 performs incident/DR/break-glass drills against the deployed system and documents same-provider limitations. #867 integrates Atlas using the released redacted projection and authenticated retrieval paths. No consumer can infer absent features from an empty successful response.

## 22. Delivery authority, issue linkage and completion record

The current controller rejects `--task-issue` from a repository different from the working repository's origin. Do not invoke it with Skills #862 inside `fiat-checkpoints` and pretend linkage succeeded. The chosen delivery arrangement is a same-repository implementation issue in `wildcat-finance/fiat-checkpoints`, explicitly linked bidirectionally to Skills #862 and this specification's digest. Creation occurs only when implementation/publication is requested; no issue is created by this specification turn.

Run Fiat against that service issue in a dedicated service worktree, following the target's current instructions. #862 remains the programme tracker and closes only after its service implementation evidence is linked and independently checked. Do not patch the controller, relabel the origin or quietly run unlinked merely to evade its repository check.

Always: verify exact worktree/branch/identity and pins; maintain the state machine and acceptance predicate; use synthetic public fixtures; preserve append-only authority; run the step's required evidence commands; retain failures and declared coverage limits.

Require separate explicit authority for: creating cloud resources/accounts/keys, spending, deploying, changing DNS/access, changing the accepted cross-repository protocol or provider decision, and physical removal of locked objects. Ordinary implementation choices and reversible local corrections within an authorized run do not need repeated permission.

Never: edit Skills under #862; self-enroll contributor keys; give archive code credentials/network; treat a signed claim as proof all tests ran; mark pending replica/signature state accepted; use a public or presigned download to bypass current denial checks; erase historical issue filing or known failures.

The closing PR and #862 completion note must include service commit and specification digest; protocol/schema/verifier/fixture pins; exact executed command results and report hashes; acceptance-case IDs; preserved upstream carryovers/containments; unresolved failures; production conformance items assigned to #863; and a clear statement that local demonstration is not production launch. An implementation-impacting unknown cannot be hidden in prose while marking the packet complete.

## 23. Source register, prior art and explicit evidence gaps

### Verified source baseline

- [Skills main at 6982793334003dc0a441d6e90e753a143e3f2a6c](https://github.com/wildcat-finance/skills/tree/6982793334003dc0a441d6e90e753a143e3f2a6c), Fiat `v6.60.1`.
- [PR #1652](https://github.com/wildcat-finance/skills/pull/1652), CP-3/#861, merged 15 September 2026 at 13:41:51 UTC. Source says inspect is not a service ownership or complete prior-acceptance check. Latest reported valid carrier is 111,860,548 bytes; parser cap is 1,363,148,800 bytes. The earlier 100,790,501-byte fixture and 201,581,002/209,715,200-byte performance budgets are distinct from hard parser limits.
- [PR #1413](https://github.com/wildcat-finance/skills/pull/1413), CP-2/#860, merged 6 September 2026 at 11:31:06 UTC, `0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`. Preserves one relocated identity; nested-restore prefixes remain refused.
- [ADR-070](https://github.com/wildcat-finance/skills/blob/6982793334003dc0a441d6e90e753a143e3f2a6c/docs/decisions/ADR-070-separate-the-checkpoint-protocol-from-its-authority-service.md), portable protocol ownership and in-toto/DSSE boundary.
- [ADR-071](https://github.com/wildcat-finance/skills/blob/6982793334003dc0a441d6e90e753a143e3f2a6c/docs/decisions/ADR-071-hold-checkpoint-authority-in-locked-storage-behind-replaceable-compute.md), version/retention/replica language needing explicit R2 amendment.
- [Programme runbook](https://github.com/wildcat-finance/skills/blob/6982793334003dc0a441d6e90e753a143e3f2a6c/docs/wave-delta-checkpoint-programme-runbook.md), Steps 3 through 8 ownership and entry gates.
- [Archive contract](https://github.com/wildcat-finance/skills/blob/6982793334003dc0a441d6e90e753a143e3f2a6c/plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md), [controller source](https://github.com/wildcat-finance/skills/blob/6982793334003dc0a441d6e90e753a143e3f2a6c/plugins/hexaemeron/skills/fiat/scripts/hexctl.py), [identity contract](https://github.com/wildcat-finance/skills/blob/6982793334003dc0a441d6e90e753a143e3f2a6c/plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md).
- [Service substrate at 61b8dc4be1587d1c6ef46f2f228833214965e7f1](https://github.com/wildcat-finance/fiat-checkpoints/blob/61b8dc4be1587d1c6ef46f2f228833214965e7f1/docs/deployment-substrate.md), read with the README; this baseline contains no service implementation or prior implementation PRs/audit history.
- [#1647](https://github.com/wildcat-finance/skills/issues/1647), [#1648](https://github.com/wildcat-finance/skills/issues/1648), [#1649](https://github.com/wildcat-finance/skills/issues/1649): diagnostic leakage, destination-name swap and restore concurrency follow-ups remain open. Service wrapper containment is not upstream closure.
- Current [#862](https://github.com/wildcat-finance/skills/issues/862) body, provided constraint note and historical August S3 documents were read for requirement reconciliation. Current source supersedes their stale implementation/state claims.

### Provider/standard evidence

Official docs checked 15 September: [R2 presigned URLs](https://developers.cloudflare.com/r2/api/s3/presigned-urls/), [temporary credentials](https://developers.cloudflare.com/r2/api/s3/temporary-credentials/), [permission scopes](https://developers.cloudflare.com/r2/api/tokens/), [bucket locks](https://developers.cloudflare.com/r2/buckets/bucket-locks/), [S3 compatibility](https://developers.cloudflare.com/r2/api/s3/api/), [consistency](https://developers.cloudflare.com/r2/reference/consistency/), [data location](https://developers.cloudflare.com/r2/reference/data-location/), [durability](https://developers.cloudflare.com/r2/reference/durability/), [request limits](https://developers.cloudflare.com/workers/platform/limits/), [lifecycle](https://developers.cloudflare.com/r2/buckets/object-lifecycles/), [data-access logs](https://developers.cloudflare.com/r2/buckets/data-access-logs/), [AWS KMS Sign](https://docs.aws.amazon.com/kms/latest/APIReference/API_Sign.html), [GitHub App login](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app), [DSSE](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md), [in-toto](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md).

### Remaining evidence and readiness

This document closes the five identified specification conflicts by assigning the missing protocol packet, amending R2 durability semantics, assigning signer/replica code, defining external contributor trust and choosing an explicit deployment profile. It also provides all five demand groups: bounded transfers, isolated validation, durable transitions, reconstruction/denial and operational evidence.

It does not establish a deployed bucket policy, live account independence, working signer, measured performance, passed hostile fixtures or full Fiat study readiness. No such live operation/test was performed here. The formal implementation study still must refresh applicable audit sources and record every known finding/coverage limit in its current source-bound inventory. The source reading here covered current contracts, implementation, issue records and the last two relevant merged PRs; it is not a whole-repository audit-synopsis currency check.

Specific blocking gates are: adopted P-862 protocol/document release before step 2 completes; real current run-key authorization before admission; current policy-head/parent verification before acceptance or download; #863 live substrate/signer conformance before production activation. All are explicit dependencies, not permission to ship a weaker fallback.
