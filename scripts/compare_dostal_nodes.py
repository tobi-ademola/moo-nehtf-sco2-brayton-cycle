r"""Node-by-node error table: PySAM sCO2 cycle vs Dostal (2004) Table 10.4.

Takes the high-performance design point solved by scripts/validate_dostal.py (700 C TIT,
32 C compressor inlet, P_high 20 MPa, PR 2.6, f_rc 0.39, eta_mc/rc 0.89, eta_t 0.90) and
compares every tabulated node against the published state table, on T, P, h and s separately.

Node map (VALIDATION.md 2.3.3 -- derived from Dostal Fig 10.1, an 8-node single-recompression
layout where the recompressed stream rejoins BETWEEN the LTR and the HTR):

    MC_IN -> 1, MC_OUT -> 2, MIXER_OUT -> 3, HTR_HP_OUT -> 4,
    TURB_IN -> 5, TURB_OUT -> 6, HTR_LP_OUT -> 7, LTR_LP_OUT -> 8

Two model nodes are deliberately NOT compared here:
  * LTR_HP_OUT -- the LTR cold outlet BEFORE mixing. Dostal's node 3 is already post-mix, so
    there is no published row for it.
  * RC_OUT     -- the recompressor outlet. Dostal does not tabulate it either.
Both are validated by conservation instead (mixing-junction closure + the recompressor
isentropic relation) -- see VALIDATION.md 2.3.3a. Do not force a Dostal number onto them.

Dostal's 'id' (ideal isentropic) and 'max' (max-regeneration, effectiveness = 1) rows are
reference states, NOT model nodes, and are never used as error targets.

% error convention:
  T  -- computed on ABSOLUTE temperature, (T_sam - T_dostal) / T_dostal[K]. The node-1 value
        is 32 C, so a Celsius denominator would divide by ~32 and inflate a 0.5 K miss into
        1.6 %; the K denominator is the only honest scale here.
  P, h, s -- (sam - dostal) / dostal, native units.
Any node whose |%err| on h or s exceeds 2 % is flagged.

Inputs:  none -- imports scripts/validate_dostal.py and re-solves the base (lossless) case.
         Requires the .venv of CLAUDE.md section 1 (PySAM, numpy, CoolProp).

Run:  .\.venv\Scripts\python.exe -u .\scripts\compare_dostal_nodes.py

Outputs (CLAUDE.md section 0.2), stamped with the UTC run time and the producing git commit:
    results/dostal_node_errors_<stamp>.csv   one row per node per quantity
    results/dostal_node_errors_<stamp>.md    the console report + a paste-ready markdown
                                             table for VALIDATION.md 2.3.4
"""

import csv
import datetime
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_dostal as vd                                     # noqa: E402

REPO_ROOT = vd.REPO_ROOT
RESULTS_DIR = vd.RESULTS_DIR

# --- Dostal 2004, Table 10.4 (High-Performance design, 700 C), p.229 ----------
# node -> (Dostal point, T [C], P [kPa], h [kJ/kg], s [kJ/kg-K]).
# Transcribed in VALIDATION.md 2.3.2; conservative-turbomachinery columns.
DOSTAL_10_4 = {
    "MC_IN":      (1,  32.00,  7692.31,  306.67, 1.3478),
    "MC_OUT":     (2,  61.10, 20000.00,  327.26, 1.3546),
    "MIXER_OUT":  (3, 159.88, 19990.22,  539.07, 1.9168),
    "HTR_HP_OUT": (4, 531.33, 19944.56, 1012.03, 2.7132),
    "TURB_IN":    (5, 700.00, 19814.56, 1223.34, 2.9529),
    "TURB_OUT":   (6, 578.31,  7929.22, 1078.95, 2.9719),
    "HTR_LP_OUT": (7, 169.85,  7802.64,  605.98, 2.2212),
    "LTR_LP_OUT": (8,  71.05,  7704.93,  480.96, 1.9020),
}

# Model state-point index for each node, from vd.NODES ("CODE  description" entries).
NODE_INDEX = {nm.split(None, 1)[0]: i for i, nm in enumerate(vd.NODES)}

