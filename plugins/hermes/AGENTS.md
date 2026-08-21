# Hermes runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Hermes.** Hermes measures one Solidity gas optimisation class at a time and rejects the candidate when its Foundry evidence does not clear every gate. Use Pandects for credit-specific laws, or Hexaemeron's audit skills for a broader security review. **Current frontier:** No complete, reproducible live Wildcat evidence bundle is published.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

This plugin holds two Agent Skills. Select from this table, then read the
chosen `SKILL.md` in full. Each is the only instruction copy for its skill; do
not add a sibling browsing README.

| Skill | Canonical instructions | Select when |
| --- | --- | --- |
| `hermes` | `skills/hermes/SKILL.md` | The number that matters is gas |
| `procrustes` | `skills/procrustes/SKILL.md` | The number that matters is deployed bytes, or a contract will not deploy under EIP-170 |

The two disagree by design. A size reduction usually costs gas, so Hermes
refuses most of what Procrustes exists to measure. Pick by the number that
matters and do not run the other one to check its work.

## Capabilities and paths

- The agent needs text-file read and write access plus a shell in the user's
  target repository.
- The target needs Git, Python 3, Foundry, and a clean working tree. If one is
  absent, follow the refusal in `SKILL.md` rather than estimating a result.
- Resolve `scripts/hermes.py` and `references/optimisation-catalogue.md` from
  `skills/hermes/`, and `scripts/procrustes.py` and
  `references/size-catalogue.md` from `skills/procrustes/`, regardless of the
  current working directory.
- Procrustes imports its sealing helpers from `skills/hermes/scripts/hermes.py`.
  Do not vendor, move or rename either script directory; the harness refuses to
  run when the pinned signatures move.
- Run the harness in the target Foundry repository. Do not use this plugin
  checkout as the target unless the user explicitly names it.

## Interpretation

- `$hermes`, `/hermes:hermes`, and a plain request to use Hermes are equivalent
  activation forms. The same holds for `$procrustes` and `/hermes:procrustes`.
- Shell snippets describe commands to execute, not text to paraphrase.
- A non-zero harness exit is a rejected gate. Do not continue, weaken a check,
  or report the candidate as accepted.
- `result.json` with status `accepted` and exit code 0 is the only acceptance
  signal. Report the evidence directory with the result.
- A Procrustes `result.json` with status `sealed` is a baseline, not an
  acceptance. This version of that skill has no candidate gates; do not report a
  size candidate as accepted.
- Repository issue, branch, review, and approval rules still apply before
  Hermes changes target source.
