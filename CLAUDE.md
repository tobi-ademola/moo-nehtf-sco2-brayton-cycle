# CLAUDE.md — Claude Code operating instructions (PySAM lane)

> Read this before touching anything. It is written so a **fresh Code session or a brand-new
> account** can run the pipeline cold with zero prior context. Companion to `MASTER_PLAN.md`.

**Last updated:** 2026-08-12 — Session C (Dostal 2004 literature validation; standing documentation rules)
**Machine:** Windows 11 Pro 10.0.26200, win32
**Repo root:** `C:\Users\meade\moo-nehtf-sco2-brayton-cycle`

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
| Python | **3.13.14** | `.venv\Scripts\python.exe --version` |
| Virtualenv | `.venv\` in repo root | — |
| PySAM | **NREL-PySAM 7.1.1.post1** | `pip list` |
| PySAM's bundled ssc | **ssc 306**, build `Windows 64 bit Visual C++ Apr 24 2026 01:21:21` | `ctypes` on `.venv\Lib\site-packages\PySAM\ssc.dll` |
| numpy | **2.5.2** | installed Session B (was **absent** — PySAM 7.1.1 does not pull it in) |
| CoolProp | **8.0.0** | installed Session C — independent CO₂ properties for validation |
| SAM install A | **`C:\SAM\2025.4.16`** → ssc **306**, build `Apr 21 2026 10:12:37` | `ctypes` on its `x64\ssc.dll` |
| SAM install B | **`C:\SAM\2026.7.3`** → ssc **308**, build `Jul  7 2026 00:00:07` | `ctypes` on its `x64\ssc.dll` |

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
cd C:\Users\meade\moo-nehtf-sco2-brayton-cycle
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

---

## 5. WEATHER FILES AVAILABLE

In `C:\SAM\2025.4.16\solar_resource\` (2026.7.3 has the same set):
`blythe_ca`, **`daggett_ca`** (CSP default), `des_moines_ia`, `fargo_nd`, `imperial_ca`,
`phoenix_az`, `tucson_az` — all `psmv3_60_tmy`.

Already downloaded by the user, in `C:\Users\meade\SAM Downloaded Weather Files\`:
`-28.2856_23.3667_..._nsrdb-msg-v1-0-0-tmy_60_tmy.csv` — **lat −28.29, lon 23.37 = Northern Cape,
South Africa (Upington region).** This is a ready-made **Objective 5 (Southern Africa)** site.
A MENA site still needs downloading.

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

**Dostal 2004 literature validation** (`scripts/validate_dostal.py`, base case: TIT 700 °C,
T_mc_in 32 °C, P_high 20 MPa, PR 2.6, f_rc 0.39, eta_mc/rc 0.89, eta_t 0.90, recuperator
effectiveness 0.95 both, zero pressure loss):
```
eta_thermal_calc = 0.51532    <-- Dostal reports 51.27 % (+0.26 pp)
P_comp_in = 7.6923 MPa        P_comp_out = 20.0000 MPa
recomp_frac = 0.39000         m_dot_co2 = 87.269 kg/s
T_turb_out = 573.364 C        T_HTR_HP_out = 522.367 C
total Sgen = +9.91403 kW/K    (all 8 components > 0)
```
Converges without trouble at the near-critical compressor inlet — the `P_LOW_OFFSET_MPA`
fallback never fires. Dostal's 51.27 % is reproduced at recuperator effectiveness ≈ 0.9467.
ssc's internal CO₂ properties match CoolProp to 1.6e-04 kJ/kg in *h* and 3.4e-07 kJ/kg-K in *s*,
so ssc is effectively REFPROP-equivalent and needs no external property lane.

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
