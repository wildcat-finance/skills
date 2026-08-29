
## audit-record-schema-timestamp-synopsis, step 1, round 1 -- 2026-08-23T04:14:45Z

Audit schema: fiat-audit-round/v1

### Coverage

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction

Elenchus verdict: guarded

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | tests/test_audit_prefix_integrity.py | The fixture could re-bless changed protected bytes without checking its named starting commit. | fixed in this commit |
| S1-R1-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Raw HTML blocks could hide a complete record or required value while the receipt treated it as visible Markdown. | fixed in this commit |
| S1-R1-03 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | A raced parent-directory symlink could redirect the final-component-only open outside the worktree. | fixed in this commit |

### Leads

Leads not pursued: step 2 synopsis generation, currency, compression, and physical-lead retention are not implemented in this step and remain explicit negative space

## audit-record-schema-timestamp-synopsis, step 1, round 2 -- 2026-08-23T04:54:18Z

Audit schema: fiat-audit-round/v1

### Coverage

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction

Elenchus verdict: guarded

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Blank-delimited CommonMark raw blocks such as div and custom tags could hide a strict heading while the receipt treated it as visible Markdown. | fixed in this commit |
| S1-R2-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The descriptor walk silently lost no-follow protection on unsupported platforms and leaked a newly opened child descriptor if fstat failed. | fixed in this commit |
| S1-R2-03 | medium | tests/test_audit_prefix_integrity.py | The permanent prefix check followed final or ancestor symlinks, so a protected audit path could be replaced with an alias to unchanged bytes. | fixed in this commit; guard itself is not independently Elenchus-guarded |
| S1-R2-04 | low | tests/promise_machine_coverage.json | The controller fixes changed its runtime digest while all three Promise inventory bindings still carried the pre-fix value, failing the root suite. | fixed in this commit at reviewed digest b500bc7118a87deb371a62cbdca4edfee68cd18d3accdb81b4575828e8f1706c; guarded by the root suite |

### Leads

Leads not pursued: S1-R2-03 changes the permanent checker and its assertion together, so the parent overlay cannot independently guard that cause; aggregate Elenchus guarded comes from four causal assertion failures for S1-R2-01 and S1-R2-02, while the fifth parent failure was the unrelated unpinned Node-version fixture; S1-R2-04 is guarded separately by the two root Promise tests that failed before its digest repair and now pass; step 2 synopsis generation, currency, compression, and physical-lead retention remain explicit negative space

## audit-record-schema-timestamp-synopsis, step 1, round 3 -- 2026-08-23T05:33:02Z

Audit schema: fiat-audit-round/v1

### Coverage

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction

Elenchus verdict: guarded

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | A four-space pseudo-closing fence or invalid backtick-info opener could leave a complete strict record inside a CommonMark code block while the selector exposed and accepted it. | fixed in this commit; guard red; Elenchus verdict `guarded` |
| S1-R3-02 | medium | tests/test_audit_prefix_integrity.py | The prefix reader checked resolution and file kind, then reopened by pathname, so a raced replacement could make it read through a symlink after validation. | fixed in this commit with a descriptor-relative no-follow reader; manual guard red; the overlay cannot isolate a checker and assertion in the same test file |
| S1-R3-03 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The final descriptor open omitted nonblocking mode, so a raced FIFO replacement could block before the regular-file check. | fixed in this commit; guard red; Elenchus verdict `guarded` |

### Leads

Leads not pursued: S1-R3-02 changes the permanent checker and its assertion together, so the Elenchus parent overlay cannot independently guard that cause; its focused manual guard failed before the fix and passed afterward; aggregate Elenchus `guarded` comes from the controller guards for S1-R3-01 and S1-R3-03, while the Promise digest fixture also changes with the controller; step 2 synopsis generation, currency, compression, atomic replacement, Horos interaction, and physical-lead retention remain explicit negative space

## audit-record-schema-timestamp-synopsis, step 1, round 4 -- 2026-08-23T05:58:15Z

Audit schema: fiat-audit-round/v1

### Coverage

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction

Elenchus verdict: guarded

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R4-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Fence closure inspected an empty suffix after the regex had consumed its remainder, so a trailing-info pseudo-close exposed a strict record still inside CommonMark code. | fixed in this commit; guard red |
| S1-R4-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Python `splitlines()` promoted non-CommonMark separators to physical line starts, allowing a phantom strict H2 after U+2028 and related characters. | fixed in this commit; guard red |
| S1-R4-03 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Inline raw-tag parsing repeated whole-line searches and lowercasing without physical-line or H2 caps, making a bounded audit log quadratic to inspect. | fixed in this commit; guard red |
| S1-R4-04 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | NUL and unpaired-surrogate configured paths escaped the controller's stable refusal and raised uncaught path-encoding exceptions. | fixed in this commit; guard red |

### Leads

Leads not pursued: the append-only legacy log retains pre-existing Brevitas diagnostics and cannot be rewritten, so this new record is checked separately; step 2 synopsis generation, currency, compression, atomic replacement, Horos interaction, and physical-lead retention remain explicit negative space

## audit-record-schema-timestamp-synopsis, step 1, round 5 -- 2026-08-23T06:18:00Z

Audit schema: fiat-audit-round/v1

### Coverage

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction

Elenchus verdict: guarded

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R5-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Risk-register duplicate checks and Covered membership each scanned an ordered list, making a Protasis-valid high-cardinality study quadratic under the accepted input cap. | fixed in this commit; guard red |
| S1-R5-02 | medium | tests/test_audit_prefix_integrity.py | The permanent prefix reader consumed each whole future audit log even though it checks only the fixed protected prefix, so a permitted append could exhaust the root gate. | fixed in this commit; bounded-read guard green |
| S1-R5-03 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Unicode whitespace was stripped as CommonMark space, so a pseudo-closing fence or nonblank HTML-block line could expose and receipt a record that remained hidden Markdown. | fixed in this commit; guard red |

### Leads

Leads not pursued: S1-R5-02 changes the permanent checker and its assertion together, so the detached-parent overlay cannot independently guard that cause; aggregate Elenchus `guarded` comes from the high-cardinality and CommonMark controller guards; step 2 synopsis generation, currency, compression, atomic replacement, Horos interaction, and physical-lead retention remain explicit negative space

