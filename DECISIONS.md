# DECISIONS.md — Modeling-Decision Debates + Resolutions

> Per `MASTER_PLAN.md` §8. Atomic, self-contained entries — a new reader has zero context.
> Each decision records: the question, the gating finding, the resolution, and the fallback.

**Last updated:** 2026-08-15 — Session G. **D5 added: the supervisor removed multi-objective
optimisation from scope.** D1 and D3 are annotated where the revision changes what they mean; their
resolutions are unchanged. D2 and D4 are untouched by the revision.
Previously 2026-08-12 — Session A (modeling-decision debate), which resolved the four debates
queued in `MASTER_PLAN.md` §9 Session A using the gating findings from Session B
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
native, so the reporting layer is arithmetic on arrays already carried. Also, exergy destruction is
a **named requirement** — not optional garnish.

> **Annotation 2026-08-15 (D5).** `min Ė_D` was a *primary objective* of the removed multi-objective
> formulation. It survives the scope change intact, in a different role: the **revised Objective 2
> names exergy assessment explicitly**, so Ė_D is now a metric **mapped over the parametric
> envelope** rather than a term in an objective vector. If anything the requirement tightens — a
> Pareto front needed Ė_D only at the non-dominated points, whereas a response surface needs it at
> **every** swept point, including the φ = 0 controls. Practical consequence: the exergy layer must
> be wired into the integrated model *before* the sweep campaign launches, or the campaign has to
> be re-run to collect it (`MASTER_PLAN.md` §11 item 6, which was moved ahead of the
> campaign for exactly this reason).

**Working rule (unchanged from `MASTER_PLAN.md` §5).** Build the model **exergy-ready** — carry
h AND s at every state point from the start (already happening). Gate only the exergy
**reporting layer** behind validation passing; do NOT gate the data collection. This keeps
novelty open without touching the critical path.

**Fallback (NO LONGER NEEDED — see below).** If node-mapping (see D4) proved messier than
expected or the buffer collapsed, the plan was to exclude exergy (supervisor-approved) and keep
energy / hydraulic / economic.

**CONFIRMED BY EXECUTION — 2026-08-13, Session E.** Session B's finding was that entropy *is
exposed*; it did not demonstrate that a correct exergy layer could be **built** from it. That has
now been done and checked end-to-end — `scripts/exergy_layer_check.py`,
`results/exergy_layer_check_20260813T023227Z.{md,csv}`, on the adopted case F baseline. All five
checks pass:

| Check | Result |
|---|---|
| e = 0 at the reference node | exact (0.000e+00) |
| exergy maximal at the turbine inlet | node 5, 426.88 kJ/kg |
| every component ĖD > 0 | 8 of 8 |
| **HTR is the largest single destroyer** | **1265.62 kW = 41.4 %** |
| **cycle-wide exergy balance closes** | residual **1.95 kW = 1.5e-04 relative** |

The balance — Ex_in(salt) = W_net + ΣĖD — is the load-bearing one: it exercises every *h*, every
*s*, both mass flows, the salt-side properties and the work terms simultaneously, so it catches
scaling and unit errors that per-component sign checks cannot. Second-law efficiency comes out at
**76.56 %**, and the HTR-dominant ranking matches Battisti 2023 (`SOURCES.md` F2) independently.

**Consequence:** the `+~1 day` CoolProp-reconstruction risk in `MASTER_PLAN.md` §5 is **closed,
not merely unlikely**, and the D1 fallback can be retired. ĖD — named in Objective 2, and one of
the metrics to be mapped over the parametric envelope — is now known to be computable from data
the model already carries.

> ⚠ **One correction this exposed, which matters for every ĖD number reported downstream.** Two
> different T₀ values are in play and they are not interchangeable: the *reference state* for the
> per-node table (Dostal node 1, 305.15 K at 7.69 MPa) is **not a dead state** — the cycle cannot
> reject heat to 7.69 MPa. Gouy-Stodola ĖD = T₀·Sgen is only meaningful at the **environment**
> temperature, T_amb = 299.15 K. Using the wrong one inflates every ĖD by ~2 % and leaves the
> exergy balance open by **−188.5 kW (−1.46 %)** instead of closing to 1.95 kW. The component
> *ranking* is identical either way, so this never shows up as a sanity-check failure — only the
> balance catches it. **Report ĖD at T_amb.**

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
`MASTER_PLAN.md` §7). Reserve variance-based Sobol for the variables Morris flags dominant.

> **Annotation 2026-08-15 (D5).** The resolution stands; **its purpose changed.** Morris was chosen
> as a *pruning* step to make an NSGA-II run affordable. With MOO out of scope, its output is no
> longer an input to an optimiser — it is (a) a **reported result** in its own right, the ranked
> influence of the ten variables with an interaction flag, which Objective 3 now names explicitly,
> and (b) the **evidence** deciding which axes the parametric sweeps resolve finely and which are
> held at a justified value. Two knock-on effects worth stating: the case for Morris over OAT gets
> *stronger*, because a response surface is exactly where an unflagged interaction does visible
> damage; and the case for Sobol gets *weaker as a screening tool*, because the Stage-2 sweeps
> themselves map the response over the full range, which is most of what a variance decomposition
> would have told us. Sobol is now genuinely optional depth, not a deferred necessity.

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

