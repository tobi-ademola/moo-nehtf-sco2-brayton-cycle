"""
PySAM integration for the nano-enhanced chloride HTF study
===========================================================

Builds a Molten Salt Power Tower (PySAM `TcsmoltenSalt`) case that uses the
CuO / NaCl-KCl-MgCl2 nanofluid from `nanofluid_properties` as a CUSTOM HTF,
runs it, and extracts the four objectives.

Verified against PySAM 7.1.1 (`TcsmoltenSalt`, config 'MSPTSingleOwner'):
  * rec_htf = 50 selects "Lookup tables" (custom fluid). Default 17 is the
    nitrate solar salt this study deliberately does NOT use.
  * field_fl_props is the 7-column custom-fluid table, matching SAM's
    "Edit Material Properties" dialog column-for-column:
        T [C] | cp [kJ/kg-K] | rho [kg/m3] | mu [Pa-s] |
        nu [m2/s] | k [W/m-K] | h [J/kg]
  * UserDefinedPowerCycle.ud_ind_od holds the power-cycle performance map
    (180 x 7 by default) and ud_is_sco2_regr flags an sCO2 regression --
    this is where the offline-generated sCO2 map is injected (see STEP 2).

PIPELINE POSITION: this is the "per-iteration" leg of the architecture. The
sCO2 cycle map is generated ONCE offline (Neises model) and loaded here; only
the HTF table and plant sizing change per optimiser candidate.
"""

from __future__ import annotations
import csv
import os
import PySAM.TcsmoltenSalt as tcs
import PySAM.Singleowner as so

import nanofluid_properties as nfp

_HERE = os.path.dirname(os.path.abspath(__file__))


# =============================================================================
# Constants verified against the PySAM API (do not guess these)
# =============================================================================
HTF_CODE_LOOKUP_TABLE = 50    # "Lookup tables" = custom fluid
HTF_CODE_SOLAR_SALT = 17      # nitrate salt (SAM default; NOT used here)

# A weather file is MANDATORY. Without one the CSP modules SEGFAULT rather than
# raising a Python error (PVWatts fails gracefully; TcsmoltenSalt does not).
# If you hit an unexplained crash, check this first.
DEFAULT_WEATHER_FILE = os.path.join(_HERE, "weather_data", "redstone_tmy.csv")

# --- sCO2 power block -------------------------------------------------------
# pc_config: 0 = SAM's built-in steam Rankine (the default we do NOT want),
# 1 = user-defined cycle, i.e. the offline sCO2 map.
PC_CONFIG_USER_DEFINED = 1

# The 7-column tower-format map written by sco2_cycle_map.to_tower_ud_ind_od().
# NOT the 13-column per-axis file -- see that module's MAP LAYOUT note.
DEFAULT_UDPC_MAP = os.path.join(_HERE, "maps", "sco2_udpc_phi_0.007_tower7.csv")

# Design magnitudes that accompany the map. ud_ind_od carries only normalised
# SHAPES; these restore the scale. Both come from the sCO2 design solve.
DEFAULT_F_W_DOT_COOL_DES = 2.0    # [%] of design gross consumed by cooling
DEFAULT_M_DOT_WATER_COOL_DES = 0.0  # [kg/s] dry-cooled: no water
DEFAULT_SCO2_DESIGN_EFF = 0.4398  # sCO2 design thermal efficiency
DEFAULT_SCO2_P_REF_MW = 115.0     # sCO2 design gross output [MWe]

# Temperature grid for the property table. Spans A1's stated validity window
# (450-700 C). Must bracket the actual operating T_cold..T_hot or SAM will
# extrapolate off the end of the table.
DEFAULT_T_GRID_C = [450.0, 500.0, 550.0, 600.0, 650.0, 700.0]

# COMMITTED cp fit: piecewise-linear (see nanofluid_properties.cp_enhancement).
# Only 3 same-salt cp points exist, so the module uses the most conservative
# interpolant and treats curve shape as an explicit uncertainty. Run band-edge
# and cp_model="cubic" cases as sensitivities, never as the primary result.
COMMITTED_CP_MODEL = "linear"