## audit-record-schema-timestamp-synopsis, step 1, round 6 -- 2026-08-23T06:45:23Z

Audit schema: fiat-audit-round/v1

### Coverage

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction

Elenchus verdict: guarded

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R6-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The CommonMark type-6 block-tag set omitted `hgroup`, so a trailing-text opener could hide a complete strict record while the receipt treated it as visible Markdown. | fixed in this commit; guard red |
| S1-R6-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Required fields and the findings table were checked independently but not ordered, so a shuffled record passed without matching the canonical schema. | fixed in this commit; guard red |
| S1-R6-03 | low | audit/AUDIT.md | Brevitas report mode rejected the mandatory two-row findings table under its three-row presentation minimum. | fixed in this commit by recording the lint finding; Brevitas red then green |

### Leads

Leads not pursued: S1-R6-03 is not independently Elenchus-guarded because the canonical audit record and its finding count move together; aggregate Elenchus `guarded` comes from the two causal controller guards; step 2 synopsis generation, currency, compression, atomic replacement, Horos interaction, and physical-lead retention remain explicit negative space

## audit-record-schema-timestamp-synopsis, step 1, round 7 -- 2026-08-23T07:22:16Z

Audit schema: fiat-audit-round/v1

### Coverage

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction

Elenchus verdict: guarded

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R7-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | A valid CommonMark closing fence with a trailing tab remained open, so the shared selector rejected a strict record or source block after it. | fixed in this commit; guard red |
| S1-R7-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | `done audit --log` could replace the final round's checked canonical log path in the closure receipt. | fixed in this commit; guard red |
| S1-R7-03 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | A multiline inline tag or link title could absorb required field lines while the receipt treated them as standalone Markdown. | fixed in this commit with blank-line field boundaries; guards red |
| S1-R7-04 | low | audit/AUDIT.md | The first Brevitas invocation supplied three drafts to its one-draft CLI and exited 2. | fixed by separate one-draft invocations; not an Elenchus guard |
| S1-R7-05 | low | audit/AUDIT.md | Whole-file Brevitas report mode exited 1 on pre-schema diagnostics in the immutable legacy prefix. | fixed by linting this appended H2 record separately; not an Elenchus guard |

### Leads

Leads not pursued: aggregate Elenchus `guarded` comes from the three causal controller guards; S1-R7-04 and S1-R7-05 are gate-scope faults without independent Elenchus guards; step 2 synopsis generation, currency, compression, atomic replacement, Horos interaction, and legacy lead extraction remain explicit negative space; issue 453 still owns signed report-byte binding

## audit-record-schema-timestamp-synopsis, step 1, round 8 -- 2026-08-23T08:11:27Z

Audit schema: fiat-audit-round/v1

### Coverage

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction

Elenchus verdict: guarded

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R8-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Type-1 raw HTML missed a bare end-of-line opener and required its closer to match, diverging from CommonMark in both directions. | fixed in this commit; guards red then green |
| S1-R8-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | A lowercase declaration opener could hide a strict record under current CommonMark while the selector exposed it. | fixed in this commit; guard red then green |
| S1-R8-03 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The findings parser stopped before a valid GFM continuation row and split escaped cell pipes as delimiters. | fixed in this commit; guards red then green |
| S1-R8-04 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The GFM type-6 `source` tag could hide a strict record while the selector exposed it. | fixed in this commit; guard red then green |
| S1-R8-05 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Masking a nonblank inline-HTML line could fabricate the blank boundary required before a field hidden in multiline raw markup. | fixed in this commit; guard red then green |

### Leads

Leads not pursued: the round-8 ceiling requires the controller's `audit-verdict` stop; step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction remain explicit negative space; issues 453, 369, and 363 remain outside this step

## audit-record-schema-timestamp-synopsis, step 1, round 9 -- 2026-08-23T08:43:51Z

Audit schema: fiat-audit-round/v1

### Coverage

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction

Elenchus verdict: guarded

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R9-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The final-H2 selector recognised only non-empty, unindented ATX headings, so a later empty or indented ATX H2 was folded into the prior strict entry and accepted. | fixed in this commit; guard red then green |
| S1-R9-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The final-H2 selector omitted Setext H2 syntax, so a later level-two Setext record was folded into the prior strict entry and accepted. | fixed in this commit; guard red then green |

### Leads

Leads not pursued: the Brevitas B011 probe was inapplicable because this schema-mandated record is completeness evidence excluded by that skill; the unwrapped Elenchus runner reached ambient Node v22.22.3 and failed only its v26.6.0 fixture, with failed report SHA-256 433e7592fc5da275e03d0ed781f8a989782a84020091a28a6b13f3a1ea1a841b preserved before the same exact report command passed under the runbook-pinned Node; differential CommonMark probes found conservative refusals outside the canonical strict append grammar but no further acceptance bypass; step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction remain explicit negative space; issues 453, 369, and 363 remain outside this step

## audit-record-schema-timestamp-synopsis, step 1, round 10 -- 2026-08-23T09:30:01Z

Audit schema: fiat-audit-round/v1

### Coverage

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction

Elenchus verdict: guarded

### Findings

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R10-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Finality and uniqueness trusted the lossy HTML visibility mask alone, so inline-code and type-7 false positives could erase a later H2 or duplicate schema field and receipt a non-canonical record. | fixed in this commit; four guards red then green |
| S1-R10-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Unicode-aware case folding treated a long-s end tag as ASCII `s`, closed a type-1 raw block early, and exposed a strict record that CommonMark kept hidden. | fixed in this commit; guard red then green |

### Leads

Leads not pursued: the raw structural parity check deliberately refuses source-column schema lookalikes inside masked Markdown rather than claiming a general Markdown parser; canonical Warden records keep quoted labels in prose or table cells; commonmark 0.31.2 differentially confirmed the five false acceptances; step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction remain explicit negative space; issues 453, 369, and 363 remain outside this step

