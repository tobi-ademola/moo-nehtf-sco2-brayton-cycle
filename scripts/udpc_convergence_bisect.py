r"""Find the convergence boundary for UDPC generation by bisecting FROM the loose bundle.

MASTER_PLAN.md §11 item 2 -- the single thing blocking the guaranteed deliverable.

THE PROBLEM, RESTATED SO THIS FILE STANDS ALONE. `scripts/build_udpc_map.py` solves the
validated case F cycle design in 0.1 s, but turning on the off-design sweep
(`is_generate_udpc = 1`) then fails to complete in 5-16 minutes. Seven single-variable
deviations FROM case F were tested in the previous session and every one still hung (the
custom fluid, free f_rc, free pressures, rel_tol, recuperator code 3, design_method 1 and 2,
narrowed sweep corners). What DOES converge -- in 93.6 s -- is the whole loose bundle at once:
design_method = 1, free f_rc, free pressures, stock tolerance. It returns `recomp_frac = 0.0`,
i.e. the cycle collapsed to simple recuperated (CLAUDE.md §4.3).

    Conclusion carried in: it is not one bad setting. The boundary is a COMBINATION inside
    {design_method, f_rc pinning, pressure pinning, rel_tol}.

*** 2026-08-14 -- THE STAGE-1 CONTROL FAILURE IS EXPLAINED, AND IT VOIDS STAGE 1 ENTIRELY. ***

The stage-1 control (`loose_all`) timed out at 360 s on 2026-08-13 although the previous session
recorded the same bundle converging in 93.6 s. Three runs settle it, and the explanation is not
machine load and not this harness:

    case F, design only, direct through build_udpc_map.py   ->  0.1 s, f_rc 0.40970, eta 0.50547
    case F, design only, THROUGH THIS HARNESS               ->  0.1 s, f_rc 0.40970, eta 0.50547
    loose_all, design only (`--sweep 0`, sweep switched OFF) ->  TIMEOUT at 300 s

The harness is exonerated: it reproduces case F to every printed digit. What the third run shows
is that THE LOOSE BUNDLE HANGS IN THE DESIGN SOLVE, with no off-design sweep running at all.

    A design-only solve cannot be slower than the same configuration WITH the sweep added, so
    the earlier session's 93.6 s figure cannot have come from this configuration. Whatever the
    93.6 s run was, it is not `loose_all` as defined here, and the 93.6 s number must not be
    carried forward as if it were.

The consequence for stage 1 is structural, not a matter of re-running it at a longer timeout.
Every stage-1 cell is "LOOSE except one knob", so every one of them inherits the hanging design
configuration. A stage-1 timeout therefore CANNOT distinguish "this knob broke map generation"
from "this cell never reached a design point". Stage 1's five recorded FAILs are uninterpretable
as knob evidence -- not weak evidence, no evidence -- and stage 3 exists to replace them.

WHY THIS SCRIPT BISECTS THE OTHER WAY. Searching down from case F is exhausted -- all seven
cells are negative, and each negative costs a full timeout (~5+ min). Searching up from the
loose bundle costs ~1.5 min per success instead. It also answers a sharper question: the goal
is not "does it converge" but "does it converge WHILE STILL BEING A RECOMPRESSION CYCLE", and
only the f_rc knob decides that. So the critical cell is `loose + pinned f_rc`, and it is run
first after the control.

VERDICT RULE. A case is USABLE only if all three hold:
    converged within the timeout, AND recomp_frac > 1e-6, AND the per-axis tables are non-empty.
A run that converges at recomp_frac = 0 is a FAILURE for this project's purpose even though ssc
calls it a success -- that is the §4.3 collapse, and it is not the validated cycle.

EVERY CASE RUNS IN ITS OWN SUBPROCESS. Two independent reasons, both from CLAUDE.md §4:
a hang cannot be interrupted in-process, and bad input VALUES segfault the interpreter rather
than raising (§4.2), which would otherwise lose the whole sweep. The worker prints a single
`##RESULT## {json}` line; the driver parses it and records a timeout or crash as data.

Inputs:  scripts/build_udpc_map.py  -- build() is reused so the case F constants stay in ONE
                                       place; this script only overrides the knobs under test.
         scripts/validate_dostal.py -- reached through build_udpc_map, not retyped.
         Requires the .venv of CLAUDE.md §1.

Run:  # stage 3 design-only first -- cheap, and it is the direction with a good origin:
      .\.venv\Scripts\python.exe -u .\scripts\udpc_convergence_bisect.py --stage 3 --sweep 0
      # then only the cells that passed, with the sweep on:
      .\.venv\Scripts\python.exe -u .\scripts\udpc_convergence_bisect.py --only F_loose_frc
      .\.venv\Scripts\python.exe -u .\scripts\udpc_convergence_bisect.py --list

Outputs: results/udpc_bisect_<stamp>.md    the report + verdict
         results/udpc_bisect_<stamp>.csv   one row per case, machine-readable
"""

