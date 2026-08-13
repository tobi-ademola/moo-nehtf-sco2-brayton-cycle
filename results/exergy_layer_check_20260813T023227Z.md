# Exergy layer -- arithmetic soundness check

| | |
|---|---|
| script | `scripts/exergy_layer_check.py` |
| run (UTC) | 20260813T023227Z |
| git commit | `f2fde9d-dirty` |
| case | case F, the adopted baseline |

```
====================================================================================================
EXERGY LAYER CHECK -- case F, computed from ssc's own h and s
====================================================================================================
  reference state  T0_ref = 305.15 K (32.00 C), P0 = 7692.31 kPa  [Dostal node 1]
  environment      T0_amb = 299.15 K (26.00 C)  [T_amb_des -- what the cycle actually rejects to]
  m_dot_co2 92.233 kg/s   f_rc 0.40970   W_net 10000.00 kW

  NOTE: node 1 is the compressor inlet at 7692.31 kPa, NOT a true dead state.
  e(node 1) = 0 is therefore true BY CONSTRUCTION -- it verifies the
  arithmetic is wired correctly, it does not verify the physics.

----------------------------------------------------------------------------------------------------
PHYSICAL EXERGY PER NODE   e = (h - h0) - T0*(s - s0),  h0/s0 = node 1
----------------------------------------------------------------------------------------------------
#   node             T[C]      P[kPa]   h[kJ/kg]  s[kJ/kg-K]     e@T0_ref     e@T0_amb
0   MC_IN          32.000     7692.31    306.675     1.34780       0.0000       0.0000
1   MC_OUT         61.099    20000.00    327.256     1.35458      18.5119      18.5526
2   LTR_HP_OUT    159.407    19990.22    538.320     1.91508      58.5392      61.9429
3   MIXER_OUT     159.643    19990.22    538.690     1.91593      58.6482      62.0570
4   HTR_HP_OUT    531.256    19944.56   1011.945     2.71310     288.6469     296.8387
5   TURB_IN       700.000    19814.56   1223.339     2.95286     426.8784     436.5088
6   TURB_OUT      578.309     7929.22   1078.948     2.97185     276.6923     286.4366
7   HTR_LP_OUT    169.583     7802.64    605.672     2.22055      32.6753      37.9119
8   LTR_LP_OUT     71.127     7704.93    481.081     1.90233       5.1906       8.5178
9   RC_OUT        159.983    19990.22    539.223     1.91716      58.8056      62.2218

   e(node 1)        = +0.000e+00 kJ/kg   -> PASS (zero by construction)
   max exergy       = node 5 (TURB_IN) at 426.8784 kJ/kg   -> PASS (turbine inlet)
   all e >= 0?        yes (min 0.0000 at node 0)

----------------------------------------------------------------------------------------------------
COMPONENT EXERGY DESTRUCTION   Ed = T0 * Sgen   (Gouy-Stodola)
----------------------------------------------------------------------------------------------------
component                Sgen[kW/K]  Ed@T0_amb[kW]  Ed@T0_ref[kW]    share%
HTR  high-T recup          +4.23071        1265.62        1291.00    41.38
TURB turbine               +1.75154         523.97         534.48    17.13
COOL precooler             +1.55023         463.75         473.05    15.16
LTR  low-T recup           +1.16569         348.71         355.71    11.40
PHX  primary HX            +0.59713         178.63         182.21     5.84
RC   recompressor          +0.56061         167.71         171.07     5.48
MC   main compressor       +0.36927         110.47         112.68     3.61
MIX  mixer                 +0.00003           0.01           0.01     0.00
TOTAL                     +10.22521        3058.87        3120.22   100.00

   every component Ed > 0?   PASS
   largest destroyer         HTR  high-T recup at 1265.62 kW (41.4 % of total)
   HTR-dominant (Battisti 2023, SOURCES.md F2)?   PASS

----------------------------------------------------------------------------------------------------
CYCLE-WIDE EXERGY BALANCE   Ex_in(salt) == W_net + sum(Ed)
----------------------------------------------------------------------------------------------------
   at T0_amb (the environment) Ex_in  13060.82 = W_net  10000.00 + Ed   3058.87  ->  residual   +1.949 kW (+0.0149 %)
   at T0_ref (node 1)          Ex_in  12931.72 = W_net  10000.00 + Ed   3120.22  ->  residual -188.502 kW (-1.4577 %)

   balance closes at T0_amb?  PASS (|residual| = 1.9491 kW, 1.49e-04 relative)
   This is the real test: it uses every h, every s, both mass flows, the
   salt-side properties and the work terms at once. Sign checks cannot
   catch a scaling or units error; this can.

   exergy efficiency (2nd law)  W_net / Ex_in = 0.7656 = 76.56 %

====================================================================================================
VERDICT
====================================================================================================
   e(node 1) = 0 by construction              PASS
   max exergy at node 5 (turbine inlet)       PASS
   every component Ed > 0                     PASS
   HTR is the largest single destroyer        PASS
   cycle exergy balance closes at T0_amb      PASS

   The exergy layer is arithmetically sound on data the model ALREADY
   carries. MASTER_PLAN 5's CoolProp-reconstruction fallback (+~1 day)
   is NOT needed and that risk can be closed.
```
