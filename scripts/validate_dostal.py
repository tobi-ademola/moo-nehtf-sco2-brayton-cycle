r"""Validate the PySAM sCO2 recompression cycle against Dostal (2004).

Runs the standalone recompression cycle at Dostal's HIGH-PERFORMANCE design point so the
resulting state table can be compared node-by-node against the published one:

    turbine inlet temperature      700 C
    compressor inlet temperature    32 C          (near-critical)
    compressor outlet pressure      20 MPa        (P_high)
    pressure ratio                   2.6          -> P_low = 7.6923 MPa
    recompressed fraction f_rc       0.39
    eta_isen  main compressor        0.89
    eta_isen  recompressor           0.89         (conservative -- NOT 0.948)
    eta_isen  turbine                0.90

Dostal's reported thermal efficiency for this case (conservative turbomachinery) is 51.27%.

Working-fluid properties: every node is independently re-evaluated from (T, P) with CoolProp
(Span-Wagner, REFPROP-equivalent). The mixer balance and all second-law checks are run on the
CoolProp numbers, so they do not depend on ssc's internal property routines being correct --
the PySAM-vs-CoolProp deviation is printed as its own validation line.

Inputs:  none -- every boundary condition is pinned in the constants block below.
         Requires NREL-PySAM 7.1.1.post1, numpy and CoolProp in .venv (CLAUDE.md section 1).

Run:  .\.venv\Scripts\python.exe -u .\scripts\validate_dostal.py

Outputs: the console report, plus three durable copies under results/ (CLAUDE.md section 0.2),
         each stamped with the UTC run time and the git commit that produced them:
             results/dostal_validation_<stamp>.md         full console report
             results/dostal_state_points_<stamp>.csv      both cases, every node
             results/dostal_recup_sweep_<stamp>.csv       effectiveness sweep

Companion to scripts/smoke_test.py, which pins the env-health baseline in CLAUDE.md section 7.
This script pins the *physics* baseline against published literature.
"""

import csv
import datetime
import math
import os
import subprocess
import sys

import numpy as np
import PySAM.Sco2CspSystem as S
from CoolProp.CoolProp import PropsSI

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")

# --- Dostal 2004 high-performance recompression design point ------------------
T_TURB_IN_C = 700.0     # turbine inlet temperature            [C]
T_MC_IN_C = 32.0        # main compressor inlet temperature    [C]
P_HIGH_MPA = 20.0       # compressor outlet pressure           [MPa]
PRESSURE_RATIO = 2.6    # P_high / P_low                       [-]
F_RECOMP = 0.39         # recompressed fraction                [-]
ETA_MC = 0.89           # main compressor isentropic eff       [-]
ETA_RC = 0.89           # recompressor isentropic eff          [-]
ETA_T = 0.90            # turbine isentropic eff               [-]
ETA_TARGET = 0.5127     # Dostal's reported thermal efficiency [-]

# Recuperators. Dostal specifies the recuperators by effectiveness, and effectiveness is
# scale-free -- unlike a UA, it transfers to this 10 MWe model without rescaling.
RECUP_EFF = 0.95

# Per-heat-exchanger CO2 pressure loss, as a fraction of inlet pressure. The base case runs
# LOSSLESS so that P_high and the pressure ratio are exactly the values specified above; the
# second case re-runs with SAM's stock 0.54% to show the sensitivity.
DELTA_P_FRAC = 0.0

# Boundary conditions the cycle itself does not fix, but ssc demands. These set the HTF loop
# around the cycle; they do not alter the CO2 states, only the salt temperatures.
DT_PHX_HOT_APPROACH = 20.0    # T_htf_hot - T_turb_in
DT_MC_APPROACH = 6.0          # T_mc_in - T_amb
W_DOT_NET_DES = 10000.0       # kWe -- cycle efficiency is scale-invariant here

# Near-critical fallback (Dyreby): if the solver cannot close at 7.69 MPa / 32 C, retry with
# the low-side pressure lifted by this much and report the offset alongside the results.
P_LOW_OFFSET_MPA = 0.3

