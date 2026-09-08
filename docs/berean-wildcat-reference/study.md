# Wildcat grounded Berean reference release

Assuming, unless corrected:

1. The user's approval to run #411 authorises this held frontier. #1144 remains a separate halted consumer; this run supplies its release reference.
2. A finite Ethereum mainnet market release satisfies the unchanged held acceptance. Plasma, Sepolia, other markets and current state after the captured block are excluded.
3. Captured official documentation describes a source subject. Captured calls describe a deployed subject. No evidence here establishes deployed bytecode equality with a current source checkout.
4. The existing Berean formats and offline verifier remain the interface. Recorded answer fixtures are authored for this release; they do not establish live agent behaviour.
5. The interpreter is CPython 3.14.6 from `.python-version`. The three implementation steps are scaffold, build and demonstration.

## 1. Problem statement

Ship the first Berean reference release grounded in captured Wildcat documentation and captured Wildcat market reads. Readers must be able to verify its document citations, chain and block, recorded answers, evaluations and promotion record offline. The replacement is the reference entrypoint; the inherited Aave release remains available for historical consumers.

The source subject is `wildcat-finance/wildcat-docs` at commit `636b1dcba90c816e699c0d876c22d39be2c58b06`. Preserve these exact blobs: `using-wildcat/terminology.md`, `using-wildcat/delinquency.md`, and `technical-overview/contract-deployments.md`. Their combined 40,001 bytes contain the terminology, delinquency descriptions and deployment-address context needed for the bounded questions. Linked pages outside this set are not captured evidence.

The deployed subject is market `0x90772c109adc8d216967a2782eae8271b4e46c1e`, chain `1`, block `25907928`, hash `0x33600dbb40dec3fbfa5898f65b80ba4dfea2873b2281db62dd3dc7dd9fc51b70`. The capture calls `delinquencyFeeBips()`, `delinquencyGracePeriod()`, `borrower()`, `asset()` and `isRegisteredMarket(address)` on the documented arch controller `0xfeb516d9d946dd487a9346f6fee11f40c6945ee4`. Document the selector and ABI-decoding assumption next to each displayed value. The responses establish recorded values at that block, with registration reported true. They do not establish a verified source build or current delinquency. A zero `delinquencyFeeBips()` result does not establish current delinquency or default; `delinquencyGracePeriod()` does not read `timeDelinquent`. Each answer must bind the exact method, target, selector, block and returned word before displaying its ABI-decoded value.

Working prototype means `plugins/berean/examples/wildcat-mainnet-v0/release/` contains the existing `berean-release/v1` artefacts and passes:

```text
python3 plugins/berean/scripts/berean.py verify-release plugins/berean/examples/wildcat-mainnet-v0/release
python3 plugins/berean/scripts/berean.py run-evals plugins/berean/examples/wildcat-mainnet-v0/release
python3 plugins/berean/examples/wildcat-mainnet-v0/demo.py
```

The demo verifies the original, reproduces the release from preserved inputs, compares every output byte, and shows named refusals after changing a citation, the fixed-block context and a preserved read. It prints the market, block, evidence classes and release digest. Positive answers include an exact documentation quote and at least one decoded market read. Refusals cover another chain or market, present-day state, a lender's claimable withdrawal without batch/position evidence, and an uncited instruction. Evaluate all five existing adversarial classes; synthetic poison or stale-state specimens must be labelled constructed and must never be represented as captured official text.

Before completion, update the reference commands, complete the mutable first-party marketplace prose reconciliation, and record one earned Berean evolution advance under the versioning contract. The separate demonstration lane remains `mixed` while material answer records or adversarial inputs are constructed. Attach one unsigned Ariadne `grounded-agent/v1` statement using the existing capture and verify API. The statement records this release digest and actual producer argv outside the exact release file set. It adds no Ariadne behaviour or evolution advance.

## 2. Prior art

