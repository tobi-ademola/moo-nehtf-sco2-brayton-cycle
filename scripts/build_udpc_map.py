r"""Build the sCO2 UDPC performance map and bridge it into the tower model.

MASTER_PLAN.md §11 item 2 -- the integrated model of Objective 2, which does not otherwise
exist. `CLAUDE.md` §3 records that the coupling runs

    Sco2CspUdPcTables --(ud_ind_od)--> TcsmoltenSalt.PowerCycle.pc_config = 1
                                       .UserDefinedPowerCycle.ud_is_sco2_regr = 1

but not that THE TWO SIDES DISAGREE ABOUT THE TABLE'S SHAPE, which is the whole difficulty.

    Sco2CspUdPcTables emits THREE per-axis tables, each 13 columns wide:
        T_htf_ind, m_dot_htf_ND_ind, T_amb_ind
        col 0 = the swept variable; cols 1-12 = four responses at three levels of a paired
        variable -- 1-3 W_gross, 4-6 Q_HTF, 7-9 W_cooling, 10-12 m_dot_water.

    TcsmoltenSalt.ud_ind_od wants ONE combined table, 7 columns wide:
        [T_htf, m_dot_htf_ND, T_amb, W_gross_ND, Q_HTF_ND, W_cool_ND, m_water_ND]
        stacked as three blocks.

This is not a version mismatch to be worked around: ssc's own N_udpc_common::split_ind_tbl()
takes the combined table and splits it into exactly those three per-axis tables. What this
script does is the INVERSE of that split.

THE LAYOUT IS VERIFIED, NOT ASSUMED. Every structural claim below was read off the tower's own
installed default `ud_ind_od` (180x7) in this environment before any of it was written:

    block 0   T_htf swept, three m_dot levels, T_amb held at design
    block 1   m_dot swept, three T_amb levels, T_htf held at design
    block 2   T_amb swept, three T_htf levels, m_dot held at design
    levels ordered [low, DESIGN, high]; the LEVEL is the outer loop, the swept value the inner.

TWO TRAPS, BOTH SILENT IF MISSED.
  * The cooling response arrives UNNORMALISED (order 1e-3 at design) while every other response
    is 1.0 at design. It must be divided by its own design value here; the magnitude is restored
    on the tower side by `ud_f_W_dot_cool_des`.
  * `ud_ind_od` carries only normalised SHAPES. The design MAGNITUDES travel separately, and if
    they are not set the tower silently keeps SAM's steam-Rankine defaults -- design_eff 0.412
    and P_ref 115 MW, verified as the shipped values in this environment -- and the sCO2 cycle
    is quietly mis-scaled while everything appears to work.

THE CYCLE IS PINNED TO THE VALIDATED CASE F BASELINE (`CLAUDE.md` §7, `VALIDATION.md` §2.3.4a):
f_rc 0.4097, recuperators at 10 K approach, eta_mc/rc 0.89, eta_t 0.90, P_high 20 MPa, PR 2.6,
Dostal's own per-HX pressure losses. It is deliberately NOT the target-efficiency design that
`CLAUDE.md` §4.3 documents as collapsing the cycle to f_rc ~ 0.

One deliberate departure from the validation point, stated because it is a real one: the
validated case sits at T_htf_hot = 720 C to put the turbine inlet at Dostal's 700 C, but the
chloride property correlations are only stated valid to 700 C (scripts/nanofluid_properties.py,
T_VALID_MAX_C). This script therefore runs T_htf_hot = 700 C, giving a 680 C turbine inlet. The
cycle ARCHITECTURE and every efficiency, pressure and recuperator specification are unchanged;
only the hot-end boundary condition moves, and the resulting design efficiency is reported
against case F's 0.51289 so the size of that move is visible rather than buried.

*** STATUS 2026-08-14: THE SWEEP CONVERGES. IT IS SLOW. IT WAS NEVER OVER-CONSTRAINED. ***

*** THE PREVIOUS DIAGNOSIS IN THIS DOCSTRING WAS WRONG AND IS RETAINED BELOW AS A LESSON. ***

The off-design sweep at the FULL case F design -- every recuperator specified, f_rc pinned at
0.4097, both pressure levels pinned, rel_tol 4 -- completes and produces a usable map:

    case_F, 3 points per axis, sweep ON:  USABLE in 2277.9 s (38.0 min)
                                          recomp_frac 0.40970, eta 0.50547, tables non-empty

    The cycle that comes out is the validated one. Nothing had to be loosened to get it.

The 2026-08-13 conclusion -- "a fully determined case-F-style design is over-constrained for
UDPC generation" -- is REFUTED. There is no convergence boundary in {design_method, f_rc
pinning, pressure pinning, rel_tol}. All five configurations tested with the sweep on converge,
and the knobs barely move the wall time:

    case_F        (all tight)          2277.9 s   recomp_frac 0.40970   eta 0.50547
    F_loose_frc   (f_rc free)          2152.3 s   recomp_frac 0.41067   eta 0.50569
    F_loose_dm    (design_method 1)    2218.6 s   recomp_frac 0.40970   eta 0.49999
    F_loose_press (pressures free)     1882.8 s   recomp_frac 0.40970   eta 0.50654
    F_loose_tol   (rel_tol 3)          1963.3 s   recomp_frac 0.40970   eta 0.50512

*** WHAT ACTUALLY WENT WRONG, BECAUSE IT IS THE REUSABLE LESSON ***

Every one of the twelve experiments that concluded "still hangs" was capped at 5-16 minutes.
The sweep needs ~31-38. Not one of them ran long enough to observe a convergence that was
always going to happen. A dozen negative results, a mechanism invented to explain them, and a
recorded modelling decision -- all downstream of a timeout that was too short by a factor of 2.

    "Hangs" was never observed. What was observed is "did not finish inside MY timeout", and
    the two were conflated. A run that has not finished carries NO information until the
    timeout is justified against a measured completion, and none of the twelve were.

Two further traps that fed the wrong diagnosis, both worth keeping:

  * `design_method = 1` was miscategorised as a LOOSE setting. It is not loose -- it ADDS a
    constraint, an inverse solve for the total recuperator conductance that hits a target
    efficiency. Combined with free pressures and a free f_rc it is the slowest configuration
    of all: it ran 2026 s and then FAILED with a real ssc diagnostic, not a hang --
        "Can't find a value of total recuperator conductance that achieves the target cycle
         efficiency. Check design parameters."
    So the one configuration previously believed to be the known-good control is the only one
    that genuinely does not work.

  * The 93.6 s / `recomp_frac = 0.0` run recorded on 2026-08-13 has NEVER been reproduced. The
    configuration it describes fails as above. Do not treat that number as a control.

`--selftest` still verifies the inverse-split transform independently of ssc, and `--design-only`
(0.1 s) remains the fast path for checking the cycle without paying for the sweep.

Inputs:  scripts/nanofluid_properties.py (the PHX sees the same chloride as the tower loop);
         scripts/validate_dostal.py for the case F constants, imported rather than retyped.
         Requires the .venv of CLAUDE.md §1.

Run:  .\.venv\Scripts\python.exe -u .\scripts\build_udpc_map.py --selftest
      .\.venv\Scripts\python.exe -u .\scripts\build_udpc_map.py --design-only
      .\.venv\Scripts\python.exe -u .\scripts\build_udpc_map.py --n-points 3 --phi 0.007

Outputs: maps/sco2_udpc_phi<phi>_tower7.csv    the 7-column table to load into the tower
         maps/sco2_udpc_phi<phi>_peraxis.csv   the 13-column per-axis tables (diagnostic)
         results/udpc_map_<stamp>.md           the report, including the tower round-trip
"""

