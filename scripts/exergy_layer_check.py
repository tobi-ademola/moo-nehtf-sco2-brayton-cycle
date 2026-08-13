r"""Prove the exergy reporting layer is arithmetically sound on data already carried.

MASTER_PLAN 5 flagged one risk against the exergy novelty booster: if PySAM exposed only lumped
efficiencies, every state would have to be rebuilt through CoolProp (+~1 day). It does not -- ssc
gives T, P, h AND s at all 10 real nodes -- so this script closes that risk by computing the whole
exergy layer from data the model already produces, before MASTER_PLAN 11 item 5 builds it for real.

Physical exergy per node:      e = (h - h0) - T0 * (s - s0)
Component exergy destruction:  Ed = T0 * Sgen        (Gouy-Stodola)

*** TWO DIFFERENT T0's ARE IN PLAY AND CONFLATING THEM IS A REAL ERROR ***

  T0_ref  = 305.15 K (32 C) at P0 = 7692.31 kPa -- Dostal node 1, the compressor inlet.
            Requested as the reference for the per-node table. It is a *reference state*, not a
            true dead state: node 1 sits at 7.69 MPa, nowhere near ambient pressure, and the
            cycle cannot reject heat to it. Choosing it makes e(node 1) = 0 BY CONSTRUCTION.
  T0_amb  = 299.15 K (26 C) = T_amb_des -- the actual environment this cycle rejects heat to
            (T_mc_in 32 C minus the 6 K main-compressor approach, CLAUDE.md 4.10).

Consequences, both checked below rather than asserted:
  * h0 and s0 only shift every e by a constant, so node-to-node exergy DIFFERENCES are unaffected
    by that choice; T0 does change them, because it scales the entropy term.
  * The Gouy-Stodola destruction Ed = T0*Sgen is only physically meaningful at the ENVIRONMENT
    temperature, so Ed is reported at T0_amb, with the T0_ref column shown alongside to make the
    ~2 % difference visible. The RANKING is identical either way -- which is the point.
  * The cycle-wide exergy balance closes ONLY at T0_amb:
        Ex_in(salt)  ==  W_net  +  sum(Ed)
    because heat dumped to a reservoir at T0 carries zero exergy by definition. Running the same
    balance at T0_ref leaves a residual, and that residual is the evidence that T0_ref is a
    reference state rather than a dead state. Both are printed.

Expected shape of the answer (stated BEFORE the run, so this is a test and not a description):
  * e(node 1) = 0 exactly, by construction of the reference.
  * e is maximal at node 5, the turbine inlet -- the hottest, highest-pressure state.
  * every component Ed > 0.
  * the HTR is the single largest Ed contributor, per Battisti 2023 (SOURCES.md F2, which reports
    HTR-dominant destruction for a solar recompression cycle) and the recompression literature.

Inputs:  none -- imports scripts/validate_dostal.py and solves the adopted case F baseline.
         Requires the .venv of CLAUDE.md section 1 (PySAM, numpy, CoolProp).

Run:  .\.venv\Scripts\python.exe -u .\scripts\exergy_layer_check.py

Outputs (CLAUDE.md section 0.2):
    results/exergy_layer_check_<stamp>.md    console report
    results/exergy_layer_check_<stamp>.csv   per-node exergy + per-component destruction
"""

import datetime
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_dostal as vd                                     # noqa: E402

REPO_ROOT = vd.REPO_ROOT
RESULTS_DIR = vd.RESULTS_DIR