import argparse
import csv
import datetime
import json
import math
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Bisection uses 3 points per axis: the question is whether the solver converges AT ALL, not
# map resolution. The winner gets re-run at 5 by build_udpc_map.py afterwards.
N_POINTS_DEFAULT = 3

# The known-good loose bundle converges in 93.6 s; the known failures ran past 5 min. 360 s
# separates the two cleanly. Any case that lands near the ceiling is re-run longer by hand --
# the report prints the margin so that is visible rather than assumed.
TIMEOUT_S_DEFAULT = 360

# design_method 1 targets an efficiency. 0.50 is used rather than case F's 0.5127 because the
# map runs at TIT 680 C (build_udpc_map.py docstring), where 0.5127 is not reachable and an
# unreachable target is itself a plausible non-convergence cause -- which would confound the
# knob under test.
ETA_TARGET_LOOSE = 0.50


# =============================================================================
# The knob lattice
# =============================================================================
# Each knob is binary: "loose" (as in the bundle that converges) or "tight" (as in case F).
KNOBS = ("design_method", "f_rc", "pressure", "rel_tol")

LOOSE = {"design_method": "loose", "f_rc": "loose", "pressure": "loose", "rel_tol": "loose"}
CASE_F = {"design_method": "tight", "f_rc": "tight", "pressure": "tight", "rel_tol": "tight"}


def _cfg(**tight):
    """A config equal to LOOSE except for the named knobs, which are set tight."""
    c = dict(LOOSE)
    for k in tight:
        if k not in KNOBS:
            raise KeyError("unknown knob %r; known: %s" % (k, ", ".join(KNOBS)))
        c[k] = "tight"
    return c


def _cfg_from_F(**loose):
    """A config equal to CASE_F except for the named knobs, which are set loose.

    Added 2026-08-14, and the reason is the whole point of stage 3. Stage 1 walks OUTWARD FROM
    THE LOOSE BUNDLE, so every one of its cells inherits `design_method = 1` with free pressures
    -- and that combination is now known to hang IN THE DESIGN SOLVE, with the off-design sweep
    switched off entirely (`--sweep 0`, verified this session at a 300 s timeout while case F
    solves the same way in 0.1 s). Stage 1's origin is therefore degenerate: its cells cannot
    distinguish "this knob broke the sweep" from "this configuration never reached a design
    point at all", which is the real reason the stage-1 control did not reproduce.

    Walking from case F instead gives every cell a known-good origin. It is also cheap now that
    the sweep can be disabled: a design-only cell costs 0.1 s when it converges, against the
    5+ minute timeouts that made this direction look unaffordable.
    """
    c = dict(CASE_F)
    for k in loose:
        if k not in KNOBS:
            raise KeyError("unknown knob %r; known: %s" % (k, ", ".join(KNOBS)))
        c[k] = "loose"
    return c


