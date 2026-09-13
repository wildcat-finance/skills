# GitHub issue publisher version 1

This reference defines the Phylax component that admits one agent-authored
issue candidate before any GitHub App credential can be used. It is the
standing interface identified by
`adr/use-a-credential-owning-github-issue-publisher`. The current Step 1
implementation proves admission only. Signer, transport, socket service,
deployment, and hostile conformance arrive in their receipted later steps.

## Promise boundary

The complete version-1 operation is intended to authorise one consequence-3
issue creation in `wildcat-finance/skills`. Its evidence is one exact request,
two publisher-executed Imprimatur results, the closed record chain, one bounded
remote lifecycle, exact readback, and a content-free terminal receipt.

Sapheneia and Vulgate records establish that their named producer declared the
bounded comparison over the named digests. They do not establish factual truth
or semantic parity independently. Imprimatur establishes only its executable
lexicon and structural checks. A successful component conformance run does not
establish that a live host uses a distinct account or denies the agent access
to the PEM.

Version 1 refuses any other repository, operation, issue comment, issue edit,
pull request, closure, merge, deployment, or retry after an uncertain create.

## Canonical request

The request schema is `github-issue-publication-request/v1`. Its top-level
fields are exactly:

- `schema`: `github-issue-publication-request/v1`;
- `operation`: `issue.create`;
- `repository`: `wildcat-finance/skills`;
- `queue`: `held-job`, `wish`, `skill-wish`, or `observation`;
- `labels`: sorted unique bounded label strings;
- `frozen`: queue prefix, opening, structure, and protected inventory;
- `source`: frozen source candidate;
- `sapheneia_candidate`: candidate after the durable-record pass;
- `final_candidate`: exact publishable candidate after Vulgate;
- `authority`: bounded record of the explicit publication request; and
- `gates`: the four records in their fixed order.

Input is canonical ASCII JSON produced with sorted keys, no insignificant
whitespace, JSON string escaping, and no non-finite number. The parser rejects
duplicate names before a dictionary exists. It accepts no floating-point
value, unknown field, coercion, default, or trailing byte.

The request is at most 1 MiB, depth 8, and 256 aggregate members. A title is at
most 256 UTF-8 bytes. Each body stage is at most 256 KiB. Strings are NFC and
contain no control or directional-formatting character; a body may contain
line feed and tab. A title may contain neither.

## Candidate identity

Each candidate has exactly `schema`, `title`, and `body`. Its schema is
`github-issue-candidate/v1`.

The candidate identity is this byte sequence:

```text
UTF8("github-issue-candidate/v1") || 0x00 ||
U32BE(len(UTF8(title))) || UTF8(title) ||
U32BE(len(UTF8(body))) || UTF8(body)
```

`candidate_sha256` is SHA-256 over that sequence. It does not depend on a JSON
spelling or file path. The publisher retains the exact final title and body
strings after admission; later code must serialise those same strings to the
issue POST.

## Frozen structure and inventory

The `frozen` schema is `github-issue-frozen-inventory/v1` with exactly these
fields:

- `title_prefix`: the queue prefix before `: `;
- `body_opening`: the required exact opening or the empty string;
- `host_structure`: one to 64 ordered non-empty strings;
- `protected_inventory`: one to 64 ordered non-empty strings; and
- `schema`.

Every source, Sapheneia, and final candidate has non-empty title text after the
frozen prefix. Each body is either the frozen opening alone or starts with that
opening followed by a line feed. Every structure and inventory string occurs
in order in each candidate. This mechanical membership check does not
establish that the inventory is complete or that a connective edit preserved
meaning.

The frozen digest is SHA-256 over its canonical JSON object. The Sapheneia and
Vulgate records carry that digest.

## Queue rules

The queue field selects one code-owned rule:

| Queue | Title prefix | Required label | Required opening |
| --- | --- | --- | --- |
| `held-job` | `{skill}-next` | `held-job` | none |
| `wish` | `{skill}-N` | `wish` | none |
| `skill-wish` | `{skill}-wish` | no queue label | none |
| `observation` | `framework-N` | `observation` | `Protasis decides which skill or skills this observation upgrades. The filer is the wrong party to guess.` |

`{skill}` is one or more lowercase ASCII letter-or-digit segments separated by
single hyphens. `N` is a positive decimal integer without a leading zero.
The full title has exactly `: ` between its prefix and a summary whose first
character is not whitespace. `framework` is reserved for the observation
queue. A request carries exactly the queue label selected by this table, or
none for `skill-wish`; it may not carry another queue's label. Other repository
labels remain bounded, sorted, and unique.

## Repository publication contract

The source, Sapheneia, and final bodies each carry exactly one unfenced
`Fiat-Required: 0` or `Fiat-Required: 1` declaration and exactly one closed
fence whose info string is `carryover`. A declaration inside a Markdown fence
does not count. The request labels include `only-pr-needed` for `0` or
`fiat-run-needed` for `1`, never both.

The `carryover` fence holds from one to 128 non-empty rows. Each row has exactly
`id | disposition | reference`. An id is lowercase kebab-case and appears once.
`filed` and `duplicate` point to one canonical GitHub issue URL. `none` carries
a non-empty reason of at most 512 bytes. The reserved row id `none` is valid
only in the single row `none | none | <reason>`.

An optional status block uses one `<!-- status:start -->` and one later
`<!-- status:end -->` outside fenced code. It appears before filing prose, has
no unmatched or repeated marker, and contains no control character. These
checks run before authority and the supplied gate records. For an observation,
the frozen opening is the first visible filing-prose line after this block; the
block itself cannot satisfy or replace that exact opening.

