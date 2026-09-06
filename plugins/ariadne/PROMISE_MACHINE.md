<!-- promise-machine: contract=promise-machine/v1; canonical=PROMISE_MACHINE.md; copies=generated -->

<p align="center">
  <img src="https://raw.githubusercontent.com/wildcat-finance/skills/main/assets/characters/promise-machine-binding.png" width="1200">
</p>

# Promise Machine contract

The Promise Machine is the rule that stops one useful result becoming a larger,
unsupported claim as it moves between agents.

Suppose Lazarus records the RPC response and proves one account-storage
relation for a historical test. A later agent may say that the named relation
was proved and the other response bytes were recorded. It may not describe the
whole response as proved, call the provider canonical, or use the fixture as a
whole-protocol safety result. The evidence moves forward with its original
boundary.

That is the practical purpose of this contract. Every governed operation says:

- what success establishes;
- which evidence supports it;
- what the result still does not establish;
- which next action it permits;
- which action must stop when the evidence is missing; and
- how a person or agent can inspect, repair, rerun, roll back, or leave safely.

This is the normative contract for every skill distributed as part of Wildcat
Labs Skills. The copies inside plugins are generated from this file and must be
byte-identical. They are installation copies, not separate laws. In the source
distribution, `docs/the-promise-machine-explained-properly.md` gives an
example-led introduction.

## Contract identity

The shared contract identity is `promise-machine/v1`. It identifies this law's
format and semantics. It is neither a plugin package version nor a skill
evolution version.

## Governing principle

> No skill may claim more than its evidence establishes, or authorise a more
> consequential transition than that evidence warrants.

This principle applies to answers, derived artefacts, repository changes,
publications, deployments, security conclusions, financial conclusions, and
other external actions produced through the suite. A passing check establishes
only the promise that names it. It does not establish the skill's general
correctness, the truth of its inputs, or a neighbouring claim.

## Scope

The contract applies to first-party skills, nested skills, vendored skills,
routers, runtime contracts, generated copies, and evidence hand-offs. Each
logical skill has one canonical implementation. Routers select that
implementation and establish no domain result of their own.

Vendored instructions remain upstream-owned and byte-for-byte unmodified. A
first-party overlay may bind a vendored operation to this contract when it
names the upstream digest, the bounded promise and the Wildcat-owned evidence.

## Vocabulary

| Term | Meaning | Required binding | Nearest refusal |
| --- | --- | --- | --- |
| Promise | A bounded claim made by one skill operation | Stable promise id and canonical skill | An adjacent claim |
| Promise boundary | The subject, scope and nearby conclusions the promise does not support | Subject and scope | Unexplained scope widening |
| Promise check | Identified evidence evaluated to decide whether a promise holds | Evidence identity and result | Unchecked evidence |
| Authorised transition | The representation or action a satisfied promise permits | Consequence level | A more consequential action |
| Refusal | Denial of the dependent transition when the promise is not established | Blocked transition | Continuing after failure |
| Recovery | Inspection, cure, rerun, rollback or safe exit left available after refusal | Actionable recovery path | Global halt or no exit |
| Exception | An attributed, scoped and recorded decision to waive or narrow one gate | Authority, scope, record and expiry | Silent waiver |
| Evidence inheritance | A consumer may narrow evidence or add separately identified evidence | Producer, consumer and original class | Unexplained strengthening |
| Bounded conformance | Observed behaviour stayed inside a declared boundary for named inputs, adapter, recorder and search | Inputs, adapter, recorder and search | Safety proof or unobserved executions |

## Evidence classes

Evidence classes describe relations, not a universal strength ordering:

| Class | Establishes | Does not establish |
| --- | --- | --- |
| `checked` | An identified deterministic rule or schema accepted the subject | Truth or completeness outside that rule |
| `recomputed` | A result was derived again from identified inputs and method | Authority beyond those inputs and method |
| `proved` | A named formal, cryptographic or defined proof relation accepted the subject | Any claim outside that proof relation |
| `measured` | A value was observed under a recorded method and environment | Universal performance or causation |
| `recorded` | Bytes or a statement were preserved from an identified source | Truth of the source assertion |
| `attested` | An identified actor or system made the statement | Independent truth of the statement |
| `inferred` | A conclusion follows under a stated rule from named evidence | Direct observation or proof |
| `unknown` | The matter was not established | Any positive transition |

A domain may refine a class, such as `proved: EIP-1186 account proof`, while
keeping the base class recognisable. A consumer records any change of class and
the evidence that supports it. Absence, ambiguity and `unknown` never pass.

