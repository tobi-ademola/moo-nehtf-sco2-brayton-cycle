# sCO2 UDPC design point (design-only run)

| | |
|---|---|
| script | `scripts/build_udpc_map.py --design-only` |
| run (UTC) | 20260813T064746Z |
| git commit | `b991b33-dirty` |
| phi | 0.0070 |

```
====================================================================================================
sCO2 UDPC MAP -> TcsmoltenSalt BRIDGE   (MASTER_PLAN.md §11 item 2)
  cycle pinned to the validated case F baseline; phi = 0.0070 (0.7 wt%)
====================================================================================================

solving the DESIGN POINT only (--design-only) ...
   solved

DESIGN POINT
   eta_thermal_calc     0.50547   (case F 0.51289 -> -0.742 pp)
   recomp_frac          0.40970   (pinned at 0.4097)
   T_turb_in            680.000 C   T_comp_in 32.000 C
   P_comp_out / in      20.0000 / 7.6923 MPa   (PR 2.6000)
   eff_HTR / eff_LTR    0.97510 / 0.93098
   T_htf_cold_des       533.340 C
```
