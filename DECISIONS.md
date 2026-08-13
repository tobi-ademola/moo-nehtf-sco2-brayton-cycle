# DECISIONS.md — Modeling-Decision Debates + Resolutions

> Per `MASTER_PLAN.md` §8. Atomic, self-contained entries — a new reader has zero context.
> Each decision records: the question, the gating finding, the resolution, and the fallback.

**Last updated:** 2026-08-12 — Session A (modeling-decision debate). Resolves the four
debates queued in `MASTER_PLAN.md` §9 Session A, using the gating findings from Session B
(`VALIDATION.md`, `CLAUDE.md`).

---

## D1 — Exergy: IN (built exergy-ready, reporting layer switched on last)

**Question.** Include component-level exergy-destruction analysis, or exclude to protect the
33 h buffer? Gated on: does PySAM expose per-state entropy for the sCO₂ recompression cycle?

**Gating finding (RESOLVED — Session B).** `PySAM.Sco2CspSystem` exposes **T, P, h AND s at
every cycle node** (`VALIDATION.md` §2.1; `CLAUDE.md` §3, §7). The smoke test already prints a
full state-point table with per-component `Sgen > 0`. **The CoolProp reconstruction fallback
(+~1 day) is NOT needed.**

**Resolution.** **IN.** Both cost drivers are gone: (a) the algebra is transcription, not
derivation — Atif & Al-Sulaiman 2018 gives component-level ĖD equations (Eqs. 41–56) for this
exact topology (recompression sCO₂ + two-tank molten salt + central receiver); (b) entropy is
native, so the reporting layer is arithmetic on arrays already carried. Also, `min ĖD` is a
**named primary objective** in the supervisor's decision sheet (`MASTER_PLAN.md` §3) — not
optional garnish.

**Working rule (unchanged from `MASTER_PLAN.md` §5).** Build the model **exergy-ready** — carry
h AND s at every state point from the start (already happening). Gate only the exergy
**reporting layer** behind validation passing; do NOT gate the data collection. This keeps
novelty open without touching the critical path.

**Fallback (intact).** If node-mapping (see D4) proves messier than expected or the buffer
collapses, exclude exergy (supervisor-approved) and keep energy / hydraulic / economic. The
entropy finding removes the only pre-emptive reason to drop it.

---

## D2 — Salt / SAM reconciliation: native nitrate in SAM; nano-chloride coupled externally

**Question.** SAM's molten-salt tower defaults to nitrate (code 17, 60/40 NaNO₃/KNO₃, ~574 °C).
The HTF is a CuO / NaCl–KCl–MgCl₂ chloride eutectic (~700–800 °C). Run SAM on native salt +
couple nano-chloride externally in the HTF→sCO₂ layer, **or** force chloride props into SAM?

**Decisive constraint.** The **only** solar-field/TES validation anchor available is
`MSPTSingleOwner`, built and pinned to nitrate at ssc 306 (`VALIDATION.md` §1). Forcing a
700–800 °C chloride into that case breaks the receiver thermal model, tank losses, and piping
hydraulics at once — and there is **nothing published to validate the altered numbers against.**
That is validating against a case you just invalidated. It is mechanically possible
(`rec_htf = 50`, 7-col user table; `CLAUDE.md` §6) but methodologically self-defeating.

**Resolution.** **Run SAM on its native nitrate for the field/TES validation; apply the
nano-chloride properties in the HTF→sCO₂ heat-transfer + hydraulic layer** (confirms
`MASTER_PLAN.md` §4 working approach). The receiver/TES physics SAM validates (heliostat field,
receiver flux, two-tank losses, dispatch) are salt-agnostic enough to transfer; the
nano-chloride's actual effect lives in the coupling layer, which is where the novelty is.

