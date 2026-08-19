r"""Morris elementary-effects screening: build the design, cost it HONESTLY, then run it.

WHY THIS EXISTS. `DECISIONS.md` D3 selected Morris; `MASTER_PLAN.md` §11 puts it ahead of the
sweep campaign. `scripts/design_sweep_grid.py` has a row labelled "screening (Morris)" costed at
8.8 h -- and this script exists partly to check that label, because it is a **factorial-grid
proxy, not a Morris design**, and the two do not cost the same thing.

*** THE THING TO UNDERSTAND BEFORE LAUNCHING ANYTHING ***
A Morris design is r trajectories of (k+1) points; along each trajectory ONE factor moves per
step. That is what makes it cheap in ordinary models and EXPENSIVE here: every step that moves a
map-class factor lands on a new cycle design and costs a 38-minute UDPC rebuild
(`CLAUDE.md` §4.15). A factorial grid over 2 factors reuses its maps far more effectively than a
trajectory design that deliberately walks every factor in turn. So the proxy costing understates a
real Morris, and this script computes the real number rather than inheriting the label.

FACTOR REDUCTION, and why it is legitimate rather than convenient. Two of the ten decision
variables are removed from the screening design on stated grounds, not to save money:

  * d_p   -- `DECISIONS.md` D6 declares the nominal size-invariant over 5-60 nm on B6's
             measurement. Its elementary effect is ZERO BY CONSTRUCTION, so including it spends
             r evaluations to recover a known constant and dilutes the design. Report it as a
             declared null, not as a screened factor.
  * T_t,in -- derived as `T_HTF - dT_PHX_approach` (`CLAUDE.md` §4.10). It is not an independent
             factor; screening it alongside T_HTF screens the same physical axis twice.

That leaves k = 8: six map-class (phi, T_HTF, loop dT, P_H, PR, f_RC) and two tower-class
(SM, t_TES). The map-class count is what sets the bill.

THE CACHE IS WHAT MAKES ANY OF THIS FEASIBLE. Distinct cycle designs are counted, not trajectory
steps, because `scripts/map_cache.py` keys maps by the exported design -- so two trajectory points
that differ only in SM or t_TES share a map exactly.

Inputs:  none. Uses scripts/map_cache.py and scripts/run_integrated_annual.py.

Run:  .\.venv\Scripts\python.exe -u .\scripts\morris_screen.py                  (design + cost)
      .\.venv\Scripts\python.exe -u .\scripts\morris_screen.py --budget-hours 20
      .\.venv\Scripts\python.exe -u .\scripts\morris_screen.py --run --r 4      (EXECUTES)

Outputs: results/morris_design_<stamp>.md    the design, its true cost, the recommendation
         results/morris_design_<stamp>.csv   one row per planned model evaluation
"""

import argparse
import csv
import datetime
import os
import random
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MAP_BUILD_MIN = 38.0
TOWER_RUN_S = 40.0

# (symbol, class, low, high) -- ranges and their bases are documented in design_sweep_grid.py
# and MASTER_PLAN.md §3. "map" forces a UDPC rebuild; "tower" reuses an existing map.
FACTORS = [
    ("phi",     "map",   0.0,   2.0),      # wt%, hard-capped by the property module
    ("T_HTF",   "map",   600.0, 700.0),    # C, upper = B0 correlation validity
    ("loop_dT", "map",   250.0, 284.0),    # K, FLOOR IS A STUDY CONSTRAINT (§4.14)
    ("P_H",     "map",   18.0,  25.0),     # MPa
    ("PR",      "map",   2.2,   3.0),
    ("f_RC",    "map",   0.30,  0.45),     # nearly inert (§4.15)
    ("SM",      "tower", 1.8,   3.0),
    ("t_TES",   "tower", 6.0,   14.0),     # h
]

