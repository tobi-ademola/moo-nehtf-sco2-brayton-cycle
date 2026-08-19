r"""OBJECTIVE 1 EVIDENCE ARTIFACT -- the five property models, with provenance.

WHY THIS EXISTS. The supervisor's revised Objective 1 (2026-08-15, MASTER_PLAN.md §1) asks for
"temperature- and concentration-dependent thermophysical property models (density, specific heat,
thermal conductivity, thermal diffusivity, and viscosity) ... with documented provenance for each
correlation." Two things follow that the project did not previously have on disk:

  1. THERMAL DIFFUSIVITY is now a named output. `scripts/nanofluid_properties.py` carried it only
     as an INPUT -- Han/B1's measured diffusivity ratios are what its k was back-derived from --
     and never returned it. That gap is closed (`diffusivity_nf`), and the round-trip
     k -> alpha -> Han must close for the derivation to be self-consistent. This script is where
     that check lands on disk instead of scrolling past in a terminal.

  2. PROVENANCE PER CORRELATION is a deliverable, not annotation. The provenance lived in source
     comments and PROPERTIES.md; this emits it alongside the numbers it produced, in one
     timestamped artifact a thesis chapter or an examiner can read without reading the source.

WHAT IT DOES. No solver, no PySAM, no network -- pure evaluation of the property module, in about
a second. Emits (a) the provenance table, (b) the five properties over the full 450-700 C validity
window at the loadings of interest, and (c) the diffusivity round-trip against Han's measured
enhancement, with its expected offset explained rather than merely tolerated.

READ THE OFFSET COLUMN, NOT JUST THE PASS FLAG. The derived alpha is EXPECTED to sit above Han's
measured value, because this module uses the volume fraction for density where Han's own table
used the mass fraction (a disclosed, deliberate divergence -- see mass_to_volume_fraction). A
residual near zero would mean the density convention had silently reverted; a large one would mean
rho, cp or k has drifted. Both directions are informative.

Inputs:  scripts/nanofluid_properties.py only. No .venv packages beyond the stdlib are needed
         (the module is pure Python), though running it under the project .venv is fine.

Run:  .\.venv\Scripts\python.exe -u .\scripts\report_htf_properties.py

Outputs: results/htf_properties_<stamp>.md    provenance + property tables + round-trip
         results/htf_properties_<stamp>.csv   the property table, machine-readable
"""

import datetime
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nanofluid_properties as nfp  # noqa: E402

# The loadings to report. 0.0 is not decoration -- Objective 4 needs the base-salt control at
# every swept point, so the phi = 0 column is half of every comparison downstream.
LOADINGS_WT = (0.0, 0.2, 0.7, 1.0, 2.0)

# Full stated validity window of the B0 correlation set (nanofluid_properties.py).
T_GRID_C = (450.0, 500.0, 550.0, 600.0, 650.0, 700.0)

# One row per correlation: (property, symbol, unit, form, primary anchor, status).
PROVENANCE = (
    ("Density", "rho", "kg/m3", "linear in T; volume-fraction mixing rule",
     "B0 set Table 9 (Wang et al., ASME J. Sol. Energy Eng. 143(4):041005, 2021) "
     "+ CuO rho back-solved from Han/B1 Table 2",
     "anchored; deliberate volume-fraction divergence from Han disclosed"),
    ("Specific heat", "cp", "J/(kg K)", "linear in T; piecewise-linear in phi",
     "Han et al. 2022, Sol. Energy Mater. Sol. Cells 234:111432 (liquid region, 450-550 C)",
     "anchored at 3 measured loadings; NON-MONOTONIC, peak at 0.7 wt% of those tested"),
    ("Thermal conductivity", "k", "W/(m K)", "linear in T; saturating in phi",
     "Han et al. 2022 endpoints (+15.85% at 0.2, +39.55% at 2.0 wt%); 0.7 wt% point "
     "derived from the paper's own alpha, rho and cp via its Eq. (1)",
     "anchored; Maxwell floor used as the lower band edge only"),
    ("Thermal diffusivity", "alpha", "m2/s", "DERIVED: alpha = k/(rho*cp)",
     "inherits provenance from k, rho and cp; cross-checked against Han et al. 2022 Sec. 3.4 "
     "measured diffusivity ratios (+10.95% / +18.98% / +37.23%)",
     "derived, not independently correlated -- see the round-trip below"),
    ("Dynamic viscosity", "mu", "Pa s", "exponential in T; linear in phi",
     "MD-filled. Base-salt anchors: Jiang 2024, Xu 2022/2023, De Stefanis 2024, Lu 2021. "
     "Loading dependence from chloride-FAMILY MD analogues (Tian 2024 SiO2/LiCl-KCl; "
     "Al2O3/NaCl-KCl)",
     "WEAKEST INPUT -- no measured mu exists for CuO in any chloride salt; declared, banded"),
)


