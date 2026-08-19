r"""
Nanofluid property module -- OBJECTIVE 1, reused from prior work
================================================================

PURPOSE. Maps nanoparticle mass fraction and temperature to the thermophysical
properties every other module in this project consumes. This is MASTER_PLAN.md
Objective 1, recorded there as largely reused from prior work -- this file IS
that prior work. It is a heavily-validated asset: treat it as a dependency to
call, not as code to re-derive. `validate()` re-checks the fits against the
measured anchor points and is the thing to run if you suspect drift.

PROVENANCE NOTE. Promoted into scripts/ on 2026-08-13 (Session E) from the repo
root, where it had been dropped in untracked. Only the module docstring, the
__main__ demo's output path and one duplicated `return` were touched; every
correlation, coefficient and uncertainty band is byte-for-byte the original.
The two files that arrived alongside it -- sam_case.py, sco2_cycle_map.py -- are
a DIFFERENT matter: they are prior-project reference material, not validated
here, and live under reference/prior_project/. See that directory's README.

INPUTS. None -- every coefficient is transcribed inline from the sources below.
Pure Python + stdlib `math`; no numpy, no PySAM, no CoolProp.

HOW TO RUN (self-check + property table + a sample SAM export):
    .\.venv\Scripts\python.exe -u .\scripts\nanofluid_properties.py

CONSUMED BY. scripts/htf_sam_bridge.py, which turns `htf_table_rows()` into the
7-column table SAM's `rec_htf = 50` custom-fluid path wants (CLAUDE.md §6).

---

Maps nanoparticle mass fraction (phi_mass, wt fraction) and temperature to the
five thermophysical properties named by Objective 1 and consumed by the sCO2 /
SAM techno-economic model:

    rho(T)    density              -> mass flow, inventory volume, dP
    cp(T)     specific heat        -> storage inventory / TES energy density
    k(T)      thermal conductivity -> HTF-side heat transfer
    alpha(T)  thermal diffusivity  -> transient/receiver response  [DERIVED]
    mu(T)     dynamic viscosity    -> pumping power

alpha = k/(rho*cp) is derived rather than independently correlated, on purpose --
see diffusivity_nf(). It was added 2026-08-15 when the supervisor's revised
Objective 1 named thermal diffusivity explicitly; the quantity was already inside
this module as the input Han's k was back-derived from, but was not an output.

COMMITTED SYSTEM (locked):
  Base fluid   : NaCl-KCl-MgCl2 ternary chloride eutectic   ......... "A1"
  Nanoparticle : CuO
  cp / k anchor: Han et al., Sol. Energy Mater. Sol. Cells 234 (2022) 111432
                 doi:10.1016/j.solmat.2021.111432 ................... "B3"
                 SAME base salt; series at 0.2 / 0.7 / 2.0 wt%.
  Mechanism    : Shin & Banerjee, IJHMT 54 (2011) 1064-1070 ......... "B1"
                 doi:10.1016/j.ijheatmasstransfer.2010.11.017
                 SiO2 in a DIFFERENT chloride eutectic -> MECHANISM ONLY,
                 never used for magnitudes here.

Every property returns a Prop(nominal, lo, hi). Bands combine the A1 base-salt
95% uncertainties with an enhancement-model uncertainty, so a parametric or
uncertainty sweep can sample within them. All property models are implemented;
sourcing/citation status for each input is documented next to its definition
below -- Objective 1 now requires DOCUMENTED PROVENANCE per correlation, so those
comments are a deliverable, not annotation. The provenance map lives in
PROPERTIES.md and the full source entries in SOURCES.md sections B, C and D.

NOT REPRESENTED HERE: particle-size (d_p) dependence. Every enhancement fit is
anchored to Han/B3's series at a FIXED particle size, so this module is size-blind
and a d_p sweep would move nothing. The revised Objective 3 names particle size as
a swept parameter, so this is now a blocking gap rather than a declared exclusion
-- see MASTER_PLAN.md §10 for the three options and do not sweep d_p through this
module until one of them is implemented and recorded in DECISIONS.md.
"""

from __future__ import annotations
import math
import os
from dataclasses import dataclass
from typing import Sequence


# =============================================================================
# Property container
# =============================================================================
@dataclass(frozen=True)
class Prop:
    """A property value with an uncertainty band."""
    nominal: float
    lo: float
    hi: float

    @classmethod
    def from_rel(cls, nominal: float, rel: float) -> "Prop":
        """Symmetric band: +/- rel (fraction). e.g. rel=0.15 -> +/-15%."""
        return cls(nominal, nominal * (1 - rel), nominal * (1 + rel))

    def sample(self, u: float) -> float:
        """Map u in [0,1] onto the band (0->lo, 0.5->nominal, 1->hi).

        Piecewise-linear so asymmetric bands are handled correctly. This is the
        hook an uncertainty-aware parametric sweep calls to propagate the band
        edges through the plant model.
        """
        if u <= 0.5:
            return self.lo + (self.nominal - self.lo) * (u / 0.5)
        return self.nominal + (self.hi - self.nominal) * ((u - 0.5) / 0.5)


