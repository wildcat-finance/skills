# The Solidity release predicate

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The grounded-agent predicate now ships as the fifth registered Ariadne predicate, with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path that binds an existing `berean-release/v1` tree without importing or running Berean, executing an agent, regrading evaluations or reaching a network.
<!-- marketplace-context:end -->

Type URI: `https://ariadne.wildcat.finance/solidity-release/v1`.
Schema: [`schemas/solidity-release-v1.json`](../schemas/solidity-release-v1.json).

The subject of a release statement is compiled bytecode. Every release subject's
creation and runtime digests appear in the statement's `subject` array, so a
reader holding the bytes can find the statement that covers them.

What the predicate adds to the core `claims` and `commands` is the part that
makes a contract release checkable rather than merely signed.

## The fields

**`source`** -- `repository`, `commit`, `tree_digest`. The commit says which
revision, the tree digest says which bytes, and they are not the same claim: a
commit can be rewritten and a tree digest cannot.

**`build`** -- `compiler`, `compiler_version`, `optimizer` with its `enabled`
and `runs`, `evm_version`, `via_ir` where it applies, `dependency_lock_digest`
and `command` as an argv. Gate 2 refuses anything less, because a version string
on its own does not let anybody reproduce the bytes.

**`release_subjects`** -- one per compiled contract: `name`, `source_path`,
`creation_digest`, `runtime_digest`, and `abi_digest` where it helps. Each
digest has to be a subject of the statement.

**`deltas`** -- the comparison against the previous release. Both sides carry a
`name` and a `digest`. The sections are `abi`, `method_identifiers` and
`storage`, and each entry inside them names both sides too. A first release
carries `"baseline": null` with a `reason`, and may leave the current side out
entirely, since there is nothing to compare it against. Leaving it out is not the
same as writing it empty: a side that is there gets checked like any other.

**`audits`** -- `report_digest`, `covered_revision`, `scope`. The covered
revision is the field that matters: a report linked beside a release, with no
revision, is exactly the gap this project starts from. It does not establish
that the audit covered what shipped.

**`deployments`** -- `chain_id`, `address`, `creation_tx`, an `implementation`
where a proxy is involved, and `confirmed_against_chain`. That last one is a
boolean rather than an omission. This build reaches no network, so everything it
writes records `false`, and an address printed with no note would read as
confirmed.

## The two gates it owns

**Gate 2, the environment is recoverable.** The build and source records above,
in full. The message names what is missing rather than saying the record is
incomplete.

**Gate 5, deltas name both sides.** A comparison fails when either side cannot
be identified by digest. It also fails when delta content sits beside a null
baseline, since a list of added functions with nothing to have added them to is
a comparison against something the statement will not name.

The current side is checked whenever it is present, on a first release as much as
on a comparison, and its digest has to be a subject of the statement. A release
that named some other pair of artefacts and presented the result as its own
history is what that last part refuses.

Both run beside the five core gates, so a release statement prints seven gate
lines and three further checks: the predicate's field shape, its audits and its
deployments.

## What the deltas measure

Three comparisons, because three things break differently.

An ABI entry disappearing breaks a caller at compile time. A method identifier
changing under an unchanged signature breaks one at run time and silently, which
is worse. A storage variable moving breaks an upgrade after the transaction has
gone through.

Storage is compared by variable rather than by slot. A variable that kept its
slot and changed type is as dangerous as one that moved, and comparing by slot
would have reported neither.

## The schema and the validator

Both ship, and they do different jobs. The schema is what another producer reads
to build a statement this tool will accept. The validator is what this tool
actually enforces, and it enforces more: absence rules, delta baselines and
determinism classes are semantic, and a schema saying `counterexamples` is an
array cannot say that an empty array beside an absent campaign record is a lie.

A test compares the schema's required-field lists against the module's own field
tables. A field added to one and not the other fails the suite rather than
shipping as a quiet disagreement.

## Worked examples

`tests/fixtures/conformance/pass-solidity-release.json` is a complete release
with a skipped fuzz campaign, an audit and an unconfirmed deployment.
`pass-solidity-first-release.json` is the same shape with a null baseline. The
`fail-gate2-*` and `fail-gate5-*` fixtures beside them each breach one gate.

```bash
python3 scripts/ariadne.py verify tests/fixtures/conformance/pass-solidity-release.json
```
