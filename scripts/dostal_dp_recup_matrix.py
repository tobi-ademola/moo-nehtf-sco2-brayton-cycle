r"""DIAGNOSTIC (not a baseline): can the two flagged nodes be fixed without losing the eta match?

VALIDATION.md 2.3.4 left one open physics question. Our model reproduces Dostal's eta = 51.27 % at
recuperator effectiveness ~0.9467 -- LOOSER than his own ~10 K HTR approach implies -- while its
HTR moves 8 % less heat than his, displacing MIXER_OUT and HTR_LP_OUT by ~5 % in h. That is two
compensating errors, not one:

    our recuperators are LOOSER than his   -> pushes eta DOWN
    our cycle is LOSSLESS, his is not      -> pushes eta UP

So tightening the recuperators ALONE should overshoot 51.27 %, and adding pressure loss ALONE
should undershoot. Only doing both should land on his eta AND his nodes. This script runs that
2x2 to test the claim rather than asserting it.

    A  baseline        eps = 0.95 both, lossless          <-- the currently pinned case
    B  tighter only    10 K approach both, lossless
    C  dP only         eps = 0.95 both, Dostal's dP
    D  both            10 K approach both, Dostal's dP    <-- the hypothesis

THE PRESSURE LOSSES ARE DOSTAL'S OWN, for this exact design. They are NOT the Basic-design values
of Table 10.6 (85.95 / 27.38 / 109.35 / 11.35 kPa) that VALIDATION.md 2.3.5 offers as a fallback:
Table 10.4 tabulates the pressure at every node of the High-Performance case, so each heat
exchanger's loss is just the difference between consecutive nodes -- see DOSTAL_DP below. The PHX
difference comes out at exactly 130.00 kPa, matching the "primary system dP 130 kPa" of Table 10.1,
which confirms the reading.

Likewise the 10 K approach is read off Table 10.4, not assumed: HTR cold end is node 7 minus node 3
= 169.85 - 159.88 = 9.97 K, and LTR cold end is node 8 minus node 2 = 71.05 - 61.10 = 9.95 K.

OUTCOME: case F was ADOPTED as the validated baseline on 2026-08-13 (VALIDATION.md 2.3.4a), so
validate_dostal.py now runs it by default and case A survives only as a regression anchor. This
script is retained as the EVIDENCE for that decision and as a regression test of it -- re-running
it should still show F winning on both eta and node agreement. Every case here sets all four
knobs explicitly, so it stays correct regardless of what build()'s defaults become.

Inputs:  none. Requires the .venv of CLAUDE.md section 1 (PySAM, numpy, CoolProp).

Run:  .\.venv\Scripts\python.exe -u .\scripts\dostal_dp_recup_matrix.py

Outputs (CLAUDE.md section 0.2):
    results/dostal_dp_recup_matrix_<stamp>.md    console report
    results/dostal_dp_recup_matrix_<stamp>.csv   one row per case per metric
"""

import datetime
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_dostal as vd                                     # noqa: E402
import compare_dostal_nodes as cmpn                              # noqa: E402

REPO_ROOT = vd.REPO_ROOT
RESULTS_DIR = vd.RESULTS_DIR

# --- Dostal's own per-HX pressure loss, derived from Table 10.4 node pressures ---------------
# Each entry: (loss [kPa], inlet pressure [kPa]) -> ssc wants the loss as a FRACTION of inlet.
#   LTR_HP  node 2 -> 3 : 20000.00 - 19990.22 =   9.78 kPa
#   HTR_HP  node 3 -> 4 : 19990.22 - 19944.56 =  45.66 kPa
#   PHX     node 4 -> 5 : 19944.56 - 19814.56 = 130.00 kPa  <-- Table 10.1's 130 kPa exactly
#   HTR_LP  node 6 -> 7 :  7929.22 -  7802.64 = 126.58 kPa
#   LTR_LP  node 7 -> 8 :  7802.64 -  7704.93 =  97.71 kPa
#   cooler  node 8 -> 1 :  7704.93 -  7692.31 =  12.62 kPa
# These now live in validate_dostal.py, since case F was adopted as the baseline and they are
# part of it. Imported rather than duplicated so there is one source of truth.
DOSTAL_DP_KPA = vd.DOSTAL_DP_KPA
DOSTAL_DP_FRAC = vd.DOSTAL_DP_FRAC
LOSSLESS = {k: 0.0 for k in DOSTAL_DP_FRAC}

