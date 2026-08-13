# PROGRESS_LOG.md — dated, append-only

Entries are **atomic and self-contained**: a reader with zero context should understand what ran,
what came out, and what is next, without opening any other file. Newest entry at the bottom.
See `MASTER_PLAN.md` §8 for this file's role in the continuity system.

---

## 2026-08-12 — Code lane — Dostal (2004) literature validation of the sCO₂ cycle

**Goal.** Move `Sco2CspSystem` off placeholder boundary conditions and onto a published design
point, so the model's state table can be checked node-by-node against literature.

**What ran.**

- `scripts/validate_dostal.py` (new) — the sCO₂ recompression cycle at Dostal's high-performance
  design point: TIT 700 °C, compressor inlet 32 °C, P_high 20 MPa, PR 2.6 (P_low 7.6923 MPa),
  f_rc 0.39, η_mc/η_rc 0.89, η_t 0.90. Recuperators specified by **effectiveness 0.95** (Dostal
  specifies effectiveness, and unlike a UA it is scale-free, so it transfers to this 10 MWe model
  without rescaling). Base case is lossless so PR is exactly 2.6; a second case re-runs with SAM's
  stock 0.54 %/HX pressure loss.
- `scripts/smoke_test.py` — re-run to confirm the two fixes below changed nothing that is pinned.

**Results** (`results/dostal_validation_*.md`, `dostal_state_points_*.csv`,
`dostal_recup_sweep_*.csv`).

1. **It converges at the near-critical compressor inlet.** Dyreby's warning about 20 MPa / 32 °C
   did not materialise: `P_comp_in = 7.6923 MPa` and `T_comp_in = 32.000 °C` exactly, and the
   `P_LOW_OFFSET_MPA = 0.3` fallback (implemented via `is_PR_fixed < 0`) never fired. Every
   target was hit exactly — TIT 700.000 °C, P_high 20.0000 MPa, PR 2.6000, f_rc 0.39000.
2. **η_thermal = 51.532 %** vs **Dostal's 51.27 %** → **+0.26 pp** (+0.51 % relative). With the
   0.54 %/HX pressure loss it falls to 50.674 % (−0.60 pp). The effectiveness sweep brackets the
   published value cleanly: 0.94 → 50.745 %, 0.945 → 51.140 %, 0.95 → 51.532 %; **Dostal's
   51.27 % is reproduced at recuperator effectiveness ≈ 0.9467**, squarely inside his stated range.
3. **All verification checks pass.** Mixer energy balance closes to 8.3e-05 kJ/kg; all eight
   components have Sgen > 0 (HTR dominates at 3.891 kW/K = 1164 kW destroyed, then precooler
   1.558, turbine 1.734; total +9.914 kW/K); power balance closes to 0.00 kW and energy balance
   to 0.35 kW.
4. **ssc's internal CO₂ properties are effectively REFPROP-equivalent.** Re-evaluating every node
   from (T, P) with CoolProp 8.0.0 gives max |Δh| = 1.6e-04 kJ/kg and max |Δs| = 3.4e-07 kJ/kg-K.
   → **The project does not need a separate CO₂ property lane.** CoolProp is still used inside the
   validation script so the mixer and second-law checks do not depend on ssc being self-consistent.

**Four PySAM defects found and documented** (all now in `CLAUDE.md` §4):

- §4.8 — returning `model.Outputs` from a function **segfaults**. The Outputs group does not keep
  its parent model alive; the model is collected on return and the caller's next attribute read
  hits freed memory. Exit 139, no traceback, no stdout even under `-u`. Cost the most time here.
- §4.9 — `m_dot_co2_full` and `m_dot_htf_des` are **1000× their documented kg/s** (87268.8 where
  three independent energy balances all give 87.2688 kg/s); powers document MW but are kW.
- §4.7 — `HTR/LTR_design_code` is `1 = UA, 2 = min dT, 3 = effectiveness`, and `HTR_UA_des_in` is
  consumed in **W/K** despite documenting kW/K.
- §4.2 — a `0.0` left in an *unused* recuperator spec segfaults; inactive specs need non-zero
  placeholders.

