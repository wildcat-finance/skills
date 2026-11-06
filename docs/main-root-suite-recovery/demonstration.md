# Recovery demonstration

This record observes the audited Step 1 head `c7db7d734fad5ab40511ae04cbb8a6c43aefb824`, tree `d83c77fa35b332592f9a44187a883619b415de0d`, on 12 September 2026. Its [hosted `invariants` check](https://github.com/wildcat-finance/skills/actions/runs/34718084267/job/103618794746) passed. That is a pull-request result; final integration still requires a passing check on the exact published `main` commit.

## Offline recovery

The [fresh offline proof](demonstration/offline-proof.json) records the input hashes, interpreter, working directories, arguments and exits. Corpus checking accepted three fixtures, 15 reviewed bindings, 14 mutations and nine questions, with zero failed, refused or unknown results. The source and profile inputs are unchanged from the Step 1 implementation commit `0578c19bb812ba34fcfc752dcb81e5df4b1090ae`. This check consumes the preserved measurement and parity records; it makes no new model observation.

The fresh package has 18,239,372 runtime payload bytes and 18,668,573 complete package bytes across 1,402 files. The complete count includes the runtime manifest and outer package files. Against the unchanged 26,214,400-byte cap, those totals leave 7,975,028 and 7,545,827 bytes respectively; both exceed the required 5,242,880-byte reserve. The generated manifest SHA-256 is `28d09f7d5e0820e4c405398ef78973f0ffc5bee8f093300056ac8d9db6d2c77d`.

[Installed verification](demonstration/offline-installed-verify.stdout) accepted the isolated package. Its [evaluation check](demonstration/offline-installed-evaluation.stdout) accepted 11 cases and 55 outcomes with no findings. Generation compared the source and packaged prompts and replayed the owner tally with the preserved answers. The generated package directory was removed after its manifest and proof were preserved under `.hexaemeron/step-2-demonstration/`; the bounded command outputs are committed beside this record.

Reproduce from the repository root, using an absent output directory whose parent exists:

```bash
uv run --no-project --python "$(cat .python-version)" python scripts/agent_instruction.py check --root . --manifest tests/fixtures/agent-instruction-v1/manifest.json
package_root="$PWD/.hexaemeron/recovery-package"
uv run --no-project --python "$(cat .python-version)" python scripts/portable_promise_machine.py package --out "$package_root"
uv run --no-project --python "$(cat .python-version)" python "$package_root/.agents/skills/promise-machine/scripts/verify_runtime.py"
uv run --no-project --python "$(cat .python-version)" python "$package_root/.agents/skills/promise-machine/runtime/scripts/promise_machine.py" check --root "$package_root/.agents/skills/promise-machine/runtime" --only evaluation --json
```

## Merge protection

The [applied request](demonstration/protection-request-effective.json), SHA-256 `0acfe3dc8e05e5b716d74889160f344effaf145d3fc8ee3434a01876dbe80fae`, requires `invariants` from GitHub Actions app `15368`, with `strict: true` and administrator enforcement. The [readbacks](demonstration/protection-readbacks.json) retain the observed values, query exits, timestamps and original wrapper digests. Before application, classic protection returned HTTP 404 and the branch rule list was empty. Afterwards, classic protection named the required check and both enforcement settings; the rule list remained empty. `main` remained `b9cafd196b1d8f8b74b207320836532c14e78bab` throughout this observation.

The [first request](demonstration/protection-request.json) was rejected with [HTTP 422](demonstration/protection-apply-response.json): supplying both legacy `contexts: []` and `checks` matched more than one API subschema. The accepted request omits only that legacy field. The rejected request was not applied.

[PR #1547](https://github.com/wildcat-finance/skills/pull/1547) remained open at head `388aaf829f1f44138b91a5a13f3b99b84b238c5b`, targeting `main`, with `mergeable: true`. Its merge state changed from `unstable` to `blocked`; its required [`invariants` check](https://github.com/wildcat-finance/skills/actions/runs/34708398254/job/103592553163) remained `FAILURE`, produced by app `15368`. The [proof](demonstration/protection-proof.json) records no merge attempt. A successful query exit means the query succeeded; the structured check state records the failure.

The existing `.github/workflows/repo.yml` already runs the `invariants` job on unfiltered pull requests, pushes to `main`, and manual dispatch. No workflow change was needed. The controller's `required-invariants` completion resolver accepted the setting; integration must reread it and observe a passing check on the final `main` head.

## Scope and final gates

The current corpus mismatch in [#1513](https://github.com/wildcat-finance/skills/issues/1513) is repaired; its reusable reconciliation capability remains open. [#1192](https://github.com/wildcat-finance/skills/issues/1192) retains the relative-offset schema. [#1198](https://github.com/wildcat-finance/skills/issues/1198) retains the guard-attribution limit; [#1199](https://github.com/wildcat-finance/skills/issues/1199) retains the acquisition-output and token-count evidence limits; the study's earlier [#1200](https://github.com/wildcat-finance/skills/issues/1200) design-report and placement limits remain. None is answered by these offline results.

[#1467](https://github.com/wildcat-finance/skills/issues/1467)'s portrait omission, reference repair and headroom criteria have independent package evidence; closure belongs to final integration. [PR #1515](https://github.com/wildcat-finance/skills/pull/1515) and its existing controller remain a separate specification effort. The narrow [#1520](https://github.com/wildcat-finance/skills/issues/1520) and [#1542](https://github.com/wildcat-finance/skills/issues/1542) test repairs remain as implemented. No new isolation guard is claimed: Warden's bypass probe stayed green under the inherited production fallback.

[#1267](https://github.com/wildcat-finance/skills/issues/1267) retains the mismatch between Fiat provenance-trailer guidance and the hosted ADR-assignment trailer gate. The integration composition must satisfy the existing canonical assignment gate; this step changes neither workflow nor validator. Canonical allocation may include the unchanged eligible draft inherited from the base as well as this run's package decision.

Step 2 changes this documentation and generated reading records. Its final local gates are the Hexaemeron suite, applicable owner and prose checks, both Horos writes, and the genuine staged-tree `.githooks/greenlight`. The `active-root-green` completion resolver invokes that hook, so its successful root suite also establishes the commit gate. A signed commit then precedes the full 12-worker checked run, including the check that requires clean committed source. Final gate reports belong to `.hexaemeron/` and name the actual input head and tree; this earlier demonstration does not claim their future outcomes. The package decision stays unnumbered until the controller's final canonical allocation.
