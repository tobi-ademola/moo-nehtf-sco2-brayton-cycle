# CLAUDE.md — Claude Code operating instructions (PySAM lane)

> Read this before touching anything. It is written so a **fresh Code session or a brand-new
> account** can run the pipeline cold with zero prior context. Companion to `MASTER_PLAN.md`.

**Last updated:** 2026-08-14 — Session F (**the UDPC blocker is cleared: the sweep converges at the
full case F design in ~38 min; it was never over-constrained, only slower than every timeout used
to test it — see §4.15**)
**Machine:** Windows 11 Pro 10.0.26200, win32
**Repo root:** `C:\Users\chukw\code\moo-nehtf-sco2-brayton-cycle`

---

## 0. STANDING DOCUMENTATION RULES (apply every session, no exceptions)

These are process rules, not suggestions — they hold regardless of how small the task looks.

1. **Every script is a durable artifact.** Commit it under `scripts/`, with a header comment
   stating its **purpose**, **inputs**, and **how to run it**. A future session (or a fresh
   account with zero context) must be able to review and re-run it — never rewrite it from
   scratch. Do not write throwaway one-liners or inline `python -c` for anything that produces
   a result worth keeping; if it matters, it gets a file.
2. **Every result goes to disk, not just the terminal.** Validation tables, sweep outputs,
   state-point dumps, etc. → write to `results/` as CSV/JSON/MD, named or stamped with a
   timestamp and the script + git commit (`git rev-parse --short HEAD`) that produced them. The
   terminal is ephemeral; the thesis and other agents/sessions read from disk, not scrollback.
3. **Log the session in `PROGRESS_LOG.md`** (append-only, dated): what ran, which script, what
   the result was, what's next. See MASTER_PLAN.md §8 for the log's role in the knowledge base.
4. **End every session by updating in place any project knowledge file you touched**
   (`CLAUDE.md`, `MASTER_PLAN.md`, `PROPERTIES.md`, `SOURCES.md`, `VALIDATION.md`, `README.md`)
   so it reflects the current state — not a stale snapshot from when the file was written.

---

## 1. ENVIRONMENT — exact versions (all verified by execution, not assumed)

| Thing | Value | How verified |
|---|---|---|
| Python | **3.13.15** (was 3.13.14 pre-migration — patch bump, no effect on results) | `.venv\Scripts\python.exe --version` |
| Virtualenv | `.venv\` in repo root — **gitignored, rebuilt Session E on this machine** | — |
| PySAM | **NREL-PySAM 7.1.1.post1** | `pip list` |
| PySAM's bundled ssc | **ssc 306**, build `Windows 64 bit Visual C++ Apr 24 2026 01:21:21` | `ctypes` on `.venv\Lib\site-packages\PySAM\ssc.dll` |
| numpy | **2.5.2** | installed Session B (was **absent** — PySAM 7.1.1 does not pull it in) |
| CoolProp | **8.0.0** | installed Session C — independent CO₂ properties for validation |
| SAM install A | **ABSENT on this machine** (was `C:\SAM\2025.4.16` → ssc 306) | `Test-Path C:\SAM` → false, 2026-08-13 |
| SAM install B | **ABSENT on this machine** (was `C:\SAM\2026.7.3` → ssc 308) | `Test-Path C:\SAM` → false, 2026-08-13 |

### 1.0 THE PYTHON VERSION IS NOT OPTIONAL — 3.14 CANNOT RUN THIS PROJECT

This machine shipped with **Python 3.14 only** (`C:\Python314`). **NREL-PySAM publishes no 3.14
wheels** — not "an older version resolves", *zero* versions resolve:

```
ERROR: Could not find a version that satisfies the requirement NREL-PySAM==7.1.1.post1
       (from versions: none)
