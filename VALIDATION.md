# VALIDATION.md

> **GATE FILE.** Per `MASTER_PLAN.md` §2, nothing downstream (screening, MOO) is defensible until
> the validations here pass. Two *decoupled* validations — power block and solar field/TES —
> documented separately with their own % error tables.

**Last updated:** 2026-08-12 — Session C (research lane). Power-block validation target RESOLVED:
node-level state tables extracted from Dostal 2004 (Tables 10.1–10.8, 13.1, 13.2). Solar-field/TES
baseline executed (Session B). Error tables await the Code-lane rebuild (§2.5 prompts).

---

## 1. SOLAR FIELD / TES VALIDATION — SAM reference case

### 1.1 The reference case available in this install

**`MSPTSingleOwner`** — NREL's stock molten-salt power tower, Single Owner financing. This is the
NREL-maintained reference configuration and the correct anchor for the solar field / TES lane.

Reachable from PySAM with no SAM GUI involvement:

```python
import PySAM.TcsmoltenSalt as T
m = T.default("MSPTSingleOwner")
m.SolarResource.solar_resource_file = (
    r"C:\SAM\2025.4.16\solar_resource\daggett_ca_34.865371_-116.783023_psmv3_60_tmy.csv")
m.execute(0)
```

> The default config ships **without** a weather file — you must set it (see `CLAUDE.md` §4.4).
> Daggett CA is SAM's conventional CSP default site.

**Important scoping note:** this reference case uses a **steam-Rankine** power block
(`pc_config = 0`), *not* sCO₂. There is **no sCO₂-tower reference case in SAM** — no such
configuration exists in the GUI (`CLAUDE.md` §3). So this case validates the
**heliostat field + receiver + TES + annual dispatch** layers only. The sCO₂ power block must be
validated separately against literature (§2). That separation is exactly the decoupled strategy
`MASTER_PLAN.md` §6 calls for, and it is a strength, not a workaround — state it that way in the thesis.

### 1.2 Reference design parameters (stock defaults, ssc 306 / PySAM 7.1.1)

| Parameter | Value | Units |
|---|---|---|
| `P_ref` (gross cycle) | 115.0 | MWe |
| `solarm` (solar multiple) | 2.4 | – |
| `tshours` (TES duration) | 10.0 | h |
| `T_htf_hot_des` | 574.0 | °C |
| `T_htf_cold_des` | 290.0 | °C |
| `design_eff` | 0.412 | – |
| `rec_htf` | 17 (60% NaNO₃ / 40% KNO₃) | – |
| `h_tower` | 194.227 | m |
| `rec_height` | 20.4598 | m |
| `D_rec` | 16.922 | m |
| `N_panels` | 20 | – |
| `d_tube_out` / `th_tube` | 40.0 / 1.25 | mm |
| `eta_pump` | 0.85 | – |
| `piping_length_mult` | 2.6 | – |
| `helio_width` × `helio_height` | 12.2 × 12.2 | m |
| `helio_optical_error_mrad` | 1.53 | mrad |
| `helio_reflectance` | 0.90 | – |
| `u_tank` | 0.4 | W/m²-K |
| `pc_config` | 0 (steam Rankine) | – |

### 1.3 Baseline result — executed this session

| Metric | Value |
|---|---|
| `annual_energy` | **593,054,474.50 kWh** |
| `capacity_factor` | **66.5926 %** |
| `annual_W_cycle_gross` | 661,026,154.83 kWh |

Environment: PySAM 7.1.1.post1 / ssc 306 / Daggett CA `psmv3_60_tmy` / stock defaults.

**Treat these as the regression baseline.** Any future change to the field/TES layer that moves
`annual_energy` must be explainable.

### 1.4 Error table — TO BE COMPLETED

| Quantity | SAM 2025.4.16 GUI | PySAM 7.1.1 | % error | Notes |
|---|---|---|---|---|
| Annual energy (kWh) | _tbd_ | 593,054,474.50 | _tbd_ | |
| Capacity factor (%) | _tbd_ | 66.5926 | _tbd_ | |
| Gross cycle output (kWh) | _tbd_ | 661,026,154.83 | _tbd_ | |

**Next action:** open this exact case in the **SAM 2025.4.16 GUI** (ssc 306 — matches PySAM),
run it with the Daggett file, and fill the column. **Do not use the 2026.7.3 GUI** — it is ssc 308
and will produce version-artifact deltas (`CLAUDE.md` §1.1).

