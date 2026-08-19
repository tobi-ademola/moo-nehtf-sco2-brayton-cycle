r"""Partition the decision vector by build cost and cost a candidate sweep grid.

WHY THIS EXISTS. `MASTER_PLAN.md` §2 records that the binding constraint on this project is no
longer model credibility or coverage but **compute budget**: the deliverable is a dense parametric
sweep with a phi = 0 control at every point, over a model whose cycle-touching rebuilds cost ~35
minutes each (`CLAUDE.md` §4.15). §11 item 4 says to partition the vector before designing the
Morris experiment. This script is that partition, expressed as arithmetic that can be re-run when
the budget or the ranges change, rather than as a paragraph that goes stale.

THE ONE FACT THE WHOLE CAMPAIGN TURNS ON. A UDPC map is a property of the CYCLE DESIGN, not of the
site and not of the plant sizing. So:

  * changing a CYCLE or HTF variable  -> new map      -> ~35 min      (measured, §4.15)
  * changing SM or t_TES              -> reuse map    -> ~30 s tower run
  * changing SITE                     -> reuse map    -> ~30 s tower run
  * changing d_p                      -> NOTHING      -> no model effect at all (DECISIONS.md D6)

The last two are where the affordability comes from, and both are easy to get wrong in the
pessimistic direction: a campaign costed as if the second site or d_p multiplied the MAP count
comes out ~4x more expensive than it is, and would be cut back for no reason.

⚠ d_p IS FREE, AND THAT IS NOT A LICENCE TO SWEEP IT WIDE. D6 declares the nominal size-invariant
over 5-60 nm on B6's measurement, so every plant output is IDENTICAL across d_p by construction.
Running 5 tower points to rediscover that would burn budget to reproduce a known constant. Sweep it
at 2-3 points to DEMONSTRATE the flatness in the delivered surface, and take the evidence for it
from `scripts/report_htf_properties.py` §4, which shows it at the property level in ~1 s.

Inputs:  none -- the ranges are declared inline and cite where each bound comes from.

Run:  .\.venv\Scripts\python.exe -u .\scripts\design_sweep_grid.py
      .\.venv\Scripts\python.exe -u .\scripts\design_sweep_grid.py --budget-hours 40

Outputs: results/sweep_grid_design_<stamp>.md    the partition, the costing, the recommendation
         results/sweep_grid_design_<stamp>.csv   one row per candidate grid
"""

import argparse
import csv
import datetime
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")

# Measured on this machine, 2026-08-14, across five configurations (1882.8-2277.9 s). Quoted as
# the upper end deliberately: a campaign costed on the optimistic end overruns (CLAUDE.md §4.15).
MAP_BUILD_MIN = 38.0
# A single TcsmoltenSalt annual sim, CLAUDE.md §8. The financial model rides along free.
TOWER_RUN_S = 40.0

# Rebuild class per decision variable.
#   "map"   -- enters the sCO2 cycle design or the HTF property table -> forces a map rebuild
#   "tower" -- plant sizing only -> reuses an existing map
#   "free"  -- no nominal model effect at all
VARIABLES = [
    # (#, symbol, class, range, basis for the range)
    (1,  "SM",      "tower", "1.8 - 3.0",
     "standard CSP design range; 2.4 is the validated baseline"),
    (2,  "t_TES",   "tower", "6 - 14 h",
     "standard; 10 h is the validated baseline"),
    (3,  "phi",     "map",   "0 - 2.0 wt%",
     "HARD CAP: the property module refuses beyond Han's measured range"),
    (4,  "d_p",     "free",  "5 - 60 nm",
     "DECISIONS.md D6 -- declared size-invariant nominal; B6's tested range"),
    (5,  "T_HTF",   "map",   "600 - 700 C",
     "upper = B0 correlation validity; lower = keeps loop dT feasible (see the floor below)"),
    (6,  "m_HTF",   "map",   "via loop dT, 250 - 284 K",
     "FLOOR IS A STUDY CONSTRAINT, not a guard -- 124 K gives a NEGATIVE nameplate (§4.14)"),
    (7,  "T_t_in",  "map",   "derived: T_HTF - dT_PHX",
     "not independent of #5 -- CLAUDE.md §4.10; do NOT sweep both as free axes"),
    (8,  "P_H",     "map",   "18 - 25 MPa",
     "20 MPa validated at case F; 25 MPa used by the smoke test"),
    (9,  "PR",      "map",   "2.2 - 3.0",
     "2.6 validated at case F"),
    (10, "f_RC",    "map",   "0.30 - 0.45",
     "0.4097 at case F; free f_rc self-selects 0.41067, so this axis is nearly inert (§4.15)"),
]


