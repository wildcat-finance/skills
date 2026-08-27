# Medusa, over an adapter you wrote

<!-- marketplace-context:start -->
> **Marketplace context: Pandects.** Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release. **Current frontier:** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
<!-- marketplace-context:end -->

`medusa.json` carries the settings and leaves `targetContracts` empty, because
the target is the only part that is yours: the contract extending
`CorpusMedusa` or `DrivenCorpusMedusa` and naming your system.

Fill it in. Copy the file, name your harness in `targetContracts`, and point
Medusa at the copy:

```bash
medusa fuzz --compilation-target . --config your-medusa.json
```

There is a shorter route and it does not run these settings:

```bash
medusa fuzz --compilation-target . --target-contracts YourHarness --test-limit 20000
```

That works, and it works under Medusa's own defaults, because naming a target on
the command line means not passing `--config` at all. Assertion testing is on by
default and off in this file, so the run is a different search from the one this
file describes. A record calling it the shipped configuration would be wrong
about the configuration.

Passing both is worse than either. With `--config` given, the file's empty
`targetContracts` wins over `--target-contracts`, Medusa finds no tests, and it
exits with `no assertion, property, optimization, or custom tests were found to
fuzz` before searching anything. That is the failure this file warns about at the
bottom, arriving from the command line instead of from the artefacts.

The settings match `adapters/echidna/echidna.yaml` wherever the two engines
have the same knob: twenty thousand transactions, sequences up to sixty-four
calls, assertion testing off and property testing on. `property_` is what
Medusa reads by default, and it is why the adapter carries that prefix rather
than a name somebody preferred.

Two things differ, and both reach the search record.

**Medusa exposes no seed.** Echidna takes one and reports the one it used, so a
campaign under it can be reproduced call for call. A record of a Medusa run
therefore carries the engine, the configuration, the sequence length and the
corpus digest, and says nothing about a seed -- rather than carrying a null,
which would read as a run that had no seed instead of one nobody can read.

That record is written by hand today. `pandects run` emits the Foundry campaign
and no other engine, so nothing here produces a Medusa entry, and a Medusa
result belongs wherever the run is reported until that changes. Widening the
runner is the corpus's held frontier.

**Medusa reports the sequence it found; Echidna shrinks it first.** Turning a
Medusa failure into a deterministic replay is work that turning an Echidna one
mostly is not.

If a campaign exits before it starts -- `Failed to initialize the test chain`,
or a target reported missing from the compilation artefacts -- clear
`crytic-export/` and `.medusa-artifact-hash` and run again. An exit like that
produces output with no failures in it, which reads exactly like a clean run
and is not one.
