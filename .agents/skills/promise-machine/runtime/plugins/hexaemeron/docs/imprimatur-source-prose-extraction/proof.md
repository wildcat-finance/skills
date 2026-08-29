# Imprimatur source-prose extraction proof

This record preserves the Step 2 product-tree demonstration for [issue 503](https://github.com/wildcat-finance/skills/issues/503), alongside the accepted [study](study.md) and [runbook](runbook.md), and records its later composition with the advanced `main` branch. The product results remain tied to the named commands and fixture bytes observed on 2026-08-26; the integration section records a separate bounded check rather than extending those observations to other source, toolchains, or executions.

## Product-tree identities

The demonstration started from signed Step 1 commit `10b4d7f04ca52abfe6aeafa0e8c2c0db5dcdf566` with Python `3.12.3` and Node `v26.6.0`. Node `v26.6.0` was placed first on `PATH` for the Hexaemeron suite. The values below describe signed Step 2 product commit `536d8d25dae60888fc2ec55d3715d47a1546adfe`, before integration with later `main` work.

| Surface | Identity | Recorded value |
| --- | --- | --- |
| `plugins/hexaemeron/skills/imprimatur/SKILL.md` | skill metadata | `2.3.0` |
| `plugins/hexaemeron/skills/imprimatur/EVOLUTION.md` | generation | `imprimatur-v2.3.0` |
| `plugins/hexaemeron/skills/imprimatur/EVOLUTION.md` | held frontier | `open`, revision `labelled-prose-v2`, SHA-256 `092addc4bcae8cd93d34df41146b3a3bbd3fd24a529cd84b1d16e0399d7affb4` |
| `plugins/hexaemeron/.claude-plugin/plugin.json` | product-tree package | `1.5.10` |
| `plugins/hexaemeron/.codex-plugin/plugin.json` | product-tree package | `1.5.10` |
| `.claude-plugin/marketplace.json` | product-tree package listing | `1.5.10` |
| `.agents/plugins/marketplace.json` | product-tree package listing | `1.5.10` |
| `tests/test_version_propagation.py` | product-tree package assertion | `1.5.10` |

The product tree moved by one patch from `1.5.9`. That historical distribution identity is separate from the Imprimatur generation and does not move its held frontier.

## Temporary fixture bytes

The six uncommitted files lived under `/tmp/fiat-503-imprimatur-proof.JYhYL1`. Each file ended with one LF. The SHA-256 values bind the observed commands to the bytes below.

| File | SHA-256 | Purpose |
| --- | --- | --- |
| `issue.sol` | `efde170eb6110eed4180b15f394d63644cb6c75141aa13ebf69b316fcf1442fd` | issue specimen |
| `matrix.py` | `1b5cf0147bad699e338c1bdafea8a4f87e4ee9adc51084406b8d3c79d68fc6d2` | Python docstrings, comment, and string exclusion |
| `matrix.ts` | `7559336980b79433299c1a031fec3531b7f352360c7ea8dbea0802f742457cfd` | TypeScript comment and string exclusion |
| `matrix.tsx` | `7ce2253006eda43a9d7f3f239a9a9852e3d75ca373b8ae0ed228fcee217dbe4c` | TSX JSDoc and JSX string exclusion |
| `ordinary.md` | `d393d42b109daeff0d43a18d2659aac19449d2d6f5190f372428091853a71dfc` | existing indented-Markdown masking |
| `malformed.sol` | `f0e6f6797bc49049f0832ea8a33e5d50219835d150097780119f1cff98a07d07` | unterminated-comment refusal |

### `issue.sol`

```solidity
contract C {
    /// @notice Leverage the underlying primitive.
}
```

### `matrix.py`

```python
"""Leverage the module primitive."""
ordinary = "Leverage is only data"
def run():
    """Leverage the function primitive."""
    # Leverage the comment primitive.
    return ordinary
```

### `matrix.ts`

```typescript
const text = "// Leverage only data";
// Leverage the helper.
```

### `matrix.tsx`

```tsx
const view = <p>{"/* Leverage only data */"}</p>;
/** Leverage the view. */
```

### `ordinary.md`

```text
    Leverage hidden in indented Markdown.
```

### `malformed.sol`

```solidity
contract Broken {
    /* Leverage the unterminated comment.
}
```

## Delivered command behavior

The exact issue command was:

```bash
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py /tmp/fiat-503-imprimatur-proof.JYhYL1/issue.sol --max-defects 0
```

It exited `1` and reported the original source coordinate:

```text
score 0.0/100   defects 1   weighted 3   /1k words 600.0

  H      2:17  high     consultant: 'leverage'
```

The matrix used the same command shape and changed only the input path:

```bash
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py /tmp/fiat-503-imprimatur-proof.JYhYL1/matrix.py --max-defects 0
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py /tmp/fiat-503-imprimatur-proof.JYhYL1/matrix.ts --max-defects 0
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py /tmp/fiat-503-imprimatur-proof.JYhYL1/matrix.tsx --max-defects 0
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py /tmp/fiat-503-imprimatur-proof.JYhYL1/ordinary.md --max-defects 0
```

| Input | Exit | Defects | Original coordinates | Excluded source text |
| --- | ---: | ---: | --- | --- |
| `.sol` issue specimen | `1` | `1` | `2:17` | contract code |
| `.py` | `1` | `3` | `1:4`, `4:8`, `5:7` | assigned string on line 2 |
| `.ts` | `1` | `1` | `2:4` | string on line 1 |
| `.tsx` | `1` | `1` | `2:5` | JSX string on line 1 |
| `.md` | `0` | `0` | none | four-space-indented Markdown remained masked |

The Python run also emitted the non-blocking cadence signal `repeated openers: leverage the` with count `3`. No literal supplied an extra finding.

The malformed-input command was:

```bash
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py /tmp/fiat-503-imprimatur-proof.JYhYL1/malformed.sol --max-defects 0
```

It exited `2` before a partial report and printed:

```text
imprimatur: /tmp/fiat-503-imprimatur-proof.JYhYL1/malformed.sol:2:5: source extraction failed: unterminated block comment
```

## Entry toolchain correction

The first entry invocation of `python3 plugins/hexaemeron/tests/run_tests.py` selected Node `v22.22.3`. The existing fixture guard expected `v26.6.0`, so the run stopped at `1160/1161` with `test_fixture_exercised_the_declared_node_version` failing. No repository bytes changed in response.

The causal change was the process environment:

```bash
PATH=/home/kethcode/.local/share/mise/installs/node/26.6.0/bin:$PATH python3 plugins/hexaemeron/tests/run_tests.py
```

That rerun executed `1161` tests and exited `0`. The same pinned Node path was used for the final Hexaemeron gate.

## Integration composition

Before the run integrated, `main` advanced to `ab611eb96a6a9bddecb57bff2416641296e0a21e` and already carried Hexaemeron `1.6.1`. The merge overlapped the two plugin manifests, both marketplace listings, and `tests/test_version_propagation.py`. The composition retains the newer `1.6.1` value in all five files; replacing it with the product tree's `1.5.10` would discard intervening Hexaemeron releases.

The signed product evidence remains attached to run-branch merge head `8ffbc2ee9a579d3ebd818c5ba68ac0eb71881387`. It still establishes the `1.5.10` product-tree demonstration rather than claiming that those earlier commands observed `1.6.1`. The integration checks below cover the changed dependency and the advanced-base paths separately.

## Product-tree gates

Every runbook exit command was repeated after this proof carried the results below. Commands ran from the repository root; the Hexaemeron command used the Node path recorded above.

| Command | Exit | Recorded result |
| --- | ---: | --- |
| `python3 scripts/promise_machine.py check` | `0` | `14` plugins and `14` copies |
| `python3 -m unittest discover -s tests` | `0` | `350/350`; inoculation summary `1258` cases, `0` crashes, `0` unexpected clean cases |
| `python3 plugins/hexaemeron/tests/run_tests.py` | `0` | `1161/1161` |
| `python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` | `0` | `112/112` |
| `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests` | `0` | `clean` |
| `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests` | `0` | `clean` |
| `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs` | `0` | `clean` |
| `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/docs/imprimatur-source-prose-extraction/study.md plugins/hexaemeron/docs/imprimatur-source-prose-extraction/runbook.md plugins/hexaemeron/docs/imprimatur-source-prose-extraction/proof.md --max-defects 0` | `0` | `0` defects in all three files |
| `git diff --check` | `0` | no whitespace errors |

The root suite's boundary-currency test found no classified tracked-tree drift, so `.horos/boundary.json` was not regenerated. The additional shipped-prose structure check, `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/docs/imprimatur-source-prose-extraction/proof.md --mode report`, also exited `0`.

## Integration revalidation

The product-first integration joins run head `8ffbc2ee9a579d3ebd818c5ba68ac0eb71881387` to pinned `main` commit `ab611eb96a6a9bddecb57bff2416641296e0a21e`. The five version-propagation conflicts retain `1.6.1`. Main's newer audit-synopsis contract also requires a committed sibling for this run's audit log, so the checked generator wrote `audit/rounds/fiat-503-imprimatur-1-read-comment-spans-in-source-fi.synopsis.md`. Its source is the unchanged 227-line audit log with SHA-256 `85680333092b7e587810a5ce5ca2b86fb07fd78e861ef7dd56fa5984b81fb197`; the ten-line synopsis has SHA-256 `bc52a6b491c8de3b7b7257cc23eb4798f2b60f29b74e30053eaf0d9c78cafa12`.

One upstream test assumed that a same-size rewrite always changes filesystem timestamps between adjacent calls. That assumption was false on the integration filesystem and made the root suite fail even though the production reader was unchanged. The test now advances the rewritten fixture's metadata explicitly before asserting the reader's refusal. The released Fiat generator remains byte-identical to pinned `main`.

The Hexaemeron suite contains ancestry checks for the joined history, so it ran after the two-parent commit existed. Its first post-commit invocation executed `1266` tests and stopped at `1265/1266`: the local keyring lacked the public OpenPGP key required to verify inherited composition `0fb3bcfba14a36c623f380105504d41d1eb66c86`. The public key returned for the `shoggoth-wildcat` GitHub account was imported into an isolated temporary GPG home; its fingerprint was exactly `636EC19DE45DF10F3CE6206F57742DA1ABED6F46`. The inherited OpenPGP commit and this run's SSH commit then verified, and the unchanged tree passed `1266/1266`. No private key entered the temporary keyring.

The bounded checks below cover the resolved composition. The first nine ran before the join was signed and were repeated where stated after it; the ancestry-sensitive Hexaemeron row records the post-commit execution.

| Command | Exit | Recorded result |
| --- | ---: | --- |
| `python3 scripts/promise_machine.py check` | `0` | `14` plugins and `14` copies |
| `python3 -m unittest discover -s tests` | `0` | `396/396`; inoculation summary `1258` cases, `0` crashes, `0` unexpected clean cases |
| `python3 -m unittest discover -s plugins/berean/tests -t plugins/berean` | `0` | `162` tests executed; one declared skip |
| `uv run --isolated --with-requirements plugins/lazarus/requirements.lock python -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus` | `0` | `414/414` in the tracked lockfile environment |
| `GNUPGHOME=/tmp/fiat-503-gnupg GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=gpg.ssh.allowedSignersFile GIT_CONFIG_VALUE_0=/tmp/fiat-503-allowed-signers PATH=/home/kethcode/.local/share/mise/installs/node/26.6.0/bin:$PATH python3 plugins/hexaemeron/tests/run_tests.py` | `0` | `1266/1266` after both inherited and run-commit signature checks |
| `python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` | `0` | `112/112` |
| `python3 -m unittest tests.test_version_propagation -v` | `0` | `7/7` |
| `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests` | `0` | `clean` |
| `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests` | `0` | `clean` |
| `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs` | `0` | `clean` |
| `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` | `0` | `14` committed synopses matched fresh bytes and their budgets |

## Discipline record and boundary

The changed package metadata, assertion, and proof are repository-owned inputs. They add no dependency, fetched host, subprocess wrapper, credential, model-output authority, unattended path, telemetry, performance budget, or timing claim. Phylax, Ephoros, and Hypomnema reported no mechanical finding. The proof is the existing runbook's requested demonstration record; distribution identity remains in the two manifests and two marketplace listings, so no second decision record was added.

These observations establish behavior only for the recorded bytes, commands, toolchain, and fixed tree. They do not establish source validity beyond successful extraction, factual correctness of comments, or coverage of source languages outside `.sol`, `.py`, `.ts`, and `.tsx`.
