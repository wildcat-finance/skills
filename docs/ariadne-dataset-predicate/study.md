# Ariadne dataset predicate

## Assumptions

Assuming, unless corrected:

1. Python 3.9 upward, standard library only, `unittest` rather than `pytest`,
   matching every other plugin in this repository.
2. The starting ref is `main`, and the run lands there through one integration
   branch.
3. Ariadne reaches no network. A dataset capture reads files already on disk
   and never fetches an input.
4. Signing and signature checking stay outside Ariadne, as they are for the
   Solidity release predicate. `cosign` owns both.
5. The dataset this predicate describes is the kind Alexandria preserves and
   Tabularium releases: a set of files under one release, with a coverage
   statement and named gaps.

## Problem statement

Ariadne's core is artefact-neutral and its registry holds one predicate, for a
Solidity release. A dataset release therefore verifies its five core gates and
is told that gates 2 and 5 went unchecked, because no module claims the type.
That is the gap: the plugin says a dataset can share the gates without sharing
a schema, and nothing yet proves it.

This run adds the dataset predicate: a type URI, a field table, its own gates 2
and 5, a published JSON schema, conformance fixtures another implementation can
check itself against, and a capture path that reads a dataset release from disk
into a statement.

A working prototype means this sequence succeeds from a clean checkout:

```text
python3 plugins/ariadne/scripts/ariadne.py capture-dataset \
  --release plugins/ariadne/tests/fixtures/dataset-release/v2 \
  --name aave-v4-credit-events-v2 \
  --coverage-dimension block \
  --coverage-start 11370000 --coverage-end 15000000 \
  --gap 'start=12000000,end=12000100,reason=the archive node returned no receipts here' \
  --producer-tool tabularium --producer-version 0.3.0 \
  --producer-command python3 --producer-command scripts/tabularium.py \
  --record-count mapping.json=1 \
  --previous plugins/ariadne/tests/fixtures/dataset-release/v1 \
  --previous-name aave-v4-credit-events-v1 \
  --out /tmp/dataset.json
python3 plugins/ariadne/scripts/ariadne.py verify /tmp/dataset.json
```

The second command exits 0 and prints seven gate lines with none unchecked.
The producer flags are required rather than defaulted. Step 4's audit found that
defaulting them put this tool's own name in the field gate 2 reads as what made
the files, and Ariadne reads a release rather than producing one.


## Prior art

**In this plugin.**

- `scripts/ariadne_lib/registry.py` maps a type URI to a module and reports an
  unknown type rather than raising. Registration is a side effect of importing
  `predicates/__init__.py`.
- `scripts/ariadne_lib/core_predicate.py` holds the `claims` and `commands`
  blocks, the closed disposition vocabulary
  (`passed`, `failed`, `skipped`, `timed_out`, `redacted`) and the determinism
  vocabulary (`exact`, `nondeterministic`).
- `scripts/ariadne_lib/gates.py` runs core gates 1, 3, 4, 6 and 7 for any
  predicate, and records that 2 and 5 belong to the predicate.
- `scripts/ariadne_lib/predicates/solidity_release.py` is the one worked
  example: `TYPE`, `SUMMARY`, field-table constants, `gate_2_environment`,
  `gate_5_deltas`, `gate_fields`, and two extra checks that return
  `Gate(None, ...)`.
- `schemas/solidity-release-v1.json` is the published shape, and
  `tests/test_schema_drift.py` holds it to the module's constants field by
  field.
- `tests/fixtures/conformance/` names its files `pass-*` and
  `fail-gate<n>-*`; `tests/test_conformance.py` requires every core gate to
  have a breaching fixture and requires each breaching fixture to fail its
  named gate alone.
- `scripts/ariadne_lib/capture/foundry.py` reads a Foundry build rather than
  re-running it, confines paths, bounds artefact size and nesting depth, and
  takes test and fuzz dispositions from the caller rather than guessing.

**In this repository.** Tabularium already publishes releases with venue-native
records, mapping provenance and explicit coverage; Alexandria preserves the
captures those releases are built from. The coverage-and-gaps shape below is
taken from that boundary rather than invented.