# State-point index -> physical node. Same ordering as scripts/smoke_test.py; the mixer
# energy balance below is what proves the ordering.
NODES = [
    "MC_IN      main compressor inlet",
    "MC_OUT     main compressor outlet",
    "LTR_HP_OUT LTR high-pressure outlet",
    "MIXER_OUT  LTR-HP + recompressor merge",
    "HTR_HP_OUT HTR high-pressure outlet = PHX inlet",
    "TURB_IN    turbine inlet",
    "TURB_OUT   turbine outlet = HTR low-pressure inlet",
    "HTR_LP_OUT HTR low-pressure outlet = LTR low-pressure inlet",
    "LTR_LP_OUT LTR low-pressure outlet = flow split point",
    "RC_OUT     recompressor outlet",
    "PC_IN      pre-compressor inlet   (partial-cooling only -> NaN here)",
    "PC_OUT     pre-compressor outlet  (partial-cooling only -> NaN here)",
]
N_REAL = 10     # nodes 10 and 11 are NaN for cycle_config = 1 (CLAUDE.md 4.5)


def build(recup_eff=RECUP_EFF, dp_frac=DELTA_P_FRAC, p_low_fixed=None):
    """Assemble the cycle. p_low_fixed pins the low-side pressure instead of the ratio."""
    m = S.new()

    d = m.SystemDesign
    d.htf = 17                                              # 60% NaNO3 / 40% KNO3
    d.T_htf_hot_des = T_TURB_IN_C + DT_PHX_HOT_APPROACH     # -> turbine inlet 700 C
    d.dT_PHX_hot_approach = DT_PHX_HOT_APPROACH
    d.T_amb_des = T_MC_IN_C - DT_MC_APPROACH                # -> compressor inlet 32 C
    d.dT_mc_approach = DT_MC_APPROACH
    d.W_dot_net_des = W_DOT_NET_DES
    d.site_elevation = 0.0
    d.design_method = 3                                     # specify each recuperator

    c = m.Common
    c.eta_isen_mc = ETA_MC
    c.eta_isen_rc = ETA_RC
    c.eta_isen_pc = ETA_RC                                  # unused: recompression config
    c.eta_isen_t = ETA_T
    c.P_high_limit = P_HIGH_MPA
    c.deltaP_counterHX_frac = dp_frac
    c.PHX_co2_deltaP_des_in = dp_frac
    c.mc_comp_type = 1
    c.is_gen_od_polynomials = 0
    # od_* inputs are ARRAYS -- leave unset for a design-only run (CLAUDE.md 4.1).

    x = m.HeatExchangerDesign
    x.cycle_config = 1                          # 1 = recompression
    x.is_recomp_ok = -abs(F_RECOMP)             # negative => PIN f_rc (CLAUDE.md 4.3)
    x.is_P_high_fixed = 1                       # P_high = P_high_limit exactly
    # is_PR_fixed: >0 = fixed pressure ratio, <0 = fixed low-side pressure at abs(input)
    x.is_PR_fixed = PRESSURE_RATIO if p_low_fixed is None else -abs(p_low_fixed)
    x.is_IP_fixed = 0
    x.des_objective = 0
    x.min_phx_deltaT = 0
    x.rel_tol = x.od_rel_tol = 4                # tighter than the stock 3 for validation
    # HTR/LTR_design_code: 1 = UA, 2 = min dT, 3 = effectiveness.
    x.HTR_design_code = x.LTR_design_code = 3
    x.HTR_eff_des_in = x.LTR_eff_des_in = recup_eff
    # Unused when design_code = 3, but ssc still reads them -- leaving them at 0.0
    # segfaults the interpreter (CLAUDE.md 4.2), so give them harmless placeholders.
    x.HTR_UA_des_in = x.LTR_UA_des_in = 5000.0
    x.HTR_min_dT_des_in = x.LTR_min_dT_des_in = 10.0
    x.HT_recup_eff_max = x.LT_recup_eff_max = 1.0
    x.HTR_n_sub_hx = x.LTR_n_sub_hx = 20
    x.HTR_od_model = x.LTR_od_model = 1
    for a in ("HTR_LP_deltaP_des_in", "HTR_HP_deltaP_des_in",
              "LTR_LP_deltaP_des_in", "LTR_HP_deltaP_des_in"):
        setattr(x, a, dp_frac)

    p = m.PHXDesign
    p.dT_PHX_cold_approach = 20.0
    p.PHX_n_sub_hx = 10
    p.PHX_od_model = 1

    a = m.AirCoolerDesign
    a.is_design_air_cooler = 1
    a.deltaP_cooler_frac = dp_frac
    a.fan_power_frac = 0.01
    a.eta_air_cooler_fan = 0.5
    a.N_nodes_air_cooler_pass = 10
    return m