# =============================================================================
# Nanoparticle material constants
# -----------------------------------------------------------------------------
# COMMITTED: CuO. rho=6320 kg/m3 is not a free choice -- it is the value implied
# by Han/B3's own density table (back-solving Table 2 gives 6317 kg/m3), so using
# it keeps this module numerically consistent with the anchor paper.
#
# cp = 667.1 J/(kg K) is pinned to a primary source: NIST-JANAF Thermochemical
# Tables (Chase, M.W. Jr., 4th ed., J. Phys. Chem. Ref. Data, Monograph 9, 1998),
# via NIST Chemistry WebBook, CuO condensed-phase Shomate table:
# https://webbook.nist.gov/cgi/cbook.cgi?Formula=CuO&Units=SI
# (Condensed phase thermochemistry data -> Solid Phase Heat Capacity). NIST's
# own tabulated Cp at 700 K (52.24 J/molK) and 800 K (53.35 J/molK), linearly
# interpolated to 773.15 K (500 C), give 53.05 J/molK -- matching the Shomate
# equation evaluated at the same T (53.06 J/molK) to within 0.02%, i.e. two
# independent readings of the same NIST data agree. Converted to mass basis
# using M(CuO) = 79.545 g/mol: cp(500 C) = 53.05 / 0.079545 = 667.1 J/(kg K).
# (cp drifts only ~660-692 J/kgK across the 450-700 C operating window, so this
# single midpoint value is a reasonable simplification for the constant.)
#
# k = 33 W/(m K) is DEFERRED: NIST WebBook carries no thermal-conductivity data
# for inorganic solids, and bulk CuO k is genuinely scarce in the literature --
# Zhang et al., J. Therm. Anal. Calorim. (2024), doi:10.1007/s10973-024-13445-5,
# note it is "seldom mentioned" and "impractical to test... directly" with
# standard instruments, which is why they resorted to an inverse method. Kept as
# a standard literature range (~20-33 W/m.K; Han/B3 itself quotes 76.51 W/m.K
# for a different sample). Revisit via a materials handbook (e.g. Touloukian,
# Thermophysical Properties of Matter) when resources allow. Low priority: k
# here feeds ONLY the Maxwell FLOOR below (which under-predicts the real,
# nanostructure-driven enhancement anyway -- see k_maxwell_floor), so its exact
# value does not affect any reported nominal.
# =============================================================================
@dataclass(frozen=True)
class Nanoparticle:
    name: str
    rho: float   # kg/m3
    cp: float    # J/(kg K)
    k: float     # W/(m K)

CUO = Nanoparticle(name="CuO", rho=6320.0, cp=667.1, k=33.0)


# =============================================================================
# Base fluid: NaCl-KCl-MgCl2 ternary chloride eutectic (A1)
# -----------------------------------------------------------------------------
# Correlations transcribed from Table 9 of the experimentally-tested A1 property
# set (Xu/Wang et al., ASME J. Sol. Energy Eng. 143(4):041005, 2021 / NREL).
# T in degrees Celsius. Stated validity 450-700 C; the authors explicitly endorse
# extrapolation to 800 C. Flag anything above 700 C as author-endorsed
# extrapolation rather than measurement.
#
# UNIT CONVERSIONS APPLIED to reach SI (this is where silent bugs hide):
#   source cp is J/(g K)  -> x1000 -> J/(kg K):  1.30138-0.0005T -> 1301.38-0.5T
#   source mu is cP       -> x1e-3 -> Pa s.
#   The exponent's (T+273.15) is an INTERNAL C->K conversion, so still pass T in
#   CELSIUS. Do not pre-convert to Kelvin or you will double-count.
# =============================================================================
MELTING_POINT_C = 401.4      # A1 Table 9 (+/-1.3). Han/B3 measured 399.7 -> consistent.
                             # Cold-tank floor: require T_cold > this + safety margin.
T_VALID_MIN_C = 450.0        # A1 stated validity window
T_VALID_MAX_C = 700.0        # (extrapolation endorsed by the authors to 800 C)

# A1 Table 9 95% uncertainties, converted to SI.
_BASE_U = {
    "rho": 15.27,            # kg/m3
    "cp": 35.8,              # J/(kg K)   (= 0.0358 J/g K)
    "k": 0.037,              # W/(m K)
    "mu": 1.138e-4,          # Pa s       (= 0.1138 cP)
}


def base_chloride_properties(T_C: float) -> dict:
    """A1 base-fluid properties at T_C [deg C], SI units."""
    return {
        "rho": 1958.8438 - 0.56355 * T_C,                                 # kg/m3
        "cp":  1301.38 - 0.5 * T_C,                                        # J/(kg K)
        "k":   0.5822 - 2.6e-4 * T_C,                                      # W/(m K)
        "mu":  1e-3 * 0.70645 * math.exp(1204.11348 / (T_C + 273.15)),      # Pa s
    }


def base_chloride_uncertainty() -> dict:
    """A1 Table 9 95% absolute uncertainties, SI units."""
    return dict(_BASE_U)