**Cheap sanity anchor (off critical path).** Use SAM's built-in chloride salts — code `6`
(68% KCl / 32% MgCl₂) and code `14` (58% NaCl / 42% MgCl₂) — as a one-off check that the
external chloride coupling isn't wildly off a salt SAM already knows (`VALIDATION.md` §3 open
item). Neither is the ternary eutectic; keep them **off** the validation critical path. Do NOT
push the ternary NaCl–KCl–MgCl₂ eutectic into the validated field case.

---

## D3 — Screening method: Morris elementary-effects (Sobol on survivors only)

**Question.** Morris elementary-effects vs one-at-a-time (OAT) vs Sobol, for 10 decision
variables under 33 h time pressure.

**OAT — rejected.** Never leaves the baseline point; misses interactions, misreads
nonlinearity. Indefensible at a defense for 10 coupled variables (nano-props → cycle temps →
exergy).

**Sobol — deferred.** True variance decomposition + interaction indices, but ~thousands of model
evaluations. A `TcsmoltenSalt` annual run is ~20–40 s (`CLAUDE.md` §7); the coupled sCO₂ + annual
loop is more. Full Sobol on 10 vars up front is an unaffordable convergence risk.

**Morris — chosen.** ~(10+1)×r evaluations (tens, not thousands). Gives a defensible variable
ranking AND flags interactions (µ* vs σ) — the exact thing OAT lacks. Correct time-to-insight
tool.

**Resolution.** **Morris now; Sobol on survivors only if time allows** (confirms
`MASTER_PLAN.md` §7). Morris produces the **guaranteed deliverable** (ranked impact → justify
pruning or full MOO). Reserve variance-based Sobol for the variables Morris flags dominant.
Bonus: pruning 10 → 5–6 variables materially de-risks the stretch NSGA-II convergence.

---

## D4 — Validation decoupling: CONFIRMED (and forced by the tool)

**Question.** Confirm or challenge the plan to validate power block and solar-TES separately.

**Confirmed — not a preference, a necessity.** There is **no sCO₂-tower reference case in SAM** —
it does not exist in the GUI, only steam-Rankine towers do (`VALIDATION.md` §1.1; `CLAUDE.md`
§3). The integrated sCO₂ plant physically cannot be validated against one SAM case. Decoupling
is forced.

**Two-lane resolution.**

- **Power block (literature).** The h,s exposure finding (D1) upgrades this from an
  efficiency-match to a **node-by-node state-point comparison** against a published table
  (candidates: Turchi 2009, Chacartegui et al. 2011, Atif & Al-Sulaiman 2018). Far stronger
  claim — **lead with it in the thesis.**
  - **Live risk:** node-numbering mismatch. Published papers use 1-based numbering with a
    different topology order (`VALIDATION.md` §2.3). **Write the published-node → SAM-index
    mapping explicitly and in writing BEFORE computing any error**, or the table is silently
    wrong.
- **Field / TES (SAM reference).** Anchor to `MSPTSingleOwner`, cross-checked against the
  **SAM 2025.4.16 GUI (ssc 306)** — the version that matches PySAM 7.1.1. **Never cross-check
  against 2026.7.3 (ssc 308);** its deltas are version artifacts, not modeling errors
  (`CLAUDE.md` §1.1). Regression baseline: `annual_energy` = 593,054,474.50 kWh, CF 66.5926 %.

**Thesis framing.** Present decoupling as a **deliberate methodological strength** — each
subsystem validated against the best available reference for that subsystem — not as a
workaround for a missing integrated case.

---

## Summary table

| # | Decision | Resolution | Status |
|---|----------|-----------|--------|
| D1 | Exergy in/out | **IN** — entropy exposed natively; build exergy-ready, report last | gate resolved |
| D2 | Salt / SAM | **Native nitrate in SAM; nano-chloride coupled externally**; codes 6/14 as off-path sanity | confirmed |
| D3 | Screening | **Morris now; Sobol on survivors if time** | confirmed |
| D4 | Validation | **Decoupled — forced by absence of sCO₂-tower case**; node-by-node power block, native-salt field/TES | confirmed & strengthened |
