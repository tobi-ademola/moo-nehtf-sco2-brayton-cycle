# MASTER PLAN — Nano-Enhanced HTF + sCO₂ Brayton CSP Thesis Sprint

> **Purpose of this file.** Single source of truth for the whole project. Written so any
> fresh Claude chat, Claude Code session, or a brand-new account can pick up the work
> **cold** by reading only this file plus the linked knowledge-base entries. Keep it
> current. If you update nothing else, update this.

**Last updated:** 2026-08-13 — Session E. **Power-block validation gate PASSED** (see §2, §6).
Critical path now runs through the **integrated model** (§11), which is not yet built. Validation
hardening is explicitly **deferred** to §12 so it stops competing with the sprint deliverable.
**Owner:** (you)
**Deadline horizon:** ~33 working hours from first session
**Thesis topic:** Multi-objective optimization of nano-enhanced HTFs integrated with an sCO₂ Brayton cycle

---

## 0. HOW TO USE THIS FILE (read first if you are a new session)

- This project runs across **many short chat/Code sessions** to conserve tokens.
- **Two lanes:**
  - **Claude Code** = build/run/debug the PySAM pipeline against a real SAM install. All version-specific reconciliation lives there.
  - **Claude chat (web)** = research, literature verification, modeling-decision debates, thesis writing, diagrams.
- Every session **ends** by writing its findings into the knowledge base (see §8) in a form that can be pasted into project knowledge for the next session.
- Research is done via **Consensus** first; **web search** is the documented fallback for pivotal items Consensus misses or when it's unavailable. Log every pivotal source in `SOURCES.md`.

---

## 1. OBJECTIVES (from supervisor)

1. Temperature- and concentration-dependent thermophysical models of the nano-enhanced molten-salt HTF.
2. Integrated CSP–nano-HTF–TES–sCO₂ Brayton model + energy, exergy, hydraulic, economic assessment.
3. Multi-objective optimization of nanoparticle concentration, particle size, and cycle operating params for: max energy efficiency, min cost, min pumping power, max TES energy density, min exergy destruction.
4. _(Post-defense)_ Pareto-optimal envelope + net benefit of nano-enhancement vs conventional salt.
5. _(Post-defense)_ Robustness of Pareto-optimal config across climates (MENA + Southern Africa).

**Sprint scope = Objectives 2 and 3 (core). Objective 1 largely reused from prior work. Objectives 4–5 are post-defense.**

---

## 2. CRITICAL PATH (what must happen, in order)

```
[Obj1 properties ready]  ->  [Model built in PySAM]  ->  [VALIDATION passes]  ->  [Parametric screening]  ->  [ (stretch) full MOO ]
        |                            |                          |                        |
   mostly done (prior work)     PARTLY DONE              POWER BLOCK: PASSED         NOT STARTED
                               power block yes,          field/TES: baseline run     <-- GUARANTEED
                               INTEGRATION no            (GUI check blocked, and     DELIVERABLE
                                    ^                     not required)
                                    |
                          *** THE CRITICAL PATH IS HERE NOW *** (§11)
```

**Gate status, 2026-08-13.** The power-block gate is **PASSED**: the sCO₂ recompression cycle
reproduces every node of Dostal (2004) Table 10.4 to within 0.070 % in *h* and η to +0.019 pp
(`VALIDATION.md` §2.3.4/§2.3.4a). **A gate is binary — it is passed, and further validation work
does not make it "more passed."** Everything still open in the validation lane is defensive depth
for the viva, not permission to proceed; it is parked in **§12** with an explicit restart trigger.

> **The binding constraint is no longer model credibility, it is model COVERAGE.** The integrated
> CSP–HTF–TES–sCO₂ model of Objective 2 does not exist yet, and the screening that is the
> *guaranteed deliverable* runs on top of it. Time spent on a second literature anchor is time not
> spent building the thing the deliverable depends on.

**Guaranteed deliverable:** validated model + parametric screening identifying the most impactful decision variables.
**Stretch deliverable:** full multi-objective optimization (NSGA-II/NSGA-III) over the pruned/full decision vector.
**Novelty booster (optional):** component-level exergy analysis (see §5).

---

## 3. DECISION VARIABLES (from supervisor's attached sheet)

Decision vector **X = [SM, tTES, φ, dp, THTF, ṁHTF, Tt,in, PH, PR, fRC]**

| #   | Category  | Variable                   | Symbol |
| --- | --------- | -------------------------- | ------ |
| 1   | Solar/TES | Solar multiple             | SM     |
| 2   | Solar/TES | TES duration (h)           | tTES   |
| 3   | Nano-HTF  | Nanoparticle concentration | φ      |
| 4   | Nano-HTF  | Nanoparticle diameter      | dp     |
| 5   | Nano-HTF  | HTF operating temperature  | THTF   |
| 6   | Nano-HTF  | HTF mass flow rate         | ṁHTF   |
| 7   | sCO₂      | Turbine inlet temperature  | Tt,in  |
| 8   | sCO₂      | High-side pressure         | PH     |
| 9   | sCO₂      | Pressure ratio             | PR     |
| 10  | sCO₂      | Recompression fraction     | fRC    |