# =============================================================================
# Concentration conversion: mass fraction -> volume fraction
# -----------------------------------------------------------------------------
# Mixing models need VOLUME fraction; experiments report MASS fraction.
# NOTE ON THE ANCHOR PAPER: Han/B3's tabulated densities (their Table 2) are
# reproduced exactly by substituting the MASS fraction into their Eq. (2), which
# is written for volume fraction (e.g. 0.7 wt%: mass-frac gives 1749.2 kg/m3 vs
# the tabulated 1749; correct vol-frac gives 1725.8). This module uses the
# volume fraction, i.e. it deliberately DIFFERS from Han's tabulated densities.
# Consequence: Han's k (derived as k = alpha*rho*cp) inherits that density
# offset, ~+0.4% at 0.2 wt% rising to ~+3.8% at 2.0 wt%. That is small relative
# to the k band, but it is disclosed in conductivity_nf() and folded in there.
# =============================================================================
def mass_to_volume_fraction(phi_mass: float, np_: Nanoparticle,
                            rho_bf: float) -> float:
    """Convert nanoparticle mass fraction [-] to volume fraction [-]."""
    if not 0.0 <= phi_mass < 1.0:
        raise ValueError("phi_mass must be in [0, 1)")
    v_np = phi_mass / np_.rho
    v_bf = (1.0 - phi_mass) / rho_bf
    return v_np / (v_np + v_bf)


# =============================================================================
# ANCHOR DATA -- Han et al. 2022 (B3). Single source of truth for the fits.
# All loadings in wt% (not fraction). Enhancements as fractions of the base.
# -----------------------------------------------------------------------------
# cp: LIQUID region 450-550 C (Table 1 / Fig. 9b). This is the cycle's operating
#     region -- the SOLID-region series peaks at a different loading and must NOT
#     be used here. Non-monotonic: BEST of the three tested at 0.7 wt%, NEGATIVE
#     by 2.0 wt%.
#     COMMITTED FIT: piecewise-linear (see cp_enhancement). With only 3 points
#     the true continuous optimum is UNRESOLVED -- it may lie anywhere in
#     0.2-2.0 wt%. 0.7 wt% is the best-TESTED loading, not a proven maximum.
#     (For CuO in A1 the best-tested loading is 0.7 wt%; contrast the nitrate/
#     SiO2 literature whose best-tested loadings cluster nearer 1 wt%.)
#
# k : Han reports the ENDPOINTS only (+15.85% at 0.2, +39.55% at 2.0 wt%;
#     base k = 0.293 W/m.K). The 0.7 wt% point is NOT stated in the text, so it
#     is DERIVED here from the paper's own components via its Eq. (1),
#     k = alpha * rho * cp, using the tabulated 500 C densities (Table 2),
#     diffusivity ratios (Sec. 3.4) and liquid cp ratios (Table 1):
#         0.2 wt%: 1.1095 * (1726/1717) * 1.0393 = 1.1591  -> +15.91%
#         0.7 wt%: 1.1898 * (1749/1717) * 1.1051 = 1.3394  -> +33.94%   <-- derived
#         2.0 wt%: 1.3723 * (1809/1717) * 0.9647 = 1.3948  -> +39.48%
#     The two derived ENDPOINTS reproduce Han's published +15.85% and +39.55% to
#     within 0.07 percentage points, which validates the derivation; the middle
#     point is therefore used with confidence. Non-linear/saturating, monotonic.
# =============================================================================
HAN_CP_LIQUID = ((0.2, 0.0393), (0.7, 0.1051), (2.0, -0.0353))
HAN_K         = ((0.2, 0.1585), (0.7, 0.3394), (2.0, 0.3955))
HAN_PHI_MAX_WT = 2.0     # do not extrapolate the fits beyond the measured range

# Enhancement-model uncertainty (RELATIVE, applied to the enhancement E itself,
# not to the property). Measurement precision in B3 is tight (cp +/-0.001 J/gK,
# k within 4%), but the real uncertainty is whether Han's curve transfers to a
# plant fluid (different prep route, particle size, dispersion, ageing). Chloride
# cp enhancements across the literature span roughly 6-38%, which is what these
# defaults reflect. Widen them for a conservative robust run.
E_CP_REL_UNC = 0.50
E_K_REL_UNC  = 0.35


# =============================================================================
# Small linear-algebra / fitting helpers (pure Python, no dependencies)
# =============================================================================
def _solve3(A: Sequence[Sequence[float]], b: Sequence[float]) -> list:
    """Solve a 3x3 linear system by Gaussian elimination with partial pivoting."""
    M = [list(A[i]) + [b[i]] for i in range(3)]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-14:
            raise ValueError("singular system")
        M[col], M[piv] = M[piv], M[col]
        for r in range(col + 1, 3):
            f = M[r][col] / M[col][col]
            for c in range(col, 4):
                M[r][c] -= f * M[col][c]
    x = [0.0, 0.0, 0.0]
    for r in (2, 1, 0):
        s = M[r][3] - sum(M[r][c] * x[c] for c in range(r + 1, 3))
        x[r] = s / M[r][r]
    return x


def _fit_cubic_through_origin(data) -> tuple:
    """Exact cubic E(phi) = a*phi + b*phi^2 + c*phi^3 through 3 points + origin.

    Zero degrees of freedom (interpolation, not regression): it honours every
    measured point exactly but can overshoot between them.
    """
    A = [[p, p ** 2, p ** 3] for p, _ in data]
    b = [e for _, e in data]
    return tuple(_solve3(A, b))


def _fit_saturating(data) -> tuple:
    """Least-squares fit of E(phi) = A*(1 - exp(-phi/tau)).

    Monotonic and saturating BY CONSTRUCTION, so unlike a cubic it cannot invent
    a non-physical dip between the measured points. Used for k, which rises
    monotonically with loading.
    """
    best = None
    tau = 0.02
    while tau <= 5.0:
        f = [1.0 - math.exp(-p / tau) for p, _ in data]
        num = sum(fi * e for fi, (_, e) in zip(f, data))
        den = sum(fi * fi for fi in f)
        if den > 1e-15:
            A = num / den
            sse = sum((A * fi - e) ** 2 for fi, (_, e) in zip(f, data))
            if best is None or sse < best[2]:
                best = (A, tau, sse)
        tau += 0.002
    return best[0], best[1]


