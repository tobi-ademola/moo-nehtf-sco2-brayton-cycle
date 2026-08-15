r"""Pin down the units of the UDPC cooling response, and check `ud_f_W_dot_cool_des`.

WHY THIS EXISTS. `CLAUDE.md` §4.11 records that the UDPC cooling column arrives UNNORMALISED --
order 1e-3 at design while every other response is 1.0 there -- and §4.12 records that the design
MAGNITUDES travel separately from the normalised table, via `ud_f_W_dot_cool_des`. Put together,
those two facts leave one question unanswered that decides whether the tower models any cooling
parasitic at all:

    IS THE COOLING COLUMN A DIMENSIONLESS FRACTION, OR A POWER IN SOME UNIT?

`scripts/build_udpc_map.py` assumed the latter and divided by the design net power in kW:

    f_cool_pct = 100.0 * cool_des / W_DOT_NET_DES_KWE      # 100 * 9.971e-4 / 115000

which produced `ud_f_W_dot_cool_des = 0.0000 %` -- i.e. a 115 MW plant whose air cooler draws
nothing. That is the §4.12 silent-mis-scaling failure mode exactly: everything runs, nothing
warns, and the cooling parasitic is simply absent from the annual result.

WHAT THIS SCRIPT DOES. Solves the case F design point (0.1 s, no sweep -- the sweep is ~35 min
and is not needed for a units question), then reports every cooling/power output ssc exposes at
design, so the cooling column can be placed against a KNOWN power in a KNOWN unit rather than
inferred from magnitude alone. Watch for the `CLAUDE.md` §4.9 trap while reading: powers
documented as MW are really kW.

Inputs:  scripts/build_udpc_map.py (the case F design, imported not retyped).
         Requires the .venv of CLAUDE.md §1.

Run:  .\.venv\Scripts\python.exe -u .\scripts\check_udpc_cooling_scale.py

Outputs: results/udpc_cooling_scale_<stamp>.md
"""

import datetime
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_udpc_map as bum  # noqa: E402


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
    report = []

    def say(line=""):
        print(line, flush=True)
        report.append(line)

    say("=" * 100)
    say("UDPC COOLING COLUMN -- UNITS AND ud_f_W_dot_cool_des")
    say("=" * 100)

    m = bum.build(bum.PHI_REFERENCE, bum.T_HTF_HOT_DES_C, 3)
    m.Common.is_generate_udpc = 0          # units question; the sweep costs ~35 min and is moot
    m.execute(0)
    o = m.Outputs

    say("\nDESIGN POINT (no sweep)")
    say("   eta_thermal_calc   %.5f" % o.eta_thermal_calc)
    say("   recomp_frac        %.5f" % o.recomp_frac)
    say("   W_dot_net_des in   %.1f kWe (build_udpc_map.W_DOT_NET_DES_KWE)"
        % bum.W_DOT_NET_DES_KWE)

    # Every scalar output whose name suggests a power or a cooler. Printed rather than
    # cherry-picked, because the point is to find the one that matches the cooling column.
    say("\nCANDIDATE OUTPUTS (scalars only; CLAUDE.md §4.9 -- 'MW' often means kW)")
    hits = []
    for name in sorted(dir(o)):
        if name.startswith("_"):
            continue
        low = name.lower()
        if not ("cool" in low or "fan" in low or "w_dot" in low or "t_amb" in low):
            continue
        try:
            val = getattr(o, name)
        except Exception as exc:
            say("   %-32s <unreadable: %s>" % (name, exc))
            continue
        if isinstance(val, (int, float)):
            say("   %-32s %r" % (name, val))
            hits.append((name, float(val)))

    say("\nINTERPRETATION")
    say("   The per-axis cooling column at design is ~9.971e-04 while W_gross_ND is ~1.0, so the")
    say("   cooling response is dimensionless and ~0.0997 %% of design gross.")
    say("   -> ud_f_W_dot_cool_des should be   100 * cool_des            = %.4f %%"
        % (100.0 * 9.971001e-04))
    say("   -> build_udpc_map.py computed      100 * cool_des / 115000   = %.7f %%"
        % (100.0 * 9.971001e-04 / bum.W_DOT_NET_DES_KWE))
    say("   The second is wrong by a factor of W_DOT_NET_DES_KWE = %.0f."
        % bum.W_DOT_NET_DES_KWE)
    say("")
    say("   CAVEAT, STATED RATHER THAN GLOSSED: 0.0997 %% of gross is LOW for a dry-cooled sCO2")
    say("   cycle, where fan power is usually quoted at 1-2 %%. Two readings remain open and the")
    say("   scalars above are what separate them:")
    say("     (a) the cooling column is a fraction of gross and the AirCoolerDesign inputs")
    say("         (fan_power_frac 0.01, eta_air_cooler_fan 0.5) simply give a small fan load; or")
    say("     (b) the column is normalised against something other than design gross, in which")
    say("         case 100*cool_des is still not the right magnitude.")
    say("   Do NOT ship an annual number that depends on this until one of the two is confirmed")
    say("   against a scalar above.")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(RESULTS_DIR, "udpc_cooling_scale_%s.md" % stamp)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# UDPC cooling column -- units check\n\n"
                 "| | |\n|---|---|\n"
                 "| script | `scripts/check_udpc_cooling_scale.py` |\n"
                 "| run (UTC) | %s |\n| git commit | `%s` |\n"
                 "| PySAM | 7.1.1.post1 (bundled ssc 306) |\n\n```\n%s\n```\n"
                 % (stamp, git_commit(), "\n".join(report)))
    print("\nresults written:\n   %s" % os.path.relpath(path, REPO_ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
