# SOURCES.md — Crossref adjudication of the 14 DOI conflicts

- Generated: 20260815T122908Z
- Script: `scripts/apply_doi_conflict_resolutions.py` @ commit `e9f6ad9`
- Mode: APPLIED to SOURCES.md
- Method: Crossref `query.bibliographic` by paper TITLE, not by resolving either candidate.
  A DOI that resolves only proves it points at *some* paper, not at *this* one.

## Outcome

| | count |
|---|---|
| conflicts adjudicated | 17 |
| hand-verified DOI correct | 13 |
| **neither candidate correct** | **1** |
| as-drafted DOI correct | 0 |

The as-drafted DOI lost **14 of 14**, and the printed volume was wrong in 12 of those —
so the volume:article line was corrected in the same pass, not just the DOI.

## Per-entry

| entry | winner | new DOI | new citation | evidence |
|---|---|---|---|---|
| A6 | verified | `10.1016/j.enconman.2024.118805` | *Energy Conversion and Management* 315:118805. | Crossref: Energy Conversion and Management 315, art. 118805, 2024 |
| A7 | verified | `10.1016/j.egyai.2023.100327` | *Energy and AI* 15:100327 (issue year 2024; DOI suffix reads 2023 — online-first). | Crossref: Energy and AI 15, art. 100327, published 2024 |
| B1 | verified | `10.1016/j.solmat.2021.111432` | *Solar Energy Materials and Solar Cells* 234:111432. | Crossref: Sol. Energy Mater. Sol. Cells 234, art. 111432, 2022. The PII S0927024821004736 already in the entry encodes a 2021 submission, corroborating the .2021. suffix against the drafted .2022. |
| B4 | verified | `10.1016/j.energy.2024.131584` | *Energy* 301:131584. | Crossref: Energy 301, art. 131584, 2024 |
| B5 | verified | `10.1007/s11630-024-2023-z` | *J. Thermal Science* 33(6):2221–2234. | Crossref: Journal of Thermal Science 33(6):2221-2234, 2024 |
| C1 | verified | `10.1016/j.icheatmasstransfer.2024.108221` | *Int. Communications in Heat and Mass Transfer* 159:108221. | Crossref: Int. Comm. Heat Mass Transfer 159, art. 108221, 2024 — volume 159 was already correct here, only the article number was wrong |
| C7 | neither | `10.1016/j.apenergy.2022.119555` | *Applied Energy* 323:119555. | Crossref: Applied Energy 323, art. 119555, 2022. NEITHER candidate was right — the drafted DOI gave 325:119921 and the hand-verified copy gave 10.1016/j.applthermaleng.2025.126209, an Applied Thermal Engineering 2025 paper. This is the one row where the hand-verified column failed. |
| C9 | verified | `10.1016/j.icheatmasstransfer.2024.107734` | *Int. Communications in Heat and Mass Transfer* 157:107734. | Crossref: Int. Comm. Heat Mass Transfer 157, art. 107734, 2024 |
| E3 | verified | `10.1016/j.enconman.2023.117551` | Management* 294:117551. | Crossref: Energy Conversion and Management 294, art. 117551, 2023 |
| F1 | verified | `10.1016/j.enconman.2023.118046` | *Energy Conversion and Management* 301:118046. | Crossref: Energy Conversion and Management 301, art. 118046, published 2024 (DOI suffix reads 2023 — online-first) |
| G1 | verified | `10.1063/5.0086032` | *AIP Conference Proceedings* 2445:090009 (SOLARPACES 2020). | Crossref: AIP Conf. Proc. 2445, art. 090009, 2022, SOLARPACES 2020. The AIP suffix encodes no article number, so no cross-check was possible before this. |
| G3 | verified | `10.1016/j.enconman.2023.116989` | Conversion and Management* 284:116989. | Crossref: Energy Conversion and Management 284, art. 116989, 2023 |
| H2 | verified | `10.1016/j.energy.2024.131548` | *Energy* 300:131548. | Crossref: Energy 300, art. 131548, 2024 (an SSRN preprint of the same title also exists at 10.2139/ssrn.4696050 — cite the journal version) |
| I7 | verified | `10.1016/j.enconman.2022.115366` | *Energy Conversion and Management* 256:115366. | Crossref: Energy Conversion and Management 256, art. 115366, 2022 — volume 256 was already correct, only the article number was wrong |
| A4 | found (was MISSING_DOI) | `` | Mammadov & Kalbaliyev (2026). "Performance Assessment of Supercritical CO₂ Brayton Cycles in Solar Power Tower Systems." *Topical Issues of Technical Sciences* 4(5), art. n19. - **DOI:** 10.47390/ts-v4i5y2026n19  *[DOI verified 2026-08-15 — Crossref]* - **Key numbers:** 4 sCO₂ configs in solar tower at **fixed T_turb,in = 700 °C, P = 25 MPa,   T_amb = 20 °C, Q = 120 MWth**; recompression η = **50.7%** (pre-comp 44.5, regen 37.7,   simple 13%). Close to our 720 °C/25 MPa smoke test (η_calc 0.4926) → useful independent   efficiency cross-check. - ⚠ **Venue caution (assessed 2026-08-15).** *Topical Issues of Technical Sciences*   (Techscience.uz) is a low-profile regional outlet, not indexed in the major abstracting   databases. The DOI is registered and resolves, but this entry should carry **no evidential   weight on its own** — it is a soft corroboration of an efficiency magnitude already   established by A0/A5/A6, never a validation anchor. Per §J's exclusion policy, it is kept   (its number is plausible and it is used only as a cross-check) but explicitly discounted. | Crossref: Topical Issues of Technical Sciences 4(5), 2026, art. n19, authors Mammadov & Kalbaliyev, DOI 10.47390/ts-v4i5y2026n19 |
| D1 | found (was MISSING_DOI) | `` | - **D1. Liu & Xiao 2023**, *Energy* 282:128732 — "Molecular dynamics investigation of   thermo-physical properties of molten salt with nanoparticles for solar energy   application." General nano-in-salt MD method reference.   DOI: 10.1016/j.energy.2023.128732  *[DOI verified 2026-08-15 — Crossref]*  [C] | Crossref: Energy 282, art. 128732, 2023, authors Liu & Xiao. Volume 282 was already correct; the title in the entry was a paraphrase ('MD' for 'Molecular dynamics', 'thermophysical' for 'thermo-physical') and is now exact. |
| D3 | found (was MISSING_DOI) | `` | - **D3. Mirahmad et al. 2025**, *Nanomaterials* 15(4):302 — "Beyond Thermal Conductivity:   A Review of Nanofluids for Enhanced Energy Storage and Heat Transfer." NPs raise k but   can lower c_p; **viscosity rise is the recurring drawback**. Framing citation for the   pumping-power objective. (Review — use for framing, not primary quantitative data.)   DOI: 10.3390/nano15040302  *[DOI verified 2026-08-15 — Crossref]*  [C] | Crossref: Nanomaterials 15(4), art. 302, 2025, authors Mirahmad, Shankar Kumar, Pato Doldán, Prieto Rios, Díez-Sierra. Title confirms it is a review, matching the entry's existing 'use for framing, not primary data' caveat. |
| D2 | verified (not a conflict — volume/title completed) | `` | - **D2. Yang et al. 2023**, *J. Energy Storage* 63:107015 — "New insights into the   heat capacity enhancement of nano-SiO₂ doped alkali metal chloride molten salt for   thermal energy storage: A molecular dynamics study." SiO₂ in KCl/NaCl/LiCl, Buckingham potential; | Crossref: Journal of Energy Storage 63, art. 107015, 2023 |
