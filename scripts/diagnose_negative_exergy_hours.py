r"""Diagnose the hours where the annual exergy balance reports Ed < 0.

WHY THIS EXISTS. Wiring the exergy layer into the integrated model (2026-08-19) produced a
working annual accounting whose OWN GUARD FIRED: 27 of 6040 operating hours came back with
Ed = Ex_htf - W_gross < 0, i.e. the power block appearing to produce more work than the salt
stream delivered exergy. That is a second-law violation, and it is invisible in every aggregate
-- Ed sums to a large positive number and eta_II looks entirely plausible at 0.727. An annual
mean can hide sign errors in individual hours indefinitely, which is why the hour count is an
instrumented output rather than a footnote.

*** DO NOT SKIP TO A FIX. *** The standing rule earned in CLAUDE.md 4.15 is that a mechanism
invented to explain an observation, without the observation being measured first, costs this
project a session and a wrong finding. The leading hypothesis is that these are startup /
shutdown transients where P_cycle is credited against a small or transient m_dot_pc, so the
salt-side stream exergy under-counts what the block actually received. This script tests that
hypothesis rather than assuming it, and prints the evidence either way.

WHAT IT DOES. Re-runs one integrated case, recomputes the hourly exergy the same way
scripts/exergy.py does, isolates the offending hours, and dumps every quantity that could
produce the sign: mass flow, both loop temperatures, gross work, cycle thermal input, the
startup thermal term, ambient, and the cp the property module returned. It then tests four
candidate explanations against that dump and states which the data supports.

Inputs:  none beyond the integrated case itself (map + TMY + .venv of CLAUDE.md section 1).

Run:  .\.venv\Scripts\python.exe -u .\scripts\diagnose_negative_exergy_hours.py
      .\.venv\Scripts\python.exe -u .\scripts\diagnose_negative_exergy_hours.py --case sco2_n5

Outputs: results/negative_exergy_hours_<stamp>.md    the argument and the verdict
         results/negative_exergy_hours_<stamp>.csv   one row per offending hour
"""