## audit-record-schema-timestamp-synopsis, step 1, round 11 -- 2026-08-23T16:24:04Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction; issue 453 report-byte and commit binding; issues 369 and 363

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R11-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The receipt used a bespoke whole-log CommonMark/GFM visibility model as append authority instead of validating the exact unreceipted raw delta. | fixed in this commit; guard red then green |
| S1-R11-02 | low | tests/promise_machine_coverage.json | Three Fiat Promise runtime rows retained the pre-redesign source digest, so both root Promise coverage tests failed PM071. | fixed mechanically in this commit; root guards red then green |
| S1-R11-03 | low | plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/study.md | The first receipted amendment ended with a blank line, so the required raw git diff check exited 2. | fixed by a supported second append-only amendment in this commit; no independent Elenchus guard |
| S1-R11-04 | low | plugins/hexaemeron/tests/test_hexctl.py | The active round-10 boundary guard called a helper absent on the parent, so pinned Elenchus reported one infrastructure AttributeError instead of a pure assertion failure. | fixed with a parent-safe callable assertion in this commit |

Leads not pursued: the first pinned Elenchus replay was inconclusive with 906 executed tests, 22 assertion failures, and one parent-only AttributeError; the parent-safe guard repair leaves the raw-delta controller and changed Promise coverage tests as aggregate Elenchus guards; the append-only study repair is guarded by controller verify, exact receipt hash and copy, and raw diff exit 0 but has no independent Elenchus claim; step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction remain explicit negative space; issues 453, 369, and 363 remain separately owned

## audit-record-schema-timestamp-synopsis, step 1, round 12 -- 2026-08-23T16:51:18Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=not-applicable; synopsis-drift=not-applicable; lead-omission=not-applicable; partial-write=not-applicable; path-boundary=reviewed; horos-self-defeat=not-applicable; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: step 2 synopsis generation, currency, compression budget, atomic replacement, Horos interaction, and legacy lead extraction; step 3 disposable v5.13.1 proof; issue 453 report-byte and commit binding; issues 369 and 363; live-controller enforcement absent from pinned v5.12.1

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: none inside step 1 after the source review and named gates; the live run remains governed by pinned v5.12.1, so this clean Warden commit records review, gate, and canonical-entry evidence without claiming live issue-429 validation or new receipt leaves; the checked-in v5.13.1 controller gets its disposable proof in step 3; step 2 and issues 453, 369, and 363 remain outside this round

## audit-record-schema-timestamp-synopsis, step 2, round 1 -- 2026-08-23T18:10:05Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; active-controller v5.13.1 enforcement and the step 3 disposable checked-in-controller proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Any H3 in a schema-bearing record forced legacy classification, so an appended strict record could bypass strict validation, including by mimicking the grandfathered heading tuple. | fixed in d926d4eb581e8a86cfcfc802bd95b34ff56c1bfb; guard red then green |
| S2-R1-02 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Repository-relative source names containing controls, table delimiters, synopsis break markup, or surrogateescaped bytes could corrupt one-line framing or escape controlled refusal. | fixed in d926d4eb581e8a86cfcfc802bd95b34ff56c1bfb; guard red then green |
| S2-R1-03 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Discovery left the walk error callback unset, so an unreadable subtree could be skipped while generation succeeded with an incomplete source set. | fixed in d926d4eb581e8a86cfcfc802bd95b34ff56c1bfb; guard red then green |
| S2-R1-04 | low | plugins/hexaemeron/skills/fiat/SKILL.md | The Fiat Promise said controller verification established current derived-synopsis currency, although verification only preserves the earlier receipt-time check and recorded sibling digest. | fixed in d926d4eb581e8a86cfcfc802bd95b34ff56c1bfb; guard red then green |

Leads not pursued: no further step-2 defects after the fixes and named gates; multi-file generation remains per-sibling atomic, so interruption between replacements can leave a mixed set of complete old and new synopses until `--check` exposes it and rerunning `--write` repairs it; the live run remains pinned to v5.12.1 and cannot receipt v5.13.1 synopsis enforcement; step 3 owns the disposable checked-in-controller proof, issue 453 report-byte binding, issue 369 downstream consumption, and issue 363 frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 2 -- 2026-08-23T18:37:22Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Path framing rejected only lowercase `<br>` and ASCII controls, so case and syntax variants plus non-printable Unicode separators and bidi controls could enter one-line synopsis metadata. | fixed in 13cd55e339fa9c835c5b14b7b5723595aceaa779; guards red then green |
| S2-R2-02 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Strict parsing discarded the source's EOF-LF state and made its trailing empty physical line optional, accepting a missing terminal LF, an extra EOF blank line, or no blank separator between records. | fixed in 13cd55e339fa9c835c5b14b7b5723595aceaa779; guards red then green |
| S2-R2-03 | low | tests/promise_machine_coverage.json | The Fiat runtime coverage subject still claimed a current synopsis digest although its Promise binds only the receipt-time digest. | fixed in 13cd55e339fa9c835c5b14b7b5723595aceaa779; guard red then green |

Leads not pursued: schema-less historical H3 records remain legacy by contract, while the only schema-bearing H3 exception is limited to root ordinals 344 through 353 and exact pinned record digests, so no future path, ordinal, or byte variant is authorised; discovery skips excluded `.git` and `.hexaemeron` sinks and intended symlink trees while unreadable included subtrees fail closed; generation is per-sibling atomic rather than cross-file transactional, so `--check` deliberately exposes a mixed set of complete siblings; the live controller remains pinned to v5.12.1, step 3 owns disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 3 -- 2026-08-23T19:10:52Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | The strict classifier let a heading-only strict record or any mutation of a reserved pinned record fall back to legacy, so malformed strict bytes could evade strict validation. | fixed in 686dc86e80ae0b9f3c99c40d021fcf25e57c9e86; guards red then green |
| S2-R3-02 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Raw partitioning did not enforce exactly one blank physical line before a strict candidate after a legacy partition, so zero or multiple LF separators survived. | fixed in 686dc86e80ae0b9f3c99c40d021fcf25e57c9e86; guards red then green |
| S2-R3-03 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Legacy CRLF input retained carriage returns inside one-line output rather than refusing non-canonical physical framing. | fixed in 686dc86e80ae0b9f3c99c40d021fcf25e57c9e86; guard red then green |
| S2-R3-04 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py, plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The generator and controller compared descriptor identity only before reading and did not re-stat it afterwards, so an in-place rewrite observed across the read could be accepted. | fixed in 686dc86e80ae0b9f3c99c40d021fcf25e57c9e86; guards red then green |
| S2-R3-05 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | The write path capped source and post-read sibling bytes but not freshly rendered bytes before replacement, so an oversized view could replace a prior valid sibling before refusal. | fixed in 686dc86e80ae0b9f3c99c40d021fcf25e57c9e86; guard red then green |
| S2-R3-06 | low | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | The audit-directory symlink diagnostic interpolated an unframed discovery path, so a control-bearing directory name could inject physical error lines. | fixed in 686dc86e80ae0b9f3c99c40d021fcf25e57c9e86; guard red then green |
| S2-R3-07 | low | plugins/hexaemeron/agents/warden.md, plugins/hexaemeron/skills/fiat/references/audit-loop.md | Staging instructions named the root synopsis instead of the configured log's sibling, directing a non-root round at the wrong derived view. | fixed in 686dc86e80ae0b9f3c99c40d021fcf25e57c9e86; guard red then green |

