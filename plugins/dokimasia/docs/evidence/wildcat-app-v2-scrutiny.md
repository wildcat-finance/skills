# Scrutiny of wildcat-app-v2

One scrutiny of one pinned commit against one reviewed workbook. This
states what was examined and what carries no disposition. It does not
state that anything passed.

## What was examined

- Application: `wildcat-app-v2` at `bb9685fb7dbe9cd2f5b7683a9b3f164509dc2de9`
- Workbook: `wildcat_v25_uat_v2-jack.xlsx`, sha256 `9da2f2e8bbdb`
- Inventory digest: `88325a449814`
- Workbook digest: `21493992f97e`
- Coverage digest: `0c015a799121`
- Skill version: `dokimasia-v3.1.0`

## The denominator

The scoped set holds **261 items**: 59 compiled from the application and 202 imported from the workbook.

| Kind | Count |
| --- | ---: |
| `api` | 35 |
| `case` | 202 |
| `guard` | 1 |
| `route` | 23 |

## Closure

- Numerator: **202** items carrying one disposition
- Denominator: **261** scoped items
- Ratio: **0.7739**
- Closed: **no**

**59 of 261 scoped items carry no disposition.** Nobody has decided about them, so the
ratio is open and the release has no coverage claim this record
can support.

This is the finding, not a failure of the run. The application
contributes a denominator that did not exist before, and the
workbook contributes rows nobody has joined to it.

## Who decided

- People: **1** distinct person confirmed the numerator
- Individually: **0** entries confirmed by a named person under no rule
- Rules declared: **1**

| Rule | Stated by | Applied | Text |
| --- | --- | ---: | --- |
| `row-author-owns-walking-it` | Laurence Day | 202 | the reviewer who wrote a row owns walking it, which holds by construction of the workbook |

A person's name here is a claim the disposition set makes under that
name; nothing verified that the person agreed. An entry confirmed
under a rule carries the judgement of the person who stated the rule.

## Gaps