The current implementation is `plugins/berean/scripts/berean_lib/`. Corpus verification rechecks exact file sets and bytes; answer verification re-slices citations and recomputes request keys; release verification checks allowlists, retention, reports and promotion records. `examples/aave-v4-demo-v0/` demonstrates these interfaces. Its corpus is authored demonstration prose. Its rebuild contains stale textual claims about slot values and pause status, so the new release must derive its own answers from its actual inputs rather than copy those sentences. Tests under `plugins/berean/tests/` and the existing `emit_report.py` supply the local test and Elenchus runner.

The last two merged first-parent PRs touching Berean were read in full through GitHub's API: [#1330](https://github.com/wildcat-finance/skills/pull/1330), merge `82f3c7736558ce9281462edcd8663d7e8cd440a2`, and [#1183](https://github.com/wildcat-finance/skills/pull/1183), merge `a46f3b508a2740520f4b31a664c9a3e2800cf76a`.

PR #1330 introduced governed demonstration records and kept constructed inputs distinct from `real-data` evidence. Its outstanding items remain with their named owners: `elenchus-report-identities` #1308, `fresh-clone-report-path` #1309, `repeat-shares-one-work-root` #1310, `contributor-guide-generator` #1311, `promise-machine-pdf` #1312, `eager-ledger-read` #1313, `imprimatur-exit-code` #1304, and `stale-example-coverage-prose` #1329. None is a prerequisite for this frozen release. Its `runbook-clause-drift` and `conformance-resolver-in-run-directory` remain recorded limitations of that run's immutable state. `adr-number-collision` was resolved in its integration and carries no work here. Keep reports fresh and collision-safe instead of repeating those limitations.

PR #1183 replaced Goldfinch demonstrations with Aave v4 evidence and explicitly preserved historical audit records and frozen specimens. It carried no new Berean implementation requirement. Its adjacent complete Aave packet #1139, unknown repayment words, uncaptured activity and provider-specific proof-depth limits remain outside this Wildcat market release. Preserve its inherited release bytes and Ariadne consumers.

Audit inventory: the whole-set `audit_synopsis.py --check .` command succeeded on the starting tree. For Berean's original implementation, the authoritative source `audit/AUDIT.md:4347-4532` was read directly to retain historical finding records. The in-scope question-span source `audit/rounds/fiat-331-bind-user-supplied-sentences-to-the-recorded.md` was read directly in full; its verified synopsis was also read. Other discovered matches in #556 and #621 concern Fiat consumers and are outside this release-authoring scope. For the existing Ariadne capture handoff, `audit/rounds/fiat-402-implement-the-grounded-agent-predicate.md:546-647` was read directly: all six capture rounds, with the source retained as authoritative. Its predicate implementation rounds remain outside this API-use-only change. #1330's audit source has no Berean-named section; the demonstration rules and carryover above are taken from its merged PR, not attributed to a Berean audit.

The original findings remain fixed: `B2-R1-01` and `B2-R1-02` at `c8c72d3` (non-finite JSON and swapped symlink), `B3-R1-01` and `B3-R1-02` at `2883291` (evidence-id collision and dead bindings), `B4-R1-01` and `B4-R1-02` at `464bc6a` (nested contract allowlist and report read/digest race), `B5-R1-01` at `df5edc7` (promotion must re-grade), and `B6-R1-01` at `07772a9` (README/demo belong outside the closed release). These legacy rounds lack structured `Covered`, `Not checked` and `Elenchus verdict` fields; those values remain unknown. Original leads retain the house-table presentation and the intentional exclusion of citation display text from forbidden-sentence scanning; all other original rounds record none.

Question-span finding `S1-R1-01` is fixed at `115231a397a93479813cf7cb79f24988c8518cea`: an unencodable question now receives a named refusal. Its source records an Elenchus `guarded` result, while the legacy synopsis lacks the structured verdict field. The source's five leads remain outside this release-only job: list-typed references in other source classes; general lone-surrogate validation; worst-case repeated-span CPU cost; semantically weak but byte-valid duplicate/zero-width/combining spans; and continued answer iteration after a release fault. No clean-up of those concerns is implied by the release demo.

