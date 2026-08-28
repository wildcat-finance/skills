# Hermes runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Hermes.** Hermes measures one Solidity gas optimisation class at a time and rejects the candidate when its Foundry evidence does not clear every gate. Use Pandects for credit-specific laws, or Hexaemeron's audit skills for a broader security review. **Current frontier:** Hermes's twelve optimisation classes name 62 of the corpus's 120 rules, so 58 documented rules cannot be selected as candidates.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Hermes is one Agent Skill. Its canonical instructions are in
`skills/hermes/SKILL.md`; read that file in full before working on Solidity gas
usage. It is the only instruction copy; do not add a sibling browsing README.

## Capabilities and paths

- The agent needs text-file read and write access plus a shell in the user's
  target repository.
- The target needs Git, Foundry, and a clean working tree. Run the harness with
  the exact interpreter in the suite
  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).
  If one is absent, follow the refusal in `SKILL.md` rather than estimating a
  result.
- Resolve `scripts/hermes.py` and `references/optimisation-catalogue.md` from
  `skills/hermes/`, regardless of the current working directory.
- Run the harness in the target Foundry repository. Do not use this plugin
  checkout as the target unless the user explicitly names it.

## Interpretation

- `$hermes`, `/hermes:hermes`, and a plain request to use Hermes are equivalent
  activation forms.
- Shell snippets describe commands to execute, not text to paraphrase.
- A non-zero harness exit is a rejected gate. Do not continue, weaken a check,
  or report the candidate as accepted.
- `result.json` with status `accepted` and exit code 0 is the only acceptance
  signal. Report the evidence directory with the result.
- Repository issue, branch, review, and approval rules still apply before
  Hermes changes target source.
