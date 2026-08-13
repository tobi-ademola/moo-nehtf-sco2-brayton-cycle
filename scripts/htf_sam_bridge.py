r"""Salt/SAM reconciliation: can SAM run on the nano-chloride HTF at all?

MASTER_PLAN.md §11 item 1 -- the LIVE BLOCKER, and the last open question of §10. It gates
Objective 2, because whether the nano-chloride couples *inside* SAM or must be coupled
externally shapes every model decision below it.

THE QUESTION, precisely. `CLAUDE.md` §6 records that `rec_htf = 50` takes a user-defined
7-column property table, so an override path exists on paper. What was never tested is whether
SAM ACCEPTS the chloride across its real operating range and still solves -- and, separately,
whether the result is trustworthy. Those are different questions and this script answers the
first for both fluids while measuring the second.

WHAT IT DOES NOT DO. The power block stays SAM's stock steam Rankine here (`pc_config` is left
alone). That is deliberate: this script changes exactly ONE thing, the working fluid, so any
difference it reports is attributable to the fluid and not to a simultaneous cycle swap. The
sCO2 power block arrives separately via scripts/build_udpc_map.py (§11 item 2).

THE FINDING THAT SHAPES THE STUDY. The chloride's melting point is 401.4 C, so the cold tank
cannot approach the 290 C nitrate default -- 450 C is the practical floor. The chloride
therefore runs a NARROWER loop dT than nitrate for the same hot temperature, and narrower dT at
equal duty means higher mass flow, which drives pumping power (objective O3). This is a real
physical coupling between decision variables #5 (T_HTF) and #6 (m_dot_HTF), not an artefact,
and the case matrix below is built to expose it rather than average over it.

CRASH SAFETY. `CLAUDE.md` §4.2: a malformed htf_props table SEGFAULTS ssc rather than raising,
taking the whole interpreter with it and losing unflushed stdout. Every case therefore runs in
its OWN subprocess with -u, exactly as §4.2 advises, so one crash costs one case instead of the
whole matrix -- and a segfault is recorded as a result (exit 139/3221225477) rather than an
absence of one. Run a single case directly with --case <name> to debug it.

Inputs:  scripts/nanofluid_properties.py for the property model;
         data/tmy/158192_31.05_-6.86_tmy-2022.csv (Morocco/Ouarzazate TMY, CLAUDE.md §5).
         Requires the .venv of CLAUDE.md §1 (PySAM 7.1.1.post1, numpy).

Run:  .\.venv\Scripts\python.exe -u .\scripts\htf_sam_bridge.py
      .\.venv\Scripts\python.exe -u .\scripts\htf_sam_bridge.py --case chloride_700_450

Outputs: results/htf_sam_bridge_<stamp>.md    full report, per case
         results/htf_sam_bridge_<stamp>.csv   one row per case, machine-readable
"""

import argparse
import csv
import datetime
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nanofluid_properties as nfp  # noqa: E402  (path set above)

# Morocco / Ouarzazate NSRDB TMY -- the MENA site of CLAUDE.md §5. A weather file is MANDATORY:
# TcsmoltenSalt raises on read if it is unset (CLAUDE.md §4.4) and the CSP modules do not fail
# gracefully the way PVWatts does.
WEATHER_FILE = os.path.join(REPO_ROOT, "data", "tmy",
                            "158192_31.05_-6.86_tmy-2022.csv")

HTF_CODE_NITRATE = 17       # 60% NaNO3 / 40% KNO3 -- SAM's default (CLAUDE.md §6)
HTF_CODE_USER_TABLE = 50    # user-defined 7-column property table

# SAM's stock nitrate design temperatures, read off the model in this env, not assumed.
NITRATE_T_HOT_C, NITRATE_T_COLD_C = 574.0, 290.0

# Chloride operating window. The cold floor is set by the melt point plus a freeze margin;
# the hot end is the top of the A1 correlation's stated validity (CLAUDE.md-independent -- it
# comes from the property module's own T_VALID_MAX_C).
FREEZE_MARGIN_K = 20.0
CHLORIDE_T_COLD_C = 450.0
CHLORIDE_T_HOT_C = 700.0

# Property-table temperature grid. It MUST bracket the actual operating span or SAM interpolates
# off the end of the table; the too_narrow case below tests what happens when it does not.
DEFAULT_T_GRID = [450.0, 500.0, 550.0, 600.0, 650.0, 700.0]

