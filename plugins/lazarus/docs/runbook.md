# Lazarus implementation runbook

<!-- marketplace-context:start -->
> **Marketplace context: Lazarus.** Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests. Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence. **Current frontier:** Receipt witnesses reconstruct receiptsRoot offline and prove one scoped receipt payload plus its consensus-log projection; transaction hashes and unrelated RPC results remain recorded evidence, while empty blocks still have no receipt-witness representation.
<!-- marketplace-context:end -->

This runbook builds the proof-checked, exact-request historical Ethereum
fixture selected in the Lazarus study. Branches stack in order under Fiat's
`chain` setting. Each step leaves the full repository test suite green and is
reviewed in its own pull request.

## Step 1: Scaffold the Lazarus plugin

**Goal.** Add the complete repository-facing plugin shell, pinned Python
toolchain, CI job and reviewed design documents without implementing capture
or replay.

**Entry.** `main` at `83fef6634a560860b930a532861dbfff8cbb3442`.

**Exit.** `plugins/lazarus/` has its runtime contract, canonical skill, host
manifests, agent metadata, MIT licence, package
shell, dependency pins and committed copies of this study and runbook. The
portable entrypoint, both marketplace manifests, root plugin inventory, root
instructions and a Lazarus CI workflow include the new plugin. `python3 -m
unittest discover -s tests` and `python3 -m unittest discover -s
plugins/lazarus/tests -t plugins/lazarus` pass.

**Files.** `plugins/lazarus/{AGENTS.md,LICENSE,README.md,requirements.txt}`,
`plugins/lazarus/.claude-plugin/plugin.json`,
`plugins/lazarus/.codex-plugin/plugin.json`,
`plugins/lazarus/docs/{study.md,runbook.md}`,
`plugins/lazarus/scripts/lazarus_lib/{__init__.py,version.py}`,
`plugins/lazarus/skills/lazarus/{SKILL.md,README.md,agents/openai.yaml}`,
`plugins/lazarus/tests/{__init__.py,support.py,test_scaffold.py}`,
`.agents/skills/lazarus/SKILL.md`, `.agents/plugins/marketplace.json`,
`.claude-plugin/marketplace.json`, `.github/workflows/lazarus.yml`,
`AGENTS.md`, `README.md` and `tests/test_portable_skills.py`.

**Tests.** Add scaffold tests for manifest parsing, skill/readme identity,
portable routing, documented entrypoints and version pins. Extend the root
portable-skill inventory to cover Lazarus.

## Step 2: Define deterministic fixtures and manifests

**Goal.** Implement the versioned plan, header, RPC-record, proof-record and
manifest formats with deterministic encoding, safe paths and digest checking.

**Entry.** The pushed tip of `step-1-scaffold-the-lazarus-plugin`.

**Exit.** The library validates the built-in JSON Schemas, rejects duplicate
keys and unsafe paths, writes canonical JSON and JSONL, derives exact request
keys, builds a manifest from confined components and verifies every component
length and SHA-256 digest. `python3 -m unittest discover -s
plugins/lazarus/tests -t plugins/lazarus` passes without network access.

**Files.** `plugins/lazarus/schemas/{plan-v1.json,header-v1.json,rpc-record-v1.json,proof-record-v1.json,manifest-v1.json}`,
`plugins/lazarus/scripts/lazarus_lib/{canonical.py,errors.py,paths.py,schemas.py,records.py,manifest.py}`,
`plugins/lazarus/scripts/lazarus.py`, and
`plugins/lazarus/tests/{test_canonical.py,test_paths.py,test_schemas.py,test_records.py,test_manifest.py}`.

**Tests.** Cover stable bytes across insertion order and repeated builds,
request-key exactness, quantity and address validation, duplicate-key
rejection, traversal, absolute paths, symlinks, digest and size mismatches,
unknown schema versions, extra files and resource limits.

## Step 3: Verify headers, accounts, storage and code

**Goal.** Add offline Ethereum block-header and EIP-1186 account/storage proof
verification with explicit proof-backed and recorded-evidence boundaries.

**Entry.** The pushed tip of `step-2-define-deterministic-fixtures-and-manifests`.

**Exit.** `lazarus verify <fixture>` recomputes the fork-appropriate header
hash, verifies account inclusion and absence against `stateRoot`, verifies
storage inclusion and absence against each proved storage root, compares
response fields with decoded leaves, and checks captured code against the
proved `codeHash`. The command reports evidence counts separately and fails
on any mutation. The plugin test suite passes offline.