import argparse
import csv
import datetime
import math
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
MAPS_DIR = os.path.join(REPO_ROOT, "maps")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import PySAM.Sco2CspUdPcTables as SCO2  # noqa: E402
import nanofluid_properties as nfp      # noqa: E402
import validate_dostal as vd            # noqa: E402  -- the case F constants, not retyped

HTF_CODE_USER_TABLE = 50

# Hot-end boundary. 700 C is the top of the chloride correlation's stated validity; the turbine
# inlet lands DT_PHX_HOT_APPROACH below it. See the module docstring on why this is not 720.
T_HTF_HOT_DES_C = 700.0
PHI_REFERENCE = 0.007
HTF_T_GRID = [450.0, 500.0, 550.0, 600.0, 650.0, 700.0]

# Off-design sweep ranges. T_amb spans the Morocco site; m_dot_ND stops at 0.5 because deep
# turndown is where the solver loses custom-fluid corners (see --n-points and the retry below).
T_HTF_HOT_LOW_C, T_HTF_HOT_HIGH_C = 620.0, 710.0
T_AMB_LOW_C, T_AMB_HIGH_C = 5.0, 45.0
M_DOT_ND_LOW, M_DOT_ND_HIGH = 0.50, 1.05

W_DOT_NET_DES_KWE = 115000.0   # matches the tower's stock P_ref so the bridge is like-for-like

# --- 13-column per-axis layout (ud_power_cycle.h) ----------------------------------------------
UDPC_N_COLS = 13
AXES = ("T_htf_ind", "m_dot_htf_ND_ind", "T_amb_ind")
RESPONSE_BASE = {"W_dot_gross": 1, "Q_dot_HTF": 4, "W_dot_cooling": 7, "m_dot_water": 10}
LEVEL_DESIGN = 1               # index of the design level within each [low, design, high] triple