def build_htf_table(phi_mass: float,
                    T_grid_C=None,
                    band: str = "nominal",
                    cp_model: str = "linear") -> list:
    """Build SAM's 7-column custom-fluid table for one nanoparticle loading.

    Column order and units are SAM's, confirmed against the Edit Material
    Properties dialog:
        T [C], cp [kJ/kg-K], rho [kg/m3], mu [Pa-s], nu [m2/s], k [W/m-K],
        h [J/kg]

    NOTE the cp unit: SAM wants kJ/(kg K) while the property module works in
    J/(kg K), hence the /1000. Getting this wrong is a silent 1000x error.

    band: "nominal" | "lo" | "hi" -- band edges give a cheap first pass at the
    robust study (run SAM at each edge) before wiring a full Monte-Carlo.
    """
    if T_grid_C is None:
        T_grid_C = DEFAULT_T_GRID_C
    if len(T_grid_C) < 2:
        raise ValueError("SAM requires at least two temperature rows")

    pick = {"nominal": lambda p: p.nominal,
            "lo": lambda p: p.lo,
            "hi": lambda p: p.hi}[band]

    E_cp = nfp.cp_enhancement(phi_mass * 100.0, model=cp_model)

    rows = []
    for T in T_grid_C:
        p = nfp.nanofluid_properties(phi_mass, T, cp_model=cp_model)
        rho = pick(p["rho"])
        mu = pick(p["mu"])
        rows.append((
            T,                          # Temperature [C]
            pick(p["cp"]) / 1000.0,     # Specific heat [kJ/kg-K]  <- /1000
            rho,                        # Density [kg/m3]
            mu,                         # Viscosity [Pa-s]
            mu / rho,                   # Kinematic viscosity [m2/s]
            pick(p["k"]),               # Conductivity [W/m-K]
            nfp._enthalpy(T, E_cp),     # Enthalpy [J/kg]
        ))
    return rows


