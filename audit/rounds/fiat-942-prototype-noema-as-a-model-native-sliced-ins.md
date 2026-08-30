## Step 1, round 1 -- 2026-08-30T06:16:25Z

Audit schema: fiat-audit-round/v2

Covered: source-omission=not-applicable; semantic-drift=reviewed; slice-omission=not-applicable; authority-confusion=reviewed; module-drift=not-applicable; alias-collision=reviewed; literal-injection=reviewed; parser-exhaustion=reviewed; profile-mismatch=not-applicable; hidden-overhead=not-applicable; evaluation-contamination=not-applicable; provider-boundary=not-applicable; derived-drift=reviewed; parallel-stack=reviewed

Not checked: the waived Pashov X-Ray and Solidity suite because Step 1 ships no Solidity; parser, module, projection, slicer, policy-runtime, source-binding, measurement and provider-adapter behavior reserved for Steps 2 through 5; hosted CI; remote publication, pull requests and GitHub-side signature verification

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | scripts/noema.py | `PurePosixPath` normalization let self-consistent ZIP inventories bless non-canonical root and member spellings such as `a/./b` and `a//b`. A later filesystem consumer could collapse two verified names to one path despite the unsafe-path refusal contract. The published schema also accepted the member aliases. | fixed in this working tree; six parent-red assertions reproduced the member, root and schema gaps; runtime and schema now require canonical POSIX spelling; all three guard methods pass |

Leads not pursued: The verifier intentionally proves equality to the supplied inventory, not provenance of an arbitrary inventory; the committed #942 inventory and public URL remain the trust anchor. It never extracts a member, and the exact 24,907-byte public archive still returns `NOE-OK` with archive SHA-256 `1e1eb5e9908551f1337b7ec58a37ae7f37fd97e41d5ac424bc4992eb1d11b540`, inventory SHA-256 `8286bad9bf07f95f5297e536c50ad23ee7b96866bf94d86387626d6d8b573cbf` and 17 files. Parent-directory replacement by a concurrent local writer remains outside the final-component no-follow check; that actor already needs local write authority, and exact post-open identity plus digest validation prevents substituted seed bytes from passing. ZIP range overlap was not promoted to a finding because the verifier performs no extraction, binds exact archive and member digests, caps the archive and decoded aggregate at 1,048,576 bytes, and rejects duplicate names and header offsets. The 31 focused scaffold tests pass; Phylax, Ephoros and Hypomnema each exit zero over the changed tree; `git diff --check` exits zero. The exact audit declaration is `--audit-filter sapheneia:sapheneia`; the candidate retained every identifier, severity, qualification, digest, verdict, status and negative-space item from the frozen round inventory. No prior audit record was edited.

## Step 1, round 2 -- 2026-08-30T06:22:08Z

Audit schema: fiat-audit-round/v2

Covered: source-omission=not-applicable; semantic-drift=reviewed; slice-omission=not-applicable; authority-confusion=reviewed; module-drift=not-applicable; alias-collision=reviewed; literal-injection=reviewed; parser-exhaustion=reviewed; profile-mismatch=not-applicable; hidden-overhead=not-applicable; evaluation-contamination=not-applicable; provider-boundary=not-applicable; derived-drift=reviewed; parallel-stack=reviewed

Not checked: the waived Pashov X-Ray and Solidity suite because Step 1 ships no Solidity; parser, module, projection, slicer, policy-runtime, source-binding, measurement and provider-adapter behavior reserved for Steps 2 through 5; hosted CI; remote publication, pull requests and GitHub-side signature verification

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | low | scripts/noema.py | The verifier returned `NOE-OK` for member names `a b` and `C:policy`, and accepted roots with the same space or colon forms, while the published closed schema rejected those records. The colon form also left a platform-dependent drive spelling inside a supposedly safe inventory. | fixed in this working tree; one missing-constant error and four accepted-invalid-path assertions were parent red; runtime regexes now match both published schema patterns byte for byte; all three guard methods pass |

Leads not pursued: The round-1 canonical-spelling fix remains effective for repeated separators, dot components and ambiguous roots. The runtime now enforces the schema's ASCII seed-path alphabet in addition to POSIX canonicality, while NFC and control checks remain defense in depth. This deliberately narrows only the seed inventory; future governed source-path and typed path-literal alphabets remain Step 2 work and are not inferred from this archive format. The exact public archive still returns `NOE-OK` with the same 24,907 bytes, 17 files and digests recorded in round 1. The 34 focused scaffold tests pass; Phylax, Ephoros and Hypomnema each exit zero over the changed tree; `git diff --check` exits zero. The exact audit declaration is `--audit-filter sapheneia:sapheneia`; the checked candidate preserved the finding id, severity, examples, platform qualification, parent-red evidence, verdict, status, negative space and prior-round facts. The round-1 record remains byte-identical.

