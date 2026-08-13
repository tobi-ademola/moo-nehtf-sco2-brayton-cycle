"""
sCO2 recompression cycle performance-map generator
===================================================

Generates the User-Defined Power Cycle (UDPC) performance map that SAM's
TcsmoltenSalt model interpolates during its 8760-hour annual run, so the sCO2
cycle need not be re-solved every timestep.

This is the OFFLINE leg of the architecture (see the SAM-based diagram): a map
is generated ahead of the optimiser run and then held constant across the
candidates it covers. The CYCLE DESIGN parameters below are frozen into the
study -- layout, pressure limit, isentropic efficiencies, recuperator UA are
NOT optimiser decision variables.

The NANOPARTICLE LOADING is a different matter and is deliberately NOT frozen
here. phi is the study's central decision variable, so it is an argument to
`generate_map()`, not a module constant. It reaches the cycle only through the
PHX (HTF-side cp/rho/k/mu set the capacity-rate profile and the pinch), which
is expected to be a weak channel compared with phi's effect on pumping power
and storage inventory -- but "expected" is not "measured". Two supported ways
to settle it, both cheap because they run offline:

  * SENSITIVITY: generate maps at the phi extremes (0 and 0.02, Han's maximum
    tested loading) and diff the normalised responses. If they agree, a single
    map becomes a *tested* assumption you can defend in the methodology rather
    than a silent one.
        python sco2_cycle_map.py --phi 0 0.02
  * MAP FAMILY: generate a grid of maps offline and interpolate between them
    inside the optimiser loop, keeping phi live end-to-end.
        python sco2_cycle_map.py --phi 0 0.002 0.007 0.014 0.02

Verified against PySAM 7.1.1 module `Sco2CspUdPcTables`.

MAP LAYOUT -- RECONCILED (see CLAUDE.md section 7 for the full write-up).

The solver returns three per-axis tables (`T_htf_ind`, `m_dot_htf_ND_ind`,
`T_amb_ind`), each 13 columns wide: column 0 is the swept independent variable
and columns 1-12 hold four responses at three levels of a paired variable
(1-3 W_gross, 4-6 Q_HTF, 7-9 W_cooling, 10-12 m_dot_water; levels ordered
[low, DESIGN, high]).

The tower's `TcsmoltenSalt.UserDefinedPowerCycle.ud_ind_od` wants a 7-column
COMBINED table instead: [T_htf, m_dot_htf_ND, T_amb, W_gross_ND, Q_HTF_ND,
W_cooling_ND, m_dot_water_ND]. This is NOT a SAM-version difference -- SSC's
`N_udpc_common::split_ind_tbl()` takes the combined table and splits it into
exactly the three per-axis tables above. `to_tower_ud_ind_od()` is the inverse
of that split, and each run writes BOTH files:

    maps/sco2_udpc_phi_<phi>.csv          13-col per-axis (diagnostic/sensitivity)
    maps/sco2_udpc_phi_<phi>_tower7.csv   7-col combined  (load into the tower)

Two things the conversion must get right, both silent if wrong:
  * the cooling column arrives UNNORMALISED (~1e-3 at design) while every other
    response is 1.0 at design -- it is divided by its own design value here, and
    the magnitude is restored by the tower's `ud_f_W_dot_cool_des`;
  * SSC's stacking order is T_htf, m_dot_htf, T_amb (`ud_power_cycle.h`).

This module fails loudly rather than silently writing a map in the wrong shape.
"""

from __future__ import annotations
import argparse
import csv
import math
import os
import PySAM.Sco2CspUdPcTables as sco2
import sam_case as sc          # reuse the identical chloride HTF table builder

# The sCO2 PHX sees the SAME custom chloride fluid as the tower loop.
HTF_CODE_LOOKUP_TABLE = 50     # "Lookup tables" = user-defined fluid

# 0.7 wt% CuO -- the best-tested loading (Han et al. 2022), used as the DEFAULT
# reference map only. NOT a locked design choice: pass --phi to sweep it.
DEFAULT_PHI_MASS = 0.007

# Where generated maps land. One file per loading, named for the loading, so a
# map can never be silently reused for the wrong fluid.
DEFAULT_OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maps")

# Expected per-axis table width for PySAM 7.1.1 (see MAP LAYOUT above).
UDPC_N_COLS = 13
# SSC's own stacking order (ud_power_cycle.h): T_htf, then m_dot_htf, then
# T_amb. Confirmed against the tower's default ud_ind_od, whose three 60-row
# blocks sweep exactly that sequence. Do not reorder.
UDPC_AXES = ("T_htf_ind", "m_dot_htf_ND_ind", "T_amb_ind")

