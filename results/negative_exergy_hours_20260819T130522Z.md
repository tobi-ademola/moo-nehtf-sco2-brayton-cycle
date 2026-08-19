# Negative-Ed hours — diagnosing the annual exergy guard

| | |
|---|---|
| script | `scripts/diagnose_negative_exergy_hours.py` |
| case | `sco2_n3` |
| run (UTC) | 20260819T130522Z |
| git commit | `400e230-dirty` |

## 1. The offending hours

**27 of 6039 operating hours** have `Ed = Ex_htf - W_gross < 0`, i.e. 0.45 %.

| h | m_dot_pc | T_pc_in | T_pc_out | loop dT | q_pb | q_pc_startup | P_cycle | eta | Ex_htf | **Ed** | cp |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 80.7 | 586.4 | 533.3 | 53.0 | 14.61 | 0.00 | 4.64 | 0.3174 | 3.243 | **-1.394** | 1.1288 |
| 811 | 83.4 | 585.6 | 533.4 | 52.2 | 14.86 | 0.00 | 4.86 | 0.3271 | 3.245 | **-1.615** | 1.1290 |
| 851 | 85.6 | 581.4 | 533.4 | 48.0 | 14.60 | 0.00 | 4.90 | 0.3352 | 3.048 | **-1.847** | 1.1301 |
| 1060 | 79.7 | 583.5 | 533.4 | 50.1 | 14.21 | 0.00 | 4.63 | 0.3257 | 2.988 | **-1.641** | 1.1296 |
| 1804 | 73.8 | 579.6 | 533.4 | 46.2 | 13.16 | 0.00 | 4.27 | 0.3249 | 2.558 | **-1.717** | 1.1307 |
| 2879 | 86.5 | 587.9 | 533.4 | 54.5 | 15.45 | 0.00 | 5.01 | 0.3243 | 3.536 | **-1.474** | 1.1284 |
| 2908 | 123.0 | 610.9 | 533.4 | 77.6 | 21.89 | 0.00 | 7.26 | 0.3317 | 7.040 | **-0.223** | 1.1220 |
| 2980 | 128.1 | 613.9 | 533.4 | 80.6 | 22.77 | 0.00 | 7.59 | 0.3334 | 7.584 | **-0.010** | 1.1212 |
| 3869 | 117.9 | 607.8 | 533.4 | 74.4 | 21.02 | 0.00 | 6.96 | 0.3313 | 6.478 | **-0.485** | 1.1229 |
| 4061 | 70.3 | 577.3 | 533.4 | 44.0 | 12.54 | 0.00 | 4.12 | 0.3289 | 2.293 | **-1.832** | 1.1313 |
| 4301 | 115.3 | 605.5 | 533.4 | 72.2 | 20.47 | 0.00 | 6.84 | 0.3339 | 6.105 | **-0.730** | 1.1235 |
| 4805 | 96.2 | 593.9 | 533.4 | 60.5 | 17.15 | 0.00 | 5.75 | 0.3353 | 4.251 | **-1.500** | 1.1267 |
| 5619 | 94.1 | 592.7 | 533.4 | 59.3 | 16.77 | 0.00 | 5.64 | 0.3359 | 4.065 | **-1.571** | 1.1271 |
| 6076 | 119.2 | 608.7 | 533.4 | 75.3 | 21.24 | 0.00 | 7.06 | 0.3321 | 6.607 | **-0.448** | 1.1226 |
| 6100 | 122.4 | 610.7 | 533.4 | 77.4 | 21.82 | 0.00 | 7.25 | 0.3325 | 6.969 | **-0.285** | 1.1221 |
| 6436 | 97.7 | 594.6 | 533.4 | 61.3 | 17.37 | 0.00 | 5.72 | 0.3292 | 4.442 | **-1.277** | 1.1265 |
| 6603 | 121.3 | 610.1 | 533.4 | 76.7 | 21.63 | 0.00 | 7.18 | 0.3319 | 6.860 | **-0.320** | 1.1222 |
| 6651 | 119.3 | 608.1 | 533.4 | 74.7 | 21.17 | 0.00 | 7.05 | 0.3329 | 6.560 | **-0.487** | 1.1228 |
| 6747 | 125.5 | 612.7 | 533.4 | 79.3 | 22.37 | 0.00 | 7.39 | 0.3306 | 7.365 | **-0.029** | 1.1215 |
| 6915 | 123.0 | 611.1 | 533.4 | 77.7 | 21.92 | 0.00 | 7.26 | 0.3314 | 7.057 | **-0.208** | 1.1220 |
| 6939 | 122.5 | 610.8 | 533.4 | 77.4 | 21.83 | 0.00 | 7.26 | 0.3328 | 6.971 | **-0.293** | 1.1221 |
| 7246 | 84.5 | 578.7 | 533.4 | 45.2 | 14.25 | 0.00 | 4.79 | 0.3359 | 2.843 | **-1.945** | 1.1309 |
| 7412 | 91.4 | 590.2 | 533.4 | 56.8 | 16.23 | 0.00 | 5.31 | 0.3274 | 3.872 | **-1.441** | 1.1277 |
| 7563 | 114.1 | 605.4 | 533.4 | 72.1 | 20.34 | 0.00 | 6.63 | 0.3261 | 6.153 | **-0.479** | 1.1235 |
| 7697 | 86.8 | 580.0 | 533.4 | 46.5 | 14.59 | 0.00 | 4.90 | 0.3360 | 3.003 | **-1.900** | 1.1305 |
| 7991 | 81.3 | 584.5 | 533.4 | 51.2 | 14.53 | 0.00 | 4.73 | 0.3254 | 3.111 | **-1.616** | 1.1293 |
| 8457 | 125.9 | 607.0 | 533.4 | 73.6 | 21.67 | 0.11 | 7.16 | 0.3304 | 6.919 | **-0.240** | 1.1231 |

## 2. Four candidate explanations, tested against that dump

| # | candidate | test | result |
|---|---|---|---|
| a | **Startup / shutdown transient** | `q_pc_startup > 0` in the hour | **1 of 27** (4 %) |
| b | **Stream energy ≠ cycle thermal input** | `m·cp·ΔT` vs `q_pb` | median -61.2 %, worst -72.1 % |
| c | **Hourly η above design** (map extrapolating) | `eta > design_eff` | **0 of 27** |
| d | **Very low mass flow** | `m_dot < 10 % of max` | **24 of 27** |

## 3. How much does this move the annual number?

The offending hours sum to **-27.0 MWh** of negative Ed. Setting them aside entirely changes the annual power-block exergy destruction by that amount — decide whether that is material against the totals in the integrated-run artifact before deciding how much effort the fix deserves.

## 4. Verdict

**(a) is PARTIAL: 1 of 27 offending hours carry a startup term.** Startup explains some but not all of them, so the remaining 26 need their own account before the annual eta_II is quoted. Look at candidates (b)-(d) above for those rows specifically.

⚠ **Until this is resolved, the annual `eta_II_power_block` should not be quoted.** The integrated-run report already refuses to endorse it while `negative_Ed_hours` is non-zero; that refusal is deliberate and should not be relaxed to make a table look tidy.
