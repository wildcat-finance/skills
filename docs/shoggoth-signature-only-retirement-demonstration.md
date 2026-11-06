# Signature-only retirement demonstration

On 7 September 2026, Fiat accepted a cryptographically signed commit attributed to Codex with no mandatory provenance trailers. GitHub verified the same object with `verified: true` and `reason: valid`. Unsigned and tampered local specimens were refused. This demonstrates the policy selected for [issue #1135](https://github.com/wildcat-finance/skills/issues/1135) and recorded in `adr/accept-any-validly-signed-authorship`.

## Exact objects

The product under test was `155abea7485595791accb4739351d4f036ce1001`, the completed Step 3 head. The demonstration adds this record without changing the implementation. Python was `3.14.6`.

| Specimen | Immutable commit | Observed result |
| --- | --- | --- |
| Signed Codex author, human committer | `80b34c365c8b7f6fd60247b9ef2fb967017f3937` | Native `verify_local_commit` accepted; GitHub `verified: true`, `reason: valid` |
| Unsigned, same empty tree and attribution | `c4dd153d74b00417c66dacf8213f3cbff17acf70` | Native `verify_local_commit` refused: no valid local signature |
| Second signed local specimen | `26dad2c3c809d37e2ec600ea68d2f68c51f1befd` | Native `verify_local_commit` accepted |
| Second specimen changed after signing | `a8807e6a86f195e805760c3abb964c1e526e5019` | Native `verify_local_commit` refused: no valid local signature |

The [published specimen](https://github.com/wildcat-finance/skills/commit/80b34c365c8b7f6fd60247b9ef2fb967017f3937) has author `Codex <codex@openai.com>` and committer `Dr Laurence E. Day <laurence@wildcat.finance>`. GitHub resolved those accounts to `codex` and `laurenceday`. It is an empty-tree proof object with no product ancestry; its message identifies it as a synthetic attribution specimen. Its signature is real, made with `3BCD9EFDA6670A3F65AF679EB83B60AE16F5DD1A`. It contains zero `Co-authored-by` and zero `Wildcat-Origin` trailers. The proof branch was `codex/1135-signature-proof`; it is disposable and is not an integration parent.

## Reproduce the local and platform checks

Create a disposable repository and an empty tree. Use an authorised signing key and synthetic attribution; no host account credentials are needed for local signing. The recorded run used these commands through argument-list subprocess calls:

```sh
git init -q
git mktree
git commit-tree -SB83B60AE16F5DD1A <empty-tree>
git commit-tree <empty-tree>
```

Both commit commands received `Synthetic runtime-host attribution signature specimen` on standard input. The environment set author `Codex <codex@openai.com>`, committer `Dr Laurence E. Day <laurence@wildcat.finance>`, and both dates to `2026-09-07T14:00:00Z`. Signature creation time may change the signed object id on a rerun. For the tampered case, append `Tampered after signing` to the signed commit bytes and pass them to `git hash-object -t commit -w --stdin` without signing again.

Import `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, with that directory on `sys.path`, and call `verify_local_commit(repository, sha, label)` on each object. Accepted calls return the requested SHA. The unsigned and tampered calls exit with the signature refusal. No fake Git executable supplied these results.

The orchestrator published the first signed object through the repository's authorised GitHub App. An authenticated REST read returned the bounded verification and attribution fields:

```sh
gh api repos/wildcat-finance/skills/commits/80b34c365c8b7f6fd60247b9ef2fb967017f3937 \
  --jq '{sha,verification:{verified:.commit.verification.verified,reason:.commit.verification.reason},author:{login:.author.login,name:.commit.author.name},committer:{login:.committer.login,name:.commit.committer.name}}'
```

The same read on product head `155abea7485595791accb4739351d4f036ce1001` returned `verified: true`, `reason: valid`, and `laurenceday` as author and committer. The record retains neither credentials nor raw signature or payload bytes.

The checked-in `verified_github_attribution` gate also accepted the published specimen through the authenticated route, returning its exact SHA, author `codex`, committer `laurenceday`, and an empty co-author list. The immutable commit URL returned HTTP `200` without authentication. Run this from the product checkout with an authenticated GitHub route:

```python
import importlib.util
import os
import sys

scripts = 'plugins/hexaemeron/skills/fiat/scripts'
sys.path.insert(0, scripts)
spec = importlib.util.spec_from_file_location('proof_hexctl', scripts + '/hexctl.py')
hexctl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hexctl)
print(hexctl.verified_github_attribution(
    os.getcwd(), ['80b34c365c8b7f6fd60247b9ef2fb967017f3937']))
```

## Refusal matrix and transport boundary

`TestCommitVerification` exercises nine local attribution shapes, five GitHub attribution shapes, runtime-host pull-request authors and bylines, unsigned or failed local verification, and GitHub false or invalid verification. The GitHub negative matrix includes all twelve non-valid reasons: `unknown_signature_type`, `no_user`, `unverified_email`, `bad_email`, `unknown_key`, `malformed_signature`, `invalid`, `expired_key`, `not_signing_key`, `gpgverify_error`, `gpgverify_unavailable`, and `unsigned`. These matrices use synthetic adapters; the native and published objects above provide the separate live demonstration.

An authenticated connector and authenticated local GitHub access have equal standing when they supply the exact bounded fields the check consumes. `checked_github_object` accepts a connector-shaped object and rejects an array; subsequent verification still requires the exact commit SHA and both valid-verification fields. This run used local authenticated REST for live readback. It did not exercise a live connector session, and does not claim that every connector exposes every required write or field.

## Hosted policy evidence

Step 3 removed only `{context: identity, integration_id: 15368}` from ruleset `21830871` in `wildcat-finance/skills`. The recorded readback is dated `2026-09-07T13:32:32.092+01:00`. Required context `invariants` retains integration `15368`; enforcement remains `evaluate`, bypass actors remain the explicit empty set, and default-branch conditions and unrelated rules are unchanged. Only server-owned `updated_at` also changed.

| Image | Raw response SHA-256 | Canonical SHA-256 |
| --- | --- | --- |
| Before | `31ddfdb7b0e0c0ec7940fd8f47bf6c0486ffaa3b4ad25d4b17b557d0a6963309` | `0417f72336685d50756a157af6bb6e53c24dc89e6fb74b18b02c489710e3f8eb` |
| Mutation response | `bc194080e34fa1daddb130814ea4f42b246976409c4ecef6b1e07246ad97bc65` | `2eff233ed09c08b0ca1ecbf31cc82df12658154e4c06fe9aa619e7a0e6b55239` |
| Readback | `bc194080e34fa1daddb130814ea4f42b246976409c4ecef6b1e07246ad97bc65` | `2eff233ed09c08b0ca1ecbf31cc82df12658154e4c06fe9aa619e7a0e6b55239` |

The App route first returned HTTP `403`, `Resource not accessible by integration`, and omitted `bypass_actors` on its read. It supplied no complete mutation baseline. An isolated local `laurenceday` configuration then supplied the complete before image, mutation and matching readback. This demonstrates an account capability difference, not a preference between connector and local transports. The bounded evidence remains in `.hexaemeron/ruleset-identity-retirement.json`; committed before/after fixtures live in `tests/fixtures/ruleset-identity-retirement/`. No ruleset mutation was repeated during Step 4.

## Product checks and composition

The focused command replaces `tests.test_host_settings`, intentionally deleted in Step 3, with `tests.test_ruleset_identity_retirement`:

```sh
python3 -m unittest tests.test_contributors tests.test_shoggoth_identity tests.test_ruleset_identity_retirement plugins.hexaemeron.tests.test_hexctl -q
python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report .elenchus/fiat-1135-step-4-product.json
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py sync
python3 scripts/promise_machine.py check
python3 scripts/run_checks.py --base 3cc0ad7f521985e46cf29f364a20e19fa99b64dd
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/shoggoth-signature-only-retirement-demonstration.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/shoggoth-signature-only-retirement-demonstration.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
git diff --check
```

Portable regeneration changed no tracked surface. Promise Machine synchronisation wrote zero copies; its check accepted 18 plugins and 18 copies. The audit synopses matched their sources. The complete checked runner also checks whether the Horos boundary is current; no speculative regeneration is needed.

The full Hexaemeron report records 2,447 tests run, 2,447 passed, zero failures, zero errors and zero skips, with `complete: true` under `elenchus.unittest.v1`. The runner used 12 workers under its automatic CPU budget. Phylax, Ephoros and the complete Hypomnema invocation exited zero. Imprimatur reported zero defects; Brevitas and `git diff --check` were clean.

The product projects `fiat-v5.55.1` from anchor `fiat-v5.54.1`. The fetched integration base `b4f59134e4cf8e8d8da17f908bcfe5275c4559a5` still carries `5.54.1`. Final generation resolution and ADR number assignment belong to the signed integration composition and its receipts. The frontier revision `state-shape-validation`, digest `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`, open status and held job [#363](https://github.com/wildcat-finance/skills/issues/363) remain unchanged. This record establishes the named object checks and recorded policy delta, not merge completion or future GitHub state.
