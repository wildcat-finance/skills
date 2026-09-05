![Ariadne](./assets/characters/ariadne.png)

# Ariadne

<!-- marketplace-context:start -->
## In one line

Ariadne writes and checks the evidence statement that joins a released artefact digest to the work actually recorded behind it.

**Current frontier.** The grounded-agent predicate now ships as the fifth registered Ariadne predicate, with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path that binds an existing `berean-release/v1` tree without importing or running Berean, executing an agent, regrading evaluations or reaching a network.

**Next Fiat job.** None -- mature.
<!-- marketplace-context:end -->

## Start here

Use Ariadne when you are about to release an artefact and need a durable answer
to “which evidence supports these exact bytes?” It writes an inspectable
in-toto statement and can check or replay the relations its registered
predicate declares.

It works for Solidity, dataset, historical-state, and grounded-agent releases.
It does not run the producer, authenticate the publisher, verify a signature,
or turn a recorded result into a claim that the artefact is safe or correct.

## Place in the collective

Ariadne receives artefacts and evidence produced elsewhere. Lazarus can supply
a verified state-fixture release, Alexandria or Tabularium can supply data
releases, Berean can supply a grounded-agent release, and Hexaemeron can supply
build and review records. Ariadne binds and gates those exact inputs; it does
not rerun their work or turn a recorded result into a stronger verdict. A
state-fixture/v2 statement can carry Lazarus's receipts root and separately
counted receipt-trie relations, but Ariadne does not reconstruct that trie or
promote transaction hashes.

The Promise Machine governs suite-wide hand-offs. Ariadne is the specialist
that serialises a release-specific evidence claim into an in-toto statement,
optionally wrapped in DSSE.

Synkrisis is the comparison boundary for validated run observations. It writes
a cohort, findings and a verified report, and an Ariadne statement would bind
such a comparison artefact without turning association into cause or action.

A release publishes a claim. The evidence behind it sits somewhere else, joined
by a URL and a promise: the compiler that produced the bytecode, the test run,
the fuzz campaign, the audit and its scope, the deployment. Ariadne writes the
join down as a statement whose subject is a digest, so a reader can check the
binding without trusting whoever assembled it.