---

## 2. POWER BLOCK VALIDATION — sCO₂ recompression cycle

### 2.1 Status — RESOLVED (target selected, data in hand)

Two decoupled sub-goals, now both anchored:

- **Node-by-node (T, P, h, s) validation → Dostal 2004** (MIT-ANP-TR-100). Publishes full state
  tables for three recompression designs (550 / 650 / 700 °C). Data transcribed in §2.3. This is
  the PRIMARY power-block anchor and REPLACES the earlier Dyreby-only plan, which could not supply
  per-node h/s (Dyreby Table 6.1 gives design inputs only). See `SOURCES.md` §A5.
- **Aggregate design-point cross-check → Dyreby 2014** (thesis Table 6.1) and **Turchi 2013**
  (config-level η). Optional secondary confirmation only. See `SOURCES.md` §A1–A3.

Session B confirmed PySAM exposes **T, P, h AND s at every cycle node**, so the Dostal table can be
compared node by node, not just on bulk efficiency. Lead with that in the thesis.

### 2.2 Current model configuration (`scripts/smoke_test.py`) — PLACEHOLDER, must be rebuilt

10 MWe · `T_htf_hot_des` 720 °C · `T_amb` 35 °C · f_rc pinned 0.30 · HTR/LTR UA 7000 kW/K each ·
P_high 25 MPa · η_isen: MC/RC/PC 0.85, turbine 0.90.

Result (placeholder conditions): `eta_thermal_calc` = 0.49257, `P_comp_in` 8.8594 MPa,
`eff_HTR` 0.97241, `eff_LTR` 0.91190. Mixer energy balance closes to 0.00; all `Sgen > 0`.

> These are **placeholder operating conditions chosen to exercise the model**, not tuned to any
> published case. **Before computing any % error, rebuild at Dostal's boundary conditions** (see
> §2.3.5). Comparing our 720 °C / 25 MPa / f_rc 0.30 run against Dostal's 700 °C / 20 MPa / f_rc 0.41
> case would produce large *legitimate* differences that are NOT validation failures.

### 2.3 DOSTAL 2004 STATE-POINT DATA (extracted from page images, 2026-08-12)

**Source:** Dostal, Driscoll, Hejzlar 2004, MIT-ANP-TR-100. Free PDF:
https://web.mit.edu/22.33/www/dostal.pdf. Values transcribed directly from Tables 10.1, 10.2,
10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 13.1, 13.2 (pp. 227–235, 279). HIGH confidence — tabular
transcription, not figure-read.

#### 2.3.0 Recommended validation case
Our model runs 720 °C. Of Dostal's three designs, **High-Performance (700 °C)** is the nearest
regime; **Advanced (650 °C)** is the next nearest. **Validate against BOTH to bracket 720 °C.**
All three share: compressor inlet 32 °C, P_high 20 MPa, PR 2.6, conservative turbomachinery
(main compressor 89 %, recompressor 89 %, turbine 90 %).

#### 2.3.1 Common design conditions (Table 10.1, p.227 — conservative "Con." columns)
| Quantity | Basic | Advanced | High-Perf |
|---|---|---|---|
| Cycle thermal power (MWth) | 600 | 600 | 600 |
| Turbine inlet T (°C) | 550 | 650 | 700 |
| Compressor inlet T (°C) | 32 | 32 | 32 |
| Compressor outlet P (MPa) | 20 | 20 | 20 |
| Pressure ratio | 2.6 | 2.6 | 2.6 |
| Primary system ΔP (kPa) | 130 | 130 | 130 |
| Cooling water inlet T (°C) | 27 | 27 | 27 |
| Mass flow rate (kg/s) | 3209 | 2953 | 2801 |
| Recompressed fraction | 0.41 | 0.41 | 0.39 |
| Total HX volume (m³) | 120 | 120 | 120 |
| Turbine η (%) | 90 | 90 | 90 |
| Main compressor η (%) | 89 | 89 | 89 |
| Recomp. compressor η (%) | 89 | 89 | 89 |
| Generator η (%) | 98 | 98 | 98 |
| Thermal efficiency (%) | 45.27 | 49.54 | 51.27 |
| Net efficiency (%) | 41.00 | 45.25 | 46.96 |
| Net electric power (MWe) | 246 | 272 | 282 |

