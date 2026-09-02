# Lazarus study

<!-- marketplace-context:start -->
> **Marketplace context: Lazarus.** Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests. Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence. **Current frontier:** Receipt witnesses reconstruct receiptsRoot offline and prove one scoped receipt payload plus its consensus-log projection; transaction hashes and unrelated RPC results remain recorded evidence, while empty blocks still have no receipt-witness representation.
<!-- marketplace-context:end -->

## Problem statement

Lazarus captures the finite part of historical Ethereum state that one
application test reads, verifies every claim that can be checked against the
named block, and serves the captured JSON-RPC responses from a local process.
It is for protocol engineers, researchers and security reviewers whose tests
currently depend on an archive RPC URL and a block number. The fixture must
remain useful when that endpoint, credential or protocol front end no longer
exists.

The central distinction is between three evidence classes:

1. **Proof-backed state:** an account or storage value checked through an
   `eth_getProof` Merkle Patricia proof against the `stateRoot` in the captured
   block header. Contract code is checked against the proved `codeHash`.
2. **Header-bound data:** block fields whose encoding and hash are checked
   locally. This proves internal consistency with the named header, but not by
   itself that the header belongs to Ethereum's canonical chain.
3. **Recorded RPC evidence:** a provider response such as `eth_call`,
   `eth_getLogs`, a receipt or a client trace. Lazarus preserves and replays
   these bytes under the exact request that produced them without upgrading
   them into a state-proof claim.

A working prototype will ship as `plugins/lazarus` and will:

- accept an explicit capture plan naming Ethereum mainnet, one finalised block,
  exact JSON-RPC requests, accounts and storage slots;
- resolve the block once, reject `latest` and `pending` in the effective plan,
  and store its full header, number, hash, parent hash and state root;
- record exact method, parameter, result or sanitised error triples;
- request `eth_getProof` for every declared account and slot, verify account,
  storage and non-existence proofs offline, and verify captured code against
  the proved code hash;
- write deterministic, schema-checked files whose component SHA-256 digests
  are bound by a manifest;
- start a local JSON-RPC replay server that answers only exact captured
  requests and returns a documented error containing the missing method and
  parameters for every miss; and
- verify and replay with network access disabled and without the capture URL.

The demonstration lives at `plugins/lazarus/examples/aave-v4-spoke-v0/`. Its plan
uses the Ethereum mainnet Aave v4 market
`0x973a023a77420ba610f06b3858ad991df6d85a08`, already named by the first row
of Tabularium's checked-in Aave v4 release. It captures the account proof,
contract code, storage slot `0x0`, the cited transaction receipt
`0xdaa7ebd15335bf809ee414876846df98d40736e7d29e3eeaca8b434653b9313e`,
and a small log query at the fixed fixture block. The demo check is:

1. verify the checked-in fixture offline;
2. start the replay server;
3. run an application test which reads the captured code, slot, receipt and
   logs through ordinary JSON-RPC and obtains the committed answers;
4. request slot `0x1` and observe a Lazarus miss rather than `0x0` or a network
   request;
5. change one proof nibble and observe verification fail; and
6. rebuild the manifest from the same captured files and obtain identical
   bytes and digests.

The Aave v4 address is a concrete replay subject, not a claim that slot
`0x0` has a particular business meaning. Interpreting Aave v4 storage is
outside this first test. The chosen reading of "replay" is exact request replay,
not arbitrary EVM execution from a partial world state. Exact replay is enough
to remove the original RPC from an application test and makes the finite
coverage boundary observable. Flexible local execution can follow once the
fixture format and proof verifier are stable.

## Prior art

### In this repository

- `specs/lazarus.md` defines the intended gates: declared capture scope,
  block-hash identity, exact proof claims, missing-data failure, secret
  removal, deterministic rebuilding and finite coverage. Lazarus is still an
  unbuilt specification on the starting ref.
- `specs/preservation-runbook.md` places Lazarus between an archive node and a
  published preservation release. It says state-derived values need
  `eth_getProof` while events remain source records. It names Aave v4 as the
  first preservation case.