**Outside.** in-toto Statement v1 and DSSE are already implemented here.
in-toto's nearest published predicates are `test-result`, `release` and `link`;
none carries a coverage interval or a record-count delta.

## Constraints and non-goals

**Constraints.**

- Starting ref `main`; Python 3.9 upward; standard library only; `unittest`.
- Both suites green at every step boundary:
  `python3 -m unittest discover -s tests` and
  `python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne`.
- No shipped document inside `plugins/ariadne/` may link outside the plugin;
  `tests/test_docs.py` asserts it, and it currently fails on `main`.
- The marketplace prose blocks between the `marketplace-context` markers must
  agree across every host file; `tests/test_marketplace_prose.py` asserts it.
- The ledger digest covers
  `{status}|{frontier revision}|{current frontier}|{next Fiat job}`, and
  `tests/test_evolution_contract.py` asserts the frontmatter version matches.

**Non-goals.**

- No signing, no signature checking, no key handling.
- No network. An input that cannot be digested from disk is recorded as absent
  with a reason rather than fetched.
- No chain-state fixture predicate and no grounded-agent predicate. Those stay
  specified and unimplemented, and Lazarus holds the first of them.
- No GitHub Action.
- No change to the core gates or to the Solidity release predicate beyond what
  registering a second type requires.

## Design options

**Option A: one predicate module, gates written out longhand.** A second module
beside `solidity_release.py`, repeating the `missing()` helper and the
both-sided delta walk.

Trade: about sixty duplicated lines, and two copies of the delta rule that can
drift apart.

**Option B: extract a shared predicate base first, then build on it.** Lift
`missing`, `check_side`, `section_faults` and the field-shape check into a
helper module, rewrite the Solidity predicate against it, then write the
dataset predicate on top.

Trade: touches a shipped, audited predicate that nothing asked to change, and
puts a refactor of it inside a run whose subject is a new type. A regression
there is a regression in the one predicate people already depend on.

**Option C: new module, and lift only the helpers both provably need.** Write
`predicates/dataset.py` with its own field tables and gates. Move `missing` and
`check_side` into `core_predicate.py` only because the dataset gates call them
verbatim, leaving `solidity_release.py` importing them from their new home with
no behavioural change.

Trade: a two-function move inside a file the audit round will read anyway,
against sixty lines of duplication that would drift.

**Chosen: C.** It is the option cheapest to comprehend that still meets the
problem statement. A reader opening `dataset.py` sees the whole shape of the
dataset predicate in one file, and the two helpers that moved are pure
functions with no state, so the Solidity predicate's behaviour is unchanged by
construction and its existing tests prove it.

## The shape

Type URI: `https://ariadne.wildcat.finance/dataset/v1`.

| Field | Holds |
| --- | --- |
| `producer` | The tool, its version, the argv that ran, and a digest over its parameters |
| `inputs` | Each upstream input: name, locator, and either a digest or a recorded absence |
| `dataset_subjects` | Each released file: name, path, digest, record count |
| `coverage` | The dimension, its bounds, and the gaps inside them |
| `deltas` | Baseline and current sides, and the record-level differences |
| `claims` | Core: what was checked, against which subject digest |
| `commands` | Core: what was run, and whether replay must match byte for byte |

`producer`, `inputs`, `dataset_subjects`, `coverage`, `deltas`, `claims` and
`commands` are all required. There is no optional block: a dataset with no
upstream input records an empty `inputs` array, which says that the question was
asked.

**Gate 2 here.** Recoverable means somebody else can produce the same files.
That takes the tool and its version, the argv, a digest over the parameters, and
a digest or a recorded absence for every input. Every `dataset_subjects` digest
must also be a subject of the statement, so the predicate cannot describe files
the statement does not cover.

**Gate 5 here.** A comparison names both sides. The baseline is a named,
digested prior release, or `null` with a reason. Record-level differences under
a null baseline fail, matching the Solidity rule that a first release cannot
record what changed.

