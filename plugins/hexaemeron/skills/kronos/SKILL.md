---
name: kronos
description: >-
  Rank the held Next Fiat jobs across explicitly in-scope, non-mature skills,
  select the most worthwhile job out of 100, set one durable goal or loop,
  run that job through Fiat, then repeat until no eligible frontier remains.
  Use only when the user explicitly asks for Kronos or for a repeated ranked
  Fiat frontier loop. Do not use it for one ordinary Fiat delivery.
metadata:
  version: "0.0.0"
---

# Kronos

Read [EVOLUTION.md](EVOLUTION.md). Kronos is terminal by design; that maturity
blocks attempts to improve Kronos itself, not the frontier loop it controls.

Named for the old knot between Kronos and Chronos: a sickle for taking the
ripest frontier first, and a clock that keeps Fiat moving until the field is
bare.

> Highest first, then Fiat runs.
>
> Kronos cuts till work is done.

## Loop

1. Resolve the scope from the user's named directories or repositories. If no
   narrower scope was named, use the current marketplace checkout.
2. Find every `EVOLUTION.md` in scope. Exclude:
   - Kronos itself;
   - vendored or third-party skills;
   - a ledger whose `Frontier status` is `mature`;
   - a ledger whose `Next Fiat job` is `None -- mature` or absent.
3. Score each remaining held job out of 100:
   - material user or protocol impact: 40;
   - evidenced urgency or defect severity: 25;
   - readiness of inputs and acceptance conditions: 20;
   - leverage for other in-scope skills: 15.
   Show the score and one-sentence basis for every candidate. Do not invent
   work to fill the list.
4. Select the highest score. Break a tie by impact, then readiness, then the
   order in which the ledgers were found.
5. When the runtime provides a durable goal facility, create one goal whose
   objective is to repeat steps 1-8 until no eligible frontier remains. When
   it does not, keep the same loop in the current run. Never create one goal
   per skill.
6. Read the selected skill's canonical instructions, its ledger, and Fiat's
   `SKILL.md`. Invoke Fiat with the held Next Fiat job byte for byte.
7. Let Fiat finish its complete terminal path: implement, validate, stage,
   commit, push, merge, branch cleanup where permitted, and issue closure.
   A PR merely opened is not a completed iteration.
8. Require the completed frontier run to update that skill's ledger under
   `VERSIONING.md`: evolution advances once and the held job is replaced, or
   the frontier becomes mature. Rescan from disk, rerank from scratch, and
   repeat.

Stop successfully when no eligible ledger remains. If Fiat halts on a genuine
external blocker, preserve the durable goal and report that blocker; do not
skip to a lower-scoring job to make the loop look busy.

## Hard rules

- Never edit, implement, audit, or rewrite a target itself. Fiat owns the work.
- Never score a mature, terminal, vendored, or out-of-scope skill.
- Never alter a held Next Fiat job before its exact frontier job completes.
- Never continue merely because the loop can continue. No eligible frontier
  means the goal is complete.