# Nodes with no published row -- validated by conservation, not lookup (VALIDATION.md 2.3.3a).
UNTABULATED = ("LTR_HP_OUT", "RC_OUT")

FLAG_PCT = 2.0          # flag |%err| above this on h or s
ETA_TARGET_PCT = 51.27  # Dostal Table 10.1, High-Performance, conservative turbomachinery


def pct_error(sam, dostal, denom=None):
    """Signed % error. denom overrides the divisor (used to put T on an absolute scale)."""
    return 100.0 * (sam - dostal) / (dostal if denom is None else denom)


def build_rows(T, P_kPa, h, s):
    """One row per (node, quantity). Returns the row list in Dostal point order."""
    rows = []
    for node, (pt, T_d, P_d, h_d, s_d) in sorted(DOSTAL_10_4.items(), key=lambda kv: kv[1][0]):
        i = NODE_INDEX[node]
        quantities = [
            # name,      unit,        dostal, pysam,      % error denominator
            ("T", "C",        T_d,    T[i],      T_d + 273.15),   # absolute scale -- see header
            ("P", "kPa",      P_d,    P_kPa[i],  None),
            ("h", "kJ/kg",    h_d,    h[i],      None),
            ("s", "kJ/kg-K",  s_d,    s[i],      None),
        ]
        for name, unit, d_val, sam_val, denom in quantities:
            err = pct_error(sam_val, d_val, denom)
            flagged = name in ("h", "s") and abs(err) > FLAG_PCT
            rows.append({
                "dostal_point": pt, "node": node, "quantity": name, "unit": unit,
                "dostal": d_val, "pysam": sam_val, "abs_error": sam_val - d_val,
                "pct_error": err, "flagged": "FLAG" if flagged else "",
            })
    return rows


def print_table(rows):
    print("%-4s %-11s %-4s %-10s %12s %12s %12s %10s  %s"
          % ("pt", "node", "qty", "unit", "Dostal", "PySAM", "abs error", "% error", "flag"))
    print("-" * 104)
    last = None
    for r in rows:
        if last is not None and r["node"] != last:
            print()
        last = r["node"]
        print("%-4d %-11s %-4s %-10s %12.4f %12.4f %+12.4f %+9.3f %%  %s"
              % (r["dostal_point"], r["node"], r["quantity"], r["unit"],
                 r["dostal"], r["pysam"], r["abs_error"], r["pct_error"], r["flagged"]))


def md_table(rows):
    """Paste-ready markdown for VALIDATION.md 2.3.4."""
    out = ["| Dostal pt | Node | Quantity | Dostal | PySAM | Abs error | % error | Flag |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| %d | `%s` | %s (%s) | %.4f | %.4f | %+.4f | %+.3f %% | %s |"
                   % (r["dostal_point"], r["node"], r["quantity"], r["unit"],
                      r["dostal"], r["pysam"], r["abs_error"], r["pct_error"],
                      "**FLAG**" if r["flagged"] else ""))
    return "\n".join(out)


