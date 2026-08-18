# PROPERTIES.md — Objective 1 provenance record

> Nano-HTF property correlations, coefficients, provenance. Includes the MD-viscosity note.
> Numeric coefficients live in the Obj1 property module (`scripts/nanofluid_properties.py`);
> this file records what each correlation is anchored to and where the defensible citations live.
> Full source entries in `SOURCES.md` section B (properties) and section C (viscosity/MD).

**Last updated:** 2026-08-15 — Session G. ⚠ **This file was a provenance *seed*; the revised
Objective 1 makes it a *deliverable*.** The objective now reads "…with documented provenance for
each correlation", so the map below is what that requirement is discharged against. It also names
**thermal diffusivity** as one of five required property models — see the α row, which changed
status from an internal intermediate to a module output on 2026-08-15.

**System:** CuO nanoparticles in ternary chloride eutectic **NaCl-KCl-MgCl2**.
**Loadings characterized (prior work):** base + 3 loadings. Target T-range: ~700-800 C hot end.
**Machine-readable evidence:** `scripts/report_htf_properties.py` → `results/htf_properties_*.{md,csv}`
(provenance table + all five properties over 450–700 C + the α round-trip).

---

## Property provenance map

The five properties named by Objective 1, in its order.

| Property | Trend to enforce | Primary anchor | Cross-check | Status |
|---|---|---|---|---|
| Density rho(T,phi) | rho down linear in T; up with phi | A1 set Table 9 (Xu/Wang 2021); CuO rho back-solved from Han 2022 Table 2 | Xu 2022 (solmat 111649); Han 2020; De Stefanis 2024 | anchored; volume-fraction convention diverges from Han's table **by design** and is disclosed |
| Specific heat c_p(T,phi) | ~T-invariant at const P; up with phi, PEAKS at low phi | **Han 2022 (+10.51% @0.7wt%)** | Wang 2023 (opt 3wt%); Yang 2023 (peak ~1wt%) | anchored at 3 loadings; non-monotonic |
| Thermal conductivity k(T,phi) | k down linear in T; up with phi | **Han 2022 (+15.85-39.55%)** | Lu 2021; Tian 2024 | anchored; 0.7 wt% point derived from Han's own alpha/rho/cp |
| **Thermal diffusivity alpha(T,phi)** | up with phi and T | **DERIVED: alpha = k/(rho*cp)** — provenance inherited from its three constituents | **Han 2022 (+10.95-37.23%)**, the measured ratios k was back-derived from | ✅ **module OUTPUT since 2026-08-15**; round-trip closes to +0.65/+1.02/+4.01 % |
| **Viscosity mu(T,phi)** | mu down with T; up with phi | **MD-filled (ours)** | see note below | **needs defense sentence** |
| ~~Particle size d_p~~ | cp falls with larger d_p (Wei 2024) | **NONE — not represented** | — | ⚠ **BLOCKING GAP.** Obj 3 names d_p as a swept parameter; every fit above is size-blind. See `MASTER_PLAN.md` §10 |

### Why alpha is derived rather than fitted

It would be easy, and wrong, to fit alpha(T,phi) directly to Han's measured diffusivity ratios.
Doing so gives the module **four** independent correlations constrained by three degrees of
freedom, so alpha would be free to drift out of the identity alpha = k/(rho*cp) that defines it —
a silent inconsistency of exactly the kind this project has been bitten by elsewhere. Deriving it
instead makes the identity hold by construction and turns Han's measured ratios into a **test**
rather than a fit target. That test is informative in both directions: the derived alpha is
*expected* to run high, because the module uses the volume fraction for density where Han's table
used the mass fraction, so a residual near zero would mean that deliberate divergence had silently
reverted. Measured offsets (500 C): **+0.65 % at 0.2 wt%, +1.02 % at 0.7 wt%, +4.01 % at 2.0 wt%**,
monotonic in loading as the explanation requires, and fully accounted for
(`scripts/nanofluid_properties.py` `check_diffusivity_roundtrip`).

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

## VALIDATION actions
- [ ] Confirm our MD mu at phi=0 lands within ~8% of Jiang 2024 / Xu 2022 base-salt mu(T). Log the
      % delta in VALIDATION.md as an internal consistency check for the viscosity module.
- [x] ~~Verify exact vol/page/article numbers + DOIs~~ — **done 2026-08-15**, every source
      reconciled against Crossref (`SOURCES.md` §J1/§J2).
- [x] ~~Expose thermal diffusivity~~ — **done 2026-08-15**, derived + round-trip checked.
- [ ] ⚠ **Decide how d_p enters the property model** — blocking for Objective 3's particle-size
      sweep. Three options in `MASTER_PLAN.md` §10; the choice must be recorded in `DECISIONS.md`.
      The candidate analogue anchor is `SOURCES.md` **B5 (Wei et al. 2024)**: MgO in a *different*
      ternary chloride, cp falling with larger particle size, 20 nm giving cp +38.2 %. Using it
      would put d_p on the same analogue footing the viscosity already stands on — acceptable if
      declared with the same candour, not acceptable if quietly presented as measured for CuO/A1.