**Coverage check.** Its own `Gate(None, "coverage", ...)`. The dimension and
both bounds are required, `start` must not exceed `end`, every gap must sit
inside the bounds, every gap must carry a reason, and gaps must not overlap. An
absent `gaps` key fails; `[]` passes and asserts that the producer looked.

**Inputs check.** Its own `Gate(None, "inputs", ...)`. An input carries a
digest, or a disposition from the core vocabulary with a reason. An input with
neither fails, because a locator on its own records nothing about what was
read.

## Risk register seed

The audit loop should look hardest at:

- **Untrusted document input.** A dataset statement arrives from elsewhere.
  `safejson.py` bounds size, depth and duplicate keys; the new gates must not
  index into a structure before checking its type, and must return rather than
  raise on every malformed shape.
- **Path handling in the capture path.** `--release` and `--previous` point at
  directories. Reuse `capture/foundry.py`'s `confined()` so a symlink or a
  `..` segment cannot read outside the named tree.
- **Unbounded reads.** A dataset file can be far larger than a build artefact.
  Digest by streaming in fixed blocks; never read a release file whole.
- **Partial writes.** `--out` must not leave a half-written statement where a
  later run reads it as complete.
- **Absence turning into silence.** This is the thing the predicate exists to
  prevent. A gap dropped, an input digest guessed, or a record count taken from
  a filename instead of the file would each pass a schema and lie to a reader.
- **Numeric coverage bounds.** Block heights are integers; timestamps are not
  necessarily. Decide one representation and refuse the other rather than
  comparing across types.
- **Gate isolation.** `test_conformance.py` requires each breaching fixture to
  fail its named gate alone. A new gate that also trips gate 3 or gate 1 breaks
  every fixture, so each gate must report only its own fault.

## Glossary seeds

- **Dataset release.** A directory of files published together under one name,
  with a coverage statement.
- **Coverage.** The interval a release claims to describe, along one named
  dimension.
- **Gap.** A sub-interval inside coverage that the release does not describe,
  with the reason it does not.
- **Input.** An upstream artefact the release was derived from.
- **Producer.** The tool that turned inputs into the released files.
- **Record count.** The number of records in one released file, read from the
  file.
- **Capture path.** Code that reads a release already on disk into a statement,
  without re-running the producer.

## Boundaries

**Always.**

- Both suites before every commit:
  `python3 -m unittest discover -s tests` and
  `python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne`.
- The imprimatur lint on every shipped document.
- The three bundled lints (`phylax`, `ephoros`, `hypomnema`) in every audit
  round, because no step here ships Solidity.
- Every new gate gets a `pass-*` and a `fail-*` conformance fixture in the same
  step.

**Ask first.**

- Adding a dependency. This run intends none.
- Changing the core gates, the disposition vocabulary or the determinism
  vocabulary.
- Changing anything in `predicates/solidity_release.py` beyond the import line
  the helper move requires.
- Touching CI workflows.
- Changing a published type URI or the `$id` of a shipped schema.

**Never.**

- Commit an RPC credential or any key material.
- Guess a record count, an input digest or a coverage bound.
- Delete or skip a failing test to make a suite pass.
- Report a lint, a gate or a suite as run when it was not.
- Sign anything, or describe a statement as verified.

## Sources

- `plugins/ariadne/scripts/ariadne_lib/` -- registry, core predicate, gates,
  verify, capture, and the Solidity release predicate.
- `plugins/ariadne/schemas/solidity-release-v1.json` -- the published shape this
  one is modelled on.
- `plugins/ariadne/tests/test_schema_drift.py`, `test_conformance.py`,
  `test_docs.py` -- the three contracts a new predicate has to satisfy.
- `plugins/ariadne/docs/design.md` -- the two-layer split and the statement that
  a dataset must be able to share the gates.
- `plugins/ariadne/skills/ariadne/EVOLUTION.md` -- the held frontier and its
  acceptance condition.
- `tests/test_marketplace_prose.py`, `tests/test_evolution_contract.py` -- the
  repository-level prose and ledger contracts.
- in-toto Statement v1 and DSSE, already implemented in `statement.py` and
  `envelope.py`.
