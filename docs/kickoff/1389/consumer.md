# Miskatonic consumer and activation contract

This record selects `wildcat-finance/miskatonic` for the headless consumer
required by [#1491](https://github.com/wildcat-finance/skills/issues/1491).
It specifies interfaces for subsequent implementation. The selected revision
contains only `README.md`; none of the Miskatonic commands below exists yet.
Acceptance of this input record does not establish a working service or
authorise production activation.

## Selection and evidence

The maintainer selected [Miskatonic](https://github.com/wildcat-finance/miskatonic)
in the delivery session on 2026-09-21, describing it as newly created.
The exact reply is preserved in [evidence/decision.json](evidence/decision.json).
The repository is private; its source links require existing repository access.
This record changes no access setting.

| Input | Pinned value | Evidence |
| --- | --- | --- |
| Consumer source | `54f86d2bed44f6b9f71edda8a883805f4b409b39`, default branch `main` | GitHub commit and complete tree responses in `evidence/commands.json` |
| Source inventory | One file, `README.md`, blob `bf94907aa21c993f1b9cbb302e5cf2dbaae0d6c1` | Complete tree; no code, tests, workflow or route declarations |
| Skills source | `7952eafa337f5ba1c4f45417ceb154673f629c1c` | File digests in `evidence/sources.json` |
| Prior active consumer release | None recorded for this new repository | Empty GitHub releases and deployments; zero workflows; maintainer's creation statement |
| External deployment inventory | Unknown | Repository APIs cannot exclude an unreported deployment elsewhere |

The producer and specification reviewer are the same Codex agent in task
`#1491: issue/16777231-875142073`. It applies Protasis to the input record,
then Phylax and Ephoros to the specified controls and signals. This is an agent
self-review, not independent or human approval. Its exact reviewed digests and
unexecuted checks appear in [evidence/review.json](evidence/review.json).

The maintainer confirmed `laurenceday` as the human owner of evaluation
threshold decisions and release approval. `evidence/decision.json` preserves
the question and the reply. This confirms the owner only; threshold values,
provider access, restricted-data entitlements and each activation still need
their own recorded approval.

## Existing interface and implementation handoff

At the Skills pin, `plugins/alexandria/scripts/alexandria.py` exposes `index`
and `query`. The query accepts repeated `--address` and `--venue`, optional
`--chain`, `--from-time` and `--to-time`, and one required `--index`.
Addresses normalise to lowercase 20-byte EVM addresses, chains use `eip155:N`,
and times are canonical non-negative integer seconds with start no later than
end. Results use `alexandria-address-query/v1` and retain request, index,
events, observations and coverage. A zero-row result keeps its coverage.

`alexandria_lib/query.py:32` calls `inspect_index` on each request.
`alexandria_lib/index.py:124` begins integrity, logical-digest and source-release
checks. This remains the operator interface; the new serving path must not
call it. [#1389](https://github.com/wildcat-finance/skills/issues/1389) owns
the split and the Miskatonic implementation. The baseline query help and index
test results are preserved in [evidence/commands.json](evidence/commands.json).
They establish no Miskatonic execution.

The following are exact target paths and interface requirements in Miskatonic,
all absent at the selected source revision. Use Python `3.14.6` for the initial
implementation and commit `.python-version`, `pyproject.toml` and dependency
pins with it. A changed interface needs a reviewed replacement input record.

| Operation | Target file and command | Owner |
| --- | --- | --- |
| Build | `miskatonic/build.py`; `python3 -m miskatonic build --inputs inputs.json --output candidate` | #1389: Alexandria and consumer maintainer |
| Address query | `miskatonic/query.py`; `python3 -m miskatonic query --state state --request request.json` | #1389: consumer maintainer |
| Admission | `miskatonic/activation.py`; `python3 -m miskatonic activate --state state --candidate candidate --decision decision.json` | #1397 verification; #1405 decision record; consumer switch |
| Rollback | `miskatonic/activation.py`; `python3 -m miskatonic rollback --state state --decision rollback.json` | #1405: Berean and consumer maintainer |
| Current selection | `miskatonic/activation.py`; `python3 -m miskatonic status --state state` | Consumer maintainer |

`miskatonic/__main__.py` supplies the dispatcher. Commands print one JSON
result, exit 0 on success and nonzero on refusal; stdout never implies success
after a nonzero exit. The initial query surface is a local CLI with OS access
controls. No HTTP listener, browser, user-account database or JWT guard is
selected.

`schemas/request-v1.json` must define a closed object with `schema` equal to
`miskatonic-address-request/v1`, one to 100 unique `addresses`, zero to 32
unique `venues`, `chain`, `from_time` and `to_time`. The last three fields may
be null; otherwise they retain the Alexandria formats above. Request bytes
are capped at 64 KiB. Venue strings must match the candidate's pinned registry.
Unknown fields, unsupported versions and invalid ranges refuse before data
retrieval. Query results are capped at 10,000 rows and 16 MiB; overflow refuses
without silently truncating. These are initial contract limits, not measured
performance claims. Multi-market cohort analytics needs its own interface.

`schemas/answer-v1.json` must bind each answer to the candidate digest, receipt
digest, full gate-report digest and promotion-record digest. Preserve the
Alexandria result inside the envelope, with the coverage and gap fields owned
by #1408. A missing venue or unreached subject stays visible; coverage metadata
does not establish a clean history or calculation correctness.

## Access, immutable outputs and activation

| Boundary | Required control | Evidence still owed by implementation |
| --- | --- | --- |
| Candidate intake | Closed manifest, relative confined paths, regular files only, byte limits, exact SHA-256 for every declared input/output and rejection of extra files | Hostile path, link, oversize and digest tests |
| Build | Read admitted local inputs only; preserve producer/source revisions, schema versions, coverage, receipt and complete Ariadne report including unchecked gates | #1389 and #1397 build reports |
| Query | Authorised local reader; read only the selected sealed candidate; no RPC, source archive, model or build verifier calls | Runtime instrumentation and external-network-denial tests |
| Activation | Operator-only state writes; exact expected predecessor; independently approved decision and evaluation; verify candidate before sealing and selecting it | Stale decision, denied caller and concurrency tests |
| Restricted data | No restricted inputs admitted by this initial contract; any later access policy must check authorisation before retrieval and isolate outputs/caches | A separately approved policy and programmatic denied-access tests |

Serving requires no RPC credential: its RPC key set is empty. No provider URL,
key value or purchase is specified. Offline build inputs are identified by
manifest digest, not fetched from arbitrary URLs. The query process cannot
write releases, decisions or the active pointer. OS root and the deployment
administrator remain trusted; read-only permissions do not protect against them.

The target layout is `state/releases/<candidate-sha256>/`,
`state/decisions/<decision-sha256>.json`, `state/journal/` and
`state/current.json`. First hash `payload-manifest.json`, which lists the
data files and their digests. The receipt and verification report bind that
payload-manifest digest. Then hash `candidate-manifest.json`, which binds the
payload manifest, every data file, receipt and report; it excludes itself and
the later promotion record, so no digest depends on itself. Encode both
manifests as UTF-8 JSON with sorted keys, compact separators, no ASCII escaping
and one trailing LF; reject duplicate keys and floating-point values.
Store the complete verification report and build receipt beside their subject.
Seal the release directory on
a read-only mount visible to the query identity; keep the writable build area
outside that mount. Reject symlinks, hard-link aliases and undeclared entries.
An operator must not reuse a release path for different bytes.

Under one writer lock, validate the expected predecessor, append and fsync the
intent record, then replace `current.json` using a temporary sibling file,
fsync and atomic rename on the same filesystem; fsync the parent directory.
The pointer binds the candidate and decision digests. Append the completion
record after readback. On restart, reconcile an unfinished intent against the
pointer before accepting another switch. Never mutate a previous decision.
A query reads the pointer once and holds that sealed release for its lifetime,
so a concurrent switch cannot mix candidates in one answer.

Rollback appends a new authorised record naming both its predecessor and the
previously accepted candidate, then follows the same switch protocol.
Missing prior bytes, a revoked candidate or failed policy refuses rollback.
First activation uses a null predecessor. Its recovery after a rejected
replacement preserves the current candidate; recovery from a failed first
activation leaves the service inactive. Production host, operator identities,
mount configuration and live authority are separate deployment inputs.

The release decision-maker owns `policy/evaluation-thresholds.json` in the
consumer, with exact metric definitions, thresholds and policy digest fixed
before evaluation. #1405 binds that policy, evaluation result, candidate,
approver and expected predecessor. Threshold values remain undecided here and
block promotion until approved; #1491 names the owner and destination only.
No passing evaluation or approval is claimed.

## Disposable acceptance plan

These commands are specified for future Miskatonic tests. They have not run
and currently cannot run at its README-only revision. Each report must carry
source revision, input/output SHA-256 values, command, exit, case results,
producer and reviewer. Use two synthetic candidates, A and B, in a temporary
state directory; never select a production path.

| Command | Required positive and refusal observations | Delivery owner |
| --- | --- | --- |
| `python3 -m unittest tests.test_build tests.test_query` | Build/query A; zero rows retain coverage; refuse invalid address, extra field, row/byte overflow and missing receipt; instrumentation observes zero request-time archive reads and verifier/RPC calls | #1389 |
| `python3 -m unittest tests.test_activation` | Activate A then B; reject corrupt bytes, stale/missing/mismatched reports, failed threshold, wrong predecessor and concurrent stale writer; deny a serving-identity write; interrupt before/after rename and recover without mixed state | #1397 and #1405 |
| `python3 -m unittest tests.test_rollback` | Append rollback B to A; preserve old decisions; query names A and new rollback record; reject missing/revoked A; test null-predecessor recovery | #1405 |
| `python3 -m unittest tests.test_replay` | Verified Lazarus fixture on `127.0.0.1` with an OS-selected port; declared read succeeds, undeclared key returns `-32070` plus capture-plan fragment, attempted external fetch fails | #1392 |
| `python3 -m unittest tests.test_coverage tests.test_access` | One row per pinned registry venue, unreached-subject gaps and zero-result coverage; refuse a dropped/altered row; deny unauthorised operator and reader before touching candidate bytes | #1408 and consumer maintainer |

For `tests.test_replay`, the declared RPC key is exactly
`{"method":"eth_chainId","params":[]}` with the expected result `0x1`.
The negative key is `{"method":"eth_blockNumber","params":[]}` and must
be absent from this synthetic fixture. #1392 must select and digest-pin a
verified #1384 fixture containing the declared key and no negative key before
execution; this test makes no historical-state claim. The application query
path itself still has no RPC reads. The runner must deny non-loopback network
access at the OS/container boundary, preserve loopback access, and remove live
fallback configuration. Monkeypatching a client alone is insufficient.

The specification's evidence lives in `docs/kickoff/1389/evidence/` in Skills.
Future consumer test evidence lives at `evidence/consumer/<source-sha>/`, with
a SHA-256 inventory committed or preserved in retrievable immutable storage.
Every downstream handoff names the actual report location and its access
requirements; a private source URL is not publicly retrievable evidence.

## Operational questions and remaining ownership

| Question | Specified signal | Bound |
| --- | --- | --- |
| Which candidate answered? | Answer contains candidate/report/decision digests and correlation id | One candidate per request |
| Why was activation refused? | Structured `activation_refused` event with closed reason code and correlation id | No credentials, raw requests or wallet linkage |
| Did a switch or rollback finish? | Intent/completion records plus `status` pointer readback | Unfinished intent reconciled before next switch |
| Are requests failing or slowing? | Count/errors and duration histogram by operation and status class | p95/p99; no wallet, digest, URL or request-id metric labels |

Ephoros's review covers this question-to-signal specification. Emitted samples,
alert delivery and operating thresholds remain untested; the runtime owner
must exercise them before unattended operation. A critical refusal is a failed
admission, not an excuse to serve an unverified candidate.

The [headless handoff](https://github.com/wildcat-finance/skills/issues/1491#issuecomment-5650385997)
excludes frontend route inventories, reviewed workbooks and Dokimasia from this
integration. There is no reviewed workbook or UI guard in the selected tree.
#1409 remains an independent UI job and receives no completion claim from this
record. If a frontend is later selected, its maintainer must supply its own
repository/SHA, route/guard denominator and reviewed workbook.

#1389 implements build/query and immutable artefacts; #1392 implements replay
isolation; #1397 binds verification reports; #1405 implements promotion and
rollback; #1408 preserves coverage. Accepted source data, Wildcat mappings and
each parent's other prerequisites retain their own admission gates. This
input record closes none of those implementation or deployment obligations.
