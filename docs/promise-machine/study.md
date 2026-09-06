# Study: establish the Promise Machine

## Assumptions

Assuming, unless corrected:

1. The implementation run targets `wildcat-finance/skills` from `main` commit
   `d577b88`, the merge of the reviewed study and runbook. The
   tracked tree is clean and matches `origin/main`; the only untracked paths
   are this provisional study and runbook.
2. The repository and suite retain the public name **Wildcat Labs Skills**. In
   the root README, `# Wildcat Labs Skills` remains the document title and
   `## The Promise Machine` immediately follows as the architectural heading.
   The Promise Machine is the governing architecture of the suite, not a
   replacement repository name, a new controller or a renamed Hexaemeron.
3. The contract applies to every skill shipped from this repository, including
   first-party, nested and vendored skills. Evolution ownership and Promise
   Machine coverage are separate classifications.
4. Vendored instructions stay byte-for-byte unmodified. First-party overlays
   bind their promise, evidence boundary and upstream digest.
5. A governed first-party logical skill has one canonical implementation and
   one authoritative skill version. A vendored skill instead has one canonical
   implementation and one authoritative provenance digest; this delivery must
   not invent Wildcat evolution versions for upstream instructions.
6. Routers and invocation aliases may select a canonical skill but carry no
   independent behavioural version and may not broaden its promise.
7. Plugin-package versions and skill versions remain distinct. Package versions
   determine what hosts install; skill versions identify behavioural contracts.
8. Supported discovery surfaces are Codex plugins, Claude Code plugins and the
   host-neutral Agent Skills convention. Unsupported personal or third-party
   skills are outside scope.
9. With a Wildcat marketplace plugin installed while this repository is open,
   Codex must not present a workspace router as a second implementation of the
   same logical skill.
10. The shared law scales evidence to the consequence of a claim or transition.
    It does not make every skill adopt Fiat, receipts or hash-chained state.
11. The implementation uses Markdown and Python 3 standard-library checks. No
    Solidity change is expected. Janus's existing Foundry suite still runs as
    conformance evidence; if closing a discovered gap requires changing Janus
    Solidity, this study is amended before that work and Fiat may not waive the
    Solidity audit.
12. Existing tests count as behavioural conformance where they actually
    exercise a promise boundary. New fixtures fill material gaps; they do not
    duplicate adequate evidence.
13. `PROMISE_MACHINE.md` is the one authored normative source. Standalone
    plugin installation requires local copies; those copies are generated and
    checked byte-for-byte rather than edited.
14. Completeness outranks brevity in this study and runbook.
15. Fiat does not start from a red affected-plugin baseline. At the original
    study ref `2b4d96f`, Berean's shipped corpus files were absent and its suite
    was red. PR #282 repaired that pre-existing defect through Elenchus and
    merged as `9c7692d`; that green descendant is the Step 1 entry ref. PR #283
    then committed the study and runbook as `d577b88`, the Fiat implementation
    run base.

Corrections to the intake's historical observations:

- The current tree contains 14 plugin directories and 14 Claude marketplace
  entries. The Codex marketplace exposes 13 and still omits Horos despite
  Horos carrying a Codex manifest.
- The current inventory contains 28 canonical skills: 23 governed first-party
  skills and 5 vendored skills. It has 20 portable entrypoints and 18 exact
  canonical-name overlaps.
- Berean and Janus are first-party canonical skills at `berean-v0.1.0` and
  `janus-v0.1.0`. Their plugin packages are both `0.1.0`.
- Canonical Protasis is now `protasis-v2.2.0`; Fiat is `fiat-v4.8.1`; Horos is
  `horos-v9.3.3`; Hexaemeron remains package `1.5.0`. Portable files are
  unversioned routers.
- The current canonical Protasis checklist has 14 checks and now requires the
  last two merged pull requests touching the target to be read and their
  unfinished work to be carried forward, refused or left visibly open.

## 1. Problem statement

The suite already contains narrow claims, fail-closed checks, evidence classes,
explicit handoffs and recovery paths. Those properties are local conventions.
Nothing currently requires every new skill to state the claim it can establish,
the evidence that supports it, the conclusions it refuses, or the transition a
passing result permits. Nothing discovers the full skill universe and rejects a
new ungoverned promise. The portable layer also exposes logical skills beside
installed canonical copies, which lets one operation appear twice and drift.

Berean and Janus make the missing suite law more concrete. Berean can verify a
recorded answer against pinned document bytes, block-bound reads and evaluation
records, yet it must not turn a recorded RPC response, an exact citation or a
promotion record into truth. Janus can show that observed hook effects stayed
inside a manifest for one host adapter and one bounded search, yet it must not
turn that result into hook safety, liveness proof or cross-host conformance.
The Promise Machine must preserve both boundaries when those skills compose
with Lemma, Lazarus, Ariadne, Pandects, Fizz or Fiat.

This delivery establishes the Promise Machine as repository law:

> No skill may claim more than its evidence establishes, or authorise a more
> consequential transition than that evidence warrants.

Expanded:

> Every skill must state the claim it can establish, the evidence and scope
> supporting that claim, what the claim does not establish, and the transition,
> if any, the claim permits. Missing, stale, conflicting or out-of-scope evidence
> remains visible. Failure blocks only the dependent transition; inspection,
> diagnosis, repair, rollback and safe exit remain available. An exception is
> explicit, attributable, scoped, recorded and, where relevant, expiring.

The same delivery establishes one canonical identity for every logical skill.
The portable layer becomes one suite router rather than a second catalogue of
apparently independent implementations.

### Working prototype

A working prototype has all of these properties:

- a canonical, installable Promise Machine contract and controlled evidence
  vocabulary;
- a filesystem-discovered inventory covering all 28 current canonical skills,
  all 14 plugins, all nested skills, all supported host surfaces and the five
  vendored overlays;