Leads not pursued: no further step-2 defects after these cause-level fixes and the named gates; schema-less H3 remains legacy by contract and the ten root exceptions require the exact path, ordinal, and record bytes; descriptor guards refuse mutations observed between opened and finished stats but do not promise an atomic snapshot after the final check; discovery fails closed for included walk errors while excluding `.git`, `.hexaemeron`, and intended non-audit symlink trees; the temporary write path uses a same-directory exclusive 0600 file, flush and fsync, replacement, cleanup, and exact post-read, with every sibling pre-rendered before per-file replacement rather than a cross-file transaction; Horos leaves every synopsis outside the hard boundary and reports the boundary current; the three affected Promise rows bind the reviewed controller bytes; the live controller remains pinned to v5.12.1, step 3 owns disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 4 -- 2026-08-23T19:47:44Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R4-01 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py, plugins/hexaemeron/skills/fiat/scripts/hexctl.py | A parent directory rename and rebind during a descriptor read let both readers accept bytes from a source no longer at the canonical path, and the same rebind during replacement could overwrite a synopsis in the detached directory. | fixed in 3a9ba9a42dbc7aedadded73c2ed58f7f4e6f8ad3; guards red then green |
| S2-R4-02 | low | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | A control-bearing path to a non-regular `AUDIT.md` reached its source-kind diagnostic without one-line framing, so a newline in the path could inject a physical diagnostic line. | fixed in 3a9ba9a42dbc7aedadded73c2ed58f7f4e6f8ad3; guard red then green |
| S2-R4-03 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | A renderer that raised during module execution or omitted its required validator interface escaped the bounded load refusal as a `RuntimeError` or `AttributeError`. | fixed in 3a9ba9a42dbc7aedadded73c2ed58f7f4e6f8ad3; guards red then green |

Leads not pursued: no further step-2 defects after the fixes and named gates; direct replacement, in-place writes, growth, shrinkage, parent rebinding, and hard-linked inode changes are refused only when observed by the identity, length, and time checks, which do not promise an atomic snapshot after the final check; corrupt or incomplete renderer modules now use the fixed load refusal, while arbitrary exceptions raised by a valid validator remain distinct and propagate; an `audit/AUDIT.md` directory is not a source because discovery admits only regular files; LF framing rejects CR and treats other same-line UTF-8 bytes as opaque by contract, source lines are capped at 1 MiB, and complete rendered views at 16 MiB without a smaller physical output-line budget; exact strict reconstruction, future-slot refusal, legacy H2, risk-table and lead retention, per-sibling atomic writes, all six prefixes, receipt-time synopsis binding, Promise digests, and frontier retention passed; Horos reports a current boundary with synopsis candidate drift and no hard synopsis entries; the live controller remains pinned to v5.12.1, step 3 owns disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 5 -- 2026-08-23T20:15:07Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R5-01 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The canonical re-open loop lost ownership of a newly opened child descriptor when closing its parent failed, leaving that descriptor open on the bounded refusal path. | fixed in 7c30bc5cbc9f96629a73b117e13d33c27734aeb8; guard red then green |
| S2-R5-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | A callable renderer could return an arbitrary value instead of one lowercase SHA-256 digest, and the controller would store it as synopsis evidence in state and the ledger. | fixed in 7c30bc5cbc9f96629a73b117e13d33c27734aeb8; guard red then green |
| S2-R5-03 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | `os.walk` placed directory-valued and directory-target symlink `audit/AUDIT.md` entries in its directory set, bypassing the reserved source-kind refusal and allowing an incomplete discovery result. | fixed in 7c30bc5cbc9f96629a73b117e13d33c27734aeb8; guard red then green |

Leads not pursued: no further step-2 defects after the fixes and named gates; the three guards failed together on the unfixed tree and Elenchus returned `guarded` from its source-bound structured parent run; schema-less H3 remains legacy by contract, the ten root draft exceptions remain bound to exact path, ordinal, and bytes, and concurrent mutation after the final identity check remains outside the claimed snapshot; discovery now refuses every reserved non-regular source name while still skipping unrelated symlink trees and state sinks; validator exceptions outside the declared renderer error stay distinct, and the controller now stores only a lowercase 64-hex synopsis digest; per-sibling writes remain atomic rather than cross-file transactional; all six sources, strict records, legacy findings and risk tables, lead occurrences, issue-327 verdicts, line budgets, prefix guards, Promise bindings, and frontier values passed; Horos reports a current boundary with no hard synopsis entries; the live controller remains pinned to v5.12.1, step 3 owns the disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 6 -- 2026-08-23T20:52:50Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R6-01 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Repository discovery traversed nested Git repositories and worktrees, so an operator-root run could parse or rewrite audit artifacts owned by a separate checkout. | fixed in 6c9c60c0fca28c6f8e4b2b659a10160ba2209274; guard red then green |
| S2-R6-02 | low | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | `--write` read an existing synopsis through the 16 MiB input cap before replacement, so an oversized stale derived file could not be repaired by regeneration. | fixed in 6c9c60c0fca28c6f8e4b2b659a10160ba2209274; guard red then green |
| S2-R6-03 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Root resolution inspected the supplied directory only before `realpath`, so a symlink rebind in that interval could redirect the accepted root outside the directory first inspected. | fixed in 6c9c60c0fca28c6f8e4b2b659a10160ba2209274; guard red then green |

