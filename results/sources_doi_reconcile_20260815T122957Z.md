# SOURCES.md <- hand-verified DOI reconcile

- Generated: 20260815T122957Z
- Script: `scripts/reconcile_sources_dois.py` @ commit `e9f6ad9`
- Base (structure): `SOURCES.md`
- Verified (DOIs):  `SOURCES - Copy.md`
- Mode: report only, base untouched

| status | count | meaning |
|---|---|---|
| CONFIRMED | 44 | same DOI in both files -- hand check carries over |
| FILLED | 0 | placeholder in base, real DOI in verified copy |
| CHANGED | 1 | different real DOIs -- CONFLICT, needs adjudication |
| MISSING_DOI | 0 | real source, no DOI in EITHER file -- hand lookup outstanding |
| NO_DOI | 12 | section heading, or DOI-less by nature (thesis / NREL report) |

## Conflicts and cross-check failures

`article_no_crosscheck = DISAGREES` means the verified DOI and the volume:article number
printed in the citation line cannot both be right -- fix the citation metadata too.

| entry | status | base DOI | verified DOI | crosscheck | action |
|---|---|---|---|---|---|
| B3 | CONFIRMED | `10.1016/j.solener.2022.12.051` | `10.1016/j.solener.2022.12.051` | DISAGREES | skip |
| B5 | CONFIRMED | `10.1007/s11630-024-2023-z` | `10.1007/s11630-024-2023-z` | DISAGREES | skip |
| C7 | CHANGED | `10.1016/j.apenergy.2022.119555` | `10.1016/j.applthermaleng.2025.126209` | DISAGREES | quarantine |

## Substitutions --apply WOULD make (base untouched this run)

_none_