# The tower's 7-column combined layout, decoded from the installed default and
# confirmed against SSC's N_udpc_common::split_ind_tbl (which reads col 0-2 as
# T_htf / m_dot / T_amb and 3-6 as the four responses).
TOWER_UD_COLS = ("T_htf [C]", "m_dot_htf_ND", "T_amb [C]", "W_dot_gross_ND",
                 "Q_dot_HTF_ND", "W_dot_cooling_ND", "m_dot_water_ND")

# Which variable supplies the 3 LEVELS for each swept table, and which variable
# is held at its design value. This is the inverse of split_ind_tbl():
#   T_htf swept -> levels of m_dot, T_amb held at design
#   m_dot swept -> levels of T_amb, T_htf held at design
#   T_amb swept -> levels of T_htf, m_dot held at design
UDPC_PAIRING = {
    "T_htf_ind":        ("m_dot", "T_amb"),
    "m_dot_htf_ND_ind": ("T_amb", "T_htf"),
    "T_amb_ind":        ("T_htf", "m_dot"),
}

# Response groups inside the 13-column layout: col 0 is the swept variable,
# then each response occupies 3 consecutive columns at the [low, design, high]
# levels of the paired variable (ud_power_cycle.h: "1)- 2)0 3)+").
UDPC_RESPONSE_BASE = {"W_dot_gross": 1, "Q_dot_HTF": 4,
                      "W_dot_cooling": 7, "m_dot_water": 10}
LEVEL_DESIGN = 1        # index of the design level within each response triple

# Property sensitivity axes. The COMMITTED case is ("linear", "nominal");
# everything else is a sensitivity and must be reported as one.
CP_MODELS = ("linear", "cubic")
BANDS = ("nominal", "lo", "hi")
DEFAULT_CP_MODEL = sc.COMMITTED_CP_MODEL   # "linear"
DEFAULT_BAND = "nominal"

# Several UDPC response columns are near-zero parasitic fractions (~1e-5). A
# RELATIVE change on those inflates wildly while the absolute change is
# meaningless -- e.g. 0.485% on a 3.7e-5 entry is an absolute move of 1.8e-7.
# Comparisons therefore report both the raw max and the max over columns whose
# committed magnitude exceeds this floor. Quote the FLOORED number as the
# headline; quote the raw one only with its absolute context.
SIGNIFICANT_MAGNITUDE = 0.01


# =============================================================================
# Committed cycle design parameters
# =============================================================================
DESIGN = dict(
    W_dot_net_des=115.0,       # MWe gross cycle design power (typical Gen3 block)
    T_htf_hot_des=700.0,       # C  design hot HTF temp (chloride high-T case)
    eta_thermal_des=0.44,      # target design thermal efficiency (solver target)
    T_amb_des=35.0,            # C  design ambient (dry-cooled desert site)
    dT_PHX_hot_approach=20.0,  # C  primary HX hot-end approach
    dT_mc_approach=6.0,        # C  main-compressor inlet approach above ambient
    site_elevation=600.0,      # m
    # design_method: 1 = specify target efficiency (simplest, matches our intent
    # of "hit ~44% and let the solver size the recuperators to get there")
    design_method=1.0,
)

# Isentropic efficiencies (turbine, main/re/pre compressors) and cycle layout
COMMON = dict(
    eta_isen_t=0.90,           # turbine
    eta_isen_mc=0.85,          # main compressor
    eta_isen_rc=0.85,          # recompressor
    eta_isen_pc=0.85,          # precompressor (unused in pure recompression)
    P_high_limit=25.0,         # MPa  max cycle pressure
    is_apply_default_htf_mins=1.0,  # guard custom-fluid sweep corners
    # --- sweep ranges for the off-design map ---
    # A modest 3x3x3 grid (27 pts). The full 5x5x5 pushed the solver into
    # infeasible corners for the custom chloride fluid (very low part-load at
    # high ambient), which crashed the sweep. Narrower ranges + fewer points
    # keep every corner solvable; SAM interpolates fine on 3 points per axis.
    T_htf_hot_low=620.0,       # C
    T_htf_hot_high=710.0,      # C  (bracket the chloride operating window)
    n_T_htf_hot=3,
    T_amb_low=5.0,             # C
    T_amb_high=45.0,           # C
    n_T_amb=3,
    m_dot_htf_ND_low=0.50,     # part-load fraction, low (0.5 avoids deep turndown)
    m_dot_htf_ND_high=1.05,    # slight over-design
    n_m_dot_htf_ND=3,
    is_generate_udpc=1.0,      # produce the UDPC table
)

HEATEX = dict(
    cycle_config=1,            # 1 = recompression (committed layout)
    is_recomp_ok=1,            # allow recompression fraction to be solved
    UA_recup_tot_des=15.0,     # MW/K total recuperator conductance (design knob)
    min_phx_deltaT=10.0,       # C  minimum PHX pinch
)

PHX = dict(
    dT_PHX_cold_approach=20.0,  # C  primary HX cold-end approach
)