# Stage 1 -- the control plus every single tightening. Ordered by value, not by lattice
# position: pin_frc is the only knob that can restore the recompression cycle, so it goes
# first after the control.
PLAN = {
    "loose_all":  (1, dict(LOOSE),                  "VOID control: hangs in the DESIGN solve (2026-08-14)"),
    "pin_frc":    (1, _cfg(f_rc=1),                 "loose + PINNED f_rc  <-- the critical cell"),
    "pin_press":  (1, _cfg(pressure=1),             "loose + pinned P_high and PR"),
    "pin_dm":     (1, _cfg(design_method=1),        "loose + design_method 3 (recuperators specified)"),
    "pin_tol":    (1, _cfg(rel_tol=1),              "loose + rel_tol 4"),

    # Stage 2 -- pairs built on whichever single tightenings survived. Run after stage 1 so the
    # pairs are chosen with evidence rather than guessed.
    "frc_press":  (2, _cfg(f_rc=1, pressure=1),     "pinned f_rc + pinned pressures"),
    "frc_dm":     (2, _cfg(f_rc=1, design_method=1), "pinned f_rc + design_method 3"),
    "frc_tol":    (2, _cfg(f_rc=1, rel_tol=1),      "pinned f_rc + rel_tol 4"),
    "frc_press_tol": (2, _cfg(f_rc=1, pressure=1, rel_tol=1),
                      "pinned f_rc + pressures + rel_tol (all but design_method)"),
    "case_F":     (2, dict(CASE_F),                 "full case F -- expected to hang; the anchor"),

    # Stage 3 -- the SAME lattice walked from the other origin: case F with ONE knob loosened.
    # Run these with `--sweep 0` first. That separates the two failure modes stage 1 conflates:
    # a cell that fails design-only never reached a design point, so it says nothing whatever
    # about map generation; only a cell that passes design-only and then fails with `--sweep 1`
    # is evidence about the sweep.
    "F_loose_dm":    (3, _cfg_from_F(design_method=1), "case F but design_method 1 (target eta)"),
    "F_loose_frc":   (3, _cfg_from_F(f_rc=1),          "case F but f_rc free  <-- costs the cycle"),
    "F_loose_press": (3, _cfg_from_F(pressure=1),      "case F but pressures free"),
    "F_loose_tol":   (3, _cfg_from_F(rel_tol=1),       "case F but rel_tol 3"),
}


def describe(cfg):
    return " ".join("%s=%s" % (k, cfg[k][0].upper()) for k in KNOBS)


# =============================================================================
# Worker -- one case, in its own process
# =============================================================================
def apply_env(m, htf, ranges, sweep, htf_mins):
    """Apply the ENVIRONMENT of the run -- everything that is not one of the four knobs.

    Added 2026-08-13 after the stage-1 control (`loose_all`, the bundle the previous session
    recorded as converging in 93.6 s) TIMED OUT at 360 s. A failed control voids the stage: with
    it failing, a knob timing out cannot be distinguished from nothing converging at all. These
    switches exist to locate the discrepancy, since the previous session's record does not state
    which fluid, sweep ranges or corner guard the 93.6 s run used.
    """
    import nanofluid_properties as nfp
    import build_udpc_map as bum

    c = m.Common
    c.is_generate_udpc = 1 if sweep else 0
    c.is_apply_default_htf_mins = htf_mins

    if htf == "nitrate":
        m.SystemDesign.htf = 17                  # SAM's built-in 60/40 NaNO3-KNO3
        try:
            del m.SystemDesign.htf_props         # a stale table alongside htf=17 is ambiguous
        except Exception:
            m.SystemDesign.htf_props = nfp.htf_table_rows(0.0, bum.HTF_T_GRID)

    if ranges == "narrow":
        # Deep turndown and wide ambient are where the off-design solver loses corners.
        c.T_htf_hot_low, c.T_htf_hot_high = 680.0, 710.0
        c.T_amb_low, c.T_amb_high = 15.0, 40.0
        c.m_dot_htf_ND_low, c.m_dot_htf_ND_high = 0.85, 1.05
    return m