Leads not pursued: no further step-2 defects after the three cause-level fixes and named gates; discovery now treats any nested `.git` marker as a checkout ownership boundary while preserving the six root sources; write mode defers stale sibling inspection to atomic replacement, which still refuses symlink and non-regular outputs and verifies exact post-write bytes; root resolution now binds the initial, current, and resolved directory identities across the observed `realpath` interval, while concurrent mutation after the final identity check remains outside the claimed snapshot; same-line UTF-8, including literal synopsis break text in source content, remains opaque by contract rather than a promised round-trip grammar; per-sibling writes remain atomic rather than cross-file transactional; all six strict and legacy retention checks, prefix guards, line budgets, Promise bindings, and frontier values passed; Horos reports the expected synopsis candidate drift with no hard synopsis entries and a matching boundary; the live controller remains pinned to v5.12.1, step 3 owns the disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 7 -- 2026-08-23T21:44:52Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R7-01 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Legacy extraction materialised one string per physical line plus per-record index and retained lists before the rendered-size refusal, so a 300,029-byte accepted source required 21,062,910 bytes of traced peak memory. | fixed in 5e1baffa709d3d2619322227ec9324b25f5ed22c; guards red then green |

Leads not pursued: no further step-2 defect after the causal streaming fix and source-bound focused checks; the corrected renderer keeps the receipted 16 MiB source, 10,000 H2, 1 MiB physical-line, 16 MiB rendered-view, and strict 15% compression bounds without adding a total-line refusal; a 400,029-byte source with 200,002 physical lines remains accepted, while the measured 300,029-byte workload retains the exact 750,347-byte output and SHA-256 b07dabc87790c93359c1aeb13e765f9fe91b551de387a23726ff3866fbbb2760 with peak memory reduced from 21,062,910 to 3,491,459 bytes; all six checked-in outputs and 1,000 seeded mixed strict and legacy differential cases remain byte-identical to the parent, and Elenchus records parent assertion failures in the Fiat, controller-runner, and synopsis suites with the fix green; the measured workload's wall time rose from about 0.60 to 0.86 seconds, with no latency improvement claimed or budget required; schema-less H3 remains legacy by contract, the ten root draft exceptions remain bound to exact path, ordinal, and bytes, and concurrent mutation after the final identity check remains outside the claimed snapshot; per-sibling writes remain atomic rather than cross-file transactional; the live controller remains pinned to v5.12.1, step 3 owns the disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 8 -- 2026-08-23T22:17:36Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R8-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | `SystemExit(0)` during renderer load, interface lookup, or validation could terminate `audit-round` with a successful process status but no receipt. | fixed in abc65441b9018709a0a4431f7c8bf00b73c125bb; guards red then green |
| S2-R8-02 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | `_table_cells` copied each growing cell repeatedly, so one accepted 1 MiB row took a 7.480113-second median in the recorded five-run CPU-time baseline. | fixed in abc65441b9018709a0a4431f7c8bf00b73c125bb; scaling guard red then green |

Leads not pursued: no further step-2 defect after the two causal fixes and named gates; 100,297 parent/current full-render differential cases and 100,009 table-row cases preserved acceptance and rendered bytes, including multibyte input, separator and EOF variants, duplicate legacy fields, tables and leads, pinned drafts, and all six live outputs; the exact 1,048,576-byte Metron workload moved from a 7.480113-second median to 0.022997 seconds across five CPU-time samples, with correctness gates green; the live controller remains pinned to v5.12.1, step 3 owns disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 9 -- 2026-08-23T22:56:24Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R9-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | `validated_audit_record` formatted a declared renderer error inside its matching handler, so an error whose `__str__` raised `SystemExit(0)` bypassed the sibling handler and let `audit-round` exit successfully without a receipt. | fixed in 6bdcc8be4ca73ac51cd82b68a8117823ea4ae664; guard red then green; Elenchus `guarded` |

Leads not pursued: no further step-2 defect after the cause-level fix and named gates; renderer `SystemExit(0)` at load, interface lookup, direct validation, and declared-error formatting now reaches a bounded code-2 refusal before state or ledger mutation, while `KeyboardInterrupt` and `GeneratorExit` remain distinct BaseException propagation; exhaustive old/new `_table_cells` comparison covered 960,800 strings through length seven over pipes, backslashes, whitespace, ASCII, Unicode, and astral input with zero acceptance or cell deltas, plus explicit empty-cell, backslash-parity, and 1 MiB rows, and the existing timing guard retained wide margin; 10,006 full renders spanning seeded strict and legacy mutations plus all six live logs had zero acceptance or output deltas against the pre-streaming renderer, and accepted 20,000-, 100,000-, and 150,000-line probes retained bounded memory scaling; schema-less H3 records remain legacy by explicit contract, the ten root draft exceptions remain bound to exact path, ordinal, and bytes, concurrent mutation after the final identity check remains outside the claimed snapshot, and sibling writes remain atomic rather than cross-file transactional; all six source/synopsis pairs, protected prefixes, risk coverage, leads, Promise bindings, and Horos boundaries passed; the live controller remains pinned to v5.12.1, step 3 owns disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 10 -- 2026-08-24T00:07:48Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R10-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | A declared renderer refusal could carry unsafe or oversized text, while an exception or `SystemExit(0)` from diagnostic emission could escape the intended code-2 boundary and report false success. | fixed in 08e311969f2f13c6b9f846bdf711824c2f12dd87; guards red then green; Elenchus `guarded` |
| S2-R10-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The controller's table scanner retained the quadratic growing-string loop already fixed in the renderer, so one accepted near-1 MiB findings row took about 7.25 seconds of CPU. | fixed in 08e311969f2f13c6b9f846bdf711824c2f12dd87; scaling guard red then green; Elenchus `guarded` |
| S2-R10-03 | low | plugins/hexaemeron/tests/test_hexctl.py | The new diagnostic regressions let the expected parent `UnicodeEncodeError` and diagnostic `OSError` escape their assertions, so the first source-bound Elenchus run reported an infrastructure error instead of proving the guards. | fixed in 08e311969f2f13c6b9f846bdf711824c2f12dd87; parent-safe assertions leave the final Elenchus run `guarded` |