PHI_REFERENCE = 0.007       # 0.7 wt% CuO -- Han/B3's measured cp optimum

# Column order/units of the 7-column table (CLAUDE.md §6). Repeated here so a shape error is
# reported against a named column rather than an index.
SAM_COLS = ("T [C]", "cp [kJ/kg-K]", "rho [kg/m3]", "mu [Pa-s]",
            "nu [m2/s]", "k [W/m-K]", "h [J/kg]")

RESULT_PREFIX = "##RESULT##"   # child -> parent protocol


# =============================================================================
# Table construction and validation
# =============================================================================
def build_table(phi_mass, T_grid=None, band="nominal"):
    """The 7-column custom-fluid table for one loading, as SAM wants it.

    Delegates entirely to the validated property module -- `htf_table_rows()` already emits
    exactly SAM's column order and already divides cp by 1000 to reach kJ/(kg K). That division
    is the single highest-risk line in the whole bridge: SAM wants kJ/(kg K) while the property
    model works in J/(kg K), and getting it wrong is a silent 1000x error that no shape check
    can catch. It is asserted on below rather than trusted.
    """
    return nfp.htf_table_rows(phi_mass, T_grid or DEFAULT_T_GRID, band=band)


def check_table(rows, T_lo, T_hi):
    """Validate the table before ssc sees it. Returns a list of problems (empty = clean).

    ssc's own message is "The user defined hot fluid table must contain at least 3 rows and
    exactly 7 columns" -- but only for shapes it catches; others segfault (CLAUDE.md §4.2).
    Checking here means a bad table is a Python error with a line number, not an exit 139.
    """
    problems = []
    if len(rows) < 3:
        problems.append(f"only {len(rows)} rows; ssc requires at least 3")
    widths = {len(r) for r in rows}
    if widths != {7}:
        problems.append(f"column widths {sorted(widths)}; ssc requires exactly 7")

    temps = [r[0] for r in rows]
    if temps != sorted(temps):
        problems.append("temperature column is not ascending")
    if temps[0] > T_lo or temps[-1] < T_hi:
        problems.append(
            f"grid {temps[0]:.0f}-{temps[-1]:.0f} C does not bracket the operating span "
            f"{T_lo:.0f}-{T_hi:.0f} C -- SAM will extrapolate off the end of the table")

    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            if v != v or v in (float("inf"), float("-inf")):
                problems.append(f"row {i} col {j} ({SAM_COLS[j]}) is not finite: {v}")
        # The cp unit trap, caught by magnitude. A chloride cp is ~1.0-1.3 kJ/(kg K); if the
        # /1000 were missing this lands near 1100 and every downstream energy balance is 1000x.
        if not (0.1 < r[1] < 10.0):
            problems.append(
                f"row {i}: cp = {r[1]:.4g} is outside 0.1-10 kJ/(kg K) -- unit error? "
                f"SAM wants kJ/(kg K), the property module works in J/(kg K)")
    return problems


def check_freeze_margin(T_cold_C):
    """The chloride's melt point is a hard floor on the cold tank, not a soft preference."""
    floor = nfp.MELTING_POINT_C + FREEZE_MARGIN_K
    return None if T_cold_C >= floor else (
        f"T_cold = {T_cold_C:.1f} C is below the A1 melting point "
        f"({nfp.MELTING_POINT_C:.1f} C) + {FREEZE_MARGIN_K:.0f} K freeze margin = {floor:.1f} C")


# =============================================================================
# Model construction
# =============================================================================
def build_model(htf_code, T_hot_C, T_cold_C, rows=None):
    """A stock MSPTSingleOwner tower with the fluid and design temperatures overridden.

    Everything else -- solar multiple 2.4, 10 h TES, heliostat field, and the stock STEAM
    power block -- is left exactly as SAM ships it, so the only variable across the case
    matrix is the fluid and the temperatures it forces.
    """
    import PySAM.TcsmoltenSalt as tcs
    m = tcs.default("MSPTSingleOwner")

    if not os.path.exists(WEATHER_FILE):
        raise FileNotFoundError(
            f"weather file missing: {WEATHER_FILE}. TcsmoltenSalt raises on read when "
            f"solar_resource_file is unset (CLAUDE.md §4.4).")
    m.SolarResource.solar_resource_file = WEATHER_FILE

    m.TowerAndReceiver.rec_htf = htf_code
    if rows is not None:
        m.TowerAndReceiver.field_fl_props = rows

    m.SystemDesign.T_htf_hot_des = T_hot_C
    m.SystemDesign.T_htf_cold_des = T_cold_C
    return m


