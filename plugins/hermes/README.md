![Hermes](./assets/characters/hermes.png)

# Hermes

<!-- marketplace-context:start -->
## In one line

Hermes measures one named Solidity gas optimisation class at a time and rejects the candidate unless every Foundry, behaviour, layout, selector, and arithmetic gate clears.

**Current frontier.** Hermes's twelve optimisation classes name 62 of the corpus's 120 rules, so 58 documented rules cannot be selected as candidates.

**Next Fiat job.** Use /hexaemeron:fiat to widen the Hermes optimisation classes against the pinned rule corpus until every rule with a source-level candidate can be selected, starting with the reduction in storage writes that STO-09's neighbour STO-12 needs and no class names. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

Hermes alone owns Solidity gas optimisation. Metron measures performance in
every other unit. Pandects supplies economic laws that a candidate may need to
preserve, Janus checks hook effects against their host boundary, and the Pashov
suite can review the resulting Solidity. None of those siblings can replace
Hermes's sealed before-and-after measurement or accept a candidate on its
behalf.

A future Synkrisis comparison may point a person towards a repeated run
pattern, but it cannot replace Hermes's controlled gas evidence. The current
Synkrisis scaffold refuses every operation and makes no such finding.

The canonical workflow and complete gate contract live in
[`skills/hermes/SKILL.md`](skills/hermes/SKILL.md).

## How it works

Gas changes are easy to praise and surprisingly easy to get wrong. Hermes takes one optimisation class at a time through a fail-closed Foundry run:

1. Seal a clean baseline with `forge snapshot` and a green `forge test`.
2. Apply exactly one declared optimisation class.
3. Prove the saving with `forge snapshot --diff`, reject every positive delta, and capture `forge test --gas-report`.
4. Run the full test suite again with the pinned fuzz seed, then once more unpinned.
5. Diff storage layouts and method identifiers for every recorded contract. Any layout change to a hook, role provider, proxied contract or other protected contract aborts the run.
6. For unchecked arithmetic that can affect persistent state, asset accounting, external calls, permissions, or rounding, run the existing targeted differential or property test before accepting the candidate.

A candidate only clears Hermes when every gate clears. The run leaves behind `result.json`, command logs, gas comparisons, the Solidity diff, storage layouts and method maps, so the number and the safety case can be reviewed together.

## What it ships

- the executable [`hermes.py`](./skills/hermes/scripts/hermes.py) harness;
- a catalogue of [12 optimisation classes](./skills/hermes/references/optimisation-catalogue.md);
- Codex metadata for explicit or automatic invocation; and
- a test suite covering accepted runs and representative failures across Gates 2 to 6.

## Day to day

**Developers.** A gas change shaves a few hundred units off a hot path and nobody can say whether behaviour moved with it. Run Hermes on that one optimisation class and the review arrives with the snapshot diff, both fuzz passes, the storage layout comparison and a `result.json`, rather than a number and an assurance.

**Security and audit.** A gas change arrives from outside the team. Instead of reading it for intent, put it through Gate 5 to see whether any protected contract's storage layout or method identifiers moved, and Gate 6 for unchecked arithmetic that reaches persistent state.
