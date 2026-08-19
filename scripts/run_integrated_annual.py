r"""Run the INTEGRATED plant: nano-chloride tower + sCO2 UDPC power block, 8760 h.

MASTER_PLAN.md §11 item 2, the last step of Objective 2. Every other module in this project has
been verified in isolation; this is the first script that runs them TOGETHER for a full year and
reports an annual number for the sCO2 plant.

WHAT IT JOINS.
    scripts/nanofluid_properties.py  -> the 7-column HTF table (rec_htf = 50, CLAUDE.md §6)
    scripts/build_udpc_map.py        -> the UDPC performance map + the design magnitudes
    scripts/htf_sam_bridge.py        -> the tower builder, the annual extractor and the
                                        `system_capacity > 0` screen, reused rather than retyped
    TcsmoltenSalt                    -> heliostats, receiver, TES, dispatch, hydraulics

NOTHING HERE IS HARDCODED FROM A PREVIOUS RUN. The design efficiency, the cold-tank temperature
and the cooling fraction are all taken from a live 0.1 s design solve of the same case F cycle
the map was generated from, so this script cannot silently drift away from its own map.

THE COMPARISON THAT MATTERS, and why the steam control is in here. `THESIS_SYNTHESIS.md` §7.5
reports the chloride trailing nitrate by 9.6 % on annual energy and attributes it to the power
block still being SAM's steam Rankine, which cannot exploit a 700 C source. That attribution was
an INFERENCE. The `steam_same_T` case tests it: identical fluid, identical loop temperatures,
identical field -- only `pc_config` differs. Any difference is the power block and nothing else.

*** THE NUMBER TO WATCH IS THE LOOP dT, AND IT IS NOT COMFORTABLE. ***
The sCO2 recompression cycle is heavily recuperated, so it returns HTF hot: T_htf_cold_des comes
out near 533 C against a 700 C source, i.e. a loop dT of only ~167 K. `THESIS_SYNTHESIS.md` §7.4
measured W_pump ~ dT^-2.56 on this fluid and found 124 K INFEASIBLE (negative nameplate) and
250 K feasible. 167 K sits between them, untested. If the nameplate comes out negative here that
is not a bug -- it is the recuperation/pumping tension the integrated model exists to expose, and
it must be reported, not tuned away. Screen every case on `system_capacity > 0` (CLAUDE.md §4.14).

Inputs:  maps/sco2_udpc_phi<phi>_n<N>_tower7.csv  (build with scripts/build_udpc_map.py)
         data/tmy/158192_31.05_-6.86_tmy-2022.csv (Morocco/Ouarzazate, CLAUDE.md §5)
         Requires the .venv of CLAUDE.md §1.

Run:  .\.venv\Scripts\python.exe -u .\scripts\run_integrated_annual.py
      .\.venv\Scripts\python.exe -u .\scripts\run_integrated_annual.py --only sco2_n3
      .\.venv\Scripts\python.exe -u .\scripts\run_integrated_annual.py --list

Outputs: results/integrated_annual_<stamp>.md
         results/integrated_annual_<stamp>.csv
"""

import argparse
import csv
import datetime
import json
import math
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
MAPS_DIR = os.path.join(REPO_ROOT, "maps")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PHI = 0.007
P_REF_MW = 115.0

# An annual TcsmoltenSalt run is ~20-40 s (CLAUDE.md §8). 900 s is a wide margin -- and after
# the UDPC episode (CLAUDE.md §4.15) the margin is deliberate: a timeout here would otherwise be
# recorded as a failure when it is only slowness.
TIMEOUT_S = 900


def map_path(n_points, phi=PHI):
    tag = ("phi%.4f_n%d" % (phi, n_points)).replace(".", "p")
    return os.path.join(MAPS_DIR, "sco2_udpc_%s_tower7.csv" % tag)


