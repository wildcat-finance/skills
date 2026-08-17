# Notice

This skill absorbs material from **slopkit** by ehmo, used under the MIT licence.

- Upstream: https://github.com/ehmo/slopkit
- Version absorbed: 1.4.1
- Absorbed: 11 August 2026

## What was taken

From `skills/slopbeth/scripts/deslop_lint.py`:

- `FILLER_PHRASES` and `ABSTRACT_WORDS` are in `lexicon/hard.json` under the `brochure` family
- `GENERIC_CLOSERS` is in `lexicon/hard.json` under `closer`
- `STRUCTURE_PATTERNS` (`not_just_but`, `whether_or`, `from_to`, `at_core`, `generic_here`) is in `lexicon/structural.json`, rewritten with per-pattern severity and a signal-only tier
- The formatting counters (emphasis, emoji, dash, title-case headings, triads) are in `lexicon/structural.json`
- The cadence idea (repeated sentence openers) is in `cadence_signals()`

From `skills/slopgent/scripts/comms_lint.py`:

- `INVENTED_CONFIDENCE` is in `lexicon/hard.json`, marked critical
- `PREAMBLE_CLOSER` is split across the `claude_tic` and `closer` families
- `DECORATIVE_JARGON` is in `consultant` and `brochure`
- `EMPTY_HEDGE` is in `empty_hedge`

From `skills/slopgent/SKILL.md`:

- The honesty ordering, the caveat guard, and the self-estimation rule are in `references/agent-replies.md`

From `skills/slopbeth/SKILL.md`:

- The preservation rules, evidence-bound mode, and Orwell ordering are in `references/rewriting.md`

## What was not taken

The benchmark corpora, the detector-panel logs, the PowerShell twins, the multi-agent installer, and the Node memory helper are all left upstream. None of them is needed to run a lexicon, and carrying 6.8 MB of benchmark JSONL into every organisation checkout is not worth it. If the benchmarks are ever wanted, they are still at the upstream repo.

## Deviations from upstream

Three, and they matter.

First, upstream ships one flat marker list where every hit counts the same. This skill separates hard bans from context-gated terms, because a lexicon that fires on "orthogonal" in a maths context is a lexicon that gets uninstalled.

Second, upstream counts quoted mentions as uses. This skill masks quoted spans by default, so a style guide can cite the terms it bans. `--strict` restores the upstream behaviour.

Third, upstream's structural patterns all score. Here `rule_of_three`, `whether_or`, and `from_x_to_y_sweep` are signal-only, because they cannot distinguish a rhetorical triad from a genuine three-item list and a rule that cannot tell should not fail a build.

## Dogfood result

Run against its own source, slopkit contains 79 instances of "load-bearing", the phrase that prompted this skill. They cluster in slopgent, where the term is used to name the caveats worth preserving. This is not a criticism of the upstream work, which is good. It is the substitution-drift argument in evidence: a wordlist cannot catch a phrase its own authors reach for while writing the wordlist.

---

## MIT License

Copyright (c) 2026 ehmo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
