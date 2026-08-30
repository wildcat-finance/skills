## Step 1, round 1 -- 2026-08-30T01:12:00Z

Audit schema: fiat-audit-round/v2

Covered: prompt-leak=reviewed; packet-write=reviewed; corpus-drift=reviewed; answer-binding=not-applicable; missing-answer=not-applicable; answer-shape=not-applicable

Not checked: the three not-applicable concerns all sit on `tally`, which step 2 builds; nothing in this step reads an answers file. The emitted packet was not handed to a graded context, so this round establishes what the bytes carry and not how a context reads them.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | `tests/router_selection_driver.py` | `emit` wrote the manifest after the prompts, which is what makes a part-written packet refusable by `tally`, but nothing stated the ordering and no guard held it. A refactor reversing the two would turn a half-emitted packet into one that reads as complete. | fixed and guarded in this round |

Leads not pursued: `CASE_ID` hard-codes the `RS-` prefix, so a corpus adopting another id grammar would refuse rather than emit, which is fail-closed and wrong only if the grammar changes; `render_prompt` replaces every `{request}` occurrence where the pinned template carries exactly one, so a second placeholder would receive the same request rather than refuse; `emit` does not refuse an output directory inside the repository, which would leave an untracked packet in a working tree rather than damage anything. Each is a bounded limit of a command a person runs and watches, none is reachable from the corpus on disk, and closing any of them would add a refusal path with no failure behind it.

## Step 1, round 2 -- 2026-08-30T01:19:00Z

Audit schema: fiat-audit-round/v2

Covered: prompt-leak=reviewed; packet-write=reviewed; corpus-drift=reviewed; answer-binding=not-applicable; missing-answer=not-applicable; answer-shape=not-applicable

Not checked: the same three concerns remain `tally`'s, which step 2 builds. No graded context was driven against the emitted packet in this round either, so what a context does with the bytes is still outside what this round establishes.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: round 1's three leads stand unchanged and for the same reason. Round 1's fix was re-driven rather than reread: appending a hint to every rendered prompt fails the leak guard, and moving the manifest write above the prompt loop fails the ordering guard, each failing exactly one case and naming it. The three lints exit 0 on the fixed tree and the root suite reports 510 of 510, up from the 495 on the base by the fifteen this step adds.

## Step 2, round 1 -- 2026-08-30T01:41:00Z

Audit schema: fiat-audit-round/v2

Covered: answer-binding=reviewed; missing-answer=reviewed; answer-shape=reviewed; corpus-drift=reviewed; prompt-leak=reviewed; packet-write=reviewed

Not checked: whether an answer a graded context actually returns parses into the closed vocabulary without an operator editing it. The driver takes a sheet, and how that sheet is assembled from context output is outside it. The demonstration in step 3 exercises one real set of answers rather than establishing that shape in general.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `tests/router_selection_driver.py` | `read_answers` parsed the sheet with a plain `json.loads`, so a case answered twice kept the second value and dropped the first silently. A sheet assembled from several contexts is where a repeated id arises, and the dropped answer would be invisible in the recorded score. | fixed and guarded in this round |

Leads not pursued: `score` accepts either refusal form against a `refuse` expectation rather than requiring the recorded `reason`, so a case expecting `ambiguous` passes on `refuse:uncovered`. Being stricter would make a claim the corpus does not support: [#697](https://github.com/wildcat-finance/skills/pull/697) recorded that `RS-33` "names no reproduction and no change, so a reader could hold that neither row matches and the refusal owed is `uncovered` rather than `ambiguous`", and left both readings open. Tightening this is a corpus decision about what a refusal reason means, not a driver defect, and it would silently change recorded scores. `tally` rewrites the corpus with `json.dumps(..., indent=2)` and no `sort_keys`, which preserves insertion order and matches the committed formatting; the guard compares every byte outside `runs` rather than trusting that.

## Step 2, round 2 -- 2026-08-30T01:46:00Z

Audit schema: fiat-audit-round/v2

Covered: answer-binding=reviewed; missing-answer=reviewed; answer-shape=reviewed; corpus-drift=reviewed; prompt-leak=reviewed; packet-write=reviewed

Not checked: the same boundary as round 1. How a sheet is assembled from what graded contexts return is outside the driver, and step 3 exercises one real set rather than establishing the shape in general.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: round 1's two leads stand for the same reasons. Round 1's fix was re-driven rather than reread: removing the `object_pairs_hook` fails the duplicate guard and names the repeated case. Three further mutations were driven against the round-1 tree and each failed exactly one case, naming it: disabling the corpus-digest comparison, disabling the answer-vocabulary check, and moving the manifest write above the prompt loop. The three lints exit 0 and the root suite reports 524 of 524.

## Step 3, round 1 -- 2026-08-30T02:03:00Z

Audit schema: fiat-audit-round/v2

Covered: prompt-leak=reviewed; packet-write=reviewed; corpus-drift=reviewed; answer-binding=reviewed; missing-answer=reviewed; answer-shape=reviewed

Not checked: whether the 38 committed answers are the ones those contexts would return again. They are a record of one grading, not a claim about a rerun, and the driver reproduces the recorded block from them rather than establishing that a fresh grading agrees. Nothing here drove a graded context.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the refusal-reason leniency from step 2 round 1 stands unchanged, and the demonstration exercises it: `RS-34` is recorded as answered `refuse:uncovered` against an expectation of `phylax`, which fails on the canonical name rather than on the reason, so the leniency does not affect this result either way. ADR-051 takes the next free number against `origin/main` at this branch's cut, which is the collision surface [#798](https://github.com/wildcat-finance/skills/issues/798) owns; the record says so in its own status section rather than leaving a reader to find it. The demonstration guard was driven rather than reread: changing one committed answer fails it and names the block mismatch.