# Dry-cooling (air cooler) design -- the sCO2 precooler rejects heat to ambient.
AIRCOOLER = dict(
    is_design_air_cooler=1.0,
    fan_power_frac=0.02,        # design fan power as fraction of net power
    deltaP_cooler_frac=0.005,   # CO2-side pressure-drop fraction across cooler
    eta_air_cooler_fan=0.5,     # fan isentropic efficiency
    N_nodes_air_cooler_pass=10.0,
)

# Design-point outputs pulled for reporting and for the sanity check below.
DESIGN_OUTPUTS = (
    ("net thermal efficiency", "eta_thermal_calc"),
    ("recompression fraction", "recomp_frac"),
    ("turbine inlet T [C]", "T_turb_in"),
    ("compressor inlet T [C]", "T_comp_in"),
    ("HTF cold return T [C]", "T_htf_cold_des"),
    ("cycle specific cost [$/kWe]", "cycle_spec_cost"),
)

# Outputs that MUST be present and finite for the solve to count as converged.
REQUIRED_DESIGN_OUTPUTS = ("eta_thermal_calc", "T_turb_in", "T_htf_cold_des")

# Verified baseline at phi = 0.007, T_htf_hot = 700 C (CLAUDE.md section 6).
# Divergence is not an error -- phi and design knobs legitimately move these --
# but a wild swing means something changed that you should look at.
BASELINE = {"eta_thermal_calc": 0.440, "T_turb_in": 680.0,
            "recomp_frac": 0.113, "T_htf_cold_des": 490.0}
BASELINE_TOL = 0.15        # relative; warn beyond +/-15%


class MapGenerationError(RuntimeError):
    """Raised when the solver or its outputs are not in a usable state."""


def _fmt_phi(phi_mass: float) -> str:
    """0.007 -> '0.007', 0.02 -> '0.02', 0.0 -> '0.0'. Stable for filenames."""
    s = f"{phi_mass:.4f}".rstrip("0")
    return s + "0" if s.endswith(".") else s


def map_path(phi_mass: float, outdir: str = DEFAULT_OUTDIR,
             cp_model: str = DEFAULT_CP_MODEL,
             band: str = DEFAULT_BAND) -> str:
    """Canonical output path, e.g. maps/sco2_udpc_phi_0.007.csv

    The COMMITTED case (linear cp fit, nominal band) gets the plain name.
    Sensitivity variants are suffixed -- `..._phi_0.007_cubic.csv`,
    `..._phi_0.007_hi.csv` -- so a sensitivity map can never be mistaken for
    the primary one, which is the whole point of running them.
    """
    name = f"sco2_udpc_phi_{_fmt_phi(phi_mass)}"
    if cp_model != DEFAULT_CP_MODEL:
        name += f"_{cp_model}"
    if band != DEFAULT_BAND:
        name += f"_{band}"
    return os.path.join(outdir, name + ".csv")


def generate_map(phi_mass: float = DEFAULT_PHI_MASS,
                 cp_model: str = DEFAULT_CP_MODEL,
                 band: str = DEFAULT_BAND,
                 verbose: bool = True):
    """Run the sCO2 design + off-design sweep at one nanoparticle loading.

    phi_mass is the CuO mass fraction (0.007 = 0.7 wt%). It enters only through
    the custom HTF table fed to the PHX; every cycle-design parameter is held
    at the committed values above so that maps at different phi are directly
    comparable.

    cp_model / band select the property SENSITIVITY case. The committed result
    is always ("linear", "nominal") -- see CLAUDE.md section 2. `cubic` infers a
    peak near 1.0 wt% that is a polynomial artifact, and the band edges push
    every property to one extreme at once (a corner, not a coherent draw), so
    both are reported as sensitivities and never as the primary result.

    Returns the solved model. Raises MapGenerationError if the solver fails or
    returns a design point that is not physically usable.
    """
    if cp_model not in CP_MODELS:
        raise ValueError(f"cp_model must be one of {CP_MODELS}, got {cp_model!r}")
    if band not in BANDS:
        raise ValueError(f"band must be one of {BANDS}, got {band!r}")

    m = sco2.new()

    # --- custom chloride HTF in the PHX (same fluid as the tower loop) ----
    m.SystemDesign.htf = HTF_CODE_LOOKUP_TABLE
    m.SystemDesign.htf_props = sc.build_htf_table(
        phi_mass, cp_model=cp_model, band=band)

    for k, v in DESIGN.items():
        setattr(m.SystemDesign, k, v)
    for k, v in COMMON.items():
        setattr(m.Common, k, v)
    for k, v in HEATEX.items():
        setattr(m.HeatExchangerDesign, k, v)
    for k, v in PHX.items():
        setattr(m.PHXDesign, k, v)
    for k, v in AIRCOOLER.items():
        setattr(m.AirCoolerDesign, k, v)

    if verbose:
        print("Solving sCO2 recompression cycle design + off-design sweep")
        tag = ("COMMITTED" if (cp_model, band) == (DEFAULT_CP_MODEL, DEFAULT_BAND)
               else "SENSITIVITY")
        print(f"  fluid : CuO / NaCl-KCl-MgCl2 at phi = {phi_mass*100:.2f} wt% "
              f"(cp '{cp_model}', band '{band}') [{tag}]")
        print(f"  design: {DESIGN['W_dot_net_des']:.0f} MWe, "
              f"TIT-side {DESIGN['T_htf_hot_des']:.0f} C, "
              f"target eta {DESIGN['eta_thermal_des']:.2f}")
        print(f"  sweep : {COMMON['n_T_htf_hot']} x {COMMON['n_T_amb']} x "
              f"{COMMON['n_m_dot_htf_ND']} = "
              f"{COMMON['n_T_htf_hot']*COMMON['n_T_amb']*COMMON['n_m_dot_htf_ND']}"
              f" operating points")

    try:
        m.execute()
    except Exception as e:
        # SSC failures surface as generic exceptions; make the context explicit
        # so a solver blow-up is never mistaken for a Python bug.
        raise MapGenerationError(
            f"sCO2 solver failed at phi = {phi_mass*100:.2f} wt%: "
            f"{type(e).__name__}: {e}. Infeasible sweep corners are the usual "
            f"cause -- narrow the T_amb / m_dot_htf_ND ranges in COMMON."
        ) from e

    validate_design(m, phi_mass, verbose=verbose)
    return m