Leads not pursued: no further step-2 defect after the three cause-level fixes and named gates; declared renderer failures at module creation, load, interface lookup, type check, validation, error formatting, digest check, and diagnostic emission now reach a bounded ASCII code-2 refusal before state or ledger mutation, including exact surrogate output `hexctl: error: unsafe\\nsurrogate: \\ud800`, while oversized text uses the fixed fallback; a foreign validator `RuntimeError` remains distinct and propagates as the same object under the accepted round-4 through round-7 boundary, and `KeyboardInterrupt` and `GeneratorExit` likewise propagate unchanged; the controller table comparison covered both raw and pipe-wrapped strings over a six-symbol alphabet through length seven, with the machine-recomputed total `sum(6**n, n=0..7) * 2 = ((6**8 - 1) / 5) * 2 = 671846` and zero deltas, while the fixed 1 MiB workload took 0.024103 seconds of CPU; all six live renders plus 5,000 seeded mutations had zero acceptance or output deltas against the pre-streaming renderer, and the existing renderer table comparison also retained 671846 zero-delta cases; schema-less H3 remains legacy by contract, the ten root draft exceptions remain bound to exact path, ordinal, and bytes, concurrent mutation after the final identity check remains outside the claimed snapshot, and sibling writes remain atomic rather than cross-file transactional; all six source and synopsis pairs, protected prefixes, strict records, legacy findings, risk tables, physical leads, line budgets, Promise bindings, and frontier values passed, and Horos reports a matching boundary with no hard synopsis entries; the live controller remains pinned to v5.12.1, step 3 owns disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 11 -- 2026-08-24T00:47:56Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R11-01 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The 4 KiB diagnostic cap applied only to the escaped payload, so a valid 4,096-byte renderer message emitted 4,112 bytes after the fixed prefix and LF. | fixed in e4617679b19bbe1775becd703cf10ea6efd01146; guard red then green; Elenchus `guarded` |
| S2-R11-02 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | Physical source bytes before the first raw H2 record were never inspected for `Leads not pursued`, so rendering could succeed after deleting a required lead occurrence from the synopsis. | fixed in e4617679b19bbe1775becd703cf10ea6efd01146; guard red then green; Elenchus `guarded` |

Leads not pursued: no further step-2 defect after the two cause-level fixes and named gates; the complete diagnostic frame is now capped at 4,096 bytes including its 15-byte prefix and terminal LF, with 4,079 and 4,080 plain payload bytes producing 4,095- and 4,096-byte frames, 4,081 through 4,097 plain payload bytes using the 57-byte fallback, 2,040 backslashes producing a 4,096-byte frame, and 2,041 backslashes using the fallback; control, escape, newline, backslash, Unicode, and surrogate cases emit only printable ASCII followed by one LF, diagnostic `OSError` and `SystemExit(0)` force code 2, and `KeyboardInterrupt` and `GeneratorExit` propagate unchanged; the declared renderer interface requires an exception superclass but no dedicated class identity, so `SynopsisError = Exception` validly catches `RuntimeError` and is not a defect, while a foreign `RuntimeError` remains the same propagated object under the canonical dedicated class and a custom metaclass cannot alter Python exception matching; invalid digest cases covering null, booleans, bytes, wrong lengths, uppercase, and newline refuse without state or ledger drift; the controller and renderer table scanners matched across 671,846 raw and pipe-wrapped strings with zero cell deltas, preserved escape parity, and parsed the exact 1,048,576-byte row in 0.023330 and 0.022478 seconds respectively; the focused 397-test suite, root 158-test suite, pinned Node 26.6.0 922-test suite, Promise, Phylax, Ephoros, Hypomnema, Protasis, Horos, Imprimatur, and diff gates passed, and all six checked-in source and synopsis pairs remained byte-identical to their starting outputs before this record; schema-less H3 remains legacy by contract, the ten root draft exceptions remain bound to exact path, ordinal, and bytes, concurrent mutation after the final identity check remains outside the claimed snapshot, and sibling writes remain atomic rather than cross-file transactional; the live controller remains pinned to v5.12.1, step 3 owns disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 12 -- 2026-08-24T03:22:10Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R12-01 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The 4 KiB diagnostic limit was computed over text characters, so a non-UTF-8 stderr encoding expanded the complete ASCII refusal frame beyond 4,096 raw bytes. | fixed in becd36a48e041d5141d442a8b2008494b18081ff; UTF-8 and UTF-16 guard red then green; Elenchus `guarded` |

Leads not pursued: no further step-2 defect after the cause-level fix and cumulative review; the exact subprocess reproducer emitted 8,192 raw bytes under `PYTHONIOENCODING=utf-16` while exiting 2, and the direct UTF-16 `TextIOWrapper` guard observed 8,194 rather than 4,096 because that stream added its two-byte prefix; the fix constructs one ASCII byte frame and writes it through the binary stream, producing exactly 4,096 bytes under UTF-8 and UTF-16 while text-only fallback streams retain code 2, diagnostic `Exception` and `SystemExit` remain bounded, and `KeyboardInterrupt` and `GeneratorExit` remain distinct; the 4,079 through 4,081 plain-payload and 2,040 through 2,041 backslash cutoffs remained green; exact-phrase placement before the first raw H2, substring and physical-line boundaries, LF and EOF separators, strict and legacy classification, table scanners, path discovery, bounded reads, atomic sibling replacement, receipt-time digest binding, Promise subjects, and all six current source views were reviewed without another finding; the focused 398-test suite, root 158-test suite, pinned Node 26.6.0 923-test suite, Promise, Phylax, Ephoros, Hypomnema, Horos, Imprimatur, synopsis, prefix, signature, trailer, and diff gates passed; Brevitas is inapplicable to this completeness-oriented schema record, Protasis is not implicated because the exact receipted study and runbook digests did not move, and Metron is not selected because no speed change or claim was made; the live controller remains pinned to v5.12.1, step 3 owns disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 13 -- 2026-08-24T04:29:12Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the non-Solidity waiver; live-controller synopsis enforcement remains pinned to v5.12.1; step 3 disposable checked-in v5.13.1 proof; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier identity

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R13-01 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The binary renderer-refusal path treated one write call as complete without checking its returned byte count, so a valid short write could emit only a prefix of the bounded ASCII diagnostic frame before exit 2. | fixed in 00db9c0daaa11f6bc7cafe47f1e92a88efdccefa; focused red then green; Elenchus guarded |