- `plugins/tabularium/examples/aave-v4-spoke-v0/` is a complete offline-verifiable
  event release with 34 borrow rows and 477 repay rows. Its
  `coverage.json` names the exact gap Lazarus should close: block 25,764,670 is
  reported by a hosted indexer, individual events lack independently checked
  block identities, and no state proof accompanies derived values. Its
  deterministic JSONL, relative-path confinement, component digests and
  coverage reporting are the local format precedent.
- `plugins/ariadne/scripts/ariadne_lib/` supplies local precedents for safe
  JSON handling, path confinement, SHA-256 subjects, scrubbing and offline
  verification. `specs/ariadne.md` reserves a future state-fixture predicate
  with the block hash, ancestry, accounts, slots and a separation between
  proof-backed and merely recorded values. Lazarus should produce the subject
  that predicate will later bind; it should not implement signing itself.
- `plugins/probitas/` shows the repository's failure and coverage style. Its
  live adapters never turn an unavailable source into a clean record, while
  its tests use network-free fixtures. The Lazarus replay miss should be just
  as visible.
- Root `AGENTS.md` and `tests/test_portable_skills.py` define the plugin shape:
  a canonical `SKILL.md`, portable entrypoint, plugin
  contract, Claude and Codex manifests, marketplace entries and tests.

The branch `codex/mnemosyne-synthesis` at `0d929a0` contains
`specs/mnemosyne.md`, an unmerged integration draft. It keeps Lazarus,
Tabularium and Ariadne as separate verifiers and says a combined release must
retain each component's claim boundary. The draft is useful prior art but is
not part of `main` and is not a dependency of this build.

The recovered OpenCode archive session
`ses_ff5057204ffe26V8p4QM5Kh9PL`, titled "Lazarus prior-art spike research",
contains the unfinished research run shown by the user. It had collected much
of the Foundry, EELS, tracing, proof and Aave v4 evidence below but had not
produced a final report. Every technical conclusion from that archive was
checked again against the named source before inclusion here.

### In the wider organisation

- The prototype was built in `laurenceday/wildcat-skills-todo` before being
  reviewed and published here in `wildcat-finance/skills`.
- Wildcat protocol tests use Foundry forks for historical integration. Their
  practical need is the application boundary Lazarus serves: a small set of
  calls and storage reads, not an exported Ethereum database.
- Tabularium and Probitas already expose the cost of endpoint loss. Aave v4
  wound down, its checked-in source came from a served Graph deployment, and
  the release records that hosted indexer's block as a limitation. Lazarus can
  preserve the state reads a later release cannot derive from logs.

### Outside the organisation

#### EIP-1186 and the execution API

EIP-1186 and `ethereum/execution-apis` define `eth_getProof`. The result has
`address`, `accountProof`, `balance`, `codeHash`, `nonce`, `storageHash` and
`storageProof`. Each storage entry has `key`, `value` and `proof`.
`accountProof` and each storage proof are lists of hex-encoded RLP trie nodes.
The account path is `keccak256(address)` under the block's state root. A
storage path is `keccak256(left_pad_32(slot))` under the account's proved
storage root. Non-existence is a proof result too; it must not be inferred
from a missing object.

The execution API repository carries runnable vectors at
`tests/eth_getProof/`, including `get-account-proof-with-storage.io` and a
block-hash request. These are better interoperability tests than the original
EIP's illustrative example. Historical availability remains a node or
provider capability: the API specifies the request shape, not how long a node
retains old state. Capture should probe the chosen block and record a
capability failure rather than describe every public RPC as archive-capable.

EIP-1898 permits block-hash selectors, including `requireCanonical`, for
state-query methods. Lazarus should prefer a block-hash selector where the
provider implements it. Providers vary, so the fallback is a fixed block
number bracketed by header reads that must return the same expected hash.

#### Foundry fork caches and Anvil state

