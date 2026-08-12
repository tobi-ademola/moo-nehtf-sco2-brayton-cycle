# PROPERTIES.md — SEED (Session C research pass)

> Nano-HTF property correlations, coefficients, provenance. Includes the MD-viscosity note.
> This is a PROVENANCE seed — numeric coefficients still come from the Obj1 property module;
> this file records what each correlation is anchored to and where the defensible citations live.
> Full source entries in `SOURCES.md` section B (properties) and section C (viscosity/MD).

**System:** CuO nanoparticles in ternary chloride eutectic **NaCl-KCl-MgCl2**.
**Loadings characterized (prior work):** base + 3 loadings. Target T-range: ~700-800 C hot end.

---

## Property provenance map

| Property | Trend to enforce | Primary anchor | Cross-check | Status |
|---|---|---|---|---|
| Density rho(T,phi) | rho down linear in T; up with phi | Xu 2022 (solmat 111649); Han 2020 | De Stefanis 2024 | anchored |
| Specific heat c_p(T,phi) | ~T-invariant at const P; up with phi, PEAKS at low phi | **Han 2022 (+10.51% @0.7wt%)** | Wang 2023 (opt 3wt%); Yang 2023 (peak ~1wt%) | anchored |
| Thermal conductivity k(T,phi) | k down linear in T; up with phi | **Han 2022 (+15.85-39.55%)** | Lu 2021; Tian 2024 | anchored |
| Thermal diffusivity alpha(T,phi) | up with phi and T | **Han 2022 (+10.95-37.23%)** | — | anchored |
| **Viscosity mu(T,phi)** | mu down with T; up with phi | **MD-filled (ours)** | see note below | **needs defense sentence** |

---

## Viscosity provenance note (the MASTER_PLAN section 4 flag, RESOLVED)

Our CuO-loaded mu(T,phi) was filled via MD because **no experimental viscosity exists for any
CuO-loaded chloride salt** — this is a field-wide gap, not a local one. Defensible because:

1. **Method precedent, exact base salt:** Tian et al. 2024 (10.1016/j.icheatmasstransfer.2024.107837)
   computes MD viscosity of nanoparticle-in-NaCl-KCl-MgCl2 (SiO2/Al2O3; +63.88% for SiO2 @870K).
   Same salt, same method class, different particle -> establishes the approach + magnitude bracket.
2. **Base-salt mu(T) anchors (phi=0 endpoint):** Jiang 2024 (molliq 124854), Xu 2023 (ACS AMI),
   Xu 2022 (solmat 111649), De Stefanis 2024 (fnuen 1341754), Lu 2021 (KCl-MgCl2).
   Our MD mu at phi=0 should reproduce these within their stated ~<8% MD error (Lu 2021).
3. **Justification quote available:** De Stefanis 2024 states chloride experimental data are
   "scarce and entail large uncertainties," explicitly endorsing MD as the viable route.

**Thesis sentence (draft):** "In the absence of experimental viscosity data for CuO-loaded
chloride eutectics — a gap common to the entire nano-chloride literature, where reported
nanoparticle viscosities are themselves MD-derived (e.g. SiO2/Al2O3 in NaCl-KCl-MgCl2,
Tian et al. 2024) — the viscosity of the CuO-enhanced HTF was obtained by molecular-dynamics
simulation, with the phi=0 base-salt viscosity validated against published MD correlations for
MgCl2-NaCl-KCl (Jiang et al. 2024; Xu et al. 2022) to within their reported uncertainty."

---

## VALIDATION action for next session
- [ ] Confirm our MD mu at phi=0 lands within ~8% of Jiang 2024 / Xu 2022 base-salt mu(T). Log the
      % delta in VALIDATION.md as an internal consistency check for the viscosity module.
- [ ] Verify exact vol/page/article numbers + DOIs flagged "(fetch at cite)" in SOURCES.md section E
      before thesis submission (several ScienceDirect pages blocked automated fetch this session).