def validate_design(m, phi_mass: float, verbose: bool = True) -> dict:
    """Confirm the solver actually produced a usable design point.

    `execute()` returning without raising is NOT sufficient -- a non-converged
    solve can leave outputs missing, zero, or NaN. Returns the design outputs
    as a dict; raises MapGenerationError if the design is unusable.
    """
    design = {}
    missing = []
    for _, attr in DESIGN_OUTPUTS:
        v = getattr(m.Outputs, attr, None)
        design[attr] = float(v) if isinstance(v, (int, float)) else v

    for attr in REQUIRED_DESIGN_OUTPUTS:
        v = design.get(attr)
        if not isinstance(v, float) or not math.isfinite(v) or v == 0.0:
            missing.append(f"{attr}={v!r}")
    if missing:
        raise MapGenerationError(
            f"sCO2 design point did not converge at phi = {phi_mass*100:.2f} wt%: "
            f"missing/invalid outputs [{', '.join(missing)}]. Do not write a map "
            f"from this solve."
        )

    eta = design["eta_thermal_calc"]
    if not 0.0 < eta < 1.0:
        raise MapGenerationError(
            f"nonsensical design efficiency eta = {eta:.4f} at "
            f"phi = {phi_mass*100:.2f} wt%."
        )

    # The chloride freezes at 401.4 C. A cold return at or below that is not a
    # valid design regardless of what the efficiency says.
    T_cold = design["T_htf_cold_des"]
    if T_cold <= sc.nfp.MELTING_POINT_C:
        raise MapGenerationError(
            f"HTF cold return {T_cold:.1f} C is at/below the A1 melting point "
            f"({sc.nfp.MELTING_POINT_C} C) -- the salt would freeze in the PHX. "
            f"Raise dT_PHX_cold_approach or lower the cycle's heat duty."
        )
    if verbose and T_cold < sc.nfp.MELTING_POINT_C + 20.0:
        print(f"  [warn] HTF cold return {T_cold:.1f} C leaves under 20 C of "
              f"freeze margin above {sc.nfp.MELTING_POINT_C} C.")

    if verbose:
        for attr, ref in BASELINE.items():
            v = design.get(attr)
            if isinstance(v, float) and ref and abs(v - ref) / abs(ref) > BASELINE_TOL:
                print(f"  [warn] {attr} = {v:,.4f} diverges >{BASELINE_TOL:.0%} "
                      f"from the verified baseline {ref:,.4f} (CLAUDE.md s6) -- "
                      f"investigate before trusting this map.")
    return design


