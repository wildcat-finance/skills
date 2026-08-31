# study: compact lossless agent instruction language

assuming, unless corrected:

| id | assumption | evidence and consequence |
| --- | --- | --- |
| A1 | the entry ref is `main` at `d1ca7ba5af741d45d1da6492632661e688157bff` | the run worktree, local `main`, and `HEAD` resolved to that commit on 2026-08-30; all repository paths and prior-art claims below are bound to those bytes |
| A2 | issue [#909](https://github.com/wildcat-finance/skills/issues/909) is the complete task authority | it asks for a bounded prototype, not a repository-wide conversion, and names the three required demonstration classes and the parity, mutation, byte, token, and bootstrap evidence |
| A3 | the issue's 2,310,966-byte census is recorded evidence, not a measurement repeated by this study | the issue records 72 `SKILL.md` files, 17 runtime `AGENTS.md` files, 17 Promise Machine contracts or copies, and 76 reference documents at the entry ref; Horos says a byte census is not a token count |
| A4 | human Markdown remains the authored source during this prototype | the issue keeps front-facing descriptions, READMEs, ADRs, primers, and similar prose; changing authorship to the compact form would be a later irreversible decision |
| A5 | “lossless” means equality in one declared, closed instruction model, not proof that arbitrary English has one meaning | a reviewed source-to-model binding states what the prototype claims; the formatter and decoder can prove exact model equality, while behavioural questions test but do not prove the human mapping |
| A6 | the first corpus contains exactly three bounded fixtures | they are `promise-machine-router-selection` from `PROMISE_MACHINE.md`, Fiat's study-and-runbook phase contract from `plugins/hexaemeron/skills/fiat/SKILL.md`, and `horos-boundary-check` from `plugins/horos/skills/horos/SKILL.md` |
| A7 | the new codec is a root framework capability, not a change to Horos, Brevitas, or a new marketplace plugin | Horos governs what is left unread, Brevitas excludes completeness-oriented specifications, and neither contract authorises a replacement representation; a plugin decision can follow evidence from the prototype |
| A8 | Python 3.14.6 and its standard library are the implementation toolchain | `.python-version` and `python3 --version` agree; no parser, model SDK, or tokenizer dependency is present in the current tree |
| A9 | a tokenizer profile and two genuinely different agent families are required evidence but are not selected by the issue | the language design keeps both behind recorded adapters; no token-reduction or cross-family-transfer claim is authorised until exact identities, context, acquisition, and results are present |
| A10 | model answers are observations, never the source of instruction meaning | the reviewed instruction model and deterministic checks are authoritative; a model result may falsify parity but may not repair or strengthen the model |
| A11 | this study does not change Shoggoth or any external repository | issue #909 expressly defers migration; all prototype paths remain in `wildcat-finance/skills` |
| A12 | all existing audit records stay immutable | the study reads verified synopses as prior evidence and carries their open limits forward; it does not rewrite a finding, disposition, or lead |

these assumptions are sufficient to choose the prototype architecture. The
unselected tokenizer profile and agent-family pair affect whether the later
demonstration earns its measurement claims, not the representation design. If
either remains unavailable at its runbook gate, that claim stays unknown and
the run cannot meet issue #909's acceptance criteria.

## 1. problem statement

The repository repeats complete agent-facing instructions in long Markdown.
That prose is inspectable, but an agent pays to ingest conditions, refusals,
evidence classes, precedence, recovery, and exact literals every time. Issue
#909 records 2,310,966 bytes across four non-overlapping instruction classes at
the entry ref. It asks whether a smaller agent-first form can preserve every
governed distinction rather than merely make the prose shorter.

The user is a contributor who needs to ship and review instruction changes
without weakening the Promise Machine boundary. The immediate user is not a
general text compressor. They need a small language whose supported meaning is
explicit, whose output can be diffed, whose decoder is deterministic, and
whose refusals are visible when a document uses meaning outside version 1.

The prototype will define `wildcat-agent-instruction/v1`, a closed instruction
model and a compact line encoding. A reviewed binding maps each source fixture
to canonical JSON that carries all supported meaning. A standard-library CLI
validates canonical JSON, formats it into the compact form, decodes the compact
form back to canonical JSON, compares the two canonical byte strings, checks
source digests, and emits a measurement record. The compact form is derived;
the human Markdown remains the authored source.

Version 1 supports only these semantic constructs:

- ordered documents, sections, and directives with stable ids;
- `require`, `forbid`, `permit`, `refuse`, `recover`, and `unknown`
  directives;
- nested `when`, `unless`, `exception`, and `scope` expressions;
- explicit `before`, `after`, and `overrides` edges between directive ids;
- Promise Machine evidence classes, promise boundaries, authorised actions,
  consequences, refusals, recovery, and exceptions;
- exact UTF-8 literals for identifiers, paths, hashes, commands, numbers,
  dates, links, and quotations, with no Unicode normalisation;
- source spans and SHA-256 bindings that locate the human statement from which
  a model node was reviewed.

It does not assign a meaning to arbitrary prose. A source statement outside
those constructs is an unsupported node and blocks encoding. Comments and
display prose may be carried as exact literals, but they grant no instruction
authority.

### working demonstration

The demonstration uses the three fixtures in assumption A6. For each it
commits:

1. the exact source path, source span, and source SHA-256;
2. reviewed canonical `wildcat-agent-instruction/v1` JSON;
3. deterministic compact bytes and their decoded canonical JSON;
4. a closed set of fresh-context questions with exact permitted answers and
   explicit refusal answers;
5. hostile mutations that drop or move one negation, precedence edge, scope,
   evidence class, or exact literal;
6. source, canonical JSON, compact, decoder-bootstrap, and corpus-amortised
   byte and token counts; and
7. one recorded run per available agent family, with model, host, date, prompt
   template, repository-instruction inventory, tool-definition inventory,
   tokenizer profile, corpus digest, and every observed answer.

The original and compact fixture are asked separately in fresh contexts. No
case shares examples, labels, answers, or previous model output with another
case. A changed required answer fails parity. A hostile mutation must either
fail parsing or validation, change the canonical model digest, or produce the
declared changed answer. A mutation that silently retains the original answer
is a finding, not proof that the dropped construct was redundant.

The prototype succeeds only when all of the following are true:

- every fixture validates and `decode(format(model))` equals the original
  canonical JSON bytes;
- every compact fixture is byte-for-byte reproduced by a second format pass;
- every source digest and source span matches the entry-ref fixture;
- all declared original-versus-compact questions have the same required
  answer in each recorded family, with zero unrecorded answer values;
- every hostile mutation is detected by structure, digest, or its required
  changed answer;
- one declared real model tokenizer reports fewer total compact-corpus tokens
  after adding the complete decoder bootstrap than the source corpus reports;
- the report keeps byte counts separate from tokenizer counts and includes the
  one-document and amortised totals; and
- the root test suite, Promise Machine checks, portable-runtime checks,
  Protasis, Imprimatur, and the focused codec tests all exit 0.

The intended proof commands are:

```bash
python3 scripts/agent_instruction.py check \
  --manifest tests/fixtures/agent-instruction-v1/manifest.json
python3 scripts/agent_instruction.py measure \
  --manifest tests/fixtures/agent-instruction-v1/manifest.json \
  --output tmp/agent-instruction-v1-measurement.json
python3 -m unittest tests.test_agent_instruction
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
```

`measure` is clean only when its manifest names an available, exact tokenizer
profile and both the bootstrap-inclusive token delta and the parity checks
pass. A byte-only or heuristic count is a recorded incomplete run.

## 2. prior art and current state

### repository and organisation prior art

The Promise Machine already supplies the semantic vocabulary that this
prototype must preserve: promise, evidence, evidence class, boundary,
authorisation, consequence, refusal, recovery, exception, precedence, and
unknown. Its installation copies also establish the right source/derived-view
asymmetry: root `PROMISE_MACHINE.md` is authored, plugin-local copies are
generated, and drift refuses. The compact language should reuse those meanings
by id rather than invent shorter synonyms.

The portable router is another relevant source. ADR-041 and
`docs/promise-machine/router-selection-v1.md` use a closed corpus, exact quoted
sentences, source locations, digests, hostile fixtures, and a report derived
from checked bytes. They also expose the limit of model grading: a run is bound
to one model, prompt, corpus, date, and incomplete context inventory; its score
is recorded evidence, never a gate.

Horos is adjacent but not the owner. Its boundary scanner saves reading by
leaving evidence-classified token sinks unread. Its census counts bytes, not
model tokens, and its skeleton map is orientation rather than full meaning.
`plugins/horos/docs/study.md` records why the earlier Epitome-style rewriting
path was rejected: its limited licensed saving came with worse task completion,
whereas excluding known sinks saved more bytes without rewriting source.
LongCodeZip is selection-based code-context reduction, so it is useful negative
prior art for a semantic codec.

Brevitas controls the volume and structure of engineering prose. Its contract
excludes completeness-oriented specifications and never authorises removal of
protected evidence. It therefore must not lint or define the compact language.

The verified audit-synopsis mechanism supplies a second source/derived-view
pattern. The whole-set currency command exited 0 before this study was written,
so the read views cited here matched their source records at the entry ref.
The issue-369 synopsis carries the exact-source-byte rule, deterministic view,
source/view asymmetry, and explicit legacy omissions. The issue-499 synopsis
is direct evidence for isolated model cases: batched context and example labels
contaminated the first grading; a later isolated regrade scored 35 of 36, and
the prompt digest still did not cover system instructions or tool definitions.
It also records failures from empty quotations, unsafe paths, missing refusal
branches, and incomplete prompt context. Those limits become checks in this
study rather than prose warnings.

No existing audit record covers `wildcat-agent-instruction/v1`, because that
capability does not exist at the entry ref. The in-scope adjacent audit records
read were:

- `audit/rounds/fiat-369-read-audit-synopsis-resigned.synopsis.md`, for
  immutable sources and deterministic read views; and
- `audit/rounds/fiat-499-grade-router-selection-not-just-resolution.synopsis.md`,
  for fresh-context grading, closed answer sets, prompt identity, and hostile
  corpus handling.

Other root and plugin audit records remain outside this prototype. Their
findings are neither closed nor reclassified here.

### last two applicable merged pull requests

No merged pull request has changed the requested language because the language
does not yet exist. The two most recent merged changes at the entry ref that
exercise the same evidence and agent-evaluation boundaries are:

- [#780](https://github.com/wildcat-finance/skills/pull/780), merged as
  `43f9ea57`, which shipped Ariadne's grounded-agent predicate with a closed
  schema, bounded capture, hostile fixtures, exact argv demonstration, and
  digest binding. It did not establish historical producer argv, live model or
  network behaviour, Windows behaviour, or an external signer.
- [#697](https://github.com/wildcat-finance/skills/pull/697), merged as
  `e5131e9a`, which shipped router-selection grading and later received the
  isolated 35-of-36 regrade. Its result stays bound to one model, one prompt
  template, one corpus digest, and one date, and never gates routing.

The prototype carries those limits forward. It records exact producer argv,
model and tokenizer identities when known; it keeps unavailable host context
as unknown; it treats behavioural runs as falsification evidence rather than a
semantic oracle; and it does not claim live-provider or cross-family coverage
from synthetic fixtures.

### outside prior art

[RFC 5234](https://www.rfc-editor.org/rfc/rfc5234.html) supplies a familiar
ABNF notation and explicit operator precedence for the grammar. It describes
syntax, not instruction meaning.

[RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html) supplies the canonical
JSON comparison pattern: constrained JSON input, deterministic property order,
and stable bytes. Version 1 follows its canonicalisation discipline but refuses
floating-point values, duplicate keys, Unicode normalisation, and implicit
string coercion, which keeps exact instruction literals visible.

The [TOON specification](https://github.com/toon-format/spec/blob/main/SPEC.md)
is line-oriented, deterministic, strict, and based on the JSON data model. It
is useful syntax prior art, but its version 4.1 document was still a working
draft when inspected and it does not define instruction authority,
precedence, evidence classes, or recovery. Depending on it would make a
generic interchange format part of this capability's trust base.

[LLMLingua](https://aclanthology.org/2023.emnlp-main.825/) uses a model to
remove prompt tokens while attempting to retain task performance. That is a
different promise: deletion is model-dependent and observed performance is not
exact model equality. The project is negative prior art for this issue's
lossless, vendor-independent boundary.

### open work carried or refused

- Horos's held frontier remains Horos work. This prototype does not change its
  boundary categories, skeleton extractor, census, or `EVOLUTION.md`.
- Brevitas remains a prose-volume skill. Its deferred marketplace candidacy
  does not authorise use on this completeness-oriented study or codec.
- The router-selection run's incomplete context digest and single-run
  repeatability remain visible. The new evaluator records a larger context
  inventory but does not claim it can hash hidden host instructions.
- Grounded-agent capture's unknown historical producer argv, live-provider
  behaviour, and external signer stay unknown. The language fixture does not
  close them.
- Authored-source reversal, repository-wide conversion, Shoggoth migration,
  and a new marketplace plugin are refused in this packet and require separate
  receipted decisions.

## 3. constraints and non-goals

The exact base is `main` at
`d1ca7ba5af741d45d1da6492632661e688157bff`. The run uses Python 3.14.6.
Implementation should use the standard library for parsing, canonicalisation,
validation, path handling, hashing, and tests. A real tokenizer may be an
external, versioned measurement adapter; it is not a runtime dependency of the
decoder.

Included:

- one versioned semantic model, grammar, decoder contract, formatter,
  validator, and measurement manifest;
- exact round-trip, canonical-byte, source-binding, mutation, resource-limit,
  and deterministic-format tests;
- the three-fixture corpus in assumption A6;
- fresh-context parity runs with a closed answer vocabulary and explicit
  unknown host context;
- source, compact, canonical-model, bootstrap, and amortised corpus
  measurements; and
- root Promise Machine registration, an ADR, a public format document, tests,
  and deterministic reports needed to verify the prototype.

Excluded:

- a claim that arbitrary English can be encoded losslessly;
- automatic prose-to-model extraction, paraphrase equivalence, embeddings,
  semantic similarity, model-written authority, hidden chain-of-thought, or an
  agent that repairs invalid instructions;
- editing the three source fixtures merely to improve compression or make the
  reviewed model easier to write;
- repository-wide conversion, runtime deletion of Markdown, context-window
  routing, or an installation mechanism;
- changing Promise Machine consequences, phase order, skill selection,
  evidence strength, audit findings, or the meaning of a source contract;
- a new plugin, new canonical skill, Horos category, Brevitas rule, CI job,
  network service, provider credential, or Shoggoth repository change; and
- speed, memory, universal model transfer, or universal tokenizer claims.

Always:

- preserve exact literals, source order, duplicate ordered directives, explicit
  unknowns, negations, exceptions, scopes, precedence, evidence classes,
  authorisations, refusals, and recovery;
- decode before use and compare canonical model bytes before a compact form can
  be called equivalent;
- run each behavioural case in a fresh context and record the exact available
  context inventory, model, host, prompt, corpus, and tokenizer identities;
- count source, model, compact, and bootstrap bytes and tokens separately;
- treat source Markdown as authored and generated compact files as derived;
- use bounded regular files, confined relative paths, atomic output, explicit
  argv, and no shell evaluation; and
- run focused tests, the root suite, Promise Machine checks, portable runtime
  checks, Protasis, Imprimatur, and `git diff --check` before delivery.

Ask first:

- adding or vendoring a tokenizer, parser, model SDK, grammar generator, or
  other dependency;
- selecting a paid or credentialed model endpoint, allowing source content to
  leave the process, or retaining model responses outside the declared report;
- changing CI, generated installation topology, public version naming, or a
  released schema after version 1 is published;
- making the compact form authoritative, expanding beyond the three fixtures,
  or changing source prose to fit the language; and
- creating a plugin, assigning a marketplace owner, or migrating another
  repository.

Never:

- silently drop, merge, reorder, infer, normalise, or paraphrase a governed
  construct;
- interpret an unknown opcode, field, version, evidence class, relation, escape,
  or duplicate map key;
- use a heuristic word count as a model-token count or omit bootstrap cost;
- feed one case's answer, label, example, or model output into another case;
- call a model answer semantic truth, expose hidden reasoning, store a secret,
  invoke untrusted text through a shell, follow a supplied symlink, or write
  outside the selected output root; or
- claim Shoggoth migration, cross-agent transfer, or token reduction without
  the exact recorded evidence that the claim names.

## 4. design options

### option A -- canonical JSON only

Use a closed JSON Schema, RFC-8785-style canonical bytes, and no second syntax.
This has the smallest parser and trust base. It gives exact round trips and
good tooling, but repeated field names, JSON punctuation, and quoted prose are
unlikely to repay decoder overhead across the bounded corpus. It also does not
test the issue's compact-language hypothesis. Reject as the control design,
and keep its canonical bytes as the comparison model.

### option B -- closed instruction model plus a small line grammar

Chosen. Review source statements into canonical JSON, then format that model
with a versioned, ABNF-defined line grammar. The grammar uses fixed short
opcodes only for constructs whose full names live in the versioned decoder
table. Nesting expresses scope; explicit ids and relation records express
order, precedence, and exceptions; exact literals use one length-prefixed
UTF-8 form so delimiters and line breaks cannot change meaning. Unknown input
refuses.

This design adds a second parser and a bootstrap dictionary, so it must prove
determinism, bounds, and net corpus savings after that complete overhead. In
return, the semantic domain stays repository-owned, inspectable, diffable,
standard-library implementable, and independent of any model or external data
format. It is the least-comprehension design that can meet every acceptance
criterion: reviewers learn one small opcode table and the same Promise Machine
terms they already use.

### option C -- canonical model encoded with TOON

Use the same closed instruction model but serialize its JSON-shaped value with
TOON. This avoids designing all lexical rules and may reduce punctuation. It
adds a working-draft external specification to the decoder trust base, still
needs an instruction schema and validator, and gives generic keys no special
compactness without another dictionary layer. Reject for version 1. The
measurement harness may include it later as a non-authoritative comparison if
dependency and version acquisition are approved.

### option D -- model-assisted prompt compression

Ask a model to delete or rewrite words, then grade task answers. This is closest
to LLMLingua and may produce the largest token reduction. It cannot establish
exact instruction-model equality, makes the compressor model part of the
authority path, and can preserve benchmark answers while dropping a rarely
asked negation or recovery branch. Reject. It may remain external performance
prior art but cannot satisfy `wildcat-agent-instruction/v1`.

### chosen grammar and decoder contract

The public contract will define one UTF-8 document with a magic version line,
one declaration per physical line, two-space nesting, stable ids, and a fixed
opcode table. Length-prefixed literals count decoded UTF-8 bytes and may carry
any scalar Unicode value except an unpaired surrogate. A canonical backslash
escape carries line terminators, controls, backslashes, and the grammar's
delimiter bytes, so a literal cannot create a second declaration. The decoder
preserves the decoded bytes and performs no NFC conversion. Numbers in the
semantic model are exact decimal strings, not JSON numeric values. Maps are
represented by sorted, unique keys; ordered constructs are arrays and remain
ordered.

The decoder accepts only version 1, the fixed opcode set, the fixed field set,
the declared indentation, bounded lengths and depth, and a final newline. It
returns one canonical JSON byte string or one path-bearing refusal. The
formatter accepts only validated canonical JSON, emits one byte sequence, and
must be idempotent. The validator separately checks reference closure,
acyclic precedence, source spans and digests, evidence-class vocabulary,
exception targets, and exact-literal types. Neither parser executes a command
or invokes a model.

The source-to-model binding is deliberately manual and reviewable in version
1. A manifest records the source blob digest, exact byte span, model digest,
compact digest, bootstrap digest, question-set digest, mutation-set digest,
and measurement-profile digest. Passing the codec proves model equality. The
fresh-context corpus supplies bounded evidence that the reviewed model still
answers the questions the source answers; it cannot prove that no unasked
human meaning was missed.

## 5. risk register seed

```risk-register
semantic-domain-gap | a source statement uses meaning outside the closed version-1 model | unsupported constructs refuse and every fixture maps each governed source span to one reviewed model node
source-model-mismatch | the reviewed model omits or strengthens what the human source says | closed fresh-context questions plus source-span review and hostile omission mutants must expose a changed required answer
precedence-collapse | formatting or nesting changes which directive wins | stable ids explicit order edges cycle checks and precedence mutants must change the model digest or refuse
negation-drop | a lost forbid unless or refusal reverses an instruction | negation-bearing nodes are distinct opcodes and one dropped-negation mutant per fixture must fail the declared answer
exception-scope-drift | an exception escapes its parent scope or applies to another rule | exception targets and ancestor scope are validated and cross-scope references refuse
evidence-authority-drift | compact evidence fields authorise more than the source promise | evidence classes boundaries authorisations consequences refusals recovery and exceptions are required typed fields for Promise nodes
exact-literal-change | Unicode normalisation escaping or numeric coercion changes an identifier path hash command date link number or quotation | length-prefixed UTF-8 literals preserve bytes and canonical comparison plus mutation fixtures covers each literal class used
unknown-opcode-acceptance | a future or misspelled construct receives an unintended version-1 meaning | unknown versions opcodes keys enums escapes and relation kinds refuse before a model is returned
duplicate-key-shadowing | a later field hides an earlier security-relevant value | canonical JSON loading and compact parsing reject duplicate map keys while ordered repeated directives remain explicit array entries
resource-exhaustion | hostile depth line count literal size or relation fan-out consumes unbounded work | manifest-owned caps are checked before allocation and boundary fixtures exercise every cap plus one
path-or-shell-escape | a source output tokenizer or model adapter escapes the repository or executes supplied text | confined regular paths explicit argv no shell symlink refusal atomic outputs and bounded subprocess records
bootstrap-understatement | a compact corpus appears smaller because decoder schema prompt or opcode-table cost is omitted | the measurement manifest hashes and counts every required bootstrap byte and reports one-document and amortised totals
tokenizer-mismatch | counts are attributed to a model tokenizer that did not produce them | the profile records tokenizer name version vocabulary digest executable digest argv and exact input digests and refuses heuristic counts
evaluation-contamination | examples labels prior answers or repository paths leak the expected result | one fresh context per case fixed neutral template context inventory and no batched model conversation are required
closed-answer-omission | the report counts a surprising answer as a pass because it was not representable | every case lists all accepted and refusal answers before execution and an unlisted answer is a failure preserved verbatim within size limits
agent-transfer-overclaim | one family or hidden shared system context is presented as cross-family parity | two distinct recorded family identities are required and unavailable host instructions stay unknown beside the claim
derived-view-drift | source model compact form report or generated Promise Machine copy changes without its siblings | manifest digests deterministic regeneration and root currency tests refuse any stale derived byte string
ownership-expansion | a root prototype silently changes Horos Brevitas Fiat or another repository | scoped paths and contract tests leave sibling skill behaviour unchanged and any plugin source reversal or external migration asks first
```

## 6. glossary seeds

| term | version-1 meaning |
| --- | --- |
| authored source | the human Markdown whose bytes and spans a fixture binds; it remains authoritative during the prototype |
| instruction model | the closed JSON-shaped domain of directives, conditions, relations, evidence fields, exact literals, and source bindings supported by version 1 |
| canonical model bytes | the sole deterministic UTF-8 JSON representation of a validated instruction model, used for equality and digests |
| compact form | the deterministic line encoding derived from canonical model bytes; it has no authority without validation and a matching manifest |
| decoder bootstrap | every grammar, opcode table, schema, decoder instruction, and fixed prompt byte that a fresh consumer needs before compact bytes can be interpreted |
| lossless | `decode(format(model))` has the same canonical model bytes; it is not a claim about arbitrary English or unasked human interpretation |
| directive | one stable-id instruction: require, forbid, permit, refuse, recover, or preserve an unknown |
| scope | the explicit ancestor path within which a directive, condition, or exception applies |
| precedence edge | an explicit `before`, `after`, or `overrides` relation between stable directive ids |
| exact literal | a length-prefixed UTF-8 value whose bytes may not be normalised, coerced, paraphrased, or inferred |
| reviewed binding | the recorded source path, byte span, source digest, model-node id, and reviewer provenance connecting Markdown to the instruction model |
| parity question | a predeclared fresh-context question with a closed set of exact accepted and refusal answers, asked separately of source and compact inputs |
| hostile mutation | one deliberate change to syntax or meaning, such as dropping a negation, precedence edge, scope, evidence class, or exact literal |
| silent acceptance | a hostile mutation that passes validation and still receives the original required answer without an expected model-digest change; it is a finding |
| tokenizer profile | the exact tokenizer identity, version, vocabulary and executable digests, argv, and input encoding used for a token count |
| measurement manifest | the canonical record binding corpus, bootstrap, tokenizer, model contexts, questions, mutations, and output digests |
| agent family | a separately identified model/runtime lineage; two aliases routed to the same undisclosed backend do not establish two families |
| unknown | a required fact that was not established and remains explicit; it is never encoded as false, empty, or inferred |

## 7. sources

### task, instructions, and live state

- [issue #909](https://github.com/wildcat-finance/skills/issues/909), read as
  the task authority and source of the entry-ref census and acceptance terms;
- `AGENTS.md`, `SHOGGOTH.md`, `.horos/boundary.json`,
  `.agents/skills/promise-machine/SKILL.md`, and `PROMISE_MACHINE.md`;
- `plugins/hexaemeron/AGENTS.md`, `plugins/hexaemeron/agents/surveyor.md`, and
  `plugins/hexaemeron/skills/fiat/SKILL.md`;
- the complete Protasis, Phylax, Ephoros, Metron, Elenchus, Hypomnema, and
  Imprimatur canonical skill contracts under `plugins/hexaemeron/skills/`; and
- `.python-version`, Git `HEAD`, local `main`, and `.hexaemeron/state.json` for
  the toolchain, ref, topic, and phase. The controller packet's declared state
  digest is retained by the coordinator; this worker did not receipt it.

### repository prior art and audit evidence

- `plugins/horos/skills/horos/SKILL.md`,
  `plugins/horos/skills/horos/EVOLUTION.md`, and
  `plugins/horos/docs/study.md`;
- `plugins/brevitas/skills/brevitas/SKILL.md` and its runtime contract;
- `docs/decisions/ADR-041-grade-router-selection-as-a-root-capability.md`,
  `docs/promise-machine/router-selection-v1.md`, and the router-selection
  prompt template and fixture corpus they name;
- `docs/protasis-audit-synopsis-read-view-study.md` and
  `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/study.md`;
- `audit/rounds/fiat-369-read-audit-synopsis-resigned.synopsis.md` and
  `audit/rounds/fiat-499-grade-router-selection-not-just-resolution.synopsis.md`;
- [pull request #780](https://github.com/wildcat-finance/skills/pull/780) and
  [pull request #697](https://github.com/wildcat-finance/skills/pull/697), with
  local merge commits `43f9ea57` and `e5131e9a`; and
- `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`,
  which exited 0 over the current whole-set audit source/view pairs.

### outside prior art

- [RFC 5234: Augmented BNF for Syntax Specifications](https://www.rfc-editor.org/rfc/rfc5234.html);
- [RFC 8785: JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785.html);
- [TOON Specification](https://github.com/toon-format/spec/blob/main/SPEC.md),
  inspected at its stated version 4.1 working-draft boundary;
- [LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models](https://aclanthology.org/2023.emnlp-main.825/)
  and the [Microsoft Research project page](https://www.microsoft.com/en-us/research/project/llmlingua/llmlingua/); and
- LongCodeZip, arXiv `2510.00446`, as identified and bounded by the repository's
  Horos study. This study did not obtain a separate authoritative copy, so it
  makes no claim beyond that local prior-art account.

### source limits

The public GitHub API returned HTTP 403 during the final metadata refresh, so
dates and full PR bodies were not re-fetched in that attempt. The issue and PR
content had already been read, and the merge ids were verified from local Git.
No source establishes the exact tokenizer profile, decoder-token accounting
convention for a particular model vendor, available second agent family, or
hidden system instructions. Those remain measurement-manifest unknowns rather
than inferred facts.

## 8. signals, and the questions behind them

This is a bounded local compiler and test harness, not a long-running service.
It needs no pager, uptime metric, trace backend, or production alert. CI sees a
non-zero exit and a bounded JSON report; a human reads the named case and
source path.

The useful questions and emitted signals are:

| question | signal | bounded fields |
| --- | --- | --- |
| did these exact bytes parse and validate? | one `validation.result` at command end | schema version, input digest, model digest, outcome, refusal code, stable node path |
| did formatting and decoding preserve the model? | one `roundtrip.result` per fixture | fixture id, model digest, compact digest, decoded digest, idempotent-format verdict |
| which source statement does a node claim to carry? | one `binding.result` per fixture | source path, blob digest, byte span, node ids, missing or overlapping span ids |
| did a hostile change disappear silently? | one `mutation.result` per mutation | fixture id, mutation id and class, expected structural or answer change, observed outcome |
| did original and compact inputs answer alike? | one `parity.result` per isolated case | family, model, context-manifest digest, question id, expected answer id, source answer id, compact answer id |
| what did the size claim count? | one `measurement.result` per corpus and tokenizer | all source, model, compact, bootstrap, one-document, amortised bytes and tokens plus tokenizer-profile digest |
| can another person reproduce the report? | one `run.summary` | tool commit, argv, Python version, manifest digest, environment facts, passed, failed, refused, unknown counts |

Events contain ids, digests, counts, verdicts, and bounded diagnostics. They do
not contain full source, compact input, prompts, model responses beyond the
closed answer id, credentials, or hidden reasoning. Correlation is the
measurement-manifest digest plus fixture, case, and mutation ids. A failure
prints the same ids to stderr and leaves the complete bounded report at the
explicit output path.

There is no counter whose movement alone warrants an alert. A non-zero exit is
the user-visible failure. Repeated `unknown` outcomes are not converted into a
pass; the runbook either supplies the missing tokenizer or agent-family
evidence or records that acceptance was not met.

## 9. boundaries, per capability

### source-to-model review

Trust crosses from authored Markdown into a human-reviewed instruction model.
The control is an exact Git blob digest, byte span, stable node id, reviewer
provenance, and closed parity corpus. This is the only non-mechanical boundary.
The tool does not infer prose meaning. Unsupported text refuses, and behavioural
parity can falsify the binding but cannot prove completeness.

### canonical model validation

Canonical JSON is untrusted input. The loader accepts one bounded regular
UTF-8 file, rejects BOMs, duplicate keys, floats, invalid scalars, unexpected
keys, unknown enums, excessive depth, length, members, nodes, relations, or
literal bytes, and validates all references before returning a model. It does
not follow symlinks or read includes.

### compact decode and format

Compact bytes are untrusted input. The decoder uses the same file and resource
limits, exact indentation, one grammar version, fixed opcodes, length-prefixed
literals, and closed escapes. It never recovers from malformed input, guesses
an opcode, skips a line, or executes a literal. The formatter accepts only a
validated model and writes through a confined temporary regular file followed
by atomic replace.

### source and output paths

Manifest paths are repository-relative, NFC-stable ASCII path strings without
empty, dot, dot-dot, control, bidirectional, or absolute components. Resolution
is confined beneath the selected root. Every input and output component is
checked with `lstat`; symlinks and special files refuse. The CLI does not delete
or overwrite an undeclared path.

### tokenizer adapter

The tokenizer is outside the standard-library trust base. The manifest must
name its semantic id, version, vocabulary digest, executable digest, exact argv
template, input encoding, and acquisition record. The runner passes an argv
list with no shell, a bounded exact UTF-8 input file, a cleared allowlist
environment, timeout, output cap, and closed integer-result schema. Unknown or
provider-reported counts without the declared local profile refuse. Adding or
vendoring the adapter asks first.

### model-family adapter

A model endpoint, runtime, and its output are untrusted. Only synthetic-public
fixture text may leave the process under an approved profile. Each request is
one fresh job with bounded bytes, tokens, time, retries, and output; no tools,
storage, uploads, remote URLs, conversation reuse, or background execution are
enabled. Credentials come from the approved host mechanism and never enter
argv, events, reports, fixtures, or Git. Responses are parsed into a closed
answer id or a bounded unknown/refusal record. Two aliases are not counted as
two families without distinct recorded backend identities.

### report and generated files

Reports and compact fixtures are derived, not authority. Their manifests bind
all input, bootstrap, context, question, mutation, tokenizer, and output
digests. Repository tests regenerate bytes in memory and compare exact output.
The root Promise Machine stays authored; installation copies continue through
the existing sync command. No compact form is installed into a runtime during
this prototype.

### operator and repository boundary

The operator chooses dependencies, credentialed providers, CI, public schema
release, source-authority reversal, scope expansion, and external migration.
The prototype may inspect and write only authorised paths in this repository.
It cannot close a GitHub issue, publish a PR, alter audit history, or touch the
Shoggoth repository by implication.

## 10. the budget, or its absence

The product budget is semantic and representational, not latency. Version 1
must preserve every declared model answer and must reduce tokens for the whole
three-fixture corpus after decoder overhead. The gate is intentionally a
strict delta rather than an invented percentage:

```text
compact_corpus_tokens + complete_decoder_bootstrap_tokens
    < source_corpus_tokens
```

The report also shows, without gating, canonical-model tokens, each individual
fixture delta, raw bytes, one-document cost, bootstrap cost, and amortised cost
for corpus sizes 1 through 3. It never calls bytes, words, Unicode code points,
provider estimates, or heuristic counts tokenizer output.

The exact tokenizer profile is not yet selected. A clean measurement requires
one real agent-model tokenizer whose id, version, vocabulary digest,
executable digest, argv, and input digests are recorded. Results from unlike
tokenizers are separate cohorts. If acquisition needs a dependency, licence,
network fetch, or paid service, the operator approves it before the runbook
step begins. Without that profile the report is byte-only and acceptance is
not met.

The repeatable Metron command is:

```bash
python3 scripts/agent_instruction.py measure \
  --manifest tests/fixtures/agent-instruction-v1/manifest.json \
  --output tmp/agent-instruction-v1-measurement.json
```

The manifest, not the shell environment, selects the exact source corpus,
compact corpus, bootstrap files, tokenizer profile, and model-run records. The
command refuses an unclean Git binding, changed input digest, missing bootstrap
file, missing tokenizer identity, parity failure, mutation failure, or
non-negative bootstrap-inclusive token delta.

There is no speed budget for the bounded prototype. The validator still has
hard resource caps so hostile input cannot turn that absence into unbounded
work. Any later claim about faster ingestion, lower model latency, memory, or
provider cost starts with a separate Metron baseline and measures the same
environment before and after.

## 11. the fail-closed posture

The compiler returns no model on malformed, oversized, unsupported,
non-canonical, cyclic, dangling, duplicate, or path-unsafe input. It returns no
equivalence verdict when source, model, compact, decoder, schema, question,
mutation, tokenizer, context, or report digests disagree. It returns no token
reduction verdict from a byte-only run, and no cross-family verdict from one
family or two undisclosed aliases.

The first failing check names one stable error code, fixture or path, and node,
case, or mutation id without echoing secret or unbounded content. Multi-fixture
commands still finish a bounded report of independent failures, but their
process result stays non-zero and no derived repository file is replaced. A
partial model, partial measurement, or majority of matching questions never
authorises use.

Each defect found during implementation or audit enters Elenchus before a fix:
preserve the exact failing bytes and environment facts, reproduce with the
smallest existing command, localise the first divergence, reduce to one
fixture, fix the cause, and add a guard that fails on the parent revision and
passes with the fix. The regression fixture keeps the stable risk id from
section 5 and the named error code.

Required guard families include:

- every grammar token, unknown version, duplicate key, non-canonical form,
  invalid UTF-8 scalar, literal delimiter, and resource cap at limit and
  limit-plus-one;
- missing, dangling, cyclic, cross-scope, and reordered relations;
- dropped negation, changed exception scope, weakened evidence class, changed
  authorisation or recovery, and each exact-literal class used by the corpus;
- contaminated batched contexts, missing prompt/context identities, unknown
  answer ids, alias-only family claims, and unavailable model runs;
- missing bootstrap bytes, mismatched tokenizer profiles, negative and
  non-integer token counts, and compact totals that fail after overhead; and
- stale source, model, compact, report, Promise Machine copy, and generated
  currency fixtures.

Recovery is to restore the exact bound source or manifest, fix the reviewed
model or codec, rerun the isolated guard, then rerun the whole corpus. Editing
a digest to agree, deleting a mutation, widening the accepted answer set after
seeing output, normalising a literal, or relabelling an unknown as a pass is
not recovery.

## 12. decisions and their homes

The following choices are expensive to reverse and need durable records:

| decision | home | why it belongs there |
| --- | --- | --- |
| use a closed instruction model and compact derived form while Markdown remains authored | `docs/decisions/ADR-051-encode-a-closed-agent-instruction-model.md` | it fixes the authority direction, semantic boundary, rejected alternatives, and reversal cost |
| define `wildcat-agent-instruction/v1`, its grammar, canonical model, decoder, formatter, limits, and compatibility rule | `docs/agent-instruction-language-v1.md` plus `schemas/agent-instruction-v1.schema.json` | consumers need one public versioned contract independent of implementation comments |
| make exact model equality the lossless promise and fresh-context questions falsification evidence only | the ADR, public contract, and root `PROMISE_MACHINE.md` promise | the boundary controls what passing tests may authorise |
| bind the three-fixture corpus, bootstrap, questions, mutations, tokenizer, and model contexts by digest | `tests/fixtures/agent-instruction-v1/manifest.json` and its schema | these are executable evidence inputs, not narrative decisions |
| keep the codec a root capability for the prototype | the ADR and `tests/promise_machine_coverage.json` | ownership affects routing and release; Horos and Brevitas must remain unchanged |
| keep tokenizer and model-family adapters outside the decoder trust base | the ADR, measurement-profile schema, and runbook entry gates | dependency, provider, licence, privacy, and repeatability choices stay explicit |
| refuse authored-source reversal, wider conversion, a new plugin, and Shoggoth migration in issue #909 | the ADR consequences and this run's committed study | later work must not treat a prototype result as migration authority |

Implementation comments should explain only local parser invariants that code
cannot state, such as why a byte length is checked before decoding or why map
keys and ordered directives differ. They must not restate the public grammar.
The CLI help points to `docs/agent-instruction-language-v1.md`; any future CI
alert points to a short runbook section in that document naming the failing
command, evidence, and recovery.

The committed study and runbook copies live under
`docs/compact-agent-instruction-language/`. The first implementation step
copies these receipted artefacts before code changes. The root Promise Machine
adds one promise for structural validation and measurement evidence, and the
coverage registry binds its checker, corpus, report, and hostile fixtures.
Generated plugin-local Promise Machine copies continue to be produced by the
existing sync mechanism.

No `EVOLUTION.md` changes in the prototype. There is no existing canonical
skill whose frontier this work closes. If the evidence later supports a new
plugin or a Horos integration, Protasis studies that separately, names the
owner, and records the migration and compatibility decision before any source
of authority moves.
