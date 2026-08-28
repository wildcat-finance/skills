---
name: ariadne
description: >
  Read and write the evidence statements that keep a release joined to the
  record behind it: an in-toto statement, optionally inside a DSSE envelope,
  with a predicate registry and gates that keep absence visible. Use when
  someone hands over an attestation and asks what it actually covers, when a
  release needs evidence a stranger can check rather than a badge, or when a
  new kind of artefact needs a predicate of its own. Ariadne neither signs nor
  verifies signatures; those operations belong to cosign.
metadata:
  version: "2.2.0"
---

<p align="center">
  <img src="../../assets/characters/ariadne.png" width="1200">
</p>

# Ariadne

## Frontier

Ariadne owns its own attestation-predicate frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Ariadne writes and checks the evidence statement that joins a released artefact digest to the work actually recorded behind it.

**Current frontier.** The grounded-agent predicate remains unimplemented; the state-fixture predicate now ships with its schema, gates, conformance fixtures and a capture path that reads a Lazarus fixture's evidence counts rather than recomputing them.
<!-- marketplace-context:end -->

A release publishes a claim. The evidence behind it sits somewhere else, joined
by a URL and a promise: the compiler that produced the bytecode, the test run,
the fuzz campaign, the audit and its scope, the deployment. Ariadne writes the
join down as a statement whose subject is a digest, so a reader can check the
binding without trusting whoever assembled it.

Lazarus can supply a state-fixture release; Alexandria, Tabularium, or Berean
can supply other release subjects and evidence. Ariadne binds and gates those
exact inputs. It neither reruns a sibling's work nor upgrades its result, and
signature creation and verification remain with cosign.

Synkrisis is the partly built comparison boundary for validated run
observations. It writes a cohort and findings. Ariadne may bind such a
comparison artefact to evidence, but that binding will not establish cause or
authorise action.

`$SKILL_DIR` is the directory holding this file. The tool lives at
`$SKILL_DIR/../../scripts/ariadne.py`; resolve it from where you loaded this
skill.

## Day to day

**Engineering.** A release goes out and someone asks, six months later, which
commit the deployed bytecode came from and whether the audit covered it. The
statement answers from its own contents rather than from a changelog nobody
updated.

**Security.** An attestation arrives with a release. `inspect` says what it
covers and whether its signatures were checked, and says plainly that this tool
did not check them. What it never does is print an author it has not verified.

**Research and data.** A dataset or a chain-state fixture needs the same thread
as a contract release: the sources read, the block boundary, what was covered
and what was not. Both have a predicate now, each one a module rather than a
fork, which is what an artefact-neutral core is for.

## The commands

```bash
python3 scripts/ariadne.py predicates

python3 scripts/ariadne.py capture solidity-release \
  --project <dir> --previous <dir> --previous-name v1.0.0 \
  --repository <url> --commit <40-hex> --out release.json

python3 scripts/ariadne.py capture-dataset \
  --release <dir> --name goldfinch-credit-events-v2 \
  --coverage-dimension block --coverage-start 11370000 --coverage-end 15000000 \
  --gap 'start=12000000,end=12000100,reason=<why this range is not described>' \
  --producer-tool tabularium --producer-version 0.3.0 \
  --producer-command python3 --producer-command scripts/tabularium.py \
  --previous <dir> --previous-name goldfinch-credit-events-v1 --out release.json

python3 scripts/ariadne.py capture-state-fixture \
  --fixture <dir> --name goldfinch-v0 \
  --capture-tool lazarus \
  --capture-command python3 --capture-command scripts/lazarus.py \
  --first-capture-reason '<why there is no earlier capture of this block>' \
  --out fixture.json

python3 scripts/ariadne.py inspect <statement-or-envelope.json>

python3 scripts/ariadne.py verify <statement-or-envelope.json>

python3 scripts/ariadne.py replay <statement.json> [--allow-execution --project <dir>]
```

`predicates` lists the predicate types this build understands. Four are registered:
`https://ariadne.wildcat.finance/solidity-release/v1`,
`https://ariadne.wildcat.finance/dataset/v1`,
`https://ariadne.wildcat.finance/state-fixture/v1`, and
`https://ariadne.wildcat.finance/state-fixture/v2`. A statement of any other type
still parses and still gets its core gates.

