r"""Smoke test for the PySAM lane.

Proves, in one run:
  1. the env is wired correctly (PySAM + its bundled ssc load and solve),
  2. the sCO2 recompression cycle converges to a genuine recompression design,
  3. per-state T / P / h / s are exposed at every node -- the exergy gate.

Run:  .\.venv\Scripts\python.exe -u .\scripts\smoke_test.py
Expected numbers are pinned in CLAUDE.md section 7.
"""

import math
import numpy as np
import PySAM.Sco2CspSystem as S

# State-point index -> physical node. Verified against the mixer energy balance below.
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

F_RECOMP = 0.30
T_AMB_C = 35.0


def build(f_recomp=F_RECOMP):
    m = S.new()

    d = m.SystemDesign
    d.htf = 17                      # 60% NaNO3 / 40% KNO3
    d.T_htf_hot_des = 720.0         # C
    d.W_dot_net_des = 10000.0       # kWe
    d.T_amb_des = T_AMB_C
    d.dT_PHX_hot_approach = 20.0
    d.dT_mc_approach = 6.0
    d.site_elevation = 588.0
    d.design_method = 3             # specify each recuperator individually

    c = m.Common
    c.eta_isen_mc = c.eta_isen_rc = c.eta_isen_pc = 0.85
    c.eta_isen_t = 0.90
    c.P_high_limit = 25.0           # MPa
    c.deltaP_counterHX_frac = 0.0054
    c.PHX_co2_deltaP_des_in = 0.0054
    c.mc_comp_type = 1
    c.is_gen_od_polynomials = 0
    # NB: od_generate_udpc / od_set_control / od_T_t_in_mode are ARRAY inputs.
    # Leave them unset for a design-only run (see CLAUDE.md 4.1).

    x = m.HeatExchangerDesign
    x.cycle_config = 1                    # 1 = recompression, 2 = partial cooling
    x.is_recomp_ok = -abs(f_recomp)       # negative => PIN f_rc (see CLAUDE.md 4.3)
    x.is_P_high_fixed = 1
    x.is_PR_fixed = 0
    x.is_IP_fixed = 0
    x.des_objective = 0
    x.min_phx_deltaT = 0
    x.rel_tol = x.od_rel_tol = 3
    # HTR/LTR_design_code: 1 = UA, 2 = min dT, 3 = effectiveness.
    # This is a min-dT design: only HTR/LTR_min_dT_des_in below is read. The UA and
    # effectiveness inputs are ignored -- but they must still be present and NON-ZERO,
    # because leaving them at 0.0 segfaults the interpreter (CLAUDE.md 4.2).
    x.HTR_design_code = x.LTR_design_code = 2      # 2 = specify minimum approach dT
    x.HTR_min_dT_des_in = x.LTR_min_dT_des_in = 10.0   # C -- the ACTIVE recuperator spec
    x.HTR_UA_des_in = x.LTR_UA_des_in = 7000.0     # unused placeholder (and it is W/K, not kW/K)
    x.HTR_eff_des_in = x.LTR_eff_des_in = 1.0      # unused placeholder
    x.HT_recup_eff_max = x.LT_recup_eff_max = 1.0
    x.HTR_n_sub_hx = x.LTR_n_sub_hx = 15
    x.HTR_od_model = x.LTR_od_model = 1
    for a in ("HTR_LP_deltaP_des_in", "HTR_HP_deltaP_des_in",
              "LTR_LP_deltaP_des_in", "LTR_HP_deltaP_des_in"):
        setattr(x, a, 0.0054)

    p = m.PHXDesign
    p.dT_PHX_cold_approach = 20.0
    p.PHX_n_sub_hx = 10
    p.PHX_od_model = 1

    a = m.AirCoolerDesign
    a.is_design_air_cooler = 1
    a.deltaP_cooler_frac = 0.005
    a.fan_power_frac = 0.01
    a.eta_air_cooler_fan = 0.5
    a.N_nodes_air_cooler_pass = 10
    return m


def main():
    m = build()
    m.execute(0)
    o = m.Outputs

    # --- guard against the silent simple-cycle collapse (CLAUDE.md 4.3) -------
    assert o.recomp_frac > 1e-6, "cycle collapsed to simple recuperated (f_rc = 0)"
    assert not math.isnan(o.q_dot_HTR), "HTR inactive -- recompression not engaged"

    print("=" * 74)
    print("sCO2 RECOMPRESSION DESIGN")
    print("  eta_thermal_calc %.5f      recomp_frac %.5f" % (o.eta_thermal_calc, o.recomp_frac))
    print("  P_comp_in  %.4f MPa        P_comp_out  %.4f MPa" % (o.P_comp_in, o.P_comp_out))
    print("  q_dot_HTR  %10.2f kW      eff_HTR %.5f" % (o.q_dot_HTR, o.eff_HTR))
    print("  q_dot_LTR  %10.2f kW      eff_LTR %.5f" % (o.q_dot_LTR, o.eff_LTR))
    print("=" * 74)

    T = np.array(o.T_state_points)
    P = np.array(o.P_state_points)
    h = np.array(o.h_state_points)
    s = np.array(o.s_state_points)

    print("%-3s %-48s %9s %8s %10s %11s" % ("#", "node", "T[C]", "P[MPa]", "h[kJ/kg]", "s[kJ/kg-K]"))
    print("-" * 94)
    for i, nm in enumerate(NODES):
        print("%-3d %-48s %9.3f %8.4f %10.3f %11.5f" % (i, nm, T[i], P[i], h[i], s[i]))

    # --- node-ordering proof: mixer must close on energy ----------------------
    f = o.recomp_frac
    mixed = (1.0 - f) * h[2] + f * h[9]
    print("\nmixer energy balance   h[3] = %.4f   (1-f)h[2]+f*h[9] = %.4f   err %.2e kJ/kg"
          % (h[3], mixed, abs(h[3] - mixed)))
    assert abs(h[3] - mixed) < 1e-3, "state-point ordering does not match assumed topology"

    # --- component exergy destruction, from exposed states alone --------------
    T0 = 273.15 + T_AMB_C
    # m_dot_co2_full is DOCUMENTED as kg/s but comes out 1000x larger. Derive the flow from
    # the turbine duty instead of trusting the label, then assert the two agree -- if a future
    # PySAM fixes the scaling this fires rather than silently skewing every Sgen below.
    mdot = o.t_W_dot / (h[5] - h[6])                       # kg/s, from W = m*(h_in - h_out)
    assert abs(mdot - o.m_dot_co2_full / 1000.0) / mdot < 1e-6, (
        "m_dot_co2_full scaling changed: energy balance gives %.4f kg/s, output reports %.4f"
        % (mdot, o.m_dot_co2_full))
    terms = {
        "HTR":  (s[4] - s[3]) + (s[7] - s[6]),
        "LTR":  (1 - f) * (s[2] - s[1]) + (s[8] - s[7]),
        "TURB": s[6] - s[5],
        "MC":   (1 - f) * (s[1] - s[0]),
        "RC":   f * (s[9] - s[8]),
        "MIX":  s[3] - ((1 - f) * s[2] + f * s[9]),
    }
    print("\ncomponent exergy destruction (T0 = %.2f K, no CoolProp)" % T0)
    for k, ds in terms.items():
        sgen = mdot * ds
        assert sgen > -1e-6, "second-law violation in %s" % k
        print("   %-5s Sgen %+.5f kW/K    Edest %9.2f kW" % (k, sgen, T0 * sgen))

    print("\nOK - env healthy, recompression engaged, h and s exposed at every node.")


if __name__ == "__main__":
    main()