def solve(recup_eff=RECUP_EFF, dp_frac=DELTA_P_FRAC):
    """Run the design point, falling back to an offset low-side pressure if it will not close.

    Returns (model, note) where note describes any fallback that was applied.

    Return the MODEL, never model.Outputs: the Outputs group does not keep its parent alive,
    so handing the caller a bare Outputs lets the model be garbage-collected out from under
    it and the next attribute read segfaults the interpreter with no traceback.
    """
    p_low = P_HIGH_MPA / PRESSURE_RATIO
    try:
        m = build(recup_eff, dp_frac)
        m.execute(0)
        o = m.Outputs
        # ssc can report "success" while silently collapsing the cycle (CLAUDE.md 4.3).
        assert o.recomp_frac > 1e-6, "collapsed to simple recuperated (f_rc = 0)"
        assert not math.isnan(o.q_dot_HTR), "HTR inactive -- recompression not engaged"
        assert o.P_comp_in > 7.4, "compressor inlet fell below the critical pressure"
        return m, ""
    except Exception as exc:
        offset = p_low + P_LOW_OFFSET_MPA
        m = build(recup_eff, dp_frac, p_low_fixed=offset)
        m.execute(0)
        note = ("NEAR-CRITICAL FALLBACK APPLIED: the solver failed at P_low = %.4f MPa\n"
                "  (%s)\n"
                "  retried with P_low pinned at %.4f MPa (+%.2f MPa), giving PR = %.4f "
                "instead of %.2f."
                % (p_low, str(exc)[:120], offset, P_LOW_OFFSET_MPA, P_HIGH_MPA / offset,
                   PRESSURE_RATIO))
        return m, note


def git_commit():
    """Short hash of the commit that produced a result, or 'unknown' outside a work tree."""
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                               capture_output=True, text=True, check=True)
        return out.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "")
    except Exception:
        return "unknown"