> **Annotation 2026-08-15 (D5).** Strengthened, not weakened, by the revision: the **revised
> Objective 3 names the decoupled validation strategy explicitly**, so what was this project's own
> methodological argument is now a stated requirement. Nothing about the two-lane resolution
> changes.

---

## D5 — Multi-objective optimisation: REMOVED FROM SCOPE (supervisor, 2026-08-15)

**Question.** Not a debate this project resolved — a **scope decision taken by the supervisor** and
recorded here because everything downstream of it changes. MOO was flagged as post-graduate work
and struck from the objectives; the objectives were reissued as the five now in
`MASTER_PLAN.md` §1.

**What is removed.** Multi-objective optimisation in all forms: NSGA-II/III, `pymoo`, Pareto-front
construction, and any TOPSIS/CRITIC multi-criteria decision layer over a front. The former
five-objective trade-off (max η_ex, max ρ_TES; min LCOE, min W_pump, min Ė_D) is removed **as an
optimisation target**. The old Objective 3 is gone in its entirety.

**What replaces it.** Morris screening of the ten variables, then **systematic parametric sweeps
across full feasible ranges producing response surfaces** (Obj 3); the **benefit envelope** of
nano-enhancement vs base salt as a continuous function of those parameters (Obj 4); and
**climate robustness** of the maps across MENA and Southern Africa (Obj 5). Objectives 4 and 5
were previously *post-defence* and are now **in scope**.

**Resolution.** Accept in full. Realign the knowledge base and codebase to the five new objectives;
retain, do not delete, the MOO-related literature and reasoning as method context.

**Consequences that are not merely editorial** — these are the ones that create work:

1. **The five former objectives become reported metrics.** η_ex, ρ_TES, LCOE, W_pump and Ė_D are
   still computed, still needed, and now **mapped over the envelope** rather than traded off. The
   modelling requirement is *unchanged*; only the reporting changes. In particular D1's exergy
   decision is untouched — see its annotation.
2. **The φ = 0 control multiplies the run count.** Objective 4 wants the benefit as a *continuous
   function of the varied parameters*, i.e. the difference of two surfaces. A base-salt twin is
   therefore needed at **every** swept point, not once at the end.
3. **Two declared exclusions stop being acceptable.** `d_p` (particle size) is named as a swept
   parameter, and it is represented in no model layer; **thermal diffusivity** is named as a
   required property model, and was only ever an internal intermediate. Both are logged in
   `MASTER_PLAN.md` §10; α is now closed, `d_p` is not.
4. **A missing data file became a blocker.** The Southern Africa (Upington) TMY was a post-defence
   footnote; Objective 5 cannot start without it. ✅ **Resolved 2026-08-19** — the user supplied
   `data/tmy/1292737_-28.27_23.38_tmy-2022.csv` (Northern Cape / Redstone corridor, 0.02° from the
   specified coordinates). Kept in this record because the *lesson* stands: under the revised
   objectives an absent input file is a scope blocker, not a footnote, and the remaining one
   (`d_p`) is of the same kind.
5. **Range declarations now carry the weight gradients used to.** An optimiser that meets a bad
   bound simply avoids that corner; a sweep *reports across the whole range*, so an indefensible
   bound corrupts the published surface. Every range in `MASTER_PLAN.md` §3 needs a stated basis.

**Fallback.** None required, and none applies — this is an instruction, not a technical risk. The
only reversal path is the supervisor reinstating MOO, in which case nothing built here obstructs
it: the model, the metrics and the screening are exactly the inputs an optimiser would need, and
`SOURCES.md` §H is deliberately retained for that reason.

---

## Summary table

| # | Decision | Resolution | Status |
|---|----------|-----------|--------|
| D1 | Exergy in/out | **IN** — entropy exposed natively; build exergy-ready, report last | gate resolved; Ė_D reframed as a mapped metric by D5 |
| D2 | Salt / SAM | **Native nitrate in SAM; nano-chloride coupled externally**; codes 6/14 as off-path sanity | confirmed |
| D3 | Screening | **Morris now; Sobol on survivors if time** | confirmed; purpose reframed by D5 (result + sweep design, not pruning) |
| D4 | Validation | **Decoupled — forced by absence of sCO₂-tower case**; node-by-node power block, native-salt field/TES | confirmed & strengthened; now a stated requirement of Obj 3 |
| D5 | **Multi-objective optimisation** | **REMOVED from scope by the supervisor; replaced by screening + parametric sweeps + benefit envelope + climate robustness** | **accepted 2026-08-15** |