- agent-visible domain promises with deterministic structural checks;
- a coverage inventory tying every promise to positive, negative, overclaim,
  recovery and exception evidence, or a reason a category does not apply;
- one canonical implementation and version or provenance identity per logical
  skill, with no independently versioned router;
- composition checks that preserve Berean's source and time-domain classes and
  Janus's adapter, delta-capture and bounded-search scope across handoffs;
- plugin-local bindings that survive installation without reaching outside the
  copied plugin directory;
- a Codex demonstration showing one authoritative Protasis while the repository
  is open and the marketplace plugin is installed;
- green root and affected-plugin suites, tree checks and prose checks.

### Demo path

```bash
python3 scripts/promise_machine.py inventory --check
python3 scripts/promise_machine.py check
python3 -m unittest tests.test_promise_machine_contract
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

The deterministic proxy is followed by the named Codex, Claude and host-neutral
manual demonstrations in the runbook's last step. The proxy does not claim to
prove UI behaviour.

## 2. Prior art and current inventory

### The original Promise Machine

The credit-system draft turns a promise into a narrow predicate governing a
specific increase in exposure. A failed condition blocks the dependent draw,
while debt, repayment, exit and cure survive. It repeatedly warns that a claim
truthful within one facility or watched set becomes false when promoted into a
borrower-wide conclusion, and that attestation does not make an off-chain fact
true. The suite generalises that shape:

```text
promise -> scoped predicate -> evidence -> authorised transition
                    \-> failure -> contained refusal + recovery