class Tee(object):
    """Mirror everything printed to the console into the results .md as well."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for st in self.streams:
            st.write(text)

    def flush(self):
        for st in self.streams:
            st.flush()


def coolprop_states(T_C, P_MPa):
    """Re-evaluate h and s at every real node from (T, P) using CoolProp CO2."""
    h = np.full(len(T_C), np.nan)
    s = np.full(len(T_C), np.nan)
    for i in range(N_REAL):
        h[i] = PropsSI("H", "T", T_C[i] + 273.15, "P", P_MPa[i] * 1e6, "CO2") / 1000.0
        s[i] = PropsSI("S", "T", T_C[i] + 273.15, "P", P_MPa[i] * 1e6, "CO2") / 1000.0
    return h, s


def report(m, note, label, case):
    o = m.Outputs                   # m stays referenced for the whole function -- see solve()
    T = np.array(o.T_state_points)
    P = np.array(o.P_state_points)
    h_sam = np.array(o.h_state_points)
    s_sam = np.array(o.s_state_points)
    h, s = coolprop_states(T, P)
    f = o.recomp_frac
    T_amb_K = 273.15 + (T_MC_IN_C - DT_MC_APPROACH)

    # m_dot_co2_full and m_dot_htf_des are DOCUMENTED as kg/s but come out 1000x larger;
    # likewise q_dot_PHX / t_W_dot are documented MW but are really kW. Derive the mass flow
    # from the turbine duty instead of trusting the label, then assert the two agree -- if a
    # future PySAM fixes the scaling this assert fires instead of silently skewing the exergy.
    mdot = o.t_W_dot / (h[5] - h[6])                    # kg/s, from W = m*(h_in - h_out)
    assert abs(mdot - o.m_dot_co2_full / 1000.0) / mdot < 1e-6, (
        "m_dot_co2_full scaling changed: energy balance gives %.4f kg/s, output reports %.4f"
        % (mdot, o.m_dot_co2_full))
    mdot_htf = o.m_dot_htf_des / 1000.0                 # kg/s, same 1000x scaling

    print("=" * 96)
    print(label)
    print("=" * 96)
    if note:
        print("  !! " + note.replace("\n", "\n  "))
        print()

    print("  turbine inlet       %8.3f C   (target %.1f)" % (o.T_turb_in, T_TURB_IN_C))
    print("  compressor inlet    %8.3f C   (target %.1f)" % (o.T_comp_in, T_MC_IN_C))
    print("  P_comp_out          %8.4f MPa (target %.2f)" % (o.P_comp_out, P_HIGH_MPA))
    print("  P_comp_in           %8.4f MPa (target %.4f)"
          % (o.P_comp_in, P_HIGH_MPA / PRESSURE_RATIO))
    print("  pressure ratio      %8.4f     (target %.2f)"
          % (o.P_comp_out / o.P_comp_in, PRESSURE_RATIO))
    print("  recomp_frac         %8.5f     (target %.2f)" % (f, F_RECOMP))
    print("  eff_HTR / eff_LTR   %8.5f / %.5f" % (o.eff_HTR, o.eff_LTR))
    print("  recup UA total      %8.1f kW/K" % o.recup_total_UA_calculated)
    print("  m_dot_co2           %8.3f kg/s   (m_dot_htf %.3f kg/s, cp_htf %.4f kJ/kg-K)"
          % (mdot, o.m_dot_htf_des / 1000.0,
             o.q_dot_PHX / ((o.m_dot_htf_des / 1000.0)
                            * (T_TURB_IN_C + DT_PHX_HOT_APPROACH - o.T_htf_cold_des))))
    print()
    print("  ETA_THERMAL         %8.5f  = %.2f %%" % (o.eta_thermal_calc,
                                                      100.0 * o.eta_thermal_calc))
    print("  Dostal target       %8.5f  = %.2f %%" % (ETA_TARGET, 100.0 * ETA_TARGET))
    print("  deviation           %+8.2f percentage points  (%+.2f %% relative)"
          % (100.0 * (o.eta_thermal_calc - ETA_TARGET),
             100.0 * (o.eta_thermal_calc - ETA_TARGET) / ETA_TARGET))
    print("  eta net less cooling%8.5f  (fan power %.1f kW deducted)"
          % (o.eta_thermal_net_less_cooling_des, o.cooler_tot_W_dot_fan))

    # --- state-point table, CoolProp properties ------------------------------
    print()
    print("STATE POINTS  (h, s from CoolProp CO2 at the ssc-solved T and P)")
    print("%-3s %-10s %9s %11s %10s %11s   %s"
          % ("#", "node", "T[C]", "P[kPa]", "h[kJ/kg]", "s[kJ/kg-K]", "description"))
    print("-" * 96)
    for i, nm in enumerate(NODES):
        code, desc = nm.split(None, 1)      # NODES entries are "CODE   description"
        if i < N_REAL:
            print("%-3d %-10s %9.3f %11.2f %10.3f %11.5f   %s"
                  % (i, code, T[i], P[i] * 1000.0, h[i], s[i], desc))
        else:
            print("%-3d %-10s %9s %11s %10s %11s   %s"
                  % (i, code, "nan", "nan", "nan", "nan", desc))

    # --- property cross-check: ssc's internal CO2 tables vs CoolProp ---------
    dh = np.abs(h[:N_REAL] - h_sam[:N_REAL])
    ds = np.abs(s[:N_REAL] - s_sam[:N_REAL])
    print("\nproperty cross-check   max |h_ssc - h_CoolProp| = %.2e kJ/kg"
          "   max |s_ssc - s_CoolProp| = %.2e kJ/kg-K" % (dh.max(), ds.max()))
    assert dh.max() < 1e-2 and ds.max() < 1e-5, "ssc CO2 properties disagree with CoolProp"

    # --- mixer energy balance ------------------------------------------------
    mixed = (1.0 - f) * h[2] + f * h[9]
    err = abs(h[3] - mixed)
    print("mixer energy balance   h[3] = %.4f   (1-f)h[2] + f*h[9] = %.4f   err %.2e kJ/kg"
          % (h[3], mixed, err))
    assert err < 1e-2, "mixer does not close -- state-point ordering is not as assumed"

    # --- second law, component by component ----------------------------------
    # Entropy generation rate, kW/K. Adiabatic components: m*(s_out - s_in).
    # The precooler and the PHX exchange heat with a reservoir, so they carry a Q/T term.
    q_cool = mdot * (1.0 - f) * (h[8] - h[0])           # kW rejected to ambient
    # Salt side of the PHX, treated as an incompressible stream: mean cp backed out of the
    # duty so the entropy term uses exactly the enthalpy change ssc solved for.
    T_htf_hot_C = T_TURB_IN_C + DT_PHX_HOT_APPROACH
    T_htf_hot_K = T_htf_hot_C + 273.15
    T_htf_cold_K = o.T_htf_cold_des + 273.15
    cp_htf = o.q_dot_PHX / (mdot_htf * (T_htf_hot_C - o.T_htf_cold_des))

    terms = {
        "MC   main compressor": mdot * (1 - f) * (s[1] - s[0]),
        "RC   recompressor":    mdot * f * (s[9] - s[8]),
        "TURB turbine":         mdot * (s[6] - s[5]),
        "LTR  low-T recup":     mdot * ((1 - f) * (s[2] - s[1]) + (s[8] - s[7])),
        "HTR  high-T recup":    mdot * ((s[4] - s[3]) + (s[7] - s[6])),
        "MIX  mixer":           mdot * (s[3] - ((1 - f) * s[2] + f * s[9])),
        "COOL precooler":       mdot * (1 - f) * (s[0] - s[8]) + q_cool / T_amb_K,
        "PHX  primary HX":      mdot * (s[5] - s[4])
                                + mdot_htf * cp_htf * math.log(T_htf_cold_K / T_htf_hot_K),
    }
    print("\nENTROPY GENERATION  (T0 = %.2f K = ambient)" % T_amb_K)
    ok = True
    for k, sgen in terms.items():
        flag = "" if sgen > 0 else "   <-- SECOND-LAW VIOLATION"
        if sgen <= 0:
            ok = False
        print("   %-22s Sgen %+9.5f kW/K    Edest %9.2f kW%s"
              % (k, sgen, T_amb_K * sgen, flag))
    print("   %-22s Sgen %+9.5f kW/K    Edest %9.2f kW"
          % ("TOTAL", sum(terms.values()), T_amb_K * sum(terms.values())))
    assert ok, "at least one component generates negative entropy"

    # --- power balance closes ------------------------------------------------
    w_net = o.t_W_dot - o.mc_W_dot - o.rc_W_dot
    print("\npower balance   W_turb %.2f - W_mc %.2f - W_rc %.2f = %.2f kW"
          "   (W_dot_net_des %.2f, err %.2e)"
          % (o.t_W_dot, o.mc_W_dot, o.rc_W_dot, w_net, W_DOT_NET_DES,
             abs(w_net - W_DOT_NET_DES)))
    print("energy balance  q_PHX %.2f = W_net %.2f + q_cool %.2f  -> err %.3f kW"
          % (o.q_dot_PHX, w_net, q_cool, abs(o.q_dot_PHX - w_net - q_cool)))

    rows = [{"case": case, "idx": i, "node": NODES[i].split(None, 1)[0],
             "description": NODES[i].split(None, 1)[1],
             "T_C": T[i], "P_kPa": P[i] * 1000.0, "h_kJ_per_kg": h[i], "s_kJ_per_kgK": s[i]}
            for i in range(len(NODES))]
    return o.eta_thermal_calc, rows


def eff_sweep():
    """Locate the recuperator effectiveness at which the model reproduces Dostal's 51.27%."""
    print("\n" + "=" * 96)
    print("RECUPERATOR EFFECTIVENESS SWEEP -- where does this model land on Dostal's 51.27%?")
    print("=" * 96)
    print("%12s %12s %14s %12s" % ("recup eff", "eta_thermal", "UA_tot [kW/K]", "d vs Dostal"))
    xs, ys = [], []
    for e in (0.90, 0.92, 0.93, 0.94, 0.945, 0.95, 0.96, 0.97):
        try:
            m, _ = solve(recup_eff=e)
            o = m.Outputs
            xs.append(e)
            ys.append(o.eta_thermal_calc)
            print("%12.4f %12.5f %14.1f %+11.2f pp"
                  % (e, o.eta_thermal_calc, o.recup_total_UA_calculated,
                     100.0 * (o.eta_thermal_calc - ETA_TARGET)))
        except Exception as exc:
            print("%12.4f  FAILED: %s" % (e, str(exc)[:70]))
    rows = [{"recup_eff": e, "eta_thermal": y, "delta_vs_dostal_pp": 100.0 * (y - ETA_TARGET)}
            for e, y in zip(xs, ys)]
    if len(xs) > 1:
        # np.interp needs an increasing x; eta rises monotonically with effectiveness.
        e_match = np.interp(ETA_TARGET, ys, xs)
        print("\n  -> eta = %.2f %% is reproduced at recuperator effectiveness ~ %.4f"
              % (100.0 * ETA_TARGET, e_match))
    return rows


