# Harness roster content and freshness demonstration

Observed on 5 September 2026 against
`b14fc8e969e1ed92d3c23c312b305bdc6827cd98`. This demonstration uses temporary
copies. It does not re-probe a live harness or edit the committed manifest.

## Boundary

The generated README region, guide region, and PDF harness page are roster
content. The manifest remains the provenance record for observation host, date,
and base commit. A separate hard check gives that observation a 30-day calendar
budget: ages zero through 30 pass; age 31 and future dates fail.

The dated outputs below prove the behavior of the named commit on the named
local calendar date. They do not establish that the committed observation is
still fresh when this document is read later. The declared freshness command
answers that question at run time.

## Committed controls

```console
$ python3 scripts/render_harness_roster.py --check
three surfaces match 6 recorded harnesses
$ python3 scripts/render_harness_roster.py --check-freshness
manifest observation age 0 days is within the 30-day budget
```

Both commands exited zero.

## Metadata-only change writes no surface

The specimen copied the manifest and all three surfaces into a directory from
`mktemp -d`, then changed only `recorded.host`, `recorded.date`, and
`recorded.base_ref`:

```bash
DEMO=$(mktemp -d)
mkdir -p "$DEMO/docs/pdf"
cp docs/harness-classification.json "$DEMO/docs/harness-classification.json"
cp README.md "$DEMO/README.md"
cp docs/how-to-help-shoggoth.md "$DEMO/docs/how-to-help-shoggoth.md"
cp docs/pdf/how-to-help-shoggoth.pdf "$DEMO/docs/pdf/how-to-help-shoggoth.pdf"
jq '.recorded.host="recorded-elsewhere"
    | .recorded.date="2026-09-04"
    | .recorded.base_ref=("0" * 40)' \
  "$DEMO/docs/harness-classification.json" > "$DEMO/docs/metadata-only.json"
python3 scripts/render_harness_roster.py \
  --manifest "$DEMO/docs/metadata-only.json" \
  --readme "$DEMO/README.md" \
  --guide "$DEMO/docs/how-to-help-shoggoth.md" \
  --pdf "$DEMO/docs/pdf/how-to-help-shoggoth.pdf"
```

The renderer exited zero and named no written path:

```text
rendered 6 harnesses into three surfaces
```

Hashes before and after were identical:

```text
603c472b39c22c9068ae9497999cbb4079d3e73966bd397136d182089f439311  README.md
e0f083516b5d115af498bf1c1ff1b06d473a071fada4976e8dcc35eec63de3b5  docs/how-to-help-shoggoth.md
dec768c96c02e9948e4c265e37211d745b7cf6f14990aff47e4e47c3f40ea732  docs/pdf/how-to-help-shoggoth.pdf
```

The content check against that metadata-only manifest also exited zero with
`three surfaces match 6 recorded harnesses`.

## A 31-day observation fails only freshness

On the observation date above, 5 September 2026, a staged date of 5 August
2026 was 31 completed calendar days old:

```bash
jq '.recorded.date="2026-08-05"' \
  "$DEMO/docs/harness-classification.json" > "$DEMO/docs/stale.json"
python3 scripts/render_harness_roster.py --check \
  --manifest "$DEMO/docs/stale.json" \
  --readme "$DEMO/README.md" \
  --guide "$DEMO/docs/how-to-help-shoggoth.md" \
  --pdf "$DEMO/docs/pdf/how-to-help-shoggoth.pdf"
python3 scripts/render_harness_roster.py --check-freshness \
  --manifest "$DEMO/docs/stale.json"
```

The content command exited zero. The freshness command exited one:

```text
three surfaces match 6 recorded harnesses
render_harness_roster: manifest observation age 31 days exceeds the 30-day budget
```

## Harness content still reddens content checks

Changing one harness name and no metadata preserved the ordinary drift gate:

```bash
jq '(.harnesses[] | select(.name=="Cline") | .name)="Clins"' \
  "$DEMO/docs/harness-classification.json" > "$DEMO/docs/content-drift.json"
python3 scripts/render_harness_roster.py --check \
  --manifest "$DEMO/docs/content-drift.json" \
  --readme "$DEMO/README.md" \
  --guide "$DEMO/docs/how-to-help-shoggoth.md" \
  --pdf "$DEMO/docs/pdf/how-to-help-shoggoth.pdf"
```

The command exited one. Temporary paths are shown as `$DEMO`:

```text
render_harness_roster: $DEMO/README.md: the roster region does not match the manifest
render_harness_roster: $DEMO/docs/how-to-help-shoggoth.md: the roster region does not match the manifest
render_harness_roster: $DEMO/docs/pdf/how-to-help-shoggoth.pdf: the harness page does not show 'GitHub Copilot  /  Cursor  /  Gemini CLI  /  Windsurf  /  Clins'
render_harness_roster: 3 surface(s) drifted from the manifest
```