def load_map(path):
    """Read a 7-column combined table back off disk, with the shape contract enforced."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            "map not found: %s -- build it with scripts/build_udpc_map.py --n-points N "
            "(~35 min, CLAUDE.md §4.15)" % os.path.relpath(path, REPO_ROOT))
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for i, rec in enumerate(csv.reader(fh)):
            if i == 0:
                continue                      # header
            rows.append([float(v) for v in rec])
    if not rows:
        raise ValueError("%s has no data rows" % path)
    widths = {len(r) for r in rows}
    if widths != {7}:
        raise ValueError("%s has column widths %s, expected exactly 7 (CLAUDE.md §4.11)"
                         % (path, sorted(widths)))
    if len(rows) % 3 != 0:
        raise ValueError("%s has %d rows, not divisible by 3 -- ssc splits it into 3 blocks"
                         % (path, len(rows)))
    return rows


def design_magnitudes():
    """Solve the case F design point (0.1 s) for the magnitudes that travel beside the map.

    CLAUDE.md §4.12: `ud_ind_od` carries normalised SHAPES only. If these are not set the tower
    silently keeps its steam-Rankine defaults and the sCO2 block is mis-scaled while everything
    appears to work.
    """
    import build_udpc_map as bum
    import validate_dostal as vd
    import exergy

    m = bum.build(PHI, bum.T_HTF_HOT_DES_C, 3)
    m.Common.is_generate_udpc = 0             # design only; the sweep is ~35 min and not needed
    m.execute(0)
    d = bum.check_design(m)
    if d["problems"]:
        raise RuntimeError("design point is not a valid recompression cycle: %s" % d["problems"])

    out = {
        "design_eff": d["eta_thermal_calc"],
        "T_htf_hot_C": bum.T_HTF_HOT_DES_C,
        "T_htf_cold_C": d["T_htf_cold_des_C"],
        "recomp_frac": d["recomp_frac"],
        "f_cool_pct": bum.cooling_fraction_pct(d, bum.W_DOT_NET_DES_KWE),
        "W_dot_cooler_fan_kWe": d["W_dot_cooler_fan_kWe"],
    }

    # -- TIER 1 exergy: free, because this solve already happened --------------
    # `m` stays referenced for the whole function; never hand a bare Outputs to a caller
    # (CLAUDE.md §4.8). The hot temperature is passed EXPLICITLY: exergy.entropy_generation
    # will not derive it, precisely so this lane's 700 C cannot silently pick up the Dostal
    # lane's 720 C (see that function's docstring).
    o = m.Outputs
    h = list(o.h_state_points)
    s = list(o.s_state_points)
    T_amb_K = 273.15 + (vd.T_MC_IN_C - vd.DT_MC_APPROACH)
    ex = exergy.design_cycle_exergy(o, h, s, T_amb_K=T_amb_K,
                                    T_htf_hot_C=bum.T_HTF_HOT_DES_C)

    # Flatten to scalars. `spawn()` round-trips every result through JSON, so nested dicts of
    # per-component values would not survive the subprocess boundary -- they are emitted as
    # one "COMPONENT=share" string plus the named leaders.
    out.update({
        "ex_eta_II_cycle": ex["eta_II"],
        "ex_Ed_total_kW": ex["Ed_total_kW"],
        "ex_Ex_in_salt_kW": ex["Ex_in_salt_kW"],
        "ex_W_net_kW": ex["W_net_kW"],
        "ex_largest_destroyer": ex["largest_destroyer"],
        "ex_largest_share_pct": ex["largest_destroyer_share_pct"],
        "ex_balance_residual_rel": ex["balance_residual_rel"],
        "ex_balance_closes": bool(ex["balance_closes"]),
        "ex_all_components_positive": bool(ex["all_components_positive"]),
        "ex_cp_htf_kJ_kgK": ex["cp_htf_kJ_kgK"],
        "ex_Ed_breakdown": "; ".join(
            "%s=%.1f kW (%.1f%%)" % (k.split()[0], ex["Ed_kW"][k], ex["Ed_share_pct"][k])
            for k in sorted(ex["Ed_kW"], key=lambda k: -ex["Ed_kW"][k])),
    })
    return out


def build_case(name):
    """Assemble one annual model. Returns (model, info) with the model still alive.

    Never return `model.Outputs` from here -- the Outputs group does not keep its parent alive
    and the caller's first read would hit freed memory (CLAUDE.md §4.8).
    """
    import htf_sam_bridge as hsb
    import build_udpc_map as bum

    mag = design_magnitudes()
    T_hot, T_cold = mag["T_htf_hot_C"], mag["T_htf_cold_C"]

    # The same builder and the same checks the HTF bridge uses -- including the cp unit assert
    # that catches the silent 1000x error (CLAUDE.md §6).
    rows_htf = hsb.build_table(PHI, bum.HTF_T_GRID)
    problems = hsb.check_table(rows_htf, T_cold, T_hot)
    if problems:
        raise ValueError("HTF property table failed its checks: %s" % problems)

    m = hsb.build_model(hsb.HTF_CODE_USER_TABLE, T_hot, T_cold, rows_htf)

    info = dict(mag)
    info["case"] = name
    info["loop_dT_K"] = T_hot - T_cold
    info["freeze_warning"] = hsb.check_freeze_margin(T_cold)

    if name == "steam_same_T":
        # The control: stock steam Rankine at its own design efficiency. Only pc_config differs
        # from the sCO2 cases, so any delta is attributable to the power block alone.
        info["power_block"] = "steam Rankine (SAM default)"
        info["map"] = None
        info["design_eff_used"] = float(m.SystemDesign.design_eff)
        return m, info

    n_points = int(name.split("_n")[1])
    path = map_path(n_points)
    rows_map = load_map(path)

    m.PowerCycle.pc_config = 1                              # user-defined cycle
    m.UserDefinedPowerCycle.ud_ind_od = rows_map
    m.UserDefinedPowerCycle.ud_is_sco2_regr = 1             # sCO2-aware regression (CLAUDE.md §3)
    m.UserDefinedPowerCycle.ud_f_W_dot_cool_des = mag["f_cool_pct"]
    m.UserDefinedPowerCycle.ud_m_dot_water_cool_des = 0.0   # dry-cooled
    m.SystemDesign.design_eff = mag["design_eff"]
    m.SystemDesign.P_ref = P_REF_MW

    got = m.UserDefinedPowerCycle.ud_ind_od
    worst = 0.0
    for a, b in zip(rows_map, got):
        for x, y in zip(a, b):
            denom = abs(x) if abs(x) > 1e-30 else 1.0
            worst = max(worst, abs(x - y) / denom)

    info["power_block"] = "sCO2 recompression (UDPC, n=%d)" % n_points
    info["map"] = os.path.relpath(path, REPO_ROOT).replace("\\", "/")
    info["map_rows"] = len(rows_map)
    info["map_roundtrip_rel"] = worst
    info["design_eff_used"] = mag["design_eff"]
    return m, info


def annual_exergy(m, name):
    """TIER 2 exergy over the 8760 h just simulated. Returns JSON-safe scalars.

    Units are the ones verified by execution on 2026-08-19, not the ones the output names
    imply (CLAUDE.md §4.9 is the standing reason to check): q_sf_inc [MWt], m_dot_pc [kg/s],
    T_pc_in/out [C], P_cycle [MWe gross], gen [kW net], tdry [C].

    THE DEAD STATE IS HOURLY. T0(t) = tdry(t), so both the Petela factor on the solar input and
    the HTF stream exergy move through the year. Objective 5 compares a MENA and a Southern-
    African site; a frozen T0 would bury the difference that comparison exists to measure.

    The steam control uses a cp fallback rather than the nano-HTF property module -- it runs the
    same fluid here, so this is belt-and-braces, but the branch is explicit so a future nitrate
    control cannot silently be costed with chloride properties.

    Never raise out of here: a failed exergy accounting must not lose an otherwise-good annual
    run. Failures are reported in the `ex_annual_error` field instead.
    """
    import exergy
    o = m.Outputs
    try:
        return exergy.annual_plant_exergy(
            q_sf_inc_MW=list(o.q_sf_inc),
            m_dot_pc_kg_s=list(o.m_dot_pc),
            T_pc_in_C=list(o.T_pc_in),
            T_pc_out_C=list(o.T_pc_out),
            P_cycle_MW=list(o.P_cycle),
            gen_kW=list(o.gen),
            tdry_C=list(o.tdry),
            phi_mass=PHI,
        )
    except Exception as e:                      # noqa: BLE001 -- see docstring
        return {"ex_annual_error": "%s: %s" % (type(e).__name__, e)}


def run_case(name):
    """Execute one case in THIS process; the driver runs each in a child."""
    import htf_sam_bridge as hsb
    import PySAM.Singleowner as Singleowner

    m, info = build_case(name)

    # The financial model shares the CSP data container and must exist BEFORE execute(), or it
    # sees a single `gen` record (CLAUDE.md §4.13).
    fin = Singleowner.from_existing(m, "MSPTSingleOwner")
    m.execute(0)
    fin.execute(0)

    info.update(hsb.extract(m))
    info.update(annual_exergy(m, name))

    cap = info.get("system_capacity_kW")
    if cap is not None and cap <= 0:
        info["status"] = "INFEASIBLE"
        info["error"] = ("design nameplate is NEGATIVE (%.1f kW): pumping exceeds gross, so "
                         "annual_energy is meaningless here (CLAUDE.md §4.14)" % cap)
    else:
        info["status"] = "OK"

    try:
        info["lcoe_real_ct_kWh"] = float(fin.Outputs.lcoe_real)
    except Exception:
        info["lcoe_real_ct_kWh"] = None
    return info


CASES = ("sco2_n3", "sco2_n5", "steam_same_T")


def spawn(name):
    """One subprocess per case: a bad table VALUE segfaults ssc rather than raising (§4.2)."""
    cmd = [sys.executable, "-u", os.path.abspath(__file__), "--case", name]
    try:
        p = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return {"case": name, "status": "timeout"}
    for line in (p.stdout or "").splitlines():
        if line.startswith("##RESULT##"):
            return json.loads(line[len("##RESULT##"):])
    tail = ((p.stderr or "").strip().splitlines() or ["<no stderr>"])[-3:]
    return {"case": name, "status": "crash(rc=%s)" % p.returncode, "error": " | ".join(tail)}


def git_commit():
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
        d = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
        return h + ("-dirty" if d else "")
    except Exception:
        return "unknown"


FIELDS = ("case", "status", "power_block", "map", "map_rows", "map_roundtrip_rel",
          "design_eff_used", "T_htf_hot_C", "T_htf_cold_C", "loop_dT_K", "recomp_frac",
          "f_cool_pct", "annual_energy_kWh", "system_capacity_kW", "capacity_factor_pct",
          "annual_W_cycle_gross_kWh", "W_dot_rec_pump_des_MW", "q_dot_rec_des_MW", "A_sf_m2",
          "lcoe_real_ct_kWh", "freeze_warning", "error",
          # Objective 2 exergy. TIER 1 (ex_*, design point) is per-COMPONENT; TIER 2
          # (Ex_*/eta_II_*/Ed_*, annual) is plant-level and lumps the power block, because the
          # UDPC map carries no per-hour state points (scripts/exergy.py docstring).
          "ex_eta_II_cycle", "ex_Ed_total_kW", "ex_Ex_in_salt_kW", "ex_W_net_kW",
          "ex_largest_destroyer", "ex_largest_share_pct", "ex_balance_residual_rel",
          "ex_balance_closes", "ex_all_components_positive", "ex_cp_htf_kJ_kgK",
          "ex_Ed_breakdown",
          "Ex_solar_MWh", "Ex_htf_to_cycle_MWh", "W_gross_MWh", "E_net_MWh",
          "Ed_power_block_MWh", "Ed_upstream_MWh", "eta_II_plant", "eta_II_power_block",
          "eta_II_collection", "petela_mean", "operating_hours", "negative_Ed_hours",
          "parasitic_MWh", "ex_annual_error")


def fmt(v, spec=",.0f"):
    if v is None:
        return "-"
    try:
        return format(v, spec)
    except (TypeError, ValueError):
        return str(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", help="worker mode: run one case, print ##RESULT## json")
    ap.add_argument("--only", help="comma-separated case names")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        for c in CASES:
            print("   %s" % c)
        return 0

    if args.case:
        res = run_case(args.case)
        print("##RESULT##" + json.dumps(res), flush=True)
        return 0

    names = [n.strip() for n in args.only.split(",")] if args.only else list(CASES)
    report = []

    def say(line=""):
        print(line, flush=True)
        report.append(line)

    say("=" * 100)
    say("INTEGRATED ANNUAL RUN -- nano-chloride tower + sCO2 UDPC power block")
    say("  MASTER_PLAN.md §11 item 2 -- the first full-year result for the sCO2 plant")
    say("=" * 100)

    rows = []
    for i, name in enumerate(names, 1):
        say("\n[%d/%d] %s" % (i, len(names), name))
        res = spawn(name)
        rows.append(res)
        if res.get("status") not in ("OK", "INFEASIBLE"):
            say("        -> %s  %s" % (res.get("status"), res.get("error", "")))
            continue
        say("        power block     %s" % res.get("power_block"))
        say("        loop            T_hot %.1f C  T_cold %.1f C  dT %.1f K"
            % (res["T_htf_hot_C"], res["T_htf_cold_C"], res["loop_dT_K"]))
        say("        design_eff      %.5f" % res["design_eff_used"])
        if res.get("map"):
            say("        map             %s (%d rows, roundtrip %.3e)"
                % (res["map"], res["map_rows"], res["map_roundtrip_rel"]))
            say("        cooling         ud_f_W_dot_cool_des %.4f %%" % res["f_cool_pct"])
        say("        annual_energy   %s kWh" % fmt(res.get("annual_energy_kWh")))
        say("        nameplate (net) %s kW" % fmt(res.get("system_capacity_kW"), ",.1f"))
        say("        rec pump (des)  %s MW" % fmt(res.get("W_dot_rec_pump_des_MW"), ",.2f"))
        if res["status"] == "INFEASIBLE":
            say("        -> INFEASIBLE   %s" % res.get("error"))
        if res.get("freeze_warning"):
            say("        -> FREEZE       %s" % res["freeze_warning"])

    # ---- comparisons ----
    by = {r["case"]: r for r in rows if r.get("status") in ("OK", "INFEASIBLE")}
    say("\n" + "=" * 100)
    say("%-14s %12s %16s %14s %10s %9s" % ("case", "status", "annual kWh", "nameplate kW",
                                           "dT K", "pump MW"))
    say("-" * 100)
    for r in rows:
        say("%-14s %12s %16s %14s %10s %9s"
            % (r["case"], r.get("status", "?"), fmt(r.get("annual_energy_kWh")),
               fmt(r.get("system_capacity_kW"), ",.0f"), fmt(r.get("loop_dT_K"), ".0f"),
               fmt(r.get("W_dot_rec_pump_des_MW"), ".2f")))

    say("")
    a, b = by.get("sco2_n3"), by.get("sco2_n5")
    if a and b and a.get("annual_energy_kWh") and b.get("annual_energy_kWh"):
        d = 100.0 * (b["annual_energy_kWh"] - a["annual_energy_kWh"]) / a["annual_energy_kWh"]
        say("MAP RESOLUTION (THESIS_SYNTHESIS.md §17 step 2)")
        say("   n=5 vs n=3 on annual energy: %+.3f %%" % d)
        if abs(d) < 1.0:
            say("   Adequate FOR SCREENING: the shift is small and, being a property of the")
            say("   surface rather than of any one design, is expected to move all designs the")
            say("   same way -- so Morris rankings survive it and can use the cheap map.")
            say("   NOT a convergence claim. This is a single 3->5 step; SAM's own default")
            say("   surface is 20 points per axis, and neither 3 nor 5 has been shown converged")
            say("   against it. A FINAL reported annual number should use the densest map that")
            say("   the build budget allows, and quote this delta as its resolution uncertainty.")
        else:
            say("   The 3-point map is NOT adequate -- resolution changes the annual answer")
            say("   materially, so screening must budget for the denser map.")
    s = by.get("steam_same_T")
    if a and s and a.get("annual_energy_kWh") and s.get("annual_energy_kWh"):
        d = 100.0 * (a["annual_energy_kWh"] - s["annual_energy_kWh"]) / s["annual_energy_kWh"]
        say("")
        say("POWER BLOCK (the §7.5 inference, now tested)")
        say("   sCO2 vs steam at IDENTICAL fluid, temperatures and field: %+.2f %% annual energy"
            % d)
        say("   design_eff %.5f (sCO2) vs %.5f (steam)"
            % (a["design_eff_used"], s["design_eff_used"]))

    # ---- exergy (Objective 2) ----
    say("")
    say("=" * 100)
    say("EXERGY -- Objective 2, DECISIONS.md D1")
    say("=" * 100)
    say("TIER 1 -- DESIGN POINT, per component (from ssc's own h and s)")
    for r in rows:
        if r.get("ex_eta_II_cycle") is None:
            continue
        say("   %s" % r["case"])
        say("      eta_II (cycle)     %.4f   = W_net %s kW / Ex_in(salt) %s kW"
            % (r["ex_eta_II_cycle"], fmt(r["ex_W_net_kW"], ",.1f"),
               fmt(r["ex_Ex_in_salt_kW"], ",.1f")))
        say("      total Ed           %s kW" % fmt(r["ex_Ed_total_kW"], ",.1f"))
        say("      largest destroyer  %s at %.1f %%"
            % (r["ex_largest_destroyer"], r["ex_largest_share_pct"]))
        say("      breakdown          %s" % r["ex_Ed_breakdown"])
        say("      balance            residual %+.2e relative -> %s"
            % (r["ex_balance_residual_rel"],
               "CLOSES" if r["ex_balance_closes"] else "DOES NOT CLOSE -- investigate"))
        say("      all Ed > 0         %s" % ("yes" if r["ex_all_components_positive"] else
                                             "NO -- second-law violation"))
    say("")
    say("   The balance is the load-bearing check, not the per-component signs: it exercises")
    say("   every h, every s, both mass flows and the salt properties at once, so it catches")
    say("   scaling errors that sign checks cannot.")

    say("")
    say("TIER 2 -- ANNUAL, plant level, with an HOURLY dead state T0(t) = tdry(t)")
    say("%-14s %13s %13s %11s %11s %11s %8s" % ("case", "Ex_solar MWh", "Ex_htf MWh",
                                                "eta_II pl", "eta_II pb", "eta_II col",
                                                "neg Ed h"))
    say("-" * 100)
    for r in rows:
        if r.get("Ex_solar_MWh") is None:
            continue
        say("%-14s %13s %13s %11s %11s %11s %8s"
            % (r["case"], fmt(r["Ex_solar_MWh"]), fmt(r["Ex_htf_to_cycle_MWh"]),
               fmt(r["eta_II_plant"], ".4f"), fmt(r["eta_II_power_block"], ".4f"),
               fmt(r["eta_II_collection"], ".4f"), fmt(r["negative_Ed_hours"], "d")))
    bad = [r["case"] for r in rows if (r.get("negative_Ed_hours") or 0) > 0]
    say("")
    if bad:
        say("   ⚠ NEGATIVE HOURLY Ed in: %s" % ", ".join(bad))
        say("   Ed = Ex_htf - W_gross < 0 is a second-law violation in that hour. Either the")
        say("   HTF cp, the temperatures or the gross work are inconsistent -- do NOT report")
        say("   the annual eta_II until this is explained.")
    else:
        say("   Hourly Ed >= 0 in every operating hour of every case -- the annual accounting")
        say("   is second-law consistent, which is what makes it safe to collect at every")
        say("   swept point of the campaign.")
    say("")
    say("   ⚠ TIER 2 LUMPS THE POWER BLOCK, deliberately. The UDPC map carries normalised")
    say("   response SHAPES only (CLAUDE.md §4.11), so there are no per-hour state points and")
    say("   no per-component Ed at any hour but the design point. Ed_power_block is the exact")
    say("   lumped quantity Ex_htf - W_gross. Do NOT infer an annual component ranking from")
    say("   the tier-1 design-point one: off-design shifts it.")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = git_commit()
    csv_path = os.path.join(RESULTS_DIR, "integrated_annual_%s.csv" % stamp)
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    md_path = os.path.join(RESULTS_DIR, "integrated_annual_%s.md" % stamp)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# Integrated annual run -- nano-chloride tower + sCO2 UDPC block\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/run_integrated_annual.py` |\n"
                 "| run (UTC) | %s |\n| git commit | `%s` |\n"
                 "| PySAM | 7.1.1.post1 (bundled ssc 306) |\n"
                 "| weather | Morocco/Ouarzazate NSRDB TMY |\n\n```\n%s\n```\n"
                 % (stamp, commit, "\n".join(report)))
    print("\nresults written (commit %s):" % commit)
    for p in (md_path, csv_path):
        print("   %s" % os.path.relpath(p, REPO_ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