Foundry is the closest practical neighbour. At Foundry commit
`3c16e2361f18f2cecc975e1d5a8d17330d92ced7` and `foundry-core` commit
`8b3ea9453789ba0d9d8ebf0fc4ee0fed9e4add8f`, fork cache paths are rooted at
`~/.foundry/cache/rpc/<chain>/<block>/`. The JSON database serialises
`meta`, `accounts`, `storage` and `block_hashes`; newer builds can write the
JSON through zstd. Storage is an address map whose entries are hex slot-to-hex
value pairs. Recent Anvil code also supports endpoint-specific files named
`storage-<keccak256(rpc-url)>.json`, resolves a fork block hash during startup,
and keeps block hashes in the database.

This is a cache, not a released proof bundle. `foundry-fork-db` documents and
implements the decisive behaviour: on an account, slot or block-hash miss,
`SharedBackend` schedules a request to the provider and writes the response
back to the cache. The cache metadata carries a block environment and hosts,
but cached account and slot values are not accompanied by EIP-1186 proofs
against the header state root. A warmed cache may let a particular test run
without fetching, but completeness is implicit and a new read follows the
provider path. Anvil's dump/load state is useful for reproducible local nodes,
but it likewise represents local state rather than a finite, proof-labelled
application capture. Lazarus should borrow the ergonomics, not declare a
Foundry cache verified or complete.

#### Execution-specification fixtures

`ethereum/execution-specs` and the associated execution test releases are
client-conformance material. State-test fixtures contain an execution
environment, a full pre-allocation, a transaction and expected post-state
roots and log hashes. Blockchain-test fixtures contain a pre-allocation,
genesis RLP and header, blocks, the last block hash and a post-allocation.
They let a client reconstruct tries from allocations and check consensus-
critical execution.

Those ordinary fixtures do not package EIP-1186 account and storage inclusion
proofs for an arbitrary historical application read. Newer fixture tooling
can optionally add an execution witness with `--witness`, but that witness is
generated for executing the test block and remains client-conformance input.
The formats and their release discipline are worth reusing as vectors; their
scope is not a replacement for an application capture plan.

#### Geth traces and prestate capture

Geth's default struct logger emits program counter, opcode, remaining gas, gas
cost, call depth and optionally memory, stack, return data and storage at each
step. `callTracer` emits nested call frames. `prestateTracer` records the
accounts and slots touched during execution and its diff mode records changed
state. Geth's own documentation says the prestate result contains trie leaves,
not cryptographic proofs.

`debug_traceCall` runs a call in a selected block context and returns the same
family of output as transaction tracing. Historical tracing may regenerate
state by re-executing blocks; Geth's `reexec` setting defaults to 128 and its
documentation shows historical regeneration taking minutes. Trace namespaces,
tracer names, defaults and encodings are not part of the stable `eth_` API and
can differ across clients. For the prototype, a trace is an exact recorded RPC
response carrying the client name, version, tracer and options. It cannot be
used as a cross-client canonical response or as proof of every value it
mentions.

#### Reth execution witnesses

Reth exposes `debug_executionWitness` and
`debug_executionWitnessByBlockHash`. Its documentation describes a map from
hashed trie nodes to the preimages needed to re-execute a whole block and
recompute its state root. This is stronger and broader than Geth's
`prestateTracer`, and it may later supply an import format. It is still a
block-execution witness, not a capture plan for an arbitrary set of
application calls, receipts and log ranges. Importing it in the first
prototype would add a second completeness model before the simpler one is
tested.

#### Hosted forks and node snapshots

Tenderly virtual testnets, provider simulations, archive RPC products, Anvil
forks, Reth databases and Erigon snapshots all preserve or expose historical
state in some form. Hosted forks retain an account and service dependency.
Client databases and snapshots are large, implementation-specific node
artefacts. Neither class gives the prototype's combination of a declared
finite request set, EIP-1186 proof labels, deterministic release bytes and an
exact local miss. They are capture sources and comparison targets, not the
fixture format.

## Constraints and non-goals

The original implementation started from `main` at
`83fef6634a560860b930a532861dbfff8cbb3442` in
`laurenceday/wildcat-skills-todo`. The worktree was clean when the study began,
and no Lazarus plugin existed on that ref.

