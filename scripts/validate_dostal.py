r"""Validate the PySAM sCO2 recompression cycle against Dostal (2004).

Runs the standalone recompression cycle at Dostal's HIGH-PERFORMANCE design point so the
resulting state table can be compared node-by-node against the published one:

    turbine inlet temperature      700 C
    compressor inlet temperature    32 C          (near-critical)
    compressor outlet pressure      20 MPa        (P_high)
    pressure ratio                   2.6          -> P_low = 7.6923 MPa
    recompressed fraction f_rc       0.4097        (NOT the 0.39 of Table 10.1 -- see below)
    recuperators                     10 K approach, both      (NOT equal effectiveness)
    per-HX pressure loss             Dostal's own, from Table 10.4's node pressures
    eta_isen  main compressor        0.89
    eta_isen  recompressor           0.89         (conservative -- NOT 0.948)
    eta_isen  turbine                0.90

Dostal's reported thermal efficiency for this case (conservative turbomachinery) is 51.27%.

*** BASELINE CHANGED 2026-08-13 (Session E): this file now runs CASE F. ***
It reproduces all 8 of Dostal's published nodes to within 0.070% in h, 0.045% in s and 0.000%
in P, with eta_thermal at +0.019 pp. The three settings that differ from the previous baseline
are each READ OFF Dostal's own tables, not fitted: the approach temperatures come from Table
10.4's node temperatures, the pressure losses from its node pressures (the PHX difference lands
on exactly the 130 kPa Table 10.1 states), and f = 0.4097 from closing the mixer on his
published enthalpies. The full argument, including why Table 10.1's f = 0.39 cannot be right
for this design, is VALIDATION.md 2.3.4a.

The previous baseline (equal effectiveness 0.95, lossless, f = 0.39) matched eta to +0.26 pp
but through two CANCELLING errors, leaving internal state points wrong by up to 5.4%. It is
retained as LEGACY_CASE_A -- a regression anchor for environment/ssc drift, NOT a validation
result. Do not quote its numbers as validation.

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
ETA_MC = 0.89           # main compressor isentropic eff       [-]
ETA_RC = 0.89           # recompressor isentropic eff          [-]
ETA_T = 0.90            # turbine isentropic eff               [-]
ETA_TARGET = 0.5127     # Dostal's reported thermal efficiency [-]

# --- Recompressed fraction: 0.4097, NOT the 0.39 Table 10.1 states ---------------------------
# Table 10.1's f and Table 10.4's state points are separate data and they disagree. Imposing the
# HTR, LTR and mixer balances on Dostal's OWN published values -- with RC_OUT fixed independently
# by the recompressor isentropic relation -- closes the mixer only at f = 0.4097. Justifying
# f = 0.39 would require eta_rc = 0.752, against Dostal's stated 0.89 / 0.948; at either stated
# value his table implies f = 0.41-0.42. The Advanced 650 C design, run as a control, needs only
# eta_rc = 0.932 to justify its stated 0.41, so the method is sound and the contrast is real.
# Full analysis: scripts/check_dostal_table_consistency.py, VALIDATION.md 2.3.4a.
F_RECOMP = 0.4097
F_RECOMP_STATED = 0.39  # what Table 10.1 says -- kept for reporting the discrepancy

# --- Recuperators: specified by APPROACH TEMPERATURE, read off Table 10.4 ---------------------
# HTR cold end = node 7 - node 3 = 169.85 - 159.88 = 9.97 K; LTR = node 8 - node 2 = 9.95 K.
# Specifying by approach (design_code 2) rather than effectiveness lets the LTR/HTR duty split
# fall out of the physics -- and it lands UNEQUAL (eff_HTR 0.976 / eff_LTR 0.931), which is what
# Dostal's fixed 120 m3 total HX volume produces and what equal-effectiveness cannot represent.
RECUP_CODE = 2          # 1 = UA, 2 = min approach dT, 3 = effectiveness (CLAUDE.md 4.7)
RECUP_MIN_DT = 10.0     # K
RECUP_EFF = 0.95        # inactive under code 2; used by the legacy case and the sweep

# --- Per-HX CO2 pressure loss: DOSTAL'S OWN, for this exact design ----------------------------
# Derived as consecutive differences of Table 10.4's node pressures -- NOT the Basic-design
# values of Table 10.6. The PHX difference lands on exactly 130.00 kPa, matching Table 10.1's
# stated primary-system dP, which independently confirms the derivation.
#   LTR_HP  node 2->3 : 20000.00 - 19990.22 =   9.78 kPa      HTR_LP  node 6->7 : 126.58 kPa
#   HTR_HP  node 3->4 : 19990.22 - 19944.56 =  45.66 kPa      LTR_LP  node 7->8 :  97.71 kPa
#   PHX     node 4->5 : 19944.56 - 19814.56 = 130.00 kPa      cooler  node 8->1 :  12.62 kPa
DOSTAL_DP_KPA = {
    "LTR_HP": (9.78, 20000.00), "HTR_HP": (45.66, 19990.22), "PHX": (130.00, 19944.56),
    "HTR_LP": (126.58, 7929.22), "LTR_LP": (97.71, 7802.64), "cooler": (12.62, 7704.93),
}
DOSTAL_DP_FRAC = {k: loss / p_in for k, (loss, p_in) in DOSTAL_DP_KPA.items()}

# Fallback for any HX not named in a dp dict. Zero, so an unlisted HX is lossless rather than
# silently inheriting someone else's loss.
DELTA_P_FRAC = 0.0

# The pre-adoption configuration, retained as a REGRESSION ANCHOR only (CLAUDE.md 7): equal
# recuperator effectiveness 0.95, lossless, f = 0.39. It agrees with Dostal on eta to +0.26 pp
# but via two cancelling errors, and its internal state points are wrong by up to 5.4 % -- which
# is why it is no longer the validation baseline. Its value now is that it reproduces
# bit-for-bit across machines, making it a good tripwire for environment or ssc drift.
LEGACY_CASE_A = dict(f_recomp=F_RECOMP_STATED, recup_code=3, recup_eff=RECUP_EFF,
                     dp={k: 0.0 for k in DOSTAL_DP_FRAC})

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


def build(recup_eff=RECUP_EFF, dp_frac=DELTA_P_FRAC, p_low_fixed=None,
          recup_code=RECUP_CODE, recup_min_dT=RECUP_MIN_DT, dp=None, f_recomp=F_RECOMP):
    """Assemble the cycle. p_low_fixed pins the low-side pressure instead of the ratio.

    Defaults are CASE F -- the adopted baseline (VALIDATION.md 2.3.4a). Override them to run a
    different configuration; LEGACY_CASE_A is the pre-adoption one, kept as a regression anchor.
      recup_code    -- 1 = UA, 2 = min approach dT, 3 = effectiveness (CLAUDE.md 4.7).
      recup_min_dT  -- the approach used when recup_code = 2; also the (ignored, but non-zero
                       and therefore non-segfaulting) placeholder otherwise.
      dp            -- per-heat-exchanger pressure-loss FRACTIONS. Keys: HTR_LP, HTR_HP, LTR_LP,
                       LTR_HP, PHX, cooler. Defaults to Dostal's own losses; any key left out
                       falls back to dp_frac.
      f_recomp      -- recompressed fraction, pinned via is_recomp_ok < 0 (CLAUDE.md 4.3).
    """
    dp = DOSTAL_DP_FRAC.copy() if dp is None else dict(dp)
    def dp_of(key):
        return dp.get(key, dp_frac)

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
    c.PHX_co2_deltaP_des_in = dp_of("PHX")
    c.mc_comp_type = 1
    c.is_gen_od_polynomials = 0
    # od_* inputs are ARRAYS -- leave unset for a design-only run (CLAUDE.md 4.1).

    x = m.HeatExchangerDesign
    x.cycle_config = 1                          # 1 = recompression
    x.is_recomp_ok = -abs(f_recomp)             # negative => PIN f_rc (CLAUDE.md 4.3)
    x.is_P_high_fixed = 1                       # P_high = P_high_limit exactly
    # is_PR_fixed: >0 = fixed pressure ratio, <0 = fixed low-side pressure at abs(input)
    x.is_PR_fixed = PRESSURE_RATIO if p_low_fixed is None else -abs(p_low_fixed)
    x.is_IP_fixed = 0
    x.des_objective = 0
    x.min_phx_deltaT = 0
    x.rel_tol = x.od_rel_tol = 4                # tighter than the stock 3 for validation
    # HTR/LTR_design_code: 1 = UA, 2 = min dT, 3 = effectiveness.
    x.HTR_design_code = x.LTR_design_code = recup_code
    x.HTR_eff_des_in = x.LTR_eff_des_in = recup_eff
    # Only the spec matching the selected code is read, but ssc reads the others regardless and
    # a 0.0 in an inactive one segfaults (CLAUDE.md 4.2) -- keep them non-zero placeholders.
    x.HTR_UA_des_in = x.LTR_UA_des_in = 5000.0
    x.HTR_min_dT_des_in = x.LTR_min_dT_des_in = recup_min_dT
    x.HT_recup_eff_max = x.LT_recup_eff_max = 1.0
    x.HTR_n_sub_hx = x.LTR_n_sub_hx = 20
    x.HTR_od_model = x.LTR_od_model = 1
    for a, key in (("HTR_LP_deltaP_des_in", "HTR_LP"), ("HTR_HP_deltaP_des_in", "HTR_HP"),
                   ("LTR_LP_deltaP_des_in", "LTR_LP"), ("LTR_HP_deltaP_des_in", "LTR_HP")):
        setattr(x, a, dp_of(key))

    p = m.PHXDesign
    p.dT_PHX_cold_approach = 20.0
    p.PHX_n_sub_hx = 10
    p.PHX_od_model = 1

    a = m.AirCoolerDesign
    a.is_design_air_cooler = 1
    a.deltaP_cooler_frac = dp_of("cooler")
    a.fan_power_frac = 0.01
    a.eta_air_cooler_fan = 0.5
    a.N_nodes_air_cooler_pass = 10
    return m


def solve(recup_eff=RECUP_EFF, dp_frac=DELTA_P_FRAC, **kw):
    """Run the design point, falling back to an offset low-side pressure if it will not close.

    Returns (model, note) where note describes any fallback that was applied.
    Extra keyword arguments (recup_code, recup_min_dT, dp) pass straight through to build().

    Return the MODEL, never model.Outputs: the Outputs group does not keep its parent alive,
    so handing the caller a bare Outputs lets the model be garbage-collected out from under
    it and the next attribute read segfaults the interpreter with no traceback.
    """
    p_low = P_HIGH_MPA / PRESSURE_RATIO
    try:
        m = build(recup_eff, dp_frac, **kw)
        m.execute(0)
        o = m.Outputs
        # ssc can report "success" while silently collapsing the cycle (CLAUDE.md 4.3).
        assert o.recomp_frac > 1e-6, "collapsed to simple recuperated (f_rc = 0)"
        assert not math.isnan(o.q_dot_HTR), "HTR inactive -- recompression not engaged"
        assert o.P_comp_in > 7.4, "compressor inlet fell below the critical pressure"
        return m, ""
    except Exception as exc:
        offset = p_low + P_LOW_OFFSET_MPA
        m = build(recup_eff, dp_frac, p_low_fixed=offset, **kw)
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


def entropy_generation(o, h, s, mdot, mdot_htf, f, T_amb_K):
    """Per-component entropy generation rate [kW/K], plus the auxiliary quantities it needs.

    Adiabatic components are simply m*(s_out - s_in). The precooler and the PHX exchange heat
    with a reservoir, so they carry a Q/T term as well.

    Shared with scripts/exergy_layer_check.py so the second-law physics is written once. The
    returned aux dict carries q_cool, cp_htf and the HTF end temperatures, which the exergy
    balance needs to compute the exergy actually delivered by the salt.
    """
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
    aux = {"q_cool": q_cool, "cp_htf": cp_htf,
           "T_htf_hot_K": T_htf_hot_K, "T_htf_cold_K": T_htf_cold_K}
    return terms, aux


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
    print("  recomp_frac         %8.5f     (target %.4f; Table 10.1 states %.2f -- see 2.3.4a)"
          % (f, F_RECOMP, F_RECOMP_STATED))
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
    terms, aux = entropy_generation(o, h, s, mdot, mdot_htf, f, T_amb_K)
    q_cool = aux["q_cool"]
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
    """Recuperator effectiveness sweep, run in the LEGACY case-A parameterisation.

    Retained because VALIDATION.md 2.3.4a cites it: it is the evidence that the old baseline
    reproduced Dostal's eta at effectiveness ~0.9467, LOOSER than his own ~10 K approach implies.
    That mismatch is what exposed the cancelling-error problem in case A. It says nothing about
    the adopted case F, which specifies the recuperators by approach temperature instead.
    """
    print("\n" + "=" * 96)
    print("RECUPERATOR EFFECTIVENESS SWEEP -- LEGACY case-A parameterisation (see docstring)")
    print("=" * 96)
    print("%12s %12s %14s %12s" % ("recup eff", "eta_thermal", "UA_tot [kW/K]", "d vs Dostal"))
    xs, ys = [], []
    legacy = {k: v for k, v in LEGACY_CASE_A.items() if k != "recup_eff"}
    for e in (0.90, 0.92, 0.93, 0.94, 0.945, 0.95, 0.96, 0.97):
        try:
            m, _ = solve(recup_eff=e, **legacy)
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
    """The whole report, in print order. Returns (baseline eta, state rows, sweep rows)."""
    eta, rows = report(*solve(), case="case_F_adopted", label=(
        "DOSTAL 2004 HIGH-PERFORMANCE RECOMPRESSION -- CASE F (ADOPTED BASELINE)\n"
        "  f_rc %.4f, recuperators at %.1f K approach, Dostal's own per-HX pressure loss.\n"
        "  All three read from his published data; none fitted. See VALIDATION.md 2.3.4a."
        % (F_RECOMP, RECUP_MIN_DT)))

    print("\n")
    eta_a, rows_a = report(*solve(**LEGACY_CASE_A), case="legacy_case_A", label=(
        "LEGACY CASE A -- REGRESSION ANCHOR ONLY, NOT THE VALIDATION BASELINE\n"
        "  equal recuperator effectiveness %.3f, lossless, f_rc %.2f. Agrees with Dostal on eta\n"
        "  via two CANCELLING errors while its internal states are wrong by up to 5.4 %%; kept\n"
        "  because it reproduces bit-for-bit across machines, so it catches environment drift."
        % (RECUP_EFF, F_RECOMP_STATED)))

    sweep = eff_sweep()

    print("\n" + "=" * 96)
    print("VERDICT: converged at %.2f MPa / %.1f C compressor inlet." %
          (P_HIGH_MPA / PRESSURE_RATIO, T_MC_IN_C))
    print("  adopted case F : eta_thermal = %.3f %%  (%+.3f pp vs Dostal %.2f %%)"
          % (100.0 * eta, 100.0 * (eta - ETA_TARGET), 100.0 * ETA_TARGET))
    print("  legacy  case A : eta_thermal = %.3f %%  (%+.3f pp) -- anchor only"
          % (100.0 * eta_a, 100.0 * (eta_a - ETA_TARGET)))
    print("=" * 96)
    return eta, rows + rows_a, sweep


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