| Item | Disposition | Reason |
| --- | --- | --- |
| `case:ADM-01` | `manual` | drafted from workbook row 1 Admin:6, identifier ADM-01; a reviewer owns this row |
| `case:ADM-02` | `manual` | drafted from workbook row 1 Admin:7, identifier ADM-02; a reviewer owns this row |
| `case:ADM-03` | `manual` | drafted from workbook row 1 Admin:8, identifier ADM-03; a reviewer owns this row |
| `case:ADM-04` | `manual` | drafted from workbook row 1 Admin:9, identifier ADM-04; a reviewer owns this row |
| `case:ADM-05` | `manual` | drafted from workbook row 1 Admin:10, identifier ADM-05; a reviewer owns this row |
| `case:ADM-06` | `manual` | drafted from workbook row 1 Admin:12, identifier ADM-06; a reviewer owns this row |
| `case:ADM-07` | `manual` | drafted from workbook row 1 Admin:13, identifier ADM-07; a reviewer owns this row |
| `case:ADM-08` | `manual` | drafted from workbook row 1 Admin:14, identifier ADM-08; a reviewer owns this row |
| `case:ADM-09` | `manual` | drafted from workbook row 1 Admin:15, identifier ADM-09; a reviewer owns this row |
| `case:ADM-10` | `manual` | drafted from workbook row 1 Admin:17, identifier ADM-10; a reviewer owns this row |
| `case:ADM-11` | `manual` | drafted from workbook row 1 Admin:18, identifier ADM-11; a reviewer owns this row |
| `case:ADM-12` | `manual` | drafted from workbook row 1 Admin:19, identifier ADM-12; a reviewer owns this row |
| `case:ADM-13` | `manual` | drafted from workbook row 1 Admin:20, identifier ADM-13; a reviewer owns this row |
| `case:BON-01` | `manual` | drafted from workbook row 2 Borrower Onboarding:6, identifier BON-01; a reviewer owns this row |
| `case:BON-02` | `manual` | drafted from workbook row 2 Borrower Onboarding:7, identifier BON-02; a reviewer owns this row |
| `case:BON-03` | `manual` | drafted from workbook row 2 Borrower Onboarding:8, identifier BON-03; a reviewer owns this row |
| `case:BON-04` | `manual` | drafted from workbook row 2 Borrower Onboarding:10, identifier BON-04; a reviewer owns this row |
| `case:BON-05` | `manual` | drafted from workbook row 2 Borrower Onboarding:11, identifier BON-05; a reviewer owns this row |
| `case:BON-06` | `manual` | drafted from workbook row 2 Borrower Onboarding:12, identifier BON-06; a reviewer owns this row |
| `case:BON-07` | `manual` | drafted from workbook row 2 Borrower Onboarding:13, identifier BON-07; a reviewer owns this row |
| `case:BON-08` | `manual` | drafted from workbook row 2 Borrower Onboarding:15, identifier BON-08; a reviewer owns this row |
| `case:BON-09` | `manual` | drafted from workbook row 2 Borrower Onboarding:16, identifier BON-09; a reviewer owns this row |
| `case:BON-10` | `manual` | drafted from workbook row 2 Borrower Onboarding:17, identifier BON-10; a reviewer owns this row |
| `case:BOP-01` | `manual` | drafted from workbook row 4 Borrower Ops:6, identifier BOP-01; a reviewer owns this row |
| `case:BOP-02` | `manual` | drafted from workbook row 4 Borrower Ops:7, identifier BOP-02; a reviewer owns this row |
| `case:BOP-03` | `manual` | drafted from workbook row 4 Borrower Ops:8, identifier BOP-03; a reviewer owns this row |
| `case:BOP-04` | `manual` | drafted from workbook row 4 Borrower Ops:9, identifier BOP-04; a reviewer owns this row |
| `case:BOP-05` | `manual` | drafted from workbook row 4 Borrower Ops:10, identifier BOP-05; a reviewer owns this row |
| `case:BOP-06` | `manual` | drafted from workbook row 4 Borrower Ops:12, identifier BOP-06; a reviewer owns this row |
| `case:BOP-07` | `manual` | drafted from workbook row 4 Borrower Ops:13, identifier BOP-07; a reviewer owns this row |
| `case:BOP-08` | `manual` | drafted from workbook row 4 Borrower Ops:14, identifier BOP-08; a reviewer owns this row |
| `case:BOP-09` | `manual` | drafted from workbook row 4 Borrower Ops:15, identifier BOP-09; a reviewer owns this row |
| `case:BOP-10` | `manual` | drafted from workbook row 4 Borrower Ops:16, identifier BOP-10; a reviewer owns this row |
| `case:BOP-11` | `manual` | drafted from workbook row 4 Borrower Ops:17, identifier BOP-11; a reviewer owns this row |
| `case:BOP-12` | `manual` | drafted from workbook row 4 Borrower Ops:19, identifier BOP-12; a reviewer owns this row |
| `case:BOP-13` | `manual` | drafted from workbook row 4 Borrower Ops:20, identifier BOP-13; a reviewer owns this row |
| `case:BOP-14` | `manual` | drafted from workbook row 4 Borrower Ops:21, identifier BOP-14; a reviewer owns this row |
| `case:BOP-15` | `manual` | drafted from workbook row 4 Borrower Ops:22, identifier BOP-15; a reviewer owns this row |
| `case:BOP-16` | `manual` | drafted from workbook row 4 Borrower Ops:23, identifier BOP-16; a reviewer owns this row |
| `case:BOP-17` | `manual` | drafted from workbook row 4 Borrower Ops:24, identifier BOP-17; a reviewer owns this row |
| `case:BOP-18` | `manual` | drafted from workbook row 4 Borrower Ops:25, identifier BOP-18; a reviewer owns this row |
| `case:BOP-19` | `manual` | drafted from workbook row 4 Borrower Ops:26, identifier BOP-19; a reviewer owns this row |
| `case:BOP-20` | `manual` | drafted from workbook row 4 Borrower Ops:27, identifier BOP-20; a reviewer owns this row |
| `case:BOP-21` | `manual` | drafted from workbook row 4 Borrower Ops:28, identifier BOP-21; a reviewer owns this row |
| `case:BOP-22` | `manual` | drafted from workbook row 4 Borrower Ops:30, identifier BOP-22; a reviewer owns this row |
| `case:BOP-23` | `manual` | drafted from workbook row 4 Borrower Ops:31, identifier BOP-23; a reviewer owns this row |
| `case:BOP-24` | `manual` | drafted from workbook row 4 Borrower Ops:32, identifier BOP-24; a reviewer owns this row |
| `case:BOP-25` | `manual` | drafted from workbook row 4 Borrower Ops:33, identifier BOP-25; a reviewer owns this row |
| `case:BOP-26` | `manual` | drafted from workbook row 4 Borrower Ops:35, identifier BOP-26; a reviewer owns this row |
| `case:BOP-27` | `manual` | drafted from workbook row 4 Borrower Ops:36, identifier BOP-27; a reviewer owns this row |
| `case:BOP-28` | `manual` | drafted from workbook row 4 Borrower Ops:37, identifier BOP-28; a reviewer owns this row |
| `case:BOP-29` | `manual` | drafted from workbook row 4 Borrower Ops:38, identifier BOP-29; a reviewer owns this row |
| `case:BOP-30` | `manual` | drafted from workbook row 4 Borrower Ops:39, identifier BOP-30; a reviewer owns this row |
| `case:BOP-31` | `manual` | drafted from workbook row 4 Borrower Ops:41, identifier BOP-31; a reviewer owns this row |
| `case:BOP-32` | `manual` | drafted from workbook row 4 Borrower Ops:42, identifier BOP-32; a reviewer owns this row |
| `case:BOP-33` | `manual` | drafted from workbook row 4 Borrower Ops:43, identifier BOP-33; a reviewer owns this row |
| `case:EDG-01` | `manual` | drafted from workbook row 10 Edge & Regression:5, identifier EDG-01; a reviewer owns this row |
| `case:EDG-02` | `manual` | drafted from workbook row 10 Edge & Regression:6, identifier EDG-02; a reviewer owns this row |
| `case:EDG-03` | `manual` | drafted from workbook row 10 Edge & Regression:7, identifier EDG-03; a reviewer owns this row |
| `case:EDG-04` | `manual` | drafted from workbook row 10 Edge & Regression:8, identifier EDG-04; a reviewer owns this row |
| `case:EDG-05` | `manual` | drafted from workbook row 10 Edge & Regression:9, identifier EDG-05; a reviewer owns this row |
| `case:EDG-06` | `manual` | drafted from workbook row 10 Edge & Regression:10, identifier EDG-06; a reviewer owns this row |
| `case:EDG-07` | `manual` | drafted from workbook row 10 Edge & Regression:12, identifier EDG-07; a reviewer owns this row |
| `case:EDG-08` | `manual` | drafted from workbook row 10 Edge & Regression:13, identifier EDG-08; a reviewer owns this row |
| `case:EDG-09` | `manual` | drafted from workbook row 10 Edge & Regression:14, identifier EDG-09; a reviewer owns this row |
| `case:EDG-10` | `manual` | drafted from workbook row 10 Edge & Regression:15, identifier EDG-10; a reviewer owns this row |
| `case:EDG-11` | `manual` | drafted from workbook row 10 Edge & Regression:16, identifier EDG-11; a reviewer owns this row |
| `case:EDG-12` | `manual` | drafted from workbook row 10 Edge & Regression:17, identifier EDG-12; a reviewer owns this row |
| `case:EDG-13` | `manual` | drafted from workbook row 10 Edge & Regression:18, identifier EDG-13; a reviewer owns this row |
| `case:EDG-14` | `manual` | drafted from workbook row 10 Edge & Regression:20, identifier EDG-14; a reviewer owns this row |
| `case:EDG-15` | `manual` | drafted from workbook row 10 Edge & Regression:21, identifier EDG-15; a reviewer owns this row |
| `case:LEN-01` | `manual` | drafted from workbook row 5 Lender Flows:6, identifier LEN-01; a reviewer owns this row |
| `case:LEN-02` | `manual` | drafted from workbook row 5 Lender Flows:7, identifier LEN-02; a reviewer owns this row |
| `case:LEN-03` | `manual` | drafted from workbook row 5 Lender Flows:8, identifier LEN-03; a reviewer owns this row |
| `case:LEN-04` | `manual` | drafted from workbook row 5 Lender Flows:9, identifier LEN-04; a reviewer owns this row |
| `case:LEN-05` | `manual` | drafted from workbook row 5 Lender Flows:11, identifier LEN-05; a reviewer owns this row |
| `case:LEN-06` | `manual` | drafted from workbook row 5 Lender Flows:12, identifier LEN-06; a reviewer owns this row |
| `case:LEN-07` | `manual` | drafted from workbook row 5 Lender Flows:13, identifier LEN-07; a reviewer owns this row |
| `case:LEN-08` | `manual` | drafted from workbook row 5 Lender Flows:14, identifier LEN-08; a reviewer owns this row |
| `case:LEN-09` | `manual` | drafted from workbook row 5 Lender Flows:15, identifier LEN-09; a reviewer owns this row |
| `case:LEN-10` | `manual` | drafted from workbook row 5 Lender Flows:16, identifier LEN-10; a reviewer owns this row |
| `case:LEN-11` | `manual` | drafted from workbook row 5 Lender Flows:17, identifier LEN-11; a reviewer owns this row |
| `case:LEN-12` | `manual` | drafted from workbook row 5 Lender Flows:18, identifier LEN-12; a reviewer owns this row |
| `case:LEN-13` | `manual` | drafted from workbook row 5 Lender Flows:20, identifier LEN-13; a reviewer owns this row |
| `case:LEN-14` | `manual` | drafted from workbook row 5 Lender Flows:21, identifier LEN-14; a reviewer owns this row |
| `case:LEN-15` | `manual` | drafted from workbook row 5 Lender Flows:23, identifier LEN-15; a reviewer owns this row |
| `case:LEN-16` | `manual` | drafted from workbook row 5 Lender Flows:24, identifier LEN-16; a reviewer owns this row |
| `case:LEN-17` | `manual` | drafted from workbook row 5 Lender Flows:25, identifier LEN-17; a reviewer owns this row |
| `case:LEN-18` | `manual` | drafted from workbook row 5 Lender Flows:26, identifier LEN-18; a reviewer owns this row |
| `case:LEN-19` | `manual` | drafted from workbook row 5 Lender Flows:27, identifier LEN-19; a reviewer owns this row |
| `case:LEN-20` | `manual` | drafted from workbook row 5 Lender Flows:28, identifier LEN-20; a reviewer owns this row |
| `case:LEN-21` | `manual` | drafted from workbook row 5 Lender Flows:29, identifier LEN-21; a reviewer owns this row |
| `case:LEN-22` | `manual` | drafted from workbook row 5 Lender Flows:30, identifier LEN-22; a reviewer owns this row |
| `case:LEN-23` | `manual` | drafted from workbook row 5 Lender Flows:32, identifier LEN-23; a reviewer owns this row |
| `case:LEN-24` | `manual` | drafted from workbook row 5 Lender Flows:33, identifier LEN-24; a reviewer owns this row |
| `case:LEN-25` | `manual` | drafted from workbook row 5 Lender Flows:34, identifier LEN-25; a reviewer owns this row |
| `case:LEN-26` | `manual` | drafted from workbook row 5 Lender Flows:35, identifier LEN-26; a reviewer owns this row |
| `case:LEN-27` | `manual` | drafted from workbook row 5 Lender Flows:36, identifier LEN-27; a reviewer owns this row |
| `case:LEN-28` | `manual` | drafted from workbook row 5 Lender Flows:38, identifier LEN-28; a reviewer owns this row |
| `case:LEN-29` | `manual` | drafted from workbook row 5 Lender Flows:39, identifier LEN-29; a reviewer owns this row |
| `case:LEN-30` | `manual` | drafted from workbook row 5 Lender Flows:40, identifier LEN-30; a reviewer owns this row |
| `case:LEN-31` | `manual` | drafted from workbook row 5 Lender Flows:41, identifier LEN-31; a reviewer owns this row |
| `case:LEN-32` | `manual` | drafted from workbook row 5 Lender Flows:43, identifier LEN-32; a reviewer owns this row |
| `case:LEN-33` | `manual` | drafted from workbook row 5 Lender Flows:44, identifier LEN-33; a reviewer owns this row |
| `case:LEN-34` | `manual` | drafted from workbook row 5 Lender Flows:45, identifier LEN-34; a reviewer owns this row |
| `case:LEN-35` | `manual` | drafted from workbook row 5 Lender Flows:46, identifier LEN-35; a reviewer owns this row |
| `case:M1-01` | `manual` | drafted from workbook row 9 Scenario Scripts:6, identifier M1-01; a reviewer owns this row |
| `case:M1-02` | `manual` | drafted from workbook row 9 Scenario Scripts:7, identifier M1-02; a reviewer owns this row |
| `case:M1-03` | `manual` | drafted from workbook row 9 Scenario Scripts:8, identifier M1-03; a reviewer owns this row |
| `case:M1-04` | `manual` | drafted from workbook row 9 Scenario Scripts:9, identifier M1-04; a reviewer owns this row |
| `case:M1-05` | `manual` | drafted from workbook row 9 Scenario Scripts:10, identifier M1-05; a reviewer owns this row |
| `case:M1-06` | `manual` | drafted from workbook row 9 Scenario Scripts:11, identifier M1-06; a reviewer owns this row |
| `case:M1-07` | `manual` | drafted from workbook row 9 Scenario Scripts:12, identifier M1-07; a reviewer owns this row |
| `case:M1-08` | `manual` | drafted from workbook row 9 Scenario Scripts:13, identifier M1-08; a reviewer owns this row |
| `case:M2-01` | `manual` | drafted from workbook row 9 Scenario Scripts:15, identifier M2-01; a reviewer owns this row |
| `case:M2-02` | `manual` | drafted from workbook row 9 Scenario Scripts:16, identifier M2-02; a reviewer owns this row |
| `case:M2-03` | `manual` | drafted from workbook row 9 Scenario Scripts:17, identifier M2-03; a reviewer owns this row |
| `case:M2-04` | `manual` | drafted from workbook row 9 Scenario Scripts:18, identifier M2-04; a reviewer owns this row |
| `case:M2-05` | `manual` | drafted from workbook row 9 Scenario Scripts:19, identifier M2-05; a reviewer owns this row |
| `case:M2-06` | `manual` | drafted from workbook row 9 Scenario Scripts:20, identifier M2-06; a reviewer owns this row |
| `case:M3-01` | `manual` | drafted from workbook row 9 Scenario Scripts:22, identifier M3-01; a reviewer owns this row |
| `case:M3-02` | `manual` | drafted from workbook row 9 Scenario Scripts:23, identifier M3-02; a reviewer owns this row |
| `case:M3-03` | `manual` | drafted from workbook row 9 Scenario Scripts:24, identifier M3-03; a reviewer owns this row |
| `case:M3-04` | `manual` | drafted from workbook row 9 Scenario Scripts:25, identifier M3-04; a reviewer owns this row |
| `case:M4-01` | `manual` | drafted from workbook row 9 Scenario Scripts:27, identifier M4-01; a reviewer owns this row |
| `case:M4-02` | `manual` | drafted from workbook row 9 Scenario Scripts:28, identifier M4-02; a reviewer owns this row |
| `case:M4-03` | `manual` | drafted from workbook row 9 Scenario Scripts:29, identifier M4-03; a reviewer owns this row |
| `case:M4-04` | `manual` | drafted from workbook row 9 Scenario Scripts:30, identifier M4-04; a reviewer owns this row |
| `case:M5-01` | `manual` | drafted from workbook row 9 Scenario Scripts:32, identifier M5-01; a reviewer owns this row |
| `case:M5-02` | `manual` | drafted from workbook row 9 Scenario Scripts:33, identifier M5-02; a reviewer owns this row |
| `case:M5-03` | `manual` | drafted from workbook row 9 Scenario Scripts:34, identifier M5-03; a reviewer owns this row |
| `case:M5-04` | `manual` | drafted from workbook row 9 Scenario Scripts:35, identifier M5-04; a reviewer owns this row |
| `case:M5-05` | `manual` | drafted from workbook row 9 Scenario Scripts:36, identifier M5-05; a reviewer owns this row |
| `case:M5-06` | `manual` | drafted from workbook row 9 Scenario Scripts:37, identifier M5-06; a reviewer owns this row |
| `case:M5-07` | `manual` | drafted from workbook row 9 Scenario Scripts:38, identifier M5-07; a reviewer owns this row |
| `case:M6-01` | `manual` | drafted from workbook row 9 Scenario Scripts:40, identifier M6-01; a reviewer owns this row |
| `case:M6-02` | `manual` | drafted from workbook row 9 Scenario Scripts:41, identifier M6-02; a reviewer owns this row |
| `case:M6-03` | `manual` | drafted from workbook row 9 Scenario Scripts:42, identifier M6-03; a reviewer owns this row |
| `case:M6-04` | `manual` | drafted from workbook row 9 Scenario Scripts:43, identifier M6-04; a reviewer owns this row |
| `case:M6-05` | `manual` | drafted from workbook row 9 Scenario Scripts:44, identifier M6-05; a reviewer owns this row |
| `case:M6-06` | `manual` | drafted from workbook row 9 Scenario Scripts:45, identifier M6-06; a reviewer owns this row |
| `case:M7-01` | `manual` | drafted from workbook row 9 Scenario Scripts:47, identifier M7-01; a reviewer owns this row |
| `case:M7-02` | `manual` | drafted from workbook row 9 Scenario Scripts:48, identifier M7-02; a reviewer owns this row |
| `case:M7-03` | `manual` | drafted from workbook row 9 Scenario Scripts:49, identifier M7-03; a reviewer owns this row |
| `case:M7-04` | `manual` | drafted from workbook row 9 Scenario Scripts:50, identifier M7-04; a reviewer owns this row |
| `case:M7-05` | `manual` | drafted from workbook row 9 Scenario Scripts:51, identifier M7-05; a reviewer owns this row |
| `case:M8-01` | `manual` | drafted from workbook row 9 Scenario Scripts:53, identifier M8-01; a reviewer owns this row |
| `case:M8-02` | `manual` | drafted from workbook row 9 Scenario Scripts:54, identifier M8-02; a reviewer owns this row |
| `case:M8-03` | `manual` | drafted from workbook row 9 Scenario Scripts:55, identifier M8-03; a reviewer owns this row |
| `case:M8-04` | `manual` | drafted from workbook row 9 Scenario Scripts:56, identifier M8-04; a reviewer owns this row |
| `case:M9-01` | `manual` | drafted from workbook row 9 Scenario Scripts:58, identifier M9-01; a reviewer owns this row |
| `case:M9-02` | `manual` | drafted from workbook row 9 Scenario Scripts:59, identifier M9-02; a reviewer owns this row |
| `case:M9-03` | `manual` | drafted from workbook row 9 Scenario Scripts:60, identifier M9-03; a reviewer owns this row |
| `case:M9-04` | `manual` | drafted from workbook row 9 Scenario Scripts:61, identifier M9-04; a reviewer owns this row |
| `case:M9-05` | `manual` | drafted from workbook row 9 Scenario Scripts:62, identifier M9-05; a reviewer owns this row |
| `case:M9-06` | `manual` | drafted from workbook row 9 Scenario Scripts:63, identifier M9-06; a reviewer owns this row |
| `case:M9-07` | `manual` | drafted from workbook row 9 Scenario Scripts:64, identifier M9-07; a reviewer owns this row |
| `case:M9-08` | `manual` | drafted from workbook row 9 Scenario Scripts:65, identifier M9-08; a reviewer owns this row |
| `case:MKT-01` | `manual` | drafted from workbook row 3 Market Creation:6, identifier MKT-01; a reviewer owns this row |
| `case:MKT-02` | `manual` | drafted from workbook row 3 Market Creation:7, identifier MKT-02; a reviewer owns this row |
| `case:MKT-03` | `manual` | drafted from workbook row 3 Market Creation:8, identifier MKT-03; a reviewer owns this row |
| `case:MKT-04` | `manual` | drafted from workbook row 3 Market Creation:9, identifier MKT-04; a reviewer owns this row |
| `case:MKT-05` | `manual` | drafted from workbook row 3 Market Creation:10, identifier MKT-05; a reviewer owns this row |
| `case:MKT-06` | `manual` | drafted from workbook row 3 Market Creation:11, identifier MKT-06; a reviewer owns this row |
| `case:MKT-07` | `manual` | drafted from workbook row 3 Market Creation:12, identifier MKT-07; a reviewer owns this row |
| `case:MKT-08` | `manual` | drafted from workbook row 3 Market Creation:14, identifier MKT-08; a reviewer owns this row |
| `case:MKT-09` | `manual` | drafted from workbook row 3 Market Creation:15, identifier MKT-09; a reviewer owns this row |
| `case:MKT-10` | `manual` | drafted from workbook row 3 Market Creation:16, identifier MKT-10; a reviewer owns this row |
| `case:MKT-11` | `manual` | drafted from workbook row 3 Market Creation:17, identifier MKT-11; a reviewer owns this row |
| `case:MKT-12` | `manual` | drafted from workbook row 3 Market Creation:19, identifier MKT-12; a reviewer owns this row |
| `case:MKT-13` | `manual` | drafted from workbook row 3 Market Creation:20, identifier MKT-13; a reviewer owns this row |
| `case:MKT-14` | `manual` | drafted from workbook row 3 Market Creation:21, identifier MKT-14; a reviewer owns this row |
| `case:MKT-15` | `manual` | drafted from workbook row 3 Market Creation:22, identifier MKT-15; a reviewer owns this row |
| `case:MKT-16` | `manual` | drafted from workbook row 3 Market Creation:24, identifier MKT-16; a reviewer owns this row |
| `case:MKT-17` | `manual` | drafted from workbook row 3 Market Creation:25, identifier MKT-17; a reviewer owns this row |
| `case:MKT-18` | `manual` | drafted from workbook row 3 Market Creation:26, identifier MKT-18; a reviewer owns this row |
| `case:MKT-19` | `manual` | drafted from workbook row 3 Market Creation:28, identifier MKT-19; a reviewer owns this row |
| `case:MKT-20` | `manual` | drafted from workbook row 3 Market Creation:29, identifier MKT-20; a reviewer owns this row |
| `case:MKT-21` | `manual` | drafted from workbook row 3 Market Creation:30, identifier MKT-21; a reviewer owns this row |
| `case:MKT-22` | `manual` | drafted from workbook row 3 Market Creation:32, identifier MKT-22; a reviewer owns this row |
| `case:MKT-23` | `manual` | drafted from workbook row 3 Market Creation:33, identifier MKT-23; a reviewer owns this row |
| `case:MKT-24` | `manual` | drafted from workbook row 3 Market Creation:34, identifier MKT-24; a reviewer owns this row |
| `case:SET-01` | `manual` | drafted from workbook row 0 Setup:6, identifier SET-01; a reviewer owns this row |
| `case:SET-02` | `manual` | drafted from workbook row 0 Setup:7, identifier SET-02; a reviewer owns this row |
| `case:SET-03` | `manual` | drafted from workbook row 0 Setup:8, identifier SET-03; a reviewer owns this row |
| `case:SET-04` | `manual` | drafted from workbook row 0 Setup:9, identifier SET-04; a reviewer owns this row |
| `case:SET-05` | `manual` | drafted from workbook row 0 Setup:10, identifier SET-05; a reviewer owns this row |
| `case:SET-06` | `manual` | drafted from workbook row 0 Setup:11, identifier SET-06; a reviewer owns this row |
| `case:WAL-01` | `manual` | drafted from workbook row 7 Wallet Matrix:6, identifier WAL-01; a reviewer owns this row |
| `case:WAL-02` | `manual` | drafted from workbook row 7 Wallet Matrix:7, identifier WAL-02; a reviewer owns this row |
| `case:WAL-03` | `manual` | drafted from workbook row 7 Wallet Matrix:8, identifier WAL-03; a reviewer owns this row |
| `case:WAL-04` | `manual` | drafted from workbook row 7 Wallet Matrix:10, identifier WAL-04; a reviewer owns this row |
| `case:WAL-05` | `manual` | drafted from workbook row 7 Wallet Matrix:12, identifier WAL-05; a reviewer owns this row |
| `case:WAL-06` | `manual` | drafted from workbook row 7 Wallet Matrix:13, identifier WAL-06; a reviewer owns this row |
| `case:WAL-07` | `manual` | drafted from workbook row 7 Wallet Matrix:14, identifier WAL-07; a reviewer owns this row |
| `case:WRP-01` | `manual` | drafted from workbook row 6 Wrappers:5, identifier WRP-01; a reviewer owns this row |
| `case:WRP-02` | `manual` | drafted from workbook row 6 Wrappers:6, identifier WRP-02; a reviewer owns this row |
| `case:WRP-03` | `manual` | drafted from workbook row 6 Wrappers:7, identifier WRP-03; a reviewer owns this row |
| `case:WRP-04` | `manual` | drafted from workbook row 6 Wrappers:8, identifier WRP-04; a reviewer owns this row |
| `case:WRP-05` | `manual` | drafted from workbook row 6 Wrappers:9, identifier WRP-05; a reviewer owns this row |
| `case:WRP-06` | `manual` | drafted from workbook row 6 Wrappers:10, identifier WRP-06; a reviewer owns this row |
| `case:WRP-07` | `manual` | drafted from workbook row 6 Wrappers:11, identifier WRP-07; a reviewer owns this row |

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

