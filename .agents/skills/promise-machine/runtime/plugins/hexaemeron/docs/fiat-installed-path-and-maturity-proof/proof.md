# Fiat installed-path and maturity proof

This document preserves the implementation-stage evidence for the bounded
Fiat frontier run described in [study.md](study.md) and
[runbook.md](runbook.md). The live controller ledger under `.hexaemeron/`
remains authoritative for phase order and terminal state.

## Path and target separation

The active controller is the installed plugin copy:

```text
/Users/c0rtexzer0/.codex/plugins/cache/wildcat-labs/hexaemeron/1.0.0+codex.20260816145806/skills/fiat/scripts/hexctl.py
```

Every invocation passes this repository separately as the controller target:

```text
/Users/c0rtexzer0/Documents/ChatGPT/Wildcat Skills
```

The target began from clean `main` at
`60a01d4c6918e6d30b45da7677dcf6d63a936a3e`, which matched
`origin/main`. The implementation branch is
`step-1-publish-fiat-installed-proof`.

The installed manifest reports package version
`1.0.0+codex.20260816145806`. This is a package identifier, separate from
Fiat's governed skill label.

## Receipt snapshot

Before this implementation was committed, the installed controller's
read-only `status` command reported step 1, "Publish the installed controller
proof and close Fiat," in the `implement` phase. Its `verify` command
reported:

```text
ok: 7 ledger entries, chain intact, state consistent
```

The seven entries, in order, were:

1. `init` for topic `fiat-installed-path-and-maturity-proof` on base `main`;
2. the initial `labs_marketplace` record;
3. the non-Solidity `security_suite` waiver;
4. `resolved_controller_path`, with entry hash
   `818952b21994aa38e9963b2aeb1284feadd7092318acfc10a43660695e4bf977`;
5. `done:study`;
6. the post-study `labs_marketplace` record; and
7. `done:runbook`, with entry hash
   `798f191a2f67aa8472808ae1d9fc69a41c0cf824e10dc61d1dd022d7c65ab917`.

This snapshot does not claim that implementation, audit, prose, push, pull
request, merge, or terminal controller receipts existed at that point. Those
events belong to later controller phases and must be established by the live
ledger before the run can report `done`.

## Installed source evidence

At study time, before the checkout metadata and ledger changed, the installed
and checkout copies had these SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `skills/fiat/scripts/hexctl.py` | `5934bca666ca019c3837aa597cb8b2f9e861e41c11f500d37f3cfdfdeceefc9d` |
| `skills/fiat/SKILL.md` | `3b9da7eb0657b3a075d93661b9b5e72b313ff4d98ede83436e5575af79c971f9` |
| `skills/fiat/EVOLUTION.md` | `3494f39b58b488bf16241cae2fa42a0a68f6b7eaeff178dd738f9980deea8d43` |
| `tests/test_hexctl.py` | `bf196207af51016c1cb48f810dddd801094e01f664eba65248250bd2fb3a852f` |

The checkout's `SKILL.md` and `EVOLUTION.md` necessarily diverge from those
study-time hashes when this step advances Fiat to `fiat-v2.2.0`. No
controller or controller-test source changes in this step.

## Frontier closure

This step keeps frontier revision `installed-path-and-maturity-proof`,
advances only the evolution counter from `fiat-v1.2.0` to `fiat-v2.2.0`,
sets the frontier status to `mature`, and records `None -- mature` as the next
Fiat job.

The canonical newline-terminated frontier record is:

```text
mature|installed-path-and-maturity-proof|Fiat's receipt-backed controller is unit-tested, and this delivery exercises its installed-path resolution and terminal maturity rule together from a packaged plugin.|None -- mature
```

Its SHA-256 digest is:

```text
17c94c70b434ea1cbc9c3cd6ff5f3054972af08f8e027b7ea9850f5e06695f77
```

The installed cache path and SHA-256 chain show which controller was used and
whether its recorded state was altered later. They do not authenticate the
plugin publisher, sign the cache, or prove the cache's build pipeline.

## Verification record

The implementation checks produced these results:

- installed Hexaemeron: 61 of 61 tests passed in 8.337 seconds;
- checkout Hexaemeron: 61 of 61 tests passed in 8.899 seconds;
- checkout Imprimatur: 55 of 55 tests passed;
- repository root: 14 of 14 tests passed;
- Fiat frontmatter and the four targeted version, digest, history-axis, and
  maturity checks passed; and
- installed Imprimatur found no defects or hard hits in the five Markdown
  files shipped by this step. Its 15 rule-of-three cadence notices are
  non-blocking signals under the lint contract.

The implementation receipt and later controller phases carry the audit,
prose, and publication evidence. This tracked proof does not claim those
later events occurred before their live receipts were written.
