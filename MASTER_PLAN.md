# MASTER PLAN — Nano-Enhanced HTF + sCO₂ Brayton CSP Thesis Sprint

> **Purpose of this file.** Single source of truth for the whole project. Written so any
> fresh Claude chat, Claude Code session, or a brand-new account can pick up the work
> **cold** by reading only this file plus the linked knowledge-base entries. Keep it
> current. If you update nothing else, update this.

**Last updated:** 2026-08-19 — Session H. **§10 is now clear: `d_p` closed as `DECISIONS.md` D6**
(declared size-invariance over an evidenced 5–60 nm band), following the Southern Africa TMY
closure earlier the same day. No representation blockers remain; the binding constraint is compute
budget and grid design (§2).
Previously 2026-08-15 — Session G. ⚠ **OBJECTIVES REVISED BY THE SUPERVISOR — multi-objective
optimisation is REMOVED from scope** (flagged as post-graduate work). The new five objectives are in
§1; what the change does to the critical path is in §2 and §11; the decision itself is recorded as
`DECISIONS.md` **D5**. Everything already built and validated survives the change unaltered — only
the terminal deliverable moves.
**Owner:** (you)
**Deadline horizon:** ~33 working hours from first session
**Thesis topic:** Parametric performance assessment of a CuO-enhanced NaCl–KCl–MgCl₂ heat transfer
fluid integrated with a recompression sCO₂ Brayton cycle for CSP

> ⚠ **Repository name is legacy.** The folder is still `moo-nehtf-sco2-brayton-cycle`; the `moo-`
> prefix stood for *multi-objective optimisation*, which is no longer in scope. Renaming the
> directory would invalidate every absolute path in `CLAUDE.md` and is deliberately **not** done
> here — treat the name as historical, not descriptive.

---

## 0. HOW TO USE THIS FILE (read first if you are a new session)

- This project runs across **many short chat/Code sessions** to conserve tokens.
- **Two lanes:**
  - **Claude Code** = build/run/debug the PySAM pipeline against a real SAM install. All version-specific reconciliation lives there.
  - **Claude chat (web)** = research, literature verification, modeling-decision debates, thesis writing, diagrams.
- Every session **ends** by writing its findings into the knowledge base (see §8) in a form that can be pasted into project knowledge for the next session.
- Research is done via **Consensus** first; **web search** is the documented fallback for pivotal items Consensus misses or when it's unavailable. Log every pivotal source in `SOURCES.md`.

---

## 1. OBJECTIVES (from supervisor — REVISED 2026-08-15)

**These five supersede the previous set in full.** Multi-objective optimisation was removed by the
supervisor as post-graduate work. Objectives 4 and 5 are **no longer post-defence** — they are
in-scope deliverables, which is the single biggest consequence of the revision.

1. Develop **temperature- and concentration-dependent thermophysical property models** — density,
   specific heat, thermal conductivity, **thermal diffusivity**, and viscosity — for the
   CuO-enhanced NaCl–KCl–MgCl₂ heat transfer fluid, **with documented provenance for each
   correlation**.
2. Construct an **integrated model** of the CSP tower, the nano-enhanced HTF, the two-tank
   molten-salt storage, and the recompression sCO₂ Brayton cycle, and equip it with **energy,
   exergy, hydraulic, and economic** assessments.
3. **Validate** the integrated model by a **decoupled strategy**, **screen the ten decision
   variables** for their influence using the **Morris elementary-effects** method, and perform
   **systematic parametric sweeps** of nanoparticle concentration, particle size, and cycle
   operating parameters **across their full feasible ranges** to generate comprehensive
   **performance response surfaces**.
4. Construct the **full parametric performance envelope** from these sweeps and quantify, **as a
   continuous function of the varied parameters**, the **net benefit of nano-enhancement relative
   to the conventional base salt** across that envelope.
