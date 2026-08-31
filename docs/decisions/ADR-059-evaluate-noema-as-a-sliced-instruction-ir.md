# ADR-059: evaluate Noema as a sliced instruction IR in shadow mode

## Status

Accepted, 2026-08-30. Continued shadowing only. Step 5 passed its fixed
semantic, token and model-family gates. This accepts further evaluation, not
integration, native authorship or migration. A later ADR must supersede this
one before any authority reversal or repository migration.

## Context

The repository repeatedly loads large agent-facing Markdown files. Issue #909
is building `wildcat-agent-instruction/v1`: authored Markdown remains
authority, a closed reviewed model carries governed meaning, and compact bytes
are a derived full-model codec. Its active stack gives Noema a control design
and reusable boundary lessons, but changing that stack would erase the control
while four or more contributors are working nearby.

Issue #942 asks a different question. A native instruction IR could author
governed semantics as a typed graph, select only the constraints reachable for
one operation and state, and let a small runtime check consequential effects
outside model obedience. The supplied seed demonstrates a possible notation
and one useful sliced-token result. It does not implement typed modules,
source-span closure, a manifest-bound slicer or a policy runtime, and it has no
cross-family behavior evidence.

The choice affects an authorship format, trust boundary and runtime interface.
Reversing it after skills depend on the format would be expensive, so the
prototype must preserve the current authority direction while it is measured.

## Decision

Build Noema as bounded root tooling in shadow mode: existing Markdown remains
authoritative; canonical `.noe`, its graph and every projection are derived;
the runtime returns policy decisions but executes no external effect; and the
final step accepts, narrows or rejects the hypothesis against the fixed #942
gates.

Noema is not a plugin or selectable skill during this run. It changes no
marketplace, router, Promise Machine claim, CI workflow, #909 path or external
repository. Native Noema authorship, a skill conversion and Shoggoth migration
each require a later decision with separate evidence.

Use fixed-position canonical JSON arrays for authored records and prefix terms,
then derive a profile-bound `NT1` text projection by injective exact-string
substitution. Store graph and lock together as one atomic build artifact. This
keeps the governing layer structural and provider-neutral while retaining Git
review, byte recovery and ordinary standard-library parsing. The text carrier
is not the semantics; the recovered typed graph is.

The Step 3 runtime uses digest-addressed checked propositions rather than
free-named facts. Its manifest contains a self-contained canonical tape of the
included policy records and reachable dictionary, while binding the complete
graph, lock, facts and derived slice projection. Unknown guards remain in that
tape. A rule can disappear for a checked guard only when the omission repeats
the exact fact and evidence digest.

The callable runtime is read-only. It returns a policy decision, transition
terms, one inert literal or a labelled explanation; it has no subprocess,
network, repository, publication, deployment or file-mutation operation.
Consequence-2 and consequence-3 effects default deny, prohibition dominates
permission, and opposed requirements need one checked typed override. These
choices are prototype controls, not authority to replace Markdown or wire the
runtime into an agent.

The Step 3 audit hardens that boundary further: definition expansion precedes
slice link discovery, closed truth rejects contradictory supplied facts,
requirements cannot stand in for permission, and an unknown competing
transition stops the state machine. Runtime calls accept only locally derived
or fully artifact-verified manifests and reject later mutation. Overrides need
an active applicable higher requirement, invalid exceptions refuse before
permission, and a missing consequence marker defaults per relevant rule.
Selection also requires an attested build and an exactly hashed profile.
Nested authority and scope wrappers accumulate, low-consequence defaulting
requires an active applicable directive, and runtime typed fields expand their
locked pure definitions before comparison. Requirement conflict work has a
fixed pair budget and indexed override lookup, while recursive and quantified
truth evaluation shares one expansion-work counter.
Slice fixed-point closure likewise has one aggregate record-scan budget, and
nested directive traversal shares one expansion-work counter. A transition is
a selection root only when its declared from-state matches the selected state;
`next` refuses any other state because its transitions may have been omitted.
Runtime substitution respects nested binder shadowing, expanded finite sets
have set rather than multiset semantics, and decimal order is independent of
the host interpreter's integer conversion ceiling. Recursive evaluation keeps
authored subfact identities beside their expanded terms.
Runtime work counters span complete operations rather than resetting at rule
or transition boundaries. Selection and manifest validation precompute their
membership indexes, and unsealed in-process policy inputs refuse before a deep
walk. A high-consequence permit reports the permission that supplied its
applicable authority as the controlling node. Exception recovery remains
reachable context without becoming the exception's checked policy subject.
Secondary-rooted governing edges close over both active endpoints, literal
references retain set identity while number literals remain comparable, and
runtime receipts bind the exact slice, inputs and output they describe.
Manifest verification correlates to the exact manifest identity, while the
runtime self-test binds all seven exact case results, including receipts and
alternate selections, under one reported digest.