def apply_knobs(m, cfg):
    """Override build_udpc_map.build()'s case F settings with the knob configuration.

    build() is left as the single source of the case F constants; this only moves the four
    knobs under test, so a case cannot silently differ from case F in some fifth way.
    """
    import validate_dostal as vd

    d, x = m.SystemDesign, m.HeatExchangerDesign

    if cfg["design_method"] == "loose":
        d.design_method = 1                      # target efficiency; solver sizes recuperators
        d.eta_thermal_des = ETA_TARGET_LOOSE
    else:
        d.design_method = 3                      # specify each recuperator (case F)

    if cfg["f_rc"] == "loose":
        x.is_recomp_ok = 1                       # solver free to choose -- may collapse to 0
    else:
        x.is_recomp_ok = -abs(vd.F_RECOMP)       # negative => PIN (CLAUDE.md §4.3)

    if cfg["pressure"] == "loose":
        x.is_P_high_fixed = 0
        x.is_PR_fixed = 0
    else:
        x.is_P_high_fixed = 1
        x.is_PR_fixed = vd.PRESSURE_RATIO

    x.rel_tol = 3 if cfg["rel_tol"] == "loose" else 4
    return m


def run_case(name, n_points, phi, htf="nano", ranges="wide", sweep=1, htf_mins=1):
    """Solve one configuration with the off-design sweep ON. Returns a JSON-able dict."""
    import build_udpc_map as bum

    cfg = PLAN[name][1]
    m = bum.build(phi, bum.T_HTF_HOT_DES_C, n_points)
    apply_env(m, htf, ranges, sweep, htf_mins)
    apply_knobs(m, cfg)

    t0 = time.time()
    m.execute(0)
    wall = time.time() - t0

    o = m.Outputs
    res = {
        "case": name, "wall_s": wall, "status": "ok",
        "htf": htf, "ranges": ranges, "sweep": sweep, "htf_mins": htf_mins,
        "eta": float(o.eta_thermal_calc), "recomp_frac": float(o.recomp_frac),
        "P_comp_in": float(o.P_comp_in), "P_comp_out": float(o.P_comp_out),
        "eff_HTR": float(o.eff_HTR), "eff_LTR": float(o.eff_LTR),
        "T_turb_in": float(o.T_turb_in),
        "q_dot_HTR_nan": bool(math.isnan(o.q_dot_HTR)),
    }
    # The sweep's actual product. A "converged" run with empty tables is not usable.
    if sweep:
        try:
            res["n_axis_rows"] = len([list(r) for r in o.T_htf_ind])
        except Exception as exc:
            res["n_axis_rows"] = 0
            res["axis_error"] = str(exc)
    return res


def verdict(res):
    """USABLE requires convergence AND a live recompression cycle AND a non-empty map."""
    if res.get("status") != "ok":
        return "FAIL(%s)" % res.get("status")
    if not (res.get("recomp_frac", 0.0) > 1e-6):
        return "COLLAPSED"            # ssc calls it success; §4.3 says it is not our cycle
    if res.get("q_dot_HTR_nan"):
        return "COLLAPSED"
    if not res.get("sweep", 1):
        return "DESIGN_OK"            # sweep disabled: says nothing about map generation
    if not res.get("n_axis_rows"):
        return "EMPTY_MAP"
    return "USABLE"


