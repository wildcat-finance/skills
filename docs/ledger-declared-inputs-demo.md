# Demonstration: a held job's declared inputs on a Kronos pass

The study for [skills#1276](https://github.com/wildcat-finance/skills/issues/1276)
states a demo path and the output it must produce. This is the output that path
produced, recorded as it was observed rather than written from the design.

Both runs are rank-only passes into a throwaway scoreboard under the system
temporary directory. Neither writes to `refs/heads/kronos/state`, neither
touches a governed ledger, and neither dispatches Fiat.

## The path

```bash
python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py record \
  --scoreboard <tmp>/.kronos/scoreboard.jsonl --root <root> < pass.json
python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py show \
  --scoreboard <tmp>/.kronos/scoreboard.jsonl
```

## One declaring ledger and one silent one

The fixture root holds the two specimen ledgers the reader's own tests use:
`ledger-with-declaration.md`, which declares three inputs, and
`ledger-without-declaration.md`, which declares none. Both are under
`plugins/hexaemeron/tests/fixtures/kronos/`.

```bash
kronos=plugins/hexaemeron/skills/kronos/scripts/kronos.py
fixtures=plugins/hexaemeron/tests/fixtures/kronos
tmp=$(mktemp -d)
fixture="$tmp/fixture"
mkdir -p "$tmp/.kronos" "$fixture/declaring" "$fixture/silent"
cp "$fixtures/ledger-with-declaration.md" "$fixture/declaring/EVOLUTION.md"
cp "$fixtures/ledger-without-declaration.md" "$fixture/silent/EVOLUTION.md"
```

The pass scores both candidates and selects the higher one. Its two bases say
where each readiness score came from, which is what the loop's step 3 now asks
for.

```json
{
  "scope": "fixture root",
  "mode": "full",
  "rank_only": true,
  "selected": "declaring",
  "candidates": [
    {"skill": "declaring", "ledger": "declaring/EVOLUTION.md",
     "impact": 30, "urgency": 15, "readiness": 12, "unblocks": 9,
     "basis": "Readiness read from the three inputs the ledger declares."},
    {"skill": "silent", "ledger": "silent/EVOLUTION.md",
     "impact": 20, "urgency": 10, "readiness": 8, "unblocks": 5,
     "basis": "Readiness inferred from the held job's prose; this ledger declares nothing."}
  ]
}
```

Observed output:

```text
$ python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py record --scoreboard $tmp/.kronos/scoreboard.jsonl --root $fixture < $tmp/pass.json
rank-only pass 1 recorded: 2 candidate(s), selected declaring

$ python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py show --scoreboard $tmp/.kronos/scoreboard.jsonl
pass 1  full  fixture root  (rank-only)
  *  66  declaring                impact=30 urgency=15 readiness=12 unblocks=9
      Readiness read from the three inputs the ledger declares.
      declared: 3 input(s)
        archive-rpc | endpoint | absent | An archive JSON-RPC endpoint for the capture window.
        release-key | credential | unknown | A signing key nobody has confirmed is to hand.
        reviewer | person | available | The maintainer who reviews the release.
     43  silent                   impact=20 urgency=10 readiness=8 unblocks=5
      Readiness inferred from the held job's prose; this ledger declares nothing.
      declared: none
1 pass(es), 0 with drift
```

One declaration and one `declared: none`, which is the study's first criterion.
The three declared rows print in the four fields the ledger wrote them in, so a
reader comparing the record against the ledger reads one spelling rather than
two.

## The real checkout

The second run uses a pass nobody invented for this document. The filing cites a
rank-only pass recorded on `refs/heads/kronos/state` at
`b8bbaa62c28e636ba8608fa7794335c339c2729b`, carrying 21 candidates with the
scores and bases a real ranking produced. That line is replayed as a fresh pass
document with the derived fields stripped, so `record` recomputes each held-job
hash and each declaration against the ledgers on disk today.

```bash
kronos=plugins/hexaemeron/skills/kronos/scripts/kronos.py
tmp=$(mktemp -d)
mkdir -p "$tmp/.kronos"
git show b8bbaa62c28e636ba8608fa7794335c339c2729b:scoreboard.jsonl \
  | python3 -c '
import json, sys
keep = {"skill","ledger","basis","total","parked","impact","urgency","readiness","unblocks"}
d = json.loads(sys.stdin.readline())
json.dump({
  "scope": d["scope"], "mode": d["mode"], "selected": d["selected"],
  "rank_only": d["rank_only"], "ungoverned": d["ungoverned"],
  "candidates": [{k: v for k, v in c.items() if k in keep} for c in d["candidates"]],
}, sys.stdout)
' > "$tmp/pass.json"
```

Observed output:

```text
$ python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py record --scoreboard $tmp/.kronos/scoreboard.jsonl --root . < $tmp/pass.json
rank-only pass 1 recorded: 21 candidate(s), selected fiat

$ python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py show --scoreboard $tmp/.kronos/scoreboard.jsonl
pass 1  full  wildcat-finance/skills marketplace checkout  (rank-only)
  *  91  fiat                     impact=36 urgency=21 readiness=19 unblocks=15
      Delegation task identities can retain a stale issue number, so the run record of every other frontier delivery can be mislabelled, and the acceptance conditions are four executable checks.
      declared: none
     83  dokimasia                impact=34 urgency=22 readiness=19 unblocks=8
      A shipped 202-of-261 coverage figure rests on a confirmation boolean anything with write access can set, so the record cannot distinguish a reviewer from a script.
      declared: none
     71  tabularium               impact=33 urgency=13 readiness=13 unblocks=12
      Compound v3 Phase 1 adds a real venue to the credit-event record Probitas underwrites from, but bundles a schema version, four mappings, a mined witness and an offline specimen into one run.
      declared: none
     70  ephoros                  impact=26 urgency=17 readiness=19 unblocks=8
      E005 already reads the TypeScript surface through the shared masked lexer, so extending E001-E003 reuses shipped machinery against a known interpolated logger message in the pinned app clone.
      declared: none
     69  probitas                 impact=34 urgency=17 readiness=11 unblocks=7
      An unattributable secondary-market close leaves a borrower's debt ledger incomplete, which is the underwriting failure that matters, but the current refusal is itself evidence the attribution input may not exist.
      declared: none
     67  hypomnema                impact=24 urgency=14 readiness=19 unblocks=10
      Half of skills#461 already ships, the remaining half has five explicit acceptance conditions, and duplicate decision homes affect every ADR and governed ledger in the repository.
      declared: none
     65  alexandria               impact=30 urgency=14 readiness=10 unblocks=11
      Live provider boundaries would firm up the capture layer Tabularium and Probitas read, but the job needs two live providers and credentials a delivery run does not control.
      declared: none
     64  metron                   impact=22 urgency=16 readiness=19 unblocks=7
      The budget check reads a run file no shipped tool produces, so the measurement is whatever a caller wrote; the recorder is small and its acceptance is fully mechanical.
      declared: none
     64  pandects                 impact=25 urgency=15 readiness=15 unblocks=9
      Echidna and Medusa campaign results survive only as audit prose today, and the Foundry recorder gives the shape to widen, though both engines must be installed to run.
      declared: none
     63  berean                   impact=30 urgency=13 readiness=12 unblocks=8
      The Wildcat-facing agent still answers from a demonstration corpus, but grounding it needs a Wildcat documentation and market-read capture that has not been taken.
      declared: none
     62  hermes                   impact=25 urgency=16 readiness=16 unblocks=5
      58 of 120 documented gas rules cannot be selected as candidates, a counted defect with a named starting rule in STO-12.
      declared: none
```

That is one continuous output, split here only because a single fence of 72
lines exceeds the structural lint's cap. Nothing between the two halves is
elided; the second picks up at the twelfth row.

```text
     62  synkrisis                impact=26 urgency=16 readiness=12 unblocks=8
      The rule catalogue is proved only on constructed records, and validating it needs captured production run observations whose availability is not established.
      declared: none
     56  anamnesis                impact=22 urgency=11 readiness=16 unblocks=7
      A hand-picked 41-finding seed has no declared scope policy, and either acceptance branch, a policy field or a decision record, is reachable.
      declared: none
     55  lazarus                  impact=20 urgency=11 readiness=18 unblocks=6
      Empty blocks have no receipt-witness representation, and the acceptance turns on one precise constant, Ethereum's empty trie root.
      declared: none
     55  vulgate                  impact=21 urgency=13 readiness=14 unblocks=7
      Content parity is asserted by model judgement rather than measured, so the voice mask ships without a repeatable check over facts, commitments and caveats.
      declared: none
     53  janus                    impact=24 urgency=11 readiness=12 unblocks=6
      Host-neutrality of the manifest format is asserted from one adapter, but the job does not name which second callback model to build against.
      declared: none
     52  imprimatur               impact=22 urgency=16 readiness=8 unblocks=6
      The v1 holdout is spent and its scores cannot support tuning, but v2 needs two fresh blind human annotations at kappa 0.80, which a delivery run cannot produce alone.
      declared: none
     52  brevitas                 impact=21 urgency=12 readiness=12 unblocks=7
      Forward-testing needs a held cross-model corpus of x-ray, auditor, gas, invariant and diff-review outputs that is not shown to exist yet.
      declared: none
     52  homologia                impact=20 urgency=10 readiness=17 unblocks=5
      Mirror execution has precise mechanical acceptance on argv pinning and bounded IO, but nothing downstream consumes a verdict the skill still does not produce.
      declared: none
     50  lemma                    impact=16 urgency=10 readiness=19 unblocks=5
      Adding return types and state mutability to ABI validation is tightly scoped and immediately buildable, but closes a narrow gap.
      declared: none
     47  sapheneia                impact=20 urgency=10 readiness=11 unblocks=6
      The ten rules are unreconciled against cross-model evidence, but building and publishing the corpus needs multi-model access a single run does not have.
      declared: none
    ungoverned: fizz
    ungoverned: solidity-auditor
    ungoverned: x-ray
1 pass(es), 0 with drift
```

Twenty-one rows, twenty-one `declared: none`, and no row printing a
declaration. That is the true state of `main`: every one of the 27 governed
ledgers carries the option and none has taken it. Before this run the same fact
had no representation at all, so a reader could not tell an absent declaration
from a reader that never looked.

The three readiness scores the filing quotes are visible above and unchanged:
`probitas` 11, `alexandria` 10, `imprimatur` 8. Each was inferred from its held
job's prose, and none of the three ledgers says so, which is the gap the block
exists to close.

## What this does not establish

The two runs show that a declaration is read where a ledger carries one and
reported as absent where it does not. They establish nothing about truth. No
declared endpoint was called, no declared credential was looked for, and no
declared person was asked. A note is its ledger owner's claim, weighed by the
ranking as evidence and never followed as an instruction.

The second run replays recorded scores against today's ledgers, so it
demonstrates the reader rather than ranking the frontier afresh. Its selection
of `fiat` is the selection that pass recorded on 2026-09-05, not a claim about
what should run next.