def extract_udpc_table(m, expect_cols: int = UDPC_N_COLS):
    """Assemble the UDPC map from the three per-axis independent tables.

    The solver emits three tables, each sweeping ONE variable while the other
    two sit at their design values:
        T_htf_ind        -- sweeps HTF hot temperature
        T_amb_ind        -- sweeps ambient temperature
        m_dot_htf_ND_ind -- sweeps HTF mass-flow (part-load) fraction
    They are stacked in that order. Column 0 of each is the swept independent
    variable; the rest are the normalised cycle responses SAM interpolates
    during the annual run.

    Every table is validated before stacking: all three must exist, be
    non-empty, be rectangular, share the expected width, and have the row count
    implied by the configured sweep resolution. A structural surprise means the
    installed SAM version lays the map out differently (see MAP LAYOUT in the
    module docstring), so this raises rather than writing a malformed CSV.

    Returns (stacked_rows, parts) where parts is [(axis_name, rows), ...].
    """
    expected_rows = {
        "T_htf_ind": int(COMMON["n_T_htf_hot"]),
        "T_amb_ind": int(COMMON["n_T_amb"]),
        "m_dot_htf_ND_ind": int(COMMON["n_m_dot_htf_ND"]),
    }

    parts, problems = [], []
    for name in UDPC_AXES:
        tbl = getattr(m.Outputs, name, None)
        if tbl is None or len(tbl) == 0:
            problems.append(f"{name}: missing or empty")
            continue

        rows = [list(r) for r in tbl]
        widths = {len(r) for r in rows}
        if len(widths) != 1:
            problems.append(f"{name}: ragged rows, widths {sorted(widths)}")
            continue
        width = widths.pop()
        if width != expect_cols:
            problems.append(
                f"{name}: {width} columns, expected {expect_cols}")
            continue
        if len(rows) != expected_rows[name]:
            problems.append(
                f"{name}: {len(rows)} rows, expected {expected_rows[name]} "
                f"from the configured sweep resolution")
            continue
        if any(not all(isinstance(v, (int, float)) and math.isfinite(v) for v in r)
               for r in rows):
            problems.append(f"{name}: contains non-finite values")
            continue
        parts.append((name, rows))

    if problems:
        raise MapGenerationError(
            "UDPC tables failed validation -- refusing to write a map:\n  "
            + "\n  ".join(problems)
            + f"\nExpected {len(UDPC_AXES)} tables of {expect_cols} columns "
              f"(PySAM 7.1.1 layout). A different column count usually means a "
              f"SAM-version layout difference; reconcile against your install's "
              f"`ud_ind_od` docstring before proceeding."
        )

    stacked = [row for _, rows in parts for row in rows]
    return stacked, parts


def udpc_levels() -> dict:
    """The [low, design, high] level values for each independent variable.

    NOTE the middle entry is the DESIGN value, not the sweep midpoint. Verified
    two ways: the tower's own default uses T_htf levels [500, 574, 580] where
    574 is the design temperature and not the midpoint of 500-580; and in our
    production map the middle W_dot_gross column reads 1.0000 (design) rather
    than ~0.775 (the m_dot sweep midpoint).
    """
    return {
        "T_htf": (COMMON["T_htf_hot_low"], DESIGN["T_htf_hot_des"],
                  COMMON["T_htf_hot_high"]),
        "m_dot": (COMMON["m_dot_htf_ND_low"], 1.0,
                  COMMON["m_dot_htf_ND_high"]),
        "T_amb": (COMMON["T_amb_low"], DESIGN["T_amb_des"],
                  COMMON["T_amb_high"]),
    }