Leads not pursued: no further step-2 defect after the cause-level fix and cold cumulative review; valid positive short writes now drain the complete frame and flush when supported, while null, zero, negative, boolean, oversized, exception, and SystemExit results retain the code-2 refusal without a loop, text-only fallback emits the exact ASCII frame, and KeyboardInterrupt and GeneratorExit remain distinct at write and flush boundaries; the first unpinned Elenchus report was inconclusive with 925 executed tests, four assertion failures, and two errors because two flush-interrupt expectations let the unfixed parent's SystemExit escape, while the assertion-safe harness correction under pinned Node 26.6.0 returned guarded with 925 executed, five assertion failures, zero errors, and zero skips; controller and renderer table scanners matched 671,846 bounded variants with no delta, four pre-H2 lead substring and physical-line variants matched the retention boundary, and strict and legacy classification, LF and EOF separators, discovery, path identity, read and write bounds, atomic replacement, receipt-time synopsis digest, refusal no-drift, Promise subjects, version surfaces, and frontier text disclosed no second finding; the focused 400-test batch, root 158-test suite, fixed-tree pinned Node 26.6.0 925-test suite, six pre-append synopsis pairs, Promise 14 of 14, Phylax, Ephoros, Hypomnema, Horos hard boundary, signature, trailer, and diff gates passed; Brevitas is excluded for this completeness-oriented strict record and no performance claim selects Metron; the live controller remains pinned to v5.12.1, step 3 owns disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns frontier identity

## audit-record-schema-timestamp-synopsis, step 2, round 14 -- 2026-08-24T04:55:17Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the recorded non-Solidity waiver; active-controller v5.13.1 enforcement, which step 3 proves in a disposable run; issue 453 report-byte binding; issue 369 downstream synopsis consumption; issue 363 delegated identity; concurrent mutation after the final identity check; a transaction across all six sibling writes

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R14-01 | medium | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | A literal `<br>` inside an accepted retained physical line collided with the synopsis separator, so the canonical consumer split one source lead into fragments and the promised exact lead occurrence disappeared from the decoded multiset. | fixed in fa944305db3b16e739af9374cca1cb3f305c9a84; scaffold-free live and fixture guards red then green; Elenchus `guarded` |

Leads not pursued: the R13 custom short-write stream remains outside standard CPython 3.12 stderr behavior, where `BufferedIOBase.write()` completes the supplied bytes or raises; an actual subprocess exited 2 with the exact 32-byte refusal frame, so that premise yielded no new product finding. The literal `<br>` remains authored in this record rather than being deleted or excluded: the renderer now encodes `%` as `%%` and `<br>` as `%b`, and the canonical decoder restores exact headings, strict fields, findings, lead lines, and wrapped legacy tails across the delimiter and escape spellings while charging encoded bytes through the existing 16 MiB cap. Two initial pinned Elenchus runs against superseded commit 0c31d79630160f94e9efe28f9cb59a484b0e88df returned `passed` because the root-only guard was outside the receipted Hexaemeron command; the JSON repeat recorded 925 executed tests, zero assertion failures, zero errors, and zero skips. The minimal parent-safe guard was moved into the commanded suite and the unreceipted fix was re-signed as fa944305db3b16e739af9374cca1cb3f305c9a84; the final pinned run returned `guarded` with 926 executed tests, one parent assertion failure, zero errors, and zero skips, and the fixed tree passed 926 of 926. The focused 403-test batch, root 160-test suite, six synopsis pairs, Promise 14 of 14, Phylax, Ephoros, Hypomnema, Horos hard boundary, Imprimatur, signature, trailers, and diff gates passed. Renderer-only foreign risk ids still cannot reach a receipt because the controller checks the receipted set first; whole-set atomic replacement remains unpromised while each sibling replacement is atomic and the required follow-up check names mixed currency. Brevitas is excluded for this completeness-oriented strict record, no performance claim selects Metron, the live controller remains pinned to v5.12.1, step 3 owns disposable v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns delegated identity; no second candidate cleared the promise, supported reachability, observable consequence, and scaffold-free reproducer together.

## audit-record-schema-timestamp-synopsis, step 2, round 15 -- 2026-08-24T06:11:54Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the recorded non-Solidity waiver; live-controller enforcement beyond pinned v5.12.1; step 3's disposable checked-in v5.13.1 proof; issue 453 report-byte binding; issue 369 downstream synopsis consumption; issue 363 delegated identity; mutation after the last identity check; a transaction across all six sibling writes

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: no candidate met all four requirements: an explicit promise, reachability through the supported runtime or accepted source, an observable result, and a minimal deterministic reproducer. The round-14 strict source, including literal `%b` and `<br>`, decoded back to all 15 exact physical lines. Exhaustive checks covered 137,257 single-line codec strings, 16,104 line sequences with empty, leading, trailing, adjacent, Unicode, delimiter, and escape spellings, and 671,846 controller/renderer table variants without a mismatch. Unicode `splitlines()` can segment U+2028, but the governed decoder receives one LF-delimited record and restores that code point exactly; no supported consumer loses a line, and issue 369 owns downstream file reading. Renderer-only foreign risk ids cannot reach a receipt because the controller checks the receipted risk set first. R13's custom binary short-write stream remains outside standard CPython 3.12 stderr behavior; the current loop still drains positive short writes, and the real stderr path exits 2. Pre-codec split-only behavior is unreleased and has no compatibility promise. Mutation after the final identity check and a transaction across all six writes remain explicit negative space; each sibling replacement is atomic and the required follow-up check exposes mixed currency. The six source/view pairs, focused 403-test batch, root 160-test suite, pinned Node 26.6.0 926-test suite, Promise 14 of 14, Phylax, Ephoros, and Hypomnema passed. Brevitas is excluded for this completeness record, no performance claim selects Metron, the live controller remains pinned to v5.12.1, step 3 owns checked-in v5.13.1 proof, issue 453 owns report-byte binding, issue 369 owns downstream consumption, and issue 363 owns delegated identity.