The Step 4 corpus binds complete current-tree Markdown bytes for Fiat, Phylax,
Sapheneia and Brevitas while mapping ten reviewed rule spans per source. Every
unmapped byte is an explicit authority-free remainder, so all four specimens
remain shadow-only. Questions carry complete expected policy outputs rather
than accepting whatever the runtime returns. Thirteen fixed hostile mutations
bind their input kind, query, baseline, semantic facets and exact changed or
refused result; the seven critical vectors accept only their named categories.
The supplied 17-file seed is copied byte-identically as non-executable
reference evidence and no seed Python enters the implementation process.

## Step 5 result

The measured hypothesis is accepted for continued shadowing. All four exact
profiles recorded counts, all three corpus gates passed under each profile,
all seven critical vectors passed, and Google and OpenAI each matched the
required answer for all eight source/Noema pairs. There were no unknown
profiles or answers. The private vocabulary digest remains unknown for all
four providers by design; token counts are endpoint accounting, not recovered
tokenizer vocabularies.

The complete corpus component counts are below. Bytes are representation bytes
and therefore common to every profile; the remaining columns are
endpoint-reported tokens after subtraction of the profile's measured wrapper.
`first use sum` is the sum of four independent per-specimen first uses. The
acceptance gate instead uses the four-document amortised first use shown in the
next table, where the kernel and aliases are paid once.

| component | bytes | Anthropic | Google | open-weight | OpenAI |
| --- | ---: | ---: | ---: | ---: | ---: |
| Markdown source | 106,269 | 35,866 | 23,980 | 23,686 | 23,141 |
| canonical `.noe` | 14,700 | 7,597 | 6,854 | 6,625 | 5,550 |
| full projection | 17,566 | 9,114 | 8,378 | 8,096 | 6,793 |
| operation slice | 14,553 | 7,699 | 7,258 | 7,046 | 5,797 |
| literals | 2,999 | 1,682 | 1,720 | 1,674 | 1,198 |
| kernel | 6,740 | 3,120 | 2,224 | 2,020 | 1,940 |
| reachable definitions | 703 | 304 | 206 | 194 | 191 |
| alias dictionary | 636 | 328 | 228 | 192 | 212 |
| first use sum | 22,161 | 11,343 | 9,790 | 9,354 | 8,045 |
| steady state | 14,553 | 7,699 | 7,258 | 7,046 | 5,797 |

| family | canonical, limit 55% | four-document first use, limit 70% | steady state, limit 40% | gate | measurement cost |
| --- | --- | --- | --- | --- | ---: |
| Anthropic | 7,597/35,866, 21.182% | 8,610/35,866, 24.006% | 7,699/35,866, 21.466% | pass | $0.876735 |
| Google | 6,854/23,980, 28.582% | 7,892/23,980, 32.911% | 7,258/23,980, 30.267% | pass | $0.1079985 |
| open-weight | 6,625/23,686, 27.970% | 7,623/23,686, 32.184% | 7,046/23,686, 29.748% | pass | $0.0305892 |
| OpenAI | 5,550/23,141, 23.983% | 6,359/23,141, 27.479% | 5,797/23,141, 25.051% | pass | $0.80443125 |

The one-through-four-document first-use evidence is not an alternate gate.
The first specimen exceeds 100% under every tokenizer because it pays the
kernel and dictionary before amortisation; the fixed gate applies to the
declared four-source corpus.