```

Hexaemeron controls delivery. Ariadne binds evidence. Every other skill
establishes its own narrow predicate. The Promise Machine is the contract that
holds the suite to what those predicates can establish.

### Repository mechanisms to extend

- `tests/test_portable_skills.py` checks portable names, links and current
  canonical routing, but deliberately accepts the duplicate catalogue.
- `tests/test_evolution_contract.py` now discovers 23 governed skills and
  excludes the five vendored skills only from Wildcat evolution ledgers.
- `tests/test_version_propagation.py` correctly separates plugin versions from
  skill versions and checks each version within its own layer.
- `tests/test_marketplace_prose.py` reconciles the 14 Claude marketplace
  plugins and public frontier prose.
- `tests/test_boundary_currency.py` now makes the Horos reading boundary fail
  when the committed classification and tracked tree drift.
- Plugin-local suites already contain many missing-evidence, mismatch,
  overclaim and recovery specimens.
- Hexaemeron's checkers already use standard-library CLIs, coded findings,
  machine-readable output and fail-closed empty-set handling.
- `plugins/hexaemeron/skills/VERSIONING.md` says prose-only clarification does
  not move a skill version, a behavioural non-frontier change moves generation,
  and an ownership or compatibility break moves epoch.

At the original study ref, the root suite was green: 38 tests passed under
Python 3.14.6. Janus was also green: 14 Python tests and 24 Foundry tests
passed. Berean was not: its 150-test suite reported 18 failures and 15 errors
because both the shipped reference release and passing conformance fixture
lacked their pinned corpus files. Root `.gitignore` line 18 ignored
`**/corpus/`; `git check-ignore` attributed the absent
`release/corpus/*.md` and
`fixtures/conformance/pass-release/corpus/terms.md` paths to that rule. The
manifests and deterministic rebuilders existed, but a manifest was not a
substitute for its pinned bytes.

PR #282 preserved that diagnosis, restored the deterministic corpus bytes,
unignored Berean corpora without widening the rule for fuzzer output and added
a packaging regression test. At green baseline ref `9c7692d`, the root suite passes
38 tests, Berean passes its complete 151-test suite and offline demonstration,
and Janus passes 14 Python tests and 24 Foundry tests. The historical failure
remains evidence for the Promise Machine design; it is no longer an entry
blocker.

### The two new Commons skills

Berean's five closed document formats separate corpus identity, answer claims,
evaluation cases, release identity and promotion history. Its verifier
re-slices citations from pinned bytes, recomputes read request keys, keeps
document and chain time domains visible, refuses unpinned evaluation and never
runs a model or retrieves documents. Its `berean-v0.1.0` frontier is deliberately
open: the shipped Aave v4 release uses a fabricated frozen corpus and recorded
mainnet reads; a Wildcat corpus, captured Wildcat market reads and an Ariadne
grounded-agent statement remain future work. The Promise Machine may govern
those future claims, but this delivery must not consume that held frontier.

Janus's manifest, state-delta recorder and Foundry harness constrain hook
effects at host thresholds. Its seven gates cover enumerated effects, value
conservation, bounded exit-liveness search, rollback, gas grief, cross-action
re-entry and adapter scope. Its `janus-v0.1.0` frontier is also open: the Wildcat
v2.5 adapter exists, while a second callback model is held to show that the
format is host-neutral. Two accepted limitations from PR #279 remain visible:
the current manifest cannot constrain the value-returning hook's in-bounds
return and does not express per-action gas coverage. This delivery records those
unknowns and may not repair them under the name of Promise Machine conformance.

### Merged-delivery carry-forward

The relevant merged deliveries were read before this rewrite:

- PR #270 delivered Berean with 150 plugin tests and an offline reference demo.
  Its body reported them green and left the Wildcat-grounded release to
  Berean's held frontier rather than claiming it was complete. The original
  study checkout exposed that its ignored corpus bytes had never shipped.
- PR #279 delivered Janus in six reviewed steps. Its body records the two
  accepted manifest limitations above and holds a second host adapter as the
  next frontier.
- PR #281 repaired the marketplace mirror after Janus added a workflow. Its
  body carries stale mirror branches, missing Horos CI and token expiry. Those
  are operational work outside this delivery; the supported-host demonstration
  records mirror and package currency but does not close those issues.
- PR #282 repaired Berean's corpus packaging, added the 151st plugin test and
  restored its offline demonstration. The repair closes only the packaging
  blocker; it does not complete Berean's Wildcat-grounded release frontier.
- PR #283 committed this study and runbook without implementing the remaining
  nine steps. Its merge commit `d577b88` is the implementation run base.

### Filesystem-derived inventory

| Surface | Current result | Evidence source | Promise Machine use |
| --- | --- | --- | --- |
| Plugin directories | 14 | `plugins/*/` | Plugin universe boundary |
| Claude marketplace entries | 14 | `.claude-plugin/marketplace.json` | Claude install exposure |
| Codex marketplace entries | 13; Horos absent | `.agents/plugins/marketplace.json` | Codex install exposure |
| Canonical `SKILL.md` files | 28 | `plugins/*/skills/**/SKILL.md` | Behavioural owners |
| Governed first-party skills | 23 | Canonical skills minus declared vendored ownership | Versioned contracts |
| Vendored skills | 5: Fizz, Fizz Convert, Fizz Sync, X-Ray, Solidity Auditor | Ownership and provenance declarations | Digest-bound upstream contracts |
| Portable entrypoints | 20 | `.agents/skills/*/SKILL.md` | Host-neutral routes |
| Exact portable/canonical name overlaps | 18 | Portable and canonical name comparison | Duplicate-discovery risk |
| Installed Wildcat Codex plugins | Not authoritative | Local installation state | Demonstration evidence only |

The 20 portable entries are the 14 plugin-facing routers plus six Hexaemeron
phase routers. `hexaemeron` and `lemma` do not exactly match canonical skill
names because they route to several Hexaemeron skills and to `chunk`
respectively. They remain competing user-visible routes, even when a string
equality test does not call them collisions.

Every plugin changes because it receives an install-local law copy and runtime
binding. The package-version entry values and proposed publication targets are:

| Plugin | Entry package | Delivery package |
| --- | --- | --- |
| Alexandria | `0.2.0` | `0.2.1` |
| Ariadne | `1.2.0` | `1.2.1` |
| Berean | `0.1.0` | `0.1.1` |
| Brevitas | `0.2.0` | `0.2.1` |
| Hermes | `0.1.0` | `0.1.1` |
| Hexaemeron | `1.5.0` | `1.5.1` |
| Horos | `0.1.0` | `0.1.1` |
| Janus | `0.1.0` | `0.1.1` |
| Lazarus | `1.1.0` | `1.1.1` |
| Lemma | `0.1.0` | `0.1.1` |
| Pandects | `0.1.0` | `0.1.1` |
| Probitas | `0.1.0` | `0.1.1` |
| Sapheneia | `0.1.0` | `0.1.1` |
| Tabularium | `0.3.0` | `0.3.1` |

These are package cache identities, not new skill frontier versions. A
canonical skill generation moves only if implementation shows that the new
contract changes its behaviour rather than exposing an already enforced
boundary. The Promise Machine law itself has one format/version identifier and
one root digest; every plugin copy must report both identically.

### Host behaviour

- OpenAI documents repository and personal plugin marketplaces separately and
  says installed plugins load from a versioned cache. It documents no rule by
  which a workspace Agent Skill router should deduplicate an installed plugin
  skill. The current Codex session and the supplied screenshot show both.
- Claude Code namespaces plugin skills as `plugin-name:skill-name`, so plugin
  skills do not collide with project or personal skill names. Claude copies a
  plugin into a versioned cache and skips updates when an explicit package
  version did not change.
- The Agent Skills specification requires one named `SKILL.md` per discovered
  directory but defines neither cross-source precedence nor alias identity.

The design therefore cannot rely on host deduplication or on byte equality
between two discovered entries.

## 3. Constraints and non-goals

### Constraints

- Historical study ref: `2b4d96f` on `main`. Green Step 1 entry ref:
  `9c7692d`, the merged PR #282 descendant that repairs Berean's ignored corpus
  packaging and passes the root, Berean, Janus Python and Janus Foundry
  baselines. Fiat implementation run base: `d577b88`, the merged PR #283
  descendant containing the reviewed study and runbook.
- Standard-library Python only; adding a dependency is ask-first and unnecessary.
- Discover canonical and nested skills from the filesystem. A hand-maintained
  list may classify evidence. It must not define the universe it claims to cover.
- Preserve the current narrow marketplace boundaries. A Promise Machine
  declaration may expose an existing boundary. It must not silently widen it.
- Keep vendored instructions unmodified and bind overlays to exact paths and
  digests.
- Keep the full law in one authored file. Repeated plugin copies are generated
  because hosts install plugin directories in isolation.
- Keep descriptions and manifest summaries focused on selection. The suite
  name belongs in public identity, policy and conformance output, not every
  trigger string. The root README preserves this exact opening and order:

  ```markdown
  # Wildcat Labs Skills

  ## The Promise Machine
  ```
- A claim or authorised transition owns its consequence level. A whole skill
  does not receive one permanent level.
- Existing durable records gain new fields only when their current transition
  cannot be inspected from existing evidence. No universal receipt format.
- Every step begins and ends green and is one reviewable pull request.

### Non-goals

- Proving arbitrary model output or declaring the suite correct or safe.
- Replacing Ariadne's evidence-binding role or Fiat's delivery controller.
- Forcing prompt-only skills to offer deterministic guarantees they cannot make.
- Governing personal or third-party skills outside this repository.
- Replacing plugin-package versions with skill versions.
- Standardising every output into one receipt schema.
- Editing vendored instructions.
- Solving discovery for undocumented hosts.
- Advancing a held frontier merely because Fiat delivers this repository change.

## 4. Design options

### Option A: Markdown declarations and a structural parser

Each canonical `SKILL.md` carries a fixed Promise Machine section. A root
checker parses required fields, paths and versions.

Trade: the contract is visible where an agent works and is cheap to understand,
but Markdown structure alone proves no behaviour and plugin-local law can drift.

### Option B: machine-readable promise records rendered into instructions

JSON or YAML is canonical; generation writes the Markdown agents read.

Trade: validation and inventory are precise, but the behavioural instruction is
no longer the authored source. Generation failure can leave an agent reading a
stale promise, and every contributor must understand two representations.

### Option C: authored Markdown promises, checked coverage records and exact
plugin-local copies

`PROMISE_MACHINE.md` is canonical. Every first-party `SKILL.md` authors its
domain promise in a standard parseable section. A machine-readable coverage
inventory points to behavioural evidence. Each plugin receives an exact
generated copy of the root law, and a drift check rejects any difference.
Vendored promises live in a first-party Hexaemeron overlay bound to upstream
digests.

The 20 portable entries become one `promise-machine` suite router. It owns only
selection: it loads root policy, selects the plugin runtime contract and then
loads exactly one canonical skill. It has no behavioural version.

Trade: a host-neutral user loses direct auto-selection of 20 narrow portable
entries and must name the suite or read root `AGENTS.md`. In return, the same
workspace no longer advertises a second Protasis, Alexandria or other logical
operation beside the installed canonical plugin.

### Option D: retain every router and declare source precedence

Keep the 18 entrypoints, generate them from canonical definitions and tell each
host which source wins.

Trade: this preserves direct discovery but depends on precedence that Codex and
the Agent Skills specification do not document. It also leaves two visible
entries in the demonstrated Codex surface. Rejected.

### Chosen design

Choose Option C. It is the least complicated construction that satisfies both
agent visibility and deterministic enforcement. Markdown remains the authority
agents read; structured data records only conformance evidence; exact copies
exist solely at installation boundaries; and one suite router preserves
host-neutral reach without creating 20 competing identities.

Berean and Janus do not receive a special universal schema. Their existing
domain formats remain authoritative: Berean owns answer and release evidence;
Janus owns hook manifests and observed deltas. The Promise Machine declaration
names what each format can establish and the coverage record points to the
existing gates. This keeps the shared law small and prevents a generic receipt
from erasing the distinctions that make either skill useful.

Horos joins the Codex marketplace because it already ships a Codex manifest and
is part of the Promise Machine. If a host exclusion is intended instead, it must
be recorded with a reason and the manifest removed; the current half-exposure is
not an identity model.

## 5. Risk register seed

| Risk | Mechanism | Treatment |
| --- | --- | --- |
| Decorative compliance | Seven bullets exist without behavioural effect | Coverage inventory and domain-native negative evidence |
| Claim laundering | A receipt, digest or attestation is promoted into proof of its contents | Controlled evidence classes and explicit boundaries |
| Empty-set success | Discovery finds no skills or no promises and reports clean | Minimum counts plus mutation fixtures |
| Path escape | Discovery or copy generation follows links outside the repository | Resolve roots, reject symlinks and parent escape |
| Gate contagion | Local refusals compose into a global halt | Recovery and composition invariants; skill-specific tests |
| Exception laundering | One waiver disables adjacent promises | Promise-local authority, scope, record and expiry |
| Stale success | Old evidence authorises a changed subject | Subject identity and freshness where material |
| Version drift | Package, canonical skill, router and cache move independently | Layer-specific checks and one canonical identity |
| Discovery duplication | Installed and workspace sources expose the same operation | One suite router and a named UI demonstration |
| Lost portability | Removing narrow routers hides capabilities | Suite router plus root/plugin selection tables |
| Vendored drift | An upstream change invalidates an overlay | Overlay path and SHA-256 binding |
| Prompt inflation | Repeated law consumes every skill context | Root law, exact install copy, concise domain declarations |
| Taxonomy abuse | Evidence labels are read as a prestige ranking | Define each by relation; forbid silent class promotion |
| Public contradiction | Browsing prose promises more than canonical instructions | Extend marketplace-prose checks |
| Release staleness | Explicit package versions prevent changed plugins updating | Bump every changed plugin package and verify all manifests |
| False UI proof | A file-level proxy is reported as a user-interface result | Separate deterministic proxy and manual demonstration receipts |
| Self-certification | The suite declares compliance from its own prose | Inspectable fixtures, exact commands and external host observations |
| Evidence-chain promotion | A Berean citation, recorded read, passing evaluation or Ariadne statement is treated as truth of an answer | Preserve source class at each handoff; test nearby overclaims and conflicting time domains |
| Promotion-as-truth | A Berean promotion record is read as factual approval rather than evidence that declared thresholds passed | Bind the record to release, corpus, report and threshold digests; refuse semantic promotion |
| Incomplete-delta pass | Janus reports conformance while a write, call, value movement or gas effect was not captured | Unknown effects fail closed; coverage cites recorder and hostile-hook guards |
| Cross-host laundering | A Wildcat adapter result is presented as general hook safety or another host's conformance | Adapter identity and bounded search belong to every Janus claim and report |
| Composition erasure | A handoff from Lemma, Lazarus, Berean, Janus, Pandects or Ariadne drops the producer's evidence boundary | Cross-skill invariants and mutation fixtures preserve relation, subject and refused overclaim |
| Manifest without bytes | Berean's release manifest is mistaken for a self-contained corpus while ignored pinned files are absent | A green entry suite is mandatory; require every manifest path to exist and match before Fiat starts |

## 6. Glossary and normative vocabulary

- **The Promise Machine.** The suite-wide governing architecture under the
  public **Wildcat Labs Skills** identity.
- **Promise Machine contract.** The universal law and its conformance rules.
- **Promise Machine contract version.** The shared law-format identity,
  initially `promise-machine/v1`; it is neither a plugin package version nor a
  canonical skill frontier version.
- **Promise.** A bounded claim made by one skill operation.
- **Promise boundary.** Its subject, scope and nearby conclusions it does not
  support.
- **Promise check.** Evidence evaluated to decide whether the promise holds.
- **Authorised transition.** The representation or action a satisfied promise
  permits.
- **Refusal.** The contained transition denied when a promise is unsatisfied.
- **Recovery.** Inspection, cure, rerun, rollback or safe exit left available.
- **Exception.** An attributed, scoped and recorded decision to waive or narrow
  one gate.
- **Logical skill.** One user-recognisable operation with one canonical
  implementation, regardless of invocation syntax.
- **Router.** An unversioned selection surface that loads a canonical skill and
  establishes no domain result.
- **Package version.** The cache and distribution identity of a plugin bundle.
- **Skill version.** The evolution identity of one governed behavioural contract.
- **Evidence inheritance.** A consumer may narrow or add evidence. It must not
  silently strengthen the class, subject, scope or freshness received from a
  producer.
- **Bounded conformance.** A result that observed behaviour stayed within a
  declared boundary for the named adapter, recorder and search; not a safety
  proof or a claim about unobserved executions.

### Evidence classes

| Class | Meaning | Minimum binding | Nearest refusal |
| --- | --- | --- | --- |
| `checked` | Evaluated against an identified deterministic rule or schema | Rule or schema identity and result | Truth or completeness outside the rule |
| `recomputed` | Derived again from identified authoritative inputs | Inputs, method and result | Authority beyond those inputs and method |
| `proved` | Checked against a named formal, cryptographic or explicitly defined proof relation | Proof relation and subject | Claims outside that relation |
| `measured` | Observed under a recorded method and environment | Method, environment and observation | Universal performance or causation |
| `recorded` | Preserved from a source without independently proving its assertion | Source, time and preserved bytes | Truth of the source assertion |
| `attested` | Asserted by an identified actor or system | Actor or system and exact statement | Independent truth of the statement |
| `inferred` | Reasoned from evidence but not directly established | Evidence, rule and derivation | Direct observation or proof |
| `unknown` | Not established | Explicit scope or question | Any positive transition |

`checked` is added to the intake vocabulary because schema validation and a
passing deterministic test are neither proof nor recomputation. The classes are
relations, not a universal strength ordering. A declaration may add a
domain-specific relation after the base class, such as `proved: EIP-1186
account proof`, but the base class must remain recognisable.

### Consequence levels

| Level | Transition | Minimum enforcement |
| --- | --- | --- |
| 0 | Response or presentation only | Preserve scope, content and uncertainty |
| 1 | Derived artefact | Validate structure, provenance and visible gaps |
| 2 | Repository or durable-data mutation | Tests, negative evidence and recoverable change |
| 3 | Publication, deployment, external action, security or financial conclusion | Fail-closed gate, recorded authority and independently inspectable evidence |

The level belongs to a promise's authorised transition. A skill may have more
than one promise when its operations cross levels.

### Per-promise declaration

Each first-party canonical skill carries exactly one `## Promise Machine
contract` section and one or more stable `### <promise-id>` blocks. Each block
contains:

- `Promise`
- `Evidence`
- `Evidence classes`
- `Boundary`
- `Authorises`
- `Consequence`
- `Refuses`
- `Recovery`
- `Exceptions`

`Exceptions: none` is explicit. A supported exception names authority, scope,
record and expiry or explains why expiry cannot apply. Operations with different
claims receive several promise ids rather than one vague skill
paragraph.

### Composition invariants

Generic checks enforce that missing is not passing, routers do not broaden a
canonical promise, exceptions do not cross promise ids, refusals name recovery,
and level-3 transitions name inspectable evidence and authority.

Skill-specific tests own semantic composition: monotonic credit gates, safe
repayment and exit, evidence freshness, no global halt from local uncertainty,
and the actual availability of a recovery action. The root checker must not
pretend Markdown proves those properties.

The initial cross-skill invariants are explicit:

- Lemma chunks remain source-linked retrieval material when Berean consumes
  them; validation of chunks does not establish the truth of an answer.
- Lazarus read records keep their original evidence class inside Berean. A
  recorded RPC response does not become proof-backed merely because a request
  key, citation or release digest matches.
- Berean evaluation and promotion establish that recorded answers passed named
  release gates and thresholds. Ariadne may bind the release digest to those
  records but does not establish the answer's factual truth or model quality.
- Janus conformance stays bound to the named host adapter, manifest revision,
  recorder coverage and bounded search. Fizz can widen search; Pandects can
  supply economic laws. Neither permits Janus to claim complete safety.
- An Ariadne statement over a Janus manifest or report establishes the evidence
  binding it declares, not cross-host validity, exit proof or absence of
  unobserved effects.

## 7. Sources

- `/Users/c0rtexzer0/Documents/For-The-Bit/tpm-yap.md`
- `/Users/c0rtexzer0/Documents/For-The-Bit/the-promise-machine-unveiling.md`
- [The Promise Machine informal draft](https://hackmd.io/@wildcatlabs/the-promise-machine-informal-draft)
- `README.md`, `AGENTS.md`, `.horos/boundary.json`
- `.agents/skills/*/SKILL.md`
- `.agents/plugins/marketplace.json`, `.claude-plugin/marketplace.json`
- `plugins/*/.{claude,codex}-plugin/plugin.json`
- every `plugins/*/AGENTS.md` that exists and every canonical or nested
  `plugins/*/skills/**/SKILL.md`
- every governed `EVOLUTION.md` and
  `plugins/hexaemeron/skills/VERSIONING.md`
- `tests/test_portable_skills.py`, `tests/test_evolution_contract.py`,
  `tests/test_version_propagation.py`, `tests/test_marketplace_prose.py`
- plugin-local behavioural suites and Hexaemeron's checker suites
- `plugins/hexaemeron/skills/fiat/references/plugin-currency.md`
- `plugins/berean/AGENTS.md`, `plugins/berean/skills/berean/{SKILL,EVOLUTION}.md`,
  `plugins/berean/docs/design.md`, and Berean PR #270
- `plugins/janus/AGENTS.md`, `plugins/janus/skills/janus/{SKILL,EVOLUTION}.md`,
  `.github/workflows/janus.yml`, and Janus PR #279
- marketplace mirror PR #281 and its carried-forward operational work
- [OpenAI: package a plugin](https://developers.openai.com/plugins/build/plugins)
- [OpenAI: build skills](https://developers.openai.com/plugins/build/skills)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Agent Skills specification](https://agentskills.io/specification)
- Git history through `d577b88`, including the Berean and Janus delivery stacks,
  the Horos reading-boundary work and the version-propagation, plugin-currency
  and marketplace-mirror changes, plus Berean repair PR #282.

## 8. Ephoros: signals and the questions behind them

No runtime telemetry service is introduced. The checker is a terminal and CI
command, so it has no three-in-the-morning operator. It must still answer four
post-run questions through stable text and JSON output:

1. Which discovered skill, router, overlay or copy failed?
2. Which promise id and field failed?
3. Was the fault structural, behavioural-coverage, identity, version or drift?
4. Which path or command clears it?

For cross-skill breaches, the report also names the producing skill, consuming
skill and the class, subject or scope that changed. That is structured
diagnostic output, not a new telemetry service.

The final Fiat run records checker exits and manual demonstration results in its
existing receipts. No metrics, traces or alerts are added.

## 9. Phylax: boundaries per capability

| Boundary | Worth taking | Control |
| --- | --- | --- |
| Filesystem discovery | Escape the repository, follow a symlink, or pass on an empty universe | Resolve beneath root, reject symlinked contract paths, assert expected non-zero classes |
| Markdown parsing | Hide duplicate fields, malformed blocks or huge input | Bounded reads, linear scans, duplicate rejection, explicit parser errors |
| Generated copies | Overwrite an authored file or install stale law | Fixed destinations, atomic writes, generated marker, byte equality check |
| Coverage paths and selectors | Cite evidence that does not exist | Confined relative paths and selector existence checks |
| Domain evidence handoffs | Upgrade Berean source/read classes or drop Janus adapter/recorder scope | Parse only declared metadata, preserve producer identity and reject an unexplained strengthening |
| Git and host state | Mistake a cache or dirty tree for canonical source | Repository is authority; cache only supplies demonstration evidence |
| Manual UI evidence | Treat a screenshot or operator statement as deterministic proof | Record it as observed evidence beside the deterministic proxy |
| No network in checker | none | Closed by construction; documentation research is not runtime behaviour |
| No subprocess in checker | Command injection | Checker does not execute evidence selectors; tests run them separately |
| No secrets | none | No credential input or persistence |

## 10. Metron: budget

The root structural check must finish within 5 seconds over the current tracked
tree on the entry machine, measured by:

```bash
/usr/bin/time -p python3 scripts/promise_machine.py check
```

The check reads instruction and metadata files, not fixtures, object stores or
build outputs. Five seconds is a regression ceiling, not a performance claim
about every plugin suite. If the baseline already exceeds it, record the
measurement and revise this study before implementation rather than weakening
the gate in code.

## 11. Elenchus: fail-closed posture

These conditions stop the dependent step:

- no discovered canonical skills, routers or plugins;
- an unclassified skill or unsupported evidence class;
- a missing declaration, overlay, generated copy or behavioural-coverage row;
- an unresolved or multi-target router;
- a duplicate canonical logical identity;
- a package/skill version conflation;
- a consequential promise with no refusal or recovery;
- an exception without authority and record;
- a stale or divergent copied law;
- a failed root or affected-plugin suite;
- the pre-existing Berean corpus-packaging failure at the entry ref;
- a manual demonstration reported without its record.
- a Berean handoff that upgrades a source/read class, hides a time-domain
  disagreement or treats promotion as answer truth;
- a Janus claim with incomplete delta capture, no adapter identity or a safety,
  proof-of-liveness or cross-host conclusion.

Every checker defect lands with a regression test that fails without the fix.
Failure leaves inventory, diagnostics, source files, repair, rerun and rollback
available. The checker never deletes, rewrites or quarantines a failing skill.

## 12. Hypomnema: decisions and their homes

| Decision | Why expensive to reverse | Home |
| --- | --- | --- |
| The Promise Machine's governing semantics | Every skill declaration and gate depends on it | `PROMISE_MACHINE.md` |
| Markdown as authored promise source | Moving authority later changes contributor workflow | `PROMISE_MACHINE.md` and this study |
| Exact generated plugin-local copies | Standalone installation cannot reach the root | generator module documentation and root decision record |
| One suite-level portable router | Changes host-neutral discovery and removes duplicate UI identities | root `AGENTS.md`, router, and `docs/decisions/` record |
| Evidence vocabulary and consequence levels | Tests and durable records cite the labels | `PROMISE_MACHINE.md` |
| Vendored overlay ownership | Upstream files must stay unmodified | `plugins/hexaemeron/PROMISES.md` and a decision record |
| Package/skill version separation | Release and behaviour lineage use different axes | existing `VERSIONING.md`, extended by a decision record |
| Cross-skill evidence inheritance | Berean and Janus expose how easily a consumer can launder a producer's narrow result | `PROMISE_MACHINE.md` and a composition decision record |

The implementation writes decision records for the portable-router change and
vendored-overlay boundary. The normative document holds the law; records hold
why these constructions were chosen.

## Boundaries

**Always.** Derive the inventory from disk; keep missing and unknown evidence
visible; preserve standalone plugin operation; reuse adequate tests; keep public
prose consistent; run every suite covering changed areas; bump every changed
explicitly versioned plugin package; commit this study and runbook before code.
For Berean, preserve source classes, read classes, time domains and append-only
promotion history. For Janus, preserve adapter identity, complete-delta refusal,
bounded-search scope and hostile-hook ownership.

**Ask first.** Add a dependency; expand beyond repository-shipped skills;
change existing version-axis meanings; rename a canonical or plugin-qualified
skill; introduce a generated file as an authored source; touch CI beyond
registering the new checks; retain a host exclusion not already justified by
repository evidence.

**Never.** Edit vendored instructions; treat an evolution exemption as a
Promise Machine exemption; claim a receipt proves its assertion; treat missing
evidence as success; force every skill through Hexaemeron; copy the law by hand;
use an installed cache as repository authority; report a UI result from the
file proxy; move a held frontier to make this delivery look evolutionary; run a
model or retrieve documents through Berean; claim Janus proves hook safety or
another host's boundary.

## Appendix A: canonical representation and file topology

```text
PROMISE_MACHINE.md                         authored normative law
scripts/promise_machine.py                 inventory, check, sync and JSON report
tests/test_promise_machine_contract.py     structural and mutation tests
tests/promise_machine_coverage.json        promise-to-evidence classification
tests/fixtures/promise-machine/            deliberately broken minimal universes
plugins/<plugin>/PROMISE_MACHINE.md         generated exact install-local copy
plugins/<plugin>/AGENTS.md                 local binding to the copied law
plugins/hexaemeron/PROMISES.md              five vendored overlays
plugins/*/skills/**/SKILL.md                first-party domain declarations
.agents/skills/promise-machine/SKILL.md     sole host-neutral suite router
docs/decisions/                             identity and vendoring decisions
```

The checker discovers the universe from plugin manifests and skill paths. The
coverage file cannot remove a discovered skill; omission is a failure.

## Appendix B: skill ownership and promise seed

Coverage codes: `P` positive, `M` missing evidence, `S` stale/mismatched subject,
`O` nearby overclaim, `R` recovery, `X` exception. “Inventory” means existing
tests must be classified before adding anything.

| Canonical skill | Identity | Promise owner | Narrow promise and nearest refused overclaim | Current evidence |
| --- | --- | --- | --- | --- |
| Alexandria | `alexandria-v0.2.0` | canonical skill | Source bytes and reviewed derivations remain digest- and source-bound; not complete or independently true credit history | strong plugin suite; classify P/M/S/O/R/X |
| Ariadne | `ariadne-v2.1.0` | canonical skill | An artefact digest is bound to recorded evidence; not signature identity, safety or factual truth | strong gates/conformance suite |
| Berean | `berean-v0.1.0` | canonical skill | Recorded answers, citations, block-bound reads, evaluations and promotion records satisfy the named release gates; not model execution, retrieval, factual truth or a silent upgrade of source/read evidence | 151 shipped tests, breach fixtures, packaging guard and offline reference release pass at `9c7692d`; classify corpus, answer, evaluation and promotion promises separately |
| Brevitas | `brevitas-v0.2.0` | canonical skill | Structure budgets hold without dropping protected evidence; not correctness, completeness, voice or register | deterministic structure/evidence tests; forward-test gap remains |
| Hermes | `hermes-v0.1.0` | canonical skill | Candidate gas fell under the recorded method while declared gates passed; not universal savings, correctness or security | harness tests and refusal paths; live bundle frontier remains |
| Elenchus | `elenchus-v1.1.0` | canonical skill | An observed failure was reproduced, localised, reduced and guarded; not absence of other causes | extensive three-outcome and hostile-report fixtures |
| Ephoros | `ephoros-v0.1.0` | canonical skill | Named operational questions have bounded signals; not correctness of the operation | deterministic lint fixtures; address-key frontier open |
| Fiat | `fiat-v4.8.1` | canonical skill | Required phases and accepted receipts occurred in controller order; not independent truth of receipt assertions | controller and state tests; receipt truth boundary needs explicit case |
| Hypomnema | `hypomnema-v0.1.0` | canonical skill | Required reasons and pointers are recorded and resolvable; not correctness of a decision | link/runbook/record fixtures |
| Imprimatur | `imprimatur-v2.1.0` | canonical skill | Prose avoids or evidences the patterns checked; not human authorship or factual accuracy | checker plus frozen labelled corpus |
| Kronos | `kronos-v0.5.0` | canonical skill | Eligible held jobs were ranked under the recorded scoreboard and mode; not objective global priority | scoreboard/mode tests; terminal mature |
| Metron | `metron-v1.1.0` | canonical skill | A change met the recorded comparison and correctness gate; not causation outside the method | extensive budget, verdict, ledger and recovery tests |
| Phylax | `phylax-v1.1.0` | canonical skill | Declared off-chain boundaries have named controls; not total security | Python/TypeScript hostile fixtures; mature |
| Protasis | `protasis-v2.2.0` | canonical skill | A study/runbook contains material required to build; not correct implementation or receipt | runbook checker strong; study checker and merged-PR carry-forward remain human-held |
| Vulgate | `vulgate-v1.1.0` | canonical skill | Register changes while intended content is preserved; not truth of that content | deterministic rules; content-parity evaluation remains open |
| Horos | `horos-v9.3.3` | canonical skill | Classified sinks and skeletons match the stated evidence and universe; not complete irrelevance classification | extensive boundary/oracle suite and root currency guard; marker self-exclusion frontier remains open |
| Janus | `janus-v0.1.0` | canonical skill | Observed hook effects stayed inside a manifest for the named host adapter, recorder and bounded search; not hook safety, complete liveness or cross-host conformance | Python validator/reporter suite, Foundry honest/hostile harness and seven gates; second-adapter and two accepted manifest limits remain open |
| Lazarus | `lazarus-v1.1.0` | canonical skill | Declared fixture fields pass named proof or replay checks; ordinary RPC records remain recorded | strong proof, replay, path, release and failure suites |
| Lemma | `lemma-v0.1.1` | canonical skill | Inputs become validated source-linked chunks; not embeddings, retrieval or correct answers | Markdown/Solidity suites; callable ABI frontier open |
| Pandects | `pandects-v1.1.0` | canonical skill | An applicable law catches its specimen and returns a scoped campaign verdict; not whole-protocol safety | catalogue, checker, specimen and record tests |
| Probitas | `probitas-v0.1.0` | canonical skill | Dossier claims trace to declared-address evidence with visible gaps; not identity or Wildcat verdict | adapter, gate, sanitisation and rendering suites |
| Sapheneia | `sapheneia-v0.1.0` | canonical skill | Replies expose action, boundary, state, evidence and next step; not diagnosis | structural contract tests; cross-model corpus gap remains |
| Tabularium | `tabularium-v0.3.0` | canonical skill | Venue-native records map reproducibly with provenance; not identity, authenticity or chain proof | release, schema, mapping and hostile verification tests |
| Fizz | vendored digest | Hexaemeron overlay | Declared harness generation and campaigns ran over recorded scope; not exhaustive property discovery or security | inventory; add overlay-focused cases without editing upstream |
| Fizz Convert | vendored digest | Hexaemeron overlay | Selected properties were converted and the harness built; not semantic adequacy or completeness | inventory gap likely |
| Fizz Sync | vendored digest | Hexaemeron overlay | Reported source/ABI drift was reconciled under the snapshot; not semantic equivalence | inventory gap likely |
| Solidity Auditor | vendored digest | Hexaemeron overlay | Named audit roles inspected recorded Solidity scope and produced findings; not absence of defects | orchestration evidence; overclaim/recovery cases needed |
| X-Ray | vendored digest | Hexaemeron overlay | The declared pre-audit inventory and analysis ran over recorded scope; not an audit or security conclusion | report validation exists in workflow; overlay cases needed |

## Appendix C: structural and behavioural acceptance

The checker and fixtures must prove:

1. Every canonical skill is classified first-party or vendored.
2. Every first-party promise has all nine semantic fields.
3. Every vendored skill has a digest-bound first-party overlay and no vendored diff.
4. Every router resolves to one canonical contract without broadening it.
5. Every logical skill has one canonical implementation.
6. No router carries an independent behavioural version.
7. Package and skill versions are validated separately.
8. Every promise has classified P/M/S/O/R/X evidence or a reason a class is inapplicable.
9. `missing-contract/` fails.
10. `unclassified-skill/` fails.
11. `unresolved-router/` fails.
12. `duplicate-canonical/` fails.
13. `divergent-copy/` fails.
14. `unsupported-evidence-class/` fails.
15. `no-recovery/` fails without deleting or hiding its diagnostic artefacts.
16. The root README starts exactly with `# Wildcat Labs Skills`, followed by a
    blank line and `## The Promise Machine`; public Promise Machine prose agrees
    across the remaining mutable surfaces.
