# Integrated annual run -- nano-chloride tower + sCO2 UDPC block

| | |
|---|---|
| script | `scripts/run_integrated_annual.py` |
| run (UTC) | 20260819T184959Z |
| git commit | `b313c6d-dirty` |
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
        map             cache:b45c75dc94e7f094 (27 rows, roundtrip 0.000e+00)
        map source      cache-hit(legacy-import, unverified)
        cooling         ud_f_W_dot_cool_des 1.0000 %
        annual_energy   440,206,500 kWh
        nameplate (net) 62,612.0 kW
        rec pump (des)  49.55 MW

[2/3] sco2_n5
        power block     sCO2 recompression (UDPC, n=5)
        loop            T_hot 700.0 C  T_cold 533.3 C  dT 166.7 K
        design_eff      0.50547
        map             cache:8d85dab5585b29bf (45 rows, roundtrip 0.000e+00)
        map source      legacy-import(unverified)
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
   Adequate FOR SCREENING: the shift is small and, being a property of the
   surface rather than of any one design, is expected to move all designs the
   same way -- so Morris rankings survive it and can use the cheap map.
   NOT a convergence claim. This is a single 3->5 step; SAM's own default
   surface is 20 points per axis, and neither 3 nor 5 has been shown converged
   against it. A FINAL reported annual number should use the densest map that
   the build budget allows, and quote this delta as its resolution uncertainty.

POWER BLOCK (the §7.5 inference, now tested)
   sCO2 vs steam at IDENTICAL fluid, temperatures and field: +13.05 % annual energy
   design_eff 0.50547 (sCO2) vs 0.41200 (steam)

====================================================================================================
EXERGY -- Objective 2, DECISIONS.md D1
====================================================================================================
TIER 1 -- DESIGN POINT, per component (from ssc's own h and s)
   sco2_n3
      eta_II (cycle)     0.7626   = W_net 115,000.0 kW / Ex_in(salt) 150,798.9 kW
      total Ed           35,775.9 kW
      largest destroyer  HTR  high-T recup at 40.5 %
      breakdown          HTR=14486.5 kW (40.5%); TURB=6204.5 kW (17.3%); COOL=5493.8 kW (15.4%); LTR=4131.4 kW (11.5%); PHX=2164.3 kW (6.0%); RC=1986.7 kW (5.6%); MC=1308.6 kW (3.7%); MIX=0.1 kW (0.0%)
      balance            residual +1.53e-04 relative -> CLOSES
      all Ed > 0         yes
   sco2_n5
      eta_II (cycle)     0.7626   = W_net 115,000.0 kW / Ex_in(salt) 150,798.9 kW
      total Ed           35,775.9 kW
      largest destroyer  HTR  high-T recup at 40.5 %
      breakdown          HTR=14486.5 kW (40.5%); TURB=6204.5 kW (17.3%); COOL=5493.8 kW (15.4%); LTR=4131.4 kW (11.5%); PHX=2164.3 kW (6.0%); RC=1986.7 kW (5.6%); MC=1308.6 kW (3.7%); MIX=0.1 kW (0.0%)
      balance            residual +1.53e-04 relative -> CLOSES
      all Ed > 0         yes
   steam_same_T -- not applicable -- tier 1 is the sCO2 cycle's per-component exergy and this case runs SAM's steam Rankine block

   The balance is the load-bearing check, not the per-component signs: it exercises
   every h, every s, both mass flows and the salt properties at once, so it catches
   scaling errors that sign checks cannot.

TIER 2 -- ANNUAL, plant level, with an HOURLY dead state T0(t) = tdry(t)
case            Ex_solar MWh    Ex_htf MWh   eta_II pl   eta_II pb  eta_II col neg Ed h
----------------------------------------------------------------------------------------------------
sco2_n3            3,027,761       813,290      0.1454      0.7173      0.2686        0
sco2_n5            3,025,503       813,215      0.1461      0.7193      0.2688        0
steam_same_T       3,014,679       884,263      0.1292      0.6300      0.2933        0

   Hourly Ed >= 0 in every operating hour of every case -- the annual accounting
   is second-law consistent, which is what makes it safe to collect at every
   swept point of the campaign.

   ⚠ TIER 2 LUMPS THE POWER BLOCK, deliberately. The UDPC map carries normalised
   response SHAPES only (CLAUDE.md §4.11), so there are no per-hour state points and
   no per-component Ed at any hour but the design point. Ed_power_block is the exact
   lumped quantity Ex_htf - W_gross. Do NOT infer an annual component ranking from
   the tier-1 design-point one: off-design shifts it.
```