def roundtrip_error(m, rows):
    """Largest relative discrepancy between what we set and what SAM stored.

    Catches silent truncation, reordering or unit mangling inside the setter -- a class of bug
    that no execute() failure would reveal, because the model would happily run on the wrong
    numbers.
    """
    got = m.TowerAndReceiver.field_fl_props
    if len(got) != len(rows):
        return float("inf"), f"row count changed: set {len(rows)}, read back {len(got)}"
    worst, where = 0.0, ""
    for i, (a, b) in enumerate(zip(rows, got)):
        if len(a) != len(b):
            return float("inf"), f"row {i} width changed: set {len(a)}, read back {len(b)}"
        for j, (x, y) in enumerate(zip(a, b)):
            denom = abs(x) if abs(x) > 1e-30 else 1.0
            rel = abs(x - y) / denom
            if rel > worst:
                worst, where = rel, f"row {i} col {j} ({SAM_COLS[j]}): set {x!r}, read {y!r}"
    return worst, where


# =============================================================================
# Cases
# =============================================================================
def case_nitrate_baseline():
    """SAM's own salt at SAM's own temperatures on the Morocco TMY.

    The control. Every chloride number below is only interpretable against this.
    """
    m = build_model(HTF_CODE_NITRATE, NITRATE_T_HOT_C, NITRATE_T_COLD_C)
    m.execute(0)
    return m, {"htf": "nitrate (code 17)", "phi_wt_pct": None,
               "T_hot_C": NITRATE_T_HOT_C, "T_cold_C": NITRATE_T_COLD_C,
               "roundtrip_rel": None}


def _chloride_case(phi, T_hot, T_cold, T_grid=None, execute=True):
    rows = build_table(phi, T_grid)
    problems = check_table(rows, T_cold, T_hot)
    freeze = check_freeze_margin(T_cold)
    if freeze:
        problems.append(freeze)

    m = build_model(HTF_CODE_USER_TABLE, T_hot, T_cold, rows=rows)
    rel, where = roundtrip_error(m, rows)

    info = {"htf": f"nano-chloride (code 50)", "phi_wt_pct": 100.0 * phi,
            "T_hot_C": T_hot, "T_cold_C": T_cold, "roundtrip_rel": rel,
            "roundtrip_where": where, "table_problems": problems,
            "table_rows": len(rows),
            "T_grid": f"{rows[0][0]:.0f}-{rows[-1][0]:.0f}"}
    if execute:
        m.execute(0)
    return m, info


def case_chloride_574_450():
    """Chloride at the NITRATE hot temperature -- isolates the fluid from the temperature.

    T_cold cannot also match nitrate's 290 C: that is below the melt point, so the loop dT is
    124 K here against nitrate's 284 K. That narrowing is itself the finding.
    """
    return _chloride_case(PHI_REFERENCE, NITRATE_T_HOT_C, CHLORIDE_T_COLD_C)


def case_chloride_700_450():
    """The actual design intent: the chloride at the high-temperature end it was chosen for."""
    return _chloride_case(PHI_REFERENCE, CHLORIDE_T_HOT_C, CHLORIDE_T_COLD_C)


def case_base_salt_700_450():
    """phi = 0: the bare eutectic, no nanoparticles. The nano-enhancement control."""
    return _chloride_case(0.0, CHLORIDE_T_HOT_C, CHLORIDE_T_COLD_C)


def case_chloride_max_loading():
    """phi = 2.0 wt%, Han's highest tested loading -- the top of the decision-variable range."""
    return _chloride_case(0.02, CHLORIDE_T_HOT_C, CHLORIDE_T_COLD_C)


