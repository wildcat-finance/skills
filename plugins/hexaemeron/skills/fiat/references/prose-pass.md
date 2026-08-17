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

## Order

1. **Lint.** Run the bundled script on each file:
   `python3 "$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py" <file>`.
   Hard hits are defects: rewrite the sentence, never substitute a
   neighbour from the same family. Keep every qualifier that carries
   scope, risk, or legal meaning.
2. **Voice.** Apply the `vulgate` mask (read
   `$PLUGIN_ROOT/skills/vulgate/SKILL.md` and follow it -- `$PLUGIN_ROOT`
   as defined in the entry skill): neutral
   register unless the document's content demands serious. The mask changes
   surface only; every fact, number, commitment, and caveat survives
   verbatim, and the spelling convention stays consistent.
3. **Re-lint.** The mask can reintroduce a marker; run the lint once more
   and settle any new hits.

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
