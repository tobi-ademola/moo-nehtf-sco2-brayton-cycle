r"""Validate the two model nodes Dostal (2004) does not tabulate, by conservation.

Dostal's node 3 is the HTR cold inlet, i.e. ALREADY POST-MIX, so two nodes of our model have no
published row to compare against:

    LTR_HP_OUT  -- LTR cold outlet, BEFORE the recompressed stream rejoins
    RC_OUT      -- recompressor outlet

VALIDATION.md 2.3.3a validates them by conservation instead. This script runs those checks on the
rebuilt 700 C high-performance case, splitting each into an INTERNAL and an ABSOLUTE variant --
the distinction matters, and collapsing them hides which physics actually failed:

  CHECK 1A (internal) -- does the mixing junction close on OUR OWN nodes?
        h[MIXER_OUT] == (1 - f) * h[LTR_HP_OUT] + f * h[RC_OUT]
      Tests the mass/energy balance at the junction and the split-fraction CONVENTION. Passing
      this means the two untabulated nodes are mutually consistent with the post-mix node.

  CHECK 1B (absolute) -- does that same mix reproduce DOSTAL's h3 = 539.07?
      NOTE: 1B is arithmetically the SAME NUMBER as the MIXER_OUT h comparison in
      compare_dostal_nodes.py, because 1A closes to ~1e-04. It is therefore NOT independent
      evidence, and a 1B failure is a statement about recuperator duty split, not about the
      junction. Both split-fraction conventions are evaluated so the convention question gets a
      definite answer rather than an assumption.

  CHECK 2A (absolute) -- RC_OUT from the recompressor isentropic relation, using DOSTAL's node 8:
        h8s = h(P = 20 MPa, s = s8_dostal);   h_RC = h8_dostal + (h8s - h8_dostal) / eta_rc
      Independent of Check 1 -- it never touches LTR_HP_OUT or the mixer.

  CHECK 2B (internal) -- the same relation driven from OUR node 8. This isolates whether ssc
      applies eta_rc = 0.89 correctly, with the node-8 offset divided out. 2A folds together the
      isentropic relation AND our small node-8 discrepancy; 2B tests the relation alone.

Inputs:  none -- imports scripts/validate_dostal.py and re-solves the base (lossless) case.
         Requires the .venv of CLAUDE.md section 1 (PySAM, numpy, CoolProp).

Run:  .\.venv\Scripts\python.exe -u .\scripts\check_untabulated_nodes.py

Outputs (CLAUDE.md section 0.2), stamped with the UTC run time and the producing git commit:
    results/dostal_junction_checks_<stamp>.md    console report
    results/dostal_junction_checks_<stamp>.csv   one row per check
"""

import datetime
import os
import sys

from CoolProp.CoolProp import PropsSI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_dostal as vd                                     # noqa: E402

REPO_ROOT = vd.REPO_ROOT
RESULTS_DIR = vd.RESULTS_DIR

# --- Dostal 2004 Table 10.4 (High-Performance, 700 C) values used here --------
H3_DOSTAL = 539.07          # node 3, post-mix HTR cold inlet   [kJ/kg]
H8_DOSTAL = 480.96          # node 8, LTR hot outlet            [kJ/kg]
S8_DOSTAL = 1.9020          # node 8                            [kJ/kg-K]
P8_DOSTAL = 7704.93         # node 8                            [kPa]
P_HIGH_KPA = 20000.0        # recompressor discharge            [kPa]

# Tolerances. The internal checks must close to solver precision; the absolute checks inherit
# our node-8 / duty-split offsets from the state-point comparison, so they get the same 2 %
# band used to flag nodes in compare_dostal_nodes.py.
TOL_INTERNAL_KJ = 1e-2      # kJ/kg
TOL_ABSOLUTE_PCT = 2.0      # %

NODE_INDEX = {nm.split(None, 1)[0]: i for i, nm in enumerate(vd.NODES)}


