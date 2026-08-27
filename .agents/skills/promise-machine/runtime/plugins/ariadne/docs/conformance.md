# Conformance fixtures

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The grounded-agent predicate remains unimplemented; the state-fixture predicate now ships with its schema, gates, conformance fixtures and a capture path that reads a Lazarus fixture's evidence counts rather than recomputing them.
<!-- marketplace-context:end -->

`tests/fixtures/conformance/` holds statements for checking an implementation
against, whether it produces them or verifies them. They exercise the core
gates, so a predicate written later inherits the whole set rather than starting
its own.

The core fixtures use the predicate type
`https://ariadne.wildcat.finance/conformance-example/v1`, which is registered
nowhere on purpose. A verifier meeting it should check the core gates, report
that gates 2 and 5 belong to a predicate it does not know, and not describe the
run as clean.

The `solidity`, `dataset` and versioned `state-fixture` fixtures use the four types
this build registers, so they exercise each predicate's own gates as well as the
core ones. Gates 2 and 5 mean different things for a state fixture than for a
dataset release or a contract release, so each type carries its own breaching
fixtures for them.

## The naming convention

The suite reads the names, so they have to be right:

- `pass-<what>.json` verifies clean. Every gate holds.
- `fail-gate<n>-<what>.json` breaches gate `n` and no other gate.
- `fail-check-<check>-<what>.json` breaches a check that carries no gate number,
  and no other check.

Gates 2 and 5 are numbered. The other checks a predicate adds carry no number,
so they need the third form: coverage and inputs on a dataset release, audits and
deployments on a contract release, and the field-shape check on either. Without
it those checks shipped with no fixture at all.

Four completeness tests hold the set together. Each core gate has a breaching
fixture. Each registered predicate has a passing fixture, and a breaching fixture
of its own type for every numbered gate it owns. Every unnumbered check any
registered predicate exposes has one too. A fifth test asserts that each
breaching fixture fails exactly the gate or check its name claims, which catches
a fixture that breaks two things at once and would pass for the wrong reason.

## What is here

