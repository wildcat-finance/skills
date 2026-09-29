# Compiler event-membership validation

## Observed result

On 2026-09-29, the production CLI accepted the public specimen under all three pinned builds and rebuilt retained Aave set-001 and set-034. Each combination ran twice; its JSONL and provenance bytes matched exactly. Three indexed-flag corruptions refused with exit 1 and preserved both existing output files. Healthy runs exited 0.

These observations use product commit `10d59f5e0cc772bb8350f64a3761d84c56474ff0`, the interpreter pinned in [`.python-version`](../../.python-version) (observed pin `3.14.6`) and Node v26.6.0 on macOS 26.5.1 arm64. No product code or fixture changed during this demonstration. Determinism is limited to these repeated executions; no speed comparison was made.

## Compiler and specimen evidence

The compiler modules were checked against their retained SHA-256 pins before execution and rechecked afterwards. Each launcher reported its exact build with `.Emscripten.clang`. The public input is `plugins/lemma/tests/fixtures/issue-1983/membership-input.json`, SHA-256 `f772b7ffc5cb8dae7f63600f829002acd363962f5488e98b97c3442da3b46af0`. Each fresh standard-JSON result matched its committed compiler fixture.

| Compiler build | soljson SHA-256 | Standard-JSON stdout SHA-256 |
| --- | --- | --- |
| `0.8.10+commit.fc410830` | `5eaee3240a06891abf5ac70c75caf9a0c33ebe9a2736abdaa22a337f86c22933` | `ada9edfa17b32cb34c88fa02ad60ae030413cc140170d8a797f743d55974b3ce` |
| `0.8.19+commit.7dd6d404` | `e0b74e0a16e783a35169f74d1a615ecb48d07c30f97346b83cd587949268681e` | `8a2a45e17037add5a22fa7d14975ad32f9b0d93ed80a9c2a928ac2df9f289b31` |
| `0.8.22+commit.4fc1097e` | `92d283c545395b91a656fa1ec94d567a464bca55aebcdbb99debf42b43026845` | `0fffc888942fa8595d4cbfd8c2501c34a1ce3872546490870aac0479d53333ce` |

The independently written expected `Derived` descriptors were `Changed(uint256 first, address indexed second)`, both `Ping(address indexed actor)` and `Ping(uint256 indexed n)`, and anonymous `Seen(uint256 n)`. The modern build also included `FromLibrary(address indexed sender)`; both legacy builds omitted it from the owner's ABI. The descriptor comparison checked names, ordered wire types, parameter names, anonymous status and indexed flags.

All three public runs produced JSONL SHA-256 `75116aa76367718b404bc9dd097058e961307c5a19016c5f90f3a555457a9114`. Their compiler-specific provenance records differed as expected:

| Compiler build | Provenance SHA-256 | Repeated CLI runs |
| --- | --- | --- |
| `0.8.10+commit.fc410830` | `4bad218e67f86050b48e8be78f4e9bf5fb9edbc1f9cd929797c11fd7866563d7` | 2, identical |
| `0.8.19+commit.7dd6d404` | `bc996c96d04aa7829e96acfd30f0f774efde22405230f6af2b2caaf91d3c517f` | 2, identical |
| `0.8.22+commit.4fc1097e` | `5e3d32e26d2582b55271b3fa1aa93df78aefaf9a793e9d71d54f66fb042d8136` | 2, identical |

Each negative adapter returned the observed compiler output with only `Changed.first.indexed` inverted. The CLI reported `event ABI agreement` and `indexed`; it changed neither previously delivered file. These adapters test refusal after compiler execution, not a compiler producing corrupt output itself.

## Retained inputs and executed checks

Aave set-001 used `0.8.10+commit.fc410830` and produced 115 chunks. Set-034 used `0.8.19+commit.7dd6d404` and produced 517 chunks. Both input digests matched the study pins before use and after execution. Each pair of healthy runs preserved identical JSONL and provenance hashes. Private input identities, generated corpora and exact command transcripts remain in ignored `.hexaemeron/evidence/compiler-demo/`; source bytes stay at their original local evidence paths. They are not part of this public record.

The following commands ran from the repository root with the interpreter pinned in [`.python-version`](../../.python-version), observed as `3.14.6`:

```bash
python3 plugins/lemma/tests/test_solidity.py --solc /private/tmp/lemma-1983-tools/solc-0.8.25
python3 plugins/lemma/tests/emit_issue_1983_report.py --case event-tests --report .elenchus/issue-1983-step-2.json
python3 plugins/lemma/tests/emit_issue_1983_report.py --case production-conformance --report .hexaemeron/reports/pinned-inheritance-production-conformance.json
```

The compiler-backed Solidity suite exited 0 with 201 successful assertions across 28 printed groups and zero failures. It used actual `0.8.25+commit.b61c2a91.Emscripten.clang`, soljson SHA-256 `f8c9554471ff2db3843167dffb7a503293b5dc728c8305b044ef9fd37d626ca7`. Each reporter invocation executed 70 tests with zero failures, errors, skips, expected failures or unexpected successes. The fixed production report declares candidate `pinned-inheritance`, criterion `production-conformance`, exit 0 and value `true`; its SHA-256 is `0aaa4e399dc46f2118a0678c39928347f2c660a603fa3bcec7864ed123debb0e`.

The reporters exercise preserved compiler output and replace the compiler process boundary. Actual compiler coverage comes from the separate executions above. The checked runner's mapped Solidity check alone does not establish that coverage.

## Reproduction and limits

Run the public CLI from `plugins/lemma/` with the absolute specimen and pinned launcher paths:

```bash
python3 chunkers/solidity.py --input "$SPECIMEN" --solc "$COMPILER" \
  --expect-solc "$BUILD" --include '**' \
  --source-ref 'issue-1983:f772b7ffc5cb8dae7f63600f829002acd363962f5488e98b97c3442da3b46af0' \
  --out "$DEST/chunks.jsonl"
```

`BUILD` is one exact build from the first table. The launcher, shared driver and input/output digests, literal argv, exit statuses and stdout/stderr digests are retained with the local demonstration. The evidence directory was created exclusively, commands used argument lists with a 300-second timeout, and digest drift stopped acceptance. No dependency download was needed.

This establishes the observed compiler AST/ABI event agreement and output custody for #1983. It does not complete #1359 or the remaining #1366 venue validation, rebuild all 135 Aave inputs, validate ABI return types or mutability, or establish deployed-bytecode behavior, source truth, compiler authenticity from a version string, retrieval quality or answer correctness. Private corpus publication and release attestation remain outside this demonstration.