#### 2.3.2 NODE STATE POINTS — validate against BOLD-NUMBERED rows ONLY
Rows tagged `id` = ideal isentropic reference (shares s with inlet); `max` = max-regeneration
reference (recuperator effectiveness = 1). These are NOT model nodes — use them only to check
that isentropic-η and recuperator-effectiveness are applied correctly, never as error-table targets.
Units: P kPa, T °C, h kJ/kg, s kJ/kg·K.

**BASIC DESIGN — 550 °C (Table 10.2, p.228):**
| Point | P (kPa) | T (°C) | h (kJ/kg) | s (kJ/kg·K) |
|---|---|---|---|---|
| 1 | 7692.31 | 32.00 | 306.67 | 1.3478 |
| 2 | 20000.00 | 61.10 | 327.26 | 1.3546 |
| 3 | 19988.68 | 157.99 | 536.10 | 1.9099 |
| 4 | 19957.95 | 396.54 | 846.36 | 2.4908 |
| 5 | 19827.95 | 550.00 | 1035.25 | 2.7429 |
| 6 | 7901.16 | 440.29 | 914.45 | 2.7619 |
| 7 | 7814.21 | 168.34 | 604.19 | 2.2189 |
| 8 | 7704.58 | 69.59 | 478.64 | 1.9026 |
| (2id) | 20000.00 | 60.20 | 324.99 | 1.3478 |
| (3id) | 19988.68 | 154.02 | 529.77 | 1.8952 |
| (6id) | 7901.16 | 428.81 | 901.03 | 2.7429 |
| (7max) | 7814.21 | 157.99 | 592.21 | 2.1992 |
| (8max) | 7704.58 | 61.10 | 464.26 | 1.8652 |

**ADVANCED DESIGN — 650 °C (Table 10.3, p.229):**
| Point | P (kPa) | T (°C) | h (kJ/kg) | s (kJ/kg·K) |
|---|---|---|---|---|
| 1 | 7692.31 | 32.00 | 306.67 | 1.3478 |
| 2 | 20000.00 | 61.10 | 327.26 | 1.3546 |
| 3 | 19981.46 | 157.11 | 534.73 | 1.9068 |
| 4 | 19922.85 | 488.75 | 959.50 | 2.6463 |
| 5 | 19792.85 | 650.00 | 1160.20 | 2.8865 |
| 6 | 8039.33 | 534.31 | 1025.79 | 2.9051 |
| 7 | 7878.03 | 165.83 | 601.01 | 2.2189 |
| 8 | 7702.54 | 68.91 | 477.57 | 1.8921 |
| (2id) | 20000.00 | 60.20 | 324.99 | 1.3478 |
| (3id) | 19981.46 | 153.17 | 528.44 | 1.8921 |
| (6id) | 8039.33 | 521.85 | 1010.85 | 2.8865 |
| (7max) | 7878.03 | 157.11 | 590.87 | 2.2083 |
| (8max) | 7702.56 | 61.10 | 464.28 | 1.8528 |

**HIGH-PERFORMANCE DESIGN — 700 °C (Table 10.4, p.229):**
| Point | P (kPa) | T (°C) | h (kJ/kg) | s (kJ/kg·K) |
|---|---|---|---|---|
| 1 | 7692.31 | 32.00 | 306.67 | 1.3478 |
| 2 | 20000.00 | 61.10 | 327.26 | 1.3546 |
| 3 | 19990.22 | 159.88 | 539.07 | 1.9168 |
| 4 | 19944.56 | 531.33 | 1012.03 | 2.7132 |
| 5 | 19814.56 | 700.00 | 1223.34 | 2.9529 |
| 6 | 7929.22 | 578.31 | 1078.95 | 2.9719 |
| 7 | 7802.64 | 169.85 | 605.98 | 2.2212 |
| 8 | 7704.93 | 71.05 | 480.96 | 1.9020 |
| (2id) | 20000.00 | 60.20 | 324.99 | 1.3478 |
| (3id) | 19990.22 | 155.84 | 532.68 | 1.9020 |
| (6id) | 7929.22 | 565.05 | 1062.90 | 2.9529 |
| (7max) | 7802.64 | 159.88 | 594.46 | 2.1949 |
| (8max) | 7704.93 | 61.10 | 464.25 | 1.8527 |

