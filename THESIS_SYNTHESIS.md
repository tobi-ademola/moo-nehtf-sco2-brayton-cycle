# THESIS SYNTHESIS — Nano-Enhanced HTF + sCO₂ Brayton CSP

> **What this file is.** A single, self-contained synthesis of everything built, run, verified and
> found in this project to date, written to feed the drafting of **Chapter 3 (Methodology)**,
> **Chapter 4 (Results & Discussion)** and **Chapter 5 (Conclusions & Future Work)**.
>
> Every number in this document is traceable to a committed script and a timestamped artifact in
> `results/`. Nothing here is recalled from memory or from a chat transcript; where a claim rests
> on inference rather than execution, it is labelled as such.
>
> **Compiled:** 2026-08-13 · **Revised:** 2026-08-14 (§1, §9, §12, §13, §17 — the UDPC
> non-convergence finding is **withdrawn**; see §9.3) · **Repo HEAD at compilation:** `fb9fd48` ·
> **Environment:** Python 3.13.15, NREL-PySAM 7.1.1.post1 (bundled ssc 306), numpy 2.5.2,
> CoolProp 8.0.0, Windows 11.

---

## TABLE OF CONTENTS

| § | Section | Feeds |
|---|---|---|
| 1 | Executive summary — what is done, partial, and not started | Ch 4 opener, Ch 5 |
| 2 | The research problem and how the work was decomposed | Ch 3.1 |
| 3 | Computational environment, tooling and reproducibility | Ch 3.2 |
| 4 | **Module A — Nano-HTF thermophysical property model** (Objective 1) | Ch 3.3, Ch 4.1 |
| 5 | **Module B — sCO₂ power block and its literature validation** (Objective 2) | Ch 3.4, Ch 4.2 |
| 6 | **Module C — Component-level exergy layer** (Objective 2/3) | Ch 3.5, Ch 4.3 |
| 7 | **Module D — Nano-HTF ⇄ SAM plant coupling** (Objective 2) | Ch 3.6, Ch 4.4 |
| 8 | **Module E — Solar field / TES baseline** (Objective 2) | Ch 3.7, Ch 4.5 |
| 9 | **Module F — UDPC bridge: the integrated model** (Objective 2) — *partial* | Ch 3.8, Ch 4.6 |
| 10 | Cross-cutting methodological contribution: the PySAM/ssc defect catalogue | Ch 3.9, Ch 4.7 |
| 11 | The decision vector: status of all ten variables | Ch 3.10, Ch 5 |
| 12 | Objective-by-objective attainment and gap analysis | Ch 5.1 |
| 13 | Limitations and threats to validity (stated honestly) | Ch 5.2 |
| 14 | Anticipated defence questions with grounded answers | viva prep |
| 15 | Artifact index — every script and result file | Appendix |
| 16 | Suggested figures and tables | Ch 4 |
| 17 | Future work and the exact restart path | Ch 5.3 |

---

## 1. EXECUTIVE SUMMARY

### 1.1 The one-paragraph version

This project set out to build an integrated CSP → nano-enhanced-HTF → TES → sCO₂ Brayton model and
to optimise it multi-objectively over ten decision variables. Five of the six required modules were
built and verified: a temperature- and loading-dependent nano-chloride property model anchored to
measured data; an sCO₂ recompression power block that reproduces a published state-point table to
**within 0.070 % in enthalpy at every node** and its thermal efficiency to **+0.019 percentage
points**; a component-level exergy layer whose cycle-wide balance closes to **1.5 × 10⁻⁴ relative**;
a verified coupling that injects the nano-chloride into SAM's plant model with **zero round-trip
deviation**; and a pinned solar-field/TES annual baseline. The sixth module — the user-defined
power-cycle (UDPC) performance map that welds the validated sCO₂ block onto the annual plant model —
**generates at the validated design point**, at 3 points per axis and ~38 minutes per build. That
last statement is a correction: this document previously reported the map as non-convergent and
attributed it to an over-constrained design, a conclusion assembled from twelve experiments none of
which had ever been allowed to run to completion. **The retraction is reported as a result in its
own right** (§9.3), because the failure was one of measurement discipline rather than of modelling,
and it is the kind that survives internal review. What the work delivers is: a validated power
block, a validated property model, a verified exergy method, a quantified and previously unreported
physical constraint (the melting-point → loop-ΔT → pumping-power coupling), a literature-consistency
finding about the validation source itself, and a working sCO₂ ⇄ annual-plant bridge that now
returns an integrated annual result — **440.21 GWh at a 62.6 MW net nameplate**, beating an
identically-configured steam block by **+13.05 %**, and exposing a new system-level tension in
which the recompression cycle's own recuperation returns the HTF at 533 °C and so spends ≈43 % of
gross on receiver pumping. That last number reproduces the independently-derived ΔT–pumping law of
§7.4 to **0.3 %**. The Morris screening and NSGA-II optimisation were still not run, and that gap
is now one of computational budget rather than of a blocked model layer.

### 1.2 Status board

| # | Module | Objective served | Status | Evidence |
|---|---|---|---|---|
| A | Nano-HTF property model (ρ, cp, k, μ vs T and φ, with uncertainty bands) | Obj 1 | ✅ **Complete & self-validating** | `scripts/nanofluid_properties.py`, `results/sam_htf_table_0p7wt.csv` |
| B | sCO₂ recompression power block + node-by-node literature validation | Obj 2 | ✅ **Complete — validation gate PASSED** | `scripts/validate_dostal.py` + 4 checker scripts, 6 result sets |
| C | Component-level exergy layer (per-node *e*, per-component Ė_D) | Obj 2, Obj 3 (min Ė_D) | ✅ **Method verified end-to-end** | `scripts/exergy_layer_check.py`, `results/exergy_layer_check_*` |
| D | Nano-HTF ⇄ SAM coupling (custom fluid inside the plant model) | Obj 2 | ✅ **Complete — question answered** | `scripts/htf_sam_bridge.py`, `results/htf_sam_bridge_*` |
| E | Solar field / TES annual baseline | Obj 2 | ✅ **Baseline pinned** (GUI cross-check blocked, not required) | `VALIDATION.md` §1.3 |
| F | UDPC bridge → integrated sCO₂ plant model | Obj 2 | ✅ **Map generates at the validated case F design** (~38 min/build; coarse at 3 pts/axis) | `scripts/build_udpc_map.py`, `scripts/udpc_convergence_bisect.py`, `results/udpc_bisect_20260814T194825Z.*` |
| G | Morris elementary-effects screening | Obj 3 | ❌ **Not started** — **no longer blocked by F**; gated by map build cost | method fixed in `DECISIONS.md` D3 |
| H | NSGA-II multi-objective optimisation | Obj 3/4 | ❌ **Not started** (was always stretch scope) | — |
| I | Climate-robustness study (MENA + Southern Africa) | Obj 5 | ❌ **Post-defence scope**; Morocco TMY in hand, SA file missing | `data/tmy/` |

### 1.3 The five defensible findings

These are results, not activity — each is a claim that can survive cross-examination:

1. **The sCO₂ power block is validated at state-point resolution, not merely at efficiency.**
   All eight tabulated nodes of Dostal (2004) Table 10.4 reproduce to ≤ 0.070 % in *h*, ≤ 0.045 % in
   *s*, 0.000 % in *P*; the two untabulated junction nodes are closed by conservation. η matches to
   +0.019 pp. (§5)

2. **A literature-consistency finding in the validation source itself.** Dostal's Table 10.1 states
   a recompressed fraction of 0.39 for the High-Performance design; his own Table 10.4 state points
   close the mixing junction only at **f = 0.4097**. A control run on his Advanced 650 °C design
   reproduces its stated 0.41 to within 0.005, which calibrates the method's resolution and makes
   the High-Performance discrepancy four times the noise floor. No plausible recompressor
   efficiency rescues 0.39. (§5.6)

3. **The nano-chloride's melting point is a hard system constraint that propagates into the
   optimisation, and it was quantified.** Because the eutectic freezes at 401.4 °C, the cold tank
   cannot sit at nitrate's 290 °C. The resulting narrow loop ΔT drives receiver pumping power
   steeply: 124 K → 162.30 MW (**negative nameplate, infeasible**), 250 K → 27.04 MW, and the
   observed scaling on the chloride is **W_pump ∝ ΔT^−2.56**. This binds decision variables #5 and
   #6 and must be given to the optimiser as a constraint, not discovered by it. (§7.4)

4. **Nano-enhancement produces an interior optimum in loading at plant level, not just at property
   level.** At 0.7 wt% CuO the plant beats the bare eutectic on annual energy (479.2 vs 466.3 GWh,
   +2.8 %) *and* on pumping power (27.04 vs 35.31 MW, −23.4 %); at 2.0 wt% it is worse than bare on
   both. This tracks the measured cp enhancement turning from +10.5 % to −3.5 %, and it is
   precisely what makes φ worth optimising rather than maximising. (§7.5)

5. ~~**A fully-determined, validated recompression design is over-constrained for UDPC generation
   in ssc 306.**~~ **WITHDRAWN 2026-08-14 — this finding was an artifact of measurement, and its
   retraction is itself the more useful result.** The UDPC sweep converges at the full case F
   design (`recomp_frac 0.40970`, η 0.50547) in **38 minutes**. All twelve experiments that
   reported "hangs" were capped at 5–16 minutes; not one had ever run to completion, so none of
   them had licence to call anything non-convergent. The replacement finding is methodological and
   belongs in the write-up in its place: **a run that has not finished carries no information until
   the timeout is justified against a measured completion time** — and a plausible mechanism
   ("the design is over-constrained") assembled from a dozen such non-observations survived review,
   reached this synthesis, and set the project's critical path for a full session. (§9)

---

## 2. THE RESEARCH PROBLEM AND HOW THE WORK WAS DECOMPOSED

*(Chapter 3.1)*

### 2.1 Objectives as set

1. Temperature- and concentration-dependent thermophysical models of the nano-enhanced molten-salt
   HTF.
2. Integrated CSP–nano-HTF–TES–sCO₂ Brayton model with energy, exergy, hydraulic and economic
   assessment.
3. Multi-objective optimisation of nanoparticle concentration, particle size and cycle operating
   parameters for: max energy efficiency, min cost, min pumping power, max TES energy density, min
   exergy destruction.
4. *(Post-defence)* Pareto-optimal envelope and net benefit of nano-enhancement vs conventional salt.
5. *(Post-defence)* Robustness of the Pareto-optimal configuration across MENA and Southern Africa.

### 2.2 The decision vector

**X = [SM, t_TES, φ, d_p, T_HTF, ṁ_HTF, T_t,in, P_H, PR, f_RC]**

| # | Category | Variable | Symbol |
|---|---|---|---|
| 1 | Solar / TES | Solar multiple | SM |
| 2 | Solar / TES | TES duration (h) | t_TES |
| 3 | Nano-HTF | Nanoparticle mass loading | φ |
| 4 | Nano-HTF | Nanoparticle diameter | d_p |
| 5 | Nano-HTF | HTF operating temperature | T_HTF |
| 6 | Nano-HTF | HTF mass flow rate | ṁ_HTF |
| 7 | sCO₂ | Turbine inlet temperature | T_t,in |
| 8 | sCO₂ | High-side pressure | P_H |
| 9 | sCO₂ | Pressure ratio | PR |
| 10 | sCO₂ | Recompression fraction | f_RC |

**Objectives:** max η_ex, max ρ_TES; min LCOE, min W_pump, min Ė_D.
**Constraints / reported indicators:** ΔP_HTF ≤ max; T_HTF ≤ material limit; W_net ≥ min;
Q_loss,TES, E_annual, Q̇_HTF–sCO₂.

### 2.3 The decomposition, and why it is the defensible one

The single most important methodological decision in the project is **validation decoupling**, and
it was forced by the tool rather than chosen for convenience: **there is no sCO₂-tower configuration
in SAM.** This was confirmed by inspecting the shipped defaults directory — only `MSPT_*`,
`MSPT IPH_*` and `MSPTV2_None` exist, all steam-Rankine. The sCO₂ block is reachable **only**
through PySAM's standalone modules.

Consequently no single reference case can validate the integrated plant, and the project validates
each subsystem against the best available reference **for that subsystem**:

```
        ┌──────────────────────────────┐        ┌───────────────────────────────┐
        │  SOLAR FIELD + RECEIVER +    │        │   sCO₂ RECOMPRESSION BLOCK    │
        │  TES + ANNUAL DISPATCH       │        │                               │
        │                              │        │                               │
        │  anchor: NREL MSPTSingleOwner│        │  anchor: Dostal (2004)        │
        │          (ssc 306)           │        │          Table 10.4, node-wise│
        │  → E_annual 593.05 GWh       │        │  → ≤0.070 % in h at 8 nodes   │
        └──────────────┬───────────────┘        └───────────────┬───────────────┘
                       │                                        │
                       │        ┌───────────────────────┐       │
                       └────────┤  UDPC BRIDGE (§9)     ├───────┘
                                │  ⚠ does not converge  │
                                └───────────────────────┘
```

**Frame this in the thesis as a methodological strength, not a workaround.** Validating the power
block node-by-node against published *h* and *s* is a materially stronger claim than the
efficiency-match that most comparable studies report, and it is only possible because PySAM exposes
per-state entropy.

### 2.4 The four modelling decisions that were debated and resolved

Recorded in full in `DECISIONS.md`; summarised here because Chapter 3 must justify each.

| # | Decision | Resolution | Basis |
|---|---|---|---|
| D1 | Include component-level exergy? | **IN** — build exergy-ready (carry *h* and *s* everywhere), switch the reporting layer on last | ssc exposes *s* natively → the +1 day CoolProp-reconstruction risk never materialised; `min Ė_D` is a named objective |
| D2 | Nano-chloride inside SAM or coupled externally? | Originally "native nitrate in SAM, chloride in the coupling layer" — **subsequently superseded by execution**: `rec_htf = 50` accepts the chloride *inside* SAM (§7) | Mechanism confirmed by test, not assumed |
| D3 | Screening method | **Morris elementary effects**, Sobol on survivors only | OAT misses interactions and is indefensible for 10 coupled variables; Sobol needs ~10³ evaluations at 20–40 s each |
| D4 | Validation strategy | **Decoupled**, node-by-node on the power block | Forced — no sCO₂-tower case exists in SAM |