def line(name, expected, actual, unit="kJ/kg"):
    """Absolute and % difference, printed identically for every check."""
    diff = actual - expected
    pct = 100.0 * diff / expected
    print("   %-30s expected %10.4f   model %10.4f   abs %+9.4f %s   %+7.3f %%"
          % (name, expected, actual, diff, unit, pct))
    return diff, pct


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = vd.git_commit()

    # Keep the model referenced -- a bare Outputs segfaults once the model is collected
    # (CLAUDE.md 4.8).
    m, note = vd.solve()
    o = m.Outputs
    h = list(o.h_state_points)
    s = list(o.s_state_points)
    f = o.recomp_frac

    h_ltr_hp = h[NODE_INDEX["LTR_HP_OUT"]]
    h_rc_out = h[NODE_INDEX["RC_OUT"]]
    h_mixer = h[NODE_INDEX["MIXER_OUT"]]
    h8_model = h[NODE_INDEX["LTR_LP_OUT"]]
    s8_model = s[NODE_INDEX["LTR_LP_OUT"]]

    md_path = os.path.join(RESULTS_DIR, "dostal_junction_checks_%s.md" % stamp)
    rows = []
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# Untabulated nodes (LTR_HP_OUT, RC_OUT) -- validation by conservation\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/check_untabulated_nodes.py` |\n"
                 "| run (UTC) | %s |\n| git commit | `%s` |\n"
                 "| case | Dostal high-performance 700 C, base (lossless) |\n\n```\n"
                 % (stamp, commit))
        real_stdout = sys.stdout
        sys.stdout = vd.Tee(real_stdout, fh)
        try:
            print("=" * 100)
            print("VALIDATING THE TWO NODES DOSTAL DOES NOT TABULATE")
            print("=" * 100)
            if note:
                print("  !! " + note.replace("\n", "\n  ") + "\n")
            print("  recomp fraction f       = %.5f   (adopted %.4f; Table 10.1 states %.2f)"
                  % (f, vd.F_RECOMP, vd.F_RECOMP_STATED))
            print("  h[LTR_HP_OUT]           = %10.4f kJ/kg   <-- no Dostal row" % h_ltr_hp)
            print("  h[RC_OUT]               = %10.4f kJ/kg   <-- no Dostal row" % h_rc_out)
            print("  h[MIXER_OUT]  (= pt 3)  = %10.4f kJ/kg   (Dostal %.2f)"
                  % (h_mixer, H3_DOSTAL))
            print("  h[LTR_LP_OUT] (= pt 8)  = %10.4f kJ/kg   (Dostal %.2f)"
                  % (h8_model, H8_DOSTAL))
            print("  s[LTR_LP_OUT] (= pt 8)  = %10.5f kJ/kg-K (Dostal %.4f)"
                  % (s8_model, S8_DOSTAL))

            # ---------------- CHECK 1A -- internal junction closure --------------
            print("\n" + "-" * 100)
            print("CHECK 1A (INTERNAL)  mixing junction closes on our own nodes")
            print("-" * 100)
            mixed = (1.0 - f) * h_ltr_hp + f * h_rc_out
            d1a, p1a = line("(1-f)h[LTR_HP] + f*h[RC]", h_mixer, mixed)
            ok_1a = abs(d1a) < TOL_INTERNAL_KJ
            print("   -> %s (tolerance %.0e kJ/kg)"
                  % ("PASS" if ok_1a else "FAIL", TOL_INTERNAL_KJ))
            rows.append({"check": "1A_internal_junction_closure", "basis": "model",
                         "expected": h_mixer, "model": mixed, "abs_diff": d1a,
                         "pct_diff": p1a, "tolerance": "%g kJ/kg" % TOL_INTERNAL_KJ,
                         "result": "PASS" if ok_1a else "FAIL"})

            # ---------------- CHECK 1B -- absolute, vs Dostal h3 -----------------
            print("\n" + "-" * 100)
            print("CHECK 1B (ABSOLUTE)  does that mix reproduce Dostal h3 = %.2f?" % H3_DOSTAL)
            print("-" * 100)
            print("   both split-fraction conventions evaluated -- f is the RECOMPRESSED")
            print("   fraction (the stream bypassing precooler + main compressor):")
            swapped = f * h_ltr_hp + (1.0 - f) * h_rc_out
            d1b, p1b = line("(1-f)h[LTR_HP] + f*h[RC]", H3_DOSTAL, mixed)
            d1s, p1s = line("SWAPPED: f*h[LTR_HP]+(1-f)h[RC]", H3_DOSTAL, swapped)
            ok_1b = abs(p1b) < TOL_ABSOLUTE_PCT
            print("   -> %s (tolerance %.0f %%)" % ("PASS" if ok_1b else "FAIL",
                                                    TOL_ABSOLUTE_PCT))
            print("   convention verdict: the as-specified convention is CONFIRMED by 1A, which")
            print("   closes to %.1e kJ/kg. The swapped form is off by %+.3f %% AND would break"
                  % (abs(d1a), p1s))
            print("   that exact internal closure, so it is not the explanation for 1B.")
            rows.append({"check": "1B_absolute_vs_dostal_h3", "basis": "Dostal h3",
                         "expected": H3_DOSTAL, "model": mixed, "abs_diff": d1b,
                         "pct_diff": p1b, "tolerance": "%g %%" % TOL_ABSOLUTE_PCT,
                         "result": "PASS" if ok_1b else "FAIL"})
            rows.append({"check": "1B_absolute_swapped_convention", "basis": "Dostal h3",
                         "expected": H3_DOSTAL, "model": swapped, "abs_diff": d1s,
                         "pct_diff": p1s, "tolerance": "%g %%" % TOL_ABSOLUTE_PCT,
                         "result": "PASS" if abs(p1s) < TOL_ABSOLUTE_PCT else "FAIL"})

            # ---------------- CHECK 2 -- recompressor isentropic relation --------
            print("\n" + "-" * 100)
            print("CHECK 2 (RC_OUT via the recompressor isentropic relation, eta_rc = %.2f)"
                  % vd.ETA_RC)
            print("-" * 100)
            # 2A -- driven from Dostal's node 8.
            h8s_d = PropsSI("H", "P", P_HIGH_KPA * 1000.0, "S", S8_DOSTAL * 1000.0,
                            "CO2") / 1000.0
            h_rc_exp_d = H8_DOSTAL + (h8s_d - H8_DOSTAL) / vd.ETA_RC
            print("   2A basis: Dostal node 8 (h %.2f, s %.4f, P %.2f kPa)"
                  % (H8_DOSTAL, S8_DOSTAL, P8_DOSTAL))
            print("      h8s(20 MPa, s8) = %.4f kJ/kg   ideal rise %.4f, actual rise %.4f"
                  % (h8s_d, h8s_d - H8_DOSTAL, (h8s_d - H8_DOSTAL) / vd.ETA_RC))
            d2a, p2a = line("h[RC_OUT]", h_rc_exp_d, h_rc_out)
            ok_2a = abs(p2a) < TOL_ABSOLUTE_PCT
            print("      -> %s (tolerance %.0f %%)" % ("PASS" if ok_2a else "FAIL",
                                                       TOL_ABSOLUTE_PCT))
            rows.append({"check": "2A_rc_isentropic_dostal_node8", "basis": "Dostal node 8",
                         "expected": h_rc_exp_d, "model": h_rc_out, "abs_diff": d2a,
                         "pct_diff": p2a, "tolerance": "%g %%" % TOL_ABSOLUTE_PCT,
                         "result": "PASS" if ok_2a else "FAIL"})

            # 2B -- driven from our own node 8: tests the relation with the node-8 offset removed.
            h8s_m = PropsSI("H", "P", P_HIGH_KPA * 1000.0, "S", s8_model * 1000.0,
                            "CO2") / 1000.0
            h_rc_exp_m = h8_model + (h8s_m - h8_model) / vd.ETA_RC
            print("\n   2B basis: OUR node 8 (h %.4f, s %.5f) -- isolates eta_rc application"
                  % (h8_model, s8_model))
            print("      h8s(20 MPa, s8) = %.4f kJ/kg   ideal rise %.4f, actual rise %.4f"
                  % (h8s_m, h8s_m - h8_model, (h8s_m - h8_model) / vd.ETA_RC))
            d2b, p2b = line("h[RC_OUT]", h_rc_exp_m, h_rc_out)
            ok_2b = abs(d2b) < 0.5           # kJ/kg -- a real test of the relation itself
            print("      -> %s (tolerance 0.5 kJ/kg)" % ("PASS" if ok_2b else "FAIL"))
            rows.append({"check": "2B_rc_isentropic_model_node8", "basis": "model node 8",
                         "expected": h_rc_exp_m, "model": h_rc_out, "abs_diff": d2b,
                         "pct_diff": p2b, "tolerance": "0.5 kJ/kg",
                         "result": "PASS" if ok_2b else "FAIL"})

            # ---------------- verdict -------------------------------------------
            print("\n" + "=" * 100)
            print("VERDICT")
            print("=" * 100)
            print("   1A internal junction closure      %s" % ("PASS" if ok_1a else "FAIL"))
            print("   1B absolute vs Dostal h3          %s" % ("PASS" if ok_1b else "FAIL"))
            print("   2A isentropic, Dostal node 8      %s" % ("PASS" if ok_2a else "FAIL"))
            print("   2B isentropic, our node 8         %s" % ("PASS" if ok_2b else "FAIL"))
            print()
            if ok_1a and ok_2a and ok_2b:
                print("   LTR_HP_OUT and RC_OUT are VALIDATED BY CONSERVATION:")
                print("     * RC_OUT is confirmed directly and independently by Check 2 -- the")
                print("       recompressor obeys the isentropic relation at eta_rc = 0.89 against")
                print("       Dostal's own node 8 (2A) and exactly against ours (2B).")
                print("     * With RC_OUT confirmed, the junction closure 1A then pins LTR_HP_OUT:")
                print("       it is the only remaining unknown in the mass/energy balance.")
                print("     * The split-fraction convention is confirmed, not assumed.")
            if not ok_1b:
                print()
                print("   1B does NOT overturn that. It is arithmetically the same quantity as the")
                print("   MIXER_OUT h error already reported by compare_dostal_nodes.py (+5.05 %),")
                print("   since 1A closes to %.1e kJ/kg -- so it carries no independent" % abs(d1a))
                print("   information about these two nodes. It restates the recuperator")
                print("   duty-split difference diagnosed in VALIDATION.md 2.3.4: our HTR is")
                print("   ~20 K approach vs Dostal's ~10 K, so our LTR does more of the work and")
                print("   every node between the LTR and HTR sits high. Both junction nodes are")
                print("   displaced by that split -- consistently, not erroneously.")
        finally:
            sys.stdout = real_stdout
        fh.write("```\n")

    csv_path = os.path.join(RESULTS_DIR, "dostal_junction_checks_%s.csv" % stamp)
    vd.write_csv(csv_path, rows)

    print("\nresults written (commit %s):" % commit)
    for p in (md_path, csv_path):
        print("   %s" % os.path.relpath(p, REPO_ROOT).replace("\\", "/"))


if __name__ == "__main__":
    main()
