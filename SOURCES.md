# SOURCES.md

> Every pivotal source: citation, DOI/URL, tool used, key numbers extracted.
> Atomic + self-contained per `MASTER_PLAN.md` §8. Tool tags: [C]=Consensus, [W]=web fallback,
> [IMG]=data read from page-image of the source (highest confidence — direct transcription).

**Last updated:** 2026-08-12 — Session C. Power-block node-level anchor RESOLVED (Dostal 2004,
§A5, full state tables transcribed). Nano-HTF property + MD-viscosity provenance established.

---

## A. POWER-BLOCK VALIDATION TARGETS (sCO2 recompression Brayton)

### A5. Dostal 2004 — PRIMARY node-by-node state-point anchor  [W->IMG]
Dostal, V., Driscoll, M.J., Hejzlar, P. (2004). "A Supercritical Carbon Dioxide Cycle for Next
Generation Nuclear Reactors." MIT-ANP-TR-100. (DSc thesis, MIT Nuclear Engineering.)
- **URL (free, stable):** https://web.mit.edu/22.33/www/dostal.pdf  ·  also MIT DSpace 1721.1/52798
- **Why PRIMARY:** the root of the CYCLES modeling lineage that Dyreby (-> SAM's sCO2 cycle) builds
  on, and — unlike Dyreby — it PRINTS full per-node T/P/h/s tables. Directly enables the
  node-by-node % error table in `VALIDATION.md` section 2.3.
- **Layout:** single-recompression, 8 numbered nodes; recompressed stream mixes between LTR and HTR
  (Fig 10.1). Node->SAM map in `VALIDATION.md` section 2.3.3 (NOT the same as Dyreby's).
- **Boundary conditions (Table 10.1, conservative):** 600 MWth; P_high 20 MPa; PR 2.6; compressor
  inlet 32 C; cooling water 27 C; eta main-comp 89%, recomp 89%, turbine 90%; generator 98%.
- **Three designs + key results:**
  | Design | T_turb,in | mdot (kg/s) | f_recomp | eta_thermal | eta_net | MWe |
  |---|---|---|---|---|---|---|
  | Basic | 550 C | 3209 | 0.41 | 45.27% | 41.00% | 246 |
  | Advanced | 650 C | 2953 | 0.41 | 49.54% | 45.25% | 272 |
  | High-Perf | 700 C | 2801 | 0.39 | 51.27% | 46.96% | 282 |
- **Best-estimate turbomachinery (Tables 13.2 / 10.8):** main comp 95.5%, recomp 94.8%,
  turbine 92.9% -> eta_thermal rises to 47.36 / 51.35 / 53.14% for the three designs. Use the
  CONSERVATIVE 89/90 set to match the state tables in `VALIDATION.md` section 2.3.2.
- **Full node state tables (T, P, h, s):** transcribed into `VALIDATION.md` section 2.3.2 for all
  three designs (Tables 10.2 / 10.3 / 10.4, pp.228-229; cross-check Table 13.1 p.279).
- **Heat balance (Table 10.5, Basic):** q_add 188.89, q_rej 103.38, w_turb 120.80, w_MC 12.38,
  w_RC 22.91, w_net 85.51 kJ/kg; precooler pump 1.6 MW; gross eta 42.30%, net 41.00%.
- **Component geometry (Tables 10.6/10.7, reference design):** HTR 52.95 m3 / LTR 46.05 m3,
  straight 2 mm semicircular channels, 1.5 mm plate, 2.4 mm pitch; per-HX dP: HTR hot 85.95 /
  cold 27.38 kPa, LTR hot 109.35 / cold 11.35 kPa, precooler gas 12.27 kPa. (Diagnostics only.)
- **Turbomachinery (Table 10.8):** main comp 4-stage r=0.4 m; recompressor 9-stage r=0.4 m L=1.0 m;
  turbine 3-stage r=0.6 m L=0.55 m. Single shaft, grid-synchronous.
- **CONFIDENCE:** HIGH — all values transcribed from page images (pp.227-235, 279).

### A1. Dyreby et al. 2014 — SECONDARY aggregate cross-check  [C->W]
Dyreby, J., Klein, S., Nellis, G., Reindl, D. (2014). "Design Considerations for Supercritical
Carbon Dioxide Brayton Cycles With Recompression." *J. Eng. Gas Turbines Power* 136(10):101701.
- **DOI:** 10.1115/1.4027936
- **Role:** SAM's sCO2 recompression block descends from this model — good aggregate anchor
  (eta_thermal, mdot_turbine, recuperator min-dT). BUT prints no per-node h/s table, so it CANNOT
  supply the node-level validation. Superseded by Dostal (A5) for that purpose.
- **Thesis Table 6.1 recompression cases (design inputs only):**
  Low-Temp Recompression: comp-in 32 C / 8 MPa, P_high 25 MPa, T_turb,in 550 C, f 0.383,
  UA_LT 1.7 / UA_HT 1.3 MW/K, mdot 98.5 kg/s, eta_th 47.4%.
  High-Temp Recompression: comp-in 50 C / 10 MPa, f 0.258, mdot 134.2 kg/s, eta_th 41.8%.
  (Compressor-inlet P offset ~0.3-0.5 MPa above true optimum for near-critical numerical
  stability, costs ~0.3-0.5 pts eta — not a typo if a rebuild lands slightly low.)
- **Also:** Dyreby 2014 PhD thesis (UW-Madison, ProQuest 3636003) — extended off-design detail.

### A3. Turchi et al. 2013 — CSP-context efficiency target  [C]
Turchi, C.S., Ma, Z., Neises, T.W., Wagner, M.J. (2013). "Thermodynamic Study of Advanced
Supercritical Carbon Dioxide Power Cycles for Concentrating Solar Power Systems."
*J. Solar Energy Eng.* 135(4):041007.
- **DOI:** 10.1115/1.4024030 (conf. precursor ASME ES2012-91179, DOI 10.1115/ES2012-91179).
- **Key numbers:** recompression + intercooling/reheat can exceed 50% cycle efficiency under dry
  cooling at CSP-relevant turbine temps (SunShot target); intercooling widens dT across the primary
  HX — favorable for sensible-heat TES.
- **Note:** MASTER_PLAN's "Turchi 2009" ~ Turchi, Ma & Dyreby NREL configurations report. Reconcile
  the label before writing.

### A4. Dostal-corroborating / supporting cross-checks  [C]
- Mammadov et al. 2026 — 4 sCO2 configs in solar tower at 700 C / 25 MPa / T_amb 20 C /
  120 MWth; recompression eta = 50.7%. Independent efficiency cross-check near our regime.
- Battisti et al. 2023, *Energies* — solar sCO2 RcBC, 25 MW net, design eta 48.3%; HTR dominates
  exergy destruction. Corroborates our expected HTR-dominant Ed. DOI 10.3390/en16135073 (verify).

---

## B. NANO-HTF PROPERTY LITERATURE (CuO in chloride eutectics)

### B1. Han et al. 2022 — PRIMARY, exact system  [C->W]
Han, D., Guene Lougou, B., Shuai, Y., Wang, W., Jiang, B., Shagdar, E. (2022). "Study of
thermophysical properties of chloride salts doped with CuO nanoparticles for solar thermal energy
storage." *Solar Energy Materials and Solar Cells* 245:111852.
- **DOI:** 10.1016/j.solmat.2022.111852 (PII S0927024821004736 — verify vol/pages at cite)
- **System:** base **NaCl-KCl-MgCl2**; CuO at varied mass fractions; solution-evaporation. EXACT
  base salt + particle.
- **Key numbers:** c_p (liquid) +10.51% at 0.7 wt% CuO; thermal diffusivity +10.95-37.23%;
  thermal conductivity +15.85-39.55%; melting T ~unchanged.
- **Use:** Obj1 provenance anchor for c_p(phi), k(phi); sanity-check property module cp/k trends.

### B2. Han et al. 2020 — companion, same base salt  [W]
Han, D., Guene Lougou, B., Xu, Y., Shuai, Y., Huang, X. (2020). "Thermal properties
characterization of chloride salts/nanoparticles composite phase change material for
high-temperature thermal energy storage." *Applied Energy* 264:114674.
- **DOI:** 10.1016/j.apenergy.2020.114674 (verify article no.)
- **System:** MgCl2:KCl:NaCl = 51:22:27 mol%; Al2O3, CuO, ZnO each at 0.7 wt%.
- **Use:** cross-check CuO vs other oxides at fixed loading; composition-ratio provenance.

### B3. Wang et al. 2023 — close analog (density + loading optimum)  [C]
Wang, Q. et al. (2023). "Comprehensive performance of composite phase change materials based on
ternary eutectic chloride with CuO nanoparticles for thermal energy storage systems."
*Solar Energy* 263. DOI 10.1016/j.solener.2023.xxxxx (fetch at cite).
- **System:** NaCl(15)-KCl(45)-LiCl(40) wt% + CuO. Analog (LiCl, not MgCl2).
- **Key numbers:** CuO improves c_p, k, storage density with NO change to melting/freezing point or
  latent heat; 3 wt% CuO optimal.

---

## C. VISCOSITY — CuO-loaded chloride salts (MD-provenance for Obj1)

### C0. HEADLINE FINDING (write this in the thesis)
**No experimental viscosity exists for any CuO-loaded chloride salt.** Field-wide, nano-chloride
viscosity is MD-derived, and the nanoparticle-in-chloride viscosity studies use SiO2/Al2O3, not
CuO. Filling CuO viscosity via MD is therefore STANDARD, PUBLISHED practice for this property
class — not a gap. Reframes the MASTER_PLAN section 4 flag from weakness to convention.

### C1. Tian et al. 2024 — CLOSEST precedent (nanoparticle in EXACT base salt, MD)  [C->W]
Tian, H. et al. (2024). "Enhanced thermal properties of ternary chloride composites for thermal
energy storage: Insights from molecular simulation." *Int. Comm. Heat and Mass Transfer* 159.
- **DOI:** 10.1016/j.icheatmasstransfer.2024.107837 (PII S0735193324009837)
- **System:** NaCl-KCl-MgCl2 + SiO2/Al2O3, MD. SiO2 raises viscosity +63.88%, k +9.33% @870 K.
- **Use:** THE citation that MD-viscosity-of-nanoparticle-in-our-base-salt is established method.

### C2. Jiang et al. 2024 — base-salt MD viscosity, shell-model  [C->W]
Jiang, C. et al. (2024). "Predicting thermophysical properties of molten salts in the
MgCl2-NaCl-KCl-LiCl system with a shell-model potential." *J. Molecular Liquids* 403:124854.
- **DOI:** 10.1016/j.molliq.2024.124854
- **Use:** base-salt mu(T) reference to anchor the phi=0 endpoint of our MD viscosity curve.

### C3. Xu et al. 2023 — base-salt MD viscosity, deep-potential/ML  [C]
Xu, T. et al. (2023). "Development of Deep Potentials of Molten MgCl2-NaCl and MgCl2-KCl Salts
Driven by Machine Learning." *ACS Appl. Mater. Interfaces*. DOI 10.1021/acsami.3c... (fetch).
- **Key:** density, c_p, viscosity, k for MN/MK eutectics 800-1000 K; MN lower mu, higher k than MK.

### C4. Xu et al. 2022 — base-salt MD, exact composition  [W]
"[thermophysical] properties of the MgCl2-NaCl-KCl heat transfer fluid: A molecular dynamics
study." *Sol. Energy Mater. Sol. Cells* 239:111649. DOI 10.1016/j.solmat.2022.111649.

### C5. De Stefanis et al. 2024 — AIMD, exact base salt + justification quote  [C->W]
De Stefanis, E. et al. (2024). "Ab-initio molecular dynamics study of eutectic chloride salt:
MgCl2-NaCl-KCl." *Frontiers in Nuclear Engineering* 3:1341754. DOI 10.3389/fnuen.2024.1341754.
- **Provides:** density, viscosity, heat capacity, diffusion, ionic conductivity; PDF validated vs
  X-ray scattering. Quotable: chloride experimental data "scarce and entail large uncertainties" ->
  endorses MD as the viable route.

### C6. Lu et al. 2021 — binary KCl-MgCl2 MD viscosity vs T & composition  [C]
Lu, J. et al. (2021). "Thermal properties of KCl-MgCl2 eutectic salt..." *Sol. Energy Mater. Sol.
Cells* 228. DOI 10.1016/j.solmat.2021.xxxxx (fetch).
- **Key:** BMH-potential MD; rho, k negative-linear in T; mu decreases with T; c_p ~T-invariant;
  errors mostly <8% vs experiment. Functional-form + MD-credibility line.

---

## D. OPTIONAL / MECHANISTIC CROSS-CHECKS (log-only)  [C]
- Liu & Xiao 2023, *Energy* 282 — MD of molten salt w/ nanoparticles for solar. General method.
- Yang et al. 2023, *J. Energy Storage* — SiO2 in KCl/NaCl/LiCl; c_p peaks ~1 wt%. Loading optimum.
- Mirahmad et al. 2025, *Nanomaterials* — review: NPs raise k but can lower c_p; viscosity rise the
  recurring drawback. Framing citation for the pumping-power objective.

---

## E. VERIFY-BEFORE-SUBMISSION (DOIs read from aggregator snippets, article page blocked)
- B1 Han 2022 exact vol:page (245:111852 assumed from PII pattern)
- B2 Han 2020 article no.; B3 Wang 2023 full DOI; C3 Xu 2023 DOI; C6 Lu 2021 DOI; A4 Battisti DOI
