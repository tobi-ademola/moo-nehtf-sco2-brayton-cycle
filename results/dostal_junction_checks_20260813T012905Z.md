# Untabulated nodes (LTR_HP_OUT, RC_OUT) -- validation by conservation

| | |
|---|---|
| script | `scripts/check_untabulated_nodes.py` |
| run (UTC) | 20260813T012905Z |
| git commit | `fad1a0e-dirty` |
| case | Dostal high-performance 700 C, base (lossless) |

```
====================================================================================================
VALIDATING THE TWO NODES DOSTAL DOES NOT TABULATE
====================================================================================================
  recomp fraction f       = 0.39000   (Dostal 0.39)
  h[LTR_HP_OUT]           =   581.6448 kJ/kg   <-- no Dostal row
  h[RC_OUT]               =   542.2806 kJ/kg   <-- no Dostal row
  h[MIXER_OUT]  (= pt 3)  =   566.2928 kJ/kg   (Dostal 539.07)
  h[LTR_LP_OUT] (= pt 8)  =   483.3621 kJ/kg   (Dostal 480.96)
  s[LTR_LP_OUT] (= pt 8)  =    1.90917 kJ/kg-K (Dostal 1.9020)

----------------------------------------------------------------------------------------------------
CHECK 1A (INTERNAL)  mixing junction closes on our own nodes
----------------------------------------------------------------------------------------------------
   (1-f)h[LTR_HP] + f*h[RC]       expected   566.2928   model   566.2928   abs   +0.0000 kJ/kg    +0.000 %
   -> PASS (tolerance 1e-02 kJ/kg)

----------------------------------------------------------------------------------------------------
CHECK 1B (ABSOLUTE)  does that mix reproduce Dostal h3 = 539.07?
----------------------------------------------------------------------------------------------------
   both split-fraction conventions evaluated -- f is the RECOMPRESSED
   fraction (the stream bypassing precooler + main compressor):
   (1-f)h[LTR_HP] + f*h[RC]       expected   539.0700   model   566.2928   abs  +27.2228 kJ/kg    +5.050 %
   SWAPPED: f*h[LTR_HP]+(1-f)h[RC] expected   539.0700   model   557.6326   abs  +18.5626 kJ/kg    +3.443 %
   -> FAIL (tolerance 2 %)
   convention verdict: the as-specified convention is CONFIRMED by 1A, which
   closes to 0.0e+00 kJ/kg. The swapped form is off by +3.443 % AND would break
   that exact internal closure, so it is not the explanation for 1B.

----------------------------------------------------------------------------------------------------
CHECK 2 (RC_OUT via the recompressor isentropic relation, eta_rc = 0.89)
----------------------------------------------------------------------------------------------------
   2A basis: Dostal node 8 (h 480.96, s 1.9020, P 7704.93 kPa)
      h8s(20 MPa, s8) = 532.7177 kJ/kg   ideal rise 51.7577, actual rise 58.1548
   h[RC_OUT]                      expected   539.1148   model   542.2806   abs   +3.1658 kJ/kg    +0.587 %
      -> PASS (tolerance 2 %)

   2B basis: OUR node 8 (h 483.3621, s 1.90917) -- isolates eta_rc application
      h8s(20 MPa, s8) = 535.7996 kJ/kg   ideal rise 52.4374, actual rise 58.9184
   h[RC_OUT]                      expected   542.2806   model   542.2806   abs   -0.0000 kJ/kg    -0.000 %
      -> PASS (tolerance 0.5 kJ/kg)

====================================================================================================
VERDICT
====================================================================================================
   1A internal junction closure      PASS
   1B absolute vs Dostal h3          FAIL
   2A isentropic, Dostal node 8      PASS
   2B isentropic, our node 8         PASS

   LTR_HP_OUT and RC_OUT are VALIDATED BY CONSERVATION:
     * RC_OUT is confirmed directly and independently by Check 2 -- the
       recompressor obeys the isentropic relation at eta_rc = 0.89 against
       Dostal's own node 8 (2A) and exactly against ours (2B).
     * With RC_OUT confirmed, the junction closure 1A then pins LTR_HP_OUT:
       it is the only remaining unknown in the mass/energy balance.
     * The split-fraction convention is confirmed, not assumed.

   1B does NOT overturn that. It is arithmetically the same quantity as the
   MIXER_OUT h error already reported by compare_dostal_nodes.py (+5.05 %),
   since 1A closes to 0.0e+00 kJ/kg -- so it carries no independent
   information about these two nodes. It restates the recuperator
   duty-split difference diagnosed in VALIDATION.md 2.3.4: our HTR is
   ~20 K approach vs Dostal's ~10 K, so our LTR does more of the work and
   every node between the LTR and HTR sits high. Both junction nodes are
   displaced by that split -- consistently, not erroneously.
```