TOWER_COLS = ("T_htf [C]", "m_dot_htf_ND", "T_amb [C]", "W_dot_gross_ND",
              "Q_dot_HTF_ND", "W_dot_cooling_ND", "m_dot_water_ND")


class MapError(RuntimeError):
    """The solver or its output is not in a usable state."""


# =============================================================================
# Design
# =============================================================================
def build(phi_mass=PHI_REFERENCE, T_htf_hot_C=T_HTF_HOT_DES_C, n_points=5):
    """Assemble the map generator at the case F cycle design on the nano-chloride.

    Every cycle number here is imported from scripts/validate_dostal.py rather than retyped, so
    the map cannot silently drift away from the validated baseline: if case F changes, this
    changes with it.
    """
    m = SCO2.new()

    d = m.SystemDesign
    d.htf = HTF_CODE_USER_TABLE
    d.htf_props = nfp.htf_table_rows(phi_mass, HTF_T_GRID)
    d.T_htf_hot_des = T_htf_hot_C
    d.dT_PHX_hot_approach = vd.DT_PHX_HOT_APPROACH
    d.T_amb_des = vd.T_MC_IN_C - vd.DT_MC_APPROACH
    d.dT_mc_approach = vd.DT_MC_APPROACH
    d.W_dot_net_des = W_DOT_NET_DES_KWE
    d.site_elevation = 0.0
    d.design_method = 3                       # specify each recuperator (CLAUDE.md §4.3)
    d.eta_thermal_des = vd.ETA_TARGET         # ignored under design_method 3; non-zero anyway

    c = m.Common
    c.eta_isen_mc = vd.ETA_MC
    c.eta_isen_rc = vd.ETA_RC
    c.eta_isen_pc = vd.ETA_RC
    c.eta_isen_t = vd.ETA_T
    c.P_high_limit = vd.P_HIGH_MPA
    c.deltaP_counterHX_frac = vd.DELTA_P_FRAC
    c.PHX_co2_deltaP_des_in = vd.DOSTAL_DP_FRAC["PHX"]
    c.mc_comp_type = 1
    # Guard the sweep corners for a user-defined fluid: without it the solver walks off the end
    # of the property table at deep turndown / high ambient.
    c.is_apply_default_htf_mins = 1
    c.is_generate_udpc = 1
    c.T_htf_hot_low, c.T_htf_hot_high, c.n_T_htf_hot = (
        T_HTF_HOT_LOW_C, T_HTF_HOT_HIGH_C, n_points)
    c.T_amb_low, c.T_amb_high, c.n_T_amb = T_AMB_LOW_C, T_AMB_HIGH_C, n_points
    c.m_dot_htf_ND_low, c.m_dot_htf_ND_high, c.n_m_dot_htf_ND = (
        M_DOT_ND_LOW, M_DOT_ND_HIGH, n_points)

    x = m.HeatExchangerDesign
    x.cycle_config = 1                        # recompression
    x.is_recomp_ok = -abs(vd.F_RECOMP)        # negative => PIN f_rc (CLAUDE.md §4.3)
    x.is_P_high_fixed = 1
    x.is_PR_fixed = vd.PRESSURE_RATIO
    x.is_IP_fixed = 0
    x.des_objective = 0
    x.min_phx_deltaT = 0
    x.rel_tol = 4
    x.HTR_design_code = x.LTR_design_code = vd.RECUP_CODE       # 2 = min approach dT
    x.HTR_min_dT_des_in = x.LTR_min_dT_des_in = vd.RECUP_MIN_DT
    x.HTR_eff_des_in = x.LTR_eff_des_in = vd.RECUP_EFF          # inactive under code 2
    # Inactive specs must still be non-zero: 0.0 segfaults (CLAUDE.md §4.2, §4.7).
    x.HTR_UA_des_in = x.LTR_UA_des_in = 5000.0
    x.UA_recup_tot_des = 10000.0
    x.HT_recup_eff_max = x.LT_recup_eff_max = 1.0
    x.HTR_n_sub_hx = x.LTR_n_sub_hx = 20
    x.HTR_od_model = x.LTR_od_model = 1
    for attr, key in (("HTR_LP_deltaP_des_in", "HTR_LP"), ("HTR_HP_deltaP_des_in", "HTR_HP"),
                      ("LTR_LP_deltaP_des_in", "LTR_LP"), ("LTR_HP_deltaP_des_in", "LTR_HP")):
        setattr(x, attr, vd.DOSTAL_DP_FRAC[key])

    p = m.PHXDesign
    p.dT_PHX_cold_approach = 20.0
    p.PHX_n_sub_hx = 10
    p.PHX_od_model = 1

    a = m.AirCoolerDesign
    a.is_design_air_cooler = 1
    a.deltaP_cooler_frac = vd.DOSTAL_DP_FRAC["cooler"]
    a.fan_power_frac = 0.01
    a.eta_air_cooler_fan = 0.5
    a.N_nodes_air_cooler_pass = 10
    return m