import argparse
import csv
import datetime
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import exergy                                                    # noqa: E402
import nanofluid_properties as nfp                               # noqa: E402


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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", default="sco2_n3")
    args = ap.parse_args()

    import run_integrated_annual as ria
    import PySAM.Singleowner as Singleowner

    m, info = ria.build_case(args.case)
    fin = Singleowner.from_existing(m, "MSPTSingleOwner")
    m.execute(0)
    fin.execute(0)
    o = m.Outputs

    q_sf = list(o.q_sf_inc)
    mdot = list(o.m_dot_pc)
    T_in = list(o.T_pc_in)
    T_out = list(o.T_pc_out)
    P_cyc = list(o.P_cycle)
    q_pb = list(o.q_pb)
    q_su = list(o.q_pc_startup)
    tdry = list(o.tdry)
    eta_h = list(o.eta)

    md, rows = [], []

    def say(line=""):
        # cp1252 console vs utf-8 artifact -- transliterate on the way out only (CLAUDE.md 4.16)
        print(line.encode("ascii", "replace").decode("ascii"), flush=True)
        md.append(line)

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = git_commit()

    say("# Negative-Ed hours — diagnosing the annual exergy guard")
    say()
    say("| | |")
    say("|---|---|")
    say("| script | `scripts/diagnose_negative_exergy_hours.py` |")
    say("| case | `%s` |" % args.case)
    say("| run (UTC) | %s |" % stamp)
    say("| git commit | `%s` |" % commit)
    say()

    def cp_of(T_mean_C):
        T = min(max(T_mean_C, nfp.T_VALID_MIN_C), nfp.T_VALID_MAX_C)
        return nfp.cp_nf(ria.PHI, nfp.base_chloride_properties(T), nfp.CUO).nominal / 1000.0

    bad, operating = [], 0
    for i in range(len(mdot)):
        if mdot[i] <= 0.0:
            continue
        T_hot_K, T_cold_K = T_in[i] + 273.15, T_out[i] + 273.15
        if T_hot_K <= T_cold_K:
            continue
        operating += 1
        cp = cp_of(0.5 * (T_in[i] + T_out[i]))
        ex_htf = exergy.stream_exergy_rate(mdot[i], cp, T_hot_K, T_cold_K,
                                           tdry[i] + 273.15) / 1000.0     # MW
        ed = ex_htf - P_cyc[i]
        if ed < 0.0:
            bad.append((i, ex_htf, ed, cp))

    say("## 1. The offending hours")
    say()
    say("**%d of %d operating hours** have `Ed = Ex_htf - W_gross < 0`, i.e. %.2f %%."
        % (len(bad), operating, 100.0 * len(bad) / operating if operating else 0.0))
    say()
    if not bad:
        say("Nothing to diagnose — the guard is clean for this case.")
    else:
        say("| h | m_dot_pc | T_pc_in | T_pc_out | loop dT | q_pb | q_pc_startup | P_cycle | "
            "eta | Ex_htf | **Ed** | cp |")
        say("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for i, ex_htf, ed, cp in bad:
            say("| %d | %.1f | %.1f | %.1f | %.1f | %.2f | %.2f | %.2f | %.4f | %.3f | "
                "**%.3f** | %.4f |"
                % (i, mdot[i], T_in[i], T_out[i], T_in[i] - T_out[i], q_pb[i], q_su[i],
                   P_cyc[i], eta_h[i], ex_htf, ed, cp))
            rows.append({
                "hour": i, "m_dot_pc_kg_s": mdot[i], "T_pc_in_C": T_in[i],
                "T_pc_out_C": T_out[i], "loop_dT_K": T_in[i] - T_out[i],
                "q_pb_MWt": q_pb[i], "q_pc_startup_MWt": q_su[i], "P_cycle_MWe": P_cyc[i],
                "eta_hourly": eta_h[i], "tdry_C": tdry[i], "cp_kJ_kgK": cp,
                "Ex_htf_MW": ex_htf, "Ed_MW": ed, "q_sf_inc_MWt": q_sf[i],
            })

        # ---------------- candidate explanations, tested ----------------------
        say()
        say("## 2. Four candidate explanations, tested against that dump")
        say()

        n = len(bad)
        idx = [b[0] for b in bad]

        # (a) startup transients
        with_startup = sum(1 for i in idx if q_su[i] > 1e-9)
        # (b) energy balance inconsistent: does q_pb match m*cp*dT that hour?
        resid = []
        for i, _ex, _ed, cp in bad:
            q_stream = mdot[i] * cp * (T_in[i] - T_out[i]) / 1000.0     # MWt
            if q_pb[i] > 1e-9:
                resid.append(100.0 * (q_stream - q_pb[i]) / q_pb[i])
        # (c) is the hourly efficiency implausible (above design)?
        above_design = sum(1 for i in idx if eta_h[i] > info["design_eff"] + 1e-9)
        # (d) tiny-flow hours
        mdot_des = max(mdot)
        tiny = sum(1 for i in idx if mdot[i] < 0.10 * mdot_des)

        say("| # | candidate | test | result |")
        say("|---|---|---|---|")
        say("| a | **Startup / shutdown transient** | `q_pc_startup > 0` in the hour | "
            "**%d of %d** (%.0f %%) |" % (with_startup, n, 100.0 * with_startup / n))
        say("| b | **Stream energy ≠ cycle thermal input** | `m·cp·ΔT` vs `q_pb` | "
            "median %+.1f %%, worst %+.1f %% |"
            % ((sorted(resid)[len(resid) // 2] if resid else float('nan')),
               (max(resid, key=abs) if resid else float('nan'))))
        say("| c | **Hourly η above design** (map extrapolating) | `eta > design_eff` | "
            "**%d of %d** |" % (above_design, n))
        say("| d | **Very low mass flow** | `m_dot < 10 %% of max` | **%d of %d** |" % (tiny, n))
        say()

        # ---------------- magnitude ------------------------------------------
        ed_bad = sum(b[2] for b in bad)
        say("## 3. How much does this move the annual number?")
        say()
        say("The offending hours sum to **%.1f MWh** of negative Ed. Setting them aside entirely "
            "changes the annual power-block exergy destruction by that amount — decide whether "
            "that is material against the totals in the integrated-run artifact before deciding "
            "how much effort the fix deserves." % ed_bad)
        say()

        # ---------------- verdict --------------------------------------------
        say("## 4. Verdict")
        say()
        if with_startup == n:
            say("**(a) is confirmed: every offending hour carries a non-zero startup term.** The "
                "salt-side stream exergy is computed from `m_dot_pc` and the loop ΔT, which do "
                "not include the energy drawn to bring the block up; `P_cycle` in the same hour "
                "does reflect it. The stream integral therefore under-counts what the block "
                "received, and the deficit shows up as negative Ed.")
            say()
            say("**The honest fix is an EXCLUSION, not a correction.** These hours cannot be "
                "given a correct exergy balance from the arrays available, because the startup "
                "energy has no accompanying temperature or flow to integrate. Exclude them, "
                "COUNT them, and report the count beside the annual figure — a silent exclusion "
                "would be exactly the sort of quiet repair this project has already paid for "
                "once (CLAUDE.md §4.15).")
        elif with_startup > 0:
            say("**(a) is PARTIAL: %d of %d offending hours carry a startup term.** Startup "
                "explains some but not all of them, so the remaining %d need their own account "
                "before the annual eta_II is quoted. Look at candidates (b)-(d) above for those "
                "rows specifically." % (with_startup, n, n - with_startup))
        else:
            say("**(a) is REFUTED — no offending hour carries a startup term.** The leading "
                "hypothesis is wrong, and the cause is elsewhere: read candidates (b)-(d) above. "
                "Do not adopt a startup exclusion on the strength of a hypothesis the data has "
                "just contradicted.")
        say()
        say("⚠ **Until this is resolved, the annual `eta_II_power_block` should not be quoted.** "
            "The integrated-run report already refuses to endorse it while `negative_Ed_hours` "
            "is non-zero; that refusal is deliberate and should not be relaxed to make a table "
            "look tidy.")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    md_path = os.path.join(RESULTS_DIR, "negative_exergy_hours_%s.md" % stamp)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    csv_path = os.path.join(RESULTS_DIR, "negative_exergy_hours_%s.csv" % stamp)
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print("\nwrote %s" % os.path.relpath(md_path, REPO_ROOT).replace("\\", "/"))
    if rows:
        print("wrote %s" % os.path.relpath(csv_path, REPO_ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