```

That error looks like a network or index failure and is not. Confirm the network is fine by
resolving something else (`pip index versions CoolProp` lists ~50 versions) before chasing it.
**Python 3.13 was installed alongside 3.14** (`winget install --id Python.Python.3.13 --scope user`,
user scope, no admin) at `%LOCALAPPDATA%\Programs\Python\Python313`. Build the venv with
`py -3.13`, never bare `py` — the launcher's default is still 3.14.

### 1.0a NO SAM GUI INSTALL ON THIS MACHINE

`C:\SAM\` does not exist here. This blocks **only** the three things §1.1 lists — GUI
cross-checking, and the bundled weather/component libraries. It does **not** affect PySAM: the
cycle scripts (`smoke_test.py`, `validate_dostal.py`) need no weather file and run fine.
`VALIDATION.md` §1.4 (the SAM 2025.4.16 GUI cross-check) stays blocked until SAM is installed;
`TcsmoltenSalt` annual runs need a weather file from `data/tmy/` (§5) instead of `C:\SAM\...`.

### 1.1 THE VERSION GOTCHA THAT MATTERS MOST

**PySAM does not use either SAM install's `ssc.dll`.** It ships and loads its **own** copy at
`.venv\Lib\site-packages\PySAM\ssc.dll`. Nothing you install, upgrade, or uninstall in
`C:\SAM\...` changes PySAM's numbers.

Consequence — the correct pairing for this project:

```
PySAM 7.1.1  ==  ssc 306  ==  SAM 2025.4.16      <-- cross-check GUI numbers against THIS
                 ssc 308  ==  SAM 2026.7.3       <-- NEWER than PySAM. Do NOT compare against it.
```

If you open the **2026.7.3** GUI and compare its results to a PySAM run, small unexplained
deltas are expected and are a *version artifact, not a modelling error*. **Use SAM 2025.4.16
for every GUI cross-check.** Do not "fix" a discrepancy that is really ssc 306 vs 308.

The SAM installs are still needed, for three things only:
1. **Weather files** — `C:\SAM\2025.4.16\solar_resource\*.csv`
2. **Component libraries** — `C:\SAM\2025.4.16\libraries\*.csv`
3. **GUI cross-checking** (2025.4.16 only)

---

## 2. HOW TO RUN A SCRIPT

PowerShell (primary shell on this machine):

```powershell
cd C:\Users\chukw\code\moo-nehtf-sco2-brayton-cycle
.\.venv\Scripts\python.exe -u .\scripts\your_script.py
```

**Always pass `-u`.** ssc is native code; on a hard crash Python's buffered stdout is lost and
you get a silent empty log. `-u` guarantees you keep everything printed up to the crash.

Smoke test (should print a solved recompression cycle and a full state-point table):

```powershell
.\.venv\Scripts\python.exe -u .\scripts\smoke_test.py
```

Literature validation — the sCO₂ cycle at Dostal 2004's high-performance design point, with
every node re-evaluated against CoolProp and full mixer / second-law / power-balance checks.
Run this whenever you touch the cycle model; it asserts on anything that drifts:

```powershell
.\.venv\Scripts\python.exe -u .\scripts\validate_dostal.py
```

Rebuilding the env from scratch on a new machine:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install "NREL-PySAM==7.1.1.post1" numpy CoolProp
```

`numpy` is **not** a PySAM dependency — install it explicitly or every script dies on import.
`CoolProp` is needed only by `validate_dostal.py`. Import order vs PySAM does not matter.

---

## 3. THE THREE MODULES THIS PROJECT USES

| PySAM module | Role |
|---|---|
| `PySAM.Sco2CspSystem` | Standalone sCO₂ recompression cycle — design + off-design. **Source of all state points.** |
| `PySAM.Sco2CspUdPcTables` | Same cycle, emits a **user-defined power-cycle (UDPC) table** for the annual model. |
| `PySAM.TcsmoltenSalt` | Full molten-salt tower plant: heliostats, receiver, TES, annual simulation, hydraulics. |

**There is no sCO₂-tower configuration in the SAM GUI.** Confirmed by inspecting
`C:\SAM\2026.7.3\runtime\defaults\` — only `MSPT_*`, `MSPT IPH_*`, `MSPTV2_None`. The sCO₂ block
is reachable **only** through PySAM. The intended coupling is:

```
Sco2CspUdPcTables  --(ud_ind_od table)-->  TcsmoltenSalt
                                            .PowerCycle.pc_config = 1        (user-defined PC)
                                            .UserDefinedPowerCycle.ud_is_sco2_regr = 1
