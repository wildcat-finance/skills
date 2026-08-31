# Study: complete amendment fixture

## 1. Problem statement

Check one amendment with `unittest`.

## 2. Prior art

The existing checker is the prior implementation.

## 3. Constraints and non-goals

Use the standard library only.

## 4. Design options

Use the existing bounded Markdown walk.

## 5. Risk register seed

```risk-register
markdown-input | the caller-named study | fields are checked without echoing values
```

## 6. Glossary seeds

Amendment: an appended study correction.

## 7. Sources

The Protasis contract.

## 8. Signals, and the questions behind them

The finding line and exit status answer whether the check accepted the file.

## 9. Boundaries, per capability

The caller-named path is bounded and read as Markdown.

## 10. The budget, or its absence

None, because this fixture makes no performance claim.

## 11. The fail-closed posture

A malformed amendment returns a finding.

## 12. Decisions and their homes

The study and runbook hold the scanner decision.

### Amendment -- 2026-08-29

**What changed.** The fixture now carries a checked amendment.
**Why.** The study scanner needs one accepted specimen.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds.
