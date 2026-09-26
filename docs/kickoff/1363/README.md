# Two pinned Wildcat V2 action maps

Issue [#1363](https://github.com/wildcat-finance/skills/issues/1363) supplies the source comparison for [#1387](https://github.com/wildcat-finance/skills/issues/1387). The report pair covers all 170 Solidity source files and 410 concrete runtime action contexts. These are source contracts and inherited signatures, not deployed-address counts.

| Role | Protocol commit | Report |
| --- | --- | --- |
| Deployed comparison | `f5a26146987926f4811b72a795d662813dedfe85` | [X-Ray and diagram](deployed/x-ray.md), [actions](deployed/entry-points.md), [properties](deployed/invariants.md) |
| Candidate | `bea503c2736d47de7fd34130c64f10783dc35b39` | [X-Ray and diagram](candidate/x-ray.md), [actions](candidate/entry-points.md), [properties](candidate/invariants.md) |
| Comparison | Both pins | [Semantic changes](comparison.md), [complete action rows](comparison.json), [literal map diff](entry-points.diff) |

## Reading the evidence

[linkage.json](linkage.json) assigns each runtime action a local event, eventless or unresolved disposition. Its conditional links lead to [named callee profiles](evidence/cross-system-links.json), including callback guards, caller identities and constructor paths. Dynamic token, hook, provider and engine implementations remain explicit unknowns. A missing event does not establish a missing transaction.

[sources.json](sources.json) binds every scoped source file and the inherited Solady inputs. The immutable compiler-derived action inventories are independent of the prose and linkage lists. [review.json](evidence/review.json) names the independent reviewer and exact reviewed bytes. [manifest.json](manifest.json) covers every retained file except itself.

The accepted deployment relationships remain those in [targets.json](../1359/targets.json) and [eventdecision.json](../1372/eventdecision.json). Named deployed verification inputs match named blobs; they do not certify the entire comparison commit against every live market. Candidate Sepolia evidence does not establish a mainnet deployment.

## Verification

From the Skills repository root, with its pinned Python:

```sh
python3 scripts/kickoff_xray_1363.py check
python3 -m unittest discover -s tests -p test_kickoff_xray_1363.py
```

The checker validates fixed source/action inventories, membership, digests, declared review and the literal diff. It cannot prove reviewer identity, semantic correctness, deployment state or protocol safety.

Both default coverage commands and both `--ir-minimum` fallbacks failed before producing coverage. The deployed default failed Solar analysis; the other three attempts failed compilation. [Execution evidence](evidence/execution.json) retains their logs, commands and versions. The reports distinguish detected test functions from tests run; no passing protocol test or coverage result is claimed.

## Recovery and ownership

[Recovery instructions](evidence/recovery.md) describe reacquiring the exact commits and submodules, rebuilding AST inputs and rendering the diagrams. The [provenance record](evidence/provenance.json) binds the canonical skill and accepted inputs; producer extraction records preserve their original bytes and declared limits. Root normalization notes record subsequent corrections.

The [study](study.md), [runbook](runbook.md), design decision `adr/keep-wildcat-xray-reports-bound-to-two-source-commits` and [selection evidence](design-evidence.json) explain the delivery scope. This bundle changes no protocol code or deployment. Issue #1387 owns any adapter or release decision.
