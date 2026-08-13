# Diagnostic: recuperator tightness x pressure loss (2x2)

| | |
|---|---|
| script | `scripts/dostal_dp_recup_matrix.py` |
| run (UTC) | 20260813T015147Z |
| git commit | `fad1a0e-dirty` |
| status | DIAGNOSTIC -- does not change any pinned baseline |

```
============================================================================================================
DIAGNOSTIC 2x2 -- RECUPERATOR TIGHTNESS x PRESSURE LOSS
============================================================================================================
Dostal's own per-HX pressure loss, derived from Table 10.4 node pressures:
   LTR_HP     9.78 kPa on  20000.00 kPa inlet  ->  frac 0.000489
   HTR_HP    45.66 kPa on  19990.22 kPa inlet  ->  frac 0.002284
   PHX      130.00 kPa on  19944.56 kPa inlet  ->  frac 0.006518
   HTR_LP   126.58 kPa on   7929.22 kPa inlet  ->  frac 0.015964
   LTR_LP    97.71 kPa on   7802.64 kPa inlet  ->  frac 0.012523
   cooler    12.62 kPa on   7704.93 kPa inlet  ->  frac 0.001638
   (PHX comes out at exactly 130.00 kPa = Table 10.1's primary-system dP.)

Dostal's approach temps, also from Table 10.4:
   HTR cold end  node7 - node3 = 169.85 - 159.88 = 9.97 K
   LTR cold end  node8 - node2 =  71.05 -  61.10 = 9.95 K   -> using 10 K

------------------------------------------------------------------------------------------------------------
CASE A -- legacy: eps 0.95, lossless, f 0.39
------------------------------------------------------------------------------------------------------------
   eta_thermal       51.532 %   (+0.262 pp vs Dostal 51.27 %)
   eff_HTR/eff_LTR  0.95000 / 0.95000      HTR approach  20.13 K (Dostal 9.97)
   HTR duty          434.61 kJ/kg  (Dostal 472.96)
   MIXER_OUT  h err  +5.050 %      HTR_LP_OUT h err  +5.373 %
   RMS h  2.649 %   RMS s  1.650 %   RMS P  1.220 %
   flagged nodes remaining: 2 of 8   (4 of 32 node-quantity pairs)
------------------------------------------------------------------------------------------------------------
CASE B -- tighter only: 10 K approach, lossless
------------------------------------------------------------------------------------------------------------
   eta_thermal       51.891 %   (+0.621 pp vs Dostal 51.27 %)
   eff_HTR/eff_LTR  0.97631 / 0.88445      HTR approach   9.96 K (Dostal 9.97)
   HTR duty          476.40 kJ/kg  (Dostal 472.96)
   MIXER_OUT  h err  -2.500 %      HTR_LP_OUT h err  -1.522 %
   RMS h  1.109 %   RMS s  0.674 %   RMS P  1.220 %
   flagged nodes remaining: 1 of 8   (1 of 32 node-quantity pairs)
------------------------------------------------------------------------------------------------------------
CASE C -- dP only: eps 0.95, Dostal dP
------------------------------------------------------------------------------------------------------------
   eta_thermal       50.327 %   (-0.943 pp vs Dostal 51.27 %)
   eff_HTR/eff_LTR  0.95000 / 0.95000      HTR approach  20.37 K (Dostal 9.97)
   HTR duty          440.68 kJ/kg  (Dostal 472.96)
   MIXER_OUT  h err  +5.026 %      HTR_LP_OUT h err  +5.329 %
   RMS h  2.600 %   RMS s  1.602 %   RMS P  0.000 %
   flagged nodes remaining: 2 of 8   (4 of 32 node-quantity pairs)
------------------------------------------------------------------------------------------------------------
CASE D -- BOTH: 10 K approach + Dostal dP
------------------------------------------------------------------------------------------------------------
   eta_thermal       50.658 %   (-0.612 pp vs Dostal 51.27 %)
   eff_HTR/eff_LTR  0.97659 / 0.87940      HTR approach   9.93 K (Dostal 9.97)
   HTR duty          483.98 kJ/kg  (Dostal 472.96)
   MIXER_OUT  h err  -2.824 %      HTR_LP_OUT h err  -1.820 %
   RMS h  1.197 %   RMS s  0.771 %   RMS P  0.000 %
   flagged nodes remaining: 1 of 8   (1 of 32 node-quantity pairs)
------------------------------------------------------------------------------------------------------------
CASE E -- f = 0.4097 only (table-implied), eps 0.95
------------------------------------------------------------------------------------------------------------
   eta_thermal       51.174 %   (-0.096 pp vs Dostal 51.27 %)
   eff_HTR/eff_LTR  0.95000 / 0.95000      HTR approach  19.99 K (Dostal 9.97)
   HTR duty          430.89 kJ/kg  (Dostal 472.96)
   MIXER_OUT  h err  +5.980 %      HTR_LP_OUT h err  +5.987 %
   RMS h  3.082 %   RMS s  1.930 %   RMS P  1.220 %
   flagged nodes remaining: 2 of 8   (4 of 32 node-quantity pairs)
------------------------------------------------------------------------------------------------------------
CASE F -- ADOPTED: f 0.4097 + 10 K + Dostal dP
------------------------------------------------------------------------------------------------------------
   eta_thermal       51.289 %   (+0.019 pp vs Dostal 51.27 %)
   eff_HTR/eff_LTR  0.97625 / 0.93095      HTR approach   9.94 K (Dostal 9.97)
   HTR duty          473.26 kJ/kg  (Dostal 472.96)
   MIXER_OUT  h err  -0.070 %      HTR_LP_OUT h err  -0.051 %
   RMS h  0.032 %   RMS s  0.020 %   RMS P  0.000 %
   flagged nodes remaining: 0 of 8   (0 of 32 node-quantity pairs)

============================================================================================================
SUMMARY
============================================================================================================
case  configuration                              eta %      d pp   MIXER h%   HTRLP h%   RMS h%   flags
------------------------------------------------------------------------------------------------------------
A     legacy: eps 0.95, lossless, f 0.39        51.532    +0.262     +5.050     +5.373    2.649       2
B     tighter only: 10 K approach, lossless     51.891    +0.621     -2.500     -1.522    1.109       1
C     dP only: eps 0.95, Dostal dP              50.327    -0.943     +5.026     +5.329    2.600       2
D     BOTH: 10 K approach + Dostal dP           50.658    -0.612     -2.824     -1.820    1.197       1
E     f = 0.4097 only (table-implied), eps 0.95    51.174    -0.096     +5.980     +5.987    3.082       2
F     ADOPTED: f 0.4097 + 10 K + Dostal dP      51.289    +0.019     -0.070     -0.051    0.032       0

Does the compensating-error hypothesis hold?
   tightening alone (A->B) moves eta +0.359 pp  -> UP, as predicted
   dP alone         (A->C) moves eta -1.205 pp  -> DOWN, as predicted
   B overshoots 51.27 %?  YES (+0.621 pp)
   D lands on 51.27 %?    NO (-0.612 pp)
   D clears both flagged nodes? NO (1 remaining)

Does the recompressed-fraction explanation compete?
   f = 0.4097 alone (A->E) moves MIXER_OUT h err +5.050 -> +5.980 %
   and eta +0.262 pp -> -0.096 pp
   full combination F: eta +0.019 pp, RMS h 0.032 %, 0 node(s) flagged

   best case on node agreement (RMS h): F
   best case on eta            (|d pp|): F

============================================================================================================
FULL NODE TABLE FOR THE BEST CASE (F) -- same format as compare_dostal_nodes.py
============================================================================================================
pt   node        qty  unit             Dostal        PySAM    abs error    % error  flag
--------------------------------------------------------------------------------------------------------
1    MC_IN       T    C               32.0000      32.0000      +0.0000    +0.000 %  
1    MC_IN       P    kPa           7692.3100    7692.3077      -0.0023    -0.000 %  
1    MC_IN       h    kJ/kg          306.6700     306.6747      +0.0047    +0.002 %  
1    MC_IN       s    kJ/kg-K          1.3478       1.3478      -0.0000    -0.000 %  

2    MC_OUT      T    C               61.1000      61.0985      -0.0015    -0.000 %  
2    MC_OUT      P    kPa          20000.0000   20000.0000      +0.0000    +0.000 %  
2    MC_OUT      h    kJ/kg          327.2600     327.2563      -0.0037    -0.001 %  
2    MC_OUT      s    kJ/kg-K          1.3546       1.3546      -0.0000    -0.002 %  

3    MIXER_OUT   T    C              159.8800     159.6429      -0.2371    -0.055 %  
3    MIXER_OUT   P    kPa          19990.2200   19990.2200      +0.0000    +0.000 %  
3    MIXER_OUT   h    kJ/kg          539.0700     538.6900      -0.3800    -0.070 %  
3    MIXER_OUT   s    kJ/kg-K          1.9168       1.9159      -0.0009    -0.045 %  

4    HTR_HP_OUT  T    C              531.3300     531.2557      -0.0743    -0.009 %  
4    HTR_HP_OUT  P    kPa          19944.5600   19944.5600      +0.0000    +0.000 %  
4    HTR_HP_OUT  h    kJ/kg         1012.0300    1011.9451      -0.0849    -0.008 %  
4    HTR_HP_OUT  s    kJ/kg-K          2.7132       2.7131      -0.0001    -0.004 %  

5    TURB_IN     T    C              700.0000     700.0000      +0.0000    +0.000 %  
5    TURB_IN     P    kPa          19814.5600   19814.5600      +0.0000    +0.000 %  
5    TURB_IN     h    kJ/kg         1223.3400    1223.3393      -0.0007    -0.000 %  
5    TURB_IN     s    kJ/kg-K          2.9529       2.9529      -0.0000    -0.001 %  

6    TURB_OUT    T    C              578.3100     578.3091      -0.0009    -0.000 %  
6    TURB_OUT    P    kPa           7929.2200    7929.2176      -0.0024    -0.000 %  
6    TURB_OUT    h    kJ/kg         1078.9500    1078.9481      -0.0019    -0.000 %  
6    TURB_OUT    s    kJ/kg-K          2.9719       2.9719      -0.0000    -0.002 %  

7    HTR_LP_OUT  T    C              169.8500     169.5830      -0.2670    -0.060 %  
7    HTR_LP_OUT  P    kPa           7802.6400    7802.6377      -0.0023    -0.000 %  
7    HTR_LP_OUT  h    kJ/kg          605.9800     605.6718      -0.3082    -0.051 %  
7    HTR_LP_OUT  s    kJ/kg-K          2.2212       2.2206      -0.0006    -0.029 %  

8    LTR_LP_OUT  T    C               71.0500      71.1272      +0.0772    +0.022 %  
8    LTR_LP_OUT  P    kPa           7704.9300    7704.9277      -0.0023    -0.000 %  
8    LTR_LP_OUT  h    kJ/kg          480.9600     481.0809      +0.1209    +0.025 %  
8    LTR_LP_OUT  s    kJ/kg-K          1.9020       1.9023      +0.0003    +0.017 %  

   Case F is the ADOPTED baseline (VALIDATION.md 2.3.4a); this run is the
   evidence for that decision and a regression test of it. F should win on
   both eta and node agreement -- if it stops winning, something regressed.
```