Ariadne capture history retains all eleven finding identities: `S3-R1-01` through `S3-R1-03`, `S3-R2-01` through `S3-R2-05`, `S3-R3-01`, `S3-R4-01`, and `S3-R5-01`. Each was open when filed; round 6 records all eleven fixed on `794c25721e1879bdca418cda32505e2d56215271` and no new finding. Their mechanisms cover corpus closure, bounded diagnostics, Unicode scalars, output aliases, malformed reserved promotion paths, UTF-8 output, rule vocabulary types, CLI diagnostics, traversal width and remaining read budgets. Every round records `Covered`: path-escape, special-file, unstable-read, resource-exhaustion, digest-confusion, evidence-upgrade, comparison-hole, promotion-ambiguity, partial-write, schema-drift, compatibility-regression and stale-prose reviewed. `Elenchus verdict` is respectively null, guarded, inconclusive, guarded, guarded, null; the third round's mixed parent report stays inconclusive despite fixed-tree guards. `Not checked` retains Solidity/Pashov/Fizz waivers, network/RPC/model/Berean execution, credentials/services, producer commands and fixture locators, live Windows/concurrent filesystem behaviour, hosted state and external signer authority; the last rounds also leave physical 2 GiB behaviour unmeasured. Leads retain output-parent retargeting and reserved-path races requiring a live adversary, success-name echo outside refusal diagnostics, promotion merit and canonicality outside capture's byte binding, and then-owned prose reconciliation. None authorises a stronger statement here.

Organisation inputs come from the official docs repository and Lazarus. The fresh finite capture is `.hexaemeron/inputs/lazarus-fixture`, independently verified with fixture digest `539aa993cc0831253d207f8bce8fd5500cf085e133532e479afd37cb779a8391`. It was produced through Lazarus `capture_fixture` with authenticated headers, not through a CLI invocation that did not run. Its five calls remain `recorded-rpc`; the account proof and header do not upgrade their results. External prior art is the preserved Blockscout response at block 25907928, captured `2026-09-06T00:39:04Z`, SHA-256 `4f2c87ddba2a5a9d709be8a09a49f18fa7dccce647716b73180ab46dd5bebc46`. The fresh Blockscout request returned 403; only the older recorded response is evidence. Its hash agrees with the fresh Lazarus bracket, which is recorded provenance rather than a canonical-chain proof.

## 3. Constraints and non-goals

Start from `main` at `41a21f8e065ce086d3ec4355c057b2623b28f205` in the verified worktree `issue/16777233-435852472`. Preserve unrelated worktrees and the existing capture root. Python 3.14.6 is installed and matches the pin. Berean remains stdlib-only. Lazarus keeps its own pinned dependencies and verification boundary.

Keep all existing Berean JSON formats and closed field tables. Put source provenance and scope in pinned corpus material or the existing `reads.source` field as appropriate; put capture plans and raw producer provenance beside the release. Do not add undeclared files inside its closed file set. A rebuild targets a fresh directory, verifies it and compares it with the committed release. It must refuse an existing output or verify it read-only; it must never delete, reset or overwrite an existing `promotions.jsonl`. Upstream relative links outside the selected corpus remain uncaptured; preserve those bytes and apply only a scoped captured-data exclusion if a prose lint mistakes them for authored documentation. Do not weaken the checker globally. Preserve external documentation verbatim, including errors and outdated claims; a citation proves the slice, not its truth. Authored explanation distinguishes document capture time from chain-read time. A documentary example is not a deployment's configured default, and a difference is not proof of protocol disagreement.

Always preserve original bytes, verify digests and produce tests before claiming a release. Ask first only for an actual widening beyond the approved release, such as additional chains, a new model service or a changed verification promise. Never upgrade recorded calls to proof-backed values, put gateway credentials in an artefact, rewrite past promotion records, or silently reopen #1144.

Non-goals are complete protocol coverage, source-to-deployment equivalence, loan diligence, current market safety, legal interpretation, lender positions, new schemas, retrieval or model execution, a service deployment, an authenticated signing claim, and repair of inherited unrelated audits or verifier leads. The source checkout at `77ac6f3080628196997281614a3f04532a376e30` is a different source-era observation and supplies no deployed equality claim.

## 4. Design options