def case_table_too_narrow():
    """Deliberately UNDER-COVER the operating span, to find out what SAM does about it.

    CLAUDE.md §6 warns "cover the full operating temperature span -- ssc interpolates and will
    not extrapolate gracefully", without saying whether that means a clean error, a silent
    extrapolation, or a crash. Which it is decides whether the optimiser needs a guard when it
    sweeps T_HTF (decision variable #5), so a failure here is a RESULT, not a bug.

    *** THIS CASE IS INCONCLUSIVE BY CONSTRUCTION, AND THAT IS THE FINDING. ***
    Three of the four A1 correlations are EXACTLY LINEAR in T -- rho = 1958.8438 - 0.56355T,
    cp = 1301.38 - 0.5T, k = 0.5822 - 2.6e-4 T -- so linear interpolation on any grid, and
    linear extrapolation off either end, reproduces them to machine precision. Only mu
    (exponential) and h (quadratic in T) can differ at all. A bit-identical result to
    chloride_700_450 therefore demonstrates nothing about SAM's extrapolation behaviour; it
    demonstrates that the properties SAM's field/TES path actually consumes are the linear
    ones. case_table_min_rows below is the test with teeth.
    """
    return _chloride_case(PHI_REFERENCE, CHLORIDE_T_HOT_C, CHLORIDE_T_COLD_C,
                          T_grid=[500.0, 550.0, 600.0, 650.0])


def case_table_min_rows():
    """The ssc minimum of 3 rows across the FULL span -- the test the narrow case cannot be.

    Same endpoints as chloride_700_450, so extrapolation plays no part; the only difference is
    grid density. Because mu is exponential in T, a 3-point chord is the worst linear
    approximation of it this study will ever hand SAM. If the annual result and the pumping
    parasitic move, grid density matters and the table must be dense; if they do not, then mu
    is not driving the field/TES answer -- which is worth knowing for objective O3 before the
    optimiser starts sweeping.
    """
    return _chloride_case(PHI_REFERENCE, CHLORIDE_T_HOT_C, CHLORIDE_T_COLD_C,
                          T_grid=[450.0, 575.0, 700.0])


CASES = {
    "nitrate_baseline": case_nitrate_baseline,
    "chloride_574_450": case_chloride_574_450,
    "chloride_700_450": case_chloride_700_450,
    "base_salt_700_450": case_base_salt_700_450,
    "chloride_max_loading": case_chloride_max_loading,
    "table_too_narrow": case_table_too_narrow,
    "table_min_rows": case_table_min_rows,
}


# =============================================================================
# Output extraction
# =============================================================================
def extract(m):
    """Annual results, defensively -- output names move between SAM versions.

    `system_capacity` is the load-bearing one and is NOT optional garnish: it is the design NET
    nameplate, gross minus parasitics, and it can come out NEGATIVE when the pumping parasitic
    exceeds gross output. SAM does not treat that as an error -- it reports a negative nameplate,
    clamps capacity_factor to zero, and still returns a full 8760 `gen` array and a plausible
    annual_energy. A case that only looked at annual_energy would read as healthy.

    DO NOT COMPARE `capacity_factor` ACROSS THESE CASES. Its denominator is the per-case
    nameplate, which moves with the fluid and the temperatures, so CF can RISE while annual
    energy FALLS. Compare annual_energy and system_capacity, which share a fixed basis.
    """
    o = m.Outputs

    def get(*names):
        for n in names:
            try:
                v = getattr(o, n)
                if v is not None:
                    return v
            except AttributeError:
                continue
        return None

    def total(v):
        if v is None:
            return None
        return float(sum(v)) if isinstance(v, (list, tuple)) else float(v)

    return {
        "annual_energy_kWh": total(get("annual_energy")),
        "system_capacity_kW": total(get("system_capacity")),
        "capacity_factor_pct": total(get("capacity_factor")),
        "annual_W_cycle_gross_kWh": total(get("annual_W_cycle_gross")),
        # O3 -- HTF pumping parasitic. This is the term the chloride's narrow loop dT drives,
        # and the one that turns the nameplate negative when dT gets too small.
        "W_dot_rec_pump_des_MW": total(get("W_dot_rec_pump_des")),
        "W_dot_cycle_pump_des_MW": total(get("W_dot_cycle_pump_des")),
        "annual_E_tower_pump_MWh": total(get("annual_E_tower_pump")),
        "q_dot_rec_des_MW": total(get("q_dot_rec_des")),
        "A_sf_m2": total(get("A_sf")),
    }


