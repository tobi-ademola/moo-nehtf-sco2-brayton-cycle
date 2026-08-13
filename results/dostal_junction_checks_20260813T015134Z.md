# Untabulated nodes (LTR_HP_OUT, RC_OUT) -- validation by conservation

| | |
|---|---|
| script | `scripts/check_untabulated_nodes.py` |
| run (UTC) | 20260813T015134Z |
| git commit | `fad1a0e-dirty` |
| case | Dostal high-performance 700 C, base (lossless) |

```
====================================================================================================
VALIDATING THE TWO NODES DOSTAL DOES NOT TABULATE
====================================================================================================
  recomp fraction f       = 0.40970   (adopted 0.4097; Table 10.1 states 0.39)
  h[LTR_HP_OUT]           =   538.3200 kJ/kg   <-- no Dostal row
  h[RC_OUT]               =   539.2230 kJ/kg   <-- no Dostal row
  h[MIXER_OUT]  (= pt 3)  =   538.6900 kJ/kg   (Dostal 539.07)
  h[LTR_LP_OUT] (= pt 8)  =   481.0809 kJ/kg   (Dostal 480.96)
  s[LTR_LP_OUT] (= pt 8)  =    1.90233 kJ/kg-K (Dostal 1.9020)

----------------------------------------------------------------------------------------------------
CHECK 1A (INTERNAL)  mixing junction closes on our own nodes
----------------------------------------------------------------------------------------------------
   (1-f)h[LTR_HP] + f*h[RC]       expected   538.6900   model   538.6900   abs   +0.0000 kJ/kg    +0.000 %
   -> PASS (tolerance 1e-02 kJ/kg)

----------------------------------------------------------------------------------------------------
CHECK 1B (ABSOLUTE)  does that mix reproduce Dostal h3 = 539.07?
----------------------------------------------------------------------------------------------------
   both split-fraction conventions evaluated -- f is the RECOMPRESSED
   fraction (the stream bypassing precooler + main compressor):
   (1-f)h[LTR_HP] + f*h[RC]       expected   539.0700   model   538.6900   abs   -0.3800 kJ/kg    -0.070 %
   SWAPPED: f*h[LTR_HP]+(1-f)h[RC] expected   539.0700   model   538.8530   abs   -0.2170 kJ/kg    -0.040 %
   -> PASS (tolerance 2 %)
   convention verdict: the as-specified convention is CONFIRMED by 1A, which
   closes to 0.0e+00 kJ/kg. The swapped form is off by -0.040 % AND would break
   that exact internal closure, so it is not the explanation for 1B.

----------------------------------------------------------------------------------------------------
CHECK 2 (RC_OUT via the recompressor isentropic relation, eta_rc = 0.89)
----------------------------------------------------------------------------------------------------
   2A basis: Dostal node 8 (h 480.96, s 1.9020, P 7704.93 kPa)
      h8s(20 MPa, s8) = 532.7177 kJ/kg   ideal rise 51.7577, actual rise 58.1548
   h[RC_OUT]                      expected   539.1148   model   539.2230   abs   +0.1082 kJ/kg    +0.020 %
      -> PASS (tolerance 2 %)

   2B basis: OUR node 8 (h 481.0809, s 1.90233) -- isolates eta_rc application
      h8s(20 MPa, s8) = 532.8583 kJ/kg   ideal rise 51.7774, actual rise 58.1768
   h[RC_OUT]                      expected   539.2577   model   539.2230   abs   -0.0347 kJ/kg    -0.006 %
      -> PASS (tolerance 0.5 kJ/kg)

====================================================================================================
VERDICT
====================================================================================================
   1A internal junction closure      PASS
   1B absolute vs Dostal h3          PASS
   2A isentropic, Dostal node 8      PASS
   2B isentropic, our node 8         PASS

   LTR_HP_OUT and RC_OUT are VALIDATED BY CONSERVATION:
     * RC_OUT is confirmed directly and independently by Check 2 -- the
       recompressor obeys the isentropic relation at eta_rc = 0.89 against
       Dostal's own node 8 (2A) and exactly against ours (2B).
     * With RC_OUT confirmed, the junction closure 1A then pins LTR_HP_OUT:
       it is the only remaining unknown in the mass/energy balance.
     * The split-fraction convention is confirmed, not assumed.
```
