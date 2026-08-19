# Nano-HTF thermophysical property models — Objective 1 evidence

| | |
|---|---|
| script | `scripts/report_htf_properties.py` |
| module under report | `scripts/nanofluid_properties.py` |
| generated (UTC) | 20260819T111927Z |
| git commit | `ae87e84-dirty` |
| system | CuO in NaCl–KCl–MgCl₂ ternary chloride eutectic (B0) |
| validity | 450–700 °C stated; ≤ 2.0 wt% (fits not extrapolated beyond Han) |
| melting point | 401.4 °C — the cold-tank floor constraint |

## 1. Provenance per correlation

Objective 1 requires documented provenance for each correlation, so this table is a deliverable rather than a working note.

| Property | Symbol | Unit | Functional form | Primary anchor | Status |
|---|---|---|---|---|---|
| Density | rho | kg/m3 | linear in T; volume-fraction mixing rule | B0 set Table 9 (Wang et al., ASME J. Sol. Energy Eng. 143(4):041005, 2021) + CuO rho back-solved from Han/B1 Table 2 | anchored; deliberate volume-fraction divergence from Han disclosed |
| Specific heat | cp | J/(kg K) | linear in T; piecewise-linear in phi | Han et al. 2022, Sol. Energy Mater. Sol. Cells 234:111432 (liquid region, 450-550 C) | anchored at 3 measured loadings; NON-MONOTONIC, peak at 0.7 wt% of those tested |
| Thermal conductivity | k | W/(m K) | linear in T; saturating in phi | Han et al. 2022 endpoints (+15.85% at 0.2, +39.55% at 2.0 wt%); 0.7 wt% point derived from the paper's own alpha, rho and cp via its Eq. (1) | anchored; Maxwell floor used as the lower band edge only |
| Thermal diffusivity | alpha | m2/s | DERIVED: alpha = k/(rho*cp) | inherits provenance from k, rho and cp; cross-checked against Han et al. 2022 Sec. 3.4 measured diffusivity ratios (+10.95% / +18.98% / +37.23%) | derived, not independently correlated -- see the round-trip below |
| Dynamic viscosity | mu | Pa s | exponential in T; linear in phi | MD-filled. Base-salt anchors: Jiang 2024, Xu 2022/2023, De Stefanis 2024, Lu 2021. Loading dependence from chloride-FAMILY MD analogues (Tian 2024 SiO2/LiCl-KCl; Al2O3/NaCl-KCl) | WEAKEST INPUT -- no measured mu exists for CuO in any chloride salt; declared, banded |

> **The viscosity gap, stated rather than buried.** No published viscosity measurement or simulation exists for CuO in the B0 (NaCl-KCl-MgCl2) ternary specifically. The band above is grounded in chloride-FAMILY MD (different salt/particle pairs), which is a stronger analogue than the nitrate cross-chemistry data used in an earlier revision of this module, but it remains an analogue, not a measurement of this system. If reviewers push on this gap, the next step is dedicated MD (Green-Kubo or NEMD) on CuO/B0 specifically, validated first against Han/B1's measured cp and k so the force field is trusted before extending it to predict viscosity.

> **Particle size, stated rather than buried.** Particle size d_p is modelled as size-INVARIANT in the nominal over 5-60 nm, with a +/-6.1% size-transfer uncertainty on the enhancement (DECISIONS.md D6). The band edge comes from Tiznobaik & Shin 2013 (B6), the only molten-salt study to vary nanoparticle diameter directly: 5/10/30/60 nm SiO2 at 1 wt% in a binary carbonate eutectic gave cp enhancements of 24/26/23/26% -- no trend over a 12x size range. Han/B1 does not report the diameter its own cp/k series was measured at, and the paper is paywalled with no open copy, so an anchored size CORRECTION cannot be normalised even in principle; a declared invariance needs no anchor, which is why the two facts resolve each other. Countervailing evidence: B5 reports cp falling with larger particle size for MgO in a different ternary chloride -- direction only, no transferable magnitude. The declared range is a CONSTRAINT OF THE STUDY: a d_p sweep must not exceed it, exactly as loading must not exceed 2.0 wt%.