#### 2.3.3 DOSTAL → SAM NODE MAP (⚠ DIFFERENT topology from Dyreby — do NOT reuse the old §2.2b map)
Dostal is a single-recompression layout with **8 numbered nodes**. The recompressed stream mixes
back **between the LTR and HTR** (visible as the 2→3 entropy jump in Fig 10.1, p.228). Map:

| Dostal | Definition (from Fig 10.1 / cycle path) | SAM node |
|---|---|---|
| 1 | main compressor inlet (= precooler outlet) | MC_IN |
| 2 | main compressor outlet (= LTR cold inlet) | MC_OUT |
| 3 | LTR cold outlet AFTER mixing w/ recompressed flow (= HTR cold inlet) | MIXER_OUT |
| 4 | HTR cold outlet (= PHX inlet) | HTR_HP_OUT |
| 5 | turbine inlet (= PHX outlet) | TURB_IN |
| 6 | turbine outlet (= HTR hot inlet) | TURB_OUT |
| 7 | HTR hot outlet (= LTR hot inlet) | HTR_LP_OUT |
| 8 | LTR hot outlet (= precooler + recompressor inlet) | LTR_LP_OUT |

⚠ **Two SAM nodes have NO direct Dostal row:** `LTR_HP_OUT` (LTR cold outlet BEFORE mixing) and
`RC_OUT` (recompressor outlet). Dostal's node 3 is already post-mix. Validate these by
conservation, not lookup — see §2.3.3a. Do NOT force a Dostal number onto RC_OUT; there isn't one.

#### 2.3.3a Validating the two un-tabulated SAM nodes (LTR_HP_OUT, RC_OUT)

**CHECK 1 — mixing junction closes to Dostal node 3:**
```
h3_dostal  ==  (1 - f) * h[LTR_HP_OUT]  +  f * h[RC_OUT]
```
where f = recompressed fraction. Plug in OUR model's LTR_HP_OUT and RC_OUT enthalpies; must
reproduce Dostal's h3. (Advanced 650 °C: h3 = 534.73, f = 0.41. High-Perf 700 °C: h3 = 539.07,
f = 0.39.) PASS → both nodes jointly validated + mixing logic confirmed. FAIL → real bug in the
mix/split; first suspect is the split-fraction CONVENTION (Dostal's f is the *recompressed*
fraction, i.e. the fraction bypassing the precooler+main compressor).

**CHECK 2 — RC_OUT via recompressor relation (independent of Check 1):**
```
recompressor inlet = Dostal node 8.   (Advanced: h8 = 477.57, s8 = 1.8921, P8 = 7702.54 kPa)
h[RC_OUT]  ==  h8 + (h8s(20 MPa) - h8) / 0.89
```
where h8s = isentropic enthalpy compressing from node 8 to 20 MPa, and 0.89 = conservative
recompressor isentropic efficiency (Table 10.1; the 94.8 % in Table 10.8 is the *best-estimate*
value — use 89 % to match the conservative state tables). Two independent checks on RC_OUT.

**Result:** 8 nodes validated by direct comparison (§2.3.2) + 2 by conservation (above) =
all 10 SAM nodes covered. Thesis wording: *"Eight state points were validated directly against
Dostal (2004); the two intermediate nodes internal to the recompression junction, which Dostal
does not tabulate separately, were validated by energy-balance closure at the mixing point and by
the recompressor isentropic relation."* Frame as a STRENGTH — it confirms junction physics, not
just endpoint values.

> ⚠ PROVENANCE NOTE: Checks 1–2 were derived from the cycle topology in Fig 10.1, not from a stated
> Dostal equation. The physics is standard and the numbers are transcribed from the tables, but
> confirm both checks close numerically in the Code-lane rebuild before treating them as
> load-bearing in the thesis.

#### 2.3.4 STATE-POINT ERROR TABLE — TO BE COMPLETED (Code lane)
One row per node, per §2.3.3 map. Fill after rebuilding at Dostal boundary conditions (§2.3.5).
Recommend running the 700 °C High-Perf case first (nearest to our 720 °C).