| Fixture | Contract | What it shows |
| --- | --- | --- |
| `pass-minimal.json` | Core | The smallest statement that holds: one subject, an empty claims block and an empty commands block. Empty is a record; absent is not |
| `pass-absence-recorded.json` | Core | A passed claim, a skipped one with its reason, a timed-out one with its reason, and both determinism classes |
| `pass-in-an-unsigned-envelope.json` | Core | The same shape inside a DSSE envelope with no signatures, verified and reported unsigned |
| `fail-gate1-claim-names-a-branch.json` | Core | A claim naming `refs/heads/main` instead of a digest |
| `fail-gate1-digest-not-in-subject.json` | Core | A claim naming a digest the statement does not cover |
| `fail-gate3-no-claims-block.json` | Core | A predicate with no claims block at all |
| `fail-gate3-no-disposition.json` | Core | A claim that does not say what happened to it |
| `fail-gate3-skipped-without-reason.json` | Core | Work marked skipped with no reason given |
| `fail-gate4-conclusion-key.json` | Core | A verdict smuggled in as `summary.verdict` |
| `fail-gate6-no-determinism.json` | Core | A recorded command with no determinism class |
| `fail-gate6-exact-without-output-digest.json` | Core | An exact command with nothing for a replay to compare against |
| `fail-gate7-self-asserted-verification.json` | Core | A payload asserting inside the signed bytes that it was verified |
| `pass-solidity-release.json` | Solidity v1 | A complete Solidity release: a skipped fuzz campaign, an audit naming its revision, an unconfirmed deployment |
| `pass-solidity-first-release.json` | Solidity v1 | The same shape with a null baseline and a reason |
| `fail-gate2-compiler-version-only.json` | Solidity v1 | A build described by a compiler version and nothing else |
| `fail-gate2-source-without-commit.json` | Solidity v1 | A source record with a tree digest and no commit |
| `fail-gate5-baseline-without-digest.json` | Solidity v1 | A comparison against a release named but not identified |
| `fail-gate5-content-against-null-baseline.json` | Solidity v1 | Added functions listed against a baseline the statement says does not exist |
| `fail-gate5-solidity-first-release-unnamed-current.json` | Solidity v1 | A first release carrying a current side with no name and a digest the statement does not cover, which gate 5 skipped before this fixture existed |
| `fail-check-audits-solidity-without-covered-revision.json` | Solidity v1 | An audit report attached to a release without naming the revision it covered |
| `fail-check-deployments-solidity-without-confirmation.json` | Solidity v1 | A deployment address printed without saying whether anything confirmed it against a chain |
| `fail-check-deployments-solidity-confirmation-is-not-a-boolean.json` | Solidity v1 | `"null"` where the confirmation belongs. The field records a decision, and a value read for truthiness turned a deployment nobody checked into one the report counted as confirmed |
| `pass-dataset-release.json` | Dataset v1 | A complete dataset release: two released files with record counts, one input digested and one recorded absent with its reason, a coverage interval with a gap, and a comparison against the previous release |
| `pass-dataset-first-release.json` | Dataset v1 | The same shape with a null baseline, its reason, and an empty gap list that asserts the producer looked |
| `fail-gate2-dataset-producer-without-parameters.json` | Dataset v1 | A producer named with a version but no digest over the parameters it was given |
| `fail-gate5-dataset-baseline-without-digest.json` | Dataset v1 | A dataset comparison against a release named but not identified |
| `fail-check-coverage-dataset-no-gaps-block.json` | Dataset v1 | A coverage interval with no gaps block, which reads as complete without saying so |
| `fail-check-inputs-dataset-locator-only.json` | Dataset v1 | An input with a locator and neither a digest nor a reason for not having one |
| `fail-check-predicate-fields-dataset-unknown-field.json` | Dataset v1 | A dataset predicate carrying a field the type does not define |
| `pass-state-fixture.json` | State fixture v1 | A Lazarus state fixture published as a statement: the pinned block with its state root, four components, the three evidence counts, and a replay that reaches no network. The digests, byte counts and counts are the ones Lazarus wrote for `plugins/lazarus/examples/goldfinch-v0` |
| `fail-gate2-state-fixture-hex-block-number.json` | State fixture v1 | A block number written as the hex quantity string a Lazarus manifest carries, which is right on the wire and orders as text |
| `fail-gate5-state-fixture-unnamed-current.json` | State fixture v1 | A first capture whose current side has no name and a digest the statement does not cover |
| `fail-check-evidence-state-fixture-proved-without-a-state-root.json` | State fixture v1 | Two proof-backed records counted with no state root to have proved them against. Gate 2 passes, which is the point: the rule reaches statements the pin check accepts |
| `fail-check-replay-state-fixture-reaches-network.json` | State fixture v1 | A replay recorded as reaching a network, which is not the boundary a fixture exists to be |
| `pass-state-fixture-proved-nothing.json` | State fixture v1 | A capture that recorded a header and some responses and proved nothing. It carries no state root, because there was nothing to prove against, and says so with a zero proof-backed count and a skipped claim rather than leaving the field quietly absent |
| `fail-gate2-state-fixture-no-block-hash.json` | State fixture v1 | A pin with a chain and a height and no hash, which does not say which of two blocks at that height |
| `fail-gate2-state-fixture-component-not-a-subject.json` | State fixture v1 | A component the predicate describes and the statement does not cover |
| `fail-gate5-state-fixture-baseline-without-digest.json` | State fixture v1 | A comparison against an earlier capture named but not identified |
| `fail-check-evidence-state-fixture-class-absent.json` | State fixture v1 | An evidence class left out, which reads as nothing of that kind having been captured rather than as nobody having said |
| `fail-check-evidence-state-fixture-count-is-a-boolean.json` | State fixture v1 | A count of `true`, which is an integer in Python and would read as one record |
| `fail-check-replay-state-fixture-canonical-chain-claim.json` | State fixture v1 | A fixture claiming its pinned block is on the canonical chain, which nothing in either tool establishes |
| `fail-gate2-state-fixture-unset-block-hash.json` | State fixture v1 | The all-zero hash, which matches the shape and identifies nothing |
| `fail-gate2-state-fixture-component-path-leaves-the-fixture.json` | State fixture v1 | A component path with a `..` segment, which resolves outside the fixture a reader has |
| `fail-check-evidence-state-fixture-count-over-the-ceiling.json` | State fixture v1 | A count above the ceiling Lazarus's own manifest schema sets |
| `fail-check-replay-state-fixture-zero-is-not-false.json` | State fixture v1 | `0` where `false` belongs. The field records a decision and `0` is not in its vocabulary |
| `pass-state-fixture-v2.json` | State fixture v2 | A manifest-v2 fixture with independent state and receipt roots, four evidence counts, a local-only replay boundary and no transaction-hash attribution |
| `fail-gate2-state-fixture-v2-backslash-path.json` | State fixture v2 | A component path containing a backslash, which another host can interpret as a separator |
| `fail-gate2-state-fixture-v2-dot-segment-path.json` | State fixture v2 | A non-canonical component path carrying a dot segment instead of one portable file name |
| `fail-gate2-state-fixture-v2-invisible-segment-path.json` | State fixture v2 | A component path whose final segment is only U+200B, which names a POSIX file and displays nothing to a reader |
| `fail-gate2-state-fixture-v2-whitespace-segment-path.json` | State fixture v2 | A component path with a whitespace-only segment, which names nothing a reader can see |
| `fail-gate2-state-fixture-v2-malformed-receipts-root.json` | State fixture v2 | A malformed `receipts_root`; the zero receipt-proof count does not excuse a root that is present but invalid |
| `fail-gate5-state-fixture-v2-empty-components-without-baseline.json` | State fixture v2 | An empty component-delta section beside an explicitly null baseline |
| `fail-gate5-state-fixture-v2-missing-baseline.json` | State fixture v2 | A comparison that omits the required explicit baseline side |
| `fail-gate5-state-fixture-v2-missing-current.json` | State fixture v2 | A comparison that omits the required current side |
| `fail-gate5-state-fixture-v2-unnamed-current.json` | State fixture v2 | A version 2 first capture whose current side names no fixture |
| `fail-check-evidence-state-fixture-v2-receipts-without-root.json` | State fixture v2 | A positive `receipt_trie_proved` count with no `receipts_root`; the state-proof rule remains independent |
| `fail-check-subject-names-state-fixture-v2-duplicate-name.json` | State fixture v2 | Two in-toto subjects with one reader-visible name, leaving a name-based consumer unable to distinguish their digests |