**Fixes applied.**

- `scripts/smoke_test.py` — mass flow was `m_dot_co2_full / 3600.0`, making every printed Sgen
  **3.6× too low**; now derived from the turbine duty with an assert against `/1000.0` so a future
  PySAM that fixes the scaling trips loudly. Also corrected the design-code comments: the file has
  always been running a **min-dT = 10 °C** design, not the UA = 7000 its comment claimed.
  All `CLAUDE.md` §7 pinned baselines are byte-identical after the fix — only the Sgen block moved.
- `CLAUDE.md` — §4.3 recipe corrected (it recommended the wrong design code), §7 baseline
  relabelled as a min-dT design, §4.2 broadened, new §4.7–§4.10, CoolProp added to §1/§2, and the
  Dostal baseline added to §7.

**Next.**

- [ ] Fold the validation numbers into `VALIDATION.md` as the first entry in the % error table.
- [ ] Note in `PROPERTIES.md` that ssc CO₂ ≡ CoolProp, so no external CO₂ property lane is needed.
- [ ] Second validation anchor against a *different* source (Turchi / Chacartegui) at a different
      TIT, to confirm the agreement is not a single-point coincidence.
- [ ] Then proceed to the `Sco2CspUdPcTables` → `TcsmoltenSalt` bridge (`CLAUDE.md` §3).

---

## 2026-08-13 — Docs lane — Repo migrated to a new machine/user; stale-path cleanup + MENA weather file added

**Goal.** `CLAUDE.md` was written on a machine where the repo lived at `C:\Users\meade\...`; this
session is running from `C:\Users\chukw\code\moo-nehtf-sco2-brayton-cycle`. Fix stale paths before
they mislead a future session, and resolve the "MENA site still needs downloading" TODO from §5.

**What ran.** No scripts — documentation and file-organization only.

**Findings and fixes.**

1. `CLAUDE.md` repo-root header and the `cd` line in §2 said `C:\Users\meade\...`; corrected to
   `C:\Users\chukw\code\moo-nehtf-sco2-brayton-cycle`. Repo-wide grep for `meade` (case-insensitive)
   confirmed no other file references it.
2. §5's Southern Africa TMY file (`C:\Users\meade\SAM Downloaded Weather Files\...`) does **not
   exist** on this machine — checked under both `meade` and `chukw` user profiles, not found.
   Flagged in `CLAUDE.md` §5 as needing re-download; **not fixed this session**.
3. User supplied a new NSRDB TMY file at repo root: `158192_31.05_-6.86_tmy-2022.csv` — lat 31.05,
   lon −6.86 (Ouarzazate region, Morocco). This fills the "MENA site still needs downloading" gap
   noted in the previous `CLAUDE.md` §5. Moved into `data/tmy/` (new directory; already covered by
   the `data/tmy/` pattern in `.gitignore`, so it stays untracked like the SA file was meant to be)
   and documented in `CLAUDE.md` §5.

**Next.**

- [ ] Locate or re-download the Southern Africa (Upington) TMY file; place it in `data/tmy/`
      alongside the Morocco file once found.
- [ ] Continue the `Sco2CspUdPcTables` → `TcsmoltenSalt` bridge work (unaffected by this session).

---

## 2026-08-13 — Code lane — Environment rebuilt from scratch; Dostal validation re-run and reproduced

**Goal.** Re-run the Dostal (2004) high-performance validation on this machine to confirm the
`CLAUDE.md` §7 pinned baseline still holds. The run was requested as a "rebuild `smoke_test.py` at
Dostal boundary conditions" task; **no rebuild was needed** — `scripts/validate_dostal.py` (Session
C, commit `d040127`) already implements exactly the requested configuration, and every one of its
constants was verified line-by-line against the request before running. `smoke_test.py` correctly
keeps the 720 °C / 25 MPa / f_rc 0.30 placeholder conditions as the *environment-health* baseline;
the two scripts pin different things and neither should absorb the other.

**Environment blocker — the repo had no runnable Python at all.**