`capture` reads a Foundry project's build output into a release statement that
`verify` accepts unedited. It does not decide whether your tests passed: a
result arrives as a stated disposition, and leaving it out records `skipped`
with a reason saying nothing was supplied.
[`docs/capturing-a-release.md`](../../docs/capturing-a-release.md) has the
flags.

`capture-dataset` reads a dataset release directory into a dataset statement. It
digests every file, counts the records in line-delimited JSON, and refuses a file
whose count is neither derivable nor stated rather than guessing one. Coverage, inputs and the
producer come from the caller, because a directory of records does not say which
interval it was meant to describe, what it was built from, or what built it. None
of the three has a default: one would put this tool's own name in the field gate 2
reads as what made the files. With `--previous` it
identifies both sides of the comparison and records no record-level differences,
because telling which records changed needs a record identity it does not have.
[`docs/capturing-a-dataset.md`](../../docs/capturing-a-dataset.md) has the flags.

`capture-state-fixture` reads a Lazarus fixture directory into a state-fixture
statement. It takes the evidence counts from the manifest rather than computing
them, because Lazarus is the only thing that knows which of its records were checked
against the state root, and a capture that recomputed one and got a larger number
would upgrade recorded evidence into proved evidence. It checks the manifest against
the directory in both directions: a component the manifest declares and the directory
lacks is refused, and so is a file the directory holds and the manifest does not
declare, because the fixture digest would not cover it. Hex quantities become the
integers this predicate compares. `reaches_network` and `canonical_chain_claim` are
written false and are not flags, because Ariadne reaches no network and neither tool
re-derives a chain, so offering a flag would imply otherwise.
[`docs/capturing-a-state-fixture.md`](../../docs/capturing-a-state-fixture.md) has
the flags.

`inspect` reads either a bare in-toto statement or a DSSE envelope wrapping
one, and reports the predicate type, whether that type is registered here, the
subjects with their digests, and what is known about the signatures.

`verify` runs the gates and prints a line for each. When the predicate type is
one this build does not know, it says gates 2 and 5 went unchecked rather than
reporting a clean run. A document that arrived from elsewhere is bounded first:
a size cap, a depth cap counted before parsing, and a refusal of duplicate keys,
all adjustable with `--max-bytes` and `--max-depth`.

`replay` re-runs the commands a statement marks `exact`. Without
`--allow-execution` it prints the plan and runs nothing, which is the default
because the commands inside a statement are somebody else's data rather than
instructions. It never uses a shell, refuses a command whose arguments were
redacted at capture, and refuses a program name carrying a path separator.

Exit codes: 0 success, 1 a gate was breached, 2 usage or validation error.

## The block every predicate carries

Two lists, which the core gates read and a predicate fills in:

- `claims`. What was checked. Each names the subject digest it covers and its
  disposition, one of `passed`, `failed`, `skipped`, `timed_out` or `redacted`.
  Anything other than `passed` carries a reason, because the reason is the
  record.
- `commands`. What was run. Each carries its `argv` and a determinism class of
  `exact` or `nondeterministic`. An `exact` command carries the digest of its
  output, since otherwise a replay would have nothing to compare against.

## What the core refuses

These are properties of the code rather than reminders:

- A subject with no digest, a digest that is not lowercase hex, a truncated
  digest, an empty digest set, or a set carrying only unsupported algorithms.
- A statement whose `_type` is not `https://in-toto.io/Statement/v1`, or whose
  `predicateType` is not a URI.
- A base64 payload mixing the standard and URL-safe alphabets, because it is
  the output of neither encoder and guessing is how a payload gets decoded two
  ways.
- Following a symlink while digesting a source tree. It raises rather than
  either following the link out of the tree or quietly skipping a file that was
  there.

Subjects match by digest and never by name. A verifier that matched by name
would accept a claim pointing at a label instead of at bytes.

## The gates

Seven. Five belong to the core and every predicate inherits them; two are shape
a predicate fills in.

| Gate | Owner | What it holds |
| --- | --- | --- |
| 1 Every claim names its subject | core | A result tied to a repository or a branch is rejected; it names the digest it covers |
| 2 The environment is recoverable | predicate | A bare tool version is not a build description |
| 3 Absence stays visible | core | Skipped, failed, timed-out and redacted work stays in the statement |
| 4 Results are not upgraded into conclusions | core | A passing property records the property and the run, not that the artefact is safe |
| 5 Deltas name both sides | predicate | A comparison fails when either baseline cannot be identified exactly |
| 6 Replay distinguishes deterministic work | core | Bytecode can require an exact match; a fuzz campaign's coverage cannot |
| 7 Signature verification is external | core | An unsigned statement is labelled unsigned and no statement receives an implied author |