## 2. The five properties over the validity window

Nominal values; band edges are in the CSV. α is derived as k/(ρ·cp).

### 0.0 wt% CuO

| T (°C) | ρ (kg/m³) | cp (J/kg·K) | k (W/m·K) | α (×10⁻⁷ m²/s) | μ (mPa·s) |
|---|---|---|---|---|---|
| 450 | 1705.2 | 1076.4 | 0.4652 | 2.5345 | 3.734 |
| 500 | 1677.1 | 1051.4 | 0.4522 | 2.5646 | 3.353 |
| 550 | 1648.9 | 1026.4 | 0.4392 | 2.5951 | 3.051 |
| 600 | 1620.7 | 1001.4 | 0.4262 | 2.6261 | 2.805 |
| 650 | 1592.5 | 976.4 | 0.4132 | 2.6574 | 2.603 |
| 700 | 1564.4 | 951.4 | 0.4002 | 2.6890 | 2.435 |

### 0.2 wt% CuO

| T (°C) | ρ (kg/m³) | cp (J/kg·K) | k (W/m·K) | α (×10⁻⁷ m²/s) | μ (mPa·s) |
|---|---|---|---|---|---|
| 450 | 1707.7 | 1118.7 | 0.5407 | 2.8302 | 3.756 |
| 500 | 1679.5 | 1092.7 | 0.5256 | 2.8639 | 3.373 |
| 550 | 1651.3 | 1066.7 | 0.5105 | 2.8979 | 3.068 |
| 600 | 1623.1 | 1040.7 | 0.4954 | 2.9325 | 2.822 |
| 650 | 1594.9 | 1014.8 | 0.4803 | 2.9674 | 2.619 |
| 700 | 1566.7 | 988.8 | 0.4651 | 3.0026 | 2.449 |

### 0.7 wt% CuO

| T (°C) | ρ (kg/m³) | cp (J/kg·K) | k (W/m·K) | α (×10⁻⁷ m²/s) | μ (mPa·s) |
|---|---|---|---|---|---|
| 450 | 1714.0 | 1189.5 | 0.6211 | 3.0464 | 3.810 |
| 500 | 1685.7 | 1161.9 | 0.6038 | 3.0825 | 3.421 |
| 550 | 1657.5 | 1134.3 | 0.5864 | 3.1192 | 3.112 |
| 600 | 1629.2 | 1106.6 | 0.5690 | 3.1562 | 2.862 |
| 650 | 1600.9 | 1079.0 | 0.5517 | 3.1937 | 2.656 |
| 700 | 1572.6 | 1051.4 | 0.5343 | 3.2316 | 2.484 |

### 1.0 wt% CuO

| T (°C) | ρ (kg/m³) | cp (J/kg·K) | k (W/m·K) | α (×10⁻⁷ m²/s) | μ (mPa·s) |
|---|---|---|---|---|---|
| 450 | 1717.8 | 1154.6 | 0.6374 | 3.2136 | 3.843 |
| 500 | 1689.5 | 1127.8 | 0.6196 | 3.2517 | 3.450 |
| 550 | 1661.2 | 1101.0 | 0.6018 | 3.2903 | 3.139 |
| 600 | 1632.9 | 1074.2 | 0.5840 | 3.3294 | 2.887 |
| 650 | 1604.5 | 1047.4 | 0.5662 | 3.3689 | 2.679 |
| 700 | 1576.2 | 1020.5 | 0.5483 | 3.4088 | 2.505 |

### 2.0 wt% CuO