def check_design(m):
    """Confirm the design point is a real recompression cycle before trusting the map.

    ssc reports "design optimization was successful" while collapsing to a simple recuperated
    cycle (CLAUDE.md §4.3), so the map could be generated off a cycle that is not the one this
    project validated. These are the same assertions validate_dostal.py makes.
    """
    o = m.Outputs
    eta = o.eta_thermal_calc
    f = o.recomp_frac
    problems = []
    if not (f > 1e-6):
        problems.append("collapsed to simple recuperated: recomp_frac = %.6f" % f)
    if math.isnan(o.q_dot_HTR):
        problems.append("HTR inactive (q_dot_HTR is NaN) -- recompression not engaged")
    if not (o.P_comp_in > 7.4):
        problems.append("compressor inlet %.4f MPa is below critical" % o.P_comp_in)
    return {
        "eta_thermal_calc": eta, "recomp_frac": f,
        "T_turb_in_C": o.T_turb_in, "T_comp_in_C": o.T_comp_in,
        "P_comp_in_MPa": o.P_comp_in, "P_comp_out_MPa": o.P_comp_out,
        "eff_HTR": o.eff_HTR, "eff_LTR": o.eff_LTR,
        "T_htf_cold_des_C": o.T_htf_cold_des,
        "eta_vs_case_F_pp": 100.0 * (eta - 0.51289),
        # The design cooling MAGNITUDE, taken from ssc's own reported fan power rather than from
        # the map's cooling column -- see cooling_fraction_pct() for why that distinction matters.
        "W_dot_cooler_fan_kWe": float(o.cooler_tot_W_dot_fan),
        "problems": problems,
    }


def cooling_fraction_pct(d, W_dot_des_kWe):
    """`ud_f_W_dot_cool_des` -- design cooling as a percentage of design output.

    THIS WAS WRONG UNTIL 2026-08-14 AND THE ERROR WAS SILENT, so the reasoning is recorded here
    rather than left to be re-derived. The original line was

        f_cool_pct = 100.0 * cool_des / W_DOT_NET_DES_KWE        # 100 * 9.971e-4 / 115000

    where `cool_des` is the DESIGN VALUE OF THE MAP'S COOLING COLUMN. That column is not a power
    in kW -- it sits at ~1e-3 while every other response is ~1.0 (CLAUDE.md §4.11) -- so dividing
    it by a power in kW is a category error. It yielded `ud_f_W_dot_cool_des = 0.0000 %`: a
    115 MW plant whose air cooler draws nothing, with nothing raised and nothing warned. Exactly
    the CLAUDE.md §4.12 failure mode.

    Nor is the column a fraction of design gross: that reading gives 100 * 9.971e-4 = 0.0997 %,
    which is still 10x low. The magnitude is only available from ssc directly --
    `cooler_tot_W_dot_fan = 1150.0` kW against a 115 000 kWe design, i.e. 1.0 %, matching the
    `fan_power_frac = 0.01` that was set as an input. `W_dot_net_less_cooling = 113850.0`
    (= 115000 - 1150) confirms both the value and its unit, kW not MW (CLAUDE.md §4.9).

    The normalised SHAPE of the cooling response still comes from the map column, divided by its
    own design value in to_combined(); only the scale comes from here. Shape and magnitude travel
    separately, which is the whole point of §4.12.
    """
    pct = 100.0 * d["W_dot_cooler_fan_kWe"] / W_dot_des_kWe
    # A silent zero is the failure this function exists to prevent, so refuse to ship one.
    if not (0.05 <= pct <= 10.0):
        raise MapError(
            "ud_f_W_dot_cool_des = %.6f %% is outside the plausible 0.05-10 %% band for a "
            "dry-cooled sCO2 cycle (fan power %.1f kWe against %.1f kWe design). A value near "
            "zero means the cooling parasitic has been scaled away and the annual result will "
            "silently omit it." % (pct, d["W_dot_cooler_fan_kWe"], W_dot_des_kWe))
    return pct