`selected-docs` freezes the three captured official documents and the finite read set. It gives the release a small explicit evidence boundary, at the cost of refusing questions that need linked pages. `whole-markdown` freezes all 86 Markdown files from the same official commit. It makes more text available but includes deprecated and other-chain material and still cannot answer those subjects from this one market's calls.

Both candidates were executed through the existing corpus builder and verifier, using exact Git blobs from commit `636b1dcba90c816e699c0d876c22d39be2c58b06`, without touching the dirty docs working tree. Both matched all three captured source blobs, verified under the existing schema, refused a changed byte and verified again after restoration. The selection gate permits at most 1,000 ms for one local build-and-verify sample; five consecutive samples per candidate all passed. This is a local corpus experiment with a warm filesystem, not a deployed performance promise or a claimed optimisation.

`selected-docs` retains 40,001 bytes; `whole-markdown` retains 496,297 bytes. The only comparative metric is exact retained corpus bytes. The respective maximum observed build/verify times were 0.431709 ms and 5.51475 ms, rounded upwards in the typed reports. Timing does not break a tie. `selected-docs` is the unique non-dominated survivor on space after the common correctness, compatibility, time and recovery gates.

The complete matrix is `.hexaemeron/design-evidence.json`; reports and raw measurements are under `.hexaemeron/design-reports/`. Every resolved cell came from `python3 .hexaemeron/design_probe.py`, which actually executed each builder, verification and tamper check. Selection establishes the documentation packaging choice only. The final Wildcat release verifier/evaluation/demo gate remains pending until `integration`, resolved by `python3 .hexaemeron/design_probe.py selected-docs`. It must run after the implementation; passing the corpus experiment cannot satisfy it. That resolver also runs `python3 plugins/ariadne/scripts/ariadne.py verify plugins/berean/examples/wildcat-mainnet-v0/grounded-agent.intoto.json`, and the demo must check the statement against the exact freshly rebuilt release, with its unsigned status explicit.

## 5. Risk register seed

```risk-register
source-custody | official document blobs and provenance | compare exact commit paths bytes and digests; preserve quotations without rewriting
subject-confusion | document subject versus deployed market | disclose scope and time domains; claim no source-bytecode equality
read-meaning | request selectors ABI decoding and scalar outputs | verify selectors lengths values and address decoding against preserved calls; do not infer defaults or live status
read-provenance | Lazarus fixture copied into Berean | verify producer and copied bytes; recompute request keys; keep calls recorded-rpc
allowlist-scope | release chain contracts and fixed block | include actual market and arch controller; refuse other chains markets and later state
statement-binding | Ariadne grounded-agent capture | verify exact local release identity and statement; keep producer truthful output external and unsigned
synthetic-evidence | adversarial specimens and recorded answers | label constructed inputs and keep captured official documents unchanged; retain mixed demo status
release-integrity | generated corpus answers evaluations and promotion | rebuild twice compare bytes and re-grade; never rewrite an inherited promotion chain
partial-output | builder destination and interruption | use bounded staging and confined paths; refuse existing or incomplete targets without losing preserved inputs
scope-refusal | questions requiring absent position or batch evidence | preserve explicit refusal cases and never infer claimable withdrawal from delinquency
reference-drift | mutable defaults and historical consumers | update the reference entrypoints; retain Aave artefacts and reconcile all mutable marketplace prose
secret-retention | authenticated producer and stored evidence | no credential in source logs argv or error output; retention none and no conversation transcript
```

## 6. Glossary seeds

Corpus: exact captured document bytes and their manifest. Source subject: the named documentation repository commit. Deployed subject: the named market at one chain and block. Recorded RPC: a preserved response whose semantic correctness is not proved by copying it. Promotion: a new record earned by verified evaluation. Reference entrypoint: the documented default demonstration command. Constructed specimen: deliberately authored evaluation material kept distinct from official captures.

## 7. Sources