# Dostal's recuperator approach temperatures, read off Table 10.4 (see module docstring).
DOSTAL_MIN_DT = 10.0

# f = 0.4097 is the recompressed fraction Dostal's Table 10.4 state points actually encode --
# see scripts/check_dostal_table_consistency.py. Table 10.1 states 0.39 for this design, and the
# two disagree, so cases E and F test whether that (not recuperator duty split) is what displaces
# MIXER_OUT and HTR_LP_OUT.
F_IMPLIED = vd.F_RECOMP           # 0.4097
F_STATED = vd.F_RECOMP_STATED     # 0.39

# EVERY case spells out all four knobs. build()'s defaults are now case F, so relying on them
# would silently turn cases A-E into variants of F and destroy the comparison.
def case(f, code, dp, eff=0.95):
    return dict(f_recomp=f, recup_code=code, recup_min_dT=DOSTAL_MIN_DT, dp=dp, recup_eff=eff)


CASES = [
    ("A", "legacy: eps 0.95, lossless, f 0.39", case(F_STATED, 3, LOSSLESS)),
    ("B", "tighter only: 10 K approach, lossless", case(F_STATED, 2, LOSSLESS)),
    ("C", "dP only: eps 0.95, Dostal dP", case(F_STATED, 3, DOSTAL_DP_FRAC)),
    ("D", "BOTH: 10 K approach + Dostal dP", case(F_STATED, 2, DOSTAL_DP_FRAC)),
    ("E", "f = 0.4097 only (table-implied), eps 0.95", case(F_IMPLIED, 3, LOSSLESS)),
    ("F", "ADOPTED: f 0.4097 + 10 K + Dostal dP", case(F_IMPLIED, 2, DOSTAL_DP_FRAC)),
]

FLAGGED = ("MIXER_OUT", "HTR_LP_OUT")     # the two nodes VALIDATION.md 2.3.4 flagged