The implementation must follow the target repository's plugin layout and
tests. Python should own the CLI, deterministic file writing and local HTTP
server, matching Ariadne, Probitas and Tabularium. Use Python 3.11 or newer.
The proof checker may use a small pinned Ethereum trie stack (`eth-hash` with a
Keccak backend, `rlp` and `trie`) rather than writing a new Keccak or Merkle
Patricia implementation. Pin and lock those packages, keep the verifier API
behind one module, and run all repository tests without a network once
dependencies are installed. Do not add Web3 merely to make JSON-RPC calls;
the standard library can send those requests.

Canonical output follows the existing repository convention: UTF-8, ASCII
schema keys, lexicographically sorted object keys, compact separators, no
floating-point values and one trailing newline for JSONL. Quantities are
validated as Ethereum hex quantities and converted to integers only for
bounded comparison. SHA-256 identifies fixture files and the fixture as a
release artefact; Keccak-256 remains the Ethereum trie and code hash.

The capture URL and headers are runtime inputs. They never enter the fixture,
diagnostics or digest material. Provider identity is limited to explicitly
safe metadata such as client family and version returned by an allowed probe.
URL user information, query strings, API keys, cookies and arbitrary provider
error text are scrubbed before anything is written.

The fixture accepts only a fixed block number and expected block hash in its
effective plan. Capture from a tag is allowed only as a convenience before
resolution; the stored plan contains neither `latest` nor `pending`. The
prototype supports Ethereum mainnet's current Merkle Patricia state trie. L2
state roots, Verkle-state formats, pre-Byzantium receipt differences and
chain-specific RPC extensions need separate profiles and are deferred.

The prototype does not:

- replace an archive node or capture unbounded state;
- execute arbitrary `eth_call` locally from partial state;
- infer which slots a dynamic call might read;
- prove logs or receipts against `receiptsRoot`;
- claim a block is canonical or final solely because its header hash is
  internally consistent;
- normalise one client's `debug_` or `trace_` result into another's;
- capture pending state, mempool contents, subscriptions or write methods;
- collect private keys, sign transactions or hold a signing key;
- silently use a live provider during replay;
- publish, sign or merge a Mnemosyne release;
- rewrite Tabularium's existing Aave v4 release; or
- provide a Foundry state backend in the first step.

The supported replay allowlist should begin with `eth_chainId`,
`eth_getBlockByHash`, `eth_getBlockByNumber`, `eth_getBalance`,
`eth_getTransactionCount`, `eth_getCode`, `eth_getStorageAt`, `eth_getProof`,
`eth_call`, `eth_getLogs`, `eth_getTransactionByHash` and
`eth_getTransactionReceipt`. A plan can store another read-only method as
recorded evidence, but the schema must label it unproved and preserve its exact
method and parameters. Write methods and subscriptions are rejected.

## Design options

### Option 1: bless the Foundry fork cache

Package a warmed `storage.json` with a wrapper that launches Forge or Anvil.
This is the shortest route to local EVM execution and matches the tests Wildcat
already runs. Completeness remains accidental, cache misses use the provider
path, values lack state proofs, the format follows Foundry internals and the
capture plan is not reviewable. Fixing those gaps would amount to building a
new layer around the cache.

### Option 2: deterministic RPC cassette with a proof bundle

Store an explicit plan, checked header, exact request-response records,
EIP-1186 proofs and a digest manifest. Verify the bundle offline and replay by
exact method-plus-parameters lookup. A miss is a JSON-RPC error and a suggested
plan entry; it never fetches. `eth_call`, logs, receipts and traces remain
labelled recorded evidence.

This is the selected construction. It has the lowest comprehension cost that
meets every prototype requirement. One format explains capture, evidence,
coverage and replay. A reviewer can inspect it with ordinary JSON tools. It
does less than a forked EVM, which is an advantage at this stage: the tool
cannot imply that uncaptured state was present.

The fixture layout should be:

```text
fixture/
  manifest.json       component digests, schema/tool versions, evidence counts
  plan.json           requested chain, block, methods, accounts and slots
  header.json         full header plus recomputed hash and state root
  rpc.jsonl           canonical exact request and result/error records
  proofs.jsonl        account/storage proofs and local verification results
  schemas/            pinned JSON Schemas used by this fixture version
```

The request key is SHA-256 over canonical JSON containing only `method` and
`params`; the caller's JSON-RPC `id` is never part of it. Replay copies the
caller's `id` into the response. JSON object member order is irrelevant after
canonicalisation, while array order, quantities, addresses, block selectors
and omitted fields remain exact. There is no convenience coercion between
`0x0`, `0x00`, decimal zero or `latest`.

### Option 3: rebuild a partial state database and execute calls in revm

Convert proved accounts, code and slots into a revm database and run arbitrary
calls against it. This gives useful Foundry-like behaviour and discovers a
miss when the EVM touches an absent slot. It also introduces hardfork
selection, block environment, precompiles, call overrides, block-hash history,
dynamic dependencies and client parity. A replay result becomes a new
calculation rather than the captured provider result. Build this later as a
consumer of the selected fixture, not as its first storage format.

### Option 4: package a client execution witness or node snapshot

Import a Reth execution witness, Erigon snapshot or other client database and
run a local execution client. This can support wider execution and stronger
block-level completeness. It is much larger, tied to a client and aimed at
block execution rather than one application's declared calls. It should be an
optional importer after Lazarus has a stable evidence model.

## Selected format and verification details

`plan.json` is both input and coverage contract. Each request has a stable
name, exact method and parameters, `required` flag and expected evidence class.
Proof targets are separate objects with an address and sorted unique 32-byte
slots. The effective plan records the resolved chain ID, block number and block
hash. Capture fails if two reads of the header disagree, if a required method
fails, if a returned object names another block, or if a proof does not verify.
An optional method failure is preserved as a sanitised error and counted in
the manifest.

For each account proof, verification must:

1. recompute the block header hash from its fork-appropriate RLP fields and
   compare it with the expected block hash;
2. traverse `accountProof` from the header `stateRoot` using
   `keccak256(address)`;
3. RLP-decode the account leaf as nonce, balance, storage root and code hash;
4. compare those values with the response fields;
5. traverse every storage proof from the proved storage root using
   `keccak256(slot32)` and compare its decoded value; and
6. Keccak-hash captured code and compare it with the proved code hash.

Proofs of absence must terminate according to trie rules and produce the
documented empty account or zero slot result. A missing proof node is an error,
not an absent account. Duplicate RLP nodes, malformed compact paths, overlong
RLP, values wider than 256 bits and a response whose `key` differs from the
planned slot all fail.

`manifest.json` records schema version, tool version, plan and block identity,
component byte lengths and SHA-256 digests, counts by evidence class, failed
optional requests and the overall fixture digest. It cannot hash itself.
Define the fixture digest as SHA-256 over canonical JSON containing the
manifest's versioned identity fields and the sorted list of component path,
byte length and digest triples. All paths are relative, slash-normalised,
confined beneath the fixture root and forbidden from being symlinks.

The replay server reads only a fixture that has passed verification in the
same process. It binds loopback by default. It has no capture URL, proxy or
fallback configuration. On an exact miss it returns a stable server error,
for example code `-32070`, whose data contains canonical `method` and `params`
plus the plan fragment needed for a later recapture. Batch requests are
answered item by item; notifications produce no response. The server refuses
write methods even if a malformed fixture contains one.

## Risk register seed

- **False chain identity.** A provider can supply a self-consistent header and
  proof for a non-canonical fork. Recompute the header hash, require the user or
  plan to name the expected hash, record how it was obtained, and state that
  consensus finality remains external.
- **Provider equivocation during capture.** Number-based calls may cross a
  reorganisation or reach inconsistent backends. Resolve once, prefer
  EIP-1898 block-hash selectors, and bracket capture with the same header hash.