5. Assess the **robustness of the parametric performance maps across contrasting climates**,
   spanning sites in the **MENA** region and in **Southern Africa**.

### 1.1 What the revision changes (and what it does not)

| | Before | Now |
|---|---|---|
| Terminal deliverable | NSGA-II Pareto front (stretch) | **Parametric response surfaces + benefit envelope + climate robustness** (Obj 3–5, all core) |
| Role of Morris screening | prune the decision vector *for the optimiser* | **justify which axes the sweeps resolve finely and which are held**; a reported result in its own right |
| Obj 4 / Obj 5 | post-defence | **in scope, on the critical path** |
| Nano-vs-base comparison | one Pareto-front comparison at the end | **a continuous function over the whole swept envelope** — needs a base-salt (φ = 0) control run at *every* sweep point |
| Particle size `d_p` | a decision variable the optimiser might have pruned | **explicitly named as a swept parameter** — no longer optional. ✅ Represented 2026-08-19 as a declared size-invariance (`DECISIONS.md` D6, §10) |
| Thermal diffusivity α | implicit inside the k derivation | **explicitly named as a required property model** (§10) |
| Everything validated so far | — | **unchanged.** No result, script, or baseline is invalidated. |

**Nothing built is discarded.** The validated power block, the property module, the exergy layer,
the HTF↔SAM coupling, the UDPC bridge and the integrated annual run are all *more* load-bearing
under the new objectives than under the old, because the deliverable is now a dense sweep over the
model rather than a search across it.

---

## 2. CRITICAL PATH (what must happen, in order)

```
[Obj1 properties]  ->  [Obj2 integrated model]  ->  [Obj3 validate + Morris]  ->  [Obj3 parametric sweeps]
        |                       |                            |                             |
  DONE - alpha & d_p       DELIVERED (annual              POWER BLOCK: PASSED          NOT STARTED
  both closed (§10)        result in hand, §11)          field/TES: baseline run       <-- now the
                                                          (GUI check blocked,           critical path
                                                           not required)                     |
                                                                                             v
                                             [Obj5 climate robustness]  <-  [Obj4 benefit envelope]
                                                        |                            |
                                              NOT STARTED - both TMYs      NOT STARTED - needs a
                                              now in hand (2026-08-19),    phi=0 control at EVERY
                                              unblocked on data            swept point
```

**Gate status, 2026-08-13.** The power-block gate is **PASSED**: the sCO₂ recompression cycle
reproduces every node of Dostal (2004) Table 10.4 to within 0.070 % in *h* and η to +0.019 pp
(`VALIDATION.md` §2.3.4/§2.3.4a). **A gate is binary — it is passed, and further validation work
does not make it "more passed."** Everything still open in the validation lane is defensive depth
for the viva, not permission to proceed; it is parked in **§12** with an explicit restart trigger.

> **The binding constraint has moved twice.** It was model *credibility* (closed by the gate), then
> model *coverage* — the integrated model, which now exists and returns an annual result (§11
> item 2). Under the revised objectives it is **compute budget**. The deliverable is a dense sweep
> paired with a φ = 0 control at every point, over a model whose cycle-touching rebuilds cost
> ~35 min each (`CLAUDE.md` §4.15). Nothing else on the list competes with getting that grid
> designed and costed before it is launched.

**Guaranteed deliverable:** validated integrated model + Morris screening of the ten decision
variables + parametric response surfaces over φ, d_p and the cycle operating parameters.
**Full deliverable (Obj 4–5, now in scope):** the benefit-of-nano-enhancement envelope as a
continuous function of the swept parameters, replicated across a MENA and a Southern-African site.
**No optimiser is run.** Multi-objective optimisation is out of scope (`DECISIONS.md` D5); the
project reports **response surfaces**, not a Pareto front.
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