## Promise declarations

Every governed first-party canonical skill has exactly one `## Promise Machine
contract` section. It contains one or more stable `### <promise-id>` blocks.
Each block carries these fields exactly once:

- `Promise`
- `Evidence`
- `Evidence classes`
- `Boundary`
- `Authorises`
- `Consequence`
- `Refuses`
- `Recovery`
- `Exceptions`

The promise id is stable within the skill. Operations whose claims or
authorised transitions differ use separate promise ids. Evidence names the
command, record, test, proof relation or observation that supports the claim.
The boundary names the nearest tempting overclaim. Refusal names the transition
that stops. Recovery remains usable when refusal occurs.

`Exceptions: none` is explicit. A supported exception follows the rules below.

## Consequence levels

The consequence belongs to the authorised transition, not to the skill as a
whole:

| Level | Transition | Minimum enforcement |
| --- | --- | --- |
| 0 | Response or presentation only | Preserve scope, content and uncertainty |
| 1 | Derived artefact | Validate structure, provenance and visible gaps |
| 2 | Repository or durable-data mutation | Tests, negative evidence and recoverable change |
| 3 | Publication, deployment, external action, security or financial conclusion | Fail-closed gate, recorded authority and independently inspectable evidence |

A skill with operations at different levels declares separate promises. A
level-3 transition cannot rest only on model judgement, unrecorded operator
memory, an unchecked receipt or evidence whose subject does not match.

## Composition

Composition preserves the producer's boundary. A handoff records the producing
skill, consuming skill, subject, scope, evidence class, time domain and any
transformation. The consumer can add separately identified evidence. It must not
rename narrow evidence into a stronger class or drop a conflict, gap, refusal
or recovery path.

In particular:

- Lemma chunks remain source-linked retrieval material; they do not establish
  answer truth.
- Lazarus recorded RPC evidence remains recorded unless its named proof check
  established a narrower proved relation.
- Berean citations, evaluations and promotion records establish their declared
  release gates; they do not establish factual truth or model quality.
- Janus results remain bound to the named host adapter, manifest, recorder and
  bounded search; they do not establish hook safety, complete liveness or
  cross-host conformance.
- Ariadne binds an artefact digest to declared evidence; without an external
  signature verifier it does not establish author identity.
- A Fiat run-observation binding preserves the observation validator and
  capture boundaries. It attaches only the checked prefix to one receipt; it
  does not make observation availability or event truth delivery evidence.
- Synkrisis contributes a checked cohort, bounded findings over it, a
  fixed-template report and a recomputation of all three. Verification
  establishes recomputability alone: it cannot turn repeated observations into
  cause, model quality, or authority to
  act. It preserves the validated observation and receipt boundaries, so a
  comparison result carries its counterevidence and unknown runs into any
  hand-off and strengthens nothing.

Any unexplained strengthening is a conformance failure.

## Refusal and recovery

Missing, stale, malformed, mismatched or insufficient evidence fails closed.
Failure blocks the dependent transition and no broader one. Inspection,
diagnosis, repair, rerun, rollback and safe exit remain available unless the
promise explains why a particular recovery cannot exist.

A refusal report names the promise id, failed field or evidence, consequence
level, blocked transition and recovery action. A checker never deletes,
rewrites or quarantines the failing source merely to produce a passing result.

## Exceptions

An exception is evidence, not silence. It names:

- the person or policy with authority;
- the promise id and exact gate being waived or narrowed;
- the affected subject and scope;
- the durable record holding the reason;
- the expiry, or why expiry cannot apply; and
- the recovery or revocation path.

An exception cannot claim that missing evidence exists, strengthen an evidence
class, erase a recorded conflict or authorise a transition beyond the named
scope. Unattributed, unrecorded, expired or over-broad exceptions fail closed.

## Conformance

Structural conformance establishes that the declarations, identities, copies
and coverage records have the required shape and agree. It does not establish
that a domain promise is true. Behavioural conformance comes from the named
domain tests, negative specimens, proof checks, measurements and manual
demonstrations.

The checker discovers the governed universe from repository manifests and
skill paths. A hand-maintained coverage file may classify discovered entries;
it may not define the universe or remove an entry from it. Empty discovery,
unclassified skills, duplicate logical identities, missing declarations,
divergent copies and unbound vendored instructions are failures.

Checker output names a stable finding code, fault class, path, promise id when
known and the action that clears it. JSON and text reports describe the same
findings. The checker reaches no network and executes no evidence command.

## First-party licence promise