> **Note for Chapter 3.** D2's *conclusion* changed when it was tested. The thesis should present
> this as evidence of a working method (a decision made under uncertainty, then falsified by
> experiment and updated) rather than quietly presenting only the final answer.

---

## 3. COMPUTATIONAL ENVIRONMENT, TOOLING AND REPRODUCIBILITY

*(Chapter 3.2)*

### 3.1 Exact software stack — all verified by execution

| Component | Version | How verified |
|---|---|---|
| Python | 3.13.15 | `.venv\Scripts\python.exe --version` |
| NREL-PySAM | 7.1.1.post1 | `pip list` |
| Bundled ssc | **306**, build `Windows 64 bit Visual C++ Apr 24 2026 01:21:21` | `ctypes` interrogation of `PySAM/ssc.dll` |
| numpy | 2.5.2 | not a PySAM dependency — installed explicitly |
| CoolProp | 8.0.0 | independent CO₂ property lane for validation |
| SAM GUI | **absent on this machine** | `Test-Path C:\SAM` → false |

Two environment facts are worth a sentence in the methodology because they affect what can be
claimed:

- **PySAM does not use any installed SAM GUI's `ssc.dll`** — it ships and loads its own. The
  correct pairing is PySAM 7.1.1 ≡ ssc 306 ≡ SAM 2025.4.16. Comparing against SAM 2026.7.3
  (ssc 308) would produce version-artifact deltas that are not modelling errors.
- **Python 3.14 cannot run this project at all.** NREL-PySAM publishes no 3.14 wheels; pip reports
  `(from versions: none)`, which reads like a network failure and is not. 3.13 was installed
  alongside.

### 3.2 Reproducibility — an established property, not an assumption

This is a claim the thesis can make that most cannot. The complete validation suite was re-run on a
**virtual environment rebuilt from scratch, on a different machine, under a different Python patch
release (3.13.15 vs 3.13.14)**, and returned numbers **identical to every printed digit** — the
adopted case F baseline, the legacy anchor case, and the whole recuperator effectiveness sweep.

Given ssc 306, the pinned baselines are therefore **environment-independent**, which means any
future deviation is a real modelling change and never drift. A deliberately-retained legacy
configuration (case A, §5.7) serves purely as this drift detector.

### 3.3 Research-artifact discipline (worth one paragraph in Chapter 3)

The project operated under four standing rules that are themselves part of the method:

1. Every script is a durable, committed artifact with a header stating purpose, inputs and how to
   run it — no throwaway one-liners.
2. Every result is written to `results/` as CSV/MD, stamped with UTC timestamp, script name and
   **the git commit that produced it**. Twenty-six such artifacts exist.
3. Every session is logged in an append-only `PROGRESS_LOG.md` (~40 kB) with what ran, what came
   out and what is next.
4. Seven knowledge files (`MASTER_PLAN`, `CLAUDE`, `PROGRESS_LOG`, `SOURCES`, `VALIDATION`,
   `PROPERTIES`, `DECISIONS`) are updated in place at the end of every session.

The practical consequence is that this synthesis document could be assembled entirely from disk,
with no reliance on anyone's memory of what happened. That is the standard the thesis should
describe.

### 3.4 Literature base

`SOURCES.md` logs **50 sources** in ten categories (power-block validation targets; nano-HTF
properties; viscosity/MD; nano-cp mechanism; integrated system modelling; exergy analysis; sCO₂
configurations; MOO methods; MENA/Southern-Africa solar resource; quality-exclusion notes). Each
entry carries citation, DOI, the tool that found it ([C] = Consensus, [C→W] = Consensus-found and
web-verified, [W] = web fallback), and the **specific numbers extracted** for use. One citation
error found and corrected in-project: Battisti et al. 2023 was logged with the wrong issue and
article number, corrected to *Energies* 16(12):4755 against the DOAJ record.

---

## 4. MODULE A — NANO-HTF THERMOPHYSICAL PROPERTY MODEL

*(Chapter 3.3 methodology; Chapter 4.1 results)*
**Script:** `scripts/nanofluid_properties.py` (673 lines, pure Python, no external dependencies)
**Status:** complete, self-validating, in active use by two downstream modules.

### 4.1 What the module does

It maps **(nanoparticle mass fraction φ, temperature T)** → **{ρ, cp, k, μ}**, each returned as a
`Prop(nominal, lo, hi)` triple carrying an uncertainty band. Every downstream consumer — the SAM
plant coupling and the sCO₂ PHX — calls this one module, so there is exactly one property truth in
the project.

Each property maps to a specific objective:

| Property | Feeds | Objective |
|---|---|---|
| ρ(T, φ) | mass flow, inventory volume, ΔP | O3 (pumping), O4 (TES density) |
| cp(T, φ) | storage inventory, loop ΔT | **O4 (max ρ_TES)** |
| k(T, φ) | HTF-side heat transfer | O1 (efficiency) |
| μ(T, φ) | pumping power | **O3 (min W_pump)** |

### 4.2 The committed system

| Element | Choice | Justification |
|---|---|---|
| Base fluid | **NaCl–KCl–MgCl₂ ternary chloride eutectic** ("A1") | Reaches ~700–800 °C, matching the sCO₂ recompression cycle's preferred hot end; nitrate salts cap near 565 °C |
| Nanoparticle | **CuO** | Measured cp/k series exists in the *exact* base salt (Han et al. 2022) |
| cp / k anchor | Han et al. 2022, *Sol. Energy Mater. Sol. Cells* 245:111852 | Same base salt, same particle, three loadings (0.2 / 0.7 / 2.0 wt%) |
| Mechanism reference | Shin & Banerjee 2011, *IJHMT* 54:1064 | **Mechanism only** — different eutectic, never used for magnitudes |

### 4.3 Base-fluid correlations (A1 set, T in °C, SI out)

```
ρ(T)  = 1958.8438 − 0.56355·T                          kg/m³
cp(T) = 1301.38 − 0.5·T                                J/(kg·K)
k(T)  = 0.5822 − 2.6×10⁻⁴·T                            W/(m·K)
μ(T)  = 1×10⁻³ · 0.70645 · exp(1204.11348/(T + 273.15)) Pa·s
```

**Stated validity 450–700 °C**, with extrapolation to 800 °C endorsed by the source authors.
Melting point **401.4 °C (±1.3)** — Han's companion measurement of 399.7 °C is consistent.

95 % uncertainties (converted to SI): ρ ±15.27 kg/m³ · cp ±35.8 J/(kg·K) · k ±0.037 W/(m·K) ·
μ ±1.138×10⁻⁴ Pa·s.

> **Unit traps documented in the code, because this is where silent bugs live.** The source cp is
> in J/(g·K) (×1000 applied) and μ in cP (×10⁻³ applied). The exponent's `(T + 273.15)` is an
> *internal* °C→K conversion, so temperature must still be passed in Celsius — pre-converting
> double-counts.

### 4.4 Nanoparticle constants and their provenance

| Constant | Value | Provenance |
|---|---|---|
| ρ_CuO | 6320 kg/m³ | **Not a free choice** — back-solving Han's own Table 2 density data gives 6317 kg/m³, so this value keeps the module numerically consistent with its anchor paper |
| cp_CuO | 667.1 J/(kg·K) | **Pinned to a primary source.** NIST-JANAF via NIST WebBook: tabulated Cp at 700 K (52.24 J/mol·K) and 800 K (53.35) interpolated to 773.15 K gives 53.05 J/mol·K, matching the Shomate equation at the same T (53.06) to 0.02 % — two independent readings of the same data agree. ÷ M(CuO) = 0.079545 kg/mol |
| k_CuO | 33 W/(m·K) | **Deliberately deferred and disclosed.** Bulk CuO conductivity is genuinely scarce; Zhang et al. (2024) call it "seldom mentioned" and "impractical to test directly." Low impact: this value feeds **only** the Maxwell floor (a lower band edge), never a reported nominal |

### 4.5 Enhancement models — the anchor data and the fits