> **Their role changed on 2026-08-15.** These ten are no longer a search space for an optimiser.
> They are (a) the factors **Morris screens** for influence, and (b) the axes the **parametric
> sweeps** traverse across their full feasible ranges. Every variable therefore needs a *declared,
> defensible range* far more than it needs a gradient — a range that is wrong makes a response
> surface wrong everywhere, whereas an optimiser would merely have avoided the bad corner.

**Reported performance metrics** (formerly "objectives" — they are now the *outputs* mapped over
the envelope, not targets to be traded off): η_energy, η_ex, ρ_TES, LCOE, W_pump, Ė_D.
**Constraints / indicators:** ΔPHTF ≤ max; THTF ≤ salt/material limit; T_cold ≥ 450 °C (melting
point 401.4 °C + margin); `system_capacity > 0`; Wnet ≥ min; Qloss,TES, Eannual, Q̇HTF–sCO₂ reported.

**Sweep-parameter status against Objective 3's explicit naming:**

| Named in Obj 3 | Variable | Implemented? |
|---|---|---|
| nanoparticle concentration | φ (#3) | ✅ 0–2.0 wt%, hard-capped by the property module |
| **particle size** | **d_p (#4)** | ✅ **represented as a declared size-invariance over 5–60 nm** (`DECISIONS.md` **D6**, 2026-08-19). Range-guarded input; contributes a 6.1 % uncertainty, **no nominal trend** — the flat surface is B6's measurement, not a gap. Sweep it at **low density**: it is a known null dimension in the nominal. |
| cycle operating parameters | T_t,in, P_H, PR, f_RC (#7–#10) | ✅ all four exposed and validated at case F |

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

## 7. METHOD — SCREENING, THEN SYSTEMATIC SWEEPS (Objectives 3–5)

**Three stages, in order. No optimiser appears at any stage.**

**Stage 1 — Morris elementary-effects screening (Obj 3).** Textbook factor screening, cheap in model
evaluations, gives a µ*/σ ranking plus an interaction flag. ~(k+1)×r evaluations for k factors.
Canonical references now logged: Morris 1991 (`SOURCES.md` **HS1**) and Campolongo 2007 (**HS2**),
whose µ\* — the mean of the *absolute* effects — is what should be reported, not µ, or effects of
opposite sign cancel and hide an influential factor. **Its output is no longer a pruned vector for an optimiser** — it is the *evidence*
deciding which axes the Stage-2 sweeps resolve finely and which are held at a justified value.
Report it as a result, not as a preprocessing step.

**Stage 2 — systematic parametric sweeps (Obj 3–4).** Full-range sweeps of φ, d_p and the cycle
operating parameters, on a grid dense enough to render a **response surface** rather than a
trend line. Two design rules the old plan never needed:
- **Every swept point needs a φ = 0 base-salt twin.** Objective 4 asks for the benefit of
  nano-enhancement *as a continuous function of the varied parameters*, which is a difference of
  two surfaces — so the control is not one run at the end, it is half of every run.
- **Budget by rebuild class, not by point count.** SM and t_TES reuse an existing UDPC map (~20–40 s
  a point); anything touching the cycle or the HTF forces a ~35 min map rebuild (`CLAUDE.md` §4.15).
  Cache maps per cycle-design or the grid is unaffordable. See §11 item 4.

**Stage 3 — climate replication (Obj 5).** Re-run the Stage-2 envelope at a MENA site (Ouarzazate
TMY, in hand) and a Southern-African site (Northern Cape / Redstone corridor, **TMY in hand since
2026-08-19**, §10), and
report whether the *shape* of the response surfaces and the *sign and size* of the nano benefit
survive the climate change. This is a robustness claim about the maps, not a site-selection study.

**Optional depth if time allows:** a small Sobol variance decomposition on the factors Morris flags
dominant. Strictly additive; it sharpens Stage 1, it does not gate Stage 2.

> **Explicitly out of scope:** NSGA-II/III, `pymoo`, Pareto fronts, TOPSIS/CRITIC decision layers.
> Removed by the supervisor 2026-08-15 as post-graduate work (`DECISIONS.md` D5). The NSGA-II
> literature in `SOURCES.md` §H is **retained as method context, not as a plan of work.**

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
- [x] **Session F (Code)** — UDPC bridge completed; the "does not converge" finding **withdrawn**
      (`CLAUDE.md` §4.15); integrated annual result delivered; map resolution settled; SOURCES DOIs
      reconciled against Crossref.
- [x] **Session G (Code)** — ⚠ **objectives revised: MOO removed** (`DECISIONS.md` D5). Whole
      knowledge base and codebase realigned to the new five objectives; thermal diffusivity α added
      to the property module (Obj 1); `d_p` and the Southern Africa TMY promoted to blocking
      (§10); Morris/Campolongo method references added (`SOURCES.md` §H).

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
- [x] ~~⚠ **the UDPC off-design sweep does not converge at the case F design**~~ — **WITHDRAWN
      2026-08-14. The risk was never real.** The sweep converges at the full case F design in
      **38 min**; every experiment that reported otherwise was capped at 5–16 min. See
      `CLAUDE.md` §4.15 and `scripts/build_udpc_map.py`.
- [ ] ⚠ **NEW — long ssc runs need a MEASURED completion time before any non-convergence is
      recorded.** This one cost a session and produced a wrong finding that reached the thesis
      synthesis. The UDPC sweep prints nothing for ~35 min and is indistinguishable from a hang.
      **Rule: quote a measured wall time, or state that none is known — never infer "hangs" from
      "my timeout expired."** Applies to every long run in this project, not just UDPC.
- [ ] MD-viscosity provenance sentence for the thesis — **research/writing**, not blocking.
      (`SOURCES.md` §C0 already reframes this from weakness to field convention.) Note the revised
      Objective 1 raises the bar here: it demands **documented provenance for each correlation**,
      which makes `PROPERTIES.md`'s provenance map a *deliverable*, not a working note.
- [x] ~~⚠ **PROMOTED TO BLOCKING 2026-08-15 — the Southern Africa TMY.**~~ ✅ **CLOSED
      2026-08-19 — the user supplied it.** `data/tmy/1292737_-28.27_23.38_tmy-2022.csv`, NSRDB
      v4.0.1 TMY-2022, lat −28.27 lon 23.38, elev 1590 m, UTC+2 — the Northern Cape / Redstone
      CSP corridor, **0.02° (~2.4 km) from the −28.29, 23.37 this item specified**. Same format
      and column layout as the Morocco file, so both sites read through one code path.
      **Both Objective-5 sites are now on disk and Obj 5 is unblocked on data.** See
      `CLAUDE.md` §5 for the pair and the one timezone caveat (UTC+0 vs UTC+2).
- [x] ✅ **CLOSED 2026-08-19 — `d_p` (particle size) is now represented.** Was blocking: the
      enhancement fits are anchored to Han 2022 at a fixed particle size, so a d_p sweep moved
      nothing and would have published a manufactured null. **Resolved as `DECISIONS.md` D6 —
      option (c), selected by evidence rather than taken as a fallback.** How the other two died:
      **(b) returned null** — no study varies particle size for CuO in any chloride eutectic;
      **(a) proved unimplementable** — an anchored correction needs *f*(d_ref) = 1 at Han's own
      diameter, and **Han 2022 does not report it in any accessible form** (paywalled, not open
      access, absent from its abstract and from the reviews that tabulate it), so there is no
      anchor point. Decisively, the mechanistic 1/d_p surface-area argument is **refuted**:
      Tiznobaik & Shin 2013 (`SOURCES.md` **B6**) measured 5/10/30/60 nm SiO₂ and got
      24/26/23/26 % — no trend across a **12× diameter range** where surface area predicts a 12×
      swing. `d_p` is therefore a validated, range-guarded input with a **declared zero nominal
      effect over 5–60 nm** and a 6.1 % size-transfer uncertainty. **The flat surface is now a
      transcribed measurement with a citation, not an unrepresented variable** — which is the
      whole distinction this item was raised to protect. ⚠ Two stated weaknesses live in D6: the
      evidence is not unanimous (B5 reports cp falling with size in a chloride), and **no
      molten-salt study resolves k against diameter at all**, so k is the weaker half.
- [ ] ⚠ **NEW — thermal diffusivity α is now an explicitly required Objective-1 model.** It was
      already the *input* from which Han's k was derived (`scripts/nanofluid_properties.py`
      ~line 215) but was never an output. ✅ **Closed 2026-08-15** — α = k/(ρ·cp) is now a
      first-class module output with a round-trip check against Han's measured diffusivity ratios.

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
   - ✅ **The off-design sweep CONVERGES at the full case F design** — 2026-08-14,
     `results/udpc_bisect_20260814T194825Z.*`. `recomp_frac 0.40970`, η 0.50547, non-empty
     tables, **2277.9 s (38.0 min)**. Nothing had to be loosened.
   - ⚠️ **The previous "does not converge" finding was an artifact of short timeouts and is
     withdrawn.** All twelve prior experiments were capped at 5–16 min against a run that needs
     31–38. There is **no** convergence boundary: five configurations tested with the sweep on
     are all usable, and the knobs move wall time by only ~20 % (`CLAUDE.md` §4.15). The claim
     that a fully determined design is "over-constrained for UDPC generation" is **refuted** —
     as is the 93.6 s loose-bundle control, which has never reproduced and in fact **fails**
     after 2026 s with a real ssc diagnostic.
   - ✅ **INTEGRATED ANNUAL RESULT DELIVERED** — `scripts/run_integrated_annual.py`,
     `results/integrated_annual_20260815T095718Z.*`. Morocco TMY, nano-chloride 0.7 wt%:
     **440.21 GWh, 62,612 kW net** (n=3 map) · 442.09 GWh (n=5) · **389.39 GWh** for an
     identically configured steam control → **+13.05 % for the sCO₂ block**, which tests the
     §7.5 inference rather than asserting it.
   - ✅ **Map resolution settled:** 3 → 5 points per axis moves annual energy **+0.428 %**.
     Screening may use the cheap 3-point map; a final figure needs the densest affordable map
     and ±0.43 % resolution uncertainty. **Not** a convergence claim (SAM's default is 20/axis).
   - ⚠️ **NEW CONSTRAINT the integrated model exposed.** The recompression cycle's recuperation
     returns HTF at **533.3 °C** from a 700 °C source — only **166.7 K** loop ΔT — costing
     **49.55 MW of receiver pumping, ≈43 % of gross**. Feasible (positive nameplate) but heavily
     penalised. This reproduces §10's ΔT–pumping law to **0.3 %** without being fitted to it, and
     it means ΔT must be an active variable in the optimisation, not a passive outcome.
3. **Close the two Objective-1/3 representation gaps** (§10) — cheap, and everything below inherits
   them:
   - ✅ **thermal diffusivity α** exposed by the property module (done 2026-08-15).
   - ✅ **`d_p`** — closed 2026-08-19 as `DECISIONS.md` **D6**: declared size-invariance over
     5–60 nm, range-guarded, 6.1 % size-transfer uncertainty. **No longer blocking.** Sweep it at
     low density — it is a known null dimension in the nominal, so run budget belongs on φ and the
     cycle variables.
   - ✅ **Southern Africa TMY** — supplied 2026-08-19,
     `data/tmy/1292737_-28.27_23.38_tmy-2022.csv` (Northern Cape / Redstone corridor). **No
     longer blocking Objective 5.**
4. **Wire the decision vector** — expose all 10 variables of §3 as model inputs with **declared
   feasible ranges and their hard constraints** (φ ≤ 2.0 wt%, T_cold ≥ 450 °C, T_hot ≤ 700 °C,
   `system_capacity > 0`). Under the revised objectives the *range* is the deliverable-critical
   part, not the plumbing — a sweep reports across the whole range, so a bad bound corrupts the
   whole surface. Partition the vector by **rebuild class** at the same time (§7 Stage 2).
5. **Morris screening** (§7 Stage 1) over the 10 variables. ← **Objective 3, first half.**
6. ✅ **Exergy reporting layer** (§5) — **DONE 2026-08-19.** `scripts/exergy.py` is the callable
   layer and `scripts/run_integrated_annual.py` collects it on every case, so Ė_D is online
   *before* the campaign — which was the whole point of moving this ahead of the sweep on
   2026-08-15. Two tiers: **tier 1** (design point, per component, free — it rides the existing
   0.1 s solve) gives η_II 0.7626 with the HTR dominant at 40.5 % and the balance closing at
   1.53e-04; **tier 2** (annual, hourly dead state) is necessarily **plant-level**, because the
   UDPC map carries no per-hour state points, so no per-component Ė_D exists off-design
   (`DECISIONS.md` D1 annotation). ⚠ **Still outstanding from this item: the receiver / TES /
   tank Ė_D terms.** Tier 2 currently lumps everything upstream of the power block into
   `Ed_upstream`; splitting it is a genuine extension, not a bug, and is worth doing before the
   envelope is written up.
7. **Parametric sweep campaign** (§7 Stage 2) — φ, d_p and the cycle parameters across their full
   feasible ranges, **each point paired with a φ = 0 base-salt control run**. ← **Objective 3
   second half + Objective 4.** This is now the project's largest single compute commitment;
   budget it against the map-rebuild partition from item 4.
8. **Benefit envelope** (Obj 4) — the nano-minus-base difference over the swept envelope, reported
   as a continuous function of the varied parameters rather than as point comparisons.
9. **Climate replication** (§7 Stage 3, Obj 5) — repeat the envelope at Ouarzazate and Upington;
   report whether surface shape and benefit sign/size survive.


---

## 12. DEFERRED BACKLOG — validation hardening (do NOT start before §11 item 5 is done)

Parked deliberately on 2026-08-13. Each item is **defensive depth for the viva, not a modelling
risk**, and the power-block gate has already passed without them.

**Restart trigger: after Morris screening (§11 item 5) is delivered.** At that point the guaranteed
deliverable is banked, and these become cheap thesis-chapter reinforcement. Pick up in this order:

1. **Dostal 550 °C + 650 °C node tables** (Tables 10.2/10.3, already transcribed in
   `VALIDATION.md` §2.3.2). **Cheapest and highest value — no new literature, scripts already
   exist.** ⬆ **The revised objectives raise this item's priority.** Two of the ten decision
   variables (T_t,in and f_RC) are now **swept across their full feasible ranges** while the model
   is validated at a single point in that space — and a response surface makes a much stronger
   claim about its off-anchor region than a Pareto front ever did, because every point on it is
   reported rather than only the non-dominated ones. This covers a 150 °C span of T_t,in. It also
   doubles as a falsifiable test of the f = 0.4097 finding (`SOURCES.md` §A8).
2. **Battisti 2023 exergy cross-check** — confirm HTR-dominant exergy destruction against
   `SOURCES.md` F2. **Do this when the §11 item 6 exergy layer exists**, not before; it costs
   almost nothing once the layer is built.
3. **Independent node-level anchor** — acquire Padilla 2015 / Moisseytsev & Sienicki 2009 /
   Sarkar 2009 (`SOURCES.md` §A8). **Highest cost, lowest marginal return.** Only worth it if the
   viva specifically presses on single-source dependence. **Do not acquire PDFs before then.**
4. **SAM GUI cross-check** (`VALIDATION.md` §1.4) — blocked on a SAM install, and tests packaging
   rather than physics since GUI and PySAM share ssc 306. Lowest priority of all.