### promise-machine-first-party-licence

- Promise: A successful `check --only licences` establishes that the root and every first-party plugin carry the same Apache-2.0 licence bytes, and that both host manifests name Apache-2.0 and Wildcat Labs.
- Evidence: The fixed root `LICENSE`, discovered first-party plugin set, byte comparisons, and parsed Claude and Codex plugin manifests.
- Evidence classes: checked, recomputed
- Boundary: The check does not establish copyright ownership, provide legal advice, or inspect, govern, or relicense vendored work; the Pashov skill trees retain their upstream MIT licence and notices.
- Authorises: Publishing the discovered first-party plugin surfaces with the repository's Apache-2.0 and Wildcat Labs licence declaration.
- Consequence: 3
- Refuses: A missing, unsafe, oversized, or divergent licence, an inconsistent host manifest, or any claim that the first-party licence covers a vendored skill.
- Recovery: Restore the canonical root licence and first-party copies, correct the host manifests, leave vendored licences untouched, and rerun the licence check.
- Exceptions: none

## Run observation promise

### promise-machine-run-observation-structural-validation

- Promise: A successful `python3 scripts/run_observation.py check <path>` establishes that the named regular JSON Lines file conforms to `promise-machine-run-observation/v1` under the validator's closed shapes, limits, lifecycle, backward-reference, evidence-binding, unknown-fact, optional-token, Unicode-path and final-snapshot rules.
- Evidence: The exact input path and validated bytes, one bounded final named-path reread with matching digest and file identity, v1 schema, standard-library validator, stable finding report, valid and refusing fixtures, focused tests and zero command exit.
- Evidence classes: checked
- Boundary: Validation does not capture a run, prove that the record is complete or externally true, establish cause or model quality, bind a Fiat receipt, make a security conclusion, authorise mutation, or prevent a writer changing the path after the final reread.
- Authorises: Treating only the named bytes as structurally conforming and passing that bounded result to a consumer that preserves its subject, scope, time domain, evidence class, unknowns and refusal boundary.
- Consequence: 1
- Refuses: Unsafe or unbounded input, a final byte or identity mismatch, malformed or duplicate-key JSON, an open event shape, missing identity, invalid order or lifecycle, a forward or cross-run reference, unbound or strengthened evidence, hidden reasoning, raw payloads, non-scalar, non-NFC, control-bearing, bidirectional or otherwise unsafe repository paths, placeholder host facts, invalid token counts or a non-zero finding report.
- Recovery: Inspect the stable finding code, repair the source record without having the checker mutate it, preserve unknowns and evidence boundaries, then rerun the same command.
- Exceptions: none

### promise-machine-run-observation-capture

- Promise: A successful `python3 scripts/run_observation_capture.py check <candidate>` establishes that the named bounded candidate was processed by `promise-machine-run-observation-capture/v1` into one accepted event, visible gap, or refusal before a durable observation exists.
- Evidence: The named candidate, closed standard-library adapter, capture schema, direct-allowlist fixtures, hostile byte-survival tests, source-owned reporter, and zero command exit.
- Evidence classes: checked
- Boundary: The result does not prove the source is true or complete, detect every secret, govern another host memory, itself bind a Fiat receipt, make a security conclusion, or authorise another controller transition.
- Authorises: Passing an accepted result to the capture writer, or recording the bounded gap or refusal without treating it as an accepted observation.
- Consequence: 1
- Refuses: An open or oversized candidate, raw payload family, malformed redaction, unsafe repository path, low-entropy correlation input, unknown shape, or writer bypass.
- Recovery: Remove the unsafe field from the candidate adapter, retain only a closed redaction or safe descriptor, then rerun the same command and hostile fixture surface.
- Exceptions: none

## Contributor ranking promise

### promise-machine-contributor-ranking