The statement is [in-toto's](https://github.com/in-toto/attestation) and the
envelope is [DSSE's](https://github.com/secure-systems-lab/dsse). Neither is
forked. What Ariadne adds is the part a bare statement does not carry: every
claim names the exact digest it covers, skipped and failed work stays in the
statement record, a result is never upgraded into a verdict, a comparison fails
when either baseline cannot be identified, and replay separates what must match
byte for byte from what cannot.

The core is artefact-neutral. A contract release is the first and sharpest case
rather than the only one; a dataset release and a chain-state fixture each have
their own predicate beside it, and a grounded-agent release gets one rather than a
tool of its own.

## How it works

A release publishes a claim. The compiler that produced the bytecode, the test run, the fuzz campaign, the audit and its scope, the deployment: all of it sits somewhere else, joined to the claim by a URL and a promise. Those links do not establish that the audit covered the released commit, that the build produced the deployed bytecode, or that the fuzz run used the settings the report describes. Ariadne writes the join down as a statement whose subject is a digest, so the binding survives the assembly.

The statement is [in-toto's](https://github.com/in-toto/attestation) and the envelope is [DSSE's](https://github.com/secure-systems-lab/dsse). Neither is forked. What Ariadne adds is the discipline a bare statement does not carry, as seven gates:

1. Every claim names the exact digest it covers. A result tied to a repository or a branch is refused, because those move.
2. The environment is recoverable. A compiler version without the optimiser settings, the EVM target, the dependency lock and the command is not a build description.
3. Absence stays visible. Skipped, failed, timed-out and redacted work stays in the statement record, and anything other than a pass carries a reason.
4. Results are not upgraded into conclusions. A passing property records the property and the run, never that the artefact is safe.
5. Deltas name both sides. A comparison fails when either baseline cannot be identified by digest, rather than degrading into a report of no changes.
6. Replay distinguishes deterministic work. Bytecode can require an exact match; a fuzz campaign's coverage cannot.
7. Signature verification is external. Ariadne holds no key, checks no signature, and says so every time it is asked.

Five of those belong to an artefact-neutral core and run for any predicate, including a type the build has never seen. The other two come from the predicate, and a type without them is reported as unchecked rather than clean.

## What it ships

- the executable [`ariadne.py`](./scripts/ariadne.py) capture, verifier and replay, standard library only;
- the [Solidity release predicate](./docs/solidity-release.md) and [its published schema](./schemas/solidity-release-v1.json), tied together by a test so the two cannot drift;
- dataset, state-fixture and grounded-agent predicates, including
  state-fixture/v2 receipt-root and receipt-trie evidence fields and a closed
  grounded-agent schema;
- four offline capture paths over local Foundry builds, dataset releases,
  Lazarus fixtures and Berean releases; none runs its producer or reaches a
  network;
- conformance fixtures with a passing statement and one breach per core gate, for anyone writing another producer or verifier;
- four example attestations spanning Solidity releases, a state fixture and a
  grounded-agent release; and
- a drift-checked offline test suite and an audit log
  ([`audit/AUDIT.md`](./audit/AUDIT.md)) recording every round.

## Day to day

**Developers.** A release goes out, and six months later somebody asks which commit the deployed bytecode came from and whether the audit covered it. `capture` reads that out of the build you already ran, and the statement answers from its own contents rather than from a changelog nobody updated.

**Security and audit.** An attestation arrives with a release. `verify` says which gates hold, which went unchecked and why, and states plainly that it checked no signature. `replay` re-runs the deterministic half and compares the artefacts, so the recorded digests are something you can test rather than something you accept.

## What is in it

**The core.** Digest sets and their matching rules, in-toto Statement v1, the
DSSE envelope with its pre-authentication encoding, the predicate registry, and
bounds on any document that arrived from somebody else.

**The gates.** Five run for any predicate, including a type this build does not
know. Two more come from the predicate, and a type without them is reported as
unchecked rather than clean.

**The Solidity release predicate.** The source and build that produced the
bytecode, the ABI, selector and storage deltas against the previous release, the
audits with the revision each covered, and the deployments with whether anything
confirmed them against a chain. Its published schema sits in
[`schemas/`](./schemas), and a test ties the schema to the validator so the two
cannot drift.

**Capture.** A local Foundry build, dataset release, Lazarus fixture or Berean
release read into a statement that verifies unedited. Capture does not run a
producer, execute an agent, regrade evaluations, confirm a deployment against
a chain or reach a network.

**Replay.** The commands a statement marks `exact`, re-run and compared against
the recorded artefact digest. Never through a shell, never without being asked,
and everything marked `nondeterministic` listed as deliberately not run.

**Fixtures and examples.** `tests/fixtures/conformance/` holds a passing
statement and, for each core gate, one that breaches it, for another
implementation to check itself against. [`examples/`](./examples) holds four
attestations: two over a real build, one over a fixed Lazarus fixture and one
over a fixed Berean release. All four verify. A tampered copy of each ships
beside them and does not.

## The path, end to end

From this directory, `plugins/ariadne`. Capture a release from a build, verify
it, and see a tampered copy refused:

```bash
python3 scripts/ariadne.py capture solidity-release \
  --project tests/fixtures/forge-project/v2 \
  --previous tests/fixtures/forge-project/v1 --previous-name v1.0.0 \
  --repository https://github.com/wildcat-finance/example-escrow \
  --commit 9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a \
  --tests passed --out release.json

python3 scripts/ariadne.py verify release.json
python3 scripts/ariadne.py verify examples/tampered/escrow-v1.1.0-claim-repointed.json
```

Seven gate lines, three checks and exit 0 for the first. Exit 1 for the second,
with gate 1 naming the claim that points at bytes the statement does not cover.

Then see what a replay would do, and do it:

```bash
python3 scripts/ariadne.py replay release.json
python3 scripts/ariadne.py replay release.json \
  --allow-execution --project tests/fixtures/forge-project/v2
```

The first prints the plan and runs nothing, which is the default because the
commands in a statement are somebody else's data. The second re-runs the build
and compares the artefacts against the recorded digest. It rebuilds inside the
fixture, so work on a copy if you want the fixture left alone.

## The subcommands

```bash
python3 scripts/ariadne.py predicates
python3 scripts/ariadne.py capture-dataset --release <dir> --name <release> \
  --coverage-dimension block --coverage-start <n> --coverage-end <n> \
  --producer-tool <tool> --producer-version <v> --producer-command <argv0> \
  --out release.json

python3 scripts/ariadne.py capture-state-fixture --fixture <dir> --name <fixture> \
  --capture-tool lazarus --capture-command <argv0> \
  --first-capture-reason <why there is nothing earlier> --out fixture.json

python3 scripts/ariadne.py capture-grounded-agent \
  --release ../berean/examples/aave-v4-demo-v0/release \
  --name aave-v4-demo-v0 \
  --producer-tool berean --producer-version 0.2.0 \
  --producer-command python3 \
  --producer-command plugins/berean/examples/aave-v4-demo-v0/rebuild.py \
  --first-capture-reason 'first Ariadne capture of this Berean release' \
  --output grounded-agent.intoto.json

python3 scripts/ariadne.py inspect <statement-or-envelope.json>
python3 scripts/ariadne.py verify <statement-or-envelope.json>
python3 scripts/ariadne.py capture solidity-release --project <dir> \
  --repository <url> --commit <40-hex> --out release.json
python3 scripts/ariadne.py replay <statement.json>
```

`inspect` takes either a bare statement or a DSSE envelope wrapping one and
reports what it covers. `verify` runs the gates and prints a line for each,
exiting 1 when one breaks. Exit codes are 0 for success, 1 for a breached gate,
2 for bad input.

[`docs/`](./docs) has the design and its rejected alternatives, the predicate
field by field, the conformance set, and the capture flags.

The fixed release at
`plugins/lazarus/examples/aave-v4-v1-release` demonstrates the
state-fixture/v2 hand-off. Its statement records the fixture's
`receipts_root` and two `receipt_trie_proved` relations, explicitly skips local
receipt-trie re-verification, and leaves transaction-hash attribution in the
recorded-RPC class.

## Where it stops

The registry holds five predicates, reached through four local capture paths.
Grounded-agent capture binds a bounded local `berean-release/v1` tree; it does
not import or run Berean, execute an agent, regrade evaluation or promotion
evidence, or reach a network.

Nothing confirms a deployment against a chain, nothing signs, and nothing runs
as a GitHub Action. Each is a deliberate boundary: the first needs a node, the
second needs key custody this tool declines, and the third needs a workflow that
owns neither.

## Keys

Ariadne holds none. `cosign attest` signs the envelope and
`cosign verify-attestation` checks the signature. Ariadne reads and writes the
envelope, reports whether signatures are present, and states every time that it
did not check them. An unsigned statement is a supported state and gets labelled
unsigned rather than treated as broken.

## Tests

```bash
python3 -m unittest discover -s tests -t .
```

No test touches a network and none needs a Solidity toolchain.

## Licence

Apache-2.0. See [LICENSE](./LICENSE).
