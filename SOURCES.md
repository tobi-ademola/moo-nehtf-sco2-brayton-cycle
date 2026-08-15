# SOURCES.md

> **Tally: 17 already logged + 33 newly added + **A0 Dostal 2004** (restored 2026-08-15) = 51 sources.**
> Every pivotal source: citation, DOI, tool used, key numbers extracted.
> Atomic + self-contained per MASTER_PLAN §8. Tool tags: [C]=Consensus, [C→W]=Consensus-found + web-verified, [W]=web fallback.

**Last updated:** 2026-08-15 — reconciled against the hand-verified DOI set in `SOURCES - Copy.md`
(`scripts/reconcile_sources_dois.py`): **17 DOIs confirmed**, **14 placeholders filled**, and every
one of those 31 now carries an inline `*[DOI verified <date>]*` marker so the check survives the
next rewrite. **All 14 conflicts were then adjudicated against Crossref and closed** (§J1) — the
as-drafted DOI lost 14 of 14, and **C7 needed a third value neither file held**. The **3 entries
with no DOI in either file** (A4, D1, D3) were found the same way (§J2). **§A0 Dostal 2004 was
added**: the project's adopted baseline had never been logged here at all. **Every source now
carries a verified DOI except the two that are DOI-less by nature** (A0, E2) and §A8's three
deferred acquisitions (§J3). Previously, 2026-08-13
(Session E): added **§A8**, the second-anchor assessment answering the "single-point coincidence"
objection to the power-block validation; corrected the **F2 Battisti 2023** citation (wrong issue
and article number).