**Primary objectives:** max ηex, max ρTES; min LCOE, min Wpump, min ĖD.
**Constraints / indicators:** ΔPHTF ≤ max; THTF ≤ salt/material limit; Wnet ≥ min; Qloss,TES, Eannual, Q̇HTF–sCO₂ reported.

---

## 4. MATERIAL / MODEL CHOICES (current working decisions)

- **Base eutectic + nanoparticle:** **NaCl–KCl–MgCl₂ + CuO** (reused from prior work).
  - Have: base eutectic characterization + enhanced at **3 loadings**. Property module approximating properties vs T and loading exists.
  - Viscosity was **not reported** → **filled via MD**. ⚠️ Needs a defensible provenance sentence in thesis + entry in SOURCES.md.
  - Rationale: chloride eutectic reaches ~700–800 °C, matching sCO₂ recompression's preferred hot-end. Defensible on merits.
- ⚠️ **OPEN FLAG — salt/SAM reconciliation:** SAM's molten-salt tower defaults to solar **nitrate** salt (60/40 NaNO₃/KNO₃, ~565 °C ceiling). Chloride is corrosive and hotter. **Working approach:** run SAM solar field/TES on its native salt for validation; apply nano-chloride properties in the HTF→sCO₂ heat-transfer + hydraulic layer. **Confirm with Claude Code whether SAM lets you override salt props or whether the power-block coupling must be external.**

---

## 5. EXERGY DECISION (currently: LEAN KEEP, gated on one check)

- The supervisor's attached paper (Atif & Al-Sulaiman 2018, _J. Energy Eng._) is effectively an **exergy template** for this exact topology: recompression sCO₂ + two-tank molten salt + central receiver. It gives component-level exergy-destruction equations (compressor ×2, turbine, HTR, LTR, cooler, storage HX, hot/cold tanks; Eqs. 41–56).
- Therefore the **algebra is mostly transcription**, not derivation → the "too complex" risk is lower than it looks.
- ✅ ~~**THE REAL RISK:** does PySAM's sCO₂ model expose **per-state entropy**?~~ **RISK CLOSED
  2026-08-13.** Entropy is exposed natively (Session B), *and* a full exergy layer has now been
  built and verified on it (Session E, `scripts/exergy_layer_check.py`): per-node exergy, per
  component ĖD all positive, **HTR-dominant at 41.4 %**, and the cycle-wide balance
  Ex_in = W_net + ΣĖD closing to **1.5e-04 relative**. The **CoolProp reconstruction (+~1 day) is
  not needed.** ⚠ Report ĖD at **T_amb = 299.15 K**, not at the node-1 reference — see
  `DECISIONS.md` D1.
- **Working rule:** build the model **exergy-ready** — carry **h AND s at every state point** from the start. Switch on the exergy _reporting layer_ last. This keeps novelty open without gating the critical path.
- **Fallback:** if the entropy-exposure check fails and CoolProp reconstruction eats the buffer, exclude exergy (supervisor-approved) and keep energy/hydraulic/economic.

---

## 6. VALIDATION STRATEGY (decoupled — the defensible approach)

Do **not** try to validate the whole integrated plant against one paper (few report enough).

- **Power block — DONE.** Validated against **Dostal 2004** (MIT-ANP-TR-100) Table 10.4, which
  publishes full node state tables — the Turchi 2009 / Chacartegui 2011 candidates named here
  originally were superseded because neither gives per-node *h* and *s*. Result: all 8 nodes within
  0.070 % in *h*, η +0.019 pp, plus the 2 untabulated junction nodes validated by conservation.
  `VALIDATION.md` §2.3.4, §2.3.4a, §2.3.3a-R.
- **Solar field / TES — baseline run, sufficient.** `MSPTSingleOwner` + Daggett TMY executed
  (`VALIDATION.md` §1.3) and pinned as a regression baseline. The SAM **GUI** cross-check (§1.4) is
  blocked — no SAM install on this machine (`CLAUDE.md` §1.0a) — and is **not on the critical path**:
  the GUI and PySAM run the *same* ssc 306, so the comparison tests packaging, not physics.
- Both documented in `VALIDATION.md` with % error tables.

---

## 7. METHOD FOR "WHICH VARIABLES MATTER" (screening)

