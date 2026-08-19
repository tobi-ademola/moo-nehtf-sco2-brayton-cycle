# TODO — live task tracker

> Working checklist across sessions. **Not** a replacement for `PROGRESS_LOG.md` (append-only
> history of what happened) or `MASTER_PLAN.md` §11 (the strategic critical path). This file is
> the short list of what is *open right now*, so a fresh session can pick up without re-deriving
> priorities. Tick items here, then record the outcome in `PROGRESS_LOG.md`.

**Last updated:** 2026-08-19 — Session H

---

## In flight — the `d_p` representation (Session H)

- [x] Extract Han et al. 2022's CuO particle size (the `d_ref` an anchored size correction needs)
- [x] Timeboxed literature search for a size-resolved CuO / NaCl–KCl–MgCl₂ anchor (option **b**)
- [x] Choose between §10 options (a)/(b)/(c) and record it in `DECISIONS.md` → **D6**
- [x] Build the chosen representation into `scripts/nanofluid_properties.py`
- [x] Reconcile the module's local source labels with `SOURCES.md` IDs
- [x] Emit the decision evidence to `results/` and log the session

---

## Done since (Session H, 2026-08-19)

- [x] **Wire the exergy layer into the integrated model** — `scripts/exergy.py` (two tiers,
      self-validating), collected on every case by `run_integrated_annual.py`. Tier 2 is
      plant-level by construction: the UDPC map carries no per-hour state points.
- [x] **Diagnose the 27 negative-Ed hours** — the startup hypothesis was *refuted* (1 of 27);
      `m_dot_pc` does not reconcile with `q_pb` in a thin part-load tail. Re-parameterised by
      duty → `negative_Ed_hours = 0` on all three cases. `CLAUDE.md` §4.17.
- [x] **Run all three integrated cases** — the §7.5 steam-vs-sCO₂ inference is now a tested
      result: **+13.05 %** annual energy, and the exergy layer shows the advantage is conversion
      quality, not better resource use.

---

## Open — next up

- [ ] **Split `Ed_upstream` into receiver / TES / tank terms** — the remaining half of
      `MASTER_PLAN.md` §11 item 6. Tier 2 currently lumps everything upstream of the power block.
      An extension, not a defect, but worth having before the envelope is written up.
- [x] ~~Partition the decision vector by map-rebuild cost~~ — done 2026-08-19,
      `scripts/design_sweep_grid.py` → `results/sweep_grid_design_*`. **7 map-class, 2
      tower-class, 1 free.** Target envelope costs **29.7 h** (30 maps + 960 tower runs), 64 % of
      it map building. The second site is **+21.9 %**, not +100 %; the φ = 0 control is **+25 %**,
      not +100 %.
