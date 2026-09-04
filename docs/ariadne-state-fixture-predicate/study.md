# The Ariadne state-fixture predicate, and the gate 5 hole it would inherit

## Assumptions

Assuming, unless corrected:

1. Python 3.9 upward, standard library only, `unittest`, matching the rest of Ariadne.
2. The starting ref is `main` at `271c7b8`, which carries the dataset predicate, the receipted
   lint round and the metron budget check.
3. Ariadne reaches no network. A state-fixture capture reads a Lazarus fixture that already
   exists on disk and never speaks to a node.
4. Signing and signature checking stay outside Ariadne. `cosign` owns both.
5. Lazarus is the producer this predicate describes. Its committed
   `examples/aave-v4-spoke-v0/` fixture is the one the capture path is built against, which is the
   same release Lazarus's own held job names.
6. Ariadne's own suite is not run by any workflow, so the evidence for this run is local. That
   is recorded rather than assumed.

## Problem statement

Two things, and the second is why the first is not shipped alone.

**The predicate.** Ariadne's registry holds two types. A Lazarus state fixture verifies its
five core gates and is told that gates 2 and 5 belong to a type nothing here knows, so the
part that makes a fixture trustworthy is unchecked: which block the state is pinned at, what
was proved against that block's state root, and what was merely recorded from an endpoint.

**The hole.** `predicates/solidity_release.py` returns from gate 5 before checking the current
side when the baseline is null, so a first release can name a current side with no name and a
digest the statement does not cover, and verify clean. The dataset run found it, fixed the same
shape in its own predicate, and recorded it as `S4-R6-06` rather than widening that run. A
state-fixture predicate written from the same template would inherit it, so it is closed here.

Confirmed live on `main` before starting:

```text
pass-solidity-first-release.json with deltas.current replaced by
{"name": "", "digest": <a digest the statement does not cover>}
  -> ok=True, failing=[]
```

A working prototype means all of these hold:

```text
python3 plugins/ariadne/scripts/ariadne.py capture-state-fixture \
  --fixture plugins/lazarus/examples/aave-v4-spoke-v0 \
  --name aave-v4-spoke-v0 \
  --capture-tool lazarus --capture-version 0.1.0 \
  --capture-command python3 --capture-command scripts/lazarus.py \
  --first-release-reason "the first preserved Aave v4 fixture" \
  --out /tmp/fixture.json
python3 plugins/ariadne/scripts/ariadne.py verify /tmp/fixture.json
python3 -m unittest discover -s tests
python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne
```

The verify exits 0 with seven numbered gates and no unchecked line, and the injected
first-release statement above now fails gate 5.

## Prior art

**In Ariadne.** The dataset predicate is the worked template: `TYPE`, `SUMMARY`, field-table
constants, `gate_2_environment`, `gate_5_deltas`, `gate_fields`, and two checks of its own
returning `Gate(None, ...)`. `schemas/dataset-v1.json` is held to the module by
`tests/test_schema_drift.py`, whose completeness test already fails when a registered
predicate ships without a schema this suite compares. `tests/test_conformance.py` requires a
passing fixture per type, a breaching fixture per numbered gate *of that type*, and one per
named check. `capture/dataset.py` reads a release that already exists and refuses what it
cannot read whole.

**In Lazarus, which is what this predicate has to be faithful to.** Its `SKILL.md` opens with
the refusal: never describe receipts, logs, calls or traces as state-proof-backed evidence. Its
code carries the three-way split as literal keys -- `proof_backed`, `header_bound`,
`recorded_rpc` -- in `manifest.py`, `capture.py` and `verifier.py`, and its manifest ships
`evidence_counts` holding exactly those three. `verifier.py` also records
`"canonical_chain_claim": False`, because nothing there establishes that the pinned block is on
the canonical chain.

The committed `examples/aave-v4-spoke-v0/manifest.json` carries `chain_id`, `block` with a hash and
number, eleven `components` each with a path, byte count and sha256, `evidence_counts`, a
`fixture_digest` and a `tool_version`. `header.json` beside it carries `state_root`.

**Outside.** in-toto Statement v1 and DSSE are implemented already. No published in-toto
predicate carries a state root or an evidence-class split.

## Constraints and non-goals

**Constraints.**

- Standard library only.
- Both suites green at every step boundary.
- The three evidence class names are Lazarus's, spelled its way. Renaming them would break the
  binding this predicate exists for.
- Nothing in `predicates/solidity_release.py` changes except gate 5's ordering, which the held
  job names.
- No shipped document inside `plugins/ariadne/` may link outside the plugin.

**Non-goals.**

- No proof checking. Lazarus verifies trie proofs; Ariadne records what Lazarus reported, the
  same division the dataset predicate and `hexctl audit-round` use.
- No network, no signing, no chain confirmation.
- No grounded-agent predicate. It stays specified and unimplemented.
- No change to Lazarus. This run reads its fixture and does not touch it.
- No CI workflow.

## Design options

**Option A: one evidence list with a class field per entry.** Every piece of evidence in one
array, each entry declaring `proof_backed`, `header_bound` or `recorded_rpc`.

Trade: an entry whose class field is absent has no class, and the check would have to invent
one or refuse. It also drifts from Lazarus, whose manifest reports three counts rather than a
tagged list.

**Option B: three counts, taken from Lazarus's manifest.** `evidence` holds exactly
`proof_backed`, `header_bound` and `recorded_rpc`, each a count.

Trade: a count says how much was proved and not which of it. That is what Lazarus's own
manifest publishes, so the statement says no more than its producer did.