T0_REF_K = 305.15           # 32 C -- Dostal node 1, the requested reference state
P0_REF_KPA = 7692.31        # kPa  -- Dostal node 1


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = vd.git_commit()

    # Adopted case F. Keep the model referenced -- a bare Outputs segfaults (CLAUDE.md 4.8).
    m, note = vd.solve()
    o = m.Outputs
    T = np.array(o.T_state_points)
    P_kPa = np.array(o.P_state_points) * 1000.0
    h = np.array(o.h_state_points)
    s = np.array(o.s_state_points)
    f = o.recomp_frac
    n = vd.N_REAL

    # Mass flow derived from the turbine duty, not read off the mislabelled output
    # (CLAUDE.md 4.9): m_dot_co2_full is 1000x its documented kg/s.
    mdot = o.t_W_dot / (h[5] - h[6])
    mdot_htf = o.m_dot_htf_des / 1000.0
    T0_amb_K = 273.15 + (vd.T_MC_IN_C - vd.DT_MC_APPROACH)
    w_net = o.t_W_dot - o.mc_W_dot - o.rc_W_dot

    md_path = os.path.join(RESULTS_DIR, "exergy_layer_check_%s.md" % stamp)
    rows = []
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# Exergy layer -- arithmetic soundness check\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/exergy_layer_check.py` |\n"
                 "| run (UTC) | %s |\n| git commit | `%s` |\n"
                 "| case | case F, the adopted baseline |\n\n```\n" % (stamp, commit))
        real_stdout = sys.stdout
        sys.stdout = vd.Tee(real_stdout, fh)
        try:
            print("=" * 100)
            print("EXERGY LAYER CHECK -- case F, computed from ssc's own h and s")
            print("=" * 100)
            if note:
                print("  !! " + note.replace("\n", "\n  ") + "\n")
            print("  reference state  T0_ref = %.2f K (%.2f C), P0 = %.2f kPa  [Dostal node 1]"
                  % (T0_REF_K, T0_REF_K - 273.15, P0_REF_KPA))
            print("  environment      T0_amb = %.2f K (%.2f C)  [T_amb_des -- what the cycle"
                  " actually rejects to]" % (T0_amb_K, T0_amb_K - 273.15))
            print("  m_dot_co2 %.3f kg/s   f_rc %.5f   W_net %.2f kW" % (mdot, f, w_net))
            print("\n  NOTE: node 1 is the compressor inlet at %.2f kPa, NOT a true dead state."
                  % P0_REF_KPA)
            print("  e(node 1) = 0 is therefore true BY CONSTRUCTION -- it verifies the")
            print("  arithmetic is wired correctly, it does not verify the physics.")

            # --- per-node physical exergy -------------------------------------
            h0, s0 = h[0], s[0]
            e_ref = (h[:n] - h0) - T0_REF_K * (s[:n] - s0)
            e_amb = (h[:n] - h0) - T0_amb_K * (s[:n] - s0)

            print("\n" + "-" * 100)
            print("PHYSICAL EXERGY PER NODE   e = (h - h0) - T0*(s - s0),  h0/s0 = node 1")
            print("-" * 100)
            print("%-3s %-11s %9s %11s %10s %11s %12s %12s"
                  % ("#", "node", "T[C]", "P[kPa]", "h[kJ/kg]", "s[kJ/kg-K]",
                     "e@T0_ref", "e@T0_amb"))
            for i in range(n):
                code = vd.NODES[i].split(None, 1)[0]
                print("%-3d %-11s %9.3f %11.2f %10.3f %11.5f %12.4f %12.4f"
                      % (i, code, T[i], P_kPa[i], h[i], s[i], e_ref[i], e_amb[i]))
                rows.append({"idx": i, "node": code, "T_C": T[i], "P_kPa": P_kPa[i],
                             "h_kJ_per_kg": h[i], "s_kJ_per_kgK": s[i],
                             "e_kJ_per_kg_T0ref": e_ref[i], "e_kJ_per_kg_T0amb": e_amb[i]})

            i_max = int(np.argmax(e_ref))
            print("\n   e(node 1)        = %+.3e kJ/kg   -> %s"
                  % (e_ref[0], "PASS (zero by construction)" if abs(e_ref[0]) < 1e-9 else "FAIL"))
            print("   max exergy       = node %d (%s) at %.4f kJ/kg   -> %s"
                  % (i_max, vd.NODES[i_max].split(None, 1)[0], e_ref[i_max],
                     "PASS (turbine inlet)" if i_max == 5 else "FAIL -- expected node 5"))
            print("   all e >= 0?        %s (min %.4f at node %d)"
                  % ("yes" if e_ref.min() >= -1e-9 else "NO", e_ref.min(),
                     int(np.argmin(e_ref))))

            # --- component exergy destruction ---------------------------------
            terms, aux = vd.entropy_generation(o, h, s, mdot, mdot_htf, f, T0_amb_K)
            print("\n" + "-" * 100)
            print("COMPONENT EXERGY DESTRUCTION   Ed = T0 * Sgen   (Gouy-Stodola)")
            print("-" * 100)
            print("%-22s %12s %14s %14s %9s" % ("component", "Sgen[kW/K]", "Ed@T0_amb[kW]",
                                                "Ed@T0_ref[kW]", "share%"))
            sgen_tot = sum(terms.values())
            ed_tot = T0_amb_K * sgen_tot
            all_pos = True
            for k, sgen in sorted(terms.items(), key=lambda kv: -kv[1]):
                if sgen <= 0:
                    all_pos = False
                print("%-22s %+12.5f %14.2f %14.2f %8.2f%s"
                      % (k, sgen, T0_amb_K * sgen, T0_REF_K * sgen,
                         100.0 * sgen / sgen_tot,
                         "   <-- SECOND-LAW VIOLATION" if sgen <= 0 else ""))
                rows.append({"idx": "", "node": k.split()[0], "T_C": "", "P_kPa": "",
                             "h_kJ_per_kg": "", "s_kJ_per_kgK": "",
                             "e_kJ_per_kg_T0ref": "", "e_kJ_per_kg_T0amb": "",
                             "Sgen_kW_per_K": sgen, "Ed_kW_T0amb": T0_amb_K * sgen,
                             "Ed_kW_T0ref": T0_REF_K * sgen,
                             "share_pct": 100.0 * sgen / sgen_tot})
            print("%-22s %+12.5f %14.2f %14.2f %8.2f"
                  % ("TOTAL", sgen_tot, ed_tot, T0_REF_K * sgen_tot, 100.0))

            worst = max(terms, key=lambda k: terms[k])
            print("\n   every component Ed > 0?   %s" % ("PASS" if all_pos else "FAIL"))
            print("   largest destroyer         %s at %.2f kW (%.1f %% of total)"
                  % (worst, T0_amb_K * terms[worst], 100.0 * terms[worst] / sgen_tot))
            print("   HTR-dominant (Battisti 2023, SOURCES.md F2)?   %s"
                  % ("PASS" if worst.startswith("HTR") else
                     "FAIL -- literature expects the HTR to dominate"))

            # --- cycle-wide exergy balance ------------------------------------
            # Salt is an incompressible stream: Ex_in = m*cp*[(Th - Tc) - T0*ln(Th/Tc)].
            # CO2 returns to its own state each cycle, and heat dumped to a reservoir AT T0
            # carries zero exergy, so the whole input must appear as work plus destruction.
            def ex_in(T0):
                return (mdot_htf * aux["cp_htf"]
                        * ((aux["T_htf_hot_K"] - aux["T_htf_cold_K"])
                           - T0 * np.log(aux["T_htf_hot_K"] / aux["T_htf_cold_K"])))

            print("\n" + "-" * 100)
            print("CYCLE-WIDE EXERGY BALANCE   Ex_in(salt) == W_net + sum(Ed)")
            print("-" * 100)
            for label, T0 in (("T0_amb (the environment)", T0_amb_K),
                              ("T0_ref (node 1)", T0_REF_K)):
                exi = ex_in(T0)
                resid = exi - w_net - T0 * sgen_tot
                print("   at %-24s Ex_in %9.2f = W_net %9.2f + Ed %9.2f  ->  residual "
                      "%+8.3f kW (%+.4f %%)"
                      % (label, exi, w_net, T0 * sgen_tot, resid, 100.0 * resid / exi))
            resid_amb = ex_in(T0_amb_K) - w_net - ed_tot
            closes = abs(resid_amb / ex_in(T0_amb_K)) < 1e-3
            print("\n   balance closes at T0_amb?  %s (|residual| = %.4f kW, %.2e relative)"
                  % ("PASS" if closes else "FAIL", abs(resid_amb),
                     abs(resid_amb / ex_in(T0_amb_K))))
            print("   This is the real test: it uses every h, every s, both mass flows, the")
            print("   salt-side properties and the work terms at once. Sign checks cannot")
            print("   catch a scaling or units error; this can.")
            print("\n   exergy efficiency (2nd law)  W_net / Ex_in = %.4f = %.2f %%"
                  % (w_net / ex_in(T0_amb_K), 100.0 * w_net / ex_in(T0_amb_K)))

            # --- verdict -------------------------------------------------------
            print("\n" + "=" * 100)
            print("VERDICT")
            print("=" * 100)
            checks = [
                ("e(node 1) = 0 by construction", abs(e_ref[0]) < 1e-9),
                ("max exergy at node 5 (turbine inlet)", i_max == 5),
                ("every component Ed > 0", all_pos),
                ("HTR is the largest single destroyer", worst.startswith("HTR")),
                ("cycle exergy balance closes at T0_amb", closes),
            ]
            for name, ok in checks:
                print("   %-42s %s" % (name, "PASS" if ok else "FAIL"))
            print()
            if all(ok for _, ok in checks):
                print("   The exergy layer is arithmetically sound on data the model ALREADY")
                print("   carries. MASTER_PLAN 5's CoolProp-reconstruction fallback (+~1 day)")
                print("   is NOT needed and that risk can be closed.")
            for name, ok in checks:
                assert ok, "exergy layer check failed: %s" % name
        finally:
            sys.stdout = real_stdout
        fh.write("```\n")

    csv_path = os.path.join(RESULTS_DIR, "exergy_layer_check_%s.csv" % stamp)
    keys = ["idx", "node", "T_C", "P_kPa", "h_kJ_per_kg", "s_kJ_per_kgK",
            "e_kJ_per_kg_T0ref", "e_kJ_per_kg_T0amb",
            "Sgen_kW_per_K", "Ed_kW_T0amb", "Ed_kW_T0ref", "share_pct"]
    vd.write_csv(csv_path, [{k: r.get(k, "") for k in keys} for r in rows])

    print("\nresults written (commit %s):" % commit)
    for p in (md_path, csv_path):
        print("   %s" % os.path.relpath(p, REPO_ROOT).replace("\\", "/"))


if __name__ == "__main__":
    main()
