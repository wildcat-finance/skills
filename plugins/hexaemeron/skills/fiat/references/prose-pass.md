# Prose pass

Everything a human will read ships in one plain voice, with the AI tells
stripped. Code stays untouched; this phase is words only. Both masks are
bundled in this plugin, so no external install is involved.

## Scope

- `README.md`, runbooks, glossaries, primers, and any other prose file the
  step created or changed (`docs/**`, top-level `*.md`, NatSpec-adjacent
  prose files -- not code comments).
- The committed copies of the study and runbook, when this step ships them.
- The PR title and body for this step. Draft them now and stash at
  `.hexaemeron/steps/<n>/pr.md` for the push phase to use verbatim.
- On the last step, the run-level title and body as well, stashed at
  `.hexaemeron/run-pr.md`. That one carries a `## Carried forward` section
  holding one fenced `carryover` block, one row per item the run leaves
  unfinished, each row disposing of its item in a filed issue, the existing
  issue that already carries it, or a stated reason it earns neither. A run that
  leaves nothing writes the single row `none | none | <why nothing is carried>`.
  `done integrate` refuses the run without it, and prose alone no longer
  satisfies it; the shape and its reasoning are in
  [push-discipline.md](push-discipline.md).

## Order

1. **Record.** Apply `hypomnema` (read `$PLUGIN_ROOT/skills/hypomnema/SKILL.md`)
   before touching a word: decide which decisions this step made that earn a
   written reason, put each in the file its rules name, and run its pointer
   lint over the changed documents so nothing shipped links to something
   absent. A record pointing nowhere fails the phase the same way a hard lint
   hit does.
2. **Lint.** Run the bundled script on each file:
   `python3 "$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py" <file>`.
   Hard hits are defects: rewrite the sentence, never substitute a
   neighbour from the same family. Keep every qualifier that carries
   scope, risk, or legal meaning.
3. **Voice.** Apply the `vulgate` mask (read
   `$PLUGIN_ROOT/skills/vulgate/SKILL.md` and follow it -- `$PLUGIN_ROOT`
   as defined in the entry skill): neutral
   register unless the document's content demands serious. The mask changes
   surface only; every fact, number, commitment, and caveat survives
   verbatim, and the spelling convention stays consistent.
4. **Re-lint.** The mask can reintroduce a marker; run the lint once more
   and settle any new hits.

## Task-issue closing comment

When `init --task-issue` bound an issue, draft its closing comment during this
phase at `.hexaemeron/task-issue-comment.md`. Keep the exact issue URL, pull
request URL, identifiers, status, and unresolved work in its protected
inventory. The integration pull request URL and final status may not exist yet;
leave explicit labelled fields for them rather than guessing either value.

The publishable comment follows the root issue rule in this exact order:
`Sapheneia -> Imprimatur -> Vulgate -> Imprimatur`. Sapheneia shapes the whole
comment, the first Imprimatur pass clears defects, Vulgate changes register
without changing content, and the second Imprimatur pass checks the exact final
bytes. Compare the protected inventory after every semantic pass. At
integration, fill the labelled fields with the exact pull request URL and
status, carry forward every unresolved item, then rerun the complete sequence.
The prose receipt records that the draft work happened; it does not claim that
the later final bytes were posted or remotely read back.

## PR text

Title: plain statement of what the PR does, in-voice, no ticket-speak.
Body: what changed and why, a pointer to the audit file and the stacked PR,
and how to run the step's proof (test command, demo path). Do not invent an
issue reference; include one only when the user independently supplied it.
Both title and body go through the same lint-voice-relint order as the files.

## Receipt

Count the files rewritten (PR text counts as one) and pass the skills that
actually ran -- the receipt rejects a list missing either configured skill:

```text
hexctl done prose --files <n> --skills hexaemeron:imprimatur,hexaemeron:vulgate
```

Do not report either skill as applied when it was not; run it or halt.
