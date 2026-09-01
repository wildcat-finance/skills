# Scrutiny of wildcat-app-v2

One scrutiny of one pinned commit against one reviewed workbook. This
states what was examined and what carries no disposition. It does not
state that anything passed.

## What was examined

- Application: `wildcat-app-v2` at `bb9685fb7dbe9cd2f5b7683a9b3f164509dc2de9`
- Workbook: `wildcat_v25_uat_v2-jack.xlsx`, sha256 `9da2f2e8bbdb`
- Inventory digest: `88325a449814`
- Workbook digest: `21493992f97e`
- Coverage digest: `70af3e184999`
- Skill version: `dokimasia-v1.1.0`

## The denominator

The scoped set holds **261 items**: 59 compiled from the application and 202 imported from the workbook.

| Kind | Count |
| --- | ---: |
| `api` | 35 |
| `case` | 202 |
| `guard` | 1 |
| `route` | 23 |

## Closure

- Numerator: **0** items carrying one disposition
- Denominator: **261** scoped items
- Ratio: **0.0000**
- Closed: **no**

**261 of 261 scoped items carry no disposition.** Nobody has decided about them, so the
ratio is open and the release has no coverage claim this record
can support.

This is the finding, not a failure of the run. The application
contributes a denominator that did not exist before, and the
workbook contributes rows nobody has joined to it.

## Gaps

No item carries `manual` or `excluded`, so there is no reason list to review. That follows from the ratio above: nothing has been decided either way.

## Neither side cites the other

- Application items no oracle is held to: **59**
- Workbook cases no item cites: **202**

The first is the uncovered application surface. The second is review
effort the inventory does not know about.

## Why a number here could move

Three identities are recorded above: the application commit, the
workbook digest and the skill version. A later scrutiny whose result
differs names which of the three moved. A result that moved with none
of them moved is reported as unattributed rather than as a change.

