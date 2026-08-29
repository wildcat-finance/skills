# Study: Homologia, numeric agreement between on-chain computations and their off-chain mirrors

This study consolidates three proposals made in the same collective poll: Isopsephia (pinned-pair integer parity, from Kronos), Homologia (differential vectors between a contract and its reference model, from Fizz) and Akribeia (fidelity of application-level numeric mirrors, from Phylax), into one charter. All three name the same missing transition: nothing in the roster establishes that an off-chain reimplementation of a contract's arithmetic produces the integer the contract produces.

Assuming, unless corrected:

1. "Domain agent" means a separately installable Wildcat Labs skill and deterministic CLI, not an always-on process or an agent allowed to change its own instructions.
2. The member is named **Homologia**, from the Greek for agreement, because agreement between two implementations is the whole subject. Isopsephia and Akribeia are recorded as rejected names: the first names only the exact-integer case, the second names a virtue of one side rather than the relation between the two.
3. The prototype executes no EVM. The chain side of every comparison is an expected integer that arrives as evidence with a named provenance class; producing that evidence stays with Lazarus (captured and proved state), with a recorded `eth_call` result, or with a committed harness output that is honestly labelled as asserted. `proved` means proved account and storage state today, not proved receipts or logs: Lazarus records those as provider evidence until [skills#383](https://github.com/wildcat-finance/skills/issues/383) lands, and its own shipped fixture cannot be upgraded from its own bytes, because the plan holds one receipt out of 218 in the block and a trie path needs all of them.
4. Mirrors are operator-declared programs run as pinned subprocess adapters speaking a fixed protocol: vectors in as JSONL on stdin, one decimal-integer string per vector on stdout. The prototype ships the protocol and a reference Python adapter; a reference TypeScript adapter is exercised in the committed example only where a Node runtime is present, and no root or plugin test depends on Node.
5. Exact integer equality is the default judgement. A tolerance exists only as an explicit per-check declaration, is echoed in the verdict it weakens, and never becomes a default.
6. Vector generation stays outside the charter. Fizz and Foundry campaigns may produce vector files; Homologia consumes declared files and never generates, mutates or minimises them.
7. The offline toolchain is Python 3.11 and the standard library, matching every other plugin. Mirror subprocesses may be any runtime the operator pins; the suite treats an absent runtime as a skipped example, never a failed contract test.
8. The Creator directed this study in response to the three-way convergence, which stands in for the routed observation that normally precedes a member's birth. Implementation still starts only after the issue owner approves these assumptions.
9. This proposal was prepared against `main` at `81105bb` on 2026-08-23, and the run's own worktree is `tmp/fiat/fiat-458-homologia-numeric-agreement`, created by the controller before preflight.

I will proceed on these assumptions unless corrected.

## 1. Problem statement

The developers this collective serves re-implement contract arithmetic off-chain constantly: a TypeScript SDK re-derives scaled balances and accrued interest for display and signing prompts, Python analytics re-derive rates, withdrawal amounts and position values for reports and risk decisions. The EVM computes in unsigned 256-bit integers with explicit rounding direction and ray/wad scaling; the mirrors compute in IEEE-754 doubles, JavaScript `BigInt`, Python `int` or `decimal.Decimal`, with token-decimal and day-count conventions applied by hand. A mirror that is wrong by one rounding direction or six orders of decimal magnitude passes every gate the collective currently runs, because Fizz's campaigns are pure EVM (the Solidity agreeing with itself), Pandects judges one implementation against reviewed laws, and Phylax guarantees a signing prompt is readable without guaranteeing its number is right.

Create **Homologia**, a standalone domain skill for maintainers who need the missing judgement: given a declared pair (one pinned on-chain computation and one pinned mirror) and a declared vector set with evidence-classed expected answers, establish whether the pair agrees, integer for integer, and preserve every divergence as a specimen. A verdict states agreement or divergence between the named pair at pinned revisions. It never states that either side is correct: two implementations of the same misunderstanding agree perfectly, and the nearest overclaim on every verdict says so.

The prototype is proved by this offline demo path:

```bash
python3 plugins/homologia/scripts/homologia.py compare \
  --manifest plugins/homologia/examples/wad-interest-v0/manifest.json \
  --out build/homologia/verdict.json
python3 plugins/homologia/scripts/homologia.py render \
  build/homologia/verdict.json --out build/homologia/report.md
python3 plugins/homologia/scripts/homologia.py verify \
  --manifest plugins/homologia/examples/wad-interest-v0/manifest.json \
  --verdict build/homologia/verdict.json \
  --report build/homologia/report.md
```

Exit 0 establishes only that the verdict and report recompute from the named manifest, vectors and adapter outputs. The committed example compares a wad-scaled interest-accrual function against a reference Python mirror over recorded vectors and agrees exactly; a second committed example seeds a floor-versus-half-up rounding divergence in the mirror and must produce a divergence verdict carrying the exact vectors that separate the pair. Negative demonstrations must refuse a mirror that emits a float-formatted answer and a verdict edited to claim correctness.

## 2. Prior art

**The originating poll.** Six members were asked whether any agent beyond Synkrisis would make the collective more useful. Three independently named this gap: Kronos from the ranking seat (no charter and no open issue names the JS/TSX surface, so the work can never become a held job), Fizz from the campaign seat (Echidna and Medusa cannot call a Python pricing model, so every asserted property is the Solidity agreeing with itself), Phylax from the boundary seat (its lint already reads `.ts`/`.tsx` for readability and hostility, and nobody owns whether the readable number is right). Protasis answered None, on the ground that no homeless framework observation exists yet and a member born ahead of demand is a contract maintained on speculation; assumption 8 records how this study answers that objection, and the objection stays live for the issue owner to weigh.

**Existing skill boundaries.** [Fizz](https://github.com/wildcat-finance/skills/blob/main/plugins/hexaemeron/skills/fizz/SKILL.md) constructs single-implementation invariant campaigns inside the EVM. [Pandects](https://github.com/wildcat-finance/skills/blob/main/plugins/pandects/skills/pandects/SKILL.md) holds one implementation to reviewed economic laws expressed as Solidity components for fuzzing engines. [Lazarus](https://github.com/wildcat-finance/skills/blob/main/plugins/lazarus/skills/lazarus/SKILL.md) captures, proves and replays historical chain state, and is the natural producer of proved expected answers. [Metron](https://github.com/wildcat-finance/skills/blob/main/plugins/hexaemeron/skills/metron/SKILL.md) judges performance against recorded measurement, not numeric agreement. [Synkrisis](https://github.com/wildcat-finance/skills/issues/449) compares agent runs over operator-declared cohorts and explicitly excludes model-quality judgement; Homologia compares two implementations at one pinned revision each and never two runs over time. [Probitas](https://github.com/wildcat-finance/skills/blob/main/plugins/probitas/skills/probitas/SKILL.md) supplies the `collect` → `render` → `verify` separation this study reuses, and [Janus](https://github.com/wildcat-finance/skills/blob/main/plugins/janus/skills/janus/SKILL.md) supplies the precedent of checking a manifest against the adapter it names (issue #330). No open issue covers cross-implementation numeric agreement: #381 has Pandects reading Fizz's campaign records, #384 gives Lazarus a Foundry replay profile, and the Synkrisis family (#434 to #437, #449) stays within run telemetry.

**A second poll, and three findings that shape the verdict shape.** On 2026-08-23 every member was asked again what it wanted, and three answers are evidence for this charter rather than beside it. Pandects found that `scripts/pandects_lib/run.py:258` writes `laws_searched` as `len(catalogue.laws)`, so its committed search record claims ten laws were searched by a campaign that structurally cannot judge several of them ([skills#504](https://github.com/wildcat-finance/skills/issues/504)). Imprimatur found that its lint answers clean on indented NatSpec it never reads ([skills#503](https://github.com/wildcat-finance/skills/issues/503)). Phylax found three shipped rules blind to the two-line assignment form real Python takes ([skills#502](https://github.com/wildcat-finance/skills/issues/502)). All three are the same defect class: a result that reads as coverage while the check never ran. A parity verdict is unusually exposed to it, because agreement over a vector set says nothing about the vectors nobody supplied, so the verdict must state what it did not compare as plainly as what it did.

**The wave and the rename.** This issue sits in `Wave 9 — comparative assurance and first statements`, which is the wave for exactly this transition; the α and β families were retired on 2026-08-23. The skill formerly called `chunk` is now `lemma`, so the boundary note below names it that way.

**Merged work read before the design options.** Homologia has no earlier pull request. The last two comparable standalone plugin scaffolds are [PR #262](https://github.com/wildcat-finance/skills/pull/262) for Berean and [PR #271](https://github.com/wildcat-finance/skills/pull/271) for Janus, as recorded in the Synkrisis study attached to issue #449; both landed the plugin shell, host manifests, portable entry, marketplace integration, canonical skill, evolution ledger, committed study and runbook, root tests, and a green stub before behaviour.

**Audit records read.** The newest family in `audit/AUDIT.md`, the Elenchus audit-round verdict rounds for issue 327, closed clean at step 3 round 3 with zero findings, and its risk table supplies two conventions this run is held to by name: `receipt-overclaim`, which refuses to call a recorded value an attestation of report bytes, and `frontier-drift`, which requires the fourteen evolution and version checks to agree. `audit/AUDIT.md` at the pinned ref was read for the Phylax TypeScript-boundaries rounds (an untrusted `.ts` file must be read bounded, at most the cap plus one byte, failing closed) and the Elenchus structured-reports rounds (never export an output path into a child's environment, and bounded single-descriptor reads close the stat/read race); both findings become controls in items 5 and 9. `plugins/pandects/audit/AUDIT.md` was read for the step-5 rounds and the leads-closed section: engines and toolchains are pinned by exact version in every round, and a lead that names a real gap becomes a new law rather than a stretched old one, the same reasoning that makes this charter a new member rather than a stretched Fizz. The root audit file was searched for Fizz and Lazarus rounds and none exist there; `plugins/hexaemeron/audit/AUDIT.md` records the step-0 `os.replace` atomicity lead, carried into item 5's partial-write control. No accepted audit lead authorises correctness language or autonomous action here.

**External standards.** [ERC-4626](https://eips.ethereum.org/EIPS/eip-4626) fixes rounding direction per operation and is the canonical example of a convention mirrors get wrong. [IEEE 754-2019](https://standards.ieee.org/ieee/754/6210/) is the arithmetic mirrors silently fall into; the [MDN BigInt reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/BigInt) and the [Python `decimal` documentation](https://docs.python.org/3/library/decimal.html) describe the exact types mirrors should use instead, and their conversion edges are where the named failure classes live.

## 3. Constraints and non-goals

- **Starting ref and versions.** Proposal evidence is bound to `main` at `81105bb`, Promise Machine `promise-machine/v1`, Hexaemeron package `1.5.5`, Protasis `4.6.0`, Elenchus `1.2.0`, Phylax `1.3.0`, Ephoros `1.2.0`, Metron `1.1.0`, Lazarus `1.1.0`, Pandects `1.1.0`, Probitas `0.1.0`, Janus `0.1.0`, Lemma `0.1.1`. The implementation run rechecks every in-scope identity at its own entry.
- **Toolchain.** Python 3.11 and the standard library for the agent. JSON and JSONL are UTF-8. Inputs are repository-relative paths. No database, no network, no model call, no EVM execution, no third-party numeric package. Mirror subprocesses use whatever runtime the manifest pins, outside the suite's dependency set.
- **Prototype scope.** One manifest is processed at a time. A manifest declares one pair and up to 16 vector sets; a vector set holds up to 100,000 vectors; each file is capped at 8 MiB and all declared inputs at 64 MiB; mirror stdout is capped proportionally to the vector count. Implementation may lower a measured cap; raising one requires a study amendment.
- **Non-goals.** Vector generation and minimisation (Fizz, Foundry), chain capture and proof (Lazarus), correctness of either implementation, economic-law judgement (Pandects), gas or performance verdicts (Hermes, Metron), UI rendering or readability (Phylax), cross-run diagnosis (Synkrisis), automatic issue filing, repository mutation, and dispatch of any kind.
- **Always.** Run the root and Homologia suites, Promise Machine checks, both Protasis modes, Imprimatur on shipped prose, Brevitas where applicable, the relevant tree lints, and a fresh Horos boundary scan before a commit.
- **Ask first.** Add a dependency; add or alter CI; change the adapter protocol; raise a cap; add a public verdict field; admit a new provenance class; or allow any external side effect.
- **Never.** Execute a mirror command not pinned in the declared manifest; export an output path into a child's environment; parse a non-integer mirror answer approximately; store credentials, raw prompts or absolute home paths; delete a failing fixture; claim a check ran when it did not.

## 4. Design options

**A. Standalone Homologia plugin with adapter-protocol mirrors and evidence-classed expected answers (chosen).** A new `plugins/homologia/` package owns manifest checking, mirror execution, comparison, rendering and verification. The chain side is evidence in, never execution; the mirror side is a pinned subprocess speaking the fixed protocol, so a mirror may be Python, TypeScript under Node, or anything else the operator pins. The trade is another marketplace package plus a public adapter protocol to hold stable, in exchange for a promise no existing charter can carry and mirror coverage in every language the thralls actually write.

**B. Fold into Fizz as precomputed differential vectors.** Bake expected answers into an Echidna/Medusa harness as constants. Rejected: the comparison then runs inside the EVM against frozen constants, so the mirror itself is never executed and mirror drift, the defect class this exists for, stays unobserved; it also widens a construction charter into cross-language verification, which the marketplace boundaries forbid.

**C. Extend Pandects.** Pandects already holds implementations to laws. Rejected: its laws are reviewed economic invariants expressed as Solidity components for fuzzing engines, one implementation at a time; pairwise integer agreement with an off-chain mirror is neither a law nor Solidity, and its own audit history shows the plugin answering adjacent gaps by adding laws, not by absorbing new subjects.

**D. A live differential harness driving forge, Node and an RPC together.** Rejected: it needs three toolchains and a network at run time, its results are not offline-recomputable, and a live RPC answer carries no provenance class: precisely the unproven third-party assertion the collective refuses elsewhere.

Option A is the least construction that owns the missing transition, and the only one in which both sides of the comparison are pinned, evidence-classed artefacts.

The initial Promise Machine surface has three promises:

- `homologia-expected-answer-provenance`: an expected answer enters a comparison only with a named provenance class, one of `proved` (derived from a Lazarus-verified capture), `recorded` (a captured call result with chain, block and contract identity), or `asserted` (a committed value with a named author), and it authorises use as the chain side of exactly that vector set.
- `homologia-mirror-execution`: a pinned adapter argv, bounded input and output, integer-only answers and a recorded runtime identity authorise treating the outputs as the mirror's answers at that revision, and nothing else.
- `homologia-parity-verdict`: recomputation of the full comparison, divergences preserved as specimens and any tolerance declaration echoed, authorises a verdict of agreement or divergence between the named pair, with the weakest provenance class used stamped on the verdict, and never a claim that either implementation is correct.

## 5. Risk register seed

```risk-register
mirror-command-boundary | the argv of the operator-declared mirror subprocess | argv is pinned in the manifest, no shell is used, and no output path or credential enters the child environment
float-contamination | mirror stdout at the integer boundary | an answer with a fraction, exponent, locale separator or non-decimal form refuses the run rather than being parsed approximately
tolerance-creep | per-check tolerance declarations | tolerance requires an explicit manifest declaration, is echoed in the verdict it weakens, and has no default
provenance-conflation | asserted expected values sitting beside proved ones | the verdict carries the weakest class used anywhere in the comparison and classes never average
decimals-scale-mismatch | token-decimal and ray/wad scale identities in vectors and manifest | a scale identity missing or unequal between vector set and mirror declaration refuses the check
runtime-drift | the interpreter and package identities behind a mirror | runtime identity is recorded per run and a changed identity forces re-execution rather than reuse
answer-count-mismatch | the pairing of vectors to mirror answers | fewer, extra or out-of-order answers refuse the whole set rather than aligning best-effort
input-exhaustion | vector files and mirror output at the CLI boundary | per-file, aggregate, per-vector and stdout caps apply before unbounded allocation, read bounded with one descriptor
subprocess-hang | a mirror that blocks, floods or never exits | a wall-clock timeout and bounded pipe reads kill the child and refuse with one named recovery
partial-write | verdict and report outputs during a long comparison | outputs are written atomically so no half-written verdict ever verifies
evidence-strengthening | an agreement verdict becoming a correctness or audit claim | verdicts state pair-agreement only, carry the nearest overclaim, and negative fixtures reject correctness language
```

Two lines of prose the block cannot carry. The mirror subprocess is the largest boundary this plugin opens: it executes operator-declared code by design, so the controls are about containing what the operator declared, not about preventing execution. And evidence-strengthening here has a specific shape worth naming: a downstream reader will want "the SDK is right" and the verdict can only ever say "the SDK and the contract agree on these vectors", so the render templates must make that gap impossible to paper over.

## 6. Glossary seeds

- `Pair`: one pinned on-chain computation (chain, contract, function identity) and one pinned mirror, declared together in a manifest.
- `Mirror`: an off-chain reimplementation of the pair's computation, executed through the adapter protocol.
- `Adapter protocol`: the fixed subprocess contract: JSONL vectors on stdin, one decimal-integer string per vector on stdout.
- `Vector`: one complete input tuple for the pair, with its scale identities.
- `Expected answer`: the chain side's integer for one vector, carrying a provenance class.
- `Provenance class`: `proved`, `recorded` or `asserted`; the verdict inherits the weakest class used.
- `Tolerance declaration`: an explicit per-check bound that turns exact equality into bounded agreement and is echoed in the verdict.
- `Divergence specimen`: the preserved vector, both answers and their difference for one disagreement.
- `Verdict`: the recomputable statement of agreement or divergence for one pair over declared vector sets.
- `Runtime identity`: the recorded interpreter, version and platform behind a mirror execution.

## 7. Sources

- The six-member poll answers of 2026-08-22 (Kronos, Fizz, Phylax proposals; the Protasis None), to be attached alongside this study when it is filed.
- Issue [#449](https://github.com/wildcat-finance/skills/issues/449) and its attached Synkrisis study; issues [#330](https://github.com/wildcat-finance/skills/issues/330), [#381](https://github.com/wildcat-finance/skills/issues/381), [#384](https://github.com/wildcat-finance/skills/issues/384).
- `PROMISE_MACHINE.md`, `AGENTS.md`, `.agents/skills/promise-machine/SKILL.md`, `audit/AUDIT.md`, `plugins/hexaemeron/audit/AUDIT.md` and `plugins/pandects/audit/AUDIT.md` at `f34e196a90d28b82da63724d73ecadbaa7a581bc`.
- Canonical contracts for Fizz, Pandects, Lazarus, Metron, Probitas, Janus, Protasis, Ephoros, Phylax, Elenchus and Hypomnema under `plugins/`.
- Comparable plugin scaffolds [PR #262](https://github.com/wildcat-finance/skills/pull/262) and [PR #271](https://github.com/wildcat-finance/skills/pull/271), via the Synkrisis study.
- [ERC-4626](https://eips.ethereum.org/EIPS/eip-4626), [IEEE 754-2019](https://standards.ieee.org/ieee/754/6210/), [MDN BigInt](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/BigInt), [Python `decimal`](https://docs.python.org/3/library/decimal.html).

## 8. Signals, and the questions behind them

The command may run in CI against SDK changes, so [Ephoros](https://github.com/wildcat-finance/skills/blob/main/plugins/hexaemeron/skills/ephoros/SKILL.md) applies. Four operator questions, answered without a telemetry service:

1. **Why was an input or a mirror refused?** Every non-zero exit emits one stable code, the manifest or vector reference responsible, the mirror's recorded runtime identity where relevant, and one recovery action.
2. **Where exactly do the implementations disagree?** The verdict names every divergent vector set and the specimen file preserves each divergent vector with both answers and the signed difference.
3. **How strong is this verdict?** The verdict carries the weakest provenance class used and every tolerance declaration in force, so a reader can tell a proved exact agreement from an asserted approximate one at a glance.
4. **Did the report still match its evidence?** `verify` recomputes the comparison from the manifest and emits the verdict, specimen and report digests plus one final status.

No alert or dashboard ships in the prototype; the structured CLI output and retained artefacts are the signals.

## 9. Boundaries, per capability

[Phylax](https://github.com/wildcat-finance/skills/blob/main/plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and controls; this section names what each capability opens.

- **Manifest and vector ingestion.** Untrusted files at the CLI boundary. Bounded single-descriptor reads under the caps, repository-relative paths only, schema checks before field access: the control set the Phylax TypeScript rounds already established.
- **Mirror execution.** The deliberate boundary: operator-declared code runs as a child process. Pinned argv, no shell, a minimal child environment carrying no output path (the Elenchus audit finding), stdin/stdout only, timeout and output caps, and the child's exit status recorded but never trusted as the comparison result.
- **Expected-answer evidence.** Provenance files are data; nothing in them is executed, and a `proved` claim is accepted only with the Lazarus artefact reference that backs it, never from a bare label.
- **Report rendering.** Fixed templates over structured fields; the renderer cannot introduce a number, a vector, a correctness verb or a provenance class absent from the verdict file.
- **Handoff.** A divergence names a possible next owner, with a reason: `elenchus` for working the divergence to cause, `fizz` for widening vectors, `human-review` for the judgement call. The CLI performs no handoff and has no network, Git or GitHub path.

## 10. The budget, or its absence

The harness has a work budget because CI will hold SDK changes against it; [Metron](https://github.com/wildcat-finance/skills/blob/main/plugins/hexaemeron/skills/metron/SKILL.md) owns the measurement method. On the checked scale fixture of one pair and 100,000 vectors with a trivial local mirror, `compare` plus `verify` must complete in at most 10.0 seconds with peak resident memory at most 256 MiB on the recorded CI runner, mirror subprocess wall-clock excluded and reported separately. The command:

```bash
python3 plugins/homologia/scripts/bench_homologia.py \
  --fixture plugins/homologia/tests/fixtures/scale/100k-vectors \
  --max-seconds 10.0 --max-rss-mib 256
```

The benchmark records Python version, platform, fixture digest, repetitions, the excluded mirror time and the maximum result. It is a bounded implementation budget, not a claim about other machines, other mirrors or larger vector sets.

## 11. The fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/main/plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule. Comparison stops before output on: an undeclared or duplicate vector file, a missing or unbacked provenance class, a missing or unequal scale identity, an unpinned mirror command, a non-integer mirror answer, an answer-count or order mismatch, a subprocess timeout or cap breach, or an unparseable manifest. Verification stops on any byte or digest difference between recomputed and presented artefacts. Every failure class gets a named negative fixture and a test observed failing before its guard lands. A mirror that refuses to run is a refused comparison, never an agreement by absence; a vector set that partially succeeds is refused whole rather than reported best-effort. Recovery names the exact manifest field, vector or adapter check to repair and reruns the full path.

## 12. Decisions and their homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/main/plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record. Four are expected to be expensive to reverse:

- One consolidated member rather than three, and the name Homologia over Isopsephia and Akribeia: `plugins/homologia/docs/decisions/ADR-001-one-charter-for-numeric-agreement.md`.
- Evidence-in rather than execution-in for the chain side (no EVM in the plugin): `plugins/homologia/docs/decisions/ADR-002-chain-answers-are-evidence.md`.
- The adapter protocol as the public mirror interface: `plugins/homologia/docs/decisions/ADR-003-subprocess-adapter-protocol.md`.
- Exact integer equality as the default with tolerance as an explicit, verdict-weakening declaration: `plugins/homologia/docs/decisions/ADR-004-exact-by-default.md`.

The manifest, vector, verdict and specimen schemas are versioned public artefacts under `plugins/homologia/references/`; their compatibility policy belongs in `plugins/homologia/docs/schema-compatibility.md`. The skill's version, frontier and next held job belong in `plugins/homologia/skills/homologia/EVOLUTION.md`. This study and its runbook are run artefacts, not substitutes for those standing records.
### Amendment -- 2026-08-23

**What changed.** Section 4 planned three promises and said the scaffold would
declare none of them. The scaffold declares one, `homologia-scaffold-identity`,
about its own packaging and refusal, and still declares none of the three. Step
1 also converts the root suite's hand-written plugin, skill and promise counts
into values derived from disk and from the coverage ledger. The promise-shape
decision is recorded in the canonical contract itself, under the heading naming
the step each domain promise arrives with; ADR-001 keeps the naming and
consolidation decision it already held.

**Why.** The Promise Machine refuses both shapes of the original plan. PM062
requires a coverage row for every declared promise, so the three domain
promises cannot be declared before the cases that evidence them exist. PM031
then requires a governed skill to declare at least one promise, so zero is not
available either. What the scaffold can evidence is that it is installed under
one identity across both host manifests and the marketplace, that its installed
root-law copy is byte-identical to the suite law, and that every verb refuses
instead of answering. That is what it declares, at consequence 0, with five
cases including a tamper case that makes the drift check fail on a mutated
copy. The derived counts follow from step 1's own exit condition: the plugin has
to be discovered, and counts written in by hand let it land with every case
passing while none of them had looked at it.

**Steps touched.** Step 1, whose exit now also covers one declared packaging
promise and its coverage row. Steps 2, 3 and 4 keep the three domain promises
they were already going to carry.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step
5: entry holds; exit holds.