# =============================================================================
# Driver
# =============================================================================
def spawn(name, n_points, phi, timeout_s, env):
    """Run one case in a subprocess so a hang or a segfault is DATA, not a lost session."""
    cmd = [sys.executable, "-u", os.path.abspath(__file__),
           "--case", name, "--n-points", str(n_points), "--phi", str(phi),
           "--htf", env["htf"], "--ranges", env["ranges"],
           "--sweep", str(env["sweep"]), "--htf-mins", str(env["htf_mins"])]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                           timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return {"case": name, "status": "timeout", "wall_s": float(timeout_s)}

    wall = time.time() - t0
    for line in (p.stdout or "").splitlines():
        if line.startswith("##RESULT##"):
            res = json.loads(line[len("##RESULT##"):])
            res["wall_s"] = res.get("wall_s", wall)
            return res

    # No result line: ssc crashed the interpreter (CLAUDE.md §4.2/§4.8) or raised.
    tail = ((p.stderr or "").strip().splitlines() or ["<no stderr>"])[-3:]
    return {"case": name, "status": "crash(rc=%s)" % p.returncode, "wall_s": wall,
            "detail": " | ".join(tail)}


def git_commit():
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
        d = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
        return h + ("-dirty" if d else "")
    except Exception:
        return "unknown"


