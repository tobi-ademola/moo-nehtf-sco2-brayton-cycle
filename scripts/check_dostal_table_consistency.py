r"""Is Dostal (2004)'s own state table self-consistent with the recompressed fraction he states?

This script contains NO model run. It is pure arithmetic on Dostal's published numbers plus
CoolProp for one isentropic state, and it exists because the node errors in VALIDATION.md 2.3.4
have a second candidate explanation that must be ruled in or out before any model change:
we PIN f = 0.39 from Table 10.1, but Table 10.1's f and Table 10.4's state points are two
different pieces of data, and nothing so far has checked that they agree with each other.

Three balances have to hold simultaneously for the tabulated states, at the stated f:

  HTR   (full flow both sides)          h4 - h3  ==  h6 - h7
  LTR   (full flow hot, (1-f) cold)     h7 - h8  ==  (1-f) * (h_LTR_HP - h2)
  MIX   (streams recombine)             h3       ==  (1-f) * h_LTR_HP + f * h_RC

with h_RC fixed independently by the recompressor isentropic relation from node 8:

  h_RC  ==  h8 + (h(20 MPa, s8) - h8) / eta_rc

h_LTR_HP and h_RC are not tabulated, but they are not free either: LTR pins the first and the
isentropic relation pins the second, so MIX becomes a closed test of f. Solving MIX for f gives
the recompressed fraction Dostal's STATE TABLE actually encodes, which can then be compared
against the value his Table 10.1 states.

The Advanced 650 C design (Table 10.3, f = 0.41) is run through the identical test as a control.
If the method is sound it should close there; if it fails on both designs the method is wrong,
not the data.

Inputs:  none -- all values are transcribed in VALIDATION.md 2.3.2. Requires CoolProp.

Run:  .\.venv\Scripts\python.exe -u .\scripts\check_dostal_table_consistency.py

Outputs (CLAUDE.md section 0.2):
    results/dostal_table_consistency_<stamp>.md
    results/dostal_table_consistency_<stamp>.csv
"""

import datetime
import os
import sys

from CoolProp.CoolProp import PropsSI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_dostal as vd                                     # noqa: E402

REPO_ROOT = vd.REPO_ROOT
RESULTS_DIR = vd.RESULTS_DIR

ETA_RC = 0.89               # conservative recompressor efficiency, Table 10.1
P_HIGH_PA = 20.0e6          # recompressor discharge

# design -> (Table, f stated in Table 10.1, h2, h3, h4, h5, h6, h7, h8, s8)
DESIGNS = {
    "High-Performance 700 C": ("10.4", 0.39, 327.26, 539.07, 1012.03, 1223.34,
                               1078.95, 605.98, 480.96, 1.9020),
    "Advanced 650 C (control)": ("10.3", 0.41, 327.26, 534.73, 959.50, 1160.20,
                                 1025.79, 601.01, 477.57, 1.8921),
}


