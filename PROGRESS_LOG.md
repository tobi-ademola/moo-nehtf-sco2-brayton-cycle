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

- [x] Second literature anchor — assessed, then **deliberately deferred**; see the entry below.
- [ ] Then the `Sco2CspUdPcTables` → `TcsmoltenSalt` bridge (`CLAUDE.md` §3).
- [ ] `VALIDATION.md` §1.4 GUI cross-check remains blocked (no SAM install, `CLAUDE.md` §1.0a).

---

## 2026-08-13 — Planning — Validation lane CLOSED and deferred; critical path re-pointed at the integrated model

**Trigger.** After the second-anchor assessment (`SOURCES.md` §A8) the question was raised
directly: is further validation on the critical path of a ~33-hour sprint, or a diversion?
**Answer: a diversion.** Acted on immediately rather than continuing.

**The reasoning, for the record.**

1. `MASTER_PLAN.md` §2 makes validation a **gate**, and a gate is binary. The power block passed
   it at 0.070 %/node and η +0.019 pp — far beyond what the gate asks. Further validation does not
   make it "more passed."
2. **One of the arguments made earlier this session cuts the other way, and is recorded here
   honestly:** `f_RC` is **decision variable #10** and `T_t,in` is **#7** — the optimizer *sweeps*
   both. So pinning f correctly matters far less than was implied when case F was recommended.
   Case F was still right (its state points feed the exergy layer, and case A's were wrong by up
   to 5.4 %), but a *second literature anchor* adds little on top of that.
3. The binding constraint is no longer credibility, it is **coverage**: the integrated
   CSP–HTF–TES–sCO₂ model of Objective 2 **does not exist yet**, and the Morris screening that is
   the *guaranteed deliverable* sits on top of it.

**What was done.** No model runs. Documentation only, to stop the validation lane competing with
the deliverable:

- `MASTER_PLAN.md` — was still at "v0.1 initial" and badly stale, which matters because §0 calls it
  the single source of truth for cold starts. Rewritten: §2 critical-path diagram now shows where
  the path actually is; §6 records Dostal as the anchor (superseding the Turchi/Chacartegui
  candidates, neither of which publishes per-node *h*/*s*); §9 replaced with sessions actually
  completed; §10 open questions resolved where answered; **new §11** (the ordered critical path)
  and **new §12** (the deferred backlog with an explicit restart trigger).
- `VALIDATION.md` §3 — deferral banner added pointing at `MASTER_PLAN.md` §12.

**Deferred, with restart trigger "after Morris screening is delivered":** Dostal 550/650 °C node
tables (cheapest, no new literature, covers the T_t,in span the optimizer will explore); Battisti
2023 exergy cross-check (free once the exergy layer exists); independent node anchors — Padilla
2015 / Moisseytsev 2009 / Sarkar 2009 (**PDFs deliberately not acquired**); SAM GUI cross-check.

**Two things surfaced that are NOT deferred.**

- ⚠ **`DECISIONS.md` does not exist.** `MASTER_PLAN.md` §8 lists it as one of the seven portable
  continuity files, and Session A was supposed to emit it. Any decision it held lives only in a
  chat transcript — which §8's own portability rule forbids.
- ⚠ **The live blocker is the salt/SAM reconciliation** (§4 flag, §10). `rec_htf = 50` gives an
  override path via a user-defined property table, but it is unverified across the chloride
  temperature range. **This gates Objective 2 and should be the next thing run.**

**Next.** `MASTER_PLAN.md` §11, in order — starting at item 1 (salt/SAM reconciliation), then the
`Sco2CspUdPcTables` → `TcsmoltenSalt` bridge.

---

## 2026-08-13 — Code lane — Exergy layer verified end-to-end; MASTER_PLAN §5's +1-day risk CLOSED

**Goal.** Prove the exergy reporting layer is arithmetically sound on data the model already
carries, before `MASTER_PLAN.md` §11 item 5 builds it for real. Session B established entropy is
*exposed*; it never demonstrated a correct layer could be *built* on it. This closes that gap.

**What ran.** `scripts/exergy_layer_check.py` (**new**) on the adopted case F baseline.
`validate_dostal.py` refactored: the per-component second-law physics extracted into
`entropy_generation()` so it is written once and shared, rather than duplicated into the new
script. Baseline re-run afterwards — case F (η 0.51289, Sgen +10.22522) and legacy case A
(η 0.51532, Sgen +9.91403) both **bit-for-bit unchanged**, exit 0.

**Results** (`results/exergy_layer_check_20260813T023227Z.{md,csv}`). **All five checks pass.**

1. e = 0 at the reference node, **exactly**; exergy maximal at `TURB_IN` (426.88 kJ/kg); every
   component ĖD > 0 (8 of 8).
2. **HTR is the largest destroyer at 1265.62 kW = 41.4 %**, then turbine 17.1 %, precooler 15.2 %,
   LTR 11.4 %. This matches **Battisti 2023** (`SOURCES.md` F2) — so the deferred exergy
   cross-check from `MASTER_PLAN.md` §12 item 2 is **already satisfied for the cycle**, at no cost.
3. **The cycle-wide exergy balance closes**: Ex_in(salt) 13060.82 = W_net 10000.00 + ΣĖD 3058.87,
   residual **1.95 kW = 1.5e-04 relative**. This is the load-bearing check — it exercises every
   *h*, every *s*, both mass flows, the salt properties and the work terms simultaneously, so it
   catches scaling/unit errors that per-component sign checks cannot (cf. the 1000× mass-flow trap,
   `CLAUDE.md` §4.9). **Second-law efficiency 76.56 %.**
4. **`MIX` destroys 0.01 kW — essentially nothing.** That is the second-law signature of case F's
   near-isenthalpic junction; the same term was 16.14 kW under legacy case A. An *independent*
   confirmation that the adopted baseline's mixing point is right.

**A correction this surfaced that affects every downstream ĖD number.** Two T₀ values are in play
and they are not interchangeable. The requested per-node reference (Dostal node 1, 305.15 K at
**7.69 MPa**) is a **reference state, not a dead state** — the cycle cannot reject heat to
7.69 MPa, and e = 0 there is true by construction, so that check tests the wiring, not the physics.
Gouy-Stodola ĖD = T₀·Sgen is only meaningful at the **environment** temperature,
**T_amb = 299.15 K**. Using node 1 instead inflates every ĖD by ~2 % and leaves the exergy balance
open by **−188.5 kW (−1.46 %)** rather than closing to 1.95 kW. The component *ranking* is
identical either way — **so no sanity check catches this; only the balance does.** Both are
computed and printed side by side so the distinction cannot be lost.

**Consequence.** `MASTER_PLAN.md` §5's CoolProp-reconstruction fallback (+~1 day) is **closed, not
merely unlikely**, and `DECISIONS.md` D1's fallback can be retired. `min ĖD` — a named primary
objective — is confirmed computable from data already carried. §11 item 5 is now wiring work
against the integrated model, not method risk.

**Docs updated.** `VALIDATION.md` new **§2.5** (node exergy + ĖD tables, the T₀ warning);
`DECISIONS.md` D1 extended with the execution evidence and the T₀ correction; `MASTER_PLAN.md` §5
risk marked closed and §11 item 5 re-scoped.

**Next.** Unchanged — `MASTER_PLAN.md` §11 item 1, the salt/SAM reconciliation, which is still the
live blocker on Objective 2.

---

## 2026-08-13 — Code lane — §11 item 1 CLOSED, item 2 PARTIAL; prior-project files triaged

**Trigger.** "What are the next steps" → a review of `MASTER_PLAN.md` §11 turned up three
substantial **untracked** files in the repo root that the plan knew nothing about. The user
clarified their status, which changed what to do with each: `nanofluid_properties.py` is a
**heavily-validated asset from previous work**, and `sam_case.py` / `sco2_cycle_map.py` are
**reference material to mine**, not code to adopt.

**⚠ A second Code session was committing to this repo concurrently** (commit `822562b`, landed
between two of this session's commands). It absorbed an in-flight `git add`, and committed the
two reference files into the repo root. No damage — its exergy work was independently re-run
here and reproduces (HTR-dominant 41.4 %, balance 1.5e-04) — but **check `git log` before
assuming the tree is yours.**

**Done.**

1. **`DECISIONS.md` committed** (`f2fde9d`). It existed only as an untracked file while §8 listed
   it as one of the seven portable continuity files — the flag raised in the previous entry.
2. **Pre-existing uncommitted work committed** (`822562b`, by the other session): the exergy
   layer check and the `entropy_generation()` refactor. Verified first — case F reproduces at
   η 0.51289 / Sgen +10.22522 and case A at 0.51532 / +9.91403, bit-for-bit.
3. **`nanofluid_properties.py` promoted** to `scripts/` (`b0c0be7`) with a §0 header. Physics
   byte-for-byte unchanged; all six Han/B3 anchor points still reproduce. Fixed its one
   portability bug — a hardcoded `/tmp` output path that killed the run on Windows.
4. **Reference files parked** in `reference/prior_project/` (`85d7eff`) with a README recording
   why they cannot be used directly: their cycle design contradicts case F (η 0.44 vs 0.51289,
   `recomp_frac` 0.113 vs 0.4097), `design_method = 1` + `is_recomp_ok = 1` is the §4.3 collapse
   mode, and their "CLAUDE.md §6/§7" citations point at a **different repo's** file.
5. **`CLAUDE.md` §4.11–§4.14 and §6 written** (`b991b33`) — every harvested claim re-verified
   here rather than transcribed on the reference's authority.

**§11 ITEM 1 — THE LIVE BLOCKER — IS CLOSED. `scripts/htf_sam_bridge.py` (`330fe7e`).**

`rec_htf = 50` **accepts** the nano-chloride table: stored with **zero** round-trip deviation
across six cases, annual model solves. **The nano-chloride couples INSIDE SAM — no external
coupling layer needed.** `DECISIONS.md` D2's mechanism is confirmed and `MASTER_PLAN.md` §4/§10's
open flag is answered.

Three things matter more than the yes:

- **Acceptance is not validity.** A chloride case at nitrate's hot temperature returned a
  **negative nameplate** (−52,858 kW; receiver pump 162 MW) with no error, no warning, a full
  8760 `gen` array and a plausible 288 GWh. Screen on `system_capacity > 0`.
- **`capacity_factor` is not comparable across these cases** — its denominator is the per-case
  nameplate, so CF *rises* while annual energy *falls*.
- **The ΔT→pumping coupling is the study's real constraint.** 124 K → 162.30 MW (infeasible);
  250 K → 27.04 MW; 284 K (nitrate) → 8.49 MW. Roughly cubic. Puts a hard floor under T_hot that
  the optimizer must be *given*, not left to discover — binds variables #5 and #6.

Nano-enhancement behaves as the property model predicts: 0.7 wt% beats bare eutectic on output
(479.2 vs 466.3 GWh) *and* pump power (27.04 vs 35.31 MW); 2.0 wt% is worse than bare on both,
tracking Han's cp enhancement from +10.5 % to −3.5 %. **The loading optimum is interior** — which
is what makes it worth optimising. The chloride still trails nitrate by −9.6 %, as expected: the
power block here is deliberately still the **steam** Rankine, which cannot exploit 700 °C.

**§11 ITEM 2 — PARTIAL, AND HONESTLY SO. `scripts/build_udpc_map.py` (`08e1121`).**

- **Design point: solid.** 0.1 s, f_rc 0.4097 held, PR 2.6000, η 0.50547 — −0.742 pp vs case F,
  the expected cost of running T_htf_hot 700 °C (TIT 680) instead of 720 °C, which keeps the
  chloride inside its stated validity. Case F constants are *imported* from `validate_dostal.py`.
- **Transform: proven.** `--selftest` verifies the 13-col→7-col inverse-split on synthetic data
  independently of ssc. Needed precisely because the sweep does not run.
- **Off-design sweep: BLOCKED.** Will not complete in 5–16 min at 3³ or 5³. Ruled out by direct
  experiment: the custom fluid (nitrate hangs identically), pinned f_rc, pinned pressures, and
  `rel_tol = 4`. A loose config converges in 93.6 s but returns **`recomp_frac = 0.0`** — the
  §4.3 collapse, same signature as the prior project's 0.113.

> **The sweep converges only when the design is loose enough to collapse; the configuration that
> preserves the validated recompression cycle will not converge.** Unresolved.

**Next.** Two suspects remain, down from six: `design_method = 3`, and the min-approach-dT
recuperator spec held across off-design. **Try `HTR/LTR_design_code = 3` (effectiveness,
scale-free, §4.7) for the MAP run while keeping code 2 for design validation** — a 10 K approach
may simply be infeasible at deep turndown. Then §11 items 3–4 (decision vector, Morris).

**UPDATE, same session — that hypothesis was tested and is WRONG, along with every other
single-variable one.** `HTR/LTR_design_code = 3`, pinned at case F's own produced
effectivenesses (0.97510 / 0.93098), **still hangs**. So do three further single changes tried
after it: `design_method = 2` (total UA 2306.6 kW/K), `design_method = 1` (target η 0.50), and
narrowing the sweep corners to m_dot 0.85–1.05 / T_amb 15–40 °C / T_htf 680–710 °C.

**That is seven single-variable deviations from case F, all negative.** The earlier framing —
"two suspects remain" — was wrong: it assumed one bad setting. There isn't one. Only the *whole
loose bundle at once* converges (93.6 s, `recomp_frac = 0.0`).

> **Revised conclusion: a case-F-style FULLY DETERMINED design — every recuperator specified,
> f_rc pinned, both pressures pinned — is over-constrained for UDPC generation.** The off-design
> solver needs degrees of freedom that the validation design deliberately removes.

**Revised next step: bisect in the OPPOSITE direction.** Start from the known-good loose bundle
and re-tighten one setting at a time toward case F until convergence breaks. The boundary is a
*combination* inside {design_method, f_rc pinning, pressure pinning}. It is also the cheaper
direction: ~1.5 min per success versus ~5 min per failure.

If the boundary excludes a pinned f_rc outright, that is a **modelling decision, not a bug**, and
belongs in `DECISIONS.md`: the map would be generated at a solver-chosen f_rc and the gap against
case F's 0.4097 measured rather than assumed small. f_rc is decision variable #10, which the
optimiser sweeps anyway — so this may cost less than it first appears.

---

## 2026-08-14/15 — Code lane — **THE UDPC BLOCKER WAS NOT REAL. §11 item 2 IS CLOSED.**

**Trigger.** "Pick up where we left off" → the documented next action was `THESIS_SYNTHESIS.md`
§17 item 1: re-establish the bisection control before interpreting anything in the Round-2 table.
That instruction was right and it broke the case open — but the answer was the opposite of the
expected one.

### 1. The finding: the sweep converges at the FULL case F design

```
case_F, sweep ON, 3 pts/axis  ->  USABLE in 2277.9 s (38.0 min)
                                  recomp_frac 0.40970, eta 0.50547, tables non-empty
```

`results/udpc_bisect_20260814T194825Z.*`. **Nothing had to be loosened.** All five configurations
run with the sweep on are usable, and the knobs move wall time by only ~20 %:

| case | wall s | recomp_frac | eta |
|---|---|---|---|
| `case_F` (all tight) | 2277.9 | 0.40970 | 0.50547 |
| `F_loose_frc` | 2152.3 | 0.41067 | 0.50569 |
| `F_loose_dm` | 2218.6 | 0.40970 | 0.49999 |
| `F_loose_press` | 1882.8 | 0.40970 | 0.50654 |
| `F_loose_tol` | 1963.3 | 0.40970 | 0.50512 |

### 2. Why the previous conclusion was wrong

**Every one of the twelve prior experiments was capped at 5–16 minutes against a run needing
31–38.** None had ever observed a completion, so none licensed the word "hangs". What was measured
was *"did not finish inside my timeout"*; what was recorded was *"does not converge"* — and a
mechanism ("a fully determined design is over-constrained for UDPC generation") was then built to
explain a dozen non-observations.

It was persuasive because it had every marker of a sound finding except a valid measurement:
twelve cells agreed (they agreed because they shared the defect); the mechanism was physically
plausible; the one anomalous point (`recomp_frac = 0`) matched the genuinely documented §4.3
collapse and so looked already explained; and the cost structure discouraged the disconfirming
test, since every redesign of the search made runs *shorter*. The single experiment that would
have settled it — let one case run to completion, however long — was never the cheap option and
was never run.

**Two supporting corrections:**

- **`design_method = 1` was miscategorised as "loose". It is not — it ADDS a constraint** (an
  inverse solve for the recuperator conductance that hits a target η). With free pressures and a
  free `f_rc` it is the **only** configuration that genuinely fails: 2026 s, then a real
  diagnostic — *"Can't find a value of total recuperator conductance that achieves the target
  cycle efficiency."* The trusted control was the one broken cell, and every stage-1 case
  inherited it, so those five results are **void**, not merely uninterpreted.
- **The 93.6 s / `recomp_frac = 0.0` run has never reproduced.** Do not cite it.

**Rule adopted** (`CLAUDE.md` §4.15, `MASTER_PLAN.md` §10): a non-convergence may be recorded only
against a **measured** completion time for that class of run, or with an explicit statement that
none is known.

### 3. A second silent bug, caught in the same pass

The n=3 bridge reported `roundtrip_rel = 0.000e+00` and "the bridge is CLOSED" while shipping
**`ud_f_W_dot_cool_des = 0.0000 %`** — a 115 MW plant with a costless air cooler.
`build_udpc_map.py` computed `100 × cool_des / 115000`, treating the map's dimensionless cooling
column as if it were kW. The first correction (`100 × cool_des` = 0.0997 %) was **also wrong**, by
10×, so `scripts/check_udpc_cooling_scale.py` was written to settle it against ssc's own scalars:

```
cooler_tot_W_dot_fan      1150.0 kW  ->  1.0 % of the 115 000 kWe design
W_dot_net_less_cooling  113850.0     =   115000 - 1150   (confirms value AND unit, §4.9)
```

1.0 % matches the `fan_power_frac = 0.01` supplied as an input. `cooling_fraction_pct()` now takes
the magnitude from ssc and **refuses to emit anything outside 0.05–10 %**.

> **Round-trip fidelity tests transport, not correctness.** The table went in and came back
> bit-identical while being scaled wrongly the whole time. It was caught by reading a magnitude
> that was physically impossible, not by any check in the script.

### 4. §11 item 2 delivered — the FIRST INTEGRATED ANNUAL RESULT

`scripts/run_integrated_annual.py`, `results/integrated_annual_20260815T094134Z.*`. Morocco TMY,
nano-chloride at 0.7 wt% via `rec_htf = 50`, UDPC map n=3, `Singleowner` created before
`execute()` (§4.13):

| case | status | annual kWh | nameplate kW | loop ΔT | rec pump des |
|---|---|---|---|---|---|
| `sco2_n3` | OK | **440,206,500** | **62,612** | 167 K | 49.55 MW |
| `steam_same_T` | OK | 389,388,747 | 22,945 | 167 K | 86.73 MW |

**The §7.5 inference is now tested rather than asserted: +13.05 % annual energy** for sCO₂ over
steam at identical fluid, loop temperatures and field area (A_sf 1,348,316 m² in both). ⚠ State it
precisely: receiver design duty is **not** held fixed (546.0 vs 669.9 MW), because
`q_rec = P_ref/design_eff × SM` — a more efficient cycle needs less heat for the same gross
output, which also cuts its pumping. The 13.05 % contains both effects.

**The integrated model's own new constraint, and it is the important one.** The sCO₂ recompression
cycle is heavily recuperated, so it returns HTF at **533.3 °C** against a 700 °C source — a loop ΔT
of only **166.7 K**. The design is feasible (positive nameplate) but pays **49.55 MW of receiver
pumping, ~43 % of gross**, leaving 62.6 MW net out of a 115 MW block.

**This cross-validates §7.4 from an independent direction.** Applying that section's ṁ ∝ q/ΔT with
W ∝ ṁ³ to its 250 K / 669.9 MW anchor predicts **49.4 MW** against **49.55 MW measured** (0.3 %);
the steam case predicts 91.3 vs 86.73 MW measured, 5 % high and consistent with §7.4's measured
sub-cubic exponent. Two independently built modules agree on a parasitic neither was fitted to.

⚠ `capacity_factor` came out at **193.73 %** for the steam case — live confirmation of the §7.7
trap, since its denominator is that case's own 22.9 MW nameplate. **Not quotable.**

### 5. Scripts and docs

- **New:** `scripts/run_integrated_annual.py`, `scripts/check_udpc_cooling_scale.py`.
- **`scripts/udpc_convergence_bisect.py`** — added **stage 3**, which walks the lattice from case F
  (a known-good origin) rather than from the void loose bundle, plus `--sweep 0` to separate
  "never reached a design point" from "map generation failed". Stage 1's origin is labelled VOID.
- **`scripts/build_udpc_map.py`** — status docstring rewritten (the old one asserted
  non-convergence); the runtime warning now says *slow, ~31–38 min, do not kill it early*; map
  filenames carry their resolution (`_n3`, `_n5`) so two resolutions cannot overwrite each other.
- **Docs:** `CLAUDE.md` §4.15 (new), §4.12 extended, header; `MASTER_PLAN.md` §10 risk withdrawn
  and §11 item 2 closed; `THESIS_SYNTHESIS.md` §1.1, §1.2, §9 (rewritten, superseded diagnosis
  retained under a collapsed block), §12, §13, §14, §15, §17.

### 6. Map resolution — settled the same session

`results/integrated_annual_20260815T095718Z.*`. The n=5 map (45 rows) was built and run against
the n=3 map (27 rows) at an identical design point:

| map | annual kWh | nameplate kW | rec pump |
|---|---|---|---|
| n=3 (27 rows) | 440,206,500 | 62,612.0 | 49.55 MW |
| n=5 (45 rows) | 442,092,058 | 62,586.5 | 49.55 MW |

**+0.428 %.** Small enough that **Morris screening may use the cheap 3-point map** — the shift is
a property of the response surface, not of any one design, so elementary-effect *rankings* should
survive it. ⚠ **Not a convergence claim.** This is a single 3 → 5 step; SAM's own default surface
is **20** points per axis and neither 3 nor 5 was shown converged against it. A final reported
annual figure should use the densest affordable map and quote **±0.43 %** as resolution
uncertainty — treating 440.21 GWh as exact would repeat this session's own mistake of promoting an
unmeasured assumption to a result.

**Next.** §11 item 4 — wire the decision vector, then Morris. The build-cost partition must be
designed first: SM and t_TES need only a ~30 s tower run against an existing map, while the six
cycle variables force a ~35 min rebuild each — and note **φ forces a rebuild too**, since it
enters through the HTF property table and therefore changes the PHX. A naive (10+1)×r Morris
design implies tens of hours of map generation alone; cache maps per cycle-design instead.
Add the new §9.5b constraint to the vector: the integrated design sits at a 166.7 K loop ΔT and
spends ≈43 % of gross on pumping, so ΔT is an active variable, not a passive outcome.

---

## 2026-08-15 — Research lane — SOURCES.md reconciled against the hand-verified DOI set

**Ran:** `scripts/reconcile_sources_dois.py` (new, durable) — report mode, then `--apply`.
**Outputs:** `results/sources_doi_reconcile_20260815T114805Z.{csv,md}` (the applying run) and
`results/sources_doi_reconcile_20260815T114945Z.{csv,md}` (final state ledger).

### 1. The two files were siblings, not ancestor and descendant

The user hand-verified every DOI in a copy of SOURCES.md, but the copy was taken from the Session D
draft, and SOURCES.md has since moved on. Neither file dominates:

```
b9db467 (165 lines, 12 DOIs)
   +--> Session D draft (50 sources) --> `SOURCES - Copy.md`  [+ hand-verified DOIs, + Prettier pass]
   +--> edd9f8b --> HEAD `SOURCES.md`                          [+ section A8, + F2 correction]
```

So `cp` in either direction destroys work. The merge was done the only correct way: **SOURCES.md
as the structural base, the copy contributing DOI VALUES only.** The copy's Prettier pass
(`*x*`→`_x_`, blank line after every heading) accounts for ~214 of the 244 diff lines and carries
no meaning — and it introduced two text corruptions that were therefore never inherited:
`c_p`→`c*p` and `_small_`→`\_small*` in C9, and `PT-CSP **+** TES` re-parsed into a list bullet
`- TES` in H5. **Do not adopt `SOURCES - Copy.md` wholesale for any reason.**

### 2. Result: 31 of 48 DOIs settled, 14 in conflict, 3 still missing

| status | n | meaning |
|---|---|---|
| CONFIRMED | 17 | identical in both files — the hand check carries over unchanged |
| FILLED | 14 | placeholder (`...2023.xxxxx`) in base, real DOI in the verified copy — applied |
| CHANGED | 14 | both real and DIFFERENT — **conflict, deliberately NOT auto-applied** |
| MISSING_DOI | 3 | A4, D1, D3 — no DOI in either file, lookup outstanding |

**F2 Battisti: caveat discharged.** Session E corrected this citation and left a "re-confirm the
DOI suffix at citation time" flag because MDPI blocks automated fetch (HTTP 403). The independent
hand pass returned the same `10.3390/en16124755`. Two routes agreeing is the confirmation asked
for. Telling detail: the copy paired that *new* DOI with the *old* `16(13):5073` volume text — the
DOI was checked, the surrounding metadata was not.

### 3. The 14 conflicts have a diagnosable signature, and it is not random

For Elsevier/MDPI/Springer the DOI suffix normally **is** the article number, so `Energy 300:131594`
should carry `10.1016/j.energy.2024.131594`. In **all 14** conflicts the as-drafted DOI satisfies
that identity and the hand-verified one does not — the signature of a DOI *synthesised from the
citation* rather than read off the article. That argues the verified column should win, **but the
two fields then contradict each other**: adopting the verified DOI makes the printed volume:article
the wrong field, and it must be corrected in the same pass. Logged as §J1 in SOURCES.md.
Check **C7 first** — there the journal itself changes (*Applied Energy* 2022 →
*Applied Thermal Engineering* 2025), so it resolves to a different paper, not a corrected suffix.

### 4. The durable fix: verification state now lives in the file

The reconcile was only necessary because **SOURCES.md recorded identifiers but no verification
state** — a checked DOI and an unchecked one were byte-identical, so the knowledge died with the
session that did the checking (§0 rule 2). `--apply` now writes an inline `*[DOI verified <date>]*`
marker on every settled line and strips the stale `(verify at cite)` hedge. **An unmarked DOI line
is an unchecked one**, and the next rewrite is reconcilable by reading rather than by archaeology.

**Also:** `scripts/audit_sources_links.py` (untracked, from an earlier attempt) assumed the verified
state lived in git rev `b9db467` — that file is 165 lines with 12 DOIs, not the 49 actually
verified, so its premise was wrong and it had never run (`normalize()` raised `NotImplementedError`).
`normalize()` is now implemented so the script at least executes, but
`reconcile_sources_dois.py` supersedes it; consider deleting it.

**Next.** Adjudicate the 14 §J1 conflicts (one lookup each, DOI *and* volume:article together),
then the 3 §J2 missing DOIs. The `apply_policy()` CHANGED branch is left unimplemented on purpose —
the trust rule is a research judgement, not a coding one.

---

## 2026-08-15 — Research lane — 14 DOI conflicts CLOSED against Crossref; §A0 Dostal 2004 restored

**Ran:** `scripts/apply_doi_conflict_resolutions.py` (new, durable), then
`scripts/reconcile_sources_dois.py` to confirm.
**Outputs:** `results/sources_doi_resolutions_20260815T121842Z.{csv,md}` (adjudication ledger),
`results/sources_doi_reconcile_20260815T122152Z.{csv,md}` (final state).

### 1. Method: ask Crossref for the paper, don't test the candidates

Each of the 14 conflicts was resolved by querying `api.crossref.org/works?query.bibliographic=`
with the paper's **title**, not by checking which candidate DOI resolves. **A DOI that resolves
only proves it points at *some* paper, not at *this* one** — and C7 below is exactly that failure
mode, so the distinction was not academic.

### 2. Outcome: the as-drafted DOI lost 14 of 14

| | count |
|---|---|
| hand-verified DOI correct | **13 / 14** |
| **neither candidate correct** | **1 / 14** (C7) |
| as-drafted DOI correct | **0 / 14** |

**The "DOI matches the printed article number" signal was backwards.** The reconcile had flagged
these because the as-drafted DOI satisfied the Elsevier identity (`Energy 300:131594` ↔
`10.1016/j.energy.2024.131594`) and the hand-verified one did not. That identity is the signature
of **fabrication, not correctness**: the DOI and the printed volume:article were invented together,
so they corroborate each other and nothing else. **The printed volume was also wrong in 12 of 14**,
so both fields were corrected in the same pass. Corrected: A6, A7, B1, B4, B5, C1, C7, C9, E3, F1,
G1, G3, H2, I7 (+ D2's volume/title completed from the same lookups).

⚠ **C7 Xian 2022 — both candidates wrong.** True record: *Applied Energy* **323**:119555,
`10.1016/j.apenergy.2022.119555`. Drafted gave 325:119921; the hand-verified copy gave
`10.1016/j.applthermaleng.2025.126209`, an *Applied Thermal Engineering* **2025** paper — a
different work. **`SOURCES - Copy.md` is therefore known-wrong at C7** and is not authoritative.

That one miss settled the open `apply_policy()` decision: **quarantine every CHANGED row.**
Auto-applying the hand-verified column would have been right 13 times and written a wrong citation
into the thesis once, silently — and a citation error costs far more than one lookup. The policy is
now implemented with this evidence in the code comment, and the `TODO(human)` is closed.

### 3. §A0 Dostal 2004 — the register was missing its most pivotal source

`SOURCES.md` had **no entry for Dostal 2004** — only passing mentions inside §A8 — despite it being
the adopted power-block baseline (`CLAUDE.md` §7 case F) and the source of every node in
`VALIDATION.md` §2.3. Added as **§A0** with: MIT-ANP-TR-100 (March 2004), free full text
`web.mit.edu/22.33/www/dostal.pdf`, DSpace `1721.1/17746`, the f_rc = 0.4097 departure and its
justification, and the ⚠ that it must not be "corrected" back to 0.39.

**Also gained a peer-reviewed companion the project did not have:** Dostal, Hejzlar & Driscoll
(2006), *Nuclear Technology* **154(3):265–282**, DOI **10.13182/nt154-265** — use where a journal
citation is required. It covers the 700 °C High-Performance design **only**; the 550/650 °C tables
and all per-node data exist solely in the 2004 report.

**Cross-ref fixed:** `VALIDATION.md` §2.1 pointed at `SOURCES.md` §A5 for Dostal. §A5 was Dostal's
slot in the original `b9db467` numbering but has since been reassigned to Stamatellos 2022, so the
reference silently pointed at an unrelated paper. Now §A0. No other stale `§A*` cross-refs found.

### 4. State

`CONFIRMED 44 · CHANGED 1 · MISSING_DOI 3 · NO_DOI 12`. The lone CHANGED is C7 and is **permanent
and correct** — SOURCES.md now holds the true DOI while the copy holds a wrong one, so the two
files are *supposed* to disagree there.

**Next.** The 3 §J2 missing DOIs (A4 Mammadov, D1 Liu & Xiao, D3 Mirahmad) — none has a DOI in
either file. A4 is a low-profile venue and may genuinely lack one. Also outstanding: §A8's three
recommended-acquisition DOIs (Padilla, Moisseytsev, Sarkar) are unverified, and the reconcile
tracks only the first, since it models one DOI per entry.

---

## 2026-08-15 — Research lane — §J2 CLOSED: the 3 missing DOIs found; SOURCES.md DOI lane finished

**Ran:** `scripts/apply_doi_conflict_resolutions.py` (batch 2 appended to the same RESOLUTIONS
table), then `scripts/reconcile_sources_dois.py` to confirm.
**Outputs:** `results/sources_doi_resolutions_20260815T122908Z.{csv,md}`,
`results/sources_doi_reconcile_20260815T122957Z.{csv,md}`.

### 1. All three found

| entry | DOI | record |
|---|---|---|
| A4 Mammadov & Kalbaliyev 2026 | `10.47390/ts-v4i5y2026n19` | *Topical Issues of Technical Sciences* 4(5), art. n19 |
| D1 Liu & Xiao 2023 | `10.1016/j.energy.2023.128732` | *Energy* 282:128732 |
| D3 Mirahmad et al. 2025 | `10.3390/nano15040302` | *Nanomaterials* 15(4):302 |

Two also needed citation corrections, because the lookups showed the recorded titles were
**paraphrases, not quotations**: D1's "MD investigation of thermophysical..." is really "Molecular
dynamics investigation of thermo-physical...", and D3 had no title recorded at all. A4 gained its
authors (Mammadov **& Kalbaliyev**) and a real title; it previously had neither.

⚠ **A4 venue caution added.** *Topical Issues of Technical Sciences* (Techscience.uz) is a
low-profile regional outlet, not indexed in the major abstracting databases. Unlike the IRJMETS
paper excluded in §J, its DOI is registered and its η = 50.7 % is thermodynamically plausible and
consistent with A0/A5/A6 — so it is **kept but explicitly discounted**: soft corroboration only,
never an anchor.

### 2. Final state — the DOI lane is closed

`CONFIRMED 44 · CHANGED 1 · MISSING_DOI 0 · NO_DOI 12`, and **zero `(verify/fetch at cite)` hedges
remain** in the file. Every source now carries a verified DOI except:

- **A0** (MIT report/dissertation) and **E2** (NREL report) — DOI-less by nature; A0 carries a
  DSpace handle plus the peer-reviewed 2006 *Nuclear Technology* companion `10.13182/nt154-265`.
- **§A8's three deferred acquisitions** (Padilla, Moisseytsev, Sarkar) — logged as new **§J3**.
  These are unverified *by design*: they have not been acquired, so they carry no marker.

### 3. Two limitations recorded rather than papered over

1. **The marker means the identifier was checked, not that the paper was read.** Every DOI is now
   confirmed against its Crossref record, but the *key numbers* in most entries still come from
   Consensus/web snippets and have not been re-read from the articles. Stated explicitly in §J so a
   later session does not over-read the marker.
2. **The reconcile models one DOI per entry**, so of §A8's three acquisition DOIs it tracks only the
   first (Padilla). Two DOIs are invisible to the CSV ledger and must be checked by reading §A8.
   Noted in §J3.

Also fixed: a cosmetic defect the marker pass introduced in **D2**, where the `(fetch at cite)`
hedge sat on a *continuation* line — stripping it left a stray `. [C]` line and a duplicated marker.

**Next.** SOURCES.md needs no further DOI work. The open research-lane item is §A8(a): re-run the
case-F method at Dostal's 550 °C and 650 °C designs, which is the falsifiable test of the f = 0.4097
finding and needs no new literature.

---

## 2026-08-15 — Research lane — Reconcile inputs retired; SOURCES.md is now the sole authority

**Deleted:** `SOURCES - Copy.md` (the hand-verified Session D copy) and — already removed by the
user — `scripts/audit_sources_links.py` (superseded, wrong premise, never ran).

**Verified safe before deleting**, not merely requested:

- **0 DOIs present only in the copy** (46 in copy vs 56 in SOURCES.md). Even C7's *wrong*
  `10.1016/j.applthermaleng.2025.126209` survives, quoted in §J1 as a documented error.
- **81 normalised lines were unique to the copy, and every one is accounted for:** DOI lines that
  differ only by the appended `*[DOI verified]*` marker; superseded citation values (`314:118689`,
  `245:111852`, `16(13):5073`, ...) that were deliberately corrected; the two Prettier corruptions
  (`deliberately \small shifts` in C9, `- TES becomes...` in H5) that were never ported; and the old
  D1/D2/D3 forms since enriched with real titles and volumes.

⚠ **`SOURCES - Copy.md` was untracked and never committed, so this deletion is not recoverable from
git.** It is safe only because of the check above; the substance it carried now lives in SOURCES.md
(the DOIs + markers), §J1/§J2 (the adjudication), and `results/sources_doi_resolutions_*.csv`.

**`scripts/reconcile_sources_dois.py` is RETIRED but kept**, because deleting its input would
otherwise leave a script that dies on a traceback — a broken artifact under §0 rule 1. It now
detects the missing input, explains that completion is the reason it is gone, points at the ledgers,
and exits 0. `--verified` still accepts any future hand-verified revision, so the tool survives for
re-use. It also remains the home of the `*[DOI verified]*` convention SOURCES.md depends on and of
the quarantine policy justified by the C7 near-miss.

`scripts/apply_doi_conflict_resolutions.py` is unaffected — it only edits SOURCES.md, and re-running
reports all 18 resolutions as ALREADY APPLIED.

**SOURCES.md is now the single authority for citations in this project.** No second copy, no
external ledger to consult first.

---

## 2026-08-15 — Code lane — ⚠ OBJECTIVES REVISED: multi-objective optimisation removed from scope

**What happened.** The supervisor removed multi-objective optimisation from the thesis (flagged as
post-graduate work) and reissued five objectives. This is a **scope instruction, not a technical
finding**; it is recorded as `DECISIONS.md` **D5** and the new objectives are `MASTER_PLAN.md` §1.

**The new objectives, in brief.** (1) T- and φ-dependent property models — ρ, cp, k, **thermal
diffusivity**, μ — **with documented provenance per correlation**. (2) The integrated CSP tower /
nano-HTF / two-tank TES / recompression sCO₂ model with energy, exergy, hydraulic and economic
assessments. (3) Decoupled validation + **Morris screening** of the ten decision variables +
**systematic parametric sweeps** of nanoparticle concentration, **particle size** and cycle
operating parameters across their **full feasible ranges**, producing **response surfaces**.
(4) The **full parametric envelope**, quantifying the net benefit of nano-enhancement vs the base
salt **as a continuous function** of the varied parameters. (5) **Robustness of those maps across
MENA and Southern African climates.**

**Nothing built was invalidated.** No result, number, baseline or validation changed. The power
block, property module, exergy layer, HTF↔SAM coupling, UDPC bridge and integrated annual run are
all *more* load-bearing under the new objectives, because the deliverable is now a dense sweep over
the model rather than a search across it. Every prior modelling decision (D1–D4) survives with only
its **purpose** re-pointed, and each now carries a dated annotation in `DECISIONS.md` saying how.

**Four consequences that create real work** — these are the entry's substance, not the edits:

1. **Objectives 4 and 5 moved from post-defence into scope.** The Objective-4 benefit envelope is a
   *difference of two surfaces*, so it needs a **φ = 0 base-salt twin at every swept point** — the
   control is half of every run, not one run at the end. Objective 5 then repeats the envelope at a
   second site. Budget roughly 4× a naive single-configuration grid.
2. **The Southern Africa (Upington) TMY became a blocker.** It was a post-defence footnote; it is
   missing from this machine and Objective 5 cannot start without it. Re-download it *before* the
   sweep grid is designed so the replication reuses the campaign instead of repeating it.
3. **`d_p` (particle size) became blocking.** It is named as a swept parameter and is represented in
   **no model layer** — every enhancement fit is anchored to Han's series at fixed particle size.
   Under the old objectives this was a defensible declared exclusion (an optimiser that never varies
   a dimension just returns a lower-dimensional answer). Under the new one it is dangerous:
   sweeping a variable the model cannot feel yields a **flat response surface**, i.e. a
   *manufactured null result* reading as "particle size does not matter". Three options are written
   up in `MASTER_PLAN.md` §10; the choice must be recorded in `DECISIONS.md` before any d_p sweep.
4. **Declared ranges now carry the weight gradients used to.** An optimiser that meets a bad bound
   simply avoids that corner; a sweep **reports across its whole declared range**, so an
   indefensible bound corrupts the published surface. Every range in the decision vector needs a
   stated basis — and the ΔT/pumping floor of `CLAUDE.md` §4.14 must be declared as a constraint of
   the study rather than left as a guard.

**Thermal diffusivity — the one gap closed this session.** Objective 1 names α explicitly. It was
already *inside* `scripts/nanofluid_properties.py` as an **input** — Han 2022's measured diffusivity
ratios are what the module's k was back-derived from — but was never an **output**. Now exposed as
`diffusivity_nf()`, **derived** as α = k/(ρ·cp) rather than independently fitted, deliberately: an
independent fit would give four correlations three degrees of freedom and let α drift out of the
identity that defines it. Han's measured ratios therefore became a **test** instead of a fit target.

**Round-trip result (500 °C, Han's own measurement temperature), and why the residual is a feature:**

| φ (wt%) | α enhancement, derived | Han measured | offset |
|---|---|---|---|
| 0.2 | +11.67 % | +10.95 % | **+0.65 %** |
| 0.7 | +20.20 % | +18.98 % | **+1.02 %** |
| 2.0 | +42.74 % | +37.23 % | **+4.01 %** |

The offset is **expected to be positive and to grow with loading**: the module uses the *volume*
fraction for density where Han's tabulated densities used the *mass* fraction — a disclosed,
deliberate divergence worth ~+0.4 % at 0.2 wt% rising to ~+3.8 % at 2.0 wt%. The remaining +0.14 %
at 2.0 wt% is the saturating k fit returning +39.75 % against Han's +39.55 %. **Nothing is
unaccounted for**, and a residual near *zero* would be the failure signal, not a success — it would
mean the density convention had silently reverted. This turns the disclosed inconsistency of
`THESIS_SYNTHESIS.md` §4.8 from an estimate into a measured number.

**What ran.**

- `scripts/nanofluid_properties.py` — α added (`diffusivity_nf`, `alpha_enhancement_han`,
  `check_diffusivity_roundtrip`, `HAN_ALPHA`); `nanofluid_properties()` now returns five properties;
  `validate()` extended with the round-trip. **`validate()` → True**, all cp and k fits unchanged.
- `scripts/report_htf_properties.py` (**new**) — the Objective-1 evidence artifact: provenance table
  per correlation, all five properties over 450–700 °C at five loadings, and the round-trip.
  → `results/htf_properties_20260815T175201Z.{md,csv}`. Exit 0.

**New tool gotcha, recorded as `CLAUDE.md` §4.16.** The first run of the new script died mid-report
with `UnicodeEncodeError: 'charmap' codec can't encode character '₂'`. Result files here are written
UTF-8 and rightly carry µ/₂/°C/—; the Windows console is **cp1252**. The common `say()` idiom — one
function that both prints a line and appends it to the report — couples the artifact's encoding to
the terminal's, and it fails *partway through*, so it reads as a logic error in whatever section
died. Fixed by transliterating on the way to the console only
(`line.encode("ascii", "replace")`), **not** by degrading the artifact to ASCII.

**Literature.** `SOURCES.md` §H rescoped rather than pruned. Added **HS1 Morris 1991**
(*Technometrics* 33(2):161–174, doi:10.1080/00401706.1991.10484804) and **HS2 Campolongo, Cariboni
& Saltelli 2007** (*Env. Modelling & Software* 22(10):1509–1518, doi:10.1016/j.envsoft.2006.10.004)
— **both verified against Crossref this session**, both canonical and previously missing while five
now-out-of-scope NSGA-II entries were present. HS2 matters practically: report **µ\***, the mean of
the *absolute* elementary effects, not µ, or effects of opposite sign cancel and hide an influential
factor. The NSGA-II entries H1–H5 are **retained and deliberately not renumbered** — the committed
`results/sources_doi_*` artifacts cite those IDs — and are relabelled as method context for the
future-work lane. §I (MENA / Southern Africa) promoted from post-defence to core scope. Tally 51 → 53.

**Files updated:** `MASTER_PLAN.md` (§1 objectives + what the revision changes, §2 critical path,
§3 decision-vector role, §7 the three-stage method, §9, §10 blockers, §11 reordered, §12),
`README.md`, `CLAUDE.md` (§0.1 new, §4.14, §4.16 new, §5, run instructions), `DECISIONS.md` (**D5**
new; D1/D3/D4 annotated), `PROPERTIES.md` (α row + why α is derived; d_p action), `VALIDATION.md`
(gate header), `THESIS_SYNTHESIS.md` (§1, §2, §10, §11, §12, §13, §14, §15, §16, §17),
`SOURCES.md`, `scripts/nanofluid_properties.py`, `scripts/htf_sam_bridge.py` (stale optimiser
wording), `scripts/report_htf_properties.py` (new).

⚠ **Earlier entries in this log were deliberately NOT rewritten.** Entries dated 2026-08-12/13
argue for case F on the grounds that "the downstream work is exergy analysis and MOO". That
reasoning was correct when written and its *conclusion* survives the rescope unchanged — a sweep
exercises off-design state points exactly as an optimiser would, in fact more visibly, since it
reports every point it visits. This file is **append-only**; the correction belongs here, not in
history.

⚠ **The repository directory is still named `moo-nehtf-sco2-brayton-cycle`.** The `moo-` prefix is
now historical. It was **not** renamed: every absolute path in `CLAUDE.md` would break, and the
rename is the user's call. Flagged in `CLAUDE.md`, `MASTER_PLAN.md` and `README.md`.

**Next.** (a) Re-download the Upington TMY. (b) Decide the `d_p` representation and record it in
`DECISIONS.md`. (c) Partition the decision vector by map-rebuild cost, then design the sweep grid
against that partition — **including the φ = 0 twins and the second site** — before launching
anything. (d) Wire the exergy layer into the integrated model *before* the campaign, since Ė_D is
one of the metrics mapped over the envelope and retrofitting it means re-running every point.

---

## 2026-08-19 — Session H — Southern Africa TMY supplied; Session G work committed

**The blocker is closed by data, not by work.** The user supplied the Southern Africa weather file
(identified as the Redstone CSP site), which had been the hard blocker on Objective 5 since the
2026-08-15 rescope. It is now `data/tmy/1292737_-28.27_23.38_tmy-2022.csv`.

**Verified before recording it as closed** — the file was inspected, not merely observed to exist:

| check | Morocco (in hand since Session D) | Southern Africa (new) |
|---|---|---|
| source / version | NSRDB v4.0.1 | NSRDB **v4.0.1 — same** |
| location id | 158192 | 1292737 |
| lat, lon | 31.05, −6.86 | **−28.27, 23.38** |
| elevation | 1260 m | **1590 m** |
| time zone | **UTC+0** | **UTC+2** |
| data rows | 8760 | **8760** |
| column layout | 28 fields | **identical, same order** |

Two things follow. (1) **The site is the one that was specified, not a substitute** — §10 named
lat −28.29, lon 23.37, and the supplied cell is **0.02° (~2.4 km)** away, the same NSRDB
neighbourhood. (2) **Both sites read through one code path**, since format, version, column set and
row count all match, so the Objective-5 replication needs no per-site branching.

⚠ **The one real difference is the timezone (+0 vs +2).** SAM reads the offset from the file header
so no handling is required — but a hard-coded timezone anywhere, or any raw hour-by-hour comparison
between the two sites that does not first align on solar time, would be silently wrong. Annual and
monthly aggregates, which is what the envelope reports, are unaffected. Recorded in `CLAUDE.md` §5.

`data/tmy/` is gitignored, so the file itself is **not committed** — same status as the Morocco
file. It is on disk for every session on this machine; a fresh machine re-downloads both.

**Session G's work is now committed and pushed.** It had been left entirely in the working tree:
`scripts/nanofluid_properties.py` (the α addition), `scripts/report_htf_properties.py` (new), the
`results/htf_properties_*` and `results/dostal_*` artifacts, and the Session G log entry itself.
Only the *documentation* realignment had been committed (`512608d`), and even that was unpushed —
`origin/main` was two sessions behind.

**Re-verified before committing rather than trusting the log:**

- `scripts/nanofluid_properties.py` → `validate()` **passed**; the α round-trip reproduces
  +11.67 / +20.20 / +42.74 % against Han's +10.95 / +18.98 / +37.23 % exactly as logged.
- `scripts/report_htf_properties.py` → exit 0, and its output is **byte-identical** to the
  2026-08-15 CSV; the .md differs only in the timestamp and commit stamp. The duplicate re-run was
  deleted rather than committed — the 2026-08-15 pair is the one `PROGRESS_LOG` references.

**Knowledge files updated for the TMY** — the blocker was asserted in six files, and leaving them
would have published a stale blocker: `CLAUDE.md` (§0.1 now names **one** remaining blocker, §5
rewritten as a two-site table with the timezone caveat), `MASTER_PLAN.md` (§2 diagram, §7 Stage 3,
§10 item closed, §11 item 3), `DECISIONS.md` (D5 consequence 4 annotated — **kept, not deleted**,
because the lesson stands for `d_p`), `SOURCES.md` (§I preamble), `THESIS_SYNTHESIS.md`
(Objective-5 status row, §gap 21, next-steps, scope-completion list).

**`d_p` is now the only blocker on the critical path.** Its three options are unchanged
(`MASTER_PLAN.md` §10) and the choice still has to be recorded in `DECISIONS.md` before any
particle-size sweep. One thing worth noting for whoever takes it: **`SOURCES.md` B1 (Han 2022),
which every enhancement fit is anchored to, does not record a particle size in its extracted key
numbers.** Option (a) — an analogue-grounded size correction from Wei/B5 — needs a reference
diameter to anchor the correction *at*, so that number must be pulled from the paper before (a) can
be specified, not during implementation.

⚠ **Naming hazard found while reading the module, not fixed here.** `scripts/nanofluid_properties.py`
uses its own local source labels that **collide with `SOURCES.md`'s IDs and mean different papers**:
the module calls Han 2022 **"B3"** (line 50) and Shin & Banerjee **"B1"** (line 52), whereas in
`SOURCES.md` **B1 is Han 2022** and **B3 is Wang et al. 2023**. The module states the DOI next to
its labels so it is internally unambiguous and **no number is affected**, but a cross-reference read
in either direction lands on the wrong paper. Left alone deliberately — a rename touches ~20
comment sites in a validated module and belongs in its own commit, not one about weather data.

**Next.** Unchanged except that (a) is done. (b) Decide the `d_p` representation and record it in
`DECISIONS.md` — pull Han's particle size first. (c) Partition the decision vector by map-rebuild
cost, then design the sweep grid — **now with both sites in view**, so the Objective-5 replication
reuses the campaign. (d) Wire the exergy layer into the integrated model before the campaign starts.

---

## 2026-08-19 — Session H (continued): the `d_p` representation, decided and built

**Task.** Pull Han's particle size, run the timeboxed option-(b) search, take the decision, build
it, and reconcile the module's source labels with `SOURCES.md`. All five done. A `TODO.md` was
added at the user's request as the live cross-session checklist (distinct from this append-only
log and from `MASTER_PLAN.md` §11's strategic path).

**1. Han's particle size: NOT RECOVERABLE.** Searched ScienceDirect (403, paywalled), OpenAlex
(`is_oa: false`, no repository full text), Semantic Scholar (abstract carries no size), Academia.edu
(403), and three reviews that tabulate the study — **none records the diameter**. This is a real
finding, not a failed errand: it makes `MASTER_PLAN.md` §10 **option (a) unimplementable**, because
an anchored size correction must be normalised so *f*(d_ref) = 1 at Han's own diameter and there is
no d_ref to anchor at. Recovered instead, and worth having: Han's base-salt composition is
**NaCl–KCl–MgCl₂ = 19.59 / 20.33 / 60.08 wt%**.

**2. Option (b) search: NULL, and something better.** No study varies particle size for CuO in any
chloride eutectic — consistent with `SOURCES.md` C0's headline about this corner of the literature.
But the search surfaced **Tiznobaik & Shin 2013** (IJHMT 57:542–548, doi:10.1016/j.ijheatmasstransfer.2012.10.062,
verified via Crossref; now `SOURCES.md` **B6**): **5 / 10 / 30 / 60 nm** SiO₂ at 1 wt% in a binary
carbonate eutectic, giving cp enhancements of **24 / 26 / 23 / 26 %**. That is **no trend across a
12× diameter range**, independently confirmed against a PMC open-access review and a second search.

**3. This refutes the mechanism I had recommended the previous turn.** Specific surface area scales
as 6/(ρ_p·d_p), so an interfacial-layer mechanism predicts enhancement ∝ 1/d_p — a 12× swing over
exactly the range B6 measured flat. Shin's own group later attributed the enhancement to a
**percolating salt nanostructure** whose length scale is set by the salt's self-assembly rather than
the particle (`Appl. Phys. Lett.` 104 (2014); `IJHMT` 91:342–346 (2015)), which makes
size-independence the *expected* result. **The surface-area argument is superseded by the same
authors who originated the mechanism it rests on.** Recorded because the tempting move — build the
1/d_p law anyway — is the one the evidence forbids.

**4. Decision: `DECISIONS.md` D6 — option (c), selected by evidence, not taken as a fallback.**
`d_p` is now a first-class, validated, **range-guarded** input whose **nominal effect is declared
zero** over **5–60 nm**, carrying a **6.1 %** size-transfer uncertainty (`E_DP_REL_UNC`, taken from
B6's own measured scatter). Out-of-band raises, mirroring the ≤ 2.0 wt% loading guard. `d_p = None`
means "Han's fluid at Han's own diameter" and carries no penalty — which is also the backward
compatibility path. **The two dead ends resolve each other:** a size *correction* needs an anchor and
Han's diameter is unrecoverable; a declared *invariance* needs no anchor at all.

**5. Built in `scripts/nanofluid_properties.py`**, with four assertions added to `validate()`:
d_p=None reproduces pre-D6 bit-for-bit · nominal invariant 5→60 nm · band widens when a diameter is
asserted · out-of-band raises. **All pass.** `scripts/report_htf_properties.py` gained §4, an audit
table (identical nominals, wider bands) so the flat surface can be checked without reading code.

**Regression evidence.** `results/htf_properties_20260819T111927Z.csv` is **byte-identical** to the
2026-08-15 baseline, and `results/sam_htf_table_0p7wt.csv` is unchanged in git. **D6 changed no
number** — it added a guard, a named uncertainty and a citation.

⚠ **The honest magnitude caveat, recorded so nobody over-claims it.** 6.1 % in quadrature with the
existing ±50 % (cp) and ±35 % (k) enhancement-transfer bands widens the cp band by only **~0.43 %**.
Particle size is **not** a material contributor to the uncertainty envelope. What D6 buys is that a
flat d_p surface is a transcribed measurement with a citation and a validity range — a **reported
null, not a manufactured one** — not that the band moved.

⚠ **Two weaknesses stated in D6 rather than hidden.** (i) The evidence is **not unanimous**: B5 (MgO
in a different ternary chloride) reports cp *falling* with larger particle size — direction only, no
transferable magnitude. (ii) **k is the weaker half**: B6 measured *specific heat*, and no
molten-salt study resolves *thermal conductivity* against diameter at all, so k's size-invariance is
an extension rather than a transcription. Flagged in `conductivity_nf()`'s docstring.

**6. Source labels reconciled — the collision was worse than last session's note said.** The module
used **three** local labels that resolved to the wrong papers in `SOURCES.md`: Han as "B3"
(`SOURCES.md` B3 = Wang 2023), Shin & Banerjee as "B1" (B1 = Han 2022), and — not previously
spotted — **the base salt as "A1", where `SOURCES.md` A1 is Dyreby's sCO₂ cycle paper**, an entirely
unrelated work. All renamed to resolving IDs (B0 / B1 / D4) across
`nanofluid_properties.py`, `report_htf_properties.py` and `htf_sam_bridge.py`. No number changed;
the DOIs beside each label were always correct.

**7. A genuine documentation gap this exposed.** The base-salt property paper — the source of
**every φ = 0 number in the project** — had **no `SOURCES.md` entry at all**, so it was the one
pivotal source the §J1 Crossref sweep never checked. Added as **B0**: Wang, Rincon, Li, Zhao &
Vidal (2021), *J. Solar Energy Engineering* 143(4):041005, **doi:10.1115/1.4049253, verified via
Crossref**. It was also mis-attributed as "Xu/Wang 2021" in `PROPERTIES.md` and both property
scripts — **there is no Xu on the author list**; Xu is a different base-salt MD source (C3/C4).
Corrected in the live files; pre-2026-08-19 `results/` artifacts keep the old attribution, being
timestamped records.

**Knowledge files updated:** `CLAUDE.md` (§0.1 — **no blockers remain**, plus an explicit warning
that a flat d_p surface is intended and must not be "fixed"), `MASTER_PLAN.md` (header, §2 diagram,
§1.1 table, §3 sweep-parameter table, §10 item closed, §11 item 3), `DECISIONS.md` (**D6 added**,
D5 consequence 3 annotated, summary table), `SOURCES.md` (**B0 and B6 added**), `PROPERTIES.md`
(particle-size position, base-salt attribution), `THESIS_SYNTHESIS.md` (decision-variable table,
the gap note rewritten as a viva-facing answer, four status rows), `TODO.md` (new).

**Next.** No representation blockers remain; the binding constraint is compute budget and grid
design. (a) Partition the decision vector by map-rebuild cost — cycle variables force a ~35 min UDPC
rebuild, SM and t_TES do not. (b) Wire the exergy layer into the integrated model *before* the
campaign, or it must be re-run to collect Ė_D. (c) Run the Morris screening. (d) Design the sweep
grid with **both TMY sites in view**, a φ = 0 control at every point, a declared T_hot floor — and
**d_p at low density**, since D6 establishes it as a known null dimension in the nominal, so the run
budget belongs on φ and the cycle variables.