FIELDS = ("case", "knobs", "verdict", "status", "wall_s", "recomp_frac", "eta",
          "P_comp_in", "P_comp_out", "eff_HTR", "eff_LTR", "n_axis_rows",
          "htf", "ranges", "sweep", "htf_mins", "detail")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", help="worker mode: run this one case and print ##RESULT## json")
    ap.add_argument("--only", help="comma-separated case names to run (overrides --stage)")
    ap.add_argument("--stage", type=int, default=1,
                    help="1 = control + single tightenings FROM the loose bundle (its origin is "
                         "degenerate -- see _cfg_from_F); 2 = pairs; 3 = single LOOSENINGS from "
                         "case F, the direction with a known-good origin. Run stage 3 with "
                         "--sweep 0 first.")
    ap.add_argument("--n-points", type=int, default=N_POINTS_DEFAULT)
    ap.add_argument("--phi", type=float, default=0.007)
    ap.add_argument("--timeout", type=int, default=TIMEOUT_S_DEFAULT, help="seconds per case")
    ap.add_argument("--list", action="store_true", help="print the plan and exit")
    # Environment switches -- NOT knobs under test. Added to chase the failed stage-1 control.
    ap.add_argument("--htf", choices=("nano", "nitrate"), default="nano")
    ap.add_argument("--ranges", choices=("wide", "narrow"), default="wide")
    ap.add_argument("--sweep", type=int, choices=(0, 1), default=1,
                    help="0 = design point only; proves the harness without the sweep")
    ap.add_argument("--htf-mins", type=int, choices=(0, 1), default=1,
                    help="Common.is_apply_default_htf_mins (the sweep-corner guard)")
    args = ap.parse_args()
    env = {"htf": args.htf, "ranges": args.ranges,
           "sweep": args.sweep, "htf_mins": args.htf_mins}

    if args.list:
        for name, (stage, cfg, note) in PLAN.items():
            print("  stage %d  %-14s  %-45s  %s" % (stage, name, describe(cfg), note))
        return 0

    if args.case:                                    # ---- worker ----
        res = run_case(args.case, args.n_points, args.phi,
                       args.htf, args.ranges, args.sweep, args.htf_mins)
        print("##RESULT##" + json.dumps(res), flush=True)
        return 0

    # ---- driver ----
    if args.only:
        names = [n.strip() for n in args.only.split(",") if n.strip()]
        bad = [n for n in names if n not in PLAN]
        if bad:
            print("unknown case(s): %s" % ", ".join(bad), file=sys.stderr)
            return 2
    else:
        names = [n for n, (stage, _, _) in PLAN.items() if stage == args.stage]

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = git_commit()
    report = []

    def say(line=""):
        print(line, flush=True)
        report.append(line)

    say("=" * 100)
    say("UDPC CONVERGENCE BISECTION -- searching UP from the loose bundle toward case F")
    say("  %d cases, %d points per axis, %d s timeout each, phi %.4f"
        % (len(names), args.n_points, args.timeout, args.phi))
    say("  environment: htf=%s  ranges=%s  sweep=%d  htf_mins=%d"
        % (args.htf, args.ranges, args.sweep, args.htf_mins))
    say("  USABLE = converged AND recomp_frac > 0 AND non-empty map")
    say("=" * 100)

    rows = []
    for i, name in enumerate(names, 1):
        stage, cfg, note = PLAN[name]
        say("\n[%d/%d] %-14s  %s" % (i, len(names), name, note))
        say("        knobs: %s" % describe(cfg))
        res = spawn(name, args.n_points, args.phi, args.timeout, env)
        v = verdict(res)
        res.update(case=name, knobs=describe(cfg), verdict=v)
        rows.append(res)

        if v == "DESIGN_OK":
            say("        -> DESIGN_OK in %.1f s   recomp_frac %.5f   eta %.5f  (sweep disabled)"
                % (res["wall_s"], res["recomp_frac"], res["eta"]))
        elif v == "USABLE":
            say("        -> USABLE in %.1f s   recomp_frac %.5f   eta %.5f   map %d rows"
                % (res["wall_s"], res["recomp_frac"], res["eta"], res["n_axis_rows"]))
        elif v == "COLLAPSED":
            say("        -> COLLAPSED in %.1f s  recomp_frac %.5f (eta %.5f) -- ssc calls this"
                % (res["wall_s"], res["recomp_frac"], res["eta"]))
            say("           a success; CLAUDE.md §4.3 says it is not the validated cycle.")
        elif res.get("status") == "timeout":
            say("        -> TIMEOUT at %.0f s (did not converge)" % res["wall_s"])
        else:
            say("        -> %s after %.1f s  %s"
                % (v, res.get("wall_s", 0.0), res.get("detail", "")))

    # ---- summary ----
    say("\n" + "=" * 100)
    say("%-14s  %-45s  %-10s  %8s  %10s  %8s" % ("case", "knobs", "verdict", "wall s",
                                                 "recomp_f", "eta"))
    say("-" * 100)
    for r in rows:
        say("%-14s  %-45s  %-10s  %8.1f  %10s  %8s"
            % (r["case"], r["knobs"], r["verdict"], r.get("wall_s", 0.0),
               ("%.5f" % r["recomp_frac"]) if "recomp_frac" in r else "-",
               ("%.5f" % r["eta"]) if "eta" in r else "-"))

    usable = [r for r in rows if r["verdict"] == "USABLE"]
    say("")
    if usable:
        say("VERDICT: %d configuration(s) both converge and keep the recompression cycle:"
            % len(usable))
        for r in usable:
            say("   %-14s  %s   recomp_frac %.5f, eta %.5f"
                % (r["case"], r["knobs"], r["recomp_frac"], r["eta"]))
        say("Next: re-run the tightest USABLE case at full resolution through")
        say("      scripts/build_udpc_map.py, and measure its f_rc/eta gap against case F.")
    else:
        say("VERDICT: no configuration in this set is usable. Every one either failed to")
        say("         converge or collapsed to recomp_frac = 0 (CLAUDE.md §4.3).")

    # ---- durable output (CLAUDE.md §0 rule 2) ----
    os.makedirs(RESULTS_DIR, exist_ok=True)
    csv_path = os.path.join(RESULTS_DIR, "udpc_bisect_%s.csv" % stamp)
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    md_path = os.path.join(RESULTS_DIR, "udpc_bisect_%s.md" % stamp)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# UDPC convergence bisection (from the loose bundle toward case F)\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/udpc_convergence_bisect.py` |\n"
                 "| run (UTC) | %s |\n| git commit | `%s` |\n"
                 "| PySAM | 7.1.1.post1 (bundled ssc 306) |\n"
                 "| points per axis | %d |\n| timeout per case | %d s |\n| phi | %.4f |\n\n"
                 "```\n%s\n```\n" % (stamp, commit, args.n_points, args.timeout,
                                     args.phi, "\n".join(report)))

    print("\nresults written (commit %s):" % commit)
    for p in (md_path, csv_path):
        print("   %s" % os.path.relpath(p, REPO_ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