| T (°C) | ρ (kg/m³) | cp (J/kg·K) | k (W/m·K) | α (×10⁻⁷ m²/s) | μ (mPa·s) |
|---|---|---|---|---|---|
| 450 | 1730.5 | 1038.4 | 0.6501 | 3.6180 | 3.951 |
| 500 | 1702.1 | 1014.3 | 0.6320 | 3.6607 | 3.548 |
| 550 | 1673.6 | 990.1 | 0.6138 | 3.7040 | 3.227 |
| 600 | 1645.2 | 966.0 | 0.5956 | 3.7478 | 2.968 |
| 650 | 1616.7 | 941.9 | 0.5775 | 3.7921 | 2.754 |
| 700 | 1588.3 | 917.8 | 0.5593 | 3.8368 | 2.576 |

## 3. Thermal-diffusivity round-trip against Han et al. 2022

α is **derived**, not fitted, so the meaningful test is whether k/(ρ·cp) returns the diffusivity that k was itself back-derived from. Evaluated at 500 °C, Han's own measurement temperature.

| φ (wt%) | α enhancement, derived | α enhancement, Han measured | offset | expected? |
|---|---|---|---|---|
| 0.2 | +11.67 % | +10.95 % | +0.65 % | yes |
| 0.7 | +20.20 % | +18.98 % | +1.02 % | yes |
| 2.0 | +42.74 % | +37.23 % | +4.01 % | yes |

**Interpretation.** The offset is expected to be positive and to grow with loading: this module uses the *volume* fraction for density where Han's tabulated densities used the *mass* fraction, a disclosed divergence worth roughly +0.4 % at 0.2 wt% rising to +3.8 % at 2.0 wt%. The residual above that at 2.0 wt% is the saturating k fit returning +39.75 % against Han's measured +39.55 %, worth a further +0.14 %. Nothing in the column is unaccounted for.

**Module self-validation (cp and k fits + this round-trip): PASSED**

## 4. Particle size — the declared-invariance position (D6)

`DECISIONS.md` **D6** (2026-08-19) represents particle size as a *declared size-invariant nominal over an evidenced band*, with a named size-transfer uncertainty. Objective 3 sweeps d_p, so a reader will meet a flat d_p response surface and should be able to check here that the flatness is a transcribed measurement and not an unrepresented variable. The table below is that check: nominals identical across the band, bands wider than at the unasserted reference.

| d_p (nm) | cp nominal (J/kg·K) | cp band width | k nominal (W/m·K) | k band width | α nominal (10⁻⁷ m²/s) |
|---|---|---|---|---|---|
| *unasserted* | 1161.9 | 189.6 | 0.6038 | 0.2049 | 3.0825 |
| 5 | 1161.9 | 190.4 | 0.6038 | 0.2065 | 3.0825 |
| 10 | 1161.9 | 190.4 | 0.6038 | 0.2065 | 3.0825 |
| 30 | 1161.9 | 190.4 | 0.6038 | 0.2065 | 3.0825 |
| 60 | 1161.9 | 190.4 | 0.6038 | 0.2065 | 3.0825 |

Evaluated at 500 °C and 0.7 wt%. The **nominal columns are constant by decision, not by accident**: verified identical to <1e-12 across the band. The *unasserted* row is the module's pre-D6 behaviour — naming no diameter means "Han's fluid at Han's own diameter", which claims no transfer and so carries no transfer penalty.

**The honest caveat on magnitude.** The size term (±6.1 %, from Tiznobaik & Shin's own measured scatter) is combined in quadrature with an enhancement-transfer uncertainty of ±50 % on cp and ±35 % on k, so it widens the cp band by only ~0.4 %. Particle size is therefore **not** a material contributor to the uncertainty envelope — the point of D6 is that d_p is now a *validated, range-guarded, separately-attributable* input whose flat nominal is citable, not that the band moved.

**Out-of-band behaviour.** A diameter outside 5–60 nm raises `ValueError` rather than extrapolating, mirroring the ≤ 2.0 wt% loading guard. The declared sweep range is a constraint of the study; a sweep that exceeds it would publish a size-invariance claim over diameters nobody has measured.

---

Generated by `scripts/report_htf_properties.py` at commit `ae87e84-dirty`.
