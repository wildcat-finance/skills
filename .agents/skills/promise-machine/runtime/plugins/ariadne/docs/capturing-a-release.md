# Capturing a release from a Foundry build

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The grounded-agent predicate now ships as the fifth registered Ariadne predicate, with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path that binds an existing `berean-release/v1` tree without importing or running Berean, executing an agent, regrading evaluations or reaching a network.
<!-- marketplace-context:end -->

```bash
python3 scripts/ariadne.py capture solidity-release \
  --project path/to/project \
  --previous path/to/previous-release --previous-name v1.0.0 \
  --repository https://github.com/you/yours \
  --commit <40-hex git object id> \
  --out release.json

python3 scripts/ariadne.py verify release.json
```

What comes out passes `verify` without anybody editing it. That is the point:
a statement somebody had to fix up by hand is a statement whose numbers came
from somewhere other than the build.

## What the project needs

`build_info = true` in `foundry.toml`, and `extra_output = ["storageLayout"]`
if you want the storage delta. Capture reads:

- `out/build-info/*.json` for the compiler version, the optimiser settings, the
  EVM target and the source list. Without it, capture refuses and says which
  setting to turn on.
- `out/<file>.sol/<Name>.json` for the ABI, both bytecodes, the method
  identifiers and the storage layout.

Nothing is recompiled. What the statement records is what the compiler wrote
down.

Gate 2 wants a dependency lock digest. Capture uses `foundry.lock`,
`soldeer.lock`, `package-lock.json` or `yarn.lock` if one is there, and the
source directory otherwise. Either way `build.dependency_lock_source` says which
it was, because a digest whose subject is unnamed tells a reader nothing.

## What capture will not do

**It does not decide whether your tests passed.** A test result arrives as a
stated disposition:

```bash
--tests "passed" --fuzz "timed_out:budget of 30 minutes reached with 4 properties outstanding"
```

Leave either out and the statement records `skipped` with a reason saying
nothing was supplied. A capture tool that wrote `passed` for a run it never saw
would be the thing this project exists to replace.

**It does not confirm a deployment.** `--deployment
chain_id=1,address=0x...,creation_tx=0x...` records the deployment with
`confirmed_against_chain: false`, because nothing here has spoken to a node. An
address printed with no note reads as confirmed.

**It scrubs the build command, and only that.** A build command is the
likeliest place for a credential to ride along, so URLs lose everything after
the scheme,
key-shaped tokens are replaced, and the value after `--rpc-url`,
`--private-key`, `--etherscan-api-key` and the rest goes whatever it looks like.
The count of redacted arguments is recorded beside the command, so the
statement describes a command somebody could recognise rather than one that
quietly lost an argument. A repository URL loses any `user:token@` in front of
its host, since the URL itself has to survive for a reader to follow it.

Reasons and scopes you pass in are recorded as written. Capture does not edit
prose, so do not put a credential in one.

**It does not read outside the project.** `--project` and `--previous` are
resolved, and an `out` that resolves outside its own project, through a symlink
or otherwise, is refused.

## The delta

With `--previous`, capture compares the two builds contract by contract and
writes the ABI, selector and storage deltas, each naming both sides. Without
it, the statement carries `"baseline": null` and a reason, which passes gate 5
because a first release has nothing to compare against and says so.

`--previous-name` is what the baseline is called in the statement. Without one,
capture uses the directory name, which is rarely what you want in a published
document.

## An audit

```bash
--audit report=audits/acme-2026.pdf,revision=<40-hex>,scope="src/Escrow.sol and its libraries"
```

The revision is the field that matters. A report linked beside a release, with
no revision, does not establish that the audit covered what shipped.

## Worked example

The fixture project in `tests/fixtures/forge-project` is two versions of one
contract, with build output committed. `v2` adds `sweep(address)` and inserts a
storage variable ahead of `balance`.

```bash
python3 scripts/ariadne.py capture solidity-release \
  --project tests/fixtures/forge-project/v2 \
  --previous tests/fixtures/forge-project/v1 --previous-name v1.0.0 \
  --repository https://github.com/wildcat-finance/example-escrow \
  --commit 9f2c1a4d6b8e0f2a4c6e8a0c2e4a6c8e0a2c4e6a \
  --out release.json
```

The delta shows `sweep(address)` added to the ABI and to the selectors,
`deadline` added to storage, and `balance` moved from slot 1 to slot 2.
