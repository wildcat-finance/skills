# Ariadne

<!-- marketplace-context:start -->
## In one line

Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release.

**Try something else when.** Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence.

**Current frontier.** The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented.

**Next Fiat job.** Use /hexaemeron:fiat to implement the dataset predicate with its schema, gates, conformance fixtures and capture path while keeping signing and signature verification external. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Release evidence another person can check.

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
rather than the only one, and a dataset, a chain-state fixture and a
grounded-agent release each get a predicate beside it rather than a tool of
their own.

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

**Capture.** A Foundry project's build output read into a release statement that
verifies unedited. It does not decide whether your tests passed, does not
confirm a deployment against a chain, and scrubs a build command before
recording it.

**Replay.** The commands a statement marks `exact`, re-run and compared against
the recorded artefact digest. Never through a shell, never without being asked,
and everything marked `nondeterministic` listed as deliberately not run.

**Fixtures and examples.** `tests/fixtures/conformance/` holds a passing
statement and, for each core gate, one that breaches it, for another
implementation to check itself against. [`examples/`](./examples) holds two
attestations over a real build: a clean release, and one carrying a fuzz
campaign that timed out and an audit covering an earlier revision. Both verify.
A tampered copy of each ships beside them and does not.

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

## Where it stops

The registry holds one predicate. The dataset, chain-state fixture and
grounded-agent predicates are specified and not implemented here, so a statement
of one of those types verifies its core gates and is told which gates went
unchecked.

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
