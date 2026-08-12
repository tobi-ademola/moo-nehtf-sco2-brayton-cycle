# Nano-Enhanced HTF + sCO₂ Brayton CSP Thesis

Master's thesis project on multi-objective optimization of nano-enhanced heat transfer fluids (HTFs) integrated with a supercritical CO₂ (sCO₂) Brayton power cycle for concentrating solar power (CSP).

## Overview

The project builds an integrated CSP → nano-HTF → thermal energy storage (TES) → sCO₂ Brayton cycle model in PySAM/SAM, then optimizes it across solar-field, storage, HTF, and cycle decision variables. The base HTF is a NaCl–KCl–MgCl₂ eutectic enhanced with CuO nanoparticles, chosen for its higher temperature ceiling (~700–800 °C) relative to conventional nitrate salts, which better matches the preferred hot-end temperature of an sCO₂ recompression cycle.

**Objectives:**
1. Temperature- and concentration-dependent thermophysical models of the nano-enhanced molten-salt HTF.
2. Integrated CSP–nano-HTF–TES–sCO₂ Brayton model with energy, exergy, hydraulic, and economic assessment.
3. Multi-objective optimization of nanoparticle concentration, particle size, and cycle operating parameters to maximize energy efficiency and TES energy density while minimizing cost, pumping power, and exergy destruction.
4. *(Post-defense)* Pareto-optimal envelope and net benefit of nano-enhancement vs. conventional salt.
5. *(Post-defense)* Robustness of the Pareto-optimal configuration across MENA and Southern Africa climates.

Guaranteed deliverable: a validated model plus parametric screening identifying the most impactful decision variables. Stretch deliverable: full NSGA-II multi-objective optimization.

See [`MASTER_PLAN.md`](MASTER_PLAN.md) for the complete critical path, decision variables, modeling decisions, and session-continuity system this project uses across multiple Claude chat/Code sessions.

## Status

Early setup — properties and modeling groundwork mostly reused from prior work; PySAM pipeline build-out and validation in progress.