| family | 1 document | 2 documents | 3 documents | 4 documents |
| --- | --- | --- | --- | --- |
| Anthropic | 2,892/2,568, 112.617% | 4,920/23,521, 20.917% | 6,794/31,513, 21.559% | 8,610/35,866, 24.006% |
| Google | 2,482/1,645, 150.881% | 4,362/15,678, 27.822% | 6,173/21,084, 29.278% | 7,892/23,980, 32.911% |
| open-weight | 2,375/1,619, 146.695% | 4,180/15,449, 27.057% | 5,944/20,798, 28.580% | 7,623/23,686, 32.184% |
| OpenAI | 2,037/1,550, 131.419% | 3,559/15,178, 23.448% | 4,991/20,356, 24.519% | 6,359/23,141, 27.479% |

| evaluation family | recorded answers | paired cases | required classes | input/output tokens | cost | result |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| Google Gemini 3.7 Flash | 16, 0 unknown | 8/8 | 5 decision, 2 refusal, 1 unknown | 94,810/9,539 | $0.10687875 | pass |
| OpenAI GPT-5.6 Sol | 16, 0 unknown | 8/8 | 5 decision, 2 refusal, 1 unknown | 86,140/942 | $0.566575 | pass |

The accepted run cost $1.81975395 for measurement and $0.67345375 for
evaluation. The cumulative append-only ledger records 932 calls and
$12.1631155 spent under the $25 ceiling. Nine unresolved reservations retain
$0.2926388325, leaving $12.5442456675 usable authority. No reservation was
deleted or discounted.

The durable evidence is anchored to commit
`f10e959c37875899b8020e19223da0e52e1e06fa` and tree
`f2d29639762e37b14223640b3c95ce72a64dce33`. The corpus identity is
`943f9f0fc38c7d9e621943018ae6c931c3af3cbb74d97a3d75a2904f2d6862f7`,
the profile set is
`2961cfffa646819470f05e5e5b85a760504c7ca92e83422dd61b637d1ffb5775`,
and the case set is
`09277294f692c16a4f6e4d90c61430a7d812ff9f86f23445933e3b7b4c2d1a5c`.
The packet, measurement, answers and evaluation digests are respectively
`41f0f3bc626df5adcff46f7a127b0508a079b77b2e8b65052eaef710110901eb`,
`60fe1eb4f78c6fe5a28fb20ab76844a7af0dcb1dbc5a03b2b7a6b94d8eb2cb88`,
`1ea323e248d759b37196751dac9c14c3ea0bd29d4288ebb76bb7f17285bd8c63`
and `8da27b64ef6d35ec0f30c77a754fe771be23757a9f2b56c8dfb83192a6245242`.

Four rejected runs remain part of the decision record:

- `a4af9ffd` scored 12/16 and 5/7 vectors. The shared generic graph, absent proposition facts and 58-byte non-grammar kernel made it a guessing test. Its packet/measurement/answers/evaluation digests are `0141beedd32870e32195f06ab3e816f697e72701727eaddfcabea259a1542543`, `a8b528123384f6bc4ba4840c25fd32fcd449b9abdf0e848dbb5427bc3e99a51d`, `8f917366ba3542ecb0aed0d54bdf6c0294454d33324167cc0ce9284cab9fd26a` and `95174a935dbcdeaa4cbe825326408fa343e287fcd1477109770350bc38bc2c46`.
- `d19b6dec` scored 13/16 and 6/7 vectors after source-bound graphs, a complete kernel and typed runtime context landed. Google missed the Sapheneia actor swap; OpenAI missed that case and Fiat's missing authority because the source's explicit-request conditions were not present as facts. Its four digests are `a3c9e4ce0865d3a99e7182eb9b242a4d77cda5ea4e454e2e867156b83a3cdb2f`, `75768505c7806c035151de707dbe4009596e14bde37117a94831ecc908918c05`, `d973df277ea78284f5f83920fbc6973efa44b9915f9bc679a8c2656491b8be9e` and `0872d13783bb514f1b6521ff265b58dd85524a86bf86c8bcd87a8b4861a62bfb`.
- `90176b6b` scored 15/16 and 6/7 vectors after those facts were bound. OpenAI's source answer permitted `model-output.authorize` while Noema correctly refused it, exposing an ambiguous Phylax source/effect mapping rather than a valid oracle. Its four digests are `004208575b085bdb2d5fe3cd6550476a8368297892cd11112abae4e0a2382ad0`, `544a711f800e0282bacc925ae73506f35359990365770547e5e529e0de8e66c0`, `725efefb370fb1fbe65e12d42fa45b26eb13e23d302a9a7cd018c7e3e5cdcb45` and `19a783df37836a7311fce48fe65a7a80793176d148ff9d45931901c0a184b96e`.
- `6235d230` scored 15/16 and 6/7 vectors after the consequence case was rebound to Phylax's exact ask-first dependency rule. Google selected the correct Noema answer but its source response ended at 1,010 of 1,024 output tokens with `finish_reason=length` before emitting `answer_id`. Raising both authorised evaluation profiles to the existing 2,048-token bound removed that adapter failure. Its four digests are `2f7dffc398f114fcbc10be441ddf8afca53945551cc8879297838b8ae102201f`, `9ad9b47224cae8e9ae81d6a1c85e9c73bd4e8b6001b9ebb5e020950e15dfa5f9`, `11cf6ad3a7c2d603459ed2ebe3927f8d0180d8449ce1dfbd1be0509b43bab7e3` and `9449b3e0910df36c454a73325a938f2c79fd9dc37d0955cbf79a50a6c62624d8`.