```

`ud_is_sco2_regr` is an sCO₂-aware regression flag — SAM explicitly supports this bridge.

---

## 4. GOTCHAS (each one cost real time — 4.1–4.6 Session B, 4.7–4.10 Session C)

### 4.1 Some `od_*` inputs are arrays, not scalars
`od_generate_udpc`, `od_set_control`, `od_T_t_in_mode`, `od_cases`, `od_P_mc_in_sweep`,
`od_T_mc_in_sweep` are **matrix/array** inputs. Assigning an int raises:
```
TypeError: error converting tuple to array: argument must be iterable
```
For a design-only run, **just don't set them.**

### 4.2 Bad input VALUES SEGFAULT the interpreter, they don't raise
Two confirmed triggers, both exit 139 with unflushed stdout lost:
- a malformed `htf_props` table (wrong column count — some shapes raise cleanly, some crash);
- a `0.0` left in an *unused* recuperator spec (`HTR_UA_des_in`, `HTR_min_dT_des_in`) — ssc reads
  them regardless of `HTR_design_code`, so give the inactive ones non-zero placeholders (4.7).

**Run any risky probe in its own subprocess with `-u`** so one crash doesn't lose the sweep.
See also 4.8, a third segfault with an entirely different cause.

### 4.3 `Sco2CspSystem` collapses to a simple cycle unless you pin the recompression fraction
With `design_method = 1` (target efficiency) or `2` (total recuperator UA), the internal optimizer
will happily return **`recomp_frac = 0.0`**, NaN out every HTR output (`q_dot_HTR`, `eff_HTR`,
`HTR_min_dT`), and in one observed case drove the main-compressor inlet to **1.5 MPa —
subcritical and physically meaningless** — while still reporting "design optimization was successful".

**`is_recomp_ok` semantics:** `1` = optimizer may choose · `0` = simple cycle only ·
**negative = pin the recompression fraction at `abs(value)`**.

Working recipe for a genuine recompression cycle:
```python
m.SystemDesign.design_method      = 3      # specify each recuperator individually
m.HeatExchangerDesign.is_recomp_ok = -0.30 # PIN f_rc = 0.30
m.HeatExchangerDesign.HTR_design_code = 3  # 3 = specify effectiveness (see 4.7)
m.HeatExchangerDesign.LTR_design_code = 3
m.HeatExchangerDesign.HTR_eff_des_in = 0.95
m.HeatExchangerDesign.LTR_eff_des_in = 0.95
# The other two specs are ignored but must be present and NON-ZERO -- 0.0 segfaults (4.2):
m.HeatExchangerDesign.HTR_UA_des_in = m.HeatExchangerDesign.LTR_UA_des_in = 5000.0
m.HeatExchangerDesign.HTR_min_dT_des_in = m.HeatExchangerDesign.LTR_min_dT_des_in = 10.0
```
**Always assert `recomp_frac > 0` and `not isnan(q_dot_HTR)` before trusting a result.**
See 4.10 for pinning the pressure levels and the two temperatures alongside `f_rc`.

### 4.4 `TcsmoltenSalt.default("MSPTSingleOwner")` ships **without** a weather file
Reading `.SolarResource.solar_resource_file` raises before you set it:
```
Exception: Runtime error: get_solar_resource_file called for SAM_TcsmoltenSalt
           but "solar_resource_file" not assigned
```
Set it explicitly:
```python
m.SolarResource.solar_resource_file = (
    r"C:\SAM\2025.4.16\solar_resource\daggett_ca_34.865371_-116.783023_psmv3_60_tmy.csv")