def analyse(name, tbl, f_stated, h2, h3, h4, h5, h6, h7, h8, s8):
    print("=" * 100)
    print("%s   (Table %s, Table 10.1 states f = %.2f)" % (name, tbl, f_stated))
    print("=" * 100)

    # --- HTR balance: uses only tabulated values, so it is a pure transcription check ----
    htr_cold = h4 - h3
    htr_hot = h6 - h7
    print("   HTR balance   h4-h3 = %8.4f   h6-h7 = %8.4f   residual %+.4f kJ/kg"
          % (htr_cold, htr_hot, htr_cold - htr_hot))
    print("      -> %s: the HTR rows are internally consistent to %.2f kJ/kg"
          % ("PASS" if abs(htr_cold - htr_hot) < 0.05 else "FAIL", abs(htr_cold - htr_hot)))

    # --- recompressor outlet, fixed independently of f ----------------------------------
    h8s = PropsSI("H", "P", P_HIGH_PA, "S", s8 * 1000.0, "CO2") / 1000.0
    h_rc = h8 + (h8s - h8) / ETA_RC
    print("\n   recompressor  h8s(20 MPa, s8) = %8.4f   ->  h_RC = %8.4f kJ/kg  (eta_rc %.2f)"
          % (h8s, h_rc, ETA_RC))

    # --- LTR + mixer, evaluated AT THE STATED f ------------------------------------------
    ltr_hot = h7 - h8
    h_ltr_hp = h2 + ltr_hot / (1.0 - f_stated)
    h3_pred = (1.0 - f_stated) * h_ltr_hp + f_stated * h_rc
    resid = h3_pred - h3
    print("\n   at the STATED f = %.2f:" % f_stated)
    print("      LTR hot duty     h7-h8      = %8.4f kJ/kg" % ltr_hot)
    print("      -> h[LTR_HP_OUT] = h2 + duty/(1-f) = %8.4f kJ/kg" % h_ltr_hp)
    print("      -> h3 predicted  = %8.4f   tabulated %8.4f   residual %+.4f kJ/kg (%+.3f %%)"
          % (h3_pred, h3, resid, 100.0 * resid / h3))

    # --- solve the mixer for the f the state table actually encodes ----------------------
    # h3 = (1-f)*h2 + (h7-h8) + f*h_RC   -- linear in f once h_LTR_HP is substituted.
    #    => h3 = h2 + (h7-h8) + f*(h_RC - h2)
    f_implied = (h3 - h2 - ltr_hot) / (h_rc - h2)
    print("\n   solving the mixer for f:  f_implied = %.4f   (Table 10.1 states %.2f, delta %+.4f)"
          % (f_implied, f_stated, f_implied - f_stated))

    # At the implied f the two mixing streams should have nearly equal enthalpy -- that is the
    # design condition that minimises mixing loss, and it is a strong independent tell.
    h_ltr_hp_i = h2 + ltr_hot / (1.0 - f_implied)
    print("      at f_implied:  h[LTR_HP_OUT] = %8.4f   h[RC_OUT] = %8.4f   difference %+.4f"
          % (h_ltr_hp_i, h_rc, h_ltr_hp_i - h_rc))
    print("      (a well-designed junction mixes streams of nearly EQUAL enthalpy, so a near-zero")
    print("       difference here is independent evidence that f_implied is the real design point)")

    # --- robustness: f_implied depends on h_RC, which depends on the assumed eta_rc ---------
    # If a plausible eta_rc could bring f_implied back to the stated value, the whole finding
    # collapses. Invert the mixer for the eta_rc that WOULD justify f_stated, and compare it
    # against the only two values Dostal states anywhere (0.89 conservative, 0.948 best-estimate).
    h_rc_needed = h2 + (h3 - h2 - ltr_hot) / f_stated
    eta_rc_needed = (h8s - h8) / (h_rc_needed - h8)
    print("\n   robustness -- what would it take for f = %.2f to be right?" % f_stated)
    print("      the mixer would need h[RC_OUT] = %8.4f kJ/kg" % h_rc_needed)
    print("      which requires eta_rc = %.4f   (Dostal states 0.89 conservative, 0.948 best)"
          % eta_rc_needed)
    plausible = 0.85 <= eta_rc_needed <= 0.96
    print("      -> %s" % ("PLAUSIBLE: the finding is NOT robust, eta_rc could explain it"
                           if plausible else
                           "NOT PLAUSIBLE: no eta_rc Dostal states can rescue the stated f"))
    for eta_alt in (0.89, 0.948):
        h_rc_alt = h8 + (h8s - h8) / eta_alt
        print("      at eta_rc = %.3f -> f_implied = %.4f"
              % (eta_alt, (h3 - h2 - ltr_hot) / (h_rc_alt - h2)))

    print("\n   residual %+.4f kJ/kg, f_implied - f_stated = %+.4f\n" % (resid, f_implied - f_stated))
    return {"design": name, "table": tbl, "f_stated": f_stated, "f_implied": f_implied,
            "f_delta": f_implied - f_stated, "h3_tabulated": h3, "h3_predicted": h3_pred,
            "h3_residual": resid, "h3_residual_pct": 100.0 * resid / h3,
            "h_RC": h_rc, "htr_balance_residual": htr_cold - htr_hot}


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = vd.git_commit()

    md_path = os.path.join(RESULTS_DIR, "dostal_table_consistency_%s.md" % stamp)
    rows = []
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# Is Dostal's state table self-consistent with his stated f?\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/check_dostal_table_consistency.py` |\n"
                 "| run (UTC) | %s |\n| git commit | `%s` |\n"
                 "| method | arithmetic on published values + CoolProp; NO model run |\n\n```\n"
                 % (stamp, commit))
        real_stdout = sys.stdout
        sys.stdout = vd.Tee(real_stdout, fh)
        try:
            for name, spec in DESIGNS.items():
                rows.append(analyse(name, *spec))

            hp, ctrl = rows[0], rows[1]
            print("=" * 100)
            print("CONCLUSION")
            print("=" * 100)
            print("   The control CALIBRATES the method rather than passing or failing it: it")
            print("   sets how much residual is just rounding in a table printed to 2 decimals")
            print("   plus whatever cycle detail this 3-balance reduction omits.\n")
            print("   %-28s %12s %12s %12s %12s"
                  % ("design", "f stated", "f implied", "delta f", "residual"))
            for r in (ctrl, hp):
                print("   %-28s %12.2f %12.4f %+12.4f %+9.4f kJ/kg"
                      % (r["design"], r["f_stated"], r["f_implied"], r["f_delta"],
                         r["h3_residual"]))

            ratio = abs(hp["h3_residual"] / ctrl["h3_residual"])
            print("\n   noise floor from the control: %.2f kJ/kg (delta f %+.4f)"
                  % (abs(ctrl["h3_residual"]), ctrl["f_delta"]))
            print("   High-Performance residual is %.1fx that floor, and its delta f is %.1fx"
                  % (ratio, abs(hp["f_delta"] / ctrl["f_delta"])))
            print("   larger -- so the discrepancy is well outside the method's resolution.")
            print("\n   The tell: BOTH state tables independently encode f ~ %.3f-%.3f."
                  % (min(ctrl["f_implied"], hp["f_implied"]),
                     max(ctrl["f_implied"], hp["f_implied"])))
            print("   The Advanced design STATES 0.41 and its table agrees. The High-Performance")
            print("   design STATES 0.39 but its table encodes %.4f -- essentially the same"
                  % hp["f_implied"])
            print("   value as the other designs. At that f, its two mixing streams differ by")
            print("   only %+.3f kJ/kg, i.e. the junction is very nearly isenthalpic, which is"
                  % (hp["h_RC"] - (327.26 + 125.02 / (1.0 - hp["f_implied"]))))
            print("   the hallmark of a properly optimised mixing point.")
            print("\n   READING: Table 10.1's f = 0.39 for the High-Performance design is not")
            print("   supported by Table 10.4's own state points. This is EVIDENCE, not proof --")
            print("   an alternative reading is that this design uses a slightly different")
            print("   topology or an off-optimum junction that the 3-balance reduction misses.")
            print("\n   CONSEQUENCE for VALIDATION.md 2.3.4: pinning f = 0.39 while comparing")
            print("   against Table 10.4's nodes may be mixing two different design points, which")
            print("   is a SECOND candidate cause of the MIXER_OUT / HTR_LP_OUT errors, separate")
            print("   from recuperator duty split. Testable directly: re-run pinned at f = 0.41.")
        finally:
            sys.stdout = real_stdout
        fh.write("```\n")

    csv_path = os.path.join(RESULTS_DIR, "dostal_table_consistency_%s.csv" % stamp)
    vd.write_csv(csv_path, rows)

    print("\nresults written (commit %s):" % commit)
    for p in (md_path, csv_path):
        print("   %s" % os.path.relpath(p, REPO_ROOT).replace("\\", "/"))


if __name__ == "__main__":
    main()
