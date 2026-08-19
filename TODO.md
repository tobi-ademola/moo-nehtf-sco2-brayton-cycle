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

## Open — next up

- [ ] **Partition the decision vector by map-rebuild cost** before any sweep. Cycle-design variables
      force a ~35 min UDPC rebuild (`CLAUDE.md` §4.15); SM and t_TES do not. Cache maps per
      cycle-design or the campaign is unaffordable. (`MASTER_PLAN.md` §11)
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
