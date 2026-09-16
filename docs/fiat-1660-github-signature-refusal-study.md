# Study: make Fiat's GitHub-signature refusal independent of keyring trust

Task issue: [wildcat-finance/skills#1660](https://github.com/wildcat-finance/skills/issues/1660). Packet handle: `fiat-1660-study-surveyor`. The source tree studied is the exact target directory supplied by the controller.

## 1. Problem, user, working prototype, and demo/check

### Assumptions

- The target is `/Users/c0rtexzer0/Documents/ChatGPT/Wildcat Skills/tmp/fiat/fiat-1660-retry2-1660-github-signature-guard` and the intended source is `origin/main` at `7d9c9844c3ee0242b4b54f37cfb84025582282dd`. The literal local `main` ref is stale at `00786ccd3406d26fb27ff4fea65937bbbe2abfab`; it is not used as current source evidence.
- The packet's `state_sha256` is `54f4d8a5d14f999562a8ced7fef431867c6aaf74946da130b4444107f92fcae6`, and the current ignored `.hexaemeron/state.json` has the same digest. This study does not edit that state.
- The policy remains the one recorded in `SHOGGOTH.md`, `PROMISE_MACHINE.md`, and `docs/decisions/ADR-099-accept-any-validly-signed-authorship.md`: a Fiat-created commit needs a valid local signature, a pushed or GitHub-created commit needs separate GitHub evidence, and neither signature route proves authorship or publication authority.
- The packet is a survey only. No product file, controller state, ledger, Git ref, keyring, remote, issue, pull request, or merge is changed here.

### Problem and user

Issue #1660 reports that `verify_local_commit` reads `GITHUB_SIGNING_KEYS` only inside the non-zero branch of `git verify-commit`. A keyring containing GitHub's public web-flow key can therefore validate a GitHub-rewritten commit, return status zero, skip the refusal, and make that commit count as locally signed. The affected user is the Fiat controller and anyone relying on its local-range admission to mean that the receipted commits were signed locally.

### Smallest working prototype

Move the existing `signing_key` read and the existing `GITHUB_SIGNING_KEYS` refusal ahead of both verification branches. The order is:

1. Resolve the exact full commit SHA as today.
2. Read `%GK` once through the existing bounded `signing_key` helper.
3. If its upper-cased value is `4AEE18F83AFDEB23` or `B5690EEEBB952194`, emit the existing GitHub-rewrite refusal and exit before the keyring can turn that signature into a successful local-verification answer.
4. Run the existing native or bounded `git verify-commit` path with the existing four verifier settings. For a non-zero normal-path result, retain the current unknown-key and bare no-signature messages.

This covers `native_relation=True` as well as the ordinary path because classification occurs before `_native_signature_git` can return or refuse. It adds no trust material, credential, API call, state field, or new refusal vocabulary. `signing_key`'s docstring must change from “used only to explain a failed verification” to the narrower fact that it supplies the pre-verification GitHub-key classification and the fallback diagnostic.

### Success criteria and demonstration

The future implementation step must demonstrate all of these cases against the exact target source:

- A valid local signature remains accepted under a keyring that does not contain either GitHub key.
- An unsigned commit still receives the existing bare signature refusal.
- A locally signed commit altered after signing still receives the existing keyed refusal.
- The immutable web-flow specimen `77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883`, whose `%GK` is `B5690EEEBB952194`, receives the GitHub-rewrite refusal under both the GitHub-free and the default keyrings. The default-keyring case is the regression that currently fails.
- A guard or version-resolution commit using the native relation path receives the same GitHub-key refusal when its keyring validates the web-flow key.
- `tests/prove_signature_only_refusals.py` no longer treats a keyring that validates the web-flow specimen as an unproven precondition. When it searches for a locally verified commit to harvest, it must skip known GitHub keys and exit 3 only when no local signer can be established. It must write no report on that exit.

The focused future commands are:

```text
python3 -m unittest plugins.hexaemeron.tests.test_hexctl -v
python3 tests/prove_signature_only_refusals.py --candidate precheck-signing-key --out .hexaemeron/design-reports/precheck-signing-key-signature-refusal-preserved.json
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study .hexaemeron/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition design-lock
```

The second command is the conformance demonstration. Its report must use `protasis-design-report/v1`, exit zero only when unsigned, altered, and web-flow objects each produce the exact expected `hexctl` refusal, and remain inside the report directory. The default-keyring run must be part of that step rather than silently skipped.

## 2. Prior art

### Repository and current source

The current implementation declares the two long GitHub key ids at `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:20397-20420`, pins the verifier programs there, reads `%GK` in `signing_key` at `:20824-20838`, and places the GitHub refusal at `:20862-20885`, below the ordinary non-zero status test. `verify_local_range` calls this function for every commit at `:20889-20894`; the native relation callers include version-resolution sync at `:4985-4990` and guard commits at `:9862-9864`.

`plugins/hexaemeron/tests/test_hexctl.py:5772-5857` already records the intended refusal text for a GitHub key, an unknown key, and no key. Its “verifying commit is not refused” case covers status zero without a GitHub-key diagnosis, but it does not cover status zero with a GitHub key. The missing regression is one case that returns a GitHub refusal after the verifier reports success, plus a native-relation case if the implementation keeps that branch separate.

`tests/prove_signature_only_refusals.py:1-58` states the current three-specimen contract and explicitly documents the keyring precondition. Its keyring discovery and local-signer search are at `:187-227`; the refusal/report protocol is at `:314-370` and `:372-392`; report writing is at `:411-454`. After this change, the web-flow refusal must be run unconditionally, and `locally_verified_commit` must skip a reachable commit whose `%GK` is in `GITHUB_SIGNING_KEYS` instead of reporting the keyring as an unproven environment.

The demonstration at `docs/signature-only-authorship/demonstration.md:36-47,83-127` records the two keyring shapes, the current local admission matrix, and the observed default-keyring exit 3. `docs/shoggoth-signature-only-retirement-demonstration.md:1-31,58-62,76-101` separates native local signature evidence from GitHub verification and confirms that the existing policy is a signature gate, not an authorship claim.

### Prior decisions and audit history

`docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md:14-27,48-55` records why a GitHub-rewritten stack loses the local signature and why importing GitHub's public key is not a repair. `docs/decisions/ADR-099-accept-any-validly-signed-authorship.md:51-66,153-165` keeps successful local `git verify-commit`, separate GitHub verification, the two web-flow key ids, and the existing “do not import” guidance. Its alternatives at `:200-203` leave the keyring-independent question open; this issue is the scoped answer to that open point.

The directly relevant audit source is `audit/rounds/fiat-1135-retire-the-shoggoth-cosignature-and-host-au.md:5,13-17`. Finding `S1-R1-03` records that the default keyring accepts `77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883` with `%G? U`, so the GitHub refusal is skipped; the GitHub-free keyring makes the same object fail verification and reaches the refusal. Finding `S1-R1-04` records that the prover cannot currently distinguish this keyring success from a removed guard, and names the possible amendment: make the refusal keyring-independent, or precheck and exit 3. `S1-R1-05` is a separate H008 design-bridge issue and is not silently absorbed here.

The current plugin audit record at `plugins/hexaemeron/audit/AUDIT.md:1-71` was read for scope. The whole-set `audit_synopsis.py --check .` completed with exit 0, and the relevant `fiat-1135` source/synopsis pair matched its recorded SHA-256 values. No current audit source was used to claim that the proposed implementation has already passed.

### Last two merged changes touching the target source

The last two merged pull requests whose live file lists include `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` are [#1670](https://github.com/wildcat-finance/skills/pull/1670), “feat(fiat): bind confined workers, cumulative carryover and command receipts,” and [#1652](https://github.com/wildcat-finance/skills/pull/1652), “feat(fiat): export, inspect and restore complete local checkpoint archives.” Their carried-forward rows remain separate work: #1652 filed `signing-key-diagnostics` as issue [#1647](https://github.com/wildcat-finance/skills/issues/1647), while neither PR resolves the keyring bypass. The directly relevant predecessor is [#1664](https://github.com/wildcat-finance/skills/pull/1664), whose carried-forward row filed this issue after retaining the refusal under a GitHub-free keyring. The latest merge [#1683](https://github.com/wildcat-finance/skills/pull/1683) does not touch `hexctl.py` and is not counted as one of the last two target changes.

### Outside this repository

Git defines `git verify-commit` as validation of the GPG signature on the named commit objects; see [the Git verify-commit manual](https://git-scm.com/docs/git-verify-commit). Git's pretty formats expose the long signing key with `%GK`; see [the Git pretty-formats manual](https://git-scm.com/docs/pretty-formats). GitHub's own [commit-signature verification documentation](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification) is the platform-side context for keeping `verified: true` and `reason: valid` separate from local Fiat admission. These external references establish command vocabulary only; the source-bound policy and key list remain the repository files above.

## 3. Constraints, non-goals, start ref, and toolchain

### Constraints

- Preserve the exact local-signature admission promise in `SHOGGOTH.md`, `PROMISE_MACHINE.md`, `plugins/hexaemeron/AGENTS.md`, and `plugins/hexaemeron/skills/fiat/SKILL.md:1059-1076`.
- Keep `SIGNATURE_VERIFIER_CONFIG`, `--no-replace-objects`, bounded subprocess behavior, and the current refusal text. The new check must use the existing `%GK` reader and the existing frozen key set.
- Make the refusal independent of whether the operator's keyring can validate GitHub's public key. A keyring is an input to signature verification, not authority to convert a platform rewrite into a local signature.
- Keep the prover's no-report and exit-3 behavior for an unestablished local signing specimen, while removing only the obsolete “GitHub key in this keyring” precondition after the product guard is independent.
- Preserve the distinction between local verification and authenticated GitHub readback. This issue does not alter GitHub API fields, hosted settings, branch protections, credentials, or publication authority.

### Non-goals

This packet does not remove `GITHUB_SIGNING_KEYS`, import or delete keys, create an isolated trust store, change Git configuration, rewrite historical commits, broaden the key list, modify the controller or ledger, or decide issue #1647's broader signing-key diagnostics. It does not prove signer ownership, GitHub account ownership, or that any future implementation has passed.

### Start ref and toolchain

The packet names `main`; the source used for this study is the exact `origin/main` object at `7d9c9844c3ee0242b4b54f37cfb84025582282dd`, which is also the target branch `HEAD`. The target branch is clean. The checked-in Fiat skill declares version `6.61.1` at `plugins/hexaemeron/skills/fiat/SKILL.md:1-10`; the ignored controller snapshot still records `fiat-v5.54.1`, so version allocation and controller reconciliation belong to the controller. The repository's `.python-version` interpreter and existing Git/GnuPG tools are sufficient; no dependency is proposed.

## 4. Candidate designs and trades

The design record is the selection interface. The prose below describes the candidates and their trade; it does not replace the matrix.

### `precheck-signing-key`: selected recommendation

Read `%GK` once before either native or ordinary verification and refuse the two known GitHub keys immediately. Then execute the existing verifier and its existing fallback diagnostics. Update the focused test with the missing status-zero case, update the prover to run the web-flow specimen under any keyring and skip GitHub-keyed commits while searching for a local specimen, and amend the demonstration/runbook text.

This is the smallest complete product change because it moves an existing bounded read and existing refusal branch, keeps the current verifier settings and error text, and covers the native relation branch without creating a second verifier. Its trade is that a malformed GitHub-keyed object receives the stable GitHub-rewrite diagnosis before native verification emits a generic invalid-signature diagnosis. Both outcomes remain refusal; the former preserves the more useful cause already promised by the message.

### `post-success-signing-key`: status-first classifier

Run the existing ordinary `git verify-commit`, then read `%GK` and apply the GitHub refusal whether the status was zero or non-zero. This preserves the current normal-path call order but cannot classify a GitHub-keyed native-relation commit when `_native_signature_git` exits directly on verification failure, and it adds a branch-sensitive exception to the policy. It is therefore not selected for a controller-wide fix.

### `isolated-keyring`: verifier environment replacement

Run every verification in a temporary keyring that contains the approved local public keys and no GitHub keys. This could make the existing failure-path refusal reachable, but it moves key custody, import, cleanup, platform-specific trust-store behavior, and recovery into the controller. The current source has no such portable keyring contract, and the issue does not authorize changing the operator's keyring or adding a new trust-state boundary.

### `prover-only`: demonstration guard

Teach `tests/prove_signature_only_refusals.py` to reject a default keyring while leaving `verify_local_commit` unchanged. This would make the demonstration honest but would leave the production admission function accepting the same commit. It fails the correctness gate and is not a repair.

## 5. Risk register

The audit loop should enumerate these risks when the implementation is derived. Each row names one boundary and one check.

```risk-register
github-key-success-bypass | verify_local_commit accepts status-zero GitHub-keyed commits | run the web-flow specimen with a keyring that validates B5690EEEBB952194 and require exit 2 with the existing GitHub message
native-relation-bypass | native_relation=True can exit before ordinary diagnostics | exercise a GitHub-keyed commit through the native relation call and require the same refusal
unknown-key-diagnostic | a failed %GK read must not be treated as proof of a local signer | force the bounded key read to be unavailable and require the existing native verification refusal
local-signer-search | the prover may choose a GitHub-keyed commit as its harvested local signer | skip keys in GITHUB_SIGNING_KEYS and exit 3 without a report when no local signer remains
refusal-message-drift | callers rely on the exact cause and do-not-import guidance | assert the complete stderr string for the GitHub, unknown-key, bare, and altered specimens
bounded-read-cost | moving signing_key changes the per-commit process count | record one bounded %GK read per checked commit and retain the existing timeout and output cap
report-on-precondition | an unproven default-keyring run could leave a misleading report | require exit 3 and no output file when the prover cannot establish a local signer
source-state-drift | the packet state digest and local state digest differ | controller revalidates state_sha256 and the source HEAD before deriving a runbook or receipt
version-boundary | plugin edits require package and evolution resolution | controller resolves the Fiat version relation after the selected implementation is integrated
```

## 6. Glossary

- **GitHub web-flow key:** One of the known public long key ids `4AEE18F83AFDEB23` or `B5690EEEBB952194` used when GitHub rewrites a commit through its merge or rebase flow.
- **Local signature:** A signature accepted by Fiat's configured local verifier for a commit in a local receipt range. It does not mean the signer is a particular person.
- **Keyring:** The verifier's available public-key store. Its ability to validate a signature is an environmental fact, not a Fiat policy decision.
- **`%GK`:** Git's long signing-key field, read here through `git log -n1 --pretty=%GK`.
- **Native relation:** The source-bound verification path that uses `_native_signature_git` and the restricted native Git environment for guard and version-resolution relations.
- **Keyring-independent refusal:** A refusal selected from the commit's declared signing-key id before verifier success can turn a known GitHub rewrite into local admission.
- **Prover precondition:** Evidence the demonstration cannot establish, such as a locally verifiable signing specimen. It must produce exit 3 and no report rather than a positive claim.

## 7. Sources

The source set is deliberately narrow and all paths below were read from the target checkout.

| Source | Use |
| --- | --- |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:20397-20420` | GitHub key declarations and verifier settings |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:20824-20894` | `%GK` reader, defective branch, and range caller |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:4985-4990,9862-9864` | native-relation call sites |
| `plugins/hexaemeron/tests/test_hexctl.py:5772-5857` | existing GitHub, unknown-key, bare, and status-zero unit cases |
| `tests/prove_signature_only_refusals.py:1-58,187-227,314-392,411-454` | current three-specimen proof and obsolete keyring precondition |
| `docs/signature-only-authorship/demonstration.md:36-47,83-127` | recorded keyrings, local matrix, and default-keyring exit 3 |
| `docs/shoggoth-signature-only-retirement-demonstration.md:1-31,58-62,76-101` | signature-only policy and separate platform evidence |
| `audit/rounds/fiat-1135-retire-the-shoggoth-cosignature-and-host-au.md:5,13-17` | S1-R1-03 and S1-R1-04 source-bound findings |
| `docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md:14-27,48-62` | rewrite and import-key rationale |
| `docs/decisions/ADR-099-accept-any-validly-signed-authorship.md:51-66,153-165,200-203` | standing signature policy and open keyring question |
| `plugins/hexaemeron/skills/fiat/SKILL.md:34-49,1059-1076` | phase ownership and hard signature rule |
| `plugins/hexaemeron/skills/protasis/SKILL.md:287-313,469-514,683-695` | design evidence, boundaries, checklist, and handback contract |
| `plugins/hexaemeron/agents/surveyor.md:1-94` | worker packet obligations |
| `plugins/hexaemeron/skills/fiat/EVOLUTION.md:78-87` | current Fiat version history and controller-owned version boundary |
| [Git verify-commit manual](https://git-scm.com/docs/git-verify-commit) | external command semantics |
| [Git pretty-formats manual](https://git-scm.com/docs/pretty-formats) | external `%GK` field semantics |
| [GitHub commit-signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification) | external platform verification context |

### Known-failure inventory

The audit history names two source-bound failures. This inventory is a handback declaration for later runbook derivation; it is not an inoculation receipt and has not been checked against a runbook in this survey packet.

```known-failure-inventory
{
  "schema": "protasis-known-failure-inventory/v1",
  "source_views": [
    {
      "id": "fiat-1135-signature-round-1",
      "path": "audit/rounds/fiat-1135-retire-the-shoggoth-cosignature-and-host-au.synopsis.md",
      "source_sha256": "92c4f236580cd6efedf0c889c0a090690f15db39325f967c86a63ee5a8d62f36",
      "view_sha256": "f2f00f0e2b594316bf8d85604411650c8f4385b9227f7bbe662b96f3dce9c829"
    }
  ],
  "findings": [
    {
      "id": "kf-1660-github-keyring-bypass",
      "source_ref": "fiat-1135-signature-round-1: S1-R1-03 at audit/rounds/fiat-1135-retire-the-shoggoth-cosignature-and-host-au.md:15",
      "failure": "a keyring that validates a GitHub web-flow key makes git verify-commit succeed before Fiat's GitHub-signature refusal can run",
      "guard_paths": [
        "plugins/hexaemeron/tests/emit_fiat1660_guard_report.py",
        "plugins/hexaemeron/tests/test_hexctl.py",
        "tests/prove_signature_only_refusals.py"
      ],
      "test_command": "python3 plugins/hexaemeron/tests/emit_fiat1660_guard_report.py --case kf-1660-github-keyring-bypass --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-1660-kf-1660-github-keyring-bypass.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/hexaemeron/tests/emit_fiat1660_guard_report.py --case kf-1660-github-keyring-bypass --report .elenchus/issue-1660-kf-1660-github-keyring-bypass-green.json",
      "consuming_step": 1
    },
    {
      "id": "kf-1660-prover-keyring-precondition",
      "source_ref": "fiat-1135-signature-round-1: S1-R1-04 at audit/rounds/fiat-1135-retire-the-shoggoth-cosignature-and-host-au.md:16",
      "failure": "the signature prover treats a keyring that validates GitHub's key as an unproven environment instead of proving the product refusal or continuing to find a local signer",
      "guard_paths": [
        "plugins/hexaemeron/tests/emit_fiat1660_guard_report.py",
        "plugins/hexaemeron/tests/test_hexctl.py",
        "tests/prove_signature_only_refusals.py"
      ],
      "test_command": "python3 plugins/hexaemeron/tests/emit_fiat1660_guard_report.py --case kf-1660-prover-keyring-precondition --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-1660-kf-1660-prover-keyring-precondition.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/hexaemeron/tests/emit_fiat1660_guard_report.py --case kf-1660-prover-keyring-precondition --report .elenchus/issue-1660-kf-1660-prover-keyring-precondition-green.json",
      "consuming_step": 1
    }
  ],
  "no_known_findings": null
}
```

## 8. On-call questions and signals

This is a bounded command path rather than a continuously running service, so no alert or metric is proposed. The operator still needs these questions answered from the command result and bounded stderr; the observation contract is `plugins/hexaemeron/skills/ephoros/SKILL.md`.

1. **Was the commit refused because it was a GitHub rewrite?** Read the stable refusal text and the one long key id from `verify_local_commit`; do not infer this from a GitHub UI badge.
2. **Did the verifier succeed under a keyring that contains a GitHub key?** The regression test must still observe a Fiat refusal. A zero `git verify-commit` status is no longer an admission answer for a known GitHub key.
3. **Did the prover establish a local signer?** Exit 0 with a closed report means all three specimens were checked. Exit 3 with no report means the local-signer precondition remained unknown; the operator must not convert it to green.
4. **Did source or controller identity drift?** Before a later receipt, compare the exact source commit and the packet state digest. A mismatch stops the controller handback.

## 9. Boundaries, capabilities, and controls

The boundary is the existing one in `plugins/hexaemeron/skills/phylax/SKILL.md`; this study names how the proposed step fits it.

| Capability | Boundary | Control |
| --- | --- | --- |
| Read a commit's signature identity | Exact commit SHA, `--no-replace-objects`, existing bounded Git invocation, fixed verifier settings, existing timeout and output caps | `signing_key` reads only `%GK`; the verifier still decides validity after the known-key refusal |
| Classify GitHub rewrites | The closed two-key `GITHUB_SIGNING_KEYS` set | Upper-case the bounded `%GK` text and refuse before any successful local-verification result can escape |
| Use the native relation path | Restricted native Git environment and exact existing call sites | The key classification runs before `_native_signature_git`; no alternate Git, replacement object, inherited config, or key import is introduced |
| Build the demonstration | Disposable object repository, fixed argv, no shell, child timeout/output cap, no credential | `tests/prove_signature_only_refusals.py` skips GitHub-keyed commits when harvesting a local signer and writes a report only after all refusals match |
| Write evidence | Report path below the declared controller directory, staged then renamed by the prover | Exit 3 and no report on an unproven keyring; later Fiat inoculation owns any guard commit and report custody |
| Read platform evidence | GitHub `verified` and `reason` remain a separate authenticated source | This change does not accept GitHub verification as local signature evidence |

## 10. Performance budget

No user-facing performance budget is needed. The selected design moves one already-existing bounded `%GK` lookup so it runs for commits that previously passed `git verify-commit`; the design estimate is one additional bounded Git process per successfully verified commit, with no new persistent bytes. This is a correctness change, not a speed optimisation, so Metron's performance-change gate is not incurred; the cap and timeout remain controls. If implementation profiling later claims a material cost, it must record a before/after measurement under `plugins/hexaemeron/skills/metron/SKILL.md` before changing the design.

## 11. Fail-closed and Elenchus guard convention

The implementation must refuse a known GitHub key whether the native verifier would return success, return failure, or run under the ordinary or native-relation branch. A missing or unreadable `%GK` is not positive evidence: the existing native verifier result and its existing no-signature diagnostics remain authoritative. An unknown non-empty key keeps the current “which this keyring cannot validate” message.

The prover must treat a missing local signer as unknown, exit 3, and leave no report. It must never turn a default keyring's successful verification of a GitHub key into a local specimen. The fixed-tree guard must fail on the parent when the precheck or prover change is removed, and pass only after the exact candidate behavior is present. The future Elenchus invocation belongs to the runbook and must use the exact `{report}` command, format, guard paths, and consuming Step named by the inventory; this survey does not run it or create its receipt.

## 12. Expensive decisions and homes

The policy decision is whether a known GitHub web-flow key remains disqualifying even when the local keyring validates it. The existing decisions already answer yes: `docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md:48-55` rejects importing GitHub's public key, and `docs/decisions/ADR-099-accept-any-validly-signed-authorship.md:153-165` preserves the refusal while identifying the keyring gap. The implementation should amend the current decision record through Hypomnema if the maintainer intends to make the ordering itself durable; do not invent an ADR number in this packet.

The concrete homes are:

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` for key classification order and the unchanged refusal text.
- `plugins/hexaemeron/tests/test_hexctl.py` for status-zero, status-nonzero, unknown-key, bare, and native-relation regression cases.
- `tests/prove_signature_only_refusals.py` for keyring-independent web-flow proof, local-signer search, exit 3, and no-report behavior.
- `docs/signature-only-authorship/study.md`, `docs/signature-only-authorship/runbook.md`, and the demonstration record for the operator-facing boundary and exact commands.
- `docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md` or `docs/decisions/ADR-099-accept-any-validly-signed-authorship.md` only through the repository's durable-record owner if the policy/order needs a permanent amendment.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | precheck-signing-key
record | docs/decisions/ADR-099-accept-any-validly-signed-authorship.md
```

### Survey handback

**State:** blocked on the packet/controller state digest mismatch and on the required design-lock reports being disallowed by the two-file boundary. The selected design is source-ready, but this survey does not claim design-lock or implementation readiness.

**Established:** the current defect at `hexctl.py:20862-20868`; the smallest complete code path; the three alternatives and their trade; the source-bound audit findings; the focused tests and prover changes; the recovery, keyring, subprocess, report, and controller boundaries; and the exact current source commit.

**Assumed:** `origin/main` at `7d9c9844c3ee0242b4b54f37cfb84025582282dd` is the controller's intended base; the two declared GitHub key ids remain the complete refusal set; the existing Git/GnuPG command interface remains available; and the controller will reconcile the supplied state digest before any receipt.

**Unknown:** whether the controller packet was generated from the current `.hexaemeron/state.json`; whether the future implementation will update the old prover's keyring search exactly as specified; and whether a maintainer wants the order recorded as an amendment to ADR-021 or ADR-099.

**Checks in this packet:** `audit_synopsis.py --check .` exited 0 before this study was written. The two required Protasis checks are run after both outputs are written; their exact exits are reported by the controller handback.

**One action:** reconcile the packet `state_sha256` with the live controller state, then allow the required per-cell design reports before attempting `design-lock`.

### Amendment -- 2026-09-16

**What changed.** The active run study now names the two armour-header sentinels
`-----BEGIN OPENSSH PRIVATE KEY-----` and `-----BEGIN PGP PRIVATE KEY BLOCK-----`.

**Why.** The repository checkpoint-archive guard scans an active run's study and
requires those sentinel forms before checking the study for secret material.
Naming the forms makes this run record self-describing without adding key
material or changing the selected design.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds.