```

### 4.5 State points 10 and 11 are NaN by design
`PC_IN` / `PC_OUT` (pre-compressor) exist only for **partial-cooling** (`cycle_config = 2`).
For recompression (`cycle_config = 1`) they are legitimately NaN. **Never `np.sum()` the raw
12-element state arrays** — slice `[0:10]` or use `np.nansum`.

### 4.6 Default config names are `MSPTSingleOwner`, not `MSPT`
Full list lives in `.venv\Lib\site-packages\PySAM\defaults\` (670 files). CSP tower ones are
`tcsmoltensalt_mspt{singleowner,none,merchantplant,saleleaseback,...}.df`.

### 4.7 `HTR_design_code` / `LTR_design_code` — real mapping, and a UA unit trap
```
1 = UA          2 = min approach dT          3 = effectiveness
```
Only the input matching the selected code is read; the other two are ignored — but must still be
present and **non-zero**, because `0.0` segfaults (4.2). Two traps:

- **`HTR_UA_des_in` is consumed in W/K even though it documents kW/K.** Passing `1e6` yields
  `HTR_UA_assigned = 1000` kW/K. Passing `7000` gives you 7 kW/K — a nearly inert recuperator.
- **Prefer code 3 (effectiveness).** It is scale-free, so a literature recuperator spec transfers
  to a differently sized model without rescaling, and it sidesteps the UA unit trap entirely.

`smoke_test.py` uses code **2** with `min_dT_des_in = 10.0`; that min-dT design — *not* a
UA = 7000 design — is what the section 7 baselines were generated from.

### 4.8 Never return `model.Outputs` from a function — it SEGFAULTS
The `Outputs` group does **not** hold a reference to its parent model. Hand a bare `Outputs`
back to a caller, let the model go out of scope, and the next attribute read dereferences freed
memory: **exit 139, no traceback, and no stdout at all even under `-u`.**
```python
def solve(...):
    m = S.new(); ...; m.execute(0)
    return m.Outputs      # WRONG -- m is collected on return, o is now dangling
    return m              # RIGHT -- caller does o = m.Outputs and keeps m alive
```
Vicious because the crash lands at the *caller's* first read, nowhere near the bug.

### 4.9 Mass flows are 1000x their documented units
`m_dot_co2_full` and `m_dot_htf_des` both document **kg/s** but come out 1000x larger
(87268.8 where three independent energy balances all give 87.2688 kg/s). Powers
(`t_W_dot`, `q_dot_PHX`) document **MW** but are really **kW**.

Don't trust the label — derive the flow and assert the two agree, so a future PySAM that fixes
the scaling trips the assert instead of silently skewing every exergy number:
```python
mdot = o.t_W_dot / (h[5] - h[6])                  # kg/s, from W = m*(h_in - h_out)
assert abs(mdot - o.m_dot_co2_full / 1000.0) / mdot < 1e-6
```
This bug was live in `smoke_test.py` (`/ 3600.0`) and made every printed `Sgen` 3.6x too low.

### 4.10 There is no direct `T_mc_in` or `T_turb_in` input
Both are derived, so back your boundary conditions out of the approaches:
```
T_mc_in   = T_amb_des     + dT_mc_approach
T_turb_in = T_htf_hot_des - dT_PHX_hot_approach
```
Pinning `P_high` and the pressure ratio together fully determines the pressure levels, leaving
no optimizer in the loop — which is what you want for a validation run:
```python
m.Common.P_high_limit                 = 20.0   # MPa
m.HeatExchangerDesign.is_P_high_fixed = 1      # P_high = P_high_limit exactly
m.HeatExchangerDesign.is_PR_fixed     = 2.6    # >0 = fixed PR, <0 = fixed LP at abs(value)
```

### 4.11 The UDPC table has TWO shapes and the two modules disagree about which

The map generator and the tower do **not** speak the same table format, and nothing in either
API says so. `Sco2CspUdPcTables` emits **three per-axis tables, 13 columns each**
(`T_htf_ind`, `m_dot_htf_ND_ind`, `T_amb_ind`); `TcsmoltenSalt.UserDefinedPowerCycle.ud_ind_od`
wants **one combined table, 7 columns**. This is not a version skew to route around — ssc's own
`N_udpc_common::split_ind_tbl()` splits the combined table into exactly those three. Writing the
bridge means writing the **inverse of that split** (`scripts/build_udpc_map.py`).

```
per-axis (13 col):  col 0 = swept variable
                    cols 1-3 W_gross | 4-6 Q_HTF | 7-9 W_cooling | 10-12 m_dot_water
                    each triple ordered [low, DESIGN, high] of a PAIRED variable