## Running them

```bash
python3 scripts/ariadne.py verify tests/fixtures/conformance/pass-absence-recorded.json
python3 scripts/ariadne.py verify tests/fixtures/conformance/fail-gate3-skipped-without-reason.json
```

Exit 0 for the first, 1 for the second, with the failing line naming the gate.
The whole set runs under:

```bash
python3 -m unittest discover -s tests -t .
```

## What passing the whole set proves

One example per rule family, not one per rule. A verifier that passes every fixture
here has been shown each *kind* of refusal: a required field absent, a value of the
wrong type, a value that satisfies the shape and identifies nothing, a digest the
statement does not cover, a path that resolves outside the tree, a field the type does
not define, and each numbered gate and named check breached on its own.

It has not been shown every field. The state-fixture predicate refuses far more
distinct things than the fourteen its breaching fixtures cover. The fourteen cover
every family. Rules distinctive to the type appear on their own: the unset hash,
the count ceiling taken from Lazarus, `0` in place of
`false`, and a proof-backed count with no state root. An implementation that checked
`block_number` and forgot `chain_id` would pass everything here.

The ratio is deliberately left unstated. Counting a predicate's distinct refusals
means choosing which messages count as one rule, and any number written here would be
the author's enumeration rather than something a reader could recompute. Fourteen is
countable; what it is fourteen out of is not.

That is a deliberate limit rather than an omission. A fixture per rule would triple
this directory and teach a reader no more, because the fixtures are read as examples
and the rules are written down in each predicate's document. The unit suites are where
every field is exercised: `tests/test_state_fixture.py` and its siblings, which is
where a rule with no fixture is still held.

Minimality is part of the teaching, and it holds for the state-fixture set rather
than for the directory. Twelve of its fourteen breaching fixtures differ from
`pass-state-fixture.json` in exactly one leaf, so a reader diffing the pair sees the
rule and nothing else. A test holds them there.

The two exceptions are both gate 5, and both for the same reason: a comparison
against a baseline has to name a current side, so no single change reaches that
branch. `fail-gate5-state-fixture-unnamed-current.json` differs in two leaves and
`fail-gate5-state-fixture-baseline-without-digest.json` in four.

The older core fixtures are written against `pass-minimal.json` instead, which is
the smallest statement that holds rather than a near sibling, so they differ by up
to eight leaves. That is a different and equally deliberate choice: a core gate is
demonstrated on the least statement that can carry the breach, not on a full release
with one thing changed.

One warning for anyone diffing these files with a tool. Two of the fixtures change
only a value's type -- `header_bound` from `1` to `true`, and `reaches_network` from
`false` to `0` -- and a comparison written in Python will call those pairs equal,
because `True == 1` and `0 == False`. The rules they breach exist because of that
same equality. A differ that ignores types reports these fixtures as identical to
the one they breach against.

## What the gates do not catch

Worth stating, so nobody reads a clean run as more than it is.

Gates 4 and 7 check keys, not prose. A predicate cannot carry `verdict` or
`verified` as a field another tool would read as structured data, and that is
the whole of it. A `reason` string reading "looks fine to me" passes, because
any wordlist over free text would fail honest sentences far more often than
dishonest ones.

Gate 1 checks that a claim names a digest the statement covers. In a statement
with several subjects it cannot tell that a claim about one names another.

None of these gates can tell whether a producer meant well, and none is asked
to. They refuse the shapes that let a careless statement read as a careful one.

## Using them elsewhere

The fixtures are plain in-toto statements and DSSE envelopes. Nothing in them
depends on this implementation, so another verifier can read the same files and
should reach the same verdicts. If yours disagrees with one, the disagreement is
worth reporting either way: a fixture can be wrong.