- Primary recommendation: **Morris elementary-effects screening** — textbook method for factor screening, cheap in model evaluations, gives ranking + interaction flag. Ideal time-to-insight tool for 10 variables.
- If time allows: small **Sobol** variance-based sensitivity for the survivors.
- Output: ranked impact of each of the 10 variables → justifies either pruning the decision vector or running full MOO.
- Full MOO (stretch): **NSGA-II/III** (via `pymoo`) over 5 objectives. Risky to converge + validate in 33h → stretch only.

---

## 8. MIGRATION / CONTINUITY SYSTEM (fail-safe)

**Files that constitute the portable project (keep all in project knowledge + a synced folder):**

| File              | Contents                                                                                   | Updated by               |
| ----------------- | ------------------------------------------------------------------------------------------ | ------------------------ |
| `MASTER_PLAN.md`  | _this file_ — single source of truth                                                       | every session, as needed |
| `CLAUDE.md`       | Claude Code operating instructions, env details, SAM/PySAM versions, run commands, gotchas | Code sessions            |
| `PROGRESS_LOG.md` | dated append-only log: what each session did, what's next                                  | every session            |
| `SOURCES.md`      | every pivotal source: citation, DOI, tool (Consensus/web), key numbers extracted           | research sessions        |
| `VALIDATION.md`   | validation targets, state points, % error tables                                           | Code + research          |
| `PROPERTIES.md`   | nano-HTF property correlations, coefficients, provenance (incl. MD viscosity note)         | Obj1 session             |
| `DECISIONS.md`    | modeling-decision debates + resolutions (exergy, salt reconciliation, etc.)                | debate sessions          |

**Rules for portability:**

- No finding lives only in a chat transcript. Every session ends by emitting a paste-ready block for the relevant file above.
- Keep entries **atomic and self-contained** (a new reader has zero context).
- If this account maxes out: the 7 files above + the SAM install + PySAM scripts = complete handoff. Nothing else required.

---

## 9. SESSIONS COMPLETED

- [x] **Session A** — modeling-decision debate. ⚠ `DECISIONS.md` is listed in §8 but **does not
      exist in the repo**; either it was never written or it lives only in chat. Recreate it if
      any decision here needs to be defended.
- [x] **Session B (Code)** — continuity scaffold + env capture → `CLAUDE.md`, `VALIDATION.md` seed.
      **Confirmed PySAM exposes T, P, h AND s at every cycle node** → exergy is viable (§5 resolved).
- [x] **Session C (research + Code)** — literature pass → `SOURCES.md`, `PROPERTIES.md`;
      Dostal 2004 selected as the power-block anchor; first validation run.
- [x] **Session D (docs)** — machine migration, stale-path cleanup, Morocco MENA TMY added.
- [x] **Session E (Code)** — env rebuilt from scratch; node-by-node error table; junction
      conservation checks; **case F adopted as the validated baseline**; second-anchor assessment
      (`SOURCES.md` §A8). **Power-block gate PASSED.**

---

## 10. OPEN QUESTIONS / RISKS (live list)

- [x] ~~Does PySAM expose per-state entropy?~~ **YES** — T, P, h, s at all 10 real nodes
      (Session B). Exergy layer is viable; §5's fallback is not needed.
- [x] ~~Which published sCO₂ case has enough reported state points?~~ **Dostal 2004**, Tables
      10.2–10.4 (Session C); validated to 0.07 %/node (Session E).
- [x] ~~**Can SAM override molten-salt properties, or must the nano-chloride HTF couple
      externally?**~~ **ANSWERED 2026-08-13 — IT COUPLES INSIDE SAM.** `rec_htf = 50` accepts the
      nano-chloride table across 450–700 °C, stores it with **zero** round-trip deviation across
      six cases, and the annual model solves on it (`scripts/htf_sam_bridge.py`,
      `results/htf_sam_bridge_*`). No external coupling layer needed; `DECISIONS.md` D2's
      mechanism confirmed. ⚠ But **acceptance is not validity** — see the new risk below.
- [ ] ⚠ **NEW — the chloride's melting point is a hard constraint, not a preference.** It melts
      at 401.4 °C, so the cold tank cannot approach nitrate's 290 °C. The resulting narrow loop
      ΔT drives receiver pump power roughly as ΔT⁻³: **124 K → 162 MW (negative nameplate,
      infeasible)**, 250 K → 27.0 MW, 284 K → 8.5 MW. **The optimizer must be given a floor under
      T_hot, not left to discover it** — this binds decision variables #5 and #6 together.
      ssc reports no error on the infeasible design, so **screen every run on
      `system_capacity > 0`** (`CLAUDE.md` §4.14).
- [ ] ⚠ **NEW — the UDPC off-design sweep does not converge at the case F design.** It completes
      only when the cycle is left loose enough to **collapse to `recomp_frac = 0`** (§4.3). This
      blocks §11 item 2. Ruled out already: the custom fluid, pinned f_rc, pinned pressures,
      `rel_tol`. Remaining suspects: `design_method = 3`, and the min-approach-dT recuperator
      spec held across off-design. See `scripts/build_udpc_map.py`.
