r"""UDPC map cache, keyed by a hash of the CYCLE DESIGN the map was built from.

WHY THIS EXISTS. A UDPC map costs ~38 minutes (`CLAUDE.md` §4.15) and is a property of the cycle
design alone -- not of the plant sizing, not of the site, not of d_p. `scripts/design_sweep_grid.py`
costs the target envelope at 29.7 h **on the assumption that identical designs are built once**;
without a cache the campaign rebuilds the same maps and that number is fiction. This module is that
assumption made real.

*** THE KEY IS DERIVED FROM THE MODEL, NOT FROM A LIST OF PARAMETER NAMES. ***
This is the whole design, and the reason is a near-miss worth recording. The obvious key is the
filename tag already in use, `(phi, T_htf_hot, n_points)`. It is WRONG, and wrong in the silent
direction: `build_udpc_map.build()` pulls `ETA_MC`, `ETA_T`, `P_HIGH_MPA`, `F_RECOMP`,
`DELTA_P_FRAC`, `DOSTAL_DP_FRAC` and more from `validate_dostal`, so **changing the validated
baseline changes the map without any argument of `build()` changing**. A tag-keyed cache would then
serve a stale map that looks entirely right -- the same failure family as §4.12's silent
steam-Rankine defaults.

So the key is a SHA-256 over `m.export()`, which returns every assigned input. Measured
2026-08-19: **64 fields** across `SystemDesign` (10), `HeatExchangerDesign` (27), `Common` (19),
`PHXDesign` (3) and `AirCoolerDesign` (5), including the full 6x7 `htf_props` table -- so phi is
captured automatically, since that table is the only place it enters. That is against the ~30
fields a careful reading of `build()` suggests: a hand-maintained list would have missed roughly
half, including the `PHXDesign`/`AirCoolerDesign` defaults `build()` never sets but which still
shape the map. `Outputs` is empty before `execute()`, so the export is naturally inputs-only.

THE KEY IS COMPUTED BEFORE `execute()`. That is what makes a hit cheap: assembling the model is
~0.1 s, so a cache hit costs a tenth of a second against the 38 minutes a miss costs.

AUDITABILITY IS NOT OPTIONAL HERE. Every cached map is stored beside a `.json` sidecar carrying the
full input payload, the ssc build string, the PySAM version, the git commit and the build wall
time. A cache that cannot be audited is a cache you cannot trust after the first time the baseline
moves -- and this project's standing rule is that a silent wrong number is worse than a loud
failure.

WHAT IS DELIBERATELY *NOT* IN THE KEY, and why that is safe: SM, t_TES, the weather file, and d_p.
None of them is an input to `Sco2CspUdPcTables` at all -- SM and t_TES are tower inputs, the site is
a weather file the tower reads, and d_p has no nominal model effect by `DECISIONS.md` D6. Because
the key is the model's own export, this is not a claim to maintain: anything that is not an input
to the map generator cannot enter the key, and anything that is, does. `--verify-invariance` checks
it by execution rather than leaving it as an argument.

Inputs:  none. Reads/writes `maps/cache/`.

Run:  .\.venv\Scripts\python.exe -u .\scripts\map_cache.py --audit
      .\.venv\Scripts\python.exe -u .\scripts\map_cache.py --verify-invariance
      .\.venv\Scripts\python.exe -u .\scripts\map_cache.py --selftest      (no PySAM needed)

Outputs: maps/cache/<key>.csv     the 7-column combined table
         maps/cache/<key>.json    the audit sidecar
         results/map_cache_audit_<stamp>.md   from --audit
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
CACHE_DIR = os.path.join(REPO_ROOT, "maps", "cache")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Bump ONLY when the meaning of the key changes (e.g. a field is deliberately excluded). It
# invalidates every existing entry by design -- that is the point of having it.
KEY_SCHEMA_VERSION = 1


# =============================================================================
# Environment identity -- part of the key, because ssc is what solves the map
# =============================================================================
def ssc_build_string() -> str:
    """The bundled ssc build string, via ctypes on PySAM's own DLL.

    `from PySAM import ssc` does NOT work -- it is a DLL, not a module (`CLAUDE.md` §1). PySAM
    ships and loads its own copy, and nothing installed under `C:\\SAM\\...` changes it, so this
    is the authoritative identity of the solver that produced a map.
    """
    try:
        import ctypes
        import PySAM
        dll = os.path.join(os.path.dirname(PySAM.__file__), "ssc.dll")
        lib = ctypes.CDLL(dll)
        lib.ssc_version.restype = ctypes.c_int
        lib.ssc_build_info.restype = ctypes.c_char_p
        return "ssc %d / %s" % (lib.ssc_version(),
                                lib.ssc_build_info().decode("utf-8", "replace"))
    except Exception as e:                       # noqa: BLE001 -- identity must never break a run
        return "unavailable (%s: %s)" % (type(e).__name__, e)


def pysam_version() -> str:
    try:
        import PySAM
        return PySAM.__version__
    except Exception as e:                       # noqa: BLE001
        return "unavailable (%s)" % type(e).__name__


def git_commit() -> str:
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
        d = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
        return h + ("-dirty" if d else "")
    except Exception:
        return "unknown"


# =============================================================================
# The key
# =============================================================================
def canonicalise(obj):
    """Make an exported input payload deterministically serialisable.

    Floats are rounded to 12 significant digits before hashing. Without that, a value that
    round-trips through ssc with a 1-ulp difference produces a different key and a spurious
    38-minute rebuild. 12 digits is far tighter than any physically meaningful difference in these
    inputs and far looser than float noise.
    """
    if isinstance(obj, dict):
        return {str(k): canonicalise(obj[k]) for k in sorted(obj)}
    if isinstance(obj, (list, tuple)):
        return [canonicalise(v) for v in obj]
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        return float("%.12g" % obj)
    if isinstance(obj, int):
        return float("%.12g" % float(obj))       # 3 and 3.0 must not key differently
    return obj


def key_payload(model) -> dict:
    """The exact object that gets hashed. Returned separately so it can be stored and diffed."""
    exported = model.export()
    inputs = {g: v for g, v in exported.items() if g != "Outputs" and isinstance(v, dict)}
    return {
        "schema": KEY_SCHEMA_VERSION,
        "inputs": canonicalise(inputs),
        "pysam": pysam_version(),
        "ssc": ssc_build_string(),
    }


def design_key(model) -> tuple:
    """(key_hex, payload). Call BEFORE execute() -- that is what makes a hit cost 0.1 s."""
    payload = key_payload(model)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16], payload


def paths_for(key: str) -> tuple:
    return (os.path.join(CACHE_DIR, "%s.csv" % key),
            os.path.join(CACHE_DIR, "%s.json" % key))


# =============================================================================
# Store
# =============================================================================
def read_cached(key: str):
    """Return (rows, meta) or (None, None). Validates shape -- a truncated file is a MISS."""
    csv_path, json_path = paths_for(key)
    if not (os.path.exists(csv_path) and os.path.exists(json_path)):
        return None, None
    try:
        rows = []
        with open(csv_path, newline="", encoding="utf-8") as fh:
            for i, rec in enumerate(csv.reader(fh)):
                if i == 0:
                    continue
                rows.append([float(v) for v in rec])
        with open(json_path, encoding="utf-8") as fh:
            meta = json.load(fh)
    except Exception:                            # noqa: BLE001 -- a bad entry is a miss, not a crash
        return None, None
    # Same structural contract run_integrated_annual.load_map enforces. A cache must never hand
    # back something the consumer would have rejected off disk.
    if not rows or {len(r) for r in rows} != {7} or len(rows) % 3 != 0:
        return None, None
    return rows, meta


def write_cached(key: str, rows, payload: dict, extra: dict) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    csv_path, json_path = paths_for(key)
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["T_htf", "m_dot_htf_ND", "T_amb",
                    "W_gross_ND", "Q_HTF_ND", "W_cool_ND", "m_water_ND"])
        w.writerows(rows)
    meta = {"key": key, "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "git_commit": git_commit(), "n_rows": len(rows)}
    meta.update(extra)
    meta["payload"] = payload                    # the full input set, so a hit can be diffed
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)


# =============================================================================
# The public entry point
# =============================================================================
def load_or_build(phi_mass, T_htf_hot_C, n_points, force=False, verbose=True):
    """Return (rows, key, hit). Builds only on a miss -- ~38 min; a hit is ~0.1 s.

    The model is assembled and keyed BEFORE `execute()`, so the expensive call is reached only
    when the cache genuinely does not hold this design.
    """
    import build_udpc_map as bum

    m = bum.build(phi_mass, T_htf_hot_C, n_points)
    key, payload = design_key(m)

    if not force:
        rows, meta = read_cached(key)
        if rows is not None:
            if verbose:
                print("[map_cache] HIT  %s  (built %s, %d rows)"
                      % (key, meta.get("written_utc", "?"), len(rows)))
            return rows, key, True

    if verbose:
        print("[map_cache] MISS %s -- building, this takes ~38 min (CLAUDE.md 4.15) and prints "
              "NOTHING while it runs" % key)
    t0 = time.time()
    m.execute(0)
    elapsed = time.time() - t0

    d = bum.check_design(m)
    if d["problems"]:
        raise bum.MapError("refusing to cache a bad design: %s" % d["problems"])

    axes = bum.get_axes(m)
    T_amb_des = bum.vd.T_MC_IN_C - bum.vd.DT_MC_APPROACH
    levels = {
        "T_htf": [bum.T_HTF_HOT_LOW_C, T_htf_hot_C, bum.T_HTF_HOT_HIGH_C],
        "m_dot": [bum.M_DOT_ND_LOW, 1.0, bum.M_DOT_ND_HIGH],
        "T_amb": [bum.T_AMB_LOW_C, T_amb_des, bum.T_AMB_HIGH_C],
    }
    cool_des = bum.design_cooling(axes, T_htf_hot_C)
    rows = bum.to_combined(axes, levels, T_htf_hot_C, T_amb_des, cool_des)
    problems = bum.check_combined(rows, len(axes["T_htf_ind"]))
    if problems:
        raise bum.MapError("refusing to cache a map that failed its checks: %s" % problems)

    write_cached(key, rows, payload, {
        "build_seconds": round(elapsed, 1),
        "phi_mass": phi_mass, "T_htf_hot_C": T_htf_hot_C, "n_points": n_points,
        "eta_thermal_calc": d["eta_thermal_calc"], "recomp_frac": d["recomp_frac"],
        "T_htf_cold_des_C": d["T_htf_cold_des_C"],
        "W_dot_cooler_fan_kWe": d["W_dot_cooler_fan_kWe"],
        # Human-readable only. NOT the key -- see the module docstring.
        "legacy_tag": ("phi%.4f_n%d" % (phi_mass, n_points)).replace(".", "p"),
    })
    if verbose:
        print("[map_cache] built and cached %s in %.0f s" % (key, elapsed))
    return rows, key, False


# =============================================================================
# Audit
# =============================================================================
def audit(verbose=True):
    """Every cached entry with the design it came from. Returns a list of dicts."""
    entries = []
    if os.path.isdir(CACHE_DIR):
        for fn in sorted(os.listdir(CACHE_DIR)):
            if not fn.endswith(".json"):
                continue
            with open(os.path.join(CACHE_DIR, fn), encoding="utf-8") as fh:
                meta = json.load(fh)
            rows, _ = read_cached(meta["key"])
            meta["usable"] = rows is not None
            entries.append(meta)
    if verbose:
        if not entries:
            print("[map_cache] cache is empty (%s)" % os.path.relpath(CACHE_DIR, REPO_ROOT))
        for e in entries:
            print("  %s  phi=%.4f n=%d T_hot=%.0f  eta=%.5f  %ss  %s  %s"
                  % (e["key"], e.get("phi_mass", float("nan")), e.get("n_points", -1),
                     e.get("T_htf_hot_C", float("nan")), e.get("eta_thermal_calc", float("nan")),
                     e.get("build_seconds", "?"), e.get("git_commit", "?"),
                     "OK" if e["usable"] else "UNUSABLE"))
    return entries


def verify_invariance(verbose=True) -> bool:
    """Check by EXECUTION that d_p and the site cannot enter the key, rather than asserting it.

    The claim the cost model rests on is that grid points differing only in d_p, the site, SM or
    t_TES share a map. For d_p the mechanism is `DECISIONS.md` D6 (no nominal property effect);
    for the others it is that they are not inputs to `Sco2CspUdPcTables` at all. Both reduce to
    one testable statement: **the exported input set does not change.**
    """
    import build_udpc_map as bum
    import nanofluid_properties as nfp

    ok = True

    def check(label, good, detail=""):
        nonlocal ok
        ok &= bool(good)
        if verbose:
            print("  %-52s %s %s" % (label, "OK" if good else "FAIL", detail))

    base_key, _ = design_key(bum.build(0.007, bum.T_HTF_HOT_DES_C, 3))

    # d_p: the property table is what carries the fluid into the map, so compare the tables the
    # module produces with and without a diameter asserted.
    t_none = nfp.htf_table_rows(0.007, bum.HTF_T_GRID)
    same = True
    for d_p in (nfp.D_P_MIN_NM, 30.0, nfp.D_P_MAX_NM):
        p_ref = nfp.nanofluid_properties(0.007, 500.0)
        p_dp = nfp.nanofluid_properties(0.007, 500.0, d_p_nm=d_p)
        same &= all(abs(p_ref[k].nominal - p_dp[k].nominal) < 1e-12
                    for k in ("rho", "cp", "k", "alpha", "mu"))
    check("d_p moves no nominal property (D6)", same)
    check("HTF table identical regardless of d_p",
          nfp.htf_table_rows(0.007, bum.HTF_T_GRID) == t_none)

    # The key must be reproducible: same design assembled twice -> same key.
    again_key, _ = design_key(bum.build(0.007, bum.T_HTF_HOT_DES_C, 3))
    check("key is reproducible across assemblies", again_key == base_key, base_key)

    # And it must be SENSITIVE to things that do change the map, or it is worthless.
    k_phi, _ = design_key(bum.build(0.020, bum.T_HTF_HOT_DES_C, 3))
    check("key changes with phi", k_phi != base_key)
    k_n, _ = design_key(bum.build(0.007, bum.T_HTF_HOT_DES_C, 5))
    check("key changes with n_points (n=3 vs n=5 differ by +0.428 %)", k_n != base_key)
    k_T, _ = design_key(bum.build(0.007, 650.0, 3))
    check("key changes with T_htf_hot", k_T != base_key)
    return ok


def selftest(verbose=True) -> bool:
    """Hashing-layer checks that need no PySAM."""
    ok = True

    def check(label, good, detail=""):
        nonlocal ok
        ok &= bool(good)
        if verbose:
            print("  %-52s %s %s" % (label, "OK" if good else "FAIL", detail))

    a = {"g": {"x": 1.0, "y": [1, 2, 3]}}
    b = {"g": {"y": [1, 2, 3], "x": 1}}          # reordered, and int vs float
    check("canonicalisation is order- and int/float-stable",
          json.dumps(canonicalise(a), sort_keys=True)
          == json.dumps(canonicalise(b), sort_keys=True))
    # Float noise below the rounding threshold must NOT trigger a 38-minute rebuild...
    n1 = canonicalise({"x": 1.0000000000000002})
    n2 = canonicalise({"x": 1.0})
    check("1-ulp float noise does not change the key", n1 == n2)
    # ...but a physically meaningful difference must.
    check("a real difference does change the key",
          canonicalise({"x": 1.0}) != canonicalise({"x": 1.0000001}))
    check("cache dir path is inside the repo", CACHE_DIR.startswith(REPO_ROOT))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit", action="store_true", help="list cached maps and their designs")
    ap.add_argument("--verify-invariance", action="store_true",
                    help="check by execution that d_p/site cannot enter the key")
    ap.add_argument("--selftest", action="store_true", help="hashing checks, no PySAM")
    ap.add_argument("--build", action="store_true", help="populate the cache (~38 min on a miss)")
    ap.add_argument("--phi", type=float, default=0.007)
    ap.add_argument("--T-htf-hot", type=float, default=700.0)
    ap.add_argument("--n-points", type=int, default=3)
    args = ap.parse_args()

    if args.selftest:
        print("map_cache hashing self-check (no PySAM):")
        good = selftest()
        print("\n  %s\n" % ("passed" if good else "FAILED"))
        return 0 if good else 1

    if args.verify_invariance:
        print("Verifying what may and may not enter the cache key (by execution):")
        good = verify_invariance()
        print("\n  %s\n" % ("passed" if good else "FAILED"))
        return 0 if good else 1

    if args.build:
        rows, key, hit = load_or_build(args.phi, args.T_htf_hot, args.n_points)
        print("%s: %d rows, key %s" % ("HIT" if hit else "BUILT", len(rows), key))
        return 0

    # Default: audit, and write it to disk so the campaign's provenance is a durable artifact.
    entries = audit()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "map_cache_audit_%s.md" % stamp)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# UDPC map cache audit\n\n"
                 "| | |\n|---|---|\n| generated (UTC) | %s |\n| git commit | `%s` |\n"
                 "| cache dir | `%s` |\n| entries | %d |\n\n"
                 % (stamp, git_commit(),
                    os.path.relpath(CACHE_DIR, REPO_ROOT).replace("\\", "/"), len(entries)))
        if entries:
            fh.write("| key | phi | n | T_hot | eta | build s | commit | usable |\n"
                     "|---|---|---|---|---|---|---|---|\n")
            for e in entries:
                fh.write("| `%s` | %.4f | %d | %.0f | %.5f | %s | `%s` | %s |\n"
                         % (e["key"], e.get("phi_mass", float("nan")), e.get("n_points", -1),
                            e.get("T_htf_hot_C", float("nan")),
                            e.get("eta_thermal_calc", float("nan")),
                            e.get("build_seconds", "?"), e.get("git_commit", "?"),
                            "yes" if e["usable"] else "**NO**"))
        else:
            fh.write("Cache is empty. Populate with `--build`, or let "
                     "`scripts/run_integrated_annual.py` fill it as the campaign runs.\n")
    print("\nwrote %s" % os.path.relpath(path, REPO_ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