- **Proof-verifier errors.** RLP length handling, hex-prefix paths, embedded
  versus hashed trie nodes, empty accounts and zero slots are easy to get
  wrong. Use a pinned trie library, execution-apis proof vectors, independent
  negative vectors and mutation tests over every proof node.
- **Code substituted for a proved hash.** `eth_getProof` proves `codeHash`, not
  code bytes. Always hash `eth_getCode` locally and fail on a mismatch.
- **Recorded evidence described as proof.** Logs, receipts, calls and traces do
  not become state proofs because they share a fixture with one. Evidence class
  is required on every record and the verifier reports counts separately.
- **Request-key collision or over-normalisation.** Address case, omitted
  parameters, quantity encoding and block tags can change method semantics.
  Canonicalise JSON syntax only, keep values exact, store the canonical request
  beside its digest and compare both on lookup.
- **Silent provider access.** A library proxy, environment variable or replay
  helper could route a miss to the network. The replay process has no provider
  client, tests run with sockets blocked except loopback, and a miss test
  asserts no outbound connection was attempted.
- **Incomplete dynamic calls.** Exact `eth_call` replay says nothing about a
  different calldata value or a later implementation which tries to execute
  from partial state. Keep call replay exact and defer EVM execution until a
  state-access discovery and miss protocol exists.
- **Client-dependent traces.** Geth, Reth, Erigon and hosted providers may emit
  different trace shapes or defaults. Record client, version, method and full
  options; treat the response as opaque recorded evidence.
- **Secret disclosure.** RPC URLs and provider errors may contain credentials.
  Use an allowlist for persisted metadata, scrub error strings, test userinfo,
  query, header and bearer-token cases, and scan every output file before
  finalisation.
- **Path and parser attacks.** A downloaded fixture is untrusted. Reject
  absolute paths, traversal, symlinks, duplicate JSON keys, oversized fields,
  excessive nesting, invalid UTF-8 and unexpected files before reading proof
  material.
- **Resource exhaustion.** Logs, traces and proof arrays can be large. Plans
  declare request and component byte limits; capture streams JSONL; verification
  applies limits before allocation.
- **Arithmetic and encoding drift.** Ethereum quantities are unsigned 256-bit
  values, while JSON numbers and Python integers have different rules. Accept
  canonical hex quantities at the boundary, reject negative or over-wide
  values, never use floating point, and test leading-zero rejection.
- **Nondeterminism.** Wall-clock time, request completion order, dictionary
  order, host paths and server-generated IDs can change bytes. Sort all records
  by request key or proof target, keep capture time outside deterministic
  identity or require it as explicit input, and own every serialisation rule.
- **Schema substitution.** A fixture could carry a permissive schema chosen by
  an attacker. The verifier selects schemas by a built-in version registry and
  then checks that bundled schema bytes match the registered digest.
- **Correction and upgrade confusion.** A new schema or verifier could reinterpret
  an old fixture. Unknown major versions fail; old verifiers remain available;
  corrections produce new fixture IDs and name the superseded digest.
- **Key custody.** The prototype holds no signing or transaction key. Future
  Ariadne signing stays an external operation, and an unsigned fixture receives
  no publisher identity claim.

## Glossary seeds

- **Capture plan:** the versioned list of chain, block, requests, proof targets,
  limits and allowed omissions fixed before collection.
- **Effective plan:** the capture plan after a tag has been resolved to one
  block number and expected hash.
- **Fixture:** the complete digest-bound directory containing plan, header,
  records, proofs, schemas and manifest.
- **Request record:** one exact JSON-RPC method-plus-parameters pair and its
  result or sanitised error.
- **Request key:** SHA-256 of the canonical JSON object containing a method and
  its exact parameters.
- **Proof target:** one account address and the finite set of storage slots
  whose EIP-1186 proofs the plan requires.
- **Proof-backed state:** a value whose trie proof verifies against the captured
  header's state root.
- **Header-bound data:** data checked against the captured header without an
  external proof that the header is canonical.
- **Recorded RPC evidence:** an exact provider response preserved without a
  stronger cryptographic claim.