def _interp_linear(x: float, data) -> float:
    """Piecewise-linear interpolation through (0,0) + the measured points."""
    pts = [(0.0, 0.0)] + [tuple(d) for d in data]
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


# Fit once at import.
_CP_CUBIC = _fit_cubic_through_origin(HAN_CP_LIQUID)
_K_SAT = _fit_saturating(HAN_K)


# =============================================================================
# Enhancement models
# =============================================================================
def cp_enhancement(phi_mass_wt: float, model: str = "linear") -> float:
    """cp enhancement E(phi) [fraction] for CuO in A1, LIQUID phase.

    COMMITTED DEFAULT: model="linear" (piecewise-linear through Han's points).
    Rationale: with only 3 measured points, no fit can distinguish curve shapes,
    so the module adopts the interpolant that claims the LEAST unmeasured
    structure. Linear honours the data exactly and places its maximum at a real
    data point (0.7 wt%, the best-tested loading), asserting nothing about
    curvature between points.

    model="cubic": SENSITIVITY CASE ONLY, not the primary. A smooth exact cubic
    through the same 3 points + origin places the peak near ~1.0 wt% at ~+11.7%
    -- an INFERRED optimum between measured loadings that is a model artifact,
    not a measurement. Run it to show the result's sensitivity to fit choice,
    and report both; do not treat its inferred peak as physical. Denser cp data
    (>=4 loadings) is what would justify committing to a smooth fit.
    """
    if phi_mass_wt < 0:
        raise ValueError("loading must be >= 0")
    if model == "linear":
        return _interp_linear(phi_mass_wt, HAN_CP_LIQUID)
    if model == "cubic":
        a, b, c = _CP_CUBIC
        p = phi_mass_wt
        return a * p + b * p * p + c * p ** 3
    raise ValueError("model must be 'linear' or 'cubic'")


def k_enhancement(phi_mass_wt: float, model: str = "saturating") -> float:
    """k enhancement E_k(phi) [fraction] for CuO in A1. Monotonic, saturating."""
    if phi_mass_wt < 0:
        raise ValueError("loading must be >= 0")
    if model == "saturating":
        A, tau = _K_SAT
        return A * (1.0 - math.exp(-phi_mass_wt / tau))
    if model == "linear":
        return _interp_linear(phi_mass_wt, HAN_K)
    raise ValueError("model must be 'saturating' or 'linear'")


# =============================================================================
# Theoretical floors (used ONLY as lower band edges, never as nominals)
# =============================================================================
def k_maxwell_floor(phi_v: float, base: dict, np_: Nanoparticle) -> float:
    """Maxwell effective-medium k for dilute spheres [W/(m K)].

    Bounded by ~3*phi_v regardless of particle conductivity. At 0.7 wt% CuO
    phi_v is only ~0.0019, so Maxwell caps out near +0.6% while Han MEASURED
    ~+34%. That gap is the anomaly (nanostructure / percolation), which
    effective-medium theory has no term for -- hence floor, not nominal.
    """
    kb, kp = base["k"], np_.k
    num = kp + 2 * kb + 2 * phi_v * (kp - kb)
    den = kp + 2 * kb - phi_v * (kp - kb)
    return kb * num / den


def mu_brinkman_floor(phi_v: float, base: dict) -> float:
    """Brinkman viscosity for dilute rigid spheres [Pa s]. Lower bound only."""
    return base["mu"] / (1.0 - phi_v) ** 2.5


# =============================================================================
# Property models
# =============================================================================
def density_nf(phi_v: float, base: dict, np_: Nanoparticle) -> Prop:
    """Nanofluid density [kg/m3]: volume-weighted mixing rule (uncontested).

    Band = A1 base-salt 95% uncertainty (+/-15.27 kg/m3) scaled by the salt's
    volume share; the particle contribution is essentially exact.
    """
    rho = phi_v * np_.rho + (1.0 - phi_v) * base["rho"]
    u = _BASE_U["rho"] * (1.0 - phi_v)
    return Prop(rho, rho - u, rho + u)


def cp_nf(phi_mass: float, base: dict, np_: Nanoparticle,
          model: str = "linear") -> Prop:
    """Nanofluid specific heat [J/(kg K)]. Anchor: Han/B3 liquid-phase series.

    NOT a mixing rule. The classical mass-weighted rule predicts a DECREASE and
    is contradicted by measurement (B1 Fig. 2 shows the thermal-equilibrium model
    predicting ~0 change against a measured +14.5%). Modelled instead as
    cp_nf = cp_base(T) * (1 + E(phi)), with E from Han's LIQUID-phase data.

    Band: A1 base cp uncertainty combined with E_CP_REL_UNC on the enhancement.
    """
    _warn_if_extrapolating(phi_mass)
    E = cp_enhancement(phi_mass * 100.0, model=model)
    cp_b = base["cp"]
    u_b = _BASE_U["cp"]
    nominal = cp_b * (1.0 + E)
    lo = (cp_b - u_b) * (1.0 + E * (1.0 - E_CP_REL_UNC))
    hi = (cp_b + u_b) * (1.0 + E * (1.0 + E_CP_REL_UNC))
    if E < 0:      # above the optimum the enhancement is a penalty: keep lo<hi
        lo, hi = min(lo, hi), max(lo, hi)
    return Prop(nominal, lo, hi)