## Step 1, round 3 -- 2026-08-30T06:26:36Z

Audit schema: fiat-audit-round/v2

Covered: source-omission=not-applicable; semantic-drift=reviewed; slice-omission=not-applicable; authority-confusion=reviewed; module-drift=not-applicable; alias-collision=reviewed; literal-injection=reviewed; parser-exhaustion=reviewed; profile-mismatch=not-applicable; hidden-overhead=not-applicable; evaluation-contamination=not-applicable; provider-boundary=not-applicable; derived-drift=reviewed; parallel-stack=reviewed

Not checked: the waived Pashov X-Ray and Solidity suite because Step 1 ships no Solidity; parser, module, projection, slicer, policy-runtime, source-binding, measurement and provider-adapter behavior reserved for Steps 2 through 5; hosted CI; remote publication, pull requests and GitHub-side signature verification

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | low | scripts/noema.py | Descriptor inspection, read and close faults escaped `_read_regular` as raw `OSError`. The CLI could therefore print a traceback instead of its promised single bounded `NOE-E-IO` refusal line. | fixed in this working tree; all three injected descriptor faults errored on the parent; expected `OSError` paths now normalize to `NOE-E-IO.READ` while existing refusals retain their codes; all three guards pass |

Leads not pursued: The two path fixes remain effective under the complete focused suite. `lstat` and `open` failures were already normalized; the repair closes the remaining regular-descriptor operations without swallowing a typed `Refusal`. A close fault after a successful read refuses the result because complete descriptor cleanup is uncertain; a close fault while another refusal is active does not replace the earlier, more specific refusal. Unexpected interpreter faults and process termination are not relabeled as I/O evidence. The exact public archive still returns `NOE-OK` with the same 24,907 bytes, 17 files and digests recorded in round 1. The 37 focused scaffold tests pass; Phylax, Ephoros and Hypomnema each exit zero over the changed tree; `git diff --check` exits zero. The exact audit declaration is `--audit-filter sapheneia:sapheneia`; the checked candidate retained the identifier, severity, three fault sites, traceback consequence, refusal code, parent-red evidence, verdict, status, negative space and prior-round facts. The first two records remain byte-identical.

## Step 1, round 4 -- 2026-08-30T06:30:28Z

Audit schema: fiat-audit-round/v2

Covered: source-omission=not-applicable; semantic-drift=reviewed; slice-omission=not-applicable; authority-confusion=reviewed; module-drift=not-applicable; alias-collision=reviewed; literal-injection=reviewed; parser-exhaustion=reviewed; profile-mismatch=not-applicable; hidden-overhead=not-applicable; evaluation-contamination=not-applicable; provider-boundary=not-applicable; derived-drift=reviewed; parallel-stack=reviewed

Not checked: the waived Pashov X-Ray and Solidity suite because Step 1 ships no Solidity; parser, module, projection, slicer, policy-runtime, source-binding, measurement and provider-adapter behavior reserved for Steps 2 through 5; hosted CI; remote publication, pull requests and GitHub-side signature verification

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R4-01 | low | scripts/noema.py | Corrupt deflate streams raised raw `zlib.error`, bypassing the archive parser's `NOE-E-SYNTAX.ZIP` refusal and producing a traceback for attacker-chosen ZIP bytes whose digest matched their inventory. | fixed in this working tree; the deterministic corrupt-member guard errored on the parent; `zlib.error` now joins the bounded decoder refusal boundary; the guard passes and a 648-case byte-mutation sweep has zero unhandled exceptions |

Leads not pursued: The mutation sweep changes each of 216 bytes in one small deflated archive by three masks; it is adversarial evidence for this exception class, not an exhaustive proof over every ZIP grammar or Python decoder path. Existing `BadZipFile`, `LargeZipFile`, `RuntimeError` and `OSError` normalization remains unchanged, as do encryption, compression-method, member, size, path and digest gates. The three earlier fixes remain effective under the complete focused suite. The exact public archive still returns `NOE-OK` with the same 24,907 bytes, 17 files and digests recorded in round 1. The 38 focused scaffold tests pass; Phylax, Ephoros and Hypomnema each exit zero over the changed tree; `git diff --check` exits zero. The exact audit declaration is `--audit-filter sapheneia:sapheneia`; the checked candidate retained the identifier, severity, exception type, attacker qualification, refusal code, parent-red error, mutation counts, verdict, status, negative space and prior-round facts. The first three records remain byte-identical.
