# Sweep-grid design — the decision vector partitioned by build cost

| | |
|---|---|
| script | `scripts/design_sweep_grid.py` |
| generated (UTC) | 20260819T133125Z |
| git commit | `fd38a00-dirty` |
| map build | **38 min** each (measured, `CLAUDE.md` §4.15) |
| tower run | **40 s** each (`CLAUDE.md` §8) |
| budget tested against | 40 h |

## 1. The partition

| # | variable | class | cost of one extra level | declared range | basis |
|---|---|---|---|---|---|
| 1 | SM | `tower` | 40 s × every map | 1.8 - 3.0 | standard CSP design range; 2.4 is the validated baseline |
| 2 | t_TES | `tower` | 40 s × every map | 6 - 14 h | standard; 10 h is the validated baseline |
| 3 | phi | `map` | **38 min × every other map axis** | 0 - 2.0 wt% | HARD CAP: the property module refuses beyond Han's measured range |
| 4 | d_p | `free` | **nothing** — no nominal model effect | 5 - 60 nm | DECISIONS.md D6 -- declared size-invariant nominal; B6's tested range |
| 5 | T_HTF | `map` | **38 min × every other map axis** | 600 - 700 C | upper = B0 correlation validity; lower = keeps loop dT feasible (see the floor below) |
| 6 | m_HTF | `map` | **38 min × every other map axis** | via loop dT, 250 - 284 K | FLOOR IS A STUDY CONSTRAINT, not a guard -- 124 K gives a NEGATIVE nameplate (§4.14) |
| 7 | T_t_in | `map` | **38 min × every other map axis** | derived: T_HTF - dT_PHX | not independent of #5 -- CLAUDE.md §4.10; do NOT sweep both as free axes |
| 8 | P_H | `map` | **38 min × every other map axis** | 18 - 25 MPa | 20 MPa validated at case F; 25 MPa used by the smoke test |
| 9 | PR | `map` | **38 min × every other map axis** | 2.2 - 3.0 | 2.6 validated at case F |
| 10 | f_RC | `map` | **38 min × every other map axis** | 0.30 - 0.45 | 0.4097 at case F; free f_rc self-selects 0.41067, so this axis is nearly inert (§4.15) |

**7 map-class, 2 tower-class, 1 free.** The map-class axes are the entire campaign cost; the other 3 are rounding.

⚠ **#7 `T_t_in` is NOT independent of #5 `T_HTF`** — it is derived as `T_HTF - dT_PHX_approach` (`CLAUDE.md` §4.10). Sweeping both as free axes multiplies the map count while exploring a one-dimensional family, which is the single easiest way to make this campaign unaffordable for nothing. Sweep `T_HTF` and let `T_t_in` follow, or sweep the approach itself as the second axis.

⚠ **#10 `f_RC` is nearly inert.** With everything else pinned, a free `f_rc` self-selects 0.41067 against case F's pinned 0.40970 — 0.24 % apart, worth +0.02 pp in efficiency (`CLAUDE.md` §4.15). Spend levels here last.

⚠ **#6's loop-ΔT floor is a CONSTRAINT OF THE STUDY, not a guard.** At 124 K the nameplate goes NEGATIVE (`CLAUDE.md` §4.14) and ssc does not raise. A sweep reports across its whole declared range, so an unfloored range publishes a response surface with an infeasible region silently baked into it.

## 2. Candidate grids, costed

| grid | map axes | tower axes | sites | maps | tower runs | map h | run h | **total h** | within 40 h? |
|---|---|---|---|---|---|---|---|---|---|
| screening (Morris) | phi:3 × T_HTF:3 | SM:3 × t_TES:3 | 1 | 12 | 108 | 7.6 | 1.2 | **8.8** | yes |
| minimal envelope | phi:3 × T_HTF:3 | SM:3 × t_TES:3 | 2 | 12 | 216 | 7.6 | 2.4 | **10.0** | yes |
| target envelope | phi:4 × T_HTF:3 × P_H:2 | SM:4 × t_TES:4 | 2 | 30 | 960 | 19.0 | 10.7 | **29.7** | yes |
| dense envelope | phi:5 × T_HTF:4 × P_H:3 | SM:5 × t_TES:5 | 2 | 72 | 3600 | 45.6 | 40.0 | **85.6** | **NO** |
| all map axes at 3 | phi:3 × T_HTF:3 × P_H:3 × PR:3 × f_RC:3 | SM:3 × t_TES:3 | 2 | 324 | 5832 | 205.2 | 64.8 | **270.0** | **NO** |

Every row includes the **φ = 0 control** (Objective 4) and, where sites = 2, the **climate replication** (Objective 5).

## 3. What the costing actually shows

Take the **target envelope** row: 30 maps and 960 tower runs, 19.0 h and 10.7 h respectively — so **64 % of the campaign is map building** and the 8760-hour annual simulations, which feel like the expensive part, are 36 % of it.

**The second site is nearly free: 29.7 h against 24.3 h, a +21.9 % increase.** A map is a property of the cycle design, so Objective 5 multiplies only the 40 s tower runs. Costing the climate replication as if it doubled the campaign would have been the obvious pessimistic error, and would have argued for cutting an objective that costs almost nothing.

**The φ = 0 control costs +25.0 %, not +100 %.** It is a single fluid, so it collapses the φ axis to one level while keeping every other map axis — its maps are the nano count divided by the number of φ levels. Objective 4's *every swept point* requirement lands on tower runs, which are the cheap half.

**`d_p` costs nothing and must still be sweep-disciplined.** D6 makes it a null dimension in the nominal, so every plant output is identical across 5-60 nm *by construction*. Sweep it at 2-3 points to demonstrate the flatness in the delivered surface; take the evidence from `scripts/report_htf_properties.py` §4, which shows it at the property level in ~1 s rather than through repeated annual runs.

## 4. Recommendation

1. **Run Morris screening on the `screening (Morris)` row first** (8.8 h). Its purpose under the revised objectives is not pruning — it is a *result*, and it tells you which map-class axes deserve levels in the envelope. Spending map builds before knowing that is the expensive mistake.
2. **Cache maps by cycle-design key, not by grid position.** Two grid points that differ only in SM, t_TES, site or d_p share a map exactly. Without a cache the campaign rebuilds identical maps and the costing above is meaningless.
3. **Do not sweep `T_t_in` and `T_HTF` as independent axes** (they are not independent), and give `f_RC` levels last (it is nearly inert).
4. **Declare the loop-ΔT floor in the methodology as a constraint of the study**, with the −52,858 kW nameplate at 124 K as its evidence.
5. **Collect exergy on every point.** It is already wired in and free at run time (`scripts/exergy.py`), and the three-case run showed it distinguishing conversion quality from resource use in a way annual energy cannot.

---

Generated by `scripts/design_sweep_grid.py` at commit `fd38a00-dirty`.
