# Decision: Omit decorative portraits from the portable runtime

## Status

Accepted, 2026-09-12. Stable identity: `adr/omit-portable-decorative-portraits`.

## Context

At `b9cafd196b1d8f8b74b207320836532c14e78bab`, the runtime used 27,036,319 bytes against the skills CLI's 26,214,400-byte ceiling. The package must retain the source documents, runtime evidence and executable checks its operations need. [Issue #1467](https://github.com/wildcat-finance/skills/issues/1467) and the specification in [PR #1515](https://github.com/wildcat-finance/skills/pull/1515) identified decorative portraits as an omission class.

## Decision

Omit direct PNG and WebP children of `assets/characters/` and `plugins/*/assets/characters/` from the generated runtime, remove inline images pointing to those omitted files from packaged Markdown, and reserve at least 5,242,880 bytes below the fixed 26,214,400-byte cap.

## Alternatives

Raising the byte cap leaves the CLI's own refusal unchanged. Removing documents or tests would remove instructions or evidence required by the portable operations. Omitting portraits while keeping their image references would leave broken packaged references. Moving the corpus to another delivery was a separate change whose operation and evidence boundary this repair did not establish.

## Consequences

Source portraits and source Markdown remain unchanged. Packaged Markdown retains other image classes, remote images, ordinary links and every byte outside the declared inline image ranges. The transform recognises Markdown inline images and HTML `img` elements with quoted `src` attributes; it removes a reference only when its relative path resolves to an actually omitted portrait.

The runtime manifest records each omitted source path, byte count and digest. An image transform records its original digest and length, output digest and length, transform identifier and removed source byte ranges. The authored outer router uses the same transformed bytes as its runtime copy. Installed verification proves agreement with the output manifest; source-based tests separately replay the recorded ranges against the original bytes and check the source digests.

The evaluation record binds whole skill files, so its packaged copy needs a separate derivation after portrait removal. The generator verifies the canonical record and compares all eleven source and packaged prompt files through the evaluation owner. A changed prompt refuses packaging. Equal prompts permit owner tally replay of the original answers, model and date. The manifest binds source and derived record bytes, prompt digests and answer identity; this is no new model observation. Canonical evidence remains unchanged, and an isolated packaged checker must accept the derived record.

Generation refuses the first byte beyond 20,971,520 bytes for both the runtime payload and the complete package, including its manifest and outer files. That threshold preserves 20% of the CLI ceiling for future growth. The file-count policy and the source distribution's portrait inventory are unchanged. The latest measurements and reproduction commands live at `docs/main-root-suite-recovery/README.md` from the repository root.