def _interp(x: float, xs: list, ys: list) -> float:
    """Linear interpolation with flat extrapolation outside the grid."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            f = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + f * (ys[i] - ys[i - 1])
    return ys[-1]


def design_cooling_nd(parts: list, verbose: bool = True) -> float:
    """The cooling column's value AT the design point, used to renormalise it.

    W_dot_gross / Q_dot_HTF / m_dot_water all come out of the sCO2 module
    already normalised to 1.0 at design. The cooling column does NOT -- it
    reads ~1e-3 there. SSC does not renormalise for you (ud_power_cycle.cpp
    interpolates the column as-is and "users are expected to provide
    pre-normalized values"), so the column must be divided by its own design
    value before it goes into the tower. Magnitude is then restored separately
    by `ud_f_W_dot_cool_des`.

    Each of the three tables must agree on this number -- they all pass through
    the same design point. Disagreement means the layout has been misread, so
    it is checked rather than assumed.
    """
    levels = udpc_levels()
    swept_design = {"T_htf_ind": levels["T_htf"][LEVEL_DESIGN],
                    "m_dot_htf_ND_ind": levels["m_dot"][LEVEL_DESIGN],
                    "T_amb_ind": levels["T_amb"][LEVEL_DESIGN]}
    col = UDPC_RESPONSE_BASE["W_dot_cooling"] + LEVEL_DESIGN

    ests, on_node = {}, {}
    for name, rows in parts:
        xs = [r[0] for r in rows]
        ys = [r[col] for r in rows]
        xd = swept_design[name]
        ests[name] = _interp(xd, xs, ys)
        on_node[name] = any(abs(x - xd) < 1e-9 for x in xs)

    # Tables whose swept grid contains the design value read it exactly; the
    # others interpolate. Cooling is nearly flat in T_htf and m_dot but STRONGLY
    # nonlinear in T_amb, so an off-node T_amb estimate carries real
    # interpolation error and must not be treated as a layout discrepancy.
    exact = [v for n, v in ests.items() if on_node[n]]
    smooth = [v for n, v in ests.items() if n != "T_amb_ind"]

    vals = list(ests.values())
    spread = (max(vals) - min(vals)) / max(abs(sum(vals) / len(vals)), 1e-12)
    smooth_spread = ((max(smooth) - min(smooth)) /
                     max(abs(sum(smooth) / len(smooth)), 1e-12)) if smooth else 0.0

    # A genuinely misread layout puts these orders of magnitude apart, not
    # percent. Two thresholds: the smooth directions must agree tightly, and
    # nothing may be wildly out.
    if smooth_spread > 0.02:
        raise MapGenerationError(
            f"the T_htf and m_dot tables disagree on the design-point cooling "
            f"value by {smooth_spread:.1%} (expected <2%): {ests}. Cooling is "
            f"nearly flat in both directions, so this indicates the 13-column "
            f"layout has been misread (column grouping or level ordering). "
            f"Do NOT write a tower table from this."
        )
    if spread > 0.25:
        raise MapGenerationError(
            f"per-axis tables disagree on the design-point cooling value by "
            f"{spread:.1%}: {ests}. Too large to be grid interpolation error; "
            f"check the layout before writing a tower table."
        )

    val = (sum(exact) / len(exact)) if exact else (sum(smooth) / len(smooth))
    if not math.isfinite(val) or val <= 0.0:
        raise MapGenerationError(
            f"design-point cooling value {val!r} is unusable for renormalisation")
    if verbose:
        src = "on-grid node" if exact else "T_htf/m_dot interpolation"
        print(f"  design-point cooling column value {val:.6g} (from {src}; "
              f"smooth dirs agree to {smooth_spread:.2%}, all-table spread "
              f"{spread:.1%}) -> renormalising to 1.0")
        if spread > 0.05:
            print(f"  [note] the T_amb table's estimate is off-node and "
                  f"nonlinear; residual error here scales only the cooling "
                  f"parasitic (~2% of gross), so a few % is immaterial.")
    return val


def to_tower_ud_ind_od(parts: list, verbose: bool = True) -> list:
    """Flatten the three 13-column tables into the tower's 7-column ud_ind_od.

    This is the exact inverse of SSC's N_udpc_common::split_ind_tbl(): that
    function reads a combined table's columns 0-2 as (T_htf, m_dot_htf_ND,
    T_amb) and rebuilds the per-axis 13-column tables; here we go the other way.

    Each 13-column row expands into THREE 7-column rows -- one per level of the
    paired variable -- with the level made explicit in the independent-variable
    columns instead of implicit in the column index.
    """
    levels = udpc_levels()
    cool_des = design_cooling_nd(parts, verbose=verbose)
    by_name = dict(parts)

    rows = []
    for name in UDPC_AXES:                       # SSC's stacking order
        tbl = by_name[name]
        level_var, const_var = UDPC_PAIRING[name]
        for r in tbl:
            for j in range(3):                   # low, design, high
                ind = {level_var: levels[level_var][j],
                       const_var: levels[const_var][LEVEL_DESIGN]}
                ind[{"T_htf_ind": "T_htf",
                     "m_dot_htf_ND_ind": "m_dot",
                     "T_amb_ind": "T_amb"}[name]] = r[0]
                rows.append([
                    ind["T_htf"], ind["m_dot"], ind["T_amb"],
                    r[UDPC_RESPONSE_BASE["W_dot_gross"] + j],
                    r[UDPC_RESPONSE_BASE["Q_dot_HTF"] + j],
                    r[UDPC_RESPONSE_BASE["W_dot_cooling"] + j] / cool_des,
                    r[UDPC_RESPONSE_BASE["m_dot_water"] + j],
                ])

    if len(rows) != sum(len(t) for _, t in parts) * 3:
        raise MapGenerationError("row expansion produced an unexpected count")
    if any(len(r) != len(TOWER_UD_COLS) for r in rows):
        raise MapGenerationError("converted rows are not 7 columns wide")
    if verbose:
        print(f"  converted 13-col -> 7-col: {len(rows)} rows "
              f"x {len(TOWER_UD_COLS)} cols")
    return rows


def write_tower_udpc_csv(rows: list, path: str) -> str:
    """Write the tower-format table (7 cols) ready for ud_ind_od."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(TOWER_UD_COLS)
        w.writerows(rows)
    return path


def write_udpc_csv(stacked: list, path: str) -> str:
    """Write the stacked map. Column 0 = swept variable, 1-12 = ND responses."""
    if not stacked:
        raise MapGenerationError("refusing to write an empty UDPC map")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    header = ["ind_var"] + [f"c{i}" for i in range(1, len(stacked[0]))]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(stacked)
    return path