## audit-record-schema-timestamp-synopsis, step 3, round 1 -- 2026-08-24T08:35:33Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the recorded non-Solidity waiver; live-controller or `.hexaemeron` mutation; credentials, network, and issue state; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier implementation; mutation after the last identity check; a transaction across all six synopsis writes

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | .github/workflows/janus.yml, .github/workflows/lazarus.yml, .github/workflows/pandects.yml | The permanent prefix guard required full Git history, so three root-suite jobs carried unreceipted checkout changes that contradicted A10 and the ask-first CI boundary; the release surface could not reconcile to the accepted study. | fixed in 9acaaf4be600e87b0348b965a5c924e60877d0d4; 927 tests, three parent assertions, zero errors; Elenchus guarded |
| S3-R1-02 | low | plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/runbook.md | All four source-bound Elenchus commands hid `{report}` inside one `--call` string, so a fix carrying tests returned `inconclusive` before the declared runner executed instead of producing its test verdict. | fixed in e9ca4ecb74f8b5de2a312c9296723c3c4eed5b00; 928 tests, one parent assertion, zero errors; Elenchus guarded |
| S3-R1-03 | low | plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/proof.md | The fixed-input table retained the pre-fix release-runbook SHA and the gate table retained only the superseded `--call` invocation, so the claimed byte-current release proof contradicted the committed runbook and omitted the successful corrected exact-argv gate. | fixed in 7ef0df81646fd517b464321aa8d0349e57859a5b; 929 tests, three parent assertions, zero errors; Elenchus guarded |

Leads not pursued: no fourth candidate met the promise, supported-reachability, observable-consequence, and deterministic-reproducer threshold. The real checked-in v5.13.1 controller accepted `null` and all four verdicts, stored the five new leaves, preserved a middle legacy record missing all five, and rejected the exact 30-case matrix without state or ledger drift. The history-free fixture carries 14 exact commit and tree objects occupying 5,070 decoded bytes and no audit blobs; carrying full blobs was rejected as needless duplication. The concrete-path `--call` form remains valid for manual suite execution, but the shipped placeholder form was a finding because Elenchus refused it before testing. The release proof now binds runbook SHA-256 `07003da0855c317d78d00f3287d6fa38eefa1b49dfe6f3037dcda60fc2236998` and retains the historical failed gate beside the corrected exact-argv guarded gate. The first two root-only guards initially returned `passed`, so their final guards were moved into the commanded suite before the fixes were re-signed. Metron attributed one concurrent multi-minute root run to host contention: the same 160-test command then took 8.898s and 8.862s against an 8.646s baseline, while the witness module took 0.007s, so no performance edit was warranted. The accepted study's three B011 table diagnostics and four Horos synopsis notices remain recorded non-gates rather than defects. All six prefix offsets, source and synopsis hashes, budgets, legacy leaves, verdicts, refusal hashes, and release surfaces otherwise reconciled; the focused 403-test batch, fixed-tree pinned Node 26.6.0 929-test suite, Promise 14 of 14, Protasis, Phylax, Ephoros, Hypomnema, Horos, Imprimatur, signatures, trailers, and diff gates passed. Issues 369, 453, and 363 remain with their named owners.

## audit-record-schema-timestamp-synopsis, step 3, round 2 -- 2026-08-24T09:09:31Z

Audit schema: fiat-audit-round/v1

Covered: legacy-prefix-integrity=reviewed; schema-bypass=reviewed; risk-id-drift=reviewed; timestamp-ambiguity=reviewed; verdict-loss=reviewed; legacy-parser-confusion=reviewed; synopsis-drift=reviewed; lead-omission=reviewed; partial-write=reviewed; path-boundary=reviewed; horos-self-defeat=reviewed; self-hosting-overclaim=reviewed; frontier-drift=reviewed

Not checked: Solidity-only Pashov X-Ray and Auditor pair under the recorded non-Solidity waiver; live-controller or `.hexaemeron` mutation; credentials, network, GitHub Actions execution, and issue state; issue 453 report-byte and commit binding; issue 369 downstream synopsis consumption; issue 363 frontier implementation; mutation after the last identity check; a transaction across all six synopsis writes; Windows and runtimes without descriptor-relative open support

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: no candidate met the explicit-promise, supported-input, observable-consequence, and deterministic scaffold-free reproducer threshold. All 14 witnessed commit and tree objects, 5,070 decoded bytes, matched `git cat-file` for their fixed object ids; their paths resolved all six protected files to the Git blob ids, while a changed prefix with re-blessed local metadata still failed membership. The 12 witness and release cases passed on Darwin CPython 3.9.6 and 3.12.13, and a real depth-one clone without `ced4e6f439021b7509833ed5da66348c86d22f01` passed the 160-test root suite. The declared CI matrices use Ubuntu CPython 3.9, 3.11, and 3.13; Windows and runtimes missing `O_NOFOLLOW`, `O_DIRECTORY`, `O_NONBLOCK`, or descriptor-relative open are not promised and fail closed. `shlex.split` placed the sole `{report}` at argv index 7; the direct `npx --yes --package=node@26.6.0 -- python3.12 ... {report}` form gave its child Node v26.6.0, and the exact pinned Elenchus replay at `e9ca4ecb74f8b5de2a312c9296723c3c4eed5b00` returned `guarded` after 928 tests with the sole parent assertion failure and no errors or skips. The fixture, release runbook, controller, generator, receipted study, source, and synopsis digests recomputed to the proof values; the historical disposable repository was not retained, so its run-local state, ledger, temporary commit, and entry hashes remain signed proof evidence rather than independently reusable inputs. Its five monotonic rounds, 30 refusal classes, four non-null verdicts, explicit-null legacy row, signature and trailer assertions, clean close, and stated boundary claims contain no conflicting value. The permanent controller, parser, currency, prefix, refusal, risk, timestamp, verdict, partial-write, path, Horos, release-version, Promise, and frontier guards cover all 13 registered risks; no mock-only, altered-fixture, SHA-1 collision, nonstandard stream, unsupported-platform, or post-final-check race lead supplied an actual shipped failure. All six source/view pairs and protected prefixes matched, a fresh Horos scan had 99 hard entries and no synopsis path, and the focused 403-test, root 160-test, pinned Node 26.6.0 929-test, Promise 14-of-14, Protasis, Phylax, Ephoros, Hypomnema, Imprimatur, signature, trailer, and diff gates passed. The accepted study's three B011 two-column-table diagnostics remain recorded non-gates; issues 369, 453, and 363 retain their named owners.