- [x] ~~**Implement the map cache, keyed by cycle design**~~ — done 2026-08-19,
      `scripts/map_cache.py`, wired into `run_integrated_annual.py`. Key = SHA-256 over
      `m.export()` (64 fields incl. `htf_props`) + PySAM version + ssc build string, computed
      *before* `execute()` so a hit costs 0.1 s. `--verify-invariance` passes. ⚠ **Debt:** the two
      existing maps were **adopted, not built** (`source: legacy-import`,
      `verified_by_rebuild: false`) — a `--build --force` rebuild-and-diff is owed before any
      final reported number, though not before a screening run.
      *(Original note, kept because the reasoning is the design:)*
      > **Design constraint found while scoping it (2026-08-19), before writing any code.** The
      > key must be **derived from the inputs actually applied to the model, not from a
      > hand-maintained list of parameter names.** `build_udpc_map.build()` sets ~30 fields across
      > `SystemDesign`, `Common` and `HeatExchangerDesign`, and several are pulled from
      > `validate_dostal` (`ETA_MC`, `P_HIGH_MPA`, `F_RECOMP`, `DOSTAL_DP_FRAC`, …) — so a change
      > to the validated baseline changes the map *without any argument of `build()` changing*.
      > A key listing only `(phi, T_htf_hot, n_points)` would then serve a **stale map that looks
      > right**, silently, which is the same failure family as §4.12's steam defaults. Hash the
      > applied input set plus the ssc build string, and store the key beside the map so a cache
      > hit can be audited. Also: `n_points` MUST be in the key — n=3 and n=5 gave +0.428 % on
      > annual energy, so they are not interchangeable.
      > ⚠ Verify the invariance claim rather than assuming it: confirm by execution that `d_p`
      > and the site genuinely do not touch any field `build()` assigns, before letting the cache
      > treat them as key-irrelevant.
      >
      > **✅ The mechanism exists — verified 2026-08-19.** `m.export()` on the assembled
      > `Sco2CspUdPcTables` returns **64 assigned input fields** across `SystemDesign` (10),
      > `HeatExchangerDesign` (27), `Common` (19), `PHXDesign` (3) and `AirCoolerDesign` (5),
      > **including the full 6×7 `htf_props` table** — which is the only place φ enters, so the
      > fluid is captured automatically. `Outputs` is empty before `execute()`, so the export is
      > naturally inputs-only and needs no filtering. **Hash a canonical JSON dump of that dict**
      > plus `PySAM.__version__` (7.1.1.post1) and the ssc build string (via ctypes on
      > `.venv\Lib\site-packages\PySAM\ssc.dll`, `CLAUDE.md` §1 — note `from PySAM import ssc`
      > does **not** work, it is a DLL not a module).
      >
      > Two things this settles: the key needs **no hand-maintained parameter list** (the original
      > worry), and it covers the `PHXDesign`/`AirCoolerDesign` defaults `build()` never sets
      > explicitly but which still affect the map — 64 fields against the ~30 I had estimated
      > from reading `build()`, so a hand-list would have missed roughly half.
- [ ] **Run the Morris screening on the costed screening grid (8.8 h)** *before* spending map
      builds on the envelope — it tells you which map-class axes deserve levels.
- [ ] **Wire the exergy layer into the integrated model** — every response functional is computable
      but the campaign needs it in the loop, not beside it.
- [ ] **Run the Morris screening** over the ten decision variables (Obj 3, part 2).
- [ ] **Declare the T_hot floor as a study constraint**, not a guard — an unfloored range publishes a
      response surface with an infeasible region baked in (`CLAUDE.md` §6, §4.14).
- [ ] **Parametric sweep campaign** — φ, d_p and cycle parameters, with a **φ = 0 base-salt control at
      every swept point** (Obj 4). Budget ~2× the runs first estimated.
- [ ] **Objective-5 climate replication** across both TMY sites now on disk (`CLAUDE.md` §5).

---

## Open — documentation debt found in passing

- [ ] **`SOURCES.md` has no entry for the base-salt property paper.** Every number in the property
      module's φ = 0 endpoint comes from Wang et al. 2021 (J. Sol. Energy Eng. 143(4):041005,
      doi:10.1115/1.4049253), and it was the only pivotal source with no `SOURCES.md` entry — so it
      was the only one never DOI-checked against Crossref in the §J1 sweep. **Added as B0 on
      2026-08-19**; the remaining task is to give it the full key-numbers treatment the other
      entries have (it is currently a short-form entry).
- [x] ~~`PROPERTIES.md` mis-attributes the base salt set as "Xu/Wang 2021".~~ Fixed 2026-08-19 —
      Crossref gives the author list as **Wang, Rincon, Li, Zhao, Vidal**; there is no Xu on it
      (Xu is a *different* base-salt MD source, `SOURCES.md` C3/C4). A residual "Xu/Wang" may
      survive in other prose — grep before quoting the base salt anywhere new.
- [ ] **Han et al. 2022's particle size is still unknown** (see `DECISIONS.md` D6). Not blocking any
      more, but if the full text is ever obtained, record `d_p` in `SOURCES.md` B1 — it would let
      D6's declared-invariance position be tested rather than only declared.
