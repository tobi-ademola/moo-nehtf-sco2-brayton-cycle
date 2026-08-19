# Integrated annual run -- nano-chloride tower + sCO2 UDPC block

| | |
|---|---|
| script | `scripts/run_integrated_annual.py` |
| run (UTC) | 20260819T114116Z |
| git commit | `14092e3-dirty` |
| PySAM | 7.1.1.post1 (bundled ssc 306) |
| weather | Morocco/Ouarzazate NSRDB TMY |

```
====================================================================================================
INTEGRATED ANNUAL RUN -- nano-chloride tower + sCO2 UDPC power block
  MASTER_PLAN.md §11 item 2 -- the first full-year result for the sCO2 plant
====================================================================================================

[1/1] sco2_n3
        power block     sCO2 recompression (UDPC, n=3)
        loop            T_hot 700.0 C  T_cold 533.3 C  dT 166.7 K
        design_eff      0.50547
        map             maps/sco2_udpc_phi0p0070_n3_tower7.csv (27 rows, roundtrip 0.000e+00)
        cooling         ud_f_W_dot_cool_des 1.0000 %
        annual_energy   440,206,500 kWh
        nameplate (net) 62,612.0 kW
        rec pump (des)  49.55 MW

====================================================================================================
case                 status       annual kWh   nameplate kW       dT K   pump MW
----------------------------------------------------------------------------------------------------
sco2_n3                  OK      440,206,500         62,612        167     49.55


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

   The balance is the load-bearing check, not the per-component signs: it exercises
   every h, every s, both mass flows and the salt properties at once, so it catches
   scaling errors that sign checks cannot.

TIER 2 -- ANNUAL, plant level, with an HOURLY dead state T0(t) = tdry(t)
case            Ex_solar MWh    Ex_htf MWh   eta_II pl   eta_II pb  eta_II col neg Ed h
----------------------------------------------------------------------------------------------------
sco2_n3            3,027,761       802,379      0.1454      0.7270      0.2650       27

   ⚠ NEGATIVE HOURLY Ed in: sco2_n3
   Ed = Ex_htf - W_gross < 0 is a second-law violation in that hour. Either the
   HTF cp, the temperatures or the gross work are inconsistent -- do NOT report
   the annual eta_II until this is explained.

   ⚠ TIER 2 LUMPS THE POWER BLOCK, deliberately. The UDPC map carries normalised
   response SHAPES only (CLAUDE.md §4.11), so there are no per-hour state points and
   no per-component Ed at any hour but the design point. Ed_power_block is the exact
   lumped quantity Ex_htf - W_gross. Do NOT infer an annual component ranking from
   the tier-1 design-point one: off-design shifts it.
```
