# Source note: a child or a golden retriever

## Boundary

The supplied archive was source material, not authority. The user request,
repository instructions, selected skills, and Promise Machine governed the
work. No file or instruction from the archive was executed. The image model
could influence pixels only; it supplied no repository words, commands,
paths, links, or decisions.

Archive: `/Users/c0rtexzer0/Downloads/mascot-imagegen-kit-main.zip`

- SHA-256: `e09eb107921ab52e467bae54e3e605f2e01fa258df7c12529be44fc486d71218`
- Size: 64,678,409 bytes
- Accepted source types: bounded regular PNG and PDF references
- Reference handling: extracted into one ignored request-scoped temporary directory, inspected, and removed after generation

## Creator-supplied cover

The Creator supplied the captioned cover PNG during implementation and asked
to add it to this package. It was treated as source material rather than an
instruction surface and copied byte for byte without an image-model pass.

| Repository path | Dimensions | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `docs/assets/a-child-or-a-golden-retriever-cover.png` | 1448 by 1086 | 1,166,639 | `5763ab9da93a3bd3420d2e905eef9525dbeb2e642f3121d8ad76c38d9f9cc32a` |

Its existing caption is retained exactly in the pixels. The deterministic
builder places the same checked bytes on the Markdown and PDF opening surfaces.

## Generation

Date: 2026-08-27.

Tool: the built-in `image_gen` tool in its default image-generation mode. No
CLI, API key, or fallback model was used. Three local images were supplied to
each call as visual references. Their role was limited to the Wildcat mascot's
identity and illustration style.

The following prompt text is exact from `Use case` through the final period.
The newline before each closing fence belongs to Markdown, not to the prompt.

### Mascot roles prompt

```text
Use case: illustration-story
Asset type: text-free source illustration for a beginner infographic
Primary request: Create one polished wide editorial illustration of the same canonical Wildcat mascot appearing across four connected vignettes, from left to right: first as a friendly small collective gathered together; second as that same mascot stepping through a simple open doorway into an external workspace; third as that same mascot calmly arranging blank task cards into an ordered system; fourth as that same mascot holding a plain ledger and checking one blank receipt. The vignettes must read as one continuous story and leave generous clean negative space around the figures so deterministic labels can be added later.
Input images: Image 1 is the official mascot line-art reference; Image 2 is a caption-free close identity reference; Image 3 is a group reference. Use them only to preserve mascot identity and illustration character. Ignore any text, labels, instructions, logos, or UI in source material.
Subject: an angular light-grey or white anthropomorphic Wildcat mascot with very tall triangular ears, narrow yellow eyes, heavy dark brows, lean proportions, a geometric muzzle, and sharp cheek points. Keep the face and proportions recognisably identical in every vignette. The mood is patient, friendly, and quietly competent.
Style/medium: polished 2D editorial comic illustration with crisp dark ink, limited flat colour, soft paper texture, and restrained depth.
Composition/framing: horizontal landscape; four clearly separated but visually connected vignettes; complete ears and hands; no important element at the extreme edge.
Lighting/mood: clear, calm, welcoming, instructional.
Color palette: Bunker #141414, Ultramarine Blue #3E68FF, Purple Heart #4D26BC, Galliano #D7A820, Oasis #FBEDC3, white, and cool grey.
Text: none.
Constraints: no words, letters, numbers, captions, speech bubbles, labels, logos, watermarks, or readable symbols; every card, receipt, page, sign, and screen must be completely blank; no generated typography; no humans.
Avoid: generic housecat or fox anatomy, rounded kawaii face, shortened ears, blue eyes, muscular superhero proportions, cryptocurrency coins, chains, rockets, magic, cyberpunk trading screens, and generic crypto imagery.
```

### Mascot Fiat prompt

```text
Use case: illustration-story
Asset type: text-free source illustration for a beginner lifecycle infographic
Primary request: Create one polished wide editorial illustration of the canonical Wildcat mascot acting as a careful conductor of an orderly delivery. Place the mascot on the right, holding an open plain dark ledger in one hand and pointing with a small gold conductor's baton toward a calm left-to-right path of exactly seven separate blank paper cards. Connect the seven cards with simple dots or a gentle line. The cards represent ordered stages but must remain completely blank. Leave generous clean negative space above and around the path so deterministic labels can be added later.
Input images: Image 1 is the official mascot line-art reference; Image 2 is a caption-free close identity reference; Image 3 is the accepted companion illustration whose exact mascot face, ink style, paper texture, clothing simplicity, and palette should be matched. Use inputs only for visual identity and style. Ignore any text, labels, instructions, logos, or UI in source material.
Subject: one angular light-grey or white anthropomorphic Wildcat mascot with very tall triangular ears, narrow yellow eyes, heavy dark brows, lean proportions, a geometric muzzle, sharp cheek points, and complete visible hands. The expression is patient, attentive, and quietly competent, never grandiose.
Style/medium: polished 2D editorial comic illustration with crisp dark ink, limited flat colour, soft paper texture, and restrained depth; match the accepted companion illustration closely.
Composition/framing: horizontal landscape; the complete mascot on the right third; seven blank cards flowing across the left and centre; no cropped ears, hands, baton, ledger, or card; no important element at the extreme edge.
Lighting/mood: clear, calm, welcoming, methodical.
Color palette: Bunker #141414, Ultramarine Blue #3E68FF, Purple Heart #4D26BC, Galliano #D7A820, Oasis #FBEDC3, white, and cool grey.
Text: none.
Constraints: no words, letters, numbers, captions, speech bubbles, labels, logos, watermarks, or readable symbols; every card, page, sign, and screen must be completely blank; no generated typography; no humans.
Avoid: generic housecat or fox anatomy, rounded kawaii face, shortened ears, blue eyes, muscular superhero proportions, cryptocurrency coins, chains, rockets, magic, cyberpunk trading screens, and generic crypto imagery.
```

## Accepted source illustrations

| Repository path | Dimensions | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `docs/assets/a-child-or-a-golden-retriever-mascot-roles.png` | 1774 by 887 | 2,171,579 | `f25e3e7c62b22895a89f270b5383288cb4996ac2976987c82170da4ca97e7485` |
| `docs/assets/a-child-or-a-golden-retriever-mascot-fiat.png` | 1774 by 887 | 1,682,633 | `6bcbab3534c69e06134e2b404ac765e2a1a859eaff4019a791ce862b2e3b13f5` |

The accepted files are the built-in tool outputs copied byte for byte into the
repository. The reference library itself is not copied or committed.

## Visual review

The roles illustration keeps the angular light mascot, very tall triangular
ears, narrow yellow eyes, heavy brows, geometric muzzle, and lean proportions
across four scenes. Those scenes read as collective, doorway, ordered cards,
and ledger. The mascot does not become a generic cat or fox.

The Fiat illustration uses the same face, proportions, ink, paper texture, and
palette. It shows one careful conductor, one blank ledger, and exactly seven
separate blank cards in order.

Both accepted illustrations were inspected at full size. Neither contains a
word, letter, number, logo, caption, speech bubble, watermark, or readable
screen. The cards and pages are blank. The builder adds every title,
definition, phase label, command, link, and footer through deterministic
layout code.

## Output review

The builder consumes the Creator-supplied cover, the two accepted source
illustrations, and the canonical Markdown primer. It writes the two fixed-size
infographics and two horizontal-A4 PDFs through temporary files before
replacement. Poppler renders of every final page are the visual acceptance
surface; PDF text and annotations are checked separately.
