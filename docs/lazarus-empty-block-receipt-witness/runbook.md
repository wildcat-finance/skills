# Issue 1360 runbook: empty-block receipt witness

This runbook derives from the receipted study at SHA-256
`2a0640f9adebb2a9c0f0b1473f923d12623e07125b4aaa169d2f9068b46f8690`.
The immutable implementation baseline is synced `main` at
`3cc0ad7f521985e46cf29f364a20e19fa99b64dd`. Use Python `3.14.6` from
`.python-version`, keep the existing dependency locks, and preserve every
currently valid plan, witness, manifest, fixture, statement, and release byte.
No step adds a dependency, changes hosted CI, rewrites a released digest, or
widens the receipt proof into canonical-chain, provider-independence, or
transaction-hash evidence.

The selected construction keeps `plan-v3` and `receipt-witness-v1` and gives
each an exclusive empty shape beside the existing scoped shape. The empty path
accepts only a verified header with Ethereum's canonical empty trie root and a
named `eth_getBlockReceipts` result of `[]`; it derives exactly zero
`receipt_trie_proved` relations. Each step is one signed, audited pull request.

```design-lock
schema | protasis-design-evidence/v1
sha256 | fa6d30980eea45815f7acaff26247af282ef3c53a1618782a4bdf422467e80c8
candidate | shape-discriminated
```

## Step 1: Lock and guard the exclusive witness shapes

**Goal.** Commit the accepted specification, record the shape decision, and make the plan, witness, and core receipt verifier distinguish empty from scoped evidence without ambiguity.

**Entry.** Run branch `fiat/1360-empty-block-receipt-witness` at `3cc0ad7f521985e46cf29f364a20e19fa99b64dd`, with the study and design-lock digests above, the existing Lazarus and root suites green, and the repository's package manifests, dependency locks, CI workflow, and Apache-2.0 licence unchanged.

**Exit.** Tracked study and runbook copies under `docs/lazarus-empty-block-receipt-witness/` preserve the receipted facts with only relative links rebased. A new non-colliding Hypomnema-owned decision record states why the existing versions gain two mutually exclusive closed shapes. `plan-v3` accepts either the existing four-field scoped request or the one-field empty request. `receipt-witness-v1` accepts either the existing non-empty target/filter witness or header plus `receipts: []` with both scoped fields absent. Core receipt verification binds an empty array only to the verified header's canonical empty trie root, returns zero relations, and refuses mixed shapes or a non-empty root. The focused test records the Step 2 conformance report. Prove the exit with `python3 plugins/lazarus/scripts/lazarus.py validate schemas`, `python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -p 'test_empty_receipts.py' -v`, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/lazarus-empty-block-receipt-witness/study.md`, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/lazarus-empty-block-receipt-witness/runbook.md`, and `python3 scripts/run_checks.py`.

**Files.** Create `docs/lazarus-empty-block-receipt-witness/{study.md,runbook.md}`, one non-colliding `docs/decisions/ADR-NNN-empty-receipt-witness-shapes.md`, and `plugins/lazarus/tests/test_empty_receipts.py`; change `plugins/lazarus/schemas/{plan-v3.json,receipt-witness-v1.json}`, `plugins/lazarus/scripts/lazarus_lib/receipts.py`, and only the schema registry, receipt helpers, tests, generated portable copy, Promise Machine coverage, and Horos boundary entries mechanically required by those authored changes.

**Tests.** Add closed-shape schema cases; empty-root acceptance; non-empty-root refusal; mixed-shape refusal; zero-relation output; unchanged non-empty root, target, and log-projection behaviour; and bounded value-free diagnostics. Run the exact design resolver `python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -p 'test_empty_receipts.py' -v` and write its zero-exit `protasis-design-report/v1` result to `.hexaemeron/reports/conformance/shape-discriminated-nonempty-root-empty-witness-refused.json`. The step audit runner contract is test command `python3 plugins/lazarus/tests/run_empty_receipt_witness_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `tmp/elenchus/lazarus-empty-receipts-step-1.json`.

**Disciplines.** phylax: schemas and receipt bytes are hostile inputs, so closed alternatives, existing caps, canonical quantities, and bounded diagnostics apply. ephoros: stable mode, root, cardinality, relation-count, and refusal fields answer the study's operator questions without payload bytes. metron: none, this is a correctness change with no speed claim. elenchus: the non-empty-root empty witness and mixed-shape specimens must fail against the entry ref and pass only after the responsible layer is fixed. hypomnema: the version-preserving exclusive-shape choice is expensive to reverse and belongs in the new decision record and tracked specification.

## Step 2: Carry verified emptiness through capture and fixture accounting

**Goal.** Capture the empty receipt set safely and carry verified zero-relation evidence through fixture verification, manifests, bindings, and releases.

**Entry.** The controller-receipted Step 1 head, with exclusive shapes registered, core empty-root verification guarded, the `nonempty-root-empty-witness-refused` conformance report green, and all existing scoped receipt tests unchanged.

**Exit.** The empty plan issues exactly one named `eth_getBlockReceipts` request for its already-fixed block, accepts only a bounded literal empty array, derives the exclusive empty witness, and retains existing staging, secret-scanning, atomic-write, and no-fallback controls. Fixture verification recomputes the canonical empty root against the verified header and reports receipt count zero, witness mode empty, and relation count zero. Manifest-v2, Lazarus binding, release-v2, and Ariadne state-fixture/v2 distinguish a successfully verified zero from missing receipt evidence while leaving positive-count/root rules and every existing format unchanged. A checked-in Ethereum genesis fixture verifies offline and the focused test records the Step 3 conformance report. Prove the exit with `python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -p 'test_empty_receipts.py' -v`, `python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1`, `python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -v`, and `python3 scripts/run_checks.py`.

**Files.** Create `plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1/`; change `plugins/lazarus/scripts/lazarus_lib/{capture.py,verifier.py,manifest.py,binding.py,release.py}`, the minimum related Lazarus schema registry and tests, and Ariadne state-fixture predicate or schema files only if existing zero-count semantics otherwise refuse a verified empty witness.

**Tests.** Cover the exact genesis block identity and empty root; named request shape and one-request count; absent, null, non-array, non-empty, oversized, or mismatched provider results; partial-write cleanup; zero-versus-missing manifest and release evidence; v1/v2 dispatch; offline operation; deterministic component digests; and unchanged non-empty fixtures and releases. Run the exact design resolver `python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -p 'test_empty_receipts.py' -v` and write its zero-exit `protasis-design-report/v1` result to `.hexaemeron/reports/conformance/shape-discriminated-genesis-empty-fixture-verifies.json`. The step audit runner contract is test command `python3 plugins/lazarus/tests/run_empty_receipt_witness_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `tmp/elenchus/lazarus-empty-receipts-step-2.json`.