def conductivity_nf(phi_mass: float, base: dict, np_: Nanoparticle,
                    phi_v: float | None = None,
                    model: str = "saturating") -> Prop:
    """Nanofluid thermal conductivity [W/(m K)]. Anchor: Han/B3 measured k.

    Nominal from the measured enhancement; LOWER band edge floored at the Maxwell
    prediction (theory) so the band spans "theory only" to "measurement plus
    scatter". The lower edge also absorbs the density-convention offset described
    in mass_to_volume_fraction() (Han's k is inflated by ~0.4-3.8% because their
    tabulated rho used the mass fraction).
    """
    _warn_if_extrapolating(phi_mass)
    E = k_enhancement(phi_mass * 100.0, model=model)
    k_b = base["k"]
    u_b = _BASE_U["k"]
    nominal = k_b * (1.0 + E)
    lo = (k_b - u_b) * (1.0 + E * (1.0 - E_K_REL_UNC))
    hi = (k_b + u_b) * (1.0 + E * (1.0 + E_K_REL_UNC))
    if phi_v is not None:                       # never fall below theory
        lo = max(lo, k_maxwell_floor(phi_v, base, np_) - u_b)
    return Prop(nominal, lo, hi)


# Viscosity band shape. See viscosity_nf() for full justification and citations.
#
# GROUNDING (chloride-FAMILY MD analogues, replacing the earlier nitrate-based
# guess). None of these are same-salt+same-particle (that data does not exist
# for CuO/A1 -- see VISCOSITY_GAP_NOTE below), but they are same-CHEMISTRY
# (chloride) MD simulations, which is a strictly better analogue basis than
# borrowing from nitrate systems:
#
#   Tian/Zhang/Kou, SiO2/(LiCl-KCl) MD (Sol. Energy Mater. Sol. Cells,
#     doi:10.1016/j.solmat.2024... / ScienceDirect S0272884224056062):
#     at 6 wt% SiO2 -> viscosity +17.21% (average)  => ~2.9%/wt% (near-linear)
#   Al2O3/(NaCl-KCl) MD, 1100-1600 K (ResearchGate, "dual core symmetric
#     molten salt nanocomposites", 2025/2026):
#     at 7 vol% -> viscosity +34.8% to +38.6%        => ~5.3%/vol% average
#   SiO2/NaCl MD (ScienceDirect S1359431119343169):
#     shear viscosity max average increase +23.6% (loading not wt%-normalised
#     in the abstract; treated as a corroborating upper-scatter point only)
#
# Basis note: the first two studies report in different fraction bases (wt%
# vs vol%) and over different loading ranges, so "%/wt%" below is a rough,
# defensible central estimate from the LOWEST-loading, most directly
# comparable point (SiO2/LiCl-KCl, 6 wt%), not a formal regression.
MU_NOM_PER_WT = 0.029     # +2.9% per 1 wt%  (SiO2/LiCl-KCl MD, 6 wt% point)
MU_HI_PER_WT = 0.386      # +38.6% per 1 wt% (Al2O3/NaCl-KCl MD, upper value)

VISCOSITY_GAP_NOTE = (
    "No published viscosity measurement or simulation exists for CuO in the "
    "A1 (NaCl-KCl-MgCl2) ternary specifically. The band above is grounded in "
    "chloride-FAMILY MD (different salt/particle pairs), which is a stronger "
    "analogue than the nitrate cross-chemistry data used in an earlier "
    "revision of this module, but it remains an analogue, not a measurement "
    "of this system. If reviewers push on this gap, the next step is "
    "dedicated MD (Green-Kubo or NEMD) on CuO/A1 specifically, validated "
    "first against Han/B3's measured cp and k so the force field is trusted "
    "before extending it to predict viscosity."
)


def viscosity_nf(phi_v: float, base: dict, np_: Nanoparticle,
                 phi_mass: float = 0.0) -> Prop:
    """Nanofluid dynamic viscosity [Pa s]. THE WEAKEST INPUT IN THIS MODULE.

    Han/B3 does NOT measure viscosity, and there is no same-salt, same-particle
    measured mu for CuO in A1 anywhere in the literature -- see
    VISCOSITY_GAP_NOTE. The band is constructed from analogues, not fitted:

      lo      : Brinkman (dilute rigid spheres). Supported by reports of molten-
                salt nanofluids with nearly unaltered viscosity (Wei et al.,
                Renew. Energy 145 (2020) 2435-2444).
      nominal : +2.9% per 1 wt%, from chloride-family MD (SiO2/LiCl-KCl at
                6 wt% -> +17.21%; Tian/Zhang/Kou).
      hi      : +38.6% per 1 wt%, from chloride-family MD (Al2O3/NaCl-KCl at
                7 vol% -> up to +38.6%; "dual core symmetric molten salt
                nanocomposites" MD study).

    These replace an earlier, more pessimistic nitrate-analogue band: chloride-
    family MD gives materially smaller viscosity penalties than the nitrate
    cross-chemistry scatter previously used here. Still an ANALOGUE basis
    (different salt and/or particle from CuO/A1), not a measurement of this
    exact system -- declare this explicitly as a limitation. Treat mu as the
    property most in need of dedicated MD or measurement if pushed further.

    CAUTION: molten-salt nanofluids are frequently shear-thinning, so a single mu
    does not exist. Interpret this as an APPARENT viscosity at the pump/receiver
    shear rate and state that choice in the methodology.
    """
    mu_b = base["mu"]
    u_b = _BASE_U["mu"]
    floor = mu_brinkman_floor(phi_v, base)
    w = phi_mass * 100.0
    nominal = mu_b * (1.0 + MU_NOM_PER_WT * w)
    lo = max(floor - u_b, 0.0)
    hi = (mu_b + u_b) * (1.0 + MU_HI_PER_WT * w)
    nominal = max(nominal, floor)
    return Prop(nominal, lo, hi)


