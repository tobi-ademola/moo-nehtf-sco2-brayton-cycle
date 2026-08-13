# reference/prior_project — READ THIS BEFORE USING ANYTHING HERE

> **These files are from a DIFFERENT, EARLIER project. Nothing in this directory has been
> validated for this one. Do not import from it, do not run it, do not cite its numbers.**

**Added:** 2026-08-13 — Session E. **Status:** reference material, frozen.

---

## What these are

| File | What it is |
|---|---|
| `sam_case.py` | A `TcsmoltenSalt` case builder from the prior project: custom chloride HTF via `rec_htf = 50`, sCO₂ power block via a user-defined map, `Singleowner` financials. |
| `sco2_cycle_map.py` | The prior project's offline UDPC performance-map generator (`Sco2CspUdPcTables` → tower table). |

They were supplied deliberately, as **references to mine for information** while building this
project's own modules — not as code to adopt. They are kept in the repo, rather than deleted, so
that the findings harvested from them (`CLAUDE.md` §4.11–§4.14) remain traceable to a source a
reader can open and check. That is their only job.

The third file that arrived with them, `nanofluid_properties.py`, is **not** in this category: it
is a validated Objective-1 asset and lives at `scripts/nanofluid_properties.py`, in active use.

---

## Why they cannot be used directly

### 1. The cycle design contradicts this project's validated baseline

`sco2_cycle_map.py`'s `DESIGN` / `COMMON` / `HEATEX` blocks describe a **different cycle** from the
one this project validated against Dostal (2004). Adopting them would silently discard the
validation:

| Quantity | Prior project | **This project (validated case F)** |
|---|---|---|
| η_thermal | 0.44 target, 0.440 baseline | **0.51289** — matched to Dostal +0.019 pp |
| `recomp_frac` | **0.113** | **0.4097** |
| `design_method` | 1 (target efficiency) | **3** (specify each recuperator) |
| `is_recomp_ok` | 1 (optimiser chooses) | **−0.4097** (pinned) |
| η_isen mc / rc | 0.85 / 0.85 | **0.89 / 0.89** |
| `P_high_limit` | 25 MPa | **20 MPa** |

### 2. One of those settings is a documented failure mode in *this* repo

`design_method = 1` together with `is_recomp_ok = 1` is precisely the combination `CLAUDE.md` §4.3
warns collapses the cycle toward a simple recuperated layout while still reporting success. The
prior project's own recorded baseline of **`recomp_frac = 0.113`** is that failure mode showing
up in its results. Do not copy the pattern.

`UA_recup_tot_des = 15.0`, labelled MW/K, runs straight into the UA unit trap of `CLAUDE.md` §4.7.

### 3. The section cross-references point at a different file

Both modules cite "CLAUDE.md section 6" and "section 7" for verification of their constants. Those
refer to the **prior project's** `CLAUDE.md`. In *this* repo those numbers address the HTF fluid
codes (§6) and the pinned sanity baselines (§7), so the citations resolve to unrelated content and
will read as validated-here when they are not. Every claim in these files is **unverified in this
environment** unless it also appears in this repo's `CLAUDE.md` with its own evidence.

### 4. Paths assume the prior project's layout

`weather_data/redstone_tmy.csv` and `maps/` do not exist here; this repo's TMY lives in
`data/tmy/`. See `CLAUDE.md` §5.

---

## What was harvested (and where it went)

Everything judged worth keeping was re-derived, re-anchored and written into this project's own
knowledge base and scripts:

- **UDPC layout reconciliation** — the 13-column per-axis → 7-column combined transform, level
  ordering, stacking order, and the unnormalised cooling column → `CLAUDE.md` §4.11, implemented
  in `scripts/build_udpc_map.py`.
- **UDPC design-magnitude restoration** — `ud_f_W_dot_cool_des`, `ud_m_dot_water_cool_des`,
  `design_eff`, `P_ref` → `CLAUDE.md` §4.12.
- **`field_fl_props` input name + the kJ/kg-K cp unit** → `CLAUDE.md` §6, implemented in
  `scripts/htf_sam_bridge.py`.
- **`Singleowner.from_existing()` ordering** → `CLAUDE.md` §4.13.
- **Off-design sweep corners crashing on a custom fluid** → `CLAUDE.md` §4.14.

If you need something from these files that is not in that list, treat it as an untested claim and
verify it before use.