- [ ] MD-viscosity provenance sentence for the thesis — **research/writing**, not blocking.
      (`SOURCES.md` §C0 already reframes this from weakness to field convention.)
- [ ] Location set for Obj5 — Morocco TMY in hand, Southern Africa file needs re-downloading.
      **Post-defense scope; not blocking.**

---

## 11. CRITICAL PATH FROM HERE (the only list that matters right now)

Ordered. Each item blocks the ones below it. **Nothing in §12 competes with these.**

1. ~~**Salt/SAM reconciliation**~~ — ✅ **DONE 2026-08-13, `scripts/htf_sam_bridge.py`.** The HTF
   couples **inside** SAM: `rec_htf = 50` accepts the nano-chloride table across 450–700 °C with
   zero round-trip deviation and the annual model solves. Two constraints came with the answer
   and are now live risks in §10: the melting-point/ΔT/pumping floor, and the fact that ssc
   reports no error on a **negative nameplate**.
2. **Build the integrated model** — `Sco2CspUdPcTables` → `TcsmoltenSalt` via `pc_config = 1` +
   `ud_is_sco2_regr = 1` (`CLAUDE.md` §3). This is **Objective 2**. ⏳ **PARTIAL —
   `scripts/build_udpc_map.py`. THE CRITICAL PATH IS HERE.**
   - ✅ Design point solves at the case F cycle on the nano-chloride (f_rc 0.4097 held, η 0.50547,
     −0.742 pp vs case F — the cost of TIT 680 °C instead of 700 °C, which keeps the chloride
     inside its stated validity).
   - ✅ The 13-col→7-col inverse-split transform is **proven** by `--selftest`, independently of
     ssc (`CLAUDE.md` §4.11).
   - ❌ **The off-design sweep does not converge** — it completes only in configurations that
     collapse the recompression cycle to `recomp_frac = 0`. **This is the single thing blocking
     the guaranteed deliverable.** **Seven** single-variable deviations from case F have now been
     tested and all are negative (fluid, f_rc pinning, pressure pinning, `rel_tol`, recuperator
     code 3, `design_method` 1 and 2, sweep corners) — so it is **not one bad setting**: a fully
     determined case-F-style design is over-constrained for UDPC generation. **Next move: bisect
     the other way** — start from the loose bundle that converges in 93.6 s and re-tighten toward
     case F until it breaks. If the boundary excludes a pinned f_rc, that is a modelling decision
     for `DECISIONS.md`, not a bug.
3. **Wire the decision vector** — expose all 10 variables of §3 as model inputs with validated
   ranges, so screening can drive them.
4. **Morris screening** (§7) over the 10 variables. ← **THE GUARANTEED DELIVERABLE.**
5. **Exergy reporting layer** (§5) — **de-risked ahead of time**: the arithmetic is already
   verified end-to-end by `scripts/exergy_layer_check.py` on the standalone cycle. What remains is
   wiring it to the *integrated* model and adding the receiver/TES/tank ĖD terms, not proving the
   method. Still build it last.
6. **NSGA-II MOO** (§7) — stretch only.

---

## 12. DEFERRED BACKLOG — validation hardening (do NOT start before §11 item 4 is done)

Parked deliberately on 2026-08-13. Each item is **defensive depth for the viva, not a modelling
risk**, and the power-block gate has already passed without them.

**Restart trigger: after Morris screening (§11 item 4) is delivered.** At that point the guaranteed
deliverable is banked, and these become cheap thesis-chapter reinforcement. Pick up in this order:

1. **Dostal 550 °C + 650 °C node tables** (Tables 10.2/10.3, already transcribed in
   `VALIDATION.md` §2.3.2). **Cheapest and highest value — no new literature, scripts already
   exist.** Two of the ten decision variables (T_t,in and f_RC) get swept by the optimizer while
   the model is validated at only one point in that space; this covers a 150 °C span. It also
   doubles as a falsifiable test of the f = 0.4097 finding (`SOURCES.md` §A8).
2. **Battisti 2023 exergy cross-check** — confirm HTR-dominant exergy destruction against
   `SOURCES.md` F2. **Do this when the §11 item 5 exergy layer exists**, not before; it costs
   almost nothing once the layer is built.
3. **Independent node-level anchor** — acquire Padilla 2015 / Moisseytsev & Sienicki 2009 /
   Sarkar 2009 (`SOURCES.md` §A8). **Highest cost, lowest marginal return.** Only worth it if the
   viva specifically presses on single-source dependence. **Do not acquire PDFs before then.**
4. **SAM GUI cross-check** (`VALIDATION.md` §1.4) — blocked on a SAM install, and tests packaging
   rather than physics since GUI and PySAM share ssc 306. Lowest priority of all.