def build_and_write(phi_mass: float, outdir: str = DEFAULT_OUTDIR,
                    cp_model: str = DEFAULT_CP_MODEL,
                    band: str = DEFAULT_BAND,
                    verbose: bool = True) -> dict:
    """Full offline pipeline for one loading: solve, validate, write.

    Returns {'phi_mass', 'cp_model', 'band', 'design', 'path', 'stacked', 'parts'}.
    """
    m = generate_map(phi_mass, cp_model=cp_model, band=band, verbose=verbose)
    design = {attr: getattr(m.Outputs, attr, None) for _, attr in DESIGN_OUTPUTS}

    if verbose:
        print("\nDesign-point results:")
        for label, attr in DESIGN_OUTPUTS:
            v = design.get(attr)
            if v is None:
                print(f"  {label:<32} (not exposed in this SAM version)")
            else:
                print(f"  {label:<32} {v:,.4f}" if isinstance(v, float)
                      else f"  {label:<32} {v}")

    stacked, parts = extract_udpc_table(m)
    path = write_udpc_csv(stacked, map_path(phi_mass, outdir, cp_model, band))

    # --- tower-format (7-col) table + the design magnitudes it needs --------
    tower_rows = to_tower_ud_ind_od(parts, verbose=verbose)
    tower_path = write_tower_udpc_csv(
        tower_rows, map_path(phi_mass, outdir, cp_model, band)
        .replace(".csv", "_tower7.csv"))

    # ud_f_W_dot_cool_des is a PERCENT of design gross output (tower docstring).
    # The sCO2 design solve gives cooling and gross directly.
    fan = getattr(m.Outputs, "cooler_tot_W_dot_fan", None)
    gross = DESIGN["W_dot_net_des"]
    f_cool_pct = (100.0 * fan / gross) if isinstance(fan, float) and gross else None

    if verbose:
        print(f"\nUDPC map assembled from {len(parts)} per-axis tables:")
        for name, rows in parts:
            print(f"  {name:<18} {len(rows)} rows x {len(rows[0])} cols")
        print(f"  stacked -> {len(stacked)} rows -> {path}")
        print(f"  tower   -> {len(tower_rows)} rows -> {tower_path}")
        if f_cool_pct is not None:
            print(f"  ud_f_W_dot_cool_des = {f_cool_pct:.4f} %  "
                  f"(= {fan:.3f} MWe cooling / {gross:.0f} MWe gross)")

    return {"phi_mass": phi_mass, "cp_model": cp_model, "band": band,
            "design": design, "path": path, "stacked": stacked, "parts": parts,
            "tower_path": tower_path, "tower_rows": tower_rows,
            "f_W_dot_cool_des_pct": f_cool_pct,
            "m_dot_water_cool_des": 0.0}   # dry-cooled: no water


def compare_maps(results: list, verbose: bool = True) -> float:
    """Max relative difference in the normalised responses across loadings.

    This is the number that decides whether one frozen map is defensible: if
    maps at the phi extremes agree closely, holding the cycle map constant
    becomes a TESTED assumption rather than a silent one. Column 0 (the swept
    independent variable) is excluded -- it is identical by construction.
    """
    if len(results) < 2:
        return 0.0
    ref = results[0]
    worst, worst_sig, where = 0.0, 0.0, None
    for other in results[1:]:
        if len(other["stacked"]) != len(ref["stacked"]):
            raise MapGenerationError(
                "maps have different row counts; cannot compare")
        for i, (ra, rb) in enumerate(zip(ref["stacked"], other["stacked"])):
            for j in range(1, len(ra)):
                rel = abs(rb[j] - ra[j]) / max(abs(ra[j]), 1e-12)
                if abs(ra[j]) > SIGNIFICANT_MAGNITUDE:
                    worst_sig = max(worst_sig, rel)
                if rel > worst:
                    worst, where = rel, (other["phi_mass"], i, j)
    if verbose:
        phi_ref = ref["phi_mass"] * 100
        print(f"\nMap sensitivity to loading (reference phi = {phi_ref:.2f} wt%):")
        print(f"  max relative change, all columns:       {worst:.4%}")
        print(f"  max relative change, significant only:  {worst_sig:.4%}  "
              f"<- headline")
        if where:
            print(f"  raw worst at phi = {where[0]*100:.2f} wt%, "
                  f"row {where[1]}, column c{where[2]}")
        if worst_sig < 0.005:
            print("  -> under 0.5%: a single frozen map is defensible. State it "
                  "in the methodology as a tested assumption, citing this run.")
        else:
            print("  -> material: generate a phi-grid of maps and interpolate "
                  "between them in the optimiser loop.")
    return worst_sig


def load_map(path: str) -> list:
    """Read a written map back as rows of floats (header dropped)."""
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        raise MapGenerationError(f"{path}: no data rows")
    return [[float(v) for v in r] for r in rows[1:]]


