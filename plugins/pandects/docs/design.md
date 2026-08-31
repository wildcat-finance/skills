# Design: pandects, executable laws for credit contracts

<!-- marketplace-context:start -->
> **Marketplace context: Pandects.** Pandects supplies executable laws for credit contracts, each paired with a deliberately broken specimen and a reduced counterexample. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness and Ariadne to carry the resulting campaign evidence with a release. **Current frontier:** The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
<!-- marketplace-context:end -->

The source specification is `specs/pandects.md`. This study fixes the runbook's
interpretation of it, records the experiments behind the architecture, and
identifies the choices the specification left open.

## Problem statement

A fuzzer searches a state space. It cannot decide which economic facts must
survive that search. Generic token property libraries cover balances,
approvals and round trips; credit adds time, accrual, queues, changing terms,
delinquency, partial repayment and claims that are neither liquid nor
reducible to a token balance. Every audit rediscovers those facts in prose,
implements a subset in a local harness, and the harness dies with the
engagement.

`pandects` is the reviewed corpus that survives the engagement. A law is not a
sentence about credit; it is a Solidity component that executes, a specimen it
is proven to catch, a minimal counterexample, and a statement of where it means
anything.

The build is a plugin at `plugins/pandects/`, in the shape every plugin in this
repository has.

**Working prototype** means this runs offline:

```bash
forge test                       # every law, against every specimen
python3 scripts/pandects.py laws # the catalogue, with applicability
python3 scripts/pandects.py check # the six parts, enforced
```

with each law caught failing by the specimen written for it, each specimen
caught by exactly one law, and a deterministic replay of every counterexample.
A corpus whose laws have never failed is the thing this exists to prevent, so
the demo is not "the laws pass" but "each law fails the specimen built to break
it, and nothing else".

## What the toolchain can actually do

Three experiments, run before the design was fixed, because two of them changed
it.

**Foundry's invariant runner needs no forge-std.** A bare contract with
`setUp()` and `invariant_*()` is fuzzed, shrunk and reported. A deliberately
weak law (`total >= seen`) was caught by `add(0)` and shrunk to a single call
on the first run. No library, no submodule, no network at test time. The
corpus therefore takes no external Solidity dependency at all.

**A tautology passes quietly.** `require(seen() >= 0)` survived 512 calls
across 16 runs without complaint. Nothing in a passing campaign distinguishes a
law that holds from a law that cannot fail. That is the whole argument for gate
2, and it means the specimen is not a nicety: it is the only evidence that a law
is a law.

**A shrunk sequence replays deterministically.** The counterexample above
converts to a plain test with no fuzzing, which is gate 6 satisfied by
construction rather than by promise.

**All three engines run here.** Echidna 2.3.3, Medusa 1.5.1 and Slither 0.11.6
are installed, and both fuzzers were proved against a contract written to break
one law: Echidna found it and shrank the sequence to `deposit(1002)`, Medusa
found it and printed the call sequence and execution trace. Both compile a
Foundry project through crytic-compile with no library present.

Two differences between them shape the adapters. Echidna takes properties
prefixed `echidna_`; Medusa defaults to `property_`. And Echidna shrinks a
failing sequence to something close to minimal while Medusa reports the sequence
it found, so converting a Medusa failure into a deterministic test is manual
work that converting an Echidna one mostly is not.

One of those differences reaches gate 7 directly. Echidna accepts `--seed` and
reports the seed it used, so a campaign under it can be reproduced. Medusa
exposes no seed at all. A search record for a Medusa run therefore states the
engine, the configuration digest, the call sequence length, the corpus digest
and the per-law surfaces its output supports. It says the seed is unavailable
rather than inventing one. That is the corpus's own absence discipline applied
to the corpus.

## Prior art

**Outside.**