**Option C: three counts, plus a gate that ties `proof_backed` to the thing it was proved
against.** Option B, and a `proof_backed` count above zero is refused unless the chain block
carries a `state_root`.

Trade: one more refusal. It buys the thing Lazarus's opening refusal is about: a statement
cannot claim proof-backed evidence without naming what the proof was against.

**Chosen: C.** A is further from the producer and invents a class where one is missing. B would
let a fixture claim two proof-backed items with no state root in sight, which is the exact
sentence Lazarus's `SKILL.md` forbids. The extra rule is four lines.

Two smaller decisions:

- **All three class keys are required, even at zero.** A fixture with no recorded RPC records
  `recorded_rpc: 0`, which says the question was asked. This is the absence rule the other two
  predicates already use.
- **`canonical_chain_claim` is required and must be false.** Lazarus records it false because
  nothing there establishes canonicity. A statement that flipped it would claim a boundary
  nobody proved, so the predicate refuses it rather than carrying it.

## The shape

Type URI: `https://ariadne.wildcat.finance/state-fixture/v1`.

| Field | Holds | Checked by |
| --- | --- | --- |
| `chain` | The pin: chain id, block number, block hash, state root | gate 2 |
| `capture` | The tool, its version, the argv, a digest over its parameters | gate 2 |
| `fixture_subjects` | Each component: name, path, digest, byte count | gate 2 |
| `evidence` | The three counts, spelled as Lazarus spells them | evidence check |
| `replay` | Whether replay reaches a network, and the canonical-chain claim | replay check |
| `deltas` | Baseline and current sides | gate 5 |
| `claims`, `commands` | Core | gates 1, 3 and 6 |

**Gate 2 here.** Recoverable means somebody else can find the same state again: the chain id,
the block number, the block hash and the state root, plus the capture tool with its version,
argv and parameters digest. Every component digest must be a subject of the statement.

**The evidence check.** All three class keys present, each a non-negative whole number, and a
`proof_backed` count above zero refused without a `state_root` to have proved it against.

**The replay check.** `reaches_network` and `canonical_chain_claim` both required and both
false. A fixture whose replay reaches a network is not the fail-closed boundary Lazarus
describes, and a canonical-chain claim is a boundary nothing here proved.

## Risk register seed

- **The predicate lending strength to recorded evidence.** The one thing Lazarus's `SKILL.md`
  forbids outright. A count in the wrong class, a proof-backed count with no state root, or a
  class key quietly absent each let a statement claim more than its producer did.
- **The gate 5 fix breaking the Solidity predicate.** It reorders a live gate on a shipped
  type. Its existing fixtures and tests are the guard, and a new breaching fixture has to
  exercise the branch that had none.
- **Untrusted document input.** A statement arrives from elsewhere. Every check returns rather
  than raises, and no arithmetic happens before a type check.
- **The bool-is-an-int trap.** Three runs, three appearances. A count of `true` must be refused.
- **Reading the Lazarus fixture.** The capture path walks a directory and reads a manifest
  written by another tool. Bounded reads, confined paths, and a refusal rather than a partial
  capture when a declared component is missing.
- **Drift from Lazarus.** The class names and `canonical_chain_claim` are copied from its code.
  A test should read them from Lazarus rather than restating them, so a rename there fails here
  instead of going unnoticed.
- **Float and hex.** Block numbers arrive as hex strings in the manifest and as integers
  elsewhere. One representation has to be chosen and the other refused.

## Glossary seeds

- **State fixture.** A pinned block's state and the RPC evidence an application test needs.
- **The pin.** Chain id, block number, block hash and state root together.
- **Proof-backed.** Checked against the pinned block's state root.
- **Header-bound.** Tied to the captured header without a trie proof.
- **Recorded RPC.** A response an endpoint gave, recorded and not proved.
- **Canonical-chain claim.** An assertion that the pinned block is on the canonical chain,
  which nothing in either tool establishes.
- **Component.** One file in the fixture directory, with its digest and byte count.

## Boundaries

**Always.**

- Both suites before every commit.
- The imprimatur lint on every shipped document.
- The three bundled lints in every audit round, recorded as exits on the round.
- A conformance fixture for every new gate and check, and one for the gate 5 branch this run
  closes.

**Ask first.**

- Adding a dependency. This run intends none.
- Any change to `plugins/lazarus/`.
- Any change to the core gates or the disposition vocabulary.
- Any change to `predicates/solidity_release.py` beyond gate 5's ordering.
- Touching CI.

**Never.**

- Describe recorded RPC evidence as proof-backed, or let a statement do so.
- Claim a canonical chain boundary.
- Verify a trie proof and report it as Lazarus's result, or the reverse.
- Delete or skip a failing test to make a suite pass.

## Sources

- `plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py` and `solidity_release.py` -- the
  template, and the gate whose ordering this run fixes.
- `plugins/ariadne/tests/test_conformance.py` and `test_schema_drift.py` -- the two contracts a
  new predicate has to satisfy.
- `plugins/lazarus/skills/lazarus/SKILL.md` -- the refusal this predicate enforces.
- `plugins/lazarus/scripts/lazarus_lib/manifest.py`, `capture.py`, `verifier.py` -- the three
  class names and `canonical_chain_claim`, in code.
- `plugins/lazarus/examples/aave-v4-spoke-v0/` -- the committed fixture the capture path reads.
- `audit/AUDIT.md`, `S4-R6-06` -- the recorded hole and its proposed patch.