| SAM node | Dostal pt | Quantity | Dostal (700 °C) | PySAM | % error |
|---|---|---|---|---|---|
| MC_IN | 1 | T,P,h,s | 32.00 / 7692.31 / 306.67 / 1.3478 | | |
| MC_OUT | 2 | T,P,h,s | 61.10 / 20000.00 / 327.26 / 1.3546 | | |
| LTR_HP_OUT | (recon) | h | via Check 1/2 | | |
| MIXER_OUT | 3 | T,P,h,s | 159.88 / 19990.22 / 539.07 / 1.9168 | | |
| HTR_HP_OUT | 4 | T,P,h,s | 531.33 / 19944.56 / 1012.03 / 2.7132 | | |
| TURB_IN | 5 | T,P,h,s | 700.00 / 19814.56 / 1223.34 / 2.9529 | | |
| TURB_OUT | 6 | T,P,h,s | 578.31 / 7929.22 / 1078.95 / 2.9719 | | |
| HTR_LP_OUT | 7 | T,P,h,s | 169.85 / 7802.64 / 605.98 / 2.2212 | | |
| LTR_LP_OUT | 8 | T,P,h,s | 71.05 / 7704.93 / 480.96 / 1.9020 | | |
| RC_OUT | (recon) | h | via Check 2 | | |
| — | — | η_thermal | 51.27 % | | |
| — | — | recomp fraction | 0.39 | | |

#### 2.3.5 REBUILD BOUNDARY CONDITIONS — set these BEFORE computing error (High-Perf 700 °C case)
| Parameter | Value | Note |
|---|---|---|
| Turbine inlet T | 700 °C | Table 10.1 High-Perf |
| Compressor inlet T | 32 °C | " |
| Compressor outlet P (P_high) | 20 MPa | " (NOT our placeholder 25 MPa) |
| Pressure ratio | 2.6 | → P_low ≈ 7.69 MPa |
| Recompressed fraction f_rc | 0.39 | " (NOT our placeholder 0.30) |
| Main compressor η_isen | 0.89 | conservative (Table 10.1) |
| Recompressor η_isen | 0.89 | conservative — NOT 0.948 (that's best-estimate) |
| Turbine η_isen | 0.90 | conservative |
| Total HX volume / UA | match to reproduce recuperator ΔT | see per-HX ΔP below |
| Working fluid | CO₂, REFPROP/CoolProp | Dostal used property tables; use CoolProp |

Per-recuperator ΔP for diagnostics (Table 10.6, reference/Basic design):
HTR hot 85.95 kPa / cold 27.38 kPa; LTR hot 109.35 kPa / cold 11.35 kPa; precooler gas side
12.27 kPa (Table 10.7). If rebuilt node *pressures* drift, this is the ΔP allocation to check.

> These are boundary-condition MATCHES, not tuning. The goal is to reproduce Dostal's case, then
> read off residual error. Any diff after matching these is the real model error.

### 2.6 EXERGY-READINESS BONUS (supports DECISIONS.md D1)
Dostal gives h AND s at every node → you can compute physical exergy e = (h−h₀) − T₀(s−s₀) at
each state directly from §2.3.2 and cross-check your model's per-node exergy against a published
reference. Also, the Basic-design heat balance (Table 10.5) closes to η_th 45.27 % from specific
work terms — q_add 188.89, q_rej 103.38, w_turb 120.80, w_MC 12.38, w_RC 22.91, w_comp,tot 35.29,
w_net 85.51 kJ/kg — so you can validate component work terms individually, not just bulk η.

---

## 3. OPEN ITEMS

- [ ] Run `MSPTSingleOwner` in the SAM **2025.4.16** GUI; fill §1.4.
- [x] Select the sCO₂ power-block validation source — **Dostal 2004** (node tables in §2.3).
- [x] Node-numbering map written (§2.3.3) — supersedes the old Dyreby 1:1 map.
- [ ] Code lane: rebuild at §2.3.5 boundary conditions (700 °C High-Perf), fill §2.3.4 error table.
- [ ] Code lane: confirm §2.3.3a Checks 1 & 2 close numerically (validates LTR_HP_OUT, RC_OUT).
- [ ] Optional: repeat error table for Advanced 650 °C to bracket our 720 °C from both sides.
- [ ] Decide whether to also validate against SAM's built-in chloride salts (codes 6, 14) as an
      intermediate step toward the NaCl–KCl–MgCl₂ nano-HTF.