# =============================================================================
# Thermal diffusivity  alpha = k / (rho * cp)
# -----------------------------------------------------------------------------
# ADDED 2026-08-15 (Session G). The revised Objective 1 names thermal diffusivity
# as one of the five required property models (MASTER_PLAN.md §1). It was already
# present in this module as an INPUT -- Han/B3's measured diffusivity ratios are
# what k was derived from (see the HAN_K comment above) -- but was never an
# OUTPUT. This closes that gap.
#
# alpha is NOT an independent correlation and must not be presented as one. It is
# the DEFINED combination k/(rho*cp), so it inherits its provenance from the three
# properties it is built out of. Giving it a separate fit would let alpha drift out
# of consistency with k, rho and cp -- the one failure mode a derived property has.
#
# HAN_ALPHA below is therefore a CROSS-CHECK, not a fit target: it is Han's own
# measured diffusivity enhancement (their Sec. 3.4), the quantity our k was
# back-derived from. Round-tripping k -> alpha must return it, up to exactly one
# known offset: this module uses the VOLUME fraction for density where Han's own
# table used the mass fraction (see mass_to_volume_fraction), so the recovered
# alpha runs high by that same ~0.4-3.8%, plus whatever the saturating k FIT
# misses Han's measured k by, and by nothing else. A residual outside that
# envelope means one of rho / cp / k has drifted -- which is precisely the
# consistency this check is here to police. check_diffusivity_roundtrip() reports
# the residual so the disclosed inconsistency of THESIS_SYNTHESIS §4.8 carries a
# measured number rather than an estimate.
#
# MEASURED 2026-08-15, at 500 C (Han's own measurement temperature):
#     0.2 wt%: derived +11.67% vs Han +10.95%  ->  offset +0.65%
#     0.7 wt%: derived +20.20% vs Han +18.98%  ->  offset +1.02%
#     2.0 wt%: derived +42.74% vs Han +37.23%  ->  offset +4.01%
# The trend is monotonic in loading, as the density-convention explanation
# requires. The 2.0 wt% point sits slightly ABOVE the 3.8% density offset, and
# the excess is fully accounted for: the saturating k fit returns +39.75% against
# Han's +39.55%, worth 1.3975/1.3955 - 1 = +0.14%, giving 3.8 + 0.14 ~ 3.95%
# against the observed 4.01%. Nothing is unexplained. The 5% check ceiling is set
# just above this so a genuine drift trips it while the known offset does not.
# =============================================================================
HAN_ALPHA = ((0.2, 0.1095), (0.7, 0.1898), (2.0, 0.3723))   # Han/B3 Sec. 3.4


def alpha_enhancement_han(phi_mass_wt: float) -> float:
    """Han/B3's MEASURED diffusivity enhancement [fraction]. Cross-check only.

    Do NOT use this to build alpha -- use diffusivity_nf(), which derives alpha
    from k, rho and cp so it cannot drift out of consistency with them. This
    exists so the derivation can be checked against the data it came from.
    """
    if phi_mass_wt < 0:
        raise ValueError("loading must be >= 0")
    return _interp_linear(phi_mass_wt, HAN_ALPHA)


def diffusivity_nf(k: Prop, rho: Prop, cp: Prop) -> Prop:
    """Nanofluid thermal diffusivity alpha = k/(rho*cp) [m2/s].

    Band edges are the CONSERVATIVE combination -- alpha is largest when k is at
    its upper edge and rho*cp at their lower edges, and vice versa. This over-
    covers the true band because the three properties' errors are not independent
    (they share the base-salt correlations and the same loading), so treat it as
    an outer bound, not a distribution.
    """
    return Prop(
        nominal=k.nominal / (rho.nominal * cp.nominal),
        lo=k.lo / (rho.hi * cp.hi),
        hi=k.hi / (rho.lo * cp.lo),
    )


def check_diffusivity_roundtrip(phi_mass_wt: float, T_C: float = 500.0,
                                np_: Nanoparticle = CUO) -> dict:
    """Recover the diffusivity ENHANCEMENT from the module and compare to Han.

    Returns {'phi_wt', 'E_derived', 'E_han', 'ratio_offset_pct'}, where
    ratio_offset_pct is the deviation of the derived alpha RATIO from Han's
    measured one. Expected to be positive and of order the density-convention
    offset (~0.4% at 0.2 wt% rising to ~3.8% at 2.0 wt%); see the header note.

    Han measured at 500 C, so the default T_C is 500 -- comparing at another
    temperature adds a base-property difference that is not part of the offset
    being checked.
    """
    phi = phi_mass_wt / 100.0
    p_nf = nanofluid_properties(phi, T_C, np_=np_)
    p_b = nanofluid_properties(0.0, T_C, np_=np_)
    a_nf = diffusivity_nf(p_nf["k"], p_nf["rho"], p_nf["cp"]).nominal
    a_b = diffusivity_nf(p_b["k"], p_b["rho"], p_b["cp"]).nominal
    E_derived = a_nf / a_b - 1.0
    E_han = alpha_enhancement_han(phi_mass_wt)
    return {
        "phi_wt": phi_mass_wt,
        "E_derived": E_derived,
        "E_han": E_han,
        "ratio_offset_pct": 100.0 * ((1.0 + E_derived) / (1.0 + E_han) - 1.0),
    }


