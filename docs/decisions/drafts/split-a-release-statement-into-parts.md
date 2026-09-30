# Decision: Split a release statement past Ariadne's bounds into an index and parts

## Status

Accepted, 2026-09-30.

## Context

[#1892](https://github.com/wildcat-finance/skills/issues/1892) asks for a
statement for every release [#1888](https://github.com/wildcat-finance/skills/issues/1888)'s
limits admit: 16,384 components, 16,384 captures and a 134,217,728-byte
manifest. At base `150943da240837040478a76c3611d150fa04f2b6`, two limits bind:

- `alexandria.py statement` refuses a statement above 8,388,608 bytes
  (`MAX_STATEMENT_BYTES`, `statement.py`). That is Ariadne's input limit.
- Ariadne's gates 4 and 7 refuse a statement whose object keys exceed 262,144
  characters. An Alexandria statement spends 257.8 key characters a component
  for Wildcat V1, 257.9 for V2 and 253.5 for Aave V3, so `verify` fails at
  about 1,016 components whatever the byte count. `statement` writes such a
  statement today, and Ariadne then refuses it.

The releases that need this exist. Twelve segment releases of the Aave V3
interval exceed both bounds, at 3,399 to 10,391 components each and up to
64,382,085 statement bytes. The design record
`plugins/alexandria/docs/statement-parts/design-evidence.json`, SHA-256
`071dcdb20c28a46fdd18933b4dcf31975d787b7c5581f2f092e5ecf00b3c2459`, graded
four candidates and selects `statement-parts` under `unique-frontier`. The
study beside it, `plugins/alexandria/docs/statement-parts/study.md`, holds the
measurements. Ariadne does not change.

## Decision

This record holds three decisions.

1. The part form. A release whose single statement stays within 8,388,608
   bytes and 262,144 key characters keeps today's statement, byte for byte.
   Any other release gets a part set: a directory holding `index.json` and
   `part-00000.json` onwards, each an in-toto Statement v1 in Alexandria's
   canonical encoding.
   - A part has predicate type
     `https://ariadne.wildcat.finance/alexandria-release-part/v1`. Its
     subjects are the release and a contiguous run of components. It carries
     those components and every capture that names them, plus
     `predicate.part` with `index`, `first_component`, `components` and
     `captures`.
   - The index has predicate type
     `https://ariadne.wildcat.finance/alexandria-release-parts/v1`. Its
     subjects are the release and each part file by SHA-256. It carries the
     part count and the release's total components and captures.
   - Packing is greedy in manifest order. A part closes before the component
     whose subject, component object and captures would carry it past either
     bound. Two closed schemas, `release-statement-part-v1.schema.json` and
     `release-statement-parts-v1.schema.json`, ship beside the existing one.
   - `statement <release> --parts <directory>` writes the set into a fresh
     sibling temporary directory, fsyncs every file and the directory,
     re-verifies the release and renames it into place. The target must be
     absent. `--parts` on a release within both single bounds refuses and names
     `--output`, so each release has one statement form. `--output` and
     `--parts` are mutually exclusive.
2. The part bound: 6,225,920 bytes and 262,144 key characters a part.
   - 6,225,920 is 6 MiB less 64 KiB. Its base64 encoding is 8,301,228 bytes,
     which leaves 87,380 bytes of an 8,388,608-byte envelope for the DSSE
     envelope's own fields and its signatures. A bare statement cannot pass
     the bound a signed one would miss.
   - 262,144 is Ariadne's aggregate key budget. The emitter counts key
     characters as gates 4 and 7 scan them: every object key under the
     predicate, plus every key of each subject's digest object.
   - A component whose own part would exceed either bound refuses by name,
     naming the component and the bound, and nothing is written. The index
     holds at most 16,385 subjects and measures 1,950,336 bytes and 98,405 key
     characters at that size, inside both bounds for every release #1888
     admits.
3. Routing the band. Laurence chose on 2026-09-30 that `statement --output`
   refuses by name a release whose single statement fits 8,388,608 bytes but
   exceeds 262,144 key characters, and names `--parts`. That covers roughly
   1,017 to 1,790 components at Wildcat V1's rate and 1,017 to 5,000 at V2's.
   Today such a release gets a file Ariadne refuses to verify. The byte
   refusal keeps its text, `release statement encodes to N bytes, above
   Ariadne's 8388608-byte input limit`. No pinned release is in the band: the
   largest, Wildcat V2, has 127 components and 32,749 key characters.

## Alternatives

The record measured each candidate on two synthetic releases at the #1888 cap,
both 16,384 components and 16,384 captures. `light` has 13,288,026 single
statement bytes and 3,588,187 key characters. `heavy` has 121,356,890 bytes.

- `per-component-statements` uses the same shapes with one component a part
  and no packing rule. It passes every gate but writes 134,458,292 bytes over
  16,385 files, and checking them takes 1,594,382 milliseconds against 6,495
  for `statement-parts`, which writes 121,372,939 bytes. Its largest file is
  the 1,950,336-byte index.
- `raised-limit-matched-reader` emits one statement up to 134,217,728 bytes and
  reads it with `--max-bytes 134217728` and a raised key budget. It fails
  `default-reader-verifies`: Ariadne's unmodified defaults refuse it. A signed
  heavy statement is a 161,809,276-byte envelope, and raising the key budget
  is an Ariadne change this run may not make.
- `compact-projection` writes arrays instead of objects for components and
  captures. It saves little (118,719,066 bytes against 121,356,890), because
  gap text is most of a heavy capture. It keeps every scope and coverage key,
  and hiding those would take verdict-bearing structure out of gates 4 and 7.
  It fails `cap-release-verifies` and `default-reader-verifies`.

For routing, the alternative keeps today's bytes for the band and files the
verify failure as its own issue. Laurence chose the refusal.

## Consequences

- Heavy takes 20 parts and light 14. The largest heavy part is 6,222,563 bytes
  bare, 8,296,840 as an unsigned DSSE envelope, with 184,093 key characters.
  Ariadne verifies all 21 files under its defaults in 6,495 milliseconds, one
  process a file.
- A reader checks up to 21 files instead of one. Completeness rests on the
  index's digests rather than on one file.
- Ariadne keeps the Alexandria predicates unregistered, so gates 2 and 5 stay
  visibly unchecked on every statement this design emits, as today.
- `--output` on a release in the band now refuses where it once wrote. The
  #1888 test `check_statement_beyond_the_old_limits`, whose 6,500-component
  release fits today (5,272,102 bytes, 1,423,591 key characters), changes to
  expect the refusal.
- The existing eleven pinned statements keep their SHA-256, and #1888's release
  limits keep their values.
- Once a signing step or a reader depends on the two predicate types and the
  part layout, each of the three decisions is expensive to reverse: a change
  needs a new predicate version.