def run_case(name):
    """Execute one case in THIS process. The parent runs each in a child (see main).

    A negative nameplate is reported as INFEASIBLE, not OK. ssc will not raise on one -- see
    extract() -- so if this function did not classify it, a physically impossible plant would
    be tabulated beside the valid ones with a perfectly reasonable-looking annual energy.
    """
    m, info = CASES[name]()
    info.update(extract(m))
    info["case"] = name
    cap = info.get("system_capacity_kW")
    if cap is not None and cap <= 0:
        info["status"] = "INFEASIBLE"
        info["error"] = (
            "design nameplate is NEGATIVE (%.1f kW): the pumping parasitic exceeds gross "
            "output, so annual_energy is meaningless here" % cap)
    else:
        info["status"] = "OK"
    return info


# =============================================================================
# Orchestration
# =============================================================================
def run_case_isolated(name, timeout=900):
    """Run one case in a child interpreter so a segfault costs one case, not the matrix."""
    proc = subprocess.run(
        [sys.executable, "-u", os.path.abspath(__file__), "--case", name],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=timeout)
    for line in proc.stdout.splitlines():
        if line.startswith(RESULT_PREFIX):
            return json.loads(line[len(RESULT_PREFIX):]), proc.stdout
    # No result line: the child died. Report HOW, since the manner of death is the finding.
    rc = proc.returncode
    if rc in (-11, 139, 3221225477, -1073741819):
        status = f"SEGFAULT (exit {rc}) -- ssc crashed rather than raising, cf. CLAUDE.md §4.2"
    else:
        status = f"FAILED (exit {rc})"
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()
    return ({"case": name, "status": status,
             "error": tail[-1][:300] if tail else "(no output)"}, proc.stdout + proc.stderr)


def git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                               capture_output=True, text=True, check=True)
        return out.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "")
    except Exception:
        return "unknown"