- Promise: A successful `python3 scripts/contributors.py --check` establishes that every contributor row GitHub returned for `wildcat-finance/skills`, and every merged pull-request author returned for each named supplemental repository, was placed in exactly one of ranked, excluded with a named reason, or refused; that each ranked login is a valid GitHub login absent from the declared runtime-host set and is neither the Shoggoth's account nor the repository owner; that a login qualified either through a resolved Skills commit with at least one bounded non-host authorship sample or by authoring a merged pull request in `wildcat-finance/shoggoth-wave-atlas`; that the order is Skills commits, then merged pull requests across both repositories, then login; and that `CONTRIBUTORS.md` and the marked region of `README.md` match that one computation byte for byte.
- Evidence: The recorded Skills contributors, per-account Skills merged-pull-request and commit-authorship reads, the complete paginated closed-pull-request read for each supplemental repository, the host-set parity check against `hexctl.py`'s declaration, the login grammar check, the per-identity classification lines, the ranking digest, the byte comparison of both artefacts and zero command exit.
- Evidence classes: checked, recorded
- Boundary: Ranking does not establish that the counts fairly measure contribution, that a commit carried judgement, who wrote which line, who else worked on a pull request, anything about a person beyond the account GitHub attached to the commit or pull request, or that GitHub's account resolution is correct. The commit column counts `wildcat-finance/skills` only; it does not count Wave Atlas commits. A pull-request author is the account that opened the PR, not every commit author, reviewer or collaborator. The run does not detect a merge that discarded commit authorship before the commit reached the Skills default branch, and its Skills authorship corroboration samples at most twenty commits per account rather than all of them.
- Authorises: Writing `CONTRIBUTORS.md` and the marked region of `README.md` and nothing outside those two targets, and reporting the ranking without strengthening what the counts mean.
- Consequence: 1
- Refuses: An account type other than User or Bot, a Bot absent from the declared host set, a merged pull request without a classifiable author, a login failing the GitHub login grammar, a repository argument carrying query syntax, a duplicate repository source, any failed API read including a rate limit, a host set diverged from `hexctl.py` in either direction, an excluded login reaching the ranked output, a `README.md` that is absent or not UTF-8, and a read that would silently truncate.
- Recovery: Read the stop, which names the identity or field at fault; extend the host set in `hexctl.py` and `scripts/contributors.py` together for an unknown host, set a token or wait for the named reset for a rate limit, and rerun with `--write` for a stale artefact. The generator never repairs an input.
- Exceptions: none

## Router selection promise

### promise-machine-router-selection

- Promise: A successful `python3 -m unittest tests.test_router_selection` establishes that `tests/fixtures/router-selection/cases.json` declares schema `promise-machine-router-selection/v1`, that every case carries the seven fields that schema names with a unique id and a recognised expectation, that every canonical name a case expects or contests and every name a pair separates is the frontmatter name of a real `SKILL.md` under `plugins/`, that every quoted deciding sentence still occurs in the section of the file its entry names, that every row of the router's selection tables is named by at least one case, that every pair the corpus declares is contested by at least one case, and that any recorded run block carries a corpus digest recomputed from the cases on disk, names the model, date and prompt-template digest a reader needs to recount it, carries a prompt-template digest equal to the digest of the template committed beside the corpus, and names each of its failures by a case id this corpus holds and by what the graded context answered, either a canonical skill that resolves or a refusal in the corpus's two-reason vocabulary.
- Evidence: The one fixed repository-relative corpus path, the closed quotable set of `AGENTS.md` and `.agents/skills/promise-machine/SKILL.md`, the canonical skill names discovered under `plugins/`, the whitespace-collapsed sentence search inside each named section, the cases digest recomputed from the cases on disk, the malformed-corpus guard and the two degraded-corpus guards read from a closed set of fixture constants, zero command exit, and, for a run block once one is recorded, its preserved model, date and prompt-template digest, the prompt template committed beside the corpus and digested from those bytes, and its observed case, pass and fail counts.
- Evidence classes: checked, measured, recomputed, recorded
- Boundary: The check establishes nothing about how any agent routes, that the corpus is representative of real requests, or that a case expects the selection a reader would agree with. A contested case establishes that the corpus declares a boundary, not that the request it carries could only be answered by reading the sentence that separates it. A recorded score is evidence about one model, one prompt template, one corpus digest and one date, and it is never a gate. The prompt-template digest names the prompt the grading supplied and not the whole context the graded agent ran in, since a harness system prompt, repository instruction files and tool definitions reach that context and no digest here covers them.
- Authorises: Reporting the corpus coverage and the latest recorded run through `tests/emit_router_selection_report.py`, whose bytes the `router_selection` coverage entry pins beside the corpus and the checker, and citing a recorded run with the model, date, prompt-template digest and corpus digest it names attached.
- Consequence: 0
- Refuses: An absent, unreadable, non-UTF-8 or non-JSON corpus, a corpus declaring a schema this checker does not support, a top-level value that is not an object, a missing or mistyped `cases`, `pairs` or `runs` key, an empty case list, a case whose field set or expectation the schema does not name, a repeated case id, a required case field that is present but empty, a `contested` that is not a list of canonical names, a quotation that is not the three keys the schema names, a quoted path outside the closed set, a canonical name no `SKILL.md` declares, a sentence its named section no longer contains, an empty or whitespace-only quotation, which would otherwise occur in every section, a pair whose field set, id, separated skills or quotation the schema does not name, and a run block whose field set the schema does not name, whose digest disagrees with the cases on disk, whose `failures` is present but is not a list, or whose case, pass and fail counts cannot all be true. It also refuses a router row whose canonical selection no case expects, two rows selecting the same canonical skill, which one case would cover for both, the one row that names no canonical skill left unquoted by every case that selects, a selection cell that is neither a canonical name in backticks nor that row's known phrase, a router carrying no `## Select one runtime contract` section or no selection table inside it, a section whose parsed rows and table lines disagree, a corpus declaring no pairs at all, a declared pair no case contests in full, and a pair carrying no list of separated skills to contest. It also refuses a run block that is not an object, a `model` that is absent, empty or not a string, a `date` that is not a `YYYY-MM-DD` date, a `prompt_template_sha256` that is not a lowercase sha256 digest, without which the prompt the run used is unrecoverable, an absent or unreadable prompt template, a `prompt_template_sha256` that is not the digest of the prompt template committed beside the corpus, since a digest naming bytes the repository does not hold is evidence about no prompt at all, a run covering no cases at all, whose counts agree with each other while measuring nothing, a failure entry whose field set is not exactly `case` and `selected`, a failure naming a case id this corpus does not hold, the same case id named by two failures, and a failure recording an answer that is neither a canonical name a `SKILL.md` declares nor one of the two refusal forms.
- Recovery: Read the failure, which names the case or pair, the file and the sentence it looked for; requote the current sentence or retire the case rather than rewording the source the corpus grades, correct a canonical name that no longer resolves, and regrade a stale run block instead of editing its digest to agree.
- Exceptions: none