- [crytic/properties](https://github.com/crytic/properties): reusable property
  tests for ERC-20, ERC-4626 and others, written as abstract contracts the
  target inherits, aimed at Echidna. The standards are covered; credit
  economics are not. Contributions upstream are in scope where a law fits.
- [Echidna](https://github.com/crytic/echidna) and
  [Medusa](https://github.com/crytic/medusa): the engines, with corpus,
  coverage and shrinking. Neither is replaced.
- Foundry invariant testing: the engine available here, with `fail_on_revert`,
  target selection and a printed fuzz seed.
- [a16z/erc4626-tests](https://github.com/a16z/erc4626-tests) and OpenZeppelin's
  ERC-4626 suites: property sets bound to one standard, useful as shape.
- Certora, Halmos and Kontrol: formal verification. Out of scope. A law here
  executes against a running state, and a proof obligation is a different
  artefact.

**In this repository.**

- `plugins/hexaemeron/skills/fizz`: generates a stateful harness for one
  repository. `pandects` supplies laws that fizz can select and adapt; fizz
  stays useful where no public law describes the protocol.
- `plugins/hexaemeron/skills/solidity-auditor`: looks for conservation,
  state-transition, rounding and economic failures by reading. The corpus is
  the executable form of what it looks for.
- `plugins/ariadne`: carries the search record. Its `commands` block already
  requires an engine, a determinism class and an output digest, which is gate 7
  in a format that already exists. The run record this ships is shaped to drop
  into an ariadne statement without translation.
- `plugins/probitas`: the gates-after-the-fact discipline, and the precedent
  for a Python checker that refuses a document missing its evidence.

## Constraints and non-goals

**Starting point.** `main` at `51157e3`, with `plugins/ariadne` and
`plugins/probitas` shipped and nothing under `plugins/pandects/`.

**Toolchain.** Solidity 0.8.28 through `forge 1.7.1`, with no external Solidity
dependency. The catalogue checker uses only the standard library and the exact
interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).

**Ruled out.** Replacing an engine, writing a harness generator, or shipping a
generic assertion library. Formal proof obligations. Wildcat-shaped law
presented as universal law.

**Deferred past the prototype**, each a line in the shipped documents rather
than a silence:

- Seven of the ten property families in the spec. The prototype covers
  conservation, accrual and withdrawal claims, which is the slice that proves
  the shape and contains the laws Wildcat most needs.
- Echidna and Medusa campaign results, for the reason above.
- The property-to-bug index against public incidents.
- The second example integration against a differently designed lender.

## Design options

**A. Laws as forge-std `Test` contracts.** Familiar and immediately runnable.
Rejected: it drags a submodule the corpus does not otherwise need, and it binds
a public law to one harness.

**B. Laws as abstract contracts the target inherits**, as crytic/properties
does. Rejected: it requires modifying and redeploying the system under test,
which is hostile to the case that matters most, a system already deployed and
being reviewed.

**C. Laws as free-standing checkers over an observables interface.** Chosen.
A law takes a view adapter describing economic roles and returns whether it
held. The target implements the adapter, or a wrapper does, and the law never
names an implementation. All three engines call functions, so one component
works under each.

**D. Laws as data, evaluated off-chain.** Rejected: gate 1 says every law
executes, and an off-chain evaluator is one more engine to trust between the
state and the verdict.

### The shape that follows from C

A law returns rather than reverts:

```solidity
function check(ICreditObservables target)
    external view returns (bool held, string memory detail);
```

Returning is the decision worth arguing about. Under `fail_on_revert = false` a
reverting law is indistinguishable from a target that reverted, so a law that
reverts on the state it was meant to judge reports nothing and is counted as
silence. A law that returns `false` with a detail string has an opinion that
survives the harness.

The catalogue is a JSON document carrying each law's identifier, statement,
applicability, bounds and the specimen it catches. The Solidity component
declares its own identifier, and a test ties the two together, so a law that
exists in one and not the other fails the suite. That is the drift check
`plugins/ariadne` already uses between its schema and its validator.

## Risk register seed

This run ships Solidity, so the audit suite runs in full. What it should look
hardest at:

1. **A law that cannot fail.** The thing the corpus exists to prevent, and
   invisible in a passing campaign. Every law faces its specimen, and a law
   that passes its own specimen is a failing test.
2. **A law that reverts instead of judging.** Arithmetic inside the property,
   an unchecked cast, a view that reverts on an edge state. Silence read as
   assent.
3. **A specimen caught by the wrong law.** If two laws catch one specimen, at
   least one is broader than its statement claims.
4. **Tolerance that hides a defect.** Gate 5: a bound must name the arithmetic
   that produces it. An epsilon chosen because it made a test pass is the
   thing being rejected.
5. **Observables that lie.** The adapter is written by whoever runs the law.
   Stale values, reentrant views, and a `totalAssets()` that counts what is
   already promised elsewhere.
6. **Specimens escaping into production.** They are deliberately broken credit
   contracts. They need a licence header and a warning that survives copying.
7. **Arithmetic in the law itself.** Overflow, truncation and ordering in the
   comparison can mask the very defect being checked.
8. **Unbounded work in a law.** A loop over a queue makes a campaign useless
   long before it makes it wrong.
9. **Cross-law interference.** Laws sharing a harness and a target must not
   leave state behind for each other.
10. **A search reported without its settings.** Gate 7: an engine, a
    configuration, a seed and a corpus digest, or the result is an anecdote.

## Glossary seeds

- **Law.** An executable statement about credit that must survive every state
  transition, with an identity, applicability and a specimen.
- **Property component.** The Solidity contract implementing one law.
- **Observables adapter.** The view interface a target implements so laws can
  read economic roles without naming an implementation.
- **Applicability contract.** The accounting model, trust assumptions and
  features a law requires before it means anything.
- **Specimen.** A deliberately broken credit implementation that a named law is
  proven to catch.
- **Counterexample.** The minimal failing sequence, replayable without a
  fuzzer.
- **Campaign.** One engine run against a harness, with its configuration.
- **Search record.** Engine, configuration, seed, sequence length and corpus
  digest, travelling with a result.
- **Tolerance.** A permitted deviation, stated with the arithmetic that
  produces it.

## Recorded readings

Where the spec left a choice, this is the reading taken.

- **The name.** Raised as weak and reaffirmed by the user, so `pandects`
  stands. The defect worth fixing is the Naming section, which glosses the
  reference rather than carrying a story, and which invokes a compilation whose
  emperor forbade commentary on it while this corpus ships an applicability
  contract inviting exactly that. The prose pass rewrites the section around
  the *Regulae Iuris*, the closing title of the Digest, where the rule is drawn
  from the law rather than the law from the rule.
- **First release scope.** Undercollateralised credit first, with each law's
  applicability stating whether an overcollateralised analogue holds. Pairing
  every law with its analogue is deferred; claiming neutrality without the
  analogue is not.
- **Versioning.** A law's identifier carries its economic statement's version.
  An adapter interface change bumps the component, not the law.
- **Specimen licensing.** Specimens ship under the plugin's licence with a
  header naming them as deliberately broken, and the checker refuses a specimen
  without one.

## Sources

- `specs/pandects.md`, and `specs/ariadne.md` for the search-record shape.
- crytic/properties, Echidna and Medusa, at `github.com/crytic/`.
- Foundry invariant testing, exercised locally at `forge 1.7.1` with
  `solc 0.8.28`.
- This repository: `plugins/ariadne` (drift check, run records),
  `plugins/probitas` (gate checker), `plugins/hexaemeron/skills/fizz`.