This result does not compete with #909 on equal coverage. #909's whole-model
codec retains the complete governed model under Markdown authority. Noema gets
its lower task cost by selecting reviewed semantics and leaving every other
byte in an explicit unsupported remainder. The benefit is executable,
task-specific policy structure; the cost is a larger trusted implementation,
source-to-graph review and incomplete semantic coverage. Neither result
licenses replacing the other.

Native Noema authorship or migration needs a separate issue and later ADR. At
minimum it must supply independently reviewed full semantic coverage or a
defined hybrid authority rule; repeat the held cases across source and model
drift without tuning on them; test native authoring, review, merge and recovery
workflows; audit the parser, slicer, runtime and intended integration boundary;
and define staged adoption, rollback and removal of the Markdown fallback.

## Alternatives

### Extend `wildcat-agent-instruction/v1`

Rejected for this run. #909 fixes a full derived codec and Markdown authority;
Noema tests task-state slicing and a possible later native-authoring endpoint.
Combining them would move the control design, couple two active stacks and make
either result harder to interpret.

### Keep Markdown and generate task-specific prose summaries

Rejected as the Noema endpoint. Summaries can reduce prompt size and remain an
evaluation baseline, but a deterministic checker cannot prove that an omitted
prohibition, authority edge or recovery path survived model-written prose.

### Compress prose into binary, base64 or private aliases

Rejected. Carrier bytes are not operational semantics, base encodings can cost
more model tokens than source, and an alias table can erase its local saving
once bootstrap cost is counted. Opaque carriers also discard ordinary Git
review and semantic diff.

### Make Noema authoritative immediately

Rejected. Source-to-graph review can establish span coverage and still encode a
reviewer's misunderstanding. Until the fixed mutations, critical vectors,
token measurements and two-family cases exist, an authority flip would promote
an untested interpretation.

## Consequences

The prototype can reuse #909's closed-model, canonicalization, bounds,
source-binding and stable-refusal lessons without modifying its files. GitHub
review keeps canonical text, semantic diff, generated views, vectors and
digests visible. Prompt-only consumers pay the complete kernel and reachable
dictionary cost; runtime consumers can keep policy enforcement outside model
context.

The parser, type checker, module registry, projector, slicer and policy
evaluator become a larger security-sensitive base. Every layer therefore has a
separate stacked step, fixed resource limits, hostile fixtures and no partial
result on refusal. Live tokenizer and model adapters remain ask-first and
outside instruction authority.

The accepted Step 5 result permits continued shadow evaluation only. It does
not permit native skill authorship, a plugin registration, a repository-wide
conversion or migration. A rejected result stays useful: it records which
semantic, compression or transfer gate failed without moving the gate after
observation.

The Step 4 evidence establishes deterministic provenance, regeneration and
counterexample behavior for these four reviewed mappings. It does not establish
that a mapping captured every meaning in its Markdown remainder, generalize to
another skill revision, satisfy any compression gate or predict model
comprehension. Source drift requires a reviewed rebind before the corpus can be
called current.

This run stops after its final prototype checkpoint. Fiat integration, merging
the run branch, closing #942 or adopting Noema anywhere is outside this ADR and
requires separately scoped follow-up issues.