## Authority record

The authority schema is `github-publication-authority/v1` with exact fields
`schema`, `kind`, `outcome`, `reference`, and `subject_sha256`. Version 1
accepts `kind: explicit-user-request` and `outcome: recorded`. The subject is
the final candidate digest. The reference is a bounded printable identifier,
not raw conversation text.

This record is required consequence-3 evidence. Its shape and subject are
checked. It does not prove that the named request occurred or that its author
had authority. The caller and operator remain responsible for that fact, and
the terminal receipt must not strengthen the record.

## Ordered gate records

There are exactly four records:

1. `sapheneia`: tool `sapheneia:sapheneia`, version `0.3.0`, outcome
   `passed`, source and candidate digests, candidate subject, frozen digest,
   and the five fixed durable-record checks.
2. `imprimatur`: tool `hexaemeron:imprimatur`, version `2.3.0`, outcome
   `clean`, the Sapheneia candidate subject, and zero defects.
3. `vulgate`: tool `hexaemeron:vulgate`, version `1.1.0`, outcome `parity`,
   source and final candidate digests, final subject, frozen digest, and the
   six fixed content-preservation checks.
4. `imprimatur-final`: tool `hexaemeron:imprimatur`, version `2.3.0`, outcome
   `clean`, the final subject, and zero defects.

The supplied Imprimatur records do not decide admission. The publisher loads
the pinned local Imprimatur implementation and reruns it first over
`sapheneia_candidate.title + "\n\n" + sapheneia_candidate.body`, then over the
same encoding of `final_candidate`. Either non-zero defect count or inability
to load or run the pinned checker refuses.

The Sapheneia checks are, in order: `subject-named`,
`host-structure-retained`, `protected-inventory-retained`, `connective-only`,
and `five-step-complete`.

The Vulgate checks are, in order: `facts-retained`, `numbers-retained`,
`commitments-retained`, `caveats-retained`, `links-retained`, and
`intent-retained`.

## Admission result

The Step 1 result schema is `github-issue-admission-result/v1`. It contains
only the request, source, Sapheneia, final, and frozen SHA-256 digests; queue;
labels; gate versions; outcome; and zero-valued mint and POST attempt counts.
It carries no title, body, inventory item, authority prose, raw diagnostic, or
credential.

Admission is a necessary input to the later runtime. It is not an issue
publication receipt and authorises no mutation by itself.

## Step 1 conformance reports

The code-owned manifest schema is
`github-issue-publisher-admission-manifest/v1`. It contains exactly `schema`
and `files`. `files` lists the six Step 1 fixtures by basename and SHA-256
digest. Paths outside that fixed set, duplicate rows, extra fields, malformed
digests, unsafe files, and changed fixture bytes refuse.

The CLI accepts only the frozen `conformance` command for candidate
`isolated-publisher`, one of the three Step 1 criteria, and that criterion's
exact report path below `.hexaemeron/design-reports/`. Before writing a report,
it checks every fixture digest, admits the golden request with the pinned local
Imprimatur runner, executes all four queue cases and all eleven rejection
cases, exercises the accepted and refused sides of both parser limits, and
binds the #855 source metadata to the exact title, body, and candidate digests.
The report writer opens each directory component relative to the working
directory with no-follow directory descriptors, then atomically replaces only
a regular single-link destination. An intermediate or final symlink refuses.
No conformance path can mint, sign, read a credential, send HTTP, or publish.

Each report has schema `protasis-design-report/v1` and exactly `schema`,
`candidate`, `criterion`, `value`, `unit`, `command`, and `exit`.
`ordered-admission-chain` reports `true` in `boolean`; `request-work-bound`
reports the enforced aggregate JSON-member ceiling of `256` in `count`; and
`request-byte-bound` reports the enforced request ceiling of `1048576` in
`bytes`. `exit` is `0`, and `command` is the exact frozen resolver command.

These reports prove only the selected Step 1 component predicates over the
digest-bound fixtures and current code. They are not signer, transport,
deployment, live-isolation, or GitHub publication evidence.

## Refusal codes

- `GIP100`: request byte size or completeness;
- `GIP101`: UTF-8 or JSON syntax;
- `GIP102`: duplicate JSON name;
- `GIP103`: JSON type, depth, member, string, or number bound;
- `GIP104`: non-canonical request bytes;
- `GIP105`: unsafe or unstable request file;
- `GIP110`: unsafe text;
- `GIP120`: request or candidate schema;
- `GIP121`: malformed digest;
- `GIP130`: queue rule;
- `GIP131`: label rule;
- `GIP132`: repository publication body rule;
- `GIP140`: frozen declaration;
- `GIP141`: frozen content missing from a candidate;
- `GIP150`: gate shape, order, subject, result, or digest;
- `GIP151`: Imprimatur found a defect;
- `GIP152`: pinned Imprimatur could not run;
- `GIP160`: authority record; and
- `GIP199`: unavailable, conformance, report, or internal operation.

Public diagnostics contain only schema, outcome, code, and field. They do not
copy a request value or exception message.

## Step boundaries

Step 1 establishes credential-free admission and the exact #855 refusal. It
exposes only the credential-free conformance report command described above.

Step 2 adds socket framing, peer policy, signer, fixed GitHub transport,
readback, receipt, and cleanup under injected tests. It still makes no live
network call in the repository suite.

Step 3 adds the closed hostile manifest, macOS deployment kit and verifier,
Phylax Promise declaration, repository route, package generation, and
component demonstration. Its result retains
`live_isolation: not-established` until a privileged operator separately
installs and verifies the service.
