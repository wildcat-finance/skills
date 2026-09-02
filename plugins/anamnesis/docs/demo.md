# The whole path, over the pilot

One command runs everything the member does, over the committed pilot:

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo \
  --specimen plugins/anamnesis/specimens/pilot
```

It prints five things and refuses rather than continuing if any of them fails.

1. **Two fresh builds agree.** The pilot is built twice into fresh temporary
   directories and compared: the release id, the file set, and every component
   byte. Comparing only the id would pass a build whose components drifted
   while their digests stayed in the manifest.
2. **The committed release verifies**, and its id equals the one a fresh build
   produces. If those differ, the release in the tree is not the release the
   inputs produce, and the command says so.
3. **The Elenchus view** is read for one query. It carries analogues and a
   `verdict` of `null`, because the projection has no field a verdict could
   occupy.
4. **The Synkrisis view** is read for one cohort. It carries its denominators,
   its exclusions and its unknowns, so the included count cannot be read as a
   share of anything the corpus did not see.
5. **A baseline, not a threshold.** Wall-clock duration and peak resident
   memory are printed. No budget is declared for either, so neither gates
   anything; they exist so a later change has something to be compared against.

## What the demo does not establish

That the corpus is complete, that any preserved finding was real, that any
recorded remedy worked, or that the pilot's 41 findings are the right 41 to have
kept. It establishes that the release rebuilds, that both views are closed, and
that restricted material reaches neither.

## The two conformance commands

The design record names these exactly, and each writes one closed report:

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py measure-release \
  --release plugins/anamnesis/specimens/pilot/release \
  --report .hexaemeron/reports/anamnesis-member-seed-release-byte-cap.json

python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py verify-rebuild \
  --specimen plugins/anamnesis/specimens/pilot \
  --report .hexaemeron/reports/anamnesis-member-deterministic-rebuild.json
```

## Reading a refusal

Every refusal names the rule that fired. Two examples are committed under
[specimens/pilot/events/](../specimens/pilot/events/): one stream of admitted
sources, and one refusal recording rule `A057`, a digest mismatch, with the
record it fired on, the policy version and a correlation id derived from the
policy bytes rather than a clock.