def load_udpc_map(path: str = DEFAULT_UDPC_MAP) -> list:
    """Read the 7-column tower-format sCO2 map from CSV.

    Validates the shape loudly. The 13-column per-axis file is NOT accepted
    here -- SSC's ud_ind_od wants the combined 7-column layout
    [T_htf, m_dot_htf_ND, T_amb, W_gross_ND, Q_HTF_ND, W_cool_ND, m_water_ND],
    which sco2_cycle_map.to_tower_ud_ind_od() produces.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"sCO2 UDPC map not found: {path}. Generate it with "
            f"`python sco2_cycle_map.py --phi <phi>`."
        )
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        raise ValueError(f"{path}: no data rows")
    table = [[float(v) for v in r] for r in rows[1:]]
    widths = {len(r) for r in table}
    if widths != {7}:
        raise ValueError(
            f"{path}: expected 7 columns, found {sorted(widths)}. If this is "
            f"13, you passed the per-axis map instead of the *_tower7.csv one."
        )
    if len(table) % 3 != 0:
        raise ValueError(
            f"{path}: {len(table)} rows is not divisible by 3; the table must "
            f"be three stacked blocks (T_htf, m_dot, T_amb sweeps)."
        )
    return table


def apply_sco2_power_block(model,
                           udpc_map: str | list = DEFAULT_UDPC_MAP,
                           f_W_dot_cool_des: float = DEFAULT_F_W_DOT_COOL_DES,
                           m_dot_water_cool_des: float = DEFAULT_M_DOT_WATER_COOL_DES,
                           design_eff: float = DEFAULT_SCO2_DESIGN_EFF,
                           P_ref_MW: float = DEFAULT_SCO2_P_REF_MW,
                           verbose: bool = False):
    """Flip the tower's power block from steam Rankine to the sCO2 map.

    This is the step that makes the model an sCO2 recompression plant rather
    than a chloride tower with SAM's stock steam cycle.

    ud_ind_od carries only NORMALISED shapes, so the design magnitudes have to
    be supplied alongside it or the cycle is silently mis-scaled:
      * ud_f_W_dot_cool_des     -- percent of design gross consumed by cooling
      * ud_m_dot_water_cool_des -- design cooling water [kg/s]; 0 when dry-cooled
      * design_eff / P_ref      -- the sCO2 design efficiency and gross power,
        which otherwise stay at SAM's steam-Rankine defaults (0.412 / 115 MW).
    """
    table = load_udpc_map(udpc_map) if isinstance(udpc_map, str) else udpc_map

    model.PowerCycle.pc_config = PC_CONFIG_USER_DEFINED
    model.UserDefinedPowerCycle.ud_ind_od = table
    model.UserDefinedPowerCycle.ud_f_W_dot_cool_des = f_W_dot_cool_des
    model.UserDefinedPowerCycle.ud_m_dot_water_cool_des = m_dot_water_cool_des
    model.SystemDesign.design_eff = design_eff
    model.SystemDesign.P_ref = P_ref_MW

    if verbose:
        print(f"  pc_config            = {model.PowerCycle.pc_config} "
              f"(1 = user-defined sCO2 map)")
        print(f"  ud_ind_od            = {len(table)} rows x {len(table[0])} cols")
        print(f"  ud_f_W_dot_cool_des  = {f_W_dot_cool_des} %")
        print(f"  design_eff           = {design_eff}")
    return model


def build_case(phi_mass: float,
               T_hot_C: float = 700.0,
               T_cold_C: float = 450.0,
               T_grid_C=None,
               band: str = "nominal",
               weather_file: str = DEFAULT_WEATHER_FILE,
               config: str = "MSPTSingleOwner",
               udpc_map: str | list | None = DEFAULT_UDPC_MAP):
    """Create a TcsmoltenSalt model configured with the nanofluid HTF.

    T_hot/T_cold default to the chloride's high-temperature window rather than
    SAM's nitrate defaults (574/290 C). The cold side MUST stay above the A1
    melting point (401.4 C) plus a freeze margin -- enforced below.
    """
    margin = 20.0
    if T_cold_C < nfp.MELTING_POINT_C + margin:
        raise ValueError(
            f"T_cold={T_cold_C} C is below the A1 melting point "
            f"({nfp.MELTING_POINT_C} C) + {margin} C freeze margin. "
            f"Chlorides melt high -- this constrains the cold tank."
        )
    if T_hot_C > nfp.T_VALID_MAX_C:
        print(f"  [warn] T_hot={T_hot_C} C exceeds A1's tested range "
              f"({nfp.T_VALID_MAX_C} C); authors endorse extrapolation to "
              f"800 C but flag this in the methodology.")

    model = tcs.default(config)

    # --- weather (MANDATORY -- omitting this segfaults SSC) ---------------
    if not os.path.exists(weather_file):
        raise FileNotFoundError(
            f"Weather file not found: {weather_file}. CSP modules SEGFAULT "
            f"without one rather than raising an error."
        )
    model.SolarResource.solar_resource_file = weather_file

    # --- custom HTF ------------------------------------------------------
    model.TowerAndReceiver.rec_htf = HTF_CODE_LOOKUP_TABLE
    model.TowerAndReceiver.field_fl_props = build_htf_table(
        phi_mass, T_grid_C=T_grid_C, band=band)

    # --- operating temperatures -----------------------------------------
    model.SystemDesign.T_htf_hot_des = T_hot_C
    model.SystemDesign.T_htf_cold_des = T_cold_C

    # --- sCO2 power block (replaces SAM's built-in steam Rankine) ---------
    if udpc_map is not None:
        apply_sco2_power_block(model, udpc_map=udpc_map)

    return model


def extract_objectives(model, financial=None) -> dict:
    """Pull the four study objectives out of a solved model.

    O1 efficiency, O2 cost (LCOE), O3 HTF pumping power, O4 storage inventory.

    IMPORTANT: several SAM outputs are 8760-hour arrays, not scalars. The
    optimiser needs scalars, so arrays are aggregated here (sum for energy-like
    quantities, max for sizing-like quantities). Output names vary by SAM
    version, so each is looked up defensively and reported as None if absent
    rather than crashing the optimiser mid-run.
    """
    def get(obj, *names):
        for n in names:
            try:
                v = getattr(obj.Outputs, n)
                if v is not None:
                    return v
            except AttributeError:
                continue
        return None

    def total(v):
        """Sum an hourly array -> annual total; pass scalars through."""
        if v is None:
            return None
        return float(sum(v)) if isinstance(v, (list, tuple)) else float(v)

    def peak(v):
        """Max of an hourly array -> design size; pass scalars through."""
        if v is None:
            return None
        return float(max(v)) if isinstance(v, (list, tuple)) else float(v)

    out = {
        # --- O1: efficiency / annual yield ---
        "annual_energy_kWh": total(get(model, "annual_energy")),
        "capacity_factor_pct": total(get(model, "capacity_factor")),
        # --- O3: HTF pumping parasitic (standalone objective) ---
        #   annual total [MWh] and design-point peak [MW]
        "pump_parasitic_MWh": total(get(model, "P_tower_pump",
                                        "annual_q_pb_pump", "pparasi")),
        "pump_parasitic_peak_MW": peak(get(model, "P_tower_pump",
                                           "annual_q_pb_pump", "pparasi")),
        # --- O4: storage inventory (peak salt mass = tank sizing) ---
        "tes_mass_peak_kg": peak(get(model, "m_tes", "mass_tes_hot")),
        "tes_hours": total(get(model, "tshours")),
    }
    if financial is not None:
        # --- O2: cost ---
        out["lcoe_real_cents_kWh"] = total(get(financial, "lcoe_real"))
        out["lcoe_nom_cents_kWh"] = total(get(financial, "lcoe_nom"))
        out["npv_usd"] = total(get(financial, "project_return_aftertax_npv"))
    return out


def run_case(phi_mass: float, with_financial: bool = True, **kwargs):
    """Build, execute, and extract. Returns (model, financial, objectives).

    NOTE on ordering: the financial model must be created via from_existing()
    BEFORE the CSP model executes, so it shares the same data container and
    sees the 8760-hour `gen` array. Creating it afterwards yields
    "invalid number of gen records (1)".
    """
    model = build_case(phi_mass, **kwargs)

    fin = so.from_existing(model, "MSPTSingleOwner") if with_financial else None

    model.execute()
    if fin is not None:
        fin.execute()

    return model, fin, extract_objectives(model, fin)


if __name__ == "__main__":
    PHI = 0.007          # 0.7 wt% CuO -- Han/B3's measured cp optimum

    print("=" * 68)
    print("STEP 1 -- custom HTF table (SAM 7-column format)")
    print("=" * 68)
    table = build_htf_table(PHI)
    hdr = ("T[C]", "cp[kJ/kgK]", "rho[kg/m3]", "mu[Pa-s]",
           "nu[m2/s]", "k[W/mK]", "h[J/kg]")
    print(("{:>8}" * 7).format(*hdr))
    for r in table:
        print("{:>8.0f}{:>11.4f}{:>11.1f}{:>10.6f}{:>11.3e}{:>9.4f}{:>10.0f}"
              .format(*r))

    print()
    print("=" * 68)
    print("STEP 2 -- build the case and verify SAM accepted the table")
    print("=" * 68)
    m = build_case(PHI, T_hot_C=700.0, T_cold_C=450.0)
    print(f"  rec_htf              = {m.TowerAndReceiver.rec_htf}  "
          f"(50 = lookup table / custom fluid)")
    fp = m.TowerAndReceiver.field_fl_props
    print(f"  field_fl_props shape = {len(fp)} rows x {len(fp[0])} cols")
    print(f"  T_htf_hot_des        = {m.SystemDesign.T_htf_hot_des} C")
    print(f"  T_htf_cold_des       = {m.SystemDesign.T_htf_cold_des} C")
    print(f"  round-trip row 0     = {tuple(round(v, 4) for v in fp[0])}")

    print()
    print("=" * 68)
    print("STEP 3 -- execute the annual simulation")
    print("=" * 68)
    try:
        model, fin, obj = run_case(PHI, T_hot_C=700.0, T_cold_C=450.0)
        print("  simulation completed\n")
        for k, v in obj.items():
            if v is None:
                print(f"    {k:<26} (not exposed in this SAM version)")
            elif isinstance(v, float):
                print(f"    {k:<26} {v:,.4f}")
            else:
                print(f"    {k:<26} {v}")
    except Exception as e:
        print(f"  execution failed: {type(e).__name__}: {e}")
        print("\n  This is the expected place to iterate -- a custom fluid at")
        print("  chloride temperatures will likely need receiver/design")
        print("  parameters retuned away from SAM's nitrate defaults.")
