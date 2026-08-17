# Wildcat Labs skills

Agent skills written and used by [Wildcat Labs](https://wildcat.finance).

This is where we publish workflows that have earned more than a prompt. Each
plugin has a narrow job, a clear trigger and enough code, evidence and tests to
make its result checkable. Read a plugin before running it: skills can execute
commands and edit source.

## Choose the job, then the plugin

The names are memorable; the boundaries matter more. This is the short map of
what each plugin does, where it hands work over and what is honestly left to
build.

| Plugin | Use it for | Try this instead | Current frontier |
| --- | --- | --- | --- |
| [Alexandria](./plugins/alexandria) | Preserving heterogeneous lending-source bytes, then deriving and querying reviewed credit views. | Tabularium for semantic event mapping; Probitas for a dossier. | Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented. |
| [Ariadne](./plugins/ariadne) | Binding an artefact digest to build, test, review and deployment evidence. | An external Sigstore or cosign verifier for signatures. | The dataset predicate is the first unimplemented predicate; state-fixture and grounded-agent predicates also remain unimplemented. |
| [Hermes](./plugins/hermes) | Measuring one Solidity gas-optimisation class through fail-closed Foundry checks. | Pandects or the audit skills for broader behavioural and security work. | No complete, reproducible live Wildcat evidence bundle is published. |
| [Hexaemeron](./plugins/hexaemeron) | Running an explicit, receipted delivery loop, ranking frontier work with Kronos, or using its fuzzing, audit and prose skills separately. | A named bundled skill when the controller is unnecessary. | The bundled Solidity audit suite has not yet been exercised in a published end-to-end Fiat delivery. |
| [Lemma](./plugins/lemma) | Producing source-linked chunks from Solidity compiler inputs or Markdown. | An embedding, index, retrieval or answering system for every later stage. | Callable-surface ABI validation does not independently check return types or state mutability. |
| [Lazarus](./plugins/lazarus) | Capturing a finite fixed-block Ethereum fixture, checking proof-backed state and replaying exact requests without fallback. | Alexandria for a lending archive; Tabularium for event interpretation. | Preservation-pipeline integration and an Ariadne state-fixture predicate remain unimplemented. |
| [Pandects](./plugins/pandects) | Supplying executable credit laws, broken specimens and reduced counterexamples. | Fizz for a protocol-specific fuzz harness. | No law prevents fees from reducing pooled lender claims below amounts owed on open withdrawal batches. |
| [Probitas](./plugins/probitas) | Building a sourced counterparty dossier from declared addresses, without identity inference or a Wildcat verdict. | Alexandria for archived inputs. | Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented. |
| [Tabularium](./plugins/tabularium) | Mapping preserved venue-native records into reproducible, venue-qualified credit events. | Alexandria for raw harvesting; Probitas for a dossier. | Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented. |

## Plugins

### Alexandria

[Alexandria](./plugins/alexandria) keeps heterogeneous lending data unchanged,
then derives only the credit rows a reviewed mapping can defend.

Raw GraphQL responses and archive logs do not need one payload schema. Each
release stores the original bytes under their SHA-256, names the source, chain,
scope, finality class and counted coverage, and verifies offline. Goldfinch and
Clearpool releases can then produce a narrow Tabularium view without turning
the archive itself into an interpretation layer.

The Compound v3 Phase 0 release pins 28 production Comet deployments at one
upstream commit and preserves a bounded old-and-recent Ethereum USDC RPC
corpus. Its offline checker binds archive access, nested calls,
transaction-start state, proxy implementation code, ordered storage writes and
a provider-reported finalized boundary. It is a one-provider method proof, not
an interval history or independent chain proof.

The SQLite address index is disposable. Every query rechecks its schema,
logical digest and exact release-backed contents before returning rows. The
explicit Probitas route keeps both venue and archive provenance and leaves all
unharvested registry venues visible as gaps.

Alexandria includes:

- the standard-library [`alexandria.py`](./plugins/alexandria/scripts/alexandria.py)
  ingest, verify, derive, index and query command;
- raw-release, coverage, credit-row, query and demonstration schemas;
- registered Goldfinch and Clearpool mappings with exact source and context
  selectors;
- the offline [`credit-history-v0`](./plugins/alexandria/examples/credit-history-v0/README.md)
  path through Probitas's five gates; and
- a checked-in [Compound v3 Phase 0 raw release](./plugins/alexandria/examples/compound-v3-phase0-v0/README.md),
  separate explicit network capture command and pinned
  [production harvest specification](./plugins/alexandria/docs/compound-v3-harvest.md).

#### Day to day

**Developers.** Preserve a protocol response now, with its gaps and usage
restrictions, then rebuild the same release after the endpoint is gone.

**Security and audit.** Check that every derived row resolves to the raw object
and mapping rule that assigned its meaning. An unknown implementation or
selector stays unsupported.

**Finance.** Query a counterparty address across the archived venues without
letting an unharvested venue read as clean history.

### Ariadne

[Ariadne](./plugins/ariadne) binds a release to the evidence behind it, in a statement another person can check.

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

Ariadne includes:

- the executable [`ariadne.py`](./plugins/ariadne/scripts/ariadne.py) capture, verifier and replay, standard library only;
- the [Solidity release predicate](./plugins/ariadne/docs/solidity-release.md) and [its published schema](./plugins/ariadne/schemas/solidity-release-v1.json), tied together by a test so the two cannot drift;
- capture from a Foundry build that reads the compiler's own output, refuses to decide whether your tests passed, and scrubs a build command before recording it;
- conformance fixtures with a passing statement and one breach per core gate, for anyone writing another producer or verifier;
- two example attestations, one of them carrying a fuzz campaign that timed out and an audit covering an earlier revision; and
- 310 tests, including a set that fails when a shipped document drifts from the code it describes, and an audit log ([`audit/AUDIT.md`](./plugins/ariadne/audit/AUDIT.md)) recording every round.

#### Day to day

**Developers.** A release goes out, and six months later somebody asks which commit the deployed bytecode came from and whether the audit covered it. `capture` reads that out of the build you already ran, and the statement answers from its own contents rather than from a changelog nobody updated.

**Security and audit.** An attestation arrives with a release. `verify` says which gates hold, which went unchecked and why, and states plainly that it checked no signature. `replay` re-runs the deterministic half and compares the artefacts, so the recorded digests are something you can test rather than something you accept.

### Hermes

[Hermes](./plugins/hermes) treats Solidity gas work as a verification problem.

Gas changes are easy to praise and surprisingly easy to get wrong. Hermes takes one optimisation class at a time through a fail-closed Foundry run:

1. Seal a clean baseline with `forge snapshot` and a green `forge test`.
2. Apply exactly one declared optimisation class.
3. Prove the saving with `forge snapshot --diff`, reject every positive delta, and capture `forge test --gas-report`.
4. Run the full test suite again with the pinned fuzz seed, then once more unpinned.
5. Diff storage layouts and method identifiers for every recorded contract. Any layout change to a hook, role provider, proxied contract or other protected contract aborts the run.
6. For unchecked arithmetic that can affect persistent state, asset accounting, external calls, permissions, or rounding, run the existing targeted differential or property test before accepting the candidate.

A candidate only clears Hermes when every gate clears. The run leaves behind `result.json`, command logs, gas comparisons, the Solidity diff, storage layouts and method maps, so the number and the safety case can be reviewed together.

Hermes includes:

- the executable [`hermes.py`](./plugins/hermes/skills/hermes/scripts/hermes.py) harness;
- a catalogue of [12 optimisation classes](./plugins/hermes/skills/hermes/references/optimisation-catalogue.md);
- Codex metadata for explicit or automatic invocation; and
- a test suite covering accepted runs and representative failures across Gates 2 to 6.

#### Day to day

**Developers.** A gas change shaves a few hundred units off a hot path and nobody can say whether behaviour moved with it. Run Hermes on that one optimisation class and the review arrives with the snapshot diff, both fuzz passes, the storage layout comparison and a `result.json`, rather than a number and an assurance.

**Security and audit.** A gas change arrives from outside the team. Instead of reading it for intent, put it through Gate 5 to see whether any protected contract's storage layout or method identifiers moved, and Gate 6 for unchecked arithmetic that reaches persistent state.


### Hexaemeron

[Hexaemeron](./plugins/hexaemeron) takes a topic from nothing to a working prototype through one receipted loop.

Let there be light. A deterministic controller (`hexctl`) decides what comes next and refuses to advance without a receipt; state and a hash-chained ledger survive context resets, so resume is the same command.

1. Study the topic and write a linted study file.
2. Derive a runbook of discrete, self-contained steps.
3. Implement the least complicated construction that satisfies each runbook step.
4. Run the vendored Pashov suite (`x-ray`, `solidity-auditor`, `fizz`) in rounds until a round comes back clean or the remaining leads are judged not worth another pass, fixes on a stacked branch.
5. Rewrite every shipped document and the PR text through the bundled `imprimatur` lint and `vulgate` voice mask.
6. Push the PR and move to the next step.

Hexaemeron includes:

- the executable [`hexctl.py`](./plugins/hexaemeron/skills/fiat/scripts/hexctl.py) controller with a tamper-evident ledger (`verify` proves both chain and state);
- the [`imprimatur`](./plugins/hexaemeron/skills/imprimatur) three-tier prose lint and the [`vulgate`](./plugins/hexaemeron/skills/vulgate) voice mask, invokable on their own;
- [`kronos`](./plugins/hexaemeron/skills/kronos), which ranks eligible held frontier jobs and loops complete Fiat runs until none remain;
- the Pashov Audit Group suite vendored verbatim (MIT; `LICENSE` and `NOTICE.md` in each skill directory);
- Codex metadata for explicit or automatic invocation; and
- 61 controller and contract tests, 55 lint tests, and a fuzz-audit log ([`audit/AUDIT.md`](./plugins/hexaemeron/audit/AUDIT.md)) covering the controller's own surfaces.

#### Day to day

**Developers.** A half-formed idea and a week to find out whether it holds. Hexaemeron turns it into a study, a runbook of discrete steps, and one pull request per step, with the audit suite run against each before it is pushed.

**Security and audit.** You want the Pashov suite over a contract and nothing else. `x-ray`, `solidity-auditor` and `fizz` are vendored whole and run on their own, without taking on the loop around them.

**Marketing.** A launch post reads like a machine wrote it. `imprimatur` says what is wrong with it across three tiers and `vulgate` rewrites it in house voice. Neither needs the controller, and neither needs installing separately.

**Business development.** An integration document has to be accurate about what the protocol does and readable by someone who is not an engineer. The study phase produces the first and the prose masks produce the second.

### Lemma

[Lemma](./plugins/lemma) turns Solidity compiler inputs and Markdown documents
into JSONL chunks. The two chunkers share one schema and keep source text used
for quotation separate from text prepared for a model or embedder.

Lemma includes:

- a Solidity chunker driven by the compiler AST;
- a Markdown chunker that splits on rendered heading structure;
- schema validation and an invented baseline corpus; and
- a pinned `solc` container wrapper for reproducible compiler output.

It stops after chunking. It does not embed, index, retrieve, or answer from the
output.

Its one skill is `chunk`, giving the qualified name `lemma:chunk`. The plain
name matches the operation and avoids implying the unrelated NLP operation of
lemmatisation.

#### Day to day

**Developers.** A documentation or verified-contract corpus needs source-linked
JSONL before it can enter a retrieval system. Lemma creates that file and
rejects chunks that fail its schema checks.

### Lazarus

[Lazarus](./plugins/lazarus) preserves the finite part of historical Ethereum
state and RPC evidence that one application test needs, then replays only the
requests in that fixture.

Capture fixes a block, records exact JSON-RPC requests and responses, and binds
the fixture to a deterministic manifest. Account and storage claims must pass
EIP-1186 trie-proof checks against the captured header; contract code must match
the proved code hash. Receipts, log queries, calls and traces remain labelled as
recorded RPC evidence. They are not promoted into state proofs.

Replay verifies the fixture before opening a loopback server. An uncaptured
request returns a stable `-32070` error describing the missing plan entry, and
there is no provider fallback. The checked-in Goldfinch example exercises
proof-backed code and storage, a receipt, a log query, a deliberate miss, proof
mutation rejection and byte-for-byte manifest rebuilding without a network.

Lazarus includes:

- finite, bounded capture from one fixed historical block;
- canonical JSON and JSONL formats with versioned, digest-pinned schemas;
- offline header, account, storage, code and manifest verification;
- exact-request JSON-RPC replay over loopback, including batches and
  notifications; and
- 144 tests plus a proof-checked Goldfinch demonstration.

#### Day to day

**Developers.** An old integration test depends on an archive endpoint that is
slow, costly or gone. Capture the exact historical state and responses the test
uses, commit the fixture, and run the same requests locally with a visible miss
for anything the plan omitted.

**Security and audit.** A historical fixture claims an account balance, code
hash or storage value. Run `verify` to check the trie path against the named
header and keep ordinary RPC evidence outside that proof boundary.

### Pandects

[Pandects](./plugins/pandects) is a corpus of executable laws for credit
contracts. Each law is a Solidity component with a deliberately broken
contract it is proven to catch, a reduced counterexample, and a statement of
the accounting model and observables it requires.

The catalogue holds nine laws across conservation, accrual and withdrawal
claims. Eight are exact. The path-independence law carries a bound derived from
the rounding performed by linear accrual, and its tests assert the figures on
both the sound reference and the compounding specimen.

Pandects includes:

- one-state and transition laws written against economic observables rather
  than protocol-specific function names;
- broken specimens and replayable counterexamples for every law;
- observer, driver and differential adapters for Foundry, Echidna and Medusa;
- a reduced Wildcat market model recording where three laws need narrower
  applicability; and
- a checker, catalogue renderer, search record and tests that keep each law's
  six required parts together.

#### Day to day

**Security and audit.** A credit protocol arrives and its economic invariants
have to be settled before a fuzz campaign can mean anything. Pandects supplies
the laws, the assumptions behind them, and evidence that each catches the fault
it names.

**Developers.** A change touches accrual or a withdrawal queue. Run the
applicable laws against the build and inspect the quantities behind any verdict
that moved.

### Probitas

[Probitas](./plugins/probitas) builds a sourced dossier on what a counterparty has done across on-chain lending venues.

Undercollateralised lending is the reason to want one: nothing stands between a lender and a total loss except a judgement about the borrower, and that judgement usually gets assembled by hand from whatever the person asking happens to remember. The tool is not limited to that case. Most on-chain borrowing is collateralised and it still tells you plenty, because a liquidation says a price moved, a bad debt says somebody was not made whole, and a missed maturity says what it says anywhere.

Two halves, doing different jobs. A deterministic collector queries venue adapters and writes an evidence file in which a record cannot exist without a transaction hash, a URL or a document reference. The model writes the narrative from that file, and a gate checker reads the document and the evidence together before either ships.

Five gates decide whether a dossier is honest enough to hand to a lender:

1. Declared, provably linked and inferred addresses stay in separate sections.
2. Every venue in the registry gets a coverage row, and a venue that was queried says over what block range. Silence about a venue would read as a clean record.
3. Every assertion carries a citation, and every figure in the document traces back to a record.
4. What could not be established gets its own section, ahead of anything that reads like a conclusion.
5. No score without a rubric printed beside it. This version emits none.

Gate 3 is the one that does the work. It rebuilds, from the evidence alone, every number and hash a truthful dossier could carry, then fails the document on any figure that is not in that set. An invented transaction hash, an amount rounded in the retelling, a market that was never there: each fails the run rather than shipping in it.

Probitas includes:

- the executable [`probitas.py`](./plugins/probitas/scripts/probitas.py) collector, renderer and gate checker, standard library only;
- adapters for [Wildcat](https://wildcat.finance) and Morpho Blue, and eleven further venues carried as named gaps rather than silence;
- nine synthetic borrower fixtures, including the cured delinquency that a hand-assembled writeup usually reads as a default;
- a [committed example dossier](./plugins/probitas/docs/example-dossier.md) that the tests regenerate and compare, so it cannot drift;
- [a guide to closing a coverage gap](./plugins/probitas/docs/adding-a-venue.md) that assumes no knowledge of Wildcat; and
- 234 tests and an audit log ([`audit/AUDIT.md`](./plugins/probitas/audit/AUDIT.md)) recording every round, including the fixes that were wrong the first time.

#### Day to day

**Business development.** A counterparty asks for a market and someone has to decide whether their word is worth anything. Give this the addresses they declared and it comes back with what they borrowed elsewhere, whether they gave it back, and a list of the venues nobody could check, so the thin parts of the record are visible rather than absent.

**Finance.** Exposure to a name that also borrows in three other places. The dossier states each position's venue, the amounts as exact on-chain integers, and whether anything was left unpaid after a liquidation, which is the number that ends up mattering.

**Security and audit.** A document arrives asserting things about a counterparty and you have to decide whether to believe it. Run `verify` against the evidence file it came with: every figure in the document has to trace back to a record with a transaction hash, and one that does not fails the check by arithmetic rather than by your reading it closely.

### Tabularium

[Tabularium](./plugins/tabularium) preserves on-chain credit events in a form
another person can rebuild after the endpoint that served them is gone.

The first release captures Goldfinch's borrower-side record: 34 borrow and 477
repay entities mapped into 511 canonical rows. Two Euler releases now add a
real Euler v1 canonical-proxy borrow log and a fixed Euler V2 owner/second
activity response from the Euler V3 API. Each row keeps the complete
venue-native record and names the source selector, adapter version and mapping
rule that produced it. Euler V2 protocol generation and Euler V3 source API
remain separate fields.

A separate Compound v3 Phase 0 path consumes Alexandria's verified raw release
and rebuilds non-canonical ordered calls, relevant proxy-storage writes and one
signed-principal transition. It establishes the recorded interpretation method
for one transaction; the canonical Compound event adapter and interval
specimen remain Phase 1 work.

The release is four files doing separate jobs. `source.json` is the preserved
response. `capture.json` records where and when it was taken. `events.jsonl` is
the interpretation. `coverage.json` binds all three by digest, counts what was
mapped and what was not, and states the evidence gaps.

Verification does not stop at those digests. It checks the capture against the
source, confines every path to the release directory, requires one ordered
source selector per event and rebuilds the canonical bytes from the preserved
input. The worked release is unsigned and its block boundary is what the hosted
indexer reported, so a clean run establishes internal consistency rather than
publisher authenticity or an independent chain proof.

Tabularium includes:

- the standard-library [`tabularium.py`](./plugins/tabularium/scripts/tabularium.py)
  builder and offline verifier;
- versioned event schemas [v1](./plugins/tabularium/schemas/canonical-event-v1.json)
  and [v2](./plugins/tabularium/schemas/canonical-event-v2.json), plus coverage
  schemas [v1](./plugins/tabularium/schemas/coverage-manifest-v1.json) and
  [v2](./plugins/tabularium/schemas/coverage-manifest-v2.json);
- the complete [`goldfinch-v0`](./plugins/tabularium/examples/goldfinch-v0/README.md)
  release, its data dictionary and a fresh-directory rebuild demonstration;
- source-bound [`euler-v1-v0`](./plugins/tabularium/examples/euler-v1-v0/README.md)
  and [`euler-v2-v0`](./plugins/tabularium/examples/euler-v2-v0/README.md)
  releases with their own dictionaries and rebuild demonstrations;
- a non-canonical [Compound v3 Phase 0 witness](./plugins/tabularium/examples/compound-v3-phase0-v0/README.md)
  rebuilt from Alexandria's verified release;
- an [adapter guide](./plugins/tabularium/docs/adding-an-adapter.md) and an
  immutable [release policy](./plugins/tabularium/docs/release-policy.md); and
- 134 tests and an audit log
  ([`audit/AUDIT.md`](./plugins/tabularium/audit/AUDIT.md)) recording every
  review round and fix.

#### Day to day

**Developers.** A hosted indexer is still answering for a venue whose front end
has gone. Preserve the response and its capture boundary, then publish a
release whose mapping and bytes somebody else can reproduce without that
endpoint.

**Security and audit.** A dataset arrives with a digest and a claim that it was
built from a named source. Run `verify`: it rebuilds the event bytes and checks
the one-to-one source trace rather than trusting the release's own row count.

**Finance.** A repayment record needs to be compared with another venue's
record without erasing the difference between them. The common family makes
the rows searchable; the venue-qualified action and native record keep the
economic meaning attached.

## Who these are for

Scored out of 10 for doing the job, not for reading the output. A marketer can quote a verified gas number without having any use for Hermes itself.

| Role | Alexandria | Ariadne | Hermes | Hexaemeron | Lemma | Lazarus | Pandects | Probitas | Tabularium |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Developers | 8 | 8 | 9 | 9 | 6 | 8 | 8 | 4 | 7 |
| Security and audit | 8 | 9 | 7 | 8 | 4 | 8 | 9 | 5 | 7 |
| Marketing | 1 | 1 | 3 | 6 | 1 | 1 | 1 | 1 | 1 |
| Business development | 6 | 2 | 2 | 5 | 1 | 2 | 2 | 9 | 3 |
| Finance | 8 | 1 | 3 | 4 | 1 | 2 | 2 | 7 | 7 |
| Legal | 3 | 3 | 1 | 4 | 1 | 2 | 2 | 4 | 2 |

Five is the barrier. At or above it, the plugin's entry carries a worked example of what that role would use it for. Below it there is no example, because there is no honest one to give. These are engineering tools, and a 2 means we could not find a reason for that desk to open the plugin rather than read what it produced.

## Install

### Codex

Add the Wildcat Labs marketplace from the Codex CLI:

```bash
codex plugin marketplace add wildcat-finance/skills
```

Restart the ChatGPT desktop app, open the Plugins Directory, select **Wildcat Labs**, and install the plugin you need.

To inspect configured sources or fetch later updates:

```bash
codex plugin marketplace list
codex plugin marketplace upgrade wildcat-labs
```

See OpenAI's [plugin packaging documentation](https://developers.openai.com/plugins/build/plugins) for the marketplace workflow.

### Claude Code

Add the same marketplace and install a plugin from inside Claude Code:

```text
/plugin marketplace add wildcat-finance/skills
/plugin install alexandria@wildcat-labs
/plugin install ariadne@wildcat-labs
/plugin install hermes@wildcat-labs
/plugin install hexaemeron@wildcat-labs
/plugin install lemma@wildcat-labs
/plugin install lazarus@wildcat-labs
/plugin install pandects@wildcat-labs
/plugin install probitas@wildcat-labs
/plugin install tabularium@wildcat-labs
```

If the install summary asks for it, run `/reload-plugins`. Claude namespaces plugin skills, so Alexandria is available as:

```text
/alexandria:alexandria
```

Ariadne is:

```text
/ariadne:ariadne
```

Hermes is:

```text
/hermes:hermes
```

Hexaemeron's entry skill is:

```text
/hexaemeron:fiat "<topic>"
```

Lemma is available as:

```text
/lemma:chunk
```

Lazarus is available as:

```text
/lazarus:lazarus
```

Pandects is available as:

```text
/pandects:pandects
```

Probitas is available as:

```text
/probitas:probitas
```

Tabularium is available as:

```text
/tabularium:tabularium
```

See Anthropic's [skills](https://code.claude.com/docs/en/skills) and [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) documentation for the underlying format.

### Local agents

Agents that support the open Agent Skills convention can discover the nine
host-neutral entries under [`.agents/skills`](./.agents/skills). Point the
agent at this repository and include that directory in its project skill
search path. Keep the repository layout intact: each entry routes to the
canonical plugin instructions instead of copying them.

A file-reading agent without automatic skill discovery should begin with
[`AGENTS.md`](./AGENTS.md). That file identifies the entrypoints, path rules,
and plugin-specific runtime contracts. Named tools in vendored skills describe
capabilities; the Hexaemeron contract maps them to file, shell, search,
planning, question, and subagent operations available in a local runtime.

Plain-text activation works alongside host syntax:

```text
Use Alexandria to preserve this lending-data capture and query its source-bound credit view.
Use Ariadne to capture this release in an evidence statement, run its gates, and report its signature state without checking signatures.
Use Hermes to optimise gas in this Foundry repository.
Use Hexaemeron Fiat to take "<topic>" through the delivery loop.
Use Hexaemeron Fizz to generate a stateful fuzz suite.
Use Lemma to chunk this Solidity standard input into JSONL.
Use Lazarus to capture, verify or replay this finite historical Ethereum fixture.
Use Pandects to check this credit protocol against the executable laws in the corpus.
Use Probitas to build a dossier on this counterparty from the addresses they declared.
Use Tabularium to build and verify a source-bound Goldfinch, Euler v1 or Euler V2 credit-event release.
```

Fiat remains explicit-only. Mentioning a similar delivery task does not start
the controller unless the user names Hexaemeron or Fiat and asks to run it.

## Use

Alexandria needs Python 3 and nothing else. Its checked-in demonstration and
all verification paths run offline. Ask:

```text
Use $alexandria to preserve this lending-data capture, derive its reviewed credit rows, and query the declared address without hiding coverage gaps.
```

The release contracts, mapping boundary and refusal rules live in
[Alexandria's `SKILL.md`](./plugins/alexandria/skills/alexandria/SKILL.md).

Ariadne needs Python 3 and nothing else. Capturing from a Foundry project needs
that project's build output, which `forge build` already wrote. Ask:

```text
Use $ariadne to capture this release in an evidence statement, run its gates, and report its signature state without checking signatures.
```

The gates, the predicate and the refusals live in [Ariadne's `SKILL.md`](./plugins/ariadne/skills/ariadne/SKILL.md).

Hermes needs Python 3, Git and [Foundry](https://getfoundry.sh/) available in the target repository. Start Codex from a clean Foundry worktree, then ask:

```text
Use $hermes to optimise gas in this repository. Work one optimisation class at a time and keep the complete verification record.
```

The full command contract, layout rules and property standard live in [Hermes's `SKILL.md`](./plugins/hermes/skills/hermes/SKILL.md).

Hexaemeron needs Python 3, Git and `gh` in the target repository (plus [Foundry](https://getfoundry.sh/) when the run ships Solidity). Ask:

```text
Use $hexaemeron to take "<topic>" from study to a merged delivery, one receipted phase at a time.
```

The loop, the receipt contract and the controller reference live in [Hexaemeron's `SKILL.md`](./plugins/hexaemeron/skills/fiat/SKILL.md).

Lemma needs Python 3.10 or later. Solidity input also needs `solc`, Docker, or
Podman. Ask:

```text
Use $chunk to turn this Solidity standard input into validated JSONL chunks.
```

The command selection and output rules live in [Lemma's `chunk` skill](./plugins/lemma/skills/chunk/SKILL.md).

Lazarus needs Python 3.11 or later and the packages pinned in its lock file.
Capture is the only command that needs an archive RPC; verification, replay and
the shipped Goldfinch demonstration run offline. Ask:

```text
Use $lazarus to capture this finite historical fixture, verify its proof-backed state, and replay only its exact requests.
```

The evidence boundary, refusal rules and commands live in [Lazarus's `SKILL.md`](./plugins/lazarus/skills/lazarus/SKILL.md).

Probitas needs Python 3 and nothing else. Neither shipped venue asks for a key, and `--fixtures` runs it with no network at all. Ask:

```text
Use $probitas to build a sourced dossier on "<entity>" from the addresses they declared.
```

The sequence, the five gates and the refusals live in [Probitas's `SKILL.md`](./plugins/probitas/skills/probitas/SKILL.md).

Tabularium needs Python 3.9 or later and nothing else. Its shipped releases and
tests use no network. Ask:

```text
Use $tabularium to rebuild the checked-in Euler V2 release and verify it offline.
```

The mapping, release rules and evidence boundary live in
[Tabularium's `SKILL.md`](./plugins/tabularium/skills/tabularium/SKILL.md).

## Repository layout

```text
.claude-plugin/marketplace.json
.agents/plugins/marketplace.json
plugins/
├── alexandria/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   ├── AGENTS.md
│   ├── docs/
│   ├── examples/
│   ├── schemas/
│   ├── scripts/
│   ├── tests/
│   └── skills/
│       └── alexandria/
├── ariadne/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   ├── AGENTS.md
│   ├── audit/
│   ├── docs/
│   ├── examples/
│   ├── schemas/
│   ├── scripts/
│   ├── tests/
│   └── skills/
│       └── ariadne/
├── hermes/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   └── skills/
│       └── hermes/
│           ├── SKILL.md
│           ├── agents/
│           ├── references/
│           └── scripts/
├── hexaemeron/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   ├── agents/
│   ├── audit/
│   ├── tests/
│   └── skills/
│       ├── fiat/
│       ├── imprimatur/
│       ├── vulgate/
│       ├── x-ray/
│       ├── solidity-auditor/
│       └── fizz/
├── lemma/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   ├── chunkers/
│   ├── tests/
│   └── skills/
│       └── chunk/
├── lazarus/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   ├── AGENTS.md
│   ├── docs/
│   ├── examples/
│   ├── schemas/
│   ├── scripts/
│   ├── tests/
│   └── skills/
│       └── lazarus/
├── pandects/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   ├── adapters/
│   ├── catalogue/
│   ├── docs/
│   ├── specimens/
│   ├── src/
│   ├── test/
│   ├── tests/
│   └── skills/
│       └── pandects/
├── probitas/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json
│   ├── AGENTS.md
│   ├── audit/
│   ├── docs/
│   ├── scripts/
│   ├── tests/
│   └── skills/
│       └── probitas/
└── tabularium/
    ├── .claude-plugin/plugin.json
    ├── .codex-plugin/plugin.json
    ├── AGENTS.md
    ├── audit/
    ├── docs/
    ├── examples/
    ├── schemas/
    ├── scripts/
    ├── tests/
    └── skills/
        └── tabularium/
```

Codex and Claude Code load the same skill directory. The host manifests only handle discovery and installation; each plugin's instructions, harness and acceptance conditions stay shared. Target-repository instructions still apply. More will turn up here as they become useful enough to keep.

Local agents load the same canonical directories through the portable
entries. The portable layer translates discovery and tool vocabulary; it does
not weaken a skill's checks or invent receipts for work that did not run.

# Wildcat Commons

Wildcat Labs spends much of its time on trust roots, attestation,
accountability and verification. That follows from the sphere it works in. In
private credit, trust is the most valuable currency there is, and a promise is
worth only as much as the evidence and recourse behind it.

Doing that work keeps exposing the same missing tools: a durable public record
of on-chain credit, shared laws for credit implementations, agents that can show
their sources, a conformance suite for hooks and a way to replay chain state
after the original infrastructure is gone. Carrying evidence with a release was
the first of them, and `ariadne` above is the answer to it. Preserving the credit
record was the next, and `tabularium` now has Goldfinch and two Euler protocol
generations. `pandects` now
carries the shared credit laws. `lazarus` preserves and replays a finite slice
of historical state. Another protocol, auditor, researcher or agent builder
should be able to use each one without needing to use Wildcat. `alexandria`
now keeps the heterogeneous raw record and serves a reviewed address view to
`probitas` without making either one own the other's claims.

What remains, listed alphabetically:

| Name | The public good |
| --- | --- |
| `berean` | A release manifest and evaluation corpus for agents that must support answers with exact documents and chain state |
| `janus` | A conformance suite for what contract hooks may observe and change before and after a host action |

These are tools we wanted and then needed. Their formats, datasets, properties,
fixtures and tests become more useful when other teams can inspect, run and
improve them, so that is who they are for too.

If Wildcat Labs means what it says about the Commons, publishing only the work
that happens to be convenient is not enough. Fine. We'll do it ourselves.