## Agent instruction prototype promise

### promise-machine-agent-instruction-prototype

- Promise: A successful `python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json` establishes that the three source-bound fixture models validate, decode from their compact forms to the exact canonical JSON bytes, reformat identically, retain all 17 reviewed bindings, including nine Fiat bindings, and answer all 14 hostile mutations by their declared outcome. It also establishes three exact structural round trips, nine closed questions and the manifest's explicit `model_evidence_status: disabled`.
- Evidence: The digest-bound manifest and schema, three authored source spans, canonical models, compact documents, 17 reviewed source-span records, nine Fiat bindings, nine closed questions, 14 hostile mutations and three exact round trips; the exact frozen digests of the historical measurement and parity files and their supporting records; the reference checker, specialised coverage entry, focused integration tests, and zero command exit.
- Evidence classes: checked, recomputed, recorded
- Boundary: Canonical-model equality applies only after the reviewed Markdown-to-model bindings and only to this closed version-1 vocabulary. Exact frozen measurement and parity byte identity remains checked, but the reports' recorded results are historical, not current evidence or transition gates, and this result makes no claim about their token counts or model answers. It does not establish losslessness for arbitrary English, deployed-agent transfer, general model behaviour, repository-wide migration safety, or Shoggoth readiness, and no adapter output has instruction authority.
- Authorises: Treating the exact checked compact documents as derived views of their bound canonical models and reporting the bound three-fixture structural, binding, question, mutation and disabled-status results with their limits attached.
- Consequence: 1
- Refuses: A missing, additional, linked, stale, malformed or mismatched manifest, source, span, schema, model, compact form, question, mutation or frozen historical evidence file; a status other than `disabled`; incomplete bindings or risk coverage; a failed round trip or mutation; a `measure` or `parity` request while evidence is disabled; or any attempt to treat a historical report, model or adapter as current instruction evidence or authority.
- Recovery: Read the stable refusal code and node path; restore the exact bound source or frozen historical bytes, or repair the reviewed model, checker or declared structural evidence at its owned boundary; regenerate affected structural derivatives and rerun the structural and hostile checks. Activation and newly issued model evidence require separate authority. Do not edit a digest, expected answer or refusal set merely to fit an observation.
- Exceptions: none

## Installation copies

The root `PROMISE_MACHINE.md` is the authored source. Each
`plugins/<plugin>/PROMISE_MACHINE.md` is written only by
`scripts/promise_machine.py sync`. The destination is fixed, writes are atomic,
symlinks and paths outside the repository are refused, and `sync --check`
rejects a missing or byte-divergent copy.

Standalone plugin runtime contracts load their local copy. Repository-wide
work loads this root file. Both surfaces therefore read the same contract
bytes under the same identity.
