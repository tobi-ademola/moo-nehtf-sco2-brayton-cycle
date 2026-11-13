# Nano-Enhanced Molten-Salt CSP with a Supercritical CO₂ Brayton Cycle

**Undergraduate thesis** — *Development of an Integrated Model for a Nano-Enhanced Molten Salt
Concentrated Solar Power Plant Coupled with a Supercritical CO₂ Brayton Cycle.*
B.Eng. Mechanical Engineering, Edo State University Iyamho, Nigeria (2026).
Supervisor: Engr. Jeremiah Akhimien.

An integrated model of a concentrating-solar-power (CSP) tower plant: a CuO-enhanced
NaCl–KCl–MgCl₂ heat-transfer fluid, two-tank thermal storage, and a recompression supercritical
CO₂ (sCO₂) power cycle. Built in Python on NREL's System Advisor Model (PySAM), with energy,
exergy, hydraulic and economic outputs.

```
heliostat field ─► receiver ─► nano-chloride HTF ─► two-tank TES ─► PHX ─► sCO₂ recompression cycle
                         (custom property tables, φ = nanoparticle loading)       (UDPC map from Sco2CspUdPcTables)
```

---

## Why this problem

Nitrate "solar salt" is limited to about 565 °C. An sCO₂ cycle gets its efficiency advantage at
about 700 °C. Chloride salts can reach that temperature, and nanoparticles can change their
specific heat and conductivity. This project asks how far nanoparticle loading moves the
**plant-level** numbers — annual energy, pumping power, storage size and cost — and not only the
fluid properties.

## Key results

| Result | Value | How to reproduce |
|---|---|---|
| sCO₂ cycle validated node-by-node against Dostal (2004) | all 8 state points within **0.070 %** (enthalpy) and **0.045 %** (entropy); cycle efficiency **51.289 %** vs. 51.27 % published | `scripts/validate_dostal.py` |
| Rejected a configuration that matched efficiency only through cancelling errors | internal state points off by up to 5.4 % despite a +0.26 pp efficiency match | `VALIDATION.md` §2.3 |
| Independent property check | ssc's CO₂ properties match CoolProp to 1.0 × 10⁻⁴ kJ/kg | `scripts/validate_dostal.py` |
| Custom nano-chloride HTF couples inside SAM | zero round-trip deviation across six cases | `scripts/htf_sam_bridge.py` |
| Full-year integrated plant (Ouarzazate, Morocco TMY) | sCO₂ block delivers **+13.05 %** annual energy vs. a steam-Rankine control at identical fluid and loop temperatures | `scripts/run_integrated_annual.py` |

Full results, with the reasoning behind each modelling decision, are in
[`THESIS_SYNTHESIS.md`](THESIS_SYNTHESIS.md).

## What is in this repository

| Path | Contents |
|---|---|
| `scripts/nanofluid_properties.py` | Temperature- and loading-dependent ρ, cp, k, α, μ for the CuO–chloride HTF, each with an uncertainty band and a source |
| `scripts/validate_dostal.py` | sCO₂ cycle validation, with a second-law and power-balance check at every node |
| `scripts/build_udpc_map.py`, `map_cache.py` | Builds the off-design sCO₂ map for the tower model and caches it by a hash of the full model input |
| `scripts/exergy.py`, `run_integrated_annual.py` | Annual energy and exergy assessment of the integrated plant |
| `scripts/morris_screen.py`, `design_sweep_grid.py` | Screening and parametric-sweep design |
| `results/` | Every reported number, stamped with the script and git commit that produced it |
| `DECISIONS.md`, `PROPERTIES.md`, `SOURCES.md`, `VALIDATION.md` | Modelling decisions, property provenance, sources, validation record |

## How to run

Requires Python **3.13** (PySAM has no 3.14 wheels).

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install "NREL-PySAM==7.1.1.post1" numpy CoolProp
.venv/bin/python -u scripts/smoke_test.py        # solved recompression cycle, ~1 s
.venv/bin/python -u scripts/validate_dostal.py   # literature validation
.venv/bin/python -u scripts/report_htf_properties.py
```

Annual runs need an NSRDB TMY weather file in `data/tmy/` (not committed; see `SOURCES.md`).

## Status

The property model, the validated sCO₂ power block and the integrated annual model are complete.
The thesis was defended in August 2026.

## Note on tooling

I wrote this project with AI coding assistants (Claude Code). The `CLAUDE.md` and `AGENTS.md`
files are the working instructions I kept for them. Every modelling decision, source and
validation check is recorded in the documents above.

## Author

**Oluwatobi Ademola** · [github.com/tobi-ademola](https://github.com/tobi-ademola)