**Measured anchors (Han 2022, liquid region 450–550 °C — the cycle's operating region):**

| φ (wt%) | Δcp | Δk |
|---|---|---|
| 0.2 | **+3.93 %** | **+15.85 %** |
| 0.7 | **+10.51 %** | **+33.94 %** *(derived — see below)* |
| 2.0 | **−3.53 %** | **+39.55 %** |

**The k midpoint is derived, and the derivation is self-validating.** Han reports only the k
endpoints. The 0.7 wt% value is reconstructed from the paper's own components via its Eq. (1),
k = α·ρ·cp, using tabulated 500 °C densities, diffusivity ratios and liquid cp ratios:

```
0.2 wt%:  1.1095 × (1726/1717) × 1.0393 = 1.1591  →  +15.91 %   (published: +15.85 %)
0.7 wt%:  1.1898 × (1749/1717) × 1.1051 = 1.3394  →  +33.94 %   ← derived, used
2.0 wt%:  1.3723 × (1809/1717) × 0.9647 = 1.3948  →  +39.48 %   (published: +39.55 %)
```

The two derived **endpoints** reproduce Han's published values to within **0.07 percentage points**,
which validates the derivation and licenses use of the middle point.

**Fit choices, and why they are the conservative ones:**

- **cp — piecewise-linear (committed default).** With only three measured points, no fit can
  distinguish curve shapes, so the module adopts the interpolant claiming the **least unmeasured
  structure**. Linear honours every data point exactly and places its maximum at a real measurement
  (0.7 wt%) rather than at an inferred location.
- **cp — exact cubic through the three points and the origin (sensitivity case only).** It places a
  peak near **~1.0 wt% at ~+11.7 %**. This is an *inferred* optimum between measured loadings — a
  model artifact, not a measurement. Report both; do not treat the cubic peak as physical. Denser
  cp data (≥ 4 loadings) is what would justify committing to a smooth fit.
- **k — saturating, E(φ) = A(1 − e^(−φ/τ)), least-squares.** Monotonic and saturating *by
  construction*, so unlike a cubic it cannot invent a non-physical dip between measured points.

**Uncertainty band construction.** Bands combine the A1 base-salt 95 % uncertainty with a
*relative* uncertainty on the enhancement itself: **±50 % on E_cp**, **±35 % on E_k**. The rationale
is explicit and defensible: Han's *measurement precision* is tight (cp ±0.001 J/g·K, k within 4 %),
but the real uncertainty is whether Han's curve transfers to a plant fluid with a different
preparation route, particle size, dispersion state and ageing history. Chloride cp enhancements
across the literature span roughly 6–38 %, and the bands reflect that.

**Hard guard against extrapolation.** Requesting φ > 2.0 wt% raises a `ValueError` with the message
"constrain the optimiser instead of extrapolating the enhancement fits." The property module
therefore enforces its own validity domain on any optimiser that calls it.

### 4.6 Theoretical floors — and the anomaly they expose

Two effective-medium models are implemented, used **only as lower band edges, never as nominals**:

- **Maxwell** k for dilute spheres.
- **Brinkman** μ for dilute rigid spheres, μ/(1 − φ_v)^2.5.

The Maxwell floor is where the physics gets interesting and belongs in the discussion chapter.
Maxwell's enhancement is bounded by ≈ 3φ_v regardless of particle conductivity. At 0.7 wt% CuO the
**volume** fraction is only φ_v ≈ 0.0019, so Maxwell caps out near **+0.6 %** while Han **measured
≈ +34 %** — a factor of ~57. That gap *is* the nanofluid anomaly (interfacial layering,
nanostructure, percolation), for which effective-medium theory has no term. This is the strongest
single argument in the thesis for why nano-enhancement is a genuine phenomenon requiring
measurement-anchored modelling rather than mixing rules.

The same argument applies to cp: the classical mass-weighted mixing rule predicts a **decrease**,
and is contradicted by measurement. The module therefore models cp_nf = cp_base(T)·(1 + E(φ)) rather
than mixing.

### 4.7 The viscosity gap — the module's weakest input, handled explicitly

**No experimental viscosity exists for any CuO-loaded chloride salt anywhere in the literature.**
This is a field-wide gap, not a local one, and `SOURCES.md` §C0 establishes it as the headline
framing: for nano-loaded chlorides, viscosity is **MD-derived across the entire field**, and the
nanoparticle-in-chloride viscosity studies that do exist use SiO₂ or Al₂O₃, never CuO.

The band is therefore **constructed from chloride-family MD analogues and declared as such**:

| Band edge | Value | Source |
|---|---|---|
| lo | Brinkman floor | supported by reports of molten-salt nanofluids with nearly unaltered viscosity (Wei et al. 2020) |
| **nominal** | **+2.9 % per 1 wt%** | SiO₂/(LiCl–KCl) MD, 6 wt% → +17.21 % (Tian, Zhang & Kou 2024) |
| hi | +38.6 % per 1 wt% | Al₂O₃/(NaCl–KCl) MD, 7 vol% → +34.8 to +38.6 % |

This replaced an earlier, more pessimistic band built from *nitrate* cross-chemistry data;
chloride-family MD gives materially smaller viscosity penalties, and same-chemistry analogues are a
strictly better basis.

**Two caveats the thesis must state, both already in the code:**

1. The two grounding studies report in **different fraction bases** (wt% vs vol%) over different
   loading ranges, so "%/wt%" is a defensible central estimate from the lowest-loading, most
   directly comparable point — **not a formal regression**.
2. **Molten-salt nanofluids are frequently shear-thinning**, so a single μ does not strictly exist.
   The value must be interpreted as an **apparent viscosity at the pump/receiver shear rate**, and
   that choice stated in the methodology.

**Draft provenance sentence (from `PROPERTIES.md`, ready to adapt):**

> "In the absence of experimental viscosity data for CuO-loaded chloride eutectics — a gap common to
> the entire nano-chloride literature, where reported nanoparticle viscosities are themselves
> MD-derived (e.g. SiO₂/Al₂O₃ in NaCl–KCl–MgCl₂, Tian et al. 2024) — the viscosity of the
> CuO-enhanced HTF was obtained by molecular-dynamics simulation, with the φ = 0 base-salt viscosity
> validated against published MD correlations for MgCl₂–NaCl–KCl (Jiang et al. 2024; Xu et al. 2022)
> to within their reported uncertainty."

**If a reviewer presses:** the stated next step is dedicated MD (Green–Kubo or NEMD) on CuO/A1
specifically, validated first against Han's measured cp and k so the force field is trusted before
being extended to predict viscosity.

### 4.8 A disclosed internal inconsistency (this is a credibility asset)

Han's tabulated densities are reproduced exactly by substituting the **mass** fraction into their
Eq. (2), which is written for **volume** fraction (at 0.7 wt%: mass-fraction gives 1749.2 kg/m³
against their tabulated 1749; the correct volume-fraction calculation gives 1725.8). This module
uses the **volume** fraction and therefore **deliberately differs from Han's tabulated densities**.

The consequence is tracked rather than ignored: Han's k, being derived as k = α·ρ·cp, inherits that
density offset — approximately **+0.4 % at 0.2 wt% rising to +3.8 % at 2.0 wt%**. That is small
relative to the k band, and it is **absorbed into the lower band edge** in `conductivity_nf()`.

### 4.9 Verified output — the 0.7 wt% property table at plant conditions

`results/sam_htf_table_0p7wt.csv`, the nominal band, 0.7 wt% CuO:

| T (°C) | cp (kJ/kg·K) | ρ (kg/m³) | μ (Pa·s) | ν (m²/s) | k (W/m·K) | h (J/kg) |
|---|---|---|---|---|---|---|
| 450 | 1.18951 | 1714.01 | 3.81023×10⁻³ | 2.22299×10⁻⁶ | 0.621112 | 58 462.6 |
| 500 | 1.16188 | 1685.74 | 3.42125×10⁻³ | 2.02953×10⁻⁶ | 0.603755 | 117 247 |
| 550 | 1.13425 | 1657.47 | 3.11244×10⁻³ | 1.87783×10⁻⁶ | 0.586398 | 174 651 |
| 600 | 1.10663 | 1629.19 | 2.86234×10⁻³ | 1.75691×10⁻⁶ | 0.569041 | 230 673 |
| 650 | 1.07900 | 1600.92 | 2.65633×10⁻³ | 1.65926×10⁻⁶ | 0.551684 | 285 313 |
| 700 | 1.05137 | 1572.64 | 2.48415×10⁻³ | 1.57960×10⁻⁶ | 0.534327 | 338 572 |

Enthalpy uses the **melting point (401.4 °C) as datum** — a physically defensible choice, disclosed
as not yet cross-checked against SAM's internal convention.

### 4.10 Self-validation

`validate()` re-checks every fit against Han's measured anchors and is the drift detector for this
module: cp within 1×10⁻⁹ (exact, by construction of the linear interpolant), k within 0.03 absolute
on the enhancement fraction. All six anchor points reproduce. The module was moved into `scripts/`
with its physics **byte-for-byte unchanged**; only the docstring, an output path and one duplicated
`return` were touched.

---

## 5. MODULE B — THE sCO₂ POWER BLOCK AND ITS VALIDATION

*(Chapter 3.4 methodology; Chapter 4.2 results — this is the strongest chapter in the thesis)*
**Scripts:** `validate_dostal.py`, `compare_dostal_nodes.py`, `check_untabulated_nodes.py`,
`check_dostal_table_consistency.py`, `dostal_dp_recup_matrix.py`
**Status:** ✅ validation gate **PASSED**.

### 5.1 Choice of validation anchor, and why the obvious candidates were rejected

The requirement was a published sCO₂ recompression case reporting **per-node h and s**, not merely
design-point efficiency — because the project's downstream work (exergy, MOO) is computed from state
points, so an efficiency match validates nothing that matters.

| Candidate | Verdict |
|---|---|
| **Dostal, Driscoll & Hejzlar 2004 (MIT-ANP-TR-100)** | **SELECTED.** Publishes full node state tables (T, P, h, s) for three recompression designs at 550 / 650 / 700 °C |
| Dyreby 2014 | Design inputs only, no per-node h/s. Also **circular**: SAM's sCO₂ block is built on Dyreby's method, so agreement tests implementation fidelity, not physics |
| Turchi 2013, Chacartegui 2011 | Config-level efficiency only |

**Validation case:** High-Performance 700 °C (Table 10.4, p. 229). Common conditions: 600 MWth,
compressor inlet 32 °C, P_high 20 MPa, PR 2.6, primary-system ΔP 130 kPa, η_turbine 90 %,
η_MC = η_RC 89 % (conservative columns), stated η_thermal **51.27 %**.

### 5.2 The node map — written before any error was computed

Dostal's layout has **8 numbered nodes**; the recompressed stream mixes back **between the LTR and
HTR**. The published-node → model-index mapping was written down explicitly *first*, because a
silent numbering mismatch would make the entire error table wrong while looking plausible:

| Dostal | Definition | Model node |
|---|---|---|
| 1 | main compressor inlet (= precooler outlet) | `MC_IN` |
| 2 | main compressor outlet (= LTR cold inlet) | `MC_OUT` |
| 3 | LTR cold outlet **after** mixing with recompressed flow | `MIXER_OUT` |
| 4 | HTR cold outlet (= PHX inlet) | `HTR_HP_OUT` |
| 5 | turbine inlet (= PHX outlet) | `TURB_IN` |
| 6 | turbine outlet (= HTR hot inlet) | `TURB_OUT` |
| 7 | HTR hot outlet (= LTR hot inlet) | `HTR_LP_OUT` |
| 8 | LTR hot outlet (= precooler + recompressor inlet) | `LTR_LP_OUT` |

**Two model nodes have no published row** — `LTR_HP_OUT` (LTR cold outlet *before* mixing) and
`RC_OUT` (recompressor outlet), because Dostal's node 3 is already post-mix. These are validated by
conservation instead (§5.5). Dostal's `id` (ideal isentropic) and `max` (max-regeneration) rows are
**reference states, never error targets** — they are used only to confirm that isentropic efficiency
and recuperator effectiveness are applied correctly.

**Error-metric convention:** % error on temperature uses the **absolute (K) denominator**. Node 1 is
at 32 °C, so a Celsius denominator would inflate a 0.5 K miss into 1.6 %.

### 5.3 The adopted baseline — case F

Reached after the diagnostic campaign of §5.6. Configuration: **f_rc = 0.4097**, recuperators at a
**10 K approach** on both, **Dostal's own per-HX pressure losses**, η_MC = η_RC = 0.89, η_t = 0.90,
P_high 20 MPa, PR 2.6, TIT 700 °C, T_MC,in 32 °C.

```
eta_thermal_calc = 0.51289    ← Dostal 51.27 %  (+0.019 pp, +0.036 % relative)
recomp_frac      = 0.40970    m_dot_co2 = 92.233 kg/s   (m_dot_htf 75.362 kg/s)
P_comp_in        = 7.6923 MPa P_comp_out = 20.0000 MPa  (PR 2.6000)
eff_HTR          = 0.97625    eff_LTR    = 0.93095      ← UNEQUAL, and that is correct
T_turb_out       = 578.309 °C T_HTR_HP_out = 531.256 °C
recup UA total   = 2306.6 kW/K
total Sgen       = +10.22522 kW/K  (all 8 components > 0)
W_turb 13317.63 − W_mc 1120.56 − W_rc 2197.06 = 10000.00 kW   (power balance err 1.8×10⁻¹²)
q_PHX 19497.52 = W_net 10000.00 + q_cool 9495.57              (energy balance err 1.944 kW)
```

**Full case F state table** (`results/dostal_state_points_20260813T023249Z.csv`):

| # | Node | T (°C) | P (kPa) | h (kJ/kg) | s (kJ/kg·K) |
|---|---|---|---|---|---|
| 0 | `MC_IN` | 32.000 | 7 692.31 | 306.675 | 1.34780 |
| 1 | `MC_OUT` | 61.099 | 20 000.00 | 327.256 | 1.35458 |
| 2 | `LTR_HP_OUT` | 159.407 | 19 990.22 | 538.320 | 1.91508 |
| 3 | `MIXER_OUT` | 159.643 | 19 990.22 | 538.690 | 1.91593 |
| 4 | `HTR_HP_OUT` | 531.256 | 19 944.56 | 1011.945 | 2.71310 |
| 5 | `TURB_IN` | 700.000 | 19 814.56 | 1223.339 | 2.95286 |
| 6 | `TURB_OUT` | 578.309 | 7 929.22 | 1078.948 | 2.97185 |
| 7 | `HTR_LP_OUT` | 169.583 | 7 802.64 | 605.672 | 2.22055 |
| 8 | `LTR_LP_OUT` | 71.127 | 7 704.93 | 481.081 | 1.90233 |
| 9 | `RC_OUT` | 159.983 | 19 990.22 | 539.223 | 1.91716 |

*(Nodes 10–11, `PC_IN`/`PC_OUT`, are NaN by design — they exist only for the partial-cooling
configuration. Never sum the raw 12-element arrays.)*

### 5.4 The headline result — the node-by-node error table

`scripts/compare_dostal_nodes.py` vs Dostal Table 10.4:

| Dostal pt | Node | T err | P err | **h err** | **s err** | Flag |
|---|---|---|---|---|---|---|
| 1 | `MC_IN` | +0.000 % | −0.000 % | +0.002 % | −0.000 % | |
| 2 | `MC_OUT` | −0.000 % | +0.000 % | −0.001 % | −0.002 % | |
| 3 | `MIXER_OUT` | −0.055 % | +0.000 % | −0.070 % | −0.045 % | |
| 4 | `HTR_HP_OUT` | −0.009 % | +0.000 % | −0.008 % | −0.004 % | |
| 5 | `TURB_IN` | +0.000 % | +0.000 % | −0.000 % | −0.001 % | |
| 6 | `TURB_OUT` | −0.000 % | −0.000 % | −0.000 % | −0.002 % | |
| 7 | `HTR_LP_OUT` | −0.060 % | −0.000 % | −0.051 % | −0.029 % | |
| 8 | `LTR_LP_OUT` | +0.022 % | −0.000 % | +0.025 % | +0.017 % | |

**Worst / RMS:** T −0.060 % / 0.030 % · P −0.000 % / 0.000 % · **h −0.070 % / 0.032 %** ·
**s −0.045 % / 0.020 %** · **η +0.019 pp.**
**No node is flagged at any threshold down to 0.1 %.**

**Independent property verification.** Every node was re-evaluated from its solved (T, P) with
CoolProp 8.0.0: max |Δh| = **1.04×10⁻⁴ kJ/kg**, max |Δs| = **2.50×10⁻⁷ kJ/kg·K**. ssc's internal
CO₂ properties are therefore effectively REFPROP-equivalent, and **the project needs no separate CO₂
property lane**. CoolProp is nonetheless retained inside the validation script so that the mixer and
second-law checks do not depend on ssc being self-consistent with itself.

### 5.5 The two untabulated nodes — validated by conservation

Each check was deliberately **split into an internal variant** (driven by the model's own nodes —
tests the physics) **and an absolute variant** (driven by Dostal's numbers — inherits any offset).
Collapsing them would hide which physics actually failed.

| Check | Basis | Expected | Model | Δ | % | Result |
|---|---|---|---|---|---|---|
| 1A — junction closes on our own nodes | model | 566.2928 | 566.2928 | +0.0000 | +0.000 % | **PASS** |
| 1B — same mix vs Dostal h₃ | Dostal | 539.0700 | 566.2928 | +27.2228 | +5.050 % | FAIL *(under case A)* → **PASS under case F** |
| 1B swapped-convention variant | Dostal | 539.0700 | 557.6326 | +18.5626 | +3.443 % | FAIL — convention ruled out |
| 2A — RC isentropic relation, Dostal node 8 | Dostal | 539.1148 | 542.2806 | +3.1658 | +0.587 % | **PASS** |
| 2B — RC isentropic relation, our node 8 | model | 542.2806 | 542.2806 | −0.0000 | −0.000 % | **PASS** |

**The logic that makes this airtight:**

- `RC_OUT` is confirmed **independently of the mixer** — Check 2 never touches `LTR_HP_OUT`. It
  closes to −0.0000 kJ/kg against our own node 8, so ssc applies η_rc = 0.89 to the letter.
- `LTR_HP_OUT` is then **pinned by 1A**: with `RC_OUT` independently confirmed and the junction
  closing exactly, it is the only remaining unknown in the mass/energy balance.
- **The split-fraction convention is confirmed, not assumed.** The swapped form was evaluated
  explicitly: it is still wrong against Dostal *and* would destroy the exact internal closure.

> **A double-counting warning to carry into the write-up.** Because 1A closes to zero, 1B is
> *arithmetically the same quantity* as the `MIXER_OUT` h error in the main table. It must **not** be
> reported as a second, separate failure — doing so counts one discrepancy twice.

**Thesis wording:** *"Eight state points were validated directly against Dostal (2004); the two
intermediate nodes internal to the recompression junction, which Dostal does not tabulate
separately, were validated by energy-balance closure at the mixing point and by the recompressor
isentropic relation."* Frame as a strength — it confirms junction physics, not just endpoints.

### 5.6 How case F was reached — the diagnostic campaign (Chapter 4's best narrative)

This is the most instructive sequence in the project and should be told as a story, because it
shows the difference between agreeing with a number and reproducing a system.

**Step 0 — the starting point (case A) agreed on η and was wrong.** Specifying both recuperators at
effectiveness 0.95, lossless, f = 0.39 gave η = 51.532 % — only +0.262 pp from Dostal. But the node
table showed **two flagged nodes at +5.05 % and +5.37 % in h**, and crucially they were **the two
ends of the LTR/HTR interface**, not scattered. Everything *outside* the recuperator train agreed to
≤ 1.1 %.

**Step 1 — diagnosis: a recuperator duty-split difference, not a defect.**

| | HTR duty (kJ/kg) | HTR cold-end approach |
|---|---|---|
| Dostal | 472.96 | ≈ 9.97 K |
| Case A model | 434.61 | ≈ 20.13 K |

Our HTR moved **8 % less heat**; the LTR compensated (our `MIXER_OUT` ran 18 K hotter), so total
regeneration and hence η still landed close. **Root cause:** Dostal allocates a fixed **120 m³ total
HX volume** between the two recuperators, producing an *unequal* split, which an equal-effectiveness
specification structurally cannot represent.

**Step 2 — the 2×2 confirmed the direction but refuted the sufficiency.** Both predicted signs held
(tightening the recuperators alone **+0.359 pp**; adding ΔP alone **−1.205 pp**), but the magnitudes
do not cancel — ΔP costs roughly 3× what tightening gains — so doing both **undershot to −0.612 pp**
and still left a flagged node. *Two compensating errors was the wrong model; there were three.*

**Step 3 — the third factor was found in Dostal's own tables, not in ours.** Imposing the HTR, LTR
and mixer balances on his **published** values, with `RC_OUT` fixed independently by the
recompressor isentropic relation, closes the mixer only at **f = 0.4097** — not the stated 0.39.

*The robustness test that makes this a finding rather than a fudge.* f_implied depends on the assumed
η_rc, so a different η_rc might in principle rescue 0.39. It cannot, and running Dostal's **Advanced
650 °C design as a control** makes the contrast sharp:

| Design | f stated | η_rc that would justify it | f at η_rc 0.89 | f at η_rc 0.948 |
|---|---|---|---|---|
| Advanced 650 °C (**control**) | 0.41 | **0.9318 — plausible**, between Dostal's own two stated values | 0.4049 | 0.4119 |
| High-Performance 700 °C | 0.39 | **0.7519 — not plausible**, far below anything he states | 0.4097 | 0.4167 |

The control reconciles at an ordinary recompressor efficiency (Δ 0.005, which **calibrates the
method's resolution** and makes the High-Performance discrepancy **4× the noise floor**); the
High-Performance design would need a 75 % recompressor against his stated 89 % / 94.8 %. At
f = 0.4097 the two mixing streams differ by **0.076 kJ/kg** — a near-isenthalpic junction, the
hallmark of an optimised mixing point.

**Step 4 — the case matrix. All three factors together reproduce the published table.**

| Case | Configuration | η % | Δ pp | MIXER h err | HTR_LP h err | RMS h | Flags |
|---|---|---|---|---|---|---|---|
| A | ε 0.95, lossless | 51.532 | +0.262 | +5.050 % | +5.373 % | 2.649 % | 2 |
| B | 10 K approach only | 51.891 | +0.621 | −2.500 % | −1.522 % | 1.109 % | 1 |
| C | Dostal ΔP only | 50.327 | −0.943 | +5.026 % | +5.329 % | 2.600 % | 2 |
| D | 10 K + ΔP | 50.658 | −0.612 | −2.824 % | −1.820 % | 1.197 % | 1 |
| E | f = 0.4097 only | 51.174 | −0.096 | +5.980 % | +5.987 % | 3.082 % | 2 |
| **F** | **f = 0.4097 + 10 K + Dostal ΔP** | **51.289** | **+0.019** | **−0.070 %** | **−0.051 %** | **0.032 %** | **0** |

**Nothing in case F is fitted.** All three settings are *read off* Dostal's own tables:

- **ΔP** derived as consecutive differences of Table 10.4's node pressures. The PHX difference comes
  out at exactly **130.00 kPa**, matching Table 10.1's stated primary-system ΔP — an independent
  confirmation of the derivation:

  | | LTR_HP | HTR_HP | **PHX** | HTR_LP | LTR_LP | cooler |
  |---|---|---|---|---|---|---|
  | ΔP (kPa) | 9.78 | 45.66 | **130.00** | 126.58 | 97.71 | 12.62 |
  | fraction of inlet | 0.000489 | 0.002284 | 0.006518 | 0.015964 | 0.012523 | 0.001638 |

- **10 K approach** read off Table 10.4 (HTR cold end 169.85 − 159.88 = 9.97 K; LTR
  71.05 − 61.10 = 9.95 K).
- **f = 0.4097** from the three-balance reduction above.

Case F's recuperators come out **unequal — ε_HTR 0.976 / ε_LTR 0.931 —** confirming the Step-1
inference about the 120 m³ volume allocation. And the model now **produces** near-isenthalpic mixing
(`LTR_HP_OUT` 538.32 vs `RC_OUT` 539.22 kJ/kg), which was *predicted from Dostal's numbers
beforehand* rather than imposed.

**Why case F was adopted over the η-matching case A.** The downstream work is exergy and MOO, both
computed from **state points**, not η. Case A's HTR moved 8 % less heat, and that error lands
squarely on the cycle's **largest exergy destroyer**. Case A was right about the bulk number for the
wrong reasons — two cancelling errors — and such an agreement does not survive moving off the design
point, which is exactly what an optimiser does.

**The residual caveat, to state in one sentence in the thesis:** f = 0.4097 rests on strong evidence,
not proof. The alternative reading is a slightly different topology or an off-optimum junction that
the three-balance reduction misses — unlikely given the near-isenthalpic mixing and the control
design's behaviour, but not excludable from the tables alone.

### 5.7 The regression anchor (case A), retained deliberately

```
eta_thermal_calc = 0.51532    recomp_frac = 0.39000    m_dot_co2 = 87.269 kg/s
eff_HTR = eff_LTR = 0.95000   recup UA total = 1882.3 kW/K
T_turb_out = 573.364 °C       T_HTR_HP_out = 522.367 °C
total Sgen = +9.91403 kW/K
```

**Never quote these as validation** — internal state points are wrong by up to 5.4 %. Its sole job
is drift detection: it reproduces bit-for-bit across machines and Python patches, so any change here
is an environment or ssc problem rather than a modelling one.

### 5.8 The recuperator effectiveness sweep (legacy parameterisation)

| ε | η_thermal | Δ vs Dostal (pp) | UA_tot (kW/K) |
|---|---|---|---|
| 0.900 | 0.47594 | −3.68 | 1114.2 |
| 0.920 | 0.49163 | −2.11 | 1326.6 |
| 0.930 | 0.49951 | −1.32 | 1468.4 |
| 0.940 | 0.50745 | −0.52 | 1646.9 |
| 0.945 | 0.51140 | −0.13 | 1755.7 |
| 0.950 | 0.51532 | +0.26 | 1882.3 |
| 0.960 | 0.52306 | +1.04 | 2213.4 |
| 0.970 | 0.53057 | +1.79 | 2731.4 |

Dostal's 51.27 % is reproduced at ε ≈ **0.9467**. This sweep is the evidence for the Step-1/Step-2
tension (the model matched η at *looser* recuperators than Dostal's own ~10 K approach implies) and
should be reported as such — it says nothing about case F.

### 5.9 Convergence behaviour worth reporting

Dyreby's documented warning about convergence difficulty near the critical point at 20 MPa / 32 °C
**did not materialise**: `P_comp_in = 7.6923 MPa` and `T_comp_in = 32.000 °C` exactly, and the
implemented `P_LOW_OFFSET_MPA = 0.3` fallback never fired in any run. Every design target was hit
exactly.

---

## 6. MODULE C — COMPONENT-LEVEL EXERGY LAYER

*(Chapter 3.5 methodology; Chapter 4.3 results)*
**Script:** `scripts/exergy_layer_check.py` · **Data:** `results/exergy_layer_check_20260813T023227Z.{md,csv}`
**Status:** ✅ method verified end-to-end on the standalone cycle.

### 6.1 Method

Physical exergy at every node, e = (h − h₀) − T₀(s − s₀), and Gouy–Stodola destruction
Ė_D = T₀·Ṡ_gen per component — computed **entirely from data the model already carries**. The
per-component second-law physics is written once in `validate_dostal.entropy_generation()` and
shared, rather than duplicated.

The template for the component equations is Atif & Al-Sulaiman (2018), which gives component-level
exergy-destruction equations (Eqs. 41–56) for **this exact topology** — recompression sCO₂ + two-tank
molten salt + central receiver. The algebra is therefore transcription, not derivation, which is why
the risk assessment for including exergy came down so sharply.

### 6.2 Per-node physical exergy (case F)

| # | Node | T (°C) | e @ T₀_ref (kJ/kg) | e @ T₀_amb (kJ/kg) |
|---|---|---|---|---|
| 0 | `MC_IN` | 32.000 | 0.0000 | 0.0000 |
| 1 | `MC_OUT` | 61.099 | 18.5119 | 18.5526 |
| 2 | `LTR_HP_OUT` | 159.407 | 58.5392 | 61.9429 |
| 3 | `MIXER_OUT` | 159.643 | 58.6482 | 62.0570 |
| 4 | `HTR_HP_OUT` | 531.256 | 288.6469 | 296.8387 |
| **5** | **`TURB_IN`** | **700.000** | **426.8784 ← max** | **436.5088** |
| 6 | `TURB_OUT` | 578.309 | 276.6923 | 286.4366 |
| 7 | `HTR_LP_OUT` | 169.583 | 32.6753 | 37.9119 |
| 8 | `LTR_LP_OUT` | 71.127 | 5.1906 | 8.5178 |
| 9 | `RC_OUT` | 159.983 | 58.8056 | 62.2218 |

### 6.3 Component exergy destruction — the ranking

| Component | Ṡ_gen (kW/K) | **Ė_D @ T₀_amb (kW)** | Share |
|---|---|---|---|
| **HTR** high-T recuperator | +4.23071 | **1265.62** | **41.4 %** |
| TURB turbine | +1.75154 | 523.97 | 17.1 % |
| COOL precooler | +1.55023 | 463.75 | 15.2 % |
| LTR low-T recuperator | +1.16569 | 348.71 | 11.4 % |
| PHX primary HX | +0.59713 | 178.63 | 5.8 % |
| RC recompressor | +0.56061 | 167.71 | 5.5 % |
| MC main compressor | +0.36927 | 110.47 | 3.6 % |
| MIX mixer | +0.00003 | **0.01** | 0.0 % |
| **TOTAL** | **+10.22521** | **3058.87** | 100 % |

### 6.4 The five verification checks — all pass

| Check | Result |
|---|---|
| e = 0 at the reference node | exact (0.000×10⁰) |
| exergy maximal at the turbine inlet | node 5, 426.88 kJ/kg |
| every component Ė_D > 0 | 8 of 8 |
| **HTR is the largest single destroyer** | **1265.62 kW = 41.4 %** — matches Battisti et al. 2023 independently |
| **cycle-wide balance closes** | Ex_in 13 060.82 = W_net 10 000.00 + ΣĖ_D 3058.87 → residual **1.949 kW = 1.5×10⁻⁴ relative** |

**Second-law (exergy) efficiency = 76.56 %.**

**The balance is the load-bearing check.** It exercises every *h*, every *s*, both mass flows, the
salt-side properties and the work terms simultaneously — so it catches scaling and unit errors that
per-component sign checks structurally cannot (cf. the 1000× mass-flow trap in §10).

### 6.5 Two findings inside the exergy layer

**(a) The mixer's near-zero destruction is independent confirmation of case F.** `MIX` destroys
**0.01 kW** under case F against **16.14 kW** under legacy case A. That is the second-law signature
of the near-isenthalpic junction — the adopted baseline's mixing point is confirmed by a completely
different physical argument from the one that selected it.

**(b) A T₀ correction that affects every Ė_D number reported downstream.** Two reference
temperatures are in play and they are **not interchangeable**:

- The per-node reference (Dostal node 1, **305.15 K at 7.69 MPa**) is a **reference state, not a
  dead state** — the cycle cannot reject heat to 7.69 MPa, so e = 0 there is true *by construction*
  and verifies the wiring, not the physics.
- Gouy–Stodola Ė_D = T₀·Ṡ_gen is only meaningful at the **environment** temperature,
  **T_amb = 299.15 K**.

Using node 1 instead inflates every Ė_D by ~2 % and leaves the exergy balance open by **−188.5 kW
(−1.46 %)** rather than closing to 1.95 kW. **The component ranking is identical either way — so no
sanity check catches this; only the balance does.** Both are computed and printed side by side so
the distinction cannot be lost. **Report Ė_D at T_amb.**

### 6.6 What this closes, and what remains

The `MASTER_PLAN` §5 risk — "does PySAM expose per-state entropy, or do we need a +1-day CoolProp
reconstruction?" — is **closed by execution, not merely judged unlikely**. `min Ė_D`, a named
primary objective, is confirmed computable from data the model already carries.

**What remains for a full Objective-2 exergy assessment:** wiring this layer to the *integrated*
model and adding the **receiver, TES and hot/cold tank** destruction terms. That is wiring work
against a model that does not yet exist (§9), not method risk. The deferred Battisti cross-check is
**already satisfied for the cycle** at no cost, since the HTR-dominant ranking matches.

---

## 7. MODULE D — NANO-HTF ⇄ SAM PLANT COUPLING

*(Chapter 3.6 methodology; Chapter 4.4 results — this section carries the study's most consequential
physical finding)*
**Script:** `scripts/htf_sam_bridge.py` · **Data:** `results/htf_sam_bridge_20260813T025745Z.{md,csv}`
**Status:** ✅ complete — the question is answered, and two constraints came with the answer.

### 7.1 The question, and the experimental design

`rec_htf = 50` accepts a user-defined 7-column property table, so an override path exists **on
paper**. What had never been tested is whether SAM *accepts* the chloride across its real operating
range and still solves — and, separately, whether the result is *trustworthy*. Those are different
questions.

**The design changes exactly one thing: the working fluid.** The power block is deliberately left as
SAM's stock steam Rankine, so any difference reported is attributable to the fluid and not to a
simultaneous cycle swap. All cases run on the Morocco/Ouarzazate NSRDB TMY (lat 31.05, lon −6.86),
and **the solar field and receiver duty are held fixed** across every case (A_sf = 1 348 316 m²,
q̇_rec,des = 669.90 MW) — so the comparisons below are at constant collected energy.

**Crash safety as method.** A malformed property table *segfaults* ssc rather than raising. Every
case therefore runs in **its own subprocess** with unbuffered output, so one crash costs one case
rather than the whole matrix, and a segfault is *recorded as a result* (exit 139) rather than as an
absence of one.

**The single highest-risk line in the bridge** is the cp unit conversion: SAM wants **kJ/(kg·K)**
while the property model works in J/(kg·K). Getting it wrong is a silent 1000× error that no shape
check can catch — so it is **asserted on** (cp must land in 0.1–10) rather than trusted.

### 7.2 Results — the full case matrix

| Case | Fluid | φ (wt%) | T_hot / T_cold (°C) | ΔT (K) | Annual energy (GWh) | Nameplate (kW) | W_pump,rec,des (MW) | CF (%) | Status |
|---|---|---|---|---|---|---|---|---|---|
| `nitrate_baseline` | nitrate (code 17) | — | 574 / 290 | 284 | **530.18** | 101 663 | **8.49** | 59.53 | OK |
| `chloride_574_450` | nano-chloride (50) | 0.7 | 574 / 450 | **124** | *288.65* | **−52 858** | **162.30** | 0.00 | **INFEASIBLE** |
| `chloride_700_450` | nano-chloride (50) | 0.7 | 700 / 450 | 250 | **479.23** | 82 923 | 27.04 | 65.97 | OK |
| `base_salt_700_450` | chloride, no CuO (50) | 0.0 | 700 / 450 | 250 | 466.31 | 74 596 | 35.31 | 71.36 | OK |
| `chloride_max_loading` | nano-chloride (50) | 2.0 | 700 / 450 | 250 | 462.95 | 71 946 | 37.94 | 73.46 | OK |
| `table_too_narrow` | nano-chloride (50) | 0.7 | 700 / 450 | 250 | 479.23 | 82 923 | 27.04 | 65.97 | OK *(see 7.6)* |
| `table_min_rows` | nano-chloride (50) | 0.7 | 700 / 450 | 250 | 479.24 | 82 925 | 27.04 | 65.97 | OK *(see 7.6)* |

### 7.3 Finding 1 — the coupling works, inside SAM

`rec_htf = 50` **accepts** the nano-chloride table across 450–700 °C, stores it with **zero
round-trip deviation** (`roundtrip_rel = 0.0`) across all six chloride cases, and the annual model
solves on it. **No external coupling layer is needed.** This answers the project's longest-standing
open question and supersedes the working assumption of `DECISIONS.md` D2.

Note that the table goes on the **receiver** group (`TowerAndReceiver.field_fl_props`) and there is
only **one** fluid definition serving receiver, field and TES alike.

### 7.4 Finding 2 — acceptance is not validity: the ΔT → pumping coupling

**This is the study's most consequential physical result and it is a genuine contribution.**

The chloride melts at **401.4 °C**, so the cold tank cannot approach nitrate's 290 °C — 450 °C is
the practical floor with a freeze margin. A chloride run at the *nitrate* hot temperature therefore
has only a **124 K loop ΔT**, and at fixed duty a narrow ΔT means high mass flow, which in a
friction-dominated loop drives pumping power steeply:

| Loop ΔT | W_pump,rec,des | Nameplate | Verdict |
|---|---|---|---|
| **124 K** | **162.30 MW** | **−52 858 kW** | **infeasible** |
| 250 K | 27.04 MW | 82 923 kW | feasible |
| 284 K (nitrate, different fluid) | 8.49 MW | 101 663 kW | feasible |

**Scaling.** Between the two chloride points — same fluid, same loading, same field — the observed
exponent is

```
ln(162.2967 / 27.0399) / ln(250 / 124) = 1.7921 / 0.7012 = 2.56
→  W_pump ∝ ΔT^(−2.56)
```

against the ΔT⁻³ expected if ṁ ∝ 1/ΔT and W ∝ ṁ³ in a fully friction-dominated loop. The
sub-cubic exponent is consistent with the loop not being purely friction-dominated (a static-head
component that scales linearly with ṁ). *(The nitrate point cannot be included in this fit — it is a
different fluid with different ρ and μ.)*

**Design consequence for the optimisation:** decision variables **#5 (T_HTF)** and **#6 (ṁ_HTF)** are
**not independent**. A hard floor on T_hot must be **given** to the optimiser as a constraint, not
left for it to discover, because the infeasible region is not signalled by the solver (§7.7).

### 7.5 Finding 3 — the loading optimum is interior at plant level

| Comparison | Annual energy | W_pump,rec,des |
|---|---|---|
| 0.7 wt% vs bare eutectic | 479.23 vs 466.31 GWh → **+2.77 %** | 27.04 vs 35.31 MW → **−23.4 %** |
| 2.0 wt% vs bare eutectic | 462.95 vs 466.31 GWh → **−0.72 %** | 37.94 vs 35.31 MW → **+7.4 %** |

Nano-enhancement at 0.7 wt% improves **both** the energy objective and the pumping objective; at
2.0 wt% it is worse than the bare salt on **both**. This tracks the measured cp enhancement turning
from **+10.5 %** to **−3.5 %** between those loadings (§4.5) and propagating through the loop mass
flow.

**Why this matters for the thesis argument:** the optimum is **interior**, which is exactly what
makes φ a genuine optimisation variable rather than a quantity to maximise. It also demonstrates
that a property-level enhancement propagates coherently to plant-level performance through the
model chain — an end-to-end consistency check on the whole property → plant pipeline.

**Context to state honestly:** the chloride still trails nitrate by **−9.6 %** on annual energy
(479.23 vs 530.18 GWh). That is expected and not a defeat — the power block in these runs is
deliberately still the **steam Rankine**, which cannot exploit a 700 °C source. Realising the
chloride's advantage is precisely the job of the sCO₂ block, i.e. of Module F.

### 7.6 Finding 4 — a negative result about grid density, correctly interpreted

Two table-robustness cases were run. Dropping from 6 rows to the 3-row minimum across the same span
moved annual energy by **0.001 %**, and a deliberately under-covering grid (500–650 °C against a
450–700 °C operating span) returned numbers **identical to the full-span case**.

**The reason matters more than the result, and prevents a wrong conclusion.** ρ, cp and k are
*exactly linear* in T in the A1 correlation set, so linear interpolation on any grid reproduces them
to machine precision; only μ (exponential) and h (quadratic) can differ at all. **A test that
under-covers the span therefore proves nothing about extrapolation — it is inconclusive by
construction.** The script flags the narrow grid as a table problem regardless of the run
succeeding.

### 7.7 Finding 5 — two silent-failure traps in the tool

Both belong in the methodology chapter as validity screens applied to every run.

1. **A negative nameplate is not an error to ssc.** `system_capacity` is design *net* output and can
   go negative when pumping exceeds gross. Observed at **−52 858 kW** — with no error, no warning, a
   full 8760-hour `gen` array, and a perfectly plausible-looking 288.65 GWh annual figure.
   **Screen every run on `system_capacity > 0`.**
2. **`capacity_factor` is not comparable across cases whose design changes.** Its denominator is the
   per-case nameplate, so CF *rises* while annual energy *falls*. The table in §7.2 shows this
   directly: the 2.0 wt% case has the **highest** CF (73.46 %) and the **lowest** annual energy of
   the three feasible chloride cases. **Compare `annual_energy` and `system_capacity`**, which share
   a fixed basis.

---

## 8. MODULE E — SOLAR FIELD / TES BASELINE

*(Chapter 3.7; Chapter 4.5)*
**Status:** ✅ baseline pinned. GUI cross-check blocked, and not required.

### 8.1 Reference case

**`MSPTSingleOwner`** — NREL's stock molten-salt power tower with Single Owner financing, the
NREL-maintained reference configuration, run on the Daggett CA `psmv3_60_tmy` file at stock defaults.

| Parameter | Value | | Parameter | Value |
|---|---|---|---|---|
| `P_ref` (gross) | 115.0 MWe | | `h_tower` | 194.227 m |
| `solarm` | 2.4 | | `rec_height` / `D_rec` | 20.4598 / 16.922 m |
| `tshours` | 10.0 h | | `N_panels` | 20 |
| `T_htf_hot_des` | 574.0 °C | | tube OD / wall | 40.0 / 1.25 mm |
| `T_htf_cold_des` | 290.0 °C | | `eta_pump` | 0.85 |
| `design_eff` | 0.412 | | `piping_length_mult` | 2.6 |
| `rec_htf` | 17 (60/40 NaNO₃/KNO₃) | | heliostat | 12.2 × 12.2 m, 1.53 mrad, ρ 0.90 |
| `pc_config` | 0 (steam Rankine) | | `u_tank` | 0.4 W/m²·K |

### 8.2 Pinned regression baseline

```
annual_energy         = 593,054,474.50 kWh
capacity_factor       = 66.5926 %
annual_W_cycle_gross  = 661,026,154.83 kWh
```

Any future change to the field/TES layer that moves `annual_energy` must be explainable.

### 8.3 Scope limits, stated plainly

- This case validates **heliostat field + receiver + TES + annual dispatch only**. Its power block
  is steam Rankine; there is no sCO₂ tower case in SAM to validate against.
- The **SAM GUI cross-check is blocked** — no SAM install exists on this machine. It is also **not on
  the critical path**: the GUI and PySAM run the *same* ssc 306, so that comparison tests packaging,
  not physics. This is a defensible reason for the gap, not an excuse.

---

## 9. MODULE F — THE UDPC BRIDGE, AND THE FINDING THAT HAD TO BE RETRACTED

*(Chapter 3.8; Chapter 4.6 — the negative result here is about **method**, not about the tool)*
**Scripts:** `scripts/build_udpc_map.py`, `scripts/udpc_convergence_bisect.py`
**Status:** ✅ **The sweep converges at the full case F design** — `recomp_frac 0.40970`,
η 0.50547, non-empty tables, **2277.9 s**. Design point solves; the transform is proven.

> ⚠️ **This section previously reported that the sweep does not converge, and that report was
> wrong.** It is rewritten below rather than deleted, because *how* a dozen consistent
> measurements produced a confident false conclusion is the most transferable thing in this
> chapter. The superseded diagnosis is preserved in §9.3 for that purpose.

### 9.1 What the bridge has to do

The intended coupling, per the tool's own design, is:

```
Sco2CspUdPcTables ──(ud_ind_od)──▶ TcsmoltenSalt.PowerCycle.pc_config = 1
                                   .UserDefinedPowerCycle.ud_is_sco2_regr = 1
```

`ud_is_sco2_regr` is an sCO₂-aware regression flag — SAM explicitly supports this bridge. The
difficulty, undocumented in either API, is that **the two sides disagree about the table's shape**.

| Side | Shape |
|---|---|
| `Sco2CspUdPcTables` **emits** | **three per-axis tables, 13 columns each** (`T_htf_ind`, `m_dot_htf_ND_ind`, `T_amb_ind`); col 0 = swept variable; cols 1–3 W_gross, 4–6 Q_HTF, 7–9 W_cooling, 10–12 ṁ_water, each triple ordered [low, DESIGN, high] of a *paired* variable |
| `TcsmoltenSalt.ud_ind_od` **wants** | **one combined table, 7 columns**: `[T_htf, ṁ_htf_ND, T_amb, W_gross_ND, Q_HTF_ND, W_cool_ND, ṁ_water_ND]` |

This is **not a version skew to route around**: ssc's own `N_udpc_common::split_ind_tbl()` splits the
combined table into exactly those three. Writing the bridge means writing **the inverse of that
split**.

**The block structure was read off the tower's own installed default `ud_ind_od` (180 × 7) in this
environment** rather than trusted from any write-up:

| block | swept (20 values) | 3 levels of | held at design |
|---|---|---|---|
| 0 | `T_htf` | ṁ — 0.3 / **1.0** / 1.2 | `T_amb` = 43 |
| 1 | ṁ | `T_amb` — 0 / **43** / 55 | `T_htf` = 574 |
| 2 | `T_amb` | `T_htf` — 500 / **574** / 580 | ṁ = 1.0 |

The **level is the outer loop**, the swept value the inner; stacking order `T_htf → ṁ → T_amb`.

### 9.2 What is proven and working

**(a) The design point solves, and it is a genuine recompression cycle.** In 0.1 s, on the
nano-chloride:

```
eta_thermal_calc  0.50547     (case F 0.51289 → −0.742 pp)
recomp_frac       0.40970     (pinned at case F's 0.4097 — held)
T_turb_in         680.000 °C  T_comp_in 32.000 °C
P_comp_out / in   20.0000 / 7.6923 MPa   (PR 2.6000)
eff_HTR / eff_LTR 0.97510 / 0.93098
T_htf_cold_des    533.340 °C
```

The −0.742 pp is **fully accounted for and deliberate**: the validated case sits at T_htf_hot 720 °C
to place the turbine inlet at Dostal's 700 °C, but the chloride correlations are stated valid only
to 700 °C. The map therefore runs T_htf_hot = 700 °C → TIT 680 °C, keeping the fluid inside its
validity. **The cycle architecture and every efficiency, pressure and recuperator specification are
unchanged**; only the hot-end boundary condition moves, and the cost is reported rather than buried.

**(b) The 13-column → 7-column inverse-split transform is proven independently of ssc.** A
`--selftest` mode verifies it on synthetic data — which is exactly why it was built that way, since
the sweep that would otherwise exercise it does not run.

**(c) Two silent traps in the transform were identified and handled.**
- The **cooling column arrives unnormalised** (order 10⁻³ at design, while every other response is
  1.0 there). It must be divided by its own design value; the magnitude is restored on the tower side
  by `ud_f_W_dot_cool_des`. Missing this makes the cooling parasitic wrong by three orders of
  magnitude with nothing flagging it.
- **`ud_ind_od` carries normalised SHAPES only.** The design magnitudes travel separately
  (`design_eff`, `P_ref`, `ud_f_W_dot_cool_des`, `ud_m_dot_water_cool_des`), and if they are not set
  the tower **silently keeps its steam-Rankine defaults** — verified in this environment as
  `design_eff = 0.412`, `P_ref = 115.0 MW`. Everything runs; the sCO₂ block is simply mis-scaled.

**(d) A third trap of the same family, found 2026-08-14 — and it was live in this project's own
bridge.** Setting the design magnitudes is necessary but not sufficient: they must be sourced
correctly. `ud_f_W_dot_cool_des` was computed from the *map's* cooling column
(`100 × 9.971e-4 / 115000`), giving **0.0000 %** — a 115 MW plant with a costless air cooler, no
error raised. The column is neither a power in kW nor a fraction of gross (that reading gives
0.0997 %, still 10× low); the magnitude exists only in ssc's own
`cooler_tot_W_dot_fan = 1150.0 kW`, i.e. **1.0 %**, which matches the `fan_power_frac = 0.01`
supplied as an input and is confirmed by `W_dot_net_less_cooling = 113850 = 115000 − 1150`.

> **Worth a line in Chapter 4, because it is the §10 pattern recurring at the last moment.** The
> bridge reported `roundtrip_rel = 0.000e+00` and "the bridge is CLOSED" while shipping a zero
> cooling parasitic. **Round-trip fidelity tests transport, not correctness** — the table went in
> and came out unchanged, and was scaled wrongly the whole time. It was caught by reading a
> reported magnitude that looked physically impossible, not by any check in the script; a guard
> that refuses to emit a value outside 0.05–10 % is now in `cooling_fraction_pct()`.

### 9.3 What actually happens — and the twelve experiments that pointed the wrong way

**The result, measured 2026-08-14** (`results/udpc_bisect_20260814T194825Z.*`). Five
configurations were run with the sweep on and a 3600 s ceiling. **All five are usable**, and the
knobs that were believed to decide convergence move only the wall time, by ~20 %:

| Configuration | Wall | `recomp_frac` | η | Verdict |
|---|---|---|---|---|
| **`case_F` — everything pinned** | **2277.9 s** | **0.40970** | **0.50547** | **USABLE** |
| `F_loose_frc` — f_rc free | 2152.3 s | 0.41067 | 0.50569 | USABLE |
| `F_loose_dm` — design_method 1 | 2218.6 s | 0.40970 | 0.49999 | USABLE |
| `F_loose_press` — pressures free | 1882.8 s | 0.40970 | 0.50654 | USABLE |
| `F_loose_tol` — rel_tol 3 | 1963.3 s | 0.40970 | 0.50512 | USABLE |

**There is no convergence boundary, and nothing had to be loosened.** The design point alone
solves in 0.1 s, so the sweep costs ~20,000× the design and emits no progress output for 31–38
minutes — which is what made it indistinguishable from a hang.

**One configuration does genuinely fail, and it is the one previously trusted as the control.**
The "loose bundle" (`design_method = 1`, free pressures, free `f_rc`) ran **2026 s** and then
returned a real ssc diagnostic — not a hang:

```
Total recuperator conductance = 218.681 [kW/K per MWe]. Optimized cycle efficiency = 0.502269
exec fail(sco2_csp_system): Can't find a value of total recuperator conductance that
                            achieves the target cycle efficiency. Check design parameters.
```

The reason is a miscategorisation worth carrying: **`design_method = 1` is not a loose setting —
it adds a constraint**, an inverse solve for the recuperator conductance that hits a target
efficiency. Calling it "loose" put the one failing configuration at the origin of the search.

#### Why the earlier conclusion was wrong, and why it looked right

This is the part to write up. The superseded reasoning was:

> Twelve configurations tested. The sweep completes only when the design is loose enough to
> collapse to `recomp_frac = 0`. Therefore a fully determined recompression design is
> over-constrained for UDPC generation in ssc 306.

Every experiment behind it was capped at **5–16 minutes** against a run needing **31–38**. Not one
had ever observed a completion, so not one licensed the word "hangs" — what was measured was
*"did not finish inside my timeout"*, and the two were conflated. The conclusion was nonetheless
persuasive because it had every marker of a sound finding except a valid measurement:

- **Consistency** — twelve independent cells all agreed. They agreed because they shared the
  defect, which is exactly what a systematic error does.
- **A plausible mechanism** — "the off-design solver needs degrees of freedom the validation
  design removes" is physically sensible and explains the data.
- **Corroboration from a known failure mode** — the loose bundle's `recomp_frac = 0` matched
  `CLAUDE.md` §4.3's documented collapse *and* the prior project's recorded 0.113, so the one
  anomalous data point appeared already explained.
- **An asymmetric cost structure that discouraged the disconfirming test** — negatives cost a
  full timeout, so the search was deliberately redesigned to run *cheaper* experiments. Every
  redesign made the runs shorter. The one experiment that would have settled it — let a single
  case run to completion, however long — was never the cheap option and was never run.

**The safeguard now in force** (`CLAUDE.md` §4.15, `MASTER_PLAN.md` §10): a non-convergence may
be recorded only against a **measured** completion time for that class of run, or with an explicit
statement that no completion time is known. It is nearly free and would have caught this on day
one.

<details>
<summary><b>Superseded — the twelve experiments as originally reported (retained for the write-up)</b></summary>

Turning on `is_generate_udpc = 1` fails to complete in 5–16 minutes at either 3³ or 5³ sweep
resolution.

**Round 1 — seven single-variable deviations from case F. Each changed exactly one thing.**

| Variable changed | Result |
|---|---|
| the custom chloride fluid → built-in nitrate (htf = 17) | **still hangs** — not a property-table problem |
| pinned f_rc → free (`is_recomp_ok = 1`) | still hangs |
| pinned pressures → free (`is_P_high_fixed = 0`, `is_PR_fixed = 0`) | still hangs |
| `rel_tol` 3 → 4 | still hangs |
| recuperators by min-approach → code 3 at case F's *own* produced effectivenesses (0.97510 / 0.93098) | still hangs |
| `design_method` 3 → 2 (total UA 2306.6 kW/K) | still hangs |
| `design_method` 3 → 1 (target η 0.50) | still hangs |
| *(also)* narrowed sweep corners to ṁ 0.85–1.05, T_amb 15–40 °C, T_htf 680–710 °C | still hangs — not a corner-feasibility problem |

**What *did* converge, once: the whole loose bundle at once** — `design_method = 1`, free f_rc, free
pressures, stock tolerance — in **93.6 s**. It returned **`recomp_frac = 0.0`**: the cycle collapsed
to simple recuperated. That is the documented ssc failure mode in which the internal optimiser
abandons recompression while still reporting "design optimization was successful," and it is the same
signature as the prior project's recorded 0.113.

> **The conclusion drawn, and it is the honest one:** this is **not one bad setting**. A
> case-F-style **fully determined** design — every recuperator specified, f_rc pinned, both pressure
> levels pinned — appears to be **over-constrained for UDPC generation**. The off-design solver needs
> degrees of freedom that the validation design deliberately removes. *The sweep converges only when
> the cycle is loose enough to stop being the cycle we validated.*

**Round 2 — bisecting from the other direction** (`scripts/udpc_convergence_bisect.py`,
`results/udpc_bisect_20260813T081729Z.{md,csv}`). Rather than continue searching down from case F
(exhausted, ~5 min per negative), this starts from the known-good loose bundle and re-tightens one
knob at a time (~1.5 min per success). The verdict rule is strict and correct for this project's
purpose: a case is **usable** only if it converges **AND** `recomp_frac > 0` **AND** the per-axis
tables are non-empty — because a run that converges at `recomp_frac = 0` is a failure even though
ssc calls it a success.

| Case | Knobs (L = loose, T = tight) | Verdict | Wall time |
|---|---|---|---|
| `loose_all` *(control)* | dm=L f_rc=L press=L tol=L | **FAIL (timeout)** | 360.0 s |
| `pin_frc` *(the critical cell)* | dm=L **f_rc=T** press=L tol=L | FAIL (timeout) | 360.0 s |
| `pin_press` | dm=L f_rc=L **press=T** tol=L | FAIL (timeout) | 360.0 s |
| `pin_dm` | **dm=T** f_rc=L press=L tol=L | FAIL (timeout) | 360.0 s |
| `pin_tol` | dm=L f_rc=L press=L **tol=T** | FAIL (timeout) | 360.0 s |

**No configuration in this set is usable.**

> ⚠ **An unresolved discrepancy that must be stated, not smoothed over.** The `loose_all` control
> **timed out at 360 s in this run**, although the same bundle converged in **93.6 s** in the earlier
> session. The two runs differ in harness (the bisect driver reruns `build()` through its own
> subprocess worker with an η target of 0.50 and 3 points per axis), so the control is **not
> confirmed reproducible**, and until it is, the Round-2 cells cannot be read as clean evidence about
> their individual knobs — the whole run may sit on the wrong side of a machine-load or
> configuration boundary. **The first action for whoever resumes is to re-establish the control**,
> at a longer timeout, before interpreting anything else in that table.

*(That last warning was the right instinct and it is what broke the case open — but the answer it
found was not the expected one. The control does not merely fail to reproduce: it is the single
configuration that genuinely errors, and it took every stage-1 cell down with it.)*

</details>

### 9.4 How to write this up

The bridge is **built and working**, and the interesting content is the retraction:

1. The *inverse-split transform* — the genuinely novel engineering in the bridge, undocumented in
   both APIs — **is implemented and independently verified** by `--selftest`, on synthetic data,
   without needing ssc at all.
2. The *design point* of the integrated cycle **solves on the nano-chloride** at the validated
   architecture, with the one deliberate boundary-condition move quantified at −0.742 pp.
3. The *off-design map generates* at the full case F design — pinned `f_rc`, pinned pressures,
   specified recuperators — in ~38 min, returning `recomp_frac 0.40970` and η 0.50547.
4. **The decision this was thought to force does not exist.** §9.4 previously reserved a modelling
   decision: generate the map at a solver-chosen `f_rc` and measure the gap. No such trade is
   needed, and the measurement is now in hand anyway — with the rest of the design pinned, a free
   `f_rc` **self-selects 0.41067** against case F's 0.40970, a 0.24 % gap worth +0.02 pp in η. The
   pinned and unpinned cycles are the same cycle to within the model's own resolution.
5. **A small independent corroboration of §5.6, worth one sentence and no more.** An optimiser
   free to choose the recompression fraction for this architecture lands at ~0.411, near the
   0.4097 that closing Dostal's published balances requires and well away from his stated 0.39.
   It is *not* independent evidence about Dostal — same ssc solver, different fluid, TIT 680 °C
   not 700 °C — so it corroborates the plausibility of ~0.41 for this topology, nothing stronger.

### 9.5 The integrated annual result — Objective 2's missing number

*(Chapter 4.6 — this is the result the whole model chain was built to produce)*
**Script:** `scripts/run_integrated_annual.py` · **Data:** `results/integrated_annual_20260815T094134Z.{md,csv}`

Morocco/Ouarzazate TMY, nano-chloride at 0.7 wt% through `rec_htf = 50`, the n=3 UDPC map,
`Singleowner` instantiated before `execute()` (§4.13), every case screened on
`system_capacity > 0` (§4.14):

| Case | Power block | Annual energy | Nameplate (net) | Loop ΔT | W_pump,rec,des |
|---|---|---|---|---|---|
| `sco2_n3` | sCO₂ recompression (UDPC) | **440.21 GWh** | **62,612 kW** | 166.7 K | 49.55 MW |
| `steam_same_T` | steam Rankine (control) | 389.39 GWh | 22,945 kW | 166.7 K | 86.73 MW |

**(a) The §7.5 attribution is now tested, not inferred.** §7.5 explained the chloride's −9.6 %
against nitrate by pointing at the steam block, which cannot exploit 700 °C — an inference. With
fluid, loop temperatures and field area (1,348,316 m²) all identical and only `pc_config`
differing, the sCO₂ block delivers **+13.05 %** annual energy.

> **State the caveat in the same breath.** Receiver *design duty* is not held fixed — 546.0 MW
> against 669.9 MW — because `q_rec = P_ref / design_eff × SM`. A more efficient cycle demands
> less heat for the same gross output, which then also cuts its pumping. The +13.05 % therefore
> bundles the conversion gain with its knock-on parasitic saving; it is the honest
> *system-level* answer to "what does the sCO₂ block buy", not an isolated conversion delta.

**(b) The finding that matters more, and it is new: recuperation and pumping pull against each
other.** The recompression cycle's heavy regeneration returns the HTF at **533.3 °C** from a
700 °C source, leaving only **166.7 K** of loop ΔT. The plant is feasible — the nameplate is
positive — but it pays **49.55 MW of receiver pumping, ≈43 % of the 115 MW gross**, netting
62.6 MW. This is §7.4's melting-point constraint arriving from the opposite direction: there the
*cold* end was floored by the freezing point, here the cold end is floored by the *cycle's own
recuperation*, and both squeeze the same ΔT.

**(c) An unplanned cross-validation between two independently built modules.** §7.4's law
(ṁ ∝ q/ΔT, W ∝ ṁ³) applied to its 250 K / 669.9 MW anchor predicts the integrated pumping load
**without being fitted to it**:

| Case | Predicted from §7.4 | Measured here | Δ |
|---|---|---|---|
| `sco2_n3` | 49.4 MW | **49.55 MW** | **0.3 %** |
| `steam_same_T` | 91.3 MW | 86.73 MW | 5 % (consistent with §7.4's sub-cubic exponent) |

A property model, a plant coupling and a power-cycle map — built separately, validated separately
— agree to 0.3 % on a parasitic none of them was tuned against.

**(d) The §7.7 trap, caught live.** `capacity_factor` came back at **193.73 %** for the steam
case. It is not a bug: the denominator is that case's own 22.9 MW nameplate. It is a standing
demonstration of why CF must never be compared across cases whose design changes.

---

## 10. CROSS-CUTTING CONTRIBUTION — THE PySAM/ssc DEFECT CATALOGUE

*(Chapter 3.9 as method-hardening; Chapter 4.7 as a contribution in its own right)*

Fourteen tool-level defects and traps were found by execution, each verified in this environment
rather than transcribed from any prior write-up. Several are **silent** — they produce plausible
wrong numbers rather than errors — which is exactly why cataloguing them is a contribution to anyone
else building on the same toolchain.

| # | Defect / trap | Why it matters |
|---|---|---|
| 4.1 | Several `od_*` inputs are arrays, not scalars | Assigning an int raises a confusing type error; for design-only runs, simply do not set them |
| 4.2 | **Bad input VALUES segfault the interpreter rather than raising** | A malformed `htf_props` table, or a `0.0` left in an *unused* recuperator spec, exits 139 with all unflushed stdout lost. Motivates the subprocess-per-case architecture used throughout |
| 4.3 | **`Sco2CspSystem` silently collapses to a simple cycle** | With `design_method` 1 or 2 the optimiser can return `recomp_frac = 0.0`, NaN out every HTR output, and in one observed case drive the compressor inlet to 1.5 MPa — **subcritical and physically meaningless** — while reporting success. `is_recomp_ok`: 1 = optimiser chooses, 0 = simple only, **negative = pin f_rc at abs(value)** |
| 4.4 | `TcsmoltenSalt.default()` ships without a weather file | Reading the field raises before you set it |
| 4.5 | State points 10–11 are NaN **by design** | Pre-compressor nodes exist only for partial cooling. Never `np.sum()` the raw 12-element arrays |
| 4.6 | Default config names are `MSPTSingleOwner`, not `MSPT` | — |
| 4.7 | `HTR/LTR_design_code` mapping (1 = UA, 2 = min ΔT, 3 = effectiveness) **and a UA unit trap** | `HTR_UA_des_in` is consumed in **W/K** despite documenting kW/K — passing 1×10⁶ yields 1000 kW/K. Effectiveness (code 3) is scale-free and sidesteps this |
| 4.8 | **Returning `model.Outputs` from a function segfaults** | The Outputs group does not keep its parent alive; the model is collected on return and the caller's next read hits freed memory. Exit 139, no traceback, no stdout even unbuffered — and the crash lands at the *caller's* first read, nowhere near the bug |
| 4.9 | **Mass flows are 1000× their documented units** | `m_dot_co2_full` reports 87 268.8 where three independent energy balances give 87.2688 kg/s; powers document MW but are kW. **This bug was live in the project's own smoke test and made every printed Ṡ_gen 3.6× too low.** Now derived from turbine duty with an assert |
| 4.10 | No direct `T_mc_in` / `T_turb_in` input | Both are derived from approach temperatures; pinning `P_high` and PR together fully determines the pressure levels |
| 4.11 | **The UDPC table has two shapes and the two modules disagree** | See §9.1, including the unnormalised cooling column |
| 4.12 | `ud_ind_od` carries shapes only | Omit the design magnitudes and the tower silently keeps steam-Rankine `design_eff = 0.412`, `P_ref = 115 MW` |
| 4.13 | `Singleowner.from_existing()` must precede `execute()` | Otherwise the financial model sees a single `gen` record |
| 4.14 | **A negative nameplate is not an error to ssc** | See §7.7 |

**The pattern worth naming in the thesis:** the dangerous defects are not the ones that crash. They
are 4.3, 4.9, 4.12 and 4.14 — each produces a complete, plausible, *wrong* result with no warning.
Every one of them was caught by a **conservation check**, never by a sanity check, which is the
methodological argument for building balance closures into the model rather than bolting on
assertions afterwards.

---

## 11. THE DECISION VECTOR — STATUS OF ALL TEN VARIABLES

*(Chapter 3.10; feeds Chapter 5)*

| # | Variable | Model handle | Status | Validated range / constraint |
|---|---|---|---|---|
| 1 | SM | `TcsmoltenSalt.solarm` | ✅ exposed, exercised at 2.4 | field held fixed in the HTF matrix — deliberate control |
| 2 | t_TES | `tshours` | ✅ exposed, exercised at 10 h | — |
| 3 | **φ** | property module → `field_fl_props` | ✅ **exposed and exercised at 0.0 / 0.7 / 2.0 wt%** | **hard-capped at 2.0 wt%** by the module; interior optimum demonstrated (§7.5) |
| 4 | **d_p** | — | ❌ **NOT represented** | See the gap note below |
| 5 | **T_HTF** | `T_htf_hot_des` | ✅ exposed, exercised at 574 / 700 °C | **≤ 700 °C** (correlation validity); **floor coupled to #6** |
| 6 | ṁ_HTF | derived from duty and loop ΔT | ✅ implicitly exercised | **T_cold ≥ 450 °C** (melt 401.4 °C + margin); ΔT ≥ ~250 K for feasibility |
| 7 | T_t,in | derived: `T_htf_hot − dT_PHX_approach` | ✅ exposed, validated at 700 °C, run at 680 °C | Dostal tables at 550/650/700 available for further validation |
| 8 | P_H | `P_high_limit` + `is_P_high_fixed` | ✅ exposed, validated at 20 MPa | — |
| 9 | PR | `is_PR_fixed` | ✅ exposed, validated at 2.6 | — |
| 10 | f_RC | `is_recomp_ok` = −f | ✅ exposed, validated at 0.4097 | ⚠ **pinning may be incompatible with UDPC map generation** (§9.3) |

> **The d_p gap, stated honestly.** Nanoparticle diameter is a named decision variable in the
> supervisor's sheet, but the property module's enhancement fits are anchored to Han's series at
> **fixed particle size** and carry no size dependence. The literature basis to add it exists — Wei
> et al. (2024) report cp falling with larger particle size, with 20 nm MgO giving cp +38.2 % — but
> it is not implemented. The defensible position is: **d_p is excluded from the current decision
> vector for want of a size-resolved property anchor in this exact system, and that exclusion is
> declared rather than silently absorbed.**

---

## 12. OBJECTIVE-BY-OBJECTIVE ATTAINMENT

*(Chapter 5.1)*

| Obj | Requirement | Attained | Evidence | Gap |
|---|---|---|---|---|
| **1** | T- and φ-dependent thermophysical models of the nano-HTF | **✅ Substantially complete** | ρ, cp, k, μ with uncertainty bands, anchored to Han 2022 in the exact base salt; self-validating; two independent consumers | μ is analogue-grounded, not measured (declared); no d_p dependence |
| **2** | Integrated CSP–nano-HTF–TES–sCO₂ model + energy/exergy/hydraulic/economic assessment | **✅ Attained at the model level, with an annual result** | Power block validated node-wise; exergy method verified; HTF↔plant coupling verified; field/TES baseline pinned; hydraulic assessment delivered as the ΔT–pumping law **and independently cross-validated to 0.3 % by the integrated run**; UDPC map generates at the validated design; **integrated annual result 440.21 GWh, nameplate 62.6 MW (§9.5)** | Map is coarse (3 pts/axis) at ~35 min per build; exergy layer still cycle-only (no receiver/TES/tank terms); economic assessment limited to what `Singleowner` returns; no LCOE study |
| **3** | Multi-objective optimisation over the decision vector | **❌ Not attained** | Method selected and justified (Morris → Sobol → NSGA-II); all objective functionals are computable (η, Ė_D, W_pump, ρ_TES) | **No longer blocked by a broken model layer** — gated by map build cost, which requires partitioning the decision vector into cycle-design variables (rebuild) and plant variables (reuse). No screening run |
| **4** | Pareto envelope, nano vs conventional benefit | **◐ Partially pre-empted** | A six-point comparison already shows the interior loading optimum and quantifies nano vs bare vs nitrate (§7.5) | Not a Pareto envelope; single-point comparisons only. *Post-defence scope* |
| **5** | Climate robustness (MENA + Southern Africa) | **◐ Infrastructure only** | Morocco/Ouarzazate TMY in hand and **already used for every HTF-bridge run** | Southern Africa (Upington) TMY missing and needs re-downloading. *Post-defence scope* |

**The honest one-sentence summary for the viva:** *Objective 1 is met; Objective 2 is met at the
model-construction level, with all five layers built and joined, though no integrated annual result
is yet reported; Objective 3 is not attained, and the reason is the computational cost of the
performance-map build plus a session lost to a measurement error that this document now reports
rather than conceals.*

---

## 13. LIMITATIONS AND THREATS TO VALIDITY

*(Chapter 5.2 — write these before a reviewer does)*

**Property model**

1. **Viscosity is analogue-grounded, not measured.** No experimental μ exists for CuO in any
   chloride salt. The band comes from chloride-family MD on *different* particle/salt pairs
   (§4.7). Mitigation: framed as field convention with published precedent; next step specified.
2. **Three loading points cannot resolve a curve shape.** The committed piecewise-linear cp fit
   places its maximum at a measured point by construction; the cubic's ~1.0 wt% peak is a model
   artifact. The true optimum may lie anywhere in 0.2–2.0 wt%.
3. **Shear-thinning is unmodelled.** A single μ does not strictly exist for these fluids; the value
   is an apparent viscosity at pump/receiver shear.
4. **Bulk CuO conductivity (33 W/m·K) is a literature range, not a sourced value.** Impact is
   confined to a lower band edge.
5. **A disclosed density-convention divergence** from the anchor paper propagates ~0.4–3.8 % into
   Han's derived k; absorbed into the band (§4.8).
6. **No d_p dependence** (§11).
7. **Enthalpy datum (melting point) is not cross-checked against SAM's internal convention.**

**Power block**

8. **Single-author validation source.** All node-level validation is against Dostal (2004). The
   *turbine-inlet-temperature* half of this objection is answerable at zero cost — his 550 °C and
   650 °C tables are already transcribed — but the *independent-source* half is not answerable from
   the current library. Dyreby is **circular** (SAM's block is built on his method); Battisti
   anchors the exergy ranking but not state points. Candidate independent anchors are identified
   (Padilla 2015, Moisseytsev & Sienicki 2009, Sarkar 2009) and deliberately not acquired.
9. **f = 0.4097 is strong evidence, not proof** (§5.6 residual caveat).
10. **Validated at one design point.** The optimiser sweeps T_t,in and f_RC; the model is validated at
    a single point in that space.

**Plant coupling**

11. **The HTF comparison runs on a steam-Rankine block**, so it cannot show the chloride's true
    advantage — by construction, not oversight.
12. **The grid-density robustness test is inconclusive by construction** (§7.6).
13. **The A1 correlations are used at their validity ceiling** (700 °C); extrapolation to 800 °C is
    author-endorsed but not exercised.

**Integrated model**

14. ~~**The UDPC off-design map does not converge**~~ — **withdrawn 2026-08-14; it converges in
    38 min at the full case F design.** What remains true is narrower and should be stated as
    such: the map is generated at **3 points per axis** against SAM's own default of 20, so it is
    a coarse performance surface, and at ~35 min per build the *resolution* is what is
    cost-limited — not the convergence.
15. ~~**The bisection control did not reproduce**~~ — **resolved, and worse than "did not
    reproduce": the control configuration is the one setting that genuinely fails.** With
    `design_method = 1`, free pressures and a free `f_rc`, ssc runs 2026 s and then errors —
    *"Can't find a value of total recuperator conductance that achieves the target cycle
    efficiency."* The 93.6 s convergence recorded on 2026-08-13 has never been reproduced and
    should not be cited. Every stage-1 bisection cell inherited this configuration, so those five
    results are **void**, not merely uninterpreted.
16. **A methodological failure inside this project is worth reporting in Chapter 5.** The
    over-constraint diagnosis was built from twelve non-observations, each of which was a timeout
    rather than a result. It was internally consistent, had a plausible mechanism, matched a
    documented ssc failure mode (§4.3's collapse), and was wrong. The safeguard adopted — quote a
    measured completion time or declare that none exists — is cheap and would have caught it on
    day one.

**Scope**

17. **No SAM GUI cross-check** — blocked by environment; tests packaging, not physics.
18. **Economic assessment is minimal.** No LCOE optimisation was run; `min LCOE` is a named
    objective and remains unaddressed beyond what `Singleowner` returns by default.
19. **Receiver/TES/tank exergy terms are not yet in the exergy layer** — cycle-only (§6.6).

---

## 14. ANTICIPATED DEFENCE QUESTIONS, WITH GROUNDED ANSWERS

**Q. You didn't finish the optimisation. What did you actually deliver?**
A validated model and a set of findings. Specifically: a power block reproducing a published
state-point table to 0.070 % at every node; a property model self-validating against measured
anchors; a verified exergy method closing to 1.5×10⁻⁴; a quantified physical constraint coupling two
decision variables that would have corrupted the optimisation had it been run naively; and a
working sCO₂ ⇄ annual-plant bridge whose novel component, the undocumented table transform, is
verified independently of the solver. The screening was not run because each performance-map build
costs ~35 minutes and a session was lost to a measurement error I found and corrected — not because
any model layer is broken.

**Q. You reported that the map would not converge, then withdrew it. Why should I trust the rest?**
Because the same discipline that produced the rest is what caught it. The error was specific and
diagnosable: twelve experiments were each capped at 5–16 minutes against a run that needs 31–38, so
"did not finish inside my timeout" was recorded as "does not converge" — and a plausible mechanism
was then built to explain a dozen non-observations. It was caught by re-running the control the
document itself flagged as unverified, which is exactly what that flag was for. The distinction
that matters is that the *validation* results rest on positive measurements against published
values with conservation closures, while the retracted claim rested on absences. Absences are what
I now require a measured completion time to interpret, and that rule is written into the operating
manual (`CLAUDE.md` §4.15).

**Q. Why validate against a 2004 report rather than something recent?**
Because the requirement was per-node *h* and *s*, and almost nobody publishes them. Dostal publishes
full state tables for three designs. Recent candidates (Turchi 2013, Chacartegui 2011, Mammadov
2026) give configuration-level efficiency only, which would validate nothing the downstream exergy
and MOO work depends on.

**Q. Isn't matching one paper at one point a coincidence?**
Two answers. First, it is not one number — it is eight independent nodes in four quantities plus two
conservation-closed junction nodes, and the agreement is 0.070 %; a coincidence does not land ten
constraints simultaneously. Second, the objection's honest half is real and is answerable from data
already transcribed: Dostal's 550 °C and 650 °C tables give a 150 °C span at zero acquisition cost,
and that run is a **falsifiable** test — the method predicts the 650 °C case reproduces at Dostal's
*stated* f while the 700 °C case does not.

**Q. Your efficiency matched at the start. Why did you change the baseline?**
Because it matched for the wrong reasons. The original case agreed on η to 0.26 pp via two
cancelling errors while its HTR moved 8 % less heat than published — and the HTR is the cycle's
largest exergy destroyer at 41 % of total. An agreement built on cancellation does not survive
moving off the design point, which is exactly what an optimiser does. The replacement uses three
settings all read from the source's own tables, with no free parameter tuned to hit 51.27 %.

**Q. You claim a published paper's stated recompression fraction is wrong. Defend that.**
It is a consistency finding, stated as such. Imposing the HTR, LTR and mixer balances on his own
published state points closes only at f = 0.4097, not the stated 0.39. The same procedure applied to
his Advanced 650 °C design as a **control** returns 0.4049 against its stated 0.41 — so the method's
resolution is ~0.005 and the High-Performance discrepancy is 4× that. A different recompressor
efficiency does not rescue it: 0.39 would require η_rc = 0.752, against his stated 0.89 and 0.948,
whereas the control reconciles at a perfectly ordinary 0.932. At f = 0.4097 his own numbers give
near-isenthalpic mixing, which is what an optimised junction looks like. The residual possibility is
a topology difference the three-balance reduction misses.

**Q. Why chloride at all, when it trails nitrate by 9.6 % in your own results?**
Because that comparison runs a steam-Rankine block that cannot use 700 °C. The chloride's entire
rationale is enabling the hot end an sCO₂ recompression cycle wants, and the comparison that would
show it is precisely the integrated run that is blocked. What the result *does* establish is the
cost side of that trade honestly, including the infeasible corner.

**Q. Is the negative-nameplate case a modelling error?**
No — it is a real, correctly-computed infeasible design that the tool does not flag. The chloride at
574 °C hot with a 450 °C cold floor has only 124 K of loop ΔT, and at fixed duty that drives the
receiver pump to 162 MW against ~100 MW of gross output. ssc returns a full 8760-hour generation
array and a plausible 288 GWh with no warning. Catching it required an explicit screen on
`system_capacity > 0`, which is now applied to every run.

**Q. Your viscosity is simulated, not measured. Doesn't that undermine the pumping objective?**
It is the weakest input and is declared as such, with a band rather than a point value. The
mitigating fact is that this is field convention, not a local shortcut: no experimental viscosity
exists for *any* CuO-loaded chloride salt, and the nanoparticle-in-chloride viscosities that exist
in the literature are themselves MD-derived. The band's edges are grounded in same-chemistry
chloride MD, which is a stronger basis than the nitrate cross-chemistry data used in an earlier
revision. The stated next step is dedicated MD on CuO/A1, validated first against Han's measured cp
and k.

**Q. Why should I believe the model isn't just fitted to reproduce what you wanted?**
Three independent reasons. Every case-F setting is read from the source's tables rather than tuned —
and the derivation self-checks, since the PHX pressure drop derived from node pressures comes out at
exactly the 130.00 kPa stated elsewhere in the same paper. The exergy balance closes to 1.5×10⁻⁴
using every enthalpy, entropy, mass flow and work term at once, which no fitting exercise would
survive. And the model *predicted* near-isenthalpic mixing at the junction before producing it.

**Q. What is the single most important thing you learned?**
That agreement on a bulk number is not validation. The efficiency matched to a quarter of a
percentage point while the internal state was wrong by 5 %, and it took node-level comparison,
conservation closure at the junction and a second-law check on the mixer to find it. Every
significant defect found in this project — the 1000× mass flow, the collapsed recompression, the
mis-scaled cooling column, the negative nameplate — produced a plausible number, and every one was
caught by a conservation check rather than by inspection.

---

## 15. ARTIFACT INDEX

### 15.1 Scripts (all committed, all with purpose/inputs/run-instructions headers)

| Script | Purpose | Key outputs |
|---|---|---|
| `scripts/nanofluid_properties.py` | **Objective 1 property model.** φ, T → {ρ, cp, k, μ} with bands; SAM 7-column export; self-validation | `results/sam_htf_table_0p7wt.csv` |
| `scripts/validate_dostal.py` | The validated sCO₂ cycle. Case F baseline + legacy case A + effectiveness sweep; mixer, second-law, power and energy balances; CoolProp cross-check | `dostal_validation_*.md`, `dostal_state_points_*.csv`, `dostal_recup_sweep_*.csv` |
| `scripts/compare_dostal_nodes.py` | Node-by-node error table vs Table 10.4 | `dostal_node_errors_*.{md,csv}` |
| `scripts/check_untabulated_nodes.py` | Conservation validation of `LTR_HP_OUT` and `RC_OUT`; internal/absolute variants | `dostal_junction_checks_*.{md,csv}` |
| `scripts/check_dostal_table_consistency.py` | **No model run** — pure arithmetic on Dostal's published values; the f_implied analysis and η_rc robustness | `dostal_table_consistency_*.{md,csv}` |
| `scripts/dostal_dp_recup_matrix.py` | The A–F case matrix; asserts F still wins so adoption is a regression test | `dostal_dp_recup_matrix_*.{md,csv}` |
| `scripts/exergy_layer_check.py` | Per-node exergy, per-component Ė_D, five verification checks, dual-T₀ reporting | `exergy_layer_check_*.{md,csv}` |
| `scripts/htf_sam_bridge.py` | Salt/SAM reconciliation; six-case matrix; subprocess-isolated | `htf_sam_bridge_*.{md,csv}` |
| `scripts/build_udpc_map.py` | The UDPC bridge: design point, 13→7 inverse-split transform, `--selftest`, tower load with guarded cooling scale | `udpc_design_only_*.md`, `udpc_map_*.md`, `maps/sco2_udpc_phi*_n*_{tower7,peraxis}.csv` |
| `scripts/udpc_convergence_bisect.py` | Convergence lattice. **Stage 1/2 walk from the loose bundle — that origin is void; stage 3 walks from case F** and is the direction to use | `udpc_bisect_*.{md,csv}` |
| `scripts/check_udpc_cooling_scale.py` | Units check for the cooling response; establishes `ud_f_W_dot_cool_des` from `cooler_tot_W_dot_fan` in 0.1 s without the ~35-min sweep | `udpc_cooling_scale_*.md` |
| `scripts/smoke_test.py` | Environment-health baseline at placeholder conditions (720 °C / 25 MPa / f 0.30) | terminal |

### 15.2 Knowledge files

| File | Role |
|---|---|
| `MASTER_PLAN.md` | Single source of truth: objectives, critical path, decision variables, deferred backlog |
| `CLAUDE.md` | Operating manual: exact versions, run commands, **the 14-item defect catalogue**, HTF fluid codes, pinned sanity baselines |
| `VALIDATION.md` | The gate file: reference cases, transcribed Dostal tables (all three designs), node map, every error table, the exergy tables |
| `SOURCES.md` | 50 sources with DOI, discovery tool, and extracted numbers |
| `PROPERTIES.md` | Property provenance map and the viscosity defence |
| `DECISIONS.md` | D1–D4 with question, gating finding, resolution, fallback |
| `PROGRESS_LOG.md` | Dated, append-only session log (~40 kB) |
| `reference/prior_project/README.md` | Why the prior project's files cannot be used directly, and what was harvested from them |

### 15.3 Result artifacts

27 timestamped files in `results/`, each stamped with script, UTC time and git commit. The
load-bearing ones for the thesis:

- `dostal_validation_20260813T023249Z.md` — the full case F + case A run
- `dostal_state_points_20260813T023249Z.csv` — both cases' complete state tables
- `dostal_node_errors_20260813T015132Z.{md,csv}` — the error table
- `dostal_junction_checks_20260813T015134Z.{md,csv}` — conservation checks
- `dostal_table_consistency_20260813T014726Z.{md,csv}` — the f = 0.4097 finding
- `dostal_dp_recup_matrix_20260813T015147Z.{md,csv}` — the A–F case matrix
- `exergy_layer_check_20260813T023227Z.{md,csv}` — exergy layer
- `htf_sam_bridge_20260813T025745Z.{md,csv}` — the six-case HTF matrix
- `sam_htf_table_0p7wt.csv` — the exported property table
- `udpc_design_only_20260813T064746Z.md` — the integrated design point
- ~~`udpc_bisect_20260813T081729Z.{md,csv}`~~ — the Round-2 search. **Retained but VOID**: every
  cell sits on the failing loose-bundle origin (§9.3). Do not cite it as knob evidence.
- **`udpc_bisect_20260814T194825Z.{md,csv}`** — **case F + sweep, USABLE in 2277.9 s.** The run
  that refutes the non-convergence finding
- `udpc_bisect_20260814T195349Z.{md,csv}` — stage 3, all four single loosenings, design-only
- `udpc_bisect_20260814T1954*.{md,csv}` — stage 3 with the sweep on; all four usable
- `udpc_cooling_scale_20260815T090703Z.md` — the cooling-units check (`cooler_tot_W_dot_fan`)
- `udpc_map_*.md` + `maps/sco2_udpc_phi0p0070_n{3,5}_*.csv` — the generated maps and tower bridge

---

## 16. SUGGESTED FIGURES AND TABLES FOR CHAPTER 4

| # | Item | Type | Source data |
|---|---|---|---|
| 1 | Cycle topology with node numbering and the Dostal→model map | schematic | §5.2 |
| 2 | Case F T–s diagram with Dostal's published points overlaid | plot | `dostal_state_points_*.csv` |
| 3 | **Node-by-node error bars in h and s, case A vs case F** | grouped bar | §5.4 + §5.6 — shows 5.4 % → 0.07 % |
| 4 | The A–F case matrix as η deviation and RMS h error | dual-axis bar | §5.6 |
| 5 | f_implied vs assumed η_rc, both designs, with stated values marked | line | §5.6 robustness table |
| 6 | Recuperator effectiveness sweep: η and UA_tot vs ε | dual-axis line | §5.8 |
| 7 | **Component exergy-destruction waterfall / Pareto bar** | bar | §6.3 |
| 8 | Per-node exergy profile along the cycle path | line | §6.2 |
| 9 | cp and k enhancement vs loading: Han points, linear fit, cubic sensitivity, Maxwell floor | scatter + lines | §4.5, §4.6 |
| 10 | Property surfaces ρ, cp, k, μ vs T with uncertainty bands, 0 / 0.7 / 2.0 wt% | 4-panel | §4.9 |
| 11 | **W_pump vs loop ΔT with the fitted exponent and the infeasibility boundary** | log-log | §7.4 |
| 12 | Annual energy and pump power vs loading — the interior optimum | dual bar | §7.5 |
| 13 | The UDPC table-shape reconciliation (13-col per-axis → 7-col combined) | schematic | §9.1 |
| 14 | Convergence experiment matrix as a status grid | table/heat | §9.3 |

---

## 17. FUTURE WORK AND THE EXACT RESTART PATH

*(Chapter 5.3 — and the handover note for whoever continues)*

**Immediate, in order:**

1. ~~Re-establish the bisection control~~ · ~~Resolve the UDPC convergence question~~ — **both done
   2026-08-14.** The control is a genuine failure (§9.3), the sweep converges at case F, and the
   modelling decision they were expected to force is not needed.
2. **Confront the map build cost, because it now sets the shape of the whole optimisation.** A map
   is **~35 min at 3 points per axis**, and SAM's own default surface is 20 points per axis. Two
   consequences that must be settled *before* screening, not during it:
   - **Resolution.** Establish what a 3-point surface costs in annual-energy accuracy against a
     denser one. Run 5 points per axis once and compare the annual result through the tower; if
     the difference is small, 3 is defensible and cheap, and that comparison is itself a
     reportable result.
   - **Which variables actually need a rebuild.** SM and t_TES (#1, #2) do not touch the power
     block — they need only a tower run (~20–40 s) against an existing map. The cycle variables
     (φ, T_HTF, T_t,in, P_H, PR, f_RC) do. **Partition the decision vector on this line and cache
     maps per cycle-design**, or a naive Morris design at (10+1)×r evaluations implies tens of
     hours of map generation alone.
3. **Wire the decision vector** — expose all ten variables with the validated ranges of §11,
   including the hard constraints (φ ≤ 2.0 wt%, T_cold ≥ 450 °C, T_hot ≤ 700 °C,
   `system_capacity > 0`).
4. **Run the Morris screening** — the guaranteed deliverable, now unblocked. Budget it against
   step 2's partition rather than against a flat per-evaluation cost.
5. **Extend the exergy layer to the integrated model**, adding receiver, TES and tank Ė_D terms.
6. **NSGA-II** over the pruned decision vector (stretch).

**Deferred validation hardening** — defensive depth for the viva, not modelling risk, with the
restart trigger *"after Morris screening is delivered"*:

1. **Dostal 550 °C and 650 °C node tables** — cheapest and highest value; no new literature, scripts
   already exist, covers a 150 °C span of T_t,in, and **falsifiably tests the f = 0.4097 finding**.
2. **Battisti 2023 exergy cross-check** — already satisfied for the cycle; formalise once the
   integrated exergy layer exists.
3. **An independent node-level anchor** (Padilla 2015 → Moisseytsev 2009 → Sarkar 2009). Highest
   cost, lowest marginal return; only worth acquiring if the viva presses on single-source
   dependence.
4. **SAM GUI cross-check** — lowest priority; tests packaging, not physics.

**Property-model extensions:** dedicated MD (Green–Kubo or NEMD) on CuO/A1 for viscosity, validated
first against Han's measured cp and k; a size-resolved enhancement anchor to bring d_p into the
decision vector; denser cp loadings (≥ 4) to justify committing to a smooth fit.

**Scope completion:** LCOE assessment to address `min LCOE`; the Southern Africa (Upington) TMY
re-download for the Objective-5 climate-robustness study.

---

*End of synthesis. Every quantitative claim above is traceable to a committed script and a
timestamped artifact under `results/`; where a claim rests on inference rather than execution — the
f = 0.4097 reading, the ΔT exponent fit, the UDPC over-constraint diagnosis, the unreproduced
bisection control — it is labelled as such in the text.*