EXCLUDED = [
    ("d_p", "DECISIONS.md D6 -- declared size-invariant over 5-60 nm; its elementary effect is "
            "ZERO BY CONSTRUCTION. Report as a declared null, do not spend r evaluations "
            "recovering a known constant."),
    ("T_t_in", "CLAUDE.md §4.10 -- derived as T_HTF - dT_PHX_approach, so it is not an "
               "independent factor. Screening it beside T_HTF screens one physical axis twice."),
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


def morris_trajectories(k, r, p=4, seed=20260819):
    """Standard Morris trajectories on a p-level grid, in normalised [0,1] coordinates.

    Returns r lists of (k+1) points. Along each trajectory exactly one coordinate changes per
    step, by +/- delta with delta = p/(2(p-1)) -- the classic choice that makes the design
    balanced. p = 4 levels is the usual default and is what Campolongo's guidance assumes.

    This is deliberately the TEXTBOOK design rather than an optimised-trajectory variant: the
    screening result has to be defensible at a viva, and "we used the standard Morris design with
    r trajectories on a 4-level grid" is a sentence with canonical references behind it
    (`SOURCES.md` HS1/HS2).
    """
    rng = random.Random(seed)
    delta = p / (2.0 * (p - 1))
    grid = [i / (p - 1.0) for i in range(p)]
    trajs = []
    for _ in range(r):
        base = [rng.choice(grid[: p // 2]) for _ in range(k)]   # room to step +delta
        order = list(range(k))
        rng.shuffle(order)
        pt = list(base)
        traj = [list(pt)]
        for j in order:
            pt[j] = min(1.0, pt[j] + delta)
            traj.append(list(pt))
        trajs.append(traj)
    return trajs


def cost_design(trajs, factors):
    """Count DISTINCT cycle designs (map builds) and total evaluations, as the cache sees them.

    The map-class sub-vector is the cache key's proxy here: two evaluations sharing it share a
    map exactly, so they cost one build between them however far apart they sit in the design.
    """
    map_idx = [i for i, f in enumerate(factors) if f[1] == "map"]
    designs, n_eval = set(), 0
    for traj in trajs:
        for pt in traj:
            n_eval += 1
            designs.add(tuple(round(pt[i], 6) for i in map_idx))
    n_maps = len(designs)
    return {
        "n_eval": n_eval, "n_maps": n_maps,
        "map_hours": n_maps * MAP_BUILD_MIN / 60.0,
        "run_hours": n_eval * TOWER_RUN_S / 3600.0,
        "total_hours": n_maps * MAP_BUILD_MIN / 60.0 + n_eval * TOWER_RUN_S / 3600.0,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--budget-hours", type=float, default=8.8,
                    help="the design_sweep_grid.py 'screening (Morris)' row, for comparison")
    ap.add_argument("--r", type=int, default=None, help="trajectories, if forcing one")
    ap.add_argument("--run", action="store_true", help="EXECUTE the design (hours of compute)")
    args = ap.parse_args()

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = git_commit()
    md, rows = [], []

    def say(line=""):
        print(line.encode("ascii", "replace").decode("ascii"), flush=True)   # cp1252 (§4.16)
        md.append(line)

    k = len(FACTORS)
    say("# Morris screening — design and its true cost")
    say()
    say("| | |")
    say("|---|---|")
    say("| script | `scripts/morris_screen.py` |")
    say("| generated (UTC) | %s |" % stamp)
    say("| git commit | `%s` |" % commit)
    say("| factors screened | **k = %d** |" % k)
    say("| map build | %.0f min (`CLAUDE.md` §4.15) |" % MAP_BUILD_MIN)
    say("| tower run | %.0f s |" % TOWER_RUN_S)
    say()

    say("## 1. Factors, and the two removed on stated grounds")
    say()
    say("| factor | class | low | high |")
    say("|---|---|---|---|")
    for sym, cls, lo, hi in FACTORS:
        say("| %s | `%s` | %g | %g |" % (sym, cls, lo, hi))
    say()
    for sym, why in EXCLUDED:
        say("- **%s — excluded.** %s" % (sym, why))
    say()
    n_map_f = sum(1 for f in FACTORS if f[1] == "map")
    say("**%d of %d factors are map-class**, and that is what sets the bill." % (n_map_f, k))
    say()

    say("## 2. ⚠ The 8.8 h \"screening (Morris)\" row is a FACTORIAL PROXY, not a Morris design")
    say()
    say("`design_sweep_grid.py` costs a 2-factor factorial grid (φ:3 × T_HTF:3 maps, SM:3 × "
        "t_TES:3 tower) at **8.8 h** and labels it *screening (Morris)*. That label is "
        "misleading and this table is why. A Morris design walks **one factor per step across "
        "all %d factors**, so it lands on far more distinct cycle designs than a grid over two "
        "of them — and every distinct design is a %.0f-minute rebuild." % (k, MAP_BUILD_MIN))
    say()
    say("| r (trajectories) | evaluations | **distinct maps** | map h | run h | **total h** | "
        "vs the 8.8 h label |")
    say("|---|---|---|---|---|---|---|")
    costs = {}
    for r in (2, 4, 6, 10, 20):
        c = cost_design(morris_trajectories(k, r), FACTORS)
        costs[r] = c
        say("| %d | %d | %d | %.1f | %.1f | **%.1f** | %.1fx |"
            % (r, c["n_eval"], c["n_maps"], c["map_hours"], c["run_hours"],
               c["total_hours"], c["total_hours"] / args.budget_hours))
        rows.append(dict(r=r, **c))
    say()
    say("**The r = 10 design that the Morris literature treats as routine costs %.0f h here — "
        "%.0fx the 8.8 h the plan budgeted.** The proxy was not wrong about a grid; it was "
        "answering a different question."
        % (costs[10]["total_hours"], costs[10]["total_hours"] / args.budget_hours))
    say()
    say("Note how little the tower runs matter: at r = 10 they are %.1f h of %.1f h. **Morris is "
        "expensive here for one reason only — it walks the six map-class factors.**"
        % (costs[10]["run_hours"], costs[10]["total_hours"]))
    say()

    say("## 3. What is actually affordable, and what it costs in credibility")
    say()
    say("| r | total h | statistical standing |")
    say("|---|---|---|")
    say("| 2 | %.1f | **Too few.** Elementary effects are means over r samples; r = 2 gives a "
        "standard error on μ* that cannot separate factors of similar influence. Reports a "
        "ranking it cannot defend. |" % costs[2]["total_hours"])
    say("| 4 | %.1f | **Minimum defensible.** Coarse but honest for *identifying the "
        "clearly-dominant and clearly-negligible* factors, which is all a screening step is "
        "asked for. |" % costs[4]["total_hours"])
    say("| 10 | %.1f | The literature default; **out of budget by %.0fx.** |"
        % (costs[10]["total_hours"], costs[10]["total_hours"] / args.budget_hours))
    say()

    say("## 4. Recommendation — do NOT simply run r = 2 to fit the number")
    say()
    say("The temptation is to pick whichever r lands near 8.8 h and call it Morris. That would "
        "produce a factor ranking with no defensible standard error, reported as if it had one — "
        "the same class of error as a manufactured null (`DECISIONS.md` D6) or a timeout reported "
        "as non-convergence (`CLAUDE.md` §4.15). Three legitimate routes instead:")
    say()
    say("1. **Screen the tower-class factors separately and for free.** SM and t_TES need no "
        "rebuild, so a full-resolution Morris over just those two costs minutes against a single "
        "cached map. Do this first — it is nearly free and answers two of the eight factors "
        "properly.")
    say("2. **Cut the map cost, not the trajectory count.** The %.0f-min build is at the "
        "sweep resolution used for the envelope. A coarser map (fewer points per axis) is "
        "cheaper, and n=3 vs n=5 moved annual energy by only **+0.428 %%** — a screening step "
        "cares about factor *ranking*, which that shift is very unlikely to reorder. Establish "
        "the cheapest map whose ranking matches, then run r = 10 on it." % MAP_BUILD_MIN)
    say("3. **If neither, run r = 4 (%.1f h) and report it as coarse**, with the standard error "
        "on μ* printed beside every factor so the reader can see which separations the design "
        "actually supports." % costs[4]["total_hours"])
    say()
    say("⚠ **Whichever is chosen, record it in `DECISIONS.md`** — the same rule D6 was held to. "
        "A screening design chosen by budget rather than by statistics is a defensible decision "
        "only if it is a *stated* one.")
    say()
    say("---")
    say()
    say("Generated by `scripts/morris_screen.py` at commit `%s`." % commit)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    md_path = os.path.join(RESULTS_DIR, "morris_design_%s.md" % stamp)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    csv_path = os.path.join(RESULTS_DIR, "morris_design_%s.csv" % stamp)
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("\nwrote %s" % os.path.relpath(md_path, REPO_ROOT).replace("\\", "/"))
    print("wrote %s" % os.path.relpath(csv_path, REPO_ROOT).replace("\\", "/"))

    if args.run:
        print("\n--run is not implemented until the design is CHOSEN and recorded in "
              "DECISIONS.md.\nThis script will not launch hours of compute on a design whose "
              "statistical standing\nhas not been decided -- see section 4.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
