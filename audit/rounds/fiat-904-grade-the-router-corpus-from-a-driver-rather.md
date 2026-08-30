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