def git_commit():
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
        d = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
        return h + ("-dirty" if d else "")
    except Exception:
        return "unknown"


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = git_commit()
    md = []
    csv = ["phi_wt,T_C,rho_kg_m3,cp_J_kgK,k_W_mK,alpha_m2_s,mu_Pa_s,"
           "rho_lo,rho_hi,cp_lo,cp_hi,k_lo,k_hi,alpha_lo,alpha_hi,mu_lo,mu_hi"]

    def say(line=""):
        # The .md file is written UTF-8 and keeps the real characters; the Windows
        # console is cp1252 and raises UnicodeEncodeError on any of them. Print a
        # transliteration rather than degrading the artifact to ASCII -- losing the
        # subscripts in a thesis-facing table to satisfy a terminal codec would be
        # the wrong trade.
        print(line.encode("ascii", "replace").decode("ascii"), flush=True)
        md.append(line)

    say("# Nano-HTF thermophysical property models — Objective 1 evidence")
    say()
    say("| | |")
    say("|---|---|")
    say("| script | `scripts/report_htf_properties.py` |")
    say("| module under report | `scripts/nanofluid_properties.py` |")
    say("| generated (UTC) | %s |" % stamp)
    say("| git commit | `%s` |" % commit)
    say("| system | CuO in NaCl–KCl–MgCl₂ ternary chloride eutectic (B0) |")
    say("| validity | %.0f–%.0f °C stated; ≤ %.1f wt%% (fits not extrapolated beyond Han) |"
        % (nfp.T_VALID_MIN_C, nfp.T_VALID_MAX_C, nfp.HAN_PHI_MAX_WT))
    say("| melting point | %.1f °C — the cold-tank floor constraint |" % nfp.MELTING_POINT_C)
    say()

    # ---------------------------------------------------------------- provenance
    say("## 1. Provenance per correlation")
    say()
    say("Objective 1 requires documented provenance for each correlation, so this table is a "
        "deliverable rather than a working note.")
    say()
    say("| Property | Symbol | Unit | Functional form | Primary anchor | Status |")
    say("|---|---|---|---|---|---|")
    for name, sym, unit, form, anchor, status in PROVENANCE:
        say("| %s | %s | %s | %s | %s | %s |" % (name, sym, unit, form, anchor, status))
    say()
    say("> **The viscosity gap, stated rather than buried.** %s"
        % nfp.VISCOSITY_GAP_NOTE.replace("\n", " "))
    say()
    say("> **Particle size, stated rather than buried.** %s"
        % nfp.PARTICLE_SIZE_NOTE.replace("\n", " "))
    say()

    # ---------------------------------------------------------------- properties
    say("## 2. The five properties over the validity window")
    say()
    say("Nominal values; band edges are in the CSV. α is derived as k/(ρ·cp).")
    say()
    for phi_wt in LOADINGS_WT:
        say("### %.1f wt%% CuO" % phi_wt)
        say()
        say("| T (°C) | ρ (kg/m³) | cp (J/kg·K) | k (W/m·K) | α (×10⁻⁷ m²/s) | μ (mPa·s) |")
        say("|---|---|---|---|---|---|")
        for T in T_GRID_C:
            p = nfp.nanofluid_properties(phi_wt / 100.0, T)
            say("| %.0f | %.1f | %.1f | %.4f | %.4f | %.3f |"
                % (T, p["rho"].nominal, p["cp"].nominal, p["k"].nominal,
                   p["alpha"].nominal * 1e7, p["mu"].nominal * 1e3))
            csv.append(",".join("%.6g" % v for v in (
                phi_wt, T, p["rho"].nominal, p["cp"].nominal, p["k"].nominal,
                p["alpha"].nominal, p["mu"].nominal,
                p["rho"].lo, p["rho"].hi, p["cp"].lo, p["cp"].hi,
                p["k"].lo, p["k"].hi, p["alpha"].lo, p["alpha"].hi,
                p["mu"].lo, p["mu"].hi)))
        say()

    # ---------------------------------------------------------------- round-trip
    say("## 3. Thermal-diffusivity round-trip against Han et al. 2022")
    say()
    say("α is **derived**, not fitted, so the meaningful test is whether k/(ρ·cp) returns the "
        "diffusivity that k was itself back-derived from. Evaluated at 500 °C, Han's own "
        "measurement temperature.")
    say()
    say("| φ (wt%) | α enhancement, derived | α enhancement, Han measured | offset | expected? |")
    say("|---|---|---|---|---|")
    all_ok = True
    for phi_wt, _ in nfp.HAN_ALPHA:
        r = nfp.check_diffusivity_roundtrip(phi_wt)
        ok = -0.5 < r["ratio_offset_pct"] < 5.0
        all_ok &= ok
        say("| %.1f | %+.2f %% | %+.2f %% | %+.2f %% | %s |"
            % (phi_wt, 100 * r["E_derived"], 100 * r["E_han"],
               r["ratio_offset_pct"], "yes" if ok else "**NO — investigate**"))
    say()
    say("**Interpretation.** The offset is expected to be positive and to grow with loading: this "
        "module uses the *volume* fraction for density where Han's tabulated densities used the "
        "*mass* fraction, a disclosed divergence worth roughly +0.4 % at 0.2 wt% rising to "
        "+3.8 % at 2.0 wt%. The residual above that at 2.0 wt% is the saturating k fit "
        "returning +39.75 % against Han's measured +39.55 %, worth a further +0.14 %. Nothing "
        "in the column is unaccounted for.")
    say()
    say("**Module self-validation (cp and k fits + this round-trip): %s**"
        % ("PASSED" if (nfp.validate(verbose=False) and all_ok) else "FAILED"))
    say()

    # ------------------------------------------------------------- particle size
    say("## 4. Particle size — the declared-invariance position (D6)")
    say()
    say("`DECISIONS.md` **D6** (2026-08-19) represents particle size as a *declared "
        "size-invariant nominal over an evidenced band*, with a named size-transfer "
        "uncertainty. Objective 3 sweeps d_p, so a reader will meet a flat d_p response "
        "surface and should be able to check here that the flatness is a transcribed "
        "measurement and not an unrepresented variable. The table below is that check: "
        "nominals identical across the band, bands wider than at the unasserted reference.")
    say()
    say("| d_p (nm) | cp nominal (J/kg·K) | cp band width | k nominal (W/m·K) | k band width | "
        "α nominal (10⁻⁷ m²/s) |")
    say("|---|---|---|---|---|---|")
    T_dp, phi_dp = 500.0, 0.7
    ref = nfp.nanofluid_properties(phi_dp / 100.0, T_dp)
    rows = [(None, ref)]
    for d in (nfp.D_P_MIN_NM, 10.0, 30.0, nfp.D_P_MAX_NM):
        rows.append((d, nfp.nanofluid_properties(phi_dp / 100.0, T_dp, d_p_nm=d)))
    nominals_flat = True
    for d, p in rows:
        nominals_flat &= (abs(p["cp"].nominal - ref["cp"].nominal) < 1e-12
                          and abs(p["k"].nominal - ref["k"].nominal) < 1e-12)
        say("| %s | %.1f | %.1f | %.4f | %.4f | %.4f |"
            % ("*unasserted*" if d is None else "%.0f" % d,
               p["cp"].nominal, p["cp"].hi - p["cp"].lo,
               p["k"].nominal, p["k"].hi - p["k"].lo,
               p["alpha"].nominal * 1e7))
    say()
    say("Evaluated at %.0f °C and %.1f wt%%. The **nominal columns are constant by decision, "
        "not by accident**: %s. The *unasserted* row is the module's pre-D6 behaviour — naming "
        "no diameter means \"Han's fluid at Han's own diameter\", which claims no transfer and "
        "so carries no transfer penalty."
        % (T_dp, phi_dp,
           "verified identical to <1e-12 across the band" if nominals_flat
           else "**FAILED — a nominal moved with d_p, which contradicts D6**"))
    say()
    say("**The honest caveat on magnitude.** The size term (±%.1f %%, from Tiznobaik & Shin's own "
        "measured scatter) is combined in quadrature with an enhancement-transfer uncertainty of "
        "±%.0f %% on cp and ±%.0f %% on k, so it widens the cp band by only ~%.1f %%. Particle "
        "size is therefore **not** a material contributor to the uncertainty envelope — the "
        "point of D6 is that d_p is now a *validated, range-guarded, separately-attributable* "
        "input whose flat nominal is citable, not that the band moved."
        % (100 * nfp.E_DP_REL_UNC, 100 * nfp.E_CP_REL_UNC, 100 * nfp.E_K_REL_UNC,
           100 * ((rows[1][1]["cp"].hi - rows[1][1]["cp"].lo)
                  / (ref["cp"].hi - ref["cp"].lo) - 1.0)))
    say()
    say("**Out-of-band behaviour.** A diameter outside %.0f–%.0f nm raises `ValueError` rather "
        "than extrapolating, mirroring the ≤ %.1f wt%% loading guard. The declared sweep range "
        "is a constraint of the study; a sweep that exceeds it would publish a size-invariance "
        "claim over diameters nobody has measured."
        % (nfp.D_P_MIN_NM, nfp.D_P_MAX_NM, nfp.HAN_PHI_MAX_WT))
    say()
    all_ok &= nominals_flat
    say("---")
    say()
    say("Generated by `scripts/report_htf_properties.py` at commit `%s`." % commit)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    md_path = os.path.join(RESULTS_DIR, "htf_properties_%s.md" % stamp)
    csv_path = os.path.join(RESULTS_DIR, "htf_properties_%s.csv" % stamp)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    with open(csv_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(csv) + "\n")
    print("\nwrote %s" % os.path.relpath(md_path, REPO_ROOT).replace("\\", "/"))
    print("wrote %s" % os.path.relpath(csv_path, REPO_ROOT).replace("\\", "/"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