**Disciplines.** phylax: provider bytes, fixture paths, local statements, digests, staging, and output publication cross existing trust boundaries and retain bounded no-follow and atomic controls. ephoros: verifier and capture outputs expose safe mode, root, receipt count, relation count, stage, and refusal category without raw receipt or provider data. metron: none, request and byte limits are safety budgets and no latency improvement is claimed. elenchus: each false accept, missing-evidence confusion, and partial-write path gets a minimal parent-red guard. hypomnema: zero-relation evidence semantics extend the decision record and receipt-proof guide rather than creating a second incompatible evidence vocabulary.

## Step 3: Demonstrate, reconcile, and close the Lazarus frontier

**Goal.** Demonstrate the receipt-less fixture offline and reconcile the complete governed surface, proof record, source coverage, and Lazarus evolution ledger.

**Entry.** The controller-receipted Step 2 head, with the Ethereum genesis fixture verifying offline, the `genesis-empty-fixture-verifies` conformance report green, zero evidence distinguished from absence, and the full Lazarus suite green.

**Exit.** A checked-in demonstration verifies the genesis fixture, manifest, statement, and release without network access; observes the canonical empty root and exactly zero receipt-trie relations; rejects a non-empty-root empty witness, a mixed shape, count inflation, and digest mutation; and reruns the shipped non-empty Aave v4 demonstration unchanged. `plugins/lazarus/docs/receipt-inclusion-proofs.md`, Lazarus runtime and marketplace prose, tracked study/runbook/proof records, portable copies, manifests, and coverage records state the empty/scoped distinction without widening the proof. The complete mutable first-party marketplace prose is cold-read and reconciled. The source-coverage refresh is run under its fail-silent gate and receipted when it passes. Lazarus advances exactly once from `lazarus-v2.2.0`, closes `empty-block-receipt-witnesses`, and records either one evidenced next job or `None -- mature`; every unrelated skill frontier remains unchanged. The full Lazarus suite records the integration conformance report. Prove the exit with `python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1`, the checked-in genesis demonstration command named by the implementation, `python3 plugins/lazarus/examples/aave-v4-spoke-v1/demo.py`, `python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -v`, `python3 scripts/run_checks.py`, and every changed-area, prose, Promise Machine, version, portable-copy, source-coverage, and Horos check selected by `AGENTS.md`.

**Files.** Create the checked-in genesis demonstration beside its fixture and `docs/lazarus-empty-block-receipt-witness/proof.md`; change `plugins/lazarus/{AGENTS.md,README.md}`, `plugins/lazarus/docs/receipt-inclusion-proofs.md`, `plugins/lazarus/skills/lazarus/{SKILL.md,EVOLUTION.md}`, `SOURCES.md` and its generated links only through the required source refresh, the Lazarus host manifests and marketplace registries only for mechanically required version propagation, portable copies, test coverage records, and `.horos/boundary.json` only when their owning checks require changes.

**Tests.** Add deterministic demonstration and hostile-copy cases for root, shape, relation count, digest, release, and no-network operation; retain the full Aave v4 two-relation demonstration and every legacy fixture/release digest; check evolution arithmetic, frontier digest, source links, package/skill version separation, marketplace and portable-copy agreement, prose lints, and final tree cleanliness. Run the exact design resolver `python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -v` and write its zero-exit `protasis-design-report/v1` result to `.hexaemeron/reports/conformance/shape-discriminated-existing-formats-stay-green.json`. The step audit runner contract is test command `python3 plugins/lazarus/tests/run_empty_receipt_witness_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `tmp/elenchus/lazarus-empty-receipts-step-3.json`.

**Disciplines.** phylax: demonstrations, generated copies, source refresh, and release readback must preserve bounded paths, exact bytes, provenance, and no-network verification. ephoros: the demonstration reports named checks, safe counts, roots, versions, digests, and network denial; no service metrics or alerts are added. metron: none, the final claims are correctness and compatibility claims, not performance claims. elenchus: every hostile mutation must materialise changed canonical bytes and fail at its owning boundary while the non-empty regression suite stays green. hypomnema: the proof record and ledger row hold the delivery evidence, rejected designs, remaining gaps, frontier decision, and homes of every durable claim.
