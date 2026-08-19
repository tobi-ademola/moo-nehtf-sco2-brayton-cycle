r"""THE EXERGY LAYER -- reusable second-law physics for Objective 2.

WHY THIS EXISTS. `DECISIONS.md` D1 put exergy IN scope, and `scripts/exergy_layer_check.py`
proved on 2026-08-13 that a correct layer can be built from data ssc already carries. But that
proof script solves the Dostal case F baseline and reports it; it is not callable, so the
integrated model had no exergy at all. Under the revised objectives that gap is expensive:
Objective 2 names exergy explicitly, and a response surface needs Ed at **every** swept point,
so a campaign run without it must be re-run to collect it (`DECISIONS.md` D1 annotation,
`MASTER_PLAN.md` §11). This module is the callable layer; `run_integrated_annual.py` consumes it.

WHAT IT PROVIDES, in two tiers that answer different questions:

  TIER 1 -- DESIGN-POINT CYCLE EXERGY (`design_cycle_exergy`). Per-node physical exergy and
      per-COMPONENT destruction for the sCO2 recompression cycle, from ssc's own h and s at the
      10 real nodes. This is the component-level breakdown -- which piece of hardware destroys
      what -- and it is the only tier that can produce one.

  TIER 2 -- ANNUAL PLANT EXERGY (`annual_plant_exergy`). Solar -> HTF -> work over 8760 h, using
      the HOURLY ambient temperature as the dead state. This is a plant-level accounting; it
      LUMPS the power block rather than resolving it into components (see the limitation below).

*** THE LIMITATION THAT DECIDES WHAT TIER 2 CAN HONESTLY CLAIM ***
The annual model reaches the sCO2 cycle through a UDPC map, and that map carries NORMALISED
RESPONSE SHAPES ONLY (CLAUDE.md §4.11/§4.12) -- there are no per-hour state points, so there is
no per-hour h or s, so there is **no per-component Ed at any hour but the design point**. Tier 2
therefore reports the power block's LUMPED destruction, Ex_htf - W_gross, which is exact and
needs no state points, and does NOT attempt a per-component annual split. Producing one would
require re-solving the cycle off-design at every hour (~0.1 s x 8760 x every swept point) or
fitting an off-design Ed regression, and neither is in scope. Do not let a future session infer
an annual component ranking from the design-point one: the design ranking is a single operating
point, and off-design shifts it.

*** TWO DIFFERENT T0's, AND A THIRD FOR THE ANNUAL LAYER ***
  T0_ref  -- an arbitrary REFERENCE state for the per-node table (Dostal node 1 in the
             validation lane). Shifts every e by a constant; node-to-node DIFFERENCES are
             unaffected. Not a dead state -- the cycle cannot reject heat to 7.69 MPa.
  T0_amb  -- the DESIGN environment. Gouy-Stodola Ed = T0*Sgen is only meaningful here, and the
             cycle-wide balance closes only here.
  T0(t)   -- the HOURLY dry-bulb temperature, used by tier 2. A CSP plant's dead state genuinely
             moves through the year, and Objective 5 compares two climates whose ambient
             distributions differ, so freezing T0 at its design value would bury exactly the
             effect that objective is asking about.

*** WHY THIS MODULE OWNS entropy_generation() RATHER THAN validate_dostal.py ***
The physics was written once, in `validate_dostal.entropy_generation`, but it derived the hot
salt temperature from ITS OWN module constants as `T_TURB_IN_C + DT_PHX_HOT_APPROACH` = 720 C.
The integrated model runs `T_htf_hot = 700 C` (`build_udpc_map.T_HTF_HOT_DES_C`), so calling that
function from the integrated lane would have used a hot-end temperature **20 K too high** --
silently inflating the salt-side exergy input and opening the balance, with nothing raised. The
temperature is now an explicit ARGUMENT. `validate_dostal.entropy_generation` delegates here and
passes its own constant, so the validation baselines are untouched and the physics stays single-
source. If you add a caller, pass the hot temperature YOUR case actually runs at.

INPUTS. None of its own. Pure Python + `math`; `scripts/nanofluid_properties.py` is imported only
by `annual_plant_exergy`, for the HTF cp used in the stream-exergy integral -- which keeps the
exergy layer consistent with the Objective 1 property module instead of hardcoding a cp.

HOW TO RUN (self-check on analytic cases -- no PySAM, ~0.1 s):
    .\.venv\Scripts\python.exe -u .\scripts\exergy.py

CONSUMED BY. scripts/run_integrated_annual.py (both tiers),
             scripts/validate_dostal.py (entropy_generation only).
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Sun's effective blackbody temperature for the Petela solar-exergy factor. 5778 K is the
# standard effective radiating temperature; the factor is insensitive to it (5700 vs 5800 K
# moves psi by <0.1 %), so this is not a tuning knob.
T_SUN_K = 5778.0

# The 10 real state points of the recompression cycle. Nodes 10/11 are the partial-cooling
# pre-compressor and are legitimately NaN for cycle_config = 1 -- never sum the raw 12-element
# arrays (CLAUDE.md §4.5).
N_REAL = 10

NODE_CODES = ("MC_IN", "MC_OUT", "LTR_HP_OUT", "MIXER_OUT", "HTR_HP_OUT",
              "TURB_IN", "TURB_OUT", "HTR_LP_OUT", "LTR_LP_OUT", "RC_OUT")


# =============================================================================
# Primitives
# =============================================================================
def petela_factor(T0_K: float, T_sun_K: float = T_SUN_K) -> float:
    """Maximum work fraction extractable from blackbody radiation at T_sun.

    psi = 1 - (4/3)(T0/Ts) + (1/3)(T0/Ts)^4    [Petela 1964; Jeter; Spanner]

    Used rather than the Carnot factor (1 - T0/Ts) because the solar input is RADIATION, not
    heat from a reservoir. At T0 = 300 K it gives ~0.9308 against Carnot's 0.9481 -- a ~1.8 pp
    difference that would otherwise show up as a systematic optimism in every plant-level
    second-law efficiency.
    """
    r = T0_K / T_sun_K
    return 1.0 - (4.0 / 3.0) * r + (1.0 / 3.0) * r ** 4


def node_exergy(h, s, T0_K: float, i_ref: int = 0, n: int = N_REAL) -> list:
    """Physical exergy per node [kJ/kg]:  e = (h - h0) - T0*(s - s0).

    h0/s0 are taken at node `i_ref`, so e(i_ref) = 0 BY CONSTRUCTION. That identity verifies the
    arithmetic is wired correctly; it does NOT verify the physics, because the reference node is
    not generally a dead state.
    """
    h0, s0 = h[i_ref], s[i_ref]
    return [(h[i] - h0) - T0_K * (s[i] - s0) for i in range(n)]


def stream_exergy_rate(mdot: float, cp: float, T_hot_K: float, T_cold_K: float,
                       T0_K: float) -> float:
    """Exergy [kW] delivered by an incompressible stream cooling T_hot -> T_cold.

        Ex = m * cp * [ (T_hot - T_cold) - T0 * ln(T_hot / T_cold) ]

    Molten salt is treated as incompressible (no pressure term), which is standard for a
    liquid-phase HTF and is what makes the cycle-wide balance close to 1e-4 relative in
    `exergy_layer_check.py`. Units: mdot [kg/s], cp [kJ/(kg K)], temperatures [K] -> kW.
    """
    if T_hot_K <= 0 or T_cold_K <= 0:
        raise ValueError("stream temperatures must be absolute (K) and positive")
    return mdot * cp * ((T_hot_K - T_cold_K) - T0_K * math.log(T_hot_K / T_cold_K))


def carnot_lm_factor(T_hot_K: float, T_cold_K: float, T0_K: float) -> float:
    """Availability fraction of heat delivered by a stream cooling T_hot -> T_cold.

        f = 1 - T0 * ln(T_hot/T_cold) / (T_hot - T_cold)

    i.e. the Carnot factor evaluated at the stream's LOG-MEAN temperature. Multiply a duty by
    this to get its exergy. Reduces to the isothermal Carnot factor as T_hot -> T_cold.

    ⚠ COMPUTED WITH log1p, NOT log(T_hot/T_cold). The naive form catastrophically cancels for
    a small temperature drop: ln(T_hot/T_cold) and (T_hot - T_cold) both go to zero, and in
    float64 the ratio becomes noise long before the difference underflows. An earlier version
    guarded with `abs(dT) < 1e-12` and still returned garbage at dT = 1e-9 K -- caught by the
    continuity assertion in validate(), not by inspection. log1p is accurate to full precision
    for small arguments, so the expression is smooth all the way down to dT = 0. This matters
    in practice: near-isothermal hours are exactly what deep part-load and TES-hold produce.
    """
    if T_hot_K <= 0 or T_cold_K <= 0:
        raise ValueError("stream temperatures must be absolute (K) and positive")
    dT = T_hot_K - T_cold_K
    if dT == 0.0:
        return 1.0 - T0_K / T_hot_K
    # ln(T_hot/T_cold) = log1p(dT/T_cold); dividing by dT keeps the quotient well-conditioned.
    return 1.0 - T0_K * math.log1p(dT / T_cold_K) / dT


def heat_stream_exergy_rate(q_dot: float, T_hot_K: float, T_cold_K: float,
                            T0_K: float) -> float:
    """Exergy of a stream duty -- SAME physics as `stream_exergy_rate`, different parameters.

        Ex = q_dot * [ 1 - T0 * ln(T_hot/T_cold) / (T_hot - T_cold) ]

    Algebraically IDENTICAL to the mass-flow form whenever q_dot = mdot*cp*(T_hot - T_cold);
    `validate()` asserts that equivalence. Units follow q_dot.

    *** WHY THE ANNUAL LAYER USES THIS ONE AND THE DESIGN LAYER DOES NOT ***
    Measured 2026-08-19 (`scripts/diagnose_negative_exergy_hours.py`, artifact
    `results/negative_exergy_hours_*`): in deep part-load hours the tower's `m_dot_pc` does NOT
    reconcile with the `q_pb` reported for the same hour -- the flow-derived duty came out a
    median 61 % LOW *within those hours*, driving 27 of 6040 operating hours to a negative Ed, a second-law
    violation. In those same hours `q_pb` and `P_cycle` are mutually consistent (their ratio is
    the reported hourly efficiency), so the duty is the trustworthy term and the mass flow is
    not. At the DESIGN point the two agree exactly (1240 kg/s x 1.0966 kJ/kgK x 166.7 K =
    226.7 MW = peak q_pb), which is why the discrepancy is invisible to any design-point check.

    Tier 1 keeps the mass-flow form deliberately: there the flow is derived from the turbine
    duty and cross-asserted (`co2_mass_flow`), and the cycle-wide balance closes to 1.5e-04 on
    it. This is not an inconsistency between the tiers -- each uses the quantity that is
    trustworthy in its own lane, and both are the same equation.
    """
    return q_dot * carnot_lm_factor(T_hot_K, T_cold_K, T0_K)


# =============================================================================
# Tier 1 -- design-point cycle exergy
# =============================================================================
def entropy_generation(o, h, s, mdot, mdot_htf, f, T_amb_K, T_htf_hot_C):
    """Per-component entropy generation rate [kW/K], plus the auxiliaries the balance needs.

    Adiabatic components are simply m*(s_out - s_in). The precooler and the PHX exchange heat
    with a reservoir, so they carry a Q/T term as well.

    ⚠ `T_htf_hot_C` IS AN ARGUMENT, NOT A CONSTANT. It used to be derived inside this function
    from validate_dostal's own `T_TURB_IN_C + DT_PHX_HOT_APPROACH` (= 720 C), which is correct
    for the Dostal validation case and **wrong by 20 K for the integrated model**, which runs a
    700 C hot tank. Pass the temperature your case actually runs at; the PHX entropy term and
    the whole salt-side exergy input both scale with it.

    `mdot` and `mdot_htf` must already be in kg/s. ssc reports both 1000x their documented
    value (CLAUDE.md §4.9), so derive the CO2 flow from the turbine duty rather than reading the
    label -- see `co2_mass_flow()`.
    """
    q_cool = mdot * (1.0 - f) * (h[8] - h[0])           # kW rejected to ambient
    T_htf_hot_K = T_htf_hot_C + 273.15
    T_htf_cold_K = o.T_htf_cold_des + 273.15
    # Mean salt cp backed out of the duty ssc actually solved, so the entropy term uses exactly
    # that enthalpy change rather than a separately-evaluated correlation.
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


def co2_mass_flow(o, h) -> float:
    """CO2 mass flow [kg/s], derived from the turbine duty rather than read off the label.

    `m_dot_co2_full` documents kg/s and comes out 1000x larger (CLAUDE.md §4.9). Deriving it and
    asserting the two agree means a future PySAM that fixes the scaling trips the assert instead
    of silently skewing every exergy number in the project.
    """
    mdot = o.t_W_dot / (h[5] - h[6])
    ratio = abs(mdot - o.m_dot_co2_full / 1000.0) / mdot
    assert ratio < 1e-6, (
        "m_dot_co2_full scaling changed: the turbine energy balance gives %.4f kg/s but the "
        "output reports %.4f kg/s (relative %.2e). CLAUDE.md §4.9 assumed a 1000x offset; "
        "re-derive it before trusting any exergy number." % (mdot, o.m_dot_co2_full, ratio))
    return mdot


def design_cycle_exergy(o, h, s, T_amb_K: float, T_htf_hot_C: float,
                        T0_ref_K: float | None = None, i_ref: int = 0) -> dict:
    """The whole tier-1 layer for one solved design point.

    Returns per-node exergy, per-component destruction, the second-law efficiency, and the
    cycle-wide balance residual. `T0_ref_K` only affects the reported per-node reference column;
    every destruction number is at `T_amb_K`, because Gouy-Stodola is meaningful only at the
    environment (see the module docstring).

    THE BALANCE IS THE LOAD-BEARING CHECK, not the per-component signs. Ex_in(salt) = W_net +
    sum(Ed) exercises every h, every s, both mass flows, the salt properties and the work terms
    at once, so it catches unit and scaling errors that sign checks cannot.
    """
    mdot = co2_mass_flow(o, h)
    mdot_htf = o.m_dot_htf_des / 1000.0                  # same 1000x scaling as the CO2 flow
    f = o.recomp_frac
    w_net = o.t_W_dot - o.mc_W_dot - o.rc_W_dot          # kW (labelled MW -- §4.9)

    terms, aux = entropy_generation(o, h, s, mdot, mdot_htf, f, T_amb_K, T_htf_hot_C)
    sgen_total = sum(terms.values())
    ed = {k: T_amb_K * v for k, v in terms.items()}
    ed_total = T_amb_K * sgen_total

    ex_in = stream_exergy_rate(mdot_htf, aux["cp_htf"], aux["T_htf_hot_K"],
                               aux["T_htf_cold_K"], T_amb_K)
    residual = ex_in - w_net - ed_total

    worst = max(terms, key=lambda k: terms[k])
    return {
        "e_nodes_T0amb": node_exergy(h, s, T_amb_K, i_ref=i_ref),
        "e_nodes_T0ref": (node_exergy(h, s, T0_ref_K, i_ref=i_ref)
                          if T0_ref_K is not None else None),
        "sgen_kW_per_K": terms,
        "sgen_total_kW_per_K": sgen_total,
        "Ed_kW": ed,
        "Ed_total_kW": ed_total,
        "Ed_share_pct": {k: 100.0 * v / ed_total for k, v in ed.items()},
        "largest_destroyer": worst,
        "largest_destroyer_share_pct": 100.0 * terms[worst] / sgen_total,
        "W_net_kW": w_net,
        "Ex_in_salt_kW": ex_in,
        "eta_II": w_net / ex_in,
        "balance_residual_kW": residual,
        "balance_residual_rel": residual / ex_in,
        "balance_closes": abs(residual / ex_in) < 1e-3,
        "all_components_positive": all(v > 0 for v in terms.values()),
        "T_amb_K": T_amb_K,
        "T_htf_hot_C": T_htf_hot_C,
        "m_dot_co2_kg_s": mdot,
        "m_dot_htf_kg_s": mdot_htf,
        "cp_htf_kJ_kgK": aux["cp_htf"],
    }


# =============================================================================
# Tier 2 -- annual plant exergy
# =============================================================================
def annual_plant_exergy(*, q_sf_inc_MW, q_pb_MW, T_pc_in_C, T_pc_out_C,
                        P_cycle_MW, gen_kW, tdry_C, phi_mass,
                        m_dot_pc_kg_s=None, cp_fallback_kJ_kgK=None) -> dict:
    """Plant-level exergy accounting over 8760 h, with an HOURLY dead state.

    Every array is an 8760-length hourly series straight off `TcsmoltenSalt.Outputs`. Units are
    verified by execution, not by label (2026-08-19 probe): q_sf_inc [MWt], m_dot_pc [kg/s],
    T_pc_in/out [C], P_cycle [MWe gross], gen [kW net], tdry [C].

    THE DEAD STATE MOVES. T0(t) = tdry(t), not a design constant. Objective 5 compares a MENA
    and a Southern-African site whose ambient distributions differ; freezing T0 would bury the
    very effect that comparison is asking about, and would also misstate the solar exergy, since
    the Petela factor depends on T0.

    *** PARAMETERISED BY DUTY (`q_pb`), NOT BY MASS FLOW -- and that is a measured choice. ***
    The first version integrated m_dot_pc*cp*dT and produced 27 hours of NEGATIVE Ed, a
    second-law violation. `scripts/diagnose_negative_exergy_hours.py` established that in those
    hours `q_pb` and `P_cycle` are mutually consistent while `m_dot_pc` under-reports the duty
    by a median 61 %, so the flow is the untrustworthy term. See `heat_stream_exergy_rate` for
    the full account. Both forms are the same equation; this one rests on the reliable input.

    ⚠ BE PRECISE ABOUT THE SCOPE OF THAT 61 %. It is the median *among the offending hours*.
    Across ALL operating hours the two agree to a median +0.004 % (`mdot_duty_median_dev_pct`,
    measured 2026-08-19), so `m_dot_pc` is NOT broadly wrong -- it diverges in a thin part-load
    tail. The re-parameterisation is therefore a robustness fix against a tail, not a correction
    of a systematically bad output: it moved annual power-block Ed by ~0.05 %.

    `m_dot_pc_kg_s` is now OPTIONAL and purely diagnostic: pass it and the returned dict carries
    `mdot_duty_median_dev_pct`, the median disagreement between the flow-derived duty and
    `q_pb`. It never enters the answer. Keeping it visible means a future PySAM that fixes the
    part-load flow shows up as this number going to zero, rather than the discrepancy being
    silently forgotten once it stopped breaking anything.

    HTF cp comes from `scripts/nanofluid_properties.py` at the hour's mean HTF temperature, so
    the exergy layer and the Objective 1 property model cannot drift apart. It is used ONLY for
    that cross-check now; pass `cp_fallback_kJ_kgK` to bypass the property module (e.g. a
    nitrate control case).

    WHAT IS LUMPED AND WHY. `Ed_power_block` is Ex_htf - W_gross for the hour: exact, and needing
    no state points. It is NOT split by component -- the UDPC path carries no per-hour h or s, so
    a component split does not exist off-design. See the module docstring.
    """
    n = len(q_sf_inc_MW)
    checks = [("q_pb", q_pb_MW), ("T_pc_in", T_pc_in_C), ("T_pc_out", T_pc_out_C),
              ("P_cycle", P_cycle_MW), ("gen", gen_kW), ("tdry", tdry_C)]
    if m_dot_pc_kg_s is not None:
        checks.append(("m_dot_pc", m_dot_pc_kg_s))
    for name, arr in checks:
        if len(arr) != n:
            raise ValueError("hourly array '%s' has length %d, expected %d" % (name, len(arr), n))

    if cp_fallback_kJ_kgK is None:
        import nanofluid_properties as nfp

        def cp_kJ_kgK(T_mean_C):
            # Clamp to the correlation's stated validity rather than extrapolating silently.
            T = min(max(T_mean_C, nfp.T_VALID_MIN_C), nfp.T_VALID_MAX_C)
            base = nfp.base_chloride_properties(T)
            return nfp.cp_nf(phi_mass, base, nfp.CUO).nominal / 1000.0
    else:
        def cp_kJ_kgK(_T_mean_C):
            return cp_fallback_kJ_kgK

    ex_solar_MWh = 0.0
    ex_htf_MWh = 0.0
    w_gross_MWh = 0.0
    ed_pb_MWh = 0.0
    negative_ed_hours = 0
    operating_hours = 0
    psi_sum = 0.0
    psi_hours = 0
    mdot_dev_pct = []

    for i in range(n):
        T0_K = tdry_C[i] + 273.15
        q_inc = q_sf_inc_MW[i]
        if q_inc > 0.0:
            psi = petela_factor(T0_K)
            ex_solar_MWh += q_inc * psi          # 1 h steps -> MW == MWh
            psi_sum += psi
            psi_hours += 1

        q_duty = q_pb_MW[i]
        if q_duty <= 0.0:
            continue
        T_hot_K = T_pc_in_C[i] + 273.15
        T_cold_K = T_pc_out_C[i] + 273.15
        if T_hot_K <= T_cold_K:
            continue                              # no usable temperature drop this hour
        operating_hours += 1
        ex_htf_MW = heat_stream_exergy_rate(q_duty, T_hot_K, T_cold_K, T0_K)
        ex_htf_MWh += ex_htf_MW
        w_gross_MWh += P_cycle_MW[i]
        ed = ex_htf_MW - P_cycle_MW[i]
        if ed < 0.0:
            negative_ed_hours += 1
        ed_pb_MWh += ed

        if m_dot_pc_kg_s is not None and m_dot_pc_kg_s[i] > 0.0:
            cp = cp_kJ_kgK(0.5 * (T_pc_in_C[i] + T_pc_out_C[i]))
            q_flow = m_dot_pc_kg_s[i] * cp * (T_pc_in_C[i] - T_pc_out_C[i]) / 1000.0
            mdot_dev_pct.append(100.0 * (q_flow - q_duty) / q_duty)

    gen_MWh = sum(gen_kW) / 1000.0
    return {
        "Ex_solar_MWh": ex_solar_MWh,
        "Ex_htf_to_cycle_MWh": ex_htf_MWh,
        "W_gross_MWh": w_gross_MWh,
        "E_net_MWh": gen_MWh,
        "Ed_power_block_MWh": ed_pb_MWh,
        "Ed_upstream_MWh": ex_solar_MWh - ex_htf_MWh,
        "eta_II_plant": (gen_MWh / ex_solar_MWh) if ex_solar_MWh > 0 else None,
        "eta_II_power_block": (w_gross_MWh / ex_htf_MWh) if ex_htf_MWh > 0 else None,
        "eta_II_collection": (ex_htf_MWh / ex_solar_MWh) if ex_solar_MWh > 0 else None,
        "petela_mean": (psi_sum / psi_hours) if psi_hours else None,
        "operating_hours": operating_hours,
        "negative_Ed_hours": negative_ed_hours,
        "parasitic_MWh": w_gross_MWh - gen_MWh,
        # Diagnostic only -- never enters the answer. See the docstring: this is the median
        # disagreement between the flow-derived duty and q_pb, which was -61 % on 2026-08-19.
        "mdot_duty_median_dev_pct": (sorted(mdot_dev_pct)[len(mdot_dev_pct) // 2]
                                     if mdot_dev_pct else None),
    }


# =============================================================================
# Self-check -- analytic cases, no PySAM
# =============================================================================
def validate(verbose: bool = True) -> bool:
    """Check the primitives against cases with known closed-form answers."""
    ok = True

    def report(label, good, detail=""):
        nonlocal ok
        ok &= bool(good)
        if verbose:
            print("  %-46s %s %s" % (label, "OK" if good else "FAIL", detail))

    # 1. Petela at T0 -> 0 must give 1 (all radiation available); at T0 = Ts must give 0.
    report("petela(T0->0) = 1", abs(petela_factor(1e-9) - 1.0) < 1e-6)
    report("petela(T0=T_sun) = 0", abs(petela_factor(T_SUN_K)) < 1e-12)
    p300 = petela_factor(300.0)
    report("petela(300 K) ~ 0.9308", abs(p300 - 0.93080) < 1e-4, "(%.5f)" % p300)
    # Petela must sit BELOW Carnot -- radiation carries entropy a reservoir does not.
    carnot = 1.0 - 300.0 / T_SUN_K
    report("petela < carnot at 300 K", p300 < carnot,
           "(%.5f < %.5f)" % (p300, carnot))

    # 2. Stream exergy vanishes when the stream is already at the dead state, and is positive
    #    for any real temperature drop above it.
    z = stream_exergy_rate(1.0, 1.0, 300.0, 300.0, 300.0)
    report("stream exergy = 0 for zero dT", abs(z) < 1e-12)
    e1 = stream_exergy_rate(2.0, 1.1, 900.0, 800.0, 300.0)
    report("stream exergy > 0 above T0", e1 > 0, "(%.3f kW)" % e1)
    # Linear in mass flow -- a scaling error in mdot would break this.
    e2 = stream_exergy_rate(4.0, 1.1, 900.0, 800.0, 300.0)
    report("stream exergy linear in mdot", abs(e2 - 2.0 * e1) < 1e-9)
    # Hotter dead state -> less available work from the same stream.
    e3 = stream_exergy_rate(2.0, 1.1, 900.0, 800.0, 320.0)
    report("stream exergy falls as T0 rises", e3 < e1, "(%.3f < %.3f)" % (e3, e1))

    # 2b. The two stream forms must be THE SAME EQUATION. This is the load-bearing test for
    #     the 2026-08-19 re-parameterisation: if they ever disagree, the annual layer and the
    #     design layer are computing different physics and the tiers cannot be compared.
    mdot_t, cp_t, Th, Tc, T0 = 3.7, 1.13, 950.0, 780.0, 301.0
    q_t = mdot_t * cp_t * (Th - Tc)
    e_flow = stream_exergy_rate(mdot_t, cp_t, Th, Tc, T0)
    e_duty = heat_stream_exergy_rate(q_t, Th, Tc, T0)
    report("duty form == mass-flow form", abs(e_flow - e_duty) < 1e-9,
           "(%.6f vs %.6f)" % (e_flow, e_duty))
    # The availability fraction must sit strictly inside (0, 1) for a real stream above T0,
    # and must collapse to the isothermal Carnot factor as the stream becomes isothermal.
    fr = carnot_lm_factor(Th, Tc, T0)
    report("0 < carnot_lm < 1", 0.0 < fr < 1.0, "(%.5f)" % fr)
    report("carnot_lm -> Carnot as dT -> 0",
           abs(carnot_lm_factor(900.0, 900.0, T0) - (1.0 - T0 / 900.0)) < 1e-12)
    report("carnot_lm continuous at dT -> 0",
           abs(carnot_lm_factor(900.0 + 1e-9, 900.0, T0)
               - carnot_lm_factor(900.0, 900.0, T0)) < 1e-6)

    # 3. Node exergy: zero at the reference by construction, and unaffected in DIFFERENCES by
    #    the choice of reference node -- the property the module docstring claims.
    h = [100.0, 200.0, 350.0] + [0.0] * 7
    s = [1.0, 1.2, 1.5] + [0.0] * 7
    a = node_exergy(h, s, 300.0, i_ref=0, n=3)
    b = node_exergy(h, s, 300.0, i_ref=1, n=3)
    report("e(reference node) = 0", abs(a[0]) < 1e-12)
    report("reference choice shifts e by a constant",
           all(abs((a[i] - a[j]) - (b[i] - b[j])) < 1e-9
               for i in range(3) for j in range(3)))
    return bool(ok)


if __name__ == "__main__":
    print("Exergy layer self-check (analytic cases, no PySAM):")
    passed = validate()
    print("\n  %s\n" % ("passed" if passed else "FAILED"))
    print("Petela factor over a realistic ambient range:")
    for t_c in (-5.0, 10.0, 25.0, 40.0, 50.0):
        print("   T0 = %6.1f C   psi = %.5f" % (t_c, petela_factor(t_c + 273.15)))
    print("\nThe spread across that range is %.4f -- small, but it is a systematic bias, not "
          "noise,\nand it moves in opposite directions at the two Objective-5 sites."
          % (petela_factor(268.15) - petela_factor(323.15)))
    sys.exit(0 if passed else 1)