> **Session D note on tool policy & quota.** Consensus was used first for every category
> (4 searches, exhausting the month's free quota). Web search was used only as a documented
> fallback for (a) canonical pre-2020 method references Consensus does not surface (NSGA-II),
> and (b) NREL/SAM system-modeling references that live in NREL's own publication registry
> rather than the indexed journal corpus. Those are tagged [W]. All 2020–2026 journal entries
> below were surfaced by Consensus and are tagged [C] (or [C→W] where a DOI/volume was
> web-verified). Eligibility window 2020–2026 honored; three pre-2020 entries are included and
> each carries a one-line pivotal-justification.

---

## A. POWER-BLOCK VALIDATION TARGETS (sCO₂ recompression Brayton)

### A0. Dostal, Driscoll & Hejzlar 2004 — **THE PRIMARY node-by-node anchor; the adopted baseline**  [W]  *(MIT report / PhD thesis)*
*Added 2026-08-15. This entry was missing from SOURCES.md entirely — the register's most pivotal
source was cited throughout `VALIDATION.md` and `CLAUDE.md` §7 but never logged here.*

Dostal, V., Driscoll, M.J., Hejzlar, P. (2004). "A Supercritical Carbon Dioxide Cycle for Next
Generation Nuclear Reactors." **MIT-ANP-TR-100**, MIT Center for Advanced Nuclear Energy Systems,
March 2004. Also issued as V. Dostal, PhD thesis, Dept. of Nuclear Engineering, MIT (advisor
M.J. Driscoll).
- **DOI:** n/a (MIT technical report / dissertation — DOI-less by nature). Free full text:
  https://web.mit.edu/22.33/www/dostal.pdf · DSpace: https://dspace.mit.edu/handle/1721.1/17746
  *[identifiers verified 2026-08-15]*
- **Peer-reviewed companion**, for where a journal citation is required: Dostal, V., Hejzlar, P.,
  Driscoll, M.J. (2006). "High-Performance Supercritical Carbon Dioxide Cycle for Next-Generation
  Nuclear Reactors." *Nuclear Technology* 154(3):265–282. **DOI:** 10.13182/nt154-265
  *[DOI verified 2026-08-15 — Crossref]*. Note this is the 700 °C High-Performance design **only**;
  the 550/650 °C tables and the full per-node data exist solely in the 2004 report.
- **Why pivotal (pre-2020, unavoidable):** it publishes **full per-node state tables (T, P, h, s)**
  for three recompression designs — Basic 550 °C (Table 10.2), Advanced 650 °C (10.3),
  High-Performance 700 °C (10.4) — which is what makes node-by-node validation possible at all.
  A1/A2 Dyreby give design *inputs* only (Table 6.1), not per-node h/s. No post-2020 source
  publishes comparable state-point detail, so there is no substitute.
- **Key numbers (High-Performance 700 °C = our adopted case F):** Dostal reports η_thermal
  **51.27 %**; our PySAM model returns **0.51289** (**+0.019 pp**), and **all 8 published nodes
  match to ≤0.070 % in *h*, 0.045 % in *s*, 0.000 % in *P*.** Shared boundary conditions across all
  three designs: compressor inlet **32 °C**, P_high **20 MPa**, PR **2.6**.
- ⚠ **Deliberate, evidenced departure from a published input:** f_rc is taken as **0.4097**, not the
  **0.39** stated in his Table 10.1. His Table 10.1 *f* and his Table 10.4 state points are separate
  data that disagree; closing the mixer on his own published enthalpies gives 0.4097, and
  justifying 0.39 would require η_rc = 0.752 against his stated 0.89. The Advanced 650 °C design,
  used as a control, needs only 0.932 to justify its stated 0.41 — so the method is sound and the
  contrast is real. Full argument: `VALIDATION.md` §2.3.4a; see also `CLAUDE.md` §7.
  **Do not "correct" this back to 0.39.**
- **Use:** PRIMARY anchor for `VALIDATION.md` §2.3 and the adopted baseline in `CLAUDE.md` §7. The
  550/650 °C designs are also the zero-cost second-anchor test proposed in **§A8(a)**.
- **Note:** MIT technical report / dissertation, not peer-reviewed journal — flagged as such; the
  2006 *Nuclear Technology* companion above carries the peer review for the 700 °C design.
- **Data provenance:** state points transcribed from page images 2026-08-12 (Tables 10.1–10.8,
  13.1–13.2, pp. 227–235, 279). HIGH confidence — tabular transcription, not figure-read.

### A1. Dyreby et al. 2014 — SECONDARY aggregate cross-check (see A0 for the primary)  [C→W]
Dyreby, J., Klein, S., Nellis, G., Reindl, D. (2014). "Design Considerations for
Supercritical Carbon Dioxide Brayton Cycles With Recompression." *J. Eng. Gas Turbines
Power* 136(10):101701.
- **DOI:** 10.1115/1.4027936  *[DOI verified 2026-08-15]*
- **Why pivotal (pre-2020, unavoidable):** SAM's sCO₂ recompression power block is built on
  this model/method (recuperators modeled at constant conductance UA; near-critical CO₂
  property handling). Validating our PySAM cycle against it = validating against the model's
  own ancestor. Canonical method reference, no post-2020 substitute.
- **Key modeling choices:** constant-UA recuperators; static≈total fluid conditions assumed
  (component velocities low → properties evaluated at total conditions).
- **Use:** aggregate design-point cross-check only. **Superseded as the node-table source by A0** —
  Dyreby's Table 6.1 gives design inputs, not per-node h/s. Note also that agreement with Dyreby
  tests *implementation fidelity, not physics*, since SAM's sCO₂ block is built on this method
  (see the circularity note in §A8).

### A2. Dyreby 2014 PhD thesis — fullest state-point detail  [W]  *(thesis)*
Dyreby, J.J. (2014). "Modeling the Supercritical Carbon Dioxide Brayton Cycle with
Recompression." PhD thesis, University of Wisconsin–Madison. ProQuest 3636003.
- **DOI:** n/a (dissertation). ProQuest/UW handle: ProQuest 3636003.
- **Why pivotal:** extended design + off-design state-point tables (T, P, h; per-node)
  beyond the journal paper. Use for full node-by-node % error table.
- **Key numbers to extract on read:** design-point compressor inlet T/P, recompression
  fraction, UA split HTR/LTR, turbine inlet T, cycle η_thermal. (Extract at PDF read.)
- **Note:** thesis, not peer-reviewed journal — flagged as such; used only for state-point
  detail already peer-reviewed in A1.

### A3. Turchi et al. 2013 — CSP-context efficiency targets  [C]
Turchi, C.S., Ma, Z., Neises, T.W., Wagner, M.J. (2013). "Thermodynamic Study of Advanced
Supercritical Carbon Dioxide Power Cycles for Concentrating Solar Power Systems."
*J. Solar Energy Eng.* 135(4):041007.
- **DOI:** 10.1115/1.4024030  (conference precursor: ASME ES2012-91179,
  DOI 10.1115/ES2012-91179).  *[DOI verified 2026-08-15]*
- **Why pivotal (pre-2020):** canonical CSP-context statement of the >50% dry-cooled sCO₂
  target that frames this thesis's power-block objective; NREL-authored, no later equivalent.
- **Key numbers:** recompression + intercooling and/or reheat can exceed **50% cycle
  efficiency** under **dry cooling** at CSP-relevant turbine inlet temps (SunShot target);
  intercooling widens ΔT across the primary HX — favorable for sensible-heat TES.
- **Use:** config-level efficiency sanity target + citation for "why recompression."
- **Note:** the "Turchi 2009" in MASTER_PLAN §6 is almost certainly Turchi, Ma & Dyreby,
  "Supercritical Carbon Dioxide Power Cycle Configurations for Use in CSP" (NREL). Reconcile
  the citation label before writing.

### A4. Mammadov et al. 2026 — independent efficiency cross-check (not primary)  [C]
Mammadov & Kalbaliyev (2026). "Performance Assessment of Supercritical CO₂ Brayton Cycles
in Solar Power Tower Systems." *Topical Issues of Technical Sciences* 4(5), art. n19.
- **DOI:** 10.47390/ts-v4i5y2026n19  *[DOI verified 2026-08-15 — Crossref]*
- **Key numbers:** 4 sCO₂ configs in solar tower at **fixed T_turb,in = 700 °C, P = 25 MPa,
  T_amb = 20 °C, Q = 120 MWth**; recompression η = **50.7%** (pre-comp 44.5, regen 37.7,
  simple 13%). Close to our 720 °C/25 MPa smoke test (η_calc 0.4926) → useful independent
  efficiency cross-check.
- ⚠ **Venue caution (assessed 2026-08-15).** *Topical Issues of Technical Sciences*
  (Techscience.uz) is a low-profile regional outlet, not indexed in the major abstracting
  databases. The DOI is registered and resolves, but this entry should carry **no evidential
  weight on its own** — it is a soft corroboration of an efficiency magnitude already
  established by A0/A5/A6, never a validation anchor. Per §J's exclusion policy, it is kept
  (its number is plausible and it is used only as a cross-check) but explicitly discounted.
- **Note:** Battisti et al. 2023 (design η 48.3%, HTR-dominant ĖD) is logged in full at **F2**
  and cross-referenced there; not duplicated here.

### A5. Stamatellos & Stamatelos 2022 — realistic recuperator-limited efficiency ceiling  [C]
Stamatellos, G., Stamatelos, A. (2022). "Effect of Actual Recuperators' Effectiveness on the
Attainable Efficiency of Supercritical CO₂ Brayton Cycles for Solar Thermal Power Plants."
*Energies* 15(20):7773.
- **DOI:** 10.3390/en15207773  *[DOI verified 2026-08-15]*
- **Category:** sCO₂ recompression Brayton for CSP (thermodynamics + exergy).
- **Key numbers:** with realistic HTR/LTR heat-exchanger computation, thermal efficiency
  **does not exceed the 50% target**; a realizable total plant efficiency of **~37% at
  900 K turbine entry** is predicted — a "don't over-claim η" ceiling for our power block.
- **Use:** guards VALIDATION.md against optimistic-recuperator efficiency inflation.

### A6. Cu et al. 2024 — sCO₂ RcBC + particle/sCO₂ fluidized-bed HX, full system  [C]
Cu, W. et al. (2024). "Investigation of thermodynamic performances of particle/supercritical
CO₂ fluidized bed heat exchanger integrated with supercritical CO₂ recompression Brayton
cycle for concentrated solar power." *Energy Conversion and Management* 315:118805.
- **DOI:** 10.1016/j.enconman.2024.118805  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** integrated CSP–power-block system modeling; sensitivity analysis.
- **Key numbers:** power-cycle efficiency **50.5%**, fluidized-bed HX thermal efficiency
  **99.1%**, overall system thermal efficiency **32.2%**; overall η rises with turbine inlet T,
  falls with main-compressor inlet T, peaks at η≈**0.35** vs recompression fraction.
- **Use:** independent recompression-fraction-vs-η trend + receiver-to-cycle efficiency chain.

### A7. Turja et al. 2023 — ML+GA multi-objective sCO₂ CSP, config comparison  [C]
Turja, A. et al. (2023). "Multi-Objective Performance Optimization & Thermodynamic Analysis
of Solar Powered Supercritical CO₂ Power Cycles Using Machine Learning Methods & Genetic
Algorithm." *Energy and AI* 15:100327 (issue year 2024; DOI suffix reads 2023 — online-first).
- **DOI:** 10.1016/j.egyai.2023.100327  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** sCO₂ config thermodynamics + multi-objective optimization bridge.
- **Key numbers:** compares Recompression, Partial-Cooling, Main-Compression-Intercooling at
  **15 MW**; advanced config improves performance by **1.68%** vs recompression and **7.87%**
  vs partial-cooling; GA + TOPSIS decision-making across climate variation.
- **Use:** config-ranking cross-check + precedent for GA+TOPSIS objective selection.

### A8. SECOND-ANCHOR ASSESSMENT — answering the "single-point coincidence" objection
*Added 2026-08-13 (Session E), after case F reproduced Dostal's 700 °C table to 0.07 %/node.*

**The objection has two halves, and they need different answers.** Conflating them is the trap:

| | Objection | Answer |
|---|---|---|
| (a) | "You matched at ONE turbine inlet temperature" | **Solved with data already on disk** — see below |
| (b) | "You matched ONE author's tables" | **Not answerable from the current library** |

**(a) — no new literature needed.** Dostal's **Basic 550 °C (Table 10.2)** and **Advanced 650 °C
(Table 10.3)** are already transcribed in `VALIDATION.md` §2.3.2. Re-running the case-F method at
those two TITs yields two more full node tables across a 150 °C span, at zero acquisition cost.

> **This is more than an extra data point — it is a falsifiable test of the f = 0.4097 finding.**
> `check_dostal_table_consistency.py` predicts the Advanced design's *stated* f = 0.41 is very
> nearly self-consistent (f_implied 0.4049, and justifiable with η_rc = 0.932), whereas the
> High-Performance design's stated 0.39 is not (would need η_rc = 0.752). **So the 650 °C case
> should reproduce well using Dostal's STATED f, while the 700 °C case does not.** If it does,
> the case-F argument is corroborated by an independent design. If it does not, the reasoning
> behind the adopted baseline is wrong and must be revisited. Run this before anything else.

**(b) — nothing in the library is a true independent node-level anchor.** Assessed honestly:

| Source | Why it does not close (b) |
|---|---|
| **A1/A2 Dyreby 2014** | Closest to node-level, but **CIRCULAR**: SAM's sCO₂ block is built on Dyreby's method, so agreement tests implementation fidelity, not physics. Worth running — but label it **verification**, never independent validation. |
| **A4 Mammadov 2026** | Same TIT (700 °C), aggregate η only (50.7 %), low-profile venue. |
| **A5 Stamatellos 2022** | An η *ceiling* guard (~900 K), not a state-point anchor. |
| **A6/A7, G-series** | Config comparisons and CO₂ mixtures; no pure-CO₂ node tables. |
| **F2 Battisti 2023** | **Best independent anchor already held — but for the EXERGY layer, not nodes.** 25 MW, η 48.3 %, independent code and site (Chile), and it reports **HTR-dominant exergy destruction**, which is exactly what case F must reproduce (ours: HTR 1164 kW of 2966 kW = 39 %, dominant ✓). Use it to validate the exergy ranking; it cannot validate state points. |

**Recommended acquisitions to close (b)**, best first — none verified for node-table content, as
all three are paywalled and could not be opened here:

1. **Padilla et al. 2015**, "Exergetic analysis of supercritical CO₂ Brayton cycles integrated
   with solar central receivers," *Applied Energy* 148:348–365, DOI 10.1016/j.apenergy.2015.03.048.
   **Best fit:** CSP context, dry cooling, recompression among its four configs, and
   **component-level exergy** — which is what this project's downstream work needs. Independent of
   the NREL/SAM/Dyreby lineage.
2. **Moisseytsev & Sienicki 2009**, *Nuclear Eng. & Design* 239:1362–1371,
   DOI 10.1016/j.nucengdes.2009.03.017. ANL's own code lineage, and a **470 °C TIT** — a far
   larger extrapolation than Dostal's span, so a much stronger coincidence test. Nuclear rather
   than CSP context; frame accordingly.
3. **Sarkar 2009**, "Second law analysis of supercritical CO₂ recompression Brayton cycle,"
   *Energy* 34(9):1172–1178. Widely-cited analytical component-exergy treatment; useful as an
   analytical cross-check even if node tables are absent.

**Also found (different purpose, not for this objection):** Neises & Turchi, "Steady-state
off-design modeling of the sCO₂ recompression cycle for CSP with two-tank sensible-heat storage,"
free full text at **OSTI.gov/pages/biblio/1726034**. This is provenance for the
`Sco2CspUdPcTables` → `TcsmoltenSalt` bridge (`CLAUDE.md` §3), not a validation anchor — same
circularity as Dyreby, since Neises wrote the ssc module.

---

## B. NANO-HTF PROPERTY LITERATURE (CuO in chloride eutectics)

### B1. Han et al. 2022 — PRIMARY, exact system  [C→W]
Han, D., Guene Lougou, B., Shuai, Y., Wang, W., Jiang, B., Shagdar, E. (2022). "Study of
thermophysical properties of chloride salts doped with CuO nanoparticles for solar thermal
energy storage." *Solar Energy Materials and Solar Cells* 234:111432.
- **DOI:** 10.1016/j.solmat.2021.111432  *[DOI verified 2026-08-15 — Crossref]*
- **System:** base **NaCl–KCl–MgCl₂**; CuO at varied mass fractions; solution-evaporation
  synthesis. **This is our exact base salt + particle.**
- **Key numbers (extracted):**
  - Specific heat (liquid phase): **+10.51%** at **0.7 wt% CuO** vs base salt.
  - Thermal diffusivity: **+10.95 – 37.23%** vs base salt (range over loadings/T).
  - Thermal conductivity: **+15.85 – 39.55%** vs base salt.
  - Melting temperature: ~unchanged vs base salt.
- **Use:** Obj1 provenance anchor for c_p(φ), k(φ); sanity-check property module cp/k trends.

### B2. Han et al. 2020 — companion, same base salt  [W]
Han, D., Guene Lougou, B., Xu, Y., Shuai, Y., Huang, X. (2020). "Thermal properties
characterization of chloride salts/nanoparticles composite phase change material for
high-temperature thermal energy storage." *Applied Energy* 264:114674.
- **DOI:** 10.1016/j.apenergy.2020.114674  *[DOI verified 2026-08-15]*
- **System:** ternary chloride **MgCl₂:KCl:NaCl = 51:22:27 mol%**; Al₂O₃, CuO, ZnO each
  dispersed at **0.7 wt%**.
- **Key numbers:** at 0.7 wt%, **Al₂O₃ gives the largest k gain (>48%** vs base salt) and best
  thermal stability; latent heat slightly lower than base salt; CuO and ZnO also enhance k/α.
- **Use:** cross-check CuO vs other oxides at fixed loading; composition-ratio provenance.

### B3. Wang et al. 2023 — close analog (density data)  [C]
Wang, Q. et al. (2023). "Comprehensive performance of composite phase change materials
based on ternary eutectic chloride with CuO nanoparticles for thermal energy storage
systems." *Solar Energy* 263:111852-analog.
- **DOI:** 10.1016/j.solener.2022.12.051  *[DOI verified 2026-08-15]*
- **System:** NaCl(15)–KCl(45)–LiCl(40) wt% + CuO; static-melt + mechanical stirring.
- **Key numbers:** CuO improves c_p, k, energy-storage density with **no change to
  melting/freezing point or latent heat**; **3 wt% CuO** identified as optimal loading.
- **Use:** analog for loading-optimum behavior; note LiCl (not MgCl₂) → analog not exact.

### B4. Huang et al. 2024 — Al₂O₃ in binary NaCl–KCl, MD + mechanism  [C]
Huang, Z. et al. (2024). "Enhancements in thermal properties of binary alkali chloride salt
by Al₂O₃ nanoparticles for thermal energy storage." *Energy* 301:131584.
- **DOI:** 10.1016/j.energy.2024.131584  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** nano-enhanced chloride properties (oxide analog) + enhancement mechanism.
- **System:** **NaCl(50)–KCl(50) mol%** + Al₂O₃, MD, 1100–1600 K, φ = 0–7%.
- **Key numbers:** at φ 0→7%, c_p **+≈14.9%**, dynamic viscosity **+34.8–38.6%**, k
  **+10.0–16.5%**; mechanism = negatively charged NP surface attracts Na⁺/K⁺ forming a
  compressed interfacial layer acting as a thermal conduit.
- **Use:** Al₂O₃ analog for the property-vs-loading trend AND the interfacial-layer mechanism
  cited in our MD-viscosity justification (viscosity-rises-with-loading precedent).

### B5. Wei et al. 2024 — MgO in ternary chloride, experiment + MD, big c_p gain  [C]
Wei, X. et al. (2024). "Experimental and Simulation Study on Enhancing Thermal Energy Storage
and Heat Transfer Performance of Ternary Chloride Eutectic Salt by Doping MgO Nanoparticles."
*J. Thermal Science* 33(6):2221–2234.
- **DOI:** 10.1007/s11630-024-2023-z  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** nano-enhanced chloride properties (oxide analog); mechanism.
- **System:** **NaCl:CaCl₂:MgCl₂ = 53:15:32 mol%** + nano-MgO; combined experiment + MD.
- **Key numbers:** **2.5 wt%, 20-nm MgO** gives **c_p +38.2%**; no heat-storage degradation
  after **1000 h at 600 °C**; MD shows a semi-solid interfacial layer; c_p falls with larger
  particle size.
- **Use:** strongest experimental c_p-enhancement + particle-size + thermal-stability evidence;
  supports interfacial-layer mechanism and the loading/size design space.

---

## C. VISCOSITY — CuO-loaded chloride salts (Task 3: the defensible-provenance file)

### C0. HEADLINE FINDING (write this in the thesis)
**No experimental viscosity exists for any CuO-loaded chloride salt in the literature.**
For nano-loaded chlorides, viscosity is MD-derived across the field, and the *nanoparticle*-
in-chloride viscosity studies that exist use **SiO₂/Al₂O₃**, not CuO. Therefore filling our
CuO viscosity via MD is **standard, published practice for this property class — not a gap
we are papering over.** This reframes the MASTER_PLAN §4 ⚠ flag from weakness to convention.

### C1. Tian et al. 2024 — CLOSEST precedent: nanoparticle-in-exact-base-salt MD viscosity [C→W]
Tian, H., Zhang, W., Kou, Z., Guo, C., Yu, Y., Zhou, J. (2024). "Enhanced thermal properties
of ternary chloride composites for thermal energy storage: Insights from molecular
simulation." *Int. Communications in Heat and Mass Transfer* 159:108221.
- **DOI:** 10.1016/j.icheatmasstransfer.2024.108221  *[DOI verified 2026-08-15 — Crossref]*
- **System:** **NaCl–KCl–MgCl₂** + SiO₂ / Al₂O₃ nanoparticles, MD.
- **Key numbers:** SiO₂ raises **viscosity +63.88%** and k +9.33% at 870 K; Al₂O₃ raises
  density +4.22%, c_p +4.18%. Mechanism: NPs modify cation–anion distance + diffusion.
- **Use:** THE citation that MD-viscosity-of-nanoparticle-in-our-base-salt is established
  method. Different particle (SiO₂/Al₂O₃ vs CuO) → cite as method precedent + magnitude
  bracket, not as a direct CuO value.

### C2. Jiang et al. 2024 — base-salt MD viscosity, polarizable shell model  [C→W]
Jiang, C., Guo, J., Andersson, D., Schwen, D., Benmore, C., Hoyt, N., Spencer, B. (2024).
"Predicting thermophysical properties of molten salts in the MgCl₂-NaCl-KCl-LiCl system
with a shell-model potential." *J. Molecular Liquids* 403:124854.
- **DOI:** 10.1016/j.molliq.2024.124854  *[DOI verified 2026-08-15]*
- **System:** MgCl₂-NaCl-KCl (± LiCl), classical MD, force-matched shell-model potential.
- **Provides:** density, c_p, **viscosity**, ionic self-diffusivity vs T; validated vs
  experiment + high-energy X-ray diffraction structure factor.
- **Use:** base-salt μ(T) reference to anchor the φ=0 endpoint of our MD viscosity curve.

### C3. Xu et al. 2023 — base-salt MD viscosity, deep-potential/ML  [C]
Xu, T. et al. (2023). "Development of Deep Potentials of Molten MgCl₂-NaCl and MgCl₂-KCl
Salts Driven by Machine Learning." *ACS Appl. Mater. Interfaces*.
- **DOI:** 10.1021/acsami.2c19272  *[DOI verified 2026-08-15]*
- **Key numbers:** density, RDF, c_p, **viscosity**, k for MN & MK eutectics at **800–1000 K**;
  MN has lower viscosity + higher k than MK (weaker Mg–Cl interaction).
- **Use:** second independent base-salt μ(T) anchor; DPMD-quality benchmark.

### C4. Xu et al. 2022 — base-salt MD, exact composition  [W]
Xu, ... (2022). "[thermophysical] properties of the MgCl₂–NaCl–KCl heat transfer fluid: A
molecular dynamics study." *Solar Energy Materials and Solar Cells* 239:111649.
- **DOI:** 10.1016/j.solmat.2022.111649  *[DOI verified 2026-08-15]*
- **Use:** base-salt property set (incl. transport) for our exact ternary HTF.

### C5. De Stefanis et al. 2024 — AIMD, exact base salt  [C→W]
De Stefanis, E., Ramic, K., Vidal, J., Zhao, Y., Gallington, L.C., Bedell, R., Liu, L.
(2024). "Ab-initio molecular dynamics study of eutectic chloride salt: MgCl₂–NaCl–KCl."
*Frontiers in Nuclear Engineering* 3:1341754.
- **DOI:** 10.3389/fnuen.2024.1341754  *[DOI verified 2026-08-15]*
- **Provides:** density, **viscosity**, heat capacity, diffusion coeff, ionic conductivity;
  PDF validated vs X-ray total scattering; μ compared to experiment for similar system.
- **Note:** explicitly frames MD as the viable route because chloride experimental data are
  "scarce with large uncertainties" — quotable justification for our MD approach.

### C6. Lu et al. 2021 — binary KCl–MgCl₂ MD viscosity vs T & composition  [C]
Lu, J. et al. (2021). "Thermal properties of KCl–MgCl₂ eutectic salt for high-temperature
heat transfer and thermal storage system." *Solar Energy Materials and Solar Cells* 228.
- **DOI:** 10.1016/j.solmat.2021.111130  *[DOI verified 2026-08-15]*
- **Key numbers:** BMH-potential MD; density & k **negative-linear in T**; shear viscosity
  decreases with T; c_p ~T-invariant at const P; errors mostly <8% vs experiment.
- **Use:** functional-form guidance (μ, k, ρ vs T) + the "errors <8%" MD-credibility line.

### C7. Xian et al. 2022 — SiO₂ in KNaCl₂, MD, viscosity + compressed-layer mechanism  [C]
Xian, L. et al. (2022). "Enhanced thermal energy storage performance of molten salt for the
next generation concentrated solar power plants by SiO₂ nanoparticles: A molecular dynamics
study." *Applied Energy* 323:119555.
- **DOI:** 10.1016/j.apenergy.2022.119555  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** MD-based property prediction of nano-in-chloride, incl. viscosity mechanism.
- **Key numbers:** max **k +25.28%**, c_p **+7.87%**; enhancement from a **~5 Å compressed
  interface layer** on the SiO₂ surface; reports k, μ, c_p vs NP volume fraction.
- **Use:** mechanism citation for interfacial-layer heat-transfer channel; SiO₂ viscosity/
  property-vs-φ precedent supporting the MD-viscosity approach.

### C8. Wang (Chao) et al. 2026 — many-particle SiO₂ MD, viscosity magnitude  [C]
Wang, C. et al. (2026). "Interfacial ion aggregation at SiO₂ nanoparticles enhances thermal
energy storage of chloride molten salts: a molecular dynamics study." *RSC Advances* 16.
- **DOI:** 10.1039/d5ra10091g  *[DOI verified 2026-08-15]*
- **Category:** MD-based property prediction; multi-particle (vs single-particle) model.
- **Key numbers:** with increasing SiO₂, **viscosity +≈51.21%**, c_p +8.25%, k +7.08%;
  compressed interfacial layer **~6 Å** from selective Na⁺/K⁺ adsorption.
- **Use:** most recent many-particle MD viscosity magnitude for NaCl–KCl; brackets our CuO
  MD-viscosity rise and shows single-particle models under/over-count — methodological note.

### C9. Yu et al. 2024 — LiCl/SiC MD, small transport shifts (counter-example)  [C]
Yu, Y. et al. (2024). "Thermal properties enhancement of recycled lithium chloride molten
salt doped with SiC used for thermal energy storage: A molecular dynamics study."
*Int. Communications in Heat and Mass Transfer* 157:107734.
- **DOI:** 10.1016/j.icheatmasstransfer.2024.107734  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** MD-based nano-in-chloride property prediction (non-oxide particle).
- **Key numbers:** 1.0 wt% SiC → k **+2.43%**, **shear viscosity +5.4%**, c_p +0.8%, melting
  enthalpy −8.85%, self-diffusion −4.57% — deliberately *small* shifts.
- **Use:** counter-example showing enhancement magnitude is particle-dependent; brackets the
  *low* end of MD viscosity change and cautions against assuming large gains universally.

### C10. Tian et al. 2024 — SiO₂/(LiCl-KCl) MD: density+viscosity+k together  [C]
Tian, H. et al. (2024). "Molecular dynamics simulations on the structure and thermal property
of SiO₂/(LiCl-KCl) nanofluids for high temperature thermal energy storage." *Ceramics
International* 50(20-B).
- **DOI:** 10.1016/j.ceramint.2024.11.486  *[DOI verified 2026-08-15]*
- **Category:** MD-based property prediction (density + viscosity + k jointly).
- **Key numbers:** at **6 wt% SiO₂**, average density **+1.22%**, **viscosity +17.21%**,
  k **+6.30%**; NPs strengthen anion–cation association and build a heat-transfer channel while
  weakening diffusion.
- **Use:** third independent nano-in-chloride MD viscosity data point at a stated loading;
  supports the ρ/μ/k co-variation used to close our property module.

---

## D. NANO-cp / MECHANISM & MODELING (why cp/k shift; interfacial layer, aggregation)  [C]
- **D1. Liu & Xiao 2023**, *Energy* 282:128732 — "Molecular dynamics investigation of
  thermo-physical properties of molten salt with nanoparticles for solar energy
  application." General nano-in-salt MD method reference.
  DOI: 10.1016/j.energy.2023.128732  *[DOI verified 2026-08-15 — Crossref]*  [C]
- **D2. Yang et al. 2023**, *J. Energy Storage* 63:107015 — "New insights into the
  heat capacity enhancement of nano-SiO₂ doped alkali metal chloride molten salt for
  thermal energy storage: A molecular dynamics study." SiO₂ in KCl/NaCl/LiCl, Buckingham potential;
  c_p **first rises then falls, peaking at 1 wt%** (KCl +6.2%, NaCl +8.6%, LiCl +19.8%);
  enhancement explained by coordination-number/number-density mismatch of cations & anions.
  Supports loading-optimum + cp-mechanism + method credibility.
  DOI: 10.1016/j.est.2023.107015  *[DOI verified 2026-08-15 — Crossref]*  [C]
- **D3. Mirahmad et al. 2025**, *Nanomaterials* 15(4):302 — "Beyond Thermal Conductivity:
  A Review of Nanofluids for Enhanced Energy Storage and Heat Transfer." NPs raise k but
  can lower c_p; **viscosity rise is the recurring drawback**. Framing citation for the
  pumping-power objective. (Review — use for framing, not primary quantitative data.)
  DOI: 10.3390/nano15040302  *[DOI verified 2026-08-15 — Crossref]*  [C]
- **D4. Shin & Banerjee 2011** — "Enhancement of specific heat capacity of high-temperature
  silica-nanoparticle suspensions." *Int. J. Heat Mass Transfer* 54(4):1064–1070.
  DOI: 10.1016/j.ijheatmasstransfer.2010.11.017. [W]  *[DOI verified 2026-08-15]*
  - **Why pivotal (pre-2020, unavoidable):** the foundational, most-cited discovery that
    nanoparticles can *increase* molten-salt c_p, and the origin of the interfacial-layer /
    compressed-layer explanation that every MD paper above builds on. No post-2020 substitute
    for the canonical mechanism reference; anchors DECISIONS.md rationale for the cp model.
  - **Key finding:** ~**1 wt% SiO₂** in alkali-carbonate eutectic raised c_p by up to ~**26%**;
    attributed to nanoscale compressed/semi-solid interfacial layering.

---

## E. INTEGRATED CSP–TES–POWER-BLOCK SYSTEM MODELING (SAM / PySAM & equivalents)

### E1. Hamilton et al. 2020 — off-design molten-salt cycle + dispatch (SAM basis)  [W]
Hamilton, W., Newman, A., Wagner, M., Braun, R. (2020). "Off-design performance of molten
salt-driven Rankine cycles and its impact on the optimal dispatch of concentrating solar
power systems." *Energy Conversion and Management* 220:113025.
- **DOI:** 10.1016/j.enconman.2020.113025  *[DOI verified 2026-08-15]*
- **Category:** integrated CSP–TES–power-block system modeling (SAM/dispatch layer).
- **Why [W]:** surfaced from NREL's own SAM publication registry rather than the Consensus
  journal index; NREL-authored SAM methodology reference.
- **Use:** justifies our off-design power-block + TES dispatch coupling in PySAM; method
  provenance for the system-level integration in MASTER_PLAN §6.

### E2. Wagner & Gilman 2011 — SAM technical manual (model provenance)  [W]  *(NREL report)*
Wagner, M.J., Gilman, P. (2011). "Technical Manual for the SAM Physical Trough Model."
NREL Report No. TP-5500-51825.
- **DOI:** n/a (NREL technical report; DOI-less).
- **Why pivotal (pre-2020, unavoidable):** the primary documentation of the SAM CSP physical
  models our PySAM run is built on; there is no journal substitute for the tool's own manual.
- **Why [W]:** NREL registry document, not journal-indexed.
- **Use:** cite for SAM/PySAM model assumptions (solar field, receiver, TES two-tank) provenance.
- **Note:** NREL technical report, not peer-reviewed journal — flagged as such.

### E3. Kee et al. 2023 — small-scale CSP + two-tank TES + sCO₂, TE optimization  [C]
Kee, Z. et al. (2023). "Small-scale concentrated solar power system with thermal energy
storage: System-level modelling and techno-economic optimisation." *Energy Conversion and
Management* 294:117551.
- **DOI:** 10.1016/j.enconman.2023.117551  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** integrated CSP–TES–sCO₂ system modeling + techno-economic optimization.
- **Key numbers:** 31.5 kWe dish + two-tank molten salt + sCO₂; multi-objective GA on solar
  multiple & storage hours → **LCOE 122.7–217.8 USD/MWhe**; TES lifts capacity factor from
  **30.4% → 87.2%**; upscale to 400 kWe drops LCOE to **121.9–172.2 USD/MWhe**; CSP beats
  PV-battery only at **high DNI**.
- **Use:** end-to-end template for our SM/TES-hours ↔ LCOE/CF objective coupling; DNI-threshold
  argument for the location-robustness objective.

### E4. Zhang et al. 2025 — solar polygeneration + TES, pinch + NSGA-II, sCO₂ block  [C]
Zhang, S. et al. (2025). "Multi-level study on solar-driven polygeneration system with thermal
energy storage based on pinch method and multi-objective optimization." *Int. J. Hydrogen
Energy* (2025).
- **DOI:** 10.1016/j.ijhydene.2025.01.360  *[DOI verified 2026-08-15]*
- **Category:** integrated CSP–TES–power-block (sCO₂) system modeling + NSGA-II.
- **Key numbers:** molten-salt + S-CO₂ Brayton + SOEC/Cu–Cl; NSGA-II Pareto → exergy
  efficiency **35.30%**, **LCOE 0.0507 $/kWh**; MATLAB + REFPROP properties.
- **Use:** worked example of pinch-based CSP–TES–sCO₂ integration with an NSGA-II objective set
  matching ours (exergy efficiency + unit cost).

---

## F. EXERGY ANALYSIS — sCO₂ / CSP power plants (component-level)  [C]

### F1. Abdelghafar et al. 2024 — energy/exergy/exergoeconomic of sCO₂-CSP configs  [C]
Abdelghafar, M.M. et al. (2024). "Comprehensive analysis of combined power cycles driven by
sCO₂-based concentrated solar power: Energy, exergy, and exergoeconomic perspectives."
*Energy Conversion and Management* 301:118046.
- **DOI:** 10.1016/j.enconman.2023.118046  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** component-level exergy + exergoeconomics of sCO₂-CSP.
- **Key numbers:** recompression Brayton in indirect systems beats direct by **0.9%** thermal;
  RBC exergy efficiency **+1.3%** (indirect vs direct); overall exergy-efficiency ranking
  triple **27%** > dual **25%** > single **20%**; indirect triple-cycle costliest at
  **56,968 USD/yr**.
- **Use:** component-level exergy-destruction ranking + exergoeconomic cost figures to validate
  our exergy layer's config comparison.

### F2. Battisti et al. 2023 — solar sCO₂ RcBC off-design exergy (HTR-dominant ĖD)  [C→W]
Battisti, F.G., Klein, C.F., Escobar, R.A., Cardemil, J.M. (2023). "Exergy Analysis and
Off-Design Modeling of a Solar-Driven Supercritical CO₂ Recompression Brayton Cycle."
*Energies* 16(12):4755.
- **DOI:** 10.3390/en16124755  *[DOI verified 2026-08-15]*
- ⚠ **CITATION CORRECTED 2026-08-13 (Session E).** This entry previously read *Energies*
  **16(13):5073**, DOI **10.3390/en16135073** — wrong issue and article number. The correct
  record (volume 16, **issue 12**, article **4755**, June 2023, four authors as above) was
  web-verified against the DOAJ listing. MDPI's site blocks automated fetch (HTTP 403), so this
  entry carried a "re-confirm the DOI suffix at citation time" caveat.
- ✅ **CAVEAT DISCHARGED 2026-08-15.** The independent hand-verification pass (`SOURCES - Copy.md`)
  returned **10.3390/en16124755** for this entry — the same suffix, arrived at without reference to
  the Session E correction. Two independent routes agreeing is the confirmation the caveat asked
  for, so the DOI is settled. Note the hand-verified copy still carried the *old* `16(13):5073`
  volume/issue text alongside the *new* DOI, which is itself the tell: the DOI was checked, the
  surrounding citation metadata was not.
- **Category:** component-level exergy of sCO₂ RcBC (off-design, yearly).
- **Key numbers:** 25 MW net, design η **48.3%**; **HTR is the top exergy-destruction component**
  at nominal; gas-cooler & turbine ĖD grow at high ambient/off-design; seasonal η **39%** vs
  literature **29%**; capacity factor up to **93.45%** with TES.
- **Use:** primary corroboration that our exergy layer should show **HTR-dominant** ĖD;
  ambient-temperature sensitivity of ĖD. (Also cross-referenced from A4 supporting item.)

### F3. Niu et al. 2022 — CO₂-mixture solar tower Brayton, component exergy loss  [C]
Niu, X. et al. (2022). "Thermodynamic analysis of supercritical Brayton cycles using
CO₂-based binary mixtures for solar power tower system application." *Energy* 254(A):124286.
- **DOI:** 10.1016/j.energy.2022.124286  *[DOI verified 2026-08-15]*
- **Category:** component-level exergy loss under desert/high-ambient operation.
- **Key numbers:** optimal split ratio falls with rising main-compressor inlet T & turbine
  inlet P; CO₂–propane raises thermal/exergy efficiency **+2.34%/+1.51%** vs pure CO₂ (GA-
  optimized); component exergy-loss breakdown under typical desert conditions.
- **Use:** high-ambient exergy-loss context for the location-robustness objective; split-ratio
  sensitivity for the recompression fraction.

---

## G. sCO₂ CYCLE CONFIGURATIONS & WORKING-FLUID THERMODYNAMICS  [C]

### G1. Valencia-Chapi et al. 2022 — complex RCC/RCMCI configs, CO₂ mixtures  [C]
Valencia-Chapi, R.M. et al. (2022). "Supercritical CO₂ mixtures for Brayton power cycles
complex configurations with concentrating solar power." *AIP Conference Proceedings* 2445:090009 (SOLARPACES 2020).
- **DOI:** 10.1063/5.0086032  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** sCO₂ recompression configurations for CSP (RCC-2RH/3RH, RCMCI-2RH/3RH).
- **Key numbers:** vs pure sCO₂, **s-CO₂/Kr (30/70)** raises cycle efficiency **+7–11%**,
  s-CO₂/CH₄ (45/55) **+3–7%**; UA_total swept **5–25 MW/K**; s-CO₂/Kr lowest solar-field cost
  **$29–34M**.
- **Use:** configuration/UA design-space map for our recompression variants; conference paper —
  noted as such.

### G2. Tafur-Escanta et al. 2023 — RCC vs RCMCI vs PCRC, irreversibility trade-off  [C]
Tafur-Escanta, P. et al. (2023). "Thermodynamics analysis of the supercritical CO₂ binary
mixtures for Brayton power cycles." *Energy* 270:126838.
- **DOI:** 10.1016/j.energy.2023.126838  *[DOI verified 2026-08-15]*
- **Category:** sCO₂ cycle-topology thermodynamics (RCC/RCMCI/PCRC).
- **Key numbers:** **RCMCI beats PCRC/RCC by up to ~4%** efficiency depending on fluid/
  conditions; mixtures add up to **~3%** over pure CO₂; higher critical-pressure mixtures
  improve heat absorption/rejection T but raise irreversibility (opposing trends).
- **Use:** topology-selection justification (why RCMCI) + irreversibility framing for exergy.

### G3. Zheng et al. 2023 — floating-critical-point CO₂ mixture, high-ambient robustness  [C]
Zheng, N. et al. (2023). "Supercritical CO₂ mixture Brayton cycle with floating critical points
for concentrating solar power application: Concept and thermodynamic analysis." *Energy
Conversion and Management* 284:116989.
- **DOI:** 10.1016/j.enconman.2023.116989  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** sCO₂ config thermodynamics under variable ambient (robustness).
- **Key numbers:** composition tuning yields larger η gain as ambient rises **20→50 °C**;
  CO₂–H₂S best, **+1.3–7.4%** over pure CO₂; daily average η **+3.5–5.1%** on hot days.
- **Use:** directly supports the location/ambient-robustness objective; quantifies hot-climate
  efficiency penalty a fixed-composition cycle would suffer.

---

## H. MULTI-OBJECTIVE OPTIMIZATION METHODS (NSGA-II / Pareto; screening)

### H1. Deb et al. 2002 — canonical NSGA-II reference  [W]
Deb, K., Pratap, A., Agarwal, S., Meyarivan, T. (2002). "A fast and elitist multiobjective
genetic algorithm: NSGA-II." *IEEE Trans. Evolutionary Computation* 6(2):182–197.
- **DOI:** 10.1109/4235.996017  *[DOI verified 2026-08-15]*
- **Why pivotal (pre-2020, unavoidable):** the algorithm this thesis's optimizer *is*. Fast
  non-dominated sorting O(MN²), elitism, crowding-distance diversity. No substitute — it is the
  method's defining reference.
- **Why [W]:** foundational method paper predating the Consensus 2020+ window; web-verified DOI.
- **Use:** cite wherever NSGA-II, crowding distance, or non-dominated sorting is invoked.

### H2. Le Roux et al. 2024 — NSGA-II on CSP thermocline TES (exergy/enviro/econ)  [C]
Le Roux, D. et al. (2024). "Multi-objective optimisation of a thermocline thermal energy
storage integrated in a concentrated solar power plant." *Energy* 300:131548.
- **DOI:** 10.1016/j.energy.2024.131548  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** NSGA-II + TOPSIS applied to CSP-TES (worked method precedent).
- **Key numbers:** NSGA-II over tank geometry/particle size/filler on **exergy + environmental +
  economic** objectives; TOPSIS + Shannon-entropy weighting; best design **LCOE 10.8 c€/kWhe**,
  **−19%** environmental impact, exergy efficiency **>99.8%**.
- **Use:** direct precedent for our NSGA-II + TOPSIS three-objective (exergy/enviro/cost) setup
  on a CSP-TES system; decision-making-method template.

### H3. Ji et al. 2025 — NSGA-II on CSP-TES hybrid, DPSP vs LCOE + CRITIC/TOPSIS  [C]
Ji, C. et al. (2025). "Optimization of a Nuclear–CSP Hybrid Energy System Through
Multi-Objective Evolutionary Algorithms." *Energies* 18(x).
- **DOI:** 10.3390/en18092189  *[DOI verified 2026-08-15]*
- **Category:** NSGA-II two-objective (reliability vs cost) with CRITIC + TOPSIS decision layer.
- **Key numbers:** NSGA-II minimizes **DPSP and LCOE** over solar multiple (SM) and storage
  duration (TSD); CRITIC + TOPSIS selects compromise; 100:100 nuclear:CSP gives lowest LCOE/ECP.
- **Use:** precedent for SM & storage-hours as decision variables and a reliability-vs-cost
  Pareto — mirrors our objective/variable choice; CRITIC/TOPSIS alternative to plain TOPSIS.

### H4. Hu et al. 2024 — bi-level NSGA-II + LP for WP/PV/CSP-sCO₂ capacity-operation  [C]
Hu, Y. et al. (2024). "Capacity-operation collaborative optimization of the system integrated
with wind power/photovoltaic/concentrating solar power with S-CO₂ Brayton cycle." *Frontiers
in Energy* 18.
- **DOI:** 10.1007/s11708-024-0922-z  *[DOI verified 2026-08-15]*
- **Category:** NSGA-II nested with linear programming (bi-level) for CSP-sCO₂ systems.
- **Key numbers:** NSGA-II-nested-LP balances carbon/economics/scheduling; after optimization
  **LCOE −3.43%**, carbon **−92.13%** vs unoptimized reference (Zhangbei case).
- **Use:** precedent for coupling a capacity-level Pareto search with an operational sub-problem;
  method reference if we add a dispatch inner loop.

### H5. Magno et al. 2024 — NSGA-II: CSP-TES vs PV-BESS, LCOE/performance trade-off  [C]
Magno, C.M.A. et al. (2024). "Comparison of Parabolic Trough Concentrated Solar Power and
Photovoltaic Plants with and without Energy Storage using NSGA-II." *2024 6th Global Power,
Energy and Communication Conference (GPECOM)*.
- **DOI:** 10.1109/GPECOM61896.2024.10582632  *[DOI verified 2026-08-15]*
- **Category:** NSGA-II applied to CSP-TES vs PV-BESS (multi-objective; LCOE vs AEP).
- **Key numbers:** elitist NSGA-II varies key decision parameters to trade **annual energy
  production vs LCOE**; storage-less PV cheaper, storage-less PT-CSP better technically; PT-CSP
  + TES becomes performance/NPV-competitive with PV-BESS though PV-BESS keeps lower LCOE.
- **Use:** precedent for the CSP-vs-alternative Pareto framing and AEP↔LCOE objective pair;
  conference paper — noted as such.
- **Note:** IEEE conference proceedings (peer-reviewed venue), not a journal.

---

## I. SOLAR RESOURCE & CSP PERFORMANCE — MENA & Southern Africa (location robustness)

### I1. Hajou et al. 2025 — MENA/Mediterranean DNI zoning for CSP  [C]
Hajou, A. et al. (2025). "Solar energy potential assessment in the MENA and Mediterranean
Regions." *J. King Saud Univ. – Eng. Sciences* (2025).
- **DOI:** 10.1007/s44444-025-00052-4  *[DOI verified 2026-08-15]*
- **Category:** solar-resource mapping (DNI) across MENA — location-robustness inputs.
- **Key numbers:** clustering of NASA POWER data → **9 DNI zones**; highest DNI zones exceed
  **6.3 kWh/m²/day**, giving up to **31% higher** per-area generation than low-DNI regions;
  parallel GHI zoning (4.57–6.46 kWh/m²/day).
- **Use:** defines the DNI spread our location-robustness objective must span across MENA;
  site-selection basis.

### I2. Azouzoute et al. 2020 — 62-site MENA CSP LCOE map (SAM)  [C]
Azouzoute, A. et al. (2020). "Overview of the integration of CSP as an alternative energy
source in the MENA region." *Energy Strategy Reviews* 29:100493.
- **DOI:** 10.1016/j.esr.2020.100493  *[DOI verified 2026-08-15]*
- **Category:** CSP performance/LCOE across MENA (SAM, 62 sites) — location robustness.
- **Key numbers:** 50 MWe parabolic-trough + 2-tank across **62 MENA sites**; competitive
  **LCOE 11.58 c€/kWh**; GIS LCOE/production maps benchmarked vs Andasol (Spain).
- **Use:** multi-site MENA LCOE spread + methodology for site-to-site robustness comparison.

### I3. Hirbodi et al. 2020 — Iran CSP techno-economic (SAM, SM/TES sweep)  [C]
Hirbodi, K. et al. (2020). "Techno-economic assessment and environmental impact of
concentrating solar power plants in Iran." *Renewable and Sustainable Energy Reviews* 120:109642.
- **DOI:** 10.1016/j.rser.2019.109642  *[DOI verified 2026-08-15]*
- **Category:** CSP techno-economic + SM/TES optimization (SAM) in a high-DNI MENA setting.
- **Key numbers:** DNI ~**6 kWh/m²/day**; best = dry-cooled 100 MWe tower, **14 h TES, SM 3.0**;
  **LCOE 11.3 ¢/kWhe**, solar-to-electric **14.7%**, payback ~15 months, **399 kt/yr** CO₂ cut.
- **Use:** SM/TES-hours sweep template + LCOE/efficiency reference point for a MENA site.

### I4. Larbi et al. 2025 — Algeria molten-salt tower TE optimization (SAM), 3 sites  [C]
Larbi, M. et al. (2025). "Comprehensive techno-economic optimization and performance analysis
of molten salt concentrated solar power tower plants in Algeria." *Scientific Reports*
15:97236.
- **DOI:** 10.1038/s41598-025-97236-4  *[DOI verified 2026-08-15]*
- **Category:** CSP tower TE optimization across Southern-Mediterranean/Saharan sites (SAM).
- **Key numbers:** Mechria optimum **SM 1.8, 10 h TES → CF 51.49%, LCOE 0.097 $/kWh**; Adrar
  LCOE 0.18 $/kWh (CF 24.03%); Tindouf LCOE 0.17 $/kWh (CF 18.95%) — strong site sensitivity.
- **Use:** demonstrates site-to-site CF/LCOE variation our robustness objective must capture;
  molten-salt-tower + SAM provenance.

### I5. Agyekum & Velkin 2020 — Ghana (Southern/West Africa) CSP TE (SAM), ST vs PT  [C]
Agyekum, E.B., Velkin, V.I. (2020). "Optimization and techno-economic assessment of
concentrated solar power (CSP) in South-Western Africa: A case study on Ghana." *Sustainable
Energy Technologies and Assessments* 40:100763.
- **DOI:** 10.1016/j.seta.2020.100763  *[DOI verified 2026-08-15]*
- **Category:** CSP performance/TE in Sub-Saharan/Southern-African context (SAM).
- **Key numbers:** solar tower **LCOE 13.67 ¢/kWh (Navrongo) / 14.73 ¢/kWh (Tamale)**; parabolic
  trough far higher (**25.83–28.83 ¢/kWh**); optimum ST **SM 1.4–1.9**; ST preferred for the
  climate.
- **Use:** Southern/West-Africa data point for the location-robustness objective; ST-vs-PT and
  SM guidance in a lower-DNI African setting.

### I6. Aljudaya et al. 2024 — Saudi LFR molten-salt + large TES, SM/TES sweep (SAM)  [C]
Aljudaya, A. et al. (2024). "Techno-Economic Assessment of Molten Salt-Based Concentrated
Solar Power: Case Study of Linear Fresnel Reflector with a Fossil Fuel Backup under Saudi
Arabia's Climate Conditions." *Energies* 17(x).
- **DOI:** 10.3390/en17112719  *[DOI verified 2026-08-15]*
- **Category:** CSP TE + SM/TES optimization (SAM), high-DNI MENA site.
- **Key numbers:** DNI **>2500 kWh/m²/yr**; ~**600 SM–TES configs**; optimum **SM 3.5, 15 h TES**
  → AEG 337 GWh, **LCOE 9.24 ¢/kWh, CF 86%** (vs solar-only 11.92 ¢/kWh, CF 36%).
- **Use:** large SM/TES design-space example + storage-driven CF/LCOE improvement magnitude for
  a MENA site (complements tower cases with an LFR data point).

### I7. Ahmad et al. 2022 — DNI reanalysis validation + geospatial CSP potential (SAM)  [C]
Ahmad, M. et al. (2022). "Validation of weather reanalysis datasets and geospatial and
techno-economic viability and potential assessment of concentrated solar power plants."
*Energy Conversion and Management* 256:115366.
- **DOI:** 10.1016/j.enconman.2022.115366  *[DOI verified 2026-08-15 — Crossref]*
- **Category:** solar-resource (DNI) dataset validation + CSP potential — robustness inputs.
- **Key numbers:** SARAH-East DNI best-correlated (**R > 0.9**) vs ground data after
  preprocessing; SAM Physical-Trough technical potential mapping; national CSP capacity
  potential **~10,035 GW**; net cost **< 0.096 USD/kWh**; 9 sites >1200 TWh/yr.
- **Use:** justifies DNI-dataset choice (reanalysis vs ground) for our multi-site robustness
  runs; guards against DNI-input bias in the location objective.

### I8. Imam et al. 2024 — Saudi GIS land-suitability + CSP TE (SAM), ST vs PT  [C]
Imam, A.A. et al. (2024). "Potential of Concentrated Solar Power in the Western Region of
Saudi Arabia: A GIS-Based Land Suitability Analysis and Techno-Economic Feasibility
Assessment." *IEEE Access* 12.
- **DOI:** 10.1109/ACCESS.2023.3344752  *[DOI verified 2026-08-15]*
- **Category:** CSP siting + techno-economics (SAM) at high-DNI MENA sites.
- **Key numbers:** Fuzzy-Boolean + AHP GIS → **70% of province land suitable**; lowest LCOE in
  Makkah: **9.58 ¢/kWh (parabolic trough) / 9.17 ¢/kWh (solar power tower)**; optimal **8 h TES**
  for lowest LCOE + highest CF.
- **Use:** siting-methodology + ST-vs-PT LCOE benchmark for a high-DNI MENA location; TES-hours
  optimum cross-check.

### I9. Abdelhady 2025 — PV/HCPV DNI-sensitivity across sites (SAM), sensitivity method  [C]
Abdelhady, S. (2025). "Techno Economic Assessment and Comparative Study of Photovoltaic (PV)
and High Concentration PV (HCPV) Large Scale Power Systems Under Different Scenarios:
Sensitivity Analysis." *Results in Engineering* 25.
- **DOI:** 10.1016/j.rineng.2025.105653  *[DOI verified 2026-08-15]*
- **Category:** DNI-driven sensitivity analysis across geographies (screening precedent).
- **Key numbers:** SAM, two 100 MW_DC systems across Egyptian + international sites; HCPV cell
  efficiency **37%**, LCOE **8.44 ¢/kWh** (DNI-reliant) vs dual-axis PV **3.64 ¢/kWh**;
  sensitivity confirms **capital cost + irradiance variability** dominate feasibility.
- **Use:** method precedent for capital-cost/DNI sensitivity screening (Morris/Sobol analog)
  and the DNI-dependence argument underpinning location robustness. HCPV/PV, not CSP — cite for
  the sensitivity methodology and DNI-sensitivity magnitude, not as a CSP performance point.

---

## J. QUALITY / EXCLUSION NOTES (transparency)

- **Predatory / low-credibility flags:** the regenerative-sCO₂ solar-tower paper in
  *Int. Research J. of Modernization in Eng. Tech. & Science* (IRJMETS) reporting Brayton
  exergy efficiency **78.99%** and cycle energy efficiency **58.92%** was **excluded** —
  IRJMETS is a low-credibility/borderline-predatory outlet and the quoted efficiencies are
  thermodynamically implausible for the stated configuration. Not logged.
- **Reviews-of-reviews:** kept to a minimum. Only D3 (Mirahmad 2025) and I-series regional
  overviews serve a framing role; all other entries carry directly usable quantitative data.
- **Category coverage status:** all eight target categories filled with recent (2020–2026)
  peer-reviewed work except where a canonical pre-2020 method reference was unavoidable
  (A1, A3, D4, E2, H1 — each justified inline). No category required weak/padding sources.
- **DOIs marked "(verify/fetch at cite)"** were surfaced via Consensus/web snippets without a
  fully confirmed article number. **All of them are now settled** — none remains in the file — and
  each carries an inline `*[DOI verified <date>]*` marker, with the hedge text removed. **A DOI line
  with no marker has not been checked**; that is the whole point of the marker, and it is what makes
  this file reconcilable after the next rewrite instead of only inside the session that did the
  checking. The only unmarked DOIs left are §A8's three deferred acquisitions (§J3).

  ⚠ **The marker records that the identifier was checked, not that the paper was read.** Every DOI
  here was confirmed against the Crossref record for that title; the reported key numbers still come
  from Consensus/web snippets for most entries and have **not** been re-read from the article.

### J1. ✅ RESOLVED 2026-08-15 — 14 DOI conflicts adjudicated against Crossref

The hand-verification pass returned a **different** DOI from the one drafted for 14 entries. Both
were real, resolvable DOIs, so inspection could not settle it. All 14 were adjudicated by querying
Crossref for each paper's authoritative record **by title** — not by testing which candidate
resolves, since a DOI that resolves only proves it points at *some* paper, not at *this* one.
Applied by `scripts/apply_doi_conflict_resolutions.py`; ledger in
`results/sources_doi_resolutions_*.csv`.

| | count |
|---|---|
| hand-verified DOI correct | **13 / 14** |
| **neither candidate correct** | **1 / 14** (C7) |
| as-drafted DOI correct | **0 / 14** |

**The "matches the printed article number" signal was backwards.** §J1 originally flagged these
because the as-drafted DOI satisfied the Elsevier/MDPI identity (`Energy 300:131594` ↔
`10.1016/j.energy.2024.131594`) while the hand-verified one did not. That identity turned out to be
evidence of *fabrication*, not correctness: the DOI and the printed volume:article were invented
together, so they agree with each other and with nothing else. **The printed volume was also wrong
in 12 of the 14**, so each entry needed both fields corrected — done in the same pass.

⚠ **C7 Xian 2022 is the cautionary row: BOTH candidates were wrong.** The true record is
*Applied Energy* **323**:119555 (`10.1016/j.apenergy.2022.119555`). The drafted DOI gave
325:119921; the hand-verified copy gave `10.1016/j.applthermaleng.2025.126209`, an *Applied Thermal
Engineering* 2025 paper — a different work entirely. One miss in fourteen is why
`reconcile_sources_dois.py` quarantines every conflict rather than trusting the hand-verified
column wholesale. **`SOURCES - Copy.md` is therefore known-wrong at C7** and must not be treated as
authoritative anywhere.

Corrected entries: A6, A7, B1, B4, B5, C1, C7, C9, E3, F1, G1, G3, H2, I7. D2's volume and title
were completed from the same lookups (its DOI was already right).

### J2. ✅ RESOLVED 2026-08-15 — the 3 entries with no DOI in either revision

Neither the drafted file nor the hand-verified copy carried a DOI for A4, D1 or D3. There was
nothing to adjudicate here, only to find; all three were located via the same Crossref title query.

| entry | DOI found | record |
|---|---|---|
| A4 Mammadov & Kalbaliyev 2026 | `10.47390/ts-v4i5y2026n19` | *Topical Issues of Technical Sciences* 4(5), art. n19 |
| D1 Liu & Xiao 2023 | `10.1016/j.energy.2023.128732` | *Energy* 282:128732 |
| D3 Mirahmad et al. 2025 | `10.3390/nano15040302` | *Nanomaterials* 15(4):302 |

Two of the three also had their citation text corrected, because the lookups showed the recorded
titles were paraphrases rather than quotations: D1's "MD investigation of thermophysical..." is
actually "Molecular dynamics investigation of thermo-physical...", and D3 had no title recorded at
all (it is "Beyond Thermal Conductivity: A Review of Nanofluids for Enhanced Energy Storage and
Heat Transfer" — which confirms the review status the entry already claimed).

⚠ **A4 carries a venue caution.** *Topical Issues of Technical Sciences* (Techscience.uz) is a
low-profile regional outlet, not indexed in the major abstracting databases. Its DOI is registered
and resolves, so it is **not** in the same category as the IRJMETS paper excluded above — its
reported η = 50.7 % is thermodynamically plausible and consistent with A0/A5/A6. It is therefore
kept, but explicitly discounted: **soft corroboration only, never an anchor.** See the ⚠ in §A4.

**Nothing in SOURCES.md now lacks a DOI except the two entries that are DOI-less by nature** —
A0 (MIT report / dissertation, which carries a DSpace handle and a peer-reviewed 2006 companion)
and E2 (NREL technical report).

### J3. ⚠ OPEN — §A8's recommended acquisitions are unverified by design

§A8 lists three papers to acquire in order to close the "one author's tables" objection: Padilla
et al. 2015, Moisseytsev & Sienicki 2009, Sarkar 2009. **These are deferred acquisitions, not
logged sources** — none has been opened, and their DOIs were surfaced from snippets. They carry no
`*[DOI verified]*` marker for that reason. Verify at acquisition time, not before.

Note the reconcile script models **one DOI per entry**, so of A8's three it tracks only the first
(Padilla). Two DOIs in that section are therefore invisible to `results/sources_doi_reconcile_*.csv`
and must be checked by reading §A8 directly.

---|---|---|
| A4 | Mammadov et al. 2026, *Topical Issues of Tech. Sci.* | DOI, and the volume/pages; low-profile venue, may genuinely lack one |
| D1 | Liu & Xiao 2023, *Energy* 282 | DOI + article number |
| D3 | Mirahmad et al. 2025, *Nanomaterials* | DOI + volume/article number |