- **Replay:** serving an exact recorded result for an exact captured request.
- **Replay miss:** the explicit error returned when no exact request key exists.
- **Coverage:** the set of requests and proof targets answered, failed or
  omitted relative to the plan.
- **Capability failure:** a sanitised record that the provider did not support
  or could not serve a planned optional method at the chosen block.
- **Fixture digest:** the SHA-256 identity derived from versioned manifest
  fields and the sorted component digest list.
- **Chain anchor:** evidence outside the fixture used to decide whether its
  internally checked block hash belongs to the intended canonical chain.
- **State witness:** the trie nodes and state needed to execute a transition;
  broader than Lazarus's first exact-request fixture.

## Sources

### Prototype repository and archived research

- `laurenceday/wildcat-skills-todo`, starting commit
  `83fef6634a560860b930a532861dbfff8cbb3442`: `specs/lazarus.md`,
  `specs/preservation-runbook.md`, `specs/ariadne.md`,
  `plugins/tabularium/examples/aave-v4-spoke-v0/`, `plugins/ariadne/`,
  `plugins/probitas/`, root `AGENTS.md` and `tests/test_portable_skills.py`.
- Unmerged local/remote branch `codex/mnemosyne-synthesis`, commit `0d929a0`:
  `specs/mnemosyne.md` and `mnemosyne/README.md`.
- OpenCode database session `ses_ff5057204ffe26V8p4QM5Kh9PL`, "Lazarus
  prior-art spike research". It is a research trail, not an authority; the
  sources it identified are listed below.

### Ethereum specifications and vectors

- EIP-1186, `eth_getProof`:
  `https://eips.ethereum.org/EIPS/eip-1186`.
- EIP-1898, block-hash selectors:
  `https://eips.ethereum.org/EIPS/eip-1898`.
- Ethereum execution APIs, state methods and account-proof schema:
  `https://github.com/ethereum/execution-apis/blob/main/src/eth/state.yaml`
  and `src/schemas/state.yaml`.
- Execution API proof vectors:
  `https://github.com/ethereum/execution-apis/tree/main/tests/eth_getProof`,
  especially `get-account-proof-with-storage.io` and
  `get-account-proof-blockhash.io`.
- Ethereum execution-specification fixture documentation:
  `https://github.com/ethereum/execution-specs/blob/forks/amsterdam/docs/running_tests/test_formats/state_test.md`
  and `blockchain_test.md`.
- Execution-specification release and generation entrypoints:
  `https://github.com/ethereum/execution-specs` and
  `docs/library/execution_testing_fixtures.md`.
- JSON-RPC 2.0: `https://www.jsonrpc.org/specification`.
- JSON Schema 2020-12: `https://json-schema.org/draft/2020-12`.
- RFC 8785, JSON Canonicalization Scheme, consulted as comparison material:
  `https://www.rfc-editor.org/rfc/rfc8785`.

### Clients and developer tools

- Foundry commit `3c16e2361f18f2cecc975e1d5a8d17330d92ced7`:
  `crates/config/src/lib.rs`, `crates/evm/core/src/fork/database.rs`,
  `crates/evm/core/src/fork/multi.rs` and `crates/anvil/src/config.rs`.
- `foundry-core` commit `8b3ea9453789ba0d9d8ebf0fc4ee0fed9e4add8f`:
  `crates/fork-db/src/cache.rs` and `crates/fork-db/src/backend.rs`.
- Foundry Anvil overview and state-management pointer:
  `https://getfoundry.sh/anvil/`.
- Geth built-in tracers:
  `https://geth.ethereum.org/docs/developers/evm-tracing/built-in-tracers`.
- Geth debug namespace, `debug_traceCall` and `reexec`:
  `https://geth.ethereum.org/docs/interacting-with-geth/rpc/ns-debug`.
- Reth debug RPC, execution witnesses:
  `https://reth.rs/jsonrpc/debug/` and
  `https://reth.rs/docs/reth_rpc_api/clients/trait.DebugApiClient.html`.