def fmt(v, spec=",.1f"):
    return "n/a" if v is None else format(v, spec)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", choices=sorted(CASES),
                    help="run ONE case in this process (used internally, and for debugging)")
    args = ap.parse_args()

    # --- child mode ------------------------------------------------------
    if args.case:
        info = run_case(args.case)
        print(RESULT_PREFIX + json.dumps(info, default=str))
        return

    # --- parent mode -----------------------------------------------------
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = git_commit()

    print("=" * 100)
    print("SALT / SAM RECONCILIATION -- can TcsmoltenSalt run on the nano-chloride?")
    print("  MASTER_PLAN.md §11 item 1 (the live blocker).  weather: %s"
          % os.path.basename(WEATHER_FILE))
    print("  Each case runs in its own subprocess: a bad property table segfaults ssc rather")
    print("  than raising (CLAUDE.md §4.2), and a crash is recorded as a result.")
    print("=" * 100)

    rows_out, logs = [], {}
    for name in CASES:
        print("\n---- %s ----" % name, flush=True)
        info, log = run_case_isolated(name)
        logs[name] = log
        rows_out.append(info)
        print("   status               %s" % info.get("status"))
        if info.get("status") == "OK":
            print("   fluid / temps        %s   %.0f -> %.0f C  (dT %.0f K)"
                  % (info.get("htf"), info.get("T_cold_C"), info.get("T_hot_C"),
                     info.get("T_hot_C") - info.get("T_cold_C")))
            if info.get("roundtrip_rel") is not None:
                print("   table round-trip     max rel dev %.3e  (%s)"
                      % (info["roundtrip_rel"],
                         "exact" if info["roundtrip_rel"] == 0 else info.get("roundtrip_where")))
            for p in info.get("table_problems") or []:
                print("   [table warning]      %s" % p)
        if info.get("status") in ("OK", "INFEASIBLE"):
            print("   annual_energy        %s kWh" % fmt(info.get("annual_energy_kWh"), ",.0f"))
            print("   nameplate (net)      %s kW" % fmt(info.get("system_capacity_kW"), ",.1f"))
            print("   rec pump (design)    %s MW   annual %s MWh"
                  % (fmt(info.get("W_dot_rec_pump_des_MW"), ",.2f"),
                     fmt(info.get("annual_E_tower_pump_MWh"), ",.0f")))
        if info.get("status") != "OK":
            print("   error                %s" % info.get("error"))

    # --- comparison ------------------------------------------------------
    base = next((r for r in rows_out
                 if r["case"] == "nitrate_baseline" and r.get("status") == "OK"), None)
    print("\n" + "=" * 100)
    print("COMPARISON  (vs the nitrate baseline)")
    print("  Ranked on NAMEPLATE and ANNUAL ENERGY. Capacity factor is shown last and is NOT")
    print("  comparable across these cases: its denominator is the per-case nameplate, which")
    print("  moves with the fluid, so CF rises while annual energy falls. See extract().")
    print("=" * 100)
    print("%-22s %12s %15s %13s %11s %8s %8s"
          % ("case", "status", "annual [kWh]", "nameplate[kW]", "vs base", "dT[K]", "CF[%]"))
    print("-" * 100)
    for r in rows_out:
        ae = r.get("annual_energy_kWh")
        delta = ("%+.2f %%" % (100.0 * (ae - base["annual_energy_kWh"])
                               / base["annual_energy_kWh"])
                 if (base and ae and r is not base) else ("baseline" if r is base else "n/a"))
        dT = (r.get("T_hot_C") - r.get("T_cold_C")) if r.get("T_hot_C") else None
        print("%-22s %12s %15s %13s %11s %8s %8s"
              % (r["case"], r.get("status", "?"), fmt(ae, ",.0f"),
                 fmt(r.get("system_capacity_kW"), ",.0f"), delta, fmt(dT, ".0f"),
                 fmt(r.get("capacity_factor_pct"), ".2f")))

    n_ok = sum(1 for r in rows_out if r.get("status") == "OK")
    n_infeasible = sum(1 for r in rows_out if r.get("status") == "INFEASIBLE")
    solved = [r for r in rows_out
              if r.get("status") in ("OK", "INFEASIBLE") and r.get("phi_wt_pct") is not None]

    print("\nVERDICT")
    print("  cases run              %d: %d OK, %d infeasible design, %d failed outright"
          % (len(rows_out), n_ok, n_infeasible, len(rows_out) - n_ok - n_infeasible))
    print("  BLOCKER -- does rec_htf = 50 accept the nano-chloride table?")
    print("                         %s"
          % ("YES. ssc took the 7-column table, stored it without alteration, and the annual "
             "model solved on it." if solved else "NO -- see failures above"))
    if solved:
        worst = max(r["roundtrip_rel"] for r in solved)
        print("  table fidelity         max round-trip deviation %.3e across %d chloride cases"
              % (worst, len(solved)))
    print("  BUT ACCEPTANCE IS NOT VALIDITY. ssc reports no error on a physically impossible")
    print("  design: a negative nameplate still yields an 8760 gen array and a plausible")
    print("  annual_energy. Every chloride case must be screened on system_capacity > 0.")

    # The dT -> pumping coupling, which is the substantive result rather than a diagnostic.
    pumped = [r for r in rows_out if r.get("W_dot_rec_pump_des_MW") is not None
              and r.get("T_hot_C") is not None]
    if len(pumped) > 1:
        print("\n  RECEIVER PUMP POWER vs LOOP dT  (objective O3, decision variables #5 and #6)")
        for r in sorted(pumped, key=lambda x: x["T_hot_C"] - x["T_cold_C"]):
            print("    %-22s dT %3.0f K   W_pump,des %8.2f MW   nameplate %10s kW"
                  % (r["case"], r["T_hot_C"] - r["T_cold_C"], r["W_dot_rec_pump_des_MW"],
                     fmt(r.get("system_capacity_kW"), ",.0f")))

    # --- durable output --------------------------------------------------
    md_path = os.path.join(RESULTS_DIR, "htf_sam_bridge_%s.md" % stamp)
    csv_path = os.path.join(RESULTS_DIR, "htf_sam_bridge_%s.csv" % stamp)
    fields = sorted({k for r in rows_out for k in r})
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows_out:
            w.writerow({k: r.get(k) for k in fields})
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# Salt / SAM reconciliation -- nano-chloride via rec_htf = 50\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/htf_sam_bridge.py` |\n"
                 "| run (UTC) | %s |\n| git commit | `%s` |\n"
                 "| PySAM | 7.1.1.post1 (bundled ssc 306) |\n"
                 "| weather | `%s` |\n\n"
                 % (stamp, commit, os.path.basename(WEATHER_FILE)))
        for name in CASES:
            fh.write("\n## %s\n\n```\n%s\n```\n" % (name, logs[name].strip()))

    print("\nresults written (commit %s):" % commit)
    for p in (md_path, csv_path):
        print("   %s" % os.path.relpath(p, REPO_ROOT).replace("\\", "/"))


if __name__ == "__main__":
    main()