The five core gates run for any predicate, including a type this build has
never heard of. Gates 2 and 5 come from the predicate: the Solidity release
predicate implements both, and for a type this build does not know, `verify`
says they went unchecked rather than passing over them in silence.

`tests/fixtures/conformance/` holds a statement that passes and, for each core
gate, one that breaches it. [`docs/conformance.md`](../../docs/conformance.md)
describes the set for anyone writing another producer or verifier.

## What this never does

- Hold a signing key, or produce a signature. `cosign attest` signs the
  envelope and `cosign verify-attestation` checks it.
- Report that a signature was verified. This tool checks none, and says so
  every time it is asked about one.
- Mint a new envelope. The statement is in-toto's and the envelope is DSSE's,
  deliberately, so a verifier written by someone else can read what this
  writes.
- Re-serialise a payload before checking it. A signature covers bytes, and a
  verifier that re-encodes first is checking a document its signer never saw.
- Record a result nobody supplied. Capture writes `skipped` with a reason
  rather than guessing at a run it did not see, and every deployment it writes
  says nothing confirmed it against a chain.

## The Solidity release predicate

The first shape on the core. Its subject is compiled bytecode, and it carries
the source and commit, the compiler and its settings, the creation and runtime
digests of every release subject, the ABI, selector and storage deltas against
the previous release, the audits with the revision each covered, and the
deployments with whether anything confirmed them against a chain. Nothing here
reaches a network, so that last field always says nothing did.

[`docs/solidity-release.md`](../../docs/solidity-release.md) describes it field
by field, and `schemas/solidity-release-v1.json` ships for producers that are not
this tool.

Type URI: `https://ariadne.wildcat.finance/solidity-release/v1`.

## The dataset predicate

The second shape. Its subject is a released data file, and it carries the
producer with its version and argv, the inputs with a digest or a recorded
reason for not having one, every released file with its digest and record count,
the interval the release claims to describe with the gaps inside it, and the
record-level differences against the previous release.

Two checks are its own. Coverage refuses an interval with no `gaps` key, a gap
outside the bounds, a gap without a reason and a pair of gaps that overlap, so an
interval printed with no gaps cannot read as complete. Inputs refuses an input
carrying neither a digest nor a disposition, because a locator alone records
nothing about what was read. Coverage bounds are whole numbers.

[`docs/dataset.md`](../../docs/dataset.md) describes it field by field, and
`schemas/dataset-v1.json` ships for producers that are not this tool.

Type URI: `https://ariadne.wildcat.finance/dataset/v1`.

## The state-fixture predicate

The third shape has two explicit versions. Its subject is a component of a captured
Lazarus fixture. Both carry the block pin, capture tool, every component with its
digest and byte count, evidence counts, and replay boundary. Version 1 carries the
three legacy evidence classes. Version 2 adds `receipts_root`,
`receipt_trie_proved`, and `provider_independence_claim`.

Two checks are its own. Evidence requires every class key and a non-negative whole
number for each. A positive `proof_backed` count independently requires
`state_root`; a positive `receipt_trie_proved` count in version 2 independently
requires `receipts_root`. Neither root or count grants the other proof class.
Replay requires its versioned fields to be exactly false. Version 2 also requires
an empty `commands` array, because its verification boundary reads local files
only.

The evidence check is the point of the type. Lazarus distinguishes what was proved
against the state root, what was proved against the receipt trie, and what an
endpoint merely said. `receipt_trie_proved` covers only the scoped consensus
receipt and log-projection relations. It does not prove a transaction-hash
attribution; transaction hashes and RPC decorations remain recorded data.

Numbers are integers. A Lazarus manifest writes the chain id and the block number
as hex quantity strings, which order as text, so this type refuses the wire form
rather than comparing it.

[`docs/state-fixture.md`](../../docs/state-fixture.md) describes both versions
field by field. `schemas/state-fixture-v1.json` and
`schemas/state-fixture-v2.json` ship for producers that are not this tool.

Type URIs: `https://ariadne.wildcat.finance/state-fixture/v1` and
`https://ariadne.wildcat.finance/state-fixture/v2`.

