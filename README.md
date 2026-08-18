# Nano-Enhanced HTF + sCO₂ Brayton CSP Thesis

Undergraduate thesis project on the parametric performance assessment of a nano-enhanced heat transfer fluid (HTF) integrated with a supercritical CO₂ (sCO₂) Brayton power cycle for concentrating solar power (CSP).

## Overview

The project builds an integrated CSP → nano-HTF → thermal energy storage (TES) → sCO₂ Brayton cycle model in PySAM/SAM, screens its ten decision variables for influence, and then sweeps the influential ones across their full feasible ranges to produce performance response surfaces. The base HTF is a NaCl–KCl–MgCl₂ eutectic enhanced with CuO nanoparticles, chosen for its higher temperature ceiling (~700–800 °C) relative to conventional nitrate salts, which better matches the preferred hot-end temperature of an sCO₂ recompression cycle.

**Objectives** (revised by the supervisor 2026-08-15):

1. Temperature- and concentration-dependent thermophysical property models — density, specific heat, thermal conductivity, thermal diffusivity, viscosity — for the CuO-enhanced NaCl–KCl–MgCl₂ HTF, with documented provenance for each correlation.
2. An integrated model of the CSP tower, the nano-enhanced HTF, two-tank molten-salt storage, and the recompression sCO₂ Brayton cycle, equipped with energy, exergy, hydraulic, and economic assessments.
3. Validation by a decoupled strategy; Morris elementary-effects screening of the ten decision variables; systematic parametric sweeps of nanoparticle concentration, particle size, and cycle operating parameters across their full feasible ranges, yielding performance response surfaces.
4. The full parametric performance envelope from those sweeps, quantifying the net benefit of nano-enhancement relative to the conventional base salt as a continuous function of the varied parameters.
5. Robustness of the parametric performance maps across contrasting climates — MENA and Southern Africa.

Deliverable: a validated integrated model, a screening result, and the parametric response surfaces / benefit envelope / climate-robustness comparison built on it.

> **No multi-objective optimisation.** MOO (NSGA-II/III, Pareto fronts) was removed from scope by the supervisor on 2026-08-15 as post-graduate work — see [`DECISIONS.md`](DECISIONS.md) D5. The project reports response surfaces over the parameter space, not a non-dominated front across it. **The repository directory name still carries a legacy `moo-` prefix; it is historical, not descriptive.**

See [`MASTER_PLAN.md`](MASTER_PLAN.md) for the complete critical path, decision variables, modeling decisions, and session-continuity system this project uses across multiple Claude chat/Code sessions, and [`THESIS_SYNTHESIS.md`](THESIS_SYNTHESIS.md) for the consolidated state of every result.

## Status

Objectives 1 and 2 are substantially delivered: the property model is complete and self-validating, the sCO₂ power block is validated node-by-node against a published state-point table, the HTF couples inside SAM, and the integrated plant returns an annual result. Objectives 3–5 — screening, sweeps, benefit envelope, climate robustness — are the remaining work.
