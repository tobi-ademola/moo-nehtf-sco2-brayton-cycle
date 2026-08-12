# MASTER PLAN — Nano-Enhanced HTF + sCO₂ Brayton CSP Thesis Sprint

> **Purpose of this file.** Single source of truth for the whole project. Written so any
> fresh Claude chat, Claude Code session, or a brand-new account can pick up the work
> **cold** by reading only this file plus the linked knowledge-base entries. Keep it
> current. If you update nothing else, update this.

**Last updated:** (set on each edit) — v0.1 initial
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
   mostly done (prior work)     Claude Code lane          GATE — nothing              GUARANTEED
                                                          downstream is valid          DELIVERABLE
                                                          until this passes
```

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
- ⚠️ **THE REAL RISK:** does PySAM's sCO₂ model expose **per-state entropy** (esp. regenerator intermediate nodes 7/8/9)? If only lumped efficiencies are exposed, reconstruct states via **CoolProp** (+~1 day).
- **Working rule:** build the model **exergy-ready** — carry **h AND s at every state point** from the start. Switch on the exergy _reporting layer_ last. This keeps novelty open without gating the critical path.
- **Fallback:** if the entropy-exposure check fails and CoolProp reconstruction eats the buffer, exclude exergy (supervisor-approved) and keep energy/hydraulic/economic.

---

## 6. VALIDATION STRATEGY (decoupled — the defensible approach)

Do **not** try to validate the whole integrated plant against one paper (few report enough).

- **Power block:** validate the sCO₂ recompression cycle against a published case **with reported state points + efficiency**. Candidate starting points (from the attached paper's refs): **Turchi 2009**, **Chacartegui et al. 2011**. → research task, this-chat lane.
- **Solar field / TES:** validate against a **SAM/NREL reference case** (e.g. a Gen3 molten-salt tower reference). → Claude Code lane.
- Document both validations separately in `VALIDATION.md` with % error tables.

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

## 9. IMMEDIATE NEXT ACTIONS (session queue)

The three launch prompts below are written to be pasted as the FIRST message of a fresh session.
Do them roughly in this order; #2 and #3 can overlap.

- [ ] **Session A (this chat lane): Modeling-decision debate** — resolve exergy in/out (needs the entropy-exposure check result from Code), screening method, salt/SAM reconciliation, validation targets. → emits `DECISIONS.md`.
- [ ] **Session B (Code lane): Continuity scaffold + env capture** — create `CLAUDE.md`, capture SAM/PySAM versions, confirm which sCO₂ state points are exposed (feeds the exergy decision). → emits `CLAUDE.md`, seeds `VALIDATION.md`.
- [ ] **Session C (this chat lane): First research pass** — validation-target papers (Turchi, Chacartegui, +sCO₂ recompression with full state points) and nano-HTF property literature to firm up Obj1 provenance. → emits `SOURCES.md`, `PROPERTIES.md` seed.

_(Launch prompts for A/B/C are provided separately in this session.)_

---

## 10. OPEN QUESTIONS / RISKS (live list)

- [ ] Does PySAM expose per-state entropy for the sCO₂ recompression cycle? (gates exergy) — **Code to answer**
- [ ] Can SAM override molten-salt properties, or must the nano-chloride HTF couple externally? — **Code to answer**
- [ ] Which published sCO₂ case has enough reported state points for power-block validation? — **research to answer**
- [ ] MD-viscosity provenance: is there a citable MD study, or is it our own? Needs a defensible thesis sentence. — **research/writing**
- [ ] Location set for Obj5: confirm specific MENA + Southern Africa sites with available TMY/solar-resource data. — **later**