## Examples

[`examples/`](../../examples) holds two attestations over the fixture project:
a clean release, and one carrying a fuzz campaign that timed out and an audit
covering an earlier revision. Both verify. The second is the more useful one to
read: a format whose only examples are clean releases teaches producers to make
their releases look clean.

`examples/tampered/` holds a copy of each with one thing changed, and each
fails a named gate.

## Where it stops

Named so the edge is visible rather than implied.

The registry holds four predicates. The grounded-agent predicate is specified and
not implemented here, so a statement of that type verifies its core gates and is
told which gates went unchecked.

Nothing confirms a deployment against a chain, nothing signs, and nothing runs
as a GitHub Action. Each of those is a deliberate boundary rather than an
omission: the first needs a node, the second needs key custody this tool
declines, and the third needs a workflow that owns neither.

## Promise Machine contract

### ariadne-capture-statement

- Promise: A successful capture command writes an in-toto statement whose subjects, predicate fields and preserved absences are derived from the named local artefact and caller-supplied boundary.
- Evidence: The capture command, local input bytes, computed subject and component digests, registered predicate schema and the emitted statement that `verify` accepts unedited.
- Evidence classes: recorded, checked, recomputed
- Boundary: Capture records caller-supplied claims and local bytes; it does not decide that tests passed, establish chain facts, verify a publisher or turn a producer assertion into truth.
- Authorises: Use of the statement as a derived evidence-binding artefact for later inspection, verification or external signing.
- Consequence: 1
- Refuses: Inventing a result, coverage boundary, evidence count, producer, digest or earlier release that the inputs do not establish.
- Recovery: Supply the missing input or explicit absence reason, correct the local artefact or boundary and rerun the relevant capture command.
- Exceptions: none

### ariadne-inspect-statement

- Promise: A successful `inspect` identifies the statement or envelope's predicate registration, subjects, digests and signature-verification status without implying an unchecked author.
- Evidence: The bounded parsed bytes, in-toto or DSSE structure, predicate registry lookup and the inspection output.
- Evidence classes: recorded, checked
- Boundary: Inspection reports document contents and registration only; it does not run predicate gates, verify a signature, authenticate an actor or establish the assertions' truth.
- Authorises: Presentation of the bounded inspection result with unsigned or unchecked status visible.
- Consequence: 0
- Refuses: Naming a signer, publisher or verified predicate result when the corresponding external verification or gate run did not occur.
- Recovery: Obtain external signature evidence or run `verify` for predicate gates, then report each result as a separate relation.
- Exceptions: none

### ariadne-verify-statement

- Promise: A successful `verify` establishes that the named statement passed every applicable core and registered-predicate gate, while unknown-predicate gates remain explicitly unchecked.
- Evidence: The exact statement or envelope bytes, bounded parser result, subject digests and the complete named gate report from `ariadne.py verify`.
- Evidence classes: checked, recomputed
- Boundary: Verification establishes the declared evidence binding only; it does not authenticate a publisher, prove underlying claim truth, confirm a deployment or make unchecked gates pass.
- Authorises: With separate release authority, attaching the verified statement to the exact subject digest as inspectable release evidence.
- Consequence: 3
- Refuses: Publication as a complete or authenticated attestation when a gate failed, was unchecked, or no external signature verifier established identity.
- Recovery: Inspect the failed or unchecked gate, repair or extend the predicate evidence, rerun verification and obtain external signature verification when identity matters.
- Exceptions: none

### ariadne-replay-command

- Promise: A successful execution-enabled `replay` runs only commands marked exact through argument-vector execution and compares their declared outputs without invoking a shell.
- Evidence: The verified statement, replay plan, explicit `--allow-execution` authority, executed argv records and exact output-digest comparisons.
- Evidence classes: checked, recomputed, recorded
- Boundary: Replay covers only eligible exact commands in the named project and does not make nondeterministic, redacted, path-bearing or hostile commands safe.
- Authorises: Execution of the accepted replay plan in the caller-selected project and reporting of its exact output comparisons.
- Consequence: 2
- Refuses: Executing by default, using a shell, running an ineligible program name, or describing a plan-only run as execution evidence.
- Recovery: Review the printed plan, remove or correct the unsafe command record, choose a controlled project and rerun with explicit execution authority.
- Exceptions: none