1. `.venv\` is gitignored and did **not** exist here (fresh clone; earlier sessions ran under the
   `meade` profile). Rebuilding it hit a hard wall: this machine has **Python 3.14 only**, and
   **NREL-PySAM ships no 3.14 wheels** — `pip` reports `(from versions: none)`, which reads like a
   network failure but is not. Confirmed the index was reachable by resolving CoolProp (~50
   versions listed) on the same interpreter.
2. Installed Python 3.13.15 alongside 3.14 with `winget install --id Python.Python.3.13
   --scope user` (user scope, no admin), rebuilt `.venv` with `py -3.13`, and installed the
   pinned set — PySAM 7.1.1.post1, numpy 2.5.2, CoolProp 8.0.0 — all resolving to the exact
   versions in `CLAUDE.md` §1.
3. `C:\SAM\` does **not** exist on this machine — both SAM installs are gone. This blocks only the
   GUI cross-check (`VALIDATION.md` §1.4) and the bundled weather/component libraries; the cycle
   scripts need neither and ran unaffected.
4. PySAM's bundled `ssc.dll` verified by `ctypes`: **ssc 306**, build
   `Windows 64 bit Visual C++ Apr 24 2026 01:21:21` — byte-identical to the §1 record, which is
   what makes the comparison below meaningful.

**Result — the baseline reproduced to every printed digit** (`results/dostal_validation_
20260813T012014Z.md` + the two CSVs; commit `fad1a0e-dirty`).

1. **Converges at the near-critical inlet.** `P_comp_in = 7.6923 MPa`, `T_comp_in = 32.000 °C`,
   PR 2.6000, P_high 20.0000 MPa, TIT 700.000 °C, `f_rc = 0.39000` — every target hit exactly.
   The `P_LOW_OFFSET_MPA = 0.3` fallback did **not** fire, so **Dyreby's convergence warning again
   did not materialise** and no offset needs reporting.
2. **η_thermal = 51.532 %** vs Dostal's **51.27 %** → **+0.26 pp** (+0.51 % relative). With SAM's
   stock 0.54 %/HX pressure loss: 50.674 % (−0.60 pp). Sweep unchanged — 51.27 % is reproduced at
   recuperator effectiveness ≈ 0.9467.
3. **All checks pass.** Mixer closes to 8.33e-05 kJ/kg; all eight components Sgen > 0 (HTR 3.891,
   turbine 1.734, precooler 1.558; total **+9.91403 kW/K**); power balance 0.00 kW, energy balance
   0.354 kW; ssc-vs-CoolProp max |Δh| 1.55e-04 kJ/kg, max |Δs| 3.40e-07 kJ/kg-K.
4. **Reproducibility is now an established property, not an assumption.** A from-scratch venv on a
   different machine and a different Python patch (3.13.15 vs 3.13.14) returned identical numbers
   throughout, including the full sweep. Recorded in `CLAUDE.md` §7 — any future deviation is a
   real modelling change, not environment drift.

**Docs updated.** `CLAUDE.md`: §1 table (Python 3.13.15, both SAM installs marked ABSENT), new
**§1.0** (the 3.14/PySAM wheel trap and how to tell it apart from a network failure) and **§1.0a**
(no SAM GUI here — what that does and does not block), §7 reproducibility note.

**Next.**

- [x] Node-by-node error table vs Dostal Table 10.4 → done immediately below.
- [ ] `VALIDATION.md` §2.3.3a Checks 1 & 2 (LTR_HP_OUT, RC_OUT by conservation).
- [ ] Commit the new `results/` artifacts — left uncommitted this session.
- [ ] `VALIDATION.md` §1.4 GUI cross-check is **blocked** until SAM 2025.4.16 is reinstalled.

---

## 2026-08-13 — Code lane — Node-by-node error table vs Dostal Table 10.4 (fills VALIDATION.md §2.3.4)

**Goal.** Compare all eight tabulated nodes of the 700 °C high-performance case against Dostal
(2004) Table 10.4 on T, P, h and s separately, and fill the error table that has gated the
power-block validation since Session C.

**What ran.** `scripts/compare_dostal_nodes.py` (**new**) — imports `validate_dostal.py`, re-solves
the base (lossless) case, and emits the per-node error table plus a paste-ready markdown block.
`LTR_HP_OUT` and `RC_OUT` are deliberately excluded (no published row; they are validated by
conservation in §2.3.3a). Dostal's `id`/`max` rows are reference states and are never used as
targets. % error on **T uses the absolute (K) denominator** — node 1 is 32 °C, so a Celsius
denominator would inflate a 0.5 K miss into 1.6 %.

**Results** (`results/dostal_node_errors_20260813T012414Z.{md,csv}`).

1. **Six of eight nodes agree to ≤ 1.1 % on h and ≤ 0.6 % on s.** `MC_IN` and `MC_OUT` match to
   ~0.002 % — i.e. the compressor line is essentially exact. **η_thermal +0.511 % error**
   (51.532 % vs 51.27 %, +0.262 pp); `recomp_frac` 0.39000 exact.
2. **Two nodes flagged (> 2 % on h or s): `MIXER_OUT` (+5.05 % h, +3.21 % s) and `HTR_LP_OUT`
   (+5.37 % h, +3.32 % s).** These are **the two ends of the LTR/HTR interface** — not scattered,
   which is what makes the cause identifiable.
3. **Diagnosis: one recuperator duty-split difference, not a defect.** Our HTR moves 434.61 kJ/kg
   against Dostal's 472.96 (−8 %), with a cold-end approach of ~20.1 K against his ~9.97 K. The
   LTR takes up the slack (our `MIXER_OUT` runs 18 K hotter), so total regeneration and η still
   agree. Cause: we specify **both** recuperators at effectiveness 0.95, whereas Dostal allocates
   a fixed **120 m³ total HX volume** between them, giving an unequal split and a tighter HTR. At
   the HTR cold end's strong cp variation, ε = 0.95 does not buy a 10 K approach.
4. **The P column is entirely the lossless assumption**, as §2.3.5 predicted: node 1 is exact and
   the error grows toward the turbine exhaust (`TURB_OUT` −2.99 %), because our low side sits at
   7692.31 kPa throughout while Dostal's ΔP accumulates. The 0.54 %/HX case pulls `TURB_OUT` to
   −1.40 %.
5. **A tension worth carrying into the thesis:** the model reproduces Dostal's η at *looser*
   recuperators (ε ≈ 0.9467) than his own ~10 K HTR implies. So tightening the HTR alone would
   push η past 51.27 % and destroy the agreement — his ΔP must be added at the same time.

**Docs updated.** `VALIDATION.md` §2.3.4 replaced with the completed table, the duty-split
diagnosis and an explicit warning against the one-sided "fix"; §3 open items re-ticked with the
combined ΔP + duty-split follow-up; header status line updated.

**Next.**

- [ ] The §2.3.4 follow-up: Dostal's HTR approach (`HTR_design_code = 2`, ~10 K) **and** his
      130 kPa primary ΔP together; check both flagged nodes come inside 2 % without η overshooting.
- [x] `VALIDATION.md` §2.3.3a Checks 1 & 2 (LTR_HP_OUT, RC_OUT by conservation) — done immediately
      below.
- [ ] Commit `scripts/compare_dostal_nodes.py` + the `results/` artifacts from both sessions today.

---

## 2026-08-13 — Code lane — LTR_HP_OUT and RC_OUT validated by conservation (fills VALIDATION.md §2.3.3a)

**Goal.** Dostal's node 3 is post-mix, so `LTR_HP_OUT` (LTR cold outlet, pre-mix) and `RC_OUT` have
no published row. Validate them by conservation instead, and discharge the provenance caveat
§2.3.3a carried — those checks were derived from Fig 10.1's topology, not a stated Dostal equation,
so they were explicitly not to be treated as load-bearing until they closed numerically.

**What ran.** `scripts/check_untabulated_nodes.py` (**new**), base lossless 700 °C case. Each check
was **split into an internal and an absolute variant**, because collapsing them hides which physics
failed: the internal variants are driven by our own nodes and test the physics; the absolute
variants are driven by Dostal's numbers and inherit the §2.3.4 duty-split offset.

**Results** (`results/dostal_junction_checks_20260813T012905Z.{md,csv}`).

| Check | Expected | Model | Abs | % | Result |
|---|---|---|---|---|---|
| 1A junction closes on our nodes | 566.2928 | 566.2928 | +0.0000 | +0.000 % | **PASS** |
| 1B same mix vs Dostal h₃ | 539.0700 | 566.2928 | +27.2228 | +5.050 % | **FAIL** |
| 1B swapped convention | 539.0700 | 557.6326 | +18.5626 | +3.443 % | FAIL |
| 2A RC isentropic, Dostal node 8 | 539.1148 | 542.2806 | +3.1658 | +0.587 % | **PASS** |
| 2B RC isentropic, our node 8 | 542.2806 | 542.2806 | −0.0000 | −0.000 % | **PASS** |

1. **`RC_OUT` is confirmed independently of the mixer** — Check 2 never touches `LTR_HP_OUT`. It
   closes to +0.587 % on Dostal's node 8 and **exactly** (−0.0000 kJ/kg) on ours, so ssc applies
   η_rc = 0.89 to the letter; the 0.587 % is just our node-8 h offset (+0.50 %) propagating.
2. **`LTR_HP_OUT` is pinned by 1A** — with `RC_OUT` confirmed and the junction closing to
   0.0000 kJ/kg, it is the only remaining unknown in the balance.
3. **The split-fraction convention is confirmed, not assumed.** The swapped form was evaluated as
   instructed: still wrong against Dostal (+3.443 %) *and* it would destroy the exact internal
   closure. A convention error is **ruled out** as the explanation for 1B.
4. **1B is not independent evidence and must not be double-counted.** Because 1A closes to zero,
   1B is *arithmetically the same quantity* as the `MIXER_OUT` h error in §2.3.4 (+5.050 %,
   identical to 3 d.p.). It restates the one recuperator duty-split difference already diagnosed —
   reporting it as a second, separate failure would count one discrepancy twice. Called out
   explicitly in §2.3.3a-R so a future reader does not make that mistake.

**Docs updated.** `VALIDATION.md`: new **§2.3.3a-R** with the results table, the verdict and the
double-counting warning; the ⚠ provenance note marked **RESOLVED**; §3 open item ticked with
"all 10 model nodes now covered"; header status line updated.

**Status:** the power-block half of the gate file is now complete — 8 nodes direct + 2 by
conservation, η within +0.26 pp.

**Next.**

- [x] The §2.3.4 follow-up (tighter HTR **and** 130 kPa primary ΔP together) — done immediately
      below; the answer was not what was expected.
- [ ] Second literature anchor at a different TIT (Turchi / Chacartegui), to show the agreement is
      not a single-point coincidence.
- [ ] Commit today's scripts + all `results/` artifacts.

---

## 2026-08-13 — Code lane — Dostal Table 10.4 reproduced to within 0.07 % at every node (VALIDATION.md §2.3.4a)

**Goal.** Test the §2.3.4 follow-up: does tightening the recuperators to Dostal's ~10 K approach
*together with* his primary ΔP fix the two flagged nodes without breaking the η agreement? Run as
a **diagnostic** — no pinned baseline was to be changed, since adoption alters every state point.

**What ran.**

- `scripts/dostal_dp_recup_matrix.py` (**new**) — a case matrix over recuperator tightness ×
  pressure loss × recompressed fraction. Reuses `compare_dostal_nodes.build_rows` for the error
  machinery rather than reimplementing it.
- `scripts/check_dostal_table_consistency.py` (**new**) — no model run at all; pure arithmetic on
  Dostal's published values plus CoolProp for one isentropic state.
- `scripts/validate_dostal.py` — `build()`/`solve()` extended with `recup_code`, `recup_min_dT`,
  `dp` (per-HX loss fractions) and `f_recomp`. **All defaults preserve the original behaviour**;
  re-run afterwards and every §7 pinned number is bit-for-bit identical (exit 0).

**Result 1 — the §2.3.4 warning was right in direction but wrong about sufficiency.** Both
predicted signs held (tightening alone **+0.359 pp**, ΔP alone **−1.205 pp**), but the magnitudes
do not cancel: ΔP costs roughly 3× what tightening gains, so **doing both undershot to −0.612 pp**
and still left a flagged node. Two compensating errors was the wrong model — there were three.

**Result 2 — the third factor was found in Dostal's own tables, not in ours.** We pin *f* = 0.39
from Table 10.1, but that value and Table 10.4's state points are separate data and had never been
cross-checked. Imposing the HTR, LTR and mixer balances on the **published** values (with `RC_OUT`
fixed independently by the recompressor isentropic relation) closes the mixer only at
**f = 0.4097**. The **Advanced 650 °C design, run as a control**, implies 0.4049 against its stated
0.41 — Δ 0.005, which calibrates the method's resolution and makes the High-Performance
discrepancy **4× the noise floor**. At f = 0.4097 the two mixing streams differ by 0.076 kJ/kg —
a near-isenthalpic junction, which is what an optimised mixing point looks like. Both state tables
independently encode f ≈ 0.405–0.410; only High-Performance's *stated* value disagrees.

**Result 3 — all three together reproduce the published table almost exactly.**

| Case | Configuration | η % | Δ pp | MIXER h | HTR_LP h | RMS h | Flags |
|---|---|---|---|---|---|---|---|
| A | ε 0.95, lossless *(pinned)* | 51.532 | +0.262 | +5.050 % | +5.373 % | 2.649 % | 2 |
| B | 10 K only | 51.891 | +0.621 | −2.500 % | −1.522 % | 1.109 % | 1 |
| C | ΔP only | 50.327 | −0.943 | +5.026 % | +5.329 % | 2.600 % | 2 |
| D | 10 K + ΔP | 50.658 | −0.612 | −2.824 % | −1.820 % | 1.197 % | 1 |
| E | f = 0.4097 only | 51.174 | −0.096 | +5.980 % | +5.987 % | 3.082 % | 2 |
| **F** | **all three** | **51.289** | **+0.019** | **−0.070 %** | **−0.051 %** | **0.032 %** | **0** |

**Case F matches every node to within 0.070 % on h, 0.045 % on s and 0.000 % on P, with η within
+0.019 pp.** Note ε_HTR 0.976 / ε_LTR 0.931 — **unequal**, confirming §2.3.4's inference that
Dostal's fixed 120 m³ volume allocation cannot be represented by equal-effectiveness specification.

**Method note worth keeping.** The ΔP values are Dostal's own for *this* design, derived as
consecutive differences of Table 10.4's node pressures — not the Basic-design Table 10.6 numbers
§2.3.5 offers as a fallback. The PHX difference came out at **exactly 130.00 kPa**, matching
Table 10.1's stated primary-system ΔP, which independently confirms the derivation. Same for the
10 K approach: read off Table 10.4, not assumed.

**Also fixed.** A reporting bug in the matrix script: the flagged-node counter was counting
(node, quantity) pairs, so it printed "4 of 2". Now reports distinct nodes and pairs separately.

**Docs updated.** `VALIDATION.md`: new **§2.3.4a** with the full case matrix, the *f* analysis and
an explicit "diagnostic, NOT the pinned baseline" status block; §2.3.4's warning annotated with
the outcome; §3 open items now carry the **decision required**. `CLAUDE.md` §7: note that a better
configuration exists and an instruction **not** to silently update the pinned baselines to it.

**Next.**

- [x] **DECISION TAKEN: case F adopted** — done immediately below.
- [x] Re-pinned `CLAUDE.md` §7, re-ran §2.3.3a, restated §2.3.4.
- [ ] Consider writing up the Table 10.1 vs Table 10.4 *f* inconsistency as a finding in its own
      right — it affects anyone validating against Dostal's High-Performance design.

---

## 2026-08-13 — Code lane — Case F ADOPTED as the validated power-block baseline

**Decision.** Case F (f_rc 0.4097 + 10 K recuperator approach + Dostal's own per-HX ΔP) replaces
case A (equal ε 0.95, lossless, f 0.39) as the pinned baseline. **Rationale:** this project's
downstream work is exergy analysis and MOO, both computed from *state points* rather than η. Case
A's HTR moved 8 % less heat than Dostal's, and that error falls on the cycle's largest exergy
destroyer (HTR, 1164 kW of 2966 kW). Case A was right about η for the wrong reasons — two errors
that cancelled — and such an agreement does not survive moving off the design point, which is
exactly what MOO does. Nothing in F is fitted; all three settings are read from Dostal's tables.

**New pinned numbers** (`scripts/validate_dostal.py`, case F):

```
eta_thermal_calc = 0.51289    <-- Dostal 51.27 % (+0.019 pp)
recomp_frac = 0.40970         m_dot_co2 = 92.233 kg/s
eff_HTR = 0.97625             eff_LTR = 0.93095      <-- UNEQUAL, and correct
T_turb_out = 578.309 C        T_HTR_HP_out = 531.256 C
recup UA total = 2306.6 kW/K  total Sgen = +10.22522 kW/K  (all 8 > 0)
```

**Changes made.**

- `scripts/validate_dostal.py` — `build()` defaults are now case F; `DOSTAL_DP_KPA`/`_FRAC` moved
  here as the single source of truth; `LEGACY_CASE_A` added and reported as a clearly-labelled
  second case; `eff_sweep()` re-scoped to the legacy parameterisation with a docstring explaining
  why it is kept (it is §2.3.4a's evidence, and says nothing about F).
- `scripts/dostal_dp_recup_matrix.py` — every case now sets **all four** knobs explicitly, since
  relying on `build()`'s defaults would silently turn cases A–E into variants of F. Imports the ΔP
  table from `validate_dostal` instead of duplicating it. Added `assert best == "F"` so the
  adoption becomes a regression test rather than a one-off result.
- `scripts/check_dostal_table_consistency.py` — added the η_rc robustness sensitivity that made
  the decision safe (below).

**Verification after adoption — everything re-run, everything passes.**

1. `compare_dostal_nodes.py` → **0 nodes flagged**; worst h −0.070 %, worst s −0.045 %, RMS P
   0.000 %; η +0.019 pp.
2. `check_untabulated_nodes.py` → **all four checks PASS, 1B included.** 1B failed under case A;
   it resolved exactly as §2.3.3a-R predicted, because it was never an independent failure — it
   was the `MIXER_OUT` error in another form.
3. `dostal_dp_recup_matrix.py` → F still wins on both η and node agreement; now asserted.
4. Legacy case A reproduces **bit-for-bit** (η 0.51532, Sgen +9.91403, UA 1882.3) after the
   refactor, so the drift-detection anchor is intact.
5. The model now *produces* near-isenthalpic mixing — `LTR_HP_OUT` 538.32 vs `RC_OUT` 539.22 kJ/kg
   — which was predicted from Dostal's numbers beforehand, not imposed on the model.

**The η_rc robustness check that made this safe.** `f_implied` depends on the assumed recompressor
efficiency, so a different η_rc might have explained the discrepancy away. It cannot, and the
control makes the contrast sharp: justifying the Advanced design's stated f = 0.41 needs
η_rc = 0.932 (**plausible** — between Dostal's own 0.89 and 0.948), whereas justifying the
High-Performance design's stated 0.39 needs η_rc = 0.752 (**not plausible**). At either stated
efficiency the High-Performance table implies f ≈ 0.41–0.42, never 0.39.

**Docs updated.** `CLAUDE.md` §7 re-pinned to case F, with case A relabelled "regression anchor
only — never quote as validation" and an explicit warning not to "correct" f back to 0.39.
`VALIDATION.md`: §2.3.4 restated from case F, the old table preserved as **§2.3.4-A** (the
§2.3.4a argument is unreadable without it), §2.3.4a status block flipped to ADOPTED with rationale
and residual caveat, §3 open items closed.

**Next.**

- [ ] Second literature anchor at a different TIT (Turchi / Chacartegui) — with F matching to
      0.07 %, the single-point-coincidence objection is the main one left.
- [ ] Then the `Sco2CspUdPcTables` → `TcsmoltenSalt` bridge (`CLAUDE.md` §3).
- [ ] `VALIDATION.md` §1.4 GUI cross-check remains blocked (no SAM install, `CLAUDE.md` §1.0a).