The reproduction inventory is `.hexaemeron/inputs/docs-provenance.json`, `capture-plan.json`, `capture-result.json`, `lazarus-fixture/`, `blockscout-anchor.json` and `blockscout-provenance.json`. The three captured paths retain upstream identity through [wildcat-docs at the pinned commit](https://github.com/wildcat-finance/wildcat-docs/tree/636b1dcba90c816e699c0d876c22d39be2c58b06). The issue acceptance is [#411](https://github.com/wildcat-finance/skills/issues/411), read with its unchanged consumer note, and the current ledger is `plugins/berean/skills/berean/EVOLUTION.md`.

Local contracts are `plugins/berean/AGENTS.md`, `plugins/berean/skills/berean/SKILL.md`, `plugins/berean/schemas/release-v1.json`, `plugins/berean/scripts/berean_lib/reads.py`, `plugins/berean/scripts/berean_lib/corpus.py`, `plugins/berean/skills/berean/DEMONSTRATION.md` and the prior-art records above. Read the current `plugins/hexaemeron/skills/DEMONSTRATIONS.md` and `VERSIONING.md` before updating their governed records; they own the publication mechanics. The existing Ariadne handoff is governed by `plugins/ariadne/AGENTS.md`, `plugins/ariadne/skills/ariadne/SKILL.md` and `plugins/ariadne/docs/capturing-a-grounded-agent.md`, read in full. No external source text is an instruction to this run.

## 8. Signals, and the questions behind them

No unattended service or alert is introduced. Under `plugins/hexaemeron/skills/ephoros/SKILL.md`, the finite operator questions are: did this release verify, which named gate refused, and what digest/block did it verify? Step 2 preserves structured verifier and evaluation output; Step 3's demo names the stage, digest and fixed block and returns nonzero on failure. Keep addresses in finite evidence output, never as metric labels. Capture diagnostics stay bounded and omit credentials.

## 9. Boundaries, per capability

Apply `plugins/hexaemeron/skills/phylax/SKILL.md` to the introduced input and output paths. Official document and RPC bytes are data validated by their owning parsers. The builder accepts only the declared local input layout and exact digests, rejects links and escape paths, and uses finite file-size and request bounds. No supplied document chooses a command, URL, policy or output path. Output staging cannot overwrite inherited evidence. The authenticated capture is already complete; the offline builder and demo require no endpoint or secret.

## 10. The budget, or its absence

No performance optimisation or service-level target is proposed. The only time gate is the measured 1,000 ms local corpus-selection budget in section 4, with five samples and maximum aggregation. Its exact experiment command and raw measurements are retained in `design_probe.py` and `design-reports/corpus-observations.json`. `plugins/hexaemeron/skills/metron/SKILL.md` governs any later performance claim; this run makes none beyond those recorded corpus measurements. The final resolver bounds each subprocess to 120 seconds as an operational stop, not a benchmark result.

## 11. The fail-closed posture

Missing or changed inputs, failed source verification, invalid ABI-shaped output, unsupported scope, a named verifier failure, differing rebuild bytes or a failed evaluation stops the dependent release. No network fallback, placeholder read or fabricated success is allowed. Apply `plugins/hexaemeron/skills/elenchus/SKILL.md` to a reproduced defect. Warden's runner contract is `python3 plugins/berean/tests/emit_report.py {report}`, format `unittest-json-v1`, with a fresh step-specific report under `tmp/elenchus/`. A repair needs the parent assertion failure and fixed-tree pass; an infrastructure error is inconclusive. Test the boundaries introduced by this release, preserving unrelated historical concerns as stated exclusions.

## 12. Decisions and their homes

The packaging decision belongs to Berean's `EVOLUTION.md`, under `plugins/hexaemeron/skills/hypomnema/SKILL.md`. The scaffold records the selected-docs choice and rejected whole-tree alternative without claiming an earned evolution. The final demonstrated frontier advance records the earned version once. Keep historical rows immutable and keep the separate demonstration frontier honest.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | selected-docs
record | plugins/berean/skills/berean/EVOLUTION.md
```

Commit copies of the study, runbook, design matrix, reports and reproducible experiment beside `docs/berean-wildcat-reference/`; retain controller-owned originals. Put usage and scope in `examples/wildcat-mainnet-v0/README.md`, beside the capture provenance and outside the closed release. Reconcile default reference commands and mutable marketplace context after the actual demonstration. The downstream #1144 handoff names this release digest, its preserved source commit and its deployed market/block; it does not start or complete #1144.
