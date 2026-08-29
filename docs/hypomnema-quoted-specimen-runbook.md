# Runbook: Tell a quoted specimen from a live runbook pointer

Derived from the study of the same name. Two steps, one pull request each,
stacked on `fiat/500-h003-must-tell-a-quoted-specimen-from-a-live` off `main`
at `5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`.

Both steps run under the same Elenchus runner contract, stated in each step's
`Tests` field: the focused suite emits one fresh report and Warden uses that
command, that format and that file for any fix it claims.

## Step 1: Scaffold: commit the study and runbook

**Goal.** Put the reviewed specification in the tracked tree before any behaviour changes.
**Entry.** The run branch `fiat/500-h003-must-tell-a-quoted-specimen-from-a-live` at `5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`, clean tree.
**Exit.** The two committed documents pass their own checks, the prose gates accept them, and the tree stays green:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/hypomnema-quoted-specimen-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/hypomnema-quoted-specimen-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/hypomnema-quoted-specimen-study.md docs/hypomnema-quoted-specimen-runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** `docs/hypomnema-quoted-specimen-study.md`, `docs/hypomnema-quoted-specimen-runbook.md`, and `.horos/boundary.json` regenerated last if the two tracked paths move it.
**Prose.** Brevitas is run over both documents and its result recorded rather than gated. It reports B010 and B001 on the runbook, which a two-step specification cannot satisfy, and two B022 line-start matches on the study where a wrapped line begins with the word `reading`. The shipped `docs/hypomnema-runbook-shape-check-runbook.md` carries the same two structure codes in the tracked tree today, and the study's bytes are frozen by its receipt, so neither is repairable in this step. Imprimatur reports no defect on either document.
**Tests.** No new behaviour test: the document checks and both suites are the regression net. Elenchus runner contract for this step, test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `.elenchus/hypomnema-quoted-specimen-step-1.json`.
**Disciplines.** phylax: none, two Markdown documents open no execution boundary. ephoros: none, nothing here runs unattended. metron: none, no behaviour changes so the recorded baseline cannot move. elenchus: none, no failure is in hand at this step. hypomnema: the tracked study is the standing source the step 2 ledger row points back to.

## Step 2: Skip the quoted specimen, keep the live pointer, record the generation

**Goal.** Make the Markdown H003 pass ignore a `runbook:` keyword that sits inside an inline code span, leave every other case exactly as it is, and record the behaviour once on the Hypomnema ledger.
**Entry.** Step 1's green exit state, on the branch the controller cuts from step 1.
**Exit.** The append-only ledger the checker could not read is clean, the documented tree command still finds nothing, both budgets hold, and every repository gate passes:

```bash
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py audit/AUDIT.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/hypomnema/SKILL.md plugins/hexaemeron/skills/hypomnema/EVOLUTION.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/hypomnema/SKILL.md plugins/hexaemeron/skills/hypomnema/EVOLUTION.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
```

**Files.** `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` for the span scan and the H003 skip, `plugins/hexaemeron/tests/test_hypomnema_checker.py` for the guards, `plugins/hexaemeron/skills/hypomnema/SKILL.md` for the sentence that states the rule, its Promise boundary clause and the `4.4.0` frontmatter version, `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md` for the `hypomnema-v4.4.0` generation row, and `.horos/boundary.json` regenerated last if the tracked tree moves it.
**Tests.** Guards in the existing `Runbooks` class of `plugins/hexaemeron/tests/test_hypomnema_checker.py`, one per register id the step covers: a wholly quoted pointer earns no H003, a bare keyword with a backticked path still earns one, an unmatched run opens no span so a later pointer still fires, a pointer on a line that opens a span left unclosed still fires, the two real ledger specimens go clean, the YAML cases stay byte-identical, and every existing case is retained. Each guard is run against the unfixed parent first and must be red there. Elenchus runner contract for this step, test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `.elenchus/hypomnema-quoted-specimen-step-2.json`.
**Budget.** The documented tree command stays at or under 0.35s against the recorded 0.26s to 0.28s baseline, and a single line carrying 30,000 backtick runs completes in under one second. Both are measured before and after and recorded in the round.
**Demonstration.** The exit's first command is the demo path from the study's problem statement: the checker over `audit/AUDIT.md`, which reports two findings at the entry and none at the exit.
**Disciplines.** phylax: the span scan is a second pass over untrusted document text, so it stays a bounded linear pass with no recursion, no filesystem access and no catastrophic pattern. ephoros: none, a lint invoked from a terminal has no unattended question, as item 8 of the study records. metron: the budget above is measured with the exact documented command before and after. elenchus: the two H003 findings are the failure in hand, each guard is proved red against the unfixed parent before the fix lands, and any round finding follows the same order. hypomnema: the discriminator and the deferred scope decision are recorded once, in the `hypomnema-v4.4.0` row, and not in an ADR.