17. The complete root suite passes.
18. Every changed plugin suite passes.
19. Phylax, Ephoros and Hypomnema tree checks pass.
20. Imprimatur and applicable prose checks pass.
21. The Codex demonstration shows one authoritative Protasis and no equivalent collision.
22. Claude and host-neutral demonstrations resolve the same canonical contract identity.
23. Fiat's final ledger verifies, and no unrun check is reported.
24. Berean coverage distinguishes corpus, answer, evaluation and promotion
    promises; citation mismatch, missing block identity, source-class upgrade,
    time-domain conflict, unpinned evaluation and promotion-as-truth each fail
    or remain visibly refused.
25. A Lazarus-to-Berean or Berean-to-Ariadne handoff preserves the producer's
    evidence class and does not promote answer truth.
26. Janus coverage fails on an unknown or incompletely recorded effect and
    binds every conformance result to its adapter, manifest, recorder and
    bounded search.
27. Janus's honest hook passes, each hostile reference hook is caught by its
    owning gate, and no result claims general safety, proven liveness or
    cross-host validity.
28. Every install-local copy reports `promise-machine/v1` and is byte-identical
    to the root law; no plugin or router invents a private law version.
29. The recorded Fiat implementation base passes the root suite, Berean's complete suite
    including the packaging guard, Janus's 14-test Python suite and Janus's
    24-test Foundry suite before Step 1; a manifest with absent pinned corpus
    bytes cannot satisfy this criterion.

## Appendix D: module decomposition

| Module id | Responsibility | Depends on |
| --- | --- | --- |
| `promise-law` | Naming, normative semantics, evidence classes, consequence model | none |
| `promise-inventory` | Filesystem discovery, classification and plugin-local copy drift | `promise-law` |
| `promise-identity` | Canonical identity, versions, routers and host exposure | `promise-inventory` |
| `promise-contracts` | First-party declarations and vendored overlays | `promise-law`, `promise-inventory` |
| `promise-conformance` | Coverage inventory and domain-native negative evidence | `promise-contracts` |
| `promise-composition` | Preservation of evidence class, subject, scope and refused overclaim across skill handoffs | `promise-contracts`, `promise-conformance` |
| `promise-runtime` | Durable-result, refusal, recovery and exception bindings | `promise-conformance`, `promise-composition` |
| `promise-evolution` | Version, release and public-prose integration | `promise-identity`, `promise-conformance`, `promise-composition` |
| `promise-demonstration` | Full-suite and supported-host evidence | all prior modules |

Build order: law; inventory; identity and contracts; conformance and
composition; runtime and evolution; demonstration. Identity and contracts may
proceed from the same inventory, but both must finish before conformance closes
and composition must close before any consequential handoff is accepted.