def _warn_if_extrapolating(phi_mass: float) -> None:
    if phi_mass * 100.0 > HAN_PHI_MAX_WT + 1e-9:
        raise ValueError(
            f"loading {phi_mass*100:.2f} wt% exceeds the measured range "
            f"(0-{HAN_PHI_MAX_WT} wt%). Constrain the sweep range instead of "
            f"extrapolating the enhancement fits."
        )


# =============================================================================
# Orchestrator -- public entry point
# =============================================================================
def nanofluid_properties(phi_mass: float, T_C: float,
                         np_: Nanoparticle = CUO,
                         cp_model: str = "linear",
                         k_model: str = "saturating") -> dict:
    """Return {rho, cp, k, alpha, mu} as Prop objects at (phi_mass, T_C [deg C]).

    'alpha' (thermal diffusivity, m2/s) is DERIVED from the other three, not
    independently correlated -- see diffusivity_nf(). It was added 2026-08-15 when
    the revised Objective 1 named it explicitly; every existing caller that reads
    the dict by key is unaffected by the extra entry.
    """
    base = base_chloride_properties(T_C)
    phi_v = mass_to_volume_fraction(phi_mass, np_, base["rho"])
    rho = density_nf(phi_v, base, np_)
    cp = cp_nf(phi_mass, base, np_, model=cp_model)
    k = conductivity_nf(phi_mass, base, np_, phi_v=phi_v, model=k_model)
    return {
        "rho": rho,
        "cp":  cp,
        "k":   k,
        "alpha": diffusivity_nf(k, rho, cp),
        "mu":  viscosity_nf(phi_v, base, np_, phi_mass=phi_mass),
    }


# =============================================================================
# SAM custom-HTF table export
# -----------------------------------------------------------------------------
# Column order and units confirmed directly against SAM's "Edit Material
# Properties" dialog (Trough/Tower Physical Trough or Molten Salt Power Tower
# -> HTF Fluid -> User Defined -> Edit). The dialog's 7 columns, in order, are
# exactly SAM_COLUMNS below, including the highest-risk assumption -- specific
# heat IS in kJ/(kg K), not J/(kg K). Kinematic viscosity is a required column
# (not optional); computed as mu/rho. SAM requires at least two temperature
# rows (imposed below). The enthalpy reference/datum convention inside SAM
# itself is not yet cross-checked -- see _H_REF_C.
# =============================================================================
SAM_COLUMNS = ("Temperature (C)", "Specific heat (kJ/kg-K)", "Density (kg/m3)",
               "Viscosity (Pa-s)", "Kinematic viscosity (m2/s)",
               "Conductivity (W/m-K)", "Enthalpy (J/kg)")

_H_REF_C = MELTING_POINT_C   # enthalpy datum (physically defensible choice;
                             # not yet cross-checked against SAM's internal
                             # convention -- see note above)


def _enthalpy(T_C: float, E_cp: float) -> float:
    """Integral of cp dT from the datum, J/kg. cp_base = 1301.38 - 0.5T."""
    def F(t):
        return 1301.38 * t - 0.25 * t * t
    return (1.0 + E_cp) * (F(T_C) - F(_H_REF_C))


def htf_table_rows(phi_mass: float, T_grid_C: Sequence[float],
                   np_: Nanoparticle = CUO, band: str = "nominal",
                   cp_model: str = "linear") -> list:
    """Build the SAM-format HTF property rows in memory (no file I/O).

    Returns a list of 7-tuples matching SAM_COLUMNS exactly:
    (T [C], cp [kJ/kgK], rho [kg/m3], mu [Pa s], nu [m2/s], k [W/mK], h [J/kg]).
    Used directly by both write_sam_htf_table() (CSV) and any PySAM caller
    (sequence[sequence], as required by field_fl_props / htf_props).
    """
    if len(T_grid_C) < 2:
        raise ValueError("SAM requires at least two temperature rows")
    if band not in ("nominal", "lo", "hi"):
        raise ValueError("band must be 'nominal', 'lo' or 'hi'")
    pick = {"nominal": lambda p: p.nominal,
            "lo": lambda p: p.lo,
            "hi": lambda p: p.hi}[band]

    E_cp = cp_enhancement(phi_mass * 100.0, model=cp_model)
    rows = []
    for T in T_grid_C:
        p = nanofluid_properties(phi_mass, T, np_=np_, cp_model=cp_model)
        rho = pick(p["rho"])
        mu = pick(p["mu"])
        rows.append((T, pick(p["cp"]) / 1000.0, rho, mu, mu / rho,
                     pick(p["k"]), _enthalpy(T, E_cp)))
    return rows