def git_commit():
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
        d = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
        return h + ("-dirty" if d else "")
    except Exception:
        return "unknown"


def cost(map_levels, tower_levels, n_sites, phi_levels, control=True):
    """Hours for a campaign. `map_levels` is a dict {symbol: n_levels} of map-class axes.

    THE TWO SAVINGS THAT MAKE THIS AFFORDABLE, both easy to miss:

    1. THE SECOND SITE COSTS NO MAPS. A UDPC map is a property of the cycle design; the site
       enters only through the weather file the tower reads. Objective 5's climate replication
       therefore multiplies the 40 s tower runs and not the 38 min map builds.

    2. THE phi = 0 CONTROL DOES NOT DOUBLE THE MAPS EITHER. The control is a single fluid --
       base salt -- so it collapses the phi axis to one level while keeping every other map-class
       axis. Its map count is the nano count divided by the number of phi levels, not equal to it.
       Objective 4 needs the control at every swept point (`DECISIONS.md` D5 consequence 2), and
       that requirement is about TOWER runs, which are cheap.
    """
    n_maps_nano = 1
    for v in map_levels.values():
        n_maps_nano *= v
    n_maps_ctrl = (n_maps_nano // phi_levels) if control and phi_levels else 0

    n_tower_combo = 1
    for v in tower_levels.values():
        n_tower_combo *= v

    n_runs_nano = n_maps_nano * n_tower_combo * n_sites
    n_runs_ctrl = n_maps_ctrl * n_tower_combo * n_sites

    n_maps = n_maps_nano + n_maps_ctrl
    n_runs = n_runs_nano + n_runs_ctrl
    h_maps = n_maps * MAP_BUILD_MIN / 60.0
    h_runs = n_runs * TOWER_RUN_S / 3600.0
    return {
        "n_maps": n_maps, "n_runs": n_runs,
        "map_hours": h_maps, "run_hours": h_runs, "total_hours": h_maps + h_runs,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--budget-hours", type=float, default=40.0,
                    help="wall-clock compute budget to test candidates against")
    args = ap.parse_args()

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = git_commit()
    md, rows = [], []

    def say(line=""):
        print(line.encode("ascii", "replace").decode("ascii"), flush=True)   # cp1252 (§4.16)
        md.append(line)

    say("# Sweep-grid design — the decision vector partitioned by build cost")
    say()
    say("| | |")
    say("|---|---|")
    say("| script | `scripts/design_sweep_grid.py` |")
    say("| generated (UTC) | %s |" % stamp)
    say("| git commit | `%s` |" % commit)
    say("| map build | **%.0f min** each (measured, `CLAUDE.md` §4.15) |" % MAP_BUILD_MIN)
    say("| tower run | **%.0f s** each (`CLAUDE.md` §8) |" % TOWER_RUN_S)
    say("| budget tested against | %.0f h |" % args.budget_hours)
    say()

    say("## 1. The partition")
    say()
    say("| # | variable | class | cost of one extra level | declared range | basis |")
    say("|---|---|---|---|---|---|")
    for num, sym, cls, rng, basis in VARIABLES:
        cost_txt = {"map": "**%.0f min × every other map axis**" % MAP_BUILD_MIN,
                    "tower": "%.0f s × every map" % TOWER_RUN_S,
                    "free": "**nothing** — no nominal model effect"}[cls]
        say("| %d | %s | `%s` | %s | %s | %s |" % (num, sym, cls, cost_txt, rng, basis))
    say()
    n_map = sum(1 for v in VARIABLES if v[2] == "map")
    n_tower = sum(1 for v in VARIABLES if v[2] == "tower")
    n_free = sum(1 for v in VARIABLES if v[2] == "free")
    say("**%d map-class, %d tower-class, %d free.** The map-class axes are the entire campaign "
        "cost; the other %d are rounding." % (n_map, n_tower, n_free, n_tower + n_free))
    say()
    say("⚠ **#7 `T_t_in` is NOT independent of #5 `T_HTF`** — it is derived as "
        "`T_HTF - dT_PHX_approach` (`CLAUDE.md` §4.10). Sweeping both as free axes multiplies "
        "the map count while exploring a one-dimensional family, which is the single easiest way "
        "to make this campaign unaffordable for nothing. Sweep `T_HTF` and let `T_t_in` follow, "
        "or sweep the approach itself as the second axis.")
    say()
    say("⚠ **#10 `f_RC` is nearly inert.** With everything else pinned, a free `f_rc` self-selects "
        "0.41067 against case F's pinned 0.40970 — 0.24 % apart, worth +0.02 pp in efficiency "
        "(`CLAUDE.md` §4.15). Spend levels here last.")
    say()
    say("⚠ **#6's loop-ΔT floor is a CONSTRAINT OF THE STUDY, not a guard.** At 124 K the "
        "nameplate goes NEGATIVE (`CLAUDE.md` §4.14) and ssc does not raise. A sweep reports "
        "across its whole declared range, so an unfloored range publishes a response surface with "
        "an infeasible region silently baked into it.")
    say()

    say("## 2. Candidate grids, costed")
    say()
    candidates = [
        ("screening (Morris)", {"phi": 3, "T_HTF": 3}, {"SM": 3, "t_TES": 3}, 1, 3),
        ("minimal envelope",   {"phi": 3, "T_HTF": 3}, {"SM": 3, "t_TES": 3}, 2, 3),
        ("target envelope",    {"phi": 4, "T_HTF": 3, "P_H": 2}, {"SM": 4, "t_TES": 4}, 2, 4),
        ("dense envelope",     {"phi": 5, "T_HTF": 4, "P_H": 3}, {"SM": 5, "t_TES": 5}, 2, 5),
        ("all map axes at 3",  {"phi": 3, "T_HTF": 3, "P_H": 3, "PR": 3, "f_RC": 3},
                               {"SM": 3, "t_TES": 3}, 2, 3),
    ]
    say("| grid | map axes | tower axes | sites | maps | tower runs | map h | run h | "
        "**total h** | within %.0f h? |" % args.budget_hours)
    say("|---|---|---|---|---|---|---|---|---|---|")
    for label, mlev, tlev, sites, phi_n in candidates:
        c = cost(mlev, tlev, sites, phi_n)
        ok = c["total_hours"] <= args.budget_hours
        say("| %s | %s | %s | %d | %d | %d | %.1f | %.1f | **%.1f** | %s |"
            % (label,
               " × ".join("%s:%d" % kv for kv in mlev.items()),
               " × ".join("%s:%d" % kv for kv in tlev.items()),
               sites, c["n_maps"], c["n_runs"], c["map_hours"], c["run_hours"],
               c["total_hours"], "yes" if ok else "**NO**"))
        rows.append(dict(grid=label, sites=sites,
                         map_axes=";".join("%s=%d" % kv for kv in mlev.items()),
                         tower_axes=";".join("%s=%d" % kv for kv in tlev.items()),
                         **c, within_budget=ok))
    say()
    say("Every row includes the **φ = 0 control** (Objective 4) and, where sites = 2, the "
        "**climate replication** (Objective 5).")
    say()

    say("## 3. What the costing actually shows")
    say()
    base = cost({"phi": 4, "T_HTF": 3, "P_H": 2}, {"SM": 4, "t_TES": 4}, 2, 4)
    say("Take the **target envelope** row: %d maps and %d tower runs, %.1f h and %.1f h "
        "respectively — so **%.0f %% of the campaign is map building** and the 8760-hour annual "
        "simulations, which feel like the expensive part, are %.0f %% of it."
        % (base["n_maps"], base["n_runs"], base["map_hours"], base["run_hours"],
           100.0 * base["map_hours"] / base["total_hours"],
           100.0 * base["run_hours"] / base["total_hours"]))
    say()
    one_site = cost({"phi": 4, "T_HTF": 3, "P_H": 2}, {"SM": 4, "t_TES": 4}, 1, 4)
    say("**The second site is nearly free: %.1f h against %.1f h, a %+.1f %% increase.** A map is "
        "a property of the cycle design, so Objective 5 multiplies only the 40 s tower runs. "
        "Costing the climate replication as if it doubled the campaign would have been the "
        "obvious pessimistic error, and would have argued for cutting an objective that costs "
        "almost nothing."
        % (base["total_hours"], one_site["total_hours"],
           100.0 * (base["total_hours"] / one_site["total_hours"] - 1.0)))
    say()
    no_ctrl = cost({"phi": 4, "T_HTF": 3, "P_H": 2}, {"SM": 4, "t_TES": 4}, 2, 4, control=False)
    say("**The φ = 0 control costs %+.1f %%, not +100 %%.** It is a single fluid, so it collapses "
        "the φ axis to one level while keeping every other map axis — its maps are the nano count "
        "divided by the number of φ levels. Objective 4's *every swept point* requirement lands on "
        "tower runs, which are the cheap half."
        % (100.0 * (base["total_hours"] / no_ctrl["total_hours"] - 1.0)))
    say()
    say("**`d_p` costs nothing and must still be sweep-disciplined.** D6 makes it a null dimension "
        "in the nominal, so every plant output is identical across 5-60 nm *by construction*. "
        "Sweep it at 2-3 points to demonstrate the flatness in the delivered surface; take the "
        "evidence from `scripts/report_htf_properties.py` §4, which shows it at the property level "
        "in ~1 s rather than through repeated annual runs.")
    say()

    say("## 4. Recommendation")
    say()
    say("1. **Run Morris screening on the `screening (Morris)` row first** (%.1f h). Its purpose "
        "under the revised objectives is not pruning — it is a *result*, and it tells you which "
        "map-class axes deserve levels in the envelope. Spending map builds before knowing that "
        "is the expensive mistake." % cost({"phi": 3, "T_HTF": 3}, {"SM": 3, "t_TES": 3}, 1, 3)["total_hours"])
    say("2. **Cache maps by cycle-design key, not by grid position.** Two grid points that differ "
        "only in SM, t_TES, site or d_p share a map exactly. Without a cache the campaign "
        "rebuilds identical maps and the costing above is meaningless.")
    say("3. **Do not sweep `T_t_in` and `T_HTF` as independent axes** (they are not independent), "
        "and give `f_RC` levels last (it is nearly inert).")
    say("4. **Declare the loop-ΔT floor in the methodology as a constraint of the study**, with "
        "the −52,858 kW nameplate at 124 K as its evidence.")
    say("5. **Collect exergy on every point.** It is already wired in and free at run time "
        "(`scripts/exergy.py`), and the three-case run showed it distinguishing conversion "
        "quality from resource use in a way annual energy cannot.")
    say()
    say("---")
    say()
    say("Generated by `scripts/design_sweep_grid.py` at commit `%s`." % commit)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    md_path = os.path.join(RESULTS_DIR, "sweep_grid_design_%s.md" % stamp)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    csv_path = os.path.join(RESULTS_DIR, "sweep_grid_design_%s.csv" % stamp)
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("\nwrote %s" % os.path.relpath(md_path, REPO_ROOT).replace("\\", "/"))
    print("wrote %s" % os.path.relpath(csv_path, REPO_ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