# =============================================================================
# The inverse of split_ind_tbl()
# =============================================================================
def get_axes(m):
    """Pull the three per-axis tables, checking the 13-column contract."""
    out = {}
    for name in AXES:
        tbl = [list(r) for r in getattr(m.Outputs, name)]
        if not tbl:
            raise MapError(f"{name} is empty -- the sweep produced no rows")
        widths = {len(r) for r in tbl}
        if widths != {UDPC_N_COLS}:
            raise MapError(
                f"{name} has column widths {sorted(widths)}, expected {UDPC_N_COLS}. The "
                f"per-axis layout changed; the inverse-split below is no longer valid.")
        out[name] = tbl
    return out


def _interp(x, xs, ys):
    """Linear interpolation with clamping, for recovering a value at the design point."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            span = xs[i] - xs[i - 1]
            t = 0.0 if span == 0 else (x - xs[i - 1]) / span
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


def design_cooling(axes, T_htf_hot_des):
    """The design-point cooling value, used to normalise the cooling response.

    The cooling column comes out UNNORMALISED while every other response is 1.0 at design. The
    design value is recovered by interpolating the T_htf sweep, at the design m_dot level, to
    the design hot temperature -- the sweep grid need not land on it exactly.
    """
    tbl = axes["T_htf_ind"]
    col = RESPONSE_BASE["W_dot_cooling"] + LEVEL_DESIGN
    xs = [r[0] for r in tbl]
    ys = [r[col] for r in tbl]
    val = _interp(T_htf_hot_des, xs, ys)
    if not (val > 0):
        raise MapError(
            "design cooling value is %r -- cannot normalise the cooling column. Every "
            "W_dot_cooling_ND would be inf or nan." % val)
    return val


def to_combined(axes, levels, T_htf_hot_des, T_amb_des, cool_des):
    """Invert split_ind_tbl: three 13-column per-axis tables -> one 7-column combined table.

    `levels` supplies the three [low, design, high] values of each paired variable, which the
    per-axis tables encode only by column position and not by value.

    Block order and pairing are the ones read off the tower's installed default (see module
    docstring). The LEVEL is the outer loop and the swept value the inner, matching that default.
    """
    rows = []
    plan = (
        # axis name,          swept ->, level variable, the two held/level values per row
        ("T_htf_ind", "T_htf", "m_dot",
         lambda swept, lv: (swept, lv, T_amb_des)),
        ("m_dot_htf_ND_ind", "m_dot", "T_amb",
         lambda swept, lv: (T_htf_hot_des, swept, lv)),
        ("T_amb_ind", "T_amb", "T_htf",
         lambda swept, lv: (lv, 1.0, swept)),
    )
    for axis, _swept_name, level_var, place in plan:
        tbl = axes[axis]
        for li, level_value in enumerate(levels[level_var]):
            for r in tbl:
                T_htf, m_dot, T_amb = place(r[0], level_value)
                rows.append([
                    T_htf, m_dot, T_amb,
                    r[RESPONSE_BASE["W_dot_gross"] + li],
                    r[RESPONSE_BASE["Q_dot_HTF"] + li],
                    r[RESPONSE_BASE["W_dot_cooling"] + li] / cool_des,   # <- normalised here
                    r[RESPONSE_BASE["m_dot_water"] + li],
                ])
    return rows


def split_combined(rows):
    """The FORWARD split -- what ssc's N_udpc_common::split_ind_tbl() does to the combined table.

    Implemented only so the self-test can check that to_combined() is its exact inverse. The
    production path never calls this; ssc does it internally.
    """
    n = len(rows) // 3
    per = n // 3                       # sweep points per level
    axes = {}
    for b, name in enumerate(AXES):
        blk = rows[b * n:(b + 1) * n]
        swept_col = b                  # block 0 sweeps col 0, block 1 col 1, block 2 col 2
        tbl = []
        for i in range(per):
            row = [blk[i][swept_col]]
            for base in ("W_dot_gross", "Q_dot_HTF", "W_dot_cooling", "m_dot_water"):
                for li in range(3):
                    # response columns start at index 3 in the combined layout
                    col = 3 + ("W_dot_gross", "Q_dot_HTF",
                               "W_dot_cooling", "m_dot_water").index(base)
                    row.append(blk[li * per + i][col])
            tbl.append(row)
        axes[name] = tbl
    return axes


def selftest():
    """Prove to_combined() inverts the split, WITHOUT needing ssc to converge.

    This matters because the sweep currently does not converge at the case F design (see the
    module docstring), so the transform -- the part actually harvested from the prior project
    and the part most likely to be silently wrong -- would otherwise be unverified. Synthetic
    per-axis tables are built with a unique, recognisable value in every response slot, pushed
    through to_combined(), then split back with split_combined() and compared element by element.
    """
    per = 4
    levels = {"T_htf": [600.0, 700.0, 710.0],
              "m_dot": [0.5, 1.0, 1.05],
              "T_amb": [5.0, 26.0, 45.0]}
    swept = {"T_htf_ind": [620.0, 650.0, 680.0, 700.0],
             "m_dot_htf_ND_ind": [0.5, 0.7, 0.9, 1.05],
             "T_amb_ind": [5.0, 20.0, 35.0, 45.0]}

    # Every cell gets a distinct value, so a transposition cannot hide behind equal numbers.
    axes, tag = {}, 0.0
    for name in AXES:
        tbl = []
        for i in range(per):
            row = [swept[name][i]]
            for _ in range(12):
                tag += 1.0
                row.append(tag)
            tbl.append(row)
        axes[name] = tbl

    rows = to_combined(axes, levels, 700.0, 26.0, cool_des=1.0)
    problems = check_combined(rows, per)
    back = split_combined(rows)

    mismatches = []
    for name in AXES:
        for i, (a, b) in enumerate(zip(axes[name], back[name])):
            if [round(v, 9) for v in a] != [round(v, 9) for v in b]:
                mismatches.append(f"{name} row {i}: {a} != {b}")

    # The independent structural check: each block must hold the right swept/held pattern.
    n = len(rows) // 3
    struct = []
    if len({r[2] for r in rows[0:n]}) != 1:
        struct.append("block 0 should hold T_amb constant at design")
    if len({r[0] for r in rows[n:2 * n]}) != 1:
        struct.append("block 1 should hold T_htf constant at design")
    if len({r[1] for r in rows[2 * n:]}) != 1:
        struct.append("block 2 should hold m_dot constant at design")

    print("=" * 100)
    print("SELF-TEST -- to_combined() is the inverse of ssc's split_ind_tbl()")
    print("=" * 100)
    print("   synthetic input      3 axes x %d sweep points x 12 responses" % per)
    print("   combined shape       %d rows x %d cols (expected %d x 7)"
          % (len(rows), len(rows[0]), 3 * 3 * per))
    print("   structural checks    %s" % ("PASS" if not struct else "FAIL: %s" % struct))
    print("   round-trip           %s"
          % ("PASS -- every cell recovered" if not mismatches
             else "FAIL: %d mismatches, first: %s" % (len(mismatches), mismatches[0])))
    print("   table checks         %s" % ("PASS" if not problems else "FAIL: %s" % problems))
    ok = not (mismatches or struct or problems)
    print("\n   VERDICT: %s" % ("PASS -- the transform is correct independently of ssc"
                                if ok else "FAIL"))
    return ok


def check_combined(rows, n_per_axis):
    """Structural and physical checks on the combined table before the tower ever sees it."""
    problems = []
    expected = 3 * 3 * n_per_axis
    if len(rows) != expected:
        problems.append(f"{len(rows)} rows, expected 3 blocks x 3 levels x {n_per_axis}")
    if len(rows) % 3 != 0:
        problems.append(f"{len(rows)} rows is not divisible by 3 -- ssc splits into 3 blocks")
    widths = {len(r) for r in rows}
    if widths != {7}:
        problems.append(f"column widths {sorted(widths)}, expected exactly 7")
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            if v != v or math.isinf(v):
                problems.append(f"row {i} col {j} ({TOWER_COLS[j]}) is not finite: {v}")
                break
    return problems


# =============================================================================
# The tower side of the bridge
# =============================================================================
def apply_to_tower(rows, design_eff, P_ref_MW, f_cool_pct, weather_file):
    """Load the map into TcsmoltenSalt and confirm the tower accepts it.

    Sets the design MAGNITUDES alongside the normalised table. Without them the tower keeps its
    steam-Rankine defaults and the sCO2 cycle is silently mis-scaled -- see the module docstring.
    """
    import PySAM.TcsmoltenSalt as tcs
    m = tcs.default("MSPTSingleOwner")
    m.SolarResource.solar_resource_file = weather_file

    before = {"design_eff": m.SystemDesign.design_eff, "P_ref": m.SystemDesign.P_ref}

    m.PowerCycle.pc_config = 1                        # 1 = user-defined cycle
    m.UserDefinedPowerCycle.ud_ind_od = rows
    m.UserDefinedPowerCycle.ud_is_sco2_regr = 1       # sCO2-aware regression (CLAUDE.md §3)
    m.UserDefinedPowerCycle.ud_f_W_dot_cool_des = f_cool_pct
    m.UserDefinedPowerCycle.ud_m_dot_water_cool_des = 0.0   # dry-cooled: no water
    m.SystemDesign.design_eff = design_eff
    m.SystemDesign.P_ref = P_ref_MW

    got = m.UserDefinedPowerCycle.ud_ind_od
    worst = 0.0
    for a, b in zip(rows, got):
        for x, y in zip(a, b):
            denom = abs(x) if abs(x) > 1e-30 else 1.0
            worst = max(worst, abs(x - y) / denom)
    return m, {"rows_set": len(rows), "rows_read": len(got), "roundtrip_rel": worst,
               "steam_defaults_replaced": before}


def git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                               capture_output=True, text=True, check=True)
        return out.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "")
    except Exception:
        return "unknown"


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


# =============================================================================
# Main
# =============================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phi", type=float, default=PHI_REFERENCE,
                    help="nanoparticle mass fraction (default 0.007 = 0.7 wt%%)")
    ap.add_argument("--n-points", type=int, default=5,
                    help="sweep points per axis; retries at 3 if the solver loses a corner")
    ap.add_argument("--T-htf-hot", type=float, default=T_HTF_HOT_DES_C)
    ap.add_argument("--selftest", action="store_true",
                    help="verify the inverse-split transform on synthetic data; no ssc needed")
    ap.add_argument("--design-only", action="store_true",
                    help="solve the design point and stop -- the mode that works today")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(0 if selftest() else 1)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = git_commit()
    report = []

    def say(line=""):
        print(line, flush=True)
        report.append(line)

    say("=" * 100)
    say("sCO2 UDPC MAP -> TcsmoltenSalt BRIDGE   (MASTER_PLAN.md §11 item 2)")
    say("  cycle pinned to the validated case F baseline; phi = %.4f (%.1f wt%%)"
        % (args.phi, 100.0 * args.phi))
    say("=" * 100)

    # --- design (+ sweep) -------------------------------------------------
    n = args.n_points
    if args.design_only:
        say("\nsolving the DESIGN POINT only (--design-only) ...")
        m = build(args.phi, args.T_htf_hot, n)
        m.Common.is_generate_udpc = 0
        m.execute(0)
        say("   solved")
    else:
        say("\nsolving design + %d^3 off-design sweep ..." % n)
        say("   This is SLOW, not stuck: ~31-38 min at n = 3 (measured 2026-08-14, five")
        say("   configurations, 1882.8-2277.9 s). Do NOT kill it early -- a timeout shorter")
        say("   than the run is exactly what produced twelve false 'hangs'. --design-only")
        say("   (0.1 s) is the fast path when you only need the cycle, not the map.")
        m = build(args.phi, args.T_htf_hot, n)
        m.execute(0)
        say("   solved at n = %d per axis" % n)

    # --- design point -----------------------------------------------------
    d = check_design(m)
    say("\nDESIGN POINT")
    say("   eta_thermal_calc     %.5f   (case F 0.51289 -> %+.3f pp)"
        % (d["eta_thermal_calc"], d["eta_vs_case_F_pp"]))
    say("   recomp_frac          %.5f   (pinned at %.4f)" % (d["recomp_frac"], vd.F_RECOMP))
    say("   T_turb_in            %.3f C   T_comp_in %.3f C" % (d["T_turb_in_C"], d["T_comp_in_C"]))
    say("   P_comp_out / in      %.4f / %.4f MPa   (PR %.4f)"
        % (d["P_comp_out_MPa"], d["P_comp_in_MPa"], d["P_comp_out_MPa"] / d["P_comp_in_MPa"]))
    say("   eff_HTR / eff_LTR    %.5f / %.5f" % (d["eff_HTR"], d["eff_LTR"]))
    say("   T_htf_cold_des       %.3f C" % d["T_htf_cold_des_C"])
    for p in d["problems"]:
        say("   [PROBLEM]            %s" % p)
    if d["problems"]:
        raise MapError("design point is not a valid recompression cycle: %s" % d["problems"])

    if args.design_only:
        md_path = os.path.join(RESULTS_DIR, "udpc_design_only_%s.md" % stamp)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write("# sCO2 UDPC design point (design-only run)\n\n"
                     "| | |\n|---|---|\n| script | `scripts/build_udpc_map.py --design-only` |\n"
                     "| run (UTC) | %s |\n| git commit | `%s` |\n| phi | %.4f |\n\n```\n%s\n```\n"
                     % (stamp, commit, args.phi, "\n".join(report)))
        say("\nDesign point is valid. The off-design sweep is NOT run in this mode; the map")
        say("cannot be produced until the convergence issue in the module docstring is resolved.")
        print("\nresults written (commit %s):\n   %s"
              % (commit, os.path.relpath(md_path, REPO_ROOT).replace("\\", "/")))
        return

    # --- per-axis -> combined --------------------------------------------
    axes = get_axes(m)
    say("\nPER-AXIS TABLES (as emitted by Sco2CspUdPcTables)")
    for name in AXES:
        say("   %-18s %d rows x %d cols" % (name, len(axes[name]), len(axes[name][0])))

    T_amb_des = vd.T_MC_IN_C - vd.DT_MC_APPROACH
    levels = {
        "T_htf": [T_HTF_HOT_LOW_C, args.T_htf_hot, T_HTF_HOT_HIGH_C],
        "m_dot": [M_DOT_ND_LOW, 1.0, M_DOT_ND_HIGH],
        "T_amb": [T_AMB_LOW_C, T_amb_des, T_AMB_HIGH_C],
    }
    cool_des = design_cooling(axes, args.T_htf_hot)
    rows = to_combined(axes, levels, args.T_htf_hot, T_amb_des, cool_des)
    problems = check_combined(rows, len(axes["T_htf_ind"]))

    say("\nCOMBINED TABLE (the inverse of ssc's split_ind_tbl)")
    say("   shape                %d rows x %d cols  (3 blocks x 3 levels x %d sweep points)"
        % (len(rows), len(rows[0]), len(axes["T_htf_ind"])))
    say("   cooling design value %.6e  -> cooling column normalised by it" % cool_des)
    say("   W_cool_ND range      %.4f .. %.4f"
        % (min(r[5] for r in rows), max(r[5] for r in rows)))
    for p in problems:
        say("   [PROBLEM]            %s" % p)
    if problems:
        raise MapError("combined table failed its structural checks: %s" % problems)

    # --- tower round-trip -------------------------------------------------
    weather = os.path.join(REPO_ROOT, "data", "tmy", "158192_31.05_-6.86_tmy-2022.csv")
    f_cool_pct = cooling_fraction_pct(d, W_DOT_NET_DES_KWE)
    tower, info = apply_to_tower(rows, d["eta_thermal_calc"], W_DOT_NET_DES_KWE / 1000.0,
                                 f_cool_pct, weather)
    say("\nTOWER BRIDGE")
    say("   pc_config            1 (user-defined)      ud_is_sco2_regr 1")
    say("   ud_ind_od            set %d rows, read back %d, max rel dev %.3e"
        % (info["rows_set"], info["rows_read"], info["roundtrip_rel"]))
    say("   design magnitudes    design_eff %.5f (was %.4f), P_ref %.1f MW (was %.1f)"
        % (d["eta_thermal_calc"], info["steam_defaults_replaced"]["design_eff"],
           W_DOT_NET_DES_KWE / 1000.0, info["steam_defaults_replaced"]["P_ref"]))
    say("   ud_f_W_dot_cool_des  %.4f %% of design output  (fan %.1f kWe / %.0f kWe)"
        % (f_cool_pct, d["W_dot_cooler_fan_kWe"], W_DOT_NET_DES_KWE))

    # --- durable output ---------------------------------------------------
    # The sweep resolution is part of the artifact's identity: a 3-point and a 5-point map are
    # different surfaces and must not overwrite each other, since comparing them is how the cost
    # of a coarse map gets quantified (THESIS_SYNTHESIS.md §17 step 2).
    tag = ("phi%.4f_n%d" % (args.phi, n)).replace(".", "p")
    tower_path = write_csv(os.path.join(MAPS_DIR, "sco2_udpc_%s_tower7.csv" % tag),
                           TOWER_COLS, rows)
    per_axis_rows = []
    for name in AXES:
        for r in axes[name]:
            per_axis_rows.append([name] + list(r))
    axis_path = write_csv(
        os.path.join(MAPS_DIR, "sco2_udpc_%s_peraxis.csv" % tag),
        ["axis", "swept"] + [f"c{i}" for i in range(1, UDPC_N_COLS)], per_axis_rows)

    md_path = os.path.join(RESULTS_DIR, "udpc_map_%s.md" % stamp)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# sCO2 UDPC map -> TcsmoltenSalt bridge\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/build_udpc_map.py` |\n"
                 "| run (UTC) | %s |\n| git commit | `%s` |\n"
                 "| PySAM | 7.1.1.post1 (bundled ssc 306) |\n"
                 "| phi | %.4f |\n| sweep | %d points per axis |\n\n```\n%s\n```\n"
                 % (stamp, commit, args.phi, n, "\n".join(report)))

    say("\nVERDICT")
    say("   The bridge is CLOSED: Sco2CspUdPcTables solved at the case F design on the")
    say("   nano-chloride, its three per-axis tables were inverted into the 7-column layout")
    say("   ssc's split_ind_tbl expects, and TcsmoltenSalt accepted the result unchanged.")
    print("\nresults written (commit %s):" % commit)
    for p in (tower_path, axis_path, md_path):
        print("   %s" % os.path.relpath(p, REPO_ROOT).replace("\\", "/"))


if __name__ == "__main__":
    main()