**Files.** `plugins/lazarus/scripts/lazarus_lib/{hexvalue.py,rlp.py,trieproof.py,header.py,proofs.py,verifier.py}`,
`plugins/lazarus/tests/fixtures/execution-api/`, and
`plugins/lazarus/tests/{test_hexvalue.py,test_rlp.py,test_trieproof.py,test_header.py,test_proofs.py,test_verifier.py}`.

**Tests.** Import compact EIP-1186 vectors and add mutations for every proof
node, malformed and overlong RLP, bad compact paths, embedded versus hashed
nodes, empty accounts, zero slots, mismatched keys, values wider than 256 bits,
wrong state roots, wrong block hashes and code substitutions.

## Step 4: Capture a finite plan safely

**Goal.** Implement the capture CLI which resolves one fixed block, records
declared RPC calls, verifies required proofs before writing and excludes
provider secrets.

**Entry.** The pushed tip of `step-3-verify-headers-accounts-storage-and-code`.

**Exit.** `lazarus capture --plan <plan> --rpc-url <url> --out <directory>`
resolves and brackets the named block, prefers EIP-1898 hash selectors, records
required and optional requests, verifies proofs and code, sanitises failures,
writes one deterministic fixture and fails without leaving a valid-looking
partial result. A local fake RPC integration test proves the complete path;
the plugin test suite passes offline.

**Files.** `plugins/lazarus/scripts/lazarus_lib/{rpc.py,capture.py,scrub.py,limits.py}`,
`plugins/lazarus/tests/{fake_rpc.py,test_rpc.py,test_capture.py,test_scrub.py,test_limits.py}`,
and the Step 2 schemas where capture-only constraints require an additive
clarification.

**Tests.** Cover fixed number and expected-hash resolution, rejected effective
tags, header equivocation, EIP-1898 fallback, required and optional failures,
proof rejection before finalisation, out-of-order responses, time and byte
limits, interrupted writes, URL userinfo, query keys, bearer headers, cookies
and provider errors containing secrets.

## Step 5: Replay exact requests and fail closed

**Goal.** Serve a verified fixture over loopback JSON-RPC with exact matching,
no provider client and a stable miss protocol.

**Entry.** The pushed tip of `step-4-capture-a-finite-plan-safely`.

**Exit.** `lazarus replay <fixture>` verifies before binding, answers captured
single and batch requests with each caller's own JSON-RPC identifier, handles
notifications, rejects write methods and returns error `-32070` plus a capture
plan fragment for an exact miss. The process has no provider or fallback
configuration. Socket-blocked tests prove a miss cannot leave loopback, and
the plugin suite passes offline.

**Files.** `plugins/lazarus/scripts/lazarus_lib/{replay.py,server.py}`,
`plugins/lazarus/tests/{test_replay.py,test_server.py,test_no_network.py}`, and
`plugins/lazarus/README.md` for the verified local replay command.

**Tests.** Cover request-object key reordering, exact value preservation,
caller IDs, notifications, mixed batches, malformed JSON-RPC, unsupported and
write methods, fixtures that fail verification, stable miss payloads,
concurrent reads, loopback binding and blocked outbound sockets.

## Step 6: Ship and run the Aave v4 demonstration

**Goal.** Prove the prototype with a checked-in, offline-verifiable Aave v4
fixture and an application test using ordinary JSON-RPC.

**Entry.** The pushed tip of `step-5-replay-exact-requests-and-fail-closed`.

**Exit.** `plugins/lazarus/examples/aave-v4-spoke-v0/` contains the fixed plan,
captured header, proof-backed account/code/slot data, the named transaction
receipt, a small log query, schemas and manifest. Its demo script verifies the
fixture, starts replay, reads the committed code, slot, receipt and logs,
observes a miss for slot `0x1`, rejects a one-nibble proof mutation and rebuilds
the same manifest bytes and digests. `python3
plugins/lazarus/examples/aave-v4-spoke-v0/demo.py` and every repository check named
in root `AGENTS.md` pass.

**Files.** `plugins/lazarus/examples/aave-v4-spoke-v0/{README.md,plan.json,header.json,rpc.jsonl,proofs.jsonl,manifest.json,demo.py}`,
`plugins/lazarus/examples/aave-v4-spoke-v0/schemas/`,
`plugins/lazarus/tests/test_aave_v4.py`, `plugins/lazarus/README.md`,
`README.md` and `specs/lazarus.md`.

**Tests.** Add the end-to-end demo test, byte-for-byte rebuild check, replay
miss assertion, proof mutation failure, no-network guard and repository-wide
regression run. Record exact test totals at implementation time.
