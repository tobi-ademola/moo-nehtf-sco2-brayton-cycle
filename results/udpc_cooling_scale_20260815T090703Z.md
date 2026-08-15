# UDPC cooling column -- units check

| | |
|---|---|
| script | `scripts/check_udpc_cooling_scale.py` |
| run (UTC) | 20260815T090703Z |
| git commit | `fb9fd48-dirty` |
| PySAM | 7.1.1.post1 (bundled ssc 306) |

```
====================================================================================================
UDPC COOLING COLUMN -- UNITS AND ud_f_W_dot_cool_des
====================================================================================================

DESIGN POINT (no sweep)
   eta_thermal_calc   0.50547
   recomp_frac        0.40970
   W_dot_net_des in   115000.0 kWe (build_udpc_map.W_DOT_NET_DES_KWE)

CANDIDATE OUTPUTS (scalars only; CLAUDE.md §4.9 -- 'MW' often means kW)
   W_dot_net_less_cooling           113850.0
   c_tot_W_dot                      39301.73726794368
   cooler_tot_UA                    11633.064870830465
   cooler_tot_W_dot_fan             1150.0
   cooler_tot_cost_bare_erected     1397.6024952194539
   cooler_tot_cost_equipment        1164.6687460162113
   eta_thermal_net_less_cooling_des 0.5004155395830008
   mc_W_dot                         13274.54539520388
   mc_cooler_P_in                   7.7049276885216935
   mc_cooler_T_in                   71.1276631748824
   mc_cooler_UA                     11633.064870830465
   mc_cooler_W_dot_fan              1150.0
   mc_cooler_co2_deltaP_des         0.0016379123496254033
   mc_cooler_cost_bare_erected      1397.6024952194539
   mc_cooler_cost_equipment         1164.6687460162113
   mc_cooler_in_isen_deltah_to_P_mc_out 51.77757010568604
   mc_cooler_m_dot_co2              644973.5752668495
   mc_cooler_q_dot                  112487.88146994624
   mc_cooler_rho_in                 162.81540254205518
   pc_W_dot                         nan
   pc_cooler_P_in                   nan
   pc_cooler_T_in                   nan
   pc_cooler_UA                     nan
   pc_cooler_W_dot_fan              nan
   pc_cooler_cost_bare_erected      nan
   pc_cooler_cost_equipment         nan
   pc_cooler_m_dot_co2              nan
   pc_cooler_q_dot                  nan
   rc_W_dot                         26027.1918727398
   t_W_dot                          154301.73726794368

INTERPRETATION
   The per-axis cooling column at design is ~9.971e-04 while W_gross_ND is ~1.0, so the
   cooling response is dimensionless and ~0.0997 %% of design gross.
   -> ud_f_W_dot_cool_des should be   100 * cool_des            = 0.0997 %
   -> build_udpc_map.py computed      100 * cool_des / 115000   = 0.0000009 %
   The second is wrong by a factor of W_DOT_NET_DES_KWE = 115000.

   CAVEAT, STATED RATHER THAN GLOSSED: 0.0997 %% of gross is LOW for a dry-cooled sCO2
   cycle, where fan power is usually quoted at 1-2 %%. Two readings remain open and the
   scalars above are what separate them:
     (a) the cooling column is a fraction of gross and the AirCoolerDesign inputs
         (fan_power_frac 0.01, eta_air_cooler_fan 0.5) simply give a small fan load; or
     (b) the column is normalised against something other than design gross, in which
         case 100*cool_des is still not the right magnitude.
   Do NOT ship an annual number that depends on this until one of the two is confirmed
   against a scalar above.
```