combined (7 col):   [T_htf, m_dot_htf_ND, T_amb, W_gross_ND, Q_HTF_ND, W_cool_ND, m_water_ND]
```

**Block structure, read off the tower's own installed default `ud_ind_od` (180×7) in this
environment — verify it this way rather than trusting any write-up, including this one:**

| block | swept (20 values) | 3 levels of | held at design |
|---|---|---|---|
| 0 | `T_htf` | `m_dot` — 0.3 / **1.0** / 1.2 | `T_amb` = 43 |
| 1 | `m_dot` | `T_amb` — 0 / **43** / 55 | `T_htf` = 574 |
| 2 | `T_amb` | `T_htf` — 500 / **574** / 580 | `m_dot` = 1.0 |

The **level is the outer loop**, the swept value the inner. Stacking order is
`T_htf → m_dot → T_amb` (`ud_power_cycle.h`). Do not reorder.

⚠ **The cooling column arrives UNNORMALISED** — order 1e-3 at design, while every other
response is 1.0 there. Divide it by its own design value when building the combined table; the
magnitude is restored on the tower side by `ud_f_W_dot_cool_des`. Miss this and the cooling
parasitic is wrong by three orders of magnitude with nothing flagging it.

### 4.12 `ud_ind_od` carries SHAPES only — set the design magnitudes or stay on the steam cycle

The combined table is entirely normalised. The scale travels separately, and if you do not set
it the tower **silently keeps its steam-Rankine defaults** — verified in this environment as
`design_eff = 0.412`, `P_ref = 115.0` MW. Everything runs; the sCO₂ block is just mis-scaled.

```python
m.PowerCycle.pc_config                            = 1     # user-defined cycle
m.UserDefinedPowerCycle.ud_is_sco2_regr           = 1     # sCO2-aware regression
m.UserDefinedPowerCycle.ud_ind_od                 = rows  # the 7-column combined table
m.UserDefinedPowerCycle.ud_f_W_dot_cool_des       = ...   # % of design gross used by cooling
m.UserDefinedPowerCycle.ud_m_dot_water_cool_des   = 0.0   # dry-cooled
m.SystemDesign.design_eff                         = ...   # <- or you keep 0.412
m.SystemDesign.P_ref                              = ...   # <- or you keep 115 MW
```

⚠ **`ud_f_W_dot_cool_des` must come from `cooler_tot_W_dot_fan`, NOT from the map's cooling
column.** This was live in `build_udpc_map.py` until 2026-08-14 and produced
`ud_f_W_dot_cool_des = 0.0000 %` — a 115 MW plant whose air cooler draws nothing, with no error
and no warning. The column's design value is ~9.971e-04 (§4.11); it is **not** a power in kW, so
dividing it by a kW design power is a category error, and it is **not** a fraction of gross
either — that reading gives 0.0997 %, still 10× low. Take the magnitude from ssc:

```python
o.cooler_tot_W_dot_fan      # 1150.0 kW at the case F design (labelled MW, really kW -- §4.9)
o.W_dot_net_less_cooling    # 113850.0 = 115000 - 1150, which confirms both value and unit
f_cool_pct = 100.0 * o.cooler_tot_W_dot_fan / W_dot_des_kWe    # = 1.0 %, matching fan_power_frac
```

The normalised **shape** still comes from the map column divided by its own design value; only
the **scale** comes from here. `scripts/check_udpc_cooling_scale.py` re-derives this in 0.1 s
without running the ~35-minute sweep.

### 4.13 `Singleowner.from_existing()` must be called BEFORE `execute()`

The financial model shares the CSP model's data container, so it has to exist before the CSP run
populates the 8760-hour `gen` array. Create it afterwards and it sees a single record:

```
invalid number of gen records (1)
```

```python
fin = Singleowner.from_existing(model, "MSPTSingleOwner")   # FIRST
model.execute(0); fin.execute(0)                            # then both
```

### 4.14 A negative nameplate is not an error to ssc

`system_capacity` is the design **net** output, and it can come out **negative** when the
pumping parasitic exceeds gross. ssc does not raise, does not warn, still returns a full 8760
`gen` array and a perfectly plausible `annual_energy`. Observed at −52,858 kW on a chloride case
whose receiver pump wanted 162 MW (`results/htf_sam_bridge_*`). **Screen every run on
`system_capacity > 0`** before believing its annual number.

Related trap in the same output set: **`capacity_factor` is not comparable across cases whose
design changes.** Its denominator is the per-case nameplate, so CF *rises* while annual energy
*falls*. Compare `annual_energy` and `system_capacity`, which share a fixed basis.

### 4.15 The UDPC sweep takes ~35 MINUTES. A short timeout manufactures false negatives.

`Sco2CspUdPcTables` with `is_generate_udpc = 1` needs **31–38 minutes** at 3 points per axis on
this machine — measured 2026-08-14 across five configurations (1882.8–2277.9 s). The design point
alone solves in **0.1 s**, so the sweep is ~20,000× the design cost and there is **no progress
output whatsoever** while it runs. It looks indistinguishable from a hang.

**This cost the project a full session and a wrong finding.** Twelve experiments across two
sessions were capped at 5–16 minutes, all reported "hangs", and a mechanism was invented to
explain them — that a fully determined recompression design is *over-constrained for UDPC
generation*. It is not. Full case F (every recuperator specified, f_rc pinned at 0.4097, both
pressures pinned, `rel_tol` 4) converges to a **usable map with `recomp_frac = 0.40970`,
η 0.50547**. Nothing had to be loosened.

> **The rule this earns:** *"did not finish inside my timeout"* is **not** *"hangs"*, and it
> carries **no information at all** until the timeout is justified against a **measured**
> completion. Before recording any non-convergence in this project, run one case to completion
> and quote its wall time, or state plainly that no completion time is known.

Two related traps found in the same investigation:

- **`design_method = 1` is not a "loose" setting — it adds a constraint.** It makes ssc solve an
  *inverse* problem (find the total recuperator conductance that hits a target efficiency), and
  with free pressures and a free `f_rc` it is the **only** configuration that genuinely fails:
  2026 s, then a real diagnostic, not a hang —
  `Can't find a value of total recuperator conductance that achieves the target cycle efficiency.`
