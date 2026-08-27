# Brevitas runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Brevitas.** Brevitas enforces mechanical volume and structure budgets on engineering review prose while preserving evidence. Use Imprimatur for banned vocabulary, Vulgate for register, and Sapheneia for AuDHD interaction shape. Brevitas does not own any of those jobs. **Current frontier:** The linter has not been forward-tested across a held cross-model corpus of engineering reviews, and preservation of counterexamples and reproduction steps remains agent-checked.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

## Skill boundary

Brevitas contains one Agent Skill. Read `skills/brevitas/SKILL.md` in full
before applying it. The canonical skill is the only behaviour contract.

## Invocation and checks

- Apply Brevitas to the agent's substantive chat answer and to engineering prose written to disk.
- Run it after Imprimatur, Vulgate, or another word-choice or register pass.
- Keep evidence precedence above every line, heading, table, and code-fence budget.
- Do not apply it to code comments, commit messages, or specifications whose completeness is the point.
- System, safety, harness, and target-repository rules still take precedence.
- `$brevitas`, `/brevitas:brevitas`, `use Brevitas`, and any audit, security-review, gas, invariant, diff-review, or protocol-commentary answer select the skill.
- Resolve relative paths from `skills/brevitas/`.
- Run `scripts/brevitas.py` on a file or stdin. A non-zero exit rejects the draft.
- When compressing existing prose, pass `--source`; missing addresses, transaction hashes, `file:line` references, or numeric tokens reject the draft.
- Run the checker with the exact interpreter in the suite
  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version); it
  needs no third-party package.
