# Study: structured multi-provider chain anchors

Assuming, unless corrected:

1. Issue [#386](https://github.com/wildcat-finance/skills/issues/386) is a
   generation job. It must leave Lazarus's `receipt-inclusion-proofs` frontier,
   its held `lazarus-next` job, and their digest unchanged.
2. "Independent providers" is an operator assertion represented by distinct
   source identifiers. Lazarus can record separate answers; it cannot establish
   that two URLs have separate operators, infrastructure, upstream clients, or
   failure domains.
3. The requested count is a separately named chain-anchor-record count. It is
   not a fourth proof class and does not increase `proof_backed`,
   `header_bound`, or `recorded_rpc`.
4. A declared anchor source is required. A transport failure, malformed answer,
   wrong chain, wrong block number, or hash disagreement aborts the staged
   capture, matching the existing primary-provider rule.
5. Existing plan-v1 fixtures and the shipped Aave v4 release remain valid
   without byte changes. The extension uses new versioned documents rather than
   editing a released v1 schema in place.

## 1. Problem statement

Lazarus currently stores `plan.block.hash_source` as prose and verifies only
that one captured header is internally self-consistent. A fixture therefore has
no structured place for the block-hash answers obtained from other providers at
capture time. Protocol engineers preserving a historical fixture need those
answers retained with the fixture while keeping their evidence class honest.

A working prototype does all of the following:

- a plan declares between 1 and 32 opaque anchor source identifiers;
- `capture` resolves an exact runtime URL for every declared identifier through
  an explicitly named environment variable, queries each source for Ethereum
  mainnet chain ID and the fixed block, and writes no URL, credential, request
  header, or raw provider error;
- successful capture writes a digest-bound `anchors.jsonl` whose records name
  the source identifier, local observation time, exact method and parameters,
  returned chain ID, block number, and block hash;
- `verify` recomputes exact plan-to-record coverage and prints
  `chain-anchor-records: N` while retaining `canonical_chain_claim: false` and
  `provider_independence_claim: false`; and
- any missing, extra, duplicate, malformed, cross-chain, wrong-height, or
  disagreeing record is refused offline, while a failed live anchor query leaves
  no final fixture.

The proving paths are:

```bash
python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -v
python3 plugins/lazarus/scripts/lazarus.py verify <anchored-fixture>
python3 plugins/lazarus/scripts/lazarus.py verify \
  plugins/lazarus/examples/aave-v4-spoke-v0
```

The first command must cover capture, schema, manifest, verification, secret,
resource-limit, and compatibility cases. The second must print the structured
count. The third must keep the existing fixture's digest and three evidence
counts unchanged.

## 2. Prior art

### Repository state

- `plugins/lazarus/schemas/plan-v1.json` requires an unstructured
  `block.hash_source` and has no provider inventory.
- `plugins/lazarus/scripts/lazarus_lib/capture.py` brackets a capture with two
  reads from one primary provider, requires its chain ID and block hash to match
  the plan, stages all output, scans staged bytes for provider secrets, and
  finalises atomically only after `verify_fixture` succeeds.
- `plugins/lazarus/scripts/lazarus_lib/manifest.py` digests every listed
  component and recomputes three evidence counts from recognised formats.
- `plugins/lazarus/scripts/lazarus_lib/verifier.py` performs a second bounded
  read of digest-bound components, reports one header-bound header, and fixes
  `canonical_chain_claim` at `false`.
- `plugins/lazarus/scripts/lazarus_lib/rpc.py` already supplies redirect refusal,
  bounded responses, JSON-RPC shape checks, and sanitised transport failures.
- `plugins/lazarus/scripts/lazarus_lib/scrub.py` derives provider secrets from
  URLs and headers and refuses any such byte found in the staged fixture.
- `plugins/lazarus/scripts/lazarus_lib/release.py` and
  `plugins/lazarus/schemas/release-v1.json` bind only the existing three evidence
  counts. An anchor component is still protected by the fixture digest without
  becoming an Ariadne predicate claim.

### Merged work and carried-forward evidence

The last two merged domain pull requests were read in full:

- [#227](https://github.com/wildcat-finance/skills/pull/227) shipped the
  preservation release. Its carried boundary is that counts must be recomputed
  from verified bytes, every stated field must be read, paths and refusals must
  be bounded, one verification pass must supply one coherent report, and no
  release may claim canonical-chain membership.
- [#59](https://github.com/wildcat-finance/skills/pull/59) introduced the
  audited capture, verifier, and exact replay plugin. Its carried boundary is
  that capture is the only provider-backed operation, credentials never enter a
  fixture, state-proof-backed and recorded evidence remain separate, and replay
  has no live fallback.

The two most recent repository pull requests that physically touched Lazarus
surfaces were also checked. [#596](https://github.com/wildcat-finance/skills/pull/596)
refreshed collective documentation, and
[#577](https://github.com/wildcat-finance/skills/pull/577) propagated the root
Promise Machine contract. Neither body carries unfinished Lazarus product work
into #386.

The in-scope historical audit is the `Aave v4 preservation release` sequence
in `audit/AUDIT.md` (21 rounds across five steps, as recorded by #227). The
relevant findings and guards are retained here: refuse fields that are present
but unread; cap both input and diagnostic size; protect against symlink and
path races; derive counts rather than trust manifests; keep one coherent
verification read; preserve exact failure boundaries; and leave
`canonical_chain_claim` false. The issue-386 audit path
`audit/rounds/fiat-386-record-a-structured-multi-provider-chain-anc.md` does not
exist yet, so it carries no prior finding.

### Organisation and external standards

Issue #386 names Tabularium's unproved-chain-boundary language and Ariadne's
fixture predicate as neighbouring work. This run consumes that boundary but
does not change either sibling. The Ethereum Execution APIs specification for
[`eth_getBlockByNumber`](https://ethereum.github.io/execution-apis/api/methods/eth_getBlockByNumber/)
defines a fixed quantity plus `false` as the block query used here.
[EIP-1474](https://eips.ethereum.org/EIPS/eip-1474) and EIP-1898 distinguish a
provider's canonicality check from proof of global canonical-chain membership.
Several agreeing JSON-RPC answers are corroborating recorded observations, not
a consensus proof.

## 3. Constraints and non-goals

The run started from `main` at
`0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`. Lazarus supports CPython 3.11 and
newer and CI runs 3.11 and 3.13 using
`plugins/lazarus/requirements.lock`. No dependency addition is needed. The
current skill label is `lazarus-v1.1.0`; under
`plugins/hexaemeron/skills/VERSIONING.md`, this meaningful non-frontier behavior
change becomes generation `lazarus-v1.2.0`, retaining the existing frontier
revision, digest, status, and held job byte for byte.

Constraints:

- accept old plan-v1 fixtures and releases unchanged;
- use a plan-v2 schema for declared source identifiers and an
  anchor-record-v1 schema for stored answers;
- preserve the existing manifest-v1 three-class `evidence_counts` shape;
- keep anchor URLs and headers runtime-only, keep their values out of argv, and
  include their secrets in the final staged-tree scan;
- share the plan's request, byte, and elapsed-time limits across primary and
  anchor clients;
- sort sources and records by identifier so fixture bytes do not depend on CLI
  argument order; and
- use injected clients and clocks for tests, with no public RPC dependency in
  CI.

Non-goals:

- proving provider independence, Ethereum consensus, finality, or canonical
  membership;
- proving receipts or logs against `receiptsRoot`, which remains issue #383;
- replaying anchor queries through the exact-request replay server;
- changing Ariadne or Tabularium schemas, predicates, or claims;
- changing the package version, writer `tool_version`, existing released
  fixture bytes, or `manifest-v1.json`; and
- retaining failed captures or raw provider disagreements as a partial
  fixture.

Always: run the Lazarus and root Python suites before a commit; validate every
new schema and example; run Imprimatur on shipped prose; and re-run the
Aave v4 verification and preservation-release demonstrations. Ask first:
add a dependency, alter an existing v1 schema, touch CI, add optional/fail-open
anchor semantics, widen release or Ariadne claims, or rewrite a released
digest. Never: persist a provider URL, header, credential, or raw error; edit a
vendored tree; delete a failing test; claim source independence or canonical
membership; or report a command that did not run.

## 4. Design options and selection

### Option A: plan-v2 plus one optional anchor component

Add a plan-v2 document with a required, sorted, unique `anchor_sources` array
of 1 to 32 source identifiers. `capture` accepts repeated
`--anchor-rpc-env SOURCE_ID=ENV_VAR` mappings whose identifier set must equal
the plan, then reads each URL from only that named variable. It writes one
`anchors.jsonl` component under a new
anchor-record-v1 schema. Manifest v1 digests the component; verifier code
recognises it, checks coverage and reports its count outside `evidence_counts`.

Trade: this adds one plan version, one record format, and a runtime mapping
surface, but keeps old bytes and all three evidence-class interfaces stable.

### Option B: mutate plan-v1 and add a fourth manifest evidence count

Add optional provider fields to plan v1 and `chain_anchor` to
manifest/release evidence counts.

Trade: fewer new schema files, but it edits a released version in place,
changes fixture identity semantics, forces release and Ariadne reconciliation,
and invites readers to treat corroboration as a stronger evidence class.

### Option C: run a separate post-capture anchor command

Let `lazarus anchor` query providers after a fixture exists and rewrite its
manifest.

Trade: a simpler capture path, but the answers no longer share capture's block
bracket or atomic finalisation. It also rewrites an already verified fixture
and creates a second networked mutation path.

### Selected design

Choose Option A. It is the smallest construction that gives structured,
digest-bound, offline-verifiable records without changing existing evidence
classes or released formats.

The exact contract is:

1. Plan v2 copies plan v1 and adds `anchor_sources`, each containing only a
   `source_id` matching `^[a-z][a-z0-9_.-]{0,127}$`. The array is sorted,
   unique, and capped at 32. Plan v1 continues to mean no anchors.
2. `capture --anchor-rpc-env SOURCE_ID=ENV_VAR` splits only the first `=` and
   requires exactly one non-empty named environment variable for each declared
   identifier and no undeclared identifier. Environment values never enter
   argv, output, or diagnostics. The legacy primary `--rpc-url` is unchanged
   and is not inferred to be an independent anchor.
3. Each anchor client uses the existing transport and shared `CaptureLimits` to
   call `eth_chainId` and `eth_getBlockByNumber` with the plan's fixed quantity
   and `false`. Every result must name chain `0x1`, the fixed number, and the
   expected hash. Any failure aborts the staged capture.
4. Each anchor record stores only schema version, source identifier, a local
   UTC observation timestamp, method, parameters, returned chain ID, returned
   block number, and returned block hash. It stores neither URL nor response
   payload beyond those answer fields. The timestamp is recorded local-clock
   evidence, not provider attestation.
5. `anchors.jsonl` is present exactly when plan v2 declares sources. Records
   are sorted by `source_id`; their source set must exactly cover the plan.
6. `verify_manifest` schema-checks and digest-checks the optional component.
   `verify_fixture` reads it once through the manifest claim, rechecks exact
   coverage and header agreement, and returns
   `chain_anchors: {records: N, canonical_chain_claim: false, provider_independence_claim: false}`.
7. CLI `verify` prints `chain-anchor-records: N`. Existing
   `evidence_counts`, release-v1, and Ariadne binding fields remain unchanged.

## 5. Risk register seed

```risk-register
provider-secret | runtime primary URL, anchor environment values, headers, and provider failures | anchor URL values stay out of argv, no URL or raw error enters a record, and every provider secret is included in the staged-tree scan
provider-identity-overclaim | operator-chosen source identifiers | distinct identifiers are recorded assertions and no output claims separate ownership or infrastructure
canonicality-overclaim | several providers returning the expected hash | header-bound stays one, both anchor claim booleans stay false, and no anchor enters a proof-backed count
anchor-coverage | the join between plan source identifiers, runtime mappings, and stored records | missing, extra, duplicate, or reordered sources are refused and exact set equality is tested
provider-disagreement | an anchor provider returns another chain, height, or hash | capture aborts before finalisation and the minimal mismatch guard fails without that check
resource-exhaustion | up to 32 providers making network calls and returning hostile payloads | shared request, elapsed-time, component, response, and total-byte limits cover every anchor call and record
partial-write | capture interruption after some providers answer | anchors remain in the temporary stage and no destination exists until complete verification and atomic finalisation
schema-drift | new plan and record schemas plus the built-in digest registry | schema digests, semantic validators, fixture copies, and compatibility tests agree exactly
one-read-race | a component changing between manifest and semantic verification | anchor bytes are reread through their manifest size and digest claim and one report carries the resulting count
release-compatibility | an anchored fixture passing through release-v1 | the fixture digest binds anchors while release evidence counts and canonical-chain claims remain unchanged
```

## 6. Glossary seeds

- **Anchor source:** one operator-declared identifier mapped to one runtime RPC
  URL for this capture.
- **Anchor record:** the bounded stored answer from one declared source for the
  fixed block query.
- **Anchor count:** the number of structurally and semantically verified anchor
  records; not an independence, consensus, or canonicality score.
- **Primary provider:** the existing provider used for the header bracket,
  declared requests, and state proofs; not automatically an anchor source.
- **Recorded corroboration:** matching provider observations preserved as
  recorded evidence without a proof relation.
- **Canonical-chain claim:** a conclusion that the captured header belongs to
  Ethereum's canonical chain; always false in this run.

## 7. Sources

- Issue [#386](https://github.com/wildcat-finance/skills/issues/386), including
  its generation boundary and named sibling handoffs.
- `plugins/lazarus/AGENTS.md` and
  `plugins/lazarus/skills/lazarus/{SKILL.md,EVOLUTION.md}`.
- `plugins/lazarus/schemas/{plan-v1.json,manifest-v1.json,release-v1.json}`.
- `plugins/lazarus/scripts/lazarus.py` and
  `plugins/lazarus/scripts/lazarus_lib/{capture,manifest,verifier,rpc,scrub,schemas,release,binding}.py`.
- `plugins/lazarus/tests/` and the checked-in Aave v4 fixture and release.
- `plugins/lazarus/docs/{study.md,runbook.md,preservation-release.md}` and
  `docs/lazarus-aave-v4-preservation-release/`.
- `audit/AUDIT.md`, especially `Aave v4 preservation release` steps 1 to 5.
- Merged pull requests [#59](https://github.com/wildcat-finance/skills/pull/59),
  [#227](https://github.com/wildcat-finance/skills/pull/227),
  [#577](https://github.com/wildcat-finance/skills/pull/577), and
  [#596](https://github.com/wildcat-finance/skills/pull/596).
- [Ethereum Execution APIs: `eth_getBlockByNumber`](https://ethereum.github.io/execution-apis/api/methods/eth_getBlockByNumber/)
  and [EIP-1474](https://eips.ethereum.org/EIPS/eip-1474).
- `plugins/hexaemeron/skills/{protasis,phylax,ephoros,metron,elenchus,hypomnema}/SKILL.md`
  and `plugins/hexaemeron/skills/VERSIONING.md`.

## 8. Signals and their questions

This is a bounded CLI capture rather than a resident service, so Ephoros's
contract applies to deterministic command output and stable refusals, not a new
metrics backend.

- How many anchor sources were declared, queried, stored, and verified? Capture
  and verify expose the declared and verified record counts.
- Which source stopped capture, and at which bounded stage? Stable errors name
  the non-secret `source_id` and one of mapping, transport, chain, height, hash,
  schema, or coverage without echoing provider data.
- Did verification preserve the epistemic boundary? The report and CLI retain
  both false claim booleans and the unchanged three evidence counts.
- Did the compatibility path move? The Aave v4 demo reports its existing
  digest and counts, while a focused anchored-fixture demo reports the new
  count.

The runbook must cite `hexaemeron:ephoros` for the implementation step that
adds these outputs and guard tests.

## 9. Boundaries per capability

Under `hexaemeron:phylax`, the new boundaries and controls are:

- **Plan to runtime mapping:** untrusted source identifiers and repeated CLI
  environment-name mappings are normalised, bounded, unique, required to match
  exactly, and resolve only the explicitly named non-empty variables.
- **Network transport:** each anchor URL uses the existing redirect-refusing,
  size-bounded JSON-RPC client and shared capture limits.
- **Provider response:** JSON-RPC envelopes, chain ID, block object, number,
  and hash are type-checked before any record is constructed.
- **Secret handling:** all primary and anchor secrets are collected before
  capture, raw errors are discarded, and the union is scanned against every
  staged component before finalisation.
- **Filesystem:** only canonical JSONL enters the existing confined staged
  directory; manifest size and digest bind it before semantic verification.
- **Evidence interpretation:** anchor records remain recorded observations,
  source independence stays an operator assertion, and canonical-chain status
  stays unknown.

## 10. Budget or its absence

There is no latency optimization claim, so `hexaemeron:metron` does not require
a before-and-after timing experiment. Provider latency is external and a wall
clock target would not isolate this change. Resource budgets do apply: at most
32 anchor sources, two planned calls per source, and the existing plan limits
for request count, elapsed seconds, component bytes, total fixture bytes, and
provider response bytes. Focused limit tests run with:

```bash
python3 -m unittest \
  plugins.lazarus.tests.test_capture \
  plugins.lazarus.tests.test_limits \
  plugins.lazarus.tests.test_records \
  plugins.lazarus.tests.test_verifier -v
```

Any implementation justified as faster must stop and add a Metron baseline
before that change.

## 11. Fail-closed posture

Capture stops before destination finalisation on an unsafe or duplicate runtime
mapping, unavailable declared source, redirect, timeout, oversized response,
malformed JSON-RPC envelope, wrong chain, missing block, wrong height, hash
disagreement, schema failure, secret scan hit, component mismatch, limit breach,
or failed whole-fixture verification. Offline verification stops on an absent or
unexpected anchor component, plan-record coverage drift, duplicate source,
non-canonical bytes, digest drift, or any anchor/header disagreement. It never
silently drops a source, reduces the count, or treats partial agreement as
success.

Under `hexaemeron:elenchus`, each failure found during implementation or audit
first receives a minimal test that reproduces the exact bad transition. The fix
must make that test green while the corresponding positive case remains green;
the full Lazarus suite then guards the cause. A test-only failure is reported as
such rather than used to claim the product was guarded.

## 12. Decisions and their homes

The expensive-to-reverse decisions are the plan-v2 source declaration, the
anchor-record-v1 bytes, the runtime mapping syntax, the refusal of partial
anchors, the separate count location, and the promise not to promote matching
answers. Their durable homes are:

- `docs/lazarus-multi-provider-chain-anchor/study.md` and `runbook.md` for the
  full rationale, rejected options, constraints, and build evidence;
- `plugins/lazarus/schemas/plan-v2.json` and `anchor-record-v1.json` for the
  public byte formats;
- `plugins/lazarus/docs/chain-anchors.md` for the operator contract, evidence
  boundary, runtime mapping, refusals, and examples;
- `plugins/lazarus/{README.md,AGENTS.md}` and
  `plugins/lazarus/skills/lazarus/SKILL.md` for discoverable command and promise
  surfaces; and
- `plugins/lazarus/skills/lazarus/EVOLUTION.md` for the single
  `lazarus-v1.2.0` generation row, with the prior frontier revision and digest
  unchanged.

Hypomnema decides during the prose phase whether the public-format choice also
needs a root ADR. Absent a repository-wide policy change, the focused study and
versioned schemas are the lower-complexity durable record.