def metrics(m):
    """Everything the comparison needs from one solved case."""
    o = m.Outputs
    T = np.array(o.T_state_points)
    P_kPa = np.array(o.P_state_points) * 1000.0
    h = np.array(o.h_state_points)
    s = np.array(o.s_state_points)
    rows = cmpn.build_rows(T, P_kPa, h, s)       # reuse the TEST 2 error machinery

    def err(node, qty):
        return next(r["pct_error"] for r in rows
                    if r["node"] == node and r["quantity"] == qty)

    def rms(qty):
        return float(np.sqrt(np.mean([r["pct_error"] ** 2 for r in rows
                                      if r["quantity"] == qty])))

    i = cmpn.NODE_INDEX
    return {
        "eta_pct": 100.0 * o.eta_thermal_calc,
        "eta_err_pp": 100.0 * o.eta_thermal_calc - cmpn.ETA_TARGET_PCT,
        "mixer_h_pct": err("MIXER_OUT", "h"),
        "htrlp_h_pct": err("HTR_LP_OUT", "h"),
        "rms_h_pct": rms("h"),
        "rms_s_pct": rms("s"),
        "rms_P_pct": rms("P"),
        "worst_h_pct": max((r["pct_error"] for r in rows if r["quantity"] == "h"), key=abs),
        # HTR cold-end approach: hot outlet (HTR_LP_OUT) minus cold inlet (MIXER_OUT).
        "htr_approach_K": T[i["HTR_LP_OUT"]] - T[i["MIXER_OUT"]],
        "htr_duty_kJkg": h[i["HTR_HP_OUT"]] - h[i["MIXER_OUT"]],
        "eff_HTR": o.eff_HTR,
        "eff_LTR": o.eff_LTR,
        # Count DISTINCT flagged nodes, not (node, quantity) pairs -- h and s are flagged
        # separately, so pair-counting would top out at 4 and read as twice the real damage.
        "n_flagged_nodes": len({r["node"] for r in rows if r["flagged"]}),
        "n_flagged_rows": sum(1 for r in rows if r["flagged"]),
        "rows": rows,
    }


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = vd.git_commit()

    md_path = os.path.join(RESULTS_DIR, "dostal_dp_recup_matrix_%s.md" % stamp)
    csv_rows = []
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# Diagnostic: recuperator tightness x pressure loss (2x2)\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/dostal_dp_recup_matrix.py` |\n"
                 "| run (UTC) | %s |\n| git commit | `%s` |\n"
                 "| status | DIAGNOSTIC -- does not change any pinned baseline |\n\n```\n"
                 % (stamp, commit))
        real_stdout = sys.stdout
        sys.stdout = vd.Tee(real_stdout, fh)
        try:
            print("=" * 108)
            print("DIAGNOSTIC 2x2 -- RECUPERATOR TIGHTNESS x PRESSURE LOSS")
            print("=" * 108)
            print("Dostal's own per-HX pressure loss, derived from Table 10.4 node pressures:")
            for k, (loss, p_in) in DOSTAL_DP_KPA.items():
                print("   %-7s %7.2f kPa on %9.2f kPa inlet  ->  frac %.6f"
                      % (k, loss, p_in, DOSTAL_DP_FRAC[k]))
            print("   (PHX comes out at exactly 130.00 kPa = Table 10.1's primary-system dP.)")
            print("\nDostal's approach temps, also from Table 10.4:")
            print("   HTR cold end  node7 - node3 = 169.85 - 159.88 = 9.97 K")
            print("   LTR cold end  node8 - node2 =  71.05 -  61.10 = 9.95 K   -> using 10 K\n")

            results = {}
            for tag, label, kw in CASES:
                m, note = vd.solve(**kw)
                r = metrics(m)
                results[tag] = r
                print("-" * 108)
                print("CASE %s -- %s" % (tag, label))
                print("-" * 108)
                if note:
                    print("  !! " + note.replace("\n", "\n  "))
                print("   eta_thermal      %7.3f %%   (%+.3f pp vs Dostal 51.27 %%)"
                      % (r["eta_pct"], r["eta_err_pp"]))
                print("   eff_HTR/eff_LTR  %7.5f / %.5f      HTR approach %6.2f K "
                      "(Dostal 9.97)" % (r["eff_HTR"], r["eff_LTR"], r["htr_approach_K"]))
                print("   HTR duty         %7.2f kJ/kg  (Dostal 472.96)" % r["htr_duty_kJkg"])
                print("   MIXER_OUT  h err %+7.3f %%      HTR_LP_OUT h err %+7.3f %%"
                      % (r["mixer_h_pct"], r["htrlp_h_pct"]))
                print("   RMS h %6.3f %%   RMS s %6.3f %%   RMS P %6.3f %%"
                      % (r["rms_h_pct"], r["rms_s_pct"], r["rms_P_pct"]))
                print("   flagged nodes remaining: %d of 8   (%d of 32 node-quantity pairs)"
                      % (r["n_flagged_nodes"], r["n_flagged_rows"]))
                csv_rows.append({"case": tag, "description": label,
                                 **{k: v for k, v in r.items() if k != "rows"}})

            # ---------------- verdict -------------------------------------------
            print("\n" + "=" * 108)
            print("SUMMARY")
            print("=" * 108)
            print("%-5s %-38s %9s %9s %10s %10s %8s %7s"
                  % ("case", "configuration", "eta %", "d pp", "MIXER h%", "HTRLP h%",
                     "RMS h%", "flags"))
            print("-" * 108)
            for tag, label, _ in CASES:
                r = results[tag]
                print("%-5s %-38s %9.3f %+9.3f %+10.3f %+10.3f %8.3f %7d"
                      % (tag, label, r["eta_pct"], r["eta_err_pp"], r["mixer_h_pct"],
                         r["htrlp_h_pct"], r["rms_h_pct"], r["n_flagged_nodes"]))

            a, b, c, d = (results[t] for t in "ABCD")
            e, g = results["E"], results["F"]
            print("\nDoes the compensating-error hypothesis hold?")
            print("   tightening alone (A->B) moves eta %+.3f pp  -> %s"
                  % (b["eta_pct"] - a["eta_pct"],
                     "UP, as predicted" if b["eta_pct"] > a["eta_pct"] else "DOWN, contradicts"))
            print("   dP alone         (A->C) moves eta %+.3f pp  -> %s"
                  % (c["eta_pct"] - a["eta_pct"],
                     "DOWN, as predicted" if c["eta_pct"] < a["eta_pct"] else "UP, contradicts"))
            print("   B overshoots 51.27 %%?  %s (%+.3f pp)"
                  % ("YES" if b["eta_err_pp"] > 0 else "no", b["eta_err_pp"]))
            print("   D lands on 51.27 %%?    %s (%+.3f pp)"
                  % ("YES, within 0.3 pp" if abs(d["eta_err_pp"]) < 0.3 else "NO",
                     d["eta_err_pp"]))
            print("   D clears both flagged nodes? %s (%d remaining)"
                  % ("YES" if d["n_flagged_nodes"] == 0 else "NO", d["n_flagged_nodes"]))
            print("\nDoes the recompressed-fraction explanation compete?")
            print("   f = 0.4097 alone (A->E) moves MIXER_OUT h err %+.3f -> %+.3f %%"
                  % (a["mixer_h_pct"], e["mixer_h_pct"]))
            print("   and eta %+.3f pp -> %+.3f pp" % (a["eta_err_pp"], e["eta_err_pp"]))
            print("   full combination F: eta %+.3f pp, RMS h %.3f %%, %d node(s) flagged"
                  % (g["eta_err_pp"], g["rms_h_pct"], g["n_flagged_nodes"]))

            print("\n   best case on node agreement (RMS h): %s"
                  % min(results, key=lambda t: results[t]["rms_h_pct"]))
            print("   best case on eta            (|d pp|): %s"
                  % min(results, key=lambda t: abs(results[t]["eta_err_pp"])))
            best = min(results, key=lambda t: results[t]["rms_h_pct"])
            print("\n" + "=" * 108)
            print("FULL NODE TABLE FOR THE BEST CASE (%s) -- same format as compare_dostal_nodes.py"
                  % best)
            print("=" * 108)
            cmpn.print_table(results[best]["rows"])

            print("\n   Case F is the ADOPTED baseline (VALIDATION.md 2.3.4a); this run is the")
            print("   evidence for that decision and a regression test of it. F should win on")
            print("   both eta and node agreement -- if it stops winning, something regressed.")
            assert best == "F", "case F no longer wins on node agreement -- baseline regressed"
        finally:
            sys.stdout = real_stdout
        fh.write("```\n")

    csv_path = os.path.join(RESULTS_DIR, "dostal_dp_recup_matrix_%s.csv" % stamp)
    vd.write_csv(csv_path, csv_rows)

    print("\nresults written (commit %s):" % commit)
    for p in (md_path, csv_path):
        print("   %s" % os.path.relpath(p, REPO_ROOT).replace("\\", "/"))


if __name__ == "__main__":
    main()
