# Integrated annual run -- nano-chloride tower + sCO2 UDPC block

| | |
|---|---|
| script | `scripts/run_integrated_annual.py` |
| run (UTC) | 20260815T095718Z |
| git commit | `80226ab-dirty` |
| PySAM | 7.1.1.post1 (bundled ssc 306) |
| weather | Morocco/Ouarzazate NSRDB TMY |

```
====================================================================================================
INTEGRATED ANNUAL RUN -- nano-chloride tower + sCO2 UDPC power block
  MASTER_PLAN.md §11 item 2 -- the first full-year result for the sCO2 plant
====================================================================================================

[1/3] sco2_n3
        power block     sCO2 recompression (UDPC, n=3)
        loop            T_hot 700.0 C  T_cold 533.3 C  dT 166.7 K
        design_eff      0.50547
        map             maps/sco2_udpc_phi0p0070_n3_tower7.csv (27 rows, roundtrip 0.000e+00)
        cooling         ud_f_W_dot_cool_des 1.0000 %
        annual_energy   440,206,500 kWh
        nameplate (net) 62,612.0 kW
        rec pump (des)  49.55 MW

[2/3] sco2_n5
        power block     sCO2 recompression (UDPC, n=5)
        loop            T_hot 700.0 C  T_cold 533.3 C  dT 166.7 K
        design_eff      0.50547
        map             maps/sco2_udpc_phi0p0070_n5_tower7.csv (45 rows, roundtrip 0.000e+00)
        cooling         ud_f_W_dot_cool_des 1.0000 %
        annual_energy   442,092,058 kWh
        nameplate (net) 62,586.5 kW
        rec pump (des)  49.55 MW

[3/3] steam_same_T
        power block     steam Rankine (SAM default)
        loop            T_hot 700.0 C  T_cold 533.3 C  dT 166.7 K
        design_eff      0.41200
        annual_energy   389,388,747 kWh
        nameplate (net) 22,944.7 kW
        rec pump (des)  86.73 MW

====================================================================================================
case                 status       annual kWh   nameplate kW       dT K   pump MW
----------------------------------------------------------------------------------------------------
sco2_n3                  OK      440,206,500         62,612        167     49.55
sco2_n5                  OK      442,092,058         62,587        167     49.55
steam_same_T             OK      389,388,747         22,945        167     86.73

MAP RESOLUTION (THESIS_SYNTHESIS.md §17 step 2)
   n=5 vs n=3 on annual energy: +0.428 %
   A 3-point map is defensible: the surface is nearly resolution-free, so screening can use the cheap map.

POWER BLOCK (the §7.5 inference, now tested)
   sCO2 vs steam at IDENTICAL fluid, temperatures and field: +13.05 % annual energy
   design_eff 0.50547 (sCO2) vs 0.41200 (steam)
```
