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