def compare_variants(phi_mass: float, outdir: str = DEFAULT_OUTDIR,
                     verbose: bool = True) -> float:
    """Max relative response difference between property-model variants on disk.

    `compare_maps` answers "does phi move the map?". This answers the other
    question: "does the CHOICE OF PROPERTY MODEL move the map?" -- would the
    cubic cp fit or a band edge have produced a different cycle map than the
    committed (linear, nominal) case, at matched phi. Reads whichever variant
    maps exist in `outdir`, so it works across separate CLI invocations.
    """
    ref_path = map_path(phi_mass, outdir)
    if not os.path.exists(ref_path):
        raise MapGenerationError(
            f"committed map {ref_path} not found -- generate it first")
    ref = load_map(ref_path)

    worst, where, compared = 0.0, None, []
    for cp_model in CP_MODELS:
        for band in BANDS:
            if (cp_model, band) == (DEFAULT_CP_MODEL, DEFAULT_BAND):
                continue
            path = map_path(phi_mass, outdir, cp_model, band)
            if not os.path.exists(path):
                continue
            other = load_map(path)
            if len(other) != len(ref) or len(other[0]) != len(ref[0]):
                raise MapGenerationError(
                    f"{path}: shape {len(other)}x{len(other[0])} does not match "
                    f"the committed map {len(ref)}x{len(ref[0])}")
            local = local_sig = 0.0
            for i, (ra, rb) in enumerate(zip(ref, other)):
                for j in range(1, len(ra)):
                    rel = abs(rb[j] - ra[j]) / max(abs(ra[j]), 1e-12)
                    local = max(local, rel)
                    if abs(ra[j]) > SIGNIFICANT_MAGNITUDE:
                        local_sig = max(local_sig, rel)
                    if rel > worst:
                        worst, where = rel, (cp_model, band, i, j)
            compared.append((f"{cp_model}/{band}", local, local_sig))

    if verbose:
        print(f"\nMap sensitivity to PROPERTY MODEL at phi = "
              f"{phi_mass*100:.2f} wt% "
              f"(reference: {DEFAULT_CP_MODEL}/{DEFAULT_BAND}, committed):")
        if not compared:
            print("  no variant maps found -- nothing to compare")
            return 0.0
        print(f"  {'variant':<18} {'all cols':>10} {'significant':>12}   "
              f"(|value| > {SIGNIFICANT_MAGNITUDE})")
        for label, local, local_sig in compared:
            print(f"  {label:<18} {local:>10.4%} {local_sig:>12.4%}")
        if where:
            print(f"  raw worst {worst:.3%} at {where[0]}/{where[1]}, "
                  f"row {where[2]}, col c{where[3]}")
        sig_worst = max(s for _, _, s in compared)
        print(f"  HEADLINE (significant columns only): {sig_worst:.4%}")
    return max((s for _, _, s in compared), default=0.0)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Generate offline sCO2 UDPC performance map(s), one per "
                    "nanoparticle loading.")
    p.add_argument("--phi", type=float, nargs="+", default=[DEFAULT_PHI_MASS],
                   metavar="PHI",
                   help="CuO mass fraction(s), e.g. 0.007 (=0.7 wt%%). Pass "
                        "several to generate a map family or a sensitivity "
                        "sweep. Default: %(default)s")
    p.add_argument("--cp-model", choices=CP_MODELS, default=DEFAULT_CP_MODEL,
                   help="cp fit. 'linear' is COMMITTED; 'cubic' is a "
                        "sensitivity case only -- its ~1.0 wt%% peak is a "
                        "polynomial artifact. Default: %(default)s")
    p.add_argument("--band", choices=BANDS, default=DEFAULT_BAND,
                   help="property uncertainty band edge. 'lo'/'hi' push every "
                        "property to one extreme at once (a corner, not a "
                        "coherent draw). Default: %(default)s")
    p.add_argument("--outdir", default=DEFAULT_OUTDIR,
                   help="directory for generated maps (default: %(default)s)")
    p.add_argument("--compare-variants", type=float, metavar="PHI",
                   help="skip generation; diff the committed map at PHI "
                        "against whichever cubic/band-edge variants exist in "
                        "--outdir, and report the max response change")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    verbose = not args.quiet

    if args.compare_variants is not None:
        compare_variants(args.compare_variants, outdir=args.outdir,
                         verbose=verbose)
        return 0

    results = []
    for phi in args.phi:
        if len(args.phi) > 1 and verbose:
            print("\n" + "=" * 68)
            print(f"phi = {phi*100:.2f} wt%  "
                  f"[cp {args.cp_model} / band {args.band}]")
            print("=" * 68)
        results.append(build_and_write(phi, outdir=args.outdir,
                                       cp_model=args.cp_model, band=args.band,
                                       verbose=verbose))

    if len(results) > 1:
        compare_maps(results, verbose=verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
