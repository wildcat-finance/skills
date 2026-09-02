# Edge-case audit record

A synthetic Warden-shaped record. The pilot's real sources carry none of these
shapes, so they are written here rather than pretended into the corpus.

## Step 1, round 1 -- 2026-08-20

Audit schema: fiat-audit-round/v2

Elenchus verdict: unguarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `src/one.py` | The first finding, fixed once here and again later | fixed in this round |
| S1-R1-02 | medium | `src/two.py` | A finding the reviewer did not accept | rejected: not reachable from any caller |
| S1-R1-03 | low | `src/three.py` | A finding whose risk was accepted rather than fixed | accepted: the alternative costs more than the exposure |
| S1-R1-04 | critical | `src/four.py` | A finding whose severity is outside the policy taxonomy | fixed in this round |
| S1-R1-05 | high | `src/one.py` | The same defect as S1-R1-01, reported separately | fixed in this round |

## Step 1, round 2 -- 2026-08-21

Audit schema: fiat-audit-round/v2

Elenchus verdict: inconclusive

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `src/one.py` | The first finding again; the first change did not hold | fixed in 9f2c1ab |
| S1-R2-01 | low | `src/five.py` | A finding nobody has answered | open |

## Step 1, round 3 -- 2026-08-22

Audit schema: fiat-audit-round/v2

Elenchus verdict: guarded

The round found nothing.

## Leads closed since

This heading owns no findings and must not become a round.