def write_sam_htf_table(phi_mass: float, T_grid_C: Sequence[float], path: str,
                        np_: Nanoparticle = CUO, band: str = "nominal",
                        cp_model: str = "linear") -> str:
    """Write a SAM custom-HTF table (CSV) for one loading.

    band: "nominal" | "lo" | "hi" -- write the lo/hi tables too if you want SAM
    runs at the band edges (a cheap first pass at the robust study before wiring
    a full Monte-Carlo over the bands).
    """
    rows = htf_table_rows(phi_mass, T_grid_C, np_=np_, band=band, cp_model=cp_model)
    with open(path, "w") as f:
        f.write(",".join(SAM_COLUMNS) + "\n")
        for r in rows:
            f.write(",".join(f"{v:.6g}" for v in r) + "\n")
    return path


# =============================================================================
# Self-validation
# =============================================================================
def validate(verbose: bool = True) -> bool:
    """Check the fits reproduce Han/B3's measured points. Run this in CI."""
    ok = True
    for w, e in HAN_CP_LIQUID:
        got = cp_enhancement(w, model="linear")
        good = abs(got - e) < 1e-9
        ok &= good
        if verbose:
            print(f"  cp  {w:>4} wt%: fit {100*got:+7.2f}%  Han {100*e:+7.2f}%  "
                  f"{'OK' if good else 'FAIL'}")
    for w, e in HAN_K:
        got = k_enhancement(w, model="saturating")
        good = abs(got - e) < 0.03
        ok &= good
        if verbose:
            print(f"  k   {w:>4} wt%: fit {100*got:+7.2f}%  Han {100*e:+7.2f}%  "
                  f"{'OK' if good else 'FAIL'}")

    # Diffusivity round-trip (added 2026-08-15). alpha is derived, so the test is
    # not "does it match a fit" but "does k/(rho*cp) return the alpha k came
    # from". The residual should be POSITIVE and bounded by the disclosed
    # density-convention offset; 5% is a deliberately loose ceiling that still
    # catches a real drift in any of the three constituent properties.
    for w, _ in HAN_ALPHA:
        r = check_diffusivity_roundtrip(w)
        good = -0.5 < r["ratio_offset_pct"] < 5.0
        ok &= good
        if verbose:
            print(f"  a   {w:>4} wt%: derived {100*r['E_derived']:+7.2f}%  "
                  f"Han {100*r['E_han']:+7.2f}%  "
                  f"offset {r['ratio_offset_pct']:+.2f}%  "
                  f"{'OK' if good else 'FAIL'}")
    return bool(ok)


if __name__ == "__main__":
    T = 500.0
    base = base_chloride_properties(T)
    print(f"A1 base @ {T:.0f} C: rho={base['rho']:.1f} kg/m3  "
          f"cp={base['cp']:.1f} J/kgK  k={base['k']:.4f} W/mK  "
          f"mu={base['mu']*1e3:.3f} mPa.s\n")

    print("Fit validation against Han/B3:")
    print(f"  cubic cp coeffs (a,b,c) = "
          f"({_CP_CUBIC[0]:.4f}, {_CP_CUBIC[1]:.4f}, {_CP_CUBIC[2]:.4f})")
    print(f"  saturating k fit: A={_K_SAT[0]:.4f}, tau={_K_SAT[1]:.4f} wt%")
    print("  passed\n" if validate() else "  FAILED\n")

    print(f"Properties vs loading @ {T:.0f} C (nominal [lo, hi]):")
    for w in (0.0, 0.2, 0.7, 1.0, 2.0):
        p = nanofluid_properties(w / 100.0, T)
        print(f"\n  {w:.1f} wt% CuO")
        print(f"    rho = {p['rho'].nominal:8.1f}  "
              f"[{p['rho'].lo:.1f}, {p['rho'].hi:.1f}] kg/m3")
        print(f"    cp  = {p['cp'].nominal:8.1f}  "
              f"[{p['cp'].lo:.1f}, {p['cp'].hi:.1f}] J/kgK   "
              f"(E={100*cp_enhancement(w):+.2f}%)")
        print(f"    k   = {p['k'].nominal:8.4f}  "
              f"[{p['k'].lo:.4f}, {p['k'].hi:.4f}] W/mK   "
              f"(E={100*k_enhancement(w):+.2f}%)")
        print(f"    a   = {p['alpha'].nominal*1e7:8.4f}  "
              f"[{p['alpha'].lo*1e7:.4f}, {p['alpha'].hi*1e7:.4f}] e-7 m2/s "
              f"(derived k/rho.cp)")
        print(f"    mu  = {p['mu'].nominal*1e3:8.3f}  "
              f"[{p['mu'].lo*1e3:.3f}, {p['mu'].hi*1e3:.3f}] mPa.s")

    # Results go to results/, not /tmp -- CLAUDE.md §0 rule 2, and /tmp does not
    # exist on Windows anyway (this line was the module's only portability bug).
    grid = [T_VALID_MIN_C, 500.0, 550.0, 600.0, 650.0, T_VALID_MAX_C]
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    os.makedirs(results_dir, exist_ok=True)
    out = write_sam_htf_table(
        0.007, grid, os.path.join(results_dir, "sam_htf_table_0p7wt.csv"))
    print(f"\nSAM table written -> {out}  (format confirmed vs SAM's Edit "
          f"Material Properties dialog; enthalpy reference/datum still TBC)")