def summarise(rows, eta_pct):
    """Per-quantity worst case, the flag list, and the efficiency comparison."""
    print("\n" + "=" * 104)
    print("SUMMARY")
    print("=" * 104)

    print("\nworst |%% error| by quantity (across the %d compared nodes):" % len(DOSTAL_10_4))
    for q in ("T", "P", "h", "s"):
        sel = [r for r in rows if r["quantity"] == q]
        worst = max(sel, key=lambda r: abs(r["pct_error"]))
        rms = float(np.sqrt(np.mean([r["pct_error"] ** 2 for r in sel])))
        print("   %-2s   worst %+8.3f %%  at %-11s (pt %d)      RMS %6.3f %%"
              % (q, worst["pct_error"], worst["node"], worst["dostal_point"], rms))

    flagged = [r for r in rows if r["flagged"]]
    print("\nnodes flagged (|%%err| > %.0f %% on h or s): %s"
          % (FLAG_PCT, "NONE" if not flagged else ""))
    for r in flagged:
        print("   %-11s (pt %d)  %s  Dostal %10.4f  PySAM %10.4f  %+8.3f %%"
              % (r["node"], r["dostal_point"], r["quantity"],
                 r["dostal"], r["pysam"], r["pct_error"]))

    err = pct_error(eta_pct, ETA_TARGET_PCT)
    print("\neta_thermal   Dostal %6.2f %%   PySAM %6.2f %%   abs %+.3f pp   %% error %+.3f %%"
          % (ETA_TARGET_PCT, eta_pct, eta_pct - ETA_TARGET_PCT, err))
    return flagged, err


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = vd.git_commit()

    # Base (lossless) case -- PR is exactly 2.6, so P_high/P_low match Dostal's stated values
    # rather than drifting with an assumed dP allocation. Keep the model referenced: handing a
    # bare Outputs around segfaults (CLAUDE.md 4.8).
    m, note = vd.solve()
    o = m.Outputs
    T = np.array(o.T_state_points)
    P_kPa = np.array(o.P_state_points) * 1000.0        # model reports MPa
    h = np.array(o.h_state_points)
    s = np.array(o.s_state_points)
    eta_pct = 100.0 * o.eta_thermal_calc

    md_path = os.path.join(RESULTS_DIR, "dostal_node_errors_%s.md" % stamp)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# sCO2 cycle -- node-by-node error vs Dostal (2004) Table 10.4\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/compare_dostal_nodes.py` |\n"
                 "| run (UTC) | %s |\n| git commit | `%s` |\n"
                 "| case | high-performance 700 C, base (lossless) |\n"
                 "| source table | Dostal 2004 Table 10.4, p.229 (conservative) |\n\n```\n"
                 % (stamp, commit))
        real_stdout = sys.stdout
        sys.stdout = vd.Tee(real_stdout, fh)
        try:
            print("=" * 104)
            print("DOSTAL 2004 TABLE 10.4 (HIGH-PERFORMANCE, 700 C) -- NODE-BY-NODE ERROR")
            print("=" * 104)
            if note:
                print("  !! " + note.replace("\n", "\n  ") + "\n")
            print("  model: TIT %.1f C, MC inlet %.1f C, P_high %.1f MPa, PR %.2f, f_rc %.2f,"
                  % (vd.T_TURB_IN_C, vd.T_MC_IN_C, vd.P_HIGH_MPA, vd.PRESSURE_RATIO,
                     o.recomp_frac))
            print("         eta_mc %.2f / eta_rc %.2f / eta_t %.2f, recup effectiveness %.2f,"
                  % (vd.ETA_MC, vd.ETA_RC, vd.ETA_T, vd.RECUP_EFF))
            print("         zero pressure loss (so PR is exactly %.2f)" % vd.PRESSURE_RATIO)
            print("  h and s below are ssc's OWN values, not re-derived -- this is a")
            print("  PySAM-vs-Dostal comparison. (validate_dostal.py separately shows ssc")
            print("  agrees with CoolProp to 1.6e-04 kJ/kg in h, 3.4e-07 kJ/kg-K in s, and")
            print("  the two share a reference state: Dostal s1 = 1.3478 vs ssc %.5f.)\n" % s[0])
            print("  NOT compared here (no Dostal row; see VALIDATION.md 2.3.3a): %s\n"
                  % ", ".join(UNTABULATED))

            rows = build_rows(T, P_kPa, h, s)
            print_table(rows)
            flagged, eta_err = summarise(rows, eta_pct)

            print("\n" + "=" * 104)
            print("MARKDOWN (paste into VALIDATION.md 2.3.4)")
            print("=" * 104)
            print(md_table(rows))
        finally:
            sys.stdout = real_stdout
        fh.write("```\n")

    csv_path = os.path.join(RESULTS_DIR, "dostal_node_errors_%s.csv" % stamp)
    vd.write_csv(csv_path, rows)

    print("\nresults written (commit %s):" % commit)
    for p in (md_path, csv_path):
        print("   %s" % os.path.relpath(p, REPO_ROOT).replace("\\", "/"))


if __name__ == "__main__":
    main()