- **Loosening buys nothing.** Freeing `f_rc`, freeing the pressures or relaxing `rel_tol` changes
  the wall time by ~20 % and does not change convergence. With everything else pinned, a free
  `f_rc` **self-selects 0.41067** against case F's pinned 0.40970 — 0.24 % apart, worth
  +0.02 pp in η. Unpinning it is nearly free, which retires the modelling decision §9.4 of
  `THESIS_SYNTHESIS.md` had reserved.

---

## 5. WEATHER FILES AVAILABLE

In `C:\SAM\2025.4.16\solar_resource\` (2026.7.3 has the same set):
`blythe_ca`, **`daggett_ca`** (CSP default), `des_moines_ia`, `fargo_nd`, `imperial_ca`,
`phoenix_az`, `tucson_az` — all `psmv3_60_tmy`.

In `data/tmy/` (gitignored — not committed, but on disk for every session):
- `158192_31.05_-6.86_tmy-2022.csv` — NSRDB TMY, **lat 31.05, lon −6.86 = Ouarzazate region,
  Morocco.** Ready-made **MENA site** (added Session D, 2026-08-13).

Previously tracked as "already downloaded by the user" at `C:\Users\meade\SAM Downloaded
Weather Files\-28.2856_23.3667_..._nsrdb-msg-v1-0-0-tmy_60_tmy.csv` — **lat −28.29, lon 23.37 =
Northern Cape, South Africa (Upington region), Objective 5 site.** **NOT FOUND on this machine**
(checked under both `meade` and `chukw` user profiles, 2026-08-13) — needs re-downloading before
next use. See `PROGRESS_LOG.md` 2026-08-13.

---

## 6. HTF FLUID CODES (`rec_htf` / `htf`)

Verified to run: `17` = Salt 60% NaNO₃ / 40% KNO₃ (**SAM default**) · `10` = 46.5%LiF-11.5%NaF-42%KF ·
`6` = 68% KCl / 32% MgCl₂ · `14` = 58% NaCl / 42% MgCl₂ · **`50` = user-defined table**.

Note `6` and `14` are **chloride** salts already built into SAM — useful as sanity anchors for the
NaCl–KCl–MgCl₂ work, though neither is the ternary eutectic.

**User-defined table format — 7 columns exactly, minimum 3 rows.** ssc error text if wrong:
> `The user defined hot fluid table must contain at least 3 rows and exactly 7 columns`

| col | quantity | units |
|---|---|---|
| 0 | Temperature | °C |
| 1 | Specific heat `Cp` | kJ/kg-K |
| 2 | Density `ρ` | kg/m³ |
| 3 | Dynamic viscosity `μ` | Pa·s |
| 4 | Kinematic viscosity `ν` | m²/s |
| 5 | Thermal conductivity `k` | W/m-K |
| 6 | Enthalpy `h` | J/kg |

Cover the **full operating temperature span** with your rows — ssc interpolates and will not
extrapolate gracefully.

**The input names, and the one unit that will bite you.** The table goes on the *receiver* group,
not a storage group — there is only **one** fluid definition and it serves receiver, field and
TES alike (`Outputs.dens_store_htf_at_T_ave` comes off the same table):

```python
m.TowerAndReceiver.rec_htf        = 50      # 17 = nitrate default
m.TowerAndReceiver.field_fl_props = rows    # the 7-column table
```

⚠ **Column 1 is kJ/(kg·K), not J/(kg·K).** `scripts/nanofluid_properties.py` works in J/(kg·K),
so the export divides by 1000. Omit that and every energy balance is 1000× out with no error
raised — `scripts/htf_sam_bridge.py` asserts cp lands in 0.1–10 rather than trusting it.

**Verified 2026-08-13 (Session E), `scripts/htf_sam_bridge.py`:** ssc **accepts** the
nano-chloride table via `rec_htf = 50`, stores it with **zero** round-trip deviation across six
cases, and the annual model solves on it. **The nano-chloride couples INSIDE SAM; no external
coupling layer is needed** — this closes the §4/§10 open flag in `MASTER_PLAN.md` and confirms
`DECISIONS.md` D2's mechanism.

⚠ **Acceptance is not validity** — see §4.14. A chloride case at the *nitrate* hot temperature
solved happily with a **negative nameplate**, because the chloride melts at 401.4 °C, cannot use
a 290 °C cold tank, and the resulting narrow loop ΔT drove the receiver pump to 162 MW. Design
receiver pump power against loop ΔT, all else equal:

| loop ΔT | W_pump,des | nameplate |
|---|---|---|
| 124 K | **162.30 MW** | **−52,858 kW (infeasible)** |
| 250 K | 27.04 MW | 82,923 kW |
| 284 K (nitrate) | 8.49 MW | 101,663 kW |

Roughly cubic, as mass flow ~ 1/ΔT in a friction-dominated loop. **Put a floor under T_hot in any
sweep of decision variables #5/#6** rather than letting the optimizer discover it.

**Grid density barely matters, and the reason is worth knowing.** ρ, cp and k are *exactly linear*
in T in the A1 correlation set, so linear interpolation on any grid reproduces them to machine
precision; only μ (exponential) and h (quadratic) can differ at all. Dropping from 6 rows to the
3-row minimum across the same span moved annual energy by **0.001 %**. A test that under-covers
the span therefore proves nothing about extrapolation — it is inconclusive by construction.

---

## 7. SANITY BASELINES — if these numbers change, something broke

**Standalone recompression cycle** (`scripts/smoke_test.py`, 10 MWe, T_htf_hot 720 °C,
T_amb 35 °C, f_rc pinned 0.30, HTR/LTR **min approach dT 10 °C** each — see 4.7, P_high 25 MPa):
```
eta_thermal_calc = 0.49257    recomp_frac = 0.30000
P_comp_in = 8.8594 MPa        P_comp_out = 25.0000 MPa
q_dot_HTR = 37396.61 kW       eff_HTR = 0.97241
q_dot_LTR = 12369.53 kW       eff_LTR = 0.91190
```

**Dostal 2004 literature validation — CASE F, the adopted baseline** (`scripts/validate_dostal.py`:
TIT 700 °C, T_mc_in 32 °C, P_high 20 MPa, PR 2.6, **f_rc 0.4097**, eta_mc/rc 0.89, eta_t 0.90,
**recuperators at 10 K approach both**, **Dostal's own per-HX ΔP**):
```
eta_thermal_calc = 0.51289    <-- Dostal reports 51.27 % (+0.019 pp)
P_comp_in = 7.6923 MPa        P_comp_out = 20.0000 MPa
recomp_frac = 0.40970         m_dot_co2 = 92.233 kg/s
eff_HTR = 0.97625             eff_LTR = 0.93095      <-- UNEQUAL, and that is correct
T_turb_out = 578.309 C        T_HTR_HP_out = 531.256 C
recup UA total = 2306.6 kW/K  total Sgen = +10.22522 kW/K  (all 8 components > 0)
```
**All 8 of Dostal's published nodes match to within 0.070 % in *h*, 0.045 % in *s*, 0.000 % in
*P*.** No node is flagged at any threshold down to 0.1 %. Converges without trouble at the
near-critical compressor inlet — the `P_LOW_OFFSET_MPA` fallback never fires. ssc's internal CO₂
properties match CoolProp to 1.0e-04 kJ/kg in *h*, so ssc is effectively REFPROP-equivalent and
needs no external property lane.

> **Why f_rc is 0.4097 and not the 0.39 Dostal's Table 10.1 states.** His Table 10.1 *f* and his
> Table 10.4 state points are separate data and they disagree. Closing the mixer on his own
> published enthalpies gives f = 0.4097; justifying 0.39 would need eta_rc = 0.752 against his
> stated 0.89/0.948. The Advanced 650 °C design, used as a control, needs only 0.932 to justify
> its stated 0.41 — so the method is sound and the contrast is real. Full argument:
> `VALIDATION.md` §2.3.4a. **This is a deliberate, evidenced departure from a published input —
> do not "correct" it back to 0.39.**

**Legacy case A — REGRESSION ANCHOR ONLY, not a validation result** (same script, second case:
equal recuperator effectiveness 0.95, lossless, f_rc 0.39):
```
eta_thermal_calc = 0.51532    recomp_frac = 0.39000    m_dot_co2 = 87.269 kg/s
P_comp_in = 7.6923 MPa        P_comp_out = 20.0000 MPa
eff_HTR = eff_LTR = 0.95000   recup UA total = 1882.3 kW/K
T_turb_out = 573.364 C        T_HTR_HP_out = 522.367 C
total Sgen = +9.91403 kW/K    (all 8 components > 0)
```
It agrees with Dostal on η to +0.26 pp but via **two cancelling errors**, with internal state
points wrong by up to 5.4 % — which is exactly why it is no longer the baseline. **Never quote
these numbers as validation.** Its job now is drift detection: it reproduces bit-for-bit across
machines, so any change here is an environment or ssc problem.

> **Reproducibility, confirmed Session E (2026-08-13):** case A was re-run on a `.venv` rebuilt
> from scratch on a different machine and a different Python patch (3.13.15 vs 3.13.14), and every
> number came back **identical to every digit printed**, as did the whole effectiveness sweep —
> including after case F was adopted and the builder refactored. Given ssc 306 these baselines are
> environment-independent, so a future deviation is a real modelling change, never drift.

**NREL MSPT reference annual run** (`MSPTSingleOwner` + Daggett TMY, stock defaults):
```
annual_energy         = 593,054,474.50 kWh
capacity_factor       = 66.5926 %
annual_W_cycle_gross  = 661,026,154.83 kWh
```

---

## 8. SESSION HYGIENE

- Temp/scratch work goes in the session scratchpad, **not** the repo.
- See **§0** for the standing documentation rules (durable scripts, results to disk,
  `PROGRESS_LOG.md`, knowledge-file updates) — they apply every session, not just this one.
- Every session ends by updating `PROGRESS_LOG.md` + emitting paste-ready blocks (MASTER_PLAN §8).
- Long annual runs: `timeout 900` is comfortable; a single `TcsmoltenSalt` annual sim is ~20–40 s.