def run_all():
    """The whole report, in print order. Returns (base eta, state rows, sweep rows)."""
    eta, rows = report(*solve(), case="base_lossless", label=(
        "DOSTAL 2004 HIGH-PERFORMANCE RECOMPRESSION -- BASE CASE\n"
        "  recuperator effectiveness %.3f, zero pressure loss (PR is exactly %.2f)"
        % (RECUP_EFF, PRESSURE_RATIO)))

    print("\n")
    _, rows_dp = report(*solve(dp_frac=0.0054), case="with_0.54pct_dP", label=(
        "SENSITIVITY -- SAME CASE WITH SAM'S STOCK 0.54%% PER-HX PRESSURE LOSS\n"
        "  recuperator effectiveness %.3f" % RECUP_EFF))

    sweep = eff_sweep()

    print("\n" + "=" * 96)
    print("VERDICT: converged at %.2f MPa / %.1f C compressor inlet; eta_thermal = %.2f %% "
          "vs Dostal %.2f %%." % (P_HIGH_MPA / PRESSURE_RATIO, T_MC_IN_C,
                                  100.0 * eta, 100.0 * ETA_TARGET))
    print("=" * 96)
    return eta, rows + rows_dp, sweep


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    # Durable results, not just scrollback (CLAUDE.md section 0.2).
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = git_commit()
    md_path = os.path.join(RESULTS_DIR, "dostal_validation_%s.md" % stamp)

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# sCO2 recompression cycle -- Dostal (2004) validation\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/validate_dostal.py` |\n"
                 "| run (UTC) | %s |\n"
                 "| git commit | `%s` |\n"
                 "| PySAM | 7.1.1.post1 (bundled ssc 306) |\n"
                 "| CO2 properties | CoolProp 8.0.0, cross-checked against ssc |\n"
                 "| Dostal target eta | %.2f %% |\n\n```\n"
                 % (stamp, commit, 100.0 * ETA_TARGET))
        real_stdout = sys.stdout
        sys.stdout = Tee(real_stdout, fh)
        try:
            _, state_rows, sweep_rows = run_all()
        finally:
            sys.stdout = real_stdout
        fh.write("```\n")

    sp_path = os.path.join(RESULTS_DIR, "dostal_state_points_%s.csv" % stamp)
    sw_path = os.path.join(RESULTS_DIR, "dostal_recup_sweep_%s.csv" % stamp)
    write_csv(sp_path, state_rows)
    write_csv(sw_path, sweep_rows)

    print("\nresults written (commit %s):" % commit)
    for p in (md_path, sp_path, sw_path):
        print("   %s" % os.path.relpath(p, REPO_ROOT).replace("\\", "/"))


if __name__ == "__main__":
    main()